import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { Layers, Zap, Settings, ArrowRight, Package, GitBranch, Globe, Shield, Activity } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function ConfigWorkspace() {
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
            <Layers className="w-5 h-5 text-aquilia-400" />
          </div>
          <div>
            <h1 className={`text-4xl ${head}`}>
              <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
                Workspace Builder
                <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
              </span>
            </h1>
            <p className={`text-sm ${subtxt}`}>aquilia.workspace — Workspace() fluent builder</p>
          </div>
        </div>

        <p className={`text-lg leading-relaxed ${txt}`}>
          <DocTerm id="config.workspace">Workspace</DocTerm> is the top-level fluent builder that defines your entire application — its name, modules, integrations, and environment config. Everything chains off a single <code>Workspace("name")</code> call and lives in <code>workspace.py</code> at the project root.
        </p>
      </div>

      {/* Quick full example */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Settings className="w-5 h-5 text-aquilia-400" />
          Minimal example
        </h2>
        <CodeBlock language="python" code={`# workspace.py
from aquilia import Workspace, Module
from aquilia.pyconfig import AquilaConfig, Env, Secret
from aquilia.integrations import DatabaseIntegration, AuthIntegration, OpenAPIIntegration

class BaseEnv(AquilaConfig):
    class server(AquilaConfig.Server):
        host = "127.0.0.1"
        port = Env("PORT", default=8000, cast=int)

    class auth(AquilaConfig.Auth):
        secret_key = Secret(env="AQ_SECRET_KEY", required=True)

workspace = (
    Workspace("myapp", version="1.0.0")
    .env_config(BaseEnv)
    .module(Module("api").route_prefix("/api"))
    .integrate(DatabaseIntegration(url=Env("DATABASE_URL", default="sqlite:///app.db")))
    .integrate(AuthIntegration(secret_key="dev-secret"))
    .integrate(OpenAPIIntegration(title="My API", version="1.0.0"))
)`} />
      </section>

      {/* Constructor */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          Workspace() constructor
        </h2>
        <CodeBlock language="python" code={`from aquilia import Workspace

workspace = Workspace(
    name="myapp",               # Required. Used in logging, traces, and OpenAPI metadata
    version="1.0.0",            # Optional. Shown in OpenAPI spec and admin panel
    description="My App",       # Optional. Human-readable description
)`} />
        <div className={`mt-4 rounded-xl border overflow-hidden ${border}`}>
          <table className="w-full text-sm">
            <thead><tr className={thead}><th className={`text-left px-4 py-3 font-semibold ${th}`}>Param</th><th className={`text-left px-4 py-3 font-semibold ${th}`}>Default</th><th className={`text-left px-4 py-3 font-semibold ${th}`}>Description</th></tr></thead>
            <tbody className={`divide-y ${divider}`}>
              {[
                ['name', '—', 'Workspace name (required). Used in structured logs, tracing, and OpenAPI metadata'],
                ['version', '"0.1.0"', 'Version string shown in OpenAPI spec and admin panel title'],
                ['description', '""', 'Human-readable description of the workspace'],
              ].map(([p, d, desc], i) => <tr key={i} className={hov}><td className="px-4 py-3 font-mono text-xs text-aquilia-400">{p}</td><td className={`px-4 py-3 font-mono text-xs ${subtxt}`}>{d}</td><td className={`px-4 py-3 text-xs ${txt}`}>{desc}</td></tr>)}
            </tbody>
          </table>
        </div>
      </section>

      {/* .env_config() */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Settings className="w-5 h-5 text-aquilia-400" />
          .env_config()
        </h2>
        <p className={`mb-4 ${txt}`}>
          Wires an <DocTerm id="config.aquilaconfig">AquilaConfig</DocTerm> base class into the workspace. At runtime, the framework reads the <code>AQ_ENV</code> environment variable and selects the matching subclass automatically. The config is then converted to a <code>ConfigLoader</code> and made available to all subsystems.
        </p>
        <CodeBlock language="python" code={`from aquilia import Workspace
from aquilia.pyconfig import AquilaConfig, Env, Secret

class BaseEnv(AquilaConfig):
    class server(AquilaConfig.Server):
        host    = "127.0.0.1"
        port    = Env("PORT", default=8000, cast=int)
        workers = 1

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
        timeout_keep_alive = 30

workspace = (
    Workspace("myapp")
    .env_config(BaseEnv)   # AQ_ENV=prod → uses ProdEnv, AQ_ENV=dev → uses DevEnv
)`} />
      </section>

      {/* .module() */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Package className="w-5 h-5 text-aquilia-400" />
          .module()
        </h2>
        <p className={`mb-4 ${txt}`}>
          Registers a <DocTerm id="config.module">Module</DocTerm> in the workspace. A module is a logical boundary that groups controllers, services, routes, models, and middleware under a single URL prefix and optional fault domain. Each <code>Module</code> builder is converted to a <code>ModuleConfig</code> internally. You can register as many modules as you need — they are isolated from each other unless explicitly declared as dependencies.
        </p>
        <CodeBlock language="python" code={`from aquilia import Workspace, Module

workspace = (
    Workspace("myapp")

    # ── Simple module with auto-discovery ────────────────────────────────
    .module(
        Module("users")
        .route_prefix("/users")
        .auto_discover("apps/users")      # scans apps/users/ for controllers, services, models
    )

    # ── Explicit component registration ──────────────────────────────────
    .module(
        Module("auth", version="2.0.0")
        .route_prefix("/auth")
        .register_controllers("LoginController", "TokenController", "OAuthController")
        .register_services("AuthService", "TokenService")
        .register_models("UserSession", "RefreshToken")
    )

    # ── Module with dependencies and fault isolation ─────────────────────
    .module(
        Module("orders")
        .route_prefix("/orders")
        .auto_discover("apps/orders")
        .depends_on("users", "catalog")   # ensures users and catalog are booted first
        .fault_domain("commerce")         # groups orders-related faults under a single domain
        .tags("Orders", "Commerce")       # OpenAPI grouping tags
    )

    # ── Module with socket controllers (WebSocket) ───────────────────────
    .module(
        Module("realtime")
        .route_prefix("/ws")
        .register_socket_controllers("ChatController", "NotificationController")
    )

    # ── Module with module-level middleware ──────────────────────────────
    .module(
        Module("admin")
        .route_prefix("/admin")
        .register_controllers("DashboardController", "UserAdminController")
        .register_middlewares("AdminAuthMiddleware", "AuditMiddleware")
        .depends_on("users")
    )
)`} />
      </section>

      {/* .integrate() */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Zap className="w-5 h-5 text-aquilia-400" />
          .integrate()
        </h2>
        <p className={`mb-4 ${txt}`}>
          Adds a typed integration dataclass to the workspace. Pass instances from <code>aquilia.integrations</code> — each one has <code>__post_init__</code> validation and a <code>_integration_type</code> field the framework uses for routing. There is no old-style <code>Integration.database()</code> static method — use the typed dataclasses directly.
        </p>
        <CodeBlock language="python" code={`from aquilia import Workspace, Module
from aquilia.integrations import (
    DatabaseIntegration,
    AuthIntegration,
    SessionIntegration,
    CacheIntegration,
    OpenAPIIntegration,
    MailIntegration, SmtpProvider, MailAuth,
    TasksIntegration,
    CorsIntegration,
    CsrfIntegration,
    RateLimitIntegration,
    TemplatesIntegration,
    StaticFilesIntegration,
    LoggingIntegration,
)
from aquilia.pyconfig import Env, Secret

workspace = (
    Workspace("myapp")

    # ── Database ──────────────────────────────────────────────────────────
    .integrate(DatabaseIntegration(
        url=Env("DATABASE_URL", required=True),
        auto_migrate=True,
        pool_size=20,
    ))

    # ── Authentication ────────────────────────────────────────────────────
    .integrate(AuthIntegration(
        secret_key=Secret(env="AQ_SECRET_KEY", required=True).reveal(),
        algorithm="HS256",
        access_token_ttl_minutes=60,
        refresh_token_ttl_days=30,
        require_auth_by_default=False,
    ))

    # ── Sessions ─────────────────────────────────────────────────────────
    .integrate(SessionIntegration(
        enabled=True,
        # Omit policy/store/transport to use smart defaults
    ))

    # ── Cache ─────────────────────────────────────────────────────────────
    .integrate(CacheIntegration(
        backend="redis",
        redis_url=Env("REDIS_URL", default="redis://localhost:6379/0"),
        default_ttl=600,
    ))

    # ── OpenAPI / Swagger UI ──────────────────────────────────────────────
    .integrate(OpenAPIIntegration(
        title="My App API",
        version="1.0.0",
        docs_path="/docs",
        redoc_path="/redoc",
        group_by_module=True,
    ))

    # ── CORS ─────────────────────────────────────────────────────────────
    .integrate(CorsIntegration(
        allow_origins=["https://myapp.com"],
        allow_credentials=True,
        max_age=600,
    ))

    # ── CSRF ─────────────────────────────────────────────────────────────
    .integrate(CsrfIntegration(
        secret_key="csrf-signing-key",
        exempt_paths=["/api/webhooks/stripe"],
    ))

    # ── Rate limiting ─────────────────────────────────────────────────────
    .integrate(RateLimitIntegration(
        limit=200, window=60, per_user=True, burst=30,
    ))

    # ── Mail ──────────────────────────────────────────────────────────────
    .integrate(MailIntegration(
        default_from="noreply@myapp.com",
        auth=MailAuth.plain("smtp_user", password_env="SMTP_PASS"),
        providers=[SmtpProvider(host="smtp.sendgrid.net", port=587, use_tls=True)],
    ))

    # ── Background tasks ──────────────────────────────────────────────────
    .integrate(TasksIntegration(
        num_workers=8,
        max_retries=5,
        scheduler_tick=15.0,
    ))

    # ── Templates ────────────────────────────────────────────────────────
    .integrate(TemplatesIntegration(
        directories=["templates"],
        bytecode_cache=True,
        autoescape=True,
    ))

    # ── Static files ──────────────────────────────────────────────────────
    .integrate(StaticFilesIntegration(
        directories=["static"],
        prefix="/static",
        cache_max_age=31536000,
    ))

    # ── Structured logging ────────────────────────────────────────────────
    .integrate(LoggingIntegration(
        level="INFO",
        format="json",
        include_request_id=True,
    ))
)`} />
      </section>

      {/* .env_config + integrate together */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <GitBranch className="w-5 h-5 text-aquilia-400" />
          Combining env_config with integrations
        </h2>
        <p className={`mb-4 ${txt}`}>
          <code>.env_config()</code> controls the environment-level settings (server, auth tokens, DB URL) through <DocTerm id="config.aquilaconfig">AquilaConfig</DocTerm> subclasses. <code>.integrate()</code> controls the subsystem behaviour (connection pools, middleware, logging). They are complementary — use both together for the cleanest production setup.
        </p>
        <CodeBlock language="python" code={`# workspace.py — combining env_config and integrate()
from aquilia import Workspace, Module
from aquilia.pyconfig import AquilaConfig, Env, Secret
from aquilia.integrations import (
    DatabaseIntegration, AuthIntegration, CacheIntegration,
    OpenAPIIntegration, CorsIntegration, TasksIntegration,
)

# ─── AquilaConfig: env-specific settings ─────────────────────────────────────
class BaseEnv(AquilaConfig):
    class server(AquilaConfig.Server):
        host    = "127.0.0.1"
        port    = Env("PORT", default=8000, cast=int)
        workers = 1

    class auth(AquilaConfig.Auth):
        secret_key = Secret(env="AQ_SECRET_KEY", required=True)

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
        timeout_keep_alive = 30
    class auth(BaseEnv.auth):
        password_hasher = AquilaConfig.PasswordHasher.argon2id(time_cost=3)

# ─── Workspace: structure + subsystem integrations ────────────────────────────
workspace = (
    Workspace("ecommerce", version="2.0.0")
    .env_config(BaseEnv)       # AQ_ENV selects DevEnv or ProdEnv

    .module(Module("catalog").route_prefix("/catalog").auto_discover("apps/catalog"))
    .module(Module("orders").route_prefix("/orders").auto_discover("apps/orders").depends_on("catalog"))
    .module(Module("users").route_prefix("/users").auto_discover("apps/users"))

    .integrate(DatabaseIntegration(url=Env("DATABASE_URL", required=True), auto_migrate=True, pool_size=20))
    .integrate(AuthIntegration(secret_key=Secret(env="AQ_SECRET_KEY", required=True).reveal()))
    .integrate(CacheIntegration(backend="redis", redis_url=Env("REDIS_URL", default="redis://localhost:6379/0")))
    .integrate(OpenAPIIntegration(title="E-Commerce API", version="2.0.0", swagger_ui_theme="dark"))
    .integrate(CorsIntegration(allow_origins=["https://myshop.com"], allow_credentials=True))
    .integrate(TasksIntegration(num_workers=8, max_retries=5))
)`} />
      </section>

      {/* .security() */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Shield className="w-5 h-5 text-aquilia-400" />
          .security() — high-level flags
        </h2>
        <p className={`mb-4 ${txt}`}>
          High-level flags that enable entire middleware categories with sensible defaults. For fine-grained control (custom CORS origins, CSRF exemptions, rate-limit algorithms), use the typed integration dataclasses via <code>.integrate()</code> instead.
        </p>
        <CodeBlock language="python" code={`workspace = (
    Workspace("myapp")
    .security(
        cors_enabled=True,          # adds CorsMiddleware with allow_origins=["*"]
        csrf_protection=True,       # adds CsrfMiddleware
        helmet_enabled=True,        # adds security response headers (X-Frame-Options, etc.)
        rate_limiting=False,        # adds RateLimitMiddleware (100 req/min default)
        https_redirect=False,       # redirects HTTP → HTTPS
        hsts=True,                  # Strict-Transport-Security header
        proxy_fix=False,            # trust X-Forwarded-* headers from reverse proxy
    )
)`} />
      </section>

      {/* .sessions() shorthand */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          Sessions shorthand
        </h2>
        <p className={`mb-4 ${txt}`}>
          You can also use <code>.sessions()</code> as a shorthand instead of <code>.integrate(SessionIntegration(...))</code>. Both are equivalent.
        </p>
        <CodeBlock language="python" code={`from aquilia.sessions import SessionPolicy, MemoryStore

# Using .sessions() shorthand:
workspace = (
    Workspace("myapp")
    .sessions(policies=[
        SessionPolicy.for_web_users()
            .lasting(days=14)
            .idle_timeout(hours=2)
            .rotating_on_privilege_change()
    ])
)

# Equivalent using .integrate():
from aquilia.integrations import SessionIntegration
workspace = (
    Workspace("myapp")
    .integrate(SessionIntegration(
        policy=SessionPolicy.for_web_users().lasting(days=14),
    ))
)`} />
      </section>

      {/* .mlops() */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Activity className="w-5 h-5 text-aquilia-400" />
          .mlops()
        </h2>
        <p className={`mb-4 ${txt}`}>
          Shorthand to enable the Aquilia MLOps platform — model registry, serving, drift detection, and lineage tracking. Equivalent to <code>.integrate(MlopsIntegration(...))</code>.
        </p>
        <CodeBlock language="python" code={`workspace = (
    Workspace("mlapp")
    .mlops(
        enabled=True,
        registry_db="registry.db",
        blob_root=".aquilia-store",
        drift_method="psi",
        drift_threshold=0.2,
        max_batch_size=16,
        max_latency_ms=50.0,
        plugin_auto_discover=True,
    )
)`} />
      </section>

      {/* Full production workspace */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Globe className="w-5 h-5 text-aquilia-400" />
          Full production workspace
        </h2>
        <CodeBlock language="python" code={`# workspace.py — production-ready multi-module workspace
from aquilia import Workspace, Module
from aquilia.pyconfig import AquilaConfig, Env, Secret
from aquilia.integrations import (
    DatabaseIntegration,
    AuthIntegration,
    SessionIntegration,
    CacheIntegration,
    OpenAPIIntegration,
    MailIntegration, SmtpProvider, SesProvider, MailAuth,
    TasksIntegration,
    CorsIntegration,
    CsrfIntegration,
    RateLimitIntegration,
    CspIntegration,
    TemplatesIntegration,
    StaticFilesIntegration,
    LoggingIntegration,
    StorageIntegration,
    AdminIntegration, AdminModules,
    I18nIntegration,
)

# ── AquilaConfig (environment-specific) ──────────────────────────────────────

class BaseEnv(AquilaConfig):
    class server(AquilaConfig.Server):
        host    = "127.0.0.1"
        port    = Env("PORT", default=8000, cast=int)
        workers = 1

    class auth(AquilaConfig.Auth):
        secret_key = Secret(env="AQ_SECRET_KEY", required=True)
        algorithm  = "HS256"

    class database(AquilaConfig.Database):
        url = Env("DATABASE_URL", default="sqlite:///dev.db")

    class signing(AquilaConfig.Signing):
        secret = Secret(env="AQ_SECRET_KEY", required=True)

class DevEnv(BaseEnv):
    env = "dev"
    class server(BaseEnv.server):
        reload    = True
        debug     = True
        log_level = "debug"

class ProdEnv(BaseEnv):
    env = "prod"
    class server(BaseEnv.server):
        host              = "0.0.0.0"
        workers           = Env("WEB_WORKERS", default=4, cast=int)
        timeout_keep_alive = 30
        proxy_headers      = True
        forwarded_allow_ips = "*"
    class auth(BaseEnv.auth):
        password_hasher = AquilaConfig.PasswordHasher.argon2id(time_cost=3, memory_cost=131072)
    class database(BaseEnv.database):
        pool_size    = 20
        auto_migrate = True

# ── Workspace (structure + subsystem config) ──────────────────────────────────

workspace = (
    Workspace("platform", version="3.0.0", description="Multi-tenant SaaS platform")
    .env_config(BaseEnv)                  # AQ_ENV → DevEnv | ProdEnv

    # ── Modules ──────────────────────────────────────────────────────────
    .module(
        Module("auth", version="2.0")
        .route_prefix("/auth")
        .auto_discover("apps/auth")
        .fault_domain("security")
    )
    .module(
        Module("users")
        .route_prefix("/users")
        .auto_discover("apps/users")
        .depends_on("auth")
        .fault_domain("users")
        .tags("Users", "Profiles")
    )
    .module(
        Module("billing")
        .route_prefix("/billing")
        .auto_discover("apps/billing")
        .depends_on("users")
        .fault_domain("billing")
    )
    .module(
        Module("notifications")
        .route_prefix("/notifications")
        .register_controllers("NotificationController")
        .register_socket_controllers("NotificationSocketController")
        .depends_on("users")
    )
    .module(
        Module("admin")
        .route_prefix("/admin")
        .auto_discover("apps/admin")
        .depends_on("users", "billing")
    )

    # ── Integrations ─────────────────────────────────────────────────────
    .integrate(DatabaseIntegration(
        url=Env("DATABASE_URL", required=True),
        auto_migrate=True,
        pool_size=20,
    ))
    .integrate(AuthIntegration(
        secret_key=Secret(env="AQ_SECRET_KEY", required=True).reveal(),
        access_token_ttl_minutes=60,
        refresh_token_ttl_days=30,
        require_auth_by_default=False,
    ))
    .integrate(SessionIntegration())
    .integrate(CacheIntegration(
        backend="composite",
        l1_max_size=1000,
        l1_ttl=60,
        l2_backend="redis",
        redis_url=Env("REDIS_URL", default="redis://localhost:6379/0"),
    ))
    .integrate(OpenAPIIntegration(
        title="Platform API",
        version="3.0.0",
        contact_email="eng@platform.io",
        swagger_ui_theme="dark",
        group_by_module=True,
    ))
    .integrate(MailIntegration(
        default_from="noreply@platform.io",
        providers=[SesProvider(region="eu-west-1")],
    ))
    .integrate(TasksIntegration(num_workers=8, max_retries=5, scheduler_tick=15.0))
    .integrate(CorsIntegration(allow_origins=["https://platform.io"], allow_credentials=True))
    .integrate(CsrfIntegration(exempt_paths=["/api/webhooks"]))
    .integrate(RateLimitIntegration(limit=200, window=60, per_user=True, burst=30))
    .integrate(CspIntegration(preset="strict", nonce=True))
    .integrate(TemplatesIntegration(directories=["templates"], bytecode_cache=True))
    .integrate(StaticFilesIntegration(directories=["static"], cache_max_age=86400))
    .integrate(StorageIntegration(backend="s3", bucket="platform-uploads", region="eu-west-1"))
    .integrate(I18nIntegration(
        default_locale="en",
        available_locales=["en", "fr", "de", "es"],
    ))
    .integrate(LoggingIntegration(level="INFO", format="json", include_request_id=True))
    .integrate(AdminIntegration(
        site_title="Platform Admin",
        prefix="/admin",
        modules=AdminModules(monitoring=True, audit=True, users=True, tasks=True),
    ))
)`} />
      </section>

      {/* Navigation */}
      <section className="mb-12 border-t pt-8" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
        <div className="grid grid-cols-2 gap-3">
          {[
            ['/docs/config', 'Config Overview', 'Configuration system, AquilaConfig, precedence'],
            ['/docs/config/pyconfig', 'AquilaConfig & Env', 'Env, Secret, PasswordHasher, section'],
            ['/docs/config/module', 'Module Builder', 'Full Module fluent API reference'],
            ['/docs/config/integrations', 'Integrations', 'All typed integration dataclasses'],
            ['/docs/config/manifest', 'AppManifest', 'Per-module component registry'],
            ['/docs/config/dotenv', '.env Files', 'File loading, syntax, DotEnvLoader'],
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