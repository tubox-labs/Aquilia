# Controller Module

> `aquilia.controller` — HTTP API framework with route decorators, validation, and rendering

The Controller module provides the core HTTP API framework: `Controller` base class, route decorators (`@GET`, `@POST`, etc.), request context, filtering, pagination, content negotiation, and OpenAPI generation.

## When to Use

Use the Controller module when building HTTP API endpoints with:

- Class-based controllers with route decorators
- Request body validation via blueprints
- Pagination (page number, limit/offset, cursor-based)
- Filtering and search
- Content negotiation (JSON, XML, YAML, HTML)
- Automatic OpenAPI spec generation

## Key Classes

| Class | Purpose |
|---|---|
| `Controller` | Base class for HTTP controllers |
| `RequestCtx` | Per-request context with DI, identity, session |
| `ControllerMetadata` | Extracted controller metadata |
| `ControllerRouter` | Compiled route table with matching |
| `OpenAPIGenerator` | Auto-generates OpenAPI 3.0 specs |
| `PageNumberPagination` | `?page=2&page_size=20` pagination |
| `LimitOffsetPagination` | `?limit=20&offset=40` pagination |
| `CursorPagination` | Cursor-based pagination |
| `NoPagination` | Disables pagination |
| `BaseFilterBackend` | Abstract filter backend |
| `FilterSet` | Declarative query filtering |
| `SearchFilter` | `?search=term` full-text search |
| `OrderingFilter` | `?ordering=-created_at` result ordering |
| `JSONRenderer` | JSON response renderer |
| `XMLRenderer` | XML response renderer |
| `YAMLRenderer` | YAML response renderer |
| `HTMLRenderer` | HTML response renderer |
| `PlainTextRenderer` | Plain text response renderer |
| `ContentNegotiator` | Accept header negotiation |

## Route Decorators

```python
from aquilia.controller import GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS, TRACE, WS
```

## Quick Example

```python
from aquilia import Controller, GET, POST, DELETE, RequestCtx, Response

class ArticlesController(Controller):
    prefix = "/articles"
    tags = ["articles"]

    @GET("/")
    async def list(self, ctx: RequestCtx):
        return Response.json({"articles": []})

    @POST("/", status_code=201)
    async def create(self, ctx: RequestCtx):
        body = await ctx.json()
        return Response.json({"created": body}, status=201)

    @GET("/<article_id:str>")
    async def detail(self, ctx: RequestCtx, article_id: str):
        return Response.json({"id": article_id})
```

## Import Path

```python
from aquilia.controller import (
    Controller,
    RequestCtx,
    GET,
    POST,
    PUT,
    PATCH,
    DELETE,
    HEAD,
    OPTIONS,
    TRACE,
    WS,
    ControllerRouter,
    ControllerMetadata,
    OpenAPIGenerator,
    PageNumberPagination,
    LimitOffsetPagination,
    CursorPagination,
    NoPagination,
    FilterSet,
    SearchFilter,
    OrderingFilter,
    BaseFilterBackend,
    JSONRenderer,
    XMLRenderer,
    YAMLRenderer,
    HTMLRenderer,
    PlainTextRenderer,
    ContentNegotiator,
)
```

## Related Modules

- [core/request](../core/request.md) — `Request` object available via `RequestCtx`
- [core/response](../core/response.md) — `Response` builders returned by controllers
- [core/flow](../core/flow.md) — Flow pipelines attached to routes
- [blueprints](../blueprints/index.md) — Request body validation in controllers