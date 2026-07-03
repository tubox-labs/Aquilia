---
title: "Defining Controllers"
description: "How to define and configure Aquilia Controller classes"
icon: lucide/code-2
---
## Overview

Controllers are class-based request handlers in Aquilia that provide a structured approach to building APIs.

!!! info
    📎 aquilia/controller/base.py:497-662


Controllers support:
- Constructor dependency injection
- Method-level route definitions with decorators
- Class-level and method-level pipelines
- Lifecycle hooks for startup, shutdown, request, and response processing
- Template rendering support
- API versioning
- Rate limiting (throttle)
- Interceptors (before/after handler hooks)
- Exception filters (structured error handling)
- Handler execution timeouts

!!! info
    📎 aquilia/controller/base.py:503-550


## Minimal Controller Example

The simplest controller inherits from `Controller` and defines routes using HTTP method decorators:

```python
from aquilia import Controller, GET

class UsersController(Controller):
    prefix = "/users"
    
    @GET("/")
    async def list(self, ctx):
        return {"users": []}
```

!!! info
    📎 aquilia/controller/base.py:497


The `prefix` attribute defines the base URL path for all routes in the controller.

!!! info
    📎 aquilia/controller/base.py:525


## Class-Level Configuration

Controllers support extensive class-level configuration through attributes:

### prefix

URL prefix prepended to all routes in the controller.

```python
class UsersController(Controller):
    prefix = "/api/users"
```

!!! info
    📎 aquilia/controller/base.py:525


### pipeline

List of pipeline nodes applied to all methods in the controller.

```python
class UsersController(Controller):
    prefix = "/users"
    pipeline = [Auth.guard()]
```

!!! info
    📎 aquilia/controller/base.py:526


Pipelines enable authentication, authorization, validation, and other cross-cutting concerns.

### tags

OpenAPI tags for documentation and API organization.

```python
class UsersController(Controller):
    prefix = "/users"
    tags = ["users", "authentication"]
```

!!! info
    📎 aquilia/controller/base.py:527


### instantiation_mode

Controls controller lifecycle: `"per_request"` (default) or `"singleton"`.

```python
class UsersController(Controller):
    instantiation_mode = "singleton"
```

!!! info
    📎 aquilia/controller/base.py:528


- `"per_request"`: New instance created for each request
- `"singleton"`: Single instance shared across all requests

### version

API version string for versioned APIs.

```python
class UsersController(Controller):
    prefix = "/users"
    version = "v1"
```

!!! info
    📎 aquilia/controller/base.py:531


### throttle

Rate limiting configuration using the `Throttle` class.

```python
from aquilia import Controller, Throttle

class UsersController(Controller):
    prefix = "/users"
    throttle = Throttle(limit=100, window=60)  # 100 requests per 60 seconds
```

!!! info
    📎 aquilia/controller/base.py:532


The throttle instance implements sliding-window rate limiting.

!!! info
    📎 aquilia/controller/base.py:355-460


Throttle constructor accepts:
- `limit`: Maximum number of requests
- `window`: Time window in seconds
- `max_clients`: Maximum tracked clients (default 10000)

!!! info
    📎 aquilia/controller/base.py:370-375


### interceptors

List of `Interceptor` instances that wrap handler execution with before/after logic.

```python
class TimingInterceptor(Interceptor):
    async def before(self, ctx):
        ctx.state["_start"] = time.monotonic()
    
    async def after(self, ctx, result):
        elapsed = time.monotonic() - ctx.state["_start"]
        return result

class UsersController(Controller):
    prefix = "/users"
    interceptors = [TimingInterceptor()]
```

!!! info
    📎 aquilia/controller/base.py:533


Interceptors support cross-cutting concerns like logging, caching, timing, and response transformation.

!!! info
    📎 aquilia/controller/base.py:303-347


### exception_filters

List of `ExceptionFilter` instances that handle exceptions from controller handlers.

```python
class NotFoundFilter(ExceptionFilter):
    catches = [KeyError, LookupError]
    
    async def catch(self, exception, ctx):
        return Response.json(
            {"error": "Not found", "detail": str(exception)},
            status=404
        )

class UsersController(Controller):
    prefix = "/users"
    exception_filters = [NotFoundFilter()]
```

!!! info
    📎 aquilia/controller/base.py:534


Exception filters convert unhandled exceptions into proper HTTP responses.

!!! info
    📎 aquilia/controller/base.py:260-295


### timeout

Handler execution timeout in seconds. Set to `0` to disable (default).

```python
class UsersController(Controller):
    prefix = "/users"
    timeout = 30  # 30 second timeout
```

!!! info
    📎 aquilia/controller/base.py:535


### max_body_size

Maximum request body size in bytes. Set to `0` to disable (default).

```python
class UsersController(Controller):
    prefix = "/users"
    max_body_size = 1048576  # 1 MB limit
```

!!! info
    📎 aquilia/controller/base.py:536


## Lifecycle Hooks

Controllers provide four lifecycle hooks for initialization and request/response processing:

### on_startup

Called when the controller is initialized (singleton mode only).

```python
class UsersController(Controller):
    instantiation_mode = "singleton"
    
    async def on_startup(self, ctx: RequestCtx) -> None:
        # One-time initialization
        await self.db.connect()
```

!!! info
    📎 aquilia/controller/base.py:615-621


**Signature:**
```python
async def on_startup(self, ctx: RequestCtx) -> None
```

Use for one-time initialization like opening database connections.

### on_shutdown

Called when the controller is destroyed (singleton mode only).

```python
class UsersController(Controller):
    instantiation_mode = "singleton"
    
    async def on_shutdown(self, ctx: RequestCtx) -> None:
        # Cleanup
        await self.db.disconnect()
```

!!! info
    📎 aquilia/controller/base.py:623-629


**Signature:**
```python
async def on_shutdown(self, ctx: RequestCtx) -> None
```

Use for cleanup like closing connections.

### on_request

Called before each request is processed.

```python
class UsersController(Controller):
    async def on_request(self, ctx: RequestCtx) -> None:
        # Per-request initialization
        ctx.state["request_time"] = time.time()
```

!!! info
    📎 aquilia/controller/base.py:631-637


**Signature:**
```python
async def on_request(self, ctx: RequestCtx) -> None
```

Use for per-request initialization or validation.

### on_response

Called after each request is processed, allowing response modification.

```python
class UsersController(Controller):
    async def on_response(self, ctx: RequestCtx, response: Response) -> Response:
        # Add custom headers
        response.headers["X-Request-Time"] = str(time.time())
        return response
```

!!! info
    📎 aquilia/controller/base.py:639-652


**Signature:**
```python
async def on_response(self, ctx: RequestCtx, response: Response) -> Response
```

The hook receives the response object and must return a (potentially modified) response.

## DI Constructor Injection

Controllers support dependency injection through constructor parameters:

```python
from typing import Annotated
from aquilia import Controller, Inject

class UsersController(Controller):
    prefix = "/users"
    
    def __init__(
        self, 
        repo: Annotated[UserRepo, Inject(tag="repo")],
        templates: TemplateEngine
    ):
        self.repo = repo
        self.templates = templates
    
    @GET("/")
    async def list(self, ctx):
        users = await self.repo.list_all()
        return users
```

!!! info
    📎 aquilia/controller/base.py:497-662


Constructor parameters are automatically resolved from the dependency injection container. The controller factory analyzes the constructor signature and resolves dependencies at runtime.

!!! warning
    ⚠️ Constructor analysis implemented in factory.py (not inspected in current session).


## Template Rendering

Controllers provide a built-in `render` method for template rendering:

```python
class UsersController(Controller):
    prefix = "/users"
    
    def __init__(self, templates: TemplateEngine):
        self._template_engine = templates
    
    @GET("/{id}")
    async def profile(self, ctx, id: int):
        user = await self.repo.get(id)
        return await self.render("profile.html", {"user": user}, ctx)
```

!!! info
    📎 aquilia/controller/base.py:566-611


**Signature:**
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
) -> Response
```

The render method:
- Accepts template name and context dictionary
- Automatically injects request context if available
- Supports custom template engine via parameter or `_template_engine` attribute
- Returns a Response object with rendered HTML

!!! info
    📎 aquilia/controller/base.py:566-611


If `request_ctx` is not provided, the method attempts to retrieve it from the current context automatically.

!!! info
    📎 aquilia/controller/base.py:581-582


## Async Context Manager

Controllers implement the async context manager protocol for per-request lifecycle management:

```python
async with controller_instance:
    # Controller lifetime for this request
    result = await controller_instance.handler(ctx)
```

!!! info
    📎 aquilia/controller/base.py:656-662


**Signatures:**
```python
async def __aenter__(self)
async def __aexit__(self, exc_type, exc_val, exc_tb)
```

This enables proper resource management for per-request controller instances.

!!! info
    📎 aquilia/controller/base.py:656-662

