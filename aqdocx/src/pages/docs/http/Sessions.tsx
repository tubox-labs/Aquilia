import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Globe } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function HTTPSessions() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

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
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Sessions provide persistent configuration, cookie storage, and connection reuse across multiple HTTP requests.
        </p>
      </div>

      {/* What is a Session */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>What is a Session?</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          HTTP sessions provide stateful, persistent context across multiple requests with automatic resource management:
        </p>
        <div className={boxClass}>
          <ul className={`space-y-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li>• <strong className={isDark ? 'text-white' : 'text-gray-900'}>Cookie persistence</strong> — Automatic CookieJar with RFC 6265 compliance. Domain/path matching, expiry tracking, SameSite/Secure/HttpOnly handling</li>
            <li>• <strong className={isDark ? 'text-white' : 'text-gray-900'}>Connection pooling</strong> — Per-host TCP connection reuse. Configurable limits (global, per-host), keepalive expiry, background cleanup</li>
            <li>• <strong className={isDark ? 'text-white' : 'text-gray-900'}>Shared configuration</strong> — Base URL, headers, auth, timeout settings, proxy config, TLS settings persist across requests</li>
            <li>• <strong className={isDark ? 'text-white' : 'text-gray-900'}>Request pipeline</strong> — Interceptors (before/after hooks) and middleware (onion model) apply to all requests</li>
            <li>• <strong className={isDark ? 'text-white' : 'text-gray-900'}>Automatic redirects</strong> — Follows 3xx responses up to max_redirects (default 10) with loop detection</li>
            <li>• <strong className={isDark ? 'text-white' : 'text-gray-900'}>Header management</strong> — Default headers merged with per-request headers. Case-insensitive handling</li>
            <li>• <strong className={isDark ? 'text-white' : 'text-gray-900'}>Error handling</strong> — Optional raise_for_status for automatic fault raising on 4xx/5xx</li>
          </ul>
        </div>
        <CodeBlock language="python" filename="session_basics.py">{`from aquilia.http import HTTPSession

async with HTTPSession() as session:
    # First request sets authentication cookie  
    await session.post("/login", json={"user": "alice", "pass": "secret"})
    
    # Subsequent requests automatically send cookies + reuse connections
    profile = await session.get("/profile")      # Cookie sent, connection reused
    settings = await session.get("/settings")    # Same connection pool
    await session.post("/update", json=data)     # POST request with cookies
    
    # Session manages all resources automatically:
    # - TCP connections pooled and reused per host
    # - Cookies stored in CookieJar and sent on matching requests
    # - Default headers and config applied to all requests`}</CodeBlock>
      </section>

      {/* Creating Sessions */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Creating Sessions</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Sessions can be created with full configuration control and automatic resource management:
        </p>
        <CodeBlock language="python" filename="create_session.py">{`from aquilia.http import HTTPSession, HTTPClientConfig, TimeoutConfig, PoolConfig
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
        "X-API-Version": "v2",
    },
    follow_redirects=True,
    max_redirects=10,
    raise_for_status=True,  # Auto-raise on 4xx/5xx
)

session = HTTPSession(
    config=config,
    cookies=None,  # Use fresh CookieJar (default)
    interceptors=[
        BasicAuth("user", "password"),
        LoggingInterceptor(level="DEBUG"),
    ],
    middleware=[
        CookieMiddleware(),
        ErrorHandlingMiddleware(),
    ],
)

# Context manager (recommended) - auto-closes
async with HTTPSession(config) as session:
    response = await session.get("/users")
    # Connections automatically closed on context exit

# Manual lifecycle
session = HTTPSession()
try:
    response = await session.get("/users")
finally:
    await session.close()  # Required for proper cleanup

# Inherit from existing session config
inherited = session.copy_config()
new_session = HTTPSession(inherited)`}</CodeBlock>
      </section>

      {/* Base URL */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Base URL</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Set a base URL to avoid repeating it in every request:
        </p>
        <CodeBlock language="python" filename="base_url.py">{`session = Session(HTTPClientConfig(
    base_url="https://api.github.com"
))

# Relative paths are appended to base_url
users = await session.get("/users")  # https://api.github.com/users
repos = await session.get("/repos")  # https://api.github.com/repos

# Absolute URLs override base_url
external = await session.get("https://httpbin.org/get")

# Paths are properly joined
session = Session(HTTPClientConfig(base_url="https://api.example.com/v1"))
await session.get("/users")     # https://api.example.com/v1/users
await session.get("users")      # https://api.example.com/v1/users
await session.get("/v2/users")  # https://api.example.com/v2/users`}</CodeBlock>
      </section>

      {/* Shared Headers */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Shared Headers</h2>
        <CodeBlock language="python" filename="shared_headers.py">{`# Headers set on session apply to all requests
session = Session(HTTPClientConfig(
    default_headers={
        "Authorization": "Bearer token123",
        "User-Agent": "MyApp/1.0",
        "Accept": "application/json",
    }
))

# All requests include these headers
await session.get("/users")    # Sends Authorization header
await session.post("/posts")   # Sends Authorization header

# Per-request headers merge with defaults
await session.get(
    "/special",
    headers={"X-Custom": "value"}
)
# Sends: Authorization, User-Agent, Accept, X-Custom

# Per-request headers override defaults
await session.get(
    "/different",
    headers={"User-Agent": "CustomAgent/2.0"}
)
# Overrides User-Agent, keeps Authorization and Accept`}</CodeBlock>
      </section>

      {/* Cookie Management */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Cookie Management</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Sessions use a sophisticated CookieJar with RFC 6265 compliance, domain/path matching, and automatic expiration:
        </p>
        
        <h3 className={`text-lg font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Automatic Cookie Handling</h3>
        <CodeBlock language="python" filename="cookie_basics.py">{`session = HTTPSession()

# Server sends Set-Cookie header  
response = await session.post("/login", json={
    "username": "alice",
    "password": "secret"
})
# Response: Set-Cookie: session_id=abc123; Path=/; HttpOnly; Secure; SameSite=Strict

# Session automatically stores cookie in CookieJar
# Future requests to matching domain/path include cookie
profile = await session.get("/profile")
# Request: Cookie: session_id=abc123

settings = await session.get("/api/settings")  
# Request: Cookie: session_id=abc123 (matches path)

# Cookies are domain/path scoped
await session.get("https://other-domain.com/api")
# No cookie sent (different domain)`}</CodeBlock>

        <h3 className={`text-lg font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Cookie Jar Access and Manipulation</h3>
        <CodeBlock language="python" filename="cookie_jar.py">{`# Access the session's CookieJar
jar = session.cookies

# View all cookies
for cookie in jar:
    print(f"{cookie.name}={cookie.value}")
    print(f"  Domain: {cookie.domain}")
    print(f"  Path: {cookie.path}")
    print(f"  Expires: {cookie.expires}")
    print(f"  Secure: {cookie.secure}")
    print(f"  HttpOnly: {cookie.http_only}")
    print(f"  SameSite: {cookie.same_site}")

# Get cookies for a specific URL
cookies_for_url = jar.get_for_url("https://api.example.com/v1/data")

# Get cookie header string
header_value = jar.get_header("https://api.example.com")
# Returns: "session_id=abc123; user_pref=dark_mode"

# Manually add a cookie
from aquilia.http import Cookie
cookie = Cookie(
    name="custom_token",
    value="xyz789",
    domain=".example.com",  # Dot prefix = subdomains included
    path="/api",
    secure=True,
    http_only=True,
    same_site="Lax"
)
jar.set(cookie)

# Set simple cookie (auto-detected domain/path from request)
jar.set_simple("preference", "dark_mode", "https://app.example.com")

# Delete cookies  
jar.clear_for_domain(".example.com")
jar.clear_expired()  # Remove expired cookies
jar.clear()          # Remove all cookies`}</CodeBlock>

        <h3 className={`text-lg font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Domain and Path Matching</h3>
        <CodeBlock language="python" filename="cookie_matching.py">{`# Domain matching rules (RFC 6265):
# .example.com matches: example.com, sub.example.com, api.example.com  
# example.com matches: example.com only

# Path matching:
# /api matches: /api, /api/v1, /api/users/123
# /api/ matches: /api/, /api/v1, but NOT /api

# Example: Cookie set from https://api.example.com/v1/login
response = await session.post("https://api.example.com/v1/login", ...)
# Server: Set-Cookie: token=abc; Domain=.example.com; Path=/

# Cookie is sent to these URLs:
await session.get("https://api.example.com/v1/users")     # ✓ matches
await session.get("https://api.example.com/v2/data")      # ✓ matches  
await session.get("https://app.example.com/dashboard")    # ✓ matches (.example.com)
await session.get("https://other.com/api")                # ✗ different domain

# Cookie expiration handling
import datetime
from aquilia.http import Cookie

# Set cookie with expiration
expires = datetime.datetime.now() + datetime.timedelta(hours=1)
cookie = Cookie("temp_token", "value", expires=expires)
jar.set(cookie)

# Expired cookies are automatically filtered out
jar.cleanup_expired()  # Manual cleanup
# Or automatic cleanup happens during normal operations`}</CodeBlock>

        <h3 className={`text-lg font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Cookie Persistence</h3>
        <CodeBlock language="python" filename="cookie_persistence.py">{`# Share cookies between sessions
jar = session1.cookies

# Create new session with shared jar
session2 = HTTPSession(cookies=jar)

# Both sessions share the same cookies
await session1.post("/login", ...)    # Sets authentication cookie
await session2.get("/profile")        # Uses authentication cookie

# Export cookies to dict
cookie_dict = jar.to_dict()
# {"session_id": "abc123", "user_pref": "dark_mode"}

# Restore cookies from dict
new_jar = CookieJar.from_dict(cookie_dict)
session3 = HTTPSession(cookies=new_jar)`}</CodeBlock>
      </section>

      {/* Interceptors and Middleware */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Interceptors and Middleware</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Sessions support both interceptors (before/after hooks) and middleware (onion-model processing) for all requests:
        </p>
        
        <h3 className={`text-lg font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Authentication Interceptors</h3>
        <CodeBlock language="python" filename="session_auth.py">{`from aquilia.http import HTTPSession, BasicAuth, BearerAuth, OAuth2Auth

# Basic authentication for all requests
auth = BasicAuth("username", "password")
session = HTTPSession(interceptors=[auth])

# All requests automatically include authentication
await session.get("/protected/data")      # Includes Basic auth header
await session.post("/api/users", ...)     # Includes Basic auth header

# Bearer token with dynamic refresh  
async def get_token():
    # Fetch fresh token from auth service
    return await fetch_current_token()

auth = BearerAuth(get_token)  # Function called for each request
session = HTTPSession(interceptors=[auth])

# OAuth2 with automatic token refresh
oauth = OAuth2Auth(
    client_id="app-id",
    client_secret="app-secret",
    token_url="https://auth.provider.com/oauth/token",
    scope="read write"
)
session = HTTPSession(interceptors=[oauth])

# Mix multiple interceptors
session = HTTPSession(interceptors=[
    LoggingInterceptor(level="INFO"),
    oauth,
    MetricsInterceptor(),
    TimeoutInterceptor(timeout=30.0),
])`}</CodeBlock>

        <h3 className={`text-lg font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Request/Response Middleware</h3>
        <CodeBlock language="python" filename="session_middleware.py">{`from aquilia.http import HTTPSession, create_middleware_stack
from aquilia.http.middleware import (
    LoggingMiddleware, HeadersMiddleware, TimeoutMiddleware,
    ErrorHandlingMiddleware, RetryMiddleware, CompressionMiddleware
)

# Create comprehensive middleware stack
middleware = create_middleware_stack(
    logging=True,           # Request/response logging
    error_handling=True,    # Convert errors to faults
    retry=True,             # Automatic retry on failures
    compression=True,       # Handle Accept-Encoding
    cache=True,             # Response caching for GET requests
    cookies=True,           # Automatic cookie management
    base_url=True,          # Prepend base URL to relative paths
    headers=True,           # Add default headers
    timeout=True,           # Enforce timeouts
)

session = HTTPSession(middleware=middleware)

# Or manually compose middleware
session = HTTPSession(middleware=[
    ErrorHandlingMiddleware(),  # Outermost - catches all errors
    RetryMiddleware(),          # Retry failed requests
    LoggingMiddleware(),        # Log request/response
    TimeoutMiddleware(),        # Enforce timeouts
    CompressionMiddleware(),    # Handle compression
    # Inner middleware processes first on request, last on response
])

# Middleware processes in onion model:
# Request:  Error -> Retry -> Logging -> Timeout -> Compression -> Transport
# Response: Compression -> Timeout -> Logging -> Retry -> Error -> Application`}</CodeBlock>

        <h3 className={`text-lg font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Custom Interceptors</h3>
        <CodeBlock language="python" filename="custom_interceptor.py">{`from aquilia.http.interceptors import HTTPInterceptor

class APIKeyInterceptor(HTTPInterceptor):
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def intercept(self, request, handler):
        # Add API key to all requests
        headers = dict(request.headers)
        headers["X-API-Key"] = self.api_key
        request = request.copy(headers=headers)
        
        # Call next handler
        response = await handler(request)
        
        # Log API usage
        print(f"API call: {request.method} {request.url} -> {response.status_code}")
        
        return response

# Use custom interceptor
api_interceptor = APIKeyInterceptor("your-api-key-here")
session = HTTPSession(interceptors=[api_interceptor])`}</CodeBlock>
      </section>

      {/* Connection Reuse */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Connection Management</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Sessions use a sophisticated connection pool with automatic lifecycle management, health tracking, and background cleanup:
        </p>
        <div className={boxClass}>
          <h3 className={`font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Connection Pool Benefits:</h3>
          <ul className={`space-y-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li>• <strong>Reduced latency</strong> — No TCP handshake/TLS negotiation overhead on reused connections</li>
            <li>• <strong>Lower CPU usage</strong> — Amortized TLS setup cost across multiple requests</li>
            <li>• <strong>Better throughput</strong> — HTTP/1.1 keep-alive eliminates connection establishment delays</li>
            <li>• <strong>Resource efficiency</strong> — Fewer file descriptors and kernel resources</li>
            <li>• <strong>Automatic cleanup</strong> — Background task expires old connections every 30s</li>
            <li>• <strong>Health tracking</strong> — Dead connections detected and removed automatically</li>
          </ul>
        </div>
        <CodeBlock language="python" filename="connection_management.py">{`from aquilia.http import HTTPSession, PoolConfig, HTTPClientConfig

session = HTTPSession(HTTPClientConfig(
    pool=PoolConfig(
        max_connections=100,             # Global pool limit across all hosts
        max_connections_per_host=10,     # Per-host connection limit
        keepalive_expiry=60.0,           # Connection lifetime (60s default)
    )
))

# First request to a host creates new connection
await session.get("https://api.example.com/users")
# Connection established: api.example.com:443

# Subsequent requests to same host reuse connection
await session.get("https://api.example.com/posts")  # Reuses connection
await session.get("https://api.example.com/data")   # Reuses connection

# Different hosts get separate connections
await session.get("https://cdn.example.com/assets")  # New connection
await session.get("https://api.example.com/users")   # Reuses api connection

# Concurrent requests share connection pool intelligently
import asyncio
tasks = [
    session.get(f"https://api.example.com/user/{i}")
    for i in range(50)
]
responses = await asyncio.gather(*tasks)
# Up to 10 concurrent connections to api.example.com
# Connections multiplexed across all 50 requests

# Pool statistics
stats = session.pool.stats
print(f"Active connections: {stats.active_connections}")
print(f"Idle connections: {stats.idle_connections}")
print(f"Total created: {stats.total_created}")
print(f"Total reused: {stats.total_reused}")
print(f"Pool exhausted count: {stats.pool_exhausted_count}")

# Manual pool management
await session.pool.cleanup()      # Remove expired connections
await session.pool.close()        # Close all connections`}</CodeBlock>

        <h3 className={`text-lg font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Connection Pool Exhaustion</h3>
        <CodeBlock language="python" filename="pool_exhaustion.py">{`from aquilia.http.faults import ConnectionPoolExhaustedFault

# When pool is exhausted, requests wait with timeout
try:
    await session.get("/api/data", timeout=5.0)
except ConnectionPoolExhaustedFault as e:
    print(f"Pool exhausted: {e.metadata['pool_size']} connections")
    print(f"Active: {e.metadata['active_connections']}")
    # Can retry with backoff or increase pool size

# Monitor pool usage
if session.pool.stats.active_connections > 80:
    print("Pool usage high - consider increasing limits")
    
# Adjust pool size at runtime
session.config.pool.max_connections = 200
session.config.pool.max_connections_per_host = 20`}</CodeBlock>
      </section>

      {/* Redirect Handling */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Redirect Handling</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Sessions automatically handle HTTP redirects with loop detection and method conversion:
        </p>
        <CodeBlock language="python" filename="redirects.py">{`session = HTTPSession(HTTPClientConfig(
    follow_redirects=True,    # Default: True
    max_redirects=10,         # Default: 10
))

# Automatic redirect following
response = await session.get("http://example.com/redirect-chain")
# Automatically follows 301, 302, 303, 307, 308 responses
# Final response is returned, redirect history preserved

# Access redirect history
if response.history:
    print("Redirect chain:")
    for i, redirect in enumerate(response.history):
        print(f"  {i+1}. {redirect.status_code} {redirect.url}")
    print(f"Final: {response.status_code} {response.url}")

# Method conversion for certain redirects:
# 303 (See Other): Always converts to GET
# 301/302: POST converts to GET, others preserve method
await session.post("/submit-form", data=form_data)  
# If server returns 303 redirect, follow-up is GET (not POST)

# Disable redirects per request
response = await session.get("/redirect", follow_redirects=False)
if response.is_redirect:
    location = response.headers.get("Location")
    print(f"Redirect to: {location}")
    # Handle manually

# Loop detection prevents infinite redirects
try:
    await session.get("/infinite-redirect-loop")
except TooManyRedirectsFault as e:
    print(f"Redirect loop detected after {e.metadata['max_redirects']} hops")
    print(f"Redirect chain: {e.metadata['redirect_chain']}")

# Custom redirect limits
session.config.max_redirects = 5   # More restrictive
await session.get("/api/data")      # Max 5 redirects`}</CodeBlock>
      </section>

      {/* Session State */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Session State</h2>
        <CodeBlock language="python" filename="session_state.py">{`session = Session()

# Access configuration
print(session.config.base_url)
print(session.config.timeout.total)
print(session.config.default_headers)

# Modify configuration (affects future requests)
session.config.timeout.total = 60.0
session.config.default_headers["X-Version"] = "2.0"

# Access cookies
print(session.cookies)
session.cookies["preference"] = "dark-mode"

# Check if session is closed
print(session.is_closed)  # False
await session.close()
print(session.is_closed)  # True

# Closed sessions reject new requests
try:
    await session.get("/users")
except RuntimeError:
    print("Session is closed")`}</CodeBlock>
      </section>

      {/* Real-World Example */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Real-World Example</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          A complete API client with session management:
        </p>
        <CodeBlock language="python" filename="api_client.py">{`from aquilia.http import Session, HTTPClientConfig, TimeoutConfig
from typing import Any

class GitHubAPIClient:
    def __init__(self, token: str):
        self.session = Session(HTTPClientConfig(
            base_url="https://api.github.com",
            default_headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=TimeoutConfig(total=30.0),
        ))
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        await self.close()
    
    async def close(self):
        await self.session.close()
    
    async def get_user(self, username: str) -> dict[str, Any]:
        response = await self.session.get(f"/users/{username}")
        response.raise_for_status()
        return await response.json()
    
    async def list_repos(self, username: str) -> list[dict[str, Any]]:
        response = await self.session.get(f"/users/{username}/repos")
        response.raise_for_status()
        return await response.json()
    
    async def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
    ) -> dict[str, Any]:
        response = await self.session.post(
            f"/repos/{owner}/{repo}/issues",
            json={"title": title, "body": body},
        )
        response.raise_for_status()
        return await response.json()

# Usage
async def main():
    async with GitHubAPIClient("your-token") as client:
        # All requests share session configuration
        user = await client.get_user("octocat")
        repos = await client.list_repos("octocat")
        
        issue = await client.create_issue(
            "owner",
            "repo",
            "Bug report",
            "Something is broken",
        )
        
        print(f"User: {user['name']}")
        print(f"Repos: {len(repos)}")
        print(f"Issue: #{issue['number']}")`}</CodeBlock>
      </section>

      {/* Session vs Client */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Session vs HTTPClient</h2>
        <div className={boxClass}>
          <div className="space-y-6">
            <div>
              <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Use Session when:</h3>
              <ul className={`space-y-1 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                <li>• Making multiple requests to the same API</li>
                <li>• You need cookie persistence (login sessions)</li>
                <li>• You want connection reuse for performance</li>
                <li>• You have shared configuration (base URL, headers, auth)</li>
              </ul>
            </div>
            <div>
              <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Use HTTPClient when:</h3>
              <ul className={`space-y-1 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                <li>• Making one-off requests</li>
                <li>• Requests to different services with different configs</li>
                <li>• You need interceptors or middleware</li>
                <li>• You need advanced retry strategies</li>
              </ul>
            </div>
            <div className={`p-4 rounded-lg ${isDark ? 'bg-aquilia-500/10' : 'bg-aquilia-50'}`}>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                <strong className="text-aquilia-500">Note:</strong> HTTPClient internally creates a Session. The main difference is that Session is a simpler API focused on connection reuse, while HTTPClient adds interceptors, retries, and middleware.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
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
