---
title: "Rate Limiting & Interceptors Tutorial"
description: "Configuring request throttles, custom interceptors, and exception filters"
icon: lucide/gauge
---In this tutorial, you will learn how to configure rate limiting (throttling), track request performance, log lifecycle events, and handle throttle exceptions gracefully in Aquilia. 

We will build an API controller step-by-step to demonstrate how these pieces interact within the Aquilia controller pipeline.

---

## Prerequisites

Ensure you have imported the core components of the Aquilia framework. We will build a controller for managing item resources:

```python
from aquilia.controller import Controller, Throttle, Interceptor, ExceptionFilter
from aquilia.decorators import GET, POST
from aquilia.response import Response
```

---

## Step 1: Controller-Level Throttling

Aquilia provides a sliding-window in-memory rate limiter using the `Throttle` class. You can apply a default rate limit across all endpoints in a controller by defining the `throttle` class attribute.

Add a default rate limit of 100 requests per 60 seconds:

```python
class ItemsController(Controller):
    prefix = "/items"
    
    # Class-level rate limiting: 100 requests per 60 seconds
    throttle = Throttle(limit=100, window=60)

    @GET("/")
    async def list_items(self, ctx):
        # Inherits the controller-level throttle (100 reqs / 60s)
        return {"items": ["Item A", "Item B"]}
```

!!! info
    **API Verification & Evidence:**
    As defined in [throttle.mdx](../controller/throttle.md#L133-L157), setting the `throttle` class attribute enforces the rate limiter automatically across all controller handler methods. The sliding-window algorithm isolates clients by resolving their IP addresses.


---

## Step 2: Per-Route Throttle Override

You can customize or entirely disable rate limits for individual routes using the `throttle` parameter directly inside route decorators.

Let's add a strict limit on creation requests (5 requests per 60 seconds) and disable throttling completely for health checks:

```python
class ItemsController(Controller):
    prefix = "/items"
    throttle = Throttle(limit=100, window=60)

    @GET("/")
    async def list_items(self, ctx):
        return {"items": ["Item A", "Item B"]}

    # Route-level override: Stricter limit for POST requests
    @POST("/", throttle=Throttle(limit=5, window=60))
    async def create_item(self, ctx):
        data = await ctx.json()
        return {"status": "created", "item": data}

    # Route-level override: Completely bypass rate limiting
    @GET("/health", throttle=None)
    async def health(self, ctx):
        return {"status": "ok"}
```

!!! info
    **API Verification & Evidence:**
    Route-level overriding is documented in [throttle.mdx](../controller/throttle.md#L159-L223). A route-level `throttle` attribute takes precedence over the controller's default `throttle`. Passing `throttle=None` excludes the route from any checks.


---

## Step 3: Request Performance Timing Interceptor

Interceptors wrap handler execution with before/after logic. We can use a custom interceptor to measure the exact execution duration of a request using `time.perf_counter()` and store the start timestamp in `ctx.state`.

```python
import time

class TimingInterceptor(Interceptor):
    """Record request execution time and inject it into dict responses."""

    async def before(self, ctx):
        # Store start counter in the request state context
        ctx.state["perf_start"] = time.perf_counter()
        return None  # Continue execution pipeline to the handler

    async def after(self, ctx, result):
        start = ctx.state.get("perf_start")
        if start is not None:
            # Measure elapsed time in milliseconds
            elapsed = time.perf_counter() - start
            elapsed_ms = round(elapsed * 1000, 2)
            
            # Inject duration metadata directly into dictionary responses
            if isinstance(result, dict):
                result["_elapsed_ms"] = elapsed_ms
        return result
```

!!! info
    **API Verification & Evidence:**
    As documented in [interceptors.mdx](../controller/interceptors.md#L155-L191), the `before` hook runs before handler execution and allows initializing request-scoped state in `ctx.state`. The `after` hook intercepts and transforms the returned result before sending the response.


---

## Step 4: Request/Response Logging Interceptor

Now let's add a second custom interceptor that logs the lifecycle of every incoming request and outgoing response, utilizing the request ID for tracing.

```python
import logging

logger = logging.getLogger("aquilia.app")

class LoggingInterceptor(Interceptor):
    """Log incoming requests and outgoing responses with tracking IDs."""

    async def before(self, ctx):
        logger.info(f"→ {ctx.method} {ctx.path} [Request ID: {ctx.request_id}]")
        return None

    async def after(self, ctx, result):
        logger.info(f"← {ctx.method} {ctx.path} [Request ID: {ctx.request_id}]")
        return result
```

!!! info
    **API Verification & Evidence:**
    `ctx.request_id`, `ctx.method`, and `ctx.path` are standard, documented properties on `RequestCtx`. As shown in [interceptors.mdx](../controller/interceptors.md#L192-L213), class-level interceptors are registered in the order they appear and execute sequentially.


---

## Step 5: Rate Limit Exception Filter

When doing manual rate limiting or using native faults, you want to return a clean JSON payload and appropriate headers (like `Retry-After`). 

Let's define a custom exception `ThrottleExceeded` for manual throttling checks, and write exception filters to handle both the custom exception and native Aquilia rate-limiting faults (`RateLimitExceededFault` and `TooManyRequestsFault`).

### Custom Exception & Exception Filter

```python
from aquilia.faults import RateLimitExceededFault, TooManyRequestsFault

class ThrottleExceeded(Exception):
    """Raised when a manual rate limit check fails."""
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after}s.")

class ThrottleExceededFilter(ExceptionFilter):
    """Convert ThrottleExceeded exception into 429 Too Many Requests response."""
    catches = [ThrottleExceeded]

    async def catch(self, exception, ctx):
        return Response.json(
            {
                "error": "Rate limit exceeded",
                "detail": str(exception),
                "retry_after": exception.retry_after
            },
            status=429,
            headers={"Retry-After": str(exception.retry_after)}
        )

class NativeThrottleFilter(ExceptionFilter):
    """Convert native Aquilia rate limiting faults into standard 429 responses."""
    catches = [RateLimitExceededFault, TooManyRequestsFault]

    async def catch(self, exception, ctx):
        if isinstance(exception, RateLimitExceededFault):
            retry_after = int(exception.metadata.get("retry_after", 60))
            message = exception.message
        else:  # TooManyRequestsFault
            retry_after = int(exception.metadata.get("retry_after", 60))
            message = exception.detail or f"Retry after {retry_after}s."

        return Response.json(
            {
                "error": "Too Many Requests",
                "detail": message,
                "retry_after": retry_after
            },
            status=429,
            headers={"Retry-After": str(retry_after)}
        )
```

### Complete Controller Assembly

Register the interceptors and exception filters at the class level:

```python
class ItemsController(Controller):
    prefix = "/items"
    
    # Rate Limiting
    throttle = Throttle(limit=100, window=60)
    
    # Interceptors
    interceptors = [TimingInterceptor(), LoggingInterceptor()]
    
    # Exception Filters
    exception_filters = [ThrottleExceededFilter(), NativeThrottleFilter()]

    @GET("/")
    async def list_items(self, ctx):
        return {"items": ["Item A", "Item B"]}

    @POST("/", throttle=Throttle(limit=5, window=60))
    async def create_item(self, ctx):
        data = await ctx.json()
        return {"status": "created", "item": data}

    # Example of raising a custom throttle exception manually
    @GET("/manual-check")
    async def manual_check(self, ctx):
        custom_limiter = Throttle(limit=2, window=10)
        if not custom_limiter.check(ctx.request):
            raise ThrottleExceeded(retry_after=custom_limiter.retry_after)
        return {"status": "allowed"}
```

!!! info
    **API Verification & Evidence:**
    Class-level registration of exception filters is documented in [exception-filters.mdx](../controller/exception-filters.md#L51-L62). The engine matches thrown exceptions against the filters' `catches` definitions sequentially ([exception-filters.mdx](../controller/exception-filters.md#L126-L152)).


---

## Step 6: Testing with curl

You can verify the rate limiting, interceptors, and exception filters using `curl`.

### 1. Test Controller-Level Throttling & Timing

Request the default route to verify the timing interceptor output:

```bash
curl -i http://localhost:8000/items
```

**Success Response (includes timing information):**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "items": [
    "Item A",
    "Item B"
  ],
  "_elapsed_ms": 1.42
}
```

Check your application console logs to see the output from the `LoggingInterceptor`:
```text
INFO:aquilia.app:→ GET /items [Request ID: req_9a8f23c1]
INFO:aquilia.app:← GET /items [Request ID: req_9a8f23c1]
```

### 2. Test Per-Route Throttle Override

Make repeated requests to the stricter route (which has a limit of 5 requests/minute):

```bash
# Execute this command 6 times rapidly:
curl -i -X POST -H "Content-Type: application/json" -d '{"name":"New Item"}' http://localhost:8000/items
```

**Throttled Response (6th request):**
```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
Retry-After: 60

{
  "error": "Too many requests",
  "retry_after": 60
}
```

### 3. Test Manual Throttling and Custom Exception Filter

Make repeated requests to the manual endpoint (which permits only 2 requests per 10 seconds):

```bash
# Execute this command 3 times rapidly:
curl -i http://localhost:8000/items/manual-check
```

**Throttled Response (3rd request, caught by exception filter):**
```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
Retry-After: 10

{
  "error": "Rate limit exceeded",
  "detail": "Rate limit exceeded. Retry after 10s.",
  "retry_after": 10
}
```
