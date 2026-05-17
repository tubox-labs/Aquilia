# Extended Middleware API Reference

This page is extracted from the current Python source. It includes public classes, methods, functions, constants, dataclass-like fields, decorators, and notable attributes.

## Public Class Summary

| Name | Source | Bases | Purpose |
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

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `ip_key_extractor` | `aquilia/middleware_ext/rate_limit.py` | `def ip_key_extractor(request: Request) -> str` | Extract client IP as rate-limit key. |
| `api_key_extractor` | `aquilia/middleware_ext/rate_limit.py` | `def api_key_extractor(request: Request) -> str &#124; None` | Extract API key from Authorization or X-API-Key header. |
| `user_key_extractor` | `aquilia/middleware_ext/rate_limit.py` | `def user_key_extractor(request: Request) -> str &#124; None` | Extract user ID from request state (set by auth middleware). |
| `create_request_scope_middleware` | `aquilia/middleware_ext/request_scope.py` | `def create_request_scope_middleware(runtime: Any) -> Callable` | Factory function to create request scope middleware. |
| `csrf_token_func` | `aquilia/middleware_ext/security.py` | `def csrf_token_func(request: Request) -> str` | Extract the CSRF token from request state. |
| `csrf_exempt` | `aquilia/middleware_ext/security.py` | `def csrf_exempt(request: Request) -> None` | Mark a request as exempt from CSRF validation. |
| `create_session_middleware` | `aquilia/middleware_ext/session_middleware.py` | `def create_session_middleware(session_engine: Optional['SessionEngine'] = None, optional: bool = False) -> SessionMiddleware &#124; OptionalSessionMiddleware` | Factory function to create session middleware. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `_COLORS` | `aquilia/middleware_ext/logging.py` | `{'reset': '\x1b[0m', 'bold': '\x1b[1m', 'dim': '\x1b[2m', 'green': '\x1b[32m', 'yellow': '\x1b[33m', 'red': '\x1b[31m', 'cyan': '\x1b[36m', 'magenta': '\x1b[35m` |
| `_EXTRA_MIME_TYPES` | `aquilia/middleware_ext/static.py` | `dict[str, str]` |

## Detailed Classes And Methods

### Class: `EffectMiddleware`

- Source: `aquilia/middleware_ext/effect_middleware.py`
- Bases: `object`
- Summary: ASGI middleware that manages per-request effect lifecycle.

### Class: `FlowContextMiddleware`

- Source: `aquilia/middleware_ext/effect_middleware.py`
- Bases: `object`
- Summary: Middleware that creates a FlowContext for each request.

### Class: `CombinedLogFormatter`

- Source: `aquilia/middleware_ext/logging.py`
- Bases: `_LogFormatter`
- Summary: Apache Combined Log Format.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `format_request` | `def format_request(self, **kwargs: Any) -> str` |  | Method. |

### Class: `StructuredLogFormatter`

- Source: `aquilia/middleware_ext/logging.py`
- Bases: `_LogFormatter`
- Summary: JSON-structured log output.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `format_request` | `def format_request(self, **kwargs: Any) -> str` |  | Method. |

### Class: `DevLogFormatter`

- Source: `aquilia/middleware_ext/logging.py`
- Bases: `_LogFormatter`
- Summary: Color-coded developer-friendly format.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `format_request` | `def format_request(self, **kwargs: Any) -> str` |  | Method. |

### Class: `LoggingMiddleware`

- Source: `aquilia/middleware_ext/logging.py`
- Bases: `object`
- Summary: Enhanced HTTP access logging middleware.

### Class: `RateLimitRule`

- Source: `aquilia/middleware_ext/rate_limit.py`
- Bases: `object`
- Summary: A single rate-limit rule.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `matches` | `def matches(self, request: Request) -> bool` |  | Check if this rule applies to the given request. |

### Class: `RateLimitMiddleware`

- Source: `aquilia/middleware_ext/rate_limit.py`
- Bases: `object`
- Summary: Multi-algorithm rate limiting middleware.

### Class: `RequestScopeMiddleware`

- Source: `aquilia/middleware_ext/request_scope.py`
- Bases: `object`
- Summary: ASGI middleware that creates request-scoped DI container.

### Class: `SimplifiedRequestScopeMiddleware`

- Source: `aquilia/middleware_ext/request_scope.py`
- Bases: `object`
- Summary: Simplified middleware for frameworks with request objects.

### Class: `CORSMiddleware`

- Source: `aquilia/middleware_ext/security.py`
- Bases: `object`
- Summary: Full-featured CORS middleware following the Fetch Standard.

### Class: `CSPPolicy`

- Source: `aquilia/middleware_ext/security.py`
- Bases: `object`
- Summary: Builder for Content-Security-Policy directives.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `default_src` | `def default_src(self, *sources: str) -> CSPPolicy` |  | Method. |
| `script_src` | `def script_src(self, *sources: str) -> CSPPolicy` |  | Method. |
| `style_src` | `def style_src(self, *sources: str) -> CSPPolicy` |  | Method. |
| `img_src` | `def img_src(self, *sources: str) -> CSPPolicy` |  | Method. |
| `font_src` | `def font_src(self, *sources: str) -> CSPPolicy` |  | Method. |
| `connect_src` | `def connect_src(self, *sources: str) -> CSPPolicy` |  | Method. |
| `media_src` | `def media_src(self, *sources: str) -> CSPPolicy` |  | Method. |
| `object_src` | `def object_src(self, *sources: str) -> CSPPolicy` |  | Method. |
| `frame_src` | `def frame_src(self, *sources: str) -> CSPPolicy` |  | Method. |
| `frame_ancestors` | `def frame_ancestors(self, *sources: str) -> CSPPolicy` |  | Method. |
| `base_uri` | `def base_uri(self, *sources: str) -> CSPPolicy` |  | Method. |
| `form_action` | `def form_action(self, *sources: str) -> CSPPolicy` |  | Method. |
| `worker_src` | `def worker_src(self, *sources: str) -> CSPPolicy` |  | Method. |
| `child_src` | `def child_src(self, *sources: str) -> CSPPolicy` |  | Method. |
| `manifest_src` | `def manifest_src(self, *sources: str) -> CSPPolicy` |  | Method. |
| `upgrade_insecure_requests` | `def upgrade_insecure_requests(self) -> CSPPolicy` |  | Method. |
| `block_all_mixed_content` | `def block_all_mixed_content(self) -> CSPPolicy` |  | Method. |
| `report_uri` | `def report_uri(self, uri: str) -> CSPPolicy` |  | Method. |
| `report_to` | `def report_to(self, group: str) -> CSPPolicy` |  | Method. |
| `directive` | `def directive(self, name: str, *sources: str) -> CSPPolicy` |  | Add an arbitrary directive. |
| `build` | `def build(self, nonce: str &#124; None = None) -> str` |  | Compile directives into a CSP header value string. |
| `strict` | `def strict(cls) -> CSPPolicy` | classmethod | Strict CSP suitable for most web applications. |
| `relaxed` | `def relaxed(cls) -> CSPPolicy` | classmethod | Relaxed CSP for rapid development. |

### Class: `CSPMiddleware`

- Source: `aquilia/middleware_ext/security.py`
- Bases: `object`
- Summary: Content-Security-Policy middleware.

### Class: `HSTSMiddleware`

- Source: `aquilia/middleware_ext/security.py`
- Bases: `object`
- Summary: HTTP Strict Transport Security middleware.

### Class: `HTTPSRedirectMiddleware`

- Source: `aquilia/middleware_ext/security.py`
- Bases: `object`
- Summary: Redirect HTTP requests to HTTPS.

### Class: `ProxyFixMiddleware`

- Source: `aquilia/middleware_ext/security.py`
- Bases: `object`
- Summary: Fix request attributes when behind a reverse proxy.

### Class: `SecurityHeadersMiddleware`

- Source: `aquilia/middleware_ext/security.py`
- Bases: `object`
- Summary: Catch-all security headers middleware (like Helmet.js for Node).

### Class: `CSRFError`

- Source: `aquilia/middleware_ext/security.py`
- Bases: `CSRFViolationFault`
- Summary: CSRF validation fault -- raised when CSRF protection detects a violation.

### Class: `CSRFMiddleware`

- Source: `aquilia/middleware_ext/security.py`
- Bases: `object`
- Summary: Production-grade CSRF (Cross-Site Request Forgery) protection middleware.

### Class: `SessionMiddleware`

- Source: `aquilia/middleware_ext/session_middleware.py`
- Bases: `object`
- Summary: Middleware that integrates SessionEngine with request lifecycle.

### Class: `OptionalSessionMiddleware`

- Source: `aquilia/middleware_ext/session_middleware.py`
- Bases: `object`
- Summary: Session middleware that gracefully handles missing SessionEngine.

### Class: `StaticMiddleware`

- Source: `aquilia/middleware_ext/static.py`
- Bases: `object`
- Summary: Production-grade static file serving middleware.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `url_for_static` | `def url_for_static(self, path: str) -> str` |  | Generate a URL for a static asset. |

## Functions

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `ip_key_extractor` | `aquilia/middleware_ext/rate_limit.py` | `def ip_key_extractor(request: Request) -> str` | Extract client IP as rate-limit key. |
| `api_key_extractor` | `aquilia/middleware_ext/rate_limit.py` | `def api_key_extractor(request: Request) -> str &#124; None` | Extract API key from Authorization or X-API-Key header. |
| `user_key_extractor` | `aquilia/middleware_ext/rate_limit.py` | `def user_key_extractor(request: Request) -> str &#124; None` | Extract user ID from request state (set by auth middleware). |
| `create_request_scope_middleware` | `aquilia/middleware_ext/request_scope.py` | `def create_request_scope_middleware(runtime: Any) -> Callable` | Factory function to create request scope middleware. |
| `csrf_token_func` | `aquilia/middleware_ext/security.py` | `def csrf_token_func(request: Request) -> str` | Extract the CSRF token from request state. |
| `csrf_exempt` | `aquilia/middleware_ext/security.py` | `def csrf_exempt(request: Request) -> None` | Mark a request as exempt from CSRF validation. |
| `create_session_middleware` | `aquilia/middleware_ext/session_middleware.py` | `def create_session_middleware(session_engine: Optional['SessionEngine'] = None, optional: bool = False) -> SessionMiddleware &#124; OptionalSessionMiddleware` | Factory function to create session middleware. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `_COLORS` | `aquilia/middleware_ext/logging.py` | `{'reset': '\x1b[0m', 'bold': '\x1b[1m', 'dim': '\x1b[2m', 'green': '\x1b[32m', 'yellow': '\x1b[33m', 'red': '\x1b[31m', 'cyan': '\x1b[36m', 'magenta': '\x1b[35m` |
| `_EXTRA_MIME_TYPES` | `aquilia/middleware_ext/static.py` | `dict[str, str]` |
