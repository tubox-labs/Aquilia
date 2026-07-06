import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { Workflow, Zap, AlertCircle, ArrowRight, CheckCircle, RotateCcw, Shield } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function ServerLifecycle() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      {/* Header */}
      <div className="mb-10">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-aquilia-500/30 to-aquilia-500/10 flex items-center justify-center shadow-lg shadow-aquilia-500/10">
            <Workflow className="w-5 h-5 text-aquilia-400" />
          </div>
          <div>
            <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
                Lifecycle
                <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
              </span>
            </h1>
            <p className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>aquilia.lifecycle — Dependency-ordered startup and shutdown</p>
          </div>
        </div>

        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The <DocTerm id="lifecycle.coordinator">LifecycleCoordinator</DocTerm> manages application startup and shutdown phases in strict dependency order. It ensures that service containers are prepared, global and module-level hooks are executed sequentially, and resources are rolled back or cleaned up safely in reverse order on boot failures.
        </p>
      </div>

      {/* Custom Boot Pipeline Timeline (No boxy style, premium layout) */}
      <div className="w-full h-32 flex items-center justify-center my-6 relative">
        <svg className="w-full h-full max-w-2xl" viewBox="0 0 600 120" fill="none">
          {/* Main timeline trace */}
          <path d="M 40 60 L 560 60" stroke="rgba(255,255,255,0.06)" strokeWidth="4" strokeLinecap="round" />
          <path d="M 40 60 L 300 60" stroke="#f59e0b" strokeWidth="3" strokeLinecap="round" />
          <path d="M 300 60 L 500 60" stroke="#3b82f6" strokeWidth="3" strokeLinecap="round" />
          
          {/* Boot Stages */}
          {/* Step 1: INIT */}
          <circle cx="100" cy="60" r="12" fill="#18181b" stroke="#f59e0b" strokeWidth="2" />
          <text x="100" y="63" textAnchor="middle" fill="#f59e0b" fontSize="7" fontWeight="bold" fontFamily="monospace">INIT</text>
          <text x="100" y="38" textAnchor="middle" fill="rgba(255,255,255,0.5)" fontSize="9" fontFamily="sans-serif">1. Wire Config</text>

          {/* Step 2: Global hook */}
          <circle cx="230" cy="60" r="12" fill="#18181b" stroke="#f59e0b" strokeWidth="2" />
          <text x="230" y="63" textAnchor="middle" fill="#f59e0b" fontSize="7" fontWeight="bold" fontFamily="monospace">GLOB</text>
          <text x="230" y="82" textAnchor="middle" fill="rgba(255,255,255,0.5)" fontSize="9" fontFamily="sans-serif">2. Global Startup</text>

          {/* Step 3: Topo Boot */}
          <circle cx="360" cy="60" r="12" fill="#18181b" stroke="#3b82f6" strokeWidth="2" />
          <text x="360" y="63" textAnchor="middle" fill="#3b82f6" fontSize="7" fontWeight="bold" fontFamily="monospace">TOPO</text>
          <text x="360" y="38" textAnchor="middle" fill="rgba(255,255,255,0.5)" fontSize="9" fontFamily="sans-serif">3. Dependency Sort</text>

          {/* Step 4: Container start */}
          <circle cx="480" cy="60" r="12" fill="#18181b" stroke="#10b981" strokeWidth="2" />
          <text x="480" y="63" textAnchor="middle" fill="#10b981" fontSize="7" fontWeight="bold" fontFamily="monospace">DI</text>
          <text x="480" y="82" textAnchor="middle" fill="rgba(255,255,255,0.5)" fontSize="9" fontFamily="sans-serif">4. DI Container Startup</text>

          {/* Step 5: READY */}
          <circle cx="540" cy="60" r="10" fill="#18181b" stroke="#10b981" strokeWidth="2" className="animate-pulse" />
          <text x="540" y="40" textAnchor="middle" fill="rgba(255,255,255,0.5)" fontSize="9" fontFamily="sans-serif">5. READY</text>
        </svg>
      </div>

      {/* Lifecycle Phases */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <ArrowRight className="w-5 h-5 text-aquilia-400" />
          Lifecycle Phases
        </h2>

        <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The application transitions through distinct states defined in the <code>LifecyclePhase</code> enum:
        </p>

        <div className="flex flex-wrap gap-2 mb-6">
          {['INIT', 'STARTING', 'READY', 'STOPPING', 'STOPPED', 'ERROR'].map((phase, i) => {
            const colors: Record<string, string> = {
              INIT: isDark ? 'bg-gray-800 text-gray-300 border-gray-700' : 'bg-gray-100 text-gray-600 border-gray-200',
              STARTING: isDark ? 'bg-blue-900/40 text-blue-300 border-blue-800' : 'bg-blue-50 text-blue-600 border-blue-200',
              READY: isDark ? 'bg-emerald-900/40 text-emerald-300 border-emerald-800' : 'bg-emerald-50 text-emerald-600 border-emerald-200',
              STOPPING: isDark ? 'bg-amber-900/40 text-amber-300 border-amber-800' : 'bg-amber-50 text-amber-600 border-amber-200',
              STOPPED: isDark ? 'bg-gray-800 text-gray-400 border-gray-700' : 'bg-gray-100 text-gray-500 border-gray-200',
              ERROR: isDark ? 'bg-red-900/40 text-red-300 border-red-800' : 'bg-red-50 text-red-600 border-red-200',
            }
            return (
              <div key={phase} className="flex items-center gap-2">
                <span className={`px-3 py-1 rounded-lg border text-xs font-mono font-bold ${colors[phase]}`}>
                  {phase}
                </span>
                {i < 5 && <ArrowRight className={`w-3 h-3 ${isDark ? 'text-gray-600' : 'text-gray-300'}`} />}
              </div>
            )
          })}
        </div>

        <CodeBlock
          code={`class LifecyclePhase(Enum):
    INIT = "init"           # Server initialized, dependencies wired
    STARTING = "starting"   # startup() called, boot hooks executing
    READY = "ready"         # All boot hooks completed, server accepting traffic
    STOPPING = "stopping"   # shutdown() called, teardown hooks executing
    STOPPED = "stopped"     # All teardown hooks completed, server down
    ERROR = "error"         # A lifecycle hook crashed during startup`}
          language="python"
        />
      </section>

      {/* LifecycleCoordinator */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Zap className="w-5 h-5 text-aquilia-400" />
          LifecycleCoordinator
        </h2>

        <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The coordinator is instantiated during <code>AquiliaServer.__init__()</code>. It retrieves module dependency configurations, tracks started applications, and fires events to registered observers:
        </p>

        <CodeBlock
          code={`class LifecycleCoordinator:
    """Coordinates application lifecycle across multiple apps/modules."""

    def __init__(self, runtime: Any, config: ConfigLoader | None = None):
        self.runtime = runtime
        self.config = config
        self.phase = LifecyclePhase.INIT
        self.started_apps: list[str] = []  # Tracks successfully booted modules
        self.event_handlers: list[Callable[[LifecycleEvent], None]] = []
        self.logger = logger

    def on_event(self, handler: Callable[[LifecycleEvent], None]):
        """Register a callback that receives LifecycleEvent notifications."""
        self.event_handlers.append(handler)`}
          language="python"
        />
      </section>

      {/* Startup & Shutdown Details */}
      <section className="mb-12 space-y-6">
        <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Lifecycle Hook Execution Flow
        </h2>

        {/* Startup Sequence */}
        <div>
          <h3 className={`text-lg font-bold mb-2 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-800'}`}>
            <ArrowRight className="w-4 h-4 text-emerald-400" />
            1. Startup Sequence (Topological Order)
          </h3>
          <p className={`text-sm mb-4 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            When <code>startup()</code> is called, the coordinator:
          </p>
          <ol className={`list-decimal list-inside text-sm space-y-2 mb-4 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
            <li>Fires the global workspace-level <DocTerm id="lifecycle.on_startup">on_startup</DocTerm> hook (if defined in <code>self.config</code>), passing the base DI container.</li>
            <li>Iterates through module application contexts (<code>runtime.meta.app_contexts</code>), which are pre-sorted in topological dependency order.</li>
            <li>For each module: starts its DI container (executes DI provider startup events) and resolves and executes the module's <DocTerm id="lifecycle.on_startup">on_startup(config_ns, container)</DocTerm> hook.</li>
            <li>Appends the booted module to <code>started_apps</code> for rollback tracking.</li>
          </ol>
          <CodeBlock
            code={`# Step-by-step app-level boot inside _startup_app():
# 1. Start DI container (runs provider startup hooks)
if di_container and hasattr(di_container, "startup"):
    await di_container.startup()

# 2. Resolve and run startup hook
hook = self._resolve_hook(ctx.on_startup)
if hook:
    if inspect.iscoroutinefunction(hook):
        await hook(config_ns, di_container)
    else:
        hook(config_ns, di_container)`}
            language="python"
          />
        </div>

        {/* Shutdown Sequence */}
        <div>
          <h3 className={`text-lg font-bold mb-2 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-800'}`}>
            <RotateCcw className="w-4 h-4 text-emerald-400" />
            2. Shutdown Sequence (Reverse Dependency Order)
          </h3>
          <p className={`text-sm mb-3 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            teardown is executed in <strong>reverse order</strong> of startup. If App A boots before App B, then App B's <DocTerm id="lifecycle.on_shutdown">on_shutdown</DocTerm> runs before App A's. This ensures dependent resources remain active while their consumers tear down.
          </p>
          <p className={`text-sm mb-3 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <strong>Graceful Error Handling:</strong> Unlike startup, exceptions raised during shutdown do not halt the process. The coordinator catches the error, logs it as a warning, and continues running the remaining teardown hooks to ensure best-effort resource cleanup.
          </p>
          <CodeBlock
            code={`# Teardown order:
for app_name in reversed(self.started_apps):
    await self._shutdown_app(app_name)

# Executes global workspace-level shutdown at the very end
global_shutdown = self.config.get("on_shutdown") if self.config else None`}
            language="python"
          />
        </div>

        {/* Rollback */}
        <div>
          <h3 className="text-lg font-bold mb-2 flex items-center gap-2 text-rose-500">
            <AlertCircle className="w-4 h-4" />
            3. Automatic Startup Rollback
          </h3>
          <p className={`text-sm mb-3 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            If any module fails to startup, the coordinator flags the phase as <code>LifecyclePhase.ERROR</code>, logs the traceback, and initiates an automatic rollback. It executes the shutdown sequence for all modules listed in <code>started_apps</code> in reverse order, ensuring no orphaned resources remain active before propagating a <code>LifecycleError</code>.
          </p>
        </div>
      </section>

      {/* Controller Lifecycle Hooks */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <CheckCircle className="w-5 h-5 text-aquilia-400" />
          Controller Lifecycle Hooks
        </h2>

        <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Controllers with <code>instantiation_mode = "singleton"</code> can hook into startup and shutdown events directly. All controllers, regardless of mode, support per-request hooks:
        </p>

        <CodeBlock
          code={`class ResourceController(Controller):
    prefix = "/resources"
    instantiation_mode = "singleton"  # Required for startup/shutdown hooks

    async def on_startup(self, ctx: RequestCtx) -> None:
        """Called once when the server boots."""
        self.client = await self.init_client()

    async def on_shutdown(self, ctx: RequestCtx) -> None:
        """Called once during server shutdown."""
        await self.client.close()

    async def on_request(self, ctx: RequestCtx) -> None:
        """Called before EVERY incoming request routed to this controller."""
        ctx.state["req_start"] = time.monotonic()

    async def on_response(self, ctx: RequestCtx, response: Response) -> Response:
        """Called after EVERY request. Allows altering response headers/body."""
        duration = time.monotonic() - ctx.state["req_start"]
        response.headers["X-Process-Time"] = f"{duration:.3f}s"
        return response`}
          language="python"
        />

        <div className={`mt-4 rounded-xl border overflow-hidden ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={isDark ? 'bg-zinc-800/80' : 'bg-gray-50'}>
                <th className={`text-left px-4 py-3 font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Hook Method</th>
                <th className={`text-left px-4 py-3 font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Trigger Frequency</th>
                <th className={`text-left px-4 py-3 font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Supported Modes</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5' : 'divide-gray-100'}`}>
              {[
                ['on_startup(ctx)', 'lifecycle.on_startup', 'Once per server startup', 'singleton only'],
                ['on_shutdown(ctx)', 'lifecycle.on_shutdown', 'Once per server shutdown', 'singleton only'],
                ['on_request(ctx)', 'lifecycle.on_request', 'Before every matched route handler', 'Both (singleton & per_request)'],
                ['on_response(ctx, response)', 'lifecycle.on_response', 'After every matched route handler', 'Both (singleton & per_request)'],
              ].map(([hook, termId, when, mode], i) => (
                <tr key={i} className={isDark ? 'hover:bg-white/5' : 'hover:bg-gray-50'}>
                  <td className="px-4 py-3 font-mono text-xs">
                    <DocTerm id={termId}>{hook}</DocTerm>
                  </td>
                  <td className={`px-4 py-3 text-xs ${isDark ? 'text-gray-400' : 'text-gray-505'}`}>{when}</td>
                  <td className={`px-4 py-3 text-xs ${isDark ? 'text-gray-550' : 'text-gray-400'}`}>{mode}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* LifecycleManager Context Manager */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Shield className="w-5 h-5 text-aquilia-400" />
          The LifecycleManager Context Manager
        </h2>

        <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          For script execution, testing, or server wrappers, the <code>LifecycleManager</code> class exposes an async context manager. This enforces startup on entry and guarantees cleanup on block exit, even if unhandled exceptions are raised:
        </p>

        <CodeBlock
          code={`from aquilia.lifecycle import LifecycleManager

# Use the manager to guarantee clean resources:
async with LifecycleManager(runtime, config) as coordinator:
    # Modules are started and available here
    await run_app_loop()

# Shut down automatically invoked on block exit`}
          language="python"
        />
      </section>

      {/* Default Observers */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <AlertCircle className="w-5 h-5 text-aquilia-400" />
          Central Observability Observers
        </h2>

        <p className={`mb-4 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The <code>AquiliaServer</code> registers two default observers on the coordinator:
        </p>

        <ul className={`space-y-3 text-sm mb-6 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          <li className="flex items-start gap-2">
            <span className="text-aquilia-400 mt-1">•</span>
            <div><strong>Fault Observer (<code>_lifecycle_fault_observer</code>):</strong> Intercepts error events and records them in the structured <code>FaultEngine</code> database.</div>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-aquilia-400 mt-1">•</span>
            <div><strong>Trace Observer (<code>_lifecycle_trace_observer</code>):</strong> Records all successful transitions and phase changes directly to the <code>.aquilia/lifecycle.log</code> journal.</div>
          </li>
        </ul>
      </section>

      {/* Next */}
      <section className="mb-12 border-t border-white/5 pt-8">
        <div className="flex flex-col gap-2">
          <Link to="/docs/server/aquilia-server" className={`text-sm font-medium ${isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-500'}`}>
            → AquiliaServer: Full server orchestration
          </Link>
          <Link to="/docs/di/lifecycle" className={`text-sm font-medium ${isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-500'}`}>
            → DI Lifecycle: Container-level lifecycle management
          </Link>
        </div>
      </section>
    
      <NextSteps />
    </div>
  )
}