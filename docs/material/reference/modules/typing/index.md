# Typing Module

> `aquilia.typing` — Core type definitions and protocols

The Typing module provides shared type definitions, protocols, and type aliases used throughout the Aquilia framework — including ASGI types, middleware types, effect types, and manifest types.

## When to Use

Use the Typing module when:

- Writing type annotations for custom components
- Implementing protocols (middleware, effects, providers)
- Extending the framework with typed interfaces

## Key Exports

| Type | Purpose |
|---|---|
| `ASGIApplication` | ASGI 3.0 application callable |
| `ASGIScope` | ASGI connection scope |
| `ASGIReceive` | ASGI receive callable |
| `ASGISend` | ASGI send callable |
| `MiddlewareCallable` | Middleware function signature |
| `RequestHandler` | Request handler signature |
| `ManifestCollection` | Collection of manifests |
| `ManifestMetadata` | Manifest metadata dict |
| `RequestState` | Per-request state dict |
| `EffectName` | Effect identifier type |

## Import Path

```python
from aquilia.typing import (
    ASGIApplication,
    ASGIScope,
    ASGIReceive,
    ASGISend,
    MiddlewareCallable,
    RequestHandler,
    ManifestCollection,
    ManifestMetadata,
    RequestState,
    EffectName,
)
```

## Related Modules

- [core/asgi](../core/asgi.md) — ASGI types in practice
- [core/middleware](../core/middleware.md) — Middleware types
- [core/effects](../core/effects.md) — Effect types