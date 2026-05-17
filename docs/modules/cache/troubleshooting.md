# Cache Troubleshooting

Async cache abstraction with memory, Redis, composite, null backends, serializers, decorators, DI providers, and HTTP caching middleware.

## Fast Diagnosis Flow

1. Confirm the command is run from a directory containing `workspace.py` unless it is help/version/init/doctor.
2. Run `aq doctor` for workspace, environment, registry, integration, and deployment checks.
3. Run `aq validate` to catch manifest errors.
4. Run `aq inspect config` to inspect resolved settings.
5. Run `aq inspect modules` and `aq inspect routes` when discovery or routing is suspect.
6. Check `api-reference.md` for exact public API signatures.

## Module-Relevant Commands

- `aq cache check`
- `aq cache inspect`
- `aq cache stats`
- `aq cache clear`

## Symptoms And Actions

| Symptom | Likely Source | Action |
| --- | --- | --- |
| Import error during startup | Bad manifest class path or optional provider dependency | Check `modules/<name>/manifest.py`, install the relevant extra, and rerun `aq validate`. |
| Route not found | Controller omitted from manifest, wrong route prefix, or startup conflict | Run `aq inspect routes`; inspect controller decorators and `Module.route_prefix()`. |
| Dependency not found | Service not registered or constructor annotation cannot be resolved | Check `AppManifest.services`, DI provider registrations, and `aq inspect di`. |
| Config value missing | Dotenv/env overlay not loaded or wrong nested key | Check `ConfigLoader` precedence and `AQ_` double-underscore key names. |
| Production security failure | Insecure secret or required key not configured | Set `AQ_SECRET_KEY`, `SECRET_KEY`, or Python-native secret config. |
| Optional subsystem unavailable | Provider/backend dependency or startup connection failed | Check startup logs; optional subsystems often log non-fatal failures. |

## Source Files To Inspect

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
