# Cache Documentation

Async cache abstraction with memory, Redis, composite, null backends, serializers, decorators, DI providers, and HTTP caching middleware.

## Coverage Snapshot

- Source files: 14
- Source lines: 3813
- Public classes: 27
- Public module functions: 10
- Constants/module flags: 5
- Public exports in `__all__`: 32

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

- `architecture.md`: module boundaries, dependencies, lifecycle, and extension points.
- `configuration.md`: configuration classes, builders, server wiring, and precedence.
- `api-reference.md`: source-extracted classes, methods, functions, constants, exports, and signatures.
- `integration-guide.md`: how to wire the module into an Aquilia app.
- `cli-reference.md`: mounted `aq` commands for this module, if any.
- `examples.md`: usage examples derived from source and checked example apps.
- `edge-cases-and-limitations.md`: implementation limits and compatibility behavior.
- `troubleshooting.md`: diagnostic commands and common failure patterns.
