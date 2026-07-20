"""
Config system - Layered typed configuration with validation.
Supports dataclass/pydantic-like behavior with merge precedence.
"""

import json
import logging
import os
from dataclasses import MISSING, fields, is_dataclass
from pathlib import Path
from typing import Any, get_args, get_origin, get_type_hints

from aquilia.faults.domains import ConfigFault, ConfigInvalidFault

log = logging.getLogger(__name__)


class NestedNamespace:
    """
    A namespace supporting nested attribute access for application configurations.

    Allows accessing nested configuration dictionary keys as properties rather than
    bracket lookups (e.g. `config.apps.auth.secret_key` instead of `config["apps"]["auth"]["secret_key"]`).

    Parameters:
        data: Optional base dictionary containing configuration settings. Defaults to `None`.

    Examples:
        ```python
        data = {"apps": {"auth": {"secret": "abc"}}}
        ns = NestedNamespace(data)
        print(ns.apps.auth.secret)  # Outputs: abc
        ```
    """

    def __init__(self, data: dict[str, Any] | None = None):
        self._data = data or {}

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            return object.__getattribute__(self, name)

        if name not in self._data:
            raise AttributeError(f"'NestedNamespace' object has no attribute '{name}'")

        value = self._data.get(name)
        if isinstance(value, dict):
            return NestedNamespace(value)
        return value

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def to_dict(self) -> dict:
        """Return the underlying data dictionary."""
        return self._data

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)


class Config:
    """
    Base class for typed configuration structures.

    Subclassed by specific application integration dataclasses or schemas to mark them
    as configuration objects compatible with validation and instantiation logic.
    """

    pass


class ConfigError(ConfigFault):
    """
    Exception raised when configuration validation or type-checking fails.

    Extends `ConfigFault` with structured error code `"CONFIG_VALIDATION_ERROR"`.

    Parameters:
        message: Descriptive error message explaining the failure.
        **kwargs: Extensible extra metadata.
    """

    def __init__(self, message: str, **kwargs):
        super().__init__(
            code="CONFIG_VALIDATION_ERROR",
            message=message,
            **kwargs,
        )


class ConfigLoader:
    """
    Centralized loader and resolver for application configurations.

    Responsible for merging configurations from multiple sources with defined precedence,
    normalizing keys, and instantiating strongly-typed config classes.

    Precedence order (highest overrides lowest):
    1. Manual overrides (passed to `.load()`)
    2. Environment variables (`AQ_*` prefix)
    3. Dotenv files (`.env`)
    4. Python configuration files (`workspace.py` or `aquilia.py`)
    5. Subsystem defaults

    Examples:
        ```python
        from aquilia.config import ConfigLoader

        loader = ConfigLoader.load(
            paths=["workspace.py"],
            overrides={"runtime": {"port": 9000}}
        )
        port = loader.get("runtime.port")
        ```
    """

    def __init__(self, env_prefix: str = "AQ_"):
        self.env_prefix = env_prefix
        self.config_data: dict[str, Any] = {}
        self.apps = NestedNamespace()  # Add apps namespace

    @classmethod
    def load(
        cls,
        paths: list[str] | None = None,
        env_prefix: str = "AQ_",
        env_file: str | None = None,
        overrides: dict[str, Any] | None = None,
    ) -> "ConfigLoader":
        """
        Load configuration from multiple sources with defined merge precedence.

        Precedence order (later overrides earlier):
        1. Workspace configuration from Python files (e.g. `workspace.py`, `aquilia.py`).
        2. Legacy `config/env.py` variant selection if present.
        3. Environment variables matching `env_prefix` (e.g., `AQ_*`).
        4. Manual overrides dictionary (highest priority).

        All configuration in Aquilia is Python-native. YAML files are unsupported.

        Parameters:
            paths: List of configuration file paths or glob patterns to load. Defaults to `["workspace.py"]` or `["aquilia.py"]`.
            env_prefix: Environment variable prefix used to match environment configuration keys. Defaults to `"AQ_"`.
            env_file: Path to a `.env` file containing environment settings.
            overrides: Dictionary of manual override values that take absolute precedence.

        Returns:
            The configured `ConfigLoader` instance.

        Examples:
            ```python
            from aquilia.config import ConfigLoader

            loader = ConfigLoader.load(
                paths=["workspace.py"],
                env_prefix="AQ_",
                overrides={"runtime": {"port": 8080}}
            )
            ```
        """
        loader = cls(env_prefix=env_prefix)

        # Step 1: Load workspace structure from workspace.py or aquilia.py
        if not paths:
            if Path("workspace.py").exists():
                paths = ["workspace.py"]
            elif Path("aquilia.py").exists():
                paths = ["aquilia.py"]

        if paths:
            for pattern in paths:
                if pattern.endswith(".py"):
                    loader._load_python_config(pattern)
                else:
                    loader._load_from_files(pattern)

        # Step 2: Legacy fallback — load config/env.py if it exists
        # (New projects inline AquilaConfig in workspace.py via .env_config())
        env_config_path = Path("config/env.py")
        if env_config_path.exists():
            loader._load_pyconfig_file(env_config_path)

        # Step 3: Load from .env file
        if env_file:
            loader._load_env_file(env_file)

        # Step 4: Native dotenv auto-load for default/legacy flows.
        # For AquilaConfig users, this is typically already resolved by
        # pyconfig class policy and remains idempotent here.
        try:
            from aquilia.dotenv import DotEnvLoader

            DotEnvLoader.ensure_loaded()
        except ImportError:
            pass

        # Step 5: Load from environment variables
        loader._load_from_env()

        # Step 6: Apply manual overrides
        if overrides:
            loader._merge_dict(loader.config_data, overrides)

        # Build apps namespace
        loader._build_apps_namespace()

        return loader

    def _load_python_config(self, path: str):
        """
        Load config from Python file (aquilia.py).

        Expects a 'workspace' variable that is a Workspace instance.
        """
        import importlib.util
        from pathlib import Path

        config_path = Path(path)
        if not config_path.exists():
            return

        # Load Python module
        spec = importlib.util.spec_from_file_location("aquilia_config", config_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Get workspace object
            if hasattr(module, "workspace"):
                workspace = module.workspace
                # Convert workspace to dict and merge
                config_dict = workspace.to_dict()
                self._merge_dict(self.config_data, config_dict)

    def _load_pyconfig_file(self, path: Path):
        """
        Load config from a Python file containing AquilaConfig subclasses.

        Uses ``PyConfigLoader`` from ``aquilia.pyconfig`` to import the
        file, resolve the correct environment variant, and merge the
        resulting dict into ``self.config_data``.
        """
        import importlib.util
        from pathlib import Path as _Path

        path = _Path(path)
        if not path.exists():
            return

        spec = importlib.util.spec_from_file_location("_aq_env_config", path)
        if spec is None or spec.loader is None:
            return

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Look for AquilaConfig subclass
        import os

        from aquilia.pyconfig import AquilaConfig

        base_cls = None
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
            return

        # Load .env BEFORE reading AQ_ENV so a .env that sets
        # AQ_ENV=prod is visible when we choose the environment class.
        from aquilia.pyconfig import _ensure_dotenv_loaded

        _ensure_dotenv_loaded(config_cls=base_cls)

        env_name = os.environ.get("AQUILIA_ENV") or os.environ.get("AQ_ENV", "dev")
        try:
            resolved = base_cls.for_env(env_name)
        except ValueError:
            resolved = base_cls

        data = resolved.to_dict()

        # Normalise server → runtime
        if "server" in data and "runtime" not in data:
            data["runtime"] = data.pop("server")
        elif "server" in data and "runtime" in data:
            data["runtime"].update(data.pop("server"))

        self._merge_dict(self.config_data, data)

    def _load_from_files(self, pattern: str):
        """Load config from Python or JSON files."""
        from glob import glob

        for path_str in glob(pattern):
            path = Path(path_str)

            if path.suffix == ".py":
                self._load_python_config(path)
            elif path.suffix == ".json":
                self._load_json_file(path)

    def _load_python_file(self, path: Path):
        """Load config from Python module."""
        import importlib.util

        spec = importlib.util.spec_from_file_location("config", path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Extract uppercase variables as config
            config = {key: value for key, value in vars(module).items() if key.isupper() and not key.startswith("_")}
            self._merge_dict(self.config_data, config)

    def _load_json_file(self, path: Path):
        """Load config from JSON file."""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            self._merge_dict(self.config_data, data)

    def _load_yaml_file(self, path: Path):
        """REMOVED — YAML config is no longer supported.

        Use Python-native configuration via ``AquilaConfig`` subclasses
        inlined in ``workspace.py``.  See ``aquilia.pyconfig`` for
        the migration guide.

        Raises:
            RuntimeError: Always, directing user to migrate.
        """
        raise ConfigInvalidFault(
            key=str(path),
            reason="YAML configuration is no longer supported. "
            "Migrate to Python-native config: define AquilaConfig subclasses "
            "in workspace.py and wire via .env_config(). See aquilia.pyconfig docs.",
        )

    def _load_env_file(self, path: str):
        """
        Load config from .env file using native dotenv loader.

        Loads ALL variables into os.environ (for Env() bindings in AquilaConfig),
        and also processes AQ_ prefixed vars into config_data.
        """
        try:
            from aquilia.dotenv import dotenv_values, load_dotenv
        except ImportError:
            # Fallback to old implementation if dotenv not available
            log.warning("Native dotenv module not available, using fallback")
            env_path = Path(path)
            if not env_path.exists():
                return

            with open(env_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")

                        if key.startswith(self.env_prefix):
                            self._set_nested(key, value)
            return

        # Use native dotenv loader - this populates os.environ with ALL variables
        load_dotenv(path, override=False)
        loaded = dotenv_values(path)

        # Also process AQ_ prefixed vars into config_data
        for key, value in loaded.items():
            if key.startswith(self.env_prefix):
                self._set_nested(key, value)

    def _load_from_env(self):
        """Load config from environment variables."""
        for key, value in os.environ.items():
            if key.startswith(self.env_prefix):
                self._set_nested(key, value)

    def _set_nested(self, key: str, value: str):
        """Convert AQ_APPS_USERS_MAX_SIZE to nested dict."""
        # Remove prefix
        key = key[len(self.env_prefix) :]

        # Split by double underscore for nested keys
        parts = key.lower().split("__")

        current = self.config_data
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        # Try to parse value
        current[parts[-1]] = self._parse_value(value)

    def _parse_value(self, value: str) -> Any:
        """Parse string value to appropriate type."""
        # Boolean
        if value.lower() in ("true", "yes", "1"):
            return True
        if value.lower() in ("false", "no", "0"):
            return False

        # Number
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            pass

        # JSON
        if value.startswith(("{", "[")):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass

        return value

    def _merge_dict(self, target: dict, source: dict):
        """Deep merge source into target."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_dict(target[key], value)
            else:
                target[key] = value

    def _build_apps_namespace(self):
        """Build nested namespace for apps from config_data['apps']."""
        apps_data = self.config_data.get("apps", {})
        self.apps = NestedNamespace(apps_data)

    def get(self, path: str, default: Any = None) -> Any:
        """
        Retrieve a configuration value by a dot-separated query path.

        Automatically logs access tracing spans to the active inspector if active,
        redacting fields that look like secrets (e.g. passwords, API keys).

        Parameters:
            path: Dot-separated path to the configuration key (e.g. `"runtime.port"`).
            default: Value returned if the path cannot be resolved. Defaults to `None`.

        Returns:
            The resolved configuration value or the specified default.

        Examples:
            ```python
            port = loader.get("runtime.port", default=8000)
            ```
        """
        t0 = None
        trace = None
        try:
            import time

            from aquilia.inspector.trace import current_trace

            trace = current_trace()
            if trace is not None:
                t0 = time.monotonic()
        except ImportError:
            pass

        parts = path.split(".")
        current = self.config_data

        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                current = default
                break

        if trace is not None and t0 is not None:
            try:
                import time

                from aquilia.inspector.trace import Lane, SpanStatus

                now_offset = (time.monotonic() - trace.started_monotonic) * 1000.0
                duration_ms = (time.monotonic() - t0) * 1000.0

                # Eagerly redact sensitive values
                val_rep = repr(current)
                if any(k in path.lower() for k in ("secret", "password", "key", "token", "signature")):
                    val_rep = "***REDACTED***"

                trace.add_span(
                    lane=Lane.SETTINGS,
                    label=f"Access config: {path}",
                    start_offset_ms=max(0.0, now_offset - duration_ms),
                    duration_ms=duration_ms,
                    status=SpanStatus.OK,
                    detail={"path": path, "value": val_rep},
                )
            except Exception:
                pass

        return current

    def get_app_config(self, app_name: str, config_class: type[Config]) -> Config:
        """
        Retrieve and validate a strongly-typed configuration block for a specific module.

        Merges root-level configurations (excluding the `apps` block) with module-specific
        overrides inside `apps.{app_name}`, then validates parameters against type hints.

        Parameters:
            app_name: Name of the application module to query config for.
            config_class: Configuration schema or dataclass subclassing `Config` or standard dataclass.

        Returns:
            The validated and instantiated configuration object.

        Raises:
            ConfigError: If a required field is missing or a type mismatch is detected.

        Examples:
            ```python
            @dataclass
            class MyModuleConfig(Config):
                enable_feature: bool = False
                api_url: str = "http://localhost"

            config = loader.get_app_config("mymodule", MyModuleConfig)
            ```
        """
        # Get app-specific config
        app_config_data = self.get(f"apps.{app_name}", {})

        # Also check root level
        root_data = {k: v for k, v in self.config_data.items() if k != "apps"}

        # Merge: app-specific overrides root
        merged = {**root_data, **app_config_data}

        # Instantiate and validate
        return self._instantiate_config(config_class, merged)

    def _instantiate_config(self, config_class: type[Config], data: dict) -> Config:
        """Instantiate config class with validation."""
        if is_dataclass(config_class):
            return self._instantiate_dataclass(config_class, data)

        # For plain Config subclasses, create instance and set attributes
        instance = config_class()

        # Get type hints
        hints = get_type_hints(config_class)

        for key, value_type in hints.items():
            if key in data:
                value = data[key]
                # Basic type validation
                if not self._check_type(value, value_type):
                    raise ConfigError(f"Config field '{key}' expected {value_type}, got {type(value)}")
                setattr(instance, key, value)
            elif hasattr(config_class, key):
                # Use default value
                default = getattr(config_class, key)
                setattr(instance, key, default)

        return instance

    def _instantiate_dataclass(self, config_class: type, data: dict):
        """Instantiate dataclass config with validation."""
        kwargs = {}

        for field_info in fields(config_class):
            field_name = field_info.name
            field_type = field_info.type

            if field_name in data:
                value = data[field_name]

                # Validate type
                if not self._check_type(value, field_type):
                    raise ConfigError(f"Config field '{field_name}' expected {field_type}, got {type(value).__name__}")

                kwargs[field_name] = value
            elif field_info.default is not MISSING:
                kwargs[field_name] = field_info.default
            elif field_info.default_factory is not MISSING:
                kwargs[field_name] = field_info.default_factory()
            else:
                raise ConfigError(f"Required config field '{field_name}' not provided")

        return config_class(**kwargs)

    def _check_type(self, value: Any, expected_type: type) -> bool:
        """Basic type checking."""
        # Handle Optional types (Optional[X] is Union[X, None])
        import types

        origin = get_origin(expected_type)
        if origin is types.UnionType or str(origin) == "typing.Union":
            args = get_args(expected_type)
            if value is None:
                return True
            if args:
                return self._check_type(value, args[0])

        # Handle generic types
        if origin:
            return isinstance(value, origin)

        # Direct type check
        try:
            return isinstance(value, expected_type)
        except TypeError:
            # For complex types, skip validation
            return True

    def to_dict(self) -> dict:
        """Export all config as dictionary."""
        return self.config_data.copy()

    def has_subsystem(self, name: str) -> bool:
        """Check if a subsystem is explicitly configured in user config data."""
        if name in self.config_data:
            return True
        integrations = self.config_data.get("integrations")
        if isinstance(integrations, dict) and name in integrations:
            return True
        return False

    def get_subsystem_config(self, name: str, defaults: dict) -> dict:
        """Generic subsystem config reader with standard merge pattern."""
        user_config = self.get(name, {}) or self.get(f"integrations.{name}", {})
        merged = defaults.copy()
        if user_config:
            merged["enabled"] = user_config.get("enabled", True)
            self._merge_dict(merged, user_config)
        return merged

    def get_session_config(self) -> dict:
        """
        Get session configuration with defaults.

        Returns:
            Session configuration dictionary
        """
        default_session_config = {
            "enabled": False,
            "policy": {
                "name": "user_default",
                "ttl_days": 7,
                "idle_timeout_minutes": 30,
                "rotate_on_privilege_change": True,
                "max_sessions_per_principal": 5,
            },
            "store": {
                "type": "memory",
                "max_sessions": 10000,
                "directory": None,
                "redis_url": None,
                "key_prefix": "aquilia:session:",
            },
            "transport": {
                "adapter": "cookie",
                "cookie_name": "aquilia_session",
                "cookie_httponly": True,
                "cookie_secure": True,
                "cookie_samesite": "lax",
                "header_name": "X-Session-ID",
            },
        }

        user_config = self.get("sessions", {})
        if not user_config:
            user_config = self.get("integrations.sessions", {})

        merged = default_session_config.copy()
        if user_config:
            merged["enabled"] = user_config.get("enabled", True)
            self._merge_dict(merged, user_config)

            if isinstance(merged.get("store"), str):
                store_str = merged["store"]
                merged["store"] = {
                    "type": store_str,
                    "max_sessions": 10000,
                }

            if "policies" in user_config and user_config["policies"]:
                first_policy = user_config["policies"][0]
                if hasattr(first_policy, "name") and hasattr(first_policy, "ttl"):
                    merged["policy"] = first_policy
                    if hasattr(first_policy, "transport"):
                        merged["transport_policy"] = first_policy.transport

        return merged

    def get_auth_config(self) -> dict:
        return self.get_subsystem_config(
            "auth",
            {
                "enabled": False,
                "store": {
                    "type": "memory",
                    "db_url": None,
                },
                "tokens": {
                    "secret_key": "aquilia_insecure_dev_secret",
                    "algorithm": "HS256",
                    "issuer": "aquilia",
                    "audience": "aquilia-app",
                    "access_token_ttl_minutes": 60,
                    "refresh_token_ttl_days": 30,
                },
                "security": {
                    "require_auth_by_default": False,
                    "hash_rounds": 12,
                    "backends": [
                        "aquilia.auth.backends.TokenBackend",
                        "aquilia.auth.backends.SessionBackend",
                    ],
                },
            },
        )

    def get_template_config(self) -> dict:
        return self.get_subsystem_config(
            "templates",
            {
                "enabled": False,
                "search_paths": [],
                "precompile": False,
                "cache": "memory",
                "sandbox": True,
                "sandbox_policy": "strict",
            },
        )

    def get_security_config(self) -> dict:
        return self.get_subsystem_config(
            "security",
            {
                "enabled": False,
                "cors_enabled": False,
                "csrf_protection": False,
                "helmet_enabled": False,
                "rate_limiting": False,
                "https_redirect": False,
                "hsts": False,
                "proxy_fix": False,
            },
        )

    def get_static_config(self) -> dict:
        return self.get_subsystem_config(
            "static_files",
            {
                "enabled": False,
                "directories": {"/static": "static"},
                "cache_max_age": 86400,
                "etag": True,
                "gzip": True,
                "brotli": True,
                "memory_cache": True,
            },
        )

    def get_cache_config(self) -> dict:
        return self.get_subsystem_config(
            "cache",
            {
                "enabled": False,
                "backend": "memory",
                "default_ttl": 300,
                "max_size": 10000,
                "eviction_policy": "lru",
                "namespace": "default",
                "key_prefix": "aq:",
                "serializer": "json",
                "redis_url": "redis://localhost:6379/0",
                "redis_max_connections": 10,
                "redis_socket_timeout": 5.0,
                "redis_socket_connect_timeout": 5.0,
                "redis_retry_on_timeout": True,
                "redis_decode_responses": True,
                "l1_max_size": 1000,
                "l1_ttl": 60,
                "l2_backend": "redis",
                "middleware_enabled": False,
                "middleware_cacheable_methods": ["GET", "HEAD"],
                "middleware_default_ttl": 60,
                "middleware_vary_headers": ["Accept", "Accept-Encoding"],
                "trace_enabled": True,
                "metrics_enabled": True,
                "log_level": "WARNING",
            },
        )

    def get_di_config(self) -> dict:
        """Get dependency-injection container configuration with defaults.

        Populates :class:`aquilia.di.settings.DISettings` at boot. See
        :class:`aquilia.pyconfig.AquilaConfig.DI` for the field reference.

        Returns:
            DI configuration dictionary.
        """
        return self.get_subsystem_config(
            "di",
            {
                "enabled": True,
                "scope_enforcement": "warn",
                "parallel_resolution": False,
                "diagnostics_enabled": False,
                "disposal_strategy": "lifo",
                "hook_timeout_seconds": 30.0,
                "pool_acquire_timeout_seconds": 30.0,
                "pool_max_waiters": None,
                "type_key_cache_max": 8192,
                "enable_conditional_providers": True,
                "enable_plugins": True,
                "strict_service_registration": False,
            },
        )

    def get_i18n_config(self) -> dict:
        return self.get_subsystem_config(
            "i18n",
            {
                "enabled": False,
                "default_locale": "en",
                "available_locales": ["en"],
                "fallback_locale": "en",
                "catalog_dirs": ["locales"],
                "catalog_format": "json",
                "missing_key_strategy": "log_and_key",
                "auto_reload": False,
                "auto_detect": True,
                "cookie_name": "aq_locale",
                "query_param": "lang",
                "path_prefix": False,
                "resolver_order": ["query", "cookie", "header"],
            },
        )

    def get_mail_config(self) -> dict:
        return self.get_subsystem_config(
            "mail",
            {
                "enabled": False,
                "default_from": "noreply@localhost",
                "default_reply_to": None,
                "subject_prefix": "",
                "providers": [],
                "console_backend": False,
                "preview_mode": False,
                "templates": {
                    "template_dirs": ["mail_templates"],
                    "auto_escape": True,
                    "cache_compiled": True,
                    "strict_mode": False,
                },
                "retry": {
                    "max_attempts": 5,
                    "base_delay": 1.0,
                    "max_delay": 3600.0,
                    "jitter": True,
                },
                "rate_limit": {
                    "global_per_minute": 1000,
                    "per_domain_per_minute": 100,
                },
                "security": {
                    "dkim_enabled": False,
                    "require_tls": True,
                    "pii_redaction_enabled": False,
                },
                "metrics_enabled": True,
                "tracing_enabled": False,
            },
        )

    def get_tasks_config(self) -> dict:
        return self.get_subsystem_config(
            "tasks",
            {
                "enabled": False,
                "backend": "memory",
                "num_workers": 4,
                "default_queue": "default",
                "cleanup_interval": 300.0,
                "cleanup_max_age": 3600.0,
                "max_retries": 3,
                "retry_delay": 1.0,
                "retry_backoff": 2.0,
                "retry_max_delay": 300.0,
                "default_timeout": 300.0,
                "auto_start": True,
                "dead_letter_max": 1000,
            },
        )

    def get_database_config(self) -> dict:
        """
        Get database configuration with defaults.

        Returns:
            Database configuration dictionary.
        """
        return self.get_subsystem_config(
            "database",
            {
                "enabled": False,
                "url": None,
                "auto_connect": True,
                "auto_create": True,
                "auto_migrate": False,
                "migrations_dir": "migrations",
                "pool_size": 5,
                "echo": False,
                "model_paths": [],
                "scan_dirs": ["models"],
            },
        )

    def get_storage_config(self) -> dict:
        return self.get_subsystem_config(
            "storage",
            {
                "enabled": False,
                "default": "default",
                "backends": [],
            },
        )

    def get_middleware_config(self) -> list | None:
        """
        Get middleware chain configuration.

        Returns the user-defined middleware chain from workspace config,
        or ``None`` if no chain was configured (server falls back to
        built-in defaults).
        """
        chain = self.get("middleware_chain")
        return chain if chain is not None else None

    def get_versioning_config(self) -> dict:
        return self.get_subsystem_config(
            "versioning",
            {
                "enabled": False,
                "strategy": "header",
                "versions": [],
                "default_version": None,
                "require_version": False,
                "header_name": "X-API-Version",
                "query_param": "api_version",
                "url_prefix": "v",
                "url_segment_index": 0,
                "strip_version_from_path": True,
                "media_type_param": "version",
                "channels": {},
                "channel_header": "X-API-Channel",
                "channel_query_param": "api_channel",
                "negotiation_mode": "exact",
                "sunset_policy": {},
                "sunset_schedules": {},
                "include_version_header": True,
                "response_header_name": "X-API-Version",
                "include_supported_versions_header": True,
                "supported_versions_header": "X-API-Supported-Versions",
                "neutral_paths": ["/_health", "/specula", "/specula/spec.json"],
            },
        )

    def get_inspector_config(self) -> dict:
        return self.get_subsystem_config(
            "inspector",
            {
                "enabled": None,
                "force_enable_in_prod": False,
                "max_traces": 200,
                "max_body_bytes": 65536,
                "capture_request_body": True,
                "capture_response_body": True,
                "capture_client_addr": False,
                "redact_headers": [
                    "authorization",
                    "cookie",
                    "set-cookie",
                    "x-api-key",
                    "x-auth-token",
                    "proxy-authorization",
                ],
                "redact_body_keys": [
                    "password",
                    "passwd",
                    "secret",
                    "token",
                    "api_key",
                    "apikey",
                    "authorization",
                    "credit_card",
                    "card_number",
                    "cvv",
                    "signature",
                ],
                "slow_request_threshold_ms": 500.0,
                "mount_path": "/__aquilia__/inspector",
                "standalone_ui_enabled": True,
                "admin_page_enabled": True,
                "replay_enabled": True,
                "live_stream_enabled": True,
                "toolbar_enabled": None,
                "store": "memory",
                "store_path": ":memory:",
                "authorized_ips": ["127.0.0.1", "::1"],
                "dashboard_auth_token": None,
                "sampling_rate": 1.0,
            },
        )
