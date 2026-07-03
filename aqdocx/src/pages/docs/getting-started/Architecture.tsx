import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Network, Layers, Cpu, Database, Box, Shield, Workflow, Plug, ArrowRight } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { ArchitectureDiagram } from '../../../components/ArchitectureDiagram'

export function ArchitecturePage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-10">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-aquilia-500/30 to-aquilia-500/10 flex items-center justify-center">
            <Network className="w-5 h-5 text-aquilia-400" />
          </div>
          <div>
            <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
                Architecture
                <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
              </span>
            </h1>
            <p className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>How Aquilia boots, compiles, and serves requests</p>
          </div>
        </div>
      </div>

      {/* Overview */}
      <section className="mb-10">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-400" />
          Overview
        </h2>

        <p className={`mb-8 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Aquilia follows a <strong>manifest → native runtime</strong> architecture. Unlike
          frameworks that discover components at import time, Aquilia separates declaration
          from request execution through explicit runtime wiring:
        </p>

        <ArchitectureDiagram isDark={isDark} />
        <div className="flex items-center justify-center py-6 mt-8">
          <img src="/architecture/complete_system.svg" alt="Complete System Orchestration" className="max-w-full h-auto max-h-[380px]" />
        </div>
      </section>

      {/* Boot Pipeline */}
      <section className="mb-10">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Cpu className="w-5 h-5 text-aquilia-400" />
          Boot Pipeline
        </h2>

        <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          When you call <code>aq run</code> or instantiate <code>AquiliaServer</code>, the following chain executes:
        </p>

        <CodeBlock
          code={`# 1. ConfigLoader resolves the Python-native configuration (AquilaConfig)
config = ConfigLoader()

# 2. Aquilary.from_manifests() validates and indexes all manifest classes
aquilary = Aquilary.from_manifests(
    manifests=[CoreManifest, UsersManifest],
    config=config,
    mode=RegistryMode.PROD,   # DEV, PROD, or TEST
)

# 3. RuntimeRegistry.from_metadata() prepares runtime metadata
#    - Creates DI Container per app (scope: "app")
#    - Registers ClassProvider for each service
#    - Compiles ControllerCompiler routes for each controller
#    - Builds model schemas through ModelMeta and ModelRegistry
runtime = RuntimeRegistry.from_metadata(aquilary, config)

# 4. AquiliaServer wires everything together
server = AquiliaServer(
    manifests=[CoreManifest, UsersManifest],
    config=config,
    mode=RegistryMode.PROD,
)
# Internally:
#   → Creates FaultEngine
#   → Builds Aquilary + RuntimeRegistry
#   → Registers services in DI containers
#   → Sets up MiddlewareStack (12+ layers)
#   → Creates ControllerFactory, ControllerEngine, ControllerCompiler
#   → Creates ControllerRouter
#   → Builds ASGIAdapter`}
          language="python"
        />
        <div className="flex items-center justify-center py-6">
          <img src="/architecture/runtime.svg" alt="Runtime Lifecycle" className="max-w-full h-auto max-h-[360px]" />
        </div>
      </section>

      {/* Component Graph */}
      <section className="mb-10">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Workflow className="w-5 h-5 text-aquilia-400" />
          Component Graph
        </h2>

        <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The following components are initialized during boot and their relationships:
        </p>

        <CodeBlock
          code={`AquiliaServer
├── ConfigLoader                 # Layered config (CLI > env > .env > config files > defaults)
├── FaultEngine                  # Typed fault handling with domains and severity
├── Aquilary                     # Manifest registry
│   ├── AquilaryRegistry         # Validated app metadata indexed by name
│   └── FingerprintGenerator     # Content-addressed hashing of artifacts
├── RuntimeRegistry              # Compiled runtime state
│   ├── DI Containers            # One Container per app module (scope: "app")
│   │   └── Providers            # ClassProvider, FactoryProvider, ValueProvider, …
│   ├── Compiled Routes          # CompiledController → CompiledRoute[]
│   └── Model Schemas            # ModelMeta metaclass → table definitions
├── MiddlewareStack              # Priority-ordered middleware chain
│   ├── ExceptionMiddleware      # Global error → Response mapping (priority: 1)
│   ├── FaultMiddleware          # Fault signal interception (priority: 2)
│   ├── ServerRequestScopeMiddleware # Request-scoped child DI container (priority: 5)
│   ├── RequestIdMiddleware      # Generates X-Request-ID header (priority: 10)
│   ├── SessionMiddleware        # Session load/save per request (priority: 15)
│   ├── AquilAuthMiddleware      # Unified auth & identity extraction (priority: 15)
│   ├── TemplateMiddleware       # Template engine rendering context (priority: 25)
│   └── Security & Extensions    # ProxyFix (3), HTTPSRedirect (4), Version (5), Static (6), SecurityHeaders (7), HSTS (8), CSP (9), CORS (11), Inspector (11), RateLimit (12), ToolbarInjection (12), CSRF (20), I18n (24), Cache (26)
├── ControllerRouter             # URL pattern → CompiledRoute mapping
├── ControllerEngine             # Route dispatch + pipeline execution
├── ControllerFactory            # Controller instantiation with DI
├── ControllerCompiler           # Decorator metadata → CompiledRoute
├── ASGIAdapter                  # ASGI ↔ Aquilia bridge
├── LifecycleCoordinator         # Dependency-ordered startup/shutdown
└── AquilaSockets                # WebSocket runtime (if enabled)`}
          language="text"
        />
        <div className="flex items-center justify-center py-6">
          <img src="/architecture/high_level.svg" alt="High-Level Component Graph" className="max-w-full h-auto max-h-[360px]" />
        </div>
      </section>

      {/* Request Lifecycle */}
      <section className="mb-10">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <ArrowRight className="w-5 h-5 text-aquilia-400" />
          Request Lifecycle
        </h2>

        <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Every incoming ASGI request flows through this pipeline:
        </p>

        <CodeBlock
          code={`# 1. ASGI scope arrives at ASGIAdapter.__call__()
#    The adapter distinguishes between HTTP and WebSocket scopes.

# 2. For HTTP: ASGIAdapter wraps the raw ASGI scope into a Request object
request = Request(scope, receive, send)

# 3. RequestCtx is constructed with request, identity, session, container, state
ctx = RequestCtx(
    request=request,
    identity=None,         # Set by AuthMiddleware
    session=None,          # Set by SessionMiddleware
    container=container,   # Per-request DI container (child of app container)
    state={},              # Mutable state dict for middleware data
    request_id=None,       # Set by RequestIdMiddleware
)

# 4. Middleware chain executes (outermost → innermost):
#    Exception → Fault → RequestScope → RequestId → Session/Auth → Template → …
#    Each middleware calls: await next_handler(request, ctx)

# 5. ControllerRouter.match(path, method) → CompiledRoute
#    Pattern matching uses CompiledPattern with «name:type» syntax

# 6. ControllerEngine.handle(compiled_route, ctx)
#    a. ControllerFactory.create(controller_cls) — per-request DI injection
#    b. Execute pipeline nodes (guards → transforms → handler)
#    c. Call controller.on_request(ctx) lifecycle hook
#    d. Call handler method: response = await controller.method(ctx, **params)
#    e. Call controller.on_response(ctx, response) lifecycle hook

# 7. Response flows back through middleware chain (innermost → outermost)
#    Session middleware saves session, Auth middleware may set cookies, etc.

# 8. Response.send(send) serializes to ASGI and sends to client`}
          language="python"
        />
        <div className="flex items-center justify-center py-6">
          <img src="/architecture/middleware.svg" alt="Request Middleware Lifecycle" className="max-w-full h-auto max-h-[360px]" />
        </div>
      </section>

      {/* Middleware ordering */}
      <section className="mb-10">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Shield className="w-5 h-5 text-aquilia-400" />
          Middleware Ordering
        </h2>

        <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Middleware is ordered by <strong>scope</strong> (global {"<"} app {"<"} controller {"<"} route) and then
          by <strong>priority</strong> (lower number = outermost). The default stack:
        </p>

        <div className={`rounded-xl border overflow-hidden ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={isDark ? 'bg-zinc-800/80' : 'bg-gray-50'}>
                <th className={`text-left px-4 py-2 font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Priority</th>
                <th className={`text-left px-4 py-2 font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Middleware</th>
                <th className={`text-left px-4 py-2 font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Purpose</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5' : 'divide-gray-100'}`}>
              {[
                ['1', 'ExceptionMiddleware', 'Catches unhandled exceptions, renders debug pages or JSON error'],
                ['2', 'FaultMiddleware', 'Intercepts Fault signals and converts to HTTP responses'],
                ['3', 'ProxyFixMiddleware', 'Applies trust-proxy headers (X-Forwarded-For, etc.) for upstream proxies'],
                ['4', 'HTTPSRedirectMiddleware', 'Redirects incoming HTTP requests to HTTPS'],
                ['5', 'ServerRequestScopeMiddleware', 'Initializes and tears down request-scoped DI container'],
                ['5', 'VersionMiddleware', 'Handles API version negotiation based on headers/query/path'],
                ['6', 'StaticMiddleware', 'Serves static files directly from configured directories'],
                ['7', 'SecurityHeadersMiddleware', 'Injects security headers (Helmet equivalents like X-Frame-Options)'],
                ['8', 'HSTSMiddleware', 'Enforces HTTP Strict Transport Security'],
                ['9', 'CSPMiddleware', 'Validates and injects Content-Security-Policy (CSP) headers & nonces'],
                ['10', 'RequestIdMiddleware', 'Generates X-Request-ID via os.urandom (no UUID overhead)'],
                ['11', 'CORSMiddleware', 'Cross-origin resource sharing header parsing and preflight routing'],
                ['11', 'InspectorMiddleware', 'Captures debugging statistics and diagnostics in development'],
                ['12', 'RateLimitMiddleware', 'Rate limits requests per IP or user key (sliding window)'],
                ['12', 'ToolbarInjectionMiddleware', 'Injects the development diagnostics toolbar into HTML responses'],
                ['15', 'SessionMiddleware', 'Loads session from store, saves session state after response'],
                ['15', 'AquilAuthMiddleware', 'Extracts Identity from JWT/session and populates ctx.identity'],
                ['20', 'CSRFMiddleware', 'Protects against Cross-Site Request Forgery via token verification'],
                ['24', 'I18nMiddleware', 'Resolves local locale settings and translates response context'],
                ['25', 'TemplateMiddleware', 'Injects template engine context and rendering helper into request context'],
                ['26', 'CacheMiddleware', 'Caches HTTP responses for GET requests to optimize throughput'],
              ].map(([pri, name, purpose], i) => (
                <tr key={i} className={isDark ? 'hover:bg-white/5' : 'hover:bg-gray-50'}>
                  <td className={`px-4 py-2 font-mono text-xs ${isDark ? 'text-aquilia-400' : 'text-aquilia-600'}`}>{pri}</td>
                  <td className={`px-4 py-2 font-mono text-xs ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>{name}</td>
                  <td className={`px-4 py-2 text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>{purpose}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* DI Architecture */}
      <section className="mb-10">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Plug className="w-5 h-5 text-aquilia-400" />
          DI Container Hierarchy
        </h2>

        <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Aquilia creates a hierarchy of DI containers that mirror the scoping model:
        </p>

        <CodeBlock
          code={`# Container Hierarchy:
#
#   Root Container (scope: "singleton")
#       │
#       ├── App Container (scope: "app") — one per Module
#       │   ├── FaultEngine (singleton)
#       │   ├── EffectRegistry (singleton)
#       │   ├── CacheService (app)
#       │   ├── MailService (app)
#       │   └── UserService (app)
#       │
#       └── Request Container (scope: "request") — created per-request
#           ├── Session (request)
#           ├── Identity (request)
#           └── RequestCtx (request)
#
# Resolution flow:
#   1. Check request container cache
#   2. If not found, check app container
#   3. If scope is "singleton"/"app", delegate to parent
#   4. Instantiate via provider.instantiate(ctx)
#   5. Cache in appropriate scope container`}
          language="python"
        />
        <div className="flex items-center justify-center py-6">
          <img src="/architecture/di.svg" alt="DI Container Hierarchy" className="max-w-full h-auto max-h-[360px]" />
        </div>
      </section>

      {/* Config layers */}
      <section className="mb-10">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Database className="w-5 h-5 text-aquilia-400" />
          Configuration Layering
        </h2>

        <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Configuration is resolved through a layered merge strategy (higher priority wins):
        </p>

        <CodeBlock
          code={`# Priority order (highest → lowest):
#
#   1. CLI arguments           (--port 9000)
#   2. Environment variables   (AQ_PORT=9000)
#   3. .env file               (AQ_PORT=9000)
#   4. Python-native config    (workspace.py / AquilaConfig)
#   5. Framework defaults      (port: 8000)
#
# Environment variable prefix: AQ_
# Nested keys use double underscores: AQ_DATABASE__URL=postgres://...`}
          language="python"
        />
      </section>

      {/* Registry Modes */}
      <section className="mb-10">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Box className="w-5 h-5 text-aquilia-400" />
          Registry Modes
        </h2>

        <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The Aquilary registry operates in one of three modes, affecting validation strictness and
          debug output:
        </p>

        <div className={`rounded-xl border overflow-hidden ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={isDark ? 'bg-zinc-800/80' : 'bg-gray-50'}>
                <th className={`text-left px-4 py-3 font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Mode</th>
                <th className={`text-left px-4 py-3 font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Behavior</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5' : 'divide-gray-100'}`}>
              <tr className={isDark ? 'hover:bg-white/5' : 'hover:bg-gray-50'}>
                <td className={`px-4 py-2 font-mono text-sm ${isDark ? 'text-emerald-400' : 'text-emerald-600'}`}>DEV</td>
                <td className={`px-4 py-2 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>Relaxed validation, debug error pages, auto-reload, verbose logging, hot-reload support</td>
              </tr>
              <tr className={isDark ? 'hover:bg-white/5' : 'hover:bg-gray-50'}>
                <td className={`px-4 py-2 font-mono text-sm ${isDark ? 'text-blue-400' : 'text-blue-600'}`}>PROD</td>
                <td className={`px-4 py-2 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>Strict validation, JSON error responses, no debug pages, performance optimizations</td>
              </tr>
              <tr className={isDark ? 'hover:bg-white/5' : 'hover:bg-gray-50'}>
                <td className={`px-4 py-2 font-mono text-sm ${isDark ? 'text-amber-400' : 'text-amber-600'}`}>TEST</td>
                <td className={`px-4 py-2 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>Relaxed validation, test-specific providers, mock-friendly lifecycle, TransactionTestCase support</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <NextSteps />
    </div>
  )
}
