<!-- Legacy mirror. Canonical page: ../modules/i18n/configuration.md -->

# I18N Configuration

Internationalization service, locale negotiation, catalogs, formatting, plural rules, lazy strings, middleware, CLI helpers, and template integration.

This page distinguishes direct configuration APIs from indirect runtime wiring. All class names and source files below are extracted from the current source tree.

## Configuration Model

This module exposes config-oriented public classes. Use the table below to locate exact constructors and `to_dict()` behavior in `api-reference.md`.

## Source Inventory

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

## Detected Config-Oriented Classes

| Class | Source | Methods | Summary |
| --- | --- | --- | --- |
| `I18nMiddleware` | `aquilia/i18n/middleware.py` |  | Aquilia middleware that resolves locale and injects i18n into requests. |
| `I18nConfig` | `aquilia/i18n/service.py` | `from_dict`, `to_dict` | Configuration for the i18n service. |

## Runtime Wiring Paths

- `workspace.py` defines workspace-level structure with `Workspace`, `Module`, and `Integration` builders.
- `modules/<name>/manifest.py` defines module internals with `AppManifest`.
- `ConfigLoader.get(...)` resolves dotted configuration paths at runtime.
- `AquiliaServer` consumes resolved config during middleware and subsystem setup.
- Subsystems with optional providers only require optional dependencies when their backend/provider is configured.

## Verification Checklist

1. Run `aq validate` to verify manifests.
2. Run `aq inspect config` to inspect resolved configuration.
3. Run `aq doctor` for workspace and integration diagnostics.
4. For server-only wiring, start via `aq run` and check startup logs plus `GET /_health`.

## Related Pages

- `api-reference.md` for exact class fields, methods, constants, and signatures.
- `integration-guide.md` for the workspace/manifest wiring pattern.
- `edge-cases-and-limitations.md` for fallback and compatibility behavior.
