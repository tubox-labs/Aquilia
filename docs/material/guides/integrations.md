# Integrations Guide

Aquilia provides 14+ typed integration dataclasses in `aquilia.integrations`. Each is a frozen dataclass with `__post_init__` validation, IDE autocompletion, and a `.to_dict()` method. They replace the legacy `Integration` monolithic class.

## Configuration pattern

All integrations follow the same pattern:

```python
from aquilia.workspace import Workspace
from aquilia.integrations import DatabaseIntegration

workspace = (
    Workspace("myapp")
    .integrate(DatabaseIntegration(url="sqlite:///app.db"))
)
```

You can also use the workspace-level shorthand methods (`.database()`, `.tasks()`, `.storage()`, `.i18n()`) which delegate to the corresponding integration dataclass.

---

## Database Integration

```python
from aquilia.integrations import DatabaseIntegration

workspace.integrate(
    DatabaseIntegration(
        url="sqlite:///app.db",        # Connection URL
        auto_connect=True,              # Connect on startup
        auto_create=True,               # Create tables on startup
        auto_migrate=False,             # Run pending migrations
        migrations_dir="migrations",    # Migration files location
        pool_size=5,                    # Connection pool size
        echo=False,                     # Log SQL statements
        model_paths=[],                 # Explicit model paths
        scan_dirs=["models"],           # Directories to scan for models
    )
)
```

Type-specific config objects are also supported:

```python
from aquilia.db.configs import PostgresConfig

workspace.integrate(
    DatabaseIntegration(
        config=PostgresConfig(
            host="localhost",
            port=5432,
            name="myapp",
            user="app",
            password_env="DB_PASSWORD",
        ),
        pool_size=10,
    )
)
```

---

## Auth Integration

```python
from aquilia.integrations import AuthIntegration

workspace.integrate(
    AuthIntegration(
        enabled=True,
        store_type="memory",          # "memory" | "sqlite" | "postgres"
        secret_key="super-secret",     # Required in production
        algorithm="HS256",             # HS256 | HS384 | HS512 | RS256 | ES256 | EdDSA
        issuer="aquilia",
        audience="aquilia-app",
        access_token_ttl_minutes=60,
        refresh_token_ttl_days=30,
        require_auth_by_default=False,
    )
)
```

Zero-dependency algorithms (`HS256`, `HS384`, `HS512`) work out of the box. For asymmetric algorithms (`RS256`, `ES256`, `EdDSA`), install `cryptography`.

---

## Session Integration

```python
from aquilia.integrations import SessionIntegration

workspace.integrate(
    SessionIntegration(
        enabled=True,
        policy=None,    # Auto-creates SessionPolicy.for_web_users()
        store=None,     # Auto-creates MemoryStore.development_focused()
        transport=None, # Auto-creates CookieTransport.with_aquilia_defaults()
    )
)
```

Session integration auto-provisions sensible defaults when `policy`, `store`, or `transport` are left as `None`.

---

## Cache Integration

```python
from aquilia.integrations import CacheIntegration

workspace.integrate(
    CacheIntegration(
        backend="redis",                  # "memory" | "redis" | "composite" | "null"
        default_ttl=300,                  # Default TTL in seconds
        max_size=10000,                   # Memory backend: max entries
        eviction_policy="lru",            # "lru" | "lfu" | "fifo" | "ttl" | "random"
        namespace="default",
        key_prefix="aq:",
        serializer="json",                # "json" | "pickle"
        redis_url="redis://localhost:6379/0",
        redis_max_connections=10,

        # Two-tier cache (composite backend)
        l1_max_size=1000,                 # L1 memory cache size
        l1_ttl=60,                        # L1 TTL in seconds
        l2_backend="redis",               # L2 remote backend

        # Middleware
        middleware_enabled=False,
        middleware_default_ttl=60,

        enabled=True,
    )
)
```

**Valid backends**: `memory`, `redis`, `composite`, `null`.
**Valid eviction policies**: `lru`, `lfu`, `fifo`, `ttl`, `random`.

---

## Mail Integration

```python
from aquilia.integrations import (
    MailIntegration, MailAuth,
    SmtpProvider, SesProvider, SendGridProvider,
    ConsoleProvider, FileProvider,
)

workspace.integrate(
    MailIntegration(
        default_from="noreply@myapp.com",
        default_reply_to="support@myapp.com",
        subject_prefix="[MyApp] ",
        auth=MailAuth.plain("smtp-user", password_env="SMTP_PASS"),
        providers=[
            SmtpProvider(
                name="primary",
                host="smtp.myapp.com",
                port=587,
                use_tls=True,
                pool_size=3,
            ),
        ],
        console_backend=False,
        retry_max_attempts=5,
        retry_base_delay=1.0,
        dkim_enabled=True,
        dkim_domain="myapp.com",
        dkim_selector="aquilia",
        require_tls=True,
        rate_limit_global=1000,       # Global sends per minute
        rate_limit_per_domain=100,    # Per-domain sends per minute
        enabled=True,
    )
)
```

### Mail authentication methods

```python
# SMTP PLAIN / LOGIN
MailAuth.plain("username", password_env="SMTP_PASS")

# API key (SendGrid, Mailgun, Postmark)
MailAuth.api_key(env="SENDGRID_API_KEY")

# AWS SES
MailAuth.aws_ses(
    access_key_id_env="AWS_ACCESS_KEY",
    secret_access_key_env="AWS_SECRET_KEY",
    region="eu-west-1",
)

# OAuth2 (Gmail, Microsoft 365)
MailAuth.oauth2(
    client_id="my-client",
    client_secret_env="OAUTH_SECRET",
    token_url="https://oauth2.googleapis.com/token",
)

# NTLM (Windows)
MailAuth.ntlm("username", domain="CORP")

# No authentication (open relay, dev only)
MailAuth.anonymous()
```

### Mail providers

```python
# SMTP / STARTTLS
SmtpProvider(
    name="primary",
    host="smtp.myapp.com",
    port=587,
    use_tls=True,
    pool_size=3,
    auth=MailAuth.plain("user", password_env="SMTP_PASS"),
)

# AWS SES
SesProvider(
    name="ses-prod",
    region="eu-west-1",
    configuration_set="my-config",
    auth=MailAuth.aws_ses(access_key_id_env="AWS_KEY"),
)

# SendGrid Web API v3
SendGridProvider(
    auth=MailAuth.api_key(env="SENDGRID_API_KEY"),
    sandbox_mode=False,
    click_tracking=True,
    open_tracking=True,
    categories=["transactional"],
)

# Console (dev only)
ConsoleProvider()

# File / .eml (testing & audit)
FileProvider(output_dir="/tmp/aquilia_mail", max_files=10000)
```

---

## Admin Integration

```python
from aquilia.integrations import (
    AdminIntegration, AdminModules, AdminAudit,
    AdminMonitoring, AdminSidebar, AdminSecurity,
    AdminContainers, AdminPods,
)

workspace.integrate(
    AdminIntegration(
        url_prefix="/admin",
        site_title="My App Admin",
        site_header="My App Administration",
        auto_discover=True,
        list_per_page=25,
        theme="auto",
        modules=AdminModules(monitoring=True, audit=True),
        audit=AdminAudit(
            enabled=True,
            max_entries=50_000,
            log_logins=True,
            log_views=False,
            log_searches=True,
        ),
        monitoring=AdminMonitoring(
            enabled=True,
            metrics=["cpu", "memory", "disk", "network"],
            refresh_interval=15,
        ),
        security=AdminSecurity(
            csrf_enabled=True,
            rate_limit_max_attempts=5,
            password_min_length=12,
            progressive_lockout=True,
        ),
        sidebar=AdminSidebar(security=True, devtools=False),
        containers=AdminContainers(
            docker_host="unix:///var/run/docker.sock",
            log_tail=500,
        ),
        pods=AdminPods(
            namespace="production",
            refresh_interval=15,
        ),
    )
)
```

`AdminModules` available flags (all `True` by default unless noted):

| Flag | Default | Description |
|------|---------|-------------|
| `dashboard` | `True` | Dashboard overview |
| `orm` | `True` | ORM / model browser |
| `migrations` | `True` | Migration management |
| `config` | `True` | Configuration view |
| `workspace` | `True` | Workspace explorer |
| `permissions` | `True` | Permission management |
| `admin_users` | `True` | Admin user management |
| `profile` | `True` | Profile settings |
| `api_keys` | `True` | API key management |
| `preferences` | `True` | User preferences |
| `monitoring` | `False` | Monitoring dashboard (opt-in) |
| `audit` | `False` | Audit trail (opt-in) |
| `containers` | `False` | Docker containers (opt-in) |
| `pods` | `False` | Kubernetes pods (opt-in) |
| `tasks` | `False` | Background tasks (opt-in) |
| `errors` | `False` | Error log (opt-in) |
| `storage` | `False` | Storage management (opt-in) |
| `mailer` | `False` | Mail management (opt-in) |
| `testing` | `False` | Testing tools (opt-in) |
| `provider` | `False` | Provider integration (opt-in) |

---

## Tasks Integration

```python
from aquilia.integrations import TasksIntegration

workspace.integrate(
    TasksIntegration(
        backend="memory",           # "memory" (more backends planned)
        num_workers=4,              # Number of concurrent workers
        default_queue="default",
        max_retries=3,              # Maximum retry attempts
        retry_delay=1.0,            # Base retry delay in seconds
        retry_backoff=2.0,          # Exponential backoff multiplier
        retry_max_delay=300.0,      # Maximum retry delay in seconds
        default_timeout=300.0,      # Default task timeout
        auto_start=True,            # Start workers on server startup
        dead_letter_max=1000,       # Max dead letter queue entries
        scheduler_tick=15.0,        # Scheduler polling interval
        cleanup_interval=300.0,     # Completed job cleanup interval
        cleanup_max_age=3600.0,     # Max age before cleanup
        enabled=True,
    )
)
```

---

## Storage Integration

```python
from aquilia.integrations import StorageIntegration
from aquilia.storage import LocalConfig, S3Config

workspace.integrate(
    StorageIntegration(
        default="local",
        backends={
            "local": LocalConfig(root="./uploads"),
            "cdn": S3Config(
                bucket="my-cdn-bucket",
                region="us-east-1",
                access_key_id_env="AWS_ACCESS_KEY",
                secret_access_key_env="AWS_SECRET_KEY",
            ),
        },
        enabled=True,
    )
)
```

Storage backends (`aquilia.storage`):

| Backend | Config Class | Description |
|---------|-------------|-------------|
| Local | `LocalConfig` | Local filesystem |
| Memory | `MemoryConfig` | In-memory (test/dev) |
| S3 | `S3Config` | AWS S3 |
| GCS | `GCSConfig` | Google Cloud Storage |
| Azure Blob | `AzureBlobConfig` | Azure Blob Storage |
| SFTP | `SFTPConfig` | SFTP remote server |
| Composite | `CompositeConfig` | Multi-backend aggregation |

---

## Templates Integration

```python
from aquilia.integrations import TemplatesIntegration

# Direct construction
workspace.integrate(
    TemplatesIntegration(
        search_paths=["templates", "shared/partials"],
        cache="memory",               # "memory" | "none"
        sandbox=True,                 # Sandboxed Jinja2
        sandbox_policy="strict",      # "strict" | "permissive"
        precompile=False,             # Precompile templates on startup
        enabled=True,
    )
)

# Fluent builder
workspace.integrate(
    TemplatesIntegration
        .source("templates")
        .cached()
        .secure(strict=True)
)
```

---

## Security Integrations

### CORS

```python
from aquilia.integrations import CorsIntegration

workspace.integrate(
    CorsIntegration(
        allow_origins=["https://example.com", "https://app.example.com"],
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
        allow_headers=["accept", "content-type", "authorization"],
        expose_headers=[],
        allow_credentials=True,
        max_age=600,
        enabled=True,
    )
)
```

### CSP (Content Security Policy)

```python
from aquilia.integrations import CspIntegration

workspace.integrate(
    CspIntegration(
        policy={
            "default-src": ["'self'"],
            "script-src": ["'self'", "https://cdn.example.com"],
            "style-src": ["'self'", "'unsafe-inline'"],
        },
        report_only=False,   # True = report-only mode
        nonce=True,          # Generate script nonces
        preset="strict",     # Built-in preset
        enabled=True,
    )
)
```

### Rate Limiting

```python
from aquilia.integrations import RateLimitIntegration

workspace.integrate(
    RateLimitIntegration(
        limit=200,                       # Requests per window
        window=60,                       # Time window in seconds
        algorithm="sliding_window",     # Rate limit algorithm
        per_user=False,                 # Per-user rate limiting
        burst=50,                       # Burst allowance
        exempt_paths=["/health", "/healthz", "/ready"],
        enabled=True,
    )
)
```

### CSRF

```python
from aquilia.integrations import CsrfIntegration

workspace.integrate(
    CsrfIntegration(
        secret_key="my-csrf-secret",
        token_length=32,
        header_name="X-CSRF-Token",
        cookie_name="_csrf_cookie",
        cookie_secure=True,
        cookie_samesite="Lax",
        cookie_max_age=3600,
        safe_methods=["GET", "HEAD", "OPTIONS", "TRACE"],
        exempt_paths=["/api/webhooks/stripe"],
        trust_ajax=True,
        rotate_token=False,
        failure_status=403,
        enabled=True,
    )
)
```

---

## OpenAPI Integration

```python
from aquilia.integrations import OpenAPIIntegration

workspace.integrate(
    OpenAPIIntegration(
        title="My API",
        version="2.0.0",
        description="The API for My App",
        terms_of_service="https://example.com/tos",
        contact_name="API Support",
        contact_email="support@example.com",
        contact_url="https://example.com/support",
        license_name="MIT",
        license_url="https://opensource.org/licenses/MIT",
        servers=[
            {"url": "https://api.example.com/v2", "description": "Production"},
        ],
        docs_path="/docs",                  # Swagger UI
        openapi_json_path="/openapi.json",  # Raw spec
        redoc_path="/redoc",               # ReDoc UI
        include_internal=False,            # Include internal endpoints
        group_by_module=True,              # Group endpoints by module
        infer_request_body=True,           # Auto-detect request schemas
        infer_responses=True,              # Auto-detect response schemas
        detect_security=True,              # Auto-detect auth requirements
        swagger_ui_theme="dark",
        swagger_ui_config={"deepLinking": True},
        enabled=True,
    )
)
```

---

## I18n Integration

```python
from aquilia.integrations import I18nIntegration

workspace.integrate(
    I18nIntegration(
        default_locale="en",
        available_locales=["en", "fr", "de", "ja"],
        fallback_locale="en",
        catalog_dirs=["locales"],
        catalog_format="json",
        missing_key_strategy="log_and_key",   # "log_and_key" | "log" | "strict"
        auto_reload=False,                    # Reload catalogs on change (dev)
        auto_detect=True,                     # Auto-detect from request
        cookie_name="aq_locale",
        query_param="lang",
        path_prefix=False,
        resolver_order=["query", "cookie", "header"],  # Detection order
        enabled=True,
    )
)
```

---

## Versioning Integration

```python
from aquilia.integrations import VersioningIntegration

workspace.integrate(
    VersioningIntegration(
        strategy="composite",          # "url" | "header" | "query" | "media_type" | "channel" | "composite"
        versions=["1.0", "2.0", "2.1"],
        default_version="2.0",
        require_version=False,         # Require version on all requests
        header_name="X-API-Version",   # For strategy="header"
        query_param="api_version",     # For strategy="query"
        url_prefix="v",                # For strategy="url"
        channels={"stable": "2.0", "preview": "2.1"},
        channel_header="X-API-Channel",
        negotiation_mode="exact",      # "exact" | "compatible" | "best_match" | "nearest" | "latest"
        include_version_header=True,   # Add X-API-Version to responses
        response_header_name="X-API-Version",
        include_supported_versions_header=True,
        neutral_paths=["/_health", "/openapi.json", "/docs", "/redoc"],
        sunset_schedules={
            "1.0": {
                "sunset_date": "2026-06-01",
                "deprecation_date": "2025-12-01",
                "link": "https://docs.example.com/migration-v2",
            },
        },
        enabled=True,
    )
)
```

**Valid strategies**:
- `url` — `/v2/users/`
- `header` — `X-API-Version: 2.0`
- `query` — `?api_version=2.0`
- `media_type` — `Accept: application/json; version=2.0`
- `channel` — `X-API-Channel: stable`
- `composite` — Combines multiple resolvers

---

## Static Files Integration

```python
from aquilia.integrations import StaticFilesIntegration

workspace.integrate(
    StaticFilesIntegration(
        directories={
            "/static": "static",
            "/media": "uploads",
        },
        cache_max_age=86400,      # Cache-Control max-age in seconds
        immutable=False,          # Use immutable caching
        etag=True,                # Generate ETag headers
        gzip=True,                # Pre-compressed .gz files
        brotli=True,              # Pre-compressed .br files
        memory_cache=True,        # In-memory cache for hot files
        html5_history=False,      # Serve index.html for SPA routing
        enabled=True,
    )
)
```

---

## Other Integrations

### Logging Integration

```python
from aquilia.integrations import LoggingIntegration

workspace.integrate(
    LoggingIntegration(
        format="%(method)s %(path)s %(status)s %(duration_ms).1fms",
        level="INFO",
        slow_threshold_ms=500.0,     # Log warnings when request exceeds threshold
        skip_paths=["/health", "/healthz", "/ready", "/metrics"],
        include_headers=False,
        include_query=True,
        include_user_agent=False,
        log_request_body=False,
        log_response_body=False,
        colorize=True,
        enabled=True,
    )
)
```

### DI Integration

```python
from aquilia.integrations import DiIntegration

workspace.integrate(
    DiIntegration(auto_wire=True, scan_packages=["modules"])
)
```

### Fault Handling Integration

```python
from aquilia.integrations import FaultHandlingIntegration

workspace.integrate(
    FaultHandlingIntegration(default_strategy="propagate")
)
```

### Render Deployment Integration

```python
from aquilia.integrations import RenderIntegration

workspace.integrate(
    RenderIntegration(
        service_name="my-api-prod",
        region="frankfurt",
        plan="standard",
        num_instances=2,
        health_path="/_health",
        auto_deploy="yes",
    )
)
```

---

## Migration from legacy Integration

The legacy `Integration` class still works:

```python
from aquilia import Integration

workspace.integrate(Integration.database(url="sqlite:///app.db"))
workspace.integrate(Integration.admin(monitoring=True))
```

But prefer the typed dataclasses for IDE support, validation, and readability.