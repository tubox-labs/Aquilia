# Aquilia I18n Documentation

This directory is the canonical documentation set for Aquilia internationalization (i18n) and localization (l10n).

It is implementation-driven and aligned with the current code in:

- `aquilia/i18n/`
- `aquilia/integrations/i18n.py`
- `aquilia/config.py`
- `aquilia/config_builders.py`
- `aquilia/server.py`
- `aquilia/cli/commands/i18n.py`
- `aquilia/cli/__main__.py`

## What This Covers

- Locale parsing, normalization, and Accept-Language negotiation
- CLDR-style plural category selection
- Translation catalog backends (`MemoryCatalog`, `FileCatalog`, `CrousCatalog`)
- Message formatting (ICU-like placeholders plus number/currency/date helpers)
- `I18nService` lookup and fallback behavior
- Lazy translation objects (`LazyString`, `LazyPluralString`)
- Locale resolver chain and request middleware integration
- Template globals and filters
- DI registration for app scope and request scope
- CLI tooling (`aq i18n`) and command-level behavior
- Edge cases, known limitations, and operational caveats

## Document Map

- `architecture.md`: Runtime architecture, lookup pipeline, and subsystem boundaries
- `configuration.md`: Full configuration surface and precedence
- `api-reference.md`: Public and internal symbol reference by module
- `integration-guide.md`: Server, DI, middleware, template, and controller integration
- `cli-reference.md`: `aq i18n` commands and operational behavior
- `edge-cases-and-limitations.md`: Proven edge cases and current gaps
- `troubleshooting.md`: Common failures, diagnostics, and mitigations
- `examples.md`: End-to-end usage patterns

## Fast Start

1) Enable i18n in workspace configuration:

```python
from aquilia.config_builders import Workspace, Integration

workspace = (
    Workspace("myapp")
    .integrate(
        Integration.i18n(
            enabled=True,
            default_locale="en",
            available_locales=["en", "fr", "de"],
            catalog_dirs=["locales"],
            catalog_format="crous",  # or "json"
            resolver_order=["query", "cookie", "header"],
        )
    )
)
```

2) Create locale files:

```bash
aq i18n init --locales en,fr,de --directory locales --format json
```

3) Translate in handlers:

```python
msg = ctx.request.state["i18n"].t("messages.welcome", locale=ctx.request.state.get("locale", "en"))
```

4) Translate in templates:

```jinja2
{{ _("messages.welcome") }}
{{ _n("messages.items", count=items_count) }}
{{ amount | format_currency("USD") }}
```

## Runtime Surfaces Added Per Request

When i18n is enabled and middleware runs, request state includes:

- `request.state["locale"]`: resolved locale tag string
- `request.state["locale_obj"]`: parsed `Locale` object
- `request.state["i18n"]`: `I18nService` instance

See `integration-guide.md` and `edge-cases-and-limitations.md` for important caveats about template locale propagation and lazy-string concurrency behavior.
