# I18n Content App

## Purpose

Demonstrates localized application copy, `Accept-Language` negotiation, fallback behavior, and plural-aware translations.

## Architecture

- `workspace.py` configures workspace-level i18n.
- `ContentLocalizationService` composes `I18nService`, `I18nConfig`, and `MemoryCatalog`.
- The controller reads headers and query parameters and delegates translation work to the service.

## Setup

```bash
python -m pip install -e ".[dev]"
python -m pytest examples/i18n_content_app -q
```

## Run

```bash
cd examples/i18n_content_app
python -m uvicorn runtime:app --reload --port 8065
```

## Expected Behavior

`GET /content/landing?name=Ana&count=3` with `Accept-Language: es` returns Spanish copy and pluralized item text.

## Common Pitfalls

- Catalog keys are dotted paths into nested dictionaries.
- Missing-key behavior is controlled by `I18nConfig.missing_key_strategy`.

## Extension Ideas

Move catalogs to `locales/`, add template integration, CLI extraction, and compiled catalog checks.

## Related APIs

`I18nService`, `I18nConfig`, `MemoryCatalog`, `negotiate_locale`, `Integration.i18n`.
