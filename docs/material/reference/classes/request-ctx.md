# RequestCtx

## Overview

`RequestCtx` is the request-scoped context object threaded through every controller handler, middleware, and pipeline node. It provides access to the request, identity, session, DI container, and mutable state — and is backed by a performance-optimized object pool.

---

## Architecture

```
RequestCtx
├── request       → Aquilia Request (path, method, headers, query, body)
├── identity      → Auth Identity (authenticated principal)
├── session       → Session store
├── auth          → Auth metadata
├── container     → Request-scoped DI container
├── state         → Arbitrary key-value dict
├── request_id    → Unique request UUID (X-Request-ID)
└── _extra        → Dynamic attribute escape hatch for plugins/middleware
```

### Object Pool (`_RequestCtxPool`)

To eliminate per-request heap allocation, `RequestCtx` instances are pooled:

```python
class _RequestCtxPool:
    def __init__(self, max_size: int = 256): ...

    def acquire(
        self,
        request: Request,
        identity: Identity | None = None,
        session: Session | None = None,
        auth: Any | None = None,
        container: Any | None = None,
        state: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> RequestCtx: ...

    def release(self, ctx: RequestCtx) -> None: ...
```

The pool pre-allocates up to 256 instances; `acquire()` resets fields in-place; `release()` clears references for GC.

---

## Constructor

```python
class RequestCtx:
    __slots__ = (
        "request",
        "identity",
        "session",
        "auth",
        "container",
        "state",
        "request_id",
        "_extra",
    )

    def __init__(
        self,
        request: Request,
        identity: Identity | None = None,
        session: Session | None = None,
        auth: Any | None = None,
        container: Any | None = None,
        state: dict[str, Any] | None = None,
        request_id: str | None = None,
    ):
```

---

## Properties

### Request Delegation

These properties delegate directly to the underlying `request` object:

| Property | Type | Description |
|---|---|---|
| `path` | `str` | Request path (e.g. `"/users/42"`) |
| `method` | `str` | HTTP method (e.g. `"GET"`) |
| `headers` | `Headers` | Request headers |
| `query_params` | `MultiDict` | Parsed query string parameters |

### Core Fields

| Property | Type | Description |
|---|---|---|
| `request` | `Request` | The raw Aquilia `Request` object |
| `identity` | `Identity \| None` | Authenticated identity (set by auth middleware) |
| `session` | `Session \| None` | Session object (set by session middleware) |
| `auth` | `Any \| None` | Auth metadata |
| `container` | `Any \| None` | Request-scoped DI container |
| `state` | `dict[str, Any]` | Mutable key-value store |
| `request_id` | `str \| None` | Unique request identifier |

---

## Methods

### Request Body Parsing

```python
async def json(self) -> Any:
    """Parse request body as JSON."""

async def body(self) -> bytes:
    """Read raw request body bytes."""

async def form(self) -> FormData:
    """Parse request body as form data (application/x-www-form-urlencoded)."""

async def multipart(self):
    """Parse multipart/form-data (file uploads)."""
```

### Query Parameters

```python
def query_param(self, key: str, default: str | None = None) -> str | None:
    """Get a single query parameter value."""
```

---

## Dynamic Attributes (`_extra`)

The `__getattr__` and `__setattr__` overrides provide an escape hatch for middleware and plugins to attach arbitrary attributes without needing to pre-declare them:

```python
# Middleware or interceptor
ctx._custom_start_time = time.monotonic()

# Later in a controller handler
elapsed = time.monotonic() - ctx._custom_start_time
```

This avoids the need for a large `__slots__` declaration while keeping core attributes fast via slots.

---

## Usage in Controller Methods

```python
class UsersController(Controller):
    prefix = "/users"

    @GET("/{id:int}")
    async def retrieve(self, ctx: RequestCtx, id: int):
        # Access request properties
        path = ctx.path                # "/users/42"
        method = ctx.method           # "GET"
        qp = ctx.query_param("verbose", default="0")

        # Read identity
        identity = ctx.identity
        if identity:
            roles = identity.attributes.get("roles", [])

        # Use state (mutable dict for cross-cutting data)
        ctx.state["_controller_label"] = "users.retrieve"

        # Parse request body (POST/PUT/PATCH)
        data = await ctx.json()

        return Response.json(...)
```

### Usage in Middleware

```python
async def custom_middleware(
    request: Request,
    ctx: RequestCtx,
    next_handler: RequestHandler,
) -> Response:
    # Store data before handler
    ctx.state["_mw_start"] = time.monotonic()

    # Attach custom attribute
    ctx.custom_analytics_id = generate_id()

    response = await next_handler(request, ctx)

    # Read elapsed
    elapsed = time.monotonic() - ctx.state["_mw_start"]
    response.headers["X-Elapsed-Ms"] = str(int(elapsed * 1000))

    return response
```

---

## Lifecycle

```
Request arrives
    │
    ▼
RequestIdMiddleware sets ctx.request_id
    │
    ▼
RequestScopeMiddleware creates request-scoped DI container
    │ → ctx.container = scoped_di
    │
    ▼
AuthMiddleware attaches ctx.identity / ctx.auth / ctx.session
    │
    ▼
ControllerEngine resolves controller, injects dependencies
    │
    ▼
Handler executes with ctx
    │
    ▼
Interceptors.after() can mutate result
    │
    ▼
Response returned → ctx released to pool (_ctx_pool.release())
```

### Pool Release

On release, all references are cleared:
- `ctx.request = None`
- `ctx.identity = None`
- `ctx.session = None`
- `ctx.container = None`
- `ctx.state = {}`
- `ctx._extra = None`

---

## Context Var Integration

The active `RequestCtx` for the current task is tracked via a `ContextVar`:

```python
_current_request_ctx: ContextVar["RequestCtx | None"] = ContextVar(...)
```

Helper functions:

```python
def _set_current_request_ctx(ctx: RequestCtx) -> Token:
def _reset_current_request_ctx(token: Token) -> None:
def _get_current_request_ctx() -> RequestCtx | None:
```

This allows `Controller.render()` to work without explicitly passing `ctx`.

---

## Metrics and Timing

While `RequestCtx` itself doesn't include built-in timing, interceptors and middleware can use `ctx.state` to track metrics:

```python
class MetricsInterceptor(Interceptor):
    async def before(self, ctx):
        ctx.state["_request_start"] = time.perf_counter_ns()

    async def after(self, ctx, result):
        start = ctx.state.pop("_request_start", 0)
        elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000
        ctx.state["_request_elapsed_ms"] = elapsed_ms
        return result
```