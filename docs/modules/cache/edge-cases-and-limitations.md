# Cache Edge Cases And Limitations

## Fault And Error Types

The following error-oriented classes are present in the implementation and should guide defensive usage.

| Type | Source | Meaning |
| --- | --- | --- |
| `CacheFault` | `aquilia/cache/faults.py` | Base class for all cache faults. |
| `CacheMissFault` | `aquilia/cache/faults.py` | Cache key not found (informational, non-error). |
| `CacheConnectionFault` | `aquilia/cache/faults.py` | Failed to connect to cache backend. |
| `CacheSerializationFault` | `aquilia/cache/faults.py` | Failed to serialize/deserialize cache value. |
| `CacheCapacityFault` | `aquilia/cache/faults.py` | Cache has reached maximum capacity. |
| `CacheBackendFault` | `aquilia/cache/faults.py` | Generic cache backend error. |
| `CacheConfigFault` | `aquilia/cache/faults.py` | Cache configuration error. |
| `CacheStampedeFault` | `aquilia/cache/faults.py` | Cache stampede detected -- multiple concurrent loads for same key. |
| `CacheHealthFault` | `aquilia/cache/faults.py` | Cache health check failure. |

## Common Edge Cases

- Optional dependencies may change behavior. Check imports and constructor docs before enabling production features.
- In-memory stores, queues, caches, adapters, and registries are usually process-local. Use durable backends when state must survive restarts or scale across workers.
- Request-scoped data must not be cached globally. Use request state, DI request scopes, or explicit parameters.
- Decorators in Aquilia generally attach metadata at import time. Runtime behavior happens later during compilation, routing, middleware execution, or service startup.
- Many subsystems intentionally convert invalid states into typed faults. Catch the specific fault type when application code can recover.

## Source-Level Limits To Review

Review these files before changing behavior:

- `aquilia/cache/__init__.py`: AquilaCache -- Production-grade, async-first caching system for Aquilia.
- `aquilia/cache/backends/__init__.py`: AquilaCache Backends -- Storage implementations.
- `aquilia/cache/backends/composite.py`: AquilaCache -- Composite (L1/L2) backend.
- `aquilia/cache/backends/memory.py`: AquilaCache -- High-performance in-memory backend.
- `aquilia/cache/backends/null.py`: AquilaCache -- Null (no-op) backend.
- `aquilia/cache/backends/redis.py`: AquilaCache -- Redis backend for distributed caching.
- `aquilia/cache/core.py`: AquilaCache -- Core types, protocols, and data structures.
- `aquilia/cache/decorators.py`: AquilaCache -- Decorators for declarative caching.
- `aquilia/cache/di_providers.py`: AquilaCache -- DI provider registration.
- `aquilia/cache/faults.py`: AquilaCache -- Fault domain integration.
- `aquilia/cache/key_builder.py`: AquilaCache -- Cache key builder implementations.
- `aquilia/cache/middleware.py`: AquilaCache -- HTTP response caching middleware.
- `aquilia/cache/serializers.py`: AquilaCache -- Pluggable serializers for cache value encoding.
- `aquilia/cache/service.py`: AquilaCache -- CacheService: High-level API for cache operations.
