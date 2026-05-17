# SQLite Configuration

## Configuration Entry Points

The implementation exposes the following configuration-like classes, policies, integrations, or dataclasses.

| Type | Source | Fields | Purpose |
| --- | --- | --- | --- |
| `SqlitePoolConfig` | `aquilia/sqlite/_config.py` | path: str, journal_mode: str, foreign_keys: bool, busy_timeout: int, synchronous: str, cache_size: int, mmap_size: int, temp_store: str, wal_autocheckpoint: int, pool_size: int, pool_min_size: int, pool_max_idle_time: float, ... | Comprehensive SQLite configuration for the native pool. |
| `SqliteMetrics` | `aquilia/sqlite/_metrics.py` | pool_size: int, pool_idle: int, pool_waiting: int, queries_total: int, query_errors_total: int, query_rows_total: int, query_latency_ns: int, transactions_total: int, transaction_commits: int, transaction_rollbacks: int, transaction_latency_ns: int, cache_hits: int, ... | Aggregated metrics for the SQLite connection pool. |
| `CacheStats` | `aquilia/sqlite/_statement_cache.py` | hits: int, misses: int, evictions: int, size: int, capacity: int | Observable statistics for a statement cache. |

## Common Entry Points

- No dedicated workspace integration was detected from module naming. Configure this module through direct constructors, manifests, or the subsystem that owns it.

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
