# controller Module

## Purpose

Controller, router, compiler, renderer, filter, pagination, and OpenAPI layer. Use this module to define HTTP routes with decorators, compile controllers into runtime routes, execute handlers, negotiate responses, filter datasets, paginate, and emit OpenAPI docs.

## Source Coverage

- Python files: 12
- Public classes: 48
- Dataclasses: 8
- Enums: 1
- Public functions: 10

## How It Fits In Aquilia

1. Subclass Controller and set prefix, tags, and optional pipeline metadata.
2. Use GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS, TRACE, WS, or route decorators.
3. The compiler extracts metadata, the router matches requests, and ControllerEngine executes handlers through filters, throttles, interceptors, and exception filters.

## Practical Guidance

- Route paths use Aquilia pattern syntax. Keep route prefixes in Workspace Module.route_prefix and endpoint-relative paths in controllers.
- Handler metadata is attached at import time, but routes are compiled later. Avoid route side effects in decorators.

## Public Classes

| Name | Source | Role |
| --- | --- | --- |
| `RequestCtx` | `aquilia/controller/base.py` | Request context provided to controller methods. |
| `ExceptionFilter` | `aquilia/controller/base.py` | Base class for exception filters. |
| `Interceptor` | `aquilia/controller/base.py` | Base class for controller interceptors. |
| `Throttle` | `aquilia/controller/base.py` | Simple in-memory sliding-window rate limiter. |
| `Controller` | `aquilia/controller/base.py` | Base Controller class. |
| `CompiledRoute` | `aquilia/controller/compiler.py` | A compiled controller route with pattern and handler. |
| `CompiledController` | `aquilia/controller/compiler.py` | A fully compiled controller with all routes. |
| `ControllerCompiler` | `aquilia/controller/compiler.py` | Compiles controllers into executable routes with pattern matching. |
| `RouteDecorator` | `aquilia/controller/decorators.py` | Base route decorator. |
| `GET` | `aquilia/controller/decorators.py` | GET request decorator. |
| `POST` | `aquilia/controller/decorators.py` | POST request decorator. |
| `PUT` | `aquilia/controller/decorators.py` | PUT request decorator. |
| `PATCH` | `aquilia/controller/decorators.py` | PATCH request decorator. |
| `DELETE` | `aquilia/controller/decorators.py` | DELETE request decorator. |
| `HEAD` | `aquilia/controller/decorators.py` | HEAD request decorator. |
| `OPTIONS` | `aquilia/controller/decorators.py` | OPTIONS request decorator. |
| `TRACE` | `aquilia/controller/decorators.py` | TRACE request decorator. |
| `WS` | `aquilia/controller/decorators.py` | WebSocket request decorator. |
| `ControllerEngine` | `aquilia/controller/engine.py` | Executes controller methods with complete integration. |
| `InstantiationMode` | `aquilia/controller/factory.py` | Controller instantiation modes. |
| `ControllerFactory` | `aquilia/controller/factory.py` | Factory for creating controller instances. |
| `ScopeViolationError` | `aquilia/controller/factory.py` | Raised when a scope rule is violated. |
| `FilterSetMeta` | `aquilia/controller/filters.py` | Metaclass for FilterSet -- collects ``Meta.fields`` at class creation. |
| `FilterSet` | `aquilia/controller/filters.py` | Declarative filter specification. |
| `BaseFilterBackend` | `aquilia/controller/filters.py` | Abstract base for pluggable filter backends. |
| `SearchFilter` | `aquilia/controller/filters.py` | Text search across multiple fields. |
| `OrderingFilter` | `aquilia/controller/filters.py` | Dynamic field ordering via ``?ordering=<field>`` query parameter. |
| `ParameterMetadata` | `aquilia/controller/metadata.py` | Metadata for a route method parameter. |
| `RouteMetadata` | `aquilia/controller/metadata.py` | Metadata for a single route (controller method). |
| `ControllerMetadata` | `aquilia/controller/metadata.py` | Complete metadata for a Controller class. |
| `ParsedDocstring` | `aquilia/controller/openapi.py` | Parsed handler docstring with structured sections. |
| `OpenAPIConfig` | `aquilia/controller/openapi.py` | Configuration for OpenAPI spec generation. |
| `OpenAPIGenerator` | `aquilia/controller/openapi.py` | Production-grade OpenAPI 3.1.0 specification generator. |
| `BasePagination` | `aquilia/controller/pagination.py` | Abstract base for pagination backends. |
| `NoPagination` | `aquilia/controller/pagination.py` | Passthrough -- no pagination applied. |
| `PageNumberPagination` | `aquilia/controller/pagination.py` | Classic page-number pagination. |
| `LimitOffsetPagination` | `aquilia/controller/pagination.py` | Limit/Offset pagination. |
| `CursorPagination` | `aquilia/controller/pagination.py` | Cursor-based (keyset) pagination -- efficient for very large datasets. |
| `BaseRenderer` | `aquilia/controller/renderers.py` | Abstract renderer. |
| `JSONRenderer` | `aquilia/controller/renderers.py` | Render data as JSON. Default renderer. |
| `XMLRenderer` | `aquilia/controller/renderers.py` | Render data as XML. |
| `YAMLRenderer` | `aquilia/controller/renderers.py` | Render data as YAML. |
| `PlainTextRenderer` | `aquilia/controller/renderers.py` | Render data as plain text (str() conversion). |
| `HTMLRenderer` | `aquilia/controller/renderers.py` | Render pre-built HTML strings (passthrough). |
| `MessagePackRenderer` | `aquilia/controller/renderers.py` | Render data as MessagePack binary (requires ``msgpack``). |
| `ContentNegotiator` | `aquilia/controller/renderers.py` | Select the best renderer for a request based on the ``Accept`` header |
| `ControllerRouteMatch` | `aquilia/controller/router.py` | Result of a successful controller route match. |
| `ControllerRouter` | `aquilia/controller/router.py` | Router for controller-based routes using pattern matching. |

## Public Functions

| Name | Source | Role |
| --- | --- | --- |
| `route` | `aquilia/controller/decorators.py` | Generic route decorator. |
| `apply_filters_to_list` | `aquilia/controller/filters.py` | Apply parsed filter clauses to an in-memory list of dicts / objects. |
| `apply_search_to_list` | `aquilia/controller/filters.py` | Apply text search over *search_fields* on an in-memory list. |
| `apply_ordering_to_list` | `aquilia/controller/filters.py` | Sort an in-memory list by one or more fields. |
| `filter_queryset` | `aquilia/controller/filters.py` | One-shot convenience: apply FilterSet + SearchFilter + OrderingFilter |
| `filter_data` | `aquilia/controller/filters.py` | One-shot convenience: apply FilterSet + SearchFilter + OrderingFilter |
| `extract_controller_metadata` | `aquilia/controller/metadata.py` | Extract metadata from a Controller class. |
| `generate_swagger_html` | `aquilia/controller/openapi.py` | Generate the Swagger UI HTML page. |
| `generate_redoc_html` | `aquilia/controller/openapi.py` | Generate the ReDoc HTML page. |
| `negotiate` | `aquilia/controller/renderers.py` | One-shot content negotiation. |

## Implementation Map

| File | What To Look For |
| --- | --- |
| `aquilia/controller/__init__.py` | Aquilia Controller System |
| `aquilia/controller/base.py` | Controller Base Class |
| `aquilia/controller/compiler.py` | Controller Compiler - Compiles controllers to patterns and routes. |
| `aquilia/controller/decorators.py` | Controller Method Decorators |
| `aquilia/controller/engine.py` | Controller Engine - Executes controller methods with full integration. |
| `aquilia/controller/factory.py` | Controller Factory |
| `aquilia/controller/filters.py` | Aquilia Filter System -- declarative filtering, searching, and ordering. |
| `aquilia/controller/metadata.py` | Controller Metadata Extraction |
| `aquilia/controller/openapi.py` | OpenAPI 3.1.0 Generation for Aquilia Controllers. |
| `aquilia/controller/pagination.py` | Aquilia Pagination System -- declarative pagination backends. |
| `aquilia/controller/renderers.py` | Aquilia Content Negotiation & Renderer System. |
| `aquilia/controller/router.py` | Controller Router - Pattern-based router for controllers. |

## Testing Pointers

Search `tests/` for `controller` to find behavior-level examples. The test suite is especially useful for edge cases because many modules expose lightweight public APIs but enforce important security and lifecycle behavior internally.
