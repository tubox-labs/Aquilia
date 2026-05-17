# Cache Configuration

Async cache abstraction with memory, Redis, composite, null backends, serializers, decorators, DI providers, and HTTP caching middleware.

This page distinguishes direct configuration APIs from indirect runtime wiring. All class names and source files below are extracted from the current source tree.

## Configuration Model

This module exposes config-oriented public classes. Use the table below to locate exact constructors and `to_dict()` behavior in `api-reference.md`.

## Source Inventory

| File | Lines | Public classes | Public functions | Purpose |
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

## Detected Config-Oriented Classes

| Class | Source | Methods | Summary |
| --- | --- | --- | --- |
| `EvictionPolicy` | `aquilia/cache/core.py` |  | Cache eviction strategies. |
| `CacheConfig` | `aquilia/cache/core.py` | `apply_jitter`, `to_dict` | Cache subsystem configuration. |
| `CacheKeyBuilder` | `aquilia/cache/core.py` | `build` | Protocol for building cache keys. |
| `CacheConfigFault` | `aquilia/cache/faults.py` |  | Cache configuration error. |
| `DefaultKeyBuilder` | `aquilia/cache/key_builder.py` | `build`, `from_args` | Default key builder using colon-separated segments. |
| `HashKeyBuilder` | `aquilia/cache/key_builder.py` | `build`, `from_args` | Hash-based key builder for long or complex keys. |
| `CacheMiddleware` | `aquilia/cache/middleware.py` |  | HTTP response caching middleware. |

## Runtime Wiring Paths

- `workspace.py` defines workspace-level structure with `Workspace`, `Module`, and `Integration` builders.
- `modules/<name>/manifest.py` defines module internals with `AppManifest`.
- `ConfigLoader.get(...)` resolves dotted configuration paths at runtime.
- `AquiliaServer` consumes resolved config during middleware and subsystem setup.
- Subsystems with optional providers only require optional dependencies when their backend/provider is configured.

## Verification Checklist

1. Run `aq validate` to verify manifests.
2. Run `aq inspect config` to inspect resolved configuration.
3. Run `aq doctor` for workspace and integration diagnostics.
4. For server-only wiring, start via `aq run` and check startup logs plus `GET /_health`.

## Related Pages

- `api-reference.md` for exact class fields, methods, constants, and signatures.
- `integration-guide.md` for the workspace/manifest wiring pattern.
- `edge-cases-and-limitations.md` for fallback and compatibility behavior.
