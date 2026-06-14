# Templates Module

> `aquilia.templates` — Sandboxed Jinja2 template engine

The Templates module provides a sandboxed Jinja2 environment with bytecode caching, template context processors, template middleware, and HMAC integrity verification — all fully async.

## When to Use

Use the Templates module when you need:

- Server-side HTML rendering in controllers
- Template-based email composition
- Safe user-submitted template rendering (sandbox mode)
- Template caching for production performance

## Key Classes

| Class | Purpose |
|---|---|
| `TemplateEngine` | Async Jinja2 template engine |
| `TemplateMiddleware` | Injects template context into requests |
| `SandboxedEnvironment` | Sandboxed Jinja2 for untrusted templates |

## Quick Example

```python
from aquilia.templates import TemplateEngine
from aquilia import Controller, GET, RequestCtx, Response

# Create engine
engine = TemplateEngine(directories=["templates/"])

# Render a template
html = await engine.render("users/profile.html", {
    "user": {"name": "Alice", "email": "alice@example.com"},
    "settings": {"theme": "dark"},
})

class PagesController(Controller):
    @GET("/profile")
    async def profile(self, ctx: RequestCtx):
        return Response.html(
            await engine.render("pages/profile.html", {"user_name": "Alice"})
        )
```

## Template Features

- **Sandboxed environment** — Safe rendering of untrusted templates
- **Bytecode caching** — Compiled templates cached for production performance
- **HMAC integrity** — Template files verified for tampering
- **Async rendering** — Non-blocking template compilation and rendering
- **Context processors** — Inject variables into every template
- **Auto-escaping** — HTML autoescaping for security

## Import Path

```python
from aquilia.templates import (
    TemplateEngine,
    TemplateMiddleware,
)
```

## Related Modules

- [mail](../mail/index.md) — Email templates via `TemplateMessage`
- [i18n](../i18n/index.md) — Translation in templates via `lazy_t`
- [integrations](../integrations/index.md) — `TemplatesIntegration` config builder