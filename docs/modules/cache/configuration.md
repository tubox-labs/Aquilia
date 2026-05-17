# Cache Configuration

## Configuration Entry Points

The implementation exposes the following configuration-like classes, policies, integrations, or dataclasses.

| Type | Source | Fields | Purpose |
| --- | --- | --- | --- |
| `EvictionPolicy` | `aquilia/cache/core.py` | See class attributes and constructor methods. | Cache eviction strategies. |
| `CacheEntry` | `aquilia/cache/core.py` | key: str, value: Any, created_at: float, expires_at: float &#124; None, last_accessed: float, access_count: int, size_bytes: int, tags: tuple[str, ...], namespace: str, version: int | Single cache entry with metadata. |
| `CacheStats` | `aquilia/cache/core.py` | hits: int, misses: int, sets: int, deletes: int, evictions: int, errors: int, stampede_joins: int, size: int, max_size: int, memory_bytes: int, backend: str, uptime_seconds: float | Aggregate cache statistics for observability. |
| `CacheConfig` | `aquilia/cache/core.py` | enabled: bool, backend: str, default_ttl: int, max_size: int, eviction_policy: str, namespace: str, key_prefix: str, serializer: str, ttl_jitter: bool, ttl_jitter_percent: float, stampede_prevention: bool, stampede_timeout: float, ... | Cache subsystem configuration. |

## Common Entry Points

- `CacheConfig`
- `CacheIntegration`
- `CacheMiddleware`

## Precedence Model

Aquilia generally resolves configuration in this order:

1. Explicit constructor arguments or typed integration dataclass values.
2. `Workspace` builder methods and `Workspace.integrate(...)` output.
3. `ConfigLoader` defaults and environment overlays.
4. Runtime defaults inside the subsystem service or provider constructor.

When this module is registered through an `AppManifest`, keep component declarations inside `modules/<name>/manifest.py` and keep cross-cutting integration settings in `workspace.py`.

## Datatype Guidance

- Prefer typed dataclasses, policy objects, and config objects listed above when they exist.
- Keep secret values in environment-backed config, not literal strings in committed workspace files.
- Keep runtime-only state in services, stores, providers, or request state rather than static configuration.
- Use `to_dict()` on integration dataclasses when you need to inspect exactly what enters `ConfigLoader`.
