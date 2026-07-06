import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { Globe, Layers, Zap, ArrowRight, AlertCircle, Settings, Shield, Cpu, Activity } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function ServerASGI() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto select-none">
      {/* Header */}
      <div className="mb-10 animate-fade-in">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-aquilia-500/30 to-aquilia-500/10 flex items-center justify-center shadow-lg shadow-aquilia-500/10">
            <Globe className="w-5 h-5 text-aquilia-400" />
          </div>
          <div>
            <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
                ASGI Adapter
                <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
              </span>
            </h1>
            <p className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>aquilia.asgi — Bridging ASGI to Aquilia internals</p>
          </div>
        </div>

        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The <code>ASGIAdapter</code> is a high-performance 777-line class designed for maximum throughput and security. It translates raw ASGI connection scopes and event streams into Aquilia's <DocTerm id="http.request_type">Request</DocTerm> and Response abstractions, manages transactional dependency injection scopes, executes the middleware stack, and handles the ASGI lifespan handshake.
        </p>
      </div>

      {/* Custom Request Wave Pipeline (No boxy style, premium curve layout) */}
      <div className="w-full h-44 flex items-center justify-center my-6 relative">
        <svg className="w-full h-full max-w-2xl" viewBox="0 0 600 160" fill="none">
          <defs>
            <linearGradient id="waveLineGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#3b82f6" />
              <stop offset="50%" stopColor="#10b981" />
              <stop offset="100%" stopColor="#8b5cf6" />
            </linearGradient>
          </defs>

          {/* Pipeline path */}
          <path d="M 40 80 Q 150 10, 300 90 T 560 80" stroke="rgba(255,255,255,0.06)" strokeWidth="4" strokeLinecap="round" />
          <path d="M 40 80 Q 150 10, 300 90 T 560 80" stroke="url(#waveLineGrad)" strokeWidth="4" strokeLinecap="round" strokeDasharray="30, 20" />

          {/* Wave Pipeline Nodes */}
          {/* Node 1: ASGI Call */}
          <circle cx="60" cy="65" r="14" fill="#18181b" stroke="#3b82f6" strokeWidth="2" />
          <text x="60" y="68" textAnchor="middle" fill="#3b82f6" fontSize="7" fontWeight="bold" fontFamily="monospace">1</text>
          <text x="60" y="40" textAnchor="middle" fill="rgba(255,255,255,0.4)" fontSize="8" fontFamily="sans-serif">ASGI Call</text>

          {/* Node 2: Pool acquire */}
          <circle cx="180" cy="40" r="14" fill="#18181b" stroke="#10b981" strokeWidth="2" />
          <text x="180" y="43" textAnchor="middle" fill="#10b981" fontSize="7" fontWeight="bold" fontFamily="monospace">2</text>
          <text x="180" y="15" textAnchor="middle" fill="rgba(255,255,255,0.4)" fontSize="8" fontFamily="sans-serif">Ctx Pool</text>

          {/* Node 3: Version resolution */}
          <circle cx="300" cy="90" r="14" fill="#18181b" stroke="#f59e0b" strokeWidth="2" />
          <text x="300" y="93" textAnchor="middle" fill="#f59e0b" fontSize="7" fontWeight="bold" fontFamily="monospace">3</text>
          <text x="300" y="118" textAnchor="middle" fill="rgba(255,255,255,0.4)" fontSize="8" fontFamily="sans-serif">Version strip</text>

          {/* Node 4: Middleware chain */}
          <circle cx="420" cy="78" r="14" fill="#18181b" stroke="#8b5cf6" strokeWidth="2" />
          <text x="420" y="81" textAnchor="middle" fill="#8b5cf6" fontSize="7" fontWeight="bold" fontFamily="monospace">4</text>
          <text x="420" y="53" textAnchor="middle" fill="rgba(255,255,255,0.4)" fontSize="8" fontFamily="sans-serif">Middleware</text>

          {/* Node 5: Controller */}
          <circle cx="540" cy="80" r="14" fill="#18181b" stroke="#ec4899" strokeWidth="2" />
          <text x="540" y="83" textAnchor="middle" fill="#ec4899" fontSize="7" fontWeight="bold" fontFamily="monospace">5</text>
          <text x="540" y="108" textAnchor="middle" fill="rgba(255,255,255,0.4)" fontSize="8" fontFamily="sans-serif">Action</text>

          {/* Floating animated request indicator */}
          <circle r="4.5" fill="#3b82f6" className="filter drop-shadow-[0_0_6px_#3b82f6]">
            <animateMotion dur="4s" repeatCount="indefinite" path="M 40 80 Q 150 10, 300 90 T 560 80" />
          </circle>
        </svg>
      </div>

      {/* ASGI Protocol */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-400" />
          The ASGI Specification
        </h2>

        <p className={`mb-4 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          ASGI (Asynchronous Server Gateway Interface) defines the standard interface between async-capable Python web servers and web applications. Aquilia is an async-native, pure ASGI application that runs on any compliant server (such as <strong>Uvicorn</strong>, <strong>Hypercorn</strong>, or <strong>Granian</strong>).
        </p>

        <CodeBlock
          code={`# The standard ASGI 3.0 application signature:
async def application(
    scope: dict[str, Any], 
    receive: Callable[[], Awaitable[dict[str, Any]]], 
    send: Callable[[dict[str, Any]], Awaitable[None]]
) -> None:
    """
    scope:   Dictionary containing connection metadata (type, path, method, headers, etc.)
    receive: Async callable to receive incoming ASGI events (HTTP request bodies, WebSocket messages)
    send:    Async callable to push outgoing ASGI events to the client
    """
    ...`}
          language="python"
        />
      </section>

      {/* Class Definition */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Settings className="w-5 h-5 text-aquilia-400" />
          ASGIAdapter Architecture
        </h2>

        <p className={`mb-4 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The adapter uses `__slots__` to eliminate per-instance dictionary overhead and caches references to subsystems to avoid expensive attribute lookups during hot paths:
        </p>

        <CodeBlock
          code={`class ASGIAdapter:
    """ASGI application adapter that converts ASGI events to Aquilia Request/Response."""

    __slots__ = (
        "controller_router",
        "controller_engine",
        "middleware_stack",
        "server",
        "socket_runtime",
        "logger",
        "_cached_middleware_chain",
        "_default_container",
        "_debug",
        "_has_routes_cache",
        "_server_runtime",
    )

    def __init__(
        self,
        controller_router: ControllerRouter,
        controller_engine: Any,
        middleware_stack: MiddlewareStack,
        server: Any | None = None,
        socket_runtime: Any | None = None,
    ):
        self.controller_router = controller_router
        self.controller_engine = controller_engine
        self.middleware_stack = middleware_stack
        self.server = server
        self.socket_runtime = socket_runtime
        self.logger = logging.getLogger("aquilia.asgi")
        self._cached_middleware_chain = None  # Built once and cached`}
          language="python"
        />
      </section>

      {/* Key Features */}
      <section className="mb-12 space-y-6">
        <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Core Adapter Operations
        </h2>

        {/* RequestCtx Pooling */}
        <div>
          <h3 className={`text-lg font-bold mb-2 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-800'}`}>
            <Cpu className="w-4 h-4 text-emerald-400" />
            1. Zero-Allocation Context Pooling
          </h3>
          <p className={`text-sm mb-3 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            To prevent garbage collection overhead under high request concurrency, the adapter uses a lock-free RequestCtx object pool (<code>_ctx_pool</code>). Instead of allocating a new context object on every request, the adapter acquires a recycled context, resets its fields in-place, and releases it back to the pool once the response is sent.
          </p>
          <CodeBlock
            code={`# Inside handle_http:
ctx = _ctx_pool.acquire(
    request=request,
    identity=None,
    session=None,
    container=di_container,
)
try:
    response = await handler(request, ctx)
finally:
    _ctx_pool.release(ctx)`}
            language="python"
          />
        </div>

        {/* API Version prefix stripping */}
        <div>
          <h3 className={`text-lg font-bold mb-2 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-800'}`}>
            <ArrowRight className="w-4 h-4 text-emerald-400" />
            2. API Version & Path Prefix Pre-Resolution
          </h3>
          <p className={`text-sm mb-3 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            API versioning can affect the routing table. To resolve this, the adapter calls <code>_resolve_route_inputs()</code> before route matching. It evaluates version headers/queries, strips structural URL prefixes (e.g., stripping <code>/v2</code> from <code>/v2/users</code>), and passes the cleaned path to the <DocTerm id="controllers.router">Router</DocTerm>, ensuring version middleware can negotiate correctly without route mismatches.
          </p>
        </div>

        {/* Auto HEAD fallback */}
        <div>
          <h3 className={`text-lg font-bold mb-2 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-800'}`}>
            <Shield className="w-4 h-4 text-emerald-400" />
            3. RFC-Compliant Auto-HEAD Fallback
          </h3>
          <p className={`text-sm mb-3 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            In compliance with the HTTP/1.1 specification (RFC 7231 §4.3.2), if a client sends a <code>HEAD</code> request but no explicit <code>HEAD</code> handler is registered on the matched path, the adapter automatically matches the route's <code>GET</code> handler, runs the full middleware and validation logic, and then strips the body from the final response before sending headers.
          </p>
        </div>

        {/* 405 Method Checked */}
        <div>
          <h3 className={`text-lg font-bold mb-2 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-800'}`}>
            <AlertCircle className="w-4 h-4 text-rose-400" />
            4. Structured 405 Method Not Allowed Responses
          </h3>
          <p className={`text-sm mb-3 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            If a path matches a route but does not support the requested HTTP method, the adapter queries alternative methods, automatically sets a valid <code>Allow</code> header, and generates a structured error (returning styled HTML for browsers or structured JSON for APIs based on the <code>Accept</code> header).
          </p>
        </div>
      </section>

      {/* Built-in Health Endpoint */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Activity className="w-5 h-5 text-aquilia-400" />
          Built-in Performance-Optimized Health Endpoint
        </h2>

        <p className={`mb-4 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The health endpoint (<code>/_health</code> and <code>/health</code>) is handled directly inside the ASGI adapter, bypassing the entire middleware stack to minimize CPU overhead.
        </p>

        <ul className={`space-y-3 mb-6 text-sm ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          <li className="flex items-start gap-2">
            <span className="text-aquilia-400 mt-1">•</span>
            <div><strong>Method Restricting:</strong> Bypassed paths are restricted to <code>GET</code> and <code>HEAD</code> requests; other methods immediately return a <code>405 Method Not Allowed</code> response.</div>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-aquilia-400 mt-1">•</span>
            <div><strong>Subsystem Diagnostics:</strong> Integrates with the central <code>HealthRegistry</code> to query status details for registered subsystems (database, cache, task workers, mail, and storage).</div>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-aquilia-400 mt-1">•</span>
            <div><strong>Security Hardening:</strong> To satisfy OWASP compliance, the health endpoint manually applies strict security headers (e.g., <code>cache-control: no-store</code>, <code>x-content-type-options: nosniff</code>, <code>x-frame-options: DENY</code>) since it bypasses normal security middleware.</div>
          </li>
        </ul>

        <CodeBlock
          code={`# JSON payload structure returned by GET /_health:
{
  "status": "healthy", // "healthy" or "degraded"
  "metrics": {
    "total_requests": 15024,
    "inflight": 3,
    "total_errors": 4,
    "mean_latency_ms": 12.48
  },
  "subsystems": {
    "aquilary": { "status": "healthy", "message": "5 apps loaded" },
    "routing": { "status": "healthy", "message": "42 routes compiled" },
    "di": { "status": "healthy", "message": "128 services registered" },
    "cache": { "status": "healthy", "message": "redis active" }
  }
}`}
          language="json"
        />
      </section>

      {/* Lifespan Handshake */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Zap className="w-5 h-5 text-aquilia-400" />
          Lifespan Startup Guards & Error Sanitization
        </h2>

        <p className={`mb-4 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The ASGI lifespan protocol coordinates application startup and shutdown. Aquilia hardens this phase with two critical behaviors:
        </p>

        <div className="space-y-4">
          <div>
            <h4 className="font-bold text-amber-500 text-sm mb-1">Database Not Ready Guard (SystemExit)</h4>
            <p className={`text-xs leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
              If a module raises <code>DatabaseNotReadyError</code> (which inherits from <code>SystemExit</code>) during startup, the adapter catches the warning, logs it, and sends <code>lifespan.startup.complete</code> anyway. This prevents ASGI servers (like Uvicorn) from logging a fatal crash and disabling lifespan events, allowing the server to boot into a degraded/retry state.
            </p>
          </div>

          <div>
            <h4 className="font-bold text-red-400 text-sm mb-1">OWASP Error Sanitization</h4>
            <p className={`text-xs leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
              For standard exceptions raised during startup, the adapter logs the full traceback inside the application logs but returns a sanitized message (<code>"Server startup failed"</code>) back to the ASGI server's startup.failed event, preventing stack traces or database connection string secrets from leaking into system logs.
            </p>
          </div>
        </div>

        <CodeBlock
          code={`# Inside handle_lifespan:
if message["type"] == "lifespan.startup":
    try:
        await self.server.startup()
        await send({"type": "lifespan.startup.complete"})
    except SystemExit as e:
        self.logger.warning(f"Startup guard warning (non-fatal): {e}")
        await send({"type": "lifespan.startup.complete"})
    except Exception as e:
        self.logger.error("Startup error", exc_info=True)
        # Sanitize exception message to prevent internal details leakage
        await send({"type": "lifespan.startup.failed", "message": "Server startup failed"})
        raise`}
          language="python"
        />
      </section>

      {/* Deployment */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Globe className="w-5 h-5 text-aquilia-400" />
          Production Deployment
        </h2>

        <p className={`mb-4 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Deploy Aquilia using uvicorn or granian workers. Ensure lifespan is explicitly enabled.
        </p>

        <div className="space-y-4">
          <div>
            <p className={`text-sm font-semibold mb-2 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Uvicorn (Standard Python Worker)</p>
            <CodeBlock
              code={`# Production run (4 workers, lifespan enabled, access logging)
uvicorn main:server.app --host 0.0.0.0 --port 8000 --workers 4 --lifespan on --access-log`}
              language="bash"
            />
          </div>

          <div>
            <p className={`text-sm font-semibold mb-2 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Granian (High-Performance Rust-based ASGI Server)</p>
            <CodeBlock
              code={`# Command line deployment
granian --interface asgi --host 0.0.0.0 --port 8000 --workers 4 --threads 2 main:server.app`}
              language="bash"
            />
          </div>
        </div>
      </section>

      {/* Next */}
      <section className="mb-12 border-t border-white/5 pt-8">
        <div className="flex flex-col gap-2">
          <Link to="/docs/server/lifecycle" className={`text-sm font-medium ${isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-500'}`}>
            → Lifecycle: Startup/shutdown coordination
          </Link>
          <Link to="/docs/request-response/request" className={`text-sm font-medium ${isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-500'}`}>
            → Request: The Request object in depth
          </Link>
          <Link to="/docs/middleware/stack" className={`text-sm font-medium ${isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-500'}`}>
            → MiddlewareStack: How the chain is built and ordered
          </Link>
        </div>
      </section>
    
      <NextSteps />
    </div>
  )
}