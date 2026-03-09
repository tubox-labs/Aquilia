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

import os
import json
import logging
import inspect
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, List, ClassVar, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from aquilia.config import ConfigLoader

log = logging.getLogger(__name__)


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

    Examples::

        secret_key = Secret(env="AQ_SECRET_KEY", required=True)
        db_password = Secret(env="DB_PASSWORD", default="devpassword")
        api_key     = Secret(value="sk-live-abc123")  # inline (dev only!)
    """

    _REDACTED = "<secret>"

    def __init__(
        self,
        value: Optional[str] = None,
        *,
        env: Optional[str] = None,
        default: Optional[str] = None,
        required: bool = False,
    ):
        self._literal = value
        self._env_name = env
        self._default = default
        self._required = required

    def reveal(self) -> Optional[str]:
        """Return the actual secret value (use deliberately)."""
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

    def __repr__(self) -> str:
        env_hint = f"env={self._env_name!r}" if self._env_name else ""
        return f"Secret({env_hint or 'inline'}, {'*required*' if self._required else 'optional'})"

    def __str__(self) -> str:
        return self._REDACTED


# ============================================================================
# Env binding — transparently reads from environment variables
# ============================================================================

class Env:
    """
    Bind a configuration field to an environment variable.

    Resolves at read time so runtime changes to the environment are
    reflected immediately (useful in test setups).

    Examples::

        debug   = Env("AQ_DEBUG",   default=False,  cast=bool)
        workers = Env("AQ_WORKERS", default=4,       cast=int)
        host    = Env("AQ_HOST",    default="127.0.0.1")
    """

    _CAST_TRUE  = {"1", "true", "yes", "on"}
    _CAST_FALSE = {"0", "false", "no", "off"}

    def __init__(
        self,
        name: str,
        *,
        default: Any = None,
        cast: Optional[type] = None,
    ):
        self._name    = name
        self._default = default
        self._cast    = cast

    def resolve(self) -> Any:
        """Return the resolved value from the environment or default."""
        raw = os.environ.get(self._name)
        if raw is None:
            return self._default
        if self._cast is bool:
            if raw.lower() in self._CAST_TRUE:
                return True
            if raw.lower() in self._CAST_FALSE:
                return False
            return bool(raw)
        if self._cast is not None:
            return self._cast(raw)
        # Auto-cast: try int → float → json → str
        try:
            return int(raw)
        except ValueError:
            pass
        try:
            return float(raw)
        except ValueError:
            pass
        if raw.startswith(("{", "[")):
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                pass
        return raw

    def __repr__(self) -> str:
        return f"Env({self._name!r}, default={self._default!r})"


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

def _resolve_value(val: Any) -> Any:
    """Unwrap ``Env`` and ``Secret`` wrappers to their runtime values."""
    if isinstance(val, Env):
        return val.resolve()
    if isinstance(val, Secret):
        return val.reveal()
    return val


def _class_to_dict(cls: type) -> Dict[str, Any]:
    """
    Recursively convert a (nested) config class into a plain dict.

    Rules:
    - Dunder and private attributes are skipped.
    - Nested classes whose name does not start with ``_`` are recursed.
    - ``Env`` instances are resolved to their runtime value.
    - ``Secret`` instances are revealed (callers decide when to call this).
    - Callable attributes (methods) are skipped.
    - Dataclass/plain-class instances with a ``to_dict`` method are called.
    """
    result: Dict[str, Any] = {}
    for name, val in inspect.getmembers(cls):
        if name.startswith("_"):
            continue
        if callable(val) and not isinstance(val, (type, Env, Secret)):
            continue
        if isinstance(val, type):
            # Nested config class → recurse
            result[name] = _class_to_dict(val)
        elif isinstance(val, Env):
            result[name] = val.resolve()
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
        host: str              = "127.0.0.1"
        port: int              = 8000
        uds: "Optional[str]"   = None        # Unix domain socket path
        fd: "Optional[int]"    = None        # File descriptor to bind
        workers: int           = 1
        mode: str              = "dev"
        debug: bool            = False

        # ── Reload / Development ─────────────────────────────────────
        reload: bool                         = False
        reload_dirs: "Optional[List[str]]"   = None   # directories to watch
        reload_delay: float                  = 0.25   # seconds between checks
        reload_includes: "Optional[List[str]]" = None # glob patterns to include
        reload_excludes: "Optional[List[str]]" = None # glob patterns to exclude

        # ── Protocol / Implementation ────────────────────────────────
        http: str              = "auto"      # "auto" | "h11" | "httptools"
        ws: str                = "auto"      # "auto" | "wsproto" | "websockets" | "none"
        lifespan: str          = "auto"      # "auto" | "on" | "off"
        interface: str         = "auto"      # "auto" | "asgi3" | "asgi2" | "wsgi"
        loop: str              = "auto"      # "auto" | "asyncio" | "uvloop"

        # ── Timeouts ─────────────────────────────────────────────────
        timeout_keep_alive: int              = 5       # seconds
        timeout_worker_healthcheck: int      = 30      # seconds before worker considered unresponsive
        timeout_graceful_shutdown: "Optional[int]" = None  # seconds (None = wait forever)

        # ── Limits ───────────────────────────────────────────────────
        backlog: int                         = 2048
        limit_concurrency: "Optional[int]"   = None    # max concurrent connections
        limit_max_requests: "Optional[int]"  = None    # restart worker after N requests

        # ── Proxy / Headers ──────────────────────────────────────────
        proxy_headers: bool                  = True
        forwarded_allow_ips: "Optional[str]" = None    # comma-separated or "*"
        server_header: bool                  = True
        date_header: bool                    = True
        root_path: str                       = ""      # ASGI root_path (reverse proxy)

        # ── Logging ──────────────────────────────────────────────────
        access_log: bool                     = True
        log_level: "Optional[str]"           = None    # "critical"|"error"|"warning"|"info"|"debug"|"trace"
        use_colors: "Optional[bool]"         = None    # None = auto-detect

        # ── WebSocket ────────────────────────────────────────────────
        ws_max_size: int                     = 16_777_216   # 16 MiB
        ws_max_queue: int                    = 32
        ws_ping_interval: "Optional[float]"  = 20.0         # seconds (None = disabled)
        ws_ping_timeout: "Optional[float]"   = 20.0         # seconds (None = disabled)
        ws_per_message_deflate: bool         = True

        # ── TLS / SSL ────────────────────────────────────────────────
        ssl_keyfile: "Optional[str]"         = None
        ssl_certfile: "Optional[str]"        = None
        ssl_keyfile_password: "Optional[str]" = None
        ssl_ca_certs: "Optional[str]"        = None
        ssl_ciphers: str                     = "TLSv1"

        # ── HTTP/1.1 ─────────────────────────────────────────────────
        h11_max_incomplete_event_size: "Optional[int]" = None  # bytes; None = h11 default (16 KiB)

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
            time_cost: int    = 2,
            memory_cost: int  = 65536,
            parallelism: int  = 4,
            hash_len: int     = 32,
            salt_len: int     = 16,
            scrypt_n: int     = 32768,
            scrypt_r: int     = 8,
            scrypt_p: int     = 1,
            scrypt_dklen: int = 32,
            bcrypt_rounds: int = 12,
            pbkdf2_iterations: int        = 600000,
            pbkdf2_sha512_iterations: int = 210000,
            pbkdf2_dklen: int             = 32,
        ):
            self.algorithm                = algorithm
            self.time_cost                = time_cost
            self.memory_cost              = memory_cost
            self.parallelism              = parallelism
            self.hash_len                 = hash_len
            self.salt_len                 = salt_len
            self.scrypt_n                 = scrypt_n
            self.scrypt_r                 = scrypt_r
            self.scrypt_p                 = scrypt_p
            self.scrypt_dklen             = scrypt_dklen
            self.bcrypt_rounds            = bcrypt_rounds
            self.pbkdf2_iterations        = pbkdf2_iterations
            self.pbkdf2_sha512_iterations = pbkdf2_sha512_iterations
            self.pbkdf2_dklen             = pbkdf2_dklen

        def to_dict(self) -> Dict[str, Any]:
            return {
                "algorithm":                self.algorithm,
                "time_cost":                self.time_cost,
                "memory_cost":              self.memory_cost,
                "parallelism":              self.parallelism,
                "hash_len":                 self.hash_len,
                "salt_len":                 self.salt_len,
                "scrypt_n":                 self.scrypt_n,
                "scrypt_r":                 self.scrypt_r,
                "scrypt_p":                 self.scrypt_p,
                "scrypt_dklen":             self.scrypt_dklen,
                "bcrypt_rounds":            self.bcrypt_rounds,
                "pbkdf2_iterations":        self.pbkdf2_iterations,
                "pbkdf2_sha512_iterations": self.pbkdf2_sha512_iterations,
                "pbkdf2_dklen":             self.pbkdf2_dklen,
            }

        def build_hasher(self):
            """Instantiate and return a configured PasswordHasher."""
            from aquilia.auth.hashing import PasswordHasher as _PH, HasherConfig as _HC
            return _PH.from_config(_HC.from_dict(self.to_dict()))

        @classmethod
        def argon2id(cls, *, time_cost: int = 2, memory_cost: int = 65536,
                     parallelism: int = 4) -> "AquilaConfig.PasswordHasher":
            """Argon2id with custom parameters."""
            return cls("argon2id", time_cost=time_cost,
                       memory_cost=memory_cost, parallelism=parallelism)

        @classmethod
        def scrypt(cls, *, n: int = 32768, r: int = 8, p: int = 1,
                   dklen: int = 32) -> "AquilaConfig.PasswordHasher":
            """scrypt with custom parameters."""
            return cls("scrypt", scrypt_n=n, scrypt_r=r, scrypt_p=p, scrypt_dklen=dklen)

        @classmethod
        def bcrypt(cls, *, rounds: int = 12) -> "AquilaConfig.PasswordHasher":
            """bcrypt with custom cost factor."""
            return cls("bcrypt", bcrypt_rounds=rounds)

        @classmethod
        def pbkdf2_sha512(cls, *, iterations: int = 210000) -> "AquilaConfig.PasswordHasher":
            """PBKDF2-HMAC-SHA-512."""
            return cls("pbkdf2_sha512", pbkdf2_sha512_iterations=iterations)

        @classmethod
        def pbkdf2_sha256(cls, *, iterations: int = 600000) -> "AquilaConfig.PasswordHasher":
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
        enabled: bool                        = True
        store_type: str                      = "memory"
        secret_key: "Optional[str]"          = None
        algorithm: str                       = "HS256"
        issuer: str                          = "aquilia"
        audience: str                        = "aquilia-app"
        access_token_ttl_minutes: int        = 60
        refresh_token_ttl_days: int          = 30
        require_auth_by_default: bool        = False
        #: Password hasher — override with an ``AquilaConfig.PasswordHasher`` instance.
        password_hasher: "Optional[AquilaConfig.PasswordHasher]" = None

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
        url: str              = "sqlite:///db.sqlite3"
        auto_connect: bool    = True
        auto_create: bool     = True
        auto_migrate: bool    = False
        pool_size: int        = 5
        echo: bool            = False
        migrations_dir: str   = "migrations"

    class Cache:
        """Cache backend configuration."""
        backend: str          = "memory"
        default_ttl: int      = 300
        max_size: int         = 10000
        eviction_policy: str  = "lru"
        namespace: str        = "default"
        key_prefix: str       = "aq:"
        redis_url: str        = "redis://localhost:6379/0"

    class Sessions:
        """Session store and transport configuration."""
        enabled: bool         = False
        store_type: str       = "memory"    # "memory" | "file" | "redis"
        cookie_name: str      = "aquilia_session"
        cookie_secure: bool   = True
        cookie_httponly: bool = True
        cookie_samesite: str  = "lax"
        ttl_days: int         = 7
        idle_timeout_minutes: int = 30

    class Mail:
        """Mail provider configuration."""
        enabled: bool               = False
        default_from: str           = "noreply@localhost"
        console_backend: bool       = False
        require_tls: bool           = True
        retry_max_attempts: int     = 5

    class Security:
        """Security middleware flags."""
        enabled: bool           = False
        cors_enabled: bool      = False
        csrf_protection: bool   = False
        helmet_enabled: bool    = False
        rate_limiting: bool     = False
        https_redirect: bool    = False
        hsts: bool              = False

    class Logging:
        """Request logging configuration."""
        level: str              = "INFO"
        colorize: bool          = True
        slow_threshold_ms: float = 1000.0
        include_headers: bool   = False

    class I18n:
        """Internationalisation configuration."""
        enabled: bool           = False
        default_locale: str     = "en"
        available_locales: "List[str]" = field(default_factory=lambda: ["en"])  # type: ignore[misc]
        fallback_locale: str    = "en"
        catalog_dirs: "List[str]" = field(default_factory=lambda: ["locales"])  # type: ignore[misc]
        catalog_format: str     = "json"

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
        secret: "Optional[str]"                   = None

        #: Retired secrets kept for backward-compatible verification
        #: (key rotation).  Tokens signed with these can still be read;
        #: new tokens always use ``secret``.
        fallback_secrets: "List[str]"             = []   # type: ignore[assignment]

        #: Default HMAC algorithm.  One of ``"HS256"`` / ``"HS384"`` / ``"HS512"``.
        algorithm: str                            = "HS256"

        #: Default namespace salt (used by the plain :class:`~aquilia.signing.Signer`).
        salt: str                                 = "aquilia.signing"

        # ── Per-subsystem salts — override to isolate subsystems further ──
        session_salt: str    = "aquilia.sessions"
        csrf_salt: str       = "aquilia.csrf"
        activation_salt: str = "aquilia.activation"
        cache_salt: str      = "aquilia.cache"

    # ── Class-level helpers ───────────────────────────────────────────────

    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """
        Serialise this config class into a plain nested dict.

        All ``Env`` bindings are resolved, ``Secret`` values are revealed,
        and nested section classes are recursed.  The resulting dict is
        compatible with :class:`~aquilia.config.ConfigLoader`.

        Returns:
            Nested configuration dictionary.
        """
        result: Dict[str, Any] = {}

        for name in dir(cls):
            if name.startswith("_"):
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
                result[name] = _class_to_dict(val)
            elif isinstance(val, Env):
                result[name] = val.resolve()
            elif isinstance(val, Secret):
                result[name] = val.reveal()
            elif hasattr(val, "to_dict") and callable(val.to_dict):
                result[name] = val.to_dict()
            elif isinstance(val, (str, int, float, bool, list, dict)):
                result[name] = val

        return result

    @classmethod
    def to_loader(cls) -> "ConfigLoader":
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
                    if hasattr(ph_val, "to_dict"):
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
    def for_env(cls, env_name: str) -> "Type[AquilaConfig]":
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
    ) -> "Type[AquilaConfig]":
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
                env_name, cls.__name__,
            )
            return cls

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Inherit parent's nested section classes if the subclass doesn't define its own.
        parent_sections = [
            name for name, val in inspect.getmembers(cls.__bases__[0])
            if isinstance(val, type) and not name.startswith("_")
        ]
        for section_name in parent_sections:
            if not hasattr(cls, section_name):
                # Inherit silently
                setattr(cls, section_name, getattr(cls.__bases__[0], section_name))

    def __repr__(cls) -> str:
        return f"<AquilaConfig env={getattr(cls, 'env', '?')!r}>"


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

    def __init__(self, config_class: Type[AquilaConfig]):
        self._cls = config_class

    @classmethod
    def from_file(
        cls,
        path: "str | Path",
        *,
        env: Optional[str] = None,
        var: str = "AQ_ENV",
        default_env: str = "dev",
    ) -> "PyConfigLoader":
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
        base_cls: Optional[Type[AquilaConfig]] = None
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
                f"No AquilaConfig subclass found in {path}. "
                "Define at least one class inheriting from AquilaConfig."
            )

        # Resolve the right environment variant
        env_name = env or os.environ.get(var, default_env)
        try:
            resolved = base_cls.for_env(env_name)
        except ValueError:
            resolved = base_cls

        return cls(resolved)

    def to_aquilia_loader(self):
        """Return a fully populated :class:`~aquilia.config.ConfigLoader`."""
        return self._cls.to_loader()

    @property
    def config_class(self) -> Type[AquilaConfig]:
        """The resolved :class:`AquilaConfig` subclass."""
        return self._cls


# ============================================================================
# Public exports
# ============================================================================

__all__ = [
    "AquilaConfig",
    "PyConfigLoader",
    "Secret",
    "Env",
    "section",
]
