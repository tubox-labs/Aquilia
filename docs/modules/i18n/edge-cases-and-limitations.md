# Internationalization Edge Cases And Limitations

## Fault And Error Types

The following error-oriented classes are present in the implementation and should guide defensive usage.

| Type | Source | Meaning |
| --- | --- | --- |
| `I18nFault` | `aquilia/i18n/faults.py` | Base fault for all i18n-related errors. |
| `MissingTranslationFault` | `aquilia/i18n/faults.py` | Raised when a translation key cannot be found in any catalog. |
| `InvalidLocaleFault` | `aquilia/i18n/faults.py` | Raised when a locale tag cannot be parsed as valid BCP 47. |
| `CatalogLoadFault` | `aquilia/i18n/faults.py` | Raised when a translation catalog file cannot be loaded. |
| `PluralRuleFault` | `aquilia/i18n/faults.py` | Raised when plural form selection fails. |

## Common Edge Cases

- Optional dependencies may change behavior. Check imports and constructor docs before enabling production features.
- In-memory stores, queues, caches, adapters, and registries are usually process-local. Use durable backends when state must survive restarts or scale across workers.
- Request-scoped data must not be cached globally. Use request state, DI request scopes, or explicit parameters.
- Decorators in Aquilia generally attach metadata at import time. Runtime behavior happens later during compilation, routing, middleware execution, or service startup.
- Many subsystems intentionally convert invalid states into typed faults. Catch the specific fault type when application code can recover.

## Source-Level Limits To Review

Review these files before changing behavior:

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
