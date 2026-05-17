# Versioning Examples

## Primary Usage

```python
from aquilia.versioning import version, version_neutral
from aquilia import Controller, GET, RequestCtx, Response

class UsersController(Controller):
    @GET("/users", version="1.0")
    async def users_v1(self, ctx: RequestCtx):
        return Response.json({"version": "1.0"})

    @GET("/health")
    @version_neutral
    async def health(self, ctx: RequestCtx):
        return Response.json({"ok": True})
```

## Manifest Registration Pattern

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

## Workspace Pattern

```python
from aquilia import Module, Workspace

workspace = (
    Workspace("myapp")
    .module(Module("example").route_prefix("/example"))
)
```

## Public API Imports

```python
from aquilia.versioning import VersionStatus, VersionChannel, ApiVersion, VersionError, InvalidVersionError, UnsupportedVersionError
```

## Test Pattern

```python
import pytest

@pytest.mark.asyncio
async def test_subsystem_contract():
    # Construct the service, provider, controller helper, or datatype directly.
    # Use the exact constructor and methods from api-reference.md.
    assert True
```
