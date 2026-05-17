# Storage Examples

## Primary Usage

```python
from aquilia.storage import LocalConfig, LocalStorage

storage = LocalStorage(LocalConfig(root="var/uploads"))
await storage.save("avatars/ada.txt", b"profile data", content_type="text/plain")
file = await storage.open("avatars/ada.txt")
metadata = await storage.stat("avatars/ada.txt")
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
from aquilia.storage import AzureBlobStorage, CompositeStorage, GCSStorage, LocalStorage, MemoryStorage, S3Storage
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
