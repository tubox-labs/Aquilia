# Distributed Throttle Backends

Aquilia's controller throttling system includes support for distributed rate limiting via pluggable storage backends. By default, throttling happens in-memory, but for multi-instance deployments, you can switch to a distributed backend like Redis.

## Architecture: The `ThrottleBackend` Protocol

The rate-limiting system is abstracted behind the `ThrottleBackend` protocol. Any backend implementing this interface can be plugged into the throttle pipeline.

```python
from typing import Protocol

class ThrottleBackend(Protocol):
    async def is_allowed(self, key: str, limit: int, window: int) -> bool: ...
    async def get_count(self, key: str, window: int) -> int: ...
    async def reset(self, key: str | None = None) -> None: ...
    async def close(self) -> None: ...
```

## Available Backends

### `MemoryThrottleBackend`

The default backend. It tracks rate limits in memory using Python dictionaries and a background cleanup cycle.

- **When to use**: Single-instance deployments, development, testing, or endpoints where exact global limits aren't strictly necessary.
- **Async-Safe**: Uses `asyncio.Lock()` to prevent race conditions during concurrent request processing.
- **Config**: Accepts a `max_clients` argument (default `10000`) to prevent memory exhaustion from an unbounded number of unique clients.

### `RedisThrottleBackend`

A distributed backend using Redis sets to track sliding-window rate limits across multiple servers.

- **Setup**: Requires the `redis` python package (`pip install aquilia[redis]`).
- **When to use**: Multi-instance deployments, containerized environments, serverless architectures, or anywhere you need strict, global API limits.
- **Options**:
  - `redis_url`: The connection string (e.g., `"redis://localhost:6379"`).
  - `key_prefix`: String to prepend to keys (default `"aq:throttle:"`).
  - `fail_open`: Boolean (default `True`). If Redis goes offline, `fail_open=True` allows requests to pass through rather than returning a 500 server error (Graceful Degradation).

## Updated `Throttle` Class API

The `Throttle` class has been updated to support both asynchronous checking and backend factories.

### Factories

Instead of manually constructing backends, use the factory methods on the `Throttle` class:

```python
from aquilia.controller import Controller, Throttle

class ApiController(Controller):
    # Default memory throttle
    throttle = Throttle.with_memory(limit=100, window=60)

    # Redis-backed distributed throttle
    # throttle = Throttle.with_redis("redis://localhost:6379", limit=100, window=60)
```

### `acheck()` vs `check()`

The internal controller engine now uses `await throttle.acheck(request)`. 

- `acheck(request)`: Asynchronously evaluates the backend (`is_allowed`).
- `check(request)`: Exists for backwards compatibility. If you use a custom backend that only implements `check()`, or if no backend is provided, it falls back to the synchronous memory check.

## `ThrottleBackendFactory`

Under the hood, `Throttle.with_memory` and `with_redis` use the `ThrottleBackendFactory`. You can use it to register custom backends.

```python
from aquilia.controller.throttle import ThrottleBackendFactory, ThrottleBackend

class MyCustomBackend(ThrottleBackend):
    ...

# Register custom backend string
ThrottleBackendFactory.register("custom", MyCustomBackend)

# Use it
backend = ThrottleBackendFactory.create("custom", param="value")
```

The `create(config)` method intelligently returns the right backend:
- `create("memory")` -> `MemoryThrottleBackend`
- `create("redis://...")` -> `RedisThrottleBackend`

## Integrations and Configuration

For application-wide setup, you can define throttling in your workspace using `ThrottleConfig` from the integrations module.

```python
from aquilia.integrations.throttle import ThrottleConfig
from aquilia.controller.throttle import ThrottleBackendFactory

config = ThrottleConfig(
    backend="redis://redis.internal:6379/1",
    fail_open=True
)

# You can subsequently instantiate controllers pulling from this central config
```

## Multi-Instance Deployment Guidance

When deploying Aquilia with multiple workers (e.g., `aq serve --workers 4`) or horizontally scaling across multiple containers, **do not use the default memory backend for strict limits.**

If you set a limit of 10 requests/minute and have 4 workers, a client could potentially make up to 40 requests/minute if round-robin load balancing distributes them perfectly.

For true global limits, you **must** use `RedisThrottleBackend`.

## Graceful Degradation Patterns

The `RedisThrottleBackend` defaults to `fail_open=True`. 

In distributed systems, caching and throttling infrastructure is usually considered a "soft dependency". If your Redis server crashes or experiences a network partition, you typically want your API to stay online and serve traffic, even if it means temporarily lifting rate limits.

If strict limits are legally or operationally required (e.g., costly external API calls per request), instantiate the backend with `fail_open=False`. In this scenario, Redis outages will cause the rate limiter to raise exceptions, which your application will map to 500 Internal Server Errors, halting traffic until Redis is restored.
