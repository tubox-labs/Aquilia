# Extended Middleware Examples

## Primary Usage

```python
from aquilia.middleware_ext import EffectMiddleware, FlowContextMiddleware, CombinedLogFormatter, DevLogFormatter, StructuredLogFormatter, EnhancedLoggingMiddleware

# The imported symbols above are public exports from this module.
# See api-reference.md for constructor signatures, methods, and data fields.
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
from aquilia.middleware_ext import EffectMiddleware, FlowContextMiddleware, CombinedLogFormatter, StructuredLogFormatter, DevLogFormatter, LoggingMiddleware
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
