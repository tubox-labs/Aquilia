import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Layers, ArrowLeft, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'

export function MiddlewareRequestScope() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <Layers className="w-4 h-4" />
          <span>MIDDLEWARE / REQUEST DI SCOPE</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Request Scope DI Middleware
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <DocTerm id="middleware.RequestScopeMiddleware">RequestScopeMiddleware</DocTerm> bridges the dependency injection container and the request handler pipeline. It isolates resources per request by spawning isolated child containers and managing their teardown.
        </p>
      </div>

      {/* Scoping Lifecycle */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Request Scoping Lifecycle</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          For each incoming HTTP request, the middleware intercepts execution and performs these operations:
        </p>
        
        <div className="space-y-6 mb-8">
          <div className="border-l-2 border-aquilia-500/30 pl-4 py-1">
            <span className="font-mono text-xs text-white font-bold">1. Container Resolution</span>
            <p className="text-sm text-gray-400 mt-1">Retrieves the parent, module-level dependency container from the active <DocTerm id="aquilary.RuntimeRegistry">RuntimeRegistry</DocTerm>.</p>
          </div>
          <div className="border-l-2 border-aquilia-500/30 pl-4 py-1">
            <span className="font-mono text-xs text-white font-bold">2. Child Scope Spawning</span>
            <p className="text-sm text-gray-400 mt-1">
              Spawns an isolated child container by executing <code className="text-aquilia-400">container.create_request_scope()</code>. This keeps request-scoped instances isolated from other requests.
            </p>
          </div>
          <div className="border-l-2 border-aquilia-500/30 pl-4 py-1">
            <span className="font-mono text-xs text-white font-bold">3. Instance Registration</span>
            <p className="text-sm text-gray-400 mt-1">
              Binds the active <DocTerm id="request.Request">Request</DocTerm> instance directly to the child container using <code className="text-aquilia-400">container.register_instance(Request, request, scope="request")</code>, making it inject-ready.
            </p>
          </div>
          <div className="border-l-2 border-aquilia-500/30 pl-4 py-1">
            <span className="font-mono text-xs text-white font-bold">4. Context Injection</span>
            <p className="text-sm text-gray-400 mt-1">Stores references in request state and the handler context <code className="text-aquilia-400">ctx.container = request_container</code>.</p>
          </div>
          <div className="border-l-2 border-aquilia-500/30 pl-4 py-1">
            <span className="font-mono text-xs text-white font-bold">5. Teardown &amp; Disposal</span>
            <p className="text-sm text-gray-400 mt-1">
              Upon response completion (inside a <code className="text-aquilia-400">finally</code> block), calls <code className="text-aquilia-400">request_container.shutdown()</code> or <code className="text-aquilia-400">dispose()</code> to release db connections and cached variables.
            </p>
          </div>
        </div>
      </section>

      {/* Code Example */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Wiring Middleware</h2>
        <CodeBlock language="python" filename="request_scope_wire.py" highlightLines={[6, 9]}>{`from aquilia.middleware_ext import RequestScopeMiddleware, SimplifiedRequestScopeMiddleware

# 1. Custom ASGI application level:
# app.add_middleware(RequestScopeMiddleware, runtime=runtime)

# 2. Simplified HTTP-level middleware setup:
server.middleware(SimplifiedRequestScopeMiddleware(runtime=runtime))`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/middleware/security" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Security Headers
        </Link>
        <Link to="/docs/middleware/session" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400 transition-colors">
          Sessions <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
