# Sessions Examples

## Primary Usage

```python
from datetime import timedelta
from aquilia.sessions import SessionPolicy, PersistencePolicy, TransportPolicy

user_sessions = SessionPolicy(
    name="user",
    ttl=timedelta(days=7),
    idle_timeout=timedelta(hours=1),
    persistence=PersistencePolicy(enabled=True, store_name="memory"),
    transport=TransportPolicy(adapter="cookie", cookie_httponly=True),
    scope="user",
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
from aquilia.sessions import SessionID, SessionScope, SessionFlag, SessionPrincipal, Session, SessionRequiredFault
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
