# Debug Module

> `aquilia.debug` — Development debug pages and error rendering

The Debug module provides development-mode debug pages, including exception tracebacks, HTTP error pages, and a welcome page. These are rendered when `AQUILIA_ENV=dev`.

## When to Use

Use the Debug module when you need:

- Interactive traceback pages in development mode
- Customised error page rendering
- A welcome/landing page for new workspaces

## Key Classes

| Class | Purpose |
|---|---|
| `DebugPageRenderer` | Renders interactive debug and error pages |
| `render_debug_exception_page` | Renders a traceback page with source context |
| `render_http_error_page` | Renders styled HTTP error pages (404, 500, etc.) |
| `render_welcome_page` | Renders the default Aquilia landing page |

## Import Path

```python
from aquilia.debug import (
    DebugPageRenderer,
    render_debug_exception_page,
    render_http_error_page,
    render_welcome_page,
)
```

## Related Modules

- [core/server](../core/server.md) — Server enables debug pages in DEV mode
- [faults](../faults/index.md) — Faults rendered by debug pages