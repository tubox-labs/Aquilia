<!-- Legacy mirror. Canonical page: ../modules/i18n/api-reference.md -->

# I18N API Reference

This page is generated from the current Python source using the AST. It lists public classes, public methods, public module-level functions, constants, exports, and source files.

## Source Inventory

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

## Public Exports

`CLDR_PLURAL_RULES`, `CatalogLoadFault`, `ChainLocaleResolver`, `CookieLocaleResolver`, `CrousCatalog`, `FileCatalog`, `HeaderLocaleResolver`, `I18nConfig`, `I18nFault`, `I18nMiddleware`, `I18nService`, `I18nTemplateExtension`, `InvalidLocaleFault`, `LazyString`, `Locale`, `LocaleResolver`, `MemoryCatalog`, `MergedCatalog`, `MessageFormatter`, `MissingTranslationFault`, `NamespacedCatalog`, `PathLocaleResolver`, `PluralCategory`, `PluralRule`, `PluralRuleFault`, `QueryLocaleResolver`, `SessionLocaleResolver`, `TranslationCatalog`, `create_i18n_service`, `format_currency`, `format_date`, `format_datetime`, `format_decimal`, `format_message`, `format_number`, `format_ordinal`, `format_percent`, `format_time`, `get_plural_rule`, `has_crous`, `lazy_t`, `lazy_tn`, `match_locale`, `negotiate_locale`, `normalize_locale`, `parse_accept_language`, `parse_locale`, `register_i18n_providers`, `register_i18n_template_globals`, `select_plural`

## Public Class Summary

| Class | Source | Bases | Summary |
| --- | --- | --- | --- |
| `TranslationCatalog` | `aquilia/i18n/catalog.py` | ABC | Abstract base for translation catalogs. |
| `MemoryCatalog` | `aquilia/i18n/catalog.py` | TranslationCatalog | In-memory translation catalog backed by nested dicts. |
| `FileCatalog` | `aquilia/i18n/catalog.py` | TranslationCatalog | File-based translation catalog loading from ``locales/`` directory. |
| `CrousCatalog` | `aquilia/i18n/catalog.py` | TranslationCatalog | CROUS artifact-backed translation catalog. |
| `NamespacedCatalog` | `aquilia/i18n/catalog.py` | TranslationCatalog | Wraps a catalog with a fixed namespace prefix. |
| `MergedCatalog` | `aquilia/i18n/catalog.py` | TranslationCatalog | Layered catalog that queries multiple catalogs with fallback. |
| `I18nFault` | `aquilia/i18n/faults.py` | Fault | Base fault for all i18n-related errors. |
| `MissingTranslationFault` | `aquilia/i18n/faults.py` | I18nFault | Raised when a translation key cannot be found in any catalog. |
| `InvalidLocaleFault` | `aquilia/i18n/faults.py` | I18nFault | Raised when a locale tag cannot be parsed as valid BCP 47. |
| `CatalogLoadFault` | `aquilia/i18n/faults.py` | I18nFault | Raised when a translation catalog file cannot be loaded. |
| `PluralRuleFault` | `aquilia/i18n/faults.py` | I18nFault | Raised when plural form selection fails. |
| `MessageFormatter` | `aquilia/i18n/formatter.py` | object | ICU MessageFormat-inspired string formatter. |
| `LazyString` | `aquilia/i18n/lazy.py` | object | A string-like object that defers translation until stringification. |
| `LazyPluralString` | `aquilia/i18n/lazy.py` | LazyString | Lazy string with plural support. |
| `Locale` | `aquilia/i18n/locale.py` | object | Immutable BCP 47 locale tag. |
| `LocaleResolver` | `aquilia/i18n/middleware.py` | ABC | Abstract locale resolver. |
| `HeaderLocaleResolver` | `aquilia/i18n/middleware.py` | LocaleResolver | Resolve locale from the ``Accept-Language`` HTTP header. |
| `CookieLocaleResolver` | `aquilia/i18n/middleware.py` | LocaleResolver | Resolve locale from a cookie. |
| `QueryLocaleResolver` | `aquilia/i18n/middleware.py` | LocaleResolver | Resolve locale from a query parameter. |
| `PathLocaleResolver` | `aquilia/i18n/middleware.py` | LocaleResolver | Resolve locale from the URL path prefix. |
| `SessionLocaleResolver` | `aquilia/i18n/middleware.py` | LocaleResolver | Resolve locale from the user's session. |
| `ChainLocaleResolver` | `aquilia/i18n/middleware.py` | LocaleResolver | Composite resolver that tries multiple resolvers in order. |
| `I18nMiddleware` | `aquilia/i18n/middleware.py` | object | Aquilia middleware that resolves locale and injects i18n into requests. |
| `PluralCategory` | `aquilia/i18n/plural.py` | str, Enum | CLDR plural categories. |
| `MissingKeyStrategy` | `aquilia/i18n/service.py` | str, Enum | What to do when a translation key is not found. |
| `I18nConfig` | `aquilia/i18n/service.py` | object | Configuration for the i18n service. |
| `I18nService` | `aquilia/i18n/service.py` | object | Central i18n orchestrator. |
| `I18nTemplateExtension` | `aquilia/i18n/template_integration.py` | object | Lightweight template extension descriptor for Aquilia's template engine. |

## Public Function Summary

| Function | Source | Signature | Summary |
| --- | --- | --- | --- |
| `has_crous` | `aquilia/i18n/catalog.py` | `def has_crous()` | Check if the CROUS binary format library is available. |
| `register_i18n_providers` | `aquilia/i18n/di_integration.py` | `def register_i18n_providers(container: Any, service: I18nService, config: I18nConfig \| None=None)` | Register i18n providers in a DI container. |
| `register_i18n_request_providers` | `aquilia/i18n/di_integration.py` | `def register_i18n_request_providers(container: Any, locale: str, service: I18nService)` | Register request-scoped i18n providers. |
| `format_message` | `aquilia/i18n/formatter.py` | `def format_message(pattern: str, locale: str='en', **kwargs: Any)` | Convenience function for one-shot message formatting. |
| `format_number` | `aquilia/i18n/formatter.py` | `def format_number(value: Number, locale: str='en', *, decimals: int \| None=None)` | Format a number with locale-specific separators. |
| `format_decimal` | `aquilia/i18n/formatter.py` | `def format_decimal(value: Number, locale: str='en', decimals: int=2)` | Format a decimal number with fixed precision. |
| `format_percent` | `aquilia/i18n/formatter.py` | `def format_percent(value: Number, locale: str='en', decimals: int=0)` | Format a fraction as a percentage. |
| `format_currency` | `aquilia/i18n/formatter.py` | `def format_currency(value: Number, currency: str='USD', locale: str='en', *, decimals: int=2)` | Format a monetary value with currency symbol. |
| `format_ordinal` | `aquilia/i18n/formatter.py` | `def format_ordinal(value: int, locale: str='en')` | Format an ordinal number. |
| `format_date` | `aquilia/i18n/formatter.py` | `def format_date(value: date, locale: str='en', *, style: str='medium')` | Format a date with locale-specific patterns. |
| `format_time` | `aquilia/i18n/formatter.py` | `def format_time(value: time \| datetime, locale: str='en', *, style: str='short')` | Format a time with locale-specific patterns. |
| `format_datetime` | `aquilia/i18n/formatter.py` | `def format_datetime(value: datetime, locale: str='en', *, date_style: str='medium', time_style: str='short', separator: str=' ')` | Format a datetime with locale-specific patterns. |
| `set_lazy_context` | `aquilia/i18n/lazy.py` | `def set_lazy_context(service: I18nService, locale: str \| None=None)` | Set the global i18n context for lazy string resolution. |
| `clear_lazy_context` | `aquilia/i18n/lazy.py` | `def clear_lazy_context()` | Clear the lazy context (called at request cleanup). |
| `lazy_t` | `aquilia/i18n/lazy.py` | `def lazy_t(key: str, *, default: str \| None=None, locale: str \| None=None, service: I18nService \| None=None, **kwargs: Any)` | Create a lazy translation string. |
| `lazy_tn` | `aquilia/i18n/lazy.py` | `def lazy_tn(key: str, count: int \| float, *, default: str \| None=None, locale: str \| None=None, service: I18nService \| None=None, **kwargs: Any)` | Create a lazy plural translation string. |
| `parse_locale` | `aquilia/i18n/locale.py` | `def parse_locale(tag: str)` | Parse a BCP 47 language tag into a ``Locale`` object. |
| `normalize_locale` | `aquilia/i18n/locale.py` | `def normalize_locale(tag: str)` | Normalize a locale tag to canonical BCP 47 form. |
| `match_locale` | `aquilia/i18n/locale.py` | `def match_locale(requested: Locale, available: Sequence[Locale])` | Find the best matching locale from available options. |
| `parse_accept_language` | `aquilia/i18n/locale.py` | `def parse_accept_language(header: str)` | Parse an ``Accept-Language`` header into a list of (tag, quality) tuples. |
| `negotiate_locale` | `aquilia/i18n/locale.py` | `def negotiate_locale(accept_language: str, available_locales: Sequence[str], default: str='en')` | Negotiate the best locale from an Accept-Language header and available locales. |
| `build_resolver` | `aquilia/i18n/middleware.py` | `def build_resolver(config: Any)` | Build a ``ChainLocaleResolver`` from an ``I18nConfig``. |
| `get_plural_rule` | `aquilia/i18n/plural.py` | `def get_plural_rule(language: str)` | Get the plural rule function for a language. |
| `select_plural` | `aquilia/i18n/plural.py` | `def select_plural(language: str, count: Number)` | Select the plural category for a number in a given language. |
| `create_i18n_service` | `aquilia/i18n/service.py` | `def create_i18n_service(config: I18nConfig \| dict[str, Any] \| None=None, catalog: TranslationCatalog \| None=None)` | Factory function for creating an ``I18nService``. |
| `register_i18n_template_globals` | `aquilia/i18n/template_integration.py` | `def register_i18n_template_globals(env: Environment, service: I18nService)` | Register i18n globals and filters on a Jinja2 Environment. |

## Constants And Module Flags

| Name | Source | Value or Type |
| --- | --- | --- |
| `_HAS_CROUS` | `aquilia/i18n/catalog.py` | `False` |
| `_NUMBER_FORMATS` | `aquilia/i18n/formatter.py` | `dict[str, dict[str, str]]` |
| `_CURRENCY_SYMBOLS` | `aquilia/i18n/formatter.py` | `dict[str, str]` |
| `_ORDINAL_SUFFIXES_EN` | `aquilia/i18n/formatter.py` | `{1: 'st', 2: 'nd', 3: 'rd'}` |
| `_DATE_FORMATS` | `aquilia/i18n/formatter.py` | `dict[str, dict[str, str]]` |
| `_TIME_FORMATS` | `aquilia/i18n/formatter.py` | `dict[str, dict[str, str]]` |
| `_SIMPLE_ARG_PATTERN` | `aquilia/i18n/formatter.py` | `re.compile('\\{(\\w+)\\}')` |
| `_PLURAL_FORM_PATTERN` | `aquilia/i18n/formatter.py` | `re.compile('(=\\d+\|\\w+)\\s*\\{([^}]*)\\}')` |
| `LOCALE_PATTERN` | `aquilia/i18n/locale.py` | `re.compile('^(?P<language>[a-zA-Z]{2,3})(?:-(?P<script>[a-zA-Z]{4}))?(?:-(?P<region>[a-zA-Z]{2}\|\\d{3}))?(?:-(?P<variant>[a-zA-Z0-9]{5,8}))?$', re.IGNORECASE)` |
| `_ACCEPT_LANG_RE` | `aquilia/i18n/locale.py` | `re.compile('(?P<tag>[a-zA-Z]{1,8}(?:-[a-zA-Z0-9]{1,8})*\|\\*)(?:\\s*;\\s*q=(?P<q>[01](?:\\.\\d{1,3})?))?')` |
| `CLDR_PLURAL_RULES` | `aquilia/i18n/plural.py` | `dict[str, PluralRule]` |

## Detailed Classes And Methods

### `TranslationCatalog`

- Source: `aquilia/i18n/catalog.py`
- Bases: `ABC`
- Summary: Abstract base for translation catalogs.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `get` | `def get(self, key: str, locale: str, *, default: str \| None=None)` | Retrieve a translation string. |
| `get_plural` | `def get_plural(self, key: str, locale: str, category: str, *, default: str \| None=None)` | Retrieve a plural translation variant. |
| `has` | `def has(self, key: str, locale: str)` | Check if a key exists for a locale. |
| `locales` | `def locales(self)` | Return set of available locale tags. |
| `keys` | `def keys(self, locale: str)` | Return all keys for a locale. |

### `MemoryCatalog`

- Source: `aquilia/i18n/catalog.py`
- Bases: `TranslationCatalog`
- Summary: In-memory translation catalog backed by nested dicts.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `add` | `def add(self, locale: str, translations: dict)` | Add translations for a locale (merges with existing). |
| `get` | `def get(self, key: str, locale: str, *, default: str \| None=None)` |  |
| `get_plural` | `def get_plural(self, key: str, locale: str, category: str, *, default: str \| None=None)` |  |
| `has` | `def has(self, key: str, locale: str)` |  |
| `locales` | `def locales(self)` |  |
| `keys` | `def keys(self, locale: str)` |  |

### `FileCatalog`

- Source: `aquilia/i18n/catalog.py`
- Bases: `TranslationCatalog`
- Summary: File-based translation catalog loading from ``locales/`` directory.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `load` | `def load(self)` | Load all translation files from configured directories. |
| `reload` | `def reload(self)` | Reload changed files (hot-reload support). |
| `get` | `def get(self, key: str, locale: str, *, default: str \| None=None)` |  |
| `get_plural` | `def get_plural(self, key: str, locale: str, category: str, *, default: str \| None=None)` |  |
| `has` | `def has(self, key: str, locale: str)` |  |
| `locales` | `def locales(self)` |  |
| `keys` | `def keys(self, locale: str)` |  |

### `CrousCatalog`

- Source: `aquilia/i18n/catalog.py`
- Bases: `TranslationCatalog`
- Summary: CROUS artifact-backed translation catalog.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `load` | `def load(self)` | Load translations from CROUS and/or JSON files. |
| `reload` | `def reload(self)` | Reload changed files (hot-reload support). |
| `compile` | `def compile(self, directory: str \| Path \| None=None)` | Compile all JSON locale files to CROUS format. |
| `get` | `def get(self, key: str, locale: str, *, default: str \| None=None)` |  |
| `get_plural` | `def get_plural(self, key: str, locale: str, category: str, *, default: str \| None=None)` |  |
| `has` | `def has(self, key: str, locale: str)` |  |
| `locales` | `def locales(self)` |  |
| `keys` | `def keys(self, locale: str)` |  |

### `NamespacedCatalog`

- Source: `aquilia/i18n/catalog.py`
- Bases: `TranslationCatalog`
- Summary: Wraps a catalog with a fixed namespace prefix.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `get` | `def get(self, key: str, locale: str, *, default: str \| None=None)` |  |
| `get_plural` | `def get_plural(self, key: str, locale: str, category: str, *, default: str \| None=None)` |  |
| `has` | `def has(self, key: str, locale: str)` |  |
| `locales` | `def locales(self)` |  |
| `keys` | `def keys(self, locale: str)` |  |

### `MergedCatalog`

- Source: `aquilia/i18n/catalog.py`
- Bases: `TranslationCatalog`
- Summary: Layered catalog that queries multiple catalogs with fallback.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `add` | `def add(self, catalog: TranslationCatalog)` | Add a catalog to the beginning (highest priority). |
| `get` | `def get(self, key: str, locale: str, *, default: str \| None=None)` |  |
| `get_plural` | `def get_plural(self, key: str, locale: str, category: str, *, default: str \| None=None)` |  |
| `has` | `def has(self, key: str, locale: str)` |  |
| `locales` | `def locales(self)` |  |
| `keys` | `def keys(self, locale: str)` |  |

### `I18nFault`

- Source: `aquilia/i18n/faults.py`
- Bases: `Fault`
- Summary: Base fault for all i18n-related errors.

### `MissingTranslationFault`

- Source: `aquilia/i18n/faults.py`
- Bases: `I18nFault`
- Summary: Raised when a translation key cannot be found in any catalog.

### `InvalidLocaleFault`

- Source: `aquilia/i18n/faults.py`
- Bases: `I18nFault`
- Summary: Raised when a locale tag cannot be parsed as valid BCP 47.

### `CatalogLoadFault`

- Source: `aquilia/i18n/faults.py`
- Bases: `I18nFault`
- Summary: Raised when a translation catalog file cannot be loaded.

### `PluralRuleFault`

- Source: `aquilia/i18n/faults.py`
- Bases: `I18nFault`
- Summary: Raised when plural form selection fails.

### `MessageFormatter`

- Source: `aquilia/i18n/formatter.py`
- Bases: `object`
- Summary: ICU MessageFormat-inspired string formatter.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `format` | `def format(self, pattern: str, locale: str \| None=None, **kwargs: Any)` | Format a message pattern with the given arguments. |

### `LazyString`

- Source: `aquilia/i18n/lazy.py`
- Bases: `object`
- Summary: A string-like object that defers translation until stringification.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `upper` | `def upper(self)` |  |
| `lower` | `def lower(self)` |  |
| `strip` | `def strip(self, chars: str \| None=None)` |  |
| `split` | `def split(self, sep: str \| None=None, maxsplit: int=-1)` |  |
| `replace` | `def replace(self, old: str, new: str, count: int=-1)` |  |
| `startswith` | `def startswith(self, prefix: str, *args)` |  |
| `endswith` | `def endswith(self, suffix: str, *args)` |  |
| `encode` | `def encode(self, encoding: str='utf-8', errors: str='strict')` |  |
| `join` | `def join(self, iterable)` |  |
| `format` | `def format(self, *args, **kwargs)` |  |
| `format_map` | `def format_map(self, mapping)` |  |

### `LazyPluralString`

- Source: `aquilia/i18n/lazy.py`
- Bases: `LazyString`
- Summary: Lazy string with plural support.

### `Locale`

- Source: `aquilia/i18n/locale.py`
- Bases: `object`
- Summary: Immutable BCP 47 locale tag.
- Decorators: `dataclass(frozen=True, slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `language` | `str` | `` |
| `script` | `str \| None` | `None` |
| `region` | `str \| None` | `None` |
| `variant` | `str \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `tag` | `def tag(self)` | Full BCP 47 tag string. |
| `language_tag` | `def language_tag(self)` | Language-only tag (no script/region/variant). |
| `fallback_chain` | `def fallback_chain(self)` | Generate fallback chain from most specific to least. |
| `matches` | `def matches(self, other: Locale)` | Check if this locale matches another using prefix matching. |

### `LocaleResolver`

- Source: `aquilia/i18n/middleware.py`
- Bases: `ABC`
- Summary: Abstract locale resolver.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `resolve` | `def resolve(self, request: Any)` | Attempt to resolve locale from the request. |

### `HeaderLocaleResolver`

- Source: `aquilia/i18n/middleware.py`
- Bases: `LocaleResolver`
- Summary: Resolve locale from the ``Accept-Language`` HTTP header.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `resolve` | `def resolve(self, request: Any)` |  |

### `CookieLocaleResolver`

- Source: `aquilia/i18n/middleware.py`
- Bases: `LocaleResolver`
- Summary: Resolve locale from a cookie.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `resolve` | `def resolve(self, request: Any)` |  |

### `QueryLocaleResolver`

- Source: `aquilia/i18n/middleware.py`
- Bases: `LocaleResolver`
- Summary: Resolve locale from a query parameter.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `resolve` | `def resolve(self, request: Any)` |  |

### `PathLocaleResolver`

- Source: `aquilia/i18n/middleware.py`
- Bases: `LocaleResolver`
- Summary: Resolve locale from the URL path prefix.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `resolve` | `def resolve(self, request: Any)` |  |

### `SessionLocaleResolver`

- Source: `aquilia/i18n/middleware.py`
- Bases: `LocaleResolver`
- Summary: Resolve locale from the user's session.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `resolve` | `def resolve(self, request: Any)` |  |

### `ChainLocaleResolver`

- Source: `aquilia/i18n/middleware.py`
- Bases: `LocaleResolver`
- Summary: Composite resolver that tries multiple resolvers in order.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `resolve` | `def resolve(self, request: Any)` |  |

### `I18nMiddleware`

- Source: `aquilia/i18n/middleware.py`
- Bases: `object`
- Summary: Aquilia middleware that resolves locale and injects i18n into requests.

### `PluralCategory`

- Source: `aquilia/i18n/plural.py`
- Bases: `str, Enum`
- Summary: CLDR plural categories.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `ZERO` | `` | `'zero'` |
| `ONE` | `` | `'one'` |
| `TWO` | `` | `'two'` |
| `FEW` | `` | `'few'` |
| `MANY` | `` | `'many'` |
| `OTHER` | `` | `'other'` |

### `MissingKeyStrategy`

- Source: `aquilia/i18n/service.py`
- Bases: `str, Enum`
- Summary: What to do when a translation key is not found.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `RETURN_KEY` | `` | `'return_key'` |
| `RETURN_EMPTY` | `` | `'return_empty'` |
| `RETURN_DEFAULT` | `` | `'return_default'` |
| `RAISE` | `` | `'raise'` |
| `LOG_AND_KEY` | `` | `'log_and_key'` |

### `I18nConfig`

- Source: `aquilia/i18n/service.py`
- Bases: `object`
- Summary: Configuration for the i18n service.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `enabled` | `bool` | `True` |
| `default_locale` | `str` | `'en'` |
| `available_locales` | `list[str]` | `field(default_factory=lambda: ['en'])` |
| `fallback_locale` | `str` | `'en'` |
| `catalog_dirs` | `list[str]` | `field(default_factory=lambda: ['locales'])` |
| `catalog_format` | `str` | `'crous'` |
| `missing_key_strategy` | `str` | `'log_and_key'` |
| `auto_reload` | `bool` | `False` |
| `auto_detect` | `bool` | `True` |
| `cookie_name` | `str` | `'aq_locale'` |
| `query_param` | `str` | `'lang'` |
| `path_prefix` | `bool` | `False` |
| `resolver_order` | `list[str]` | `field(default_factory=lambda: ['query', 'cookie', 'header'])` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `from_dict` | `def from_dict(cls, data: dict[str, Any])` | Create config from a dictionary (e.g. from ConfigLoader). |
| `to_dict` | `def to_dict(self)` | Serialize to dict for ConfigLoader round-tripping. |

### `I18nService`

- Source: `aquilia/i18n/service.py`
- Bases: `object`
- Summary: Central i18n orchestrator.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `t` | `def t(self, key: str, *, locale: str \| None=None, default: str \| None=None, **kwargs: Any)` | Translate a key. |
| `tn` | `def tn(self, key: str, count: int \| float, *, locale: str \| None=None, default: str \| None=None, **kwargs: Any)` | Translate a key with plural selection. |
| `tp` | `def tp(self, key: str, *, locale: str \| None=None, default: str \| None=None, **kwargs: Any)` | Translate with explicit parameterized formatting. |
| `has` | `def has(self, key: str, locale: str \| None=None)` | Check if a key exists for the given locale. |
| `available_locales` | `def available_locales(self)` | Return the list of configured available locales. |
| `is_available` | `def is_available(self, locale: str)` | Check if a locale is in the available list. |
| `negotiate` | `def negotiate(self, accept_language: str)` | Negotiate locale from an Accept-Language header. |
| `locale` | `def locale(self, tag: str \| None=None)` | Get a ``Locale`` object for the given tag. |
| `reload_catalogs` | `def reload_catalogs(self)` | Force reload all file-based catalogs. |

### `I18nTemplateExtension`

- Source: `aquilia/i18n/template_integration.py`
- Bases: `object`
- Summary: Lightweight template extension descriptor for Aquilia's template engine.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `apply` | `def apply(self, env: Environment)` | Apply the i18n extension to the Jinja2 environment. |
