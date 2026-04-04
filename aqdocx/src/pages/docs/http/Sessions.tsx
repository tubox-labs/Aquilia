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
          An HTTP session maintains state across multiple requests:
        </p>
        <div className={boxClass}>
          <ul className={`space-y-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li>• <strong className={isDark ? 'text-white' : 'text-gray-900'}>Cookie persistence</strong> — Automatically stores and sends cookies</li>
            <li>• <strong className={isDark ? 'text-white' : 'text-gray-900'}>Connection pooling</strong> — Reuses TCP connections for efficiency</li>
            <li>• <strong className={isDark ? 'text-white' : 'text-gray-900'}>Shared configuration</strong> — Base URL, headers, auth, timeout settings</li>
            <li>• <strong className={isDark ? 'text-white' : 'text-gray-900'}>Request context</strong> — Interceptors and middleware apply to all requests</li>
          </ul>
        </div>
        <CodeBlock language="python" filename="session_basics.py">{`from aquilia.http import Session

async with Session() as session:
    # First request sets a cookie
    await session.post("/login", json={"user": "alice", "pass": "secret"})
    
    # Subsequent requests automatically send the cookie
    profile = await session.get("/profile")  # Authenticated
    settings = await session.get("/settings")  # Still authenticated
    
    # All requests share the same connection pool
    # Connections are reused automatically`}</CodeBlock>
      </section>

      {/* Creating Sessions */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Creating Sessions</h2>
        <CodeBlock language="python" filename="create_session.py">{`from aquilia.http import Session, HTTPClientConfig, TimeoutConfig

# Basic session
session = Session()

# Session with configuration
session = Session(HTTPClientConfig(
    base_url="https://api.example.com",
    default_headers={
        "User-Agent": "MyApp/1.0",
        "Accept": "application/json",
    },
    timeout=TimeoutConfig(total=30.0),
))

# Context manager (recommended)
async with Session(config) as session:
    response = await session.get("/users")
    # Session automatically closes when context exits

# Manual lifecycle
session = Session()
try:
    response = await session.get("/users")
finally:
    await session.close()  # Release connections`}</CodeBlock>
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
          Sessions automatically handle cookies:
        </p>
        <CodeBlock language="python" filename="cookies.py">{`session = Session()

# Server sends Set-Cookie header
response = await session.post("/login", json={
    "username": "alice",
    "password": "secret"
})
# Response includes: Set-Cookie: session_id=abc123; Path=/

# Session stores the cookie automatically
# Future requests include the cookie
profile = await session.get("/profile")
# Request includes: Cookie: session_id=abc123

# Access stored cookies
print(session.cookies)
# {"session_id": "abc123"}

# Manually set cookies
session.cookies["custom"] = "value"

# Delete a cookie
del session.cookies["session_id"]

# Clear all cookies
session.cookies.clear()

# Cookies persist across requests in the session
for i in range(10):
    await session.get(f"/api/data/{i}")
    # All requests send the same cookies`}</CodeBlock>
      </section>

      {/* Authentication */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Authentication</h2>
        <CodeBlock language="python" filename="auth.py">{`# Bearer token auth
session = Session(HTTPClientConfig(
    default_headers={"Authorization": "Bearer your-token-here"}
))
response = await session.get("/protected")

# Basic auth (per request)
response = await session.get(
    "/protected",
    auth=("username", "password")
)

# OAuth2 flow with session
session = Session(HTTPClientConfig(base_url="https://api.example.com"))

# 1. Get access token
token_response = await session.post("/oauth/token", json={
    "grant_type": "client_credentials",
    "client_id": "your-client-id",
    "client_secret": "your-secret",
})
token = (await token_response.json())["access_token"]

# 2. Update session headers
session.config.default_headers["Authorization"] = f"Bearer {token}"

# 3. All future requests are authenticated
users = await session.get("/api/users")
posts = await session.get("/api/posts")`}</CodeBlock>
      </section>

      {/* Connection Reuse */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Connection Reuse</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Sessions maintain a connection pool for performance:
        </p>
        <div className={boxClass}>
          <h3 className={`font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Benefits:</h3>
          <ul className={`space-y-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li>• <strong>Reduced latency</strong> — No TCP handshake overhead</li>
            <li>• <strong>Lower CPU usage</strong> — No repeated TLS negotiation</li>
            <li>• <strong>Better throughput</strong> — HTTP keep-alive and pipelining</li>
            <li>• <strong>Resource efficiency</strong> — Fewer file descriptors</li>
          </ul>
        </div>
        <CodeBlock language="python" filename="connection_pool.py">{`from aquilia.http import Session, PoolConfig, HTTPClientConfig

session = Session(HTTPClientConfig(
    pool=PoolConfig(
        max_connections=100,             # Total pool size
        max_connections_per_host=10,     # Per-host limit
        keepalive_expiry=60.0,           # Connection lifetime (seconds)
    )
))

# First request creates a connection
await session.get("https://api.example.com/users")
# Connection to api.example.com:443 is opened

# Second request reuses the connection
await session.get("https://api.example.com/posts")
# Same connection is reused (no handshake)

# Concurrent requests share the pool
import asyncio
tasks = [
    session.get(f"https://api.example.com/user/{i}")
    for i in range(50)
]
responses = await asyncio.gather(*tasks)
# Uses up to 10 concurrent connections to api.example.com
# Connections are reused across tasks`}</CodeBlock>
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
