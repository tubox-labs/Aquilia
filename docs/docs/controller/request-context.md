---
title: "Request Context"
description: "Understanding the RequestCtx object"
icon: lucide/arrow-left-right
---
## What is RequestCtx?

`RequestCtx` is the request context object provided to all controller methods in Aquilia. It encapsulates the HTTP request along with authentication, session, dependency injection container, and other request-scoped data.

!!! info "Implementation"
    Lines 60-68 in `base.py`: RequestCtx uses `__slots__` for compact memory layout and faster attribute access. It's pooled via `_RequestCtxPool` to eliminate per-request heap allocation while still allowing middleware/plugins to attach data via the `state` dict or `_extra` dict.


The RequestCtx provides a clean, unified interface for accessing request data, authentication state, and framework services without coupling your handlers to low-level ASGI interfaces.

---

## Slots

RequestCtx uses `__slots__` to define a fixed set of attributes, providing significant performance benefits:

```python
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
```

!!! info "Performance Rationale"
    Lines 4-7 in `base.py`: Using `__slots__` provides ~40% faster attribute access compared to regular `__dict__`-based instances. The object pool (`_RequestCtxPool`) eliminates per-request allocation by recycling RequestCtx objects using a pre-allocated ring buffer where `acquire()` resets fields in-place.


### Benefits of Slots

- **Memory efficiency**: Each instance saves ~200+ bytes by not having a `__dict__`
- **Faster attribute access**: Direct memory offsets instead of dictionary lookups
- **Better cache locality**: Compact memory layout improves CPU cache utilization
- **Pool-friendly**: Fixed size enables efficient object pooling

---

## Constructor Parameters

The RequestCtx constructor accepts the following parameters:

```python
def __init__(
    self,
    request: Request,
    identity: Optional[Identity] = None,
    session: Optional[Session] = None,
    auth: Any | None = None,
    container: Any | None = None,
    state: dict[str, Any] | None = None,
    request_id: str | None = None,
)
```

!!! info "Source Reference"
    Lines 79-90 in `base.py`: Constructor signature with all parameters, types, and defaults.


### Parameter Details

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `request` | `Request` | *required* | The underlying HTTP request object |
| `identity` | `Optional[Identity]` | `None` | Authenticated user identity (set by auth middleware) |
| `session` | `Optional[Session]` | `None` | Session object for stateful interactions |
| `auth` | `Any \| None` | `None` | Additional authentication data |
| `container` | `Any \| None` | `None` | Dependency injection container |
| `state` | `dict[str, Any] \| None` | `None` | Request-scoped state dictionary (shared across middleware) |
| `request_id` | `str \| None` | `None` | Unique request identifier for tracing |

---

## Properties

RequestCtx provides convenient read-only properties that delegate to the underlying request object:

### path

```python
@property
def path(self) -> str
```

Returns the request path (e.g., `/users/123`).

!!! info "Source Reference"
    Line 135-137 in `base.py`: Path property delegates to `self.request.path`.


### method

```python
@property
def method(self) -> str
```

Returns the HTTP method (e.g., `GET`, `POST`, `PUT`, `DELETE`).

!!! info "Source Reference"
    Line 139-141 in `base.py`: Method property delegates to `self.request.method`.


### headers

```python
@property
def headers(self) -> Headers
```

Returns the request headers as a `Headers` object (case-insensitive multi-value mapping).

!!! info "Source Reference"
    Line 143-145 in `base.py`: Headers property delegates to `self.request.headers`.


### query_params

```python
@property
def query_params(self) -> MultiDict
```

Returns parsed query string parameters as a `MultiDict` (supports multiple values per key).

!!! info "Source Reference"
    Line 147-149 in `base.py`: Query params property delegates to `self.request.query_params`.


### query_param Helper

```python
def query_param(self, key: str, default: str | None = None) -> str | None
```

Convenience method to get a single query parameter value.

!!! info "Source Reference"
    Line 151-153 in `base.py`: Delegates to `self.request.query_param()`.


---

## Async Methods

RequestCtx provides async methods for reading and parsing the request body:

### json

```python
async def json(self) -> Any
```

Parse the request body as JSON and return the deserialized Python object.

!!! info "Source Reference"
    Line 155-157 in `base.py`: Delegates to `await self.request.json()`.


**Example:**
```python
@POST("/users")
async def create_user(self, ctx: RequestCtx):
    data = await ctx.json()
    user = await self.repo.create(data)
    return {"user": user}
```

### body

```python
async def body(self) -> bytes
```

Read the raw request body as bytes.

!!! info "Source Reference"
    Line 159-161 in `base.py`: Delegates to `await self.request.body()`.


**Example:**
```python
@POST("/upload")
async def upload_raw(self, ctx: RequestCtx):
    raw_data = await ctx.body()
    # Process raw bytes
    return {"size": len(raw_data)}
```

### form

```python
async def form(self) -> FormData
```

Parse the request body as `application/x-www-form-urlencoded` or `multipart/form-data` and return a `FormData` object.

!!! info "Source Reference"
    Line 163-165 in `base.py`: Delegates to `await self.request.form()`.


**Example:**
```python
@POST("/login")
async def login(self, ctx: RequestCtx):
    form_data = await ctx.form()
    username = form_data.get("username")
    password = form_data.get("password")
    # Authenticate...
```

### multipart

```python
async def multipart(self)
```

Parse `multipart/form-data` for file uploads. Returns the parsed multipart data.

!!! info "Source Reference"
    Line 167-169 in `base.py`: Delegates to `await self.request.multipart()`.


**Example:**
```python
@POST("/upload")
async def upload_file(self, ctx: RequestCtx):
    data = await ctx.multipart()
    file = data.get("file")
    # Process file upload...
```

---

## Effect Methods

Effects are managed resources (database connections, file handles, etc.) that are acquired and released automatically per request.

### get_effect

```python
def get_effect(self, name: str) -> Any
```

Get an acquired effect resource by name. Raises `KeyError` if the effect is not found.

!!! info "Source Reference"
    Line 92-96 in `base.py`: Delegates to `self.request.get_effect(name)`.


**Example:**
```python
@GET("/users")
async def list_users(self, ctx: RequestCtx):
    db = ctx.get_effect("database")
    users = await db.query("SELECT * FROM users")
    return {"users": users}
```

### has_effect

```python
def has_effect(self, name: str) -> bool
```

Check if an effect resource is currently acquired. Returns `True` if the effect exists, `False` otherwise.

!!! info "Source Reference"
    Line 98-102 in `base.py`: Delegates to `self.request.has_effect(name)`.


**Example:**
```python
@GET("/data")
async def get_data(self, ctx: RequestCtx):
    if ctx.has_effect("cache"):
        cache = ctx.get_effect("cache")
        return cache.get("data")
    # Fallback to database...
```

---

## Dynamic Attributes

While RequestCtx uses `__slots__` for performance, it still supports dynamic attributes through the `_extra` dictionary escape hatch.

### _extra Dictionary

The `_extra` slot holds a dictionary for storing truly dynamic attributes that don't fit into the predefined slots.

!!! info "Source Reference"
    Line 90 in `base.py`: `_extra` is defined in `__slots__` and initialized to `None` in the constructor. It's lazily created on first dynamic attribute assignment.


### __getattr__

```python
def __getattr__(self, name: str) -> Any
```

Fallback for accessing dynamic attributes stored in `_extra`.

!!! info "Source Reference"
    Lines 105-111 in `base.py`: `__getattr__` is only called for unknown attributes (after `__slots__` lookup fails). It checks the `_extra` dict and raises `AttributeError` if not found.


### __setattr__

```python
def __setattr__(self, name: str, value: Any) -> None
```

Allows setting extra dynamic attributes. Known slots are set normally; unknown attributes are stored in `_extra`.

!!! info "Source Reference"
    Lines 113-122 in `base.py`: Fast path tries `object.__setattr__` first (for slots). On `AttributeError`, it lazily creates the `_extra` dict and stores the attribute there.


**Example:**
```python
# Middleware can attach custom attributes
ctx.custom_metric = 42
ctx.tracing_id = "abc-123"

# Later in handler
@GET("/debug")
async def debug(self, ctx: RequestCtx):
    return {
        "custom_metric": ctx.custom_metric,
        "tracing_id": ctx.tracing_id,
    }
```

---

## Object Pool

The `_RequestCtxPool` eliminates per-request heap allocation by recycling RequestCtx instances.

!!! info "Performance"
    Lines 175-266 in `base.py`: The pool uses a lock-free design safe for single-threaded async code. It pre-allocates RequestCtx objects and resets fields in-place on `acquire()`, avoiding `__init__` overhead.


### Pool Configuration

```python
class _RequestCtxPool:
    def __init__(self, max_size: int = 256):
        self._max_size = max_size
        self._pool: list[RequestCtx] = []
```

!!! info "Source Reference"
    Lines 186-189 in `base.py`: Pool initialization with configurable `max_size` (default 256).


**Parameters:**
- `max_size`: Maximum number of RequestCtx instances to keep in the pool (default: 256)

### acquire

```python
def acquire(
    self,
    request: Request,
    identity: Optional[Identity] = None,
    session: Optional[Session] = None,
    auth: Any | None = None,
    container: Any | None = None,
    state: dict[str, Any] | None = None,
    request_id: str | None = None,
) -> RequestCtx
```

Get a RequestCtx from the pool or create a new one. If `request_id` is `None`, a fresh random ID is generated.

!!! info "Source Reference"
    Lines 191-227 in `base.py`: `acquire()` pops from the pool if available and resets fields in-place. Otherwise, creates a new instance. ARCH-08: Auto-generates request_id if not provided to ensure reused contexts never carry stale IDs.


**Field Reset Strategy:**
- Resets all slot attributes to new values
- Avoids calling `__init__` (performance optimization)
- Clears `_extra` dict to prevent data leakage

### release

```python
def release(self, ctx: RequestCtx) -> None
```

Return a RequestCtx to the pool for reuse. Clears all references to allow garbage collection of request-scoped objects.

!!! info "Source Reference"
    Lines 229-241 in `base.py`: `release()` clears all references (sets to `None` or `_EMPTY_STATE`) before returning the instance to the pool, but only if pool hasn't reached `max_size`.


**Cleanup Strategy:**
- Clears all references (`request`, `identity`, `session`, etc.)
- Sets `state` to `_EMPTY_STATE` (reusable empty dict constant)
- Clears `_extra` dict
- Only pools if under `max_size` limit

### Module-level Pool Singleton

```python
_ctx_pool = _RequestCtxPool(max_size=256)
```

!!! info "Source Reference"
    Line 244 in `base.py`: Module-level singleton pool instance used throughout the framework.


---

## ContextVar Integration

Aquilia uses Python's `contextvars` module to make the current RequestCtx available anywhere in the async call stack without explicit passing.

!!! info "Source Reference"
    Lines 24-40 in `base.py`: ContextVar-based request context management with `_CURRENT_REQUEST_CTX` for thread-safe, async-aware context propagation.


### _CURRENT_REQUEST_CTX

```python
_CURRENT_REQUEST_CTX: ContextVar["RequestCtx | None"] = ContextVar(
    "aquilia_controller_request_ctx",
    default=None
)
```

Global ContextVar that holds the current request context for the active async task.

### _set_current_request_ctx

```python
def _set_current_request_ctx(ctx: RequestCtx) -> Token[RequestCtx | None]
```

Bind the current request context for helper APIs invoked during handler execution. Returns a token for later reset.

!!! info "Source Reference"
    Lines 27-29 in `base.py`: Sets the ContextVar and returns a token for cleanup.


### _reset_current_request_ctx

```python
def _reset_current_request_ctx(token: Token[RequestCtx | None]) -> None
```

Reset the bound request context token (cleanup after request processing).

!!! info "Source Reference"
    Lines 32-34 in `base.py`: Resets the ContextVar to its previous state using the token.


### _get_current_request_ctx

```python
def _get_current_request_ctx() -> RequestCtx | None
```

Get the current request context for the active task, if any. Returns `None` if called outside request context.

!!! info "Source Reference"
    Lines 37-39 in `base.py`: Retrieves the current value from the ContextVar.


**Use Case:**
```python
# Deep in your application code, no need to pass ctx explicitly
def log_user_action(action: str):
    ctx = _get_current_request_ctx()
    if ctx and ctx.identity:
        logger.info(f"User {ctx.identity.id} performed {action}")
```

---

## Code Examples

### Basic Handler Access

```python
from aquilia.controller import Controller, RequestCtx
from aquilia.decorators import GET, POST

class UsersController(Controller):
    prefix = "/users"
    
    @GET("/")
    async def list_users(self, ctx: RequestCtx):
        # Access request properties
        path = ctx.path  # "/users"
        method = ctx.method  # "GET"
        
        # Access query parameters
        page = ctx.query_param("page", "1")
        limit = ctx.query_param("limit", "10")
        
        # Access headers
        user_agent = ctx.headers.get("User-Agent")
        
        return {
            "path": path,
            "method": method,
            "page": page,
            "limit": limit,
        }
```

### Working with Request Body

```python
class UsersController(Controller):
    prefix = "/users"
    
    @POST("/")
    async def create_user(self, ctx: RequestCtx):
        # Parse JSON body
        data = await ctx.json()
        
        # Create user with parsed data
        user = User(
            name=data["name"],
            email=data["email"],
        )
        await self.repo.save(user)
        
        return {"user": user.to_dict()}
    
    @POST("/upload")
    async def upload_avatar(self, ctx: RequestCtx):
        # Handle multipart form data
        form = await ctx.multipart()
        avatar = form.get("avatar")
        
        # Save file
        path = await self.storage.save(avatar)
        
        return {"avatar_url": path}
```

### Authentication and Authorization

```python
from aquilia.auth import Auth

class DashboardController(Controller):
    prefix = "/dashboard"
    pipeline = [Auth.guard()]  # Require authentication
    
    @GET("/")
    async def index(self, ctx: RequestCtx):
        # Access authenticated user
        user_id = ctx.identity.id
        username = ctx.identity.username
        
        # Check custom claims
        if "admin" in ctx.identity.roles:
            # Admin-specific logic
            pass
        
        return {
            "user_id": user_id,
            "username": username,
        }
```

### Session Management

```python
class CartController(Controller):
    prefix = "/cart"
    
    @POST("/add")
    async def add_item(self, ctx: RequestCtx):
        data = await ctx.json()
        
        # Access session
        cart = ctx.session.get("cart", [])
        cart.append({
            "product_id": data["product_id"],
            "quantity": data["quantity"],
        })
        ctx.session["cart"] = cart
        
        return {"cart": cart}
    
    @GET("/")
    async def view_cart(self, ctx: RequestCtx):
        cart = ctx.session.get("cart", [])
        return {"cart": cart}
```

### Using Effects (Managed Resources)

```python
class ProductsController(Controller):
    prefix = "/products"
    
    @GET("/")
    async def list_products(self, ctx: RequestCtx):
        # Get database connection from effect
        db = ctx.get_effect("database")
        
        # Check if cache is available
        if ctx.has_effect("cache"):
            cache = ctx.get_effect("cache")
            cached = await cache.get("products")
            if cached:
                return {"products": cached, "source": "cache"}
        
        # Query database
        products = await db.query("SELECT * FROM products")
        
        return {"products": products, "source": "database"}
```

### Request-scoped State

```python
class TimingInterceptor(Interceptor):
    async def before(self, ctx: RequestCtx):
        # Store timing in request state
        ctx.state["_start_time"] = time.monotonic()
    
    async def after(self, ctx: RequestCtx, result: Any):
        elapsed = time.monotonic() - ctx.state["_start_time"]
        
        # Add timing to response
        if isinstance(result, dict):
            result["_elapsed_ms"] = round(elapsed * 1000, 2)
        
        return result

class APIController(Controller):
    prefix = "/api"
    interceptors = [TimingInterceptor()]
    
    @GET("/data")
    async def get_data(self, ctx: RequestCtx):
        # Access shared state (set by middleware)
        request_id = ctx.state.get("request_id")
        
        return {
            "request_id": request_id,
            "data": "...",
        }
```

### Dynamic Attributes

```python
# Middleware can attach custom attributes
class TracingMiddleware:
    async def __call__(self, request, call_next):
        ctx = _get_current_request_ctx()
        if ctx:
            ctx.trace_id = str(uuid.uuid4())
            ctx.span_id = str(uuid.uuid4())
        
        response = await call_next(request)
        return response

# Handler can access them
class APIController(Controller):
    @GET("/endpoint")
    async def endpoint(self, ctx: RequestCtx):
        # Access custom attributes
        trace_id = getattr(ctx, "trace_id", None)
        span_id = getattr(ctx, "span_id", None)
        
        return {
            "trace_id": trace_id,
            "span_id": span_id,
        }
```

### Dependency Injection Container

```python
class UsersController(Controller):
    prefix = "/users"
    
    def __init__(self, repo: UserRepository):
        self.repo = repo
    
    @GET("/{user_id}")
    async def get_user(self, ctx: RequestCtx, user_id: int):
        # Access DI container if needed
        if ctx.container:
            # Resolve additional dependencies
            cache = ctx.container.resolve("cache")
        
        user = await self.repo.find(user_id)
        return {"user": user}
```

### ContextVar Usage

```python
# Utility function that doesn't receive ctx explicitly
def get_current_user_id() -> int | None:
    ctx = _get_current_request_ctx()
    if ctx and ctx.identity:
        return ctx.identity.id
    return None

# Can be called from anywhere in the call stack
class AuditLogger:
    def log(self, action: str):
        user_id = get_current_user_id()
        logger.info(f"User {user_id} performed {action}")

# Handler
class UsersController(Controller):
    def __init__(self, audit: AuditLogger):
        self.audit = audit
    
    @POST("/{user_id}/delete")
    async def delete_user(self, ctx: RequestCtx, user_id: int):
        await self.repo.delete(user_id)
        
        # Audit logger automatically gets user from context
        self.audit.log(f"delete_user:{user_id}")
        
        return {"deleted": user_id}
```
