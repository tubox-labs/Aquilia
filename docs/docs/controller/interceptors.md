---
title: "Interceptors"
description: "Request/response interceptors"
icon: lucide/waypoints
---## Purpose

Interceptors wrap handler execution with before/after logic, enabling cross-cutting concerns like logging, caching, timing, authentication checks, and response transformation. They provide a clean separation between business logic and infrastructure concerns.

Common use cases:
- **Logging and monitoring**: Record request/response timing and metadata
- **Caching**: Check cache before handler execution, store results after
- **Response transformation**: Add computed fields, format data, inject headers
- **Request validation**: Perform additional validation before handler runs
- **Audit trails**: Track who accessed what and when

## Interceptor API

The `Interceptor` base class defines before/after hooks (lines 333-370):

```python
class Interceptor:
    async def before(self, ctx: "RequestCtx") -> Optional["Response"]:
        """
        Called before the handler executes.
        
        Return a ``Response`` to short-circuit the handler.
        Return ``None`` to continue.
        """
        return None

    async def after(
        self,
        ctx: "RequestCtx",
        result: Any,
    ) -> Any:
        """
        Called after the handler executes.
        
        Receives the handler result and can transform it.
        """
        return result
```

### `before` Method Signature

```python
async def before(self, ctx: RequestCtx) -> Optional[Response]
```

- **`ctx`**: The current request context
- **Returns**: 
  - `None` to continue to the handler
  - A `Response` object to short-circuit execution (see Short-circuiting section)

The `before` method is invoked before the controller handler executes. Use it to:
- Set up request-scoped state in `ctx.state`
- Perform validation or authorization checks
- Check caches or early-exit conditions

### `after` Method Signature

```python
async def after(self, ctx: RequestCtx, result: Any) -> Any
```

- **`ctx`**: The current request context
- **`result`**: The return value from the controller handler
- **Returns**: The transformed result (or the original result if no transformation)

The `after` method is invoked after the handler completes successfully. Use it to:
- Transform handler results (add fields, format data)
- Add computed metadata
- Log results or send metrics

## Registration

Interceptors are registered at the controller class level using the `interceptors` attribute (line 436):

```python
class UsersController(Controller):
    prefix = "/users"
    interceptors = [TimingInterceptor(), CacheInterceptor()]
```

The `interceptors` list is automatically copied for each controller class by the `_ControllerMeta` metaclass (lines 427-440), ensuring each controller has its own list.

## Short-circuiting

If the `before()` method returns a `Response` object instead of `None`, the handler execution is **short-circuited**—the handler never runs, and the response is returned immediately.

This is useful for:
- Returning cached responses without hitting the handler
- Rejecting requests early (custom authorization, rate limiting)
- Implementing fast-path optimizations

**Example:**

```python
class CacheInterceptor(Interceptor):
    def __init__(self, cache):
        self.cache = cache

    async def before(self, ctx):
        # Check cache
        cache_key = f"{ctx.method}:{ctx.path}"
        cached = await self.cache.get(cache_key)
        
        if cached is not None:
            # Short-circuit: return cached response without calling handler
            return Response.json(cached)
        
        # Store cache key for after() hook
        ctx.state["cache_key"] = cache_key
        return None  # Continue to handler

    async def after(self, ctx, result):
        # Store result in cache
        cache_key = ctx.state.get("cache_key")
        if cache_key:
            await self.cache.set(cache_key, result, ttl=300)
        return result
```

When `before()` returns a `Response`:
- The controller handler is **not executed**
- The `after()` method **is still called** with the short-circuit response as `result`
- Exception filters do not apply (no exception was raised)

## Result Transformation

The `after()` method receives the handler's return value and can transform it before it's converted into an HTTP response.

**Common transformations:**
- Add computed fields (timestamps, pagination metadata)
- Inject context-specific data (user preferences, feature flags)
- Format or normalize data structures
- Add response headers via `ctx.state`

**Example:**

```python
class MetadataInterceptor(Interceptor):
    async def after(self, ctx, result):
        # Only transform dict results
        if isinstance(result, dict):
            result["_metadata"] = {
                "request_id": ctx.request_id,
                "timestamp": time.time(),
                "version": "v1",
            }
        return result
```

## Working Example

Here's a complete timing interceptor that measures handler execution time:

```python
import time
from aquilia.controller import Controller, Interceptor
from aquilia.response import Response

class TimingInterceptor(Interceptor):
    """Record request timing and inject into response."""

    async def before(self, ctx):
        # Store start time in request state
        ctx.state["_start_time"] = time.monotonic()
        return None  # Continue to handler

    async def after(self, ctx, result):
        # Calculate elapsed time
        start = ctx.state.get("_start_time")
        if start is not None:
            elapsed = time.monotonic() - start
            elapsed_ms = round(elapsed * 1000, 2)
            
            # Inject timing into dict results
            if isinstance(result, dict):
                result["_elapsed_ms"] = elapsed_ms
            
            # Log slow requests
            if elapsed_ms > 1000:
                logger.warning(
                    f"Slow request: {ctx.method} {ctx.path} took {elapsed_ms}ms"
                )
        
        return result


class LoggingInterceptor(Interceptor):
    """Log all requests and responses."""

    async def before(self, ctx):
        logger.info(f"→ {ctx.method} {ctx.path} [{ctx.request_id}]")
        return None

    async def after(self, ctx, result):
        logger.info(f"← {ctx.method} {ctx.path} [{ctx.request_id}]")
        return result


class UsersController(Controller):
    prefix = "/users"
    interceptors = [TimingInterceptor(), LoggingInterceptor()]

    @GET("/{user_id}")
    async def get_user(self, ctx, user_id: int):
        user = await self.repo.get_by_id(user_id)
        return {"user": user}
        # Response will include "_elapsed_ms" field automatically
```

**Output example:**

```json
{
  "user": {
    "id": 123,
    "name": "Alice"
  },
  "_elapsed_ms": 45.23
}
```

## Interceptor vs Pipeline

Both interceptors and pipelines provide request/response processing, but they serve different purposes:

| Feature | Interceptor | Pipeline |
|---------|-------------|----------|
| **Scope** | Controller-level | Route-level or controller-level |
| **Use case** | Cross-cutting concerns (timing, logging, caching) | Request validation, auth, dependency injection |
| **API** | `before()` / `after()` methods | `run()` method returning `Request` or `Response` |
| **Short-circuit** | Return `Response` from `before()` | Return `Response` from `run()` |
| **Result transformation** | Yes, via `after()` | No (works with request/response only) |
| **Execution order** | After pipeline, wraps handler | Before handler, before interceptors |
| **Registration** | `interceptors = [...]` | `pipeline = [...]` |

**Execution flow:**

```
Request
  ↓
Pipeline nodes (Auth, guards, validation)
  ↓
Interceptor.before()  ← Can short-circuit
  ↓
Controller handler
  ↓
Interceptor.after()   ← Can transform result
  ↓
Response
```

**When to use what:**

- **Use pipelines** for: Authentication, authorization, input validation, dependency injection
- **Use interceptors** for: Logging, timing, caching, response transformation, audit trails

Both can be used together—pipelines handle request processing and access control, while interceptors handle cross-cutting concerns and response enhancement.
