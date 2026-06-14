# Logging Guide

Aquilia provides structured request logging, request ID tracking, and configurable middleware through `LoggingMiddleware` and `RequestIdMiddleware`.

## LoggingMiddleware

`LoggingMiddleware` records the HTTP method, path, status code, and duration for every request:

```python
from aquilia.middleware import LoggingMiddleware
```

The middleware is included by default in the middleware chain with priority 20. It emits at `INFO` level using the `aquilia.requests` logger.

### Log output

```
GET /api/users/ 200 12.3ms
POST /api/orders/ 201 85.7ms
DELETE /api/documents/42 403 2.1ms
```

### Slow request detection

Requests exceeding the configured threshold are logged at `WARNING` level:

```
Slow request: POST /api/orders/import took 2500.8ms
```

The threshold defaults to 1000ms and is configurable:

```python
from aquilia import AquilaConfig

class BaseEnv(AquilaConfig):
    class logging(AquilaConfig.Logging):
        slow_threshold_ms = 500.0
```

Or via the integration dataclass:

```python
from aquilia.integrations import LoggingIntegration

workspace.integrate(
    LoggingIntegration(
        slow_threshold_ms=500.0,
    )
)
```

### Performance

`LoggingMiddleware` checks `logger.isEnabledFor(logging.INFO)` once and skips all formatting work if disabled, ensuring zero overhead when logging is turned off.

---

## Request ID tracking

`RequestIdMiddleware` assigns a unique 32-character hex ID to every request:

```python
from aquilia.middleware import RequestIdMiddleware
```

### Behavior

1. Checks for an incoming `X-Request-ID` header (preserves forwarded IDs from upstream proxies).
2. If absent, generates a new cryptographically random ID using `os.urandom(16)`.
3. Stores the ID in `request.state["request_id"]` and `RequestCtx.request_id`.
4. Adds `X-Request-ID` to every response.

### Accessing the request ID

```python
from aquilia import Controller, GET, RequestCtx

class MyController(Controller):
    @GET("/")
    async def endpoint(self, ctx: RequestCtx):
        request_id = ctx.request_id
        # Or: request_id = ctx.request.state["request_id"]
        ...
```

### Custom header name

```python
# Configure via middleware chain
workspace.middleware(
    MiddlewareChain()
    .use("aquilia.middleware.RequestIdMiddleware", priority=10)
)
```

The header name defaults to `X-Request-ID`. Pass `header_name` to the constructor in custom setups.

---

## ExceptionMiddleware and error logging

`ExceptionMiddleware` catches all exceptions and logs them:

| Error type | Log level | Status code |
|-----------|-----------|-------------|
| `HTTPFault` (5xx) | `ERROR` | 500+ |
| `HTTPFault` (4xx) | `WARNING` | 400-499 |
| `Fault` (5xx) | `ERROR` | 500+ |
| `Fault` (4xx) | `WARNING` | 400-499 |
| Raw `Exception` | `ERROR` | 500 |

The logger is `aquilia.exceptions`.

### Debug HTML error pages

When `debug=True`, the middleware renders beautiful React-style error pages with the Atlas color palette and dark/light mode for browser clients (`Accept: text/html`).

```python
from aquilia import AquilaConfig

class DevEnv(AquilaConfig):
    class server(AquilaConfig.Server):
        debug = True
```

!!! warning
    Never enable `debug=True` in production. Error pages with tracebacks leak internal code structure.

---

## Configuration via LoggingIntegration

The `LoggingIntegration` dataclass provides full control:

```python
from aquilia.integrations import LoggingIntegration

workspace.integrate(
    LoggingIntegration(
        format="%(method)s %(path)s %(status)s %(duration_ms).1fms",
        level="INFO",
        slow_threshold_ms=500.0,
        skip_paths=["/health", "/healthz", "/ready", "/metrics"],
        include_headers=False,
        include_query=True,
        include_user_agent=False,
        log_request_body=False,
        log_response_body=False,
        colorize=True,
        enabled=True,
    )
)
```

| Field | Default | Description |
|-------|---------|-------------|
| `format` | `"%(method)s %(path)s %(status)s %(duration_ms).1fms"` | Log format string |
| `level` | `"INFO"` | Minimum log level |
| `slow_threshold_ms` | `1000.0` | Threshold for slow-request warnings |
| `skip_paths` | `["/health", "/healthz", "/ready", "/metrics"]` | Paths to skip logging |
| `include_headers` | `False` | Include request headers in logs |
| `include_query` | `True` | Include query string |
| `include_user_agent` | `False` | Include User-Agent header |
| `log_request_body` | `False` | Log request bodies |
| `log_response_body` | `False` | Log response bodies |
| `colorize` | `True` | ANSI color in terminal |
| `enabled` | `True` | Enable/disable logging middleware |

---

## Configuring log levels

Set the server log level via `AquilaConfig.Server`:

```python
class server(AquilaConfig.Server):
    log_level = "debug"  # critical | error | warning | info | debug | trace
```

Or via `LoggingIntegration`:

```python
LoggingIntegration(level="DEBUG")
```

### Python logging configuration

Aquilia uses Python's standard `logging` module. Configure root/handler levels using standard methods:

```python
import logging

# Application-level logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# Aquilia-specific loggers
logging.getLogger("aquilia.requests").setLevel(logging.DEBUG)
logging.getLogger("aquilia.exceptions").setLevel(logging.WARNING)
logging.getLogger("aquilia.health").setLevel(logging.INFO)
logging.getLogger("aquilia.otel.middleware").setLevel(logging.DEBUG)
```

### Logger hierarchy

| Logger name | Purpose |
|------------|---------|
| `aquilia.requests` | HTTP request/response logging |
| `aquilia.exceptions` | Error and fault logging |
| `aquilia.health` | Subsystem health checks |
| `aquilia.otel.middleware` | OpenTelemetry tracing |
| `aquilia.controller` | Controller execution |
| `aquilia.controller.validation` | Blueprint validation |
| `aquilia.auth.manager` | Authentication operations |

---

## Structured logging patterns

Use Python's logging extra dict for structured data:

```python
import logging

logger = logging.getLogger("myapp.orders")

# Structured logging
logger.info(
    "Order created",
    extra={
        "order_id": "ord_123",
        "customer_id": "usr_456",
        "amount": 99.95,
    },
)
```

In production, pair with structured log formatters (e.g., `python-json-logger`) for JSON output consumable by log aggregators.

---

## Middleware chain ordering

The default middleware chain and priorities:

| Priority | Middleware | Purpose |
|----------|-----------|---------|
| 1 | `ExceptionMiddleware` | Catch all exceptions first |
| 10 | `RequestIdMiddleware` | Assign request IDs |
| 20 | `LoggingMiddleware` | Log request timing |

Configure your own chain:

```python
from aquilia.integrations import MiddlewareChain

workspace.middleware(
    MiddlewareChain()
    .use("aquilia.middleware.ExceptionMiddleware", priority=1)
    .use("myapp.middleware.AuditMiddleware", priority=5)
    .use("aquilia.middleware.RequestIdMiddleware", priority=10)
    .use("aquilia.middleware.LoggingMiddleware", priority=20)
    .use("aquilia.middleware.CompressionMiddleware", priority=90)
)
```

### Fast-path handler

For latency-sensitive routes, `MiddlewareStack.build_fast_handler()` skips `LoggingMiddleware` and `TimeoutMiddleware` while keeping essential middleware (RequestId, Exception, CORS, Compression).