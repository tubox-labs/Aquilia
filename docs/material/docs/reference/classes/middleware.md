# Middleware

## Overview

Aquilia's middleware system is composable, async-first, and effect-aware. Middleware wraps every request in a deterministic chain — global → app → controller → route — sorted by priority. Each middleware receives `(request: Request, ctx: RequestCtx, next: Handler) → Response`.

---

## `MiddlewareStack`

!!! abstract "`aquilia.middleware.MiddlewareStack`"

Manages the middleware chain with deterministic ordering.

```python
class MiddlewareStack:
    def __init__(self): ...
    def add(
        self,
        middleware: Middleware,
        scope: str = "global",
        priority: int = 50,
        name: str | None = None,
    ): ...
    def build_handler(self, final_handler: Handler) -> Handler: ...
    def build_fast_handler(self, final_handler: Handler) -> Handler: ...
```

### `add()`

| Parameter | Type | Default | Description |
|---|---|---|---|
| `middleware` | `Middleware` | — | Callable or instance supporting `__call__(request, ctx, next)` |
| `scope` | `str` | `"global"` | `"global"`, `"app:myapp"`, `"controller:Users"`, `"route:/users/{id}"` |
| `priority` | `int` | `50` | Lower = runs earlier in chain |
| `name` | `str \| None` | `None` | Human-readable name (auto-detected from `__name__`) |

### Scope Ordering

```
global (scope_rank=0) → app:* (1) → controller:* (2) → route:* (3)
```

Within each scope, lower `priority` runs first.

### `build_handler()`

Wraps `final_handler` in reverse so the first middleware in the sorted list is the outermost:

```python
handler = final_handler
for desc in reversed(self.middlewares):   # innermost first
    handler = self._wrap_middleware(desc.middleware, handler)
```

### `build_fast_handler()`

Minimal chain for latency-sensitive routes. Skips `LoggingMiddleware` and `TimeoutMiddleware`; keeps essential middleware (RequestId, Exception, CORS, Compression).

---

## Middleware Descriptor

```python
@dataclass
class MiddlewareDescriptor:
    middleware: Middleware
    scope: str
    priority: int
    name: str
```

---

## Core Built-in Middleware

### `RequestIdMiddleware`

!!! abstract "`aquilia.middleware.RequestIdMiddleware`"

Adds unique request ID to every request (scans raw ASGI headers for performance).

```python
class RequestIdMiddleware:
    def __init__(self, header_name: str = "X-Request-ID"):
    async def __call__(self, request: Request, ctx: RequestCtx, next: Handler) -> Response:
```

- Reads from `X-Request-ID` if present in incoming request
- Generates `os.urandom(16).hex()` if absent (≈4× faster than `uuid.uuid4()`)
- Sets `request.state["request_id"]` and `ctx.request_id`
- Adds `X-Request-ID` header to response

### `ExceptionMiddleware`

!!! abstract "`aquilia.middleware.ExceptionMiddleware`"

Catches exceptions and converts to structured error responses.

```python
class ExceptionMiddleware:
    def __init__(self, debug: bool = False):
    async def __call__(self, request: Request, ctx: RequestCtx, next: Handler) -> Response:
```

- When `debug=True` and client prefers HTML: renders React-style debug pages with Atlas color palette
- Otherwise: structured JSON error response
- Routes through `FaultEngine` for proper handling

### `LoggingMiddleware`

!!! abstract "`aquilia.middleware_ext.LoggingMiddleware`" (Enhanced)

Structured access logging with multiple formatters.

```python
class LoggingMiddleware:
    async def __call__(self, request: Request, ctx: RequestCtx, next: Handler) -> Response:
```

Formatters:

```python
class CombinedLogFormatter: ...   # Apache Combined Log Format
class StructuredLogFormatter: ... # JSON structured logging
class DevLogFormatter: ...        # Colorized dev output
```

### `TimeoutMiddleware`

!!! abstract "`aquilia.middleware.TimeoutMiddleware`"

```python
class TimeoutMiddleware:
    def __init__(self, timeout: float = 30.0):
    async def __call__(self, request: Request, ctx: RequestCtx, next: Handler) -> Response:
```

### `CompressionMiddleware`

!!! abstract "`aquilia.middleware.CompressionMiddleware`"

```python
class CompressionMiddleware:
    def __init__(self, *, level: int = 6, min_size: int = 500):
    async def __call__(self, request: Request, ctx: RequestCtx, next: Handler) -> Response:
```

Offloads `gzip.compress` to thread pool to avoid blocking the event loop.

---

## Security Middleware

### `CORSMiddleware`

!!! abstract "`aquilia.middleware_ext.CORSMiddleware`"

Full RFC 6454/7231 CORS with efficient LRU-cached origin matching.

```python
class CORSMiddleware:
    def __init__(
        self,
        allow_origins: list[str | Pattern] | None = None,
        allow_methods: list[str] | None = None,
        allow_headers: list[str] | None = None,
        expose_headers: list[str] | None = None,
        allow_credentials: bool = False,
        max_age: int = 600,
        allow_origin_regex: str | None = None,
    ):
```

| Parameter | Default | Description |
|---|---|---|
| `allow_origins` | `["*"]` | Strings, globs (`"*.example.com"`), or compiled regex |
| `allow_methods` | `GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS` | |
| `allow_headers` | `accept, content-type, authorization, ...` | |
| `expose_headers` | `[]` | Headers exposed to browser |
| `allow_credentials` | `False` | Enable cookies/Authorization |
| `max_age` | `600` | Preflight cache (seconds) |
| `allow_origin_regex` | `None` | Convenience regex string |

Per-route opt-out via `request.state["cors_skip"] = True`.

### `CSPMiddleware`

!!! abstract "`aquilia.middleware_ext.CSPMiddleware`"

Content-Security-Policy header with per-request nonce support.

```python
class CSPMiddleware:
    def __init__(
        self,
        policy: CSPPolicy | None = None,
        *,
        report_only: bool = False,
        report_uri: str | None = None,
    ):
```

```python
class CSPPolicy:
    def __init__(
        self,
        *,
        default_src: str = "'self'",
        script_src: str = "'self'",
        style_src: str = "'self'",
        img_src: str = "'self'",
        font_src: str = "'self'",
        connect_src: str = "'self'",
        frame_src: str = "'self'",
        object_src: str = "'none'",
        base_uri: str = "'self'",
        form_action: str = "'self'",
        upgrade_insecure_requests: bool = False,
    ):
```

### `CSRFMiddleware`

!!! abstract "`aquilia.middleware_ext.CSRFMiddleware`"

Cross-Site Request Forgery protection (Synchronizer Token + Double Submit Cookie).

```python
class CSRFMiddleware:
    def __init__(
        self,
        *,
        cookie_name: str = "csrftoken",
        header_name: str = "X-CSRFToken",
        safe_methods: list[str] | None = None,  # default: GET, HEAD, OPTIONS
        token_length: int = 64,
    ):
```

Helpers:

```python
def csrf_exempt(view_func): ...       # decorator to exempt routes
def csrf_token_func(request) -> str: ...  # expose csrf token to templates
```

### `HSTSMiddleware`

!!! abstract "`aquilia.middleware_ext.HSTSMiddleware`"

```python
class HSTSMiddleware:
    def __init__(
        self,
        *,
        max_age: int = 31536000,              # 1 year
        include_subdomains: bool = True,
        preload: bool = False,
    ):
```

### `HTTPSRedirectMiddleware`

```python
class HTTPSRedirectMiddleware:
    def __init__(self, *, exempt_paths: list[str] | None = None):
```

### `ProxyFixMiddleware`

```python
class ProxyFixMiddleware:
    def __init__(
        self,
        *,
        trusted_proxies: str | list[str] = "127.0.0.1",
        x_for: int = 1,              # number of trusted X-Forwarded-For entries
        x_proto: int = 1,
        x_host: int = 0,
        x_port: int = 0,
    ):
```

### `SecurityHeadersMiddleware`

Helmet-style catch-all security headers.

```python
class SecurityHeadersMiddleware:
    def __init__(
        self,
        *,
        x_content_type_options: str = "nosniff",
        x_frame_options: str = "DENY",
        x_xss_protection: str = "0",             # modern browsers ignore this
        referrer_policy: str = "strict-origin-when-cross-origin",
        permissions_policy: str | None = None,
        cross_origin_opener_policy: str | None = None,
    ):
```

---

## Other Extended Middleware

### `RateLimitMiddleware`

!!! abstract "`aquilia.middleware_ext.RateLimitMiddleware`"

Token bucket + sliding window rate limiting.

```python
class RateLimitMiddleware:
    def __init__(
        self,
        *,
        rules: list[RateLimitRule] | None = None,
        key_extractor: Callable[[Request], str] = ip_key_extractor,
    ):
```

```python
@dataclass
class RateLimitRule:
    path_pattern: str
    max_requests: int
    window_seconds: int
    methods: list[str] | None = None  # None = all
```

Key extractors:

```python
def ip_key_extractor(request): ...
def api_key_extractor(request): ...
def user_key_extractor(request): ...
```

### `StaticMiddleware`

!!! abstract "`aquilia.middleware_ext.StaticMiddleware`"

Production-grade static file serving with radix trie, ETag, and range requests.

```python
class StaticMiddleware:
    def __init__(
        self,
        *,
        directory: str | Path,
        url_prefix: str = "/static",
        max_age: int = 3600,
        cache_control: str | None = None,
        index_files: list[str] | None = None,  # ["index.html"]
    ):
```

### `SessionMiddleware`

```python
class SessionMiddleware:
    async def __call__(self, request: Request, ctx: RequestCtx, next: Handler) -> Response:
```

### `RequestScopeMiddleware`

```python
class RequestScopeMiddleware:
    """Creates request-scoped DI container."""
    async def __call__(self, request: Request, ctx: RequestCtx, next: Handler) -> Response:
```

### `EffectMiddleware`

```python
class EffectMiddleware:
    """Auto-acquires/releases per-request effects."""
    async def __call__(self, request: Request, ctx: RequestCtx, next: Handler) -> Response:
```

### `FlowContextMiddleware`

```python
class FlowContextMiddleware:
    """Creates FlowContext and binds to request scope."""
    async def __call__(self, request: Request, ctx: RequestCtx, next: Handler) -> Response:
```

---

## Auth Middleware

### `AquilAuthMiddleware`

!!! abstract "`aquilia.auth.integration.middleware`"

Wires authentication into the request lifecycle. Extracts tokens, resolves identity, and attaches to `ctx.identity`, `ctx.auth`.

```python
class AquilAuthMiddleware:
    def __init__(self, auth_manager: AuthManager): ...
    async def __call__(self, request: Request, ctx: RequestCtx, next: Handler) -> Response:
```

---

## Custom Middleware

### Function-Based

```python
from aquilia.response import Response
from aquilia.request import Request

async def custom_logger(
    request: Request,
    ctx: RequestCtx,
    next: Handler,
) -> Response:
    start = time.monotonic()
    response = await next(request, ctx)
    elapsed = time.monotonic() - start

    if isinstance(response, Response):
        response.headers["X-Elapsed-Ms"] = str(int(elapsed * 1000))

    return response

# Register
stack.add(custom_logger, scope="global", priority=70, name="CustomLogger")
```

### Class-Based

```python
class ApiVersionMiddleware:
    def __init__(self, default_version: str = "v1"):
        self.default_version = default_version

    async def __call__(
        self,
        request: Request,
        ctx: RequestCtx,
        next: Handler,
    ) -> Response:
        version = request.headers.get("Accept-Version", self.default_version)
        ctx.state["api_version"] = version

        response = await next(request, ctx)
        response.headers["X-API-Version"] = version
        return response

stack.add(ApiVersionMiddleware("v2"), scope="global", priority=25)
```

### Short-Circuit Example

```python
async def maintenance_mode(
    request: Request,
    ctx: RequestCtx,
    next: Handler,
) -> Response:
    if os.environ.get("MAINTENANCE_MODE") == "1":
        return Response.json({"error": "Maintenance mode"}, status=503)
    return await next(request, ctx)
```

---

## Middleware Scopes

| Scope | Value Pattern | When Applied |
|---|---|---|
| Global | `"global"` | Every request |
| App | `"app:myapp"` | Specific app only |
| Controller | `"controller:Users"` | Specific controller |
| Route | `"route:/users/{id}"` | Specific route pattern |

---

## Typical Middleware Stack

```python
stack = MiddlewareStack()

# Essential (low priority = runs first)
stack.add(RequestIdMiddleware(), scope="global", priority=10)
stack.add(ExceptionMiddleware(debug=True), scope="global", priority=20)

# Connection / proxy
stack.add(ProxyFixMiddleware(trusted_proxies=["10.0.0.1"]), scope="global", priority=25)

# Security
stack.add(CORSMiddleware(allow_origins=["*.example.com"]), scope="global", priority=30)
stack.add(CSPMiddleware(), scope="global", priority=31)
stack.add(CSRFMiddleware(), scope="global", priority=32)
stack.add(HSTSMiddleware(), scope="global", priority=33)

# DI / Scope
stack.add(RequestScopeMiddleware(), scope="global", priority=35)

# Auth
stack.add(AquilAuthMiddleware(auth_manager), scope="global", priority=40)

# Observability
stack.add(LoggingMiddleware(), scope="global", priority=60)

# Compression (runs last on outer wrappers)
stack.add(CompressionMiddleware(), scope="global", priority=70)
```