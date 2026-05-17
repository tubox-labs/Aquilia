# Internationalization Configuration

## Configuration Entry Points

The implementation exposes the following configuration-like classes, policies, integrations, or dataclasses.

| Type | Source | Fields | Purpose |
| --- | --- | --- | --- |
| `Locale` | `aquilia/i18n/locale.py` | language: str, script: str &#124; None, region: str &#124; None, variant: str &#124; None | Immutable BCP 47 locale tag. |
| `I18nConfig` | `aquilia/i18n/service.py` | enabled: bool, default_locale: str, available_locales: list[str], fallback_locale: str, catalog_dirs: list[str], catalog_format: str, missing_key_strategy: str, auto_reload: bool, auto_detect: bool, cookie_name: str, query_param: str, path_prefix: bool, ... | Configuration for the i18n service. |

## Common Entry Points

- `I18nIntegration`
- `I18nConfig`

## Precedence Model

Aquilia generally resolves configuration in this order:

1. Explicit constructor arguments or typed integration dataclass values.
2. `Workspace` builder methods and `Workspace.integrate(...)` output.
3. `ConfigLoader` defaults and environment overlays.
4. Runtime defaults inside the subsystem service or provider constructor.

When this module is registered through an `AppManifest`, keep component declarations inside `modules/<name>/manifest.py` and keep cross-cutting integration settings in `workspace.py`.

## Datatype Guidance

- Prefer typed dataclasses, policy objects, and config objects listed above when they exist.
- Keep secret values in environment-backed config, not literal strings in committed workspace files.
- Keep runtime-only state in services, stores, providers, or request state rather than static configuration.
- Use `to_dict()` on integration dataclasses when you need to inspect exactly what enters `ConfigLoader`.
