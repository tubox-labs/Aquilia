# Mail Examples

Async mail subsystem with message classes, config blueprints, providers, DI registration, templates, faults, and convenience send APIs.

Examples here use public symbols and checked patterns from the repository. When a module has no safe standalone constructor example, the example focuses on importing and wiring the actual source-backed API.

## Source-Backed Import Examples

```python
from aquilia.mail.config import ProviderConfigBlueprint
from aquilia.mail.config import MailAuthConfigBlueprint
from aquilia.mail.di_providers import MailConfigProvider
from aquilia.mail.di_providers import MailServiceProvider
from aquilia.mail.di_providers import create_mail_config
from aquilia.mail.envelope import EnvelopeStatus
```

## Workspace/Manifest Wiring Example

```python
from aquilia import AppManifest, Integration, Module, Workspace

workspace = (
    Workspace("example", version="1.0.0")
    .runtime(mode="dev", port=8000)
    .module(Module("example").route_prefix("/example"))
    .integrate(Integration.di(auto_wire=True))
)

manifest = AppManifest(
    name="example",
    version="1.0.0",
    controllers=["modules.example.controllers:ExampleController"],
    services=["modules.example.services:ExampleService"],
)
```

## Verification

- Run `python -m aquilia.cli.__main__ --help` to confirm CLI availability.
- Run `aq validate` in a workspace to validate manifest paths.
- Run related tests under `tests/` or `examples/*/tests/` for executable behavior.
