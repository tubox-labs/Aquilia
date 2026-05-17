# Internationalization Architecture

## Runtime Role

The internationalization and localization layer for locale parsing, catalog lookup, plural rules, formatting, lazy strings, middleware, DI, template integration, and CLI commands.

The implementation is split across 11 Python files. The module boundary is visible in the file inventory below and the API reference is generated from the same source files.

## Primary Source Files

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

## Internal Dependency Shape

The table below is derived from import statements in the module. It shows which top-level packages this module depends on most often.

| Imported package | Import count |
| --- | --- |
| `__future__` | 10 |
| `typing` | 8 |
| `logging` | 5 |
| `collections` | 4 |
| `locale` | 3 |
| `plural` | 3 |
| `abc` | 2 |
| `aquilia` | 2 |
| `catalog` | 2 |
| `dataclasses` | 2 |
| `datetime` | 2 |
| `enum` | 2 |
| `formatter` | 2 |
| `lazy` | 2 |
| `pathlib` | 2 |
| `re` | 2 |
| `contextvars` | 1 |
| `decimal` | 1 |
| `di_integration` | 1 |
| `faults` | 1 |
| `hashlib` | 1 |
| `json` | 1 |
| `middleware` | 1 |
| `service` | 1 |
| `template_integration` | 1 |

## Data And Control Flow

1. Configuration or direct construction creates the public service objects, controllers, providers, or helpers for this module.
2. Runtime code imports the registered classes from manifests, workspace integrations, middleware stacks, or direct application code.
3. Public methods perform validation and convert invalid states into typed Aquilia faults where the implementation defines fault classes.
4. Integration points return Python data structures, `Response` objects, provider results, jobs, sessions, connections, or model instances depending on the subsystem.

## Boundary Rules

- Keep application-specific business decisions outside framework classes unless the class is explicitly a service or controller owned by your app.
- Prefer the public exports and typed configuration dataclasses shown in `api-reference.md`.
- When a module supplies both a low-level primitive and a high-level service, use the service in application code and keep primitives for tests, providers, or advanced integrations.
