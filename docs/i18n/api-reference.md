# I18n API Reference

This reference documents the current i18n symbols in Aquilia, including public exports and notable internal helpers.

## Module: `aquilia/i18n/locale.py`

### Constants

- `LOCALE_PATTERN: re.Pattern`
- `_ACCEPT_LANG_RE: re.Pattern` (internal)

### Class: `Locale`

Signature:

```python
@dataclass(frozen=True, slots=True)
class Locale:
    language: str
    script: str | None = None
    region: str | None = None
    variant: str | None = None
```

Methods and properties:

- `__post_init__(self) -> None`: normalizes casing
- `tag(self) -> str`: full normalized BCP 47 tag
- `language_tag(self) -> str`: language-only tag
- `fallback_chain(self) -> list[Locale]`: specificity fallback chain
- `matches(self, other: Locale) -> bool`: prefix-compatible matching
- `__str__(self) -> str`
- `__repr__(self) -> str`

### Functions

- `parse_locale(tag: str) -> Locale`
  - Raises `ConfigInvalidFault` for invalid inputs.
- `normalize_locale(tag: str) -> str | None`
  - Returns `None` for unparseable tags.
- `match_locale(requested: Locale, available: Sequence[Locale]) -> Locale | None`
- `parse_accept_language(header: str) -> list[tuple[str, float]]`
  - Parses quality values and clamps to `[0, 1]`.
- `negotiate_locale(accept_language: str, available_locales: Sequence[str], default: str = "en") -> str`

## Module: `aquilia/i18n/plural.py`

### Types

- `Number = int | float`
- `PluralRule = Callable[[Number], str]`

### Enum

- `PluralCategory(str, Enum)`
  - `ZERO`, `ONE`, `TWO`, `FEW`, `MANY`, `OTHER`

### Public functions

- `get_plural_rule(language: str) -> PluralRule`
- `select_plural(language: str, count: Number) -> str`

### Public data

- `CLDR_PLURAL_RULES: dict[str, PluralRule]`

### Internal helpers and rules

- `_operands(n: Number) -> tuple`
- `_plural_english`, `_plural_french`, `_plural_no_plural`, `_plural_arabic`
- `_plural_russian`, `_plural_polish`, `_plural_czech`, `_plural_romanian`
- `_plural_german`, `_plural_latvian`, `_plural_lithuanian`
- `_plural_welsh`, `_plural_irish`, `_plural_slovenian`
- `_plural_maltese`, `_plural_hebrew`

## Module: `aquilia/i18n/catalog.py`

### Abstract base: `TranslationCatalog`

Required methods:

- `get(key: str, locale: str, *, default: str | None = None) -> str | None`
- `get_plural(key: str, locale: str, category: str, *, default: str | None = None) -> str | None`
- `has(key: str, locale: str) -> bool`
- `locales() -> set[str]`
- `keys(locale: str) -> set[str]`

### Class: `MemoryCatalog(TranslationCatalog)`

Constructor:

- `__init__(translations: dict[str, dict] | None = None)`

Methods:

- `add(locale: str, translations: dict) -> None`
- `_resolve_key(data: dict, key: str) -> Any` (internal)
- `get(...) -> str | None`
- `get_plural(...) -> str | None`
- `has(...) -> bool`
- `locales() -> set[str]`
- `keys(locale: str) -> set[str]`
- `_collect_keys(data: dict, prefix: str, result: set[str]) -> None` (internal)
- `_deep_merge(base: dict, overlay: dict) -> None` (internal staticmethod)

Behavior notes:

- Non-string values are stringified.
- Plural dicts return category-specific value or `other` fallback.

### Class: `FileCatalog(TranslationCatalog)`

Constructor:

```python
def __init__(
    directories: Sequence[str | Path],
    file_extensions: Sequence[str] = (".json",),
    watch: bool = False,
)
```

Methods:

- `load() -> None`
- `reload() -> None`
- `_scan_directory(root: Path, check_mtime: bool = False) -> None` (internal)
- `_load_file(path: Path) -> dict | None` (internal)
- `_ensure_loaded() -> None` (internal)
- `get(...) -> str | None`
- `get_plural(...) -> str | None`
- `has(...) -> bool`
- `locales() -> set[str]`
- `keys(locale: str) -> set[str]`

### Function: `has_crous() -> bool`

Returns whether optional `crous` package is importable.

### Class: `CrousCatalog(TranslationCatalog)`

Constructor:

```python
def __init__(
    directories: Sequence[str | Path],
    artifact_dir: str | Path | None = None,
    auto_compile: bool = True,
    watch: bool = False,
)
```

Methods:

- `load() -> None`
- `reload() -> None`
- `compile(directory: str | Path | None = None) -> int`
- `_scan_directory(root: Path, check_mtime: bool = False) -> None` (internal)
- `_load_crous_file(path: Path) -> dict | None` (internal staticmethod)
- `_load_json_file(path: Path) -> dict | None` (internal staticmethod)
- `_load_yaml_file(path: Path) -> dict | None` (internal staticmethod)
- `_write_crous_file(path: Path, locale: str, namespace: str, data: dict) -> None` (internal staticmethod)
- `_ensure_loaded() -> None` (internal)
- `get(...) -> str | None`
- `get_plural(...) -> str | None`
- `has(...) -> bool`
- `locales() -> set[str]`
- `keys(locale: str) -> set[str]`

Behavior notes:

- Prefers `.crous` when available and package installed.
- Can auto-compile newer JSON sources back to CROUS.
- Supports JSON and YAML fallback scans.

### Class: `NamespacedCatalog(TranslationCatalog)`

Constructor:

- `__init__(inner: TranslationCatalog, namespace: str)`

Methods:

- `_prefix(key: str) -> str` (internal)
- `get(...) -> str | None`
- `get_plural(...) -> str | None`
- `has(...) -> bool`
- `locales() -> set[str]`
- `keys(locale: str) -> set[str]`

### Class: `MergedCatalog(TranslationCatalog)`

Constructor:

- `__init__(catalogs: Sequence[TranslationCatalog])`

Methods:

- `add(catalog: TranslationCatalog) -> None`
- `get(...) -> str | None`
- `get_plural(...) -> str | None`
- `has(...) -> bool`
- `locales() -> set[str]`
- `keys(locale: str) -> set[str]`

## Module: `aquilia/i18n/formatter.py`

### Data constants

- `_NUMBER_FORMATS`
- `_CURRENCY_SYMBOLS`
- `_ORDINAL_SUFFIXES_EN`
- `_DATE_FORMATS`
- `_TIME_FORMATS`
- `_SIMPLE_ARG_PATTERN`
- `_PLURAL_FORM_PATTERN`

### Types

- `Number = int | float | Decimal`

### Functions

- `_find_icu_args(pattern: str)` (internal generator)
- `format_message(pattern: str, locale: str = "en", **kwargs: Any) -> str`
- `_get_number_format(locale: str) -> dict[str, str]` (internal)
- `format_number(value: Number, locale: str = "en", *, decimals: int | None = None) -> str`
- `format_decimal(value: Number, locale: str = "en", decimals: int = 2) -> str`
- `format_percent(value: Number, locale: str = "en", decimals: int = 0) -> str`
- `format_currency(value: Number, currency: str = "USD", locale: str = "en", *, decimals: int = 2) -> str`
- `format_ordinal(value: int, locale: str = "en") -> str`
- `format_date(value: date, locale: str = "en", *, style: str = "medium") -> str`
- `format_time(value: time | datetime, locale: str = "en", *, style: str = "short") -> str`
- `format_datetime(value: datetime, locale: str = "en", *, date_style: str = "medium", time_style: str = "short", separator: str = " ") -> str`

### Class: `MessageFormatter`

Constructor:

- `__init__(locale: str = "en")`

Methods:

- `format(pattern: str, locale: str | None = None, **kwargs: Any) -> str`
- `_format_plural(count: Number, style: str, locale: str) -> str` (internal)
- `_format_select(value: Any, style: str) -> str` (internal)

## Module: `aquilia/i18n/service.py`

### Enum: `MissingKeyStrategy`

Values:

- `RETURN_KEY`
- `RETURN_EMPTY`
- `RETURN_DEFAULT`
- `RAISE`
- `LOG_AND_KEY`

### Dataclass: `I18nConfig`

Fields:

- `enabled: bool = True`
- `default_locale: str = "en"`
- `available_locales: list[str] = ["en"]`
- `fallback_locale: str = "en"`
- `catalog_dirs: list[str] = ["locales"]`
- `catalog_format: str = "crous"`
- `missing_key_strategy: str = "log_and_key"`
- `auto_reload: bool = False`
- `auto_detect: bool = True`
- `cookie_name: str = "aq_locale"`
- `query_param: str = "lang"`
- `path_prefix: bool = False`
- `resolver_order: list[str] = ["query", "cookie", "header"]`

Methods:

- `from_dict(data: dict[str, Any]) -> I18nConfig`
- `to_dict() -> dict[str, Any]`

### Class: `I18nService`

Constructor:

- `__init__(config: I18nConfig, catalog: TranslationCatalog | None = None)`

Public methods:

- `t(key: str, *, locale: str | None = None, default: str | None = None, **kwargs: Any) -> str`
- `tn(key: str, count: int | float, *, locale: str | None = None, default: str | None = None, **kwargs: Any) -> str`
- `tp(key: str, *, locale: str | None = None, default: str | None = None, **kwargs: Any) -> str`
- `has(key: str, locale: str | None = None) -> bool`
- `available_locales() -> list[str]`
- `is_available(locale: str) -> bool`
- `negotiate(accept_language: str) -> str`
- `locale(tag: str | None = None) -> Locale`
- `reload_catalogs() -> None`

Internal methods:

- `_resolve(key: str, locale: str, *, default: str | None = None) -> str`
- `_handle_missing(key: str, locale: str, default: str | None = None) -> str`
- `_build_catalog() -> TranslationCatalog`

### Factory

- `create_i18n_service(config: I18nConfig | dict[str, Any] | None = None, catalog: TranslationCatalog | None = None) -> I18nService`

## Module: `aquilia/i18n/lazy.py`

### Module globals

- `_service_ref: I18nService | None`
- `_locale_ref: str | None`

### Context functions

- `set_lazy_context(service: I18nService, locale: str | None = None) -> None`
- `clear_lazy_context() -> None`

### Class: `LazyString`

Constructor:

```python
def __init__(
    key: str,
    *,
    default: str | None = None,
    locale: str | None = None,
    service: I18nService | None = None,
    **kwargs: Any,
)
```

Internal resolver:

- `_resolve() -> str`

Implemented protocol methods include:

- `__str__`, `__repr__`, `__len__`, `__contains__`, `__iter__`, `__getitem__`
- comparison and hashing operators
- `__add__`, `__radd__`, `__mod__`, `__format__`, `__bool__`
- delegated string methods: `upper`, `lower`, `strip`, `split`, `replace`, `startswith`, `endswith`, `encode`, `join`, `format`, `format_map`

### Class: `LazyPluralString(LazyString)`

Constructor:

- `__init__(key: str, count: int | float, *, default: str | None = None, locale: str | None = None, service: I18nService | None = None, **kwargs: Any)`

Methods:

- `_resolve() -> str`
- `__repr__() -> str`

### Factory functions

- `lazy_t(key: str, *, default: str | None = None, locale: str | None = None, service: I18nService | None = None, **kwargs: Any) -> LazyString`
- `lazy_tn(key: str, count: int | float, *, default: str | None = None, locale: str | None = None, service: I18nService | None = None, **kwargs: Any) -> LazyPluralString`

## Module: `aquilia/i18n/middleware.py`

### Abstract class: `LocaleResolver`

- `resolve(request: Any) -> str | None`

### Concrete resolvers

- `HeaderLocaleResolver(available_locales: Sequence[str], default_locale: str = "en")`
- `CookieLocaleResolver(cookie_name: str = "aq_locale", available_locales: Sequence[str] | None = None)`
- `QueryLocaleResolver(param_name: str = "lang", available_locales: Sequence[str] | None = None)`
- `PathLocaleResolver(available_locales: Sequence[str] | None = None)`
- `SessionLocaleResolver(session_key: str = "locale", available_locales: Sequence[str] | None = None)`
- `ChainLocaleResolver(resolvers: Sequence[LocaleResolver])`

All resolvers implement:

- `resolve(request: Any) -> str | None`

### Middleware class

- `I18nMiddleware(service: I18nService, resolver: LocaleResolver | None = None)`
- `__call__(request: Any, ctx: Any, next_handler: Callable) -> Any`

### Factory and request helpers

- `build_resolver(config: Any) -> ChainLocaleResolver`
- `_get_header(request: Any, name: str) -> str | None`
- `_get_cookies(request: Any) -> dict[str, str]`
- `_get_query_params(request: Any) -> dict[str, str]`
- `_get_path(request: Any) -> str`
- `_get_state(request: Any) -> dict[str, Any]`

## Module: `aquilia/i18n/template_integration.py`

### Registration function

- `register_i18n_template_globals(env: Environment, service: I18nService) -> None`

Registers globals:

- `_`, `_n`, `_p`, `gettext`, `ngettext`, `i18n_service`
- formatting globals (`format_number`, `format_currency`, `format_date`, `format_time`, `format_datetime`, `format_percent`, `format_ordinal`)

Registers filters:

- `translate`, `t`, `format_number`, `format_currency`, `format_date`, `format_time`, `format_percent`

### Class: `I18nTemplateExtension`

- `__init__(service: I18nService)`
- `apply(env: Environment) -> None`
- `__repr__() -> str`

### Internal helper

- `_get_ctx_locale(env: Environment) -> str`

## Module: `aquilia/i18n/di_integration.py`

### Functions

- `register_i18n_providers(container: Any, service: I18nService, config: I18nConfig | None = None) -> None`
  - Registers app-scoped `I18nService` and `I18nConfig` across supported container APIs.
- `register_i18n_request_providers(container: Any, locale: str, service: I18nService) -> None`
  - Registers request-scoped `Locale` and locale string values.

## Module: `aquilia/i18n/faults.py`

### Fault domain setup

- `FaultDomain.I18N = FaultDomain("i18n", "Internationalization and localization faults")`

### Classes

- `I18nFault(Fault)`
- `MissingTranslationFault(I18nFault)`
- `InvalidLocaleFault(I18nFault)`
- `CatalogLoadFault(I18nFault)`
- `PluralRuleFault(I18nFault)`

## Module: `aquilia/i18n/__init__.py`

Public re-exports include:

- Locale APIs
- Catalog APIs
- Plural APIs and data
- Formatter APIs
- Service APIs
- Lazy APIs
- Middleware APIs
- Fault APIs
- Template and DI integration APIs

`__all__` is explicitly defined and validated by tests.

## Module: `aquilia/integrations/i18n.py`

### Dataclass: `I18nIntegration`

Typed integration config used by builder-style workspace declarations.

Fields mirror the primary i18n configuration shape and serialize via:

- `to_dict() -> dict[str, Any]`

## Exception and Side-Effect Map

This map highlights behavior that materially affects caller expectations.

| Symbol | Exceptions/Faults | Side effects |
|---|---|---|
| `parse_locale` | raises `ConfigInvalidFault` on invalid input | none |
| `normalize_locale` | suppresses parse errors and returns `None` | none |
| `negotiate_locale` | may propagate parser faults for malformed tags that are not caught by current `ValueError` branch | none |
| `I18nService.t` | can raise `MissingTranslationFault` when missing strategy is `raise` | none |
| `I18nService.tn` | same as `t` on unresolved keys under raise strategy | injects `count` into formatter kwargs |
| `I18nService.reload_catalogs` | none expected in normal path | replaces active catalog instance |
| `FileCatalog.load/reload` | fail-soft (logs load errors) | mutates in-memory cache and file mtime registry |
| `CrousCatalog.load/reload/compile` | fail-soft logging for per-file failures; returns compile count | mutates cache, may write `.crous` artifacts |
| `register_i18n_providers` | catches errors and logs; typically non-throwing | mutates DI container registrations |
| `register_i18n_request_providers` | catches errors silently in current implementation | mutates request DI container |
| `I18nMiddleware.__call__` | resolver errors are swallowed; downstream handler errors propagate | writes request state keys and sets/clears lazy global context |
| `set_lazy_context` / `clear_lazy_context` | none | mutates module-level globals used by lazy strings |

## Usage Notes for Internal APIs

- Internal helpers prefixed with `_` are not stable API contracts.
- `register_i18n_request_providers` is designed for custom request DI plumbing and is not invoked by default server wiring.
- `CrousCatalog._write_crous_file` performs atomic replacement via temporary file.
