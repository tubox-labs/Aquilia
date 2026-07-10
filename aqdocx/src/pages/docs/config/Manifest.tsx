import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import {
  Package, Layers, AlertTriangle, CheckCircle, GitBranch,
  Shield, ArrowRight, Cpu, Zap, Hash,
} from 'lucide-react'

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
            <p className={`text-sm ${subtxt}`}>aquilia.manifest — per-module component registry & request-pipeline declaration</p>
          </div>
        </div>

        <p className={`text-lg leading-relaxed ${txt}`}>
          Every module in Aquilia has an <DocTerm id="config.appmanifest">AppManifest</DocTerm> — a dataclass that acts as the definitive component registry for that module. It declares which controllers, services, models, guards, pipes, interceptors, tasks, and middleware the module contributes. The <DocTerm id="config.module">Module</DocTerm> in <code>workspace.py</code> is just a name pointer; the <code>manifest.py</code> inside the module directory is the source of truth. No import-time side effects, fully serialisable, inspectable, and fingerprint-stable.
        </p>
      </div>

      {/* Architecture diagram — flow-based, premium */}
      <div className="mb-12 w-full">
        <svg className="w-full" viewBox="0 0 740 300" fill="none">
          <defs>
            <linearGradient id="mfg1" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.7" />
              <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0.7" />
            </linearGradient>
            <linearGradient id="mfg2" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.7" />
              <stop offset="100%" stopColor="#10b981" stopOpacity="0.7" />
            </linearGradient>
            <linearGradient id="mfgv" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#10b981" stopOpacity="0.6" />
              <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.3" />
            </linearGradient>
            <marker id="ma" markerWidth="7" markerHeight="7" refX="3.5" refY="3.5" orient="auto">
              <path d="M0,0 L7,3.5 L0,7 Z" fill="rgba(255,255,255,0.25)" />
            </marker>
            <filter id="glow">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
            </filter>
          </defs>

          {/* ── workspace.py ─────────────────────────────────── */}
          <rect x="10" y="100" width="148" height="100" rx="14"
            fill="rgba(245,158,11,0.05)" stroke="rgba(245,158,11,0.35)" strokeWidth="1.5" />
          <text x="84" y="125" textAnchor="middle" fill="#f59e0b" fontSize="9.5" fontWeight="700" fontFamily="monospace">workspace.py</text>
          <text x="84" y="142" textAnchor="middle" fill="rgba(255,255,255,0.35)" fontSize="7.5" fontFamily="monospace">Workspace("myapp")</text>
          <text x="84" y="157" textAnchor="middle" fill="rgba(255,255,255,0.25)" fontSize="7" fontFamily="monospace">.module(Module("users"))</text>
          <text x="84" y="170" textAnchor="middle" fill="rgba(255,255,255,0.25)" fontSize="7" fontFamily="monospace">.module(Module("auth"))</text>
          <text x="84" y="183" textAnchor="middle" fill="rgba(255,255,255,0.25)" fontSize="7" fontFamily="monospace">.integrate(...)</text>

          {/* arrow workspace → manifest */}
          <path d="M 160 150 L 210 150" stroke="url(#mfg1)" strokeWidth="1.5" markerEnd="url(#ma)" />
          <text x="185" y="142" textAnchor="middle" fill="rgba(255,255,255,0.2)" fontSize="7" fontFamily="sans-serif">resolves</text>

          {/* ── AppManifest box ──────────────────────────────── */}
          <rect x="212" y="40" width="200" height="220" rx="14"
            fill="rgba(139,92,246,0.04)" stroke="rgba(139,92,246,0.45)" strokeWidth="1.5" />

          {/* manifest.py label */}
          <text x="312" y="66" textAnchor="middle" fill="#8b5cf6" fontSize="9.5" fontWeight="700" fontFamily="monospace">modules/users/manifest.py</text>
          <text x="312" y="80" textAnchor="middle" fill="rgba(255,255,255,0.3)" fontSize="7.5" fontFamily="sans-serif">AppManifest(name="users", ...)</text>

          {/* divider */}
          <line x1="228" y1="88" x2="396" y2="88" stroke="rgba(139,92,246,0.2)" strokeWidth="1" />

          {/* Component pills inside manifest */}
          {[
            { y: 105, label: 'controllers',       color: '#10b981', sub: 'HTTP route handlers' },
            { y: 123, label: 'services',           color: '#3b82f6', sub: 'DI-managed services' },
            { y: 141, label: 'models',             color: '#f59e0b', sub: 'ORM model classes' },
            { y: 159, label: 'guards',             color: '#ec4899', sub: 'auth/authz gates' },
            { y: 177, label: 'pipes',              color: '#f97316', sub: 'input transformation' },
            { y: 195, label: 'interceptors',       color: '#a855f7', sub: 'cross-cutting concerns' },
            { y: 213, label: 'middleware',         color: '#64748b', sub: 'request pipeline' },
            { y: 231, label: 'socket_controllers', color: '#06b6d4', sub: 'WebSocket handlers' },
            { y: 249, label: 'background_tasks',   color: '#d97706', sub: 'task references' },
          ].map(({ y, label, color, sub }) => (
            <g key={label}>
              <rect x="228" y={y - 9} width="174" height="14" rx="4" fill="rgba(0,0,0,0.0)" />
              <circle cx="240" cy={y - 1} r="3" fill={color} opacity="0.7" />
              <text x="249" y={y + 2} fill={color} fontSize="7.5" fontWeight="600" fontFamily="monospace">{label}</text>
              <text x="340" y={y + 2} fill="rgba(255,255,255,0.25)" fontSize="6.5" fontFamily="sans-serif">{sub}</text>
            </g>
          ))}

          {/* arrow manifest → pipeline */}
          <path d="M 414 150 L 466 150" stroke="url(#mfg2)" strokeWidth="1.5" markerEnd="url(#ma)" />
          <text x="440" y="142" textAnchor="middle" fill="rgba(255,255,255,0.2)" fontSize="7" fontFamily="sans-serif">compiled</text>

          {/* ── Runtime subsystems ──────────────────────────── */}
          <rect x="468" y="40" width="258" height="220" rx="14"
            fill="rgba(16,185,129,0.03)" stroke="rgba(16,185,129,0.35)" strokeWidth="1.5" />
          <text x="597" y="66" textAnchor="middle" fill="#10b981" fontSize="9.5" fontWeight="700" fontFamily="monospace">Runtime Subsystems</text>
          <line x1="484" y1="74" x2="710" y2="74" stroke="rgba(16,185,129,0.2)" strokeWidth="1" />

          {[
            { y: 92,  icon: '⎇', label: 'Route Registry',    sub: 'URL → controller mapping compiled', color: '#10b981' },
            { y: 118, icon: '⚙', label: 'DI Containers',     sub: 'One per module; exports shared',   color: '#3b82f6' },
            { y: 144, icon: '⛨', label: 'Guard Pipeline',    sub: 'Ordered guard chain per route',    color: '#ec4899' },
            { y: 170, icon: '⊞', label: 'Model Registry',    sub: 'ORM tables & migration scanning',  color: '#f59e0b' },
            { y: 196, icon: '⟳', label: 'Task Scheduler',    sub: '@task refs registered with worker',color: '#d97706' },
            { y: 222, icon: '⬡', label: 'Lifecycle Hooks',   sub: 'startup/shutdown in topo order',   color: '#a855f7' },
            { y: 248, icon: '#', label: 'Fingerprint',       sub: 'SHA-256 of to_dict() for deploys', color: '#64748b' },
          ].map(({ y, label, sub, color }) => (
            <g key={label}>
              <rect x="484" y={y - 11} width="226" height="20" rx="5"
                fill={`${color}08`} stroke={`${color}25`} strokeWidth="1" />
              <circle cx="496" cy={y - 1} r="3" fill={color} opacity="0.6" />
              <text x="505" y={y + 2} fill={color} fontSize="7.5" fontWeight="600" fontFamily="monospace">{label}</text>
              <text x="505" y={y + 13} fill="rgba(255,255,255,0.25)" fontSize="6.5" fontFamily="sans-serif">{sub}</text>
            </g>
          ))}

          {/* exports/imports arrows between modules */}
          <path d="M 312 262 C 312 280, 130 280, 84 262" stroke="rgba(139,92,246,0.3)"
            strokeWidth="1" strokeDasharray="3 3" markerEnd="url(#ma)" />
          <text x="198" y="293" textAnchor="middle" fill="rgba(255,255,255,0.18)" fontSize="7" fontFamily="sans-serif">
            exports → imports cross-module DI
          </text>
        </svg>

        <p className={`text-center text-xs mt-2 ${subtxt}`}>
          <code>workspace.py</code> is the orchestrator — <code>manifest.py</code> is the source of truth — the runtime compiles manifests into live subsystems
        </p>
      </div>

      {/* Minimal example */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <CheckCircle className="w-5 h-5 text-aquilia-400" />
          Minimal manifest
        </h2>
        <p className={`mb-4 ${txt}`}>
          Create <code>modules/users/manifest.py</code>. Every component is a dot-path string in the form <code>"module.path:ClassName"</code>. The <code>:</code> separator is required — <code>__post_init__</code> validates and raises <code>ManifestInvalidFault</code> if it is missing.
        </p>
        <CodeBlock language="python" code={`# modules/users/manifest.py
from aquilia.manifest import AppManifest

manifest = AppManifest(
    name="users",           # must match Module("users") in workspace.py
    version="0.1.0",
    description="User management — CRUD, profiles, roles",
    author="Platform Team",

    controllers=["modules.users.controllers:UsersController"],
    services=["modules.users.services:UsersService"],
    models=["modules.users.models:User", "modules.users.models:Role"],

    # Exports make UsersService available to other modules that import "users"
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
                ['name', 'str (required)', 'Module identifier — must match Module("name") in workspace.py. Alphanumeric + underscores only.'],
                ['version', 'str (required)', 'Semantic version string, e.g. "0.2.0". Required — ManifestInvalidFault raised if empty.'],
                ['description', 'str', 'Human-readable module purpose. Shown in manifest inspection and admin panel.'],
                ['author', 'str', 'Module author name. Shown in aq inspect and fingerprint output.'],
                ['controllers', 'list[str | ComponentRef]', 'HTTP controllers. Each entry "module.path:ClassName". Registered with route registry.'],
                ['socket_controllers', 'list[str | ComponentRef]', 'WebSocket controllers. Requires WebSocket/Socket integration enabled.'],
                ['services', 'list[str | ServiceConfig | ComponentRef]', 'DI-managed services. Strings auto-promoted to ServiceConfig(scope=APP). Full control via ServiceConfig.'],
                ['models', 'list[str | ComponentRef]', 'ORM model classes. Registered for migration scanning and QuerySet generation.'],
                ['serializers', 'list[str | ComponentRef]', 'Contract serializer classes. Auto-wired for request/response schema generation.'],
                ['guards', 'list[str | ComponentRef]', 'Auth/authorization gates applied before route handlers. Evaluated in declaration order.'],
                ['pipes', 'list[str | ComponentRef]', 'Input transformation and validation pipes. Transform incoming request data before handlers.'],
                ['interceptors', 'list[str | ComponentRef]', 'Cross-cutting concerns (logging, caching, telemetry). Wrap route handler execution.'],
                ['middleware', 'list[str | MiddlewareConfig | ComponentRef]', 'Module-scoped middleware. Strings promoted to MiddlewareConfig(priority=50, scope="global").'],
                ['exports', 'list[str]', 'Service class names made visible to modules that list this module in imports.'],
                ['imports', 'list[str]', 'Module names whose exported services this module can inject. Canonical form — prefer over depends_on.'],
                ['lifecycle', 'LifecycleConfig | None', 'Startup/shutdown hooks as dot-path strings. Resolved in topological dependency order.'],
                ['background_tasks', 'BackgroundTaskConfig | None', 'Background task declarations: task paths, default queue, auto_discover.'],
                ['features', 'list[FeatureConfig]', 'Feature flags with conditional service/controller/route activation.'],
                ['auto_discover', 'bool (default True)', 'Scan controllers/, services/, models/, guards/, tasks/ subdirs by convention.'],
                ['discover_patterns', 'list[str]', 'Subdirectory names scanned when auto_discover=True. Defaults: ["controllers", "services", "middleware", "guards", "models", "tasks"].'],
                ['tags', 'list[str]', 'Arbitrary tags for grouping, OpenAPI organisation, and aq inspect filtering.'],
                ['versioning', 'AppVersioningConfig | dict | None', 'Per-module API versioning override (strategy, versions, header_name, etc.).'],
                ['config_schema', 'dict | None', 'JSON Schema for manifest structure validation.'],
              ].map(([f, type_, desc], i) => (
                <tr key={i} className={hover}>
                  <td className="px-4 py-3 font-mono text-xs text-aquilia-400 whitespace-nowrap">{f}</td>
                  <td className={`px-4 py-3 font-mono text-xs ${subtxt}`}>{type_}</td>
                  <td className={`px-4 py-3 text-xs ${txt}`}>{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* ComponentRef */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Hash className="w-5 h-5 text-aquilia-400" />
          ComponentRef — typed references with metadata
        </h2>
        <p className={`mb-4 ${txt}`}>
          When you need to attach metadata (priority, feature flags, custom config) to a component declaration, use <code>ComponentRef</code> instead of a bare string. The <code>class_path</code> must contain a <code>:</code> separator — <code>ManifestInvalidFault</code> is raised at construction if it does not.
        </p>
        <CodeBlock language="python" code={`from aquilia.manifest import (
    AppManifest, ComponentRef, ComponentKind,
    ServiceConfig, ServiceScope, MiddlewareConfig,
)

manifest = AppManifest(
    name="auth",
    version="1.0.0",

    # ── Services with explicit DI scope and aliases ───────────────────────
    services=[
        # String shorthand (scope=APP by default)
        "modules.auth.services:AuthService",

        # Full ServiceConfig — explicit control
        ServiceConfig(
            class_path="modules.auth.services:TokenService",
            scope=ServiceScope.REQUEST,   # New instance per HTTP request
            aliases=["TokenProvider"],    # Alternative injection names
            tag="jwt",                    # For Inject(tag="jwt") resolution
            observable=True,             # Include in metrics/tracing
        ),

        # ServiceConfig with factory pattern
        ServiceConfig(
            class_path="modules.auth.services:OAuthClient",
            scope=ServiceScope.SINGLETON,
            factory="modules.auth.factories:make_oauth_client",
            factory_args={"timeout": 30},
        ),
    ],

    # ── Guards via ComponentRef ───────────────────────────────────────────
    guards=[
        ComponentRef(
            "modules.auth.guards:JWTGuard",
            ComponentKind.GUARD,
            metadata={"priority": 10},      # lower = evaluated first
        ),
        ComponentRef(
            "modules.auth.guards:RoleGuard",
            ComponentKind.GUARD,
            metadata={"priority": 20},
        ),
    ],

    # ── Middleware with priority ──────────────────────────────────────────
    middleware=[
        MiddlewareConfig(
            class_path="modules.auth.middleware:AuditMiddleware",
            scope="global",        # "global" | "app" | "route"
            priority=30,           # lower = earlier in pipeline
            log_requests=True,
        ),
    ],
)`} />
      </section>

      {/* ComponentKind enum */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>ComponentKind — classification enum</h2>
        <p className={`mb-4 text-sm ${txt}`}>
          Used in <code>ComponentRef</code> to classify the component for auto-discovery, filtering, and inspection. All values are lowercase strings.
        </p>
        <div className={`rounded-xl border overflow-hidden ${border}`}>
          <table className="w-full text-sm">
            <thead><tr className={thead}>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>Kind</th>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>Value</th>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>Used for</th>
            </tr></thead>
            <tbody className={`divide-y ${divider}`}>
              {[
                ['CONTROLLER',        '"controller"',        'HTTP route handlers — registered with route registry'],
                ['SERVICE',           '"service"',           'DI-managed business logic services'],
                ['MIDDLEWARE',        '"middleware"',        'Request/response pipeline middleware'],
                ['GUARD',             '"guard"',             'Auth/authorization gates — checked before route handlers'],
                ['PIPE',              '"pipe"',              'Input transformation and data validation pipes'],
                ['INTERCEPTOR',       '"interceptor"',       'Cross-cutting wrappers (logging, caching, telemetry)'],
                ['EFFECT',            '"effect"',            'Side-effect handlers triggered by events'],
                ['MODEL',             '"model"',             'ORM model classes — registered for migrations and QuerySets'],
                ['FAULT_HANDLER',     '"fault_handler"',     'Domain-specific error handlers'],
                ['SOCKET_CONTROLLER', '"socket_controller"', 'WebSocket event handlers'],
                ['SERIALIZER',        '"serializer"',        'Contract schema serializers'],
                ['TASK',              '"task"',              '@task decorated background task functions'],
                ['EVENT_HANDLER',     '"event_handler"',     'Application event bus subscribers'],
                ['INTEGRATION',       '"integration"',       'Subsystem integration hooks'],
                ['COMMAND',           '"command"',           'CLI command handlers'],
                ['VALIDATOR',         '"validator"',         'Request/data validators'],
              ].map(([kind, val, used], i) => (
                <tr key={i} className={hover}>
                  <td className="px-4 py-3 font-mono text-xs text-aquilia-400">{kind}</td>
                  <td className={`px-4 py-3 font-mono text-xs ${subtxt}`}>{val}</td>
                  <td className={`px-4 py-3 text-xs ${txt}`}>{used}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* ServiceScope */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Cpu className="w-5 h-5 text-aquilia-400" />
          ServiceScope — DI lifecycle
        </h2>
        <div className={`rounded-xl border overflow-hidden ${border}`}>
          <table className="w-full text-sm">
            <thead><tr className={thead}>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>Scope</th>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>Lifetime</th>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>Use for</th>
            </tr></thead>
            <tbody className={`divide-y ${divider}`}>
              {[
                ['SINGLETON', 'One instance for the entire process', 'Config objects, connection pools, global rate limiters, global caches'],
                ['APP',       'One per module DI container (default)', 'Most services — repositories, domain services, email senders'],
                ['REQUEST',   'New instance per HTTP request', 'Services that must not leak state across requests (e.g. per-request logger)'],
                ['TRANSIENT', 'Always a new instance on injection', 'Lightweight value objects, formatters, parsers'],
                ['POOLED',    'Object pool — acquire/release', 'Expensive resources with bounded concurrency (e.g. DB connection per query)'],
                ['EPHEMERAL', 'No lifecycle hooks — fastest', 'Pure functions wrapped as services, stateless utilities'],
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

      {/* Guards, Pipes, Interceptors */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Shield className="w-5 h-5 text-aquilia-400" />
          Guards, Pipes, and Interceptors
        </h2>
        <p className={`mb-4 ${txt}`}>
          These three types form the v2 request pipeline. They are evaluated <em>before</em> the route handler runs, in order: guards first (gate), then pipes (transform), then interceptors (wrap). All are declared as dot-path strings or <code>ComponentRef</code>.
        </p>
        <CodeBlock language="python" code={`from aquilia.manifest import AppManifest, ComponentRef, ComponentKind, MiddlewareConfig

manifest = AppManifest(
    name="api",
    version="1.0.0",

    # ── Guards: authentication / authorisation gates ──────────────────────
    # Evaluated before the route handler. Return False or raise to block.
    guards=[
        "modules.api.guards:JWTGuard",          # validates JWT, populates request.user
        "modules.api.guards:PermissionGuard",    # checks request.user has required permissions
        ComponentRef(
            "modules.api.guards:RateLimitGuard",
            ComponentKind.GUARD,
            metadata={"priority": 5},            # evaluated first (lower priority number)
        ),
    ],

    # ── Pipes: input transformation and validation ────────────────────────
    # Transform and coerce incoming request data before the handler sees it.
    pipes=[
        "modules.api.pipes:ValidationPipe",     # validate against Contract schema
        "modules.api.pipes:SanitizationPipe",   # strip HTML/XSS from string inputs
        "modules.api.pipes:ParseIntPipe",       # coerce string IDs to int
    ],

    # ── Interceptors: cross-cutting concerns ─────────────────────────────
    # Wrap handler execution — run code before AND after the response.
    interceptors=[
        "modules.api.interceptors:CacheInterceptor",     # read/write response cache
        "modules.api.interceptors:LoggingInterceptor",   # structured request logging
        "modules.api.interceptors:MetricsInterceptor",   # OpenTelemetry spans
    ],
)`} />
      </section>

      {/* LifecycleConfig */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <GitBranch className="w-5 h-5 text-aquilia-400" />
          LifecycleConfig — startup and shutdown hooks
        </h2>
        <p className={`mb-4 ${txt}`}>
          Hooks are declared as dot-path strings — not callables. This enables lazy loading, manifest serialisation, and fingerprinting without importing the actual function at manifest parse time. The runtime resolves and calls them in topological dependency order.
        </p>
        <CodeBlock language="python" code={`from aquilia.manifest import AppManifest, LifecycleConfig

manifest = AppManifest(
    name="workers",
    version="1.0.0",

    lifecycle=LifecycleConfig(
        # Called during ASGI lifespan startup — async def welcome to use async I/O
        on_startup="modules.workers.hooks:startup",

        # Called during ASGI lifespan shutdown — should release resources
        on_shutdown="modules.workers.hooks:shutdown",

        # These modules must be fully started before this module's on_startup fires
        depends_on=["database", "cache"],

        # Maximum seconds to wait for startup before raising
        startup_timeout=30.0,

        # Maximum seconds to wait for shutdown before force-killing
        shutdown_timeout=30.0,

        # How startup errors propagate:
        # "propagate" → server fails to start (default, recommended for prod)
        # "log"       → log the error, continue booting (risky)
        # "ignore"    → silently swallow the error (dev/debug only)
        error_strategy="propagate",
    ),
)

# ── The actual hook functions ─────────────────────────────────────────────────
# modules/workers/hooks.py

async def startup(config_ns, di_container):
    """Called by the framework during ASGI lifespan startup."""
    worker_service = di_container.resolve("WorkerService")
    await worker_service.connect()

async def shutdown(config_ns, di_container):
    """Called by the framework during ASGI lifespan shutdown."""
    worker_service = di_container.resolve("WorkerService")
    await worker_service.disconnect()`} />
      </section>

      {/* BackgroundTaskConfig */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Zap className="w-5 h-5 text-aquilia-400" />
          BackgroundTaskConfig — task declarations
        </h2>
        <p className={`mb-4 ${txt}`}>
          Declares which <code>@task</code>-decorated functions this module contributes. Tasks listed here are auto-registered with the <code>TaskManager</code> during server startup. The <code>@task</code> decorator provides the runtime metadata (retry policy, queue, timeout); this config gives the manifest layer visibility into what tasks a module owns.
        </p>
        <CodeBlock language="python" code={`from aquilia.manifest import AppManifest, BackgroundTaskConfig

manifest = AppManifest(
    name="auth",
    version="1.0.0",

    background_tasks=BackgroundTaskConfig(
        # Dot-path refs to @task-decorated functions in this module
        tasks=[
            "modules.auth.tasks:cleanup_expired_sessions",
            "modules.auth.tasks:record_login_attempt",
            "modules.auth.tasks:send_password_reset_email",
        ],
        default_queue="auth",          # fallback queue for unspecified tasks
        auto_discover=True,            # also scan tasks.py automatically
        enabled=True,                  # set False to disable all module tasks
    ),
)`} />
      </section>

      {/* Cross-module exports/imports */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <ArrowRight className="w-5 h-5 text-aquilia-400" />
          Cross-module exports and imports
        </h2>
        <p className={`mb-4 ${txt}`}>
          Aquilia's DI system is module-scoped by default — one DI container per module, fully isolated. To share a service across module boundaries, <strong>export</strong> it from the provider and <strong>import</strong> the module name in the consumer. The framework resolves all exports into the consumer's DI container automatically at boot.
        </p>
        <CodeBlock language="python" code={`# ── modules/auth/manifest.py — service PROVIDER ──────────────────────────────
manifest = AppManifest(
    name="auth",
    version="1.0.0",
    services=[
        "modules.auth.services:AuthService",
        "modules.auth.services:JWTService",
        "modules.auth.services:PermissionService",
    ],
    # These three class names are now visible to any module that imports "auth"
    exports=["AuthService", "JWTService", "PermissionService"],
)

# ── modules/users/manifest.py — service CONSUMER ─────────────────────────────
manifest = AppManifest(
    name="users",
    version="1.0.0",
    # Declare that this module depends on the "auth" module
    imports=["auth"],                   # resolves auth's exports into users' DI container
    services=["modules.users.services:UsersService"],
    exports=["UsersService"],           # users can also export to other modules
)

# ── modules/users/services.py ─────────────────────────────────────────────────
# AuthService and JWTService are type-injected from auth's DI container
class UsersService:
    def __init__(self, auth: AuthService, jwt: JWTService):
        self.auth = auth
        self.jwt  = jwt

# ── modules/orders/manifest.py — multi-level import ──────────────────────────
manifest = AppManifest(
    name="orders",
    version="1.0.0",
    imports=["auth", "users"],          # imports from both auth AND users
    services=["modules.orders.services:OrdersService"],
)`} />
      </section>

      {/* FeatureConfig */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>FeatureConfig — conditional activation</h2>
        <p className={`mb-4 ${txt}`}>
          Feature flags control which services, controllers, middleware, and routes are registered at boot time. Useful for gradual rollouts, A/B testing, or environment-conditional features.
        </p>
        <CodeBlock language="python" code={`from aquilia.manifest import AppManifest, FeatureConfig

manifest = AppManifest(
    name="api",
    version="1.0.0",

    features=[
        FeatureConfig(
            name="new_dashboard",
            enabled=False,                 # disabled by default
            conditions={"env": "dev"},     # auto-enable in dev environment
            controllers=["modules.api.controllers:NewDashboardController"],
            services=["modules.api.services:DashboardService"],
            log_usage=True,
        ),
        FeatureConfig(
            name="beta_api_v2",
            enabled=False,
            conditions={"header": "X-Beta: true"},   # enable for requests with this header
            routes=["/api/v2/experimental"],
            metrics_enabled=True,
        ),
    ],
)`} />
      </section>

      {/* auto_discover */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          auto_discover — convention over configuration
        </h2>
        <p className={`mb-4 ${txt}`}>
          When <code>auto_discover=True</code> (the default), Aquilia scans the following subdirectories inside the module package directory and auto-registers anything it finds that matches the expected base classes. Explicit declarations in the manifest take precedence over discovered components.
        </p>
        <CodeBlock language="text" code={`modules/
└── users/
    ├── manifest.py                ← AppManifest lives here
    ├── controllers/               ← auto-discovered: Controller subclasses
    │     ├── __init__.py
    │     ├── users_controller.py  → UsersController
    │     └── profile_controller.py → ProfileController
    ├── services/                  ← auto-discovered: any class injected as service
    │     ├── users_service.py     → UsersService
    │     └── avatar_service.py    → AvatarService
    ├── models/                    ← auto-discovered: Model subclasses
    │     └── user.py              → User, Role
    ├── guards/                    ← auto-discovered: Guard subclasses
    │     └── roles_guard.py       → RolesGuard
    ├── middleware/                ← auto-discovered: Middleware subclasses
    │     └── user_context.py      → UserContextMiddleware
    └── tasks/                     ← auto-discovered: @task decorated functions
          └── maintenance.py       → cleanup_expired_tokens`} />
        <CodeBlock language="python" code={`# Override the default scan directories
manifest = AppManifest(
    name="users",
    version="1.0.0",
    auto_discover=True,
    # Default: ["controllers", "services", "middleware", "guards", "models", "tasks"]
    discover_patterns=["controllers", "services", "models", "guards", "validators", "tasks"],
)

# Fully explicit — disable auto-discovery, declare everything manually
manifest = AppManifest(
    name="users",
    version="1.0.0",
    auto_discover=False,
    controllers=["modules.users.controllers:UsersController"],
    services=["modules.users.services:UsersService"],
    models=["modules.users.models:User"],
)`} />
      </section>

      {/* Versioning */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>Per-module API versioning</h2>
        <p className={`mb-4 ${txt}`}>
          Use <code>AppVersioningConfig</code> or the convenience <code>versioning()</code> function to override the workspace-level versioning strategy for a specific module.
        </p>
        <CodeBlock language="python" code={`from aquilia.manifest import AppManifest, AppVersioningConfig, versioning

manifest = AppManifest(
    name="api_v2",
    version="2.0.0",

    # ── Using AppVersioningConfig directly ───────────────────────────────
    versioning=AppVersioningConfig(
        strategy="url_prefix",          # "url_prefix" | "header" | "content_type"
        versions=["v1", "v2"],
        default_version="v2",
        url_prefix="v",                 # /v2/users → users module
        url_position="before",          # prefix before module path
        expose_unversioned_alias=True,  # /users also resolves to v2
        require_version=False,          # fallback to default_version if missing
        include_version_header=True,    # X-API-Version: v2 in response
    ),

    # ── Or using the versioning() convenience function ───────────────────
    # versioning=versioning(
    #     strategy="header",
    #     versions=["v1", "v2"],
    #     default_version="v1",
    #     header_name="X-API-Version",
    # ),
)`} />
      </section>

      {/* Fingerprint */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${head}`}>
          <Hash className="w-5 h-5 text-aquilia-400" />
          Fingerprinting — reproducible deploys
        </h2>
        <p className={`mb-4 ${txt}`}>
          Every manifest exposes a <code>.fingerprint()</code> method that produces a 16-character SHA-256 hash of the manifest's serialised <code>to_dict()</code> output. This enables reproducible deploy verification — if the fingerprint changes between deploys, you know the component registry changed.
        </p>
        <CodeBlock language="python" code={`from modules.users.manifest import manifest

# Generate a stable fingerprint for CI/CD verification
fp = manifest.fingerprint()       # → "a1b2c3d4e5f6a7b8" (16-char hex)
print(f"Manifest fingerprint: {fp}")

# Inspect the full serialised manifest
import pprint
pprint.pprint(manifest.to_dict()) # → {name, version, controllers, services, ...}

# Both methods are deterministic — identical manifests always produce identical output`} />
      </section>

      {/* Deprecated fields */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 text-amber-500`}>
          <AlertTriangle className="w-5 h-5" />
          Deprecated fields
        </h2>
        <p className={`mb-4 text-sm ${txt}`}>
          These fields still work at runtime but emit <code>DeprecationWarning</code> via Python's <code>warnings</code> module. Migrate to the current alternatives before the next major release.
        </p>
        <div className={`rounded-xl border border-amber-500/20 overflow-hidden`}>
          <table className="w-full text-sm">
            <thead><tr className={`${isDark ? 'bg-amber-900/20' : 'bg-amber-50'}`}>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>Deprecated field</th>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>Replacement</th>
              <th className={`text-left px-4 py-3 font-semibold ${th}`}>What the runtime does</th>
            </tr></thead>
            <tbody className={`divide-y ${divider}`}>
              {[
                ['route_prefix', 'Module.route_prefix() in workspace.py', 'Emits DeprecationWarning. Workspace value takes precedence at runtime.'],
                ['database (DatabaseConfig)', 'DatabaseIntegration in workspace.py', 'Emits DeprecationWarning and sets manifest.database = None. Completely ignored at runtime.'],
                ['on_startup / on_shutdown (Callable)', 'LifecycleConfig(on_startup="path:fn")', 'Pass a dot-path string — enables lazy loading, serialisation, and fingerprinting.'],
                ['middlewares (list[tuple])', 'middleware: list[str | MiddlewareConfig]', 'Auto-promoted to MiddlewareConfig entries with DeprecationWarning.'],
                ['default_fault_domain (str)', 'faults=FaultHandlingConfig(default_domain=...)', 'Auto-promoted to FaultHandlingConfig with DeprecationWarning.'],
                ['config (type)', 'AquilaConfig in workspace.py', 'Config classes belong in workspace.py, not in the module manifest.'],
                ['depends_on', 'imports', 'Auto-migrated to imports list with DeprecationWarning. Kept for backward compat.'],
              ].map(([deprecated, replacement, note], i) => (
                <tr key={i} className={hover}>
                  <td className="px-4 py-3 font-mono text-xs text-amber-400 whitespace-nowrap">{deprecated}</td>
                  <td className={`px-4 py-3 font-mono text-xs text-aquilia-400`}>{replacement}</td>
                  <td className={`px-4 py-3 text-xs ${subtxt}`}>{note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Full production example */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>Full production manifest</h2>
        <CodeBlock language="python" code={`# modules/orders/manifest.py
from aquilia.manifest import (
    AppManifest,
    ComponentRef, ComponentKind,
    ServiceConfig, ServiceScope,
    MiddlewareConfig,
    LifecycleConfig,
    BackgroundTaskConfig,
    AppVersioningConfig,
)

manifest = AppManifest(
    name="orders",
    version="2.1.0",
    description="Order lifecycle — creation, fulfilment, invoicing",
    author="Commerce Team",

    # ── Controllers ───────────────────────────────────────────────────────
    controllers=[
        "modules.orders.controllers:OrdersController",
        "modules.orders.controllers:FulfilmentController",
        "modules.orders.controllers:InvoiceController",
    ],

    # ── Services ─────────────────────────────────────────────────────────
    services=[
        ServiceConfig(
            class_path="modules.orders.services:OrderService",
            scope=ServiceScope.APP,
            aliases=["Orders"],
            observable=True,
        ),
        ServiceConfig(
            class_path="modules.orders.services:PaymentService",
            scope=ServiceScope.SINGLETON,
        ),
        "modules.orders.services:InvoiceService",
    ],

    # ── Models ────────────────────────────────────────────────────────────
    models=[
        "modules.orders.models:Order",
        "modules.orders.models:OrderItem",
        "modules.orders.models:Invoice",
    ],

    # ── Pipeline components ───────────────────────────────────────────────
    guards=[
        ComponentRef("modules.orders.guards:OrderOwnerGuard", ComponentKind.GUARD),
    ],
    pipes=[
        "modules.orders.pipes:OrderValidationPipe",
    ],
    interceptors=[
        "modules.orders.interceptors:OrderAuditInterceptor",
    ],
    middleware=[
        MiddlewareConfig(
            class_path="modules.orders.middleware:OrderContextMiddleware",
            scope="app",
            priority=40,
        ),
    ],

    # ── Cross-module DI ───────────────────────────────────────────────────
    imports=["auth", "users", "catalog"],
    exports=["OrderService"],

    # ── Lifecycle ─────────────────────────────────────────────────────────
    lifecycle=LifecycleConfig(
        on_startup="modules.orders.hooks:startup",
        on_shutdown="modules.orders.hooks:shutdown",
        depends_on=["database", "cache"],
        startup_timeout=30.0,
        error_strategy="propagate",
    ),

    # ── Background tasks ──────────────────────────────────────────────────
    background_tasks=BackgroundTaskConfig(
        tasks=[
            "modules.orders.tasks:process_payment",
            "modules.orders.tasks:send_confirmation_email",
            "modules.orders.tasks:generate_invoice",
        ],
        default_queue="orders",
        auto_discover=True,
    ),

    # ── Versioning ────────────────────────────────────────────────────────
    versioning=AppVersioningConfig(
        strategy="url_prefix",
        versions=["v1", "v2"],
        default_version="v2",
    ),

    tags=["Orders", "Commerce", "Billing"],
    auto_discover=False,   # all components declared explicitly above
)`} />
      </section>

      {/* Related */}
      <section className="mb-12 border-t pt-8" style={{ borderColor: 'rgba(255,255,255,0.06)' }}>
        <div className="grid grid-cols-2 gap-3">
          {[
            ['/docs/config/module', 'Module Builder', 'workspace.py pointer that maps to this manifest'],
            ['/docs/config/workspace', 'Workspace Builder', 'Workspace.module() wires Module → manifest'],
            ['/docs/di/overview', 'DI System', 'How exports/imports resolve across module containers'],
            ['/docs/config/integrations', 'Integrations', 'Typed integration dataclasses — the workspace layer'],
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
