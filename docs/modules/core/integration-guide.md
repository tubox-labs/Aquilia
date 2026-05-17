# Core Integration Guide

Root framework runtime files: ASGI adapter, server, runtime bootstrap, config, pyconfig, request/response, middleware, lifecycle, signing, effects, dotenv, uploads, and data structures.

## Where This Module Fits

Use `AquiliaRuntime.from_workspace()` or `aquilia.entrypoint:app` for ASGI boot. Use `Workspace`, `Module`, `Integration`, and `AppManifest` for declarations.

## Manifest Pattern

```python
from aquilia import AppManifest

manifest = AppManifest(
    name="example",
    version="1.0.0",
    controllers=["modules.example.controllers:ExampleController"],
    services=["modules.example.services:ExampleService"],
)
```

## Verification

- `aq validate` checks manifest structure.
- `aq doctor` runs broader workspace diagnostics.
- `aq inspect config` shows resolved configuration.
- `aq inspect routes` shows compiled HTTP routes after discovery/compilation.
