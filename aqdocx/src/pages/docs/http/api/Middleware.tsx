import { useTheme } from '../../../../context/ThemeContext'
import { CodeBlock } from '../../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { Globe } from 'lucide-react'
import { NextSteps } from '../../../../components/NextSteps'

export function HTTPAPIMiddleware() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Globe className="w-4 h-4" />
          HTTP Client / Core API
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            middleware.py
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Outbound onion-style middleware pipeline for request/response transformation, timeout enforcement, retries,
          caching, and error policy wrapping.
        </p>
      </div>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>1. Overview</h2>
        <div className={boxClass}>
          <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'} mb-3`}>
            middleware.py provides a composable client-side middleware abstraction. Middleware executes in insertion order
            before transport and unwinds in reverse order for response handling.
          </p>
          <p className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
            Lifecycle fit: RequestBuilder output -&gt; MiddlewareStack -&gt; InterceptorChain -&gt; Transport -&gt; Response.
          </p>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>2. Architecture and Design</h2>
        <div className="space-y-4">
          <div className={boxClass}>
            <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Core Abstractions</h3>
            <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              <li>• HTTPClientMiddleware: async callable contract with call_next continuation.</li>
              <li>• MiddlewareStack: mutable registry that compiles handlers and executes chain.</li>
              <li>• Built-ins: logging, headers, timeout, error policy, retry, compression, cache, base URL, cookies.</li>
            </ul>
          </div>
          <div className={boxClass}>
            <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Subsystem Integration</h3>
            <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              <li>• faults: TimeoutMiddleware and TimeoutInterceptor raise RequestTimeoutFault.</li>
              <li>• retry.py: RetryMiddleware delegates to RetryExecutor.</li>
              <li>• cookies.py: CookieMiddleware manages request Cookie and response Set-Cookie plumbing.</li>
              <li>• request/response: all middleware operate on immutable-copy request rewriting and response post-processing.</li>
            </ul>
          </div>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>3. API Reference (Exhaustive)</h2>
        <CodeBlock language="python" filename="Core protocol and stack">{`MiddlewareHandler = Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]]

class HTTPClientMiddleware(ABC):
    async def __call__(self, request: HTTPClientRequest, call_next: MiddlewareHandler) -> HTTPClientResponse

class MiddlewareStack:
    def __init__(self)
    def add(self, middleware: HTTPClientMiddleware) -> MiddlewareStack
    def add_many(self, middleware: list[HTTPClientMiddleware]) -> MiddlewareStack
    def set_handler(self, handler: MiddlewareHandler) -> MiddlewareStack
    def build(self) -> MiddlewareHandler
    async def execute(self, request: HTTPClientRequest) -> HTTPClientResponse`}</CodeBlock>

        <CodeBlock language="python" filename="Built-in middleware classes">{`class LoggingMiddleware(HTTPClientMiddleware):
    def __init__(self, logger_name: str = "aquilia.http.client", log_body: bool = False)
    async def __call__(...)

class HeadersMiddleware(HTTPClientMiddleware):
    def __init__(self, headers: dict[str, str])
    async def __call__(...)

class TimeoutMiddleware(HTTPClientMiddleware):
    def __init__(self, timeout: float)
    async def __call__(...)  # raises RequestTimeoutFault on timeout

class ErrorHandlingMiddleware(HTTPClientMiddleware):
    def __init__(self, raise_for_status: bool = True)
    async def __call__(...)  # calls response.raise_for_status() when enabled

class RetryMiddleware(HTTPClientMiddleware):
    def __init__(self, strategy: Any = None)
    async def __call__(...)  # delegates RetryExecutor.execute

class CompressionMiddleware(HTTPClientMiddleware):
    def __init__(self, accept_encoding: str = "gzip, deflate")
    async def __call__(...)

class CacheMiddleware(HTTPClientMiddleware):
    def __init__(self, cache: dict[str, tuple[HTTPClientResponse, float]] | None = None, max_age: float = 300.0)
    async def __call__(...)  # caches successful GET responses

class BaseURLMiddleware(HTTPClientMiddleware):
    def __init__(self, base_url: str)
    async def __call__(...)

class CookieMiddleware(HTTPClientMiddleware):
    def __init__(self, jar: Any = None)
    @property def jar(self) -> Any
    async def __call__(...)`}</CodeBlock>

        <CodeBlock language="python" filename="Factory">{`def create_middleware_stack(
    *,
    base_url: str | None = None,
    timeout: float | None = None,
    headers: dict[str, str] | None = None,
    enable_logging: bool = False,
    enable_retry: bool = False,
    enable_cache: bool = False,
    enable_cookies: bool = False,
    raise_for_status: bool = False,
) -> list[HTTPClientMiddleware]`}</CodeBlock>

        <div className={boxClass}>
          <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Exceptions and Fault Mapping</h3>
          <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li>• RuntimeError: MiddlewareStack.build/execute when no handler is configured.</li>
            <li>• RequestTimeoutFault: TimeoutMiddleware timeout path.</li>
            <li>• HTTPStatusFault subclasses: ErrorHandlingMiddleware when raise_for_status=True and status is 4xx/5xx.</li>
            <li>• RetryExhaustedFault and transport faults may surface through RetryMiddleware strategy execution.</li>
          </ul>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>4. Behavior and Lifecycle</h2>
        <CodeBlock language="python" filename="Onion execution order">{`# insertion order
stack.add(LoggingMiddleware())
stack.add(TimeoutMiddleware(3.0))
stack.add(RetryMiddleware())

# request path: Logging -> Timeout -> Retry -> handler
# response path: handler -> Retry -> Timeout -> Logging`}</CodeBlock>

        <CodeBlock language="python" filename="Dynamic chain execution">{`response = await stack.execute(request)
# MiddlewareStack.execute builds wrappers per call and runs composed handler`}</CodeBlock>

        <div className={boxClass}>
          <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Async behavior: each middleware awaits call_next and can short-circuit by returning response directly.
            CacheMiddleware is an example that can return cached response without invoking downstream handlers.
          </p>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>5. Usage Examples</h2>
        <CodeBlock language="python" filename="Minimal custom middleware">{`class CorrelationMiddleware(HTTPClientMiddleware):
    async def __call__(self, request, call_next):
        headers = dict(request.headers)
        headers.setdefault("X-Correlation-ID", "corr-123")
        return await call_next(request.copy(headers=headers))`}</CodeBlock>

        <CodeBlock language="python" filename="Factory usage">{`middleware = create_middleware_stack(
    base_url="https://api.example.com",
    timeout=5.0,
    enable_retry=True,
    enable_cookies=True,
    raise_for_status=True,
)

client = AsyncHTTPClient(middleware=middleware)`}</CodeBlock>

        <CodeBlock language="python" filename="Edge case: cache only GET">{`cache = CacheMiddleware(max_age=60)
# POST requests bypass cache logic entirely`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>6. Advanced Topics</h2>
        <div className="space-y-4">
          <div className={boxClass}>
            <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Performance Considerations</h3>
            <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              <li>• Keep middleware count bounded on hot paths to reduce per-request wrapper overhead.</li>
              <li>• CacheMiddleware stores HTTPClientResponse objects in-memory; budget memory per URL and TTL policy.</li>
              <li>• Logging body payloads is expensive and sensitive; keep log_body disabled unless debugging.</li>
            </ul>
          </div>
          <div className={boxClass}>
            <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Extensibility Points</h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Implement HTTPClientMiddleware for cross-cutting concerns such as distributed tracing, request shaping,
              custom circuit breakers, and policy-driven fallback responses.
            </p>
          </div>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>7. Integration</h2>
        <div className={boxClass}>
          <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li>• sessions: CookieMiddleware can bridge upstream sticky sessions across requests.</li>
            <li>• config/pyconfig: create_middleware_stack flags are typically derived from environment config profiles.</li>
            <li>• storage: combine middleware with streaming responses to pipe to storage providers.</li>
            <li>• tasks: background workers can reuse a stable middleware chain for consistent retry/logging semantics.</li>
            <li>• effects/flow: mount middleware-configured HTTP clients as effect dependencies for deterministic side-effect boundaries.</li>
          </ul>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>8. Best Practices</h2>
        <div className={boxClass}>
          <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li>• Order middleware intentionally: auth/header shaping before timeout/retry, error policy at outer boundary.</li>
            <li>• Keep RetryMiddleware idempotency-aware (default retry methods are idempotent verbs).</li>
            <li>• Prefer execute() over build() in async contexts to avoid event-loop reentry issues.</li>
            <li>• Separate cache instances by tenant/auth context to avoid cross-principal data bleed.</li>
          </ul>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>9. Edge Cases and Failure Modes</h2>
        <CodeBlock language="python" filename="Missing handler">{`stack = MiddlewareStack()
await stack.execute(request)  # RuntimeError: MiddlewareStack requires a handler`}</CodeBlock>

        <CodeBlock language="python" filename="Timeout failure">{`timeout = TimeoutMiddleware(0.01)
# if downstream call exceeds threshold -> RequestTimeoutFault`}</CodeBlock>

        <CodeBlock language="python" filename="Non-reusable cache entries">{`# CacheMiddleware caches successful responses only
# 4xx/5xx responses bypass cache insert`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>10. Internal Notes</h2>
        <div className={boxClass}>
          <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li>• MiddlewareStack.build composes chain using run_until_complete on make_chain coroutine.</li>
            <li>• MiddlewareStack.execute composes chain in-call and is the safer path for active async runtimes.</li>
            <li>• CompressionMiddleware only sets Accept-Encoding; decompression is transport responsibility.</li>
            <li>• BaseURLMiddleware only rewrites URLs lacking scheme.</li>
          </ul>
        </div>
      </section>

      <div className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
        Related references: <Link className="text-aquilia-500 hover:text-aquilia-400" to="/docs/http/api/request">request.py</Link>,{' '}
        <Link className="text-aquilia-500 hover:text-aquilia-400" to="/docs/http/api/auth">auth.py</Link>,{' '}
        <Link className="text-aquilia-500 hover:text-aquilia-400" to="/docs/http/advanced">Advanced HTTP Usage</Link>.
      </div>

      <NextSteps
        items={[
          { text: 'multipart.py Reference', link: '/docs/http/api/multipart' },
          { text: 'streaming.py Reference', link: '/docs/http/api/streaming' },
          { text: 'Retry Strategies', link: '/docs/http/advanced' },
        ]}
      />
    </div>
  )
}
