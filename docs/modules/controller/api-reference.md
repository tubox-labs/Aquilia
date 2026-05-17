# Controllers API Reference

This page is extracted from the current Python source. It includes public classes, methods, functions, constants, dataclass-like fields, decorators, and notable attributes.

## Public Class Summary

| Name | Source | Bases | Purpose |
| --- | --- | --- | --- |
| `RequestCtx` | `aquilia/controller/base.py` | object | Request context provided to controller methods. |
| `ExceptionFilter` | `aquilia/controller/base.py` | object | Base class for exception filters. |
| `Interceptor` | `aquilia/controller/base.py` | object | Base class for controller interceptors. |
| `Throttle` | `aquilia/controller/base.py` | object | Simple in-memory sliding-window rate limiter. |
| `Controller` | `aquilia/controller/base.py` | object | Base Controller class. |
| `CompiledRoute` | `aquilia/controller/compiler.py` | object | A compiled controller route with pattern and handler. |
| `CompiledController` | `aquilia/controller/compiler.py` | object | A fully compiled controller with all routes. |
| `ControllerCompiler` | `aquilia/controller/compiler.py` | object | Compiles controllers into executable routes with pattern matching. |
| `RouteDecorator` | `aquilia/controller/decorators.py` | object | Base route decorator. |
| `GET` | `aquilia/controller/decorators.py` | RouteDecorator | GET request decorator. |
| `POST` | `aquilia/controller/decorators.py` | RouteDecorator | POST request decorator. |
| `PUT` | `aquilia/controller/decorators.py` | RouteDecorator | PUT request decorator. |
| `PATCH` | `aquilia/controller/decorators.py` | RouteDecorator | PATCH request decorator. |
| `DELETE` | `aquilia/controller/decorators.py` | RouteDecorator | DELETE request decorator. |
| `HEAD` | `aquilia/controller/decorators.py` | RouteDecorator | HEAD request decorator. |
| `OPTIONS` | `aquilia/controller/decorators.py` | RouteDecorator | OPTIONS request decorator. |
| `TRACE` | `aquilia/controller/decorators.py` | RouteDecorator | TRACE request decorator. |
| `WS` | `aquilia/controller/decorators.py` | RouteDecorator | WebSocket request decorator. |
| `ControllerEngine` | `aquilia/controller/engine.py` | object | Executes controller methods with complete integration. |
| `InstantiationMode` | `aquilia/controller/factory.py` | str, Enum | Controller instantiation modes. |
| `ControllerFactory` | `aquilia/controller/factory.py` | object | Factory for creating controller instances. |
| `ScopeViolationError` | `aquilia/controller/factory.py` | Exception | Raised when a scope rule is violated. |
| `FilterSetMeta` | `aquilia/controller/filters.py` | type | Metaclass for FilterSet -- collects ``Meta.fields`` at class creation. |
| `FilterSet` | `aquilia/controller/filters.py` | object | Declarative filter specification. |
| `BaseFilterBackend` | `aquilia/controller/filters.py` | object | Abstract base for pluggable filter backends. |
| `SearchFilter` | `aquilia/controller/filters.py` | BaseFilterBackend | Text search across multiple fields. |
| `OrderingFilter` | `aquilia/controller/filters.py` | BaseFilterBackend | Dynamic field ordering via ``?ordering=<field>`` query parameter. |
| `ParameterMetadata` | `aquilia/controller/metadata.py` | object | Metadata for a route method parameter. |
| `RouteMetadata` | `aquilia/controller/metadata.py` | object | Metadata for a single route (controller method). |
| `ControllerMetadata` | `aquilia/controller/metadata.py` | object | Complete metadata for a Controller class. |
| `ParsedDocstring` | `aquilia/controller/openapi.py` | object | Parsed handler docstring with structured sections. |
| `OpenAPIConfig` | `aquilia/controller/openapi.py` | object | Configuration for OpenAPI spec generation. |
| `OpenAPIGenerator` | `aquilia/controller/openapi.py` | object | Production-grade OpenAPI 3.1.0 specification generator. |
| `BasePagination` | `aquilia/controller/pagination.py` | object | Abstract base for pagination backends. |
| `NoPagination` | `aquilia/controller/pagination.py` | BasePagination | Passthrough -- no pagination applied. |
| `PageNumberPagination` | `aquilia/controller/pagination.py` | BasePagination | Classic page-number pagination. |
| `LimitOffsetPagination` | `aquilia/controller/pagination.py` | BasePagination | Limit/Offset pagination. |
| `CursorPagination` | `aquilia/controller/pagination.py` | BasePagination | Cursor-based (keyset) pagination -- efficient for very large datasets. |
| `BaseRenderer` | `aquilia/controller/renderers.py` | object | Abstract renderer. |
| `JSONRenderer` | `aquilia/controller/renderers.py` | BaseRenderer | Render data as JSON. Default renderer. |
| `XMLRenderer` | `aquilia/controller/renderers.py` | BaseRenderer | Render data as XML. |
| `YAMLRenderer` | `aquilia/controller/renderers.py` | BaseRenderer | Render data as YAML. |
| `PlainTextRenderer` | `aquilia/controller/renderers.py` | BaseRenderer | Render data as plain text (str() conversion). |
| `HTMLRenderer` | `aquilia/controller/renderers.py` | BaseRenderer | Render pre-built HTML strings (passthrough). |
| `MessagePackRenderer` | `aquilia/controller/renderers.py` | BaseRenderer | Render data as MessagePack binary (requires ``msgpack``). |
| `ContentNegotiator` | `aquilia/controller/renderers.py` | object | Select the best renderer for a request based on the ``Accept`` header |
| `ControllerRouteMatch` | `aquilia/controller/router.py` | object | Result of a successful controller route match. |
| `ControllerRouter` | `aquilia/controller/router.py` | object | Router for controller-based routes using pattern matching. |

## Public Function Summary

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `route` | `aquilia/controller/decorators.py` | `def route(method: str &#124; list[str], path: str &#124; None = None, *, pipeline: list[Any] &#124; None = None, summary: str &#124; None = None, description: str &#124; None = None, tags: list[str] &#124; None = None, deprecated: bool = False, response_model: type &#124; None = None, status_code: int = 200, request_blueprint: type &#124; None = None, response_blueprint: type &#124; None = None, filterset_class: type &#124; None = None, filterset_fields: list[str] &#124; Any &#124; None = None, search_fields: list[str] &#124; None = None, ordering_fields: list[str] &#124; None = None, pagination_class: type &#124; None = None, renderer_classes: list[Any] &#124; None = None, throttle: Any &#124; None = None, timeout: float &#124; None = None, version: str &#124; list[str] &#124; None = None) -> Callable[[F], F]` | Generic route decorator. |
| `apply_filters_to_list` | `aquilia/controller/filters.py` | `def apply_filters_to_list(data: list[Any], filters: dict[str, Any]) -> list[Any]` | Apply parsed filter clauses to an in-memory list of dicts / objects. |
| `apply_search_to_list` | `aquilia/controller/filters.py` | `def apply_search_to_list(data: list[Any], search_term: str, search_fields: list[str]) -> list[Any]` | Apply text search over *search_fields* on an in-memory list. |
| `apply_ordering_to_list` | `aquilia/controller/filters.py` | `def apply_ordering_to_list(data: list[Any], ordering: list[str]) -> list[Any]` | Sort an in-memory list by one or more fields. |
| `filter_queryset` | `aquilia/controller/filters.py` | `async def filter_queryset(queryset: Any, request: Any, *, filterset_class: type[FilterSet] &#124; None = None, filterset_fields: list[str] &#124; dict[str, list[str]] &#124; None = None, search_fields: list[str] &#124; None = None, ordering_fields: list[str] &#124; None = None) -> Any` | One-shot convenience: apply FilterSet + SearchFilter + OrderingFilter |
| `filter_data` | `aquilia/controller/filters.py` | `def filter_data(data: list[Any], request: Any, *, filterset_class: type[FilterSet] &#124; None = None, filterset_fields: list[str] &#124; dict[str, list[str]] &#124; None = None, search_fields: list[str] &#124; None = None, ordering_fields: list[str] &#124; None = None) -> list[Any]` | One-shot convenience: apply FilterSet + SearchFilter + OrderingFilter |
| `extract_controller_metadata` | `aquilia/controller/metadata.py` | `def extract_controller_metadata(controller_class: type, module_path: str) -> ControllerMetadata` | Extract metadata from a Controller class. |
| `generate_swagger_html` | `aquilia/controller/openapi.py` | `def generate_swagger_html(config: OpenAPIConfig) -> str` | Generate the Swagger UI HTML page. |
| `generate_redoc_html` | `aquilia/controller/openapi.py` | `def generate_redoc_html(config: OpenAPIConfig) -> str` | Generate the ReDoc HTML page. |
| `negotiate` | `aquilia/controller/renderers.py` | `def negotiate(data: Any, request: Any, *, renderers: Sequence[BaseRenderer] &#124; None = None, status: int = 200, headers: dict[str, str] &#124; None = None) -> tuple[str &#124; bytes, str, int]` | One-shot content negotiation. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `_EMPTY_STATE` | `aquilia/controller/base.py` | `dict[str, Any]` |
| `_CURRENT_REQUEST_CTX` | `aquilia/controller/base.py` | `ContextVar['RequestCtx &#124; None']` |
| `F` | `aquilia/controller/decorators.py` | `TypeVar('F', bound=Callable[..., Any])` |
| `VALID_HTTP_METHODS` | `aquilia/controller/decorators.py` | `frozenset({'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS', 'TRACE', 'WS'})` |
| `_MAX_REGEX_LENGTH` | `aquilia/controller/filters.py` | `int` |
| `_DANGEROUS_REGEX_PATTERNS` | `aquilia/controller/filters.py` | `tuple[re.Pattern, ...]` |
| `LOOKUP_TYPES` | `aquilia/controller/filters.py` | `dict[str, str]` |
| `_PYTHON_TYPE_MAP` | `aquilia/controller/openapi.py` | `dict[type, dict[str, str]]` |
| `_BODY_METHODS` | `aquilia/controller/openapi.py` | `{'POST', 'PUT', 'PATCH'}` |
| `_BODY_DOC_PATTERN` | `aquilia/controller/openapi.py` | `re.compile('Body:\\s*\\{([^}]+)\\}', re.DOTALL &#124; re.IGNORECASE)` |
| `_BODY_FIELD_PATTERN` | `aquilia/controller/openapi.py` | `re.compile('"(\\w+)"\\s*:\\s*"?([^",\\n}]+)"?')` |
| `_STATUS_DESCRIPTIONS` | `aquilia/controller/openapi.py` | `dict[int, str]` |
| `_SWAGGER_UI_VERSION` | `aquilia/controller/openapi.py` | `'5.18.2'` |
| `_SWAGGER_UI_HTML` | `aquilia/controller/openapi.py` | `'<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="utf-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1">\n    <title>{ti` |
| `_REDOC_HTML` | `aquilia/controller/openapi.py` | `'<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="utf-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1">\n    <title>{ti` |
| `_EMPTY_DICT` | `aquilia/controller/router.py` | `dict[str, Any]` |
| `_EMPTY_QUERY` | `aquilia/controller/router.py` | `dict[str, str]` |

## Detailed Classes And Methods

### Class: `RequestCtx`

- Source: `aquilia/controller/base.py`
- Bases: `object`
- Summary: Request context provided to controller methods.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `path` | `def path(self) -> str` | property | Request path. |
| `method` | `def method(self) -> str` | property | Request method. |
| `headers` | `def headers(self) -> Headers` | property | Request headers. |
| `query_params` | `def query_params(self) -> MultiDict` | property | Query parameters (parsed from query string). |
| `query_param` | `def query_param(self, key: str, default: str &#124; None = None) -> str &#124; None` |  | Get single query parameter. |
| `json` | `async def json(self) -> Any` |  | Parse request body as JSON. |
| `body` | `async def body(self) -> bytes` |  | Read raw request body bytes. |
| `form` | `async def form(self) -> FormData` |  | Parse request body as form data. |
| `multipart` | `async def multipart(self)` |  | Parse multipart/form-data (file uploads). |

### Class: `ExceptionFilter`

- Source: `aquilia/controller/base.py`
- Bases: `object`
- Summary: Base class for exception filters.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `catches` | `list[type]` | `[]` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `catch` | `async def catch(self, exception: Exception, ctx: 'RequestCtx') -> Optional['Response']` |  | Handle the exception and return a Response. |

### Class: `Interceptor`

- Source: `aquilia/controller/base.py`
- Bases: `object`
- Summary: Base class for controller interceptors.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `before` | `async def before(self, ctx: 'RequestCtx') -> Optional['Response']` |  | Called before the handler executes. |
| `after` | `async def after(self, ctx: 'RequestCtx', result: Any) -> Any` |  | Called after the handler executes. |

### Class: `Throttle`

- Source: `aquilia/controller/base.py`
- Bases: `object`
- Summary: Simple in-memory sliding-window rate limiter.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `check` | `def check(self, request: Any) -> bool` |  | Check if the request is within the rate limit. |
| `retry_after` | `def retry_after(self) -> int` | property | Seconds until the window resets (approximate). |
| `reset` | `def reset(self)` |  | Clear all rate limit state. |

### Class: `Controller`

- Source: `aquilia/controller/base.py`
- Bases: `object`
- Summary: Base Controller class.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `prefix` | `str` | `''` |
| `pipeline` | `list[Any]` | `[]` |
| `tags` | `list[str]` | `[]` |
| `instantiation_mode` | `str` | `'per_request'` |
| `version` | `str &#124; None` | `None` |
| `throttle` | `Throttle &#124; None` | `None` |
| `interceptors` | `list[Any]` | `[]` |
| `exception_filters` | `list[Any]` | `[]` |
| `timeout` | `float` | `0` |
| `max_body_size` | `int` | `0` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `render` | `async def render(self, template_name: str, context: dict[str, Any] &#124; None = None, request_ctx: RequestCtx &#124; None = None, *, engine: Any &#124; None = None, status: int = 200, headers: dict[str, str] &#124; None = None) -> 'Response'` |  | Render template and return Response. |
| `on_startup` | `async def on_startup(self, ctx: RequestCtx) -> None` |  | Called when controller is initialized (singleton mode only). |
| `on_shutdown` | `async def on_shutdown(self, ctx: RequestCtx) -> None` |  | Called when controller is destroyed (singleton mode only). |
| `on_request` | `async def on_request(self, ctx: RequestCtx) -> None` |  | Called before each request is processed. |
| `on_response` | `async def on_response(self, ctx: RequestCtx, response: 'Response') -> 'Response'` |  | Called after each request is processed. |

### Class: `CompiledRoute`

- Source: `aquilia/controller/compiler.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A compiled controller route with pattern and handler.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `controller_class` | `type` |  |
| `controller_metadata` | `ControllerMetadata` |  |
| `route_metadata` | `RouteMetadata` |  |
| `compiled_pattern` | `CompiledPattern` |  |
| `full_path` | `str` |  |
| `http_method` | `str` |  |
| `specificity` | `int` |  |
| `app_name` | `str &#124; None` | `None` |
| `version_metadata` | `dict[str, Any] &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialize to dict for caching. |

### Class: `CompiledController`

- Source: `aquilia/controller/compiler.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: A fully compiled controller with all routes.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `controller_class` | `type` |  |
| `metadata` | `ControllerMetadata` |  |
| `routes` | `list[CompiledRoute]` |  |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialize to dict. |

### Class: `ControllerCompiler`

- Source: `aquilia/controller/compiler.py`
- Bases: `object`
- Summary: Compiles controllers into executable routes with pattern matching.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `compile_controller` | `def compile_controller(self, controller_class: type, base_prefix: str &#124; None = None) -> CompiledController` |  | Compile a controller class into routes. |
| `validate_route_tree` | `def validate_route_tree(self, compiled_controllers: list[CompiledController]) -> list[dict[str, Any]]` |  | Validate the entire compiled route tree for conflicts. |
| `check_conflicts` | `def check_conflicts(self, controllers: list[type]) -> list[dict[str, Any]]` |  | Check for route conflicts across controllers (Legacy). |
| `export_routes` | `def export_routes(self, controllers: list[CompiledController]) -> dict[str, Any]` |  | Export all compiled routes for inspection/debugging. |

### Class: `RouteDecorator`

- Source: `aquilia/controller/decorators.py`
- Bases: `object`
- Summary: Base route decorator.

### Class: `GET`

- Source: `aquilia/controller/decorators.py`
- Bases: `RouteDecorator`
- Summary: GET request decorator.

### Class: `POST`

- Source: `aquilia/controller/decorators.py`
- Bases: `RouteDecorator`
- Summary: POST request decorator.

### Class: `PUT`

- Source: `aquilia/controller/decorators.py`
- Bases: `RouteDecorator`
- Summary: PUT request decorator.

### Class: `PATCH`

- Source: `aquilia/controller/decorators.py`
- Bases: `RouteDecorator`
- Summary: PATCH request decorator.

### Class: `DELETE`

- Source: `aquilia/controller/decorators.py`
- Bases: `RouteDecorator`
- Summary: DELETE request decorator.

### Class: `HEAD`

- Source: `aquilia/controller/decorators.py`
- Bases: `RouteDecorator`
- Summary: HEAD request decorator.

### Class: `OPTIONS`

- Source: `aquilia/controller/decorators.py`
- Bases: `RouteDecorator`
- Summary: OPTIONS request decorator.

### Class: `TRACE`

- Source: `aquilia/controller/decorators.py`
- Bases: `RouteDecorator`
- Summary: TRACE request decorator.

### Class: `WS`

- Source: `aquilia/controller/decorators.py`
- Bases: `RouteDecorator`
- Summary: WebSocket request decorator.

### Class: `ControllerEngine`

- Source: `aquilia/controller/engine.py`
- Bases: `object`
- Summary: Executes controller methods with complete integration.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `execute` | `async def execute(self, route: CompiledRoute, request: Request, path_params: dict[str, Any], container: Container) -> Response` |  | Execute a controller route. |
| `shutdown_controller` | `async def shutdown_controller(self, controller_class: type, container: Container)` |  | Execute controller shutdown hooks. |
| `clear_caches` | `def clear_caches(cls)` | classmethod | Clear all class-level caches. |

### Class: `InstantiationMode`

- Source: `aquilia/controller/factory.py`
- Bases: `str, Enum`
- Summary: Controller instantiation modes.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `PER_REQUEST` |  | `'per_request'` |
| `SINGLETON` |  | `'singleton'` |

### Class: `ControllerFactory`

- Source: `aquilia/controller/factory.py`
- Bases: `object`
- Summary: Factory for creating controller instances.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `create` | `async def create(self, controller_class: type, mode: InstantiationMode = InstantiationMode.PER_REQUEST, request_container: Any &#124; None = None, ctx: Any &#124; None = None) -> Any` |  | Create controller instance. |
| `shutdown` | `async def shutdown(self)` |  | Shutdown all singleton controllers. |
| `validate_scope` | `def validate_scope(self, controller_class: type, mode: InstantiationMode) -> None` |  | Validate that controller doesn't violate scope rules. |
| `clear_caches` | `def clear_caches(cls)` | classmethod | Clear all class-level caches. |

### Class: `ScopeViolationError`

- Source: `aquilia/controller/factory.py`
- Bases: `Exception`
- Summary: Raised when a scope rule is violated.

### Class: `FilterSetMeta`

- Source: `aquilia/controller/filters.py`
- Bases: `type`
- Summary: Metaclass for FilterSet -- collects ``Meta.fields`` at class creation.

### Class: `FilterSet`

- Source: `aquilia/controller/filters.py`
- Bases: `object`
- Summary: Declarative filter specification.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `parse` | `def parse(self) -> dict[str, Any]` |  | Parse query parameters into ORM-compatible filter clauses. |
| `filter_list` | `def filter_list(self, data: list[Any]) -> list[Any]` |  | Convenience: parse + apply to an in-memory list. |
| `filter_queryset` | `async def filter_queryset(self, queryset: Any) -> Any` |  | Apply parsed clauses to an Aquilia QuerySet (Q object). |

### Class: `BaseFilterBackend`

- Source: `aquilia/controller/filters.py`
- Bases: `object`
- Summary: Abstract base for pluggable filter backends.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `filter_data` | `def filter_data(self, data: list[Any], request: Any, **options: Any) -> list[Any]` |  | Filter an in-memory list. Return the filtered list. |
| `filter_queryset` | `async def filter_queryset(self, queryset: Any, request: Any, **options: Any) -> Any` |  | Filter an ORM queryset. Return the filtered queryset. |

### Class: `SearchFilter`

- Source: `aquilia/controller/filters.py`
- Bases: `BaseFilterBackend`
- Summary: Text search across multiple fields.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `search_param` | `str` | `'search'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `filter_data` | `def filter_data(self, data: list[Any], request: Any, *, search_fields: list[str] &#124; None = None, **options: Any) -> list[Any]` |  | Method. |
| `filter_queryset` | `async def filter_queryset(self, queryset: Any, request: Any, *, search_fields: list[str] &#124; None = None, **options: Any) -> Any` |  | Method. |

### Class: `OrderingFilter`

- Source: `aquilia/controller/filters.py`
- Bases: `BaseFilterBackend`
- Summary: Dynamic field ordering via ``?ordering=<field>`` query parameter.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `ordering_param` | `str` | `'ordering'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `filter_data` | `def filter_data(self, data: list[Any], request: Any, *, ordering_fields: list[str] &#124; None = None, **options: Any) -> list[Any]` |  | Method. |
| `filter_queryset` | `async def filter_queryset(self, queryset: Any, request: Any, *, ordering_fields: list[str] &#124; None = None, **options: Any) -> Any` |  | Method. |

### Class: `ParameterMetadata`

- Source: `aquilia/controller/metadata.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Metadata for a route method parameter.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |
| `type` | `type` |  |
| `default` | `Any` | `inspect.Parameter.empty` |
| `source` | `str` | `'query'` |
| `required` | `bool` | `True` |
| `pattern` | `str &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `has_default` | `def has_default(self) -> bool` | property | Method. |

### Class: `RouteMetadata`

- Source: `aquilia/controller/metadata.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Metadata for a single route (controller method).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `http_method` | `str` |  |
| `path_template` | `str` |  |
| `full_path` | `str` |  |
| `handler_name` | `str` |  |
| `parameters` | `list[ParameterMetadata]` | `field(default_factory=list)` |
| `pipeline` | `list[Any]` | `field(default_factory=list)` |
| `summary` | `str` | `''` |
| `description` | `str` | `''` |
| `tags` | `list[str]` | `field(default_factory=list)` |
| `deprecated` | `bool` | `False` |
| `response_model` | `type &#124; None` | `None` |
| `status_code` | `int` | `200` |
| `specificity` | `int` | `0` |
| `version` | `Any &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `compute_specificity` | `def compute_specificity(self) -> int` |  | Compute route specificity for conflict resolution. |

### Class: `ControllerMetadata`

- Source: `aquilia/controller/metadata.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Complete metadata for a Controller class.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `class_name` | `str` |  |
| `module_path` | `str` |  |
| `prefix` | `str` |  |
| `routes` | `list[RouteMetadata]` | `field(default_factory=list)` |
| `pipeline` | `list[Any]` | `field(default_factory=list)` |
| `tags` | `list[str]` | `field(default_factory=list)` |
| `instantiation_mode` | `str` | `'per_request'` |
| `constructor_params` | `list[ParameterMetadata]` | `field(default_factory=list)` |
| `version` | `Any &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_route` | `def get_route(self, method: str, path: str) -> RouteMetadata &#124; None` |  | Find route by method and path. |
| `has_conflict` | `def has_conflict(self, other: 'ControllerMetadata') -> tuple &#124; None` |  | Check for route conflicts with another controller. |

### Class: `ParsedDocstring`

- Source: `aquilia/controller/openapi.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Parsed handler docstring with structured sections.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `summary` | `str` | `''` |
| `description` | `str` | `''` |
| `params` | `dict[str, str]` | `field(default_factory=dict)` |
| `returns` | `str` | `''` |
| `raises` | `list[dict[str, str]]` | `field(default_factory=list)` |
| `request_body` | `str &#124; None` | `None` |

### Class: `OpenAPIConfig`

- Source: `aquilia/controller/openapi.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Configuration for OpenAPI spec generation.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `title` | `str` | `'Aquilia API'` |
| `version` | `str` | `'1.0.0'` |
| `description` | `str` | `''` |
| `terms_of_service` | `str` | `''` |
| `contact_name` | `str` | `''` |
| `contact_email` | `str` | `''` |
| `contact_url` | `str` | `''` |
| `license_name` | `str` | `''` |
| `license_url` | `str` | `''` |
| `servers` | `list[dict[str, str]]` | `field(default_factory=list)` |
| `docs_path` | `str` | `'/docs'` |
| `openapi_json_path` | `str` | `'/openapi.json'` |
| `redoc_path` | `str` | `'/redoc'` |
| `include_internal` | `bool` | `False` |
| `group_by_module` | `bool` | `True` |
| `infer_request_body` | `bool` | `True` |
| `infer_responses` | `bool` | `True` |
| `detect_security` | `bool` | `True` |
| `external_docs_url` | `str` | `''` |
| `external_docs_description` | `str` | `''` |
| `swagger_ui_theme` | `str` | `''` |
| `swagger_ui_config` | `dict[str, Any]` | `field(default_factory=dict)` |
| `enabled` | `bool` | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `from_dict` | `def from_dict(cls, data: dict[str, Any]) -> OpenAPIConfig` | classmethod | Create config from dict (e.g., from workspace config). |

### Class: `OpenAPIGenerator`

- Source: `aquilia/controller/openapi.py`
- Bases: `object`
- Summary: Production-grade OpenAPI 3.1.0 specification generator.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `generate` | `def generate(self, router: ControllerRouter) -> dict[str, Any]` |  | Generate the full OpenAPI 3.1.0 specification. |

### Class: `BasePagination`

- Source: `aquilia/controller/pagination.py`
- Bases: `object`
- Summary: Abstract base for pagination backends.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `paginate_list` | `def paginate_list(self, data: list[Any], request: Any) -> dict[str, Any]` |  | Paginate an in-memory list. |
| `paginate_queryset` | `async def paginate_queryset(self, queryset: Any, request: Any) -> dict[str, Any]` |  | Paginate an ORM queryset. |

### Class: `NoPagination`

- Source: `aquilia/controller/pagination.py`
- Bases: `BasePagination`
- Summary: Passthrough -- no pagination applied.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `paginate_list` | `def paginate_list(self, data: list[Any], request: Any) -> dict[str, Any]` |  | Method. |

### Class: `PageNumberPagination`

- Source: `aquilia/controller/pagination.py`
- Bases: `BasePagination`
- Summary: Classic page-number pagination.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `page_size` | `int` | `20` |
| `max_page_size` | `int` | `1000` |
| `page_param` | `str` | `'page'` |
| `page_size_param` | `str` | `'page_size'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `paginate_list` | `def paginate_list(self, data: list[Any], request: Any) -> dict[str, Any]` |  | Method. |
| `paginate_queryset` | `async def paginate_queryset(self, queryset: Any, request: Any) -> dict[str, Any]` |  | Optimised ORM pagination -- uses .count() + .offset().limit() |

### Class: `LimitOffsetPagination`

- Source: `aquilia/controller/pagination.py`
- Bases: `BasePagination`
- Summary: Limit/Offset pagination.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `default_limit` | `int` | `20` |
| `max_limit` | `int` | `1000` |
| `limit_param` | `str` | `'limit'` |
| `offset_param` | `str` | `'offset'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `paginate_list` | `def paginate_list(self, data: list[Any], request: Any) -> dict[str, Any]` |  | Method. |
| `paginate_queryset` | `async def paginate_queryset(self, queryset: Any, request: Any) -> dict[str, Any]` |  | Method. |

### Class: `CursorPagination`

- Source: `aquilia/controller/pagination.py`
- Bases: `BasePagination`
- Summary: Cursor-based (keyset) pagination -- efficient for very large datasets.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `page_size` | `int` | `20` |
| `max_page_size` | `int` | `1000` |
| `cursor_param` | `str` | `'cursor'` |
| `page_size_param` | `str` | `'page_size'` |
| `ordering` | `str` | `'-id'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `paginate_list` | `def paginate_list(self, data: list[Any], request: Any) -> dict[str, Any]` |  | Method. |
| `paginate_queryset` | `async def paginate_queryset(self, queryset: Any, request: Any) -> dict[str, Any]` |  | Cursor pagination on an ORM queryset. |

### Class: `BaseRenderer`

- Source: `aquilia/controller/renderers.py`
- Bases: `object`
- Summary: Abstract renderer.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `media_type` | `str` | `'application/octet-stream'` |
| `format_suffix` | `str` | `''` |
| `charset` | `str &#124; None` | `'utf-8'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `render` | `def render(self, data: Any, *, request: Any = None, response_status: int = 200, response_headers: dict[str, str] &#124; None = None) -> str &#124; bytes` |  | Render data to the target format. |

### Class: `JSONRenderer`

- Source: `aquilia/controller/renderers.py`
- Bases: `BaseRenderer`
- Summary: Render data as JSON. Default renderer.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `media_type` |  | `'application/json'` |
| `format_suffix` |  | `'json'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `render` | `def render(self, data: Any, **kwargs) -> str` |  | Method. |

### Class: `XMLRenderer`

- Source: `aquilia/controller/renderers.py`
- Bases: `BaseRenderer`
- Summary: Render data as XML.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `media_type` |  | `'application/xml'` |
| `format_suffix` |  | `'xml'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `render` | `def render(self, data: Any, **kwargs) -> str` |  | Method. |

### Class: `YAMLRenderer`

- Source: `aquilia/controller/renderers.py`
- Bases: `BaseRenderer`
- Summary: Render data as YAML.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `media_type` |  | `'application/x-yaml'` |
| `format_suffix` |  | `'yaml'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `render` | `def render(self, data: Any, **kwargs) -> str` |  | Method. |

### Class: `PlainTextRenderer`

- Source: `aquilia/controller/renderers.py`
- Bases: `BaseRenderer`
- Summary: Render data as plain text (str() conversion).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `media_type` |  | `'text/plain'` |
| `format_suffix` |  | `'text'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `render` | `def render(self, data: Any, **kwargs) -> str` |  | Method. |

### Class: `HTMLRenderer`

- Source: `aquilia/controller/renderers.py`
- Bases: `BaseRenderer`
- Summary: Render pre-built HTML strings (passthrough).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `media_type` |  | `'text/html'` |
| `format_suffix` |  | `'html'` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `render` | `def render(self, data: Any, **kwargs) -> str` |  | Method. |

### Class: `MessagePackRenderer`

- Source: `aquilia/controller/renderers.py`
- Bases: `BaseRenderer`
- Summary: Render data as MessagePack binary (requires ``msgpack``).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `media_type` |  | `'application/msgpack'` |
| `format_suffix` |  | `'msgpack'` |
| `charset` |  | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `render` | `def render(self, data: Any, **kwargs) -> bytes` |  | Method. |

### Class: `ContentNegotiator`

- Source: `aquilia/controller/renderers.py`
- Bases: `object`
- Summary: Select the best renderer for a request based on the ``Accept`` header

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `select_renderer` | `def select_renderer(self, request: Any) -> tuple[BaseRenderer, str]` |  | Return ``(renderer_instance, media_type)`` for the request. |

### Class: `ControllerRouteMatch`

- Source: `aquilia/controller/router.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Result of a successful controller route match.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `route` | `CompiledRoute` |  |
| `params` | `dict[str, Any]` |  |
| `query` | `dict[str, Any]` |  |

### Class: `ControllerRouter`

- Source: `aquilia/controller/router.py`
- Bases: `object`
- Summary: Router for controller-based routes using pattern matching.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `add_controller` | `def add_controller(self, compiled_controller: CompiledController)` |  | Add a compiled controller to the router. |
| `initialize` | `def initialize(self)` |  | Build fast-path lookup structures including segment trie. |
| `match_sync` | `def match_sync(self, path: str, method: str, query_params: dict[str, str] &#124; None = None, api_version: Any &#124; None = None) -> ControllerRouteMatch &#124; None` |  | Synchronous route matching -- the hot path. |
| `get_allowed_methods` | `def get_allowed_methods(self, path: str) -> list[str]` |  | Return the HTTP methods registered for *path* (normalised). |
| `match` | `async def match(self, path: str, method: str, query_params: dict[str, str] &#124; None = None, api_version: Any &#124; None = None) -> ControllerRouteMatch &#124; None` |  | Async compat wrapper -- delegates to sync hot path. |
| `get_routes` | `def get_routes(self) -> list[dict[str, Any]]` |  | Get all registered routes. |
| `get_routes_full` | `def get_routes_full(self) -> list[CompiledRoute]` |  | Get all CompiledRoute objects. |
| `get_controller` | `def get_controller(self, name: str) -> CompiledController &#124; None` |  | Get compiled controller by name. |
| `has_route` | `def has_route(self, method: str, path: str) -> bool` |  | Check if a route exists. |
| `url_for` | `def url_for(self, name: str, *, api_version: str &#124; None = None, **params) -> str` |  | Reverse URL generation. |

## Functions

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `route` | `aquilia/controller/decorators.py` | `def route(method: str &#124; list[str], path: str &#124; None = None, *, pipeline: list[Any] &#124; None = None, summary: str &#124; None = None, description: str &#124; None = None, tags: list[str] &#124; None = None, deprecated: bool = False, response_model: type &#124; None = None, status_code: int = 200, request_blueprint: type &#124; None = None, response_blueprint: type &#124; None = None, filterset_class: type &#124; None = None, filterset_fields: list[str] &#124; Any &#124; None = None, search_fields: list[str] &#124; None = None, ordering_fields: list[str] &#124; None = None, pagination_class: type &#124; None = None, renderer_classes: list[Any] &#124; None = None, throttle: Any &#124; None = None, timeout: float &#124; None = None, version: str &#124; list[str] &#124; None = None) -> Callable[[F], F]` | Generic route decorator. |
| `apply_filters_to_list` | `aquilia/controller/filters.py` | `def apply_filters_to_list(data: list[Any], filters: dict[str, Any]) -> list[Any]` | Apply parsed filter clauses to an in-memory list of dicts / objects. |
| `apply_search_to_list` | `aquilia/controller/filters.py` | `def apply_search_to_list(data: list[Any], search_term: str, search_fields: list[str]) -> list[Any]` | Apply text search over *search_fields* on an in-memory list. |
| `apply_ordering_to_list` | `aquilia/controller/filters.py` | `def apply_ordering_to_list(data: list[Any], ordering: list[str]) -> list[Any]` | Sort an in-memory list by one or more fields. |
| `filter_queryset` | `aquilia/controller/filters.py` | `async def filter_queryset(queryset: Any, request: Any, *, filterset_class: type[FilterSet] &#124; None = None, filterset_fields: list[str] &#124; dict[str, list[str]] &#124; None = None, search_fields: list[str] &#124; None = None, ordering_fields: list[str] &#124; None = None) -> Any` | One-shot convenience: apply FilterSet + SearchFilter + OrderingFilter |
| `filter_data` | `aquilia/controller/filters.py` | `def filter_data(data: list[Any], request: Any, *, filterset_class: type[FilterSet] &#124; None = None, filterset_fields: list[str] &#124; dict[str, list[str]] &#124; None = None, search_fields: list[str] &#124; None = None, ordering_fields: list[str] &#124; None = None) -> list[Any]` | One-shot convenience: apply FilterSet + SearchFilter + OrderingFilter |
| `extract_controller_metadata` | `aquilia/controller/metadata.py` | `def extract_controller_metadata(controller_class: type, module_path: str) -> ControllerMetadata` | Extract metadata from a Controller class. |
| `generate_swagger_html` | `aquilia/controller/openapi.py` | `def generate_swagger_html(config: OpenAPIConfig) -> str` | Generate the Swagger UI HTML page. |
| `generate_redoc_html` | `aquilia/controller/openapi.py` | `def generate_redoc_html(config: OpenAPIConfig) -> str` | Generate the ReDoc HTML page. |
| `negotiate` | `aquilia/controller/renderers.py` | `def negotiate(data: Any, request: Any, *, renderers: Sequence[BaseRenderer] &#124; None = None, status: int = 200, headers: dict[str, str] &#124; None = None) -> tuple[str &#124; bytes, str, int]` | One-shot content negotiation. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `_EMPTY_STATE` | `aquilia/controller/base.py` | `dict[str, Any]` |
| `_CURRENT_REQUEST_CTX` | `aquilia/controller/base.py` | `ContextVar['RequestCtx &#124; None']` |
| `F` | `aquilia/controller/decorators.py` | `TypeVar('F', bound=Callable[..., Any])` |
| `VALID_HTTP_METHODS` | `aquilia/controller/decorators.py` | `frozenset({'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS', 'TRACE', 'WS'})` |
| `_MAX_REGEX_LENGTH` | `aquilia/controller/filters.py` | `int` |
| `_DANGEROUS_REGEX_PATTERNS` | `aquilia/controller/filters.py` | `tuple[re.Pattern, ...]` |
| `LOOKUP_TYPES` | `aquilia/controller/filters.py` | `dict[str, str]` |
| `_PYTHON_TYPE_MAP` | `aquilia/controller/openapi.py` | `dict[type, dict[str, str]]` |
| `_BODY_METHODS` | `aquilia/controller/openapi.py` | `{'POST', 'PUT', 'PATCH'}` |
| `_BODY_DOC_PATTERN` | `aquilia/controller/openapi.py` | `re.compile('Body:\\s*\\{([^}]+)\\}', re.DOTALL &#124; re.IGNORECASE)` |
| `_BODY_FIELD_PATTERN` | `aquilia/controller/openapi.py` | `re.compile('"(\\w+)"\\s*:\\s*"?([^",\\n}]+)"?')` |
| `_STATUS_DESCRIPTIONS` | `aquilia/controller/openapi.py` | `dict[int, str]` |
| `_SWAGGER_UI_VERSION` | `aquilia/controller/openapi.py` | `'5.18.2'` |
| `_SWAGGER_UI_HTML` | `aquilia/controller/openapi.py` | `'<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="utf-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1">\n    <title>{ti` |
| `_REDOC_HTML` | `aquilia/controller/openapi.py` | `'<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="utf-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1">\n    <title>{ti` |
| `_EMPTY_DICT` | `aquilia/controller/router.py` | `dict[str, Any]` |
| `_EMPTY_QUERY` | `aquilia/controller/router.py` | `dict[str, str]` |
