# Authentication And Authorization Examples

## Primary Usage

```python
from aquilia.auth.core import Identity, IdentityType, PasswordCredential
from aquilia.auth.hashing import PasswordHasher
from aquilia.auth.manager import AuthManager
from aquilia.auth.stores import MemoryCredentialStore, MemoryIdentityStore, MemoryTokenStore
from aquilia.auth.tokens import KeyDescriptor, KeyRing, TokenManager

identity_store = MemoryIdentityStore()
credential_store = MemoryCredentialStore()
token_store = MemoryTokenStore()
key = KeyDescriptor.generate(kid="dev", algorithm="HS256", secret="replace-me")
manager = AuthManager(
    token_manager=TokenManager(KeyRing(keys=[key]), token_store),
    identity_store=identity_store,
    credential_store=credential_store,
    password_hasher=PasswordHasher(),
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
from aquilia.auth import AuditEventType, AuditSeverity, AuditEvent, AuditStore, MemoryAuditStore, LoggingAuditStore
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
