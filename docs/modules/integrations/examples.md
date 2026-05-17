# Integrations Examples

## Primary Usage

```python
from aquilia import Module, Workspace
from aquilia.integrations import CacheIntegration, DatabaseIntegration, OpenAPIIntegration

workspace = (
    Workspace("myapp")
    .module(Module("catalog").route_prefix("/catalog"))
    .integrate(DatabaseIntegration(url="sqlite:///app.db", auto_create=True))
    .integrate(CacheIntegration(backend="memory", default_ttl=300))
    .integrate(OpenAPIIntegration(title="My API", version="1.0.0"))
)
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
from aquilia.integrations import IntegrationConfig, AdminModules, AdminAudit, AdminMonitoring, AdminSidebar, AdminContainers
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
