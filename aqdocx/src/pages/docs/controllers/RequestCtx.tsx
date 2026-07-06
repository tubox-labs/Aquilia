import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { Box, Layers, Zap, Code, ArrowRight } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function ControllersRequestCtx() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto space-y-12 pb-16">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-aquilia-500/30 to-aquilia-500/10 flex items-center justify-center">
            <Box className="w-5 h-5 text-aquilia-400" />
          </div>
          <div>
            <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
                RequestCtx
                <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
              </span>
            </h1>
            <p className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>aquilia.controller.base.RequestCtx — Request context object</p>
          </div>
        </div>

        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The <DocTerm id="controllers.requestctx">RequestCtx</DocTerm> class encapsulates the request lifecycle, providing access to the current request, user identity, session state, DI container, and mutable state dict.
        </p>
      </div>

      {/* Class definition */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Code className="w-5 h-5 text-aquilia-400" />
          Class Definition & slots
        </h2>

        <p className={`${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          For maximum performance, <code className="text-aquilia-500">RequestCtx</code> is optimized using Python <code className="text-aquilia-500">__slots__</code>, yielding up to 40% faster attribute access:
        </p>

        <CodeBlock
          code={`class RequestCtx:
    __slots__ = (
        "request",
        "identity",
        "session",
        "auth",
        "container",
        "state",
        "request_id",
        "_extra",
    )

    def __init__(
        self,
        request: "Request",
        identity: Optional["Identity"] = None,
        session: Optional["Session"] = None,
        auth: Any | None = None,
        container: Any | None = None,
        state: dict[str, Any] | None = None,
        request_id: str | None = None,
    ):
        self.request = request
        self.identity = identity
        self.session = session
        self.auth = auth
        self.container = container
        self.state: dict[str, Any] = state if state is not None else {}
        self.request_id = request_id
        self._extra: dict[str, Any] | None = None`}
          language="python"
        />

        <div className="p-4 border-l-4 border-aquilia-500 bg-aquilia-500/5 rounded-r-xl">
          <p className={`text-xs ${isDark ? 'text-aquilia-300' : 'text-aquilia-700'}`}>
            <strong>Escape Hatch:</strong> If middleware or extensions need to set dynamic attributes, <code className="text-aquilia-500">RequestCtx</code> intercepts those calls via custom <code className="text-aquilia-500">__getattr__</code> and <code className="text-aquilia-500">__setattr__</code> methods, storing them inside the <code className="text-aquilia-500">_extra</code> dictionary safely.
          </p>
        </div>
      </section>

      {/* RequestCtx Pool */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-400" />
          RequestCtx Object Pool
        </h2>
        <p className={`${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          To avoid heap allocation overhead during high-concurrency requests, Aquilia uses a lock-free <code className="text-aquilia-500">_RequestCtxPool</code>. Used internally by the engine to acquire and release contexts, resetting fields in-place:
        </p>

        <CodeBlock
          code={`# Behind the scenes:
ctx = _ctx_pool.acquire(request=request, container=container)
# ... execution ...
_ctx_pool.release(ctx)  # clears references to prevent GC leaks`}
          language="python"
        />
      </section>

      {/* Properties */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Zap className="w-5 h-5 text-aquilia-400" />
          Delegated Properties & Methods
        </h2>
        <p className={`${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          For convenience, <code className="text-aquilia-500">RequestCtx</code> exposes properties that forward directly to the underlying <code className="text-aquilia-500">Request</code> object:
        </p>

        <div className="overflow-x-auto py-2">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-white/10 text-gray-500 dark:text-gray-400">
                <th className="text-left px-4 py-3 font-semibold">Attribute</th>
                <th className="text-left px-4 py-3 font-semibold">Type</th>
                <th className="text-left px-4 py-3 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5 text-gray-300' : 'divide-gray-100 text-gray-700'}`}>
              {[
                ['path', 'str', 'Current request path.'],
                ['method', 'str', 'HTTP method (e.g. GET).'],
                ['headers', 'Headers', 'Case-insensitive request headers.'],
                ['query_params', 'MultiDict', 'URL query parameters.'],
                ['query_param(key, default)', 'str | None', 'Retrieves first query parameter value.'],
                ['json()', 'async Any', 'Parses JSON request body.'],
                ['body()', 'async bytes', 'Reads raw body bytes.'],
                ['form()', 'async FormData', 'Parses URL-encoded or multipart form data.']
              ].map(([attr, type_, desc], i) => (
                <tr key={i} className="hover:bg-aquilia-500/5 transition-colors">
                  <td className="px-4 py-2 font-mono text-xs text-aquilia-500 font-semibold">{attr}</td>
                  <td className="px-4 py-2 font-mono text-xs">{type_}</td>
                  <td className="px-4 py-2 text-xs">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Navigation */}
      <div className="flex justify-between items-center pt-8 border-t border-gray-200 dark:border-white/10">
        <Link to="/docs/controllers/decorators" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition-colors">
          <ArrowRight className="w-4 h-4 rotate-180" />
          <span>Route Decorators</span>
        </Link>
        <Link to="/docs/controllers/factory" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition-colors">
          <span>ControllerFactory</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}