# I18n Edge Cases and Limitations

This page records implementation-verified behavior from code and tests.

## Proven Edge Cases (Validated by Tests)

- Deep dotted keys resolve correctly (`a.b.c.d`).
- Numeric translation values are returned as strings.
- Empty-string translations are valid and are not treated as missing.
- Unicode strings are preserved across memory and CROUS-backed catalogs.
- `MemoryCatalog.keys()` returns plural parent keys (for example `items`) rather than `items.one` or `items.other`.
- `parse_accept_language` clamps quality values into `[0.0, 1.0]`.
- Russian plural boundaries handle `11-14` as `many` and `21` as `one`.
- English ordinals correctly handle teens (`11th`, `12th`, `13th`).
- Lazy translation context is task-local through `contextvars` and does not bleed across concurrent tasks.

## Current Limitations and Behavior Gaps

### 1) Template locale source expects `request_locale` global

`_get_ctx_locale` in `template_integration.py` reads `env.globals["request_locale"]` first, then falls back to service default locale.

Current gap:

- no repository-wide automatic setter for `request_locale` was found in i18n server wiring

Impact:

- template translation helpers may default to service default locale unless locale is explicitly passed or a custom integration sets `request_locale`

### 2) Request DI locale registration helper is not auto-wired

`register_i18n_request_providers(...)` exists but is not called by server or middleware integration paths.

Impact:

- request-scoped DI injection of `Locale`/`"locale"` is not available unless added manually

### 3) Config flags present but not actively consumed in runtime logic

The following fields exist in config surfaces but are not used directly in middleware/service decision paths:

- `auto_detect`
- `path_prefix`
- `auto_reload`

Actual resolver behavior is controlled by `resolver_order` and chosen resolver set.

### 4) Header resolver comment and behavior diverge

`HeaderLocaleResolver.resolve()` comment says default result should not be returned to allow overrides, but implementation returns any non-empty negotiated result (including default locale).

Impact:

- if header resolver is early in `resolver_order`, it can short-circuit later resolvers even when negotiation only produced default

### 5) YAML loading in service boot path is not automatic for non-CROUS format

`I18nService._build_catalog()` builds `FileCatalog([path])` for non-`crous` formats.

`FileCatalog` default extensions are `(".json",)`.

Impact:

- YAML files are not loaded by default through service boot unless custom catalog construction is used

### 6) Fault usage is not fully uniform

i18n fault classes exist (`InvalidLocaleFault`, etc.), but some parsing failures currently raise `ConfigInvalidFault` from generic config domain.

Impact:

- error handling may need to account for both i18n-specific and config-domain fault types

### 7) `negotiate_locale` exception handling is narrow

`negotiate_locale` catches `ValueError` when parsing candidate tags, while `parse_locale` currently raises `ConfigInvalidFault` for invalid tags.

Impact:

- malformed accepted tags that pass regex but fail locale parsing may propagate faults unexpectedly

### 8) Default values differ across config entry points

Default values for keys like `enabled` and `catalog_format` are not identical in all layers (`ConfigLoader`, `Integration.i18n`, `I18nConfig`, `I18nIntegration`).

Impact:

- behavior can differ between manual object construction and full server boot path

## Risk Mitigations You Can Apply Today

- Keep `resolver_order` explicit in production config.
- Pass locale explicitly in template helper calls when strict correctness is required.
- Use request-state locale (`request.state["locale"]`) in controllers as the primary source.
- In custom middleware flows, ensure `clear_lazy_context()` is always called in `finally` blocks after `set_lazy_context()`.
- Prefer startup-time catalog validation and a smoke test that reads representative keys for each locale.
