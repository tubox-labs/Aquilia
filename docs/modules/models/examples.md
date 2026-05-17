# Models And ORM Examples

## Primary Usage

```python
from aquilia.models import Model
from aquilia.models.fields import BooleanField, CharField, DateTimeField

class User(Model):
    table = "users"
    email = CharField(max_length=255, unique=True)
    name = CharField(max_length=150)
    active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)

user = await User.objects.create(email="ada@example.com", name="Ada")
active_users = await User.objects.filter(active=True).all()
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
from aquilia.models import Aggregate, Sum, Avg, Count, Max, Min
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
