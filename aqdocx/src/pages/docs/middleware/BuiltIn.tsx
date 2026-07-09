import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Layers, ArrowLeft, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'

export function MiddlewareBuiltIn() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <Layers className="w-4 h-4" />
          <span>MIDDLEWARE / BUILT-IN</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Built-in Middleware
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia packages four highly optimized built-in middlewares covering request identification, error content negotiation, timeouts, and asynchronous compression.
        </p>
      </div>

      {/* RequestIdMiddleware */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-4`}><DocTerm id="middleware.RequestIdMiddleware">RequestIdMiddleware</DocTerm></h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Assigns a unique request ID. To maximize performance, it scans raw ASGI scope headers directly as raw byte arrays, avoiding costly high-level header parsing. Rather than calling slower <code className="text-aquilia-500">uuid.uuid4()</code>, it uses <code className="text-aquilia-500">os.urandom(16).hex()</code>, executing roughly 4× faster.
        </p>
        
        <div className="border-l-2 border-aquilia-500/30 pl-4 py-1 my-4 text-sm text-gray-400">
          The ID is stored in both <code className="text-aquilia-300">request.state["request_id"]</code> and <code className="text-aquilia-300">ctx.request_id</code>, and returned in the response header.
        </div>

        <CodeBlock language="python" filename="request_id.py" highlightLines={[4]}>{`from aquilia.middleware import RequestIdMiddleware

# Configure on server
server.middleware(RequestIdMiddleware(header_name="X-Request-ID"))

# Handler usage
async def my_handler(request, ctx):
    request_id = ctx.request_id  # accessible directly
    # or request.state["request_id"]`}</CodeBlock>
      </section>

      {/* ExceptionMiddleware */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-4`}><DocTerm id="middleware.ExceptionMiddleware">ExceptionMiddleware</DocTerm></h2>
        <p className={`mb-4 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Intercepts uncaught exceptions and converts them into structured error responses. It uses content negotiation via the client's <code className="text-aquilia-400">Accept</code> header:
        </p>

        <div className="border-l border-white/10 pl-6 py-4 my-6 text-sm text-gray-400 space-y-4">
          <div>
            <span className="font-mono text-xs text-white font-bold uppercase">HTML Clients (Accept: text/html)</span>
            <p className="mt-1">
              Renders a beautiful debug page in local development (<code className="text-aquilia-400">debug=True</code>) detailing local variables, stack frames, and active code slices. Renders a clean production error page when disabled.
            </p>
          </div>
          <div>
            <span className="font-mono text-xs text-white font-bold uppercase">API Clients (JSON)</span>
            <p className="mt-1">
              Enforces security policy <strong>ARCH-04</strong>: Never leaks stack tracebacks or raw exception strings in JSON bodies. Instead, serialized output follows a strict standard format:
            </p>
            <CodeBlock language="json" filename="error_response.json">{`{
  "error": {
    "code": "BP200",
    "message": "Validation failed",
    "domain": "validation",
    "details": [
      { "field": "email", "issue": "invalid email pattern" }
    ]
  }
}`}</CodeBlock>
          </div>
        </div>

        <div className="border-l-2 border-red-500/30 pl-4 py-1 my-4 text-sm text-gray-400">
          <strong>Domain to HTTP Status Code Mapping:</strong>
          <ul className="list-disc list-inside text-xs font-mono space-y-1 mt-2">
            <li>SECURITY / auth → 401 / 403</li>
            <li>ROUTING / MODEL (Not Found) → 404</li>
            <li>VALIDATION (BP200) → 400</li>
            <li>IO / STORAGE / CACHE → 502 / 503</li>
            <li>SYSTEM / FLOW → 500</li>
          </ul>
        </div>
      </section>

      {/* TimeoutMiddleware */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-4`}><DocTerm id="middleware.TimeoutMiddleware">TimeoutMiddleware</DocTerm></h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Wraps downstream execution inside a strict time constraint. If execution exceeds the limit, it raises a <code className="text-aquilia-400">RequestTimeoutFault</code> which bubbles through the exception middleware, returning a structured <code className="text-aquilia-400">504 Gateway Timeout</code>.
        </p>

        <CodeBlock language="python" filename="timeout.py" highlightLines={[3]}>{`from aquilia.middleware import TimeoutMiddleware

server.middleware(TimeoutMiddleware(timeout_seconds=15.0))`}</CodeBlock>
      </section>

      {/* CompressionMiddleware */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-4`}><DocTerm id="middleware.CompressionMiddleware">CompressionMiddleware</DocTerm></h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Compresses response payloads. Because CPU-bound Gzip compression can block Python's single-threaded event loop, this middleware offloads the actual compression call to a background thread pool via <code className="text-aquilia-500">asyncio.to_thread</code>.
        </p>
        
        <div className="border-l border-white/10 pl-6 py-4 my-6 text-sm text-gray-400 space-y-2 font-mono text-xs">
          <div>- Skips active streaming and chunked responses.</div>
          <div>- Emits HTTP header <code className="text-white">Vary: Accept-Encoding</code> to safeguard cache proxies.</div>
        </div>

        <CodeBlock language="python" filename="compression.py" highlightLines={[3]}>{`from aquilia.middleware import CompressionMiddleware

server.middleware(CompressionMiddleware(minimum_size=1024)) # Compress responses >= 1KB`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/middleware/stack" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> MiddlewareStack
        </Link>
        <Link to="/docs/middleware/static" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400 transition-colors">
          Static Files <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}