# Blueprints Examples

## Primary Usage

```python
from aquilia.blueprints import Blueprint

class CreateUser(Blueprint):
    email: str
    name: str
    active: bool = True

    class Spec:
        extra_fields = "reject"

    def seal_email(self, data):
        email = data.get("email", "").strip().lower()
        if "@" not in email:
            self.reject("email", "Email address is required")
        data["email"] = email

bp = CreateUser(data={"email": "ADA@example.com", "name": "Ada"})
assert bp.is_sealed() is True
payload = bp.validated_data
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
from aquilia.blueprints import Field, NestedBlueprintFacet, LazyBlueprintFacet, BlueprintMeta, Blueprint, BlueprintFault
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
