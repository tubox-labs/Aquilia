# Middleware_Ext Architecture

Extended production middleware for security, CORS/CSP/CSRF/HSTS, static files, rate limits, sessions, request scopes, effects, and logging.

## Source Boundaries

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/middleware_ext/__init__.py` | 99 | 0 | 0 | Extended middleware components for Aquilia framework. |
| `aquilia/middleware_ext/effect_middleware.py` | 260 | 2 | 0 | Effect Middleware -- Per-request effect lifecycle management. |
| `aquilia/middleware_ext/logging.py` | 283 | 4 | 0 | Enhanced Logging Middleware - Structured access logging. |
| `aquilia/middleware_ext/rate_limit.py` | 473 | 2 | 3 | Rate Limiting Middleware - Production-grade request rate limiting. |
| `aquilia/middleware_ext/request_scope.py` | 168 | 2 | 1 | Request Scope Middleware - Creates request-scoped DI container per request. |
| `aquilia/middleware_ext/security.py` | 1187 | 9 | 2 | Security Middleware Suite - Production-grade HTTP security middleware. |
| `aquilia/middleware_ext/session_middleware.py` | 214 | 2 | 1 | Session Middleware - Integrates SessionEngine with request lifecycle. |
| `aquilia/middleware_ext/static.py` | 590 | 1 | 0 | Static File Middleware - Production-grade static asset serving. |

## Internal Shape

`middleware_ext` has 8 Python files, 22 public classes, 7 public module-level functions, and 7 constants or module flags detected by AST.

## Runtime Responsibilities

- No mounted `aq` command group maps directly to this module; it is used through Python APIs, manifests, workspace integrations, or server startup wiring.

## Internal Imports

| Import | Count |
| --- | ---: |
| `aquilia.request` | 5 |
| `aquilia.response` | 5 |
| `aquilia.faults.domains` | 3 |
| `.logging` | 2 |
| `.effect_middleware` | 1 |
| `.rate_limit` | 1 |
| `.request_scope` | 1 |
| `.security` | 1 |
| `.session_middleware` | 1 |
| `.static` | 1 |
| `aquilia.di` | 1 |
| `aquilia.middleware` | 1 |

## External And Stdlib Imports

| Import root | Count |
| --- | ---: |
| `collections` | 7 |
| `typing` | 7 |
| `__future__` | 5 |
| `logging` | 3 |
| `contextlib` | 2 |
| `datetime` | 2 |
| `re` | 2 |
| `time` | 2 |
| `email` | 1 |
| `hashlib` | 1 |
| `ipaddress` | 1 |
| `math` | 1 |
| `mimetypes` | 1 |
| `os` | 1 |
| `pathlib` | 1 |
| `secrets` | 1 |

## Lifecycle And Extension Points

| Extension Type | Source | Role |
| --- | --- | --- |
| `EffectMiddleware` | `aquilia/middleware_ext/effect_middleware.py` | ASGI middleware that manages per-request effect lifecycle. |
| `FlowContextMiddleware` | `aquilia/middleware_ext/effect_middleware.py` | Middleware that creates a FlowContext for each request. |
| `LoggingMiddleware` | `aquilia/middleware_ext/logging.py` | Enhanced HTTP access logging middleware. |
| `RateLimitMiddleware` | `aquilia/middleware_ext/rate_limit.py` | Multi-algorithm rate limiting middleware. |
| `RequestScopeMiddleware` | `aquilia/middleware_ext/request_scope.py` | ASGI middleware that creates request-scoped DI container. |
| `SimplifiedRequestScopeMiddleware` | `aquilia/middleware_ext/request_scope.py` | Simplified middleware for frameworks with request objects. |
| `CORSMiddleware` | `aquilia/middleware_ext/security.py` | Full-featured CORS middleware following the Fetch Standard. |
| `CSPPolicy` | `aquilia/middleware_ext/security.py` | Builder for Content-Security-Policy directives. |
| `CSPMiddleware` | `aquilia/middleware_ext/security.py` | Content-Security-Policy middleware. |
| `HSTSMiddleware` | `aquilia/middleware_ext/security.py` | HTTP Strict Transport Security middleware. |
| `HTTPSRedirectMiddleware` | `aquilia/middleware_ext/security.py` | Redirect HTTP requests to HTTPS. |
| `ProxyFixMiddleware` | `aquilia/middleware_ext/security.py` | Fix request attributes when behind a reverse proxy. |
| `SecurityHeadersMiddleware` | `aquilia/middleware_ext/security.py` | Catch-all security headers middleware (like Helmet.js for Node). |
| `CSRFMiddleware` | `aquilia/middleware_ext/security.py` | Production-grade CSRF (Cross-Site Request Forgery) protection middleware. |
| `SessionMiddleware` | `aquilia/middleware_ext/session_middleware.py` | Middleware that integrates SessionEngine with request lifecycle. |
| `OptionalSessionMiddleware` | `aquilia/middleware_ext/session_middleware.py` | Session middleware that gracefully handles missing SessionEngine. |
| `StaticMiddleware` | `aquilia/middleware_ext/static.py` | Production-grade static file serving middleware. |

## Error Handling

Fault/error classes defined here:

`CSRFError`
