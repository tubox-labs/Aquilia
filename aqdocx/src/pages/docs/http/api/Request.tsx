import { useTheme } from '../../../../context/ThemeContext'
import { CodeBlock } from '../../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { Globe } from 'lucide-react'
import { NextSteps } from '../../../../components/NextSteps'

export function HTTPAPIRequest() {
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
            request.py
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Low-level request construction primitives for AquilaHTTP. This module defines immutable request objects,
          URL/header/body validation, and the fluent request builder used by AsyncHTTPClient, HTTPSession,
          interceptors, middleware, and transport execution.
        </p>
      </div>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>1. Overview</h2>
        <div className={boxClass}>
          <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'} mb-3`}>
            request.py is the canonical request-shaping boundary for the HTTP client subsystem. It is intentionally split
            into two layers:
          </p>
          <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li>• HTTPClientRequest: immutable payload consumed by transport and interception stacks.</li>
            <li>• RequestBuilder: mutable fluent DSL that validates and materializes HTTPClientRequest.</li>
          </ul>
          <p className={`mt-3 text-sm ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
            Request lifecycle fit: controller/task code -&gt; AsyncHTTPClient or HTTPSession helpers -&gt; RequestBuilder -&gt;
            HTTPClientRequest -&gt; middleware/interceptors -&gt; transport.
          </p>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>2. Architecture and Design</h2>
        <div className="space-y-4">
          <div className={boxClass}>
            <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Design Decisions</h3>
            <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              <li>• RequestBuilder stores mutable assembly state in private slots for low-overhead chaining.</li>
              <li>• build() emits HTTPClientRequest dataclass instances to isolate downstream processing from mutation.</li>
              <li>• Header names/values are validated to prevent malformed request lines and header injection issues.</li>
              <li>• JSON/form serialization occurs at build time, not transport time, so faults are deterministic.</li>
              <li>• Multipart inputs are recorded in extensions for later encoding by higher-level client logic.</li>
            </ul>
          </div>
          <div className={boxClass}>
            <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Subsystem Interactions</h3>
            <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              <li>• faults: raises InvalidHeaderFault, InvalidURLFault, RequestBuildFault for deterministic build failures.</li>
              <li>• config: consumes TimeoutConfig for per-request timeout overrides.</li>
              <li>• transport: host/path/query helpers are consumed by low-level serializers and connection pools.</li>
              <li>• sessions/cookies/auth: cookie and auth helpers produce standard headers consumed by middleware/auth interceptors.</li>
            </ul>
          </div>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>3. API Reference (Exhaustive)</h2>

        <CodeBlock language="python" filename="request.py core types">{`class HTTPMethod(str, Enum):
    GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS, TRACE, CONNECT

HeadersType = Mapping[str, str] | list[tuple[str, str]] | None
ParamsType = Mapping[str, str | int | float | bool | None] | list[tuple[str, str]] | None
CookiesType = Mapping[str, str] | None
DataType = Mapping[str, Any] | str | bytes | None
JsonType = Any
ContentType = str | bytes | AsyncIterator[bytes] | BinaryIO | None

SINGLE_VALUE_HEADERS: frozenset[str]`}</CodeBlock>

        <CodeBlock language="python" filename="request.py validation helpers">{`def _normalize_header_name(name: str) -> str
# Title-Case normalization

def _validate_header_name(name: str) -> None
# Raises InvalidHeaderFault on empty, control chars, delimiters, or invalid whitespace

def _validate_header_value(value: str, name: str = "") -> None
# Raises InvalidHeaderFault on forbidden control chars`}</CodeBlock>

        <CodeBlock language="python" filename="HTTPClientRequest signature">{`@dataclass
class HTTPClientRequest:
    method: HTTPMethod
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    body: bytes | AsyncIterator[bytes] | None = None
    timeout: TimeoutConfig | None = None
    follow_redirects: bool | None = None
    auth: tuple[str, str] | None = None
    extensions: dict[str, Any] = field(default_factory=dict)

    @property def host(self) -> str
    @property def path(self) -> str
    @property def scheme(self) -> str
    @property def query_string(self) -> str
    @property def content_type(self) -> str | None
    @property def content_length(self) -> int | None

    def has_body(self) -> bool
    def is_streaming(self) -> bool
    def copy(self, **changes: Any) -> HTTPClientRequest
    def to_dict(self) -> dict[str, Any]`}</CodeBlock>

        <CodeBlock language="python" filename="RequestBuilder signature">{`class RequestBuilder:
    def __init__(self, method: str | HTTPMethod, url: str, *, base_url: str | None = None)

    # Header and query APIs
    def header(self, name: str, value: str) -> RequestBuilder
    def headers(self, headers: HeadersType) -> RequestBuilder
    def param(self, name: str, value: str | int | float | bool | None) -> RequestBuilder
    def params(self, params: ParamsType) -> RequestBuilder

    # Body APIs
    def body(self, content: bytes | AsyncIterator[bytes]) -> RequestBuilder
    def json(self, data: JsonType) -> RequestBuilder
    def form(self, data: Mapping[str, Any] | str) -> RequestBuilder
    def multipart(
        self,
        fields: dict[str, str | tuple[str, bytes | BinaryIO, str | None]] | None = None,
        files: list[tuple[str, tuple[str, bytes | BinaryIO, str | None]]] | None = None,
    ) -> RequestBuilder

    # Cookie/Auth APIs
    def cookie(self, name: str, value: str) -> RequestBuilder
    def cookies(self, cookies: CookiesType) -> RequestBuilder
    def auth_basic(self, username: str, password: str) -> RequestBuilder
    def auth_bearer(self, token: str) -> RequestBuilder

    # Runtime controls
    def timeout(self, total: float | None = None, connect: float | None = None,
                read: float | None = None, write: float | None = None,
                pool: float | None = None) -> RequestBuilder
    def follow_redirects(self, follow: bool = True) -> RequestBuilder
    def extension(self, key: str, value: Any) -> RequestBuilder

    # Internal build pipeline
    def _build_url(self) -> str
    def _build_body(self) -> tuple[bytes | AsyncIterator[bytes] | None, dict[str, str]]
    def _build_cookies(self) -> str | None
    def _build_auth_header(self) -> str | None

    # Materialization
    def build(self) -> HTTPClientRequest`}</CodeBlock>

        <CodeBlock language="python" filename="Convenience builders">{`def get(url: str, **kwargs: Any) -> RequestBuilder
def post(url: str, **kwargs: Any) -> RequestBuilder
def put(url: str, **kwargs: Any) -> RequestBuilder
def patch(url: str, **kwargs: Any) -> RequestBuilder
def delete(url: str, **kwargs: Any) -> RequestBuilder
def head(url: str, **kwargs: Any) -> RequestBuilder
def options(url: str, **kwargs: Any) -> RequestBuilder`}</CodeBlock>

        <div className={boxClass}>
          <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Fault Mapping</h3>
          <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li>• InvalidHeaderFault: malformed header name/value in header() / headers() / internal validation.</li>
            <li>• InvalidURLFault: missing scheme or host after base URL merge.</li>
            <li>• RequestBuildFault: JSON serialization errors and other build-time field violations.</li>
          </ul>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>4. Behavior and Lifecycle</h2>
        <CodeBlock language="python" filename="Builder execution flow">{`# 1. Initialize builder with method+url
builder = RequestBuilder("POST", "/users", base_url="https://api.example.com")

# 2. Apply mutators in any order (headers, params, body, auth)
builder.header("X-Request-ID", "req_123").json({"name": "Ada"}).timeout(total=3)

# 3. build() normalizes and validates
#    - _build_url(): base URL join + scheme/host validation + query assembly
#    - _build_body(): raw/json/form/multipart decision tree
#    - cookie and auth headers merged

# 4. Immutable HTTPClientRequest emitted
request = builder.build()`}</CodeBlock>
        <div className={boxClass}>
          <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Concurrency model: RequestBuilder is mutable and not thread-safe for shared mutation; HTTPClientRequest is
            immutable by convention (copy() returns new instances) and safe to pass across async boundaries.
          </p>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>5. Usage Examples</h2>
        <CodeBlock language="python" filename="Minimal">{`from aquilia.http.request import get

request = get("https://httpbin.org/get").build()`}</CodeBlock>

        <CodeBlock language="python" filename="Real-world signed request">{`from aquilia.http.request import RequestBuilder

request = (
    RequestBuilder("POST", "/events", base_url="https://collector.internal")
    .header("X-Tenant", "acme")
    .header("X-Trace-ID", "trace_789")
    .json({"type": "page.view", "duration_ms": 182})
    .timeout(total=2.5, connect=0.5, read=2.0)
    .build()
)`}</CodeBlock>

        <CodeBlock language="python" filename="Edge case: repeated params + explicit auth">{`request = (
    RequestBuilder("GET", "https://api.example.com/search")
    .param("tag", "python")
    .param("tag", "asyncio")
    .auth_basic("svc", "secret")
    .build()
)
# URL => ...?tag=python&tag=asyncio`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>6. Advanced Topics</h2>
        <div className="space-y-4">
          <div className={boxClass}>
            <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Performance and Memory</h3>
            <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              <li>• Prefer body(AsyncIterator[bytes]) for large payloads to avoid buffering full content in memory.</li>
              <li>• Use bytes for already serialized payloads to skip JSON/form encoder overhead.</li>
              <li>• Avoid repeatedly rebuilding equivalent immutable requests in hot loops; precompute and copy only deltas.</li>
            </ul>
          </div>
          <div className={boxClass}>
            <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Extensibility Hooks</h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              extension(key, value) stores opaque metadata in request.extensions, enabling custom interceptors/middleware
              to pass correlation IDs, cache keys, trace metadata, or policy hints without mutating core request fields.
            </p>
          </div>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>7. Integration</h2>
        <div className={boxClass}>
          <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li>• sessions: outbound HTTP requests are independent from server sessions; propagate selected session data via headers explicitly.</li>
            <li>• config/pyconfig: TimeoutConfig injected at request level can override client defaults for endpoint-specific SLAs.</li>
            <li>• storage: combine RequestBuilder.body(async_stream) with storage readers to stream binary blobs upstream.</li>
            <li>• tasks: prebuild immutable requests in scheduled/background jobs for deterministic retries.</li>
            <li>• effects/flow: use RequestBuilder in effect nodes to standardize outbound call policy and tracing metadata.</li>
          </ul>
        </div>
        <div className={`mt-4 text-sm ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
          Related: <Link className="text-aquilia-500 hover:text-aquilia-400" to="/docs/sessions">Sessions</Link>,{' '}
          <Link className="text-aquilia-500 hover:text-aquilia-400" to="/docs/config">Configuration</Link>,{' '}
          <Link className="text-aquilia-500 hover:text-aquilia-400" to="/docs/cli/subsystems">Task Tooling</Link>.
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>8. Best Practices</h2>
        <div className={boxClass}>
          <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li>• Always call build() as the single validation boundary before execution.</li>
            <li>• Keep auth material in interceptors for rotation; reserve auth_basic/auth_bearer for static credentials.</li>
            <li>• Set per-request timeout overrides for known slow endpoints instead of globally widening all requests.</li>
            <li>• Prefer params()/headers() batching when values are already available as mappings.</li>
          </ul>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>9. Edge Cases and Failure Modes</h2>
        <CodeBlock language="python" filename="Representative failures">{`# InvalidURLFault
RequestBuilder("GET", "/relative-without-base").build()

# InvalidHeaderFault
RequestBuilder("GET", "https://api.example.com").header("Bad Header", "x")

# RequestBuildFault (non-JSON-serializable payload)
RequestBuilder("POST", "https://api.example.com").json({"bad": object()}).build()`}</CodeBlock>
        <p className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
          Faults are raised at build time, before network I/O, which simplifies retry policy and error attribution.
        </p>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>10. Internal Notes</h2>
        <div className={boxClass}>
          <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li>• multipart() marks extensions["_multipart_files"] and sets Content-Type to multipart/form-data without boundary.</li>
            <li>• Boundary-aware multipart encoding is currently performed by higher-level multipart handlers in client/session flows.</li>
            <li>• _validate_header_value allows extended byte values greater than 126 (modern UTF-8 tolerant behavior).</li>
            <li>• copy() is the canonical mechanism used by middleware/interceptors to mutate requests without side effects.</li>
          </ul>
        </div>
      </section>

      <NextSteps
        items={[
          { text: 'response.py Reference', link: '/docs/http/api/response' },
          { text: 'auth.py Reference', link: '/docs/http/api/auth' },
          { text: 'HTTP Transport Layer', link: '/docs/http/transport' },
        ]}
      />
    </div>
  )
}
