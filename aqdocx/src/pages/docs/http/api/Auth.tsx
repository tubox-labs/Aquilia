import { useTheme } from '../../../../context/ThemeContext'
import { CodeBlock } from '../../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { Globe } from 'lucide-react'
import { NextSteps } from '../../../../components/NextSteps'

export function HTTPAPIAuth() {
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
            auth.py
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Outbound authentication interceptors for HTTP requests: Basic, Bearer, API Key, Digest, OAuth2 token refresh,
          and AWS Signature V4 request signing.
        </p>
      </div>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>1. Overview</h2>
        <div className={boxClass}>
          <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'} mb-3`}>
            auth.py implements authentication as HTTPInterceptor-compatible units. Each strategy transforms
            HTTPClientRequest headers and delegates transport execution through next_handler.
          </p>
          <p className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
            Request lifecycle fit: RequestBuilder builds request -&gt; auth interceptor mutates request copy -&gt; downstream
            middleware/transport executes.
          </p>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>2. Architecture and Design</h2>
        <div className="space-y-4">
          <div className={boxClass}>
            <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Interception Model</h3>
            <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              <li>• AuthInterceptor defines a get_auth_header() contract and shared intercept() implementation.</li>
              <li>• Stateless strategies (BasicAuth/APIKey header mode) only set deterministic headers.</li>
              <li>• Stateful strategies (DigestAuth/OAuth2Auth) can execute multiple network passes.</li>
              <li>• AWS SignatureV4 computes canonical request signatures against request URL, headers, and body.</li>
            </ul>
          </div>
          <div className={boxClass}>
            <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Interactions</h3>
            <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              <li>• request.py: consumes HTTPClientRequest and produces request.copy(headers=...).</li>
              <li>• response.py: Digest/OAuth2 flows inspect status and WWW-Authenticate headers.</li>
              <li>• interceptors.py: auth classes compose in InterceptorChain with metrics/logging/redirect logic.</li>
              <li>• faults: auth.py itself does not declare new faults; downstream faults propagate from transport/response layers.</li>
            </ul>
          </div>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>3. API Reference (Exhaustive)</h2>
        <CodeBlock language="python" filename="Base interceptor">{`class AuthInterceptor(HTTPInterceptor, ABC):
    @abstractmethod
    def get_auth_header(self, request: HTTPClientRequest) -> tuple[str, str] | None

    async def intercept(
        self,
        request: HTTPClientRequest,
        next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]],
    ) -> HTTPClientResponse`}</CodeBlock>

        <CodeBlock language="python" filename="Concrete classes">{`class BasicAuth(AuthInterceptor):
    def __init__(self, username: str, password: str)
    def get_auth_header(self, request: HTTPClientRequest) -> tuple[str, str]

class BearerAuth(AuthInterceptor):
    def __init__(self, token: str | None = None, token_getter: Callable[[], str] | None = None)
    # raises ValueError if both token and token_getter are None
    def get_auth_header(self, request: HTTPClientRequest) -> tuple[str, str]

class APIKeyAuth(AuthInterceptor):
    def __init__(self, key: str, header_name: str = "X-API-Key", in_query: bool = False)
    def get_auth_header(self, request: HTTPClientRequest) -> tuple[str, str] | None
    async def intercept(...)

class DigestAuth(AuthInterceptor):
    def __init__(self, username: str, password: str)
    def get_auth_header(self, request: HTTPClientRequest) -> tuple[str, str] | None
    def _compute_digest(...)
    async def intercept(...)

@dataclass
class OAuth2Token:
    access_token: str
    token_type: str = "Bearer"
    expires_in: int | None = None
    refresh_token: str | None = None
    scope: str | None = None
    created_at: float = 0.0

    def __post_init__(self)
    @property def is_expired(self) -> bool

class OAuth2Auth(AuthInterceptor):
    def __init__(
        self,
        token: OAuth2Token,
        refresh_callback: Callable[[OAuth2Token], Awaitable[OAuth2Token]] | None = None,
    )
    @property def token(self) -> OAuth2Token
    def set_token(self, token: OAuth2Token) -> None
    def get_auth_header(self, request: HTTPClientRequest) -> tuple[str, str]
    async def intercept(...)

class AWSSignatureV4Auth(AuthInterceptor):
    def __init__(
        self,
        access_key: str,
        secret_key: str,
        region: str,
        service: str,
        session_token: str | None = None,
    )
    def get_auth_header(self, request: HTTPClientRequest) -> tuple[str, str] | None
    def _sign(self, key: bytes, msg: str) -> bytes
    def _get_signature_key(self, date_stamp: str) -> bytes
    async def intercept(...)`}</CodeBlock>

        <div className={boxClass}>
          <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Error Surface</h3>
          <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li>• BearerAuth.__init__ raises ValueError on invalid constructor state.</li>
            <li>• DigestAuth/OAuth2Auth/AWSSignatureV4Auth propagate network and parsing faults from downstream handlers.</li>
            <li>• OAuth2 token refresh failures are logged and fallback to current token behavior when possible.</li>
          </ul>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>4. Behavior and Lifecycle</h2>
        <CodeBlock language="python" filename="Execution flow">{`# Generic path (Basic/Bearer/API key header)
request -> get_auth_header() -> request.copy(headers=...) -> next_handler(request)

# Digest path
request(no auth) -> 401 + WWW-Authenticate: Digest -> compute digest -> retry with Authorization: Digest ...

# OAuth2 path
if token expired and refresh_callback present: refresh before send
send request
if response.status == 401 and refresh_callback present: refresh + single retry`}</CodeBlock>
        <div className={boxClass}>
          <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Concurrency: strategy instances are generally reusable, but stateful classes (DigestAuth nonce count,
            OAuth2Auth mutable token) should be shared carefully across high-concurrency call sites.
          </p>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>5. Usage Examples</h2>
        <CodeBlock language="python" filename="Minimal basic auth">{`client = AsyncHTTPClient(interceptors=[BasicAuth("service", "secret")])
response = await client.get("https://api.example.com/private")`}</CodeBlock>

        <CodeBlock language="python" filename="Dynamic bearer token">{`def token_getter() -> str:
    return current_token_store.read()

client = AsyncHTTPClient(interceptors=[BearerAuth(token_getter=token_getter)])`}</CodeBlock>

        <CodeBlock language="python" filename="OAuth2 with refresh">{`async def refresh_token(old: OAuth2Token) -> OAuth2Token:
    refreshed = await issue_refresh(old.refresh_token)
    return OAuth2Token(access_token=refreshed.access, refresh_token=refreshed.refresh, expires_in=3600)

auth = OAuth2Auth(
    token=OAuth2Token(access_token="initial", expires_in=60),
    refresh_callback=refresh_token,
)
client = AsyncHTTPClient(interceptors=[auth])`}</CodeBlock>

        <CodeBlock language="python" filename="API key in query string">{`client = AsyncHTTPClient(interceptors=[APIKeyAuth("key_123", header_name="api_key", in_query=True)])
# transforms URL: /items -> /items?api_key=key_123`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>6. Advanced Topics</h2>
        <div className="space-y-4">
          <div className={boxClass}>
            <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Performance and Security</h3>
            <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              <li>• Prefer header-based API key transport unless upstream explicitly requires query transport.</li>
              <li>• For OAuth2, cache refresh responses and avoid synchronized refresh storms under concurrent load.</li>
              <li>• For AWS SigV4, ensure body bytes are stable before signing; post-sign mutation invalidates signature.</li>
            </ul>
          </div>
          <div className={boxClass}>
            <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Extensibility</h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Build custom auth by subclassing AuthInterceptor or HTTPInterceptor. Keep custom state immutable where
              possible and use request.extensions for auth metadata needed by downstream middleware.
            </p>
          </div>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>7. Integration</h2>
        <div className={boxClass}>
          <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li>• sessions: bridge server-side session identity into outbound headers (for service-to-service propagation).</li>
            <li>• config/pyconfig: load auth credential sources via environment-backed config builders before interceptor construction.</li>
            <li>• storage: token/certificate material can be sourced from secure storage providers before startup.</li>
            <li>• tasks: use OAuth2Auth refresh callbacks in background task runners for long-lived jobs.</li>
            <li>• effects/flow: inject auth interceptors inside flow/effect nodes to keep policy centralized.</li>
          </ul>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>8. Best Practices</h2>
        <div className={boxClass}>
          <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li>• Keep interceptors ordered: auth before logging if logs must include signed headers, after logging if not.</li>
            <li>• Never store static secrets directly in code; inject from config/env/secret stores.</li>
            <li>• Recreate DigestAuth instance if nonce-count state should not be shared across trust domains.</li>
            <li>• Guard refresh_callback with timeout/circuit breaker for high-availability paths.</li>
          </ul>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>9. Edge Cases and Failure Modes</h2>
        <CodeBlock language="python" filename="Common failure patterns">{`# BearerAuth constructor misuse
BearerAuth()  # ValueError: Either token or token_getter must be provided

# DigestAuth on non-digest challenge: returns original 401 response

# OAuth2 refresh failure:
# - exception is logged
# - request proceeds with existing token when possible

# API key query mode can duplicate key if same param already present`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>10. Internal Notes</h2>
        <div className={boxClass}>
          <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li>• Digest challenge parsing uses regex extraction and supports qop list handling by selecting first option.</li>
            <li>• OAuth2Token.is_expired uses created_at + expires_in wall-clock comparison.</li>
            <li>• AWSSignatureV4Auth lowercases header names for canonicalization and includes x-amz-content-sha256.</li>
            <li>• Auth interceptors always create new request copies; input requests are not mutated in place.</li>
          </ul>
        </div>
      </section>

      <div className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
        Related references: <Link className="text-aquilia-500 hover:text-aquilia-400" to="/docs/http/api/request">request.py</Link>,{' '}
        <Link className="text-aquilia-500 hover:text-aquilia-400" to="/docs/http/api/middleware">middleware.py</Link>,{' '}
        <Link className="text-aquilia-500 hover:text-aquilia-400" to="/docs/auth/integration">Auth Integration</Link>.
      </div>

      <NextSteps
        items={[
          { text: 'cookies.py Reference', link: '/docs/http/api/cookies' },
          { text: 'middleware.py Reference', link: '/docs/http/api/middleware' },
          { text: 'HTTP Session Internals', link: '/docs/http/sessions' },
        ]}
      />
    </div>
  )
}
