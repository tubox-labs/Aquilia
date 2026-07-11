import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { Plug, Shield, Database, Mail, Cpu, Globe, Lock, Layers, ArrowRight, Activity, Zap } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function ConfigIntegrations() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const txt = isDark ? 'text-gray-300' : 'text-gray-600'
  const subtxt = isDark ? 'text-gray-400' : 'text-gray-500'
  const head = isDark ? 'text-white' : 'text-gray-900'
  const divider = isDark ? 'divide-white/5' : 'divide-gray-100'
  const thead = isDark ? 'bg-zinc-800/80' : 'bg-gray-50'
  const th = isDark ? 'text-gray-300' : 'text-gray-700'
  const hov = isDark ? 'hover:bg-white/5' : 'hover:bg-gray-50'
  const border = isDark ? 'border-white/10' : 'border-gray-200'

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-10">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-aquilia-500/30 to-aquilia-500/10 flex items-center justify-center shadow-lg shadow-aquilia-500/10">
            <Plug className="w-5 h-5 text-aquilia-400" />
          </div>
          <div>
            <h1 className={`text-4xl ${head}`}>
              <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
                Integrations
                <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
              </span>
            </h1>
            <p className={`text-sm ${subtxt}`}>aquilia.integrations — typed subsystem configuration dataclasses</p>
          </div>
        </div>

        <p className={`text-lg leading-relaxed ${txt}`}>
          Every subsystem in Aquilia is configured through a typed <code>@dataclass</code> — one class per concern. Each integration is passed to <code>Workspace.integrate()</code>, has <code>__post_init__</code> validation, full IDE autocompletion, and a <code>.to_dict()</code> method that serialises into the format the runtime expects.
        </p>
      </div>

      {/* How to use */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Layers className="w-5 h-5 text-aquilia-400" />
          How integrations work
        </h2>
        <p className={`mb-4 ${txt}`}>
          Import the typed dataclasses from <code>aquilia.integrations</code> and pass instances to <code>.integrate()</code>. The <DocTerm id="config.workspace">Workspace</DocTerm> builder inspects the <code>_integration_type</code> field on each dataclass to route it to the correct subsystem.
        </p>
        <CodeBlock language="python" code={`from aquilia import Workspace
from aquilia.integrations import (
    DatabaseIntegration,
    AuthIntegration,
    CacheIntegration,
    SessionIntegration,
    OpenAPIIntegration,
    MailIntegration, SmtpProvider, MailAuth,
    TasksIntegration,
    CorsIntegration,
    CsrfIntegration,
    RateLimitIntegration,
    CspIntegration,
    TemplatesIntegration,
    StorageIntegration,
    I18nIntegration,
    LoggingIntegration,
    StaticFilesIntegration,
    VersioningIntegration,
    AdminIntegration, AdminModules,
)

workspace = (
    Workspace("myapp")
    .integrate(DatabaseIntegration(url="sqlite:///app.db"))
    .integrate(AuthIntegration(secret_key="my-secret", access_token_ttl_minutes=60))
    .integrate(OpenAPIIntegration(title="My API", version="1.0.0"))
    .integrate(CorsIntegration(allow_origins=["https://myapp.com"]))
    # ... more integrations
)`} />
      </section>

      {/* Quick-reference table */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>All available integrations</h2>
        <div className={`rounded-xl border overflow-hidden ${border}`}>
          <table className="w-full text-sm">
            <thead><tr className={thead}>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>Class</th>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>Module</th>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>Purpose</th>
            </tr></thead>
            <tbody className={`divide-y ${divider}`}>
              {[
                ['DatabaseIntegration', 'database.py', 'Database — URL, pool, auto-migrate, model scanning'],
                ['AuthIntegration', 'auth.py', 'JWT auth — secret key, algorithm, token TTLs, store'],
                ['SessionIntegration', 'sessions.py', 'Sessions — policy, store backend, transport'],
                ['CacheIntegration', 'cache.py', 'Cache — memory / redis / composite L1+L2'],
                ['MailIntegration', 'mail.py', 'Mail — SMTP / SES / SendGrid / console providers'],
                ['TasksIntegration', 'tasks.py', 'Background tasks — workers, queue, retry, scheduler'],
                ['OpenAPIIntegration', 'openapi.py', 'OpenAPI spec generation and Swagger UI / ReDoc'],
                ['CorsIntegration', 'security.py', 'CORS — origins, methods, headers, credentials, max-age'],
                ['CsrfIntegration', 'security.py', 'CSRF — token header/cookie, exemptions, rotation'],
                ['CspIntegration', 'security.py', 'Content-Security-Policy — policy dict, nonce, preset'],
                ['RateLimitIntegration', 'security.py', 'Rate limiting — limit, window, per-user, burst, algorithm'],
                ['TemplatesIntegration', 'templates.py', 'Jinja2 templates — dirs, globals, bytecode cache'],
                ['StorageIntegration', 'storage.py', 'File storage — local / S3 / GCS / Azure / SFTP'],
                ['StaticFilesIntegration', 'static.py', 'Static file serving — dirs, cache, compression'],
                ['I18nIntegration', 'i18n.py', 'Internationalisation — locale, catalog, extraction'],
                ['LoggingIntegration', 'logging_cfg.py', 'Structured request/response logging'],
                ['VersioningIntegration', 'versioning_cfg.py', 'API versioning — URL prefix / header / content-type'],
                ['AdminIntegration', 'admin.py', 'Admin panel — site title, modules, security, sidebar'],
                ['DiIntegration', 'simple.py', 'Dependency injection — auto-wiring settings'],
                ['RoutingIntegration', 'simple.py', 'Routing configuration — strategy, trailing slash'],
                ['FaultHandlingIntegration', 'simple.py', 'Fault handling defaults — error format, logging'],
                ['RegistryIntegration', 'simple.py', 'Global component registry'],
                ['SerializersIntegration', 'simple.py', 'Global serializer settings'],
                ['PatternsIntegration', 'simple.py', 'Pattern matching configuration'],
              ].map(([cls, module, purpose], i) => (
                <tr key={i} className={hov}>
                  <td className="px-4 py-3 font-mono text-xs text-aquilia-400 whitespace-nowrap">{cls}</td>
                  <td className={`px-4 py-3 font-mono text-xs ${subtxt} whitespace-nowrap`}>{module}</td>
                  <td className={`px-4 py-3 text-xs ${txt}`}>{purpose}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* DatabaseIntegration */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Database className="w-5 h-5 text-aquilia-400" />
          DatabaseIntegration
        </h2>
        <p className={`mb-4 ${txt}`}>
          Accepts either a <code>url</code> string or a typed config object (<code>SqliteConfig</code>, <code>PostgresConfig</code>). Controls the connection pool, auto-migration, and model scanning directories.
        </p>
        <CodeBlock language="python" code={`from aquilia.integrations import DatabaseIntegration
from aquilia.pyconfig import Env

# ── URL-based (simplest) ──────────────────────────────────────────────────
workspace.integrate(DatabaseIntegration(
    url="sqlite:///app.db",         # or Env("DATABASE_URL", required=True)
))

# ── Production Postgres ───────────────────────────────────────────────────
workspace.integrate(DatabaseIntegration(
    url=Env("DATABASE_URL", required=True),
    auto_connect=True,
    auto_create=True,
    auto_migrate=True,              # runs migrations at startup
    migrations_dir="migrations",
    pool_size=20,
    echo=False,                     # True → logs every SQL statement
    scan_dirs=["models"],           # sub-dirs to scan for Model subclasses
))

# ── Typed config object ───────────────────────────────────────────────────
from aquilia.db.configs import PostgresConfig
workspace.integrate(DatabaseIntegration(
    config=PostgresConfig(
        host="db.internal",
        port=5432,
        name="myapp_prod",
        user="app",
        password=Env("DB_PASSWORD", required=True),
    ),
    pool_size=10,
    auto_migrate=True,
))`} />

        <div className={`mt-4 rounded-xl border overflow-hidden ${border}`}>
          <table className="w-full text-sm">
            <thead><tr className={thead}><th className={`text-left px-4 py-2 font-semibold text-xs ${th}`}>Field</th><th className={`text-left px-4 py-2 font-semibold text-xs ${th}`}>Default</th><th className={`text-left px-4 py-2 font-semibold text-xs ${th}`}>Description</th></tr></thead>
            <tbody className={`divide-y ${divider}`}>
              {[
                ['url', 'None', 'SQLAlchemy connection URL string — mutually exclusive with config'],
                ['config', 'None', 'Typed database config object (PostgresConfig, SqliteConfig, etc.)'],
                ['auto_connect', 'True', 'Connect to the database at server startup'],
                ['auto_create', 'True', 'Create the database schema if it does not exist'],
                ['auto_migrate', 'False', 'Apply pending migrations at startup'],
                ['migrations_dir', '"migrations"', 'Directory where migration files are stored'],
                ['pool_size', '5', 'Connection pool size'],
                ['echo', 'False', 'Log every SQL statement to stdout'],
                ['scan_dirs', '["models"]', 'Subdirectories to scan for Model subclasses'],
              ].map(([f, d, desc], i) => <tr key={i} className={hov}><td className="px-4 py-2 font-mono text-xs text-aquilia-400">{f}</td><td className={`px-4 py-2 font-mono text-xs ${subtxt}`}>{d}</td><td className={`px-4 py-2 text-xs ${txt}`}>{desc}</td></tr>)}
            </tbody>
          </table>
        </div>
      </section>

      {/* AuthIntegration */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Lock className="w-5 h-5 text-aquilia-400" />
          AuthIntegration
        </h2>
        <p className={`mb-4 ${txt}`}>
          Configures JWT token signing, store backend, and session security policy.
        </p>
        <CodeBlock language="python" code={`from aquilia.integrations import AuthIntegration
from aquilia.pyconfig import Secret

workspace.integrate(AuthIntegration(
    enabled=True,
    store_type="memory",            # "memory" | "redis" | "database"
    secret_key=Secret(env="AQ_SECRET_KEY", required=True).reveal(),
    algorithm="HS256",              # HS256/HS384/HS512 (stdlib) or RS256/ES256/EdDSA (cryptography pkg)
    issuer="myapp",
    audience="myapp-api",
    access_token_ttl_minutes=60,
    refresh_token_ttl_days=30,
    require_auth_by_default=False,  # True → all routes require JWT unless @public
))`} />
      </section>

      {/* SessionIntegration */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Shield className="w-5 h-5 text-aquilia-400" />
          SessionIntegration
        </h2>
        <p className={`mb-4 ${txt}`}>
          Composable session config — a policy object defines TTL and idle behaviour, a store backend determines persistence, and a transport handles cookie or header delivery. All three default to sensible values when omitted.
        </p>
        <CodeBlock language="python" code={`from aquilia.integrations import SessionIntegration
from aquilia.sessions import SessionPolicy, MemoryStore, CookieTransport

# ── Minimal (all defaults) ────────────────────────────────────────────────
workspace.integrate(SessionIntegration())

# ── Custom policy, store, and transport ─────────────────────────────────
workspace.integrate(SessionIntegration(
    enabled=True,
    policy=SessionPolicy.for_web_users().lasting(days=14),
    store=MemoryStore.with_capacity(50_000),
    transport=CookieTransport.secure_defaults(),
))

# ── Redis-backed sessions ─────────────────────────────────────────────────
from aquilia.sessions import RedisStore
workspace.integrate(SessionIntegration(
    policy=SessionPolicy.for_web_users().lasting(days=30),
    store=RedisStore(url="redis://localhost:6379/1"),
    transport=CookieTransport.secure_defaults(),
))`} />
      </section>

      {/* CacheIntegration */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Zap className="w-5 h-5 text-aquilia-400" />
          CacheIntegration
        </h2>
        <p className={`mb-4 ${txt}`}>
          Selects the cache backend and tunes the key settings, eviction policy, and optional two-tier (composite) caching.
        </p>
        <CodeBlock language="python" code={`from aquilia.integrations import CacheIntegration

# ── In-memory cache (default) ─────────────────────────────────────────────
workspace.integrate(CacheIntegration(
    backend="memory",
    default_ttl=300,
    max_size=10_000,
    eviction_policy="lru",          # "lru" | "lfu" | "fifo" | "ttl" | "random"
    namespace="default",
    key_prefix="aq:",
))

# ── Redis-backed ──────────────────────────────────────────────────────────
workspace.integrate(CacheIntegration(
    backend="redis",
    redis_url="redis://localhost:6379/0",
    redis_max_connections=20,
    default_ttl=600,
    serializer="json",              # "json" | "msgpack" | "pickle"
))

# ── Composite (L1 memory + L2 Redis) ─────────────────────────────────────
workspace.integrate(CacheIntegration(
    backend="composite",
    l1_max_size=1000,               # items kept in process memory
    l1_ttl=60,                      # L1 entry TTL in seconds
    l2_backend="redis",
    redis_url="redis://localhost:6379/0",
))`} />
      </section>

      {/* MailIntegration */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Mail className="w-5 h-5 text-aquilia-400" />
          MailIntegration
        </h2>
        <p className={`mb-4 ${txt}`}>
          Supports SMTP, AWS SES, SendGrid, file-based, and console (dev) providers. <code>MailAuth.plain()</code> handles credentials; <code>MailAuth.oauth2()</code> handles OAuth2 flows.
        </p>
        <CodeBlock language="python" code={`from aquilia.integrations import (
    MailIntegration, SmtpProvider, SesProvider,
    SendGridProvider, ConsoleProvider, MailAuth,
)
from aquilia.pyconfig import Secret

# ── SMTP ─────────────────────────────────────────────────────────────────
workspace.integrate(MailIntegration(
    default_from="noreply@myapp.com",
    auth=MailAuth.plain("smtp_user", password_env="SMTP_PASS"),
    providers=[
        SmtpProvider(
            host="smtp.sendgrid.net",
            port=587,
            use_tls=True,
        ),
    ],
))

# ── AWS SES ──────────────────────────────────────────────────────────────
workspace.integrate(MailIntegration(
    default_from="noreply@myapp.com",
    providers=[
        SesProvider(
            region="eu-west-1",
            access_key_env="AWS_ACCESS_KEY_ID",
            secret_key_env="AWS_SECRET_ACCESS_KEY",
        ),
    ],
))

# ── SendGrid ─────────────────────────────────────────────────────────────
workspace.integrate(MailIntegration(
    default_from="noreply@myapp.com",
    providers=[
        SendGridProvider(api_key_env="SENDGRID_API_KEY"),
    ],
))

# ── Dev: console output (prints mail to stdout) ───────────────────────────
workspace.integrate(MailIntegration(
    default_from="dev@localhost",
    providers=[ConsoleProvider()],
))`} />
      </section>

      {/* TasksIntegration */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Cpu className="w-5 h-5 text-aquilia-400" />
          TasksIntegration
        </h2>
        <p className={`mb-4 ${txt}`}>
          Configures the background task worker pool — concurrency, retry policy, scheduler tick rate, and dead-letter queue size.
        </p>
        <CodeBlock language="python" code={`from aquilia.integrations import TasksIntegration

workspace.integrate(TasksIntegration(
    backend="memory",               # "memory" | "redis" (future)
    num_workers=8,                  # concurrent worker coroutines
    default_queue="default",
    max_retries=5,
    retry_delay=1.0,                # seconds before first retry
    retry_backoff=2.0,              # multiplier per retry (exponential)
    retry_max_delay=300.0,          # cap on retry wait time
    default_timeout=300.0,          # task execution timeout (seconds)
    auto_start=True,                # start workers at server boot
    scheduler_tick=15.0,            # interval (seconds) between cron checks
    dead_letter_max=1000,           # max failed tasks to keep
    cleanup_interval=300.0,         # purge old tasks every N seconds
    cleanup_max_age=3600.0,         # tasks older than this are purged
))`} />
      </section>

      {/* OpenAPIIntegration */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Globe className="w-5 h-5 text-aquilia-400" />
          OpenAPIIntegration
        </h2>
        <p className={`mb-4 ${txt}`}>
          Drives automatic OpenAPI spec generation and serves Swagger UI at <code>/docs</code> and ReDoc at <code>/redoc</code>.
        </p>
        <CodeBlock language="python" code={`from aquilia.integrations import OpenAPIIntegration

workspace.integrate(OpenAPIIntegration(
    title="My App API",
    version="2.0.0",
    description="REST API for My Application",
    contact_name="Engineering",
    contact_email="eng@myapp.com",
    license_name="MIT",
    license_url="https://opensource.org/licenses/MIT",

    # Endpoint paths
    docs_path="/docs",
    redoc_path="/redoc",
    openapi_json_path="/openapi.json",

    # Behaviour
    include_internal=False,         # exclude routes tagged @internal
    group_by_module=True,           # group by Aquilia module name
    infer_request_body=True,        # infer request body from Contract type hints
    infer_responses=True,           # infer response schemas from return type hints
    detect_security=True,           # auto-detect JWT/session guards and add security scheme

    # Servers list (shown in Swagger UI)
    servers=[
        {"url": "https://api.myapp.com", "description": "Production"},
        {"url": "http://localhost:8000",  "description": "Local dev"},
    ],

    # Custom Swagger UI theme
    swagger_ui_theme="dark",
    swagger_ui_config={"persistAuthorization": True},
))`} />
      </section>

      {/* Security integrations */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Shield className="w-5 h-5 text-aquilia-400" />
          Security integrations
        </h2>
        <p className={`mb-4 ${txt}`}>
          CORS, CSRF, CSP, and rate-limiting are each separate integrations so you can tune them independently or disable any one without touching the others.
        </p>
        <CodeBlock language="python" code={`from aquilia.integrations import (
    CorsIntegration,
    CsrfIntegration,
    CspIntegration,
    RateLimitIntegration,
)

# ── CORS ─────────────────────────────────────────────────────────────────
workspace.integrate(CorsIntegration(
    allow_origins=["https://myapp.com", "https://admin.myapp.com"],
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    allow_credentials=True,
    max_age=600,                    # seconds browser caches preflight
    allow_origin_regex=None,        # e.g. r"https://.*\\.myapp\\.com"
))

# ── CSRF ─────────────────────────────────────────────────────────────────
workspace.integrate(CsrfIntegration(
    secret_key="csrf-secret",
    header_name="X-CSRF-Token",     # token sent in this request header
    field_name="_csrf_token",       # hidden form field name
    cookie_name="_csrf_cookie",
    cookie_secure=True,
    cookie_samesite="Lax",
    safe_methods=["GET", "HEAD", "OPTIONS", "TRACE"],
    exempt_paths=["/api/webhooks/stripe"],
    trust_ajax=True,                # X-Requested-With: XMLHttpRequest bypasses check
    rotate_token=False,             # True → new token per request
))

# ── Content-Security-Policy ───────────────────────────────────────────────
workspace.integrate(CspIntegration(
    policy={
        "default-src": ["'self'"],
        "script-src":  ["'self'", "https://cdn.myapp.com"],
        "style-src":   ["'self'", "https://fonts.googleapis.com"],
        "img-src":     ["'self'", "data:", "https:"],
        "font-src":    ["'self'", "https://fonts.gstatic.com"],
        "object-src":  ["'none'"],
        "frame-ancestors": ["'none'"],
    },
    nonce=True,                     # inject ${'$'}{nonce} into script-src automatically
    report_only=False,              # True → log violations but don't block
))

# ── Rate Limiting ─────────────────────────────────────────────────────────
workspace.integrate(RateLimitIntegration(
    limit=200,                      # requests allowed per window
    window=60,                      # window in seconds
    algorithm="sliding_window",     # "sliding_window" | "fixed_window" | "token_bucket"
    per_user=True,                  # rate-limit per authenticated user, not global IP
    burst=50,                       # extra requests allowed momentarily above limit
    exempt_paths=["/health", "/healthz", "/ready", "/metrics"],
))`} />
      </section>

      {/* TemplatesIntegration */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Activity className="w-5 h-5 text-aquilia-400" />
          TemplatesIntegration
        </h2>
        <CodeBlock language="python" code={`from aquilia.integrations import TemplatesIntegration

workspace.integrate(TemplatesIntegration(
    directories=["templates", "modules/users/templates"],
    autoescape=True,                # HTML escaping on by default
    bytecode_cache=True,            # cache compiled templates to disk
    bytecode_cache_dir=".jinja_cache",
    auto_reload=True,               # reload templates on change (dev only)
    globals={                       # variables available in every template
        "app_name": "My App",
        "version": "2.0.0",
    },
))`} />
      </section>

      {/* AdminIntegration */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Layers className="w-5 h-5 text-aquilia-400" />
          AdminIntegration
        </h2>
        <CodeBlock language="python" code={`from aquilia.integrations import AdminIntegration, AdminModules, AdminSecurity

workspace.integrate(AdminIntegration(
    site_title="My App Admin",
    site_logo_url="/static/logo.svg",
    prefix="/admin",
    modules=AdminModules(
        monitoring=True,
        audit=True,
        users=True,
        permissions=True,
        storage=True,
        tasks=True,
    ),
    security=AdminSecurity(
        require_mfa=False,
        session_timeout_minutes=30,
        allowed_ips=["10.0.0.0/8"],    # restrict to internal network
    ),
))`} />
      </section>

      {/* I18n */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>Other integrations</h2>
        <CodeBlock language="python" code={`from aquilia.integrations import (
    I18nIntegration,
    LoggingIntegration,
    StaticFilesIntegration,
    VersioningIntegration,
    StorageIntegration,
)

# ── Internationalisation ──────────────────────────────────────────────────
workspace.integrate(I18nIntegration(
    default_locale="en",
    available_locales=["en", "fr", "de", "es"],
    fallback_locale="en",
    catalog_dirs=["locales"],
    catalog_format="json",         # "json" | "po" | "mo"
))

# ── Logging ──────────────────────────────────────────────────────────────
workspace.integrate(LoggingIntegration(
    level="INFO",
    format="json",                 # "json" | "text"
    include_request_id=True,
))

# ── Static files ──────────────────────────────────────────────────────────
workspace.integrate(StaticFilesIntegration(
    directories=["static", "public"],
    prefix="/static",
    cache_max_age=31536000,        # 1 year in seconds
))

# ── API versioning ────────────────────────────────────────────────────────
workspace.integrate(VersioningIntegration(
    strategy="url_prefix",         # "url_prefix" | "header" | "content_type"
    default_version="v1",
    supported_versions=["v1", "v2"],
))

# ── Storage backend ───────────────────────────────────────────────────────
workspace.integrate(StorageIntegration(
    backend="s3",
    bucket="my-app-uploads",
    region="eu-west-1",
    access_key_env="AWS_ACCESS_KEY_ID",
    secret_key_env="AWS_SECRET_ACCESS_KEY",
))`} />
      </section>

      {/* Navigation */}
      <section className="mb-12 border-t pt-8" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
        <div className="grid grid-cols-2 gap-3">
          {[
            ['/docs/config/workspace', 'Workspace Builder', '.integrate(), .module(), .env_config() — full API'],
            ['/docs/config/pyconfig', 'AquilaConfig & Env', 'Env, Secret, PasswordHasher, section'],
            ['/docs/config/dotenv', '.env Files', 'File loading, syntax, precedence'],
            ['/docs/config/manifest', 'AppManifest', 'Per-module component registry'],
          ].map(([href, label, desc]) => (
            <Link key={href as string} to={href as string} className="flex flex-col gap-0.5 group">
              <span className={`text-sm font-semibold flex items-center gap-1 ${isDark ? 'text-aquilia-400 group-hover:text-aquilia-300' : 'text-aquilia-600 group-hover:text-aquilia-500'} transition-colors`}>
                <ArrowRight className="w-3 h-3" />{label}
              </span>
              <span className={`text-xs ${subtxt}`}>{desc}</span>
            </Link>
          ))}
        </div>
      </section>

      <NextSteps />
    </div>
  )
}