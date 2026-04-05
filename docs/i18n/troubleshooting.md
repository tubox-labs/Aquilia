# I18n Troubleshooting

## Symptom: Translations always return keys

Possible causes:

- i18n integration not enabled
- catalog directory missing
- key path mismatch (`messages.welcome` vs `welcome`)

Checks:

```bash
aq i18n inspect
aq i18n check
```

Code checks:

- verify `request.state["i18n"]` exists in handlers
- verify `ctx.request.state.get("locale")` has expected locale

## Symptom: Wrong locale selected

Possible causes:

- unexpected resolver order
- locale value not in `available_locales`
- header resolver selected default before later resolvers

Fixes:

- set explicit `resolver_order`
- validate locale tags are normalized and allowed
- move `header` later in resolver chain when overrides should win

## Symptom: Template helpers use default locale instead of request locale

Possible causes:

- `request_locale` not set in template environment globals for render path

Fix:

- set `env.globals["request_locale"]` from request state before rendering
- or pass `locale=` explicitly in helper calls

## Symptom: YAML locale files ignored

Possible causes:

- service built `FileCatalog` with default `.json` extension filter

Fix options:

- use JSON files in standard server path
- or build custom catalog explicitly if YAML-only workflow is required

## Symptom: Locale DI injection unavailable in request scope

Cause:

- request-scoped i18n provider helper is not auto-wired

Fix:

- call `register_i18n_request_providers(...)` in request integration layer

## Symptom: Intermittent locale mix-up under concurrency when using lazy strings

Cause:

- custom flow sets lazy context without guaranteed cleanup

Mitigation:

- ensure `set_lazy_context(...)` and `clear_lazy_context()` are paired in `try/finally`
- prefer standard `I18nMiddleware` flow, which already enforces cleanup

## Symptom: Unexpected exception while negotiating malformed Accept-Language

Cause:

- `negotiate_locale` catches `ValueError`, but parser currently raises `ConfigInvalidFault`

Mitigation:

- sanitize/validate headers at gateway or middleware boundary
- add defensive exception handling around negotiation in custom paths
