<!-- Legacy mirror. Canonical page: ../modules/i18n/examples.md -->

# I18N Examples

Internationalization service, locale negotiation, catalogs, formatting, plural rules, lazy strings, middleware, CLI helpers, and template integration.

Examples here use public symbols and checked patterns from the repository. When a module has no safe standalone constructor example, the example focuses on importing and wiring the actual source-backed API.

## Source-Backed Import Examples

```python
from aquilia.i18n.catalog import TranslationCatalog
from aquilia.i18n.catalog import MemoryCatalog
from aquilia.i18n.catalog import has_surp
from aquilia.i18n.di_integration import register_i18n_providers
from aquilia.i18n.faults import I18nFault
from aquilia.i18n.faults import MissingTranslationFault
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
