# Middleware_Ext API Reference

This page is generated from the current Python source using the AST. It lists public classes, public methods, public module-level functions, constants, exports, and source files.

## Source Inventory

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

## Public Exports

`CORSMiddleware`, `CSPMiddleware`, `CSPPolicy`, `CSRFError`, `CSRFMiddleware`, `CombinedLogFormatter`, `DevLogFormatter`, `EffectMiddleware`, `EnhancedLoggingMiddleware`, `FlowContextMiddleware`, `HSTSMiddleware`, `HTTPSRedirectMiddleware`, `LoggingMiddleware`, `OptionalSessionMiddleware`, `ProxyFixMiddleware`, `RateLimitMiddleware`, `RateLimitRule`, `RequestScopeMiddleware`, `SecurityHeadersMiddleware`, `SessionMiddleware`, `SimplifiedRequestScopeMiddleware`, `StaticMiddleware`, `StructuredLogFormatter`, `api_key_extractor`, `create_session_middleware`, `csrf_exempt`, `csrf_token_func`, `ip_key_extractor`, `user_key_extractor`

## Public Class Summary

| Class | Source | Bases | Summary |
| --- | --- | --- | --- |
| `EffectMiddleware` | `aquilia/middleware_ext/effect_middleware.py` | object | ASGI middleware that manages per-request effect lifecycle. |
| `FlowContextMiddleware` | `aquilia/middleware_ext/effect_middleware.py` | object | Middleware that creates a FlowContext for each request. |
| `CombinedLogFormatter` | `aquilia/middleware_ext/logging.py` | _LogFormatter | Apache Combined Log Format. |
| `StructuredLogFormatter` | `aquilia/middleware_ext/logging.py` | _LogFormatter | JSON-structured log output. |
| `DevLogFormatter` | `aquilia/middleware_ext/logging.py` | _LogFormatter | Color-coded developer-friendly format. |
| `LoggingMiddleware` | `aquilia/middleware_ext/logging.py` | object | Enhanced HTTP access logging middleware. |
| `RateLimitRule` | `aquilia/middleware_ext/rate_limit.py` | object | A single rate-limit rule. |
| `RateLimitMiddleware` | `aquilia/middleware_ext/rate_limit.py` | object | Multi-algorithm rate limiting middleware. |
| `RequestScopeMiddleware` | `aquilia/middleware_ext/request_scope.py` | object | ASGI middleware that creates request-scoped DI container. |
| `SimplifiedRequestScopeMiddleware` | `aquilia/middleware_ext/request_scope.py` | object | Simplified middleware for frameworks with request objects. |
| `CORSMiddleware` | `aquilia/middleware_ext/security.py` | object | Full-featured CORS middleware following the Fetch Standard. |
| `CSPPolicy` | `aquilia/middleware_ext/security.py` | object | Builder for Content-Security-Policy directives. |
| `CSPMiddleware` | `aquilia/middleware_ext/security.py` | object | Content-Security-Policy middleware. |
| `HSTSMiddleware` | `aquilia/middleware_ext/security.py` | object | HTTP Strict Transport Security middleware. |
| `HTTPSRedirectMiddleware` | `aquilia/middleware_ext/security.py` | object | Redirect HTTP requests to HTTPS. |
| `ProxyFixMiddleware` | `aquilia/middleware_ext/security.py` | object | Fix request attributes when behind a reverse proxy. |
| `SecurityHeadersMiddleware` | `aquilia/middleware_ext/security.py` | object | Catch-all security headers middleware (like Helmet.js for Node). |
| `CSRFError` | `aquilia/middleware_ext/security.py` | CSRFViolationFault | CSRF validation fault -- raised when CSRF protection detects a violation. |
| `CSRFMiddleware` | `aquilia/middleware_ext/security.py` | object | Production-grade CSRF (Cross-Site Request Forgery) protection middleware. |
| `SessionMiddleware` | `aquilia/middleware_ext/session_middleware.py` | object | Middleware that integrates SessionEngine with request lifecycle. |
| `OptionalSessionMiddleware` | `aquilia/middleware_ext/session_middleware.py` | object | Session middleware that gracefully handles missing SessionEngine. |
| `StaticMiddleware` | `aquilia/middleware_ext/static.py` | object | Production-grade static file serving middleware. |

## Public Function Summary

| Function | Source | Signature | Summary |
| --- | --- | --- | --- |
| `ip_key_extractor` | `aquilia/middleware_ext/rate_limit.py` | `def ip_key_extractor(request: Request)` | Extract client IP as rate-limit key. |
| `api_key_extractor` | `aquilia/middleware_ext/rate_limit.py` | `def api_key_extractor(request: Request)` | Extract API key from Authorization or X-API-Key header. |
| `user_key_extractor` | `aquilia/middleware_ext/rate_limit.py` | `def user_key_extractor(request: Request)` | Extract user ID from request state (set by auth middleware). |
| `create_request_scope_middleware` | `aquilia/middleware_ext/request_scope.py` | `def create_request_scope_middleware(runtime: Any)` | Factory function to create request scope middleware. |
| `csrf_token_func` | `aquilia/middleware_ext/security.py` | `def csrf_token_func(request: Request)` | Extract the CSRF token from request state. |
| `csrf_exempt` | `aquilia/middleware_ext/security.py` | `def csrf_exempt(request: Request)` | Mark a request as exempt from CSRF validation. |
| `create_session_middleware` | `aquilia/middleware_ext/session_middleware.py` | `def create_session_middleware(session_engine: Optional['SessionEngine']=None, optional: bool=False)` | Factory function to create session middleware. |

## Constants And Module Flags

| Name | Source | Value or Type |
| --- | --- | --- |
| `_COLORS` | `aquilia/middleware_ext/logging.py` | `{'reset': '\x1b[0m', 'bold': '\x1b[1m', 'dim': '\x1b[2m', 'green': '\x1b[32m', 'yellow': '\x1b[33m', 'red': '\x1b[31m', 'cyan': '\x1b[36m', 'magenta': '\x1b[35m', 'blue': '\x1b[34m', 'white': '\x1b[37m'}` |
| `_EXTRA_MIME_TYPES` | `aquilia/middleware_ext/static.py` | `dict[str, str]` |

## Detailed Classes And Methods

### `EffectMiddleware`

- Source: `aquilia/middleware_ext/effect_middleware.py`
- Bases: `object`
- Summary: ASGI middleware that manages per-request effect lifecycle.

### `FlowContextMiddleware`

- Source: `aquilia/middleware_ext/effect_middleware.py`
- Bases: `object`
- Summary: Middleware that creates a FlowContext for each request.

### `CombinedLogFormatter`

- Source: `aquilia/middleware_ext/logging.py`
- Bases: `_LogFormatter`
- Summary: Apache Combined Log Format.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `format_request` | `def format_request(self, **kwargs: Any)` |  |

### `StructuredLogFormatter`

- Source: `aquilia/middleware_ext/logging.py`
- Bases: `_LogFormatter`
- Summary: JSON-structured log output.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `format_request` | `def format_request(self, **kwargs: Any)` |  |

### `DevLogFormatter`

- Source: `aquilia/middleware_ext/logging.py`
- Bases: `_LogFormatter`
- Summary: Color-coded developer-friendly format.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `format_request` | `def format_request(self, **kwargs: Any)` |  |

### `LoggingMiddleware`

- Source: `aquilia/middleware_ext/logging.py`
- Bases: `object`
- Summary: Enhanced HTTP access logging middleware.

### `RateLimitRule`

- Source: `aquilia/middleware_ext/rate_limit.py`
- Bases: `object`
- Summary: A single rate-limit rule.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `matches` | `def matches(self, request: Request)` | Check if this rule applies to the given request. |

### `RateLimitMiddleware`

- Source: `aquilia/middleware_ext/rate_limit.py`
- Bases: `object`
- Summary: Multi-algorithm rate limiting middleware.

### `RequestScopeMiddleware`

- Source: `aquilia/middleware_ext/request_scope.py`
- Bases: `object`
- Summary: ASGI middleware that creates request-scoped DI container.

### `SimplifiedRequestScopeMiddleware`

- Source: `aquilia/middleware_ext/request_scope.py`
- Bases: `object`
- Summary: Simplified middleware for frameworks with request objects.

### `CORSMiddleware`

- Source: `aquilia/middleware_ext/security.py`
- Bases: `object`
- Summary: Full-featured CORS middleware following the Fetch Standard.

### `CSPPolicy`

- Source: `aquilia/middleware_ext/security.py`
- Bases: `object`
- Summary: Builder for Content-Security-Policy directives.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `default_src` | `def default_src(self, *sources: str)` |  |
| `script_src` | `def script_src(self, *sources: str)` |  |
| `style_src` | `def style_src(self, *sources: str)` |  |
| `img_src` | `def img_src(self, *sources: str)` |  |
| `font_src` | `def font_src(self, *sources: str)` |  |
| `connect_src` | `def connect_src(self, *sources: str)` |  |
| `media_src` | `def media_src(self, *sources: str)` |  |
| `object_src` | `def object_src(self, *sources: str)` |  |
| `frame_src` | `def frame_src(self, *sources: str)` |  |
| `frame_ancestors` | `def frame_ancestors(self, *sources: str)` |  |
| `base_uri` | `def base_uri(self, *sources: str)` |  |
| `form_action` | `def form_action(self, *sources: str)` |  |
| `worker_src` | `def worker_src(self, *sources: str)` |  |
| `child_src` | `def child_src(self, *sources: str)` |  |
| `manifest_src` | `def manifest_src(self, *sources: str)` |  |
| `upgrade_insecure_requests` | `def upgrade_insecure_requests(self)` |  |
| `block_all_mixed_content` | `def block_all_mixed_content(self)` |  |
| `report_uri` | `def report_uri(self, uri: str)` |  |
| `report_to` | `def report_to(self, group: str)` |  |
| `directive` | `def directive(self, name: str, *sources: str)` | Add an arbitrary directive. |
| `build` | `def build(self, nonce: str \| None=None)` | Compile directives into a CSP header value string. |
| `strict` | `def strict(cls)` | Strict CSP suitable for most web applications. |
| `relaxed` | `def relaxed(cls)` | Relaxed CSP for rapid development. |

### `CSPMiddleware`

- Source: `aquilia/middleware_ext/security.py`
- Bases: `object`
- Summary: Content-Security-Policy middleware.

### `HSTSMiddleware`

- Source: `aquilia/middleware_ext/security.py`
- Bases: `object`
- Summary: HTTP Strict Transport Security middleware.

### `HTTPSRedirectMiddleware`

- Source: `aquilia/middleware_ext/security.py`
- Bases: `object`
- Summary: Redirect HTTP requests to HTTPS.

### `ProxyFixMiddleware`

- Source: `aquilia/middleware_ext/security.py`
- Bases: `object`
- Summary: Fix request attributes when behind a reverse proxy.

### `SecurityHeadersMiddleware`

- Source: `aquilia/middleware_ext/security.py`
- Bases: `object`
- Summary: Catch-all security headers middleware (like Helmet.js for Node).

### `CSRFError`

- Source: `aquilia/middleware_ext/security.py`
- Bases: `CSRFViolationFault`
- Summary: CSRF validation fault -- raised when CSRF protection detects a violation.

### `CSRFMiddleware`

- Source: `aquilia/middleware_ext/security.py`
- Bases: `object`
- Summary: Production-grade CSRF (Cross-Site Request Forgery) protection middleware.

### `SessionMiddleware`

- Source: `aquilia/middleware_ext/session_middleware.py`
- Bases: `object`
- Summary: Middleware that integrates SessionEngine with request lifecycle.

### `OptionalSessionMiddleware`

- Source: `aquilia/middleware_ext/session_middleware.py`
- Bases: `object`
- Summary: Session middleware that gracefully handles missing SessionEngine.

### `StaticMiddleware`

- Source: `aquilia/middleware_ext/static.py`
- Bases: `object`
- Summary: Production-grade static file serving middleware.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `url_for_static` | `def url_for_static(self, path: str)` | Generate a URL for a static asset. |
