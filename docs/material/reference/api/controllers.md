# Controllers

The controller system is the heart of Aquilia's HTTP API layer. Controllers are class-based request handlers with declarative route decorators, validation, pagination, filtering, content negotiation, and OpenAPI generation.

## Controller Base Class

```python
class Controller(metaclass=_ControllerMeta):
    """
    Base Controller class.

    Controllers are class-based request handlers with:
    - Constructor DI injection
    - Method-level route definitions
    - Class-level and method-level pipelines
    - Lifecycle hooks
    - Template rendering support
    - API versioning
    - Rate limiting (throttle)
    - Interceptors (before/after handler hooks)
    - Exception filters (structured error handling)
    - Handler execution timeouts
    """
```

### Class Attributes

| Attribute | Type | Default | Description |
|---|---|---|---|
| `prefix` | `str` | `""` | URL prefix for all routes (e.g. `"/users"`) |
| `pipeline` | `list[Any]` | `[]` | Pipeline nodes applied to all methods |
| `tags` | `list[str]` | `[]` | OpenAPI tags |
| `instantiation_mode` | `str` | `"per_request"` | `"per_request"` or `"singleton"` |
| `version` | `str \| None` | `None` | API version string (e.g. `"v1"`, `"v2"`) |
| `throttle` | `Throttle \| None` | `None` | Rate limiting instance |
| `interceptors` | `list[Any]` | `[]` | `Interceptor` instances |
| `exception_filters` | `list[Any]` | `[]` | `ExceptionFilter` instances |
| `timeout` | `float` | `0` | Handler timeout in seconds (0 = disabled) |
| `max_body_size` | `int` | `0` | Max body size in bytes (0 = no limit) |

### Lifecycle Hooks

```python
async def on_startup(self, ctx: RequestCtx) -> None:
    """Called when controller is initialized (singleton mode only)."""

async def on_shutdown(self, ctx: RequestCtx) -> None:
    """Called when controller is destroyed (singleton mode only)."""

async def on_request(self, ctx: RequestCtx) -> None:
    """Called before each request is processed."""

async def on_response(self, ctx: RequestCtx, response: Response) -> Response:
    """Called after each request is processed. Can modify the response."""
    return response
```

### Template Rendering

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

Convenience method for rendering templates. Automatically injects request context (request, session, identity) into the template variables.

### Example

```python
from aquilia import Controller, GET, RequestCtx, Response

class UsersController(Controller):
    prefix = "/users"
    version = "v1"
    pipeline = [Auth.guard()]
    throttle = Throttle(limit=100, window=60)
    timeout = 30

    def __init__(self, repo: UserRepo, templates: TemplateEngine):
        self.repo = repo
        self.templates = templates

    @GET("/")
    async def list_users(self, ctx: RequestCtx):
        users = await self.repo.list_all()
        return Response.json({"users": users})

    @GET("/{id:int}")
    async def get_user(self, ctx: RequestCtx, id: int):
        user = await self.repo.get_by_id(id)
        if not user:
            raise NotFoundFault(detail=f"User {id} not found")
        return await self.render("users/profile.html", {"user": user}, ctx)
```

---

## RequestCtx

```python
class RequestCtx:
    """
    Request context provided to controller methods.

    Uses __slots__ for compact memory layout and faster attribute access.
    Pooled via _RequestCtxPool to eliminate per-request heap allocation.
    """

    __slots__ = ("request", "identity", "session", "auth", "container", "state", "request_id", "_extra")

    def __init__(
        self,
        request: Request,
        identity: Optional[Identity] = None,
        session: Optional[Session] = None,
        auth: Any | None = None,
        container: Any | None = None,
        state: dict[str, Any] | None = None,
        request_id: str | None = None,
    ):
```

### Properties

| Property | Return Type | Description |
|---|---|---|
| `path` | `str` | Request path |
| `method` | `str` | HTTP method |
| `headers` | `Headers` | Request headers |
| `query_params` | `MultiDict` | Parsed query parameters |

### Methods

```python
def query_param(self, key: str, default: str | None = None) -> str | None:
    """Get single query parameter."""

async def json(self) -> Any:
    """Parse request body as JSON."""

async def body(self) -> bytes:
    """Read raw request body bytes."""

async def form(self) -> FormData:
    """Parse request body as form data."""

async def multipart(self):
    """Parse multipart/form-data (file uploads)."""
```

### Object Pooling

`_RequestCtxPool` is a lock-free object pool with `max_size=256` that recycles RequestCtx instances to eliminate per-request heap allocation:

```python
class _RequestCtxPool:
    def __init__(self, max_size: int = 256):

    def acquire(self, request, identity=None, session=None, auth=None,
                container=None, state=None, request_id=None) -> RequestCtx:

    def release(self, ctx: RequestCtx) -> None:
```

!!! note "request_id"
    If `request_id` is `None` when acquiring, a fresh `os.urandom(16).hex()` ID is generated to ensure reused contexts never carry a stale ID.

---

## Interceptor

```python
class Interceptor:
    """
    Base class for controller interceptors.

    Interceptors wrap handler execution with before/after logic.
    """

    async def before(self, ctx: RequestCtx) -> Optional[Response]:
        """Called before the handler. Return a Response to short-circuit."""
        return None

    async def after(self, ctx: RequestCtx, result: Any) -> Any:
        """Called after the handler. Receives and can transform the result."""
        return result
```

### Example

```python
class TimingInterceptor(Interceptor):
    async def before(self, ctx):
        ctx.state["_start"] = time.monotonic()

    async def after(self, ctx, result):
        elapsed = time.monotonic() - ctx.state["_start"]
        if isinstance(result, dict):
            result["_elapsed_ms"] = round(elapsed * 1000, 2)
        return result

class UsersController(Controller):
    prefix = "/users"
    interceptors = [TimingInterceptor()]
```

---

## ExceptionFilter

```python
class ExceptionFilter:
    """
    Base class for exception filters.

    Exception filters intercept unhandled exceptions from controller
    handlers and convert them into proper HTTP responses.
    """

    catches: list[type] = []  # Exception types this filter handles

    async def catch(self, exception: Exception, ctx: RequestCtx) -> Optional[Response]:
        """Handle the exception and return a Response. Return None to propagate."""
        raise NotImplementedError
```

### Example

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

## Throttle

```python
class Throttle:
    """
    Simple in-memory sliding-window rate limiter.
    """

    def __init__(self, limit: int = 100, window: int = 60, max_clients: int = 10000):
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `limit` | `int` | `100` | Max requests per window |
| `window` | `int` | `60` | Window size in seconds |
| `max_clients` | `int` | `10000` | Max tracked clients (LRU eviction beyond this) |

```python
def check(self, request: Any) -> bool:
    """Check if request is within rate limit. Returns True if allowed."""

@property
def retry_after(self) -> int:
    """Seconds until the window resets."""

def reset(self):
    """Clear all rate limit state."""
```

---

## Route Decorators

All HTTP method decorators extend `RouteDecorator` and attach metadata to controller methods at import time.

### `RouteDecorator` (base)

```python
class RouteDecorator:
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

### HTTP Method Decorators

The following decorators are available. All accept the same keyword arguments as `RouteDecorator`:

| Decorator | HTTP Method | Path Default |
|---|---|---|
| `@GET(path, **opts)` | GET | Derived from method name |
| `@POST(path, **opts)` | POST | Derived from method name |
| `@PUT(path, **opts)` | PUT | Derived from method name |
| `@PATCH(path, **opts)` | PATCH | Derived from method name |
| `@DELETE(path, **opts)` | DELETE | Derived from method name |
| `@HEAD(path, **opts)` | HEAD | Derived from method name |
| `@OPTIONS(path, **opts)` | OPTIONS | Derived from method name |
| `@TRACE(path, **opts)` | TRACE | Derived from method name |
| `@WS(path, **opts)` | WS (WebSocket) | Derived from method name |

### `@route()` — Generic Decorator

```python
def route(
    method: str | list[str],
    path: str | None = None,
    *,
    pipeline: list[Any] | None = None,
    ...
) -> Callable[[F], F]:
```

Supports specifying a method string or list of methods:

```python
@route("GET", "/users")
async def get_users(self, ctx): ...

@route(["GET", "POST"], "/items")
async def handle_items(self, ctx): ...
```

Valid HTTP methods are: `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `HEAD`, `OPTIONS`, `TRACE`, `WS`.

### Decorator Metadata

Each decorated method receives `__route_metadata__` — a list of dicts with:

```python
{
    "http_method": "GET",
    "path": "/",
    "pipeline": [...],
    "summary": "List Users",
    "description": "...",
    "tags": ["users"],
    "deprecated": False,
    "response_model": None,
    "status_code": 200,
    "request_blueprint": None,
    "response_blueprint": None,
    "filterset_class": None,
    "filterset_fields": None,
    "search_fields": None,
    "ordering_fields": None,
    "pagination_class": None,
    "renderer_classes": None,
    "throttle": None,
    "timeout": None,
    "version": None,
    "func_name": "list_users",
    "signature": <inspect.Signature>,
}
```

Version-specific routes also receive `__version_metadata__`:

```python
func.__version_metadata__ = {"versions": ["1.0", "2.0"]}
```

---

## ControllerRouter

```python
class ControllerRouter:
    """
    Router for controller-based routes using pattern matching.

    Two-tier architecture for maximum performance:
    1. Static route hash map: O(1) lookup for routes with no parameters
    2. Trie + regex fallback: O(k) for parameterized routes
    """
```

### Methods

```python
def __init__(self):
    self.compiled_controllers: list[CompiledController]
    self.routes_by_method: dict[str, list[CompiledRoute]]
    self.matcher: PatternMatcher

def add_controller(self, compiled_controller: CompiledController):
    """Add a compiled controller to the router."""

def initialize(self):
    """Build fast-path lookup structures including segment trie."""

def match_sync(
    self,
    path: str,
    method: str,
    query_params: dict[str, str] | None = None,
    api_version: Any | None = None,
) -> ControllerRouteMatch | None:
    """Synchronous route matching — the hot path."""

async def match(
    self,
    path: str,
    method: str,
    query_params: dict[str, str] | None = None,
    api_version: Any | None = None,
) -> ControllerRouteMatch | None:
    """Async compat wrapper — delegates to sync hot path."""

def get_allowed_methods(self, path: str) -> list[str]:
    """Return HTTP methods registered for a path. Used for 405 responses."""

def get_routes(self) -> list[dict[str, Any]]:
    """Get all registered routes as dicts."""

def get_routes_full(self) -> list[CompiledRoute]:
    """Get all CompiledRoute objects."""

def get_controller(self, name: str) -> CompiledController | None:
    """Get compiled controller by name."""

def has_route(self, method: str, path: str) -> bool:
    """Check if a route exists."""

def url_for(self, name: str, *, api_version: str | None = None, **params) -> str:
    """Reverse URL generation."""
```

### `ControllerRouteMatch`

```python
@dataclass
class ControllerRouteMatch:
    route: CompiledRoute
    params: dict[str, Any]
    query: dict[str, Any]
```

### Three-Tier Matching Architecture

1. **Static O(1) hash map** — routes with no path parameters or query params
2. **Trie O(k) segment walk** — parameterized routes with simple `{name}`, `<name>`, `<name:type>` segments
3. **Regex O(n) fallback** — complex patterns (wildcards, regex constraints) the trie cannot represent

Version filtering (`_version_matches()`) is applied after path/method matching and checks:
- Route-level explicit version lists (`@GET(version="2.0")`)
- Route-level version ranges (`@version_range()`)
- Controller-level version strings
- Version-neutral sentinel (`VERSION_NEUTRAL`)

### Segment Trie (`_TrieNode`)

```python
class _TrieNode:
    __slots__ = ("children", "param_child", "param_name", "param_castor", "route", "query_params")

    children: dict[str, _TrieNode]  # static segment → child
    param_child: _TrieNode | None   # single param child
    param_name: str | None          # parameter name
    param_castor: Any | None        # type-cast function
    route: CompiledRoute | None     # terminal node
    query_params: dict | None       # query parameter metadata
```

---

## Validation — `validate_body`

```python
def validate_body(
    blueprint_class: type,
    *,
    projection: str = "__all__",
) -> Any:
    """
    Decorator: parse + validate the request body through a Blueprint.

    On success:  injects ``body: dict`` as the first extra keyword argument.
    On failure:  returns HTTP 422 Unprocessable Entity with structured errors.
    """
```

### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `blueprint_class` | `type` | (required) | The Aquilia Blueprint class to validate against |
| `projection` | `str` | `"__all__"` | Blueprint projection for allowed fields |

### Usage

```python
from aquilia.controller.validation import validate_body

class UsersController(Controller):
    prefix = "/users"

    @POST("/")
    @validate_body(CreateUserBlueprint)
    async def create_user(self, ctx: RequestCtx, body: dict):
        user = await self.user_service.create(**body)
        return Response.json({"id": user.id}, status=201)
```

### Behavior

1. Reads raw body via `ctx.body()`
2. Parses based on `Content-Type`:
    - `application/json` → `json.loads()`
    - `application/x-www-form-urlencoded` / `multipart/form-data` → `ctx.form()`
    - Other → `json.loads()` (fallback)
3. Parse errors return **400** with `RequestBodyParseFault`
4. Blueprint sealing failures return **422** with `RequestBodyValidationFault` and field-level errors
5. On success, injects `body=validated_data` into the handler kwargs

### Fault Classes

```python
class ValidationFault(Fault):
    domain = "validation"
    severity = Severity.WARN

class RequestBodyValidationFault(ValidationFault):
    code = "validation.body_invalid"

class RequestBodyParseFault(ValidationFault):
    code = "validation.body_parse_error"
```

---

## Pagination

Three pagination backends are available, usable either declaratively on route decorators or explicitly in handler code.

### `BasePagination` (abstract)

```python
class BasePagination:
    def paginate_list(self, data: list[Any], request: Any) -> dict[str, Any]:
        raise NotImplementedError

    async def paginate_queryset(self, queryset: Any, request: Any) -> dict[str, Any]:
        """Default: fetch all() then delegate to paginate_list."""
```

### `PageNumberPagination`

```python
class PageNumberPagination(BasePagination):
    page_size: int = 20
    max_page_size: int = 1000
    page_param: str = "page"
    page_size_param: str = "page_size"

    def __init__(self, page_size: int | None = None, max_page_size: int | None = None):
```

**Query params:** `?page=2&page_size=20`

**Response envelope:**

```json
{
    "count": 1200,
    "total_pages": 60,
    "page": 2,
    "page_size": 20,
    "next": "http://host/items/?page=3&page_size=20",
    "previous": "http://host/items/?page=1&page_size=20",
    "results": [...]
}
```

**ORM optimization:** Uses `.count()` + `.offset().limit()` instead of fetching all rows.

### `LimitOffsetPagination`

```python
class LimitOffsetPagination(BasePagination):
    default_limit: int = 20
    max_limit: int = 1000
    limit_param: str = "limit"
    offset_param: str = "offset"

    def __init__(self, default_limit: int | None = None, max_limit: int | None = None):
```

**Query params:** `?limit=20&offset=40`

**Response envelope:**

```json
{
    "count": 1200,
    "limit": 20,
    "offset": 40,
    "next": "http://host/items/?limit=20&offset=60",
    "previous": "http://host/items/?limit=20&offset=20",
    "results": [...]
}
```

### `CursorPagination`

```python
class CursorPagination(BasePagination):
    page_size: int = 20
    max_page_size: int = 1000
    cursor_param: str = "cursor"
    page_size_param: str = "page_size"
    ordering: str = "-id"

    def __init__(self, page_size: int | None = None, ordering: str | None = None):
```

**Query params:** `?cursor=<opaque>&page_size=20`

Cursor tokens are HMAC-SHA256 signed base64 payloads. The signing secret is read from `AQUILIA_CURSOR_SECRET` env var (falls back to a per-process ephemeral key).

**Response envelope:**

```json
{
    "next": "http://host/items/?cursor=abc...",
    "previous": "http://host/items/?cursor=xyz...",
    "results": [...]
}
```

**ORM optimization:** Uses `WHERE` + `ORDER BY` + `LIMIT` for true keyset pagination (constant-time page jumps regardless of dataset size).

Cursor data format (signed):

```python
{"v": <ordering_value>, "d": "next"}  # d = "next" or "prev"
```

### `NoPagination`

```python
class NoPagination(BasePagination):
    """Passthrough — no pagination applied."""
```

Returns all items in the standard envelope with `next` and `previous` as `None`.

### Declarative Usage

```python
@GET("/", pagination_class=PageNumberPagination)
async def list_products(self, ctx):
    return await Product.objects.all()  # engine auto-paginates
```

### Explicit Usage

```python
paginator = PageNumberPagination(page_size=25)
page = paginator.paginate_list(products, ctx.request)
```

---

## Filters

### `FilterSet`

Declarative field-based filtering using query parameters.

```python
class FilterSet(metaclass=FilterSetMeta):
    _filter_fields: ClassVar[dict[str, list[str]]] = {}

    def __init__(self, *, request: Any = None, query_params: dict[str, str] | None = None):

    def parse(self) -> dict[str, Any]:
        """Parse query parameters into filter clauses {field__lookup: value}."""

    def filter_list(self, data: list[Any]) -> list[Any]:
        """Parse + apply to in-memory list."""

    async def filter_queryset(self, queryset: Any) -> Any:
        """Parse + apply to ORM queryset."""
```

### `FilterSetMeta` (metaclass)

Accepts two forms for `Meta.fields`:

**List form** (exact-match only):
```python
class MyFilter(FilterSet):
    class Meta:
        fields = ["status", "created_at"]
```

**Dict form** (explicit lookups per field):
```python
class MyFilter(FilterSet):
    class Meta:
        fields = {
            "status": ["exact", "in"],
            "price": ["gte", "lte", "range"],
            "name": ["icontains"],
        }
```

### Supported Lookup Types

| Lookup | Description | Example Query |
|---|---|---|
| `exact` | Exact match (default) | `?status=active` |
| `iexact` | Case-insensitive exact | `?name__iexact=John` |
| `contains` | Substring match | `?desc__contains=sale` |
| `icontains` | Case-insensitive substring | `?name__icontains=john` |
| `startswith` | Starts with | `?email__startswith=admin` |
| `istartswith` | Case-insensitive starts with | |
| `endswith` | Ends with | |
| `iendswith` | Case-insensitive ends with | |
| `gt` / `gte` | Greater than (or equal) | `?price__gte=10` |
| `lt` / `lte` | Less than (or equal) | `?price__lt=100` |
| `in` | In list (comma-separated) | `?category__in=books,music` |
| `range` | Between two values | `?price__range=10,50` |
| `isnull` | Is null (true/false) | `?deleted_at__isnull=true` |
| `regex` | Regex match | |
| `iregex` | Case-insensitive regex | |
| `ne` | Not equal | |
| `date` | Date portion | |
| `year` | Year extract | `?created_at__year=2024` |
| `month` | Month extract | |
| `day` | Day extract | |

### Custom Filter Methods

```python
class ProductFilter(FilterSet):
    class Meta:
        fields = {"category": ["exact"]}

    def filter_category(self, value: str) -> dict:
        if value == "sale":
            return {"discount__gt": 0}
        return {"category": value}
```

### `SearchFilter`

```python
class SearchFilter(BaseFilterBackend):
    search_param: str = "search"

    def filter_data(self, data, request, *, search_fields=None, **options) -> list:
        """In-memory case-insensitive substring search."""

    async def filter_queryset(self, queryset, request, *, search_fields=None, **options):
        """ORM: builds Q-node OR chain (name__icontains=term | desc__icontains=term)."""
```

**Query parameter:** `?search=<term>`

```python
@GET("/", search_fields=["name", "description", "sku"])
async def list_products(self, ctx): ...
```

### `OrderingFilter`

```python
class OrderingFilter(BaseFilterBackend):
    ordering_param: str = "ordering"

    def filter_data(self, data, request, *, ordering_fields=None, **options) -> list:
        """Sort in-memory list."""

    async def filter_queryset(self, queryset, request, *, ordering_fields=None, **options):
        """ORM: qs.order(*ordering)."""
```

**Query parameter:** `?ordering=-price,name` (prefix `-` for descending)

```python
@GET("/", ordering_fields=["price", "created_at", "name"])
async def list_products(self, ctx): ...
```

### `BaseFilterBackend` (for custom backends)

```python
class BaseFilterBackend:
    def filter_data(self, data: list[Any], request: Any, **options) -> list[Any]:
        return data

    async def filter_queryset(self, queryset: Any, request: Any, **options) -> Any:
        return queryset
```

### Convenience Functions

```python
async def filter_queryset(
    queryset, request, *,
    filterset_class=None, filterset_fields=None,
    search_fields=None, ordering_fields=None,
) -> Any:
    """One-shot: apply FilterSet + SearchFilter + OrderingFilter to ORM queryset."""

def filter_data(
    data, request, *,
    filterset_class=None, filterset_fields=None,
    search_fields=None, ordering_fields=None,
) -> list[Any]:
    """One-shot: apply FilterSet + SearchFilter + OrderingFilter to in-memory list."""
```

---

## Renderers

Content negotiation based on the `Accept` header with a pluggable renderer architecture.

### `BaseRenderer` (abstract)

```python
class BaseRenderer:
    media_type: str = "application/octet-stream"
    format_suffix: str = ""  # e.g. "json", "xml"
    charset: str | None = "utf-8"

    def render(self, data: Any, *, request=None, response_status=200,
               response_headers=None) -> str | bytes:
        raise NotImplementedError
```

### Built-in Renderers

| Renderer | Media Type | Format Suffix |
|---|---|---|
| `JSONRenderer` | `application/json` | `json` |
| `XMLRenderer` | `application/xml` | `xml` |
| `YAMLRenderer` | `application/x-yaml` | `yaml` |
| `PlainTextRenderer` | `text/plain` | `text` |
| `HTMLRenderer` | `text/html` | `html` |
| `MessagePackRenderer` | `application/msgpack` | `msgpack` |

### `JSONRenderer`

```python
class JSONRenderer(BaseRenderer):
    media_type = "application/json"
    format_suffix = "json"

    def __init__(self, *, indent: int | None = None, ensure_ascii: bool = False):
```

Uses `orjson` if available, falls back to `ujson`, then `json` stdlib. Handles `set`, `tuple`, `datetime` (isoformat), `to_dict()` objects, and `__dict__` objects.

### `XMLRenderer`

```python
class XMLRenderer(BaseRenderer):
    media_type = "application/xml"
    format_suffix = "xml"

    def __init__(self, *, root_tag: str = "response", item_tag: str = "item"):
```

### `YAMLRenderer`

```python
class YAMLRenderer(BaseRenderer):
    media_type = "application/x-yaml"
    format_suffix = "yaml"
```

Uses `pyyaml` if available; falls back to a minimal built-in YAML formatter.

### `ContentNegotiator`

```python
class ContentNegotiator:
    def __init__(self, renderers: Sequence[BaseRenderer] | None = None):

    def select_renderer(self, request: Any) -> tuple[BaseRenderer, str]:
        """Return (renderer_instance, media_type) for the request."""
```

**Resolution order:**
1. `?format=json` → pick renderer whose `format_suffix` matches
2. `Accept` header negotiation (quality-weighted)
3. First renderer (default)

### Convenience Function

```python
def negotiate(
    data: Any,
    request: Any,
    *,
    renderers: Sequence[BaseRenderer] | None = None,
    status: int = 200,
    headers: dict[str, str] | None = None,
) -> tuple[str | bytes, str, int]:
    """One-shot content negotiation. Returns (body, content_type, status_code)."""
```

---

## OpenAPI

```python
class OpenAPIGenerator:
    """
    Production-grade OpenAPI 3.1.0 specification generator.
    """

    def __init__(
        self,
        title: str = "Aquilia API",
        version: str = "1.0.0",
        config: OpenAPIConfig | None = None,
    ):

    def generate(self, router: ControllerRouter) -> dict[str, Any]:
        """Generate the full OpenAPI 3.1.0 specification."""
```

### `OpenAPIConfig`

```python
@dataclass
class OpenAPIConfig:
    title: str = "Aquilia API"
    version: str = "1.0.0"
    description: str = ""
    terms_of_service: str = ""
    contact_name: str = ""
    contact_email: str = ""
    contact_url: str = ""
    license_name: str = ""
    license_url: str = ""
    servers: list[dict[str, str]] = field(default_factory=list)
    docs_path: str = "/docs"
    openapi_json_path: str = "/openapi.json"
    redoc_path: str = "/redoc"
    include_internal: bool = False
    group_by_module: bool = True
    infer_request_body: bool = True
    infer_responses: bool = True
    detect_security: bool = True
    external_docs_url: str = ""
    external_docs_description: str = ""
    swagger_ui_theme: str = ""
    swagger_ui_config: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
```

### Security Scheme Detection

Auto-detects from pipeline guards:
- `oauth` / `oauth2` → OAuth2 flow definition
- `apikey` → API key auth (`X-API-Key` header)
- `authguard` / `auth` → Bearer JWT

### Request Body Inference (4 strategies)

1. **ParameterMetadata** with `source="body"` — from route metadata
2. **Annotated body params** — `Annotated[UserInput, Body(...)]` type hints
3. **Docstring parsing** — `Body: {"field": "example"}` pattern
4. **Source analysis** — detects `ctx.json()` or `ctx.form()` calls

### Response Inference

- From `response_model` attribute
- From handler source analysis (`Response.json()`, `Response.html()`, `self.render()`, `Response.text()`)
- Error responses from docstring `Raises:` sections
- Status codes from source patterns like `status=403`

### Swagger UI and ReDoc

```python
def generate_swagger_html(config: OpenAPIConfig) -> str:
    """Generate the Swagger UI HTML page."""

def generate_redoc_html(config: OpenAPIConfig) -> str:
    """Generate the ReDoc HTML page."""
```

Swagger UI uses v5.18.2 from CDN. Theme support: `"dark"`, `"monokai"`.

---

## Metadata

Used for static analysis during `aq compile`.

### `ControllerMetadata`

```python
@dataclass
class ControllerMetadata:
    class_name: str
    module_path: str
    prefix: str
    routes: list[RouteMetadata] = field(default_factory=list)
    pipeline: list[Any] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    instantiation_mode: str = "per_request"
    constructor_params: list[ParameterMetadata] = field(default_factory=list)
    version: Any | None = None

    def get_route(self, method: str, path: str) -> RouteMetadata | None: ...
    def has_conflict(self, other: ControllerMetadata) -> tuple | None: ...
```

### `RouteMetadata`

```python
@dataclass
class RouteMetadata:
    http_method: str
    path_template: str
    full_path: str
    handler_name: str
    parameters: list[ParameterMetadata] = field(default_factory=list)
    pipeline: list[Any] = field(default_factory=list)
    summary: str = ""
    description: str = ""
    tags: list[str] = field(default_factory=list)
    deprecated: bool = False
    response_model: type | None = None
    status_code: int = 200
    specificity: int = 0
    version: Any | None = None

    def compute_specificity(self) -> int:
        """Score: static(100) > typed param(50) > untyped param(25) > wildcard(1)"""
```

### `ParameterMetadata`

```python
@dataclass
class ParameterMetadata:
    name: str
    type: type
    default: Any = inspect.Parameter.empty
    source: str = "query"  # "path", "query", "body", "header", "di", "dep"
    required: bool = True
    pattern: str | None = None

    @property
    def has_default(self) -> bool: ...
```

### Source Inference

Parameter source is determined automatically:
- Path params → `"path"`
- Blueprint subclass types → `"body"`
- `Inject`/`Dep` annotations → `"di"` / `"dep"`
- `dict` generics → `"body"`
- `Session`/`Identity` types → `"di"`
- Other → `"query"`

### Extraction Function

```python
def extract_controller_metadata(
    controller_class: type,
    module_path: str,
) -> ControllerMetadata:
    """Extract metadata from a Controller class without executing business logic."""
```