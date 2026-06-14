# Configuration Guide

Aquilia uses a **zero-YAML, Python-native** configuration system. All settings are pure Python classes — type-checked by your IDE, diffable in `git blame`, and validated at startup.

## Architecture overview

```mermaid
graph TD
    A[workspace.py] --> B[Workspace Builder]
    A --> C[AquilaConfig Class]
    B --> D[Modules & Routing]
    B --> E[Integration Dataclasses]
    C --> F[Server Settings]
    C --> G[Auth / DB / Cache]
    C --> D
    E --> D
    D --> H[ConfigLoader]
    H --> I[AquiliaServer]
```

The configuration flows from two files:

| File | Responsibility |
|------|---------------|
| `workspace.py` | Workspace orchestration, modules, typed integration dataclasses |
| `workspace.py` (inline) | `AquilaConfig` subclasses — server, auth, database, etc. |

## Environment modes

Aquilia supports three runtime modes set via `AQUILIA_ENV`:

| Mode | Behavior |
|------|----------|
| `dev` | Auto-reload, debug pages, verbose errors, in-memory stores |
| `test` | Isolated, deterministic, no external I/O |
| `prod` | Full security, production optimisations, no debug info |

Set via environment variable or `.env` file:

```bash
export AQUILIA_ENV=dev
```

## Workspace setup (`workspace.py`)

The `Workspace` class from `aquilia.workspace` is the entry point. It is a **fluent builder** that orchestrates modules, integrations, middleware, and runtime settings:

```python
from aquilia.workspace import Workspace, Module
from aquilia.integrations import (
    DatabaseIntegration,
    CacheIntegration,
    MailIntegration,
    AuthIntegration,
    AdminIntegration,
    AdminModules,
)

workspace = (
    Workspace("myapp", version="1.0.0")
    .runtime(mode="dev", host="127.0.0.1", port=8000, reload=True)
    .module(
        Module("users", version="0.1.0")
        .route_prefix("/users")
        .depends_on("auth")
        .tags("core", "users")
    )
    .module(
        Module("auth", version="0.1.0")
        .route_prefix("/auth")
    )
    .integrate(DatabaseIntegration(url="sqlite:///app.db"))
    .integrate(CacheIntegration(backend="redis", redis_url="redis://localhost:6379/0"))
    .integrate(
        AdminIntegration(
            site_title="My Admin",
            modules=AdminModules(monitoring=True, audit=True),
        )
    )
)
```

### Module configuration

`Module` is a fluent builder for workspace-level orchestration metadata. Component declarations (controllers, services, middleware) live in each module's `manifest.py` via `AppManifest`:

```python
Module("payments", version="0.2.0")
    .route_prefix("/payments")
    .depends_on("auth", "users")
    .tags("billing")
    .on_startup("modules.payments.hooks:on_startup")
    .on_shutdown("modules.payments.hooks:on_shutdown")
    .database(
        url="sqlite:///payments.db",
        auto_connect=True,
        auto_create=True,
        auto_migrate=False,
        migrations_dir="migrations",
    )
```

Module configuration fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | `str` | — | Module identifier |
| `version` | `str` | `"0.1.0"` | Semantic version |
| `description` | `str` | `""` | Human-readable description |
| `route_prefix` | `str \| None` | `None` | URL prefix for the module |
| `depends_on` | `list[str]` | `[]` | Modules this module depends on |
| `tags` | `list[str]` | `[]` | Organisational tags |
| `imports` | `list[str]` | `[]` | Cross-module imports |
| `exports` | `list[str]` | `[]` | Cross-module exports |
| `auto_discover` | `bool` | `True` | Convention-based component scanning |
| `on_startup` | `str \| None` | `None` | Dotted path to startup hook |
| `on_shutdown` | `str \| None` | `None` | Dotted path to shutdown hook |

### Middleware chain

Configure the global middleware stack on the workspace:

```python
from aquilia.integrations import MiddlewareChain

workspace.middleware(
    MiddlewareChain()
    .use("aquilia.middleware.ExceptionMiddleware", priority=1)
    .use("aquilia.middleware.RequestIdMiddleware", priority=10)
    .use("aquilia.middleware.LoggingMiddleware", priority=20)
)
```

### Workspace-level helpers

```python
workspace = (
    Workspace("myapp")
    .runtime(mode="prod", workers=4)
    .security(cors_enabled=True, csrf_protection=True, hsts=True)
    .sessions()
    .telemetry(tracing_enabled=True, metrics_enabled=True)
    .database(url="postgresql://user:pass@host/db", auto_migrate=True)
    .tasks(num_workers=8, max_retries=5)
    .i18n(default_locale="en", available_locales=["en", "fr", "de"])
    .storage(
        default="local",
        backends={
            "local": {"backend": "local", "root": "./uploads"},
            "cdn": {"backend": "s3", "bucket": "cdn-bucket"},
        },
    )
    .env_config(BaseEnv)
)
```

## AquilaConfig class DSL

`AquilaConfig` (from `aquilia.pyconfig`) is a class-based config DSL that replaces YAML/JSON files. Define it inline in `workspace.py`:

```python
from aquilia import AquilaConfig, Env, Secret

class BaseEnv(AquilaConfig):
    env = "dev"

    class server(AquilaConfig.Server):
        host = "127.0.0.1"
        port = 8000
        workers = 1

    class auth(AquilaConfig.Auth):
        secret_key = Secret(env="AQ_SECRET_KEY", required=True)
        password_hasher = AquilaConfig.PasswordHasher(algorithm="argon2id")

class DevEnv(BaseEnv):
    env = "dev"

    class server(BaseEnv.server):
        reload = True
        debug = True

    class database(AquilaConfig.Database):
        url = "sqlite:///dev.db"
        echo = True

class ProdEnv(BaseEnv):
    env = "prod"

    class server(BaseEnv.server):
        host = "0.0.0.0"
        workers = Env("WEB_WORKERS", default=4, cast=int)
        ssl_certfile = "/etc/certs/cert.pem"
        ssl_keyfile = "/etc/certs/key.pem"

    class auth(BaseEnv.auth):
        secret_key = Secret(env="AQ_SECRET_KEY", required=True)
        password_hasher = AquilaConfig.PasswordHasher(
            algorithm="argon2id",
            time_cost=3,
            memory_cost=131072,
        )
```

Wire the config into your workspace:

```python
workspace = Workspace("myapp").env_config(BaseEnv)
```

At runtime, Aquilia reads `AQUILIA_ENV` and selects the matching subclass. `DevEnv` is selected when `AQUILIA_ENV=dev`, `ProdEnv` for `prod`, and so on.

### How `to_loader()` works

The `to_loader()` method bridges Python-native config into the `ConfigLoader` that all subsystems consume:

```python
loader = ProdEnv.to_loader()
auth_cfg = loader.get_auth_config()
hasher = loader.build_password_hasher()
```

The `Workspace.env_config()` hook calls this automatically during server startup.

### Dotenv loading

`AquilaConfig` provides a `Dotenv` nested class to control `.env` file loading:

```python
class MyConfig(AquilaConfig):
    class dotenv(AquilaConfig.Dotenv):
        files = [".env", ".env.local", ".env.{env}"]
        auto_load = True
        override = False
        interpolate = True
        strict = False  # If True, all files are required
```

The `{env}` placeholder is replaced by the resolved environment name. By default, Aquilia searches: `.env`, `.env.example`, `.env.defaults`, `.env.local`, `.env.{env}`, `.env.{env}.local`, `config/.env`, and `config/.env.{env}`.

You can also use single-file syntax:

```python
class dotenv(AquilaConfig.Dotenv):
    file = ".env.production"
```

And with per-file required semantics:

```python
class dotenv(AquilaConfig.Dotenv):
    files = [
        AquilaConfig.EnvFile(".env", required=True),
        AquilaConfig.EnvFile(".env.local", required=False),
    ]
```

## Env and Secret values

`Env` and `Secret` are special value types that resolve at read time from environment variables.

### Env — environment variable bindings

```python
class server(AquilaConfig.Server):
    host = Env("AQ_HOST", default="127.0.0.1")
    port = Env("AQ_PORT", default=8000, cast=int)
    workers = Env("AQ_WORKERS", default=4, cast=int)
    debug = Env("AQ_DEBUG", default=False, cast=bool)
```

Type casting:
- `cast=int` — integer parsing
- `cast=float` — float parsing
- `cast=bool` — supports `"1"`, `"true"`, `"yes"`, `"on"` (truthy) and `"0"`, `"false"`, `"no"`, `"off"` (falsy)
- `cast=<callable>` — custom cast function
- No `cast` — auto-casts: tries int → float → JSON → str

`Env` values are resolved lazily at read time and cached per-request.

### Secret — sensitive values

`Secret` never leaks values into `repr()` or logs. It reads from the environment with `reveal()`:

```python
class auth(AquilaConfig.Auth):
    secret_key = Secret(env="AQ_SECRET_KEY", required=True)
    db_password = Secret(env="DB_PASSWORD", default="devpassword")
    api_key = Secret(value="sk-dev-abc123")  # inline only for dev
```

Resolution priority:
1. `env` — named environment variable
2. `value` — literal value at definition time
3. `default` — fallback

If `required=True` and no value is found, a `ConfigMissingFault` is raised at startup.

## Built-in configuration sections

### Server

```python
class server(AquilaConfig.Server):
    # Core
    host = "127.0.0.1"
    port = 8000
    workers = 1
    mode = "dev"
    debug = False

    # Reload / Development
    reload = False
    reload_dirs = None
    reload_delay = 0.25

    # Protocol / Implementation
    http = "auto"       # "auto" | "h11" | "httptools"
    ws = "auto"         # "auto" | "wsproto" | "websockets" | "none"
    lifespan = "auto"   # "auto" | "on" | "off"

    # Timeouts (seconds)
    timeout_keep_alive = 5
    timeout_graceful_shutdown = None

    # Limits
    backlog = 2048
    limit_concurrency = None
    limit_max_requests = None

    # Proxy / Headers
    proxy_headers = True
    forwarded_allow_ips = None

    # Logging
    access_log = True
    log_level = None

    # WebSocket
    ws_max_size = 16_777_216  # 16 MiB
    ws_ping_interval = 20.0

    # TLS / SSL
    ssl_keyfile = None
    ssl_certfile = None
    ssl_ca_certs = None
    ssl_ciphers = "TLSv1"
```

### Auth

```python
class auth(AquilaConfig.Auth):
    enabled = True
    store_type = "memory"         # "memory" | "sqlite" | "postgres"
    secret_key = None             # Required in production
    algorithm = "HS256"           # HS256 | HS384 | HS512 | RS256 | ES256 | EdDSA
    issuer = "aquilia"
    audience = "aquilia-app"
    access_token_ttl_minutes = 60
    refresh_token_ttl_days = 30
    require_auth_by_default = False
    password_hasher = None        # AquilaConfig.PasswordHasher instance
```

Zero-dependency algorithms: `HS256`, `HS384`, `HS512` (stdlib `hmac` + `hashlib`).
Asymmetric algorithms: `RS256`, `ES256`, `EdDSA` — require `pip install cryptography`.

### PasswordHasher

```python
# Argon2id (recommended) — requires pip install argon2-cffi
AquilaConfig.PasswordHasher.argon2id(
    time_cost=3, memory_cost=131072, parallelism=4
)

# scrypt (stdlib, no deps)
AquilaConfig.PasswordHasher.scrypt(n=32768, r=8, p=1)

# bcrypt — requires pip install bcrypt
AquilaConfig.PasswordHasher.bcrypt(rounds=12)

# PBKDF2-HMAC-SHA512 (stdlib, no deps)
AquilaConfig.PasswordHasher.pbkdf2_sha512(iterations=210000)
```

### Database

```python
class database(AquilaConfig.Database):
    url = "sqlite:///db.sqlite3"
    auto_connect = True
    auto_create = True
    auto_migrate = False
    pool_size = 5
    echo = False
    migrations_dir = "migrations"
```

### Cache

```python
class cache(AquilaConfig.Cache):
    backend = "memory"          # "memory" | "redis" | "composite" | "null"
    default_ttl = 300
    max_size = 10000
    eviction_policy = "lru"     # "lru" | "lfu" | "fifo" | "ttl" | "random"
    namespace = "default"
    key_prefix = "aq:"
    redis_url = "redis://localhost:6379/0"
```

### Sessions

```python
class sessions(AquilaConfig.Sessions):
    enabled = False
    store_type = "memory"       # "memory" | "file" | "redis"
    cookie_name = "aquilia_session"
    cookie_secure = True
    cookie_httponly = True
    cookie_samesite = "lax"
    ttl_days = 7
    idle_timeout_minutes = 30
```

### Mail

```python
class mail(AquilaConfig.Mail):
    enabled = False
    default_from = "noreply@localhost"
    console_backend = False
    require_tls = True
    retry_max_attempts = 5
```

### Security

```python
class security(AquilaConfig.Security):
    enabled = False
    cors_enabled = False
    csrf_protection = False
    helmet_enabled = False
    rate_limiting = False
    https_redirect = False
    hsts = False
```

### Logging

```python
class logging(AquilaConfig.Logging):
    level = "INFO"
    colorize = True
    slow_threshold_ms = 1000.0
    include_headers = False
```

### I18n

```python
class i18n(AquilaConfig.I18n):
    enabled = False
    default_locale = "en"
    available_locales = ["en"]
    fallback_locale = "en"
    catalog_dirs = ["locales"]
    catalog_format = "json"
```

### Signing

```python
class signing(AquilaConfig.Signing):
    secret = Secret(env="AQ_SECRET_KEY", required=True)
    fallback_secrets = []        # Key rotation
    algorithm = "HS256"          # HS256 | HS384 | HS512
    salt = "aquilia.signing"
    session_salt = "aquilia.sessions"
    csrf_salt = "aquilia.csrf"
    activation_salt = "aquilia.activation"
    cache_salt = "aquilia.cache"
```

### Render (PaaS deployment)

```python
class render(AquilaConfig.Render):
    enabled = True
    service_name = "my-api"
    region = "oregon"           # oregon | frankfurt | ohio | virginia | singapore
    plan = "starter"            # free | starter | standard | pro | pro_plus | pro_max | pro_ultra
    num_instances = 1
    image = Env("RENDER_IMAGE", default="ghcr.io/org/app:latest")
    health_path = "/_health"
    auto_deploy = "no"
```

## Typed integration dataclasses

As an alternative to `AquilaConfig` sections, you can use typed integration dataclasses from `aquilia.integrations`:

```python
from aquilia.integrations import (
    DatabaseIntegration,
    CacheIntegration,
    AuthIntegration,
    MailIntegration,
    SmtpProvider,
    MailAuth,
    CorsIntegration,
    CspIntegration,
    RateLimitIntegration,
    CsrfIntegration,
    OpenAPIIntegration,
    SessionIntegration,
    TasksIntegration,
    StorageIntegration,
    TemplatesIntegration,
    I18nIntegration,
    VersioningIntegration,
    StaticFilesIntegration,
    AdminIntegration,
)
```

These are passed via `workspace.integrate(...)`. See the [Integrations guide](integrations.md) for detailed coverage.

## Accessing configuration at runtime

From a controller or service, get configuration through dependency injection or the `Env` descriptor:

```python
from aquilia import Env

api_url = Env("EXTERNAL_API_URL", default="https://api.example.com").resolve()
```

Use `ConfigLoader` for structured access:

```python
loader = BaseEnv.from_env_var().to_loader()
db_config = loader.get_database_config()
cache_config = loader.get_cache_config()
```

## Caching and invalidation

`AquilaConfig.to_dict()` results are cached at the class level for performance. In tests, invalidate the cache:

```python
MyConfig.invalidate_cache()
# or globally:
AquilaConfig.clear_all_caches()
```