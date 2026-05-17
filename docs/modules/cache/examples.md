# Cache Examples

## Primary Usage

```python
from aquilia.cache import CacheService, MemoryBackend, cached

cache = CacheService(backend=MemoryBackend())
await cache.set("catalog:featured", [{"sku": "AQ-STARTER"}], ttl=300)
items = await cache.get("catalog:featured")

@cached(ttl=60)
async def expensive_lookup(key: str):
    return {"key": key}
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
from aquilia.cache import CompositeBackend, MemoryBackend, NullBackend, RedisBackend, EvictionPolicy, CacheEntry
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
