# Internationalization Documentation

This directory is the professional documentation set for `i18n`. It is implementation-driven and aligned with the current source files under `aquilia/i18n`.

## What This Covers

The internationalization and localization layer for locale parsing, catalog lookup, plural rules, formatting, lazy strings, middleware, DI, template integration, and CLI commands.

## Source Files Read

- `aquilia/i18n/__init__.py`: AquilaI18n - Industry-grade Internationalization & Localization for Aquilia.
- `aquilia/i18n/catalog.py`: Translation Catalogs - Storage and retrieval of translation strings.
- `aquilia/i18n/di_integration.py`: I18n DI Integration - Register i18n providers in Aquilia's DI container.
- `aquilia/i18n/faults.py`: I18n Faults - Typed fault signals for the i18n subsystem.
- `aquilia/i18n/formatter.py`: Message Formatter - ICU MessageFormat-inspired interpolation & locale formatting.
- `aquilia/i18n/lazy.py`: Lazy Strings - Deferred translation resolution.
- `aquilia/i18n/locale.py`: Locale - BCP 47 locale tag parsing, normalization, and negotiation.
- `aquilia/i18n/middleware.py`: I18n Middleware - Request-scoped locale resolution & injection.
- `aquilia/i18n/plural.py`: Plural Rules - CLDR-based plural category selection for 200+ languages.
- `aquilia/i18n/service.py`: I18n Service - Central orchestrator for all translation operations.
- `aquilia/i18n/template_integration.py`: I18n Template Integration - Jinja2 globals, filters, and extensions.

## Document Map

- `architecture.md`: Runtime architecture and module boundaries
- `configuration.md`: Configuration entry points, datatypes, and precedence
- `api-reference.md`: Classes, methods, functions, constants, and data fields extracted from source
- `integration-guide.md`: How to wire the module into a real Aquilia application
- `cli-reference.md`: Command line surface and operational commands
- `edge-cases-and-limitations.md`: Known edge cases and implementation limits
- `troubleshooting.md`: Common failures and diagnosis steps
- `examples.md`: Code examples and usage patterns

## Public Surface Snapshot

- Python files: 11
- Public classes: 28
- Configuration or dataclass-like types: 2
- Public functions: 26
- Constants detected: 11

## Fast Start

```python
from aquilia.i18n import __version__, CrousCatalog, FileCatalog, MemoryCatalog, MergedCatalog, NamespacedCatalog

# The imported symbols above are public exports from this module.
# See api-reference.md for constructor signatures, methods, and data fields.
```

## Read Next

Start with `architecture.md` if you are learning how the subsystem fits into runtime boot. Use `api-reference.md` when you need exact methods, datatypes, and class fields. Use `examples.md` for copyable patterns that match the current code.
