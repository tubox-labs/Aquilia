# Admin Examples

Built-in administration interface, audit log, permissions, dashboards, model CRUD, operational pages, and admin security.

Examples here use public symbols and checked patterns from the repository. When a module has no safe standalone constructor example, the example focuses on importing and wiring the actual source-backed API.

## Source-Backed Import Examples

```python
from aquilia.admin.audit import AdminAction
from aquilia.admin.audit import AdminAuditEntry
from aquilia.admin.controller import AdminController
from aquilia.admin.di_providers import provide_admin_site
from aquilia.admin.error_tracker import ErrorRecord
from aquilia.admin.error_tracker import ErrorGroup
```

## Workspace/Manifest Wiring Example

```python
from aquilia import AppManifest, Integration, Module, Workspace

workspace = (
    Workspace("example", version="1.0.0")
    .runtime(mode="dev", port=8000)
    .module(Module("example").route_prefix("/example"))
    .integrate(Integration.di(auto_wire=True))
)

manifest = AppManifest(
    name="example",
    version="1.0.0",
    controllers=["modules.example.controllers:ExampleController"],
    services=["modules.example.services:ExampleService"],
)
```

## Admin Integration Pattern

```python
from aquilia import Integration, Workspace

workspace = (
    Workspace("admin-app")
    .integrate(Integration.admin(url_prefix="/admin"))
    .integrate(Integration.static_files(directories={"/static": "assets"}))
)
```

## Verification

- Run `python -m aquilia.cli.__main__ --help` to confirm CLI availability.
- Run `aq validate` in a workspace to validate manifest paths.
- Run related tests under `tests/` or `examples/*/tests/` for executable behavior.
