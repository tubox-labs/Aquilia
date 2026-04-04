import { useTheme } from '../../../../context/ThemeContext'
import { CodeBlock } from '../../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { Globe } from 'lucide-react'
import { NextSteps } from '../../../../components/NextSteps'

export function HTTPAPIResponse() {
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
            response.py
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Immutable response envelope with lazy body consumption, streaming iterators, text/JSON decoding helpers,
          status classification, and fault-aware status escalation.
        </p>
      </div>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>1. Overview</h2>
        <div className={boxClass}>
          <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'} mb-3`}>
            response.py is the terminal read model for outbound HTTP execution. It provides a single object that supports
            both buffered and streaming usage patterns and propagates structured faults for decoding/status errors.
          </p>
          <p className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
            Lifecycle fit: transport parses status + headers and returns stream/body -&gt; create_response() builds
            HTTPClientResponse -&gt; middleware/interceptors/consumer code reads and transforms content.
          </p>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>2. Architecture and Design</h2>
        <div className="space-y-4">
          <div className={boxClass}>
            <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Representation Model</h3>
            <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              <li>• Headers are stored as dict[str, str] with case-insensitive lookup helpers.</li>
              <li>• Body can be pre-buffered (_body) or lazy-streamed (_stream) with one-time consumption semantics.</li>
              <li>• history captures redirect chain when redirect handling is enabled.</li>
              <li>• extensions is a metadata bag for transport/interceptor-specific fields.</li>
            </ul>
          </div>
          <div className={boxClass}>
            <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Subsystem Coupling</h3>
            <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              <li>• faults: DecodingFault, ClientErrorFault, ServerErrorFault.</li>
              <li>• streaming: iter_bytes/iter_text/iter_lines expose async iteration boundaries.</li>
              <li>• retry/interceptors: status predicates and headers feed retry and redirect policies.</li>
              <li>• cookies: cookies property parses Set-Cookie values into simple key/value map.</li>
            </ul>
          </div>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>3. API Reference (Exhaustive)</h2>
        <CodeBlock language="python" filename="Core constants and JSON loader">{`HTTP_STATUS_REASONS: dict[int, str]

# JSON parser selection order:
# 1) orjson
# 2) ujson
# 3) stdlib json

def _json_loads(data: bytes | str) -> Any`}</CodeBlock>

        <CodeBlock language="python" filename="HTTPClientResponse signature">{`@dataclass
class HTTPClientResponse:
    status_code: int
    headers: dict[str, str]
    url: str
    http_version: str = "1.1"
    elapsed: float = 0.0
    request_url: str = ""
    history: list[HTTPClientResponse] = field(default_factory=list)
    extensions: dict[str, Any] = field(default_factory=dict)

    _body: bytes | None = None
    _stream: AsyncIterator[bytes] | None = None
    _body_consumed: bool = False

    @property def reason(self) -> str
    @property def is_informational(self) -> bool
    @property def is_success(self) -> bool
    @property def is_redirect(self) -> bool
    @property def is_client_error(self) -> bool
    @property def is_server_error(self) -> bool
    @property def is_error(self) -> bool
    @property def ok(self) -> bool
    @property def content_type(self) -> str
    @property def content_length(self) -> int | None
    @property def encoding(self) -> str
    @property def etag(self) -> str | None
    @property def last_modified(self) -> datetime | None
    @property def location(self) -> str | None
    @property def cookies(self) -> dict[str, str]

    def get_header(self, name: str, default: str | None = None) -> str | None
    def get_headers(self, name: str) -> list[str]

    async def read(self) -> bytes
    async def text(self, encoding: str | None = None) -> str
    async def json(self) -> Any
    async def iter_bytes(self, chunk_size: int = 65536) -> AsyncIterator[bytes]
    async def iter_text(self, chunk_size: int = 65536, encoding: str | None = None) -> AsyncIterator[str]
    async def iter_lines(self, encoding: str | None = None, delimiter: str = "\n") -> AsyncIterator[str]

    def raise_for_status(self) -> None
    async def close(self) -> None
    async def __aenter__(self) -> HTTPClientResponse
    async def __aexit__(self, *exc: Any) -> None
    def to_dict(self) -> dict[str, Any]
    def __repr__(self) -> str`}</CodeBlock>

        <CodeBlock language="python" filename="Factory function">{`def create_response(
    status_code: int,
    headers: dict[str, str] | list[tuple[str, str]] | None = None,
    *,
    body: bytes | None = None,
    stream: AsyncIterator[bytes] | None = None,
    url: str = "",
    http_version: str = "1.1",
    elapsed: float = 0.0,
    request_url: str = "",
    history: list[HTTPClientResponse] | None = None,
    extensions: dict[str, Any] | None = None,
) -> HTTPClientResponse`}</CodeBlock>

        <div className={boxClass}>
          <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Fault Mapping</h3>
          <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li>• DecodingFault: invalid charset decode or invalid JSON parsing, including empty-body JSON decode.</li>
            <li>• ClientErrorFault: raise_for_status() on 4xx status.</li>
            <li>• ServerErrorFault: raise_for_status() on 5xx status.</li>
          </ul>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>4. Behavior and Lifecycle</h2>
        <CodeBlock language="python" filename="Buffered vs streaming lifecycle">{`# Buffered response path
response = create_response(status_code=200, headers={}, body=b'{"ok":true}')
await response.json()  # uses cached _body

# Streaming response path
response = create_response(status_code=200, headers={}, stream=stream_iter)
chunk = await response.read()  # consumes stream once, caches bytes

# Iteration path
async for line in response.iter_lines():
    ...  # stops when stream ends, marks _body_consumed`}</CodeBlock>
        <div className={boxClass}>
          <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            State transitions: UNCONSUMED(stream present) -&gt; CONSUMED(_body cached or stream drained) -&gt; CLOSED.
            close() drains remaining stream to release pooled transport resources.
          </p>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>5. Usage Examples</h2>
        <CodeBlock language="python" filename="Minimal">{`response = await client.get("https://api.example.com/health")
if response.ok:
    print(await response.text())`}</CodeBlock>

        <CodeBlock language="python" filename="Structured status handling">{`response = await client.get("https://api.example.com/jobs/42")
if response.is_success:
    data = await response.json()
elif response.is_client_error:
    # deterministic domain fault conversion
    response.raise_for_status()`}</CodeBlock>

        <CodeBlock language="python" filename="Streaming large response">{`async with await client.get("https://cdn.example.com/dump") as response:
    async for chunk in response.iter_bytes(1024 * 1024):
        process(chunk)
# __aexit__ drains and closes response`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>6. Advanced Topics</h2>
        <div className="space-y-4">
          <div className={boxClass}>
            <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Memory and Resource Handling</h3>
            <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              <li>• read() joins all chunks in memory; avoid for unbounded payloads.</li>
              <li>• iter_bytes() preserves streaming behavior and supports backpressure through async iteration.</li>
              <li>• close() is important when consumers partially read streamed payloads.</li>
            </ul>
          </div>
          <div className={boxClass}>
            <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Internal Optimizations</h3>
            <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              <li>• JSON loader auto-selects fastest installed backend.</li>
              <li>• encoding property caches no state but resolves with deterministic Content-Type fallback logic.</li>
              <li>• create_response merges duplicate list-based headers into comma-joined dict entries.</li>
            </ul>
          </div>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>7. Integration</h2>
        <div className={boxClass}>
          <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li>• sessions: HTTP response cookies can be bridged into server session workflows explicitly at application boundaries.</li>
            <li>• config/pyconfig: raise_for_status policies originate from HTTPClientConfig and can be overridden per call path.</li>
            <li>• storage: iter_bytes supports direct sink-to-storage uploads without materializing complete payloads.</li>
            <li>• tasks: response objects should be reduced to serializable dict/data before queueing background work.</li>
            <li>• effects/flow: map is_success/is_error into flow branching or effect retries.</li>
          </ul>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>8. Best Practices</h2>
        <div className={boxClass}>
          <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li>• Call raise_for_status() at module boundaries where fault-first behavior is desired.</li>
            <li>• Use iter_bytes for binary payloads and iter_lines for NDJSON/event streams.</li>
            <li>• Avoid mixing partial streaming consumption with read(); choose one pattern.</li>
            <li>• Convert to_dict() for logging rather than logging full bodies by default.</li>
          </ul>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>9. Edge Cases and Failure Modes</h2>
        <CodeBlock language="python" filename="Representative failure cases">{`# Empty body JSON decode -> DecodingFault
response = create_response(status_code=200, headers={"Content-Type": "application/json"}, body=b"")
await response.json()

# Bad charset decode -> DecodingFault
response = create_response(status_code=200, headers={"Content-Type": "text/plain; charset=bad-enc"}, body=b"abc")
await response.text()

# 4xx/5xx fault conversion
response = create_response(status_code=503, headers={}, body=b"oops")
response.raise_for_status()  # ServerErrorFault`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>10. Internal Notes</h2>
        <div className={boxClass}>
          <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li>• get_headers() returns all matching values by scanning dict keys case-insensitively.</li>
            <li>• cookies property parses each set-cookie header entry independently via SimpleCookie.</li>
            <li>• close() drains the stream iterator; this preserves transport pool health for keep-alive scenarios.</li>
            <li>• __repr__ is intentionally compact for log density: &lt;HTTPClientResponse [status reason]&gt;.</li>
          </ul>
        </div>
      </section>

      <div className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
        Related references: <Link className="text-aquilia-500 hover:text-aquilia-400" to="/docs/http/api/request">request.py</Link>,{' '}
        <Link className="text-aquilia-500 hover:text-aquilia-400" to="/docs/http/api/streaming">streaming.py</Link>,{' '}
        <Link className="text-aquilia-500 hover:text-aquilia-400" to="/docs/http/faults">HTTP Faults</Link>.
      </div>

      <NextSteps
        items={[
          { text: 'auth.py Reference', link: '/docs/http/api/auth' },
          { text: 'cookies.py Reference', link: '/docs/http/api/cookies' },
          { text: 'HTTP Fault System', link: '/docs/http/faults' },
        ]}
      />
    </div>
  )
}
