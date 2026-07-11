import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { BookOpen, Terminal, FileCode, Cpu, Layers, Settings, Shield } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function TutorialOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-10">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-aquilia-500/30 to-aquilia-500/10 flex items-center justify-center">
            <BookOpen className="w-5 h-5 text-aquilia-400" />
          </div>
          <div>
            <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
                Tutorials Overview
                <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
              </span>
            </h1>
            <p className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>Understanding the Aquilia Application Architecture and Scaffolded Project Layout</p>
          </div>
        </div>

        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Welcome to the Aquilia step-by-step tutorials! Aquilia is a high-performance, modular, and manifest-driven ASGI web framework built for Python 3.12+.
          Before we dive into writing code, let's understand the architectural principles, how to scaffold a new application, and what files are created under the hood.
        </p>
      </div>

      {/* Core Architectural Pillars */}
      <section className="mb-14">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Cpu className="w-6 h-6 text-aquilia-400" />
          Core Architectural Pillars
        </h2>

        <div className="relative pl-8 border-l-2 border-aquilia-500/10 space-y-10 ml-2 my-8">
          {/* Pillar 1 */}
          <div className="relative">
            <div className={`absolute -left-[39px] top-1.5 w-3.5 h-3.5 rounded-full bg-blue-500 border-4 ${isDark ? 'border-black' : 'border-[#fafafa]'}`} />
            <div className="flex items-center gap-2 mb-2">
              <Layers className="w-5 h-5 text-blue-400" />
              <h3 className={`font-bold text-lg ${isDark ? 'text-white' : 'text-gray-900'}`}>Manifest-First Topology</h3>
            </div>
            <p className={`text-sm leading-relaxed max-w-2xl ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Topologies and component registries are declared explicitly in Python manifests (<DocTerm id="cli.add_module">manifest.py</DocTerm>).
              This guarantees zero implicit class scanning or magic imports during start-up.
            </p>
          </div>

          {/* Pillar 2 */}
          <div className="relative">
            <div className={`absolute -left-[39px] top-1.5 w-3.5 h-3.5 rounded-full bg-purple-500 border-4 ${isDark ? 'border-black' : 'border-[#fafafa]'}`} />
            <div className="flex items-center gap-2 mb-2">
              <FileCode className="w-5 h-5 text-purple-400" />
              <h3 className={`font-bold text-lg ${isDark ? 'text-white' : 'text-gray-900'}`}>Contract-Based APIs</h3>
            </div>
            <p className={`text-sm leading-relaxed max-w-2xl ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Input and output structures are validated using <DocTerm id="bp.blueprint">Blueprints</DocTerm>.
              Blueprints act as the single source of truth for validation, serialization, database imprinting, and OpenAPI schema generation.
            </p>
          </div>

          {/* Pillar 3 */}
          <div className="relative">
            <div className={`absolute -left-[39px] top-1.5 w-3.5 h-3.5 rounded-full bg-emerald-500 border-4 ${isDark ? 'border-black' : 'border-[#fafafa]'}`} />
            <div className="flex items-center gap-2 mb-2">
              <Terminal className="w-5 h-5 text-emerald-400" />
              <h3 className={`font-bold text-lg ${isDark ? 'text-white' : 'text-gray-900'}`}>Dependency Injection</h3>
            </div>
            <p className={`text-sm leading-relaxed max-w-2xl ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              An async-first <DocTerm id="di.container">DI Container</DocTerm> resolves class dependencies, managing lifecycle scopes,
              validating cross-module boundaries, and preventing circular dependencies.
            </p>
          </div>
        </div>
      </section>

      {/* Building a Workspace */}
      <section className="mb-14">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Terminal className="w-6 h-6 text-aquilia-400" />
          Scaffolding Your First Workspace
        </h2>

        <p className={`mb-6 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Aquilia projects are organized inside a <strong className="text-aquilia-400">Workspace</strong>. A workspace defines the shared environment settings, database connections, global middleware, and enabled integrations.
          To initialize a new workspace, use the <DocTerm id="cli.init_workspace">aq init workspace</DocTerm> command:
        </p>

        <CodeBlock
          code={`# Create a new workspace named "my_server"
aq init workspace my_server

# Navigate into the generated directory
cd my_server`}
          language="bash"
        />

        <p className={`mt-6 mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          This scaffolds a production-grade directory layout. Let's inspect the files it generates:
        </p>

        <CodeBlock
          code={`my_server/
├── workspace.py          # Root configuration (integrations, database, environments)
├── starter.py            # Welcome-page controller (runs only when debug=True)
├── modules/              # Sub-modules folder (where your business code lives)
├── tests/                # Test suite with pytest configurations
│   ├── conftest.py       # Shared test fixtures (e.g. TestClient, TestServer)
│   └── test_smoke.py     # Smoke test validating server start-up
├── requirements.txt      # Python dependencies list
├── .env.example          # Environment variables template file
├── .gitignore            # Ignores local databases and the runtime directory
└── Makefile              # Quick developer shortcuts (e.g., make run, make test)`}
          language="text"
        />
      </section>

      {/* Key Scaffolded Files Explained */}
      <section className="mb-14">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <FileCode className="w-6 h-6 text-aquilia-400" />
          Key Scaffolded Files Explained
        </h2>

        <p className={`mb-6 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Let's view the exact contents of the primary files generated by the CLI, highlighting how they orchestrate the application lifecycle.
        </p>

        {/* workspace.py */}
        <div className="mb-10">
          <h3 className={`text-lg font-mono font-bold mb-2 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            <span className="w-2 h-2 rounded-full bg-aquilia-500"></span>
            workspace.py
          </h3>
          <p className={`text-sm mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            This is the root configuration file loaded by the <DocTerm id="cli.run">aq run</DocTerm> server.
            It defines environment profiles (<code className="text-aquilia-400">BaseEnv</code>, <code className="text-aquilia-400">DevEnv</code>, <code className="text-aquilia-400">ProdEnv</code>)
            and registers core integrations like the database ORM, dependency injection, caching, and templates.
          </p>

          <CodeBlock
            code={`"""
Aquilia Workspace Configuration - Production Grade
Generated by: aq init workspace test-space

Single-file workspace configuration.
Everything — structure, modules, integrations, and operational
settings (server, auth, DB) — lives in this one file.

- Type-safe with full IDE support
- Version-controlled and shared across team
- Observable via introspection
- Environment layering via AquilaConfig subclasses

Override order: BaseEnv → <AQ_ENV>Env → environment variables
"""

from aquilia import Workspace, Module
from aquilia import AquilaConfig, Secret, Env
from aquilia.integrations import (
    MiddlewareChain,
    DiIntegration,
    RegistryIntegration,
    RoutingIntegration,
    FaultHandlingIntegration,
    PatternsIntegration,
    DatabaseIntegration,
    CacheIntegration,
    TemplatesIntegration,
    StaticFilesIntegration,
)


# ── Environment Configuration ────────────────────────────────────
# Operational settings (server, auth, DB, mail) as Python classes.
# Activate: AQ_ENV=dev (default) | AQ_ENV=prod

class BaseEnv(AquilaConfig):
    """Shared defaults — every environment inherits these."""
    env = "dev"

    class server(AquilaConfig.Server):
        host    = "127.0.0.1"
        port    = 8000
        workers = 1
        reload  = False

        # ── Timeouts ───────────────────────────────────────────
        # timeout_keep_alive = 5        # seconds to keep idle connections open
        # timeout_worker_healthcheck = 30  # seconds before worker considered unresponsive
        # timeout_graceful_shutdown = 30 # seconds to wait on shutdown

        # ── Limits ─────────────────────────────────────────────
        # backlog            = 2048      # TCP connection backlog
        # limit_concurrency  = None      # max concurrent connections
        # limit_max_requests = None      # restart worker after N requests

        # ── Proxy / Headers ───────────────────────────────────
        # proxy_headers      = True      # trust X-Forwarded-* headers
        # forwarded_allow_ips = "*"      # IPs allowed to set proxy headers
        # root_path          = ""        # ASGI root_path for reverse proxies

        # ── WebSocket ─────────────────────────────────────────
        # ws_max_size        = 16_777_216  # max WebSocket message (16 MiB)
        # ws_ping_interval   = 20.0        # ping every N seconds
        # ws_ping_timeout    = 20.0        # close if pong not received

        # ── TLS / SSL ─────────────────────────────────────────
        # ssl_certfile       = "/etc/certs/cert.pem"
        # ssl_keyfile        = "/etc/certs/key.pem"
        # ssl_ca_certs       = None

        # ── Protocol Implementation ───────────────────────────
        # http = "auto"        # "auto" | "h11" | "httptools"
        # ws   = "auto"        # "auto" | "wsproto" | "websockets" | "none"
        # loop = "auto"        # "auto" | "asyncio" | "uvloop"

    class auth(AquilaConfig.Auth):
        secret_key      = Secret(env="AQ_SECRET_KEY", default="change-me-in-prod")
        password_hasher = AquilaConfig.PasswordHasher(algorithm="argon2id")


class DevEnv(BaseEnv):
    """Development — hot-reload, debug pages, single worker."""
    env = "dev"

    class server(BaseEnv.server):
        debug   = True
        reload  = True
        workers = 1


class ProdEnv(BaseEnv):
    """Production — multi-worker, no reload, no debug."""
    env = "prod"

    class server(BaseEnv.server):
        host               = Env("AQ_HOST", default="0.0.0.0")
        port               = Env("AQ_PORT", default=8000, cast=int)
        workers            = Env("AQ_WORKERS", default=4, cast=int)
        reload             = False
        access_log         = False
        timeout_keep_alive = 30
        limit_max_requests = 10_000   # auto-restart workers after 10k requests
        proxy_headers      = True     # trust X-Forwarded-* from load balancer

    class auth(BaseEnv.auth):
        secret_key = Secret(env="AQ_SECRET_KEY", required=True)


# ── Workspace Structure ──────────────────────────────────────────

workspace = (
    Workspace(
        name="test-space",
        version="1.0.0",
        description="Aquilia workspace",
    )
    # Wire environment config (resolved by AQ_ENV at runtime)
    .env_config(BaseEnv)

    # Starter module -- registered here so the server does not need
    # to hard-code it. Delete this line (and starter.py) once you
    # add your own modules with a GET "/" route.
    .starter("starter")

    # Add modules here with explicit configuration:
    # .module(Module("auth", version="1.0.0", description="Authentication module").route_prefix("/api/v1/auth").depends_on("core"))
    # .module(Module("users", version="1.0.0", description="User management").route_prefix("/api/v1/users").depends_on("auth", "core"))

    # Middleware chain -- controls which middleware runs and in what order.
    # Presets: defaults() (dev), production(), minimal()
    # Custom: MiddlewareChain.chain().use("aquilia.middleware.ExceptionMiddleware", priority=1).use(...)
    .middleware(MiddlewareChain.defaults())

    # Integrations - Configure core systems
    .integrate(DiIntegration(auto_wire=True))
    .integrate(RegistryIntegration())
    .integrate(RoutingIntegration(strict_matching=True))
    .integrate(FaultHandlingIntegration(default_strategy="propagate"))
    .integrate(PatternsIntegration())

    # Database - Configure the ORM backend
    .integrate(DatabaseIntegration(
        url="sqlite:///db.sqlite3",       # SQLite (dev)
        # url="postgresql://user:pass@localhost:5432/test-space",  # PostgreSQL
        pool_size=5,
        echo=False,
        auto_migrate=False,
    ))

    # Cache - In-memory by default, switch to Redis for production
    .integrate(CacheIntegration(
        backend="memory",
        default_ttl=300,
        max_size=1024,
        key_prefix="test-space:",
    ))

    # Templates - Fluent configuration
    .integrate(
        TemplatesIntegration.builder()
        .source("templates")
        .scan_modules()
        .cached("memory")
        .secure()
    )

    # Static Files - Serve static assets (CSS, JS, images)
    .integrate(StaticFilesIntegration(
        directories={"/static": "static"},
        cache_max_age=86400,
        etag=True,
    ))

    # Sessions (uncomment to enable session management)
    # .sessions(
    #     policies=[
    #         SessionPolicy(
    #             name="default",
    #             ttl=timedelta(days=7),
    #             idle_timeout=timedelta(hours=1),
    #             absolute_timeout=timedelta(days=30),
    #             rotate_on_use=False,
    #             rotate_on_privilege_change=True,
    #             fingerprint_binding=False,
    #             scope="user",
    #             persistence=PersistencePolicy(
    #                 enabled=True,
    #                 store_name="default",
    #                 write_through=True,
    #                 compress=False,
    #             ),
    #             concurrency=ConcurrencyPolicy(
    #                 max_sessions_per_principal=5,
    #                 behavior_on_limit="evict_oldest",
    #             ),
    #             transport=TransportPolicy(
    #                 cookie_name="test-space_session",
    #                 cookie_secure=False,
    #                 cookie_httponly=True,
    #                 cookie_samesite="lax",
    #             ),
    #         ),
    #     ],
    # )

    # Security (uncomment to enable security middleware)
    # Fine-grained: use Integration.cors(), Integration.csp(),
    # Integration.rate_limit() with .integrate().
    # .security(
    #     cors_enabled=False,
    #     csrf_protection=False,
    #     helmet_enabled=True,
    #     rate_limiting=False,
    # )

    # Telemetry (uncomment to enable observability)
    # .telemetry(
    #     tracing_enabled=False,
    #     metrics_enabled=True,
    #     logging_enabled=True,
    # )

    # Admin Dashboard (uncomment to enable admin at /admin/)
    # Requires: aq admin createsuperuser
    # .integrate(AdminIntegration(
    #     url_prefix="/admin",
    #     site_title="test-space Admin",
    #     auto_discover=True,
    # ))
)`}
            language="python"
            filename="workspace.py"
            highlightLines={[17, 92, 106, 125, 127, 141, 148, 157, 167]}
          />
        </div>

        {/* starter.py */}
        <div className="mb-10">
          <h3 className={`text-lg font-mono font-bold mb-2 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            <span className="w-2 h-2 rounded-full bg-aquilia-500"></span>
            starter.py
          </h3>
          <p className={`text-sm mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            The starter script provides a default welcome endpoint when the server starts up. In production or once custom modules are created,
            the <code className="text-aquilia-400">.starter("starter")</code> pointer is removed from <code className="text-aquilia-400">workspace.py</code>, and this file is deleted.
          </p>

          <CodeBlock
            code={`"""
Aquilia Starter Page -- shown at / when debug=True.
"""

from aquilia import Controller, GET, RequestCtx, Response


class StarterController(Controller):
    prefix = "/"
    tags = ["starter"]

    @GET("/")
    async def welcome(self, ctx: RequestCtx):
        """Render the Aquilia welcome page."""
        from aquilia.debug.pages import render_welcome_page
        try:
            from aquilia import __version__
            version = __version__
        except Exception:
            version = ""

        html = render_welcome_page(aquilia_version=version)
        return Response(
            content=html.encode("utf-8"),
            status=200,
            headers={"content-type": "text/html; charset=utf-8"},
        )
`}
            language="python"
            filename="starter.py"
            highlightLines={[8, 12, 13, 22, 23]}
          />
        </div>
      </section>

      {/* Scaffolding Modules */}
      <section className="mb-14">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Settings className="w-6 h-6 text-aquilia-400" />
          Scaffolding Modules with <code className="text-aquilia-400">aq add module</code>
        </h2>

        <p className={`mb-6 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Aquilia's CLI features a complete code-generation engine to scaffold self-contained application modules.
          Running <code className="text-aquilia-400">aq add module &lt;name&gt;</code> prompts you interactively, but you can also configure options directly using command line arguments.
        </p>

        <h3 className={`text-lg font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Command Arguments and Options</h3>
        <div className="space-y-4 my-6 pl-4 border-l border-aquilia-500/10">
          {[
            {
              option: "name (Argument)",
              desc: "The name of the module to create (e.g. users, catalog). Must be a valid Python identifier."
            },
            {
              option: "--depends-on <dependency>",
              desc: "Declare a module dependency. This is added to the generated manifest's depends_on list. Repeat this option to declare multiple dependencies."
            },
            {
              option: "--route-prefix <prefix>",
              desc: "Specify a custom routing prefix for the module's controllers. Defaults to /name if not specified."
            },
            {
              option: "--fault-domain <domain>",
              desc: "Declare a custom structured fault domain (e.g. USER_FAULT). Defaults to the uppercase module name."
            },
            {
              option: "--with-tests",
              desc: "A flag that instructs the generator to scaffold a test_routes.py file containing pre-wired endpoint smoke tests."
            },
            {
              option: "--minimal",
              desc: "A flag to scaffold a minimal module structure. Generates only manifest.py (lean) and controllers.py (single GET root route), skipping the models, services, and faults boilerplates."
            },
            {
              option: "--no-docker",
              desc: "A flag to prevent the CLI from auto-generating workspace deployment Dockerfile and docker-compose.yml configurations."
            },
            {
              option: "-y, --yes",
              desc: "Skip the interactive prompts completely and generate the module immediately using default settings."
            }
          ].map((opt) => (
            <div key={opt.option} className="flex flex-col md:flex-row md:items-start gap-1 md:gap-4">
              <div className="font-mono text-sm text-aquilia-400 font-bold w-48 shrink-0 flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-aquilia-500" />
                {opt.option}
              </div>
              <div className={`text-xs leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{opt.desc}</div>
            </div>
          ))}
        </div>

        <h3 className={`text-lg font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Scaffolded Module Directory Layout</h3>
        <p className={`text-sm mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Executing <code className="text-aquilia-400">aq add module &lt;name&gt;</code> generates the following files inside your module directory:
        </p>
        <CodeBlock
          code={`modules/<name>/
├── __init__.py
├── manifest.py       # Module manifest (single source of truth for dependencies and components)
├── controllers.py    # Class-based route handler controllers (e.g. GET, POST endpoints)
├── services.py       # Dependency injected services containing business logic
├── models.py         # Database ORM models mapping to SQL tables
├── blueprints.py     # Request/response validation blueprint contracts using Facets
└── faults.py         # Module-specific structured domain exception faults`}
          language="text"
        />

        <h3 className={`text-lg font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Default manifest.py Content</h3>
        <p className={`text-sm mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-400">manifest.py</code> file acts as the registration hub for all components in the module. Here is the exact scaffolded template generated by the CLI:
        </p>
        <CodeBlock
          code={`"""
Module Manifest: auth
Generated by: aq add module auth

This file is the single source of truth for the auth module.
It controls:

Component Registration:
  - controllers, services, models, middleware, guards, pipes, interceptors

Module-Level Settings (override workspace defaults for this module only):
  - sessions: Module-specific session policies
  - cache: Module-specific cache configuration
  - auth: Module-specific authentication settings
  - templates: Module-specific template directories
  - faults: Module-specific error handling and fault domains

Cross-Module Dependencies:
  - imports: Modules this module depends on
  - exports: Services/components visible to other modules
"""

from aquilia import AppManifest
from aquilia.manifest import (
    FaultHandlingConfig,
    MiddlewareConfig,
    SessionConfig,
    TemplateConfig,
)


manifest = AppManifest(
    # ── Identity ─────────────────────────────────────────────────────
    name="auth",
    version="0.1.0",
    description="Auth module",
    author="",
    tags=["auth"],

    # ── Components ────────────────────────────────────────────────────
    controllers=[
        "modules.auth.controllers:AuthController",
    ],
    services=[
        "modules.auth.services:AuthService",
    ],
    models=[
        "modules.auth.models:Auth",
    ],
    middleware=[],
    guards=[],
    pipes=[],
    interceptors=[],

    # ── Routing ───────────────────────────────────────────────────────
    # Note: route_prefix is configured in workspace.py via Module.route_prefix()
    base_path="modules.auth",

    # ── Cross-Module Dependencies ─────────────────────
    imports=[],
    exports=[
        # Services/components visible to modules that import this module.
        # "modules.auth.services:AuthService",
    ],

    # ── Error Handling (module-level) ─────────────────────────────────
    faults=FaultHandlingConfig(
        default_domain="y",
        strategy="propagate",
    ),

    # ── Sessions (module-level override) ──────────────────────────────
    # Uncomment to define module-specific session policies:
    # sessions=[
    #     SessionConfig(
    #         name="auth_session",
    #         ttl=timedelta(hours=1),
    #         store="memory",
    #     ),
    # ],

    # ── Templates (module-level) ──────────────────────────────────────
    # Uncomment to add module-specific template directories:
    # templates=TemplateConfig(
    #     search_paths=["modules/auth/templates"],
    # ),

    # ── Auto-Discovery ────────────────────────────────────────────────
    auto_discover=True,
    discover_patterns=["controllers", "services", "models", "middleware", "guards"],
)


__all__ = ["manifest"]`}
          language="python"
          filename="manifest.py"
          highlightLines={[32, 38, 41, 44, 53, 56, 61, 78]}
        />

        <h3 className={`text-lg font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>CLI Usage Examples</h3>
        <CodeBlock
          code={`# 1. Run interactive scaffolding wizard
aq add module

# 2. Scaffold a products module pre-wired to depend on users
aq add module products --depends-on=users -y

# 3. Create a minimal API module with a custom route prefix and fault domain
aq add module admin --route-prefix=/api/v1/admin --fault-domain=SYSTEM_ADMIN --minimal`}
          language="bash"
        />
      </section>

      {/* Enabling the Admin Dashboard */}
      <section className="mb-14">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Shield className="w-6 h-6 text-aquilia-400" />
          Enabling the Admin Dashboard
        </h2>

        <p className={`mb-6 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Aquilia includes a secure, built-in admin dashboard for user and permissions auditing, database records inspection,
          Docker container monitoring, and server telemetry. Let's look at how to enable it and set up your credentials.
        </p>

        <h3 className={`text-lg font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>1. Configure integrations in workspace.py</h3>
        <p className={`text-sm mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The admin panel requires active session management, database connectivity, and static files configuration.
          By default, basic admin pages are visible, but advanced systems (monitoring, Kubernetes pods, SQL query profiling, task queues) are opt-in.
          To enable <strong className="text-aquilia-400">all</strong> administrative modules, you can use the fluent <code className="text-aquilia-400">.enable_all()</code> method or the class method <code className="text-aquilia-400">AdminModules.all_enabled()</code>:
        </p>

        <CodeBlock
          code={`from aquilia.integrations import (
    AdminIntegration,
    AdminModules,
    SessionIntegration,
    DatabaseIntegration,
    StaticFilesIntegration,
)

workspace = (
    Workspace(name="my_server")
    
    # 1. Enable sessions (required for admin auth cookies)
    .sessions(policies=[...])
    
    # 2. Integrate the Admin dashboard (Enabling all admin modules)
    .integrate(AdminIntegration(
        url_prefix="/admin",
        site_title="Aquilia Admin Console",
        auto_discover=True,
        # Option A: Call enable_all() on the constructor
        modules=AdminModules().enable_all()
        # Option B: Use the all_enabled() classmethod
        # modules=AdminModules.all_enabled()
    ))
    
    # 3. Enable database and static files
    .integrate(DatabaseIntegration(url="sqlite:///db.sqlite3"))
    .integrate(StaticFilesIntegration(directories={"/static": "static"}))
)`}
          language="python"
          filename="workspace.py"
          highlightLines={[12, 15, 16, 17, 18, 19, 20, 21, 22, 25]}
        />

        <h3 className={`text-lg font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Understanding AdminModules Config Options</h3>
        <p className={`text-sm mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-400">AdminModules</code> config class lets you selectively enable or disable admin sections:
        </p>
        <div className="space-y-4 my-6 pl-4 border-l border-aquilia-500/10">
          {[
            {
              module: "monitoring",
              desc: "Displays system host performance metrics (CPU, Memory, Disk, Network) and ASGI process telemetry. Defaults to False."
            },
            {
              module: "query_inspector",
              desc: "Profiles active SQL queries executed by the ORM, highlighting slow queries and connection pool sizes. Defaults to False."
            },
            {
              module: "containers",
              desc: "Lists local Docker containers, stats, logs, and controls start/stop/restart lifecycles. Requires Docker installed. Defaults to False."
            },
            {
              module: "pods",
              desc: "Lists Kubernetes pods, statuses, namespaces, and streams logs from active kubectl contexts. Defaults to False."
            },
            {
              module: "tasks",
              desc: "Inspects background queues, worker concurrency, and completed/failed tasks. Defaults to False."
            },
            {
              module: "mailer",
              desc: "Logs outgoing email envelopes, delivery statuses, and allows test mail dispatch. Defaults to False."
            }
          ].map((m) => (
            <div key={m.module} className="flex flex-col md:flex-row md:items-start gap-1 md:gap-4">
              <div className="font-mono text-sm text-aquilia-400 font-bold w-40 shrink-0 flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-aquilia-500" />
                {m.module}
              </div>
              <div className={`text-xs leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{m.desc}</div>
            </div>
          ))}
        </div>

        <h3 className={`text-lg font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>2. Run Pre-flight Dependency Checks</h3>
        <p className={`text-sm mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Use the CLI's <code className="text-aquilia-400">aq admin check</code> command to statically verify that all dependencies are enabled:
        </p>

        <CodeBlock
          code={`# Run pre-flight checks to catch misconfigurations
aq admin check

# Automatically uncomment session configurations in workspace.py
aq admin check --fix`}
          language="bash"
        />

        <h3 className={`text-lg font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>3. Database Migrations (Two-Step Flow)</h3>
        <p className={`text-sm mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Before creating a superuser, the database tables must exist.
          <strong className="text-aquilia-400"> Important:</strong> You must always run the migrations in two separate steps:
        </p>
        <div className="pl-4 border-l-2 border-aquilia-500/10 space-y-4 my-4">
          <p className="text-xs leading-relaxed">
            <strong className={isDark ? 'text-white' : 'text-gray-900'}>Step A: Generate Migration Files (aq db makemigrations)</strong><br />
            This command inspects all ORM models declared in your module manifests, compares them to database schema snapshots, and generates python migration scripts inside each module's <code className="text-aquilia-400">migrations/</code> directory.
          </p>
          <p className="text-xs leading-relaxed">
            <strong className={isDark ? 'text-white' : 'text-gray-900'}>Step B: Run Migration (aq db migrate)</strong><br />
            This command reads the generated migration files, applies table mutations to your database, and registers them in the history logs.
          </p>
        </div>
        <CodeBlock
          code={`# 1. ALWAYS run makemigrations first to scan models and output scripts
aq db makemigrations

# 2. Then run migrate to execute DDL statements on the database
aq db migrate`}
          language="bash"
        />

        <h3 className={`text-lg font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>4. Create an Admin Superuser</h3>
        <p className={`text-sm mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Once migrations are completed, create a superuser using the CLI:
        </p>

        <CodeBlock
          code={`# Create a superuser account (interactively prompts for details)
aq admin createsuperuser

# Create a superuser non-interactively using options
aq admin createsuperuser \\
  --username=admin \\
  --email=admin@site.com \\
  --password=secretpassword \\
  --first-name=John \\
  --last-name=Doe`}
          language="bash"
        />

        <p className={`mt-4 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Once created, run <code className="text-aquilia-400">aq run</code>, navigate to <code className="text-aquilia-400">http://127.0.0.1:8000/admin</code>, and log in to explore the dashboard.
        </p>
      </section>

      {/* Starting the Server */}
      <section className="mb-14">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Terminal className="w-6 h-6 text-aquilia-400" />
          Running and Verifying the Workspace
        </h2>

        <p className={`mb-6 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          To spin up the local development server with hot-reloading active, run the following CLI command:
        </p>

        <CodeBlock
          code={`# Run dev server
aq run`}
          language="bash"
        />

        <p className={`mt-6 mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The server will start at <code className="text-aquilia-400">http://127.0.0.1:8000</code>.
          Open your browser and navigate to this URL to view the default welcome page.
        </p>

        <div className="pl-4 border-l-2 border-emerald-500/50 flex gap-3 my-6">
          <div className="text-xs leading-relaxed text-gray-500 dark:text-gray-400">
            <strong className={`font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Integrity Validation:</strong>
            {" "}You can run <DocTerm id="cli.validate">aq validate</DocTerm> at any time to statically verify module manifests, route configurations, and DI provider chains.
          </div>
        </div>
      </section>

      {/* Next Steps */}
      <section className="mb-10">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Begin Your Journey</h2>
        <p className={`mb-6 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Now that we understand how a workspace is bootstrapped and what its core structure represents, let's build a real-world application!
          Click the link below to follow our complete step-by-step tutorial on building a CRUD-based Todo API with database storage.
        </p>

        <div className="flex flex-col gap-2">
          <Link to="/docs/tutorials/todo-app" className={`text-sm font-medium flex items-center gap-1.5 ${isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-500'}`}>
            <span>→ Build a Todo Application (End-to-End Tutorial)</span>
          </Link>
        </div>
      </section>

      <NextSteps />
    </div>
  )
}
