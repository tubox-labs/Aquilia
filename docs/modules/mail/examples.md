# Mail Examples

## Primary Usage

```python
from aquilia.mail import EmailMessage, MailConfig, MailService
from aquilia.mail.providers.console import ConsoleProvider

service = MailService(config=MailConfig(default_from="noreply@example.test"), provider=ConsoleProvider())
message = EmailMessage(to=["user@example.test"], subject="Welcome", body="Hello")
result = await service.send(message)
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
from aquilia.mail import ProviderConfigBlueprint, MailAuthConfigBlueprint, RetryConfigBlueprint, RateLimitConfigBlueprint, SecurityConfigBlueprint, TemplateConfigBlueprint
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
