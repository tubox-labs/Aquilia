# Controller API Reference

This page is generated from the current Python source using the AST. It lists public classes, public methods, public module-level functions, constants, exports, and source files.

## Source Inventory

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/controller/__init__.py` | 169 | 0 | 0 | Aquilia Controller System |
| `aquilia/controller/base.py` | 650 | 5 | 0 | Controller Base Class |
| `aquilia/controller/compiler.py` | 381 | 3 | 0 | Controller Compiler - Compiles controllers to patterns and routes. |
| `aquilia/controller/decorators.py` | 739 | 10 | 1 | Controller Method Decorators |
| `aquilia/controller/engine.py` | 1386 | 1 | 0 | Controller Engine - Executes controller methods with full integration. |
| `aquilia/controller/factory.py` | 403 | 3 | 0 | Controller Factory |
| `aquilia/controller/filters.py` | 766 | 5 | 5 | Aquilia Filter System -- declarative filtering, searching, and ordering. |
| `aquilia/controller/metadata.py` | 461 | 3 | 1 | Controller Metadata Extraction |
| `aquilia/controller/openapi.py` | 1089 | 3 | 2 | OpenAPI 3.1.0 Generation for Aquilia Controllers. |
| `aquilia/controller/pagination.py` | 724 | 5 | 0 | Aquilia Pagination System -- declarative pagination backends. |
| `aquilia/controller/renderers.py` | 453 | 8 | 1 | Aquilia Content Negotiation & Renderer System. |
| `aquilia/controller/router.py` | 592 | 2 | 0 | Controller Router - Pattern-based router for controllers. |

## Public Exports

`BaseFilterBackend`, `BasePagination`, `BaseRenderer`, `CompiledController`, `CompiledRoute`, `ContentNegotiator`, `Controller`, `ControllerCompiler`, `ControllerEngine`, `ControllerFactory`, `ControllerMetadata`, `ControllerRouter`, `CursorPagination`, `DELETE`, `ExceptionFilter`, `FilterSet`, `FilterSetMeta`, `GET`, `HEAD`, `HTMLRenderer`, `InstantiationMode`, `Interceptor`, `JSONRenderer`, `LimitOffsetPagination`, `MessagePackRenderer`, `NoPagination`, `OPTIONS`, `OpenAPIConfig`, `OpenAPIGenerator`, `OrderingFilter`, `PATCH`, `POST`, `PUT`, `PageNumberPagination`, `ParameterMetadata`, `PlainTextRenderer`, `RequestCtx`, `RouteMetadata`, `SearchFilter`, `TRACE`, `Throttle`, `VALID_HTTP_METHODS`, `WS`, `XMLRenderer`, `YAMLRenderer`, `apply_filters_to_list`, `apply_ordering_to_list`, `apply_search_to_list`, `extract_controller_metadata`, `filter_data`, `filter_queryset`, `generate_redoc_html`, `generate_swagger_html`, `negotiate`, `route`

## Public Class Summary

| Class | Source | Bases | Summary |
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
| `ContentNegotiator` | `aquilia/controller/renderers.py` | object | Select the best renderer for a request based on the ``Accept`` header and an optional ``?format=`` query parameter. |
| `ControllerRouteMatch` | `aquilia/controller/router.py` | object | Result of a successful controller route match. |
| `ControllerRouter` | `aquilia/controller/router.py` | object | Router for controller-based routes using pattern matching. |

## Public Function Summary

| Function | Source | Signature | Summary |
| --- | --- | --- | --- |
| `route` | `aquilia/controller/decorators.py` | `def route(method: str \| list[str], path: str \| None=None, *, pipeline: list[Any] \| None=None, summary: str \| None=None, description: str \| None=None, tags: list[str] \| None=None, deprecated: bool=False, response_model: type \| None=None, status_code: int=200, request_blueprint: type \| None=None, response_blueprint: type \| None=None, filterset_class: type \| None=None, filterset_fields: list[str] \| Any \| None=None, search_fields: list[str] \| None=None, ordering_fields: list[str] \| None=None, pagination_class: type \| None=None, renderer_classes: list[Any] \| None=None, throttle: Any \| None=None, timeout: float \| None=None, version: str \| list[str] \| None=None)` | Generic route decorator. |
| `apply_filters_to_list` | `aquilia/controller/filters.py` | `def apply_filters_to_list(data: list[Any], filters: dict[str, Any])` | Apply parsed filter clauses to an in-memory list of dicts / objects. |
| `apply_search_to_list` | `aquilia/controller/filters.py` | `def apply_search_to_list(data: list[Any], search_term: str, search_fields: list[str])` | Apply text search over *search_fields* on an in-memory list. |
| `apply_ordering_to_list` | `aquilia/controller/filters.py` | `def apply_ordering_to_list(data: list[Any], ordering: list[str])` | Sort an in-memory list by one or more fields. |
| `filter_queryset` | `aquilia/controller/filters.py` | `async def filter_queryset(queryset: Any, request: Any, *, filterset_class: type[FilterSet] \| None=None, filterset_fields: list[str] \| dict[str, list[str]] \| None=None, search_fields: list[str] \| None=None, ordering_fields: list[str] \| None=None)` | One-shot convenience: apply FilterSet + SearchFilter + OrderingFilter to an Aquilia Q queryset. |
| `filter_data` | `aquilia/controller/filters.py` | `def filter_data(data: list[Any], request: Any, *, filterset_class: type[FilterSet] \| None=None, filterset_fields: list[str] \| dict[str, list[str]] \| None=None, search_fields: list[str] \| None=None, ordering_fields: list[str] \| None=None)` | One-shot convenience: apply FilterSet + SearchFilter + OrderingFilter to an in-memory list of dicts/objects. |
| `extract_controller_metadata` | `aquilia/controller/metadata.py` | `def extract_controller_metadata(controller_class: type, module_path: str)` | Extract metadata from a Controller class. |
| `generate_swagger_html` | `aquilia/controller/openapi.py` | `def generate_swagger_html(config: OpenAPIConfig)` | Generate the Swagger UI HTML page. |
| `generate_redoc_html` | `aquilia/controller/openapi.py` | `def generate_redoc_html(config: OpenAPIConfig)` | Generate the ReDoc HTML page. |
| `negotiate` | `aquilia/controller/renderers.py` | `def negotiate(data: Any, request: Any, *, renderers: Sequence[BaseRenderer] \| None=None, status: int=200, headers: dict[str, str] \| None=None)` | One-shot content negotiation. |

## Constants And Module Flags

| Name | Source | Value or Type |
| --- | --- | --- |
| `_EMPTY_STATE` | `aquilia/controller/base.py` | `dict[str, Any]` |
| `_CURRENT_REQUEST_CTX` | `aquilia/controller/base.py` | `ContextVar['RequestCtx \| None']` |
| `F` | `aquilia/controller/decorators.py` | `TypeVar('F', bound=Callable[..., Any])` |
| `VALID_HTTP_METHODS` | `aquilia/controller/decorators.py` | `frozenset({'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS', 'TRACE', 'WS'})` |
| `_MAX_REGEX_LENGTH` | `aquilia/controller/filters.py` | `int` |
| `_DANGEROUS_REGEX_PATTERNS` | `aquilia/controller/filters.py` | `tuple[re.Pattern, ...]` |
| `LOOKUP_TYPES` | `aquilia/controller/filters.py` | `dict[str, str]` |
| `_PYTHON_TYPE_MAP` | `aquilia/controller/openapi.py` | `dict[type, dict[str, str]]` |
| `_BODY_METHODS` | `aquilia/controller/openapi.py` | `{'POST', 'PUT', 'PATCH'}` |
| `_BODY_DOC_PATTERN` | `aquilia/controller/openapi.py` | `re.compile('Body:\\s*\\{([^}]+)\\}', re.DOTALL \| re.IGNORECASE)` |
| `_BODY_FIELD_PATTERN` | `aquilia/controller/openapi.py` | `re.compile('"(\\w+)"\\s*:\\s*"?([^",\\n}]+)"?')` |
| `_STATUS_DESCRIPTIONS` | `aquilia/controller/openapi.py` | `dict[int, str]` |
| `_SWAGGER_UI_VERSION` | `aquilia/controller/openapi.py` | `'5.18.2'` |
| `_SWAGGER_UI_HTML` | `aquilia/controller/openapi.py` | `'<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="utf-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1">\n    <title>{title} - API Documentation</title>\n    <link rel="icon" type="image/png"\n          href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@{version}/favicon-32x32.png">\n    <link rel="stylesheet"\n          href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@{version}/swagger-ui.css">\n    <style>\n        html {{ box-sizing: border-box; overflow-y: scroll; }}\n        *, *:before, *:after {{ box-sizing: inherit; }}\n        body {{ margin: 0; background: #fafafa; }}\n        .topbar {{ display: none !important; }}\n        .swagger-ui .info hgroup.main a {{\n            font-size: 0;\n        }}\n        .swagger-ui .info hgroup.main a::after {{\n            content: \'{title}\';\n            font-size: 36px;\n        }}\n        {extra_css}\n    </style>\n</head>\n<body>\n    <div id="swagger-ui"></div>\n    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@{version}/swagger-ui-bundle.js">\n    </script>\n    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@{version}/swagger-ui-standalone-preset.js">\n    </script>\n    <script>\n        window.onload = () => {{\n            window.ui = SwaggerUIBundle({{\n                url: \'{spec_url}\',\n                dom_id: \'#swagger-ui\',\n                deepLinking: true,\n                presets: [\n                    SwaggerUIBundle.presets.apis,\n                    SwaggerUIStandalonePreset,\n                ],\n                plugins: [\n                    SwaggerUIBundle.plugins.DownloadUrl,\n                ],\n                layout: \'StandaloneLayout\',\n                defaultModelsExpandDepth: 1,\n                defaultModelExpandDepth: 2,\n                docExpansion: \'list\',\n                filter: true,\n                showExtensions: true,\n                showCommonExtensions: true,\n                tryItOutEnabled: true,\n                {extra_config}\n            }});\n        }};\n    </script>\n</body>\n</html>'` |
| `_REDOC_HTML` | `aquilia/controller/openapi.py` | `'<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="utf-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1">\n    <title>{title} - API Reference</title>\n    <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700\|Roboto:300,400,700"\n          rel="stylesheet">\n    <style>\n        body {{ margin: 0; padding: 0; }}\n    </style>\n</head>\n<body>\n    <redoc spec-url=\'{spec_url}\'\n           hide-hostname\n           expand-responses="200,201"\n           path-in-middle-panel\n           native-scrollbars>\n    </redoc>\n    <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>\n</body>\n</html>'` |
| `_EMPTY_DICT` | `aquilia/controller/router.py` | `dict[str, Any]` |
| `_EMPTY_QUERY` | `aquilia/controller/router.py` | `dict[str, str]` |

## Detailed Classes And Methods

### `RequestCtx`

- Source: `aquilia/controller/base.py`
- Bases: `object`
- Summary: Request context provided to controller methods.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `path` | `def path(self)` | Request path. |
| `method` | `def method(self)` | Request method. |
| `headers` | `def headers(self)` | Request headers. |
| `query_params` | `def query_params(self)` | Query parameters (parsed from query string). |
| `query_param` | `def query_param(self, key: str, default: str \| None=None)` | Get single query parameter. |
| `json` | `async def json(self)` | Parse request body as JSON. |
| `body` | `async def body(self)` | Read raw request body bytes. |
| `form` | `async def form(self)` | Parse request body as form data. |
| `multipart` | `async def multipart(self)` | Parse multipart/form-data (file uploads). |

### `ExceptionFilter`

- Source: `aquilia/controller/base.py`
- Bases: `object`
- Summary: Base class for exception filters.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `catches` | `list[type]` | `[]` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `catch` | `async def catch(self, exception: Exception, ctx: 'RequestCtx')` | Handle the exception and return a Response. |

### `Interceptor`

- Source: `aquilia/controller/base.py`
- Bases: `object`
- Summary: Base class for controller interceptors.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `before` | `async def before(self, ctx: 'RequestCtx')` | Called before the handler executes. |
| `after` | `async def after(self, ctx: 'RequestCtx', result: Any)` | Called after the handler executes. |

### `Throttle`

- Source: `aquilia/controller/base.py`
- Bases: `object`
- Summary: Simple in-memory sliding-window rate limiter.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `check` | `def check(self, request: Any)` | Check if the request is within the rate limit. |
| `retry_after` | `def retry_after(self)` | Seconds until the window resets (approximate). |
| `reset` | `def reset(self)` | Clear all rate limit state. |

### `Controller`

- Source: `aquilia/controller/base.py`
- Bases: `object`
- Summary: Base Controller class.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `prefix` | `str` | `''` |
| `pipeline` | `list[Any]` | `[]` |
| `tags` | `list[str]` | `[]` |
| `instantiation_mode` | `str` | `'per_request'` |
| `version` | `str \| None` | `None` |
| `throttle` | `Throttle \| None` | `None` |
| `interceptors` | `list[Any]` | `[]` |
| `exception_filters` | `list[Any]` | `[]` |
| `timeout` | `float` | `0` |
| `max_body_size` | `int` | `0` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `render` | `async def render(self, template_name: str, context: dict[str, Any] \| None=None, request_ctx: RequestCtx \| None=None, *, engine: Any \| None=None, status: int=200, headers: dict[str, str] \| None=None)` | Render template and return Response. |
| `on_startup` | `async def on_startup(self, ctx: RequestCtx)` | Called when controller is initialized (singleton mode only). |
| `on_shutdown` | `async def on_shutdown(self, ctx: RequestCtx)` | Called when controller is destroyed (singleton mode only). |
| `on_request` | `async def on_request(self, ctx: RequestCtx)` | Called before each request is processed. |
| `on_response` | `async def on_response(self, ctx: RequestCtx, response: 'Response')` | Called after each request is processed. |

### `CompiledRoute`

- Source: `aquilia/controller/compiler.py`
- Bases: `object`
- Summary: A compiled controller route with pattern and handler.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `controller_class` | `type` | `` |
| `controller_metadata` | `ControllerMetadata` | `` |
| `route_metadata` | `RouteMetadata` | `` |
| `compiled_pattern` | `CompiledPattern` | `` |
| `full_path` | `str` | `` |
| `http_method` | `str` | `` |
| `specificity` | `int` | `` |
| `app_name` | `str \| None` | `None` |
| `version_metadata` | `dict[str, Any] \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` | Serialize to dict for caching. |

### `CompiledController`

- Source: `aquilia/controller/compiler.py`
- Bases: `object`
- Summary: A fully compiled controller with all routes.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `controller_class` | `type` | `` |
| `metadata` | `ControllerMetadata` | `` |
| `routes` | `list[CompiledRoute]` | `` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` | Serialize to dict. |

### `ControllerCompiler`

- Source: `aquilia/controller/compiler.py`
- Bases: `object`
- Summary: Compiles controllers into executable routes with pattern matching.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `compile_controller` | `def compile_controller(self, controller_class: type, base_prefix: str \| None=None)` | Compile a controller class into routes. |
| `validate_route_tree` | `def validate_route_tree(self, compiled_controllers: list[CompiledController])` | Validate the entire compiled route tree for conflicts. |
| `check_conflicts` | `def check_conflicts(self, controllers: list[type])` | Check for route conflicts across controllers (Legacy). |
| `export_routes` | `def export_routes(self, controllers: list[CompiledController])` | Export all compiled routes for inspection/debugging. |

### `RouteDecorator`

- Source: `aquilia/controller/decorators.py`
- Bases: `object`
- Summary: Base route decorator.

### `GET`

- Source: `aquilia/controller/decorators.py`
- Bases: `RouteDecorator`
- Summary: GET request decorator.

### `POST`

- Source: `aquilia/controller/decorators.py`
- Bases: `RouteDecorator`
- Summary: POST request decorator.

### `PUT`

- Source: `aquilia/controller/decorators.py`
- Bases: `RouteDecorator`
- Summary: PUT request decorator.

### `PATCH`

- Source: `aquilia/controller/decorators.py`
- Bases: `RouteDecorator`
- Summary: PATCH request decorator.

### `DELETE`

- Source: `aquilia/controller/decorators.py`
- Bases: `RouteDecorator`
- Summary: DELETE request decorator.

### `HEAD`

- Source: `aquilia/controller/decorators.py`
- Bases: `RouteDecorator`
- Summary: HEAD request decorator.

### `OPTIONS`

- Source: `aquilia/controller/decorators.py`
- Bases: `RouteDecorator`
- Summary: OPTIONS request decorator.

### `TRACE`

- Source: `aquilia/controller/decorators.py`
- Bases: `RouteDecorator`
- Summary: TRACE request decorator.

### `WS`

- Source: `aquilia/controller/decorators.py`
- Bases: `RouteDecorator`
- Summary: WebSocket request decorator.

### `ControllerEngine`

- Source: `aquilia/controller/engine.py`
- Bases: `object`
- Summary: Executes controller methods with complete integration.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `execute` | `async def execute(self, route: CompiledRoute, request: Request, path_params: dict[str, Any], container: Container)` | Execute a controller route. |
| `shutdown_controller` | `async def shutdown_controller(self, controller_class: type, container: Container)` | Execute controller shutdown hooks. |
| `clear_caches` | `def clear_caches(cls)` | Clear all class-level caches. |

### `InstantiationMode`

- Source: `aquilia/controller/factory.py`
- Bases: `str, Enum`
- Summary: Controller instantiation modes.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `PER_REQUEST` | `` | `'per_request'` |
| `SINGLETON` | `` | `'singleton'` |

### `ControllerFactory`

- Source: `aquilia/controller/factory.py`
- Bases: `object`
- Summary: Factory for creating controller instances.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `create` | `async def create(self, controller_class: type, mode: InstantiationMode=InstantiationMode.PER_REQUEST, request_container: Any \| None=None, ctx: Any \| None=None)` | Create controller instance. |
| `shutdown` | `async def shutdown(self)` | Shutdown all singleton controllers. |
| `validate_scope` | `def validate_scope(self, controller_class: type, mode: InstantiationMode)` | Validate that controller doesn't violate scope rules. |
| `clear_caches` | `def clear_caches(cls)` | Clear all class-level caches. |

### `ScopeViolationError`

- Source: `aquilia/controller/factory.py`
- Bases: `Exception`
- Summary: Raised when a scope rule is violated.

### `FilterSetMeta`

- Source: `aquilia/controller/filters.py`
- Bases: `type`
- Summary: Metaclass for FilterSet -- collects ``Meta.fields`` at class creation.

### `FilterSet`

- Source: `aquilia/controller/filters.py`
- Bases: `object`
- Summary: Declarative filter specification.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `parse` | `def parse(self)` | Parse query parameters into ORM-compatible filter clauses. |
| `filter_list` | `def filter_list(self, data: list[Any])` | Convenience: parse + apply to an in-memory list. |
| `filter_queryset` | `async def filter_queryset(self, queryset: Any)` | Apply parsed clauses to an Aquilia QuerySet (Q object). |

### `BaseFilterBackend`

- Source: `aquilia/controller/filters.py`
- Bases: `object`
- Summary: Abstract base for pluggable filter backends.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `filter_data` | `def filter_data(self, data: list[Any], request: Any, **options: Any)` | Filter an in-memory list. Return the filtered list. |
| `filter_queryset` | `async def filter_queryset(self, queryset: Any, request: Any, **options: Any)` | Filter an ORM queryset. Return the filtered queryset. |

### `SearchFilter`

- Source: `aquilia/controller/filters.py`
- Bases: `BaseFilterBackend`
- Summary: Text search across multiple fields.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `search_param` | `str` | `'search'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `filter_data` | `def filter_data(self, data: list[Any], request: Any, *, search_fields: list[str] \| None=None, **options: Any)` |  |
| `filter_queryset` | `async def filter_queryset(self, queryset: Any, request: Any, *, search_fields: list[str] \| None=None, **options: Any)` |  |

### `OrderingFilter`

- Source: `aquilia/controller/filters.py`
- Bases: `BaseFilterBackend`
- Summary: Dynamic field ordering via ``?ordering=<field>`` query parameter.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `ordering_param` | `str` | `'ordering'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `filter_data` | `def filter_data(self, data: list[Any], request: Any, *, ordering_fields: list[str] \| None=None, **options: Any)` |  |
| `filter_queryset` | `async def filter_queryset(self, queryset: Any, request: Any, *, ordering_fields: list[str] \| None=None, **options: Any)` |  |

### `ParameterMetadata`

- Source: `aquilia/controller/metadata.py`
- Bases: `object`
- Summary: Metadata for a route method parameter.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `type` | `type` | `` |
| `default` | `Any` | `inspect.Parameter.empty` |
| `source` | `str` | `'query'` |
| `required` | `bool` | `True` |
| `pattern` | `str \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `has_default` | `def has_default(self)` |  |

### `RouteMetadata`

- Source: `aquilia/controller/metadata.py`
- Bases: `object`
- Summary: Metadata for a single route (controller method).
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `http_method` | `str` | `` |
| `path_template` | `str` | `` |
| `full_path` | `str` | `` |
| `handler_name` | `str` | `` |
| `parameters` | `list[ParameterMetadata]` | `field(default_factory=list)` |
| `pipeline` | `list[Any]` | `field(default_factory=list)` |
| `summary` | `str` | `''` |
| `description` | `str` | `''` |
| `tags` | `list[str]` | `field(default_factory=list)` |
| `deprecated` | `bool` | `False` |
| `response_model` | `type \| None` | `None` |
| `status_code` | `int` | `200` |
| `specificity` | `int` | `0` |
| `version` | `Any \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `compute_specificity` | `def compute_specificity(self)` | Compute route specificity for conflict resolution. |

### `ControllerMetadata`

- Source: `aquilia/controller/metadata.py`
- Bases: `object`
- Summary: Complete metadata for a Controller class.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `class_name` | `str` | `` |
| `module_path` | `str` | `` |
| `prefix` | `str` | `` |
| `routes` | `list[RouteMetadata]` | `field(default_factory=list)` |
| `pipeline` | `list[Any]` | `field(default_factory=list)` |
| `tags` | `list[str]` | `field(default_factory=list)` |
| `instantiation_mode` | `str` | `'per_request'` |
| `constructor_params` | `list[ParameterMetadata]` | `field(default_factory=list)` |
| `version` | `Any \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `get_route` | `def get_route(self, method: str, path: str)` | Find route by method and path. |
| `has_conflict` | `def has_conflict(self, other: 'ControllerMetadata')` | Check for route conflicts with another controller. |

### `ParsedDocstring`

- Source: `aquilia/controller/openapi.py`
- Bases: `object`
- Summary: Parsed handler docstring with structured sections.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `summary` | `str` | `''` |
| `description` | `str` | `''` |
| `params` | `dict[str, str]` | `field(default_factory=dict)` |
| `returns` | `str` | `''` |
| `raises` | `list[dict[str, str]]` | `field(default_factory=list)` |
| `request_body` | `str \| None` | `None` |

### `OpenAPIConfig`

- Source: `aquilia/controller/openapi.py`
- Bases: `object`
- Summary: Configuration for OpenAPI spec generation.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
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

| Method | Signature | Summary |
| --- | --- | --- |
| `from_dict` | `def from_dict(cls, data: dict[str, Any])` | Create config from dict (e.g., from workspace config). |

### `OpenAPIGenerator`

- Source: `aquilia/controller/openapi.py`
- Bases: `object`
- Summary: Production-grade OpenAPI 3.1.0 specification generator.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `generate` | `def generate(self, router: ControllerRouter)` | Generate the full OpenAPI 3.1.0 specification. |

### `BasePagination`

- Source: `aquilia/controller/pagination.py`
- Bases: `object`
- Summary: Abstract base for pagination backends.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `paginate_list` | `def paginate_list(self, data: list[Any], request: Any)` | Paginate an in-memory list. |
| `paginate_queryset` | `async def paginate_queryset(self, queryset: Any, request: Any)` | Paginate an ORM queryset. |

### `NoPagination`

- Source: `aquilia/controller/pagination.py`
- Bases: `BasePagination`
- Summary: Passthrough -- no pagination applied.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `paginate_list` | `def paginate_list(self, data: list[Any], request: Any)` |  |

### `PageNumberPagination`

- Source: `aquilia/controller/pagination.py`
- Bases: `BasePagination`
- Summary: Classic page-number pagination.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `page_size` | `int` | `20` |
| `max_page_size` | `int` | `1000` |
| `page_param` | `str` | `'page'` |
| `page_size_param` | `str` | `'page_size'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `paginate_list` | `def paginate_list(self, data: list[Any], request: Any)` |  |
| `paginate_queryset` | `async def paginate_queryset(self, queryset: Any, request: Any)` | Optimised ORM pagination -- uses .count() + .offset().limit() instead of fetching all rows. |

### `LimitOffsetPagination`

- Source: `aquilia/controller/pagination.py`
- Bases: `BasePagination`
- Summary: Limit/Offset pagination.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `default_limit` | `int` | `20` |
| `max_limit` | `int` | `1000` |
| `limit_param` | `str` | `'limit'` |
| `offset_param` | `str` | `'offset'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `paginate_list` | `def paginate_list(self, data: list[Any], request: Any)` |  |
| `paginate_queryset` | `async def paginate_queryset(self, queryset: Any, request: Any)` |  |

### `CursorPagination`

- Source: `aquilia/controller/pagination.py`
- Bases: `BasePagination`
- Summary: Cursor-based (keyset) pagination -- efficient for very large datasets.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `page_size` | `int` | `20` |
| `max_page_size` | `int` | `1000` |
| `cursor_param` | `str` | `'cursor'` |
| `page_size_param` | `str` | `'page_size'` |
| `ordering` | `str` | `'-id'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `paginate_list` | `def paginate_list(self, data: list[Any], request: Any)` |  |
| `paginate_queryset` | `async def paginate_queryset(self, queryset: Any, request: Any)` | Cursor pagination on an ORM queryset. |

### `BaseRenderer`

- Source: `aquilia/controller/renderers.py`
- Bases: `object`
- Summary: Abstract renderer.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `media_type` | `str` | `'application/octet-stream'` |
| `format_suffix` | `str` | `''` |
| `charset` | `str \| None` | `'utf-8'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `render` | `def render(self, data: Any, *, request: Any=None, response_status: int=200, response_headers: dict[str, str] \| None=None)` | Render data to the target format. |

### `JSONRenderer`

- Source: `aquilia/controller/renderers.py`
- Bases: `BaseRenderer`
- Summary: Render data as JSON. Default renderer.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `media_type` | `` | `'application/json'` |
| `format_suffix` | `` | `'json'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `render` | `def render(self, data: Any, **kwargs)` |  |

### `XMLRenderer`

- Source: `aquilia/controller/renderers.py`
- Bases: `BaseRenderer`
- Summary: Render data as XML.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `media_type` | `` | `'application/xml'` |
| `format_suffix` | `` | `'xml'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `render` | `def render(self, data: Any, **kwargs)` |  |

### `YAMLRenderer`

- Source: `aquilia/controller/renderers.py`
- Bases: `BaseRenderer`
- Summary: Render data as YAML.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `media_type` | `` | `'application/x-yaml'` |
| `format_suffix` | `` | `'yaml'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `render` | `def render(self, data: Any, **kwargs)` |  |

### `PlainTextRenderer`

- Source: `aquilia/controller/renderers.py`
- Bases: `BaseRenderer`
- Summary: Render data as plain text (str() conversion).

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `media_type` | `` | `'text/plain'` |
| `format_suffix` | `` | `'text'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `render` | `def render(self, data: Any, **kwargs)` |  |

### `HTMLRenderer`

- Source: `aquilia/controller/renderers.py`
- Bases: `BaseRenderer`
- Summary: Render pre-built HTML strings (passthrough).

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `media_type` | `` | `'text/html'` |
| `format_suffix` | `` | `'html'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `render` | `def render(self, data: Any, **kwargs)` |  |

### `MessagePackRenderer`

- Source: `aquilia/controller/renderers.py`
- Bases: `BaseRenderer`
- Summary: Render data as MessagePack binary (requires ``msgpack``).

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `media_type` | `` | `'application/msgpack'` |
| `format_suffix` | `` | `'msgpack'` |
| `charset` | `` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `render` | `def render(self, data: Any, **kwargs)` |  |

### `ContentNegotiator`

- Source: `aquilia/controller/renderers.py`
- Bases: `object`
- Summary: Select the best renderer for a request based on the ``Accept`` header and an optional ``?format=`` query parameter.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `select_renderer` | `def select_renderer(self, request: Any)` | Return ``(renderer_instance, media_type)`` for the request. |

### `ControllerRouteMatch`

- Source: `aquilia/controller/router.py`
- Bases: `object`
- Summary: Result of a successful controller route match.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `route` | `CompiledRoute` | `` |
| `params` | `dict[str, Any]` | `` |
| `query` | `dict[str, Any]` | `` |

### `ControllerRouter`

- Source: `aquilia/controller/router.py`
- Bases: `object`
- Summary: Router for controller-based routes using pattern matching.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `add_controller` | `def add_controller(self, compiled_controller: CompiledController)` | Add a compiled controller to the router. |
| `initialize` | `def initialize(self)` | Build fast-path lookup structures including segment trie. |
| `match_sync` | `def match_sync(self, path: str, method: str, query_params: dict[str, str] \| None=None, api_version: Any \| None=None)` | Synchronous route matching -- the hot path. |
| `get_allowed_methods` | `def get_allowed_methods(self, path: str)` | Return the HTTP methods registered for *path* (normalised). |
| `match` | `async def match(self, path: str, method: str, query_params: dict[str, str] \| None=None, api_version: Any \| None=None)` | Async compat wrapper -- delegates to sync hot path. |
| `get_routes` | `def get_routes(self)` | Get all registered routes. |
| `get_routes_full` | `def get_routes_full(self)` | Get all CompiledRoute objects. |
| `get_controller` | `def get_controller(self, name: str)` | Get compiled controller by name. |
| `has_route` | `def has_route(self, method: str, path: str)` | Check if a route exists. |
| `url_for` | `def url_for(self, name: str, *, api_version: str \| None=None, **params)` | Reverse URL generation. |
