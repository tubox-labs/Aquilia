# Cache Edge Cases And Limitations

Async cache abstraction with memory, Redis, composite, null backends, serializers, decorators, DI providers, and HTTP caching middleware.

## Source-Backed Limits

- Cache startup failure is logged as non-fatal in server startup.

## Fault And Error Classes Detected

`CacheFault`, `CacheMissFault`, `CacheConnectionFault`, `CacheSerializationFault`, `CacheCapacityFault`, `CacheBackendFault`, `CacheConfigFault`, `CacheStampedeFault`, `CacheHealthFault`

## Operational Boundaries

- Optional external libraries are only required when the corresponding provider/backend/runtime is configured.
- Deprecated APIs generally warn when retained for migration rather than disappearing silently.
- Server startup intentionally degrades non-critical optional subsystems where source catches and logs exceptions.
- Use `api-reference.md` to check exact constructor defaults and method signatures before depending on behavior.

## Verification

- `aq doctor` for workspace/integration issues.
- `aq validate` for manifest issues.
- `aq inspect config` for merged configuration.
- `GET /_health` for live subsystem status once the app is running.
