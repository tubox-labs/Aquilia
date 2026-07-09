import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Globe } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function HTTPSessions() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const textMuted = isDark ? 'text-gray-400' : 'text-gray-600'
  const borderSubtle = isDark ? 'border-white/5' : 'border-gray-100'

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Globe className="w-4 h-4" />
          HTTP Client / Sessions
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            HTTP Sessions
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${textMuted}`}>
          Sessions provide persistent configuration, cookie storage, and connection reuse across multiple HTTP requests.
        </p>
      </div>

      {/* What is a Session */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>What is a Session?</h2>
        <p className={`mb-6 ${textMuted}`}>
          An <DocTerm id="http.HTTPSession">HTTPSession</DocTerm> provides stateful, persistent context across multiple requests with automatic resource management:
        </p>
        <div className="space-y-4 mb-8">
          {[
            ['Cookie Persistence', 'Automatic CookieJar matching domain and path scopes per RFC 6265.'],
            ['Connection Pooling', 'TCP connection reuse per host with expiry times and automated background pruning.'],
            ['Shared Configuration', 'Base URL, authentication headers, default timeouts, and proxies are shared across all requests.'],
            ['Request Pipeline', 'Interceptors and middleware are executed sequentially for every outgoing call.'],
          ].map(([title, desc], i) => (
            <div key={i} className="border-l-2 border-aquilia-500/20 pl-4 py-1">
              <strong className={`font-mono text-sm ${isDark ? 'text-white' : 'text-gray-900'}`}>{title}</strong>
              <p className={`text-sm ${textMuted}`}>{desc}</p>
            </div>
          ))}
        </div>
        <CodeBlock language="python" filename="session_basics.py" highlightLines={[3, 7, 8]}>{`from aquilia.http import HTTPSession

async with HTTPSession() as session:
    # First request sets authentication cookie  
    await session.post("/login", json={"user": "alice", "pass": "secret"})
    
    # Subsequent requests automatically send cookies + reuse connections
    profile = await session.get("/profile")
    settings = await session.get("/settings")
    await session.post("/update", json=data)
`}</CodeBlock>
      </section>

      {/* Creating Sessions */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Creating Sessions</h2>
        <CodeBlock language="python" filename="create_session.py" highlightLines={[7, 16, 20]}>{`from aquilia.http import HTTPSession, HTTPClientConfig, TimeoutConfig, PoolConfig
from aquilia.http import BasicAuth, LoggingInterceptor, CookieMiddleware

# Basic session with auto-generated config
session = HTTPSession()

# Session with comprehensive configuration
config = HTTPClientConfig(
    base_url="https://api.example.com",
    timeout=TimeoutConfig(total=30.0, connect=10.0),
    pool=PoolConfig(max_connections=50, max_connections_per_host=10),
    default_headers={
        "User-Agent": "MyApp/1.0",
        "Accept": "application/json",
    },
    follow_redirects=True,
    max_redirects=10,
    raise_for_status=True,
)

session = HTTPSession(
    config=config,
    cookies=None,
    interceptors=[
        BasicAuth("user", "password"),
    ],
)
`}</CodeBlock>
      </section>

      {/* Base URL */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Base URL</h2>
        <CodeBlock language="python" filename="base_url.py" highlightLines={[5, 8]}>{`session = HTTPSession(HTTPClientConfig(
    base_url="https://api.github.com"
))

# Relative paths are appended to base_url
users = await session.get("/users")  # https://api.github.com/users
repos = await session.get("/repos")  # https://api.github.com/repos

# Absolute URLs override base_url
external = await session.get("https://httpbin.org/get")
`}</CodeBlock>
      </section>

      {/* Cookie Management */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Cookie Management</h2>
        <p className={`mb-4 ${textMuted}`}>
          Sessions manage cookies compliant with RFC 6265, handling SameSite, Secure, and HttpOnly attributes:
        </p>
        
        <h3 className={`text-lg font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Automatic Cookie Handling</h3>
        <CodeBlock language="python" filename="cookie_basics.py" highlightLines={[10, 13]}>{`session = HTTPSession()

# Server sends Set-Cookie header  
response = await session.post("/login", json={
    "username": "alice",
    "password": "secret"
})

# Session automatically stores cookie in CookieJar
profile = await session.get("/profile")  # Sends Cookie header

# Cookies are domain/path scoped
await session.get("https://other-domain.com/api")  # No cookie sent
`}</CodeBlock>
      </section>

      {/* Connection Reuse */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Connection Management</h2>
        <p className={`mb-4 ${textMuted}`}>
          Connections are reused to reduce handshake overhead and TLS setup latency:
        </p>
        <CodeBlock language="python" filename="connection_management.py" highlightLines={[3, 11]}>{`from aquilia.http import HTTPSession, PoolConfig, HTTPClientConfig

session = HTTPSession(HTTPClientConfig(
    pool=PoolConfig(
        max_connections=100,
        max_connections_per_host=10,
        keepalive_expiry=60.0,
    )
))

await session.get("https://api.example.com/users")  # Establishes TCP connection
await session.get("https://api.example.com/posts")  # Reuses TCP connection
`}</CodeBlock>
      </section>

      {/* Session vs Client */}
      <section className="mb-16 border-l-2 border-aquilia-500/20 pl-6 py-1">
        <h2 className={`text-xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Session vs HTTPClient</h2>
        <p className={`text-sm mb-4 ${textMuted}`}>
          While both make async requests, choose them based on lifetime requirements:
        </p>
        <div className="space-y-4">
          <div>
            <h4 className={`text-sm font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Use HTTPSession when:</h4>
            <p className={`text-xs ${textMuted}`}>Making multiple sequential calls to the same host, keeping login cookies, or sharing a connection pool.</p>
          </div>
          <div>
            <h4 className={`text-sm font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Use HTTPClient when:</h4>
            <p className={`text-xs ${textMuted}`}>Performing isolated, one-off operations or accessing diverse external endpoints with unique request configurations.</p>
          </div>
        </div>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${borderSubtle}`}>
        <Link to="/docs/http/client" className={`flex items-center gap-2 text-sm ${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`}>
          <ArrowLeft className="w-4 h-4" /> HTTPClient
        </Link>
        <Link to="/docs/http/transport" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400">
          Transport Layer <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    
      <NextSteps />
    </div>
  )
}
