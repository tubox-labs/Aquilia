# I18n Examples

## 1) Basic Workspace Integration

```python
from aquilia.config_builders import Workspace, Integration

workspace = (
    Workspace("myapp")
    .integrate(
        Integration.i18n(
            enabled=True,
            default_locale="en",
            available_locales=["en", "fr", "de", "ja"],
            fallback_locale="en",
            catalog_dirs=["locales"],
            catalog_format="crous",
            resolver_order=["query", "cookie", "header"],
        )
    )
)
```

## 2) Locale File Layout

```text
locales/
  en/
    messages.json
    errors.json
  fr/
    messages.json
    errors.json
```

`locales/en/messages.json`:

```json
{
  "welcome": "Welcome, {name}!",
  "items": {
    "one": "{count} item",
    "other": "{count} items"
  }
}
```

## 3) Controller Translation

```python
from aquilia import Controller, GET, RequestCtx

class DemoController(Controller):
    prefix = "/demo"

    @GET("/welcome")
    async def welcome(self, ctx: RequestCtx):
        i18n = ctx.request.state["i18n"]
        locale = ctx.request.state.get("locale", "en")

        return {
            "message": i18n.t("messages.welcome", locale=locale, name="World"),
            "count": i18n.tn("messages.items", 3, locale=locale),
        }
```

## 4) Template Translation and Formatting

```jinja2
<h1>{{ _("messages.welcome", name=user_name) }}</h1>
<p>{{ _n("messages.items", count=items_count) }}</p>
<p>{{ total | format_currency("USD") }}</p>
<p>{{ created_at | format_date }}</p>
```

## 5) Query and Cookie Locale Overrides

```python
Integration.i18n(
    enabled=True,
    available_locales=["en", "fr"],
    query_param="lang",
    cookie_name="aq_locale",
    resolver_order=["query", "cookie", "header"],
)
```

Behavior:

- `?lang=fr` wins first
- then cookie `aq_locale=...`
- then `Accept-Language`

## 6) Session Locale Resolver

```python
Integration.i18n(
    enabled=True,
    available_locales=["en", "fr"],
    resolver_order=["session", "query", "cookie", "header"],
)
```

Expected session shape:

```python
request.state["session"] = {"locale": "fr"}
```

## 7) Programmatic Service Construction

```python
from aquilia.i18n.catalog import MemoryCatalog
from aquilia.i18n.service import I18nConfig, I18nService

catalog = MemoryCatalog(
    {
        "en": {"messages": {"welcome": "Welcome"}},
        "fr": {"messages": {"welcome": "Bienvenue"}},
    }
)

svc = I18nService(
    I18nConfig(default_locale="en", available_locales=["en", "fr"]),
    catalog=catalog,
)

assert svc.t("messages.welcome", locale="fr") == "Bienvenue"
```

## 8) Namespaced Module Catalog

```python
from aquilia.i18n.catalog import FileCatalog, NamespacedCatalog

base = FileCatalog(["locales"])
auth_i18n = NamespacedCatalog(base, "auth")

msg = auth_i18n.get("errors.invalid_credentials", "en")
# resolves to key: auth.errors.invalid_credentials
```

## 9) Lazy Translation for Module Constants

```python
from aquilia.i18n.lazy import lazy_t

TITLE = lazy_t("messages.title", default="Title")
```

At render/usage time:

```python
text = str(TITLE)
```

Note:

- lazy translation context is set by i18n middleware and currently stored globally; see `edge-cases-and-limitations.md`.

## 10) CLI Bootstrap and Extraction

```bash
aq i18n init --locales en,fr --format json
aq i18n extract --source-dirs modules,templates --output locales/en/messages.json
aq i18n coverage --verbose
```

## 11) Manual Template Locale Override

If your template rendering path does not set `request_locale` automatically:

```python
env.globals["request_locale"] = request.state.get("locale", "en")
```

This ensures `_`, `_n`, filters, and formatting helpers resolve with request locale rather than service default.
