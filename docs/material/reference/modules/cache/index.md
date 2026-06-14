# Cache Module

> `aquilia.cache` — Multi-backend caching with decorators and middleware

The Cache module provides an async caching layer with multiple backends (memory, Redis, composite, null), cache-aside and cache-through decorators, HTTP cache middleware, and HMAC-signed cache keys.

## When to Use

Use the Cache module when you need:

- Application-level caching of expensive operations
- HTTP response caching via middleware
- Redis-backed distributed caching
- Cache stampede protection
- Cache invalidation patterns

## Key Classes

| Class | Purpose |
|---|---|
| `CacheService` | Central async caching service |
| `MemoryBackend` | In-memory cache (dev/testing) |
| `RedisBackend` | Redis-backed distributed cache |
| `CompositeBackend` | Multi-level cache (L1 memory + L2 Redis) |
| `NullBackend` | No-op cache (disables caching) |
| `CacheMiddleware` | HTTP response cache middleware |
| `DefaultKeyBuilder` | Namespace-prefixed key builder |
| `HashKeyBuilder` | SHA256-hashed key builder |
| `CacheStats` | Cache hit/miss/size metrics |
| `EvictionPolicy` | Cache eviction strategies (LRU, TTL) |

## Quick Example

```python
from aquilia.cache import CacheService, MemoryBackend, cached

# Create a cache service
cache = CacheService(MemoryBackend(max_size=1000))

# Cache a function result
@cached(ttl=300, key_prefix="users")
async def get_user(user_id: str):
    # Expensive DB query...
    return {"id": user_id, "name": "Alice"}

# Cache-aside pattern
from aquilia.cache import cache_aside
@cache_aside(ttl=600)
async def get_expensive_data(key: str):
    return await compute_expensive(key)

# Invalidate
from aquilia.cache import invalidate
await invalidate("users", user_id)
```

## Import Path

```python
from aquilia.cache import (
    CacheService,
    CacheBackend,
    MemoryBackend,
    RedisBackend,
    CompositeBackend,
    NullBackend,
    CacheMiddleware,
    cached,
    cache_aside,
    invalidate,
    CacheConfig,
    CacheStats,
    DefaultKeyBuilder,
    HashKeyBuilder,
    EvictionPolicy,
)
```

## Related Modules

- [core/effects](../core/effects.md) — CacheEffect for pipeline integration
- [integrations](../integrations/index.md) — CacheIntegration config builder
- [core/signing](../core/signing.md) — HMAC-signed cache keys