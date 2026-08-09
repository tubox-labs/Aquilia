import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Layers, ArrowLeft, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'

export function MiddlewareStack() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <Layers className="w-4 h-4" />
          <span>MIDDLEWARE / STACK & COMPOSITION</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Middleware Stack
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <DocTerm id="middleware.MiddlewareStack">MiddlewareStack</DocTerm> manages middleware registration, verifies structural contracts at startup, and compiles the execution pipelines.
        </p>
      </div>

      {/* Strict Signature Validation */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Startup Contract Validation</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          When you register middleware using <code className="text-aquilia-500">.middleware()</code> or direct <code className="text-aquilia-500">stack.add()</code>, Aquilia performs four rigorous inspection checks using Python's reflection APIs before running the server:
        </p>

        <div className="space-y-6 mb-8">
          <div className="border-l-2 border-red-500/30 pl-4">
            <span className="font-mono text-xs text-red-400 uppercase font-bold">1. Inheritance Check</span>
            <p className="text-sm text-gray-400 mt-1">
              Class instances must inherit from the <code className="text-aquilia-400">Middleware</code> base class. Raw functions bypass this check if they are directly callable.
            </p>
          </div>
          <div className="border-l-2 border-red-500/30 pl-4">
            <span className="font-mono text-xs text-red-400 uppercase font-bold">2. Callability Check</span>
            <p className="text-sm text-gray-400 mt-1">
              The registered object must be callable (i.e. possess an active <code className="text-aquilia-400">__call__</code> method or be a routine).
            </p>
          </div>
          <div className="border-l-2 border-red-500/30 pl-4">
            <span className="font-mono text-xs text-red-400 uppercase font-bold">3. Parameter Count Check</span>
            <p className="text-sm text-gray-400 mt-1">
              Signature inspection (via <code className="text-aquilia-400">inspect.signature</code>) enforces exactly three parameters: <code className="text-aquilia-300">(request, ctx, next_handler)</code>. Binds are verified at registration.
            </p>
          </div>
          <div className="border-l-2 border-red-500/30 pl-4">
            <span className="font-mono text-xs text-red-400 uppercase font-bold">4. Async Coroutine Check</span>
            <p className="text-sm text-gray-400 mt-1">
              The entrypoint MUST be a coroutine function (<code className="text-aquilia-400">async def</code>). Sync callables trigger a runtime <code className="text-aquilia-400">TypeError</code> at boot.
            </p>
          </div>
        </div>
      </section>

            {/* New Hook-Based API */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Middleware Hooks</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          The <code>Middleware</code> base class (now located in <code>aquilia.middleware.core.base</code>) provides a rich hook-based API for intercepting requests and managing lifespan:
        </p>

        <div className="space-y-4 mb-8 text-sm">
          <div className="border-l-2 border-aquilia-500/30 pl-4">
            <code className="text-aquilia-400 font-bold">async def handle(self, request, ctx, next_handler)</code>
            <p className="text-gray-400 mt-1">The primary hook for wrapping the request. Call <code>await next_handler(request, ctx)</code> to continue the chain.</p>
          </div>
          <div className="border-l-2 border-aquilia-500/30 pl-4">
            <code className="text-aquilia-400 font-bold">async def before(self, request, ctx) -&gt; Response | None</code>
            <p className="text-gray-400 mt-1">Runs before the request is passed to the next handler. Return a Response to short-circuit.</p>
          </div>
          <div className="border-l-2 border-aquilia-500/30 pl-4">
            <code className="text-aquilia-400 font-bold">async def after(self, request, ctx, response) -&gt; Response</code>
            <p className="text-gray-400 mt-1">Runs after the request returns from the downstream chain. Allows modifying the outgoing response.</p>
          </div>
          <div className="border-l-2 border-aquilia-500/30 pl-4">
            <code className="text-aquilia-400 font-bold">async def should_run(self, request, ctx) -&gt; bool</code>
            <p className="text-gray-400 mt-1">Opt-in conditional execution. If returns False, the middleware is skipped for this request.</p>
          </div>
          <div className="border-l-2 border-aquilia-500/30 pl-4">
            <code className="text-aquilia-400 font-bold">async def setup(self, app)</code> / <code className="text-aquilia-400 font-bold">async def teardown(self, app)</code>
            <p className="text-gray-400 mt-1">Lifespan hooks for initializing or cleaning up resources (e.g. database pools) on application startup and shutdown.</p>
          </div>
        </div>
      </section>

      {/* Priority Collision Detection */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Priority Collision Detection</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          When adding middleware via <code>stack.add()</code>, Aquilia will check for priority collisions. If two middlewares share the exact same scope and priority, a warning is emitted. If the app is configured with <code>strict_priorities=True</code>, this will instead raise a <code className="text-aquilia-400">MiddlewarePriorityCollisionFault</code> (from <code>aquilia.middleware.stack.errors</code>).
        </p>
      </section>

      {/* Code Example */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Manipulating the Stack</h2>
        <CodeBlock language="python" filename="custom_stack.py" highlightLines={[6, 9, 13]}>{`from aquilia.middleware.stack.registry import MiddlewareStack
from my_middlewares import SecurityMiddleware, LoggingMiddleware, Handler

stack = MiddlewareStack()

# 1. Register with scopes and priority
stack.add(SecurityMiddleware(), scope="global", priority=10, name="security")
stack.add(LoggingMiddleware(), scope="global", priority=90, name="logging")

# 2. Build normal handler (executes: Security -> Logging -> Handler)
handler = stack.build_handler(final_handler=Handler)

# 3. Build fast handler (executes: Security -> Handler; skips Logging)
# build_fast_handler has been removed in v1.4.0b2`}</CodeBlock>
      </section>

      {/* Priority Reference Constants */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Priority Reference (aquilia.middleware.core.priority.Priority)</h2>
        <p className={`mb-4 leading-relaxed text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          These are the exact priority numbers <code className="text-aquilia-500">AquiliaServer</code> assigns when it wires each built-in middleware — not the fictional numbers you'll find in older docs. Lower number = wraps closer to the outside = runs first on the way in.
        </p>
        
        <div className="w-full overflow-x-auto">
          <table className="w-full text-sm text-left border-collapse">
            <thead>
              <tr className="border-b border-white/10 text-aquilia-400 font-mono text-xs uppercase tracking-wider">
                <th className="py-3 px-4">Priority Constant</th>
                <th className="py-3 px-4">Value</th>
                <th className="py-3 px-4">Middleware</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 font-sans text-gray-400">
              <tr className="hover:bg-white/2 transition-colors"><td className="py-3.5 px-4 font-mono text-xs">EXCEPTION</td><td className="py-3.5 px-4 font-mono text-xs">1</td><td className="py-3.5 px-4 text-xs">ExceptionMiddleware</td></tr>
              <tr className="hover:bg-white/2 transition-colors"><td className="py-3.5 px-4 font-mono text-xs">FAULTS</td><td className="py-3.5 px-4 font-mono text-xs">2</td><td className="py-3.5 px-4 text-xs">FaultMiddleware</td></tr>
              <tr className="hover:bg-white/2 transition-colors"><td className="py-3.5 px-4 font-mono text-xs">PROXY_FIX</td><td className="py-3.5 px-4 font-mono text-xs">3</td><td className="py-3.5 px-4 text-xs">ProxyFixMiddleware</td></tr>
              <tr className="hover:bg-white/2 transition-colors"><td className="py-3.5 px-4 font-mono text-xs">HTTPS_REDIRECT</td><td className="py-3.5 px-4 font-mono text-xs">4</td><td className="py-3.5 px-4 text-xs">HTTPSRedirectMiddleware</td></tr>
              <tr className="hover:bg-white/2 transition-colors"><td className="py-3.5 px-4 font-mono text-xs">REQUEST_SCOPE</td><td className="py-3.5 px-4 font-mono text-xs">5</td><td className="py-3.5 px-4 text-xs">ServerRequestScopeMiddleware</td></tr>
              <tr className="hover:bg-white/2 transition-colors"><td className="py-3.5 px-4 font-mono text-xs">VERSIONING</td><td className="py-3.5 px-4 font-mono text-xs">5</td><td className="py-3.5 px-4 text-xs">VersionMiddleware</td></tr>
              <tr className="hover:bg-white/2 transition-colors"><td className="py-3.5 px-4 font-mono text-xs">STATIC</td><td className="py-3.5 px-4 font-mono text-xs">6</td><td className="py-3.5 px-4 text-xs">StaticMiddleware</td></tr>
              <tr className="hover:bg-white/2 transition-colors"><td className="py-3.5 px-4 font-mono text-xs">SECURITY_HEADERS</td><td className="py-3.5 px-4 font-mono text-xs">7</td><td className="py-3.5 px-4 text-xs">SecurityHeadersMiddleware</td></tr>
              <tr className="hover:bg-white/2 transition-colors"><td className="py-3.5 px-4 font-mono text-xs">HSTS</td><td className="py-3.5 px-4 font-mono text-xs">8</td><td className="py-3.5 px-4 text-xs">HSTSMiddleware</td></tr>
              <tr className="hover:bg-white/2 transition-colors"><td className="py-3.5 px-4 font-mono text-xs">CSP</td><td className="py-3.5 px-4 font-mono text-xs">9</td><td className="py-3.5 px-4 text-xs">CSPMiddleware</td></tr>
              <tr className="hover:bg-white/2 transition-colors"><td className="py-3.5 px-4 font-mono text-xs">REQUEST_ID</td><td className="py-3.5 px-4 font-mono text-xs">10</td><td className="py-3.5 px-4 text-xs">RequestIdMiddleware</td></tr>
              <tr className="hover:bg-white/2 transition-colors"><td className="py-3.5 px-4 font-mono text-xs">CORS</td><td className="py-3.5 px-4 font-mono text-xs">11</td><td className="py-3.5 px-4 text-xs">CORSMiddleware</td></tr>
              <tr className="hover:bg-white/2 transition-colors"><td className="py-3.5 px-4 font-mono text-xs">RATE_LIMIT_ANON</td><td className="py-3.5 px-4 font-mono text-xs">12</td><td className="py-3.5 px-4 text-xs">RateLimitMiddleware</td></tr>
              <tr className="hover:bg-white/2 transition-colors"><td className="py-3.5 px-4 font-mono text-xs">INSPECTOR</td><td className="py-3.5 px-4 font-mono text-xs">13</td><td className="py-3.5 px-4 text-xs">InspectorMiddleware</td></tr>
              <tr className="hover:bg-white/2 transition-colors"><td className="py-3.5 px-4 font-mono text-xs">INSPECTOR_TOOLBAR</td><td className="py-3.5 px-4 font-mono text-xs">14</td><td className="py-3.5 px-4 text-xs">ToolbarInjectionMiddleware</td></tr>
              <tr className="hover:bg-white/2 transition-colors"><td className="py-3.5 px-4 font-mono text-xs">AUTH</td><td className="py-3.5 px-4 font-mono text-xs">15</td><td className="py-3.5 px-4 text-xs">AquilAuthMiddleware</td></tr>
              <tr className="hover:bg-white/2 transition-colors"><td className="py-3.5 px-4 font-mono text-xs">RATE_LIMIT_IDENTITY</td><td className="py-3.5 px-4 font-mono text-xs">16</td><td className="py-3.5 px-4 text-xs">RateLimitMiddleware (Identity)</td></tr>
              <tr className="hover:bg-white/2 transition-colors"><td className="py-3.5 px-4 font-mono text-xs">CSRF</td><td className="py-3.5 px-4 font-mono text-xs">20</td><td className="py-3.5 px-4 text-xs">CSRFMiddleware</td></tr>
              <tr className="hover:bg-white/2 transition-colors"><td className="py-3.5 px-4 font-mono text-xs">I18N</td><td className="py-3.5 px-4 font-mono text-xs">24</td><td className="py-3.5 px-4 text-xs">I18nMiddleware</td></tr>
              <tr className="hover:bg-white/2 transition-colors"><td className="py-3.5 px-4 font-mono text-xs">TEMPLATES</td><td className="py-3.5 px-4 font-mono text-xs">25</td><td className="py-3.5 px-4 text-xs">TemplateMiddleware</td></tr>
              <tr className="hover:bg-white/2 transition-colors"><td className="py-3.5 px-4 font-mono text-xs">CACHE</td><td className="py-3.5 px-4 font-mono text-xs">26</td><td className="py-3.5 px-4 text-xs">CacheMiddleware</td></tr>
              <tr className="hover:bg-white/2 transition-colors"><td className="py-3.5 px-4 font-mono text-xs">APPLICATION_DEFAULT</td><td className="py-3.5 px-4 font-mono text-xs">50</td><td className="py-3.5 px-4 text-xs">Application User Middlewares</td></tr>
            </tbody>
          </table>
        </div>
        <p className={`mt-4 text-xs leading-relaxed ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
          Source: <code className="text-aquilia-500">aquilia.middleware.core.priority.Priority</code>
        </p>

      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/middleware" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Overview
        </Link>
        <Link to="/docs/middleware/built-in" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400 transition-colors">
          Built-in Middleware <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}