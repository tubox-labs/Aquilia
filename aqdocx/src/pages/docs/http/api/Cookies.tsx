import { useTheme } from '../../../../context/ThemeContext'
import { CodeBlock } from '../../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { Globe } from 'lucide-react'
import { NextSteps } from '../../../../components/NextSteps'

export function HTTPAPICookies() {
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
            cookies.py
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Cookie model, matching engine, in-memory jar, and interceptor glue for transparent outbound cookie handling.
        </p>
      </div>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>1. Overview</h2>
        <div className={boxClass}>
          <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'} mb-3`}>
            cookies.py implements client-side cookie behavior for HTTPSession and cookie middleware/interceptors. It
            handles Set-Cookie parsing, domain/path matching, secure transport filtering, and jar mutation APIs.
          </p>
          <p className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
            Lifecycle fit: response headers -&gt; Cookie.from_set_cookie -&gt; CookieJar.set/set_from_response -&gt; request
            assembly via get_header() for matching URL.
          </p>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>2. Architecture and Design</h2>
        <div className="space-y-4">
          <div className={boxClass}>
            <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Core Components</h3>
            <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              <li>• Cookie: value object + domain/path/security matching and Set-Cookie serialization/parsing.</li>
              <li>• CookieJar: keyed store domain:path:name with filtering, cleanup, and export helpers.</li>
              <li>• CookieInterceptor: request/response bridge that injects and persists cookies around next_handler calls.</li>
            </ul>
          </div>
          <div className={boxClass}>
            <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Design Notes</h3>
            <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              <li>• Domain and path checks are explicit and deterministic; matching cookies are path-sorted by specificity.</li>
              <li>• Expired cookie filtering is configurable via ignore_expired flag.</li>
              <li>• max_age handling currently treats positive max_age as non-expired without creation timestamp arithmetic.</li>
            </ul>
          </div>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>3. API Reference (Exhaustive)</h2>
        <CodeBlock language="python" filename="Cookie signature">{`@dataclass
class Cookie:
    name: str
    value: str
    domain: str = ""
    path: str = "/"
    expires: float | None = None
    max_age: int | None = None
    secure: bool = False
    http_only: bool = False
    same_site: str = ""

    @property def is_expired(self) -> bool
    @property def is_session(self) -> bool
    def matches_domain(self, request_domain: str) -> bool
    def matches_path(self, request_path: str) -> bool
    def matches(self, url: str) -> bool
    def to_header_value(self) -> str
    def to_set_cookie(self) -> str

    @classmethod
    def from_set_cookie(cls, header: str, request_url: str = "") -> Cookie`}</CodeBlock>

        <CodeBlock language="python" filename="CookieJar signature">{`class CookieJar:
    def __init__(self, ignore_expired: bool = True)
    def _cookie_key(self, cookie: Cookie) -> str
    def set(self, cookie: Cookie) -> None
    def set_from_response(
        self,
        headers: dict[str, str] | list[tuple[str, str]],
        request_url: str,
    ) -> list[Cookie]
    def get(self, name: str, domain: str = "", path: str = "/") -> Cookie | None
    def get_for_url(self, url: str) -> list[Cookie]
    def get_header(self, url: str) -> str | None
    def delete(self, name: str, domain: str = "", path: str = "/") -> bool
    def clear(self, domain: str = "") -> int
    def cleanup_expired(self) -> int
    def all(self) -> list[Cookie]
    def to_dict(self) -> dict[str, str]
    def __len__(self) -> int
    def __contains__(self, name: str) -> bool
    def __iter__(self)`}</CodeBlock>

        <CodeBlock language="python" filename="CookieInterceptor signature">{`class CookieInterceptor:
    def __init__(self, jar: CookieJar | None = None)
    @property def jar(self) -> CookieJar
    async def intercept(self, request: Any, next_handler: Any) -> Any`}</CodeBlock>

        <div className={boxClass}>
          <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Error and Fault Surface</h3>
          <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li>• Cookie.from_set_cookie may raise ValueError for malformed cookie headers.</li>
            <li>• CookieJar.set_from_response catches ValueError and logs warning instead of raising.</li>
            <li>• No Aquilia faults are emitted directly in this module; upstream faults remain unchanged.</li>
          </ul>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>4. Behavior and Lifecycle</h2>
        <CodeBlock language="python" filename="Cookie round trip">{`# Response phase
set = jar.set_from_response(response.headers, request_url)

# Request phase
cookie_header = jar.get_header("https://api.example.com/path")
if cookie_header:
    request = request.copy(headers={**request.headers, "Cookie": cookie_header})`}</CodeBlock>
        <div className={boxClass}>
          <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            State model: INSERT/UPDATE via set(), EVICT via delete/clear/cleanup_expired, READ via get/get_for_url.
            Matching order is path-length descending to prioritize more specific cookies.
          </p>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>5. Usage Examples</h2>
        <CodeBlock language="python" filename="Minimal">{`jar = CookieJar()
jar.set(Cookie(name="sid", value="abc", domain="example.com"))
print(jar.get_header("https://example.com/dashboard"))`}</CodeBlock>

        <CodeBlock language="python" filename="Session integration with interceptor">{`cookie_interceptor = CookieInterceptor()
client = AsyncHTTPClient(interceptors=[cookie_interceptor])

await client.get("https://auth.example.com/login")
# Set-Cookie from login response stored automatically
await client.get("https://auth.example.com/me")  # Cookie auto-attached`}</CodeBlock>

        <CodeBlock language="python" filename="Edge case: secure cookie over HTTP">{`jar = CookieJar()
jar.set(Cookie(name="secure_sid", value="x", domain="example.com", secure=True))
assert jar.get_header("http://example.com") is None`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>6. Advanced Topics</h2>
        <div className="space-y-4">
          <div className={boxClass}>
            <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Performance</h3>
            <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              <li>• get_for_url is linear over stored cookies; call cleanup_expired periodically in long-lived clients.</li>
              <li>• to_dict intentionally flattens by name only; use all() when domain/path fidelity is required.</li>
            </ul>
          </div>
          <div className={boxClass}>
            <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Extensibility</h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Custom persistence can wrap CookieJar APIs to snapshot and restore cookie states between process restarts.
              CookieInterceptor accepts injected jars, enabling tenant-specific jar partitioning.
            </p>
          </div>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>7. Integration</h2>
        <div className={boxClass}>
          <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li>• sessions: cookie-based server sessions and outbound client cookies are separate stores; bridge explicitly when needed.</li>
            <li>• config/pyconfig: domain, secure defaults, and tenancy policies can be centralized in app config before jar construction.</li>
            <li>• storage: persist jar snapshots to storage providers for durable scraping/integration workflows.</li>
            <li>• tasks: serialize cookie snapshots into tasks when long-running workflows span worker boundaries.</li>
            <li>• effects/flow: inject cookie-aware clients as effect dependencies to preserve sticky upstream affinity.</li>
          </ul>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>8. Best Practices</h2>
        <div className={boxClass}>
          <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li>• Isolate jars per trust domain or tenant to avoid cookie bleeding across upstream services.</li>
            <li>• Keep ignore_expired=True for request-time filtering and run cleanup_expired on schedule.</li>
            <li>• Use explicit domain and path when deleting cookies to avoid ambiguous removals.</li>
            <li>• Avoid logging full Set-Cookie values in production diagnostics.</li>
          </ul>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>9. Edge Cases and Failure Modes</h2>
        <CodeBlock language="python" filename="Malformed Set-Cookie handling">{`headers = [("Set-Cookie", "bad-cookie-format")]
cookies = jar.set_from_response(headers, "https://example.com")
# returns [] and logs warning`}</CodeBlock>

        <CodeBlock language="python" filename="Max-Age expiry semantics">{`cookie = Cookie(name="x", value="1", max_age=300)
cookie.is_expired  # False (creation-time countdown is not modeled in current implementation)`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>10. Internal Notes</h2>
        <div className={boxClass}>
          <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li>• from_set_cookie infers domain from request_url when Domain attribute is omitted.</li>
            <li>• clear(domain=...) uses matches_domain semantics, not exact key equality.</li>
            <li>• CookieInterceptor appends to existing Cookie header instead of overwriting.</li>
            <li>• Path comparison trims trailing slash for cookie path normalization.</li>
          </ul>
        </div>
      </section>

      <div className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
        Related references: <Link className="text-aquilia-500 hover:text-aquilia-400" to="/docs/http/api/request">request.py</Link>,{' '}
        <Link className="text-aquilia-500 hover:text-aquilia-400" to="/docs/http/sessions">HTTP Sessions</Link>,{' '}
        <Link className="text-aquilia-500 hover:text-aquilia-400" to="/docs/sessions/transport">Server Session Transport</Link>.
      </div>

      <NextSteps
        items={[
          { text: 'middleware.py Reference', link: '/docs/http/api/middleware' },
          { text: 'multipart.py Reference', link: '/docs/http/api/multipart' },
          { text: 'HTTP Session Docs', link: '/docs/http/sessions' },
        ]}
      />
    </div>
  )
}
