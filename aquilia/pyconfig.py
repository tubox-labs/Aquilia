"""
Aquilia Python-Native Configuration System  (``aquilia.pyconfig``)
==================================================================

A zero-YAML, class-based configuration DSL for operational environment config.

**Single-file architecture** — define AquilaConfig subclasses directly
in ``workspace.py`` alongside your Workspace builder:

+-------------------+------------------------------------------+
| ``workspace.py``  | Everything: structure, modules,          |
|                   | integrations, AND environment config     |
|                   | (AquilaConfig subclasses)                |
+-------------------+------------------------------------------+

Design goals
------------
* **Pure Python, zero YAML** — config is code; type-checked by Pylance/mypy,
  auto-completed in the IDE, diffable in ``git blame``.
* **Layered inheritance** — environments subclass a ``BaseEnv``; only changed
  fields are redefined, everything else is inherited.
* **Secret management** — ``Secret`` never leaks values into ``repr()`` or logs.
* **Live env-var overlay** — ``Env("VAR", default=...)`` reads the OS environment
  at access time so CI/CD can inject values without touching source.
* **ConfigLoader bridge** — :meth:`AquilaConfig.to_loader` returns a populated
  :class:`~aquilia.config.ConfigLoader` so all existing subsystems work unchanged.

Quick-start
-----------
Define environment config inline in ``workspace.py``::

    from aquilia import Workspace, Module, Integration
    from aquilia.config_builders import AquilaConfig, Env, Secret

    class BaseEnv(AquilaConfig):
        class server(AquilaConfig.Server):
            host    = "127.0.0.1"
            port    = 8000
            workers = 1

        class auth(AquilaConfig.Auth):
            secret_key      = Secret(env="AQ_SECRET_KEY", required=True)
            password_hasher = AquilaConfig.PasswordHasher(algorithm="argon2id")

    class DevEnv(BaseEnv):
        env = "dev"
        class server(BaseEnv.server):
            reload = True
            debug  = True

    class ProdEnv(BaseEnv):
        env = "prod"
        class server(BaseEnv.server):
            host    = "0.0.0.0"
            workers = Env("WEB_WORKERS", default=4, cast=int)
        class auth(BaseEnv.auth):
            secret_key      = Secret(env="AQ_SECRET_KEY", required=True)
            password_hasher = AquilaConfig.PasswordHasher(
                algorithm="argon2id", time_cost=3, memory_cost=131072,
            )

    workspace = (
        Workspace("myapp")
        .env_config(BaseEnv)      # resolved by AQ_ENV at runtime
        .module(...)
    )

``Workspace.env_config()`` wires the config automatically.
To load manually::

    loader = BaseEnv.from_env_var().to_loader()   # reads AQ_ENV
"""

from __future__ import annotations

import inspect
import json
import logging
import os
import threading
import warnings
from collections.abc import Callable
from dataclasses import field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, TypeAlias, TypeVar, cast

if TYPE_CHECKING:
    from aquilia.config import ConfigLoader

log = logging.getLogger(__name__)

# ============================================================================
# Type definitions for configuration values
# ============================================================================

#: Any value that can be used in configuration
ConfigValue: TypeAlias = str | int | float | bool | list[Any] | dict[str, Any] | None

#: Type variable for generic config value casting
T = TypeVar("T")

#: Callable that casts string environment values to typed values
EnvCaster: TypeAlias = Callable[[str], Any]

#: Valid cast types for Env class
EnvCastType: TypeAlias = type | EnvCaster | None

# ============================================================================
# Module-level caching for resolved AquilaConfig classes
# ============================================================================

#: Cache for AquilaConfig.to_dict() results - dict[config_class, resolved_dict]
_config_class_cache: dict[type, dict[str, Any]] = {}
_config_cache_lock = threading.RLock()


# ============================================================================
# Secret descriptor — never leaks values in repr/logs
# ============================================================================


class Secret:
    """
    A configuration field that holds a sensitive value (password, API key …).

    Values are sourced in this priority order:
      1. ``env`` — from the named environment variable.
      2. ``value`` — from the literal value passed at definition time.
      3. ``default`` — fallback (may be ``None``).

    The value is **never** included in :func:`repr`, :func:`str`, or
    serialised :func:`to_dict` output unless you call
    :meth:`reveal`.

    Dotenv Integration
    ------------------
    When ``reveal()`` is called, the native dotenv loader is automatically
    triggered to ensure ``.env`` files are loaded before resolving.
    This means you do NOT need to call ``load_dotenv()`` manually.

    Examples::

        secret_key = Secret(env="AQ_SECRET_KEY", required=True)
        db_password = Secret(env="DB_PASSWORD", default="devpassword")
        api_key     = Secret(value="sk-live-abc123")  # inline (dev only!)
    """

    _REDACTED: Final[str] = "<secret>"

    __slots__ = ("_literal", "_env_name", "_default", "_required")

    def __init__(
        self,
        value: str | None = None,
        *,
        env: str | None = None,
        default: str | None = None,
        required: bool = False,
    ) -> None:
        self._literal: str | None = value
        self._env_name: str | None = env
        self._default: str | None = default
        self._required: bool = required

    def reveal(self) -> str | None:
        """
        Return the actual secret value (use deliberately).

        Automatically loads .env files if not already loaded.
        """
        # Ensure dotenv is loaded before resolving
        _ensure_dotenv_loaded()

        if self._env_name:
            val = os.environ.get(self._env_name)
            if val is not None:
                return val
        if self._literal is not None:
            return self._literal
        if self._default is not None:
            return self._default
        if self._required:
            from aquilia.faults.domains import ConfigMissingFault

            raise ConfigMissingFault(
                key=self._env_name or "secret",
                metadata={
                    "hint": f"Set environment variable {self._env_name!r} or provide a literal value.",
                },
            )
        return None

    @property
    def env_name(self) -> str | None:
        """Return the environment variable name, if any."""
        return self._env_name

    @property
    def is_required(self) -> bool:
        """Return whether this secret is required."""
        return self._required

    def __repr__(self) -> str:
        env_hint = f"env={self._env_name!r}" if self._env_name else ""
        return f"Secret({env_hint or 'inline'}, {'*required*' if self._required else 'optional'})"

    def __str__(self) -> str:
        return self._REDACTED


# ============================================================================
# Env binding — transparently reads from environment variables
# ============================================================================

# Flag to track if dotenv has been loaded
_dotenv_loaded: bool = False
_dotenv_lock: bool = False  # Simple reentrant protection


def _resolve_dotenv_options(config_cls: type[Any] | None) -> dict[str, Any]:
    """
    Resolve dotenv loading options from an AquilaConfig class.

    Returns default loader options when no class-specific policy exists.
    """
    default_env_name = str(getattr(config_cls, "env", os.environ.get("AQUILIA_ENV") or "dev"))

    defaults: dict[str, Any] = {
        "search_paths": [],
        "auto_load": True,
        "override": False,
        "interpolate": True,
        "required_paths": set(),
    }

    try:
        from aquilia.dotenv import _default_dotenv_search_paths

        defaults["search_paths"] = _default_dotenv_search_paths(default_env_name)
    except ImportError:
        defaults["search_paths"] = [
            ".env",
            ".env.example",
            ".env.defaults",
            ".env.default",
            ".env.local",
            f".env.{default_env_name}",
            f".env.{default_env_name}.local",
            "config/.env",
            f"config/.env.{default_env_name}",
            f"config/.env.{default_env_name}.local",
        ]
    if config_cls is None:
        return defaults

    dotenv_cfg = getattr(config_cls, "dotenv", None)
    if not isinstance(dotenv_cfg, type):
        return defaults

    env_name = default_env_name
    strict = bool(getattr(dotenv_cfg, "strict", False))

    entries: list[Any] = []
    single = getattr(dotenv_cfg, "file", None)
    if single is not None:
        entries.append(single)

    many = getattr(dotenv_cfg, "files", None)
    if many is not None:
        if isinstance(many, (list, tuple)):
            entries.extend(many)
        else:
            entries.append(many)

    if not entries:
        entries = defaults["search_paths"].copy()

    search_paths: list[str] = []
    required_paths: set[str] = set()

    for entry in entries:
        required = strict
        raw_path: Any = entry

        if hasattr(entry, "path"):
            raw_path = getattr(entry, "path", None)
            required = bool(getattr(entry, "required", strict))

        if raw_path is None:
            continue

        path_str = str(raw_path)
        if "{env}" in path_str:
            path_str = path_str.format(env=env_name)

        search_paths.append(path_str)
        if required:
            required_paths.add(path_str)

    if not search_paths:
        search_paths = defaults["search_paths"].copy()

    auto_load = bool(getattr(dotenv_cfg, "auto_load", True))
    override = bool(getattr(dotenv_cfg, "override", False))
    interpolate = bool(getattr(dotenv_cfg, "interpolate", True))

    return {
        "search_paths": search_paths,
        "auto_load": auto_load,
        "override": override,
        "interpolate": interpolate,
        "required_paths": required_paths,
    }


def _validate_required_dotenv_files(search_paths: list[str], required_paths: set[str]) -> None:
    """Validate required dotenv files before invoking the loader."""
    if not required_paths:
        return

    from aquilia.dotenv import _find_workspace_root
    from aquilia.faults.domains import ConfigMissingFault

    workspace_root = _find_workspace_root()
    missing: list[str] = []

    for path in search_paths:
        if path not in required_paths:
            continue
        file_path = Path(path)
        if not file_path.is_absolute() and workspace_root is not None:
            file_path = workspace_root / file_path
        if not file_path.exists():
            missing.append(path)

    if missing:
        raise ConfigMissingFault(
            key="dotenv.files",
            metadata={
                "hint": f"Missing required dotenv file(s): {', '.join(missing)}",
            },
        )


def _ensure_dotenv_loaded(*, config_cls: type[Any] | None = None) -> None:
    """
    Ensure .env files are loaded into os.environ.

    This is called automatically when Env.resolve() or Secret.reveal()
    is invoked. Uses the DotEnvLoader singleton for thread-safe,
    idempotent loading.
    """
    global _dotenv_loaded, _dotenv_lock

    if _dotenv_loaded or _dotenv_lock:
        return

    _dotenv_lock = True
    try:
        from aquilia.dotenv import DotEnvLoader

        options = _resolve_dotenv_options(config_cls)
        _validate_required_dotenv_files(options["search_paths"], options["required_paths"])
        DotEnvLoader.configure(
            search_paths=options["search_paths"],
            auto_load=options["auto_load"],
            override=options["override"],
            interpolate=options["interpolate"],
        )
        DotEnvLoader.ensure_loaded(search_paths=options["search_paths"])
        _dotenv_loaded = True
    except ImportError:
        # Fallback if dotenv module is not available
        log.debug("aquilia.dotenv not available, skipping auto-load")
        _dotenv_loaded = True
    except Exception as exc:
        from aquilia.faults.domains import ConfigMissingFault

        if isinstance(exc, ConfigMissingFault):
            raise
        log.warning("Failed to auto-load .env: %s", exc)
        _dotenv_loaded = True
    finally:
        _dotenv_lock = False


def reset_dotenv_state() -> None:
    """
    Reset the dotenv loading state.

    Use this in tests to allow .env reloading with different configuration.
    """
    global _dotenv_loaded
    _dotenv_loaded = False
    try:
        from aquilia.dotenv import DotEnvLoader

        DotEnvLoader.reset()
    except ImportError:
        pass


class Env:
    """
    Bind a configuration field to an environment variable.

    Resolves at read time so runtime changes to the environment are
    reflected immediately (useful in test setups).

    Dotenv Integration
    ------------------
    When ``resolve()`` is called, the native dotenv loader is automatically
    triggered to ensure ``.env`` files are loaded. This means you do NOT
    need to call ``load_dotenv()`` manually — it's handled automatically.

    The loader respects existing environment variables (will not override).

    Type Casting
    ------------
    - If ``cast`` is provided, it's applied to the raw string value.
    - If ``cast`` is ``bool``, special handling converts common truthy/falsy strings.
    - If no ``cast`` is provided, auto-casting is attempted:
      int → float → JSON → str (in that order).

    Examples::

        # These will automatically read from .env if present
        debug   = Env("AQ_DEBUG",   default=False,  cast=bool)
        workers = Env("AQ_WORKERS", default=4,       cast=int)
        host    = Env("AQ_HOST",    default="127.0.0.1")

        # .env file contents:
        # AQ_DEBUG=true
        # AQ_WORKERS=8
        # AQ_HOST=0.0.0.0
    """

    _CAST_TRUE: Final[frozenset[str]] = frozenset({"1", "true", "yes", "on"})
    _CAST_FALSE: Final[frozenset[str]] = frozenset({"0", "false", "no", "off"})

    # Class-level flag to control auto-loading behavior
    _auto_load_enabled: bool = True

    __slots__ = ("_name", "_default", "_cast", "_required", "_resolved_cache", "_cache_valid")

    def __init__(
        self,
        name: str,
        *,
        default: ConfigValue = None,
        cast: EnvCastType = None,
        required: bool = False,
    ) -> None:
        """
        Initialize an environment variable binding.

        Args:
            name: Environment variable name (e.g., "DATABASE_URL").
            default: Default value if the variable is not set.
            cast: Type or callable to cast the string value.
            required: If True, raise ConfigMissingFault when the variable
                      is not set and no default is provided.
        """
        self._name: str = name
        self._default: ConfigValue = default
        self._cast: EnvCastType = cast
        self._required: bool = required
        # Cache to avoid repeated resolution during the same config load
        self._resolved_cache: ConfigValue = None
        self._cache_valid: bool = False

    @property
    def name(self) -> str:
        """Return the environment variable name."""
        return self._name

    @property
    def default(self) -> ConfigValue:
        """Return the default value."""
        return self._default

    @property
    def is_required(self) -> bool:
        """Return whether this env var is required."""
        return self._required

    def resolve(self, *, use_cache: bool = False) -> ConfigValue:
        """
        Return the resolved value from the environment or default.

        Automatically loads .env files on first call if auto-loading is enabled.

        Args:
            use_cache: If True, return cached value if available.
                       Useful during config serialization to avoid
                       resolving the same value multiple times.

        Returns:
            The resolved and cast value.
        """
        # Return cached value if requested and available
        if use_cache and self._cache_valid:
            return self._resolved_cache

        # Ensure dotenv is loaded before resolving
        if self._auto_load_enabled:
            _ensure_dotenv_loaded()

        raw = os.environ.get(self._name)

        if raw is None:
            # No value in environment - check if required
            if self._required and self._default is None:
                from aquilia.faults.domains import ConfigMissingFault

                raise ConfigMissingFault(
                    key=self._name,
                    metadata={
                        "hint": f"Set environment variable {self._name!r} or provide a default value.",
                    },
                )
            value = self._default
        elif self._cast is bool:
            value = self._cast_bool(raw)
        elif self._cast is not None:
            value = self._cast(raw)
        else:
            value = self._auto_cast(raw)

        # Cache the result
        self._resolved_cache = value
        self._cache_valid = True

        return value

    def _cast_bool(self, raw: str) -> bool:
        """Cast a string to boolean with common truthy/falsy values."""
        lower = raw.lower()
        if lower in self._CAST_TRUE:
            return True
        if lower in self._CAST_FALSE:
            return False
        return bool(raw)

    def _auto_cast(self, raw: str) -> ConfigValue:
        """
        Auto-cast a string value to the most appropriate type.

        Tries: int → float → JSON → str (in that order).
        """
        # Try int
        try:
            return int(raw)
        except ValueError:
            pass

        # Try float
        try:
            return float(raw)
        except ValueError:
            pass

        # Try JSON (for arrays and objects)
        if raw.startswith(("{", "[")):
            try:
                return cast(ConfigValue, json.loads(raw))
            except json.JSONDecodeError:
                pass

        # Fall back to string
        return raw

    def invalidate_cache(self) -> None:
        """Invalidate the cached resolved value."""
        self._cache_valid = False
        self._resolved_cache = None

    @classmethod
    def disable_auto_load(cls) -> None:
        """
        Disable automatic .env loading.

        Use this if you want to control when .env files are loaded,
        or if you're loading them through a different mechanism.
        """
        cls._auto_load_enabled = False

    @classmethod
    def enable_auto_load(cls) -> None:
        """Enable automatic .env loading (default behavior)."""
        cls._auto_load_enabled = True

    def __repr__(self) -> str:
        return f"Env({self._name!r}, default={self._default!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Env):
            return NotImplemented
        return self._name == other._name and self._default == other._default

    def __hash__(self) -> int:
        return hash((self._name, type(self._default)))


# ============================================================================
# section decorator — annotates nested config classes
# ============================================================================


def section(cls: type) -> type:
    """
    Mark a nested class as a config *section*.

    Sections provide logical grouping and participate in the deep-merge
    produced by :meth:`AquilaConfig.to_dict`.  This is a lightweight
    marker; no runtime behaviour is added beyond tagging.

    Example::

        class MyConfig(AquilaConfig):
            @section
            class database:
                url     = "sqlite:///dev.db"
                echo    = False
    """
    cls._is_aquila_section = True  # type: ignore[attr-defined]
    return cls


# ============================================================================
# ConfigMeta — metaclass for section resolution
# ============================================================================


def _resolve_value(val: Any, *, use_cache: bool = True) -> ConfigValue:
    """
    Unwrap ``Env`` and ``Secret`` wrappers to their runtime values.

    Args:
        val: The value to potentially unwrap.
        use_cache: For Env values, use cached resolution if available.

    Returns:
        The resolved value.
    """
    if isinstance(val, Env):
        return val.resolve(use_cache=use_cache)
    if isinstance(val, Secret):
        return val.reveal()
    return cast(ConfigValue, val)


def _class_to_dict(cls: type, *, use_cache: bool = True) -> dict[str, Any]:
    """
    Recursively convert a (nested) config class into a plain dict.

    Rules:
    - Dunder and private attributes are skipped.
    - Nested classes whose name does not start with ``_`` are recursed.
    - ``Env`` instances are resolved to their runtime value.
    - ``Secret`` instances are revealed (callers decide when to call this).
    - Callable attributes (methods) are skipped.
    - Dataclass/plain-class instances with a ``to_dict`` method are called.

    Args:
        cls: The config class to convert.
        use_cache: For Env values, use cached resolution to avoid
                   duplicate environment lookups during the same
                   to_dict() call.

    Returns:
        Dictionary representation of the config class.
    """
    result: dict[str, Any] = {}
    for name, val in inspect.getmembers(cls):
        if name.startswith("_"):
            continue
        if callable(val) and not isinstance(val, (type, Env, Secret)):
            continue
        if isinstance(val, type):
            # Nested config class → recurse
            result[name] = _class_to_dict(val, use_cache=use_cache)
        elif isinstance(val, Env):
            result[name] = val.resolve(use_cache=use_cache)
        elif isinstance(val, Secret):
            result[name] = val.reveal()
        elif hasattr(val, "to_dict") and callable(val.to_dict):
            result[name] = val.to_dict()
        else:
            result[name] = val
    return result


# ============================================================================
# AquilaConfig — base class for all Python-native configs
# ============================================================================


class AquilaConfig:
    """
    Base class for Aquilia Python-native configuration.

    Subclass this (or a pre-built environment subclass) and override nested
    section classes to declare your configuration.

    Built-in nested section types
    ------------------------------
    Use these as base classes for your section overrides to get type-safe
    defaults and IDE completion:

    - :class:`AquilaConfig.Server`       — HTTP server settings
    - :class:`AquilaConfig.Auth`         — Auth & JWT settings
    - :class:`AquilaConfig.PasswordHasher` — password hashing algorithm config
    - :class:`AquilaConfig.Apps`         — per-module app-specific settings
    - :class:`AquilaConfig.Database`     — database connection settings
    - :class:`AquilaConfig.Cache`        — cache backend settings
    - :class:`AquilaConfig.Sessions`     — session store / transport settings
    - :class:`AquilaConfig.Mail`         — mail provider settings
    - :class:`AquilaConfig.Security`     — security middleware flags
    - :class:`AquilaConfig.Logging`      — logging configuration
    - :class:`AquilaConfig.I18n`         — internationalisation settings

    Example::

        from aquilia.pyconfig import AquilaConfig, Secret, Env

        class MyConfig(AquilaConfig):
            env = "dev"

            class server(AquilaConfig.Server):
                port    = 8080
                workers = Env("WORKERS", default=2, cast=int)

            class auth(AquilaConfig.Auth):
                secret_key = Secret(env="SECRET_KEY", required=True)

            class apps(AquilaConfig.Apps):
                class users:
                    max_connections = 100

        # Load into Aquilia's ConfigLoader
        loader = MyConfig.to_loader()
    """

    #: Which environment this config represents (arbitrary string label).
    env: str = "dev"

    class EnvFile:
        """Descriptor for dotenv file entries with optional required semantics."""

        __slots__ = ("path", "required")

        def __init__(self, path: str | Path, *, required: bool = False) -> None:
            self.path = str(path)
            self.required = required

        def __repr__(self) -> str:
            return f"EnvFile(path={self.path!r}, required={self.required})"

    class Dotenv:
        """Class-level dotenv loading policy for AquilaConfig subclasses."""

        _is_aquila_section: bool = True

        #: Single dotenv file path (alias for ``files=[...]``).
        file: str | Path | None = None
        #: Ordered list of dotenv files. Later files override earlier dotenv files.
        files: list[str | Path | AquilaConfig.EnvFile] | tuple[str | Path | AquilaConfig.EnvFile, ...] | None = None
        #: Enable automatic loading before resolving Env/Secret bindings.
        auto_load: bool = True
        #: If True, dotenv values can override process environment variables.
        override: bool = False
        #: Enable ${VAR} / $VAR interpolation while parsing dotenv files.
        interpolate: bool = True
        #: If True, all configured files are required.
        strict: bool = False

    # ── Built-in nested section types ────────────────────────────────────

    class Server:
        """
        HTTP server settings.

        Maps to the ``server`` / ``runtime`` config path and is forwarded
        to the underlying ASGI server (uvicorn).  Every attribute that
        matches a ``uvicorn.Config`` parameter is passed through
        automatically, so adding a new field here is all you need.

        Grouped by concern:

        **Core**
            host, port, uds, fd, workers, mode, debug

        **Reload / Development**
            reload, reload_dirs, reload_delay, reload_includes,
            reload_excludes

        **Protocol / Implementation**
            http, ws, lifespan, interface, loop

        **Timeouts**
            timeout_keep_alive, timeout_worker_healthcheck,
            timeout_graceful_shutdown

        **Limits**
            backlog, limit_concurrency, limit_max_requests

        **Proxy / Headers**
            proxy_headers, forwarded_allow_ips, server_header,
            date_header, root_path

        **Logging**
            access_log, log_level, use_colors

        **WebSocket**
            ws_max_size, ws_max_queue, ws_ping_interval,
            ws_ping_timeout, ws_per_message_deflate

        **TLS / SSL**
            ssl_keyfile, ssl_certfile, ssl_keyfile_password,
            ssl_ca_certs, ssl_ciphers

        Example (workspace.py)::

            class BaseEnv(AquilaConfig):
                class server(AquilaConfig.Server):
                    host    = "0.0.0.0"
                    port    = 9000
                    workers = 4
                    timeout_keep_alive = 30
                    limit_max_requests = 10000
                    proxy_headers      = True
                    ssl_certfile       = "/etc/certs/cert.pem"
                    ssl_keyfile        = "/etc/certs/key.pem"
        """

        # ── Core ─────────────────────────────────────────────────────
        host: str = "127.0.0.1"
        port: int = 8000
        uds: str | None = None  # Unix domain socket path
        fd: int | None = None  # File descriptor to bind
        workers: int = 1
        mode: str = "dev"
        debug: bool = False

        # ── Reload / Development ─────────────────────────────────────
        reload: bool = False
        reload_dirs: list[str] | None = None  # directories to watch
        reload_delay: float = 0.25  # seconds between checks
        reload_includes: list[str] | None = None  # glob patterns to include
        reload_excludes: list[str] | None = None  # glob patterns to exclude

        # ── Protocol / Implementation ────────────────────────────────
        http: str = "auto"  # "auto" | "h11" | "httptools"
        ws: str = "auto"  # "auto" | "wsproto" | "websockets" | "none"
        lifespan: str = "auto"  # "auto" | "on" | "off"
        interface: str = "auto"  # "auto" | "asgi3" | "asgi2" | "wsgi"
        loop: str = "auto"  # "auto" | "asyncio" | "uvloop"

        # ── Timeouts ─────────────────────────────────────────────────
        timeout_keep_alive: int = 5  # seconds
        timeout_worker_healthcheck: int = 30  # seconds before worker considered unresponsive
        timeout_graceful_shutdown: int | None = None  # seconds (None = wait forever)

        # ── Limits ───────────────────────────────────────────────────
        backlog: int = 2048
        limit_concurrency: int | None = None  # max concurrent connections
        limit_max_requests: int | None = None  # restart worker after N requests

        # ── Proxy / Headers ──────────────────────────────────────────
        proxy_headers: bool = True
        forwarded_allow_ips: str | None = None  # comma-separated or "*"
        server_header: bool = True
        date_header: bool = True
        root_path: str = ""  # ASGI root_path (reverse proxy)

        # ── Logging ──────────────────────────────────────────────────
        access_log: bool = True
        log_level: str | None = None  # "critical"|"error"|"warning"|"info"|"debug"|"trace"
        use_colors: bool | None = None  # None = auto-detect

        # ── WebSocket ────────────────────────────────────────────────
        ws_max_size: int = 16_777_216  # 16 MiB
        ws_max_queue: int = 32
        ws_ping_interval: float | None = 20.0  # seconds (None = disabled)
        ws_ping_timeout: float | None = 20.0  # seconds (None = disabled)
        ws_per_message_deflate: bool = True

        # ── TLS / SSL ────────────────────────────────────────────────
        ssl_keyfile: str | None = None
        ssl_certfile: str | None = None
        ssl_keyfile_password: str | None = None
        ssl_ca_certs: str | None = None
        ssl_ciphers: str = "TLSv1"

        # ── HTTP/1.1 ─────────────────────────────────────────────────
        h11_max_incomplete_event_size: int | None = None  # bytes; None = h11 default (16 KiB)

    class PasswordHasher:
        """
        Password hashing algorithm configuration.

        Maps to ``auth.password_hasher``.

        Example::

            class auth(AquilaConfig.Auth):
                password_hasher = AquilaConfig.PasswordHasher(
                    algorithm="argon2id",
                    time_cost=3,
                    memory_cost=131072,   # 128 MiB
                )
        """

        # Make it instantiable so it can be used as a field value
        def __init__(
            self,
            algorithm: str = "argon2id",
            *,
            time_cost: int = 2,
            memory_cost: int = 65536,
            parallelism: int = 4,
            hash_len: int = 32,
            salt_len: int = 16,
            scrypt_n: int = 32768,
            scrypt_r: int = 8,
            scrypt_p: int = 1,
            scrypt_dklen: int = 32,
            bcrypt_rounds: int = 12,
            pbkdf2_iterations: int = 600000,
            pbkdf2_sha512_iterations: int = 210000,
            pbkdf2_dklen: int = 32,
        ):
            self.algorithm = algorithm
            self.time_cost = time_cost
            self.memory_cost = memory_cost
            self.parallelism = parallelism
            self.hash_len = hash_len
            self.salt_len = salt_len
            self.scrypt_n = scrypt_n
            self.scrypt_r = scrypt_r
            self.scrypt_p = scrypt_p
            self.scrypt_dklen = scrypt_dklen
            self.bcrypt_rounds = bcrypt_rounds
            self.pbkdf2_iterations = pbkdf2_iterations
            self.pbkdf2_sha512_iterations = pbkdf2_sha512_iterations
            self.pbkdf2_dklen = pbkdf2_dklen

        def to_dict(self) -> dict[str, Any]:
            return {
                "algorithm": self.algorithm,
                "time_cost": self.time_cost,
                "memory_cost": self.memory_cost,
                "parallelism": self.parallelism,
                "hash_len": self.hash_len,
                "salt_len": self.salt_len,
                "scrypt_n": self.scrypt_n,
                "scrypt_r": self.scrypt_r,
                "scrypt_p": self.scrypt_p,
                "scrypt_dklen": self.scrypt_dklen,
                "bcrypt_rounds": self.bcrypt_rounds,
                "pbkdf2_iterations": self.pbkdf2_iterations,
                "pbkdf2_sha512_iterations": self.pbkdf2_sha512_iterations,
                "pbkdf2_dklen": self.pbkdf2_dklen,
            }

        def build_hasher(self):
            """Instantiate and return a configured PasswordHasher."""
            from aquilia.auth.hashing import HasherConfig as _HC
            from aquilia.auth.hashing import PasswordHasher as _PH

            return _PH.from_config(_HC.from_dict(self.to_dict()))

        @classmethod
        def argon2id(
            cls, *, time_cost: int = 2, memory_cost: int = 65536, parallelism: int = 4
        ) -> AquilaConfig.PasswordHasher:
            """Argon2id with custom parameters."""
            return cls("argon2id", time_cost=time_cost, memory_cost=memory_cost, parallelism=parallelism)

        @classmethod
        def scrypt(cls, *, n: int = 32768, r: int = 8, p: int = 1, dklen: int = 32) -> AquilaConfig.PasswordHasher:
            """scrypt with custom parameters."""
            return cls("scrypt", scrypt_n=n, scrypt_r=r, scrypt_p=p, scrypt_dklen=dklen)

        @classmethod
        def bcrypt(cls, *, rounds: int = 12) -> AquilaConfig.PasswordHasher:
            """bcrypt with custom cost factor."""
            return cls("bcrypt", bcrypt_rounds=rounds)

        @classmethod
        def pbkdf2_sha512(cls, *, iterations: int = 210000) -> AquilaConfig.PasswordHasher:
            """PBKDF2-HMAC-SHA-512."""
            return cls("pbkdf2_sha512", pbkdf2_sha512_iterations=iterations)

        @classmethod
        def pbkdf2_sha256(cls, *, iterations: int = 600000) -> AquilaConfig.PasswordHasher:
            """PBKDF2-HMAC-SHA-256 (legacy fallback)."""
            return cls("pbkdf2_sha256", pbkdf2_iterations=iterations)

        def __repr__(self) -> str:
            return f"PasswordHasher(algorithm={self.algorithm!r})"

    class Auth:
        """
        Authentication & JWT configuration.

        Maps to the ``auth`` config path.

        **Algorithm selection:**

        Zero-dependency algorithms (stdlib ``hmac`` + ``hashlib``):
          * ``"HS256"`` — HMAC-SHA-256  ← **default, no extra packages**
          * ``"HS384"`` — HMAC-SHA-384
          * ``"HS512"`` — HMAC-SHA-512

        Asymmetric algorithms (requires ``pip install cryptography``):
          * ``"RS256"`` — RSA 3072-bit + SHA-256
          * ``"ES256"`` — ECDSA P-256  + SHA-256
          * ``"EdDSA"`` — Ed25519

        Example::

            class auth(AquilaConfig.Auth):
                # Use HS512 (stdlib, no deps):
                algorithm = "HS512"

                # Use RS256 (requires: pip install cryptography):
                # algorithm = "RS256"
        """

        enabled: bool = True
        store_type: str = "memory"
        secret_key: str | None = None
        algorithm: str = "HS256"
        issuer: str = "aquilia"
        audience: str = "aquilia-app"
        access_token_ttl_minutes: int = 60
        refresh_token_ttl_days: int = 30
        require_auth_by_default: bool = False
        #: Password hasher — override with an ``AquilaConfig.PasswordHasher`` instance.
        password_hasher: AquilaConfig.PasswordHasher | None = None

    class Apps:
        """
        Per-module app-specific settings.

        Subclass and add nested classes named after your modules::

            class apps(AquilaConfig.Apps):
                class auth:
                    max_login_attempts = 5
                    token_expiry       = 3600

                class users:
                    cache_ttl = 300
        """

    class Database:
        """Database connection configuration."""

        url: str = "sqlite:///db.sqlite3"
        auto_connect: bool = True
        auto_create: bool = True
        auto_migrate: bool = False
        pool_size: int = 5
        echo: bool = False
        migrations_dir: str = "migrations"

    class Cache:
        """Cache backend configuration."""

        backend: str = "memory"
        default_ttl: int = 300
        max_size: int = 10000
        eviction_policy: str = "lru"
        namespace: str = "default"
        key_prefix: str = "aq:"
        redis_url: str = "redis://localhost:6379/0"

    class Sessions:
        """Session store and transport configuration."""

        enabled: bool = False
        store_type: str = "memory"  # "memory" | "file" | "redis"
        cookie_name: str = "aquilia_session"
        cookie_secure: bool = True
        cookie_httponly: bool = True
        cookie_samesite: str = "lax"
        ttl_days: int = 7
        idle_timeout_minutes: int = 30

    class Mail:
        """Mail provider configuration."""

        enabled: bool = False
        default_from: str = "noreply@localhost"
        console_backend: bool = False
        require_tls: bool = True
        retry_max_attempts: int = 5

    class Security:
        """Security middleware flags."""

        enabled: bool = False
        cors_enabled: bool = False
        csrf_protection: bool = False
        helmet_enabled: bool = False
        rate_limiting: bool = False
        https_redirect: bool = False
        hsts: bool = False

    class Logging:
        """Request logging configuration."""

        level: str = "INFO"
        colorize: bool = True
        slow_threshold_ms: float = 1000.0
        include_headers: bool = False

    class I18n:
        """Internationalisation configuration."""

        enabled: bool = False
        default_locale: str = "en"
        available_locales: list[str] = field(default_factory=lambda: ["en"])  # type: ignore[misc]
        fallback_locale: str = "en"
        catalog_dirs: list[str] = field(default_factory=lambda: ["locales"])  # type: ignore[misc]
        catalog_format: str = "json"

    class Signing:
        """
        Cryptographic signing engine configuration (``aquilia.signing``).

        Controls the :mod:`aquilia.signing` module that backs session
        cookies, CSRF tokens, one-time activation links, cache integrity
        checks, and any other value that must be tamper-proof without a
        database round-trip.

        **Quick-start** — override in your config::

            class signing(AquilaConfig.Signing):
                secret = Secret(env="AQ_SECRET_KEY", required=True)

        **Algorithm selection (all zero-dependency, stdlib only):**

        * ``"HS256"`` — HMAC-SHA-256 ← **default**
        * ``"HS384"`` — HMAC-SHA-384
        * ``"HS512"`` — HMAC-SHA-512

        **Key rotation** — list retired secrets in ``fallback_secrets``::

            class signing(AquilaConfig.Signing):
                secret           = Secret(env="AQ_NEW_KEY", required=True)
                fallback_secrets = [Secret(env="AQ_OLD_KEY")]

        Old tokens signed with the old key continue to work until
        ``fallback_secrets`` is cleared (after the TTL of your tokens
        has elapsed).

        **Namespace salts** — each subsystem uses an isolated salt so
        cross-subsystem token reuse is cryptographically impossible::

            Salt "aquilia.sessions"    → session cookies
            Salt "aquilia.csrf"        → CSRF tokens
            Salt "aquilia.activation"  → activation / password-reset links
            Salt "aquilia.cache"       → cache integrity (signed pickle)
            Salt "aquilia.cookies"     → generic signed cookies
            Salt "aquilia.apikeys"     → short-lived signed API keys
        """

        #: Primary signing secret.  **Must** be set in production.
        #: Use ``Secret(env="AQ_SECRET_KEY", required=True)`` in real apps.
        secret: str | None = None

        #: Retired secrets kept for backward-compatible verification
        #: (key rotation).  Tokens signed with these can still be read;
        #: new tokens always use ``secret``.
        fallback_secrets: list[str] = []  # type: ignore[assignment]

        #: Default HMAC algorithm.  One of ``"HS256"`` / ``"HS384"`` / ``"HS512"``.
        algorithm: str = "HS256"

        #: Default namespace salt (used by the plain :class:`~aquilia.signing.Signer`).
        salt: str = "aquilia.signing"

        # ── Per-subsystem salts — override to isolate subsystems further ──
        session_salt: str = "aquilia.sessions"
        csrf_salt: str = "aquilia.csrf"
        activation_salt: str = "aquilia.activation"
        cache_salt: str = "aquilia.cache"

    class Render:
        """
        Render PaaS deployment configuration.

        Controls how ``aq deploy render`` deploys the workspace to the
        Render cloud platform.  All attributes can use ``Env()``
        bindings for twelve-factor compatibility.

        **Regions** (datacenter location):
          * ``"oregon"``     — Oregon (US West) ← **default**
          * ``"frankfurt"``  — Frankfurt (EU)
          * ``"ohio"``       — Ohio (US East)
          * ``"virginia"``   — Virginia (US East)
          * ``"singapore"``  — Singapore (Asia)

        **Plans** (compute size):
          * ``"free"``      — shared CPU, 512 MiB RAM (hobby)
          * ``"starter"``   — 0.5 CPU, 512 MiB RAM ← **default**
          * ``"standard"``  — 1 CPU, 2 GiB RAM
          * ``"pro"``       — 2 CPU, 4 GiB RAM
          * ``"pro_plus"``  — 4 CPU, 8 GiB RAM
          * ``"pro_max"``   — 8 CPU, 16 GiB RAM
          * ``"pro_ultra"`` — 16 CPU, 32 GiB RAM

        Example::

            class render(AquilaConfig.Render):
                service_name  = "my-api"
                region        = "frankfurt"
                plan          = "standard"
                num_instances = 2
                image         = Env("RENDER_IMAGE", default="ghcr.io/org/app:latest")
                health_path   = "/_health"

            # High-performance
            class render(AquilaConfig.Render):
                plan          = "pro_plus"
                num_instances = 4
        """

        #: Enable/disable Render deployment integration.
        enabled: bool = True

        #: Render service name (defaults to workspace name at deploy time).
        service_name: str | None = None

        #: Deployment region.
        region: str = "oregon"

        #: Render compute plan.
        plan: str = "starter"

        #: Number of running instances.
        num_instances: int = 1

        #: Docker image reference (``registry/name:tag``).
        #: If ``None``, ``aq deploy render`` builds from the workspace Dockerfile.
        image: str | None = None

        #: Health-check endpoint path.
        health_path: str = "/_health"

        #: Auto-deploy on image push (``"yes"`` or ``"no"``).
        auto_deploy: str = "no"

        #: Internal service port (the port your ASGI server listens on).
        port: int = 8000

    # ── Class-level helpers ───────────────────────────────────────────────

    @classmethod
    def to_dict(cls, *, use_cache: bool = True) -> dict[str, Any]:
        """
        Serialise this config class into a plain nested dict.

        All ``Env`` bindings are resolved, ``Secret`` values are revealed,
        and nested section classes are recursed.  The resulting dict is
        compatible with :class:`~aquilia.config.ConfigLoader`.

        Caching
        -------
        When ``use_cache=True`` (default), the resolved dict is cached at
        the class level. Subsequent calls return a copy of the cached result,
        avoiding re-resolution of all ``Env`` bindings.

        Use :meth:`invalidate_cache` to clear the cache when you need to
        re-resolve values (e.g., after environment changes in tests).

        Dotenv Integration
        ------------------
        When this method is called, the native dotenv loader is automatically
        triggered to ensure ``.env`` files are loaded before resolving any
        ``Env`` bindings. You do NOT need to call ``load_dotenv()`` manually.

        Args:
            use_cache: If True (default), use cached results if available
                       and cache new results for future calls.

        Returns:
            Nested configuration dictionary.
        """
        # Ensure dotenv is loaded up front
        _ensure_dotenv_loaded(config_cls=cls)

        # Check class-level cache first
        if use_cache:
            with _config_cache_lock:
                if cls in _config_class_cache:
                    return _config_class_cache[cls].copy()

        result: dict[str, Any] = {}

        for name in dir(cls):
            if name.startswith("_"):
                continue
            if name == "dotenv":
                continue
            val = getattr(cls, name, None)
            if val is None:
                continue
            if callable(val) and not isinstance(val, type):
                # Skip methods, classmethods, staticmethods
                if not isinstance(inspect.getattr_static(cls, name), (classmethod, staticmethod)):
                    continue
            if isinstance(val, type) and issubclass(val, object):
                # Nested class — check if it looks like a config section
                if val.__module__ != cls.__module__ and not getattr(val, "_is_aquila_section", False):
                    # Skip imported types from other modules that are not sections
                    continue
                result[name] = _class_to_dict(val, use_cache=use_cache)
            elif isinstance(val, Env):
                result[name] = val.resolve(use_cache=use_cache)
            elif isinstance(val, Secret):
                result[name] = val.reveal()
            elif hasattr(val, "to_dict") and callable(val.to_dict):
                result[name] = val.to_dict()
            elif isinstance(val, (str, int, float, bool, list, dict)):
                result[name] = val

        # Cache the result
        if use_cache:
            with _config_cache_lock:
                _config_class_cache[cls] = result.copy()

        return result

    @classmethod
    def invalidate_cache(cls) -> None:
        """
        Invalidate the cached config dict for this class.

        Call this after environment variables change to ensure the next
        ``to_dict()`` or ``get()`` call re-resolves all values.

        Example::

            os.environ["MY_VAR"] = "new_value"
            MyConfig.invalidate_cache()
            print(MyConfig.get("my_var"))  # Uses new value
        """
        with _config_cache_lock:
            _config_class_cache.pop(cls, None)

    @classmethod
    def clear_all_caches(cls) -> None:
        """
        Clear all config class caches.

        Use this in test teardown to reset state between tests.
        """
        with _config_cache_lock:
            _config_class_cache.clear()
        # Also reset dotenv state
        reset_dotenv_state()

    @classmethod
    def to_loader(cls) -> ConfigLoader:
        """
        Convert this Python config into a :class:`~aquilia.config.ConfigLoader`.

        This is the bridge between the Python-native DSL and all the
        existing subsystem config methods (``get_auth_config``,
        ``get_session_config``, etc.)::

            loader = MyDevConfig.to_loader()
            auth   = loader.get_auth_config()
            hasher = loader.build_password_hasher()

        Returns:
            A populated :class:`~aquilia.config.ConfigLoader` instance.
        """
        from aquilia.config import ConfigLoader

        data = cls.to_dict()
        loader = ConfigLoader()

        # Normalise: promote ``server`` → ``runtime`` so ConfigLoader is happy
        if "server" in data and "runtime" not in data:
            data["runtime"] = data.pop("server")
        elif "server" in data and "runtime" in data:
            # Merge server into runtime (server keys override runtime)
            data["runtime"].update(data.pop("server"))

        # Normalise: promote ``auth`` and ``password_hasher`` into expected paths
        if "auth" in data:
            # Ensure password_hasher is nested under auth
            auth_data = data["auth"]
            if "password_hasher" not in auth_data:
                ph_instance = getattr(cls, "auth", None)
                if ph_instance is not None:
                    ph_val = getattr(ph_instance, "password_hasher", None)
                    if ph_val is not None and hasattr(ph_val, "to_dict"):
                        auth_data["password_hasher"] = ph_val.to_dict()

        loader._merge_dict(loader.config_data, data)
        loader._load_from_env()
        loader._build_apps_namespace()
        return loader

    @classmethod
    def get(cls, path: str, default: Any = None) -> Any:
        """Dot-path accessor on the serialised config dict."""
        data = cls.to_dict()
        parts = path.split(".")
        current = data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        return current

    @classmethod
    def for_env(cls, env_name: str) -> type[AquilaConfig]:
        """
        Resolve the correct subclass for *env_name* from the subclass tree.

        Scans all direct subclasses and returns the first whose ``env``
        attribute equals *env_name* (case-insensitive).

        Example::

            Config = AquilaConfig.for_env("prod")
            loader = Config.to_loader()

        Raises:
            ``ValueError`` if no matching subclass is found.
        """
        for subcls in cls.__subclasses__():
            if getattr(subcls, "env", "").lower() == env_name.lower():
                return subcls
            # Recurse one more level
            for subsub in subcls.__subclasses__():
                if getattr(subsub, "env", "").lower() == env_name.lower():
                    return subsub
        from aquilia.faults.domains import ConfigMissingFault

        raise ConfigMissingFault(
            key=f"AquilaConfig.env={env_name}",
            metadata={
                "hint": f"No AquilaConfig subclass with env={env_name!r} found. "
                f"Available: {[getattr(s, 'env', '?') for s in cls.__subclasses__()]}",
            },
        )

    @classmethod
    def from_env_var(
        cls,
        var: str = "AQ_ENV",
        default: str = "dev",
    ) -> type[AquilaConfig]:
        """
        Read ``var`` from the environment and return the matching subclass.

        Perfect for a 12-factor app entrypoint::

            from config.settings import BaseConfig

            Config = BaseConfig.from_env_var("APP_ENV", default="dev")
            loader = Config.to_loader()

        Returns self (not a subclass) if no subclass matches.
        """
        env_name = os.environ.get(var, default)
        try:
            return cls.for_env(env_name)
        except ValueError:
            log.warning(
                "No AquilaConfig subclass for env=%r; using %s.",
                env_name,
                cls.__name__,
            )
            return cls

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        # Legacy compatibility: map deprecated filename dunder attributes.
        legacy_single = cls.__dict__.get("__filename__")
        legacy_many = cls.__dict__.get("__filenames__")
        if legacy_single is not None or legacy_many is not None:
            warnings.warn(
                "AquilaConfig.__filename__ / __filenames__ are deprecated; "
                "define class dotenv(AquilaConfig.Dotenv): files=[...] instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            if "dotenv" not in cls.__dict__:
                legacy_files: list[Any] = []
                if legacy_single is not None:
                    legacy_files.append(legacy_single)
                if legacy_many is not None:
                    if isinstance(legacy_many, (list, tuple)):
                        legacy_files.extend(legacy_many)
                    else:
                        legacy_files.append(legacy_many)
                legacy_dotenv = type(
                    "dotenv",
                    (getattr(cls, "Dotenv", object),),
                    {
                        "files": legacy_files,
                        "_is_aquila_section": True,
                    },
                )
                cls.dotenv = legacy_dotenv  # type: ignore[attr-defined]

        # Inherit parent's nested section classes if the subclass doesn't define its own.
        parent_sections = [
            name
            for name, val in inspect.getmembers(cls.__bases__[0])
            if isinstance(val, type) and not name.startswith("_")
        ]
        for section_name in parent_sections:
            if not hasattr(cls, section_name):
                # Inherit silently
                setattr(cls, section_name, getattr(cls.__bases__[0], section_name))

    def __repr__(self) -> str:
        return f"<AquilaConfig env={getattr(self, 'env', '?')!r}>"


# ============================================================================
# PyConfigLoader — standalone loader that reads a Python config file
# ============================================================================


class PyConfigLoader:
    """
    Load an ``AquilaConfig`` subclass from a Python source file.

    This is the plug-in replacement for ``ConfigLoader._load_yaml_file``.
    It is used by :class:`~aquilia.config.ConfigLoader` when a ``*.py``
    config path is provided.

    Usage::

        from aquilia.pyconfig import PyConfigLoader
        loader = PyConfigLoader.from_file("config/settings.py", env="prod")
        aq_loader = loader.to_aquilia_loader()
    """

    def __init__(self, config_class: type[AquilaConfig]):
        self._cls = config_class

    @classmethod
    def from_file(
        cls,
        path: str | Path,
        *,
        env: str | None = None,
        var: str = "AQ_ENV",
        default_env: str = "dev",
    ) -> PyConfigLoader:
        """
        Import a Python config file and resolve the right subclass.

        Args:
            path:        Path to the Python settings file.
            env:         Environment name to load (overrides env-var).
            var:         Name of the environment variable that picks the env.
            default_env: Default environment if neither *env* nor *var* is set.

        Returns:
            :class:`PyConfigLoader` wrapping the resolved subclass.
        """
        import importlib.util

        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        spec = importlib.util.spec_from_file_location("_aquilia_pyconfig", path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load config from {path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]

        # Find the first AquilaConfig subclass exported at module level
        base_cls: type[AquilaConfig] | None = None
        for name in dir(module):
            obj = getattr(module, name)
            if (
                isinstance(obj, type)
                and issubclass(obj, AquilaConfig)
                and obj is not AquilaConfig
                and not name.startswith("_")
            ):
                base_cls = obj
                break

        if base_cls is None:
            raise ImportError(
                f"No AquilaConfig subclass found in {path}. Define at least one class inheriting from AquilaConfig."
            )

        # Resolve the right environment variant
        env_name = env or os.environ.get(var, default_env)
        try:
            resolved = base_cls.for_env(str(env_name))
        except ValueError:
            resolved = base_cls

        return cls(resolved)

    def to_aquilia_loader(self):
        """Return a fully populated :class:`~aquilia.config.ConfigLoader`."""
        return self._cls.to_loader()

    @property
    def config_class(self) -> type[AquilaConfig]:
        """The resolved :class:`AquilaConfig` subclass."""
        return self._cls


# ============================================================================
# Public exports
# ============================================================================

__all__ = [
    # Core classes
    "AquilaConfig",
    "PyConfigLoader",
    "Secret",
    "Env",
    "section",
    # Dotenv control functions
    "reset_dotenv_state",
    # Type aliases (from top of module)
    "ConfigValue",
    "EnvCaster",
    "EnvCastType",
]
