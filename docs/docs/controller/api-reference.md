---
title: "Controller API Reference"
description: "Comprehensive reference of all public symbols exported by the aquilia.controller module."
icon: lucide/terminal
---
This page documents all public symbols exported by the [aquilia.controller](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/__init__.py) module.

---

## Base Architecture

### [Controller](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/base.py#L497-L662)

Base Controller class. Replaces function-based handlers with class-based routing, lifecycle hooks, and dependency injection.

```python
class Controller(metaclass=_ControllerMeta):
    prefix: str = ""
    pipeline: list[Any] = []
    tags: list[str] = []
    instantiation_mode: str = "per_request"
    version: str | None = None
    throttle: Throttle | None = None
    interceptors: list[Any] = []
    exception_filters: list[Any] = []
    timeout: float = 0
    max_body_size: int = 0
```

#### Class Attributes

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `prefix` | `str` | `""` | URL prefix prepended to all routes in this controller. |
| `pipeline` | `list[Any]` | `[]` | List of pipeline nodes applied to all handlers in this controller. |
| `tags` | `list[str]` | `[]` | OpenAPI tags applied to all handlers for API documentation. |
| `instantiation_mode` | `"per_request" \| "singleton"` | `"per_request"` | Governs controller instantiation lifecycle. |
| `version` | `str \| None` | `None` | API version string (e.g., "v1", "v2"). |
| `throttle` | `Throttle \| None` | `None` | Rate limiting configuration applied to this controller. |
| `interceptors` | `list[Any]` | `[]` | List of Interceptor instances to wrap handler execution. |
| `exception_filters` | `list[Any]` | `[]` | List of ExceptionFilter instances to catch unhandled errors. |
| `timeout` | `float` | `0` | Handler execution timeout in seconds (0 = disabled). |
| `max_body_size` | `int` | `0` | Max request body size in bytes (0 = no limit). |


#### Methods

- **`render(self, template_name: str, context: dict[str, Any] | None = None, request_ctx: RequestCtx | None = None, *, engine: Any | None = None, status: int = 200, headers: dict[str, str] | None = None) -> Response`**
  - Renders a template using the template engine and returns a Response.
- **`on_startup(self, ctx: RequestCtx) -> None`**
  - Asynchronous lifecycle hook called when the controller is initialized (singleton mode only).
- **`on_shutdown(self, ctx: RequestCtx) -> None`**
  - Asynchronous lifecycle hook called when the controller is destroyed (singleton mode only).
- **`on_request(self, ctx: RequestCtx) -> None`**
  - Asynchronous lifecycle hook called before each request is processed.
- **`on_response(self, ctx: RequestCtx, response: Response) -> Response`**
  - Asynchronous lifecycle hook called to post-process the response before sending it.

* **Evidence**: [aquilia/controller/base.py:L497-L662](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/base.py#L497-L662)

---

### [RequestCtx](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/base.py#L55-L168)

Request context provided to controller handlers. Uses `__slots__` and object pooling for maximum performance.

```python
class RequestCtx:
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

#### Parameters

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `request` | `Request` |  | The active ASGI request. |
| `identity` | `Optional[Identity]` | `None` | Authenticated user identity (if available). |
| `session` | `Optional[Session]` | `None` | Active session object. |
| `auth` | `Any \| None` | `None` | Parsed auth token or credentials. |
| `container` | `Any \| None` | `None` | Request-scoped Dependency Injection container. |
| `state` | `dict[str, Any] \| None` | `None` | State dictionary for middleware metadata. |
| `request_id` | `str \| None` | `None` | Unique request ID for tracing. |


* **Evidence**: [aquilia/controller/base.py:L55-L168](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/base.py#L55-L168)

---

### [ExceptionFilter](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/base.py#L260-L296)

Base class for exception filters to convert unhandled exceptions into HTTP responses.

```python
class ExceptionFilter:
    catches: list[type] = []

    async def catch(
        self,
        exception: Exception,
        ctx: RequestCtx,
    ) -> Optional[Response]
```

#### Parameters (catch)

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `exception` | `Exception` |  | The exception raised during route handling. |
| `ctx` | `RequestCtx` |  | The active request context. |


* **Returns**: `Optional[Response]` - Return `None` to let the exception propagate, or a `Response` to short-circuit.
* **Evidence**: [aquilia/controller/base.py:L260-L296](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/base.py#L260-L296)

---

### [Interceptor](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/base.py#L303-L348)

Base class for interceptors to wrap handler execution with before/after logic.

```python
class Interceptor:
    async def before(self, ctx: RequestCtx) -> Optional[Response]: ...
    async def after(self, ctx: RequestCtx, result: Any) -> Any: ...
```

* **Evidence**: [aquilia/controller/base.py:L303-L348](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/base.py#L303-L348)

---

### [Throttle](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/base.py#L355-L461)

Simple in-memory sliding-window rate limiter with LRU eviction and expired entry cleanup to prevent memory growth.

```python
class Throttle:
    def __init__(
        self,
        limit: int = 100,
        window: int = 60,
        max_clients: int = 10000,
    )
```

#### Parameters

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `limit` | `int` | `100` | Max requests allowed within the window. |
| `window` | `int` | `60` | Time window in seconds. |
| `max_clients` | `int` | `10000` | Maximum number of client IPs tracked concurrently. |


* **Evidence**: [aquilia/controller/base.py:L355-L461](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/base.py#L355-L461)

---

## Route Decorators

### [GET](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/decorators.py#L180-L227)
### [POST](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/decorators.py#L230-L277)
### [PUT](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/decorators.py#L280-L327)
### [PATCH](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/decorators.py#L330-L377)
### [DELETE](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/decorators.py#L380-L427)
### [HEAD](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/decorators.py#L430-L477)
### [OPTIONS](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/decorators.py#L480-L527)
### [TRACE](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/decorators.py#L530-L577)
### [WS](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/decorators.py#L580-L627)

HTTP and WebSocket decorators for routing controller methods. They attach metadata to handlers without import-time side effects.

```python
# Signature for GET decorator (mirrored across POST, PUT, etc.)
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
    )
```

#### Shared Parameters

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `path` | `str \| None` |  |  |
| `pipeline` | `list[Any] \| None` | `None` | Method-level pipeline nodes (extends class pipeline). |
| `summary` | `str \| None` | `None` | OpenAPI summary. Capitalized method name if None. |
| `description` | `str \| None` | `None` | OpenAPI description. Extracts handler docstring if None. |
| `tags` | `list[str] \| None` | `None` | OpenAPI tags for the route. |
| `deprecated` | `bool` | `False` | Marks route as deprecated in OpenAPI. |
| `response_model` | `type \| None` | `None` | Return model class for OpenAPI schema generation. |
| `status_code` | `int` | `200` | Successful HTTP response code. |
| `request_blueprint` | `type \| None` | `None` | Blueprint class to cast and validate request body. |
| `response_blueprint` | `type \| None` | `None` | Blueprint class to mold response output. |
| `filterset_class` | `type \| None` | `None` | FilterSet class for parsing filters from query parameters. |
| `filterset_fields` | `list[str] \| dict[str, list[str]] \| None` | `None` | Shorthand fields configuration to auto-generate a FilterSet. |
| `search_fields` | `list[str] \| None` | `None` | Fields searched via ?search=<term> parameters. |
| `ordering_fields` | `list[str] \| None` | `None` | Fields orderable via ?ordering=<field> parameters. |
| `pagination_class` | `type \| None` | `None` | Pagination class (e.g. PageNumberPagination). |
| `renderer_classes` | `list[Any] \| None` | `None` | Renderers for Content Negotiation. |
| `throttle` | `Any \| None` | `None` | Per-route throttle limiter. |
| `timeout` | `float \| None` | `None` | Per-route execution timeout in seconds. |
| `version` | `str \| list[str] \| None` | `None` | Version string constraints. |


* **Evidence**: [aquilia/controller/decorators.py:L180-L627](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/decorators.py#L180-L627)

---

### [route](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/decorators.py#L630-L739)

Generic decorator supporting multiple HTTP methods and paths.

```python
def route(
    method: str | list[str],
    path: str | None = None,
    *,
    # ... accepts all keyword arguments from RouteDecorator above
) -> Callable[[F], F]
```

* **Evidence**: [aquilia/controller/decorators.py:L630-L739](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/decorators.py#L630-L739)

---

### [VALID_HTTP_METHODS](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/decorators.py#L15-L27)

Frozenset of valid HTTP/WebSocket method tokens: `{"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "TRACE", "WS"}`.

* **Evidence**: [aquilia/controller/decorators.py:L15-L27](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/decorators.py#L15-L27)

---

## Static Metadata Extraction

### [ParameterMetadata](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/metadata.py#L14-L36)

Dataclass storing parameters extracted during compilation.

```python
@dataclass
class ParameterMetadata:
    name: str
    type: type
    default: Any = inspect.Parameter.empty
    source: str = "query"
    required: bool = True
    pattern: str | None = None
```

* **Evidence**: [aquilia/controller/metadata.py:L14-L36](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/metadata.py#L14-L36)

---

### [RouteMetadata](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/metadata.py#L40-L121)

Introspection metadata for a single route method.

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
```

* **Evidence**: [aquilia/controller/metadata.py:L40-L121](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/metadata.py#L40-L121)

---

### [ControllerMetadata](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/metadata.py#L125-L168)

Introspection metadata for an entire Controller class.

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
```

* **Evidence**: [aquilia/controller/metadata.py:L125-L168](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/metadata.py#L125-L168)

---

### [extract_controller_metadata](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/metadata.py#L171-L242)

Extracts metadata from a Controller class for static analysis compiling without importing runtime dependencies.

```python
def extract_controller_metadata(
    controller_class: type,
    module_path: str,
) -> ControllerMetadata
```

* **Evidence**: [aquilia/controller/metadata.py:L171-L242](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/metadata.py#L171-L242)

---

## Dependency Injection & Assembly Factory

### [InstantiationMode](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L17-L21)

Enum defining the lifecycle instantiation modes.

```python
class InstantiationMode(str, Enum):
    PER_REQUEST = "per_request"
    SINGLETON = "singleton"
```

* **Evidence**: [aquilia/controller/factory.py:L17-L21](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L17-L21)

---

### [ControllerFactory](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L24-L402)

Factory class responsible for instantiating Controller classes, resolving constructor parameters from DI containers, validating scope boundaries, and invoking startup/shutdown lifecycles.

```python
class ControllerFactory:
    def __init__(self, app_container: Any | None = None)
```

#### Methods

- **`create(self, controller_class: type, mode: InstantiationMode = InstantiationMode.PER_REQUEST, request_container: Any | None = None, ctx: Any | None = None) -> Any`**
  - Instantiates a controller class. Raises a `ScopeViolationError` if a singleton controller tries to inject request-scoped dependencies.
- **`validate_scope(self, controller_class: type, mode: InstantiationMode) -> None`**
  - Verifies class provider dependencies to ensure singleton controllers never wrap ephemeral/transient components.
- **`shutdown(self) -> None`**
  - Asynchronously destroys all singletons created by this factory.

* **Evidence**: [aquilia/controller/factory.py:L24-L402](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L24-L402)

---

## Execution Engine

### [ControllerEngine](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/engine.py#L103-L1756)

Runtime execution engine for controllers. Handles route dispatching, dependency parameters binding, rate limiting, and response format serialization.

```python
class ControllerEngine:
    def __init__(
        self,
        factory: ControllerFactory,
        enable_lifecycle: bool = True,
        fault_engine: Any | None = None,
        effect_registry: Any | None = None,
        clearance_engine: Any | None = None,
    )
```

* **Evidence**: [aquilia/controller/engine.py:L103-L1756](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/engine.py#L103-L1756)

---

## Router & Compiler

### [CompiledRoute](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/compiler.py#L28-L52)

Wrapper containing route patterns and static metadata.

```python
@dataclass
class CompiledRoute:
    controller_class: type
    controller_metadata: ControllerMetadata
    route_metadata: RouteMetadata
    compiled_pattern: CompiledPattern
    full_path: str
    http_method: str
    specificity: int
    app_name: str | None = None
    version_metadata: dict[str, Any] | None = None
    bound_version: Any | None = None
```

* **Evidence**: [aquilia/controller/compiler.py:L28-L52](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/compiler.py#L28-L52)

---

### [CompiledController](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/compiler.py#L56-L69)

Fully compiled controller class packaging its routing configurations.

```python
@dataclass
class CompiledController:
    controller_class: type
    metadata: ControllerMetadata
    routes: list[CompiledRoute]
```

* **Evidence**: [aquilia/controller/compiler.py:L56-L69](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/compiler.py#L56-L69)

---

### [ControllerCompiler](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/compiler.py#L72-L611)

Compiles Controllers into optimized executable route specifications.

```python
class ControllerCompiler:
    def __init__(self)
```

#### Methods

- **`compile_controller(self, controller_class: type, base_prefix: str | None = None, version_strategy: Any | None = None, module_versioning: dict[str, Any] | None = None) -> CompiledController`**
  - Compiles route definitions, converting templates to regex patterns.
- **`validate_route_tree(self, compiled_controllers: list[CompiledController]) -> list[dict[str, Any]]`**
  - Audits prefix paths across compiled controllers for collisions.

* **Evidence**: [aquilia/controller/compiler.py:L72-L611](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/compiler.py#L72-L611)

---

### [ControllerRouter](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/router.py#L66-L677)

Pattern-matching route router using O(1) hash maps for static paths and O(k) segment trie/regex searches for dynamic parameters.

```python
class ControllerRouter:
    def __init__(self)
```

#### Methods

- **`add_controller(self, compiled_controller: CompiledController) -> None`**
  - Mounts compiled routes.
- **`initialize(self) -> None`**
  - Optimizes indices for request routing.
- **`match(self, path: str, method: str, query_params: dict[str, str] | None = None, api_version: Any | None = None) -> ControllerRouteMatch | None`**
  - Matches paths to handlers.

* **Evidence**: [aquilia/controller/router.py:L66-L677](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/router.py#L66-L677)

---

## Validation Systems

### [validate_body](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/validation.py#L50-L122)

Decorator: parses and validates request bodies against an Aquilia Blueprint.

```python
def validate_body(
    blueprint_class: type,
    *,
    projection: str = "__all__",
) -> Any
```

* **Evidence**: [aquilia/controller/validation.py:L50-L122](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/validation.py#L50-L122)

---

### [ValidationFault](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/validation.py#L35-L37)

Base class for request data validation errors.

* **Evidence**: [aquilia/controller/validation.py:L35-L37](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/validation.py#L35-L37)

---

### [RequestBodyValidationFault](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/validation.py#L40-L42)

Fault raised when Blueprint constraints fail.

* **Evidence**: [aquilia/controller/validation.py:L40-L42](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/validation.py#L40-L42)

---

## OpenAPI Integration

### [OpenAPIConfig](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L578-L632)

Dataclass configuring OpenAPI 3.1.0 specifications generators.

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

* **Evidence**: [aquilia/controller/openapi.py:L578-L632](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L578-L632)

---

### [OpenAPIGenerator](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L638-L960)

Generates complete OpenAPI 3.1.0 documents.

```python
class OpenAPIGenerator:
    def __init__(
        self,
        title: str = "Aquilia API",
        version: str = "1.0.0",
        config: OpenAPIConfig | None = None,
    )
```

* **Evidence**: [aquilia/controller/openapi.py:L638-L960](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L638-L960)

---

### [generate_swagger_html](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L1027-L1055)

Generates Swagger UI HTML pages.

```python
def generate_swagger_html(config: OpenAPIConfig) -> str
```

* **Evidence**: [aquilia/controller/openapi.py:L1027-L1055](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L1027-L1055)

---

### [generate_redoc_html](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L1084-L1089)

Generates ReDoc HTML pages.

```python
def generate_redoc_html(config: OpenAPIConfig) -> str
```

* **Evidence**: [aquilia/controller/openapi.py:L1084-L1089](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L1084-L1089)

---

## Filtering, Ordering & Search

### [BaseFilterBackend](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/filters.py#L525-L549)

Base class for custom filter backends.

```python
class BaseFilterBackend:
    def filter_data(self, data: list[Any], request: Any, **options: Any) -> list[Any]: ...
    async def filter_queryset(self, queryset: Any, request: Any, **options: Any) -> Any: ...
```

* **Evidence**: [aquilia/controller/filters.py:L525-L549](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/filters.py#L525-L549)

---

### [FilterSetMeta](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/filters.py#L372-L408)

Metaclass collecting declared `Meta.fields` criteria.

* **Evidence**: [aquilia/controller/filters.py:L372-L408](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/filters.py#L372-L408)

---

### [FilterSet](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/filters.py#L411-L517)

Declarative filter parser resolving field lookups from query strings.

```python
class FilterSet(metaclass=FilterSetMeta):
    def __init__(
        self,
        *,
        request: Any = None,
        query_params: dict[str, str] | None = None,
    )
```

* **Evidence**: [aquilia/controller/filters.py:L411-L517](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/filters.py#L411-L517)

---

### [SearchFilter](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/filters.py#L557-L619)

Filter backend applying substring text searches across multiple fields.

```python
class SearchFilter(BaseFilterBackend):
    search_param: str = "search"
```

* **Evidence**: [aquilia/controller/filters.py:L557-L619](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/filters.py#L557-L619)

---

### [OrderingFilter](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/filters.py#L622-L677)

Filter backend sorting results dynamically based on a query parameter.

```python
class OrderingFilter(BaseFilterBackend):
    ordering_param: str = "ordering"
```

* **Evidence**: [aquilia/controller/filters.py:L622-L677](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/filters.py#L622-L677)

---

### [filter_queryset](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/filters.py#L685-L724)

Applies FilterSet, SearchFilter, and OrderingFilter to ORM querysets.

```python
async def filter_queryset(
    queryset: Any,
    request: Any,
    *,
    filterset_class: type[FilterSet] | None = None,
    filterset_fields: list[str] | dict[str, list[str]] | None = None,
    search_fields: list[str] | None = None,
    ordering_fields: list[str] | None = None,
) -> Any
```

* **Evidence**: [aquilia/controller/filters.py:L685-L724](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/filters.py#L685-L724)

---

### [filter_data](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/filters.py#L727-L766)

Applies FilterSet, SearchFilter, and OrderingFilter to lists in memory.

```python
def filter_data(
    data: list[Any],
    request: Any,
    *,
    filterset_class: type[FilterSet] | None = None,
    filterset_fields: list[str] | dict[str, list[str]] | None = None,
    search_fields: list[str] | None = None,
    ordering_fields: list[str] | None = None,
) -> list[Any]
```

* **Evidence**: [aquilia/controller/filters.py:L727-L766](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/filters.py#L727-L766)

---

### [apply_filters_to_list](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/filters.py#L284-L311)

Filters lists by evaluation dictionary matching.

```python
def apply_filters_to_list(
    data: list[Any],
    filters: dict[str, Any],
) -> list[Any]
```

* **Evidence**: [aquilia/controller/filters.py:L284-L311](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/filters.py#L284-L311)

---

### [apply_search_to_list](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/filters.py#L314-L328)

Performs search queries across list dict keys.

```python
def apply_search_to_list(
    data: list[Any],
    search_term: str,
    search_fields: list[str],
) -> list[Any]
```

* **Evidence**: [aquilia/controller/filters.py:L314-L328](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/filters.py#L314-L328)

---

### [apply_ordering_to_list](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/filters.py#L331-L364)

Orders lists based on configuration key directives.

```python
def apply_ordering_to_list(
    data: list[Any],
    ordering: list[str],
) -> list[Any]
```

* **Evidence**: [aquilia/controller/filters.py:L331-L364](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/filters.py#L331-L364)

---

## Pagination Systems

### [BasePagination](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/pagination.py#L104-L137)

Base class for pagination engines.

```python
class BasePagination:
    def paginate_list(self, data: list[Any], request: Any) -> dict[str, Any]: ...
    async def paginate_queryset(self, queryset: Any, request: Any) -> dict[str, Any]: ...
```

* **Evidence**: [aquilia/controller/pagination.py:L104-L137](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/pagination.py#L104-L137)

---

### [NoPagination](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/pagination.py#L140-L149)

Passthrough pagination wrapper.

* **Evidence**: [aquilia/controller/pagination.py:L140-L149](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/pagination.py#L140-L149)

---

### [PageNumberPagination](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/pagination.py#L157-L298)

Standard page numbers pagination resolver.

```python
class PageNumberPagination(BasePagination):
    page_size: int = 20
    max_page_size: int = 1000
    page_param: str = "page"
    page_size_param: str = "page_size"

    def __init__(
        self,
        page_size: int | None = None,
        max_page_size: int | None = None,
    )
```

* **Evidence**: [aquilia/controller/pagination.py:L157-L298](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/pagination.py#L157-L298)

---

### [LimitOffsetPagination](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/pagination.py#L306-L425)

Offset constraints paginator.

```python
class LimitOffsetPagination(BasePagination):
    default_limit: int = 20
    max_limit: int = 1000
    limit_param: str = "limit"
    offset_param: str = "offset"

    def __init__(
        self,
        default_limit: int | None = None,
        max_limit: int | None = None,
    )
```

* **Evidence**: [aquilia/controller/pagination.py:L306-L425](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/pagination.py#L306-L425)

---

### [CursorPagination](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/pagination.py#L433-L675)

Keyset seek-based paginator using signed opaque HMAC base64 cursors for fast paging.

```python
class CursorPagination(BasePagination):
    page_size: int = 20
    max_page_size: int = 1000
    cursor_param: str = "cursor"
    page_size_param: str = "page_size"
    ordering: str = "-id"

    def __init__(
        self,
        page_size: int | None = None,
        ordering: str | None = None,
    )
```

* **Evidence**: [aquilia/controller/pagination.py:L433-L675](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/pagination.py#L433-L675)

---

## Renderers & Content Negotiation

### [BaseRenderer](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/renderers.py#L119-L144)

Base renderer class.

```python
class BaseRenderer:
    media_type: str = "application/octet-stream"
    format_suffix: str = ""
    charset: str | None = "utf-8"

    def render(
        self,
        data: Any,
        *,
        request: Any = None,
        response_status: int = 200,
        response_headers: dict[str, str] | None = None,
    ) -> str | bytes
```

* **Evidence**: [aquilia/controller/renderers.py:L119-L144](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/renderers.py#L119-L144)

---

### [JSONRenderer](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/renderers.py#L152-L179)

Renders responses to JSON formatted strings.

```python
class JSONRenderer(BaseRenderer):
    media_type = "application/json"
    format_suffix = "json"

    def __init__(
        self,
        *,
        indent: int | None = None,
        ensure_ascii: bool = False,
    )
```

* **Evidence**: [aquilia/controller/renderers.py:L152-L179](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/renderers.py#L152-L179)

---

### [XMLRenderer](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/renderers.py#L187-L228)

Renders dictionary structures into valid XML outputs.

```python
class XMLRenderer(BaseRenderer):
    media_type = "application/xml"
    format_suffix = "xml"

    def __init__(
        self,
        *,
        root_tag: str = "response",
        item_tag: str = "item",
    )
```

* **Evidence**: [aquilia/controller/renderers.py:L187-L228](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/renderers.py#L187-L228)

---

### [YAMLRenderer](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/renderers.py#L246-L289)

Renders structures into YAML representations.

```python
class YAMLRenderer(BaseRenderer):
    media_type = "application/x-yaml"
    format_suffix = "yaml"
```

* **Evidence**: [aquilia/controller/renderers.py:L246-L289](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/renderers.py#L246-L289)

---

### [PlainTextRenderer](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/renderers.py#L297-L308)

Renders structures into raw plain strings.

```python
class PlainTextRenderer(BaseRenderer):
    media_type = "text/plain"
    format_suffix = "text"
```

* **Evidence**: [aquilia/controller/renderers.py:L297-L308](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/renderers.py#L297-L308)

---

### [HTMLRenderer](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/renderers.py#L316-L331)

Renders raw HTML pages or wraps items inside HTML boxes.

```python
class HTMLRenderer(BaseRenderer):
    media_type = "text/html"
    format_suffix = "html"
```

* **Evidence**: [aquilia/controller/renderers.py:L316-L331](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/renderers.py#L316-L331)

---

### [MessagePackRenderer](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/renderers.py#L339-L359)

Renders structured payloads as binary MessagePack.

```python
class MessagePackRenderer(BaseRenderer):
    media_type = "application/msgpack"
    format_suffix = "msgpack"
    charset = None
```

* **Evidence**: [aquilia/controller/renderers.py:L339-L359](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/renderers.py#L339-L359)

---

### [ContentNegotiator](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/renderers.py#L367-L418)

Audits accept-headers and format variables to match appropriate renderers.

```python
class ContentNegotiator:
    def __init__(self, renderers: Sequence[BaseRenderer] | None = None)
```

* **Evidence**: [aquilia/controller/renderers.py:L367-L418](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/renderers.py#L367-L418)

---

### [negotiate](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/renderers.py#L426-L453)

Helper running Content Negotiation and output formatting.

```python
def negotiate(
    data: Any,
    request: Any,
    *,
    renderers: Sequence[BaseRenderer] | None = None,
    status: int = 200,
    headers: dict[str, str] | None = None,
) -> tuple[str | bytes, str, int]
```

* **Evidence**: [aquilia/controller/renderers.py:L426-L453](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/renderers.py#L426-L453)
