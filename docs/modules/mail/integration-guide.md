# Mail Integration Guide

Async mail subsystem with message classes, config blueprints, providers, DI registration, templates, faults, and convenience send APIs.

## Where This Module Fits

Configure this subsystem through the matching `Integration.*(...)` builder when available, or through typed classes in `aquilia.integrations`.

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
