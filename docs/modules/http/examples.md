# HTTP Client Examples

## Primary Usage

```python
from aquilia.http import AsyncHTTPClient, HTTPClientConfig, RetryConfig

client = AsyncHTTPClient(
    HTTPClientConfig(
        base_url="https://api.example.test",
        retry=RetryConfig(max_attempts=3),
    )
)
response = await client.get("/health")
data = await response.json()
await client.close()
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
from aquilia.http import RawResponse, ConnectionInfo, ConnectionPool, HTTPTransport, NativeTransport, MockTransport
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
