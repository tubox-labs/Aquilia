<!-- Legacy mirror. Canonical page: ../modules/i18n/architecture.md -->

# I18N Architecture

Internationalization service, locale negotiation, catalogs, formatting, plural rules, lazy strings, middleware, CLI helpers, and template integration.

## Source Boundaries

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/i18n/__init__.py` | 182 | 0 | 0 | AquilaI18n — Industry-grade Internationalization & Localization for Aquilia. |
| `aquilia/i18n/catalog.py` | 810 | 6 | 1 | Translation Catalogs — Storage and retrieval of translation strings. |
| `aquilia/i18n/di_integration.py` | 183 | 0 | 2 | I18n DI Integration — Register i18n providers in Aquilia's DI container. |
| `aquilia/i18n/faults.py` | 187 | 5 | 0 | I18n Faults — Typed fault signals for the i18n subsystem. |
| `aquilia/i18n/formatter.py` | 627 | 1 | 9 | Message Formatter — ICU MessageFormat-inspired interpolation & locale formatting. |
| `aquilia/i18n/lazy.py` | 289 | 2 | 4 | Lazy Strings — Deferred translation resolution. |
| `aquilia/i18n/locale.py` | 352 | 1 | 5 | Locale — BCP 47 locale tag parsing, normalization, and negotiation. |
| `aquilia/i18n/middleware.py` | 423 | 8 | 1 | I18n Middleware — Request-scoped locale resolution & injection. |
| `aquilia/i18n/plural.py` | 515 | 1 | 2 | Plural Rules — CLDR-based plural category selection for 200+ languages. |
| `aquilia/i18n/service.py` | 425 | 3 | 1 | I18n Service — Central orchestrator for all translation operations. |
| `aquilia/i18n/template_integration.py` | 197 | 1 | 1 | I18n Template Integration — Jinja2 globals, filters, and extensions. |

## Internal Shape

`i18n` has 11 Python files, 28 public classes, 26 public module-level functions, and 12 constants or module flags detected by AST.

## Runtime Responsibilities

- This module has `aq` command coverage documented in `cli-reference.md`; 6 commands map to this subsystem.

## Internal Imports

| Import | Count |
| --- | ---: |
| `.locale` | 3 |
| `.plural` | 3 |
| `.catalog` | 2 |
| `.formatter` | 2 |
| `.lazy` | 2 |
| `.di_integration` | 1 |
| `.faults` | 1 |
| `.middleware` | 1 |
| `.service` | 1 |
| `.template_integration` | 1 |
| `aquilia._version` | 1 |
| `aquilia.faults.core` | 1 |

## External And Stdlib Imports

| Import root | Count |
| --- | ---: |
| `__future__` | 10 |
| `typing` | 8 |
| `logging` | 5 |
| `collections` | 4 |
| `abc` | 2 |
| `dataclasses` | 2 |
| `datetime` | 2 |
| `enum` | 2 |
| `pathlib` | 2 |
| `re` | 2 |
| `contextvars` | 1 |
| `decimal` | 1 |
| `hashlib` | 1 |
| `json` | 1 |

## Lifecycle And Extension Points

| Extension Type | Source | Role |
| --- | --- | --- |
| `I18nMiddleware` | `aquilia/i18n/middleware.py` | Aquilia middleware that resolves locale and injects i18n into requests. |
| `I18nConfig` | `aquilia/i18n/service.py` | Configuration for the i18n service. |

## Error Handling

Fault/error classes defined here:

`I18nFault`, `MissingTranslationFault`, `InvalidLocaleFault`, `CatalogLoadFault`, `PluralRuleFault`
