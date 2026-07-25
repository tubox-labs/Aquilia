# Distributed Throttle Backends

Aquilia v1.3.4 modernizes the controller rate limiting system by introducing a pluggable, asynchronous throttle backend architecture. This enables developers to move from single-process memory tracking to distributed, multi-worker rate limiting seamlessly.

## Architecture Overview

The rate-limiting logic has been abstracted into a `ThrottleBackend` protocol defined in `aquilia/controller/throttle.py`. 

```python
class ThrottleBackend(Protocol):
    async def is_allowed(self, key: str, limit: int, window: int) -> bool: ...
    async def get_count(self, key: str, window: int) -> int: ...
    async def reset(self, key: str | None = None) -> None: ...
    async def close(self) -> None: ...
```

The core `Throttle` class has been updated to accept an optional `backend` parameter. `ControllerEngine._check_throttle()` is now an async method that awaits `Throttle.acheck()` if a backend is configured, falling back to the legacy synchronous `check()` for backward compatibility.

## Included Backends

### MemoryThrottleBackend

An async-safe, sliding window memory tracker utilizing `asyncio.Lock`.

- Maintains an internal dictionary of request timestamps.
- Implements LRU eviction when the tracking dictionary exceeds `max_clients` (default: 10,000).
- Performs periodic cleanup of expired timestamps to keep memory usage bounded.

### RedisThrottleBackend

A distributed, sliding window rate limiter backed by a Redis sorted set.

- **Distributed:** Tracks requests across multiple processes, containers, or pods.
- **Lazy Connection:** Uses `redis.asyncio` to connect only when needed.
- **Graceful Degradation:** The `fail_open: bool = True` parameter ensures that if the Redis server goes down, the application will allow requests through rather than failing entirely, prioritizing availability.

**Note:** Requires `pip install redis`.

## Usage & API Changes

### Factory Methods on `Throttle`

The `Throttle` class now provides ergonomic factory methods:

```python
from aquilia.controller.throttle import Throttle

# Memory Backend
throttle_mem = Throttle.with_memory(limit=60, window=60)

# Redis Backend
throttle_redis = Throttle.with_redis(
    url="redis://localhost:6379/0",
    limit=100,
    window=60,
    fail_open=True
)

@route(["GET"], path="/api", throttle=throttle_redis)
async def my_endpoint(self, ctx):
    pass
```

### ThrottleBackendFactory

For dynamic configuration, you can use `ThrottleBackendFactory.create(config)`:

```python
from aquilia.controller.throttle import ThrottleBackendFactory

# Returns a MemoryThrottleBackend
mem_backend = ThrottleBackendFactory.create("memory")

# Returns a RedisThrottleBackend
redis_backend = ThrottleBackendFactory.create("redis://redis-server:6379")
```

Custom backends can be registered globally:
```python
ThrottleBackendFactory.register("custom", MyCustomBackend)
```

## ThrottleConfig Integration

A new `ThrottleConfig` dataclass is available in `aquilia.integrations.throttle` to facilitate standard injection and configuration of default application-wide rate limits.

## Migration from Old Throttle

No breaking changes have been introduced for existing `Throttle` usage. Legacy synchronous `Throttle(limit=X, window=Y)` instantiations without a backend continue to use the legacy synchronous tracking mechanism. 

To upgrade, simply replace your `Throttle(...)` calls with `Throttle.with_memory(...)` or `Throttle.with_redis(...)`.
