# API Reference

Aquilia is an async-native, manifest-first Python web framework. This API reference documents every public framework subsystem with code signatures, parameter details, and usage examples. All content is derived from Aquilia source code.

## Subsystems

| Subsystem | Description |
|---|---|
| [ASGI Adapter](asgi.md) | ASGI protocol bridging: HTTP, WebSocket, lifespan handling |
| [Controllers](controllers.md) | Controller base, route decorators, validation, pagination, filters, renderers, OpenAPI, metadata |
| [WebSockets](websockets.md) | SocketController, decorators, events, subscriptions, guards, connection lifecycle |
| [SSE](sse.md) | Server-Sent Events: SSEEvent, SSEResponse, streaming |
| [API Versioning](versioning.md) | Version strategies, decorators, resolvers, sunset policies, middleware |
| [Structured Faults](faults.md) | Fault base class, domains, severity, engine, all ~70 fault subclasses |
| [Flow Pipeline](flow.md) | FlowPipeline, nodes, contexts, priorities, effect scoping, composition |
| [Effect System](effects.md) | Effect tokens, providers, handles (Cache, HTTP, Queue, Storage), EffectRegistry |
| [Health Registry](health.md) | Centralized subsystem health tracking and reporting |

## Architecture

The boot sequence is:

```
Manifests → Aquilary → RuntimeRegistry → Controllers → ASGI
```

1. **`workspace.py`** declares workspace orchestration
2. **`modules/*/manifest.py`** each module declares its controllers, services, middleware
3. **`aquilia/entrypoint.py:create_app()`** reads workspace, discovers manifests, constructs `AquiliaServer`
4. **`aquilia/server.py:AquiliaServer`** builds metadata, registry, router, middleware, ASGI app
5. **`aquilia/asgi.py:ASGIAdapter`** handles HTTP/WebSocket/lifespan, performs route matching, creates request-scoped DI containers

## Key Types

### RequestCtx

```python
class RequestCtx:
    request: Request           # The incoming ASGI request
    identity: Optional[Identity]  # Authenticated identity
    session: Optional[Session]    # Session object
    auth: Any                     # Auth state
    container: Any                # DI container (request-scoped)
    state: dict[str, Any]         # Arbitrary middleware state
    request_id: str               # Unique request ID

    # Convenience properties
    path: str                     # Request path
    method: str                   # HTTP method
    headers: Headers              # Request headers
    query_params: MultiDict       # Query parameters

    # Body parsing
    async def json() -> Any       # Parse JSON body
    async def body() -> bytes     # Read raw body
    async def form() -> FormData  # Parse form data
    async def multipart()         # Parse multipart/form-data
```

### Response

```python
class Response:
    def __init__(content, status=200, headers=None, media_type=None, ...)

    # Factory methods
    @classmethod def json(obj, status=200, **kwargs) -> Response
    @classmethod def html(content: str, status=200, **kwargs) -> Response
    @classmethod def text(content: str, status=200, **kwargs) -> Response
    @classmethod def redirect(url: str, status=307, **kwargs) -> Response
    @classmethod def stream(iterator, status=200, media_type=..., **kwargs) -> Response
    @classmethod def file(path, *, filename=None, media_type=None, ...) -> Response
    @classmethod def sse(event_iter, status=200, **kwargs) -> Response
    @classmethod def surp(obj, status=200, *, compression=None, ...) -> Response

    # Cookie helpers
    def set_cookie(name, value, *, max_age=None, secure=True, httponly=True, ...)
    def delete_cookie(name, path="/", domain=None)

    # Header helpers
    def set_header(name: str, value: str)
    def add_header(name: str, value: str)
    def unset_header(name: str)

    # Caching helpers
    def set_etag(etag: str, weak=False)
    def set_last_modified(dt: datetime)
    def cache_control(**directives)
    def secure_headers(*, hsts=True, csp=None, frame_options="DENY", ...)
```

### Request

```python
class Request:
    scope: dict              # Raw ASGI scope
    method: str              # HTTP method
    path: str                # Request path
    query_params: MultiDict  # Parsed query string
    headers: Headers         # Request headers
    state: dict              # Arbitrary middleware state

    def header(name: str, default=None) -> str | None
    def query_param(key: str, default=None) -> str | None
    async def json() -> Any
    async def body() -> bytes
    async def form() -> FormData
    async def multipart()
```

## Middleware Stack

Aquilia ships with these built-in middleware classes:

| Middleware | Purpose |
|---|---|
| `RequestIdMiddleware` | Adds unique X-Request-ID to every request |
| `ExceptionMiddleware` | Converts Faults/exceptions to HTTP responses |
| `LoggingMiddleware` | Logs request/response with timing |
| `TimeoutMiddleware` | Enforces request timeout |
| `CompressionMiddleware` | Gzip response compression |
| `CORSMiddleware` | CORS headers and preflight handling |
| `VersionMiddleware` | API version resolution |
| `SessionMiddleware` | Session persistence |
| `CSRFMiddleware` | Cross-Site Request Forgery protection |
| `CSPMiddleware` | Content-Security-Policy headers |
| `HSTSMiddleware` | HTTP Strict Transport Security |
| `RateLimitMiddleware` | Request rate limiting |
| `StaticMiddleware` | Static file serving with caching |