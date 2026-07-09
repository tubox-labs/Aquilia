import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Layers, ArrowRight } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { Link } from 'react-router-dom'

export function MiddlewareOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <Layers className="w-4 h-4" />
          <span>MIDDLEWARE / OVERVIEW</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Middleware System &amp; Flows
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Middleware in Aquilia acts as a series of composable wrappers around the request/response lifecycle. Managed by the <DocTerm id="middleware.MiddlewareStack">MiddlewareStack</DocTerm>, every middleware conforms to a strict async signature, enabling deterministic priority execution and scoped filtering.
        </p>
      </div>

      {/* Pipeline Diagram */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Middleware Pipeline Flow</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          <DocTerm id="middleware.MiddlewareStack">MiddlewareStack</DocTerm>.<code className="text-aquilia-500">build_handler()</code> sorts every registered descriptor by <code className="text-aquilia-400">(scope_rank, priority)</code> ascending, then wraps the final handler in <strong>reverse</strong> order — so the <strong>lowest priority number becomes the outermost layer</strong> and runs first on the way in / last on the way out.
        </p>
        <div className="border-l border-white/10 pl-6 py-4 my-6 text-sm text-gray-400 leading-relaxed">
          <p className="mb-4">
            <code className="text-aquilia-400">AquiliaServer._setup_middleware()</code> always registers two internal plumbing middlewares first, regardless of any workspace/module configuration — they are framework infrastructure, not part of the user-facing chain:
          </p>
          <div className="flex flex-col gap-2 font-mono text-xs my-4 max-w-lg">
            <div className="flex items-center gap-4 py-2 px-3 bg-white/2 border-l-2 border-aquilia-500 text-white rounded-r">
              <span className="text-aquilia-500 font-bold">INCOMING REQUEST</span>
            </div>
            <div className="pl-6 border-l border-white/10 flex flex-col gap-2 py-1">
              <div className="p-2 bg-white/5 rounded border border-white/5 text-gray-300">
                priority 2 &mdash; <DocTerm id="faults.FaultMiddleware">FaultMiddleware</DocTerm> <span className="text-gray-600">(always on — bridges FaultEngine to the response)</span>
              </div>
              <div className="p-2 bg-white/5 rounded border border-white/5 text-gray-300">
                priority 3 &mdash; <DocTerm id="middleware.ProxyFixMiddleware">ProxyFixMiddleware</DocTerm> <span className="text-gray-600">(only if configured)</span>
              </div>
              <div className="p-2 bg-white/5 rounded border border-white/5 text-gray-300">
                priority 4 &mdash; <DocTerm id="middleware.HTTPSRedirectMiddleware">HTTPSRedirectMiddleware</DocTerm> <span className="text-gray-600">(only if configured)</span>
              </div>
              <div className="p-2 bg-white/5 rounded border border-white/5 text-gray-300">
                priority 5 &mdash; internal <code>ServerRequestScopeMiddleware</code> <span className="text-gray-600">(always on — creates the request-scoped DI container)</span>
              </div>
              <div className="p-2 bg-white/5 rounded border border-white/5 text-gray-300">
                priority 1 (if using the built-in fallback chain) &mdash; <DocTerm id="middleware.ExceptionMiddleware">ExceptionMiddleware</DocTerm>
              </div>
              <div className="p-2 bg-white/5 rounded border border-white/5 text-gray-300">
                priority 10 (fallback) &mdash; <DocTerm id="middleware.RequestIdMiddleware">RequestIdMiddleware</DocTerm>
              </div>
              <div className="p-2 bg-white/5 rounded border border-white/5 text-gray-300">
                priority 6&ndash;26 &mdash; static files, security headers, HSTS, CSP, CORS, rate limit, auth/session, CSRF, i18n, templates, cache <span className="text-gray-600">(only whichever are configured)</span>
              </div>
            </div>
            <div className="flex items-center gap-4 py-2 px-3 bg-aquilia-500/10 border-l-2 border-aquilia-500 text-aquilia-400 rounded-r">
              <span>Final <DocTerm id="controller.controller">Controller</DocTerm> Route Handler</span>
            </div>
          </div>
          <p className="text-xs">
            Note the <strong>overlap</strong>: if you leave <code className="text-aquilia-400">.middleware(...)</code> unset, the server falls back to a hardcoded chain of just <code>ExceptionMiddleware</code> (priority 1) + <code>RequestIdMiddleware</code> (priority 10) — <code>ExceptionMiddleware</code> then sits <em>outside</em> the always-on <code>FaultMiddleware</code> (priority 2) as a last-resort catch-all in case <code>FaultEngine.process()</code> re-raises. See <Link to="/docs/middleware/built-in" className="text-aquilia-400 underline">Built-in Middleware</Link> for the full, source-verified priority table.
          </p>
        </div>
      </section>

      {/* Scope is ordering, not isolation */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-yellow-400 uppercase tracking-wider mb-6`}>⚠ Scope Controls Order, Not Which Requests Run It</h2>
        <p className={`mb-4 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          <code className="text-aquilia-500">scope</code> (<code>"global"</code> / <code>"app"</code> / <code>"controller"</code> / <code>"route"</code>) only feeds <code className="text-aquilia-400">MiddlewareStack._sort_middlewares()</code>'s <code>scope_order</code> ranking (<code>global=0, app=1, controller=2, route=3</code>) — it decides <strong>where in the wrapping order</strong> a middleware sits. <code className="text-aquilia-500">build_handler()</code> then wraps <strong>every</strong> registered descriptor unconditionally; nothing in the stack filters a middleware out for requests outside its declared app or route.
        </p>
        <p className={`mb-4 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          <code className="text-aquilia-500">MiddlewareConfig.scope_target</code> (intended for <code>"app:name"</code> / <code>"route:/pattern"</code> pinning) is accepted as a field but is never read by <code>MiddlewareStack</code>, <code>MiddlewareConfig.to_dict()</code>, or <code>AquiliaServer._register_app_middleware()</code> — it has no runtime effect. A middleware registered with <code>scope="app"</code> from one module's manifest still runs for <strong>every</strong> request handled by the process, not just that module's routes.
        </p>
        <div className="text-xs text-orange-400 bg-orange-500/5 p-3 rounded font-mono border border-orange-500/10">
          If you need a middleware to run only for a subset of routes, gate it inside <code>__call__</code> yourself (check <code>request.path</code> / <code>request.state</code>) — don't rely on <code>scope</code> for isolation.
        </div>
      </section>

      {/* Auto-discovery gotcha */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-yellow-400 uppercase tracking-wider mb-6`}>⚠ Auto-Discovery Can Silently Reset Your Manifest Config</h2>
        <p className={`mb-4 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          When <code className="text-aquilia-500">AppManifest.auto_discover</code> is <code>True</code> (the default), <code className="text-aquilia-400">RuntimeRegistry.perform_autodiscovery()</code> scans your module's package for any class named <code>*Middleware</code> or subclassing <DocTerm id="middleware.Middleware">Middleware</DocTerm>. For every discovered class whose import path lives <strong>inside your own module package</strong>, it rebuilds a fresh <code>MiddlewareConfig(class_path=...)</code> with default <code>scope="global"</code>, <code>priority=50</code>, no <code>config</code> — discarding any custom <code>scope</code>, <code>priority</code>, or constructor <code>config</code> you had explicitly set for that same class in <code>middleware=[MiddlewareConfig(...)]</code>.
        </p>
        <p className={`mb-4 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Middleware pointing at classes <strong>outside</strong> your module's package (e.g. built-ins from <code>aquilia.middleware_ext</code>) are left untouched — only local, in-package middleware classes are re-discovered and reset.
        </p>
        <CodeBlock language="python" filename="modules/billing/manifest.py" highlightLines={[8]}>{`from aquilia.manifest import AppManifest, MiddlewareConfig

manifest = AppManifest(
    name="billing",
    version="0.1.0",
    middleware=[
        # Custom priority/config here is DISCARDED at startup unless
        # auto_discover=False, because StripeClientMiddleware lives
        # inside modules.billing (this module's own package).
        MiddlewareConfig(
            class_path="modules.billing.middleware:StripeClientMiddleware",
            priority=30,
            config={"timeout_seconds": 15.0},
        ),
    ],
    auto_discover=False,  # <-- required to keep the custom priority/config
)`}</CodeBlock>
      </section>

      {/* The Middleware Contract */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>The Middleware Contract</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Every middleware in Aquilia must inherit from the <code className="text-aquilia-500">Middleware</code> base class and implement a callable coroutine signature that accepts exactly three parameters. The signature validation is enforced strictly at startup by the <DocTerm id="middleware.MiddlewareStack">MiddlewareStack</DocTerm>:
        </p>

        <CodeBlock language="python" filename="custom_middleware.py" highlightLines={[6, 9, 12]}>{`from aquilia.middleware import Middleware
from aquilia.response import Response

class CustomMiddleware(Middleware):
    async def __call__(self, request, ctx, next_handler) -> Response:
        # 1. Pre-processing: inspect or modify request
        # request.state["my_key"] = "value"

        # 2. Yield control to the next handler
        response = await next_handler(request, ctx)

        # 3. Post-processing: modify response
        # response.headers["X-Custom"] = "done"
        return response`}</CodeBlock>
      </section>

      {/* Short-circuiting */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Short-Circuiting a Request</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          A middleware is never <em>required</em> to call <code className="text-aquilia-500">next_handler</code> — returning a <DocTerm id="response.Response">Response</DocTerm> directly stops the request from reaching any middleware further in (and the controller). <code className="text-aquilia-500">MiddlewareStack._wrap_middleware()</code> only checks that <em>something</em> resolving to a <code>Response</code> came back; it doesn't care whether <code>next_handler</code> was ever awaited. Two built-ins do exactly this:
        </p>

        <div className="border-l border-white/10 pl-6 py-4 my-6 text-sm text-gray-400 space-y-4">
          <div>
            <span className="font-mono text-xs text-white font-bold uppercase">CORSMiddleware — preflight</span>
            <p className="mt-1">
              For <code className="text-aquilia-400">OPTIONS</code> preflight requests it builds and returns the 204 preflight <code>Response</code> straight from <code>_preflight()</code> — <code>next_handler</code> (and therefore your controller) is never invoked for that request.
            </p>
          </div>
          <div>
            <span className="font-mono text-xs text-white font-bold uppercase">CSRFMiddleware — missing/invalid token</span>
            <p className="mt-1">
              On an unsafe method with no valid token, it constructs a <code>403</code> JSON <code>Response</code> with <code>resp._fault = CSRFError(...)</code> attached and returns it immediately — again, without awaiting <code>next_handler</code>.
            </p>
          </div>
        </div>

        <CodeBlock language="python" filename="auth_guard_middleware.py" highlightLines={[7, 8, 9]}>{`from aquilia.middleware import Middleware
from aquilia.response import Response

class RequireApiKeyMiddleware(Middleware):
    async def __call__(self, request, ctx, next_handler) -> Response:
        api_key = request.header("x-api-key")
        if not api_key or api_key not in ("secret-key-1", "secret-key-2"):
            # Short-circuit: never calls next_handler, so the controller
            # and every middleware with a HIGHER priority number never runs.
            return Response.json({"error": "Invalid API key"}, status=401)

        return await next_handler(request, ctx)`}</CodeBlock>
      </section>

      {/* Production composition example */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Composing a Production Chain</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          <code className="text-aquilia-500">MiddlewareChain</code> ships three presets — <code className="text-aquilia-400">.chain()</code> (empty), <code className="text-aquilia-400">.minimal()</code>, <code className="text-aquilia-400">.defaults()</code> (both identical: <code>ExceptionMiddleware</code> priority 1 + <code>RequestIdMiddleware</code> priority 10), and <code className="text-aquilia-400">.production()</code> which additionally adds <code>CompressionMiddleware</code> (priority 15) and <code>TimeoutMiddleware</code> (priority 18, 30s). Start from a preset and append your own entries — the list append order doesn't matter, only <code>priority</code> does:
        </p>

        <CodeBlock language="python" filename="workspace.py" highlightLines={[6, 9, 10, 11]}>{`from aquilia.workspace import Workspace
from aquilia.integrations import MiddlewareChain

workspace = (
    Workspace("myapp")
    .middleware(
        MiddlewareChain
        .production()  # ExceptionMiddleware(1) + RequestIdMiddleware(10)
                        # + CompressionMiddleware(15) + TimeoutMiddleware(18)
        .use("modules.auth.middleware:JwtAuthMiddleware", priority=25)
        .use("aquilia.middleware_ext.RateLimitMiddleware", priority=30,
             default_limit=200, default_window=60.0)
    )
)`}</CodeBlock>
        <p className={`mt-4 text-xs leading-relaxed ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
          Remember: <code className="text-aquilia-400">FaultMiddleware</code> (priority 2, always on) still wraps everything at priority 1 <code>ExceptionMiddleware</code> in this example, so it fires first when a plain <code>Fault</code> subclass is raised. <code>ExceptionMiddleware</code> is your last-resort net if <code>FaultEngine.process()</code> itself re-raises.
        </p>
      </section>

      {/* Workspace Configuration (Global) */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Workspace-Level Middleware Config</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Workspace-level middleware configurations define the global pipeline wrapping all application modules. There are two primary styles to declare these in <code className="text-aquilia-500">workspace.py</code>:
        </p>

        {/* New Style */}
        <div className="mb-8">
          <span className="font-mono text-xs text-green-400 font-bold uppercase tracking-wider block mb-2">1. Fluent MiddlewareChain (Recommended Style)</span>
          <p className="text-sm text-gray-400 mb-4">
            Instantiates the fluent <code className="text-aquilia-400">MiddlewareChain</code> directly on the Workspace. This provides auto-completion, priority order sorting, and inline argument checks:
          </p>
          <CodeBlock language="python" filename="workspace.py" highlightLines={[5, 6, 7]}>{`from aquilia.workspace import Workspace
from aquilia.integrations import MiddlewareChain

workspace = (
    Workspace("myapp")
    .middleware(
        MiddlewareChain()
        .use("aquilia.middleware.ExceptionMiddleware", priority=1)
        .use("aquilia.middleware.RequestIdMiddleware", priority=5)
        .use("modules.auth.middleware:JwtAuthMiddleware", priority=25)
    )
)`}</CodeBlock>
        </div>

        {/* Old Style */}
        <div className="mb-8 border-l-2 border-red-500/30 pl-4 py-2">
          <span className="font-mono text-xs text-red-400 font-bold uppercase tracking-wider block mb-2">⚠️ Integration.middleware_chain() + .integrate() — Does Nothing at Runtime</span>
          <p className="text-sm text-gray-400 mb-4">
            <code className="text-yellow-400">Integration.middleware_chain()</code> is a static builder that returns a plain dict tagged <code className="text-aquilia-400">_integration_type: "middleware_chain"</code>. Passed into <code className="text-aquilia-400">Workspace.integrate()</code>, it is stored at <code className="text-aquilia-300">self._integrations["middleware_chain"]</code>, which serializes into <code className="text-aquilia-300">config["integrations"]["middleware_chain"]</code> — <strong>not</strong> the top-level <code className="text-aquilia-300">config["middleware_chain"]</code> key.
          </p>

          <div className="text-xs text-red-400 mb-4 bg-red-500/5 p-3 rounded font-mono border border-red-500/10 leading-relaxed">
            <strong>WARNING (verified from source):</strong> Every other integration reader (sessions, cache, storage, ...) uses <code>ConfigLoader.get_subsystem_config()</code>, which falls back from <code>get(name)</code> to <code>get(f"integrations.{'{name}'}")</code>. But <code>ConfigLoader.get_middleware_config()</code> is hand-written as <code>self.get("middleware_chain")</code> only — it has <strong>no</strong> fallback to <code>integrations.middleware_chain</code>. Entries configured this way are read by nothing and are silently never instantiated into the running <code>MiddlewareStack</code>. Only <code>Workspace.middleware(MiddlewareChain())</code> (which sets the dedicated top-level <code>_middleware_chain</code> attribute) actually wires middleware. Do not use <code>Integration.middleware_chain()</code> for anything you need to run.
          </div>

          <CodeBlock language="python" filename="workspace_legacy_broken.py" highlightLines={[5, 6, 7]}>{`from aquilia.workspace import Workspace
from aquilia.integrations import Integration

workspace = (
    Workspace("myapp")
    .integrate(
        # This chain is parsed, stored, and then never read again.
        Integration.middleware_chain(
            entries=[
                {"path": "aquilia.middleware.ExceptionMiddleware", "priority": 1},
                {"path": "aquilia.middleware.RequestIdMiddleware", "priority": 5},
            ]
        )
    )
)`}</CodeBlock>
        </div>
      </section>

      {/* Manifest-Based Module Configuration */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Module-Level Middleware Config</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Instead of wrapping the entire workspace, modules declare local middlewares inside their own <code className="text-aquilia-400">manifest.py</code> via <code className="text-aquilia-500">AppManifest</code>.
        </p>

        <div className="mb-8">
          <span className="font-mono text-xs text-green-400 font-bold uppercase tracking-wider block mb-2">1. AppManifest middleware Config (Recommended)</span>
          <p className="text-sm text-gray-400 mb-4">
            Passes list of <code className="text-aquilia-400">MiddlewareConfig</code> objects specifying the class path, target scope, priority, and custom parameters:
          </p>
          <CodeBlock language="python" filename="manifest.py" highlightLines={[6, 7, 8, 9]}>{`from aquilia.manifest import AppManifest, MiddlewareConfig

manifest = AppManifest(
    name="billing",
    version="0.1.0",
    middleware=[
        MiddlewareConfig(
            class_path="modules.billing.middleware:StripeClientMiddleware",
            scope="app",          # Affects wrap ORDER only — see warning above,
                                   # it does NOT limit this middleware to "billing"
            priority=30,
            config={"timeout_seconds": 15.0} # Custom constructor kwargs
        )
    ],
    auto_discover=False,  # keep this exact priority/config — see warning above
)`}</CodeBlock>
        </div>

        <div className="mb-8 border-l-2 border-yellow-500/20 pl-4 py-2">
          <span className="font-mono text-xs text-yellow-400 font-bold uppercase tracking-wider block mb-2">⚠️ AppManifest middlewares list (Deprecated)</span>
          <p className="text-sm text-gray-400 mb-4">
            Legacy manifests declared middleware as a list of tuples containing string paths and configuration dicts.
          </p>
          
          <div className="text-xs text-orange-400 mb-4 bg-orange-500/5 p-3 rounded font-mono border border-orange-500/10">
            <strong>WARNING:</strong> AppManifest will issue a deprecation warning at startup when detecting the <code>middlewares</code> attribute and will auto-convert them internally to MiddlewareConfig instances.
          </div>

          <CodeBlock language="python" filename="manifest_legacy.py" highlightLines={[6]}>{`manifest = AppManifest(
    name="billing",
    version="0.1.0",
    # Legacy tuples configuration
    middlewares=[
        ("modules.billing.middleware:StripeClientMiddleware", {"timeout_seconds": 15.0})
    ]
)`}</CodeBlock>
        </div>
      </section>

      {/* Next Section */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <span />
        <Link to="/docs/middleware/stack" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400 transition-colors">
          MiddlewareStack <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}