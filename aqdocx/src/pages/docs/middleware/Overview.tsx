import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Layers } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function MiddlewareOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4"><Layers className="w-4 h-4" />Middleware</div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Middleware
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Middleware wraps every request/response cycle. Aquilia's <code className="text-aquilia-500">MiddlewareStack</code> supports scoped middleware (global, app, controller, route) with deterministic priority ordering.
        </p>
      </div>

      {/* Architecture SVG */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Middleware Pipeline</h2>
        <div className="flex items-center justify-center py-6">
          <img src="/architecture/middleware.svg" alt="Middleware Stack Architecture" className="max-w-full h-auto max-h-[360px]" />
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Writing Middleware</h2>
        <CodeBlock language="python" filename="Custom Middleware">{`from aquilia.request import Request
from aquilia.response import Response

# Middleware signature: (request, ctx, next) → Response
async def timing_middleware(request, ctx, next):
    """Measure request processing time."""
    import time
    start = time.perf_counter()

    # Call next handler in the chain
    response = await next(request, ctx)

    elapsed = time.perf_counter() - start
    response.headers["X-Response-Time"] = f"{elapsed:.4f}s"
    return response

# Class-based middleware
class CORSMiddleware:
    def __init__(self, allow_origins: list[str] = ["*"]):
        self.allow_origins = allow_origins

    async def __call__(self, request, ctx, next):
        response = await next(request, ctx)
        origin = request.header("Origin") or "*"
        if "*" in self.allow_origins or origin in self.allow_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
        return response`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Registering Middleware</h2>
        <CodeBlock language="python" filename="Registration">{`from aquilia.server import AquiliaServer
from aquilia.middleware import MiddlewareStack

server = AquiliaServer()

# Global middleware
server.middleware(timing_middleware)
server.middleware(CORSMiddleware(allow_origins=["https://example.com"]))

# With priority (lower = earlier in chain)
server.middleware(logging_middleware, priority=10)
server.middleware(auth_middleware, priority=20)

# Scoped middleware
server.middleware(admin_middleware, scope="controller:AdminController")

# MiddlewareStack API directly
stack = MiddlewareStack()
stack.add(timing_middleware, scope="global", priority=10, name="timing")
stack.add(auth_middleware, scope="global", priority=20, name="auth")

# Build the handler chain
handler = stack.build_handler(final_handler)`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Scope &amp; Priority</h2>
        <div className={`p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`}>
          <p className={`mb-3 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            Middleware is sorted by scope first, then by priority within each scope:
          </p>
          <ol className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li><span className="text-aquilia-500 font-bold">1.</span> <code className="text-aquilia-400">global</code> — Runs on every request</li>
            <li><span className="text-aquilia-500 font-bold">2.</span> <code className="text-aquilia-400">app:name</code> — Runs for a specific app module</li>
            <li><span className="text-aquilia-500 font-bold">3.</span> <code className="text-aquilia-400">controller:name</code> — Runs for a specific controller</li>
            <li><span className="text-aquilia-500 font-bold">4.</span> <code className="text-aquilia-400">route:pattern</code> — Runs for a specific route pattern</li>
          </ol>
          <p className={`mt-3 text-sm ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
            Within each scope, lower priority numbers execute first (outermost layer).
          </p>
        </div>
      </section>
    
      <NextSteps />
    </div>
  )
}