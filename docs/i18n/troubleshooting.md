<!-- Legacy mirror. Canonical page: ../modules/i18n/troubleshooting.md -->

# I18N Troubleshooting

Internationalization service, locale negotiation, catalogs, formatting, plural rules, lazy strings, middleware, CLI helpers, and template integration.

## Fast Diagnosis Flow

1. Confirm the command is run from a directory containing `workspace.py` unless it is help/version/init/doctor.
2. Run `aq doctor` for workspace, environment, registry, integration, and deployment checks.
3. Run `aq validate` to catch manifest errors.
4. Run `aq inspect config` to inspect resolved settings.
5. Run `aq inspect modules` and `aq inspect routes` when discovery or routing is suspect.
6. Check `api-reference.md` for exact public API signatures.

## Module-Relevant Commands

- `aq i18n init`
- `aq i18n check`
- `aq i18n inspect`
- `aq i18n extract`
- `aq i18n coverage`
- `aq i18n compile`

## Symptoms And Actions

| Symptom | Likely Source | Action |
| --- | --- | --- |
| Import error during startup | Bad manifest class path or optional provider dependency | Check `modules/<name>/manifest.py`, install the relevant extra, and rerun `aq validate`. |
| Route not found | Controller omitted from manifest, wrong route prefix, or startup conflict | Run `aq inspect routes`; inspect controller decorators and `Module.route_prefix()`. |
| Dependency not found | Service not registered or constructor annotation cannot be resolved | Check `AppManifest.services`, DI provider registrations, and `aq inspect di`. |
| Config value missing | Dotenv/env overlay not loaded or wrong nested key | Check `ConfigLoader` precedence and `AQ_` double-underscore key names. |
| Production security failure | Insecure secret or required key not configured | Set `AQ_SECRET_KEY`, `SECRET_KEY`, or Python-native secret config. |
| Optional subsystem unavailable | Provider/backend dependency or startup connection failed | Check startup logs; optional subsystems often log non-fatal failures. |

## Source Files To Inspect

| File | Lines | Public classes | Public functions | Purpose |
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
