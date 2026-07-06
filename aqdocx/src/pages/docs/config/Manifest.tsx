import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Package, Layers, AlertTriangle, CheckCircle, GitBranch } from 'lucide-react'

export function ConfigManifest() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const txt = isDark ? 'text-gray-300' : 'text-gray-600'
  const subtxt = isDark ? 'text-gray-400' : 'text-gray-500'
  const head = isDark ? 'text-white' : 'text-gray-900'
  const divider = isDark ? 'divide-white/5' : 'divide-gray-100'
  const thead = isDark ? 'bg-zinc-800/80' : 'bg-gray-50'
  const th = isDark ? 'text-gray-300' : 'text-gray-700'
  const hover = isDark ? 'hover:bg-white/5' : 'hover:bg-gray-50'
  const border = isDark ? 'border-white/10' : 'border-gray-200'

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-10">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-aquilia-500/30 to-aquilia-500/10 flex items-center justify-center shadow-lg shadow-aquilia-500/10">
            <Package className="w-5 h-5 text-aquilia-400" />
          </div>
          <div>
            <h1 className={`text-4xl ${head}`}>
              <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
                AppManifest
                <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
              </span>
            </h1>
            <p className={`text-sm ${subtxt}`}>aquilia.manifest — per-module component registry</p>
          </div>
        </div>

        <p className={`text-lg leading-relaxed ${txt}`}>
          Every module in Aquilia has a <DocTerm id="config.appmanifest">AppManifest</DocTerm> — a dataclass that acts as the definitive component registry for that module. It declares exactly which controllers, services, models, guards, tasks and middleware this module contributes to the application. The <DocTerm id="config.module">Module</DocTerm> in <code>workspace.py</code> is just a pointer; the manifest is the source of truth.
        </p>
      </div>

      {/* Manifest-first architecture diagram */}
      <div className="w-full h-64 flex items-center justify-center my-6">
        <svg className="w-full h-full max-w-2xl" viewBox="0 0 600 240" fill="none">
          <defs>
            <linearGradient id="mfGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.6" />
              <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0.6" />
            </linearGradient>
          </defs>

          {/* workspace.py box */}
          <rect x="20" y="80" width="140" height="80" rx="12" fill="none" stroke="rgba(245,158,11,0.4)" strokeWidth="1.5" />
          <text x="90" y="106" textAnchor="middle" fill="#f59e0b" fontSize="10" fontWeight="bold" fontFamily="monospace">workspace.py</text>
          <text x="90" y="122" textAnchor="middle" fill="rgba(255,255,255,0.4)" fontSize="8" fontFamily="sans-serif">Workspace("myapp")</text>
          <text x="90" y="136" textAnchor="middle" fill="rgba(255,255,255,0.3)" fontSize="7" fontFamily="sans-serif">.module(Module("users"))</text>
          <text x="90" y="148" textAnchor="middle" fill="rgba(255,255,255,0.3)" fontSize="7" fontFamily="sans-serif">.integrate(...)</text>

          {/* Arrow workspace → manifest */}
          <path d="M 162 120 L 218 120" stroke="url(#mfGrad)" strokeWidth="1.5" markerEnd="url(#arrow)" />
          <text x="190" y="112" textAnchor="middle" fill="rgba(255,255,255,0.3)" fontSize="7" fontFamily="sans-serif">pointer</text>

          <defs>
            <marker id="arrow" markerWidth="6" markerHeight="6" refX="3" refY="3" orient="auto">
              <path d="M0,0 L6,3 L0,6 Z" fill="rgba(255,255,255,0.3)" />
            </marker>
          </defs>

          {/* manifest.py box */}
          <rect x="220" y="50" width="165" height="140" rx="12" fill="none" stroke="rgba(139,92,246,0.5)" strokeWidth="1.5" />
          <text x="302" y="76" textAnchor="middle" fill="#8b5cf6" fontSize="10" fontWeight="bold" fontFamily="monospace">manifest.py</text>
          <text x="302" y="93" textAnchor="middle" fill="rgba(255,255,255,0.4)" fontSize="8" fontFamily="sans-serif">AppManifest(</text>
          <text x="302" y="107" textAnchor="middle" fill="#10b981" fontSize="7" fontFamily="monospace">  controllers=[...]</text>
          <text x="302" y="120" textAnchor="middle" fill="#3b82f6" fontSize="7" fontFamily="monospace">  services=[...]</text>
          <text x="302" y="133" textAnchor="middle" fill="#f59e0b" fontSize="7" fontFamily="monospace">  models=[...]</text>
          <text x="302" y="146" textAnchor="middle" fill="#ec4899" fontSize="7" fontFamily="monospace">  guards=[...]</text>
          <text x="302" y="159" textAnchor="middle" fill="#8b5cf6" fontSize="7" fontFamily="monospace">  exports=[...]</text>
          <text x="302" y="172" textAnchor="middle" fill="rgba(255,255,255,0.4)" fontSize="8" fontFamily="sans-serif">)</text>

          {/* Arrow manifest → runtime */}
          <path d="M 387 120 L 440 120" stroke="url(#mfGrad)" strokeWidth="1.5" markerEnd="url(#arrow)" />
          <text x="414" y="112" textAnchor="middle" fill="rgba(255,255,255,0.3)" fontSize="7" fontFamily="sans-serif">compiled</text>

          {/* Runtime registry */}
          <rect x="442" y="80" width="140" height="80" rx="12" fill="none" stroke="rgba(16,185,129,0.4)" strokeWidth="1.5" />
          <text x="512" y="106" textAnchor="middle" fill="#10b981" fontSize="10" fontWeight="bold" fontFamily="monospace">RuntimeRegistry</text>
          <text x="512" y="122" textAnchor="middle" fill="rgba(255,255,255,0.4)" fontSize="8" fontFamily="sans-serif">routes compiled</text>
          <text x="512" y="136" textAnchor="middle" fill="rgba(255,255,255,0.3)" fontSize="7" fontFamily="sans-serif">DI containers wired</text>
          <text x="512" y="150" textAnchor="middle" fill="rgba(255,255,255,0.3)" fontSize="7" fontFamily="sans-serif">models registered</text>

          <text x="300" y="220" textAnchor="middle" fill="rgba(255,255,255,0.2)" fontSize="8" fontFamily="sans-serif">Manifest-First Architecture — workspace.py is the orchestrator, manifest.py is the source of truth</text>
        </svg>
      </div>

      {/* Quickstart */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <CheckCircle className="w-5 h-5 text-aquilia-400" />
          Minimal manifest
        </h2>
        <p className={`mb-4 ${txt}`}>
          Create <code>modules/users/manifest.py</code>. Every component is declared as a dot-path string in the form <code>"module.path:ClassName"</code>. Auto-discovery (<code>auto_discover=True</code>) also scans <code>controllers/</code>, <code>services/</code>, <code>models/</code>, <code>tasks/</code> inside the module directory by convention.
        </p>
        <CodeBlock language="python" code={`# modules/users/manifest.py
from aquilia.manifest import AppManifest

manifest = AppManifest(
    name="users",
    version="0.1.0",
    description="User management — CRUD, profile, roles",

    controllers=["modules.users.controllers:UsersController"],
    services=["modules.users.services:UsersService"],
    models=["modules.users.models:User", "modules.users.models:Role"],

    # Exports make UsersService visible to other modules that import "users"
    exports=["UsersService"],
)`} />
      </section>

      {/* Full field reference */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Layers className="w-5 h-5 text-aquilia-400" />
          Full field reference
        </h2>
        <div className={`rounded-xl border overflow-hidden ${border}`}>
          <table className="w-full text-sm">
            <thead><tr className={thead}>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>Field</th>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>Type</th>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>Description</th>
            </tr></thead>
            <tbody className={`divide-y ${divider}`}>
              {[
                ['name', 'str (required)', 'Module identifier — must match the Module("name") pointer in workspace.py'],
                ['version', 'str', 'Semantic version string, e.g. "0.2.0"'],
                ['description', 'str', 'Human-readable description of the module\'s purpose'],
                ['author', 'str', 'Module author name for manifest inspection'],
                ['controllers', 'list[str | ComponentRef]', 'HTTP controllers. Each entry is a dot-path string or ComponentRef'],
                ['services', 'list[str | ServiceConfig | ComponentRef]', 'Dependency-injected services. Accepts strings, ServiceConfig with scope, or ComponentRef'],
                ['models', 'list[str | ComponentRef]', 'ORM model classes to register for migration scanning and QuerySet generation'],
                ['serializers', 'list[str | ComponentRef]', 'Blueprint serializer classes'],
                ['socket_controllers', 'list[str | ComponentRef]', 'WebSocket controllers. Requires WebSocket integration'],
                ['guards', 'list[str | ComponentRef]', 'v2: Auth/authorization gates applied before route handlers'],
                ['pipes', 'list[str | ComponentRef]', 'v2: Input transformation and validation pipes'],
                ['interceptors', 'list[str | ComponentRef]', 'v2: Cross-cutting concerns (logging, caching, metrics)'],
                ['middleware', 'list[str | MiddlewareConfig | ComponentRef]', 'Module-scoped middleware with optional priority and scope'],
                ['exports', 'list[str]', 'Service class names made visible to importing modules via DI'],
                ['imports', 'list[str]', 'Module names whose exports this module can inject'],
                ['lifecycle', 'LifecycleConfig | None', 'Startup/shutdown hooks with timeout and error strategy'],
                ['auto_discover', 'bool (default True)', 'Enable convention-based scanning of controllers/, services/, models/, guards/, tasks/'],
                ['discover_patterns', 'list[str]', 'Subdirectory names to scan when auto_discover=True'],
                ['tags', 'list[str]', 'Arbitrary tags for grouping, filtering, and OpenAPI organisation'],
              ].map(([field, type, desc], i) => (
                <tr key={i} className={hover}>
                  <td className="px-4 py-3 font-mono text-xs text-aquilia-400 whitespace-nowrap">{field}</td>
                  <td className={`px-4 py-3 font-mono text-xs ${subtxt} whitespace-nowrap`}>{type}</td>
                  <td className={`px-4 py-3 text-xs ${txt}`}>{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* ComponentRef */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>ComponentRef — typed references</h2>
        <p className={`mb-4 ${txt}`}>
          When you need to attach metadata to a component declaration (DI scope, priority, feature flags), use <code>ComponentRef</code> instead of a bare string.
        </p>
        <CodeBlock language="python" code={`from aquilia.manifest import AppManifest, ComponentRef, ComponentKind, ServiceConfig, ServiceScope

manifest = AppManifest(
    name="auth",
    version="0.1.0",

    services=[
        # Simple string path (app scope by default)
        "modules.auth.services:AuthService",

        # ServiceConfig — full control over scope and lifecycle
        ServiceConfig(
            class_path="modules.auth.services:TokenRefreshService",
            scope=ServiceScope.REQUEST,     # New instance per request
            aliases=["TokenService"],       # Alternative injection name
            tag="token",                    # For Inject(tag="token") resolution
        ),
    ],

    guards=[
        ComponentRef(
            "modules.auth.guards:JWTGuard",
            ComponentKind.GUARD,
            metadata={"priority": 10},
        ),
    ],
)`} />
      </section>

      {/* Service scopes */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>Service scopes</h2>
        <div className={`rounded-xl border overflow-hidden ${border}`}>
          <table className="w-full text-sm">
            <thead><tr className={thead}>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>Scope</th>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>Lifetime</th>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>Use for</th>
            </tr></thead>
            <tbody className={`divide-y ${divider}`}>
              {[
                ['SINGLETON', 'One instance for the entire process', 'Config objects, connection pools, global caches'],
                ['APP', 'One per module DI container (default)', 'Most services — database sessions, repositories'],
                ['REQUEST', 'New instance per HTTP request', 'Services that must not leak state across requests'],
                ['TRANSIENT', 'Always a new instance on injection', 'Lightweight value objects, formatters'],
                ['POOLED', 'Object pool — acquire/release', 'Expensive resources with bounded concurrency'],
                ['EPHEMERAL', 'Fastest — no lifecycle hooks', 'Pure functions wrapped as services'],
              ].map(([scope, lifetime, use]) => (
                <tr key={scope as string} className={hover}>
                  <td className="px-4 py-3 font-mono text-xs text-aquilia-400">{scope}</td>
                  <td className={`px-4 py-3 text-xs ${subtxt}`}>{lifetime}</td>
                  <td className={`px-4 py-3 text-xs ${txt}`}>{use}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Lifecycle hooks in manifest */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <GitBranch className="w-5 h-5 text-aquilia-400" />
          Lifecycle hooks via LifecycleConfig
        </h2>
        <p className={`mb-4 ${txt}`}>
          Module-level startup and shutdown hooks are declared as dot-path strings in a <code>LifecycleConfig</code>. The coordinator resolves and calls them in topological dependency order during server boot.
        </p>
        <CodeBlock language="python" code={`from aquilia.manifest import AppManifest, LifecycleConfig

manifest = AppManifest(
    name="workers",
    version="0.1.0",

    lifecycle=LifecycleConfig(
        on_startup="modules.workers.hooks:startup",   # async def startup(config_ns, di_container)
        on_shutdown="modules.workers.hooks:shutdown", # async def shutdown(config_ns, di_container)
        depends_on=["database", "cache"],             # Wait for these modules to boot first
        startup_timeout=30.0,                         # Seconds before giving up
        shutdown_timeout=30.0,
        error_strategy="propagate",                   # "propagate" | "log" | "ignore"
    ),
)`} />
      </section>

      {/* Cross-module exports/imports */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>Cross-module exports and imports</h2>
        <p className={`mb-4 ${txt}`}>
          Aquilia's DI system is module-scoped by default — one DI container per module. To share a service across modules, <strong>export</strong> it from the provider module and <strong>import</strong> the module name in the consumer.
        </p>
        <CodeBlock language="python" code={`# modules/auth/manifest.py — provider
manifest = AppManifest(
    name="auth",
    services=["modules.auth.services:AuthService", "modules.auth.services:JWTService"],
    exports=["AuthService", "JWTService"],   # ← visible to importers
)

# modules/users/manifest.py — consumer
manifest = AppManifest(
    name="users",
    imports=["auth"],                        # ← resolves auth's exports into users' DI container
    services=["modules.users.services:UsersService"],
)

# modules/users/services.py
class UsersService:
    def __init__(self, auth: AuthService):   # ← injected from auth module
        self.auth = auth`} />
      </section>

      {/* Deprecated fields */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 text-amber-500`}>
          <AlertTriangle className="w-5 h-5" />
          Deprecated fields
        </h2>
        <p className={`mb-4 text-sm ${txt}`}>
          These fields still work at runtime but emit <code>DeprecationWarning</code>. Migrate to the current alternatives before the next major release.
        </p>
        <div className={`rounded-xl border border-amber-500/20 overflow-hidden`}>
          <table className="w-full text-sm">
            <thead><tr className={`${isDark ? 'bg-amber-900/20' : 'bg-amber-50'}`}>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>Deprecated field</th>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>Replacement</th>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>Notes</th>
            </tr></thead>
            <tbody className={`divide-y ${divider}`}>
              {[
                ['route_prefix', 'Module.route_prefix() in workspace.py', 'Routing topology belongs in the workspace orchestration layer, not the manifest'],
                ['database', 'DatabaseIntegration in workspace.py', 'Ignored at runtime; database config lives in workspace integrations'],
                ['on_startup / on_shutdown (Callable)', 'LifecycleConfig(on_startup="path:fn")', 'Pass a dot-path string, not a callable — enables lazy loading and serialisation'],
                ['middlewares (old list[tuple] format)', 'middleware: list[str | MiddlewareConfig]', 'Use the typed MiddlewareConfig dataclass instead of raw (class_path, kwargs) tuples'],
                ['config (type)', 'AquilaConfig in workspace.py', 'Config classes belong in workspace.py, not in the module manifest'],
                ['depends_on', 'imports', 'imports is the canonical dependency declaration; depends_on is kept for backward compat'],
              ].map(([deprecated, replacement, notes], i) => (
                <tr key={i} className={hover}>
                  <td className="px-4 py-3 font-mono text-xs text-amber-400 whitespace-nowrap">{deprecated}</td>
                  <td className={`px-4 py-3 font-mono text-xs text-aquilia-400`}>{replacement}</td>
                  <td className={`px-4 py-3 text-xs ${subtxt}`}>{notes}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* auto_discover */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>auto_discover — convention over configuration</h2>
        <p className={`mb-4 ${txt}`}>
          When <code>auto_discover=True</code> (the default), Aquilia scans the following subdirectories inside the module package directory and auto-registers anything it finds that matches the expected base classes:
        </p>
        <CodeBlock language="text" code={`modules/
└── users/
    ├── manifest.py         ← AppManifest lives here
    ├── controllers/        ← auto-discovered: Controller subclasses
    ├── services/           ← auto-discovered: any class registered as service
    ├── models/             ← auto-discovered: Model subclasses
    ├── guards/             ← auto-discovered: Guard subclasses
    └── tasks/              ← auto-discovered: @task decorated functions`} />
        <p className={`mt-4 text-sm ${txt}`}>
          Override the scan directories with <code>discover_patterns=["controllers", "services", "validators"]</code> or disable scanning entirely with <code>auto_discover=False</code> to require explicit declarations only.
        </p>
      </section>

      {/* Related */}
      <section className="mb-12 border-t border-white/5 pt-8">
        <div className="flex flex-col gap-2">
          <Link to="/docs/config/module" className={`text-sm font-medium ${isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-500'}`}>
            → Module: workspace-level orchestration pointer
          </Link>
          <Link to="/docs/config/workspace" className={`text-sm font-medium ${isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-500'}`}>
            → Workspace: wiring modules together
          </Link>
          <Link to="/docs/di/overview" className={`text-sm font-medium ${isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-500'}`}>
            → DI: how exports/imports resolve into containers
          </Link>
        </div>
      </section>

      <NextSteps />
    </div>
  )
}
