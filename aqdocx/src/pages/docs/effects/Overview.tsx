import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Zap, ShieldAlert } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function EffectsOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <Zap className="w-4 h-4" />
          <span>EFFECTS &amp; FLOW / OVERVIEW</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Effects &amp; Flow System
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The Effects &amp; Flow system provides a declarative way to request side-effects (database transactions, caching, message queues, HTTP requests, or storage access) and chain them into typed, composable pipelines. Rather than invoking hardcoded dependencies, handlers declare capability tokens, which the <DocTerm id="effects.EffectRegistry">EffectRegistry</DocTerm> resolves per-request.
        </p>
      </div>

      {/* Philosophy & Architecture */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Philosophy &amp; Decoupling</h2>
        <div className={`space-y-6 font-light leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          <p>
            In traditional backend frameworks, handlers (e.g., controllers or services) instantiate database connections, cache clients, or message brokers directly. This tight coupling creates mock-heavy tests, configuration drift, and makes it challenging to swap backends (like switching from a local filesystem storage to AWS S3).
          </p>
          <p>
            Aquilia solves this via the <strong className="font-semibold text-aquilia-500">Explicit Capability Injection</strong> pattern. Handlers declare *what* capability they require via a typed token, and the runtime handles the lifecycle (setup, connection pooling, and automatic commit/rollback cleanup) around the request execution.
          </p>
        </div>
      </section>

      {/* Architecture Diagram Section */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Request Lifecycle Architecture</h2>
        <p className={`mb-8 font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The diagram below illustrates how an incoming request flows through the middleware stack, resolving capability requirements lazily through the registry proxy, and releasing resources safely.
        </p>

        {/* Premium SVG Flow-Based Architecture Diagram */}
        <div className="w-full flex justify-center py-6 bg-transparent">
          <svg viewBox="0 0 900 340" className="w-full h-auto drop-shadow-2xl font-mono select-none">
            <defs>
              <linearGradient id="waveGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#22c55e" stopOpacity="0.9" />
                <stop offset="50%" stopColor="#3b82f6" stopOpacity="0.9" />
                <stop offset="100%" stopColor="#a855f7" stopOpacity="0.9" />
              </linearGradient>
              <radialGradient id="glow1" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#22c55e" stopOpacity="0.15" />
                <stop offset="100%" stopColor="#22c55e" stopOpacity="0" />
              </radialGradient>
              <radialGradient id="glow2" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.15" />
                <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
              </radialGradient>
              <radialGradient id="glow3" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#a855f7" stopOpacity="0.15" />
                <stop offset="100%" stopColor="#a855f7" stopOpacity="0" />
              </radialGradient>
              <filter id="glowFilter" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>

            {/* Glowing Halos Behind Nodes */}
            <circle cx="80" cy="160" r="50" fill="url(#glow1)" />
            <circle cx="240" cy="100" r="50" fill="url(#glow1)" />
            <circle cx="400" cy="80" r="50" fill="url(#glow2)" />
            <circle cx="560" cy="220" r="50" fill="url(#glow2)" />
            <circle cx="720" cy="180" r="50" fill="url(#glow3)" />
            <circle cx="840" cy="160" r="50" fill="url(#glow1)" />

            {/* Connecting Wave Lines (Bundle of Light Fibers) */}
            <path d="M 80 160 C 160 160, 160 100, 240 100 C 320 100, 320 80, 400 80 C 480 80, 480 220, 560 220 C 640 220, 640 180, 720 180 C 800 180, 800 160, 840 160" fill="none" stroke="url(#waveGrad)" strokeWidth="4.5" strokeLinecap="round" />
            <path d="M 80 160 C 160 160, 160 100, 240 100 C 320 100, 320 80, 400 80 C 480 80, 480 220, 560 220 C 640 220, 640 180, 720 180 C 800 180, 800 160, 840 160" fill="none" stroke="#ffffff" strokeWidth="1" strokeOpacity="0.25" strokeDasharray="4 8" strokeLinecap="round" />

            {/* Node 1: Request Inbound */}
            <g transform="translate(80, 160)">
              <circle cx="0" cy="0" r="10" fill={isDark ? "#02040a" : "#ffffff"} stroke="#22c55e" strokeWidth="2.5" filter="url(#glowFilter)" />
              <circle cx="0" cy="0" r="4" fill="#22c55e" />
              <text x="0" y="32" textAnchor="middle" fontSize="10" fill={isDark ? "#e4e4e7" : "#1f2937"} fontWeight="bold">HTTP REQUEST</text>
              <text x="0" y="44" textAnchor="middle" fontSize="8" fill="#71717a">Client Inbound</text>
            </g>

            {/* Node 2: FlowContext creation */}
            <g transform="translate(240, 100)">
              <circle cx="0" cy="0" r="10" fill={isDark ? "#02040a" : "#ffffff"} stroke="#22c55e" strokeWidth="2.5" filter="url(#glowFilter)" />
              <circle cx="0" cy="0" r="4" fill="#22c55e" />
              <text x="0" y="32" textAnchor="middle" fontSize="10" fill={isDark ? "#e4e4e7" : "#1f2937"} fontWeight="bold">FLOWCONTEXT</text>
              <text x="0" y="44" textAnchor="middle" fontSize="8" fill="#71717a">Scoped container</text>
            </g>

            {/* Node 3: Discovery */}
            <g transform="translate(400, 80)">
              <circle cx="0" cy="0" r="10" fill={isDark ? "#02040a" : "#ffffff"} stroke="#3b82f6" strokeWidth="2.5" filter="url(#glowFilter)" />
              <circle cx="0" cy="0" r="4" fill="#3b82f6" />
              <text x="0" y="32" textAnchor="middle" fontSize="10" fill={isDark ? "#e4e4e7" : "#1f2937"} fontWeight="bold">@REQUIRES SCAN</text>
              <text x="0" y="44" textAnchor="middle" fontSize="8" fill="#71717a">Discovery phase</text>
            </g>

            {/* Node 4: Lazy Acquisition */}
            <g transform="translate(560, 220)">
              <circle cx="0" cy="0" r="10" fill={isDark ? "#02040a" : "#ffffff"} stroke="#3b82f6" strokeWidth="2.5" filter="url(#glowFilter)" />
              <circle cx="0" cy="0" r="4" fill="#3b82f6" />
              <text x="0" y="-24" textAnchor="middle" fontSize="10" fill={isDark ? "#e4e4e7" : "#1f2937"} fontWeight="bold">LAZY ACQUISITION</text>
              <text x="0" y="-12" textAnchor="middle" fontSize="8" fill="#71717a">Registry session lease</text>
            </g>

            {/* Node 5: Controller Execute */}
            <g transform="translate(720, 180)">
              <circle cx="0" cy="0" r="10" fill={isDark ? "#02040a" : "#ffffff"} stroke="#a855f7" strokeWidth="2.5" filter="url(#glowFilter)" />
              <circle cx="0" cy="0" r="4" fill="#a855f7" />
              <text x="0" y="32" textAnchor="middle" fontSize="10" fill={isDark ? "#e4e4e7" : "#1f2937"} fontWeight="bold">CONTROLLER RUN</text>
              <text x="0" y="44" textAnchor="middle" fontSize="8" fill="#71717a">Leased handles bound</text>
            </g>

            {/* Node 6: Release */}
            <g transform="translate(840, 160)">
              <circle cx="0" cy="0" r="10" fill={isDark ? "#02040a" : "#ffffff"} stroke="#22c55e" strokeWidth="2.5" filter="url(#glowFilter)" />
              <circle cx="0" cy="0" r="4" fill="#22c55e" />
              <text x="0" y="32" textAnchor="middle" fontSize="10" fill={isDark ? "#e4e4e7" : "#1f2937"} fontWeight="bold">SAFE RELEASE</text>
              <text x="0" y="44" textAnchor="middle" fontSize="8" fill="#71717a">Commit / Rollback</text>
            </g>
          </svg>
        </div>
      </section>

      {/* Workspace Integration: How to Add Middleware */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Workspace Integration</h2>
        <div className={`space-y-6 font-light leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'} mb-8`}>
          <p>
            To use the capability system, register <DocTerm id="effects.EffectMiddleware">EffectMiddleware</DocTerm> and <DocTerm id="effects.FlowContextMiddleware">FlowContextMiddleware</DocTerm> in your application's middleware stack inside your project's workspace configuration (usually in <code className="text-aquilia-400">workspace.py</code>).
          </p>
          <p>
            <strong className="text-yellow-500 font-semibold flex items-center gap-1.5"><ShieldAlert className="w-4 h-4 shrink-0" /> IMPORTANT NOTE ON ORDERING:</strong> The <DocTerm id="effects.FlowContextMiddleware">FlowContextMiddleware</DocTerm> must precede <DocTerm id="effects.EffectMiddleware">EffectMiddleware</DocTerm> in execution (meaning it has a lower priority number or is added first in the chain). This ensures that a request-scoped <DocTerm id="effects.FlowContext">FlowContext</DocTerm> exists so that the Effect Middleware can inject the acquired capability handles into it.
          </p>
        </div>

        <CodeBlock language="python" filename="workspace.py" highlightLines={[6, 7]}>{`from aquilia.workspace import Workspace
from aquilia.middleware import MiddlewareChain

app = (
    Workspace.new("aquilia-project")
    .middleware(
        MiddlewareChain.chain()
        .defaults()
        .use("aquilia.middleware_ext.FlowContextMiddleware", priority=14)
        .use("aquilia.middleware_ext.EffectMiddleware", priority=15)
    )
)`}</CodeBlock>

        <p className={`font-light leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'} mt-6`}>
          The framework will load the middleware string paths and dynamically inject dependencies. The <DocTerm id="effects.EffectMiddleware">EffectMiddleware</DocTerm> will look for a configured <DocTerm id="effects.EffectRegistry">EffectRegistry</DocTerm> in the global dependency injection container and defer to it.
        </p>
      </section>

      {/* Declaring Requirements with requires() */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Declaring Capabilities with @requires</h2>
        <div className={`space-y-6 font-light leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'} mb-8`}>
          <p>
            To declare that a route handler or flow pipeline node requires a capability, decorate it with the <DocTerm id="effects.requires">@requires</DocTerm> decorator, passing in the names of the required effects (e.g. <code className="text-white">"DBTx"</code>, <code className="text-white">"Cache"</code>).
          </p>
          <p>
            <strong className="text-yellow-500 font-semibold flex items-center gap-1.5"><ShieldAlert className="w-4 h-4 shrink-0" /> CRITICAL DECORATOR ORDERING:</strong> The <DocTerm id="effects.requires">@requires(...)</DocTerm> decorator must be placed **below** the routing decorators (e.g. <code className="text-aquilia-400">@POST</code> or <code className="text-aquilia-400">@Get</code>). Python evaluates decorators from bottom to top; applying <code className="text-aquilia-400">@requires</code> closest to the method body registers its metadata under <code className="text-white">__flow_effects__</code> on the original method, allowing routing compiles to read it.
          </p>
        </div>

        <CodeBlock language="python" filename="controllers/order.py" highlightLines={[5, 6]}>{`from aquilia.controller import Controller, POST, RequestCtx
from aquilia.flow import requires

class CorporateOrderIngestController(Controller):
    @POST("/orders/ingest")
    @requires("DBTx", "Cache")
    async def ingest_corporate_order(self, ctx: RequestCtx) -> dict:
        # Resolve capabilities safely
        db = ctx.get_effect("DBTx")        # Returns a DBTxHandle
        cache = ctx.get_effect("Cache")    # Returns a CacheServiceHandle
        
        body = await ctx.json()
        
        # 1. Store order payload in Database
        order_id = await db.fetch_val(
            "INSERT INTO orders (corporate_id, total, status) VALUES (?, ?, ?) RETURNING id",
            (body["corporate_id"], body["total"], "RECEIVED")
        )
        
        # 2. Update cache with hot corporate statistics
        latest_orders = await cache.get(f"corp:{body['corporate_id']}:recent") or []
        latest_orders.insert(0, {"order_id": order_id, "total": body["total"]})
        await cache.set(f"corp:{body['corporate_id']}:recent", latest_orders[:5], ttl=600)
        
        return {"status": "order_ingested", "order_id": order_id}`}</CodeBlock>
      </section>

      {/* Deep-Dive: Under the Hood Lifecycle */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Under The Hood: Deferred Resolving</h2>
        <div className={`space-y-6 font-light leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          <p>
            Aquilia uses a *lazy deferred registry* model via the internal proxy <code className="text-aquilia-400">_DeferredEffectRegistry</code>. This resolves a fundamental bootstrap ordering constraint:
          </p>
          <div className="border-l border-aquilia-500/30 pl-6 space-y-4 py-2 font-mono text-xs my-6">
            <div className="flex items-center gap-2">
              <span className="text-aquilia-500 font-bold">1. Bootstrap:</span>
              <span className={isDark ? "text-gray-400" : "text-gray-600"}>Middleware stack is constructed early before providers are registered.</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-blue-500 font-bold">2. ASGI Startup:</span>
              <span className={isDark ? "text-gray-400" : "text-gray-600"}>Subsystems load and register their effect providers with the central registry.</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-yellow-500 font-bold">3. Request Time:</span>
              <span className={isDark ? "text-gray-400" : "text-gray-600"}>The lazy proxy forwards lookups to the populated live registry on every request.</span>
            </div>
          </div>
          <p>
            When a request comes in:
          </p>
          <ol className="list-decimal list-inside space-y-3 pl-2">
            <li>
              The middleware detects the capabilities needed by checking <code className="text-white">__flow_effects__</code> on the handler method.
            </li>
            <li>
              It calls <code className="text-white">await registry.acquire(name, mode)</code>. The provider sets up any connection or client state, returning a scoped handle.
            </li>
            <li>
              Handles are bound to the request's <code className="text-white">state["effects"]</code> dictionary.
            </li>
            <li>
              If the request completes successfully, the middleware invokes <code className="text-white">await registry.release(name, resource, success=True)</code>.
            </li>
            <li>
              If an exception is raised, it catches it and invokes <code className="text-white">await registry.release(name, resource, success=False)</code> (guaranteeing that database transactions are rolled back), before re-raising the error to be handled by the Fault system.
            </li>
          </ol>
        </div>
      </section>

      {/* Provider Contract */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">The EffectProvider Contract</h2>
        <p className={`mb-6 leading-relaxed font-light ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Every effect resource must have a corresponding <DocTerm id="effects.EffectProvider">EffectProvider</DocTerm> implementation. It defines five lifecycle hooks:
        </p>

        <div className="space-y-8 mb-8 text-sm text-gray-400">
          <div>
            <CodeBlock language="python" compact showLineNumbers={false}>{`async def initialize(self) -> None`}</CodeBlock>
            <p className="mt-2 text-sm font-light">Invoked once at server startup. Ideal for connecting client pools or setting up driver connections.</p>
          </div>
          <div>
            <CodeBlock language="python" compact showLineNumbers={false}>{`async def acquire(self, mode: str | None = None) -> Any`}</CodeBlock>
            <p className="mt-2 text-sm font-light">Invoked per-request. Retrieves the scoped handle representing the resource connection (e.g. transaction, bucket client).</p>
          </div>
          <div>
            <CodeBlock language="python" compact showLineNumbers={false}>{`async def release(self, resource: Any, success: bool = True) -> None`}</CodeBlock>
            <p className="mt-2 text-sm font-light">Invoked when a request finishes. The success boolean flags whether the endpoint completed without throwing an exception, allowing providers to safely commit or abort changes.</p>
          </div>
          <div>
            <CodeBlock language="python" compact showLineNumbers={false}>{`async def finalize(self) -> None`}</CodeBlock>
            <p className="mt-2 text-sm font-light">Invoked at server shutdown. Closes client connections and drains active pools safely.</p>
          </div>
          <div>
            <CodeBlock language="python" compact showLineNumbers={false}>{`async def health_check(self) -> dict[str, Any]`}</CodeBlock>
            <p className="mt-2 text-sm font-light">Aggregates connection health metrics (e.g., checks connection ping, error counts). Returns a dictionary with a "healthy" boolean key.</p>
          </div>
        </div>
      </section>

      {/* Layer System: Composing Dependency Graphs */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Topological Dependency Resolution (Layer)</h2>
        <div className={`space-y-6 font-light leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'} mb-8`}>
          <p>
            Aquilia integrates an Effect-TS inspired <DocTerm id="effects.Layer">Layer</DocTerm> class that facilitates modular initialization. Layers specify setup factories and declare explicit dependencies. The runtime resolves the full dependency graph topologically at startup.
          </p>
          <p>
            For a detailed guide on managing initialization layers, composing them, and acquiring resources outside of HTTP paths, see the dedicated <Link to="/docs/effects/layers" className="text-aquilia-400 hover:underline font-medium">Layers &amp; Compositions</Link> reference.
          </p>
        </div>

        <CodeBlock language="python" filename="effects_layers.py" highlightLines={[9, 15, 20]}>{`from aquilia.flow import Layer
from aquilia.effects import DBTxProvider, CacheProvider

# Define configuration dependencies
config_layer = Layer(
    name="Config",
    factory=lambda: AppConfig.load_from_env()
)

db_layer = Layer(
    name="DBTx",
    factory=lambda cfg: DBTxProvider(cfg.database_url),
    deps=["Config"]
)

cache_layer = Layer(
    name="Cache",
    factory=lambda cfg: CacheProvider(cfg.cache_backend),
    deps=["Config"]
)

# Compose and bootstrap layers sequentially
app_layer = Layer.merge(db_layer, cache_layer)`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/aquilary/fingerprint" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Fingerprinting
        </Link>
        <Link to="/docs/effects/pipelines" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400 transition-colors">
          Flow Pipelines <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}