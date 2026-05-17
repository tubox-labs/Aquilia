# middleware_ext Module

## Purpose

Production middleware extensions. Use this module for CORS, CSP, CSRF, HSTS, HTTPS redirects, proxy fixes, static files, request scopes, sessions, rate limiting, logging, and effect-aware middleware.

## Source Coverage

- Python files: 8
- Public classes: 22
- Dataclasses: 0
- Enums: 0
- Public functions: 7

## How It Fits In Aquilia

1. Import the package from `aquilia.middleware_ext` or its concrete submodules.
2. Configure it through workspace integrations, manifests, or direct service construction depending on the subsystem.
3. Keep business logic outside transport and framework glue so the subsystem stays testable.

## Practical Guidance

- Prefer typed configuration objects and framework helpers over ad hoc dictionaries when they exist.
- Use the tests in `tests/` as behavioral examples when changing this subsystem.

## Public Classes

| Name | Source | Role |
| --- | --- | --- |
| `EffectMiddleware` | `aquilia/middleware_ext/effect_middleware.py` | ASGI middleware that manages per-request effect lifecycle. |
| `FlowContextMiddleware` | `aquilia/middleware_ext/effect_middleware.py` | Middleware that creates a FlowContext for each request. |
| `CombinedLogFormatter` | `aquilia/middleware_ext/logging.py` | Apache Combined Log Format. |
| `StructuredLogFormatter` | `aquilia/middleware_ext/logging.py` | JSON-structured log output. |
| `DevLogFormatter` | `aquilia/middleware_ext/logging.py` | Color-coded developer-friendly format. |
| `LoggingMiddleware` | `aquilia/middleware_ext/logging.py` | Enhanced HTTP access logging middleware. |
| `RateLimitRule` | `aquilia/middleware_ext/rate_limit.py` | A single rate-limit rule. |
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
| `CSRFError` | `aquilia/middleware_ext/security.py` | CSRF validation fault -- raised when CSRF protection detects a violation. |
| `CSRFMiddleware` | `aquilia/middleware_ext/security.py` | Production-grade CSRF (Cross-Site Request Forgery) protection middleware. |
| `SessionMiddleware` | `aquilia/middleware_ext/session_middleware.py` | Middleware that integrates SessionEngine with request lifecycle. |
| `OptionalSessionMiddleware` | `aquilia/middleware_ext/session_middleware.py` | Session middleware that gracefully handles missing SessionEngine. |
| `StaticMiddleware` | `aquilia/middleware_ext/static.py` | Production-grade static file serving middleware. |

## Public Functions

| Name | Source | Role |
| --- | --- | --- |
| `ip_key_extractor` | `aquilia/middleware_ext/rate_limit.py` | Extract client IP as rate-limit key. |
| `api_key_extractor` | `aquilia/middleware_ext/rate_limit.py` | Extract API key from Authorization or X-API-Key header. |
| `user_key_extractor` | `aquilia/middleware_ext/rate_limit.py` | Extract user ID from request state (set by auth middleware). |
| `create_request_scope_middleware` | `aquilia/middleware_ext/request_scope.py` | Factory function to create request scope middleware. |
| `csrf_token_func` | `aquilia/middleware_ext/security.py` | Extract the CSRF token from request state. |
| `csrf_exempt` | `aquilia/middleware_ext/security.py` | Mark a request as exempt from CSRF validation. |
| `create_session_middleware` | `aquilia/middleware_ext/session_middleware.py` | Factory function to create session middleware. |

## Implementation Map

| File | What To Look For |
| --- | --- |
| `aquilia/middleware_ext/__init__.py` | Extended middleware components for Aquilia framework. |
| `aquilia/middleware_ext/effect_middleware.py` | Effect Middleware -- Per-request effect lifecycle management. |
| `aquilia/middleware_ext/logging.py` | Enhanced Logging Middleware - Structured access logging. |
| `aquilia/middleware_ext/rate_limit.py` | Rate Limiting Middleware - Production-grade request rate limiting. |
| `aquilia/middleware_ext/request_scope.py` | Request Scope Middleware - Creates request-scoped DI container per request. |
| `aquilia/middleware_ext/security.py` | Security Middleware Suite - Production-grade HTTP security middleware. |
| `aquilia/middleware_ext/session_middleware.py` | Session Middleware - Integrates SessionEngine with request lifecycle. |
| `aquilia/middleware_ext/static.py` | Static File Middleware - Production-grade static asset serving. |

## Testing Pointers

Search `tests/` for `middleware_ext` to find behavior-level examples. The test suite is especially useful for edge cases because many modules expose lightweight public APIs but enforce important security and lifecycle behavior internally.
