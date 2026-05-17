# Cache Documentation

This directory is the professional documentation set for `cache`. It is implementation-driven and aligned with the current source files under `aquilia/cache`.

## What This Covers

The async cache abstraction with memory, null, Redis, and composite backends, serializers, key builders, decorators, and middleware.

## Source Files Read

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

## Document Map

- `architecture.md`: Runtime architecture and module boundaries
- `configuration.md`: Configuration entry points, datatypes, and precedence
- `api-reference.md`: Classes, methods, functions, constants, and data fields extracted from source
- `integration-guide.md`: How to wire the module into a real Aquilia application
- `cli-reference.md`: Command line surface and operational commands
- `edge-cases-and-limitations.md`: Known edge cases and implementation limits
- `troubleshooting.md`: Common failures and diagnosis steps
- `examples.md`: Code examples and usage patterns

## Public Surface Snapshot

- Python files: 14
- Public classes: 27
- Configuration or dataclass-like types: 4
- Public functions: 10
- Constants detected: 3

## Fast Start

```python
from aquilia.cache import CacheService, MemoryBackend, cached

cache = CacheService(backend=MemoryBackend())
await cache.set("catalog:featured", [{"sku": "AQ-STARTER"}], ttl=300)
items = await cache.get("catalog:featured")

@cached(ttl=60)
async def expensive_lookup(key: str):
    return {"key": key}
```

## Read Next

Start with `architecture.md` if you are learning how the subsystem fits into runtime boot. Use `api-reference.md` when you need exact methods, datatypes, and class fields. Use `examples.md` for copyable patterns that match the current code.
