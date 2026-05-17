# Testing Examples

## Primary Usage

```python
from aquilia.testing import make_test_request, TestClient

request = make_test_request(method="GET", path="/health")
client = TestClient(app)
response = await client.get("/health")
assert response.status_code == 200
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
from aquilia.testing import AquiliaAssertions, TestIdentityFactory, IdentityBuilder, AuthTestMixin, MockCacheBackend, CacheTestMixin
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
