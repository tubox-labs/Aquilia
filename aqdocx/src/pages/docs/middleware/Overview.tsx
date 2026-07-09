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
        <div className="border-l border-white/10 pl-6 py-4 my-6 text-sm text-gray-400 leading-relaxed">
          <p className="mb-4">
            Requests cascade through the stack from the outermost layer (lowest priority index) to the innermost layer (handler). Responses bubble back up in reverse order:
          </p>
          <div className="flex flex-col gap-2 font-mono text-xs my-4 max-w-lg">
            <div className="flex items-center gap-4 py-2 px-3 bg-white/2 border-l-2 border-aquilia-500 text-white rounded-r">
              <span className="text-aquilia-500 font-bold">INCOMING REQUEST</span>
            </div>
            <div className="pl-6 border-l border-white/10 flex flex-col gap-2 py-1">
              <div className="p-2 bg-white/5 rounded border border-white/5 text-gray-300">
                1. <DocTerm id="middleware.RequestIdMiddleware">RequestIdMiddleware</DocTerm> (Priority 5)
              </div>
              <div className="p-2 bg-white/5 rounded border border-white/5 text-gray-300">
                2. <DocTerm id="middleware.ExceptionMiddleware">ExceptionMiddleware</DocTerm> (Priority 10)
              </div>
              <div className="p-2 bg-white/5 rounded border border-white/5 text-gray-300">
                3. <DocTerm id="middleware.CORSMiddleware">CORSMiddleware</DocTerm> (Priority 20)
              </div>
              <div className="p-2 bg-white/5 rounded border border-white/5 text-gray-300">
                4. <DocTerm id="middleware.RequestScopeMiddleware">RequestScopeMiddleware</DocTerm> (Priority 30)
              </div>
            </div>
            <div className="flex items-center gap-4 py-2 px-3 bg-aquilia-500/10 border-l-2 border-aquilia-500 text-aquilia-400 rounded-r">
              <span>5. Final <DocTerm id="controller.controller">Controller</DocTerm> Route Handler</span>
            </div>
          </div>
        </div>
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
        <div className="mb-8 border-l-2 border-yellow-500/20 pl-4 py-2">
          <span className="font-mono text-xs text-yellow-400 font-bold uppercase tracking-wider block mb-2">⚠️ Legacy Integration.middleware_chain (Deprecated Style)</span>
          <p className="text-sm text-gray-400 mb-4">
            The older method calls the static builder helper <code className="text-yellow-400">Integration.middleware_chain()</code> inside the workspace <code className="text-aquilia-400">.integrate()</code> method.
          </p>
          
          <div className="text-xs text-orange-400 mb-4 bg-orange-500/5 p-3 rounded font-mono border border-orange-500/10">
            <strong>WARNING:</strong> This style bypasses direct validation constraints on the workspace object and is kept solely for backward compatibility. Do not use this in new projects.
          </div>

          <CodeBlock language="python" filename="workspace_legacy.py" highlightLines={[5, 6]}>{`from aquilia.workspace import Workspace
from aquilia.integrations import Integration

workspace = (
    Workspace("myapp")
    .integrate(
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
            scope="app",          # Limit scope to this app module only
            priority=30,
            config={"timeout_seconds": 15.0} # Custom constructor kwargs
        )
    ]
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