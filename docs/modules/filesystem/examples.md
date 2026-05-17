# Filesystem Examples

## Primary Usage

```python
from aquilia.filesystem import FileSystemConfig, FileSystemService

service = FileSystemService(FileSystemConfig(root="var/data"))
await service.write_bytes("reports/today.txt", b"ready")
content = await service.read_bytes("reports/today.txt")
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
from aquilia.filesystem import FileSystemConfig, DirEntry, FileSystemFault, FileNotFoundFault, PermissionDeniedFault, FileExistsFault
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
