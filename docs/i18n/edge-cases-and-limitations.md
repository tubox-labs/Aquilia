<!-- Legacy mirror. Canonical page: ../modules/i18n/edge-cases-and-limitations.md -->

# I18N Edge Cases And Limitations

Internationalization service, locale negotiation, catalogs, formatting, plural rules, lazy strings, middleware, CLI helpers, and template integration.

## Source-Backed Limits

- No module-specific edge branch was detected beyond optional imports, validation, and dependency availability.

## Fault And Error Classes Detected

`I18nFault`, `MissingTranslationFault`, `InvalidLocaleFault`, `CatalogLoadFault`, `PluralRuleFault`

## Operational Boundaries

- Optional external libraries are only required when the corresponding provider/backend/runtime is configured.
- Deprecated APIs generally warn when retained for migration rather than disappearing silently.
- Server startup intentionally degrades non-critical optional subsystems where source catches and logs exceptions.
- Use `api-reference.md` to check exact constructor defaults and method signatures before depending on behavior.

## Verification

- `aq doctor` for workspace/integration issues.
- `aq validate` for manifest issues.
- `aq inspect config` for merged configuration.
- `GET /_health` for live subsystem status once the app is running.
