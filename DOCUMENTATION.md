# Aquilia Framework — Comprehensive Documentation

> **Version**: 1.0.0  
> **Python**: ≥ 3.12  
> **Protocol**: ASGI 3.0  
> **License**: Custom (see LICENSE)

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Core Runtime](#2-core-runtime)
3. [Manifest & Registry System](#3-manifest--registry-system)
4. [Controller System](#4-controller-system)
5. [Dependency Injection](#5-dependency-injection)
6. [Middleware Pipeline](#6-middleware-pipeline)
7. [Fault System](#7-fault-system)
8. [Session Management](#8-session-management)
9. [Authentication & Authorization](#9-authentication--authorization)
10. [Blueprints (Data Validation)](#10-blueprints-data-validation)
11. [Database & ORM](#11-database--orm)
12. [Effects System](#12-effects-system)
13. [Template Engine](#13-template-engine)
14. [Cache Subsystem](#14-cache-subsystem)
15. [Mail Subsystem](#15-mail-subsystem)
16. [WebSocket Support](#16-websocket-support)
17. [Build Pipeline](#17-build-pipeline)
18. [CLI Tooling](#18-cli-tooling)
19. [Testing Infrastructure](#19-testing-infrastructure)
20. [Deployment](#20-deployment)
21. [Configuration Reference](#21-configuration-reference)
22. [Architecture Comparison](#22-architecture-comparison)
23. [Audit Report & Changelog](#23-audit-report--changelog)

---

## 1. Architecture Overview

### 1.1 Design Philosophy

Aquilia is a **manifest-first, modular async Python web framework** built on ASGI 3.0. It draws inspiration from:

| Influence | What Aquilia adopts |
|-----------|-------------------|
| **NestJS** | Module/manifest-driven architecture, DI containers, controller classes |
| **Django** | Batteries-included (ORM, auth, sessions, templates, mail, cache), opinionated structure |
| **FastAPI** | ASGI-native, async-first, type-annotated handlers, auto-generated OpenAPI |
| **Phoenix (Elixir)** | Effect system, fault supervision, lifecycle hooks |
| **Spring Boot** | Bean scoping (singleton/request/transient), container hierarchies |

### 1.2 Request Lifecycle

```
HTTP Request
    │
    ▼
┌─────────────────┐
│   ASGI Adapter   │  ← scope/receive/send → Request object
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Middleware Stack  │  ← RequestId → Exception → Fault → Logging → CORS → CSRF
│  (cached chain)  │    → Helmet → HSTS → Rate Limit → Auth → Session → Template
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Controller Router │  ← O(1) static hash + O(k) dynamic trie/regex
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Controller Engine │  ← DI injection, Blueprint validation, Pipeline execution
│  + Factory + DI  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Handler Method   │  ← Your code: async def get_users(self, ctx)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Content Negotiation│ ← JSON/XML/YAML/MsgPack/HTML renderers
│ + Filters + Paging │
└────────┬────────┘
         │
         ▼
    Response (ASGI send)
```

### 1.3 Boot Sequence

```
1. AquiliaServer.__init__()
   ├── ConfigLoader (6-layer merge)
   ├── Aquilary.from_manifests() → AquilaryRegistry (static metadata only)
   ├── RuntimeRegistry.from_metadata() (lazy — no imports yet)
   ├── _register_services() → DI containers populated
   ├── MiddlewareStack + ControllerRouter + ControllerEngine
   └── ASGIAdapter wraps everything

2. server.startup() [via ASGI lifespan]
   ├── perform_autodiscovery() → PackageScanner finds controllers/services
   ├── _load_controllers() → import, compile, register routes
   ├── compile_routes() → wrap handlers with DI
   ├── coordinator.startup() → app lifecycle hooks (topological order)
   ├── _register_amdl_models() → database setup
   ├── EffectRegistry.initialize_all()
   ├── CacheService.initialize()
   └── HealthRegistry status → "Server ready"

3. server.shutdown() [via ASGI lifespan]
   ├── coordinator.shutdown() → reverse order hooks
   ├── Mail/Cache subsystem shutdown
   ├── DI container cleanup (LIFO finalizers)
   ├── EffectRegistry.finalize_all()
   ├── WebSocket runtime shutdown
   └── Database disconnect
```

---

## 2. Core Runtime

### 2.1 AquiliaServer (`server.py` — 2510 lines)

The central orchestrator. Creates all subsystems in `__init__`, runs lifecycle in `startup()/shutdown()`.

```python
from aquilia import AquiliaServer, ConfigLoader

server = AquiliaServer(
    manifests=[UsersManifest, OrdersManifest],
    config=ConfigLoader(workspace_path="./"),
    mode=RegistryMode.PROD,
)
server.run(host="0.0.0.0", port=8000)
```

**Key attributes:**
- `server.aquilary` — `AquilaryRegistry` (static metadata)
- `server.runtime` — `RuntimeRegistry` (DI containers, compiled routes)
- `server.coordinator` — `LifecycleCoordinator`
- `server.controller_router` — Two-tier route matcher
- `server.middleware_stack` — Priority-ordered middleware chain
- `server.fault_engine` — Typed error handling
- `server.health_registry` — Subsystem health tracking

### 2.2 ASGIAdapter (`asgi.py` — 410 lines)

Bridges ASGI protocol to Aquilia internals with a **cached middleware chain** for zero-overhead repeated requests.

**Hot path optimizations:**
- `_cached_middleware_chain` — built once, reused for all requests
- `_server_runtime` — cached reference avoids attribute lookups
- `_default_container` — cached for routes without app context
- O(1) static route matching → O(k) dynamic only if needed

### 2.3 Request (`request.py` — 1656 lines)

Production-grade ASGI request wrapper with:
- Lazy header/query/cookie parsing
- Streaming body support with size limits
- Multipart file upload handling
- State dictionary for middleware communication
- Security limits (max body size, max headers)
- Fault integration for malformed requests

### 2.4 Response (`response.py` — 1635 lines)

Full-featured response builder:
- `Response.json(data, status=200)` — JSON serialization
- `Response.html(body)` — HTML response
- `Response.redirect(url, status=302)` — Redirect
- `Response.stream(async_gen)` — Streaming response
- `Response.sse(async_gen)` — Server-Sent Events
- `Response.file(path)` — File download with range request support
- Cookie management with signing support
- Automatic content-encoding negotiation (gzip, brotli)

### 2.5 Engine (`engine.py` — 286 lines)

Lightweight request context and metrics:

```python
@dataclass
class RequestCtx:
    request: Request
    identity: Optional[Identity]
    session: Optional[Session]
    container: Container
    state: dict
    request_id: Optional[str]

class EngineMetrics:
    # Thread-safe counters: total requests, in-flight, error count
    # Mean/p99 latency tracking via rolling window
```

---

## 3. Manifest & Registry System

### 3.1 Manifests (`manifest.py`)

Manifests declare application modules without importing them:

```python
class UsersManifest:
    name = "users"
    version = "1.0.0"
    controllers = ["modules.users.controllers:UserController"]
    services = ["modules.users.services:UserService"]
    models = ["modules/users/models.py"]
    depends_on = ["auth"]
    middleware = []
    effects = []
    
    @staticmethod
    async def on_startup(config, container):
        print("Users module starting...")
    
    @staticmethod
    async def on_shutdown(config, container):
        print("Users module stopping...")
```

### 3.2 Aquilary Registry (`aquilary/core.py` — 1254 lines)

Two-phase architecture:

1. **`AquilaryRegistry`** (static) — metadata only, no imports
   - Validates manifests, builds dependency graph, computes fingerprint
   - Topological sort for load order
   - Route index (lazy metadata)
   - `export_manifest(path)` → writes `.crous` binary for production

2. **`RuntimeRegistry`** (runtime) — imports and compiles
   - `perform_autodiscovery()` — scans `modules/<name>/` recursively
   - `compile_routes()` — imports controllers, wraps handlers with DI
   - `_register_services()` — populates DI containers from manifest declarations
   - `_register_effects()` — registers effect providers
   - `validate_all()` → checks dependencies, routes, effects

### 3.3 Manifest Loader (`aquilary/loader.py`)

Supports multiple formats:
- Python classes with attributes
- `.crous` binary manifests (production)
- `.json` manifest files (legacy fallback)
- Filesystem autodiscovery

### 3.4 Crous Binary Format

Custom binary format for fast manifest serialization:
- Native backend: `_crous_native` (Rust via PyO3) — ~10× faster
- Pure Python fallback: `crous` package
- Sidecar `.aq.json` metadata files for tooling

---

## 4. Controller System

### 4.1 Controller Base (`controller/base.py`)

```python
from aquilia import Controller, GET, POST, PUT, DELETE, RequestCtx, Response

class UserController(Controller):
    prefix = "/users"
    
    @GET("/")
    async def list_users(self, ctx: RequestCtx):
        return {"users": []}
    
    @GET("/:id")
    async def get_user(self, ctx: RequestCtx, id: int):
        return {"id": id, "name": "Alice"}
    
    @POST("/")
    async def create_user(self, ctx: RequestCtx, data: dict):
        return Response.json({"created": True}, status=201)
    
    async def on_request(self, ctx: RequestCtx):
        """Called before every handler (lifecycle hook)."""
        pass
    
    async def on_response(self, ctx: RequestCtx, response: Response):
        """Called after every handler (lifecycle hook)."""
        pass
```

### 4.2 Router (`controller/router.py` — 281 lines)

**Two-tier matching:**
1. **Static routes** — O(1) hash map lookup (`{(method, path): route}`)
2. **Dynamic routes** — O(k) trie/regex matching for parameterized paths

```python
# Static: GET /users → instant lookup
# Dynamic: GET /users/:id → regex match → params = {"id": "42"}
```

### 4.3 Controller Engine (`controller/engine.py` — 953 lines)

Full integration orchestrator:
- DI-aware controller instantiation via `ControllerFactory`
- Pipeline execution (class-level + method-level guards/pipes)
- Parameter binding from path, query, body, DI, and `Dep()` descriptors
- Blueprint auto-parsing for typed request bodies
- Content negotiation with multiple renderers
- FilterSet, SearchFilter, OrderingFilter, Pagination support
- Lifecycle hooks (`on_request`, `on_response`)

**Fast path:** Simple handlers (no pipeline, no blueprint) skip the full machinery and are called directly.

### 4.4 Decorators (`controller/decorators.py`)

```python
@GET("/path", pipeline=[auth_guard], request_blueprint=CreateUserBP)
@POST("/path", renderer_classes=[JSONRenderer, XMLRenderer])
@PUT("/path/:id")
@PATCH("/path/:id")
@DELETE("/path/:id")
@HEAD("/path")
@OPTIONS("/path")
@WS("/ws")  # WebSocket handler
```

### 4.5 Filters & Pagination (`controller/filters.py`, `controller/pagination.py`)

```python
class UserController(Controller):
    @GET("/", filterset_fields=["name", "email"],
         search_fields=["name"], ordering_fields=["created_at"],
         pagination_class=PageNumberPagination)
    async def list_users(self, ctx):
        return users  # Automatically filtered + paginated
```

**Pagination strategies:**
- `PageNumberPagination` — `?page=2&page_size=10`
- `LimitOffsetPagination` — `?limit=10&offset=20`
- `CursorPagination` — `?cursor=<opaque>&limit=10`

### 4.6 Renderers (`controller/renderers.py`)

Content negotiation via `Accept` header:
- `JSONRenderer` — `application/json`
- `XMLRenderer` — `application/xml`
- `YAMLRenderer` — `application/yaml`
- `PlainTextRenderer` — `text/plain`
- `HTMLRenderer` — `text/html`
- `MessagePackRenderer` — `application/msgpack`

### 4.7 OpenAPI (`controller/openapi.py`)

Auto-generates OpenAPI 3.x specification from controller metadata:

```python
# Built-in endpoints (enabled by default):
# GET /docs/openapi.json  → OpenAPI spec
# GET /docs               → Swagger UI
# GET /docs/redoc          → ReDoc
```

---

## 5. Dependency Injection

### 5.1 Container (`di/core.py` — 874 lines)

Hierarchical scoped containers with <3µs cached lookups:

```python
from aquilia.di import Container, Inject
from aquilia.di.decorators import service, factory, inject
from aquilia.di.providers import ClassProvider, FactoryProvider, ValueProvider

# Scopes
container = Container(scope="app")
request_container = container.create_request_scope()  # Very cheap
```

**Scopes:**
| Scope | Lifetime | Use Case |
|-------|----------|----------|
| `singleton` | Entire process | Database pools, config |
| `app` | App lifecycle | Services, repositories |
| `request` | Single HTTP request | Request-specific state |
| `transient` | Each resolution | Stateless utilities |
| `pooled` | Pool-managed | Connection pools |
| `ephemeral` | Immediate disposal | One-shot operations |

### 5.2 Providers

```python
# Class provider — auto-resolves constructor dependencies
@service(scope="app")
class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

# Factory provider — custom instantiation
@factory(scope="request")
def get_db_session(pool: ConnectionPool) -> DBSession:
    return pool.acquire()

# Value provider — pre-built instance
container.register(ValueProvider(value=config, token=Config, scope="singleton"))

# Alias provider — interface → implementation binding
container.bind(UserRepository, SqlUserRepository)
```

### 5.3 Dep() Descriptors (`di/dep.py`)

```python
from aquilia.di.dep import Dep, Header, Query, Body
from typing import Annotated

class UserController(Controller):
    @GET("/")
    async def get_users(
        self,
        ctx: RequestCtx,
        service: Annotated[UserService, Dep()],           # DI injection
        auth_token: Annotated[str, Header("Authorization")],  # Header
        page: Annotated[int, Query("page", default=1)],       # Query param
    ):
        ...
```

### 5.4 Cycle Detection (`di/graph.py`)

Uses **Tarjan's algorithm** for strongly connected components to detect circular dependencies at build time.

### 5.5 Cross-App Dependency Validation

Ensures apps only consume services from declared `depends_on` peers, preventing hidden coupling.

---

## 6. Middleware Pipeline

### 6.1 MiddlewareStack (`middleware.py` — 464 lines)

Priority-ordered middleware chain with scope hierarchy:

```
Scope ordering: global < app < controller < route
Within scope: sorted by priority (ascending)
```

**Signature:** `async (request, ctx, next) -> Response`

### 6.2 Built-in Middleware

| Middleware | Priority | Purpose |
|-----------|----------|---------|
| `ExceptionMiddleware` | 1 | Catches all exceptions, renders debug pages |
| `FaultMiddleware` | 2 | Processes typed Fault signals |
| `RequestIdMiddleware` | 3 | Adds `X-Request-ID` header (os.urandom, 4× faster than uuid4) |
| `LoggingMiddleware` | 100 | Request/response logging with timing |
| `TimeoutMiddleware` | — | Enforces request timeout (asyncio.wait_for) |
| `CORSMiddleware` | — | Cross-origin resource sharing |
| `CompressionMiddleware` | — | Response gzip compression |

### 6.3 Security Middleware (`middleware_ext/`)

Configured via `server._setup_security_middleware()`:

| Middleware | Purpose |
|-----------|---------|
| `ProxyFix` | X-Forwarded-For/Proto handling |
| `HTTPSRedirect` | Force HTTPS |
| `StaticFiles` | Serve static assets with ETag/compression |
| `Helmet` | Security headers (X-Frame-Options, X-Content-Type, etc.) |
| `HSTS` | HTTP Strict Transport Security |
| `CSP` | Content Security Policy |
| `CORS` | Cross-Origin Resource Sharing |
| `CSRF` | Cross-Site Request Forgery protection |
| `RateLimit` | Rate limiting (memory/Redis backends) |

---

## 7. Fault System

### 7.1 Philosophy

Aquilia uses **typed fault signals** instead of bare exceptions. A `Fault` carries domain, severity, recovery strategy, and structured context.

### 7.2 Core Types (`faults/core.py` — 470 lines)

```python
from aquilia.faults import Fault, FaultDomain, Severity, RecoveryStrategy

raise Fault(
    code="USER_NOT_FOUND",
    message="User with ID 42 not found",
    domain=FaultDomain.MODEL,
    severity=Severity.WARNING,
    recovery=RecoveryStrategy.RETURN_DEFAULT,
    context={"user_id": 42},
    public=True,  # Safe to expose to client
)
```

**Domains:** `ROUTING`, `SECURITY`, `IO`, `EFFECT`, `MODEL`, `CACHE`, `CONFIG`, `REGISTRY`, `DI`, `FLOW`, `SYSTEM`

**Severity levels:** `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

### 7.3 Fault → HTTP Status Mapping

The `ExceptionMiddleware` automatically maps faults to HTTP status codes:

| Code Pattern | Status |
|-------------|--------|
| `AUTH_REQUIRED`, `AUTHENTICATION_REQUIRED` | 401 |
| `FaultDomain.SECURITY` | 403 |
| `*NOT_FOUND*`, `*MISSING*` | 404 |
| `USER_ALREADY_EXISTS` | 409 |
| `*VALIDATION*`, `*INVALID*` | 400 |
| `FaultDomain.IO` | 502 |
| `FaultDomain.EFFECT` | 503 |
| Everything else | 500 |

### 7.4 Pre-built Fault Domains (`faults/domains.py`)

```python
# Raises structured faults:
ModelFault("User", "not_found", user_id=42)
SecurityFault("access_denied", resource="admin_panel")
```

---

## 8. Session Management

### 8.1 Architecture

Policy-driven sessions with pluggable storage and transport:

```
SessionPolicy → SessionEngine → SessionStore + SessionTransport
```

### 8.2 Session Policy (`sessions/policy.py`)

```python
SessionPolicy(
    name="user_default",
    ttl=timedelta(days=7),
    idle_timeout=timedelta(minutes=30),
    rotate_on_privilege_change=True,
    max_sessions_per_principal=5,
    persistence=PersistencePolicy.LAZY,
    concurrency=ConcurrencyPolicy.MULTI_SESSION,
    transport=TransportPolicy.COOKIE,
)
```

### 8.3 Stores

| Store | Backend | Use Case |
|-------|---------|----------|
| `MemoryStore` | In-process dict | Development, testing |
| `FileStore` | Filesystem JSON | Simple deployments |
| `RedisStore` | Redis | Production, multi-process |

### 8.4 Transports

| Transport | Mechanism |
|-----------|-----------|
| `CookieTransport` | `Set-Cookie` / `Cookie` header |
| `HeaderTransport` | Custom header (e.g., `X-Session-ID`) |

### 8.5 Decorators

```python
from aquilia.sessions.decorators import session, authenticated, stateful

@session           # Requires active session
@authenticated     # Requires authenticated identity
@stateful(CartState)  # Requires specific state type
```

---

## 9. Authentication & Authorization

### 9.1 Auth Manager (`auth/manager.py`)

Central authentication hub:

```python
# Registration
result = await auth_manager.register(
    Identity(email="user@example.com"),
    Credential(password="secret"),
)

# Login
result = await auth_manager.authenticate(
    Credential(email="user@example.com", password="secret"),
)
# → AuthResult(success=True, identity=..., tokens=TokenPair(...))

# Token refresh
new_tokens = await auth_manager.refresh(refresh_token)
```

### 9.2 Token Manager (`auth/tokens.py`)

- JWT-based with RS256/HS256
- Key rotation with `KeyRing`
- Access + refresh token pairs
- Configurable TTL

### 9.3 Authorization (`auth/authz.py`)

**RBAC Engine:**
```python
@rbac(roles=["admin", "moderator"])
async def delete_user(self, ctx, id: int): ...
```

**ABAC Engine:**
```python
@abac(policy=lambda identity, resource: identity.department == resource.department)
async def view_report(self, ctx): ...
```

### 9.4 OAuth2 / OIDC (`auth/oauth.py`)

Supports external identity providers (Google, GitHub, etc.) via OAuth2 authorization code flow.

### 9.5 Multi-Factor Authentication (`auth/mfa.py`)

TOTP-based MFA with setup, verify, and recovery flows.

---

## 10. Blueprints (Data Validation)

### 10.1 Core (`blueprints/core.py`)

Blueprints are **typed data contracts** between the world and your models:

```python
from aquilia.blueprints import Blueprint, field

class CreateUserBlueprint(Blueprint):
    class Meta:
        model = User
        fields = ["name", "email", "age"]
        readonly = ["id", "created_at"]
    
    name = field(str, min_length=2, max_length=100)
    email = field(str, format="email")
    age = field(int, min_value=13, max_value=150, required=False)
```

### 10.2 Features

- **Auto-parsing:** Controller engine auto-parses request body through blueprints
- **Sealing:** `blueprint.is_sealed(raise_fault=True)` validates all fields
- **Partial mode:** PATCH requests auto-enable partial validation
- **Projections:** `Blueprint["summary"]` returns only projected fields
- **Facets:** Read/write views of the same model
- **Lenses:** Computed/transformed fields

---

## 11. Database & ORM

### 11.1 AquiliaDatabase (`db/`)

Async database adapter supporting:
- SQLite (via `aiosqlite`)
- PostgreSQL (via `asyncpg`)
- MySQL (via `aiomysql`)

### 11.2 Python Models (`models/base.py`)

Pure Python ORM with metaclass registration:

```python
from aquilia.models import Model, StringField, IntField, ForeignKey

class User(Model):
    class Meta:
        table = "users"
    
    name = StringField(max_length=100)
    email = StringField(unique=True)
    age = IntField(nullable=True)
```

### 11.3 AMDL (Legacy)

Aquilia Model Definition Language — a custom DSL for schema definitions in `.amdl` files. Supported for backwards compatibility.

### 11.4 Migrations (`models/migrations.py`)

```python
runner = MigrationRunner(db, "migrations/")
await runner.migrate()  # Apply pending migrations
```

---

## 12. Effects System

### 12.1 Concept

Effects represent **typed side-effect capabilities** that handlers declare they need:

```python
from aquilia.effects import DBTx, CacheEffect, QueueEffect

# Handler declares its effects:
@GET("/users", effects=[DBTx("read"), CacheEffect("users")])
async def get_users(self, ctx):
    db = await ctx.container.resolve_async(DBTx)
    cache = await ctx.container.resolve_async(CacheEffect)
    ...
```

### 12.2 Built-in Effects

| Effect | Kind | Description |
|--------|------|-------------|
| `DBTx` | DB | Database transaction (read/write) |
| `CacheEffect` | CACHE | Cache namespace access |
| `QueueEffect` | QUEUE | Message queue publish |

### 12.3 EffectRegistry

Manages provider lifecycle:
```python
registry = EffectRegistry()
registry.register("DBTx", DBTxProvider(connection_string="..."))
await registry.initialize_all()  # Startup
await registry.finalize_all()    # Shutdown
```

---

## 13. Template Engine

### 13.1 Features

- Jinja2-based with bytecode caching (memory or Crous binary)
- Sandbox mode (strict/permissive policies)
- DI integration via `TemplateMiddleware`
- CLI commands: compile, lint, inspect, clear-cache

### 13.2 Usage

```python
# In controller:
@GET("/profile")
async def profile(self, ctx: RequestCtx):
    return ctx.container.resolve(TemplateEngine).render(
        "profile.html", user=ctx.identity
    )
```

---

## 14. Cache Subsystem

### 14.1 Backends

| Backend | Class | Use Case |
|---------|-------|----------|
| Memory | `MemoryCache` | Development, single-process |
| Redis | `RedisCache` | Production, multi-process |
| Composite | `CompositeCache` | L1 memory + L2 Redis |

### 14.2 CacheService

```python
cache = await container.resolve_async(CacheService)
await cache.set("user:42", user_data, ttl=300)
user = await cache.get("user:42")
await cache.delete("user:42")
```

### 14.3 Eviction Policies

- LRU (Least Recently Used)
- LFU (Least Frequently Used)
- TTL-based expiry

---

## 15. Mail Subsystem

### 15.1 Architecture

```
MailService → MailProvider (SMTP/SES/SendGrid/Console)
     ↓
Envelope → Template → Send with retry + rate limiting
```

### 15.2 Usage

```python
mail = await container.resolve_async(MailService)
await mail.send(
    to="user@example.com",
    subject="Welcome!",
    template="welcome.html",
    context={"name": "Alice"},
)
```

### 15.3 Features

- Multiple provider backends (SMTP, AWS SES, SendGrid, Console)
- Template-based emails with Jinja2
- Retry with exponential backoff + jitter
- Per-domain rate limiting
- DKIM signing support
- PII redaction for logging

---

## 16. WebSocket Support

### 16.1 Socket Controllers (`sockets/`)

```python
from aquilia.sockets import Socket, OnConnect, OnMessage, OnDisconnect

@Socket("/ws/chat")
class ChatSocket:
    @OnConnect
    async def on_connect(self, ctx):
        await ctx.join_room("general")
    
    @OnMessage
    async def on_message(self, ctx, data):
        await ctx.broadcast_to_room("general", data)
    
    @OnDisconnect
    async def on_disconnect(self, ctx):
        await ctx.leave_room("general")
```

### 16.2 Features

- DI-integrated socket controllers
- Room-based messaging
- Guards for auth/rate-limiting
- In-memory adapter (Redis adapter planned)

---

## 17. Build Pipeline

### 17.1 Components

| Component | Purpose |
|-----------|---------|
| `StaticChecker` | Validates Python files for syntax/import errors |
| `CrousBundler` | Bundles workspace into `.crous` binary |
| `BuildResolver` | Resolves build artifacts from cache |
| `AquiliaBuildPipeline` | Orchestrates check → bundle → resolve |

### 17.2 Usage

```python
from aquilia.build import AquiliaBuildPipeline
from pathlib import Path

pipeline = AquiliaBuildPipeline(workspace_root=Path("."))
result = pipeline.run(mode="production")
print(result.bundle_manifest)  # BundleManifest with stats
```

### 17.3 CLI

```bash
aquilia build --mode production
aquilia build --check-only        # Syntax check without bundling
```

---

## 18. CLI Tooling

### 18.1 Commands

```bash
# Scaffolding
aquilia new workspace my_app      # Create new workspace
aquilia new module users          # Generate module scaffold
aquilia new controller Users      # Generate controller

# Build & Deploy
aquilia build                     # Run build pipeline
aquilia deploy --target gunicorn  # Generate deployment configs

# Utilities
aquilia routes                    # List all registered routes
aquilia discover                  # Show discovered components
aquilia fingerprint               # Show registry fingerprint
```

### 18.2 Generators

- `WorkspaceGenerator` — Full workspace scaffold
- `ModuleGenerator` — Module with manifest, controller, service
- `ControllerGenerator` — Controller with CRUD methods
- `ComposeGenerator` — Docker Compose configurations
- `MakefileGenerator` — Makefile for common tasks

---

## 19. Testing Infrastructure

### 19.1 TestClient (`testing/`)

```python
from aquilia.testing import TestClient, TestServer

async def test_users():
    server = TestServer(manifests=[UsersManifest])
    async with TestClient(server) as client:
        response = await client.get("/users")
        assert response.status == 200
        assert "users" in response.json()
```

### 19.2 TestCase

```python
from aquilia.testing import TestCase

class UserTests(TestCase):
    manifests = [UsersManifest]
    
    async def test_create_user(self):
        response = await self.client.post("/users", json={"name": "Alice"})
        self.assertEqual(response.status, 201)
```

---

## 20. Deployment

### 20.1 Development

```python
server.run(host="127.0.0.1", port=8000, reload=True)
```

### 20.2 Production (Uvicorn)

```bash
uvicorn app:server.app --host 0.0.0.0 --port 8000 --workers 4
```

### 20.3 Production (Gunicorn)

```bash
gunicorn app:server.app -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000
```

Configuration generated via `aquilia deploy --target gunicorn`:

```python
# gunicorn.conf.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
graceful_timeout = 30
```

### 20.4 Docker

```bash
aquilia deploy --target docker   # Generates Dockerfile + docker-compose.yml
```

---

## 21. Configuration Reference

### 21.1 Six-Layer Merge Strategy

```
1. Workspace defaults (Python config)
2. base.yaml/json config file
3. {env}.yaml config file (e.g., production.yaml)
4. Environment variables (AQ_ prefix)
5. .env file
6. Runtime overrides
```

Each layer deep-merges into the previous, with later layers taking precedence.

### 21.2 Environment Variables

```bash
AQ_DATABASE__URL=postgresql://localhost/mydb
AQ_SESSIONS__ENABLED=true
AQ_SESSIONS__STORE__TYPE=redis
AQ_AUTH__TOKENS__SECRET_KEY=my-secret
AQ_CACHE__BACKEND=redis
AQ_CACHE__REDIS_URL=redis://localhost:6379/0
```

Double underscore (`__`) creates nested config keys.

### 21.3 Config Sections

| Section | Description |
|---------|-------------|
| `database` | URL, auto_create, auto_migrate, migrations_dir |
| `sessions` | policy, store, transport |
| `auth` | store, tokens, security |
| `security` | CORS, CSRF, Helmet, HSTS, rate limiting |
| `cache` | backend, TTL, eviction, Redis options |
| `mail` | providers, templates, retry, rate limits |
| `templates` | search_paths, precompile, cache, sandbox |
| `static_files` | directories, cache_max_age, ETag, gzip |

---

## 22. Architecture Comparison

### 22.1 vs Django

| Feature | Django | Aquilia |
|---------|--------|---------|
| Protocol | WSGI (ASGI optional) | ASGI-native |
| Async | Partial (views only) | Full async throughout |
| DI | None (manual wiring) | Full container with scopes |
| Configuration | `settings.py` module | 6-layer merge with typed validation |
| ORM | Powerful, sync | Lightweight, async |
| Routing | URL patterns + `urls.py` | Controller classes + decorators |
| Middleware | `MIDDLEWARE` list | Priority-ordered stack with scopes |
| Error handling | `handler404/500` | Typed Fault system with domains |
| Admin | Built-in admin panel | ✗ (planned) |
| Community | Massive | Emerging |

### 22.2 vs FastAPI

| Feature | FastAPI | Aquilia |
|---------|---------|---------|
| Routing | Function decorators | Controller classes |
| Validation | Pydantic models | Blueprint system |
| DI | `Depends()` (functional) | Container with scopes + graph analysis |
| Modules | APIRouter (flat) | Manifests with dependency graph |
| Session | Via Starlette | Full policy-driven engine |
| Auth | Manual | Built-in (OAuth2, MFA, RBAC/ABAC) |
| WebSockets | Basic support | Socket controllers with rooms + DI |
| ORM | None (bring your own) | Built-in with migrations |
| Build | None | Build pipeline with Crous binary |
| Error model | HTTPException | Typed Fault system |

### 22.3 vs NestJS

| Feature | NestJS | Aquilia |
|---------|--------|---------|
| Language | TypeScript | Python |
| Module system | `@Module()` decorator | Manifest classes |
| DI | Hierarchical containers | Scoped containers + cross-app validation |
| Guards | `CanActivate` interface | Pipeline nodes + auth guards |
| Pipes | Transform + validate | Blueprint system |
| Interceptors | Before/after advice | Middleware + controller lifecycle hooks |
| Filters | Exception filters | Fault domains + handlers |

### 22.4 Strengths of Aquilia

1. **Manifest-first architecture** — apps are declared, not imported, enabling static analysis
2. **Typed fault system** — structured errors with domains, severity, recovery strategies
3. **Crous binary format** — fast serialization for production manifests and caches
4. **Effect system** — typed side-effect declarations for dependency tracking
5. **Blueprint validation** — model-aware data contracts with projections and facets
6. **Six-layer config** — environment-aware configuration with typed validation
7. **Build pipeline** — Vite-inspired static checking and bundling

---

## 23. Audit Report & Changelog

### 23.1 Issues Found & Fixed

#### CRITICAL — Startup Race Condition

**Problem:** In `server.py startup()`, only Steps 0-1 (autodiscovery, controller loading) were inside the `async with self._startup_lock` block. Steps 2-end (route compilation, lifecycle hooks, model registration, effect initialization, cache startup, health registration) were **outside the lock**, allowing concurrent startup calls to execute them in parallel.

**Impact:** In multi-worker deployments or when lifespan events fire rapidly, duplicate route compilation, double DI registration, or corrupted state could occur.

**Fix:** Moved all startup steps inside the `async with self._startup_lock:` block.

#### CRITICAL — Double Event Loop in `run()`

**Problem:** `server.run()` called `asyncio.run(self.startup())` to create one event loop, then `asyncio.new_event_loop()` for signal handlers, then `uvicorn.run()` which creates its own event loop. Three event loops were created, and `asyncio.run(self.graceful_shutdown())` in `finally` created a fourth.

**Impact:** Startup hooks ran in a different event loop than the request handlers, causing `RuntimeError: attached to a different loop` for any async resources (database connections, etc.) created during startup.

**Fix:** Removed manual `startup()` and `graceful_shutdown()` calls. Uvicorn manages the event loop and calls startup/shutdown via the ASGI lifespan protocol.

#### HIGH — Operator Precedence Bug in Model Discovery

**Problem:** In `RuntimeRegistry._discover_python_models()`:
```python
not getattr(attr, '_meta', None) or (
    hasattr(attr, '_meta') and not getattr(attr._meta, 'abstract', False)
)
```
Due to Python's operator precedence, `not X or Y` is `(not X) or Y`, meaning:
- If `_meta` is `None` → `not None` is `True` → model is included ✓
- If `_meta` exists → `not _meta` is `False` → falls to OR → checks `abstract` ✓
- But if `_meta` is truthy AND `abstract` is `False` → `not False` is `True` → **but this whole expression is part of the outer `and` chain** which was already short-circuited incorrectly.

Actually the bug was: the `and not getattr(attr, '_meta', None) or (...)` was evaluated as `(... and (not getattr(attr, '_meta', None))) or (...)`, meaning any object with a truthy `_meta` would fail the `and` clause, fall to `or`, and then the right side would include models that have `_meta.abstract=False` — even if they aren't `type` or don't subclass `Model`.

**Fix:** Restructured to explicit `if/continue` logic:
```python
if isinstance(attr, type) and issubclass(attr, Model) and attr is not Model:
    meta = getattr(attr, '_meta', None)
    if meta is not None and getattr(meta, 'abstract', False):
        continue
    discovered.append(attr)
```

#### HIGH — DI `resolve()` Sync Method Error Handling

**Problem:** The sync `resolve()` method tried to detect if an event loop was running using `asyncio.get_running_loop()`, but its `except RuntimeError` clause caught ALL `RuntimeError` exceptions — including the intentional one it raised about using `resolve_async()`. This meant calling `resolve()` from async context would raise the error, catch it, and then try `asyncio.run()` inside a running loop, causing a different `RuntimeError`.

**Fix:** Added check for our own error message before re-raising:
```python
except RuntimeError as e:
    if "resolve()" in str(e):
        raise  # Re-raise our own error
    # No running loop — safe to use asyncio.run()
```

#### MID — Bare `print()` Statements in Runtime Code

**Problem:** 15+ bare `print()` calls in `aquilary/core.py` and `di/core.py` for warnings, debug output, and status messages. In production, these bypass the logging system entirely — can't be filtered, formatted, or routed to monitoring.

**Fix:** Replaced all with proper `logging.getLogger('aquilia.*')` calls:
- `print(f"Warning: ...")` → `logger.warning(...)`
- `print(f"✓ Registered ...")` → `logger.info(...)`
- `print(f"Error during ...")` → `logger.warning(...)`
- Removed all commented-out `DEBUG` prints

### 23.2 Issues Identified (Lower Priority)

#### LOW — Inconsistent Config Access Patterns

Multiple config access patterns coexist:
- `self.config.get("key")` (dict-style)
- `self.config.to_dict()["key"]` (dict export)
- `hasattr(self.config, 'attr')` (attribute-style)

**Recommendation:** Unify around `config.get()` with dot-path support.

#### LOW — Template `print()` Statements

`templates/manager.py` and `templates/cli.py` use `print()` for CLI output. These are acceptable for CLI commands but the `manager.py` ones should use logging.

#### LOW — Missing `py.typed` Marker

No `py.typed` marker file exists, so type checkers won't check `aquilia` as typed even though it has type annotations throughout.

#### LOW — Session Store `max_sessions` Not Enforced by Memory Store

The `MemoryStore` config accepts `max_sessions` but there's no eviction when the limit is reached.

### 23.3 Phase 1-3 Summary

| Phase | What Was Done | Files Changed |
|-------|--------------|---------------|
| **Phase 1: Build System** | Created `aquilia/build/` module — StaticChecker, CrousBundler, BuildResolver, AquiliaBuildPipeline | 5 new files |
| **Phase 2: Architecture** | Removed `aquilia/trace/` (8 files), migrated JSON→Crous binary format, added Gunicorn deploy support | 12+ files modified, 8 deleted, 3 new |
| **Phase 3: Regression Tests** | 106 tests across 20 test classes, removed broken `e2e/` and `test_mlops/` suites | 1 new file, 20+ deleted |
| **Phase 4: Audit & Docs** | Fixed 4 critical/high bugs, replaced 15+ bare prints with logging, wrote this documentation | 3 files modified, 1 new |

### 23.4 Test Results

```
106 passed in 0.33s
```

All tests pass after all fixes applied.

---

*Generated for Aquilia v1.0.0 — Last updated during Phase 4 audit.*
