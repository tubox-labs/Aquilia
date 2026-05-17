# Integrations Integration Guide

Typed workspace integration configuration objects consumed by `Workspace.integrate(...)` and server setup.

## Where This Module Fits

Create typed integration objects and pass them to `Workspace.integrate(...)`. The server reads their serialized dictionaries through `ConfigLoader`.

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
