# Templates Portal App

## Purpose

Demonstrates server-rendered HTML using Aquilia's async template engine, sandboxed loader, globals, filters, and streaming.

## Architecture

- `workspace.py` configures the template integration with memory caching and sandboxing.
- `PortalRenderService` owns `TemplateEngine` and `TemplateLoader`.
- `manifest.py` declares a module-level `TemplateConfig`.

## Setup

```bash
python -m pip install -e ".[dev]"
python -m pytest examples/templates_portal_app -q
```

## Run

```bash
cd examples/templates_portal_app
python -m uvicorn runtime:app --reload --port 8068
```

## Expected Behavior

`GET /portal/dashboard` renders HTML with account data, custom globals, and a currency filter.

## Common Pitfalls

- Use `TemplateLoader` search paths rooted at the example workspace.
- Keep sandboxing enabled for user-controlled templates.

## Extension Ideas

Add auth/session template globals, static asset tags, module-namespaced templates, and bytecode cache inspection.

## Related APIs

`TemplateEngine`, `TemplateLoader`, `TemplateConfig`, `Integration.templates`.
