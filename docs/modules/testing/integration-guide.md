# Testing Integration Guide

## Workspace Integration

Use workspace-level configuration for cross-cutting behavior and module manifests for component registration.

```python
from aquilia import Module, Workspace

workspace = (
    Workspace("myapp")
    .module(Module("example").route_prefix("/example"))
)
```

If this subsystem has a typed integration object, attach it with `workspace.integrate(...)`. See `configuration.md` for detected configuration datatypes.

## Module Manifest Integration

Register application-owned classes from `modules/<name>/manifest.py`.

```python
from aquilia import AppManifest

manifest = AppManifest(
    name="example",
    version="1.0.0",
    controllers=["modules.example.controllers:ExampleController"],
    services=["modules.example.services:ExampleService"],
    base_path="modules.example",
)
```

## Request-Time Integration

When this module participates in request handling, data normally flows through `RequestCtx`, `request.state`, DI containers, middleware, controllers, or providers. Use the public service methods shown in `api-reference.md` instead of reaching into private attributes.

## Testing Integration

Use the classes and helpers listed in `api-reference.md` directly in unit tests. For framework-level behavior, prefer Aquilia testing helpers from `aquilia.testing` and keep tests scoped to the module boundary.
