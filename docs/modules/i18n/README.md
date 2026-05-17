# i18n Module

## Purpose

Internationalization and localization service. Use this module for catalogs, locale parsing, negotiation, plural rules, message formatting, lazy strings, middleware, DI, and template integration.

## Source Coverage

- Python files: 11
- Public classes: 28
- Dataclasses: 2
- Enums: 2
- Public functions: 26

## How It Fits In Aquilia

1. Import the package from `aquilia.i18n` or its concrete submodules.
2. Configure it through workspace integrations, manifests, or direct service construction depending on the subsystem.
3. Keep business logic outside transport and framework glue so the subsystem stays testable.

## Practical Guidance

- Prefer typed configuration objects and framework helpers over ad hoc dictionaries when they exist.
- Use the tests in `tests/` as behavioral examples when changing this subsystem.

## Public Classes

| Name | Source | Role |
| --- | --- | --- |
| `TranslationCatalog` | `aquilia/i18n/catalog.py` | Abstract base for translation catalogs. |
| `MemoryCatalog` | `aquilia/i18n/catalog.py` | In-memory translation catalog backed by nested dicts. |
| `FileCatalog` | `aquilia/i18n/catalog.py` | File-based translation catalog loading from ``locales/`` directory. |
| `CrousCatalog` | `aquilia/i18n/catalog.py` | CROUS artifact-backed translation catalog. |
| `NamespacedCatalog` | `aquilia/i18n/catalog.py` | Wraps a catalog with a fixed namespace prefix. |
| `MergedCatalog` | `aquilia/i18n/catalog.py` | Layered catalog that queries multiple catalogs with fallback. |
| `I18nFault` | `aquilia/i18n/faults.py` | Base fault for all i18n-related errors. |
| `MissingTranslationFault` | `aquilia/i18n/faults.py` | Raised when a translation key cannot be found in any catalog. |
| `InvalidLocaleFault` | `aquilia/i18n/faults.py` | Raised when a locale tag cannot be parsed as valid BCP 47. |
| `CatalogLoadFault` | `aquilia/i18n/faults.py` | Raised when a translation catalog file cannot be loaded. |
| `PluralRuleFault` | `aquilia/i18n/faults.py` | Raised when plural form selection fails. |
| `MessageFormatter` | `aquilia/i18n/formatter.py` | ICU MessageFormat-inspired string formatter. |
| `LazyString` | `aquilia/i18n/lazy.py` | A string-like object that defers translation until stringification. |
| `LazyPluralString` | `aquilia/i18n/lazy.py` | Lazy string with plural support. |
| `Locale` | `aquilia/i18n/locale.py` | Immutable BCP 47 locale tag. |
| `LocaleResolver` | `aquilia/i18n/middleware.py` | Abstract locale resolver. |
| `HeaderLocaleResolver` | `aquilia/i18n/middleware.py` | Resolve locale from the ``Accept-Language`` HTTP header. |
| `CookieLocaleResolver` | `aquilia/i18n/middleware.py` | Resolve locale from a cookie. |
| `QueryLocaleResolver` | `aquilia/i18n/middleware.py` | Resolve locale from a query parameter. |
| `PathLocaleResolver` | `aquilia/i18n/middleware.py` | Resolve locale from the URL path prefix. |
| `SessionLocaleResolver` | `aquilia/i18n/middleware.py` | Resolve locale from the user's session. |
| `ChainLocaleResolver` | `aquilia/i18n/middleware.py` | Composite resolver that tries multiple resolvers in order. |
| `I18nMiddleware` | `aquilia/i18n/middleware.py` | Aquilia middleware that resolves locale and injects i18n into requests. |
| `PluralCategory` | `aquilia/i18n/plural.py` | CLDR plural categories. |
| `MissingKeyStrategy` | `aquilia/i18n/service.py` | What to do when a translation key is not found. |
| `I18nConfig` | `aquilia/i18n/service.py` | Configuration for the i18n service. |
| `I18nService` | `aquilia/i18n/service.py` | Central i18n orchestrator. |
| `I18nTemplateExtension` | `aquilia/i18n/template_integration.py` | Lightweight template extension descriptor for Aquilia's template engine. |

## Public Functions

| Name | Source | Role |
| --- | --- | --- |
| `has_crous` | `aquilia/i18n/catalog.py` | Check if the CROUS binary format library is available. |
| `register_i18n_providers` | `aquilia/i18n/di_integration.py` | Register i18n providers in a DI container. |
| `register_i18n_request_providers` | `aquilia/i18n/di_integration.py` | Register request-scoped i18n providers. |
| `format_message` | `aquilia/i18n/formatter.py` | Convenience function for one-shot message formatting. |
| `format_number` | `aquilia/i18n/formatter.py` | Format a number with locale-specific separators. |
| `format_decimal` | `aquilia/i18n/formatter.py` | Format a decimal number with fixed precision. |
| `format_percent` | `aquilia/i18n/formatter.py` | Format a fraction as a percentage. |
| `format_currency` | `aquilia/i18n/formatter.py` | Format a monetary value with currency symbol. |
| `format_ordinal` | `aquilia/i18n/formatter.py` | Format an ordinal number. |
| `format_date` | `aquilia/i18n/formatter.py` | Format a date with locale-specific patterns. |
| `format_time` | `aquilia/i18n/formatter.py` | Format a time with locale-specific patterns. |
| `format_datetime` | `aquilia/i18n/formatter.py` | Format a datetime with locale-specific patterns. |
| `set_lazy_context` | `aquilia/i18n/lazy.py` | Set the global i18n context for lazy string resolution. |
| `clear_lazy_context` | `aquilia/i18n/lazy.py` | Clear the lazy context (called at request cleanup). |
| `lazy_t` | `aquilia/i18n/lazy.py` | Create a lazy translation string. |
| `lazy_tn` | `aquilia/i18n/lazy.py` | Create a lazy plural translation string. |
| `parse_locale` | `aquilia/i18n/locale.py` | Parse a BCP 47 language tag into a ``Locale`` object. |
| `normalize_locale` | `aquilia/i18n/locale.py` | Normalize a locale tag to canonical BCP 47 form. |
| `match_locale` | `aquilia/i18n/locale.py` | Find the best matching locale from available options. |
| `parse_accept_language` | `aquilia/i18n/locale.py` | Parse an ``Accept-Language`` header into a list of (tag, quality) tuples. |
| `negotiate_locale` | `aquilia/i18n/locale.py` | Negotiate the best locale from an Accept-Language header and available locales. |
| `build_resolver` | `aquilia/i18n/middleware.py` | Build a ``ChainLocaleResolver`` from an ``I18nConfig``. |
| `get_plural_rule` | `aquilia/i18n/plural.py` | Get the plural rule function for a language. |
| `select_plural` | `aquilia/i18n/plural.py` | Select the plural category for a number in a given language. |
| `create_i18n_service` | `aquilia/i18n/service.py` | Factory function for creating an ``I18nService``. |
| `register_i18n_template_globals` | `aquilia/i18n/template_integration.py` | Register i18n globals and filters on a Jinja2 Environment. |

## Implementation Map

| File | What To Look For |
| --- | --- |
| `aquilia/i18n/__init__.py` | AquilaI18n - Industry-grade Internationalization & Localization for Aquilia. |
| `aquilia/i18n/catalog.py` | Translation Catalogs - Storage and retrieval of translation strings. |
| `aquilia/i18n/di_integration.py` | I18n DI Integration - Register i18n providers in Aquilia's DI container. |
| `aquilia/i18n/faults.py` | I18n Faults - Typed fault signals for the i18n subsystem. |
| `aquilia/i18n/formatter.py` | Message Formatter - ICU MessageFormat-inspired interpolation & locale formatting. |
| `aquilia/i18n/lazy.py` | Lazy Strings - Deferred translation resolution. |
| `aquilia/i18n/locale.py` | Locale - BCP 47 locale tag parsing, normalization, and negotiation. |
| `aquilia/i18n/middleware.py` | I18n Middleware - Request-scoped locale resolution & injection. |
| `aquilia/i18n/plural.py` | Plural Rules - CLDR-based plural category selection for 200+ languages. |
| `aquilia/i18n/service.py` | I18n Service - Central orchestrator for all translation operations. |
| `aquilia/i18n/template_integration.py` | I18n Template Integration - Jinja2 globals, filters, and extensions. |

## Testing Pointers

Search `tests/` for `i18n` to find behavior-level examples. The test suite is especially useful for edge cases because many modules expose lightweight public APIs but enforce important security and lifecycle behavior internally.
