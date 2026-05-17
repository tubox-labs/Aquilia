# Templates Examples

## Primary Usage

```python
from aquilia.templates import TemplateEngine, create_development_engine

engine = create_development_engine(search_paths=["templates"])
html = await engine.render("orders/detail.html", {"order_id": "ord_001"})
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
from aquilia.templates import IdentityTemplateProxy, TemplateAuthGuard, TemplateAuthMixin, BytecodeCache, InMemoryBytecodeCache, CrousBytecodeCache
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
