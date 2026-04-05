# I18n Integration Guide

## Server-Level Integration

The default server integration path is automatic when config enables i18n.

`AquiliaServer._setup_i18n` performs:

1. Load merged config (`ConfigLoader.get_i18n_config`).
2. Build typed config (`I18nConfig.from_dict`).
3. Create service (`create_i18n_service`).
4. Register app DI providers (`register_i18n_providers`).
5. Build resolver chain (`build_resolver`).
6. Attach middleware (`I18nMiddleware`) at priority 24.
7. Register template globals if template engine exists.

If `enabled` is false, no i18n service or middleware is installed.

## Middleware Ordering

Current i18n middleware insertion priority is 24.

Design intent from server comments:

- after session/auth stages
- before template-layer rendering helpers

Practical result:

- locale and i18n state are available to downstream handlers and template rendering paths that run later in the chain.

## Request State Contract

After i18n middleware executes, request state includes:

- `locale: str`
- `locale_obj: Locale`
- `i18n: I18nService`

Controller usage pattern:

```python
@GET("/welcome")
async def welcome(self, ctx: RequestCtx):
    i18n = ctx.request.state["i18n"]
    locale = ctx.request.state.get("locale", "en")
    return {"message": i18n.t("messages.welcome", locale=locale)}
```

## DI Integration

### App-scoped providers

`register_i18n_providers` attempts these container APIs in order:

- `register_value`
- `register`
- `set`
- plain dictionary assignment

Injected keys/tokens:

- `I18nService`
- `I18nConfig`

### Request-scoped locale providers

`register_i18n_request_providers` can inject request locale tokens:

- `Locale` object
- string token `"locale"`

Important: this helper is currently not called automatically by middleware/server. Call it manually if your request DI container relies on per-request locale injection.

## Template Integration

`register_i18n_template_globals(env, service)` adds:

Globals:

- `_`, `_n`, `_p`
- `gettext`, `ngettext`
- `i18n_service`
- formatting helpers

Filters:

- `translate`/`t`
- `format_number`, `format_currency`, `format_date`, `format_time`, `format_percent`

Additional helper outside i18n module:

- `aquilia/templates/context.py::inject_i18n(context, gettext_func=None)`
    Injects `_` and `gettext` into template context.
    If no gettext function is provided, it falls back to identity lambda.

Template usage:

```jinja2
{{ _("messages.welcome") }}
{{ _n("messages.items", count=items_count) }}
{{ "messages.greeting" | translate(name=user_name) }}
{{ amount | format_currency("USD") }}
```

## Session and Auth Interplay

I18n does not perform authentication. Locale resolution can optionally read session data via `SessionLocaleResolver`.

To enable session-based locale:

- include `"session"` in `resolver_order`
- ensure session middleware populates `request.state["session"]`
- store locale under configured `session_key` (default `"locale"`)

## Manual Integration (Non-Default Server Boot)

If constructing middleware stack manually:

```python
from aquilia.i18n.service import I18nConfig, create_i18n_service
from aquilia.i18n.middleware import I18nMiddleware, build_resolver
from aquilia.i18n.di_integration import register_i18n_providers
from aquilia.i18n.template_integration import register_i18n_template_globals

cfg = I18nConfig(
    default_locale="en",
    available_locales=["en", "fr"],
    catalog_dirs=["locales"],
)

svc = create_i18n_service(cfg)
register_i18n_providers(app_container, svc, cfg)
resolver = build_resolver(cfg)

middleware_stack.add(I18nMiddleware(svc, resolver), scope="global", priority=24, name="i18n")
register_i18n_template_globals(template_env, svc)
```

## Integration Validation Checklist

- `ConfigLoader.get_i18n_config()["enabled"]` is true
- expected locale files exist under each `catalog_dirs` root
- middleware stack contains `I18nMiddleware`
- request state contains `locale` and `i18n` in downstream handlers
- template env exposes `_` and `translate`
- `I18nService` resolves from DI container
