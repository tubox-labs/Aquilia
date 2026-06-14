# Configuration

## Overview

Aquilia uses a **zero-YAML, class-based Python configuration DSL**. Define `AquilaConfig` subclasses directly in `workspace.py`. Config is code: type-checked by Pylance/mypy, IDE auto-completed, diffable in `git blame`.

```python
from aquilia.config import AquilaConfig, Env, Secret, section

class BaseEnv(AquilaConfig):
    class server(AquilaConfig.Server):
        host = "127.0.0.1"
        port = 8000

    class auth(AquilaConfig.Auth):
        secret_key = Secret(env="AQ_SECRET_KEY", required=True)

class DevEnv(BaseEnv):
    env = "dev"
    class server(BaseEnv.server):
        reload = True
        debug = True
```

---

## Core Types

### `Env`

!!! abstract "`aquilia.pyconfig.Env`"

Binds a configuration field to an environment variable. Resolves at read time.

```python
class Env:
    def __init__(
        self,
        name: str,
        *,
        default: ConfigValue = None,
        cast: type | Callable[[str], Any] | None = None,
        required: bool = False,
    ) -> None:
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `name` | `str` | — | Env var name (e.g. `"DATABASE_URL"`) |
| `default` | `ConfigValue` | `None` | Fallback value |
| `cast` | `type \| Callable \| None` | `None` | Type caster (e.g. `int`, `bool`, custom) |
| `required` | `bool` | `False` | Raise `ConfigMissingFault` if not set and no default |

```python
def resolve(self, *, use_cache: bool = False) -> ConfigValue:
    """Resolve from os.environ. Auto-loads .env on first call."""

def invalidate_cache(self) -> None: ...

@classmethod
def disable_auto_load(cls) -> None: ...

@classmethod
def enable_auto_load(cls) -> None: ...
```

Auto-casting: when `cast` is not specified, tries `int → float → JSON → str`.

```python
debug   = Env("AQ_DEBUG",   default=False, cast=bool)
workers = Env("AQ_WORKERS", default=4,     cast=int)
host    = Env("AQ_HOST",    default="127.0.0.1")
```

### `Secret`

!!! abstract "`aquilia.pyconfig.Secret`"

Holds sensitive values. Never exposed in `repr()`, `str()`, or `to_dict()` unless `reveal()` is called.

```python
class Secret:
    def __init__(
        self,
        value: str | None = None,          # Literal value (dev only)
        *,
        env: str | None = None,             # Environment variable name
        default: str | None = None,         # Fallback
        required: bool = False,
    ) -> None:

    def reveal(self) -> str | None:
        """Return actual secret. Auto-loads .env. Raises ConfigMissingFault if required + missing."""
```

Resolution priority: `env` → `value` → `default`.

```python
secret_key = Secret(env="AQ_SECRET_KEY", required=True)
db_password = Secret(env="DB_PASSWORD", default="devpassword")
api_key = Secret(value="sk-test-abc123")   # inline (dev only)
```

### `section`

```python
def section(cls: type) -> type:
    """Mark a nested class as a config section."""
```

---

## `AquilaConfig` Base Class

!!! abstract "`aquilia.pyconfig.AquilaConfig`"

```python
class AquilaConfig:
    env: str = "dev"    # Environment label

    @classmethod
    def to_dict(cls, *, use_cache: bool = True) -> dict[str, Any]:
        """Serialize config to nested dict. All Env/Secret resolved."""

    @classmethod
    def to_loader(cls) -> ConfigLoader:
        """Populate and return a ConfigLoader for subsystem consumption."""

    @classmethod
    def invalidate_cache(cls) -> None:
        """Clear cached to_dict() result."""

    @classmethod
    def from_env_var(cls, *, env_var: str = "AQUILIA_ENV") -> type[AquilaConfig]:
        """Resolve to a subclass based on env name."""
```

### Dotenv Configuration

```python
class AquilaConfig.Dotenv:
    file: str | Path | None = None           # Single .env path
    files: list | tuple | None = None         # Multiple .env paths
    auto_load: bool = True                    # Auto-load before Env/Secret resolution
    override: bool = False                    # Allow .env to override existing env vars
    interpolate: bool = True                  # Enable ${VAR} interpolation
    strict: bool = False                      # All configured files required

class AquilaConfig.EnvFile:
    def __init__(self, path: str | Path, *, required: bool = False):
```

```python
class MyConfig(AquilaConfig):
    class dotenv(AquilaConfig.Dotenv):
        files = [
            AquilaConfig.EnvFile(".env", required=True),
            ".env.local",
        ]
```

Auto-searched paths (when `dotenv.files` not set):

```
.env, .env.example, .env.defaults, .env.default, .env.local,
.env.{env}, .env.{env}.local,
config/.env, config/.env.{env}, config/.env.{env}.local
```

---

## Built-in Section Classes

### `AquilaConfig.Server`

HTTP / ASGI server settings. Maps to uvicorn parameters automatically.

```python
class AquilaConfig.Server:
    # ── Core ──────────────────────────────
    host: str = "127.0.0.1"
    port: int = 8000
    uds: str | None = None                # Unix domain socket
    fd: int | None = None                 # File descriptor bind
    workers: int = 1
    mode: str = "dev"
    debug: bool = False

    # ── Reload / Development ──────────────
    reload: bool = False
    reload_dirs: list[str] | None = None
    reload_delay: float = 0.25
    reload_includes: list[str] | None = None
    reload_excludes: list[str] | None = None

    # ── Protocol ──────────────────────────
    http: str = "auto"                   # "auto" | "h11" | "httptools"
    ws: str = "auto"                     # "auto" | "wsproto" | "websockets" | "none"
    lifespan: str = "auto"
    interface: str = "auto"              # "auto" | "asgi3" | "asgi2" | "wsgi"
    loop: str = "auto"                   # "auto" | "asyncio" | "uvloop"

    # ── Timeouts ──────────────────────────
    timeout_keep_alive: int = 5
    timeout_worker_healthcheck: int = 30
    timeout_graceful_shutdown: int | None = None

    # ── Limits ────────────────────────────
    backlog: int = 2048
    limit_concurrency: int | None = None
    limit_max_requests: int | None = None

    # ── Proxy / Headers ───────────────────
    proxy_headers: bool = True
    forwarded_allow_ips: str | None = None
    server_header: bool = True
    date_header: bool = True
    root_path: str = ""

    # ── Logging ───────────────────────────
    access_log: bool = True
    log_level: str | None = None
    use_colors: bool | None = None

    # ── WebSocket ─────────────────────────
    ws_max_size: int = 16777216            # 16 MiB
    ws_max_queue: int = 32
    ws_ping_interval: float | None = 20.0
    ws_ping_timeout: float | None = 20.0
    ws_per_message_deflate: bool = True

    # ── TLS / SSL ─────────────────────────
    ssl_keyfile: str | None = None
    ssl_certfile: str | None = None
    ssl_keyfile_password: str | None = None
    ssl_ca_certs: str | None = None
    ssl_ciphers: str = "TLSv1"

    # ── HTTP/1.1 ──────────────────────────
    h11_max_incomplete_event_size: int | None = None
```

### `AquilaConfig.Auth`

```python
class AquilaConfig.Auth:
    enabled: bool = True
    store_type: str = "memory"               # "memory" | "database" | "redis"
    secret_key: str | None = None            # JWT signing key
    algorithm: str = "HS256"                 # "HS256"|"HS384"|"HS512"|"RS256"|"ES256"|"EdDSA"
    issuer: str = "aquilia"
    audience: str = "aquilia-app"
    access_token_ttl_minutes: int = 60
    refresh_token_ttl_days: int = 30
    require_auth_by_default: bool = False
    password_hasher: AquilaConfig.PasswordHasher | None = None
```

### `AquilaConfig.PasswordHasher`

```python
class AquilaConfig.PasswordHasher:
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

    def to_dict(self) -> dict[str, Any]: ...
    def build_hasher(self) -> PasswordHasher: ...

    # Factory classmethods
    @classmethod
    def argon2id(cls, *, time_cost=2, memory_cost=65536, parallelism=4): ...
    @classmethod
    def scrypt(cls, *, n=32768, r=8, p=1, dklen=32): ...
    @classmethod
    def bcrypt(cls, *, rounds=12): ...
    @classmethod
    def pbkdf2_sha512(cls, *, iterations=210000): ...
    @classmethod
    def pbkdf2_sha256(cls, *, iterations=600000): ...
```

### `AquilaConfig.Database`

```python
class AquilaConfig.Database:
    url: str = "sqlite:///db.sqlite3"
    auto_connect: bool = True
    auto_create: bool = True
    auto_migrate: bool = False
    pool_size: int = 5
    echo: bool = False                          # SQL logging
    migrations_dir: str = "migrations"
```

### `AquilaConfig.Cache`

```python
class AquilaConfig.Cache:
    backend: str = "memory"                     # "memory" | "redis"
    default_ttl: int = 300
    max_size: int = 10000
    eviction_policy: str = "lru"                # "lru" | "lfu" | "ttl" | "fifo"
    namespace: str = "default"
    key_prefix: str = "aq:"
    redis_url: str = "redis://localhost:6379/0"
```

### `AquilaConfig.Sessions`

```python
class AquilaConfig.Sessions:
    enabled: bool = False
    store_type: str = "memory"                  # "memory" | "file" | "redis"
    cookie_name: str = "aquilia_session"
    cookie_secure: bool = True
    cookie_httponly: bool = True
    cookie_samesite: str = "lax"                # "strict" | "lax" | "none"
    ttl_days: int = 7
    idle_timeout_minutes: int = 30
```

### `AquilaConfig.Security`

```python
class AquilaConfig.Security:
    enabled: bool = False
    cors_enabled: bool = False
    csrf_protection: bool = False
    helmet_enabled: bool = False                # SecurityHeadersMiddleware
    rate_limiting: bool = False
    https_redirect: bool = False
    hsts: bool = False
```

### `AquilaConfig.Logging`

```python
class AquilaConfig.Logging:
    level: str = "INFO"
    colorize: bool = True
    slow_threshold_ms: float = 1000.0           # Log warning for slow requests
    include_headers: bool = False
```

### `AquilaConfig.I18n`

```python
class AquilaConfig.I18n:
    enabled: bool = False
    default_locale: str = "en"
    available_locales: list[str] = ["en"]
    fallback_locale: str = "en"
    catalog_dirs: list[str] = ["locales"]
    catalog_format: str = "json"
```

### `AquilaConfig.Signing`

```python
class AquilaConfig.Signing:
    secret: str | None = None                   # Primary signing secret
    fallback_secrets: list[str] = []            # Retired secrets for key rotation
    algorithm: str = "HS256"
    salt: str = "aquilia.signing"
    session_salt: str = "aquilia.sessions"
    csrf_salt: str = "aquilia.csrf"
    activation_salt: str = "aquilia.activation"
    cache_salt: str = "aquilia.cache"
```

### `AquilaConfig.Render`

```python
class AquilaConfig.Render:
    enabled: bool = True
    service_name: str | None = None
    region: str = "oregon"                      # "oregon" | "frankfurt" | "ohio" |
                                                # "virginia" | "singapore"
    plan: str = "starter"                       # "free" | "starter" | "standard" |
                                                # "pro" | "pro_plus" | "pro_max" | "pro_ultra"
    num_instances: int = 1
    image: str | None = None                    # registry/name:tag
    health_path: str = "/_health"
    auto_deploy: str = "no"                     # "yes" | "no"
    port: int = 8000
```

### `AquilaConfig.Mail`

```python
class AquilaConfig.Mail:
    enabled: bool = False
    default_from: str = "noreply@localhost"
    console_backend: bool = False               # Print to console instead of sending
    require_tls: bool = True
    retry_max_attempts: int = 5
```

### `AquilaConfig.Apps`

Per-module app-specific settings. Subclass and add nested classes named after modules.

```python
class apps(AquilaConfig.Apps):
    class auth:
        max_login_attempts = 5
        token_expiry = 3600
    class users:
        cache_ttl = 300
```

---

## Environment Overlays

```python
class BaseEnv(AquilaConfig):
    class server(AquilaConfig.Server):
        host = "127.0.0.1"
        port = 8000
        workers = 1

    class auth(AquilaConfig.Auth):
        secret_key = Secret(env="AQ_SECRET_KEY", required=True)
        algorithm = "HS256"

class DevEnv(BaseEnv):
    env = "dev"
    class server(BaseEnv.server):
        reload = True
        debug = True

class ProdEnv(BaseEnv):
    env = "prod"
    class server(BaseEnv.server):
        host = "0.0.0.0"
        workers = Env("WEB_WORKERS", default=4, cast=int)
        ssl_certfile = "/etc/certs/cert.pem"
        ssl_keyfile = "/etc/certs/key.pem"

    class auth(BaseEnv.auth):
        algorithm = "HS512"
        password_hasher = AquilaConfig.PasswordHasher(
            algorithm="argon2id",
            time_cost=3,
            memory_cost=131072,
        )
```

### Wiring in Workspace

```python
workspace = (
    Workspace("myapp")
    .env_config(BaseEnv)         # Resolved by AQUILIA_ENV
    .module(...)
)
```

Environment is selected via `AQUILIA_ENV` (defaults to `"dev"`):

```bash
AQUILIA_ENV=prod aq serve
```

### Manual Loading

```python
from aquilia.config import AquilaConfig

# Load based on env variable
config_cls = BaseEnv.from_env_var()
loader = config_cls.to_loader()

# Direct instantiation
loader = ProdEnv.to_loader()
```

---

## ConfigLoader (internal)

!!! abstract "`aquilia.config.ConfigLoader`"

The internal runtime config reader. `AquilaConfig.to_loader()` produces this. All subsystem configs are read through it.

```python
class ConfigLoader:
    def get(self, key: str, default: Any = None) -> Any: ...
    def get_section(self, section: str) -> ConfigLoader: ...
    def get_list(self, key: str, default: list | None = None) -> list: ...
    def get_dict(self, key: str, default: dict | None = None) -> dict: ...
    def get_bool(self, key: str, default: bool = False) -> bool: ...
    def get_int(self, key: str, default: int = 0) -> int: ...
    def get_float(self, key: str, default: float = 0.0) -> float: ...
    def to_dict(self) -> dict[str, Any]: ...
```

---

## Full Example

```python
# workspace.py
from aquilia.config import Workspace, Module, Integration, AquilaConfig, Env, Secret, section

class BaseEnv(AquilaConfig):
    env = "dev"

    class dotenv(AquilaConfig.Dotenv):
        files = [AquilaConfig.EnvFile(".env", required=True), ".env.local"]
        strict = False

    class server(AquilaConfig.Server):
        host = "127.0.0.1"
        port = 8000
        workers = Env("WEB_WORKERS", default=2, cast=int)
        reload = False
        debug = False
        timeout_keep_alive = 30
        proxy_headers = True
        forwarded_allow_ips = Env("TRUSTED_PROXIES", default="127.0.0.1")

    class auth(AquilaConfig.Auth):
        enabled = True
        secret_key = Secret(env="AQ_SECRET_KEY", required=True)
        algorithm = "HS256"
        issuer = "myapp"
        access_token_ttl_minutes = Env("TOKEN_TTL", default=30, cast=int)
        password_hasher = AquilaConfig.PasswordHasher.argon2id(time_cost=2, memory_cost=65536)

    class database(AquilaConfig.Database):
        url = Env("DATABASE_URL", default="sqlite:///db.sqlite3")
        pool_size = 5
        echo = Env("DB_ECHO", default=False, cast=bool)

    class cache(AquilaConfig.Cache):
        backend = Env("CACHE_BACKEND", default="memory")
        default_ttl = 300
        redis_url = Env("REDIS_URL", default="redis://localhost:6379/0")

    class sessions(AquilaConfig.Sessions):
        enabled = True
        store_type = Env("SESSION_STORE", default="memory")
        cookie_secure = True
        cookie_httponly = True

    class security(AquilaConfig.Security):
        cors_enabled = True
        csrf_protection = True
        rate_limiting = True
        hsts = True

    class logging(AquilaConfig.Logging):
        level = Env("LOG_LEVEL", default="INFO")
        colorize = True
        slow_threshold_ms = 500.0

    class signing(AquilaConfig.Signing):
        secret = Secret(env="AQ_SECRET_KEY", required=True)
        algorithm = "HS256"

# Dev environment override
class DevEnv(BaseEnv):
    env = "dev"
    class server(BaseEnv.server):
        reload = True
        debug = True
    class database(BaseEnv.database):
        echo = True

# Production environment override
class ProdEnv(BaseEnv):
    env = "prod"
    class server(BaseEnv.server):
        host = "0.0.0.0"
        workers = 4
        ssl_certfile = "/etc/ssl/cert.pem"
        ssl_keyfile = "/etc/ssl/key.pem"
    class auth(BaseEnv.auth):
        algorithm = "HS512"
        password_hasher = AquilaConfig.PasswordHasher.argon2id(
            time_cost=3, memory_cost=131072, parallelism=4,
        )
    class sessions(BaseEnv.sessions):
        store_type = "redis"

workspace = (
    Workspace("myapp")
    .env_config(BaseEnv)
    .module(Module("users", path="modules/users"))
    .module(Module("products", path="modules/products"))
    .integration(Integration.database())
    .integration(Integration.cache())
    .integration(Integration.sessions())
    .integration(Integration.security())
)
```