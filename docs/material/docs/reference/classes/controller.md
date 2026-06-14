# Controller

## Overview

The `Controller` is the primary class-based abstraction for handling HTTP requests in Aquilia. Controllers are declared in module manifests, discovered automatically at boot, and instantiated via the DI container.

```python
from aquilia import Controller, GET, POST, RequestCtx, Response

class UsersController(Controller):
    prefix = "/users"
    tags = ["users"]

    @GET("/")
    async def list_users(self, ctx: RequestCtx):
        return Response.json({"users": []})
```

---

## `Controller` Base Class

!!! abstract "`aquilia.controller.Controller`"
    Metaclass: `_ControllerMeta` (ensures `pipeline`, `tags`, `interceptors`, `exception_filters` are deep-copied per subclass).

### Class Attributes

| Attribute | Type | Default | Description |
|---|---|---|---|
| `prefix` | `str` | `""` | URL prefix for all routes (e.g. `"/users"`) |
| `pipeline` | `list[Any]` | `[]` | Flow nodes applied to all methods |
| `tags` | `list[str]` | `[]` | OpenAPI tags |
| `instantiation_mode` | `str` | `"per_request"` | `"per_request"` or `"singleton"` |
| `version` | `str \| None` | `None` | API version (`"v1"`, `"v2"`) |
| `throttle` | `Throttle \| None` | `None` | Rate limiting instance |
| `interceptors` | `list[Any]` | `[]` | `Interceptor` instances |
| `exception_filters` | `list[Any]` | `[]` | `ExceptionFilter` instances |
| `timeout` | `float` | `0` | Handler timeout in seconds (0 = disabled) |
| `max_body_size` | `int` | `0` | Max request body size in bytes (0 = disabled) |

### Constructor DI

Constructor parameters are resolved from the DI container automatically:

```python
class UsersController(Controller):
    prefix = "/users"

    def __init__(self, repo: UserRepo, templates: TemplateEngine):
        self.repo = repo
        self.templates = templates
```

### Render Helper

```python
async def render(
    self,
    template_name: str,
    context: dict[str, Any] | None = None,
    request_ctx: RequestCtx | None = None,
    *,
    engine: Any | None = None,
    status: int = 200,
    headers: dict[str, str] | None = None,
) -> Response:
```

### Lifecycle Hooks

```python
async def on_startup(self, ctx: RequestCtx) -> None: ...
async def on_shutdown(self, ctx: RequestCtx) -> None: ...
async def on_request(self, ctx: RequestCtx) -> None: ...
async def on_response(self, ctx: RequestCtx, response: Response) -> Response: ...
```

### Context Manager Support

```python
async def __aenter__(self): ...
async def __aexit__(self, exc_type, exc_val, exc_tb): ...
```

---

## `RequestCtx`

!!! abstract "`aquilia.controller.RequestCtx`"

The request context passed to every controller method. Uses `__slots__` for performance; instances are pooled and recycled.

### Constructor

```python
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

### Properties

| Property | Type | Description |
|---|---|---|
| `request` | `Request` | The current request |
| `identity` | `Identity \| None` | Authenticated identity |
| `session` | `Session \| None` | Current session |
| `auth` | `Any \| None` | Auth data |
| `container` | `Any \| None` | Request-scoped DI container |
| `state` | `dict[str, Any]` | Arbitrary state dict |
| `request_id` | `str \| None` | Unique request ID |
| `path` | `str` | Request path (delegates to `request.path`) |
| `method` | `str` | Request method (delegates to `request.method`) |
| `headers` | `Headers` | Request headers |
| `query_params` | `MultiDict` | Parsed query string params |

### Methods

```python
def query_param(self, key: str, default: str | None = None) -> str | None: ...
async def json(self) -> Any: ...
async def body(self) -> bytes: ...
async def form(self) -> FormData: ...
async def multipart(self): ...
```

### Dynamic Attributes (`_extra`)

Middleware/plugins can set arbitrary attributes:

```python
ctx.my_custom_attr = "value"    # stored in _extra dict
print(ctx.my_custom_attr)       # __getattr__ fallback
```

---

## Route Decorators

All decorators extend `RouteDecorator` and attach metadata (`__route_metadata__`, `__version_metadata__`) for compile-time extraction. The `@route()` generic decorator accepts a `method` string or list.

### Base Signature (`RouteDecorator`)

```python
def __init__(
    self,
    path: str | None = None,
    *,
    method: str | None = None,
    pipeline: list[Any] | None = None,
    summary: str | None = None,
    description: str | None = None,
    tags: list[str] | None = None,
    deprecated: bool = False,
    response_model: type | None = None,
    status_code: int = 200,
    request_blueprint: type | None = None,
    response_blueprint: type | None = None,
    filterset_class: type | None = None,
    filterset_fields: list[str] | Any | None = None,
    search_fields: list[str] | None = None,
    ordering_fields: list[str] | None = None,
    pagination_class: type | None = None,
    renderer_classes: list[Any] | None = None,
    throttle: Any | None = None,
    timeout: float | None = None,
    version: str | list[str] | None = None,
):
```

### `@GET`

```python
class GET(RouteDecorator):
    def __init__(
        self,
        path: str | None = None,
        *,
        pipeline: list[Any] | None = None,
        summary: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        deprecated: bool = False,
        response_model: type | None = None,
        status_code: int = 200,
        request_blueprint: type | None = None,
        response_blueprint: type | None = None,
        filterset_class: type | None = None,
        filterset_fields: list[str] | Any | None = None,
        search_fields: list[str] | None = None,
        ordering_fields: list[str] | None = None,
        pagination_class: type | None = None,
        renderer_classes: list[Any] | None = None,
        throttle: Any | None = None,
        timeout: float | None = None,
        version: str | list[str] | None = None,
    ):
```

### `@POST` / `@PUT` / `@PATCH` / `@DELETE` / `@HEAD` / `@OPTIONS` / `@TRACE` / `@WS`

All have identical signatures to `@GET`, differing only in the `method` parameter set internally.

### `@route()` Generic Decorator

```python
def route(
    method: str | list[str],
    path: str | None = None,
    *,
    pipeline: list[Any] | None = None,
    summary: str | None = None,
    description: str | None = None,
    tags: list[str] | None = None,
    deprecated: bool = False,
    response_model: type | None = None,
    status_code: int = 200,
    request_blueprint: type | None = None,
    response_blueprint: type | None = None,
    filterset_class: type | None = None,
    filterset_fields: list[str] | Any | None = None,
    search_fields: list[str] | None = None,
    ordering_fields: list[str] | None = None,
    pagination_class: type | None = None,
    renderer_classes: list[Any] | None = None,
    throttle: Any | None = None,
    timeout: float | None = None,
    version: str | list[str] | None = None,
) -> Callable[[F], F]:
```

Example:
```python
@route(["GET", "POST"], "/items")
async def handle_items(self, ctx):
    ...
```

| Parameter | Type | Description |
|---|---|---|
| `path` | `str \| None` | URL path template (`"/"`, `"/{id:int}"`). `None` = derive from method name |
| `pipeline` | `list[Any] \| None` | Method-level pipeline (overrides class-level) |
| `summary` | `str \| None` | OpenAPI summary |
| `description` | `str \| None` | OpenAPI description |
| `tags` | `list[str] \| None` | OpenAPI tags (extends class-level) |
| `deprecated` | `bool` | Mark deprecated in OpenAPI |
| `response_model` | `type \| None` | Response schema for OpenAPI |
| `status_code` | `int` | Default status code |
| `request_blueprint` | `type \| None` | Blueprint class for request body casting/sealing |
| `response_blueprint` | `type \| None` | Blueprint class or `ProjectedRef` for response molding |
| `filterset_class` | `type \| None` | `FilterSet` subclass |
| `filterset_fields` | `list[str] \| Any \| None` | Field names for exact-match filtering |
| `search_fields` | `list[str] \| None` | Fields for text search (`?search=term`) |
| `ordering_fields` | `list[str] \| None` | Fields for ordering (`?ordering=field`) |
| `pagination_class` | `type \| None` | Pagination backend |
| `renderer_classes` | `list[Any] \| None` | Content negotiation renderers |
| `throttle` | `Any \| None` | Per-route `Throttle` override |
| `timeout` | `float \| None` | Per-route timeout in seconds |
| `version` | `str \| list[str] \| None` | API version binding |

---

## `@validate_body`

!!! abstract "`aquilia.controller.validation.validate_body`"

```python
def validate_body(blueprint_class: type, *, projection: str = "__all__") -> Any:
```

Parses + validates the request body through a Blueprint. On success, injects `body: dict` as a keyword argument. On failure, returns HTTP 422 with structured errors.

```python
from aquilia.controller.validation import validate_body

@POST("/")
@validate_body(CreateUserBlueprint)
async def create_user(self, ctx: RequestCtx, body: dict):
    user = await self.user_service.create(**body)
    return Response.json({"id": user.id}, status=201)
```

---

## `Throttle`

!!! abstract "`aquilia.controller.Throttle`"

In-memory sliding-window rate limiter.

```python
class Throttle:
    def __init__(self, limit: int = 100, window: int = 60, max_clients: int = 10000):
        self.limit = limit
        self.window = window
        self.max_clients = max_clients
        self.retry_after: int  # seconds until window resets

    def check(self, request: Any) -> bool: ...  # True = allowed
    def reset(self) -> None: ...                 # clear all state
```

Usage:

```python
class UsersController(Controller):
    throttle = Throttle(limit=100, window=60)  # 100 req / 60s

    @GET("/", throttle=Throttle(limit=10, window=60))
    async def list(self, ctx): ...
```

---

## `Interceptor`

!!! abstract "`aquilia.controller.Interceptor`"

Before/after hooks wrapping handler execution.

```python
class Interceptor:
    async def before(self, ctx: RequestCtx) -> Response | None:
        """Return Response to short-circuit. Return None to continue."""
        return None

    async def after(self, ctx: RequestCtx, result: Any) -> Any:
        """Transform the handler result."""
        return result
```

```python
class TimingInterceptor(Interceptor):
    async def before(self, ctx):
        ctx.state["_start"] = time.monotonic()

    async def after(self, ctx, result):
        elapsed = time.monotonic() - ctx.state["_start"]
        if isinstance(result, dict):
            result["_elapsed_ms"] = round(elapsed * 1000, 2)
        return result
```

---

## `ExceptionFilter`

!!! abstract "`aquilia.controller.ExceptionFilter`"

Catches unhandled exceptions and converts them to HTTP responses.

```python
class ExceptionFilter:
    catches: list[type] = []

    async def catch(self, exception: Exception, ctx: RequestCtx) -> Response | None:
        """Return a Response, or None to propagate."""
        raise NotImplementedError
```

```python
class NotFoundFilter(ExceptionFilter):
    catches = [KeyError, LookupError]

    async def catch(self, exception, ctx):
        return Response.json(
            {"error": "Not found", "detail": str(exception)},
            status=404,
        )

class UsersController(Controller):
    exception_filters = [NotFoundFilter()]
```

---

## Full Example

```python
from aquilia import Controller, GET, POST, DELETE, RequestCtx, Response
from aquilia.controller.validation import validate_body
from aquilia.controller.pagination import PageNumberPagination
from aquilia.controller.filters import SearchFilter, OrderingFilter

class UserCreateBlueprint(Blueprint):
    class Spec:
        model = User
        fields = ["name", "email"]
        projections = {"default": ["name", "email"]}

class UserResponseBlueprint(Blueprint):
    class Spec:
        model = User
        projections = {
            "summary": ["id", "name", "email", "active"],
        }

class UsersController(Controller):
    prefix = "/users"
    tags = ["users"]
    version = "v1"
    throttle = Throttle(limit=100, window=60)
    interceptors = [TimingInterceptor()]
    exception_filters = [NotFoundFilter()]

    def __init__(self, user_service: UserService):
        self.user_service = user_service

    @GET("/", pagination_class=PageNumberPagination,
          search_fields=["name", "email"],
          ordering_fields=["name", "created_at"],
          response_blueprint=UserResponseBlueprint["summary"])
    async def list(self, ctx: RequestCtx):
        users = await self.user_service.list_all()
        return users

    @POST("/", request_blueprint=UserCreateBlueprint,
           response_blueprint=UserResponseBlueprint["summary"])
    @validate_body(UserCreateBlueprint)
    async def create(self, ctx: RequestCtx, body: dict):
        user = await self.user_service.create(**body)
        return Response.json(user, status=201)

    @GET("/{id:int}", response_blueprint=UserResponseBlueprint["summary"])
    async def retrieve(self, ctx: RequestCtx, id: int):
        user = await self.user_service.get(id)
        return user

    @DELETE("/{id:int}")
    async def remove(self, ctx: RequestCtx, id: int):
        await self.user_service.delete(id)
        return Response.json({}, status=204)
```