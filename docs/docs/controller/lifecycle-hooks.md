---
title: "Lifecycle Hooks"
description: "Understanding and hook-in to the Aquilia Controller execution lifecycle"
icon: lucide/activity
---
## Overview

Aquilia controllers provide hook methods that allow you to execute logic at key points in the application and request lifecycle. These hooks support database connections, logging, custom validations, and response manipulations.

---

## Startup & Shutdown Hooks

!!! info
    Evidence: `aquilia/controller/base.py:615-629`


These hooks are executed when the controller itself starts up or shuts down.

### on_startup

[on_startup](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/base.py#L615-L621) is called when the controller is initialized. 

> [!NOTE]
> This hook is executed **only in singleton instantiation mode**.

- **Signature**: `async def on_startup(self, ctx: RequestCtx) -> None`
- **Use Case**: One-time setup operations, such as establishing persistent database pools or opening HTTP client sessions.

### on_shutdown

[on_shutdown](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/base.py#L623-L629) is called when the controller is destroyed.

> [!NOTE]
> This hook is executed **only in singleton instantiation mode**.

- **Signature**: `async def on_shutdown(self, ctx: RequestCtx) -> None`
- **Use Case**: Cleanup operations, such as closing database connection pools or terminating background tasks.

---

## Request & Response Hooks

!!! info
    Evidence: `aquilia/controller/base.py:631-652`


These hooks execute on every HTTP request processed by the controller's route handlers.

### on_request

[on_request](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/base.py#L631-L637) is called immediately before the matched handler method is executed.

- **Signature**: `async def on_request(self, ctx: RequestCtx) -> None`
- **Use Case**: Setting request-scoped parameters in `ctx.state`, logging request entry, or executing controller-wide preprocessing.

### on_response

[on_response](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/base.py#L639-L652) is called after the handler method has successfully executed and returned a `Response` object.

- **Signature**: `async def on_response(self, ctx: RequestCtx, response: "Response") -> "Response"`
- **Use Case**: Modifying headers (e.g., adding caching headers or security headers), logging execution time, or transforming response payloads.

---

## Code Example

```python
import time
from aquilia import Controller, GET, RequestCtx, Response

class LifecycleDemoController(Controller):
    prefix = "/lifecycle"
    instantiation_mode = "singleton"

    async def on_startup(self, ctx: RequestCtx) -> None:
        # Initialize resources
        self.start_time = time.time()

    async def on_shutdown(self, ctx: RequestCtx) -> None:
        # Cleanup resources
        pass

    async def on_request(self, ctx: RequestCtx) -> None:
        # Track start time of the request
        ctx.state["start_time"] = time.perf_counter()

    async def on_response(self, ctx: RequestCtx, response: Response) -> Response:
        # Calculate request execution duration and append header
        duration = time.perf_counter() - ctx.state["start_time"]
        response.headers["X-Process-Time"] = f"{duration:.4f}s"
        return response

    @GET("/ping")
    async def ping(self, ctx: RequestCtx) -> dict:
        return {"message": "pong"}
```
