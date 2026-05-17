# Cache Architecture

## Runtime Role

The async cache abstraction with memory, null, Redis, and composite backends, serializers, key builders, decorators, and middleware.

The implementation is split across 14 Python files. The module boundary is visible in the file inventory below and the API reference is generated from the same source files.

## Primary Source Files

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

## Internal Dependency Shape

The table below is derived from import statements in the module. It shows which top-level packages this module depends on most often.

| Imported package | Import count |
| --- | --- |
| `__future__` | 12 |
| `typing` | 11 |
| `logging` | 8 |
| `core` | 7 |
| `backends` | 6 |
| `aquilia` | 5 |
| `asyncio` | 4 |
| `builtins` | 4 |
| `time` | 4 |
| `collections` | 3 |
| `contextlib` | 3 |
| `key_builder` | 3 |
| `faults` | 2 |
| `fnmatch` | 2 |
| `hashlib` | 2 |
| `inspect` | 2 |
| `random` | 2 |
| `service` | 2 |
| `abc` | 1 |
| `composite` | 1 |
| `dataclasses` | 1 |
| `decorators` | 1 |
| `enum` | 1 |
| `functools` | 1 |
| `heapq` | 1 |
| `hmac` | 1 |
| `json` | 1 |
| `memory` | 1 |
| `middleware` | 1 |
| `null` | 1 |

## Data And Control Flow

1. Configuration or direct construction creates the public service objects, controllers, providers, or helpers for this module.
2. Runtime code imports the registered classes from manifests, workspace integrations, middleware stacks, or direct application code.
3. Public methods perform validation and convert invalid states into typed Aquilia faults where the implementation defines fault classes.
4. Integration points return Python data structures, `Response` objects, provider results, jobs, sessions, connections, or model instances depending on the subsystem.

## Boundary Rules

- Keep application-specific business decisions outside framework classes unless the class is explicitly a service or controller owned by your app.
- Prefer the public exports and typed configuration dataclasses shown in `api-reference.md`.
- When a module supplies both a low-level primitive and a high-level service, use the service in application code and keep primitives for tests, providers, or advanced integrations.
