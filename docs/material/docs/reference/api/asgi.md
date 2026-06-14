# ASGI Adapter

The `ASGIAdapter` bridges the ASGI protocol to Aquilia's request/response system. It supports HTTP, WebSocket, and Lifespan events with optimized hot paths for route matching and DI container resolution.

## ASGIAdapter

```python
class ASGIAdapter:
    """
    ASGI application adapter.
    Converts ASGI events to Aquilia Request/Response.
    Uses controller-based routing exclusively.
    """

    __slots__ = (
        "controller_router",
        "controller_engine",
        "middleware_stack",
        "server",
        "socket_runtime",
        "logger",
        "_cached_middleware_chain",
        "_default_container",
        "_debug",
        "_has_routes_cache",
        "_server_runtime",
    )

    def __init__(
        self,
        controller_router: ControllerRouter,
        controller_engine: Any,
        middleware_stack: MiddlewareStack,
        server: Any | None = None,
        socket_runtime: Any | None = None,
    ):
```

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `controller_router` | `ControllerRouter` | Compiled controller router with all routes |
| `controller_engine` | `Any` | Controller execution engine |
| `middleware_stack` | `MiddlewareStack` | Configured middleware stack |
| `server` | `Any \| None` | Reference to `AquiliaServer` (optional) |
| `socket_runtime` | `Any \| None` | WebSocket runtime (optional) |

## ASGI Entry Point

```python
async def __call__(
    self,
    scope: ASGIScope,
    receive: ASGIReceive,
    send: ASGISend,
) -> None:
```

Dispatches based on `scope["type"]`:

| Scope Type | Handler | Description |
|---|---|---|
| `"http"` | `handle_http()` | HTTP request processing |
| `"websocket"` | `handle_websocket()` | WebSocket connection handling |
| `"lifespan"` | `handle_lifespan()` | Startup/shutdown events |

## HTTP Handling

```python
async def handle_http(
    self,
    scope: ASGIScope,
    receive: ASGIReceive,
    send: ASGISend,
) -> None:
```

**Request flow:**

1. **Fast-path health endpoint** (`GET /_health` or `HEAD /_health`) — served directly without middleware
2. **Middleware chain** built once and cached (`_build_cached_chain()`)
3. **Version pre-resolution** — URL-path versions (e.g. `/v2/users`) are resolved before router matching so versioned routes match correctly
4. **Sync route matching** — three-tier O(1)/O(k)/O(n) via `ControllerRouter.match_sync()`
5. **HEAD auto-support** — if `HEAD` has no route but `GET` does, the `GET` route is used with an empty body (HTTP/1.1 §9.4)
6. **405 Method Not Allowed** — when a path exists but the method is not registered
7. **DI container** resolved per-app for request-scoped containers
8. **RequestCtx pooling** — zero-alloc acquisition from `_RequestCtxPool`
9. **Middleware execution** — the cached chain wraps the final handler which dispatches to the matched controller
10. **Metrics** — `EngineMetrics` tracks in-flight count, request started/finished/errored

### `_send_method_not_allowed()`

```python
async def _send_method_not_allowed(
    self,
    send: ASGISend,
    allowed: list[str],
    scope: ASGIScope | None = None,
) -> None:
```

Sends a `405 Method Not Allowed` response with an `Allow` header. Renders the styled error page for browser clients (`text/html` Accept) or structured JSON for API clients.

**JSON response format:**

```json
{
    "error": {
        "code": "HTTP_405",
        "message": "Method Not Allowed",
        "status": 405,
        "detail": "Method DELETE is not allowed for /users. Allowed: GET, HEAD, POST",
        "allowed_methods": ["GET", "HEAD", "POST"]
    }
}
```

### `_serve_health()`

```python
async def _serve_health(
    self,
    send: ASGISend,
    *,
    head_only: bool = False,
) -> None:
```

Built-in `GET /_health` endpoint returning:

```json
{
    "status": "healthy",
    "metrics": {
        "inflight": 3,
        "total_requests": 15000,
        "mean_latency_ms": 12.5,
        ...
    },
    "subsystems": {
        "database": {"name": "database", "status": "healthy", ...},
        "cache": {"name": "cache", "status": "healthy", ...}
    }
}
```

- `status` degrades to `"degraded"` if any subsystem is unhealthy (from `HealthRegistry`)
- Security headers applied: `no-store`, `nosniff`, `DENY` frame options

### Error Handling

When the middleware chain throws an unhandled exception:

- **Browser clients** (`Accept: text/html`): Renders a debug exception page in debug mode, or a styled 500 error page in production
- **API clients**: Returns `{"error": "Internal server error"}` with status 500
- Never leaks tracebacks in JSON responses
- Fallback safe HTML response if the error renderer itself crashes

## WebSocket Handling

```python
async def handle_websocket(
    self,
    scope: ASGIScope,
    receive: ASGIReceive,
    send: ASGISend,
) -> None:
```

Delegates to `socket_runtime.handle_websocket()` if sockets are configured. Otherwise sends `websocket.close` with code 1003.

## Lifespan Handling

```python
async def handle_lifespan(
    self,
    scope: ASGIScope,
    receive: ASGIReceive,
    send: ASGISend,
) -> None:
```

Handles `lifespan.startup` and `lifespan.shutdown` ASGI events.

**Startup:**
1. Calls `server.startup()` to initialize all subsystems
2. Invalidates cached middleware chain, DI container, routes cache, and debug flag
3. Sends `lifespan.startup.complete`

**Shutdown:**
1. Calls `server.shutdown()` to gracefully stop subsystems
2. Sends `lifespan.shutdown.complete`

!!! note "Startup Guards"
    `DatabaseNotReadyError` (a `SystemExit` subclass) is caught during startup and logged as a warning. The lifespan still completes to prevent uvicorn from falling back to "lifespan unsupported."

## Cached Helpers

```python
def _is_debug(self) -> bool:
    """Check if running in debug mode (lazily evaluated and cached)."""

def _get_default_container(self):
    """Get or create the default app DI container (cached)."""

def _has_routes(self) -> bool:
    """Check if any routes are registered (cached)."""
```

## Middleware Chain Building

```python
def _build_cached_chain(self):
    """Build the middleware chain once. The final handler dispatches
    to the matched controller stored in request.state."""
```

The final handler in the chain:

1. Reads `request.state["_controller_match"]` for the matched route
2. Calls `controller_engine.execute()` with the matched route, request, params, and DI container
3. On no match:
    - **Browser clients**: Returns a styled 404 HTML error page (or welcome page at `/` in debug mode with no routes)
    - **API clients**: Raises `NotFoundFault`

## Version Pre-Resolution

```python
def _resolve_route_inputs(
    self,
    request: Request,
    raw_path: str,
) -> tuple[str, Any | None]:
```

Used in the HTTP hot path to pre-resolve API version and strip the version prefix from the URL path. This ensures routes like `/v2/users` match against `/users` patterns when URL-path versioning is active. The `VersionMiddleware` remains the source of truth for `request.state` population and error responses.