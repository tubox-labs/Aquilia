import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, Globe } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function HTTPIntegration() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Globe className="w-4 h-4" />
          HTTP Client / Integration
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Aquilia Integration
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Using the HTTP client within Aquilia: dependency injection, config builders, and integration with other subsystems.
        </p>
      </div>

      {/* Dependency Injection */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Dependency Injection</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The HTTPClient integrates seamlessly with Aquilia's DI system:
        </p>
        <CodeBlock language="python" filename="di_basic.py">{`from aquilia import Controller, RequestCtx, Response
from aquilia.http import HTTPClient

# Inject HTTPClient into controllers
class UsersController(Controller):
    prefix = "/users"
    
    def __init__(self, http: HTTPClient):
        self.http = http
    
    async def get_user_data(self, ctx: RequestCtx):
        # HTTPClient is injected automatically
        response = await self.http.get("https://api.github.com/users/octocat")
        user_data = await response.json()
        return Response.json(user_data)

# Inject into services
class GitHubService:
    def __init__(self, http: HTTPClient):
        self.http = http
    
    async def get_repos(self, username: str):
        response = await self.http.get(f"https://api.github.com/users/{username}/repos")
        return await response.json()

# Register service in manifest
from aquilia import AppManifest

manifest = AppManifest(
    services=[GitHubService],
    controllers=[UsersController],
)`}</CodeBlock>
      </section>

      {/* Configuration via Workspace */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Configuration via Workspace</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Configure HTTP clients in your workspace.py:
        </p>
        <CodeBlock language="python" filename="workspace.py">{`from aquilia import Workspace, Integration
from aquilia.http import HTTPClientConfig, TimeoutConfig, RetryConfig, PoolConfig

workspace = Workspace(
    integrations=[
        # Configure default HTTP client
        Integration.http_client(
            config=HTTPClientConfig(
                timeout=TimeoutConfig(
                    total=30.0,
                    connect=10.0,
                    read=20.0,
                ),
                pool=PoolConfig(
                    max_connections=100,
                    max_connections_per_host=10,
                ),
                default_headers={
                    "User-Agent": "MyApp/1.0",
                },
                retry=RetryConfig(
                    max_attempts=3,
                    backoff_factor=2.0,
                ),
            ),
        ),
        
        # Named HTTP client for specific API
        Integration.http_client(
            name="github_client",
            config=HTTPClientConfig(
                base_url="https://api.github.com",
                default_headers={
                    "Accept": "application/vnd.github+json",
                    "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
                },
            ),
        ),
        
        # Another named client
        Integration.http_client(
            name="internal_api",
            config=HTTPClientConfig(
                base_url="http://internal-api:8080",
                verify_ssl=False,  # Internal network
                timeout=TimeoutConfig(total=60.0),
            ),
        ),
    ],
)

# In controllers/services, inject by name
class GitHubController(Controller):
    def __init__(self, github_client: HTTPClient):
        # Injects the "github_client" instance
        self.http = github_client
    
    async def get_repos(self, ctx: RequestCtx):
        # Already configured with base_url and auth
        response = await self.http.get("/users/octocat/repos")
        return Response.json(await response.json())`}</CodeBlock>
      </section>

      {/* Provider Scopes */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Provider Scopes</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          HTTP clients can be registered with different DI scopes:
        </p>
        <div className={boxClass}>
          <div className="space-y-4">
            <div>
              <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Singleton (default)</h3>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                One client instance shared across entire app lifecycle. Best for most use cases — enables connection pooling and reuse.
              </p>
            </div>
            <div>
              <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>App Scope</h3>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                One instance per application instance (useful in multi-tenant scenarios).
              </p>
            </div>
            <div>
              <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Request Scope</h3>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                New client per request (not recommended — loses connection pooling benefits).
              </p>
            </div>
          </div>
        </div>
        <CodeBlock language="python" filename="scopes.py">{`from aquilia.di import Scope

# Singleton (recommended)
Integration.http_client(
    name="api_client",
    config=config,
    scope=Scope.SINGLETON,  # Default
)

# App scope
Integration.http_client(
    name="tenant_client",
    config=config,
    scope=Scope.APP,
)

# Request scope (not recommended)
Integration.http_client(
    name="per_request_client",
    config=config,
    scope=Scope.REQUEST,
)`}</CodeBlock>
      </section>

      {/* Multiple Clients */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Multiple Named Clients</h2>
        <CodeBlock language="python" filename="multiple_clients.py">{`# workspace.py
workspace = Workspace(
    integrations=[
        Integration.http_client(
            name="github",
            config=HTTPClientConfig(base_url="https://api.github.com"),
        ),
        Integration.http_client(
            name="stripe",
            config=HTTPClientConfig(
                base_url="https://api.stripe.com",
                default_headers={"Authorization": f"Bearer {STRIPE_KEY}"},
            ),
        ),
        Integration.http_client(
            name="sendgrid",
            config=HTTPClientConfig(
                base_url="https://api.sendgrid.com",
                default_headers={"Authorization": f"Bearer {SENDGRID_KEY}"},
            ),
        ),
    ],
)

# Service using multiple clients
class IntegrationService:
    def __init__(
        self,
        github: HTTPClient,
        stripe: HTTPClient,
        sendgrid: HTTPClient,
    ):
        self.github = github
        self.stripe = stripe
        self.sendgrid = sendgrid
    
    async def process_payment_and_notify(self, user_id: str, amount: int):
        # Fetch user from GitHub
        user_response = await self.github.get(f"/users/{user_id}")
        user = await user_response.json()
        
        # Create payment in Stripe
        payment_response = await self.stripe.post(
            "/v1/charges",
            json={"amount": amount, "currency": "usd"},
        )
        payment = await payment_response.json()
        
        # Send notification via SendGrid
        await self.sendgrid.post(
            "/v3/mail/send",
            json={
                "personalizations": [{"to": [{"email": user["email"]}]}],
                "from": {"email": "noreply@example.com"},
                "subject": "Payment Confirmation",
                "content": [{"type": "text/plain", "value": f"Payment confirmed"}],
            },
        )
        
        return payment`}</CodeBlock>
      </section>

      {/* Integration with RequestCtx */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Integration with RequestCtx</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Pass request context to upstream APIs:
        </p>
        <CodeBlock language="python" filename="request_context.py">{`class ProxyController(Controller):
    prefix = "/api"
    
    def __init__(self, http: HTTPClient):
        self.http = http
    
    async def proxy_request(self, ctx: RequestCtx):
        # Forward headers from incoming request
        headers = {
            "X-Request-ID": ctx.request_id,
            "X-User-ID": ctx.user.id if ctx.user else None,
            "Authorization": ctx.headers.get("Authorization"),
        }
        
        # Proxy to upstream API
        response = await self.http.get(
            f"https://api.example.com{ctx.path}",
            headers=headers,
            params=dict(ctx.query_params),
        )
        
        # Return upstream response
        return Response(
            body=await response.read(),
            status=response.status_code,
            headers=dict(response.headers),
        )`}</CodeBlock>
      </section>

      {/* Integration with Cache */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Integration with Cache</h2>
        <CodeBlock language="python" filename="cache_integration.py">{`from aquilia.cache import Cache
from aquilia.http import HTTPClient

class CachedAPIService:
    def __init__(self, http: HTTPClient, cache: Cache):
        self.http = http
        self.cache = cache
    
    async def get_user(self, user_id: str):
        # Try cache first
        cache_key = f"user:{user_id}"
        cached = await self.cache.get(cache_key)
        
        if cached:
            return cached
        
        # Cache miss, fetch from API
        response = await self.http.get(f"/users/{user_id}")
        user_data = await response.json()
        
        # Store in cache (1 hour TTL)
        await self.cache.set(cache_key, user_data, ttl=3600)
        
        return user_data
    
    async def invalidate_user(self, user_id: str):
        await self.cache.delete(f"user:{user_id}")`}</CodeBlock>
      </section>

      {/* Integration with Tasks */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Integration with Tasks</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Use HTTPClient in background tasks:
        </p>
        <CodeBlock language="python" filename="tasks_integration.py">{`from aquilia.tasks import task, TaskContext
from aquilia.http import HTTPClient

@task(name="sync_github_repos")
async def sync_github_repos(ctx: TaskContext, username: str):
    # HTTPClient can be injected in tasks
    http: HTTPClient = ctx.container.resolve(HTTPClient)
    
    # Fetch repos from GitHub
    response = await http.get(f"https://api.github.com/users/{username}/repos")
    repos = await response.json()
    
    # Process repos
    for repo in repos:
        await process_repo(repo)
    
    return {"synced": len(repos)}

# Schedule task
from aquilia.tasks import TaskScheduler

scheduler = TaskScheduler()
await scheduler.enqueue(sync_github_repos, username="octocat")

# Periodic task with HTTP client
@task(name="health_check", schedule="*/5 * * * *")  # Every 5 minutes
async def health_check(ctx: TaskContext):
    http = ctx.container.resolve(HTTPClient)
    
    services = [
        "https://api.example.com/health",
        "https://db.example.com/ping",
        "https://cache.example.com/status",
    ]
    
    results = []
    for service_url in services:
        try:
            response = await http.get(service_url, timeout=TimeoutConfig(total=5.0))
            results.append({"url": service_url, "status": "healthy"})
        except HTTPClientFault as e:
            results.append({"url": service_url, "status": "unhealthy", "error": str(e)})
    
    return results`}</CodeBlock>
      </section>

      {/* Integration with Storage */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Integration with Storage</h2>
        <CodeBlock language="python" filename="storage_integration.py">{`from aquilia.storage import StorageBackend
from aquilia.http import HTTPClient

class ImageDownloadService:
    def __init__(self, http: HTTPClient, storage: StorageBackend):
        self.http = http
        self.storage = storage
    
    async def download_and_store(self, url: str, key: str):
        # Stream download from HTTP
        response = await self.http.get(url)
        
        # Stream directly to storage (no intermediate buffer)
        async with await self.storage.open(key, "wb") as f:
            async for chunk in response.stream():
                await f.write(chunk)
        
        return {
            "key": key,
            "size": response.headers.get("Content-Length"),
            "content_type": response.headers.get("Content-Type"),
        }
    
    async def upload_to_api(self, key: str):
        # Stream from storage to HTTP
        async with await self.storage.open(key, "rb") as f:
            data = await f.read()
        
        response = await self.http.post(
            "https://api.example.com/upload",
            data=data,
            headers={"Content-Type": "application/octet-stream"},
        )
        
        return await response.json()`}</CodeBlock>
      </section>

      {/* Integration with Sessions */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Integration with Sessions</h2>
        <CodeBlock language="python" filename="sessions_integration.py">{`from aquilia.sessions import SessionManager
from aquilia.http import HTTPClient

class OAuthService:
    def __init__(self, http: HTTPClient, sessions: SessionManager):
        self.http = http
        self.sessions = sessions
    
    async def oauth_callback(self, ctx: RequestCtx):
        code = ctx.query_params.get("code")
        
        # Exchange code for token
        response = await self.http.post(
            "https://oauth.example.com/token",
            json={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
            },
        )
        
        token_data = await response.json()
        access_token = token_data["access_token"]
        
        # Store token in session
        session = await self.sessions.get(ctx)
        session["access_token"] = access_token
        await self.sessions.save(session)
        
        return Response.redirect("/dashboard")
    
    async def api_request(self, ctx: RequestCtx, endpoint: str):
        # Get token from session
        session = await self.sessions.get(ctx)
        access_token = session.get("access_token")
        
        if not access_token:
            return Response.redirect("/login")
        
        # Use token for API request
        response = await self.http.get(
            f"https://api.example.com{endpoint}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        
        return Response.json(await response.json())`}</CodeBlock>
      </section>

      {/* Complete Example */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Complete Example</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          A full Aquilia app using HTTP client with DI:
        </p>
        <CodeBlock language="python" filename="complete_example.py">{`# workspace.py
from aquilia import Workspace, Module, Integration
from aquilia.http import HTTPClientConfig, TimeoutConfig

workspace = Workspace(
    modules=[
        Module("api", path="./modules/api"),
    ],
    integrations=[
        Integration.http_client(
            name="github",
            config=HTTPClientConfig(
                base_url="https://api.github.com",
                timeout=TimeoutConfig(total=30.0),
                default_headers={
                    "Accept": "application/vnd.github+json",
                    "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
                },
            ),
        ),
    ],
)

# modules/api/manifest.py
from aquilia import AppManifest
from .controllers import GitHubController
from .services import GitHubService

manifest = AppManifest(
    name="api",
    services=[GitHubService],
    controllers=[GitHubController],
)

# modules/api/services.py
from aquilia.http import HTTPClient

class GitHubService:
    def __init__(self, github: HTTPClient):
        self.http = github
    
    async def get_user(self, username: str):
        response = await self.http.get(f"/users/{username}")
        response.raise_for_status()
        return await response.json()
    
    async def list_repos(self, username: str):
        response = await self.http.get(f"/users/{username}/repos")
        response.raise_for_status()
        return await response.json()

# modules/api/controllers.py
from aquilia import Controller, GET, RequestCtx, Response
from .services import GitHubService

class GitHubController(Controller):
    prefix = "/github"
    tags = ["github"]
    
    def __init__(self, github_service: GitHubService):
        self.github = github_service
    
    @GET("/users/{username}")
    async def get_user(self, ctx: RequestCtx):
        username = ctx.path_params["username"]
        
        try:
            user = await self.github.get_user(username)
            return Response.json(user)
        
        except HTTPClientFault as e:
            return Response.json(
                {"error": e.message, "code": e.code},
                status=500,
            )
    
    @GET("/users/{username}/repos")
    async def list_repos(self, ctx: RequestCtx):
        username = ctx.path_params["username"]
        repos = await self.github.list_repos(username)
        return Response.json({"repos": repos, "count": len(repos)})

# Run the app
# aq serve`}</CodeBlock>
      </section>

      {/* Best Practices */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Best Practices</h2>
        <div className={boxClass}>
          <ul className={`space-y-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li>
              <strong className={isDark ? 'text-white' : 'text-gray-900'}>Use singleton scope</strong> — Enables connection pooling and reuse
            </li>
            <li>
              <strong className={isDark ? 'text-white' : 'text-gray-900'}>Configure in workspace.py</strong> — Centralize HTTP client configuration
            </li>
            <li>
              <strong className={isDark ? 'text-white' : 'text-gray-900'}>Use named clients</strong> — One client per external API for isolation
            </li>
            <li>
              <strong className={isDark ? 'text-white' : 'text-gray-900'}>Inject into services</strong> — Not directly in controllers
            </li>
            <li>
              <strong className={isDark ? 'text-white' : 'text-gray-900'}>Handle faults explicitly</strong> — Catch and convert to appropriate responses
            </li>
            <li>
              <strong className={isDark ? 'text-white' : 'text-gray-900'}>Set reasonable timeouts</strong> — Prevent hanging requests
            </li>
            <li>
              <strong className={isDark ? 'text-white' : 'text-gray-900'}>Enable retries for transient failures</strong> — Network blips, rate limits
            </li>
            <li>
              <strong className={isDark ? 'text-white' : 'text-gray-900'}>Use base_url for API clients</strong> — Avoid repetition
            </li>
          </ul>
        </div>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/http/faults" className={`flex items-center gap-2 text-sm ${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`}>
          <ArrowLeft className="w-4 h-4" /> Error Handling
        </Link>
      </div>
    
      <NextSteps />
    </div>
  )
}
