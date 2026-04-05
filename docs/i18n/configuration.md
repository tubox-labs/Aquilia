# I18n Configuration

## Configuration Entry Points

I18n configuration can enter the system from four primary places:

1. `Integration.i18n(...)` in `aquilia/config_builders.py`
2. `Workspace.i18n(...)` shorthand in `aquilia/config_builders.py`
3. Typed integration object `I18nIntegration` in `aquilia/integrations/i18n.py`
4. Runtime merge defaults from `ConfigLoader.get_i18n_config()` in `aquilia/config.py`

Typed integration option:

- `I18nIntegration` dataclass in `aquilia/integrations/i18n.py` mirrors builder fields and serializes with `to_dict()`.

At server boot, effective config is converted with `I18nConfig.from_dict(...)`.

## Precedence and Runtime Merge

Effective behavior at runtime follows this path:

1. User config under `i18n` or `integrations.i18n`
2. Merged with `ConfigLoader.get_i18n_config()` defaults
3. Converted by `I18nConfig.from_dict`
4. Used by `create_i18n_service`

If i18n is not explicitly enabled, server setup skips subsystem wiring.

## Effective Keys

| Key | Type | Purpose |
|---|---|---|
| `enabled` | `bool` | Enables subsystem boot in server setup |
| `default_locale` | `str` | Default locale tag |
| `available_locales` | `list[str]` | Allowed locale set for middleware/service checks |
| `fallback_locale` | `str` | Global fallback locale when lookup misses |
| `catalog_dirs` | `list[str]` | Locale directory roots |
| `catalog_format` | `str` | Backend preference (`crous`, `json`, `yaml` metadata) |
| `missing_key_strategy` | `str` | Missing-key handling policy |
| `auto_reload` | `bool` | Intended hot-reload behavior metadata |
| `auto_detect` | `bool` | Intended auto-detect behavior metadata |
| `cookie_name` | `str` | Locale cookie key |
| `query_param` | `str` | Locale query parameter |
| `path_prefix` | `bool` | Path-prefix mode intent (`/en/...`) |
| `resolver_order` | `list[str]` | Ordered resolver chain names |

## Default Value Matrix

Defaults are not fully uniform across all entry points.

| Key | `ConfigLoader.get_i18n_config()` | `Integration.i18n(...)` | `I18nIntegration` | `I18nConfig` dataclass | `I18nConfig.from_dict` fallback |
|---|---|---|---|---|---|
| `enabled` | `False` | `True` | `True` | `True` | `True` |
| `catalog_format` | `crous` | `json` | `json` | `crous` | `json` |
| `resolver_order` | `query,cookie,header` | `query,cookie,header` | `query,cookie,header` | `query,cookie,header` | `query,cookie,header` |

Practical implication:

- Server runtime usually uses ConfigLoader defaults (`enabled=False`, `catalog_format=crous`) unless user config overrides.
- Constructing `I18nConfig` manually without `ConfigLoader` can produce different behavior.

## Missing Key Strategies

Supported strategy names:

- `return_key`
- `return_empty`
- `return_default`
- `raise`
- `log_and_key`

Behavior notes:

- Passing `default=...` to `t` or `tn` bypasses strategy and returns provided default.
- `raise` emits `MissingTranslationFault`.
- `return_default` returns `default or key`; with no explicit default this behaves like `return_key`.

## Resolver Order and Names

Accepted resolver names in `build_resolver`:

- `header`
- `cookie`
- `query`
- `path`
- `session`

Unknown names are ignored with a warning log.

## Recommended Production Config

```python
.integrate(
    Integration.i18n(
        enabled=True,
        default_locale="en",
        available_locales=["en", "fr", "de", "ja"],
        fallback_locale="en",
        catalog_dirs=["locales", "modules/auth/locales"],
        catalog_format="crous",
        missing_key_strategy="log_and_key",
        resolver_order=["query", "cookie", "session", "header"],
        cookie_name="aq_locale",
        query_param="lang",
        auto_reload=False,
    )
)
```

## Operational Notes

- `path_prefix` and `auto_detect` are currently configuration metadata fields; resolver behavior is controlled directly by `resolver_order`.
- In service boot wiring, any non-`crous` `catalog_format` currently creates a `FileCatalog` with default extensions (`.json` only). YAML files are not loaded by default through `I18nService._build_catalog`.
- `CrousCatalog` scans `.crous`, `.json`, `.yaml`, and `.yml`, and can auto-compile JSON to CROUS when `crous` is installed.
