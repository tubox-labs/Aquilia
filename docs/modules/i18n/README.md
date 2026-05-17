# I18N Documentation

Internationalization service, locale negotiation, catalogs, formatting, plural rules, lazy strings, middleware, CLI helpers, and template integration.

## Coverage Snapshot

- Source files: 11
- Source lines: 4190
- Public classes: 28
- Public module functions: 26
- Constants/module flags: 12
- Public exports in `__all__`: 50

## Source Files Read

- `aquilia/i18n/__init__.py`: AquilaI18n — Industry-grade Internationalization & Localization for Aquilia.
- `aquilia/i18n/catalog.py`: Translation Catalogs — Storage and retrieval of translation strings.
- `aquilia/i18n/di_integration.py`: I18n DI Integration — Register i18n providers in Aquilia's DI container.
- `aquilia/i18n/faults.py`: I18n Faults — Typed fault signals for the i18n subsystem.
- `aquilia/i18n/formatter.py`: Message Formatter — ICU MessageFormat-inspired interpolation & locale formatting.
- `aquilia/i18n/lazy.py`: Lazy Strings — Deferred translation resolution.
- `aquilia/i18n/locale.py`: Locale — BCP 47 locale tag parsing, normalization, and negotiation.
- `aquilia/i18n/middleware.py`: I18n Middleware — Request-scoped locale resolution & injection.
- `aquilia/i18n/plural.py`: Plural Rules — CLDR-based plural category selection for 200+ languages.
- `aquilia/i18n/service.py`: I18n Service — Central orchestrator for all translation operations.
- `aquilia/i18n/template_integration.py`: I18n Template Integration — Jinja2 globals, filters, and extensions.

## Document Map

- `architecture.md`: module boundaries, dependencies, lifecycle, and extension points.
- `configuration.md`: configuration classes, builders, server wiring, and precedence.
- `api-reference.md`: source-extracted classes, methods, functions, constants, exports, and signatures.
- `integration-guide.md`: how to wire the module into an Aquilia app.
- `cli-reference.md`: mounted `aq` commands for this module, if any.
- `examples.md`: usage examples derived from source and checked example apps.
- `edge-cases-and-limitations.md`: implementation limits and compatibility behavior.
- `troubleshooting.md`: diagnostic commands and common failure patterns.
