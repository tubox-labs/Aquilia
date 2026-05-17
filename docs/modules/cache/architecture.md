# Cache Architecture

Async cache abstraction with memory, Redis, composite, null backends, serializers, decorators, DI providers, and HTTP caching middleware.

## Source Boundaries

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/cache/__init__.py` | 119 | 0 | 0 | AquilaCache -- Production-grade, async-first caching system for Aquilia. |
| `aquilia/cache/backends/__init__.py` | 15 | 0 | 0 | AquilaCache Backends -- Storage implementations. |
| `aquilia/cache/backends/composite.py` | 281 | 1 | 0 | AquilaCache -- Composite (L1/L2) backend. |
| `aquilia/cache/backends/memory.py` | 514 | 1 | 0 | AquilaCache -- High-performance in-memory backend. |
| `aquilia/cache/backends/null.py` | 67 | 1 | 0 | AquilaCache -- Null (no-op) backend. |
| `aquilia/cache/backends/redis.py` | 462 | 1 | 0 | AquilaCache -- Redis backend for distributed caching. |
| `aquilia/cache/core.py` | 534 | 7 | 0 | AquilaCache -- Core types, protocols, and data structures. |
| `aquilia/cache/decorators.py` | 272 | 0 | 5 | AquilaCache -- Decorators for declarative caching. |
| `aquilia/cache/di_providers.py` | 201 | 0 | 4 | AquilaCache -- DI provider registration. |
| `aquilia/cache/faults.py` | 143 | 9 | 0 | AquilaCache -- Fault domain integration. |
| `aquilia/cache/key_builder.py` | 110 | 2 | 0 | AquilaCache -- Cache key builder implementations. |
| `aquilia/cache/middleware.py` | 275 | 1 | 0 | AquilaCache -- HTTP response caching middleware. |
| `aquilia/cache/serializers.py` | 191 | 3 | 1 | AquilaCache -- Pluggable serializers for cache value encoding. |
| `aquilia/cache/service.py` | 629 | 1 | 0 | AquilaCache -- CacheService: High-level API for cache operations. |

## Internal Shape

`cache` has 14 Python files, 27 public classes, 10 public module-level functions, and 5 constants or module flags detected by AST.

## Runtime Responsibilities

- This module has `aq` command coverage documented in `cli-reference.md`; 4 commands map to this subsystem.

## Internal Imports

| Import | Count |
| --- | ---: |
| `..core` | 4 |
| `.core` | 3 |
| `.key_builder` | 3 |
| `.backends.memory` | 2 |
| `.backends.null` | 2 |
| `.faults` | 2 |
| `.service` | 2 |
| `aquilia.faults.domains` | 2 |
| `.backends.composite` | 1 |
| `.backends.redis` | 1 |
| `.composite` | 1 |
| `.decorators` | 1 |
| `.memory` | 1 |
| `.middleware` | 1 |
| `.null` | 1 |
| `.redis` | 1 |
| `.serializers` | 1 |
| `aquilia._version` | 1 |
| `aquilia.faults.core` | 1 |
| `aquilia.response` | 1 |

## External And Stdlib Imports

| Import root | Count |
| --- | ---: |
| `__future__` | 12 |
| `typing` | 11 |
| `logging` | 8 |
| `asyncio` | 4 |
| `builtins` | 4 |
| `time` | 4 |
| `collections` | 3 |
| `contextlib` | 3 |
| `fnmatch` | 2 |
| `hashlib` | 2 |
| `inspect` | 2 |
| `random` | 2 |
| `abc` | 1 |
| `dataclasses` | 1 |
| `enum` | 1 |
| `functools` | 1 |
| `heapq` | 1 |
| `hmac` | 1 |
| `json` | 1 |
| `os` | 1 |
| `sys` | 1 |

## Lifecycle And Extension Points

| Extension Type | Source | Role |
| --- | --- | --- |
| `CompositeBackend` | `aquilia/cache/backends/composite.py` | Two-level cache: L1 (fast/local) + L2 (distributed/persistent). |
| `MemoryBackend` | `aquilia/cache/backends/memory.py` | In-memory cache backend with configurable eviction policies. |
| `NullBackend` | `aquilia/cache/backends/null.py` | No-op cache backend -- all operations are pass-through. |
| `RedisBackend` | `aquilia/cache/backends/redis.py` | Redis-backed cache using aioredis (redis-py async). |
| `EvictionPolicy` | `aquilia/cache/core.py` | Cache eviction strategies. |
| `CacheConfig` | `aquilia/cache/core.py` | Cache subsystem configuration. |
| `CacheBackend` | `aquilia/cache/core.py` | Abstract cache backend -- defines the storage contract. |
| `CacheBackendFault` | `aquilia/cache/faults.py` | Generic cache backend error. |
| `CacheConfigFault` | `aquilia/cache/faults.py` | Cache configuration error. |
| `CacheMiddleware` | `aquilia/cache/middleware.py` | HTTP response caching middleware. |

## Error Handling

Fault/error classes defined here:

`CacheFault`, `CacheMissFault`, `CacheConnectionFault`, `CacheSerializationFault`, `CacheCapacityFault`, `CacheBackendFault`, `CacheConfigFault`, `CacheStampedeFault`, `CacheHealthFault`
