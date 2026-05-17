# cache Module

## Purpose

Async cache abstraction with middleware integration. Use this module for cache-aside helpers, key building, JSON and binary serializers, in-memory, null, Redis, and composite backends.

## Source Coverage

- Python files: 14
- Public classes: 27
- Dataclasses: 3
- Enums: 1
- Public functions: 10

## How It Fits In Aquilia

1. Import the package from `aquilia.cache` or its concrete submodules.
2. Configure it through workspace integrations, manifests, or direct service construction depending on the subsystem.
3. Keep business logic outside transport and framework glue so the subsystem stays testable.

## Practical Guidance

- Prefer typed configuration objects and framework helpers over ad hoc dictionaries when they exist.
- Use the tests in `tests/` as behavioral examples when changing this subsystem.

## Public Classes

| Name | Source | Role |
| --- | --- | --- |
| `EvictionPolicy` | `aquilia/cache/core.py` | Cache eviction strategies. |
| `CacheEntry` | `aquilia/cache/core.py` | Single cache entry with metadata. |
| `CacheStats` | `aquilia/cache/core.py` | Aggregate cache statistics for observability. |
| `CacheConfig` | `aquilia/cache/core.py` | Cache subsystem configuration. |
| `CacheSerializer` | `aquilia/cache/core.py` | Protocol for cache value serialization. |
| `CacheKeyBuilder` | `aquilia/cache/core.py` | Protocol for building cache keys. |
| `CacheBackend` | `aquilia/cache/core.py` | Abstract cache backend -- defines the storage contract. |
| `CacheFault` | `aquilia/cache/faults.py` | Base class for all cache faults. |
| `CacheMissFault` | `aquilia/cache/faults.py` | Cache key not found (informational, non-error). |
| `CacheConnectionFault` | `aquilia/cache/faults.py` | Failed to connect to cache backend. |
| `CacheSerializationFault` | `aquilia/cache/faults.py` | Failed to serialize/deserialize cache value. |
| `CacheCapacityFault` | `aquilia/cache/faults.py` | Cache has reached maximum capacity. |
| `CacheBackendFault` | `aquilia/cache/faults.py` | Generic cache backend error. |
| `CacheConfigFault` | `aquilia/cache/faults.py` | Cache configuration error. |
| `CacheStampedeFault` | `aquilia/cache/faults.py` | Cache stampede detected -- multiple concurrent loads for same key. |
| `CacheHealthFault` | `aquilia/cache/faults.py` | Cache health check failure. |
| `DefaultKeyBuilder` | `aquilia/cache/key_builder.py` | Default key builder using colon-separated segments. |
| `HashKeyBuilder` | `aquilia/cache/key_builder.py` | Hash-based key builder for long or complex keys. |
| `CacheMiddleware` | `aquilia/cache/middleware.py` | HTTP response caching middleware. |
| `JsonCacheSerializer` | `aquilia/cache/serializers.py` | JSON serializer -- safe, human-readable, cross-language. |
| `PickleCacheSerializer` | `aquilia/cache/serializers.py` | HMAC-signed pickle serializer -- supports arbitrary Python objects. |
| `MsgpackCacheSerializer` | `aquilia/cache/serializers.py` | MessagePack serializer -- compact binary, cross-language. |
| `CacheService` | `aquilia/cache/service.py` | High-level cache service -- the primary API for application code. |
| `CompositeBackend` | `aquilia/cache/backends/composite.py` | Two-level cache: L1 (fast/local) + L2 (distributed/persistent). |
| `MemoryBackend` | `aquilia/cache/backends/memory.py` | In-memory cache backend with configurable eviction policies. |
| `NullBackend` | `aquilia/cache/backends/null.py` | No-op cache backend -- all operations are pass-through. |
| `RedisBackend` | `aquilia/cache/backends/redis.py` | Redis-backed cache using aioredis (redis-py async). |

## Public Functions

| Name | Source | Role |
| --- | --- | --- |
| `set_default_cache_service` | `aquilia/cache/decorators.py` | Register a module-level CacheService for decorator resolution. |
| `get_default_cache_service` | `aquilia/cache/decorators.py` | Get the module-level default CacheService. |
| `cached` | `aquilia/cache/decorators.py` | Decorator to cache function results. |
| `cache_aside` | `aquilia/cache/decorators.py` | Cache-aside decorator -- identical to @cached but semantically |
| `invalidate` | `aquilia/cache/decorators.py` | Decorator to invalidate cache entries after function execution. |
| `create_cache_backend` | `aquilia/cache/di_providers.py` | Factory: create cache backend from configuration. |
| `create_cache_service` | `aquilia/cache/di_providers.py` | Factory: create CacheService from configuration. |
| `build_cache_config` | `aquilia/cache/di_providers.py` | Build CacheConfig from dictionary (e.g., from ConfigLoader). |
| `register_cache_providers` | `aquilia/cache/di_providers.py` | Register cache providers in a DI container. |
| `get_serializer` | `aquilia/cache/serializers.py` | Factory for serializer instances. |

## Implementation Map

| File | What To Look For |
| --- | --- |
| `aquilia/cache/__init__.py` | AquilaCache -- Production-grade, async-first caching system for Aquilia. |
| `aquilia/cache/backends/__init__.py` | AquilaCache Backends -- Storage implementations. |
| `aquilia/cache/backends/composite.py` | AquilaCache -- Composite (L1/L2) backend. |
| `aquilia/cache/backends/memory.py` | AquilaCache -- High-performance in-memory backend. |
| `aquilia/cache/backends/null.py` | AquilaCache -- Null (no-op) backend. |
| `aquilia/cache/backends/redis.py` | AquilaCache -- Redis backend for distributed caching. |
| `aquilia/cache/core.py` | AquilaCache -- Core types, protocols, and data structures. |
| `aquilia/cache/decorators.py` | AquilaCache -- Decorators for declarative caching. |
| `aquilia/cache/di_providers.py` | AquilaCache -- DI provider registration. |
| `aquilia/cache/faults.py` | AquilaCache -- Fault domain integration. |
| `aquilia/cache/key_builder.py` | AquilaCache -- Cache key builder implementations. |
| `aquilia/cache/middleware.py` | AquilaCache -- HTTP response caching middleware. |
| `aquilia/cache/serializers.py` | AquilaCache -- Pluggable serializers for cache value encoding. |
| `aquilia/cache/service.py` | AquilaCache -- CacheService: High-level API for cache operations. |

## Testing Pointers

Search `tests/` for `cache` to find behavior-level examples. The test suite is especially useful for edge cases because many modules expose lightweight public APIs but enforce important security and lifecycle behavior internally.
