# Middleware Extension

> `aquilia.middleware_ext` — Extended middleware for security, rate limiting, and static files

The middleware extensions module provides production-grade security middleware (CORS, CSP, CSRF, HSTS), rate limiting, static file serving, proxy fix middleware, and HTTPS redirect middleware.

## When to Use

Use the middleware_ext module when you need:

- Cross-Origin Resource Sharing (CORS) headers
- Content Security Policy (CSP) headers
- Cross-Site Request Forgery (CSRF) protection
- HTTP Strict Transport Security (HSTS)
- Rate limiting on routes
- Static file serving
- Proxy-aware IP detection

## Key Classes

| Class | Purpose |
|---|---|
| `CORSMiddleware` | CORS header management and preflight |
| `CSPMiddleware` | Content-Security-Policy header management |
| `CSPPolicy` | CSP directive configuration |
| `CSRFMiddleware` | CSRF token validation |
| `HSTSMiddleware` | Strict-Transport-Security header |
| `HTTPSRedirectMiddleware` | Redirect HTTP to HTTPS |
| `SecurityHeadersMiddleware` | Applies multiple security headers |
| `RateLimitMiddleware` | Rate limiting with configurable rules |
| `RateLimitRule` | Individual rate limit rule |
| `StaticMiddleware` | Static file serving with caching |
| `ProxyFixMiddleware` | Corrects client IP behind proxies |

## Quick Example

```python
from aquilia.middleware_ext.security import (
    CORSMiddleware,
    CSRFMiddleware,
    HSTSMiddleware,
    CSPMiddleware,
    SecurityHeadersMiddleware,
)
from aquilia.middleware_ext.static import StaticMiddleware
from aquilia.middleware_ext.rate_limit import RateLimitMiddleware, RateLimitRule

# CORS
cors = CORSMiddleware(
    origins=["http://localhost:3000"],
    methods=["GET", "POST"],
    headers=["Content-Type", "Authorization"],
)

# Rate limiting
rate_limit = RateLimitMiddleware(rules=[
    RateLimitRule(path="/api/*", limit=100, window=60),
    RateLimitRule(path="/login", limit=5, window=300),
])

# CSRF
csrf = CSRFMiddleware(secret="csrf-secret")

# Static files
static = StaticMiddleware(directory="static/", cache_control="public, max-age=3600")
```

## Import Path

```python
from aquilia.middleware_ext import (
    CORSMiddleware,
    CSPMiddleware,
    CSPPolicy,
    CSRFMiddleware,
    HSTSMiddleware,
    HTTPSRedirectMiddleware,
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    RateLimitRule,
    StaticMiddleware,
    ProxyFixMiddleware,
    csrf_exempt,
    csrf_token_func,
)
```

## Related Modules

- [core/middleware](../core/middleware.md) — Middleware composition and ordering
- [auth](../auth/index.md) — Auth middleware integration
- [sessions](../sessions/index.md) — Session middleware