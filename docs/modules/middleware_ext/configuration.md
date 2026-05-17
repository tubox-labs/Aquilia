# Middleware_Ext Configuration

Extended production middleware for security, CORS/CSP/CSRF/HSTS, static files, rate limits, sessions, request scopes, effects, and logging.

This page distinguishes direct configuration APIs from indirect runtime wiring. All class names and source files below are extracted from the current source tree.

## Configuration Model

This module exposes config-oriented public classes. Use the table below to locate exact constructors and `to_dict()` behavior in `api-reference.md`.

## Source Inventory

| File | Lines | Public classes | Public functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/middleware_ext/__init__.py` | 99 | 0 | 0 | Extended middleware components for Aquilia framework. |
| `aquilia/middleware_ext/effect_middleware.py` | 260 | 2 | 0 | Effect Middleware -- Per-request effect lifecycle management. |
| `aquilia/middleware_ext/logging.py` | 283 | 4 | 0 | Enhanced Logging Middleware - Structured access logging. |
| `aquilia/middleware_ext/rate_limit.py` | 473 | 2 | 3 | Rate Limiting Middleware - Production-grade request rate limiting. |
| `aquilia/middleware_ext/request_scope.py` | 168 | 2 | 1 | Request Scope Middleware - Creates request-scoped DI container per request. |
| `aquilia/middleware_ext/security.py` | 1187 | 9 | 2 | Security Middleware Suite - Production-grade HTTP security middleware. |
| `aquilia/middleware_ext/session_middleware.py` | 214 | 2 | 1 | Session Middleware - Integrates SessionEngine with request lifecycle. |
| `aquilia/middleware_ext/static.py` | 590 | 1 | 0 | Static File Middleware - Production-grade static asset serving. |

## Detected Config-Oriented Classes

| Class | Source | Methods | Summary |
| --- | --- | --- | --- |
| `EffectMiddleware` | `aquilia/middleware_ext/effect_middleware.py` |  | ASGI middleware that manages per-request effect lifecycle. |
| `FlowContextMiddleware` | `aquilia/middleware_ext/effect_middleware.py` |  | Middleware that creates a FlowContext for each request. |
| `LoggingMiddleware` | `aquilia/middleware_ext/logging.py` |  | Enhanced HTTP access logging middleware. |
| `RateLimitMiddleware` | `aquilia/middleware_ext/rate_limit.py` |  | Multi-algorithm rate limiting middleware. |
| `RequestScopeMiddleware` | `aquilia/middleware_ext/request_scope.py` |  | ASGI middleware that creates request-scoped DI container. |
| `SimplifiedRequestScopeMiddleware` | `aquilia/middleware_ext/request_scope.py` |  | Simplified middleware for frameworks with request objects. |
| `CORSMiddleware` | `aquilia/middleware_ext/security.py` |  | Full-featured CORS middleware following the Fetch Standard. |
| `CSPPolicy` | `aquilia/middleware_ext/security.py` | `default_src`, `script_src`, `style_src`, `img_src`, `font_src`, `connect_src`, `media_src`, `object_src`, `frame_src`, `frame_ancestors`, `base_uri`, `form_action`, `worker_src`, `child_src`, `manifest_src`, `upgrade_insecure_requests`, `block_all_mixed_content`, `report_uri`, `report_to`, `directive` | Builder for Content-Security-Policy directives. |
| `CSPMiddleware` | `aquilia/middleware_ext/security.py` |  | Content-Security-Policy middleware. |
| `HSTSMiddleware` | `aquilia/middleware_ext/security.py` |  | HTTP Strict Transport Security middleware. |
| `HTTPSRedirectMiddleware` | `aquilia/middleware_ext/security.py` |  | Redirect HTTP requests to HTTPS. |
| `ProxyFixMiddleware` | `aquilia/middleware_ext/security.py` |  | Fix request attributes when behind a reverse proxy. |
| `SecurityHeadersMiddleware` | `aquilia/middleware_ext/security.py` |  | Catch-all security headers middleware (like Helmet.js for Node). |
| `CSRFMiddleware` | `aquilia/middleware_ext/security.py` |  | Production-grade CSRF (Cross-Site Request Forgery) protection middleware. |
| `SessionMiddleware` | `aquilia/middleware_ext/session_middleware.py` |  | Middleware that integrates SessionEngine with request lifecycle. |
| `OptionalSessionMiddleware` | `aquilia/middleware_ext/session_middleware.py` |  | Session middleware that gracefully handles missing SessionEngine. |
| `StaticMiddleware` | `aquilia/middleware_ext/static.py` | `url_for_static` | Production-grade static file serving middleware. |

## Runtime Wiring Paths

- `workspace.py` defines workspace-level structure with `Workspace`, `Module`, and `Integration` builders.
- `modules/<name>/manifest.py` defines module internals with `AppManifest`.
- `ConfigLoader.get(...)` resolves dotted configuration paths at runtime.
- `AquiliaServer` consumes resolved config during middleware and subsystem setup.
- Subsystems with optional providers only require optional dependencies when their backend/provider is configured.

## Verification Checklist

1. Run `aq validate` to verify manifests.
2. Run `aq inspect config` to inspect resolved configuration.
3. Run `aq doctor` for workspace and integration diagnostics.
4. For server-only wiring, start via `aq run` and check startup logs plus `GET /_health`.

## Related Pages

- `api-reference.md` for exact class fields, methods, constants, and signatures.
- `integration-guide.md` for the workspace/manifest wiring pattern.
- `edge-cases-and-limitations.md` for fallback and compatibility behavior.
