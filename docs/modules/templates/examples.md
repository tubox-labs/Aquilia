# Templates Examples

Jinja2 template engine, loaders, manager, middleware, bytecode cache, sandbox, DI providers, manifest/session/auth/i18n integration, and template CLI helpers.

Examples here use public symbols and checked patterns from the repository. When a module has no safe standalone constructor example, the example focuses on importing and wiring the actual source-backed API.

## Source-Backed Import Examples

```python
from aquilia.templates.auth_integration import IdentityTemplateProxy
from aquilia.templates.auth_integration import TemplateAuthGuard
from aquilia.templates.auth_integration import create_auth_helpers
from aquilia.templates.bytecode_cache import BytecodeCache
from aquilia.templates.bytecode_cache import InMemoryBytecodeCache
from aquilia.templates.cli import create_template_engine_from_config
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
