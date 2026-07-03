---
title: "Throttle & Rate Limiting"
description: "Rate limiting with Throttle"
icon: lucide/timer
---## Purpose

The `Throttle` class provides a **sliding-window in-memory rate limiter** for Aquilia controllers (lines 379-481). It tracks request timestamps per client and enforces configurable rate limits to protect against abuse and ensure fair resource allocation.

**Key characteristics:**
- **Sliding window algorithm**: Tracks actual request timestamps, not fixed time buckets
- **In-memory storage**: Fast but ephemeral (resets on application restart)
- **Per-client isolation**: Uses client IP addresses to identify distinct clients
- **Automatic cleanup**: Prevents memory leaks through periodic cleanup and LRU eviction

Evidence: Class docstring at lines 379-390.

## Constructor

```python
Throttle(limit: int = 100, window: int = 60, max_clients: int = 10000)
```

**Parameters:**

- **`limit`** (int, default: 100): Maximum number of requests allowed within the time window
- **`window`** (int, default: 60): Time window in seconds for rate limiting
- **`max_clients`** (int, default: 10000): Maximum number of clients to track before evicting oldest entries

**Defaults:** 100 requests per 60 seconds, tracking up to 10,000 unique clients.

Evidence: Constructor signature at lines 392-397.

## `check()` Method

```python
def check(self, request: Any) -> bool
```

Validates whether a request is within the rate limit.

**Return contract:**
- Returns `True` if the request is **allowed** (within limit)
- Returns `False` if the request is **throttled** (limit exceeded)

**Side effects:**
- Records the current timestamp for allowed requests
- Triggers periodic cleanup when `window` seconds have elapsed since last cleanup
- Evicts the oldest client when `max_clients` limit is reached (LRU eviction)
- Prunes expired timestamps for the current client

Evidence: Method signature and behavior at lines 414-441, with SEC-CTRL-04 security note at lines 419-422.

## Client Identification

### `_client_key()` Method

```python
def _client_key(self, request: Any) -> str
```

Extracts a unique client identifier from the request (lines 399-412).

**Resolution strategy:**
1. **First**: Calls `request.client_ip()` if available — respects trusted proxy chain validation
2. **Fallback**: Extracts direct client IP from ASGI scope `client` tuple
3. **Last resort**: Returns `"unknown"`

**Security note:** Never trusts `X-Forwarded-For` headers directly; relies on Aquilia's validated `client_ip()` method to handle proxy chains correctly.

Evidence: Implementation at lines 399-412 with inline comments about trusted-proxy validation.

## Memory Management

The `Throttle` class implements two memory protection mechanisms to prevent unbounded growth:

### Periodic Cleanup

```python
def _cleanup_expired(self, now: float) -> None
```

Removes all clients whose request timestamps have fully expired (lines 443-447). Triggered automatically during `check()` when `window` seconds have elapsed since the last cleanup (lines 428-430).

**Logic:** Deletes clients where the most recent timestamp is older than `now - window`.

Evidence: Method at lines 443-447, invoked at lines 428-430.

### LRU Eviction

```python
def _evict_oldest(self, now: float) -> None
```

Evicts the client with the oldest last-access time when `max_clients` limit is reached (lines 449-461).

**Trigger:** Automatically called in `check()` when adding a new client would exceed `max_clients` (lines 432-434).

**Algorithm:** Iterates through all tracked clients, finds the one with the oldest most-recent timestamp, and removes it.

Evidence: Method at lines 449-461, invoked at lines 432-434 with SEC-CTRL-04 security annotation.

## `retry_after` Property

```python
@property
def retry_after(self) -> int
```

Returns the number of seconds until the rate limit window resets (lines 463-465).

**Return value:** The configured `window` value (approximate reset time).

**Use case:** Can be used to populate the `Retry-After` HTTP header in 429 (Too Many Requests) responses.

Evidence: Property definition at lines 463-465.

## `reset()` Method

```python
def reset(self) -> None
```

Clears all rate limit state by emptying the internal `_requests` dictionary (lines 467-469).

**Use cases:**
- Testing and development
- Administrative reset operations
- Graceful state clearing

Evidence: Method at lines 467-469.

## Controller-Level Usage

Apply rate limiting to **all routes** in a controller by setting the `throttle` class attribute:

```python
from aquilia.controller import Controller, Throttle
from aquilia.decorators import GET

class UsersController(Controller):
    prefix = "/users"
    throttle = Throttle(limit=100, window=60)  # 100 requests per 60 seconds

    @GET("/")
    async def list(self, ctx):
        return {"users": [...]}

    @GET("/:id")
    async def get(self, ctx):
        user_id = ctx.request.path_params["id"]
        return {"user": {...}}
```

Both `/users` and `/users/:id` will enforce the 100 req/60s limit per client.

Evidence: Class attribute `throttle` at line 583, example usage in docstring at lines 387-390.

## Route-Level Override

Override controller-level throttling for **specific routes** by passing a `throttle` parameter to the route decorator:

```python
class UsersController(Controller):
    prefix = "/users"
    throttle = Throttle(limit=100, window=60)  # Default for all routes

    @GET("/")
    async def list(self, ctx):
        return {"users": [...]}  # Uses controller throttle (100/60s)

    @GET("/search", throttle=Throttle(limit=10, window=60))
    async def search(self, ctx):
        # More restrictive: 10 requests per 60 seconds
        query = ctx.query_param("q")
        return {"results": [...]}
```

The `/users/search` endpoint has a stricter limit than other routes.

Evidence: Route-level throttle parameter mentioned in docstring at lines 388-390.

## Code Examples

### Basic Rate Limiting

```python
from aquilia.controller import Controller, Throttle
from aquilia.decorators import POST

class AuthController(Controller):
    prefix = "/auth"
    throttle = Throttle(limit=5, window=300)  # 5 login attempts per 5 minutes

    @POST("/login")
    async def login(self, ctx):
        data = await ctx.json()
        # Authentication logic here
        return {"token": "..."}
```

### Per-Route Customization

```python
class APIController(Controller):
    prefix = "/api"
    throttle = Throttle(limit=1000, window=3600)  # 1000 requests/hour default

    @GET("/stats")
    async def stats(self, ctx):
        return {"requests": 12345}  # Uses default throttle

    @POST("/upload", throttle=Throttle(limit=10, window=3600))
    async def upload(self, ctx):
        # Restricted: 10 uploads per hour
        form = await ctx.form()
        return {"status": "uploaded"}

    @GET("/health", throttle=None)
    async def health(self, ctx):
        # No throttling for health checks
        return {"status": "ok"}
```

### High-Capacity Throttle

```python
class HighVolumeController(Controller):
    prefix = "/stream"
    # Track 50k clients, allow 10k requests per minute
    throttle = Throttle(limit=10000, window=60, max_clients=50000)

    @GET("/events")
    async def events(self, ctx):
        return {"events": [...]}
```

### Manual Throttle Check

You can also check throttle state manually in handler logic:

```python
from aquilia.response import Response

class CustomController(Controller):
    prefix = "/custom"

    def __init__(self):
        self.manual_throttle = Throttle(limit=20, window=60)

    @POST("/action")
    async def action(self, ctx):
        if not self.manual_throttle.check(ctx.request):
            return Response.json(
                {"error": "Rate limit exceeded"},
                status=429,
                headers={"Retry-After": str(self.manual_throttle.retry_after)}
            )
        
        # Process the action
        return {"result": "success"}
```

---

**Evidence Summary:**
- Class definition: lines 379-481
- Constructor: lines 392-397
- `check()` method: lines 414-441
- `_client_key()`: lines 399-412
- Cleanup methods: lines 443-461
- Properties and reset: lines 463-469
- Controller integration: line 583 (class attribute)
- Usage examples: docstrings at lines 379-390

All line references are from `/Users/kuroyami/TuboxLabProject/aquilia_docs/aquilia/controller/base.py`.
