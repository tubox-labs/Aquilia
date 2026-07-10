---
title: "HTTP Decorators"
description: "Route decorators for defining HTTP endpoints"
icon: lucide/braces
---
## Overview

!!! info
    HTTP decorators attach metadata to controller methods for compile-time extraction without import-time side effects (lines 30-177).


All HTTP method decorators inherit from the `RouteDecorator` base class, which provides a declarative interface for defining routes. The decorator system uses Python's function metadata (`__route_metadata__`) to store route configuration that is later compiled by the framework.

!!! info
    The base `RouteDecorator.__call__` method attaches metadata to functions and performs deduplication to prevent the same method+path combination from being registered twice (lines 140-145).


### Key Features

- **Metadata-driven**: Decorators attach metadata without executing logic at import time
- **Deduplication**: Prevents duplicate route registration for the same method+path pair (lines 140-145)
- **Version binding**: Supports route-level API versioning (lines 164-172)
- **Pipeline support**: Override controller-level pipelines per route
- **OpenAPI integration**: Automatic documentation generation from decorator parameters

## Decorator Inventory

Aquilia provides decorators for all standard HTTP methods plus WebSocket support:

| Decorator | HTTP Method | Line Range | Description |
|-----------|-------------|------------|-------------|
| `@GET` | GET | 180-227 | Retrieve resources |
| `@POST` | POST | 230-277 | Create resources |
| `@PUT` | PUT | 280-327 | Replace resources |
| `@PATCH` | PATCH | 330-377 | Partial updates |
| `@DELETE` | DELETE | 380-427 | Remove resources |
| `@HEAD` | HEAD | 430-477 | Headers-only GET |
| `@OPTIONS` | OPTIONS | 480-527 | Supported methods |
| `@TRACE` | TRACE | 530-577 | Diagnostic echo |
| `@WS` | WebSocket | 580-627 | WebSocket handler |
| `@route()` | Custom/Multiple | 630-739 | Multi-method decorator |

!!! info
    Valid HTTP methods are defined in `VALID_HTTP_METHODS` frozenset (lines 13-23): GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS, TRACE, and WS.


## Universal Parameters

All `RouteDecorator` subclasses accept the following parameters in their `__init__` method (lines 37-122):

### Path & Method

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | `str \| None` | `None` | URL path template (e.g., `"/"`, `"/{id:int}"`) - derives from method name if None |
| `method` | `str \| None` | Set by subclass | HTTP method (GET, POST, etc.) |

### OpenAPI Documentation

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `summary` | `str \| None` | `None` | OpenAPI summary |
| `description` | `str \| None` | `None` | OpenAPI description |
| `tags` | `list[str] \| None` | `None` | OpenAPI tags (extends class-level) |
| `deprecated` | `bool` | `False` | Mark as deprecated in OpenAPI |

### Request/Response Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `response_model` | `type \| None` | `None` | Response type for OpenAPI |
| `status_code` | `int` | `200` | Default HTTP status code |
| `request_contract` | `type \| None` | `None` | Aquilia Contract class for request body casting and sealing |
| `response_contract` | `type \| None` | `None` | Aquilia Contract class (or ProjectedRef) for response molding |

### Filtering, Searching, Ordering

!!! info
    Filter parameters (lines 56-59) enable declarative query parameter filtering without manual parsing.


| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `filterset_class` | `type \| None` | `None` | FilterSet subclass for declarative filtering |
| `filterset_fields` | `list[str] \| Any \| None` | `None` | List of field names (exact-match) or dict mapping fields to lookup lists |
| `search_fields` | `list[str] \| None` | `None` | Field names for text search (activated via `?search=<term>`) |
| `ordering_fields` | `list[str] \| None` | `None` | Fields allowed for dynamic ordering (activated via `?ordering=<field>`) |

### Pagination

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `pagination_class` | `type \| None` | `None` | Pagination backend (PageNumberPagination, LimitOffsetPagination, CursorPagination) |

### Content Negotiation

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `renderer_classes` | `list[Any] \| None` | `None` | List of renderer instances/classes for content negotiation |

### Performance & Security

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `pipeline` | `list[Any] \| None` | `None` | Method-level pipeline nodes (overrides class-level) |
| `throttle` | `Any \| None` | `None` | Per-route Throttle override |
| `timeout` | `float \| None` | `None` | Per-route handler timeout (seconds) |

### API Versioning

!!! info
    The `version` parameter (lines 71-74, 164-172) binds routes to specific API versions, overriding controller-level versioning.


| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `version` | `str \| list[str] \| None` | `None` | Single version (e.g., `"2.0"`) or list (e.g., `["1.0", "2.0"]`) - overrides controller `version` attribute |

## Multi-method route() Decorator

!!! info
    The `route()` function (lines 630-739) accepts a single method or list of methods to bind multiple HTTP verbs to one handler.


The `@route()` decorator provides a generic interface for defining routes with custom or multiple HTTP methods:

```python
@route(method: str | list[str], path: str | None = None, **kwargs)
```

### Method Validation

!!! warning
    The decorator validates methods against `VALID_HTTP_METHODS` and raises `ConfigInvalidFault` for invalid methods (lines 704-712).


```python
# Single method
@route("GET", "/users")
async def get_users(self, ctx):
    ...

# Multiple methods
@route(["GET", "POST"], "/items")
async def handle_items(self, ctx):
    if ctx.method == "GET":
        # Handle GET
        ...
    else:
        # Handle POST
        ...
```

### Internal Implementation

!!! info
    The `route()` decorator uses a method map (lines 693-703) to dispatch to the appropriate decorator class (GET, POST, etc.) for each specified method.


For each method in the list, `route()` instantiates the corresponding decorator class and applies it to the function (lines 715-735).

## WebSocket Handler (@WS)

!!! info
    The `@WS` decorator (lines 580-627) marks a method as a WebSocket handler with method type "WS".


WebSocket routes use the same parameter interface as HTTP decorators:

```python
from aquilia.controller import Controller, WS

class ChatController(Controller):
    prefix = "/chat"
    
    @WS("/ws")
    async def websocket_handler(self, ctx):
        websocket = ctx.request.websocket
        
        await websocket.accept()
        
        try:
            while True:
                message = await websocket.receive_text()
                await websocket.send_text(f"Echo: {message}")
        except Exception:
            await websocket.close()
```

!!! info
    WebSocket routes are registered with HTTP method "WS" in the route metadata (line 585) and validated like other HTTP methods (line 15).


## Version Binding

!!! info
    Routes store version metadata in `__version_metadata__` (lines 164-172) for server registration, with automatic deduplication of version lists.


Route-level versioning overrides controller-level version attributes:

```python
from aquilia.controller import Controller, GET

class UserController(Controller):
    prefix = "/users"
    version = "1.0"  # Controller-level version
    
    @GET("/")
    async def list_users(self, ctx):
        # Available in v1.0 only
        ...
    
    @GET("/profile", version="2.0")
    async def get_profile(self, ctx):
        # Available in v2.0 only (overrides controller version)
        ...
    
    @GET("/stats", version=["1.0", "2.0"])
    async def get_stats(self, ctx):
        # Available in both versions
        ...
```

### Version Metadata Storage

When a route specifies `version`, the decorator:

1. Creates or reuses `__version_metadata__` dict on the function (line 165)
2. Normalizes single version to list (line 168)
3. Deduplicates and merges with existing versions (lines 169-171)

## Metadata Deduplication

!!! info
    The decorator prevents duplicate route registration by checking if a route with the same `http_method` and `path` already exists (lines 140-145).


This prevents errors when decorators are applied multiple times:

```python
@GET("/users")
@GET("/users")  # Silently ignored - same method+path
async def list_users(self, ctx):
    ...
```

The deduplication logic:

```python
# Deduplicate: don't add the same method+path twice
for existing in func_any.__route_metadata__:
    if existing["http_method"] == self.method and existing["path"] == self.path:
        return func  # Skip adding duplicate
```

## Code Examples

### Basic Route Definition

```python
from aquilia.controller import Controller, GET, POST, DELETE

class ArticleController(Controller):
    prefix = "/articles"
    
    @GET("/")
    async def list_articles(self, ctx):
        """List all articles."""
        return {"articles": [...]}
    
    @GET("/{id:int}")
    async def get_article(self, ctx, id: int):
        """Get article by ID."""
        return {"article": {...}}
    
    @POST("/", status_code=201)
    async def create_article(self, ctx):
        """Create a new article."""
        body = await ctx.json()
        return {"article": {...}}
    
    @DELETE("/{id:int}", status_code=204)
    async def delete_article(self, ctx, id: int):
        """Delete an article."""
        # Delete logic
        return None
```

### Request/Response Contracts

```python
from aquilia.contract import Contract
from aquilia.controller import Controller, POST, GET

class CreateUserInput(Contract):
    username: str
    email: str
    age: int

class UserOutput(Contract):
    id: int
    username: str
    email: str

class UserController(Controller):
    prefix = "/users"
    
    @POST(
        "/",
        request_contract=CreateUserInput,
        response_contract=UserOutput,
        status_code=201
    )
    async def create_user(self, ctx, body: CreateUserInput):
        # body is automatically validated and cast
        user = await self.user_service.create(body)
        # response is automatically molded to UserOutput
        return user
```

### Filtering and Pagination

```python
from aquilia.controller import Controller, GET
from aquilia.controller.pagination import PageNumberPagination

class ProductController(Controller):
    prefix = "/products"
    
    @GET(
        "/",
        filterset_fields=["category", "price"],
        search_fields=["name", "description"],
        ordering_fields=["price", "created_at"],
        pagination_class=PageNumberPagination
    )
    async def list_products(self, ctx):
        """
        List products with filtering, search, ordering, and pagination.
        
        Query parameters:
        - category: Filter by category
        - price: Filter by exact price
        - search: Search in name and description
        - ordering: Sort by field (prefix with '-' for descending)
        - page: Page number
        - page_size: Items per page
        """
        products = await self.product_service.list()
        return products  # Automatically filtered and paginated
```

### Content Negotiation

```python
from aquilia.controller import Controller, GET
from aquilia.controller.renderers import JSONRenderer, XMLRenderer

class DataController(Controller):
    prefix = "/data"
    
    @GET(
        "/export",
        renderer_classes=[JSONRenderer(), XMLRenderer()]
    )
    async def export_data(self, ctx):
        """
        Export data in JSON or XML based on Accept header.
        
        Examples:
        - Accept: application/json → JSON response
        - Accept: application/xml → XML response
        """
        return {"data": [...]}
```

### Pipeline and Throttle Overrides

```python
from aquilia.controller import Controller, GET, POST, Throttle

class AdminController(Controller):
    prefix = "/admin"
    throttle = Throttle(limit=100, window=60, max_clients=1000)
    
    @GET("/stats")
    async def get_stats(self, ctx):
        # Uses controller-level throttle
        ...
    
    @POST(
        "/reset",
        throttle=Throttle(limit=5, window=60, max_clients=100),  # Stricter limit
        timeout=30.0  # 30-second timeout
    )
    async def reset_system(self, ctx):
        # Uses route-specific throttle and timeout
        ...
```

### Deprecated Routes

```python
from aquilia.controller import Controller, GET

class LegacyController(Controller):
    prefix = "/legacy"
    
    @GET("/old-endpoint", deprecated=True)
    async def old_endpoint(self, ctx):
        """
        This endpoint is deprecated. Use /new-endpoint instead.
        """
        return {"message": "Please use /new-endpoint"}
    
    @GET("/new-endpoint")
    async def new_endpoint(self, ctx):
        return {"message": "New endpoint"}
```

### Multi-method Routes

```python
from aquilia.controller import Controller, route

class FlexibleController(Controller):
    prefix = "/flexible"
    
    @route(["GET", "POST"], "/data")
    async def handle_data(self, ctx):
        if ctx.method == "GET":
            return {"data": [...]}
        else:  # POST
            body = await ctx.json()
            return {"created": body}
    
    @route("PATCH", "/{id:int}")
    async def partial_update(self, ctx, id: int):
        # Explicitly use route() for single method
        body = await ctx.json()
        return {"updated": id}
```
