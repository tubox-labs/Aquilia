# Monitoring Guide

Aquilia provides built-in health checks, OpenTelemetry distributed tracing, and an admin dashboard monitoring page.

## Health checks

The `HealthRegistry` (from `aquilia.health`) tracks subsystem health and provides a `/health` endpoint suitable for load balancers and orchestration.

### Health status model

```python
from aquilia.health import HealthRegistry, HealthStatus, SubsystemStatus

# Subsystem statuses
SubsystemStatus.HEALTHY     # Fully operational
SubsystemStatus.DEGRADED    # Operating but with reduced capability
SubsystemStatus.UNHEALTHY   # Failed or unreachable
SubsystemStatus.UNKNOWN     # Not yet checked
SubsystemStatus.STARTING    # Initialising
SubsystemStatus.STOPPED     # Deliberately stopped
```

### Registering health checks

```python
from aquilia.health import HealthRegistry, HealthStatus, SubsystemStatus

health = HealthRegistry()

# Register a static status
health.register(
    "database",
    HealthStatus(
        name="database",
        status=SubsystemStatus.HEALTHY,
        message="Connected to PostgreSQL 15",
        latency_ms=2.3,
        details={"pool_size": 10, "active": 3},
    ),
)

# Register a callable health check (evaluated on demand)
def check_database() -> HealthStatus:
    import time
    start = time.monotonic()
    try:
        # Run a ping query
        db.execute("SELECT 1")
        return HealthStatus(
            name="database",
            status=SubsystemStatus.HEALTHY,
            latency_ms=(time.monotonic() - start) * 1000,
        )
    except Exception as e:
        return HealthStatus(
            name="database",
            status=SubsystemStatus.UNHEALTHY,
            message=str(e),
        )

health.register_check("database", check_database)

# Async health checks also supported
async def check_redis() -> HealthStatus:
    try:
        await redis.ping()
        return HealthStatus(name="redis", status=SubsystemStatus.HEALTHY)
    except Exception as e:
        return HealthStatus(name="redis", status=SubsystemStatus.UNHEALTHY, message=str(e))

health.register_check("redis", check_redis)
```

### Running checks and getting status

```python
# Run all registered checks
results = await health.run_checks()

# Get overall aggregate health
overall = health.overall()
print(overall.status)    # "healthy" | "degraded" | "unhealthy"

# Get a specific subsystem
db_status = health.get("database")

# Full JSON-serializable report
report = health.to_dict()
# {
#   "status": "healthy",
#   "message": "All 3 subsystems healthy",
#   "checked_at": "2026-06-14T12:00:00Z",
#   "subsystems": {
#     "database": {"name": "database", "status": "healthy", "latency_ms": 2.3, ...},
#     "redis": {"name": "redis", "status": "healthy", "latency_ms": 1.1, ...},
#     "cache": {"name": "cache", "status": "healthy", "latency_ms": 0.5, ...},
#   }
# }
```

### Health endpoint controller

```python
from aquilia import Controller, GET, RequestCtx, Response

class HealthController(Controller):
    prefix = "/_health"

    @GET("/")
    async def health(self, ctx: RequestCtx):
        from aquilia.health import HealthRegistry
        # In production, obtain the registry from DI
        report = health.to_dict()
        status_code = 200 if report["status"] == "healthy" else 503
        return Response.json(report, status=status_code)

    @GET("/ready")
    async def ready(self, ctx: RequestCtx):
        return Response.json({"status": "ready"})
```

### Aggregate health rules

The `overall()` method computes aggregate health:

1. If **any** required subsystem is `UNHEALTHY` → overall `UNHEALTHY`
2. If **any** subsystem is `DEGRADED` → overall `DEGRADED`
3. Otherwise → `HEALTHY`

---

## OpenTelemetry distributed tracing

Aquilia supports OpenTelemetry via the `aquilia.otel` package (requires `pip install aquilia[otel]`).

### Setup

```python
from aquilia import Workspace
from aquilia.otel import OTelConfig

workspace = (
    Workspace("myapp", version="1.0.0")
    .configure_otel(OTelConfig(
        service_name="my-api",
        service_version="1.0.0",
        otlp_endpoint="http://otel-collector:4317",
        trace_all=True,
        propagators=["tracecontext", "baggage"],
        resource_attrs={
            "deployment.environment": "production",
            "service.namespace": "myorg",
        },
    ))
)
```

### OTelConfig fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `service_name` | `str` | `"aquilia-app"` | Service name in traces |
| `service_version` | `str` | `""` | Service version string |
| `otlp_endpoint` | `str \| None` | `None` | OTLP gRPC endpoint. `None` disables export. |
| `trace_all` | `bool` | `True` | Create a span for every request |
| `propagators` | `list[str]` | `["tracecontext", "baggage"]` | Context propagation formats |
| `resource_attrs` | `dict` | `{}` | Extra OTEL resource attributes |

### Automatic instrumentation

When `trace_all=True`, `OTelMiddleware` automatically creates a span for every HTTP and WebSocket request with these attributes:

| Attribute | Source |
|-----------|--------|
| `http.method` | Request method |
| `http.route` | Matched route pattern |
| `http.url` | Full request URL |
| `http.status_code` | Response status |
| `http.user_agent` | User-Agent header |
| `net.host.name` | Server hostname |
| `net.host.port` | Server port |

Errors (status ≥ 500) automatically set span status to `ERROR` and record the exception.

### Manual instrumentation

```python
from aquilia.otel import get_current_span
from aquilia import Controller, GET, RequestCtx

class OrderController(Controller):
    prefix = "/orders"

    @GET("/{id:int}")
    async def get_order(self, ctx: RequestCtx, id: int):
        span = get_current_span()
        span.set_attribute("order.id", id)
        span.set_attribute("order.customer_id", ctx.identity.id)

        # Create child spans
        from aquilia.otel import get_tracer
        tracer = get_tracer()

        with tracer.start_as_current_span("database.fetch_order") as db_span:
            db_span.set_attribute("db.statement", f"SELECT * FROM orders WHERE id={id}")
            order = await self.repo.get(id)

        return Response.json(order.to_dict())
```

### Programmatic setup

For advanced setups outside the workspace builder:

```python
from aquilia.otel import setup, shutdown, get_tracer

# Initialize
setup(OTelConfig(
    service_name="my-worker",
    otlp_endpoint="http://collector:4317",
))

# Get tracer
tracer = get_tracer()

# Use tracer
with tracer.start_as_current_span("custom.operation") as span:
    span.set_attribute("custom.key", "value")
    # Do work...

# Clean shutdown (flushes pending spans)
shutdown()
```

---

## Admin dashboard monitoring

The admin dashboard provides a real-time monitoring page via `AdminIntegration`:

```python
from aquilia.integrations import AdminIntegration, AdminMonitoring, AdminModules

workspace.integrate(
    AdminIntegration(
        site_title="My App Admin",
        modules=AdminModules(monitoring=True),
        monitoring=AdminMonitoring(
            enabled=True,
            metrics=["cpu", "memory", "disk", "network", "process", "python", "system"],
            refresh_interval=15,   # Auto-refresh every 15 seconds
        ),
    )
)
```

Available metrics:

| Metric | Description |
|--------|-------------|
| `cpu` | CPU usage percentage |
| `memory` | RAM usage |
| `disk` | Disk I/O and capacity |
| `network` | Network throughput |
| `process` | Process-level metrics |
| `python` | Python runtime metrics (GC, objects) |
| `system` | OS-level system metrics |
| `health_checks` | Subsystem health status |

Access the monitoring dashboard at `/admin/monitoring/`.

---

## Metric-emitting middleware

The `LoggingMiddleware` (enabled by default) emits timing data:

```python
# Slow request detection (configurable)
from aquilia.integrations import LoggingIntegration

workspace.integrate(
    LoggingIntegration(
        slow_threshold_ms=500.0,  # Log warnings when request exceeds 500ms
        level="INFO",
    )
)
```

Requests exceeding the threshold are logged with `WARNING` level:

```
Slow request: POST /api/orders took 1250.3ms
```

---

## Telemetry configuration

Enable or disable telemetry subsystems at the workspace level:

```python
workspace.telemetry(
    tracing_enabled=True,      # OpenTelemetry
    metrics_enabled=True,      # Health registry
    logging_enabled=True,      # Request logging
)
```