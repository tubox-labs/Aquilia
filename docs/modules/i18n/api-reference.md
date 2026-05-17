# Internationalization API Reference

This page is extracted from the current Python source. It includes public classes, methods, functions, constants, dataclass-like fields, decorators, and notable attributes.

## Public Class Summary

| Name | Source | Bases | Purpose |
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

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `has_crous` | `aquilia/i18n/catalog.py` | `def has_crous() -> bool` | Check if the CROUS binary format library is available. |
| `register_i18n_providers` | `aquilia/i18n/di_integration.py` | `def register_i18n_providers(container: Any, service: I18nService, config: I18nConfig &#124; None = None) -> None` | Register i18n providers in a DI container. |
| `register_i18n_request_providers` | `aquilia/i18n/di_integration.py` | `def register_i18n_request_providers(container: Any, locale: str, service: I18nService) -> None` | Register request-scoped i18n providers. |
| `format_message` | `aquilia/i18n/formatter.py` | `def format_message(pattern: str, locale: str = 'en', **kwargs: Any) -> str` | Convenience function for one-shot message formatting. |
| `format_number` | `aquilia/i18n/formatter.py` | `def format_number(value: Number, locale: str = 'en', *, decimals: int &#124; None = None) -> str` | Format a number with locale-specific separators. |
| `format_decimal` | `aquilia/i18n/formatter.py` | `def format_decimal(value: Number, locale: str = 'en', decimals: int = 2) -> str` | Format a decimal number with fixed precision. |
| `format_percent` | `aquilia/i18n/formatter.py` | `def format_percent(value: Number, locale: str = 'en', decimals: int = 0) -> str` | Format a fraction as a percentage. |
| `format_currency` | `aquilia/i18n/formatter.py` | `def format_currency(value: Number, currency: str = 'USD', locale: str = 'en', *, decimals: int = 2) -> str` | Format a monetary value with currency symbol. |
| `format_ordinal` | `aquilia/i18n/formatter.py` | `def format_ordinal(value: int, locale: str = 'en') -> str` | Format an ordinal number. |
| `format_date` | `aquilia/i18n/formatter.py` | `def format_date(value: date, locale: str = 'en', *, style: str = 'medium') -> str` | Format a date with locale-specific patterns. |
| `format_time` | `aquilia/i18n/formatter.py` | `def format_time(value: time &#124; datetime, locale: str = 'en', *, style: str = 'short') -> str` | Format a time with locale-specific patterns. |
| `format_datetime` | `aquilia/i18n/formatter.py` | `def format_datetime(value: datetime, locale: str = 'en', *, date_style: str = 'medium', time_style: str = 'short', separator: str = ' ') -> str` | Format a datetime with locale-specific patterns. |
| `set_lazy_context` | `aquilia/i18n/lazy.py` | `def set_lazy_context(service: I18nService, locale: str &#124; None = None) -> None` | Set the global i18n context for lazy string resolution. |
| `clear_lazy_context` | `aquilia/i18n/lazy.py` | `def clear_lazy_context() -> None` | Clear the lazy context (called at request cleanup). |
| `lazy_t` | `aquilia/i18n/lazy.py` | `def lazy_t(key: str, *, default: str &#124; None = None, locale: str &#124; None = None, service: I18nService &#124; None = None, **kwargs: Any) -> LazyString` | Create a lazy translation string. |
| `lazy_tn` | `aquilia/i18n/lazy.py` | `def lazy_tn(key: str, count: int &#124; float, *, default: str &#124; None = None, locale: str &#124; None = None, service: I18nService &#124; None = None, **kwargs: Any) -> LazyPluralString` | Create a lazy plural translation string. |
| `parse_locale` | `aquilia/i18n/locale.py` | `def parse_locale(tag: str) -> Locale` | Parse a BCP 47 language tag into a ``Locale`` object. |
| `normalize_locale` | `aquilia/i18n/locale.py` | `def normalize_locale(tag: str) -> str &#124; None` | Normalize a locale tag to canonical BCP 47 form. |
| `match_locale` | `aquilia/i18n/locale.py` | `def match_locale(requested: Locale, available: Sequence[Locale]) -> Locale &#124; None` | Find the best matching locale from available options. |
| `parse_accept_language` | `aquilia/i18n/locale.py` | `def parse_accept_language(header: str) -> list[tuple[str, float]]` | Parse an ``Accept-Language`` header into a list of (tag, quality) tuples. |
| `negotiate_locale` | `aquilia/i18n/locale.py` | `def negotiate_locale(accept_language: str, available_locales: Sequence[str], default: str = 'en') -> str` | Negotiate the best locale from an Accept-Language header and available locales. |
| `build_resolver` | `aquilia/i18n/middleware.py` | `def build_resolver(config: Any) -> ChainLocaleResolver` | Build a ``ChainLocaleResolver`` from an ``I18nConfig``. |
| `get_plural_rule` | `aquilia/i18n/plural.py` | `def get_plural_rule(language: str) -> PluralRule` | Get the plural rule function for a language. |
| `select_plural` | `aquilia/i18n/plural.py` | `def select_plural(language: str, count: Number) -> str` | Select the plural category for a number in a given language. |
| `create_i18n_service` | `aquilia/i18n/service.py` | `def create_i18n_service(config: I18nConfig &#124; dict[str, Any] &#124; None = None, catalog: TranslationCatalog &#124; None = None) -> I18nService` | Factory function for creating an ``I18nService``. |
| `register_i18n_template_globals` | `aquilia/i18n/template_integration.py` | `def register_i18n_template_globals(env: Environment, service: I18nService) -> None` | Register i18n globals and filters on a Jinja2 Environment. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `_HAS_CROUS` | `aquilia/i18n/catalog.py` | `False` |
| `_NUMBER_FORMATS` | `aquilia/i18n/formatter.py` | `dict[str, dict[str, str]]` |
| `_CURRENCY_SYMBOLS` | `aquilia/i18n/formatter.py` | `dict[str, str]` |
| `_ORDINAL_SUFFIXES_EN` | `aquilia/i18n/formatter.py` | `{1: 'st', 2: 'nd', 3: 'rd'}` |
| `_DATE_FORMATS` | `aquilia/i18n/formatter.py` | `dict[str, dict[str, str]]` |
| `_TIME_FORMATS` | `aquilia/i18n/formatter.py` | `dict[str, dict[str, str]]` |
| `_SIMPLE_ARG_PATTERN` | `aquilia/i18n/formatter.py` | `re.compile('\\{(\\w+)\\}')` |
| `_PLURAL_FORM_PATTERN` | `aquilia/i18n/formatter.py` | `re.compile('(=\\d+ &#124; \\w+)\\s*\\{([^}]*)\\}')` |
| `LOCALE_PATTERN` | `aquilia/i18n/locale.py` | `re.compile('^(?P<language>[a-zA-Z]{2,3})(?:-(?P<script>[a-zA-Z]{4}))?(?:-(?P<region>[a-zA-Z]{2} &#124; \\d{3}))?(?:-(?P<variant>[a-zA-Z0-9]{5,8}))?$', re.IGNORECASE)` |
| `_ACCEPT_LANG_RE` | `aquilia/i18n/locale.py` | `re.compile('(?P<tag>[a-zA-Z]{1,8}(?:-[a-zA-Z0-9]{1,8})* &#124; \\*)(?:\\s*;\\s*q=(?P<q>[01](?:\\.\\d{1,3})?))?')` |
| `CLDR_PLURAL_RULES` | `aquilia/i18n/plural.py` | `dict[str, PluralRule]` |

## Detailed Classes And Methods

### Class: `TranslationCatalog`

- Source: `aquilia/i18n/catalog.py`
- Bases: `ABC`
- Summary: Abstract base for translation catalogs.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get` | `def get(self, key: str, locale: str, *, default: str &#124; None = None) -> str &#124; None` | abstractmethod | Retrieve a translation string. |
| `get_plural` | `def get_plural(self, key: str, locale: str, category: str, *, default: str &#124; None = None) -> str &#124; None` | abstractmethod | Retrieve a plural translation variant. |
| `has` | `def has(self, key: str, locale: str) -> bool` | abstractmethod | Check if a key exists for a locale. |
| `locales` | `def locales(self) -> set[str]` | abstractmethod | Return set of available locale tags. |
| `keys` | `def keys(self, locale: str) -> set[str]` | abstractmethod | Return all keys for a locale. |

### Class: `MemoryCatalog`

- Source: `aquilia/i18n/catalog.py`
- Bases: `TranslationCatalog`
- Summary: In-memory translation catalog backed by nested dicts.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `add` | `def add(self, locale: str, translations: dict) -> None` |  | Add translations for a locale (merges with existing). |
| `get` | `def get(self, key: str, locale: str, *, default: str &#124; None = None) -> str &#124; None` |  | Method. |
| `get_plural` | `def get_plural(self, key: str, locale: str, category: str, *, default: str &#124; None = None) -> str &#124; None` |  | Method. |
| `has` | `def has(self, key: str, locale: str) -> bool` |  | Method. |
| `locales` | `def locales(self) -> set[str]` |  | Method. |
| `keys` | `def keys(self, locale: str) -> set[str]` |  | Method. |

### Class: `FileCatalog`

- Source: `aquilia/i18n/catalog.py`
- Bases: `TranslationCatalog`
- Summary: File-based translation catalog loading from ``locales/`` directory.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `load` | `def load(self) -> None` |  | Load all translation files from configured directories. |
| `reload` | `def reload(self) -> None` |  | Reload changed files (hot-reload support). |
| `get` | `def get(self, key: str, locale: str, *, default: str &#124; None = None) -> str &#124; None` |  | Method. |
| `get_plural` | `def get_plural(self, key: str, locale: str, category: str, *, default: str &#124; None = None) -> str &#124; None` |  | Method. |
| `has` | `def has(self, key: str, locale: str) -> bool` |  | Method. |
| `locales` | `def locales(self) -> set[str]` |  | Method. |
| `keys` | `def keys(self, locale: str) -> set[str]` |  | Method. |

### Class: `CrousCatalog`

- Source: `aquilia/i18n/catalog.py`
- Bases: `TranslationCatalog`
- Summary: CROUS artifact-backed translation catalog.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `load` | `def load(self) -> None` |  | Load translations from CROUS and/or JSON files. |
| `reload` | `def reload(self) -> None` |  | Reload changed files (hot-reload support). |
| `compile` | `def compile(self, directory: str &#124; Path &#124; None = None) -> int` |  | Compile all JSON locale files to CROUS format. |
| `get` | `def get(self, key: str, locale: str, *, default: str &#124; None = None) -> str &#124; None` |  | Method. |
| `get_plural` | `def get_plural(self, key: str, locale: str, category: str, *, default: str &#124; None = None) -> str &#124; None` |  | Method. |
| `has` | `def has(self, key: str, locale: str) -> bool` |  | Method. |
| `locales` | `def locales(self) -> set[str]` |  | Method. |
| `keys` | `def keys(self, locale: str) -> set[str]` |  | Method. |

### Class: `NamespacedCatalog`

- Source: `aquilia/i18n/catalog.py`
- Bases: `TranslationCatalog`
- Summary: Wraps a catalog with a fixed namespace prefix.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get` | `def get(self, key: str, locale: str, *, default: str &#124; None = None) -> str &#124; None` |  | Method. |
| `get_plural` | `def get_plural(self, key: str, locale: str, category: str, *, default: str &#124; None = None) -> str &#124; None` |  | Method. |
| `has` | `def has(self, key: str, locale: str) -> bool` |  | Method. |
| `locales` | `def locales(self) -> set[str]` |  | Method. |
| `keys` | `def keys(self, locale: str) -> set[str]` |  | Method. |

### Class: `MergedCatalog`

- Source: `aquilia/i18n/catalog.py`
- Bases: `TranslationCatalog`
- Summary: Layered catalog that queries multiple catalogs with fallback.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `add` | `def add(self, catalog: TranslationCatalog) -> None` |  | Add a catalog to the beginning (highest priority). |
| `get` | `def get(self, key: str, locale: str, *, default: str &#124; None = None) -> str &#124; None` |  | Method. |
| `get_plural` | `def get_plural(self, key: str, locale: str, category: str, *, default: str &#124; None = None) -> str &#124; None` |  | Method. |
| `has` | `def has(self, key: str, locale: str) -> bool` |  | Method. |
| `locales` | `def locales(self) -> set[str]` |  | Method. |
| `keys` | `def keys(self, locale: str) -> set[str]` |  | Method. |

### Class: `I18nFault`

- Source: `aquilia/i18n/faults.py`
- Bases: `Fault`
- Summary: Base fault for all i18n-related errors.

### Class: `MissingTranslationFault`

- Source: `aquilia/i18n/faults.py`
- Bases: `I18nFault`
- Summary: Raised when a translation key cannot be found in any catalog.

### Class: `InvalidLocaleFault`

- Source: `aquilia/i18n/faults.py`
- Bases: `I18nFault`
- Summary: Raised when a locale tag cannot be parsed as valid BCP 47.

### Class: `CatalogLoadFault`

- Source: `aquilia/i18n/faults.py`
- Bases: `I18nFault`
- Summary: Raised when a translation catalog file cannot be loaded.

### Class: `PluralRuleFault`

- Source: `aquilia/i18n/faults.py`
- Bases: `I18nFault`
- Summary: Raised when plural form selection fails.

### Class: `MessageFormatter`

- Source: `aquilia/i18n/formatter.py`
- Bases: `object`
- Summary: ICU MessageFormat-inspired string formatter.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `format` | `def format(self, pattern: str, locale: str &#124; None = None, **kwargs: Any) -> str` |  | Format a message pattern with the given arguments. |

### Class: `LazyString`

- Source: `aquilia/i18n/lazy.py`
- Bases: `object`
- Summary: A string-like object that defers translation until stringification.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `upper` | `def upper(self) -> str` |  | Method. |
| `lower` | `def lower(self) -> str` |  | Method. |
| `strip` | `def strip(self, chars: str &#124; None = None) -> str` |  | Method. |
| `split` | `def split(self, sep: str &#124; None = None, maxsplit: int = -1) -> list[str]` |  | Method. |
| `replace` | `def replace(self, old: str, new: str, count: int = -1) -> str` |  | Method. |
| `startswith` | `def startswith(self, prefix: str, *args) -> bool` |  | Method. |
| `endswith` | `def endswith(self, suffix: str, *args) -> bool` |  | Method. |
| `encode` | `def encode(self, encoding: str = 'utf-8', errors: str = 'strict') -> bytes` |  | Method. |
| `join` | `def join(self, iterable) -> str` |  | Method. |
| `format` | `def format(self, *args, **kwargs) -> str` |  | Method. |
| `format_map` | `def format_map(self, mapping) -> str` |  | Method. |

### Class: `LazyPluralString`

- Source: `aquilia/i18n/lazy.py`
- Bases: `LazyString`
- Summary: Lazy string with plural support.

### Class: `Locale`

- Source: `aquilia/i18n/locale.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Immutable BCP 47 locale tag.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `language` | `str` |  |
| `script` | `str &#124; None` | `None` |
| `region` | `str &#124; None` | `None` |
| `variant` | `str &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `tag` | `def tag(self) -> str` | property | Full BCP 47 tag string. |
| `language_tag` | `def language_tag(self) -> str` | property | Language-only tag (no script/region/variant). |
| `fallback_chain` | `def fallback_chain(self) -> list[Locale]` | property | Generate fallback chain from most specific to least. |
| `matches` | `def matches(self, other: Locale) -> bool` |  | Check if this locale matches another using prefix matching. |

### Class: `LocaleResolver`

- Source: `aquilia/i18n/middleware.py`
- Bases: `ABC`
- Summary: Abstract locale resolver.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `resolve` | `def resolve(self, request: Any) -> str &#124; None` | abstractmethod | Attempt to resolve locale from the request. |

### Class: `HeaderLocaleResolver`

- Source: `aquilia/i18n/middleware.py`
- Bases: `LocaleResolver`
- Summary: Resolve locale from the ``Accept-Language`` HTTP header.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `resolve` | `def resolve(self, request: Any) -> str &#124; None` |  | Method. |

### Class: `CookieLocaleResolver`

- Source: `aquilia/i18n/middleware.py`
- Bases: `LocaleResolver`
- Summary: Resolve locale from a cookie.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `resolve` | `def resolve(self, request: Any) -> str &#124; None` |  | Method. |

### Class: `QueryLocaleResolver`

- Source: `aquilia/i18n/middleware.py`
- Bases: `LocaleResolver`
- Summary: Resolve locale from a query parameter.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `resolve` | `def resolve(self, request: Any) -> str &#124; None` |  | Method. |

### Class: `PathLocaleResolver`

- Source: `aquilia/i18n/middleware.py`
- Bases: `LocaleResolver`
- Summary: Resolve locale from the URL path prefix.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `resolve` | `def resolve(self, request: Any) -> str &#124; None` |  | Method. |

### Class: `SessionLocaleResolver`

- Source: `aquilia/i18n/middleware.py`
- Bases: `LocaleResolver`
- Summary: Resolve locale from the user's session.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `resolve` | `def resolve(self, request: Any) -> str &#124; None` |  | Method. |

### Class: `ChainLocaleResolver`

- Source: `aquilia/i18n/middleware.py`
- Bases: `LocaleResolver`
- Summary: Composite resolver that tries multiple resolvers in order.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `resolve` | `def resolve(self, request: Any) -> str &#124; None` |  | Method. |

### Class: `I18nMiddleware`

- Source: `aquilia/i18n/middleware.py`
- Bases: `object`
- Summary: Aquilia middleware that resolves locale and injects i18n into requests.

### Class: `PluralCategory`

- Source: `aquilia/i18n/plural.py`
- Bases: `str, Enum`
- Summary: CLDR plural categories.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `ZERO` |  | `'zero'` |
| `ONE` |  | `'one'` |
| `TWO` |  | `'two'` |
| `FEW` |  | `'few'` |
| `MANY` |  | `'many'` |
| `OTHER` |  | `'other'` |

### Class: `MissingKeyStrategy`

- Source: `aquilia/i18n/service.py`
- Bases: `str, Enum`
- Summary: What to do when a translation key is not found.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `RETURN_KEY` |  | `'return_key'` |
| `RETURN_EMPTY` |  | `'return_empty'` |
| `RETURN_DEFAULT` |  | `'return_default'` |
| `RAISE` |  | `'raise'` |
| `LOG_AND_KEY` |  | `'log_and_key'` |

### Class: `I18nConfig`

- Source: `aquilia/i18n/service.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Configuration for the i18n service.

Attributes and fields:

| Name | Type | Default |
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

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `from_dict` | `def from_dict(cls, data: dict[str, Any]) -> I18nConfig` | classmethod | Create config from a dictionary (e.g. from ConfigLoader). |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialize to dict for ConfigLoader round-tripping. |

### Class: `I18nService`

- Source: `aquilia/i18n/service.py`
- Bases: `object`
- Summary: Central i18n orchestrator.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `t` | `def t(self, key: str, *, locale: str &#124; None = None, default: str &#124; None = None, **kwargs: Any) -> str` |  | Translate a key. |
| `tn` | `def tn(self, key: str, count: int &#124; float, *, locale: str &#124; None = None, default: str &#124; None = None, **kwargs: Any) -> str` |  | Translate a key with plural selection. |
| `tp` | `def tp(self, key: str, *, locale: str &#124; None = None, default: str &#124; None = None, **kwargs: Any) -> str` |  | Translate with explicit parameterized formatting. |
| `has` | `def has(self, key: str, locale: str &#124; None = None) -> bool` |  | Check if a key exists for the given locale. |
| `available_locales` | `def available_locales(self) -> list[str]` |  | Return the list of configured available locales. |
| `is_available` | `def is_available(self, locale: str) -> bool` |  | Check if a locale is in the available list. |
| `negotiate` | `def negotiate(self, accept_language: str) -> str` |  | Negotiate locale from an Accept-Language header. |
| `locale` | `def locale(self, tag: str &#124; None = None) -> Locale` |  | Get a ``Locale`` object for the given tag. |
| `reload_catalogs` | `def reload_catalogs(self) -> None` |  | Force reload all file-based catalogs. |

### Class: `I18nTemplateExtension`

- Source: `aquilia/i18n/template_integration.py`
- Bases: `object`
- Summary: Lightweight template extension descriptor for Aquilia's template engine.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `apply` | `def apply(self, env: Environment) -> None` |  | Apply the i18n extension to the Jinja2 environment. |

## Functions

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `has_crous` | `aquilia/i18n/catalog.py` | `def has_crous() -> bool` | Check if the CROUS binary format library is available. |
| `register_i18n_providers` | `aquilia/i18n/di_integration.py` | `def register_i18n_providers(container: Any, service: I18nService, config: I18nConfig &#124; None = None) -> None` | Register i18n providers in a DI container. |
| `register_i18n_request_providers` | `aquilia/i18n/di_integration.py` | `def register_i18n_request_providers(container: Any, locale: str, service: I18nService) -> None` | Register request-scoped i18n providers. |
| `format_message` | `aquilia/i18n/formatter.py` | `def format_message(pattern: str, locale: str = 'en', **kwargs: Any) -> str` | Convenience function for one-shot message formatting. |
| `format_number` | `aquilia/i18n/formatter.py` | `def format_number(value: Number, locale: str = 'en', *, decimals: int &#124; None = None) -> str` | Format a number with locale-specific separators. |
| `format_decimal` | `aquilia/i18n/formatter.py` | `def format_decimal(value: Number, locale: str = 'en', decimals: int = 2) -> str` | Format a decimal number with fixed precision. |
| `format_percent` | `aquilia/i18n/formatter.py` | `def format_percent(value: Number, locale: str = 'en', decimals: int = 0) -> str` | Format a fraction as a percentage. |
| `format_currency` | `aquilia/i18n/formatter.py` | `def format_currency(value: Number, currency: str = 'USD', locale: str = 'en', *, decimals: int = 2) -> str` | Format a monetary value with currency symbol. |
| `format_ordinal` | `aquilia/i18n/formatter.py` | `def format_ordinal(value: int, locale: str = 'en') -> str` | Format an ordinal number. |
| `format_date` | `aquilia/i18n/formatter.py` | `def format_date(value: date, locale: str = 'en', *, style: str = 'medium') -> str` | Format a date with locale-specific patterns. |
| `format_time` | `aquilia/i18n/formatter.py` | `def format_time(value: time &#124; datetime, locale: str = 'en', *, style: str = 'short') -> str` | Format a time with locale-specific patterns. |
| `format_datetime` | `aquilia/i18n/formatter.py` | `def format_datetime(value: datetime, locale: str = 'en', *, date_style: str = 'medium', time_style: str = 'short', separator: str = ' ') -> str` | Format a datetime with locale-specific patterns. |
| `set_lazy_context` | `aquilia/i18n/lazy.py` | `def set_lazy_context(service: I18nService, locale: str &#124; None = None) -> None` | Set the global i18n context for lazy string resolution. |
| `clear_lazy_context` | `aquilia/i18n/lazy.py` | `def clear_lazy_context() -> None` | Clear the lazy context (called at request cleanup). |
| `lazy_t` | `aquilia/i18n/lazy.py` | `def lazy_t(key: str, *, default: str &#124; None = None, locale: str &#124; None = None, service: I18nService &#124; None = None, **kwargs: Any) -> LazyString` | Create a lazy translation string. |
| `lazy_tn` | `aquilia/i18n/lazy.py` | `def lazy_tn(key: str, count: int &#124; float, *, default: str &#124; None = None, locale: str &#124; None = None, service: I18nService &#124; None = None, **kwargs: Any) -> LazyPluralString` | Create a lazy plural translation string. |
| `parse_locale` | `aquilia/i18n/locale.py` | `def parse_locale(tag: str) -> Locale` | Parse a BCP 47 language tag into a ``Locale`` object. |
| `normalize_locale` | `aquilia/i18n/locale.py` | `def normalize_locale(tag: str) -> str &#124; None` | Normalize a locale tag to canonical BCP 47 form. |
| `match_locale` | `aquilia/i18n/locale.py` | `def match_locale(requested: Locale, available: Sequence[Locale]) -> Locale &#124; None` | Find the best matching locale from available options. |
| `parse_accept_language` | `aquilia/i18n/locale.py` | `def parse_accept_language(header: str) -> list[tuple[str, float]]` | Parse an ``Accept-Language`` header into a list of (tag, quality) tuples. |
| `negotiate_locale` | `aquilia/i18n/locale.py` | `def negotiate_locale(accept_language: str, available_locales: Sequence[str], default: str = 'en') -> str` | Negotiate the best locale from an Accept-Language header and available locales. |
| `build_resolver` | `aquilia/i18n/middleware.py` | `def build_resolver(config: Any) -> ChainLocaleResolver` | Build a ``ChainLocaleResolver`` from an ``I18nConfig``. |
| `get_plural_rule` | `aquilia/i18n/plural.py` | `def get_plural_rule(language: str) -> PluralRule` | Get the plural rule function for a language. |
| `select_plural` | `aquilia/i18n/plural.py` | `def select_plural(language: str, count: Number) -> str` | Select the plural category for a number in a given language. |
| `create_i18n_service` | `aquilia/i18n/service.py` | `def create_i18n_service(config: I18nConfig &#124; dict[str, Any] &#124; None = None, catalog: TranslationCatalog &#124; None = None) -> I18nService` | Factory function for creating an ``I18nService``. |
| `register_i18n_template_globals` | `aquilia/i18n/template_integration.py` | `def register_i18n_template_globals(env: Environment, service: I18nService) -> None` | Register i18n globals and filters on a Jinja2 Environment. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `_HAS_CROUS` | `aquilia/i18n/catalog.py` | `False` |
| `_NUMBER_FORMATS` | `aquilia/i18n/formatter.py` | `dict[str, dict[str, str]]` |
| `_CURRENCY_SYMBOLS` | `aquilia/i18n/formatter.py` | `dict[str, str]` |
| `_ORDINAL_SUFFIXES_EN` | `aquilia/i18n/formatter.py` | `{1: 'st', 2: 'nd', 3: 'rd'}` |
| `_DATE_FORMATS` | `aquilia/i18n/formatter.py` | `dict[str, dict[str, str]]` |
| `_TIME_FORMATS` | `aquilia/i18n/formatter.py` | `dict[str, dict[str, str]]` |
| `_SIMPLE_ARG_PATTERN` | `aquilia/i18n/formatter.py` | `re.compile('\\{(\\w+)\\}')` |
| `_PLURAL_FORM_PATTERN` | `aquilia/i18n/formatter.py` | `re.compile('(=\\d+ &#124; \\w+)\\s*\\{([^}]*)\\}')` |
| `LOCALE_PATTERN` | `aquilia/i18n/locale.py` | `re.compile('^(?P<language>[a-zA-Z]{2,3})(?:-(?P<script>[a-zA-Z]{4}))?(?:-(?P<region>[a-zA-Z]{2} &#124; \\d{3}))?(?:-(?P<variant>[a-zA-Z0-9]{5,8}))?$', re.IGNORECASE)` |
| `_ACCEPT_LANG_RE` | `aquilia/i18n/locale.py` | `re.compile('(?P<tag>[a-zA-Z]{1,8}(?:-[a-zA-Z0-9]{1,8})* &#124; \\*)(?:\\s*;\\s*q=(?P<q>[01](?:\\.\\d{1,3})?))?')` |
| `CLDR_PLURAL_RULES` | `aquilia/i18n/plural.py` | `dict[str, PluralRule]` |
