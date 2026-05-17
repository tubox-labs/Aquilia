# Faults Examples

## Primary Usage

```python
from aquilia.faults import Fault, FaultDomain, Severity

class CatalogFault(Fault):
    def __init__(self, sku: str):
        super().__init__(
            code="CATALOG_NOT_FOUND",
            message=f"Product {sku} was not found",
            domain=FaultDomain.MODEL,
            severity=Severity.WARNING,
            metadata={"sku": sku},
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
from aquilia.faults import Severity, FaultDomain, RecoveryStrategy, Fault, FaultContext, Resolved
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
