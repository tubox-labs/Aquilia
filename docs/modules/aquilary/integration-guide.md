# Aquilary Integration Guide

Manifest registry, validation, dependency graph, route table compilation metadata, fingerprinting, and runtime registry construction.

## Where This Module Fits

Import the public classes/functions listed in `api-reference.md` or wire the module through manifests and services.

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
