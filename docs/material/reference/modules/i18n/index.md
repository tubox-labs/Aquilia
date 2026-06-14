# I18n Module

> `aquilia.i18n` — Internationalization and localization

The I18n module provides full internationalization support including translation catalogs, locale negotiation, plural rules, lazy translation strings, date/number/currency formatters, and I18nMiddleware.

## When to Use

Use the I18n module when you need:

- Multi-language support in your application
- Locale negotiation from Accept-Language headers
- Plural-aware message formatting
- Date, number, and currency formatting per locale
- Lazy translation strings for deferred evaluation

## Key Classes

| Class | Purpose |
|---|---|
| `I18nService` | Central internationalization service |
| `TranslationCatalog` | Translation catalog interface |
| `MemoryCatalog` | In-memory translation catalog |
| `FileCatalog` | File-based translation catalog (JSON/YAML/PO) |
| `NamespacedCatalog` | Namespace-prefixed catalog wrapper |
| `MergedCatalog` | Merges multiple catalogs with precedence |
| `Locale` | Locale representation and parsing |
| `LazyString` | Deferred-translation string |
| `MessageFormatter` | ICU message formatting |
| `I18nMiddleware` | Locale negotiation middleware |
| `PluralCategory` | Plural rule categories (zero, one, two, few, many, other) |

## Quick Example

```python
from aquilia.i18n import I18nService, MemoryCatalog, format_date, format_number

# Create a service with catalogs
service = I18nService(
    default_locale="en",
    catalogs={
        "en": MemoryCatalog({"hello": "Hello, {name}!"}),
        "fr": MemoryCatalog({"hello": "Bonjour, {name}!"}),
        "ja": MemoryCatalog({"hello": "こんにちは、{name}さん！"}),
    },
)

# Translate
msg = service.translate("hello", locale="fr", name="Alice")
# "Bonjour, Alice!"

# Lazy translation
from aquilia.i18n import lazy_t
msg = lazy_t("hello", name=user.name)
# Evaluated when rendered, using the current request locale

# Formatters
from aquilia.i18n import format_number, format_currency, format_date

format_number(1234567.89, locale="de")    # "1.234.567,89"
format_currency(42.99, "EUR", locale="fr")  # "42,99 €"
format_date(dt, locale="ja")               # "2026年6月14日"
```

## Import Path

```python
from aquilia.i18n import (
    I18nService,
    I18nConfig,
    I18nMiddleware,
    TranslationCatalog,
    MemoryCatalog,
    FileCatalog,
    NamespacedCatalog,
    MergedCatalog,
    Locale,
    LazyString,
    lazy_t,
    lazy_tn,
    MessageFormatter,
    PluralCategory,
    negotiate_locale,
    parse_locale,
    normalize_locale,
    format_date,
    format_time,
    format_datetime,
    format_number,
    format_currency,
    format_percent,
    format_ordinal,
)
```

## Related Modules

- [templates](../templates/index.md) — Template rendering with translations
- [integrations](../integrations/index.md) — `I18nIntegration` config builder
- [cli](../cli/index.md) — `aq i18n` extraction and compilation