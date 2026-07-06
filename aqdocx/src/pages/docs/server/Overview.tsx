import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'
import { Server, Layers, Settings, Shield, Database, Zap, Globe, AlertCircle } from 'lucide-react'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function ServerOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto select-none">
      {/* Header */}
      <div className="mb-10">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-aquilia-500/30 to-aquilia-500/10 flex items-center justify-center shadow-lg shadow-aquilia-500/10">
            <Server className="w-5 h-5 text-aquilia-400" />
          </div>
          <div>
            <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
                AquiliaServer
                <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
              </span>
            </h1>
            <p className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>aquilia.server — Main server orchestration</p>
          </div>
        </div>

        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          <code>AquiliaServer</code> is the central orchestrator that wires together every subsystem —
          from Aquilary manifest compilation to ASGI request handling. It is a 4,000+ line class that
          serves as the single entry point for the entire framework.
        </p>
      </div>

      {/* Visual System Topology (No boxy layout, premium concentric SVG) */}
      <div className="w-full h-80 flex items-center justify-center my-6 relative">
        <svg className="w-full h-full max-w-2xl" viewBox="0 0 600 320" fill="none">
          <defs>
            <radialGradient id="centerGlow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#f59e0b" stopOpacity="0" />
            </radialGradient>
            <linearGradient id="orbitLineGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="rgba(255,255,255,0.08)" />
              <stop offset="50%" stopColor="rgba(245,158,11,0.2)" />
              <stop offset="100%" stopColor="rgba(255,255,255,0.08)" />
            </linearGradient>
          </defs>

          {/* Glowing background circles */}
          <circle cx="300" cy="160" r="100" fill="url(#centerGlow)" />
          <circle cx="300" cy="160" r="150" fill="none" stroke="url(#orbitLineGrad)" strokeWidth="1" strokeDasharray="5,5" />
          <circle cx="300" cy="160" r="80" fill="none" stroke="url(#orbitLineGrad)" strokeWidth="1.5" />

          {/* Connecting bezier lines */}
          <g stroke="rgba(255,255,255,0.12)" strokeWidth="1.5">
            <path d="M 300 160 Q 200 100 100 100" />
            <path d="M 300 160 Q 400 100 500 100" />
            <path d="M 300 160 Q 200 220 100 220" />
            <path d="M 300 160 Q 400 220 500 220" />
          </g>

          {/* Satellites circles with text labels */}
          {/* Center Hub */}
          <circle cx="300" cy="160" r="28" fill="#18181b" stroke="#f59e0b" strokeWidth="2.5" className="filter drop-shadow-[0_0_12px_rgba(245,158,11,0.4)]" />
          <text x="300" y="164" textAnchor="middle" fill="#fff" fontSize="9" fontWeight="bold" fontFamily="monospace">Server</text>

          {/* Satellites */}
          {/* Top Left: DI Container */}
          <circle cx="100" cy="100" r="20" fill="#18181b" stroke="#10b981" strokeWidth="2" />
          <text x="100" y="103" textAnchor="middle" fill="#10b981" fontSize="8" fontWeight="bold" fontFamily="monospace">DI</text>
          <text x="100" y="74" textAnchor="middle" fill="rgba(255,255,255,0.5)" fontSize="9" fontFamily="sans-serif">DI Containers</text>

          {/* Top Right: ASGI Adapter */}
          <circle cx="500" cy="100" r="20" fill="#18181b" stroke="#3b82f6" strokeWidth="2" />
          <text x="500" y="103" textAnchor="middle" fill="#3b82f6" fontSize="8" fontWeight="bold" fontFamily="monospace">ASGI</text>
          <text x="500" y="74" textAnchor="middle" fill="rgba(255,255,255,0.5)" fontSize="9" fontFamily="sans-serif">ASGI Adapter</text>

          {/* Bottom Left: Registry */}
          <circle cx="100" cy="220" r="20" fill="#18181b" stroke="#ec4899" strokeWidth="2" />
          <text x="100" y="223" textAnchor="middle" fill="#ec4899" fontSize="8" fontWeight="bold" fontFamily="monospace">REG</text>
          <text x="100" y="254" textAnchor="middle" fill="rgba(255,255,255,0.5)" fontSize="9" fontFamily="sans-serif">App Registry</text>

          {/* Bottom Right: Engine */}
          <circle cx="500" cy="220" r="20" fill="#18181b" stroke="#8b5cf6" strokeWidth="2" />
          <text x="500" y="223" textAnchor="middle" fill="#8b5cf6" fontSize="8" fontWeight="bold" fontFamily="monospace">ENG</text>
          <text x="500" y="254" textAnchor="middle" fill="rgba(255,255,255,0.5)" fontSize="9" fontFamily="sans-serif">Controller Engine</text>

          {/* Interactive animated flow indicator */}
          <circle r="4" fill="#f59e0b">
            <animateMotion dur="4s" repeatCount="indefinite" path="M 300 160 Q 200 100 100 100" />
          </circle>
          <circle r="4" fill="#f59e0b">
            <animateMotion dur="3s" repeatCount="indefinite" path="M 300 160 Q 400 100 500 100" />
          </circle>
        </svg>
      </div>

      {/* Constructor */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Settings className="w-5 h-5 text-aquilia-400" />
          Constructor
        </h2>

        <CodeBlock
          code={`from aquilia.server import AquiliaServer
from aquilia.config import ConfigLoader
from aquilia.aquilary import RegistryMode

server = AquiliaServer(
    manifests=[CoreManifest, UsersManifest],  # List of manifest classes
    config=ConfigLoader(),                     # Optional: custom config loader
    mode=RegistryMode.PROD,                    # DEV, PROD, or TEST
    aquilary_registry=None,                    # Optional: pre-built AquilaryRegistry
)`}
          language="python"
        />

        <div className={`mt-4 rounded-xl border overflow-hidden ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={isDark ? 'bg-zinc-800/80' : 'bg-gray-50'}>
                <th className={`text-left px-4 py-3 font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Parameter</th>
                <th className={`text-left px-4 py-3 font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Type</th>
                <th className={`text-left px-4 py-3 font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5' : 'divide-gray-100'}`}>
              {[
                ['manifests', 'List[Any] | None', 'List of manifest classes. Required unless aquilary_registry is provided.'],
                ['config', 'ConfigLoader | None', 'Configuration loader instance. Created automatically if None.'],
                ['mode', 'RegistryMode', 'Registry mode: DEV (relaxed), PROD (strict), TEST (mocks). Default: PROD.'],
                ['aquilary_registry', 'AquilaryRegistry | None', 'Pre-built registry for advanced usage. Bypasses manifest compilation.'],
              ].map(([param, type, desc], i) => (
                <tr key={i} className={isDark ? 'hover:bg-white/5' : 'hover:bg-gray-50'}>
                  <td className={`px-4 py-2 font-mono text-xs ${isDark ? 'text-aquilia-400' : 'text-aquilia-600'}`}>{param}</td>
                  <td className={`px-4 py-2 font-mono text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>{type}</td>
                  <td className={`px-4 py-2 text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Initialization sequence */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Zap className="w-5 h-5 text-aquilia-400" />
          Initialization Sequence
        </h2>

        <p className={`mb-4 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The <code>__init__</code> method performs the following steps in order. Understanding this
          sequence is critical for debugging boot issues:
        </p>

        <CodeBlock
          code={`# AquiliaServer.__init__() sequence:

# 1. Load configuration
self.config = config or ConfigLoader()

# 2. Initialize fault engine
self.fault_engine = FaultEngine(debug=self._is_debug())

# 3. Apply fault integration patches to subsystems
from aquilia.faults.integrations import patch_all_subsystems
patch_all_subsystems()

# 4. Build Aquilary registry from manifests
self.aquilary = Aquilary.from_manifests(
    manifests=manifests,
    config=self.config,
    mode=mode,
)

# 5. Create RuntimeRegistry (lazy compilation)
self.runtime = RuntimeRegistry.from_metadata(self.aquilary, self.config)
self.runtime._register_services()  # Populate DI containers immediately

# 6. Register framework services in every DI container
#    - FaultEngine (scope: app)
#    - EffectRegistry (scope: app)

# 7. Create LifecycleCoordinator
self.coordinator = LifecycleCoordinator(self.runtime, self.config)

# 8. Setup middleware stack
#    - ExceptionMiddleware (priority: 1)
#    - FaultMiddleware (priority: 2)
#    - ProxyFixMiddleware (priority: 3)
#    - HTTPSRedirectMiddleware (priority: 4)
#    - ServerRequestScopeMiddleware / VersionMiddleware (priority: 5)
#    - StaticMiddleware (priority: 6)
#    - SecurityHeadersMiddleware (priority: 7)
#    - HSTSMiddleware (priority: 8)
#    - CSPMiddleware (priority: 9)
#    - RequestIdMiddleware (priority: 10)
#    - CORSMiddleware / InspectorMiddleware (priority: 11)
#    - RateLimitMiddleware / ToolbarInjectionMiddleware (priority: 12)
#    - SessionMiddleware / AquilAuthMiddleware (priority: 15)
#    - CSRFMiddleware (priority: 20)
#    - I18nMiddleware (priority: 24)
#    - TemplateMiddleware (priority: 25)
#    - CacheMiddleware (priority: 26)

# 9. Create controller pipeline
#    - ControllerFactory (with base DI container)
#    - ControllerEngine (with fault engine)
#    - ControllerCompiler

# 10. Create ASGI adapter
self.app = ASGIAdapter(
    controller_router=self.controller_router,
    controller_engine=self.controller_engine,
    socket_runtime=self.aquila_sockets,
    middleware_stack=self.middleware_stack,
    server=self,
)`}
          language="python"
        />
      </section>

      {/* Key Attributes */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Database className="w-5 h-5 text-aquilia-400" />
          Key Attributes
        </h2>

        <div className={`rounded-xl border overflow-hidden ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={isDark ? 'bg-zinc-800/80' : 'bg-gray-50'}>
                <th className={`text-left px-4 py-3 font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Attribute</th>
                <th className={`text-left px-4 py-3 font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Type</th>
                <th className={`text-left px-4 py-3 font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5' : 'divide-gray-100'}`}>
              {[
                ['config', 'ConfigLoader', 'Merged configuration object with layered resolution'],
                ['fault_engine', 'FaultEngine', 'Fault signal processor with handler chain'],
                ['aquilary', 'AquilaryRegistry', 'Compiled manifest registry with app metadata'],
                ['runtime', 'RuntimeRegistry', 'DI containers, compiled routes, model schemas'],
                ['coordinator', 'LifecycleCoordinator', 'Dependency-ordered startup/shutdown manager'],
                ['controller_router', 'ControllerRouter', 'URL pattern → CompiledRoute matcher'],
                ['controller_engine', 'ControllerEngine', 'Route dispatch and pipeline execution'],
                ['controller_factory', 'ControllerFactory', 'Controller instantiation with DI'],
                ['controller_compiler', 'ControllerCompiler', 'Decorator metadata → CompiledRoute'],
                ['middleware_stack', 'MiddlewareStack', 'Priority-ordered middleware chain'],
                ['aquila_sockets', 'AquilaSockets', 'WebSocket runtime (if configured)'],
                ['app', 'ASGIAdapter', 'The callable ASGI application'],
              ].map(([attr, type, desc], i) => (
                <tr key={i} className={isDark ? 'hover:bg-white/5' : 'hover:bg-gray-50'}>
                  <td className={`px-4 py-2 font-mono text-xs ${isDark ? 'text-aquilia-400' : 'text-aquilia-600'}`}>{attr}</td>
                  <td className={`px-4 py-2 font-mono text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                    {type === 'LifecycleCoordinator' ? (
                      <DocTerm id="lifecycle.coordinator">{type}</DocTerm>
                    ) : (
                      type
                    )}
                  </td>
                  <td className={`px-4 py-2 text-xs ${isDark ? 'text-gray-400' : 'text-gray-505'}`}>{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Middleware Setup */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-400" />
          Middleware Setup
        </h2>

        <p className={`mb-4 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The <code>_setup_middleware()</code> method builds the middleware stack from configuration.
          Middleware is added conditionally based on what integrations are enabled:
        </p>

        <CodeBlock
          code={`# Always added in the pipeline:
ExceptionMiddleware(debug=True)      # Priority 1 — global exception handling
FaultMiddleware(fault_engine)         # Priority 2 — converts fault signals to HTTP responses
ServerRequestScopeMiddleware(...)     # Priority 5 — initializes/tears down request-scoped DI container

# Added if versions configured:
VersionMiddleware(strategy)           # Priority 5 — API version resolution

# Added if sessions/auth configured:
SessionMiddleware(session_engine)     # Priority 15 — loads and saves session state
AquilAuthMiddleware(...)              # Priority 15 — unified auth and identity extraction

# Added if templates configured:
TemplateMiddleware(...)               # Priority 25 — injects template engine and rendering helper

# Added if caching configured:
CacheMiddleware(...)                  # Priority 26 — caches GET responses

# Security & Infrastructure Middleware (via _setup_security_middleware):
ProxyFixMiddleware(...)               # Priority 3 — handles trust-proxy headers
HTTPSRedirectMiddleware(...)          # Priority 4 — redirects HTTP to HTTPS
StaticMiddleware(...)                 # Priority 6 — serves static files directly
SecurityHeadersMiddleware(...)        # Priority 7 — security response headers
HSTSMiddleware(...)                   # Priority 8 — Strict-Transport-Security header
CSPMiddleware(...)                    # Priority 9 — Content-Security-Policy header & nonces
CORSMiddleware(...)                   # Priority 11 — CORS preflight and access control
RateLimitMiddleware(...)              # Priority 12 — sliding window request rate limiting
CSRFMiddleware(...)                   # Priority 20 — CSRF token validation
I18nMiddleware(...)                   # Priority 24 — locale resolution and translating

# Development/Inspector Middleware:
RequestIdMiddleware()                 # Priority 10 — request trace ID generator (default/fallback)
InspectorMiddleware(...)              # Priority 11 — captures debugging statistics
ToolbarInjectionMiddleware(...)      # Priority 12 — injects dev diagnostics toolbar`}
          language="python"
        />
      </section>

      {/* Session Engine Creation */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Shield className="w-5 h-5 text-aquilia-400" />
          Session & Auth Setup
        </h2>

        <p className={`mb-4 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The server supports configuration for sessions using the typed <code>SessionIntegration</code> class:
        </p>

        <CodeBlock
          code={`# SessionIntegration class (recommended)
from aquilia.integrations import SessionIntegration
from aquilia.sessions import SessionPolicy, MemoryStore, CookieTransport

workspace = (
    Workspace("myapp")
    .integrate(SessionIntegration(
        policy=SessionPolicy.for_web_users()
            .lasting(days=14)
            .idle_timeout(hours=2)
            .rotating_on_privilege_change()
            .scoped_to("tenant"),
        store=MemoryStore.with_capacity(50000),
        transport=CookieTransport.secure_defaults(),
    ))
)`}
          language="python"
        />
      </section>

      {/* startup/shutdown */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Zap className="w-5 h-5 text-aquilia-400" />
          Startup & Shutdown
        </h2>

        <CodeBlock
          code={`# startup() is called automatically by the ASGI adapter on first request,
# or can be called manually:

await server.startup()
# 1. Idempotent: uses asyncio.Lock to prevent double startup
# 2. Loads controllers from RuntimeRegistry
# 3. Registers OpenAPI docs routes (if configured)
# 4. Loads WebSocket controllers
# 5. Registers AMDL models (legacy support, 5 phases)
# 6. Runs LifecycleCoordinator.startup() — executes all on_startup hooks
# 7. Sets self._startup_complete = True

await server.shutdown()
# 1. Runs LifecycleCoordinator.shutdown() — reverse dependency order
# 2. Closes all DI container finalizers
# 3. Shuts down WebSocket connections
# 4. Logs shutdown summary`}
          language="python"
        />
      </section>

      {/* run() method */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Globe className="w-5 h-5 text-aquilia-400" />
          Running the Server
        </h2>

        <CodeBlock
          code={`# Using the run() convenience method (wraps uvicorn):
server.run(host="0.0.0.0", port=8000)

# Or use the ASGI adapter directly with any ASGI server:
import uvicorn
uvicorn.run(server.app, host="0.0.0.0", port=8000)

# Or with hypercorn:
import asyncio
from hypercorn.asyncio import serve
from hypercorn.config import Config

config = Config()
config.bind = ["0.0.0.0:8000"]
asyncio.run(serve(server.app, config))`}
          language="python"
        />

        <div className="mt-4 text-sm leading-relaxed">
          <p className={isDark ? 'text-aquilia-400' : 'text-aquilia-700'}>
            <strong>Production tip:</strong> Use <code>aq serve</code> for production deployments. It
            runs uvicorn with production-optimized settings (no reload, access logs, worker configuration).
            Use <code>aq run</code> for development (auto-reload enabled).
          </p>
        </div>
      </section>

      {/* Debug mode */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <AlertCircle className="w-5 h-5 text-aquilia-400" />
          Debug Mode
        </h2>

        <p className={`mb-4 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          When <code>debug=True</code> (via config, <code>AQ_DEBUG=true</code>, or <code>RegistryMode.DEV</code>),
          the server enables:
        </p>

        <ul className={`space-y-2 text-sm leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          <li className="flex items-start gap-2">
            <span className="text-aquilia-400 mt-1">•</span>
            <div><strong>Debug error pages</strong> — ExceptionMiddleware renders rich HTML error pages with tracebacks, request details, and source code context</div>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-aquilia-400 mt-1">•</span>
            <div><strong>Verbose logging</strong> — Full request/response body logging</div>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-aquilia-400 mt-1">•</span>
            <div><strong>Relaxed validation</strong> — Missing optional providers don't cause boot failures</div>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-aquilia-400 mt-1">•</span>
            <div><strong>Auto-reload</strong> — File watcher restarts server on code changes (uvicorn --reload)</div>
          </li>
        </ul>
      </section>

      {/* Next */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Related</h2>
        <div className="flex flex-col gap-2">
          <Link to="/docs/server/asgi" className={`text-sm font-medium ${isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-500'}`}>
            → ASGI Adapter: How Aquilia bridges ASGI and its internal pipeline
          </Link>
          <Link to="/docs/server/lifecycle" className={`text-sm font-medium ${isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-500'}`}>
            → Lifecycle: Dependency-ordered startup/shutdown coordination
          </Link>
          <Link to="/docs/middleware/stack" className={`text-sm font-medium ${isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-500'}`}>
            → MiddlewareStack: How middleware ordering works
          </Link>
        </div>
      </section>

      <NextSteps />
    </div>
  )
}