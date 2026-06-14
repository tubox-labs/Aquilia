# OTel Module

> `aquilia.otel` — OpenTelemetry distributed tracing

The OTel module provides OpenTelemetry integration for distributed tracing, metrics, and logging across synchronous and asynchronous code. It includes a no-op fallback when the OTel SDK is not available.

## When to Use

Use the OTel module when you need:

- Distributed tracing across microservices
- Request latency metrics
- Error rate tracking
- Span enrichment with custom attributes

## Key Classes

| Class | Purpose |
|---|---|
| `OTelConfig` | Configuration for OTel tracing |
| `OTelMiddleware` | Middleware that creates spans per request |

## Quick Example

```python
from aquilia.otel import OTelConfig, OTelMiddleware

config = OTelConfig(
    service_name="my-api",
    exporter_endpoint="http://jaeger:4317",
    sampler_rate=0.1,
)

# The middleware automatically creates spans
# for each HTTP request with method, path, and status code
middleware = OTelMiddleware(config)
```

## Installation

```bash
pip install aquilia[otel]
```

## Import Path

```python
from aquilia.otel import OTelConfig, OTelMiddleware
```

## Related Modules

- [core/middleware](../core/middleware.md) — Middleware chain integration
- [integrations](../integrations/index.md) — Integration configuration