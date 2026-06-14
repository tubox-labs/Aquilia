# Health Registry

The Health Registry provides centralized subsystem health tracking, enabling graceful degradation and health endpoint support for load balancers and monitoring systems.

## SubsystemStatus

```python
class SubsystemStatus(str, Enum):
    """Status of a subsystem."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    STARTING = "starting"
    STOPPED = "stopped"
```

---

## HealthStatus

```python
@dataclass
class HealthStatus:
    """Health status for a single subsystem."""

    name: str
    status: SubsystemStatus = SubsystemStatus.UNKNOWN
    latency_ms: float = 0.0
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        """Serialize for JSON response."""
        return {
            "name": self.name,
            "status": self.status.value,
            "latency_ms": round(self.latency_ms, 2),
            "message": self.message,
            "checked_at": self.checked_at.isoformat(),
        }
```

---

## HealthRegistry

```python
class HealthRegistry:
    """
    Centralized health tracking for all subsystems.

    Subsystems register their health during startup and can update
    it at any time. The registry provides an aggregate health status
    suitable for load balancer health checks.
    """

    def __init__(self):
        self._statuses: dict[str, HealthStatus] = {}
        self._checks: dict[str, Callable[[], HealthStatus]] = {}
```

### Methods

#### Registration and Updates

```python
def register(self, name: str, status: HealthStatus) -> None:
    """Register or update a subsystem's health status."""

def register_check(self, name: str, check: Callable[[], HealthStatus]) -> None:
    """Register a health check function for periodic evaluation."""

def update(self, name: str, status: SubsystemStatus, message: str = "") -> None:
    """Update an existing subsystem's status.

    If the subsystem doesn't exist yet, it is created with the given status.
    The checked_at timestamp is updated to now.
    """
```

#### Queries

```python
def get(self, name: str) -> HealthStatus | None:
    """Get a specific subsystem's health status."""

@property
def all_statuses(self) -> dict[str, HealthStatus]:
    """Get all registered health statuses."""
```

#### Aggregate Health

```python
def overall(self) -> HealthStatus:
    """
    Compute aggregate health across all subsystems.

    Rules:
    - If any subsystem is UNHEALTHY → overall UNHEALTHY
    - If any subsystem is DEGRADED → overall DEGRADED
    - Otherwise → HEALTHY
    - If no subsystems registered → UNKNOWN
    """
```

#### Serialization

```python
def to_dict(self) -> dict:
    """Serialize full health report for /health endpoint.

    Returns:
        {
            "status": "healthy",
            "message": "All 5 subsystems healthy",
            "checked_at": "2025-01-15T10:30:00+00:00",
            "subsystems": {
                "database": {
                    "name": "database",
                    "status": "healthy",
                    "latency_ms": 2.5,
                    "message": "",
                    "checked_at": "2025-01-15T10:30:00+00:00"
                },
                ...
            }
        }
    """
```

#### Running Checks

```python
async def run_checks(self) -> dict[str, HealthStatus]:
    """
    Run all registered health checks and update statuses.

    For each registered check function:
    1. Calls the check (supports both sync and async functions)
    2. Records latency in latency_ms
    3. On exception, marks the subsystem as UNHEALTHY with the exception message
    4. Updates self._statuses with results

    Returns:
        Dict of {name: HealthStatus} for all checked subsystems.
    """
```

---

## Integration with /_health Endpoint

The `ASGIAdapter._serve_health()` method uses the `HealthRegistry` (if attached to the server) to include subsystem health in the response:

```json
{
    "status": "healthy",
    "metrics": {
        "inflight": 3,
        "total_requests": 15000,
        "mean_latency_ms": 12.5
    },
    "subsystems": {
        "database": {"name": "database", "status": "healthy", ...},
        "cache": {"name": "cache", "status": "healthy", ...},
        "storage": {"name": "storage", "status": "degraded", "message": "High latency", ...}
    }
}
```

If any subsystem is unhealthy, the overall `status` degrades from `"healthy"` to `"degraded"` or `"unhealthy"`.

---

## Usage Examples

### Registering Subsystem Health

```python
from aquilia.health import HealthRegistry, HealthStatus, SubsystemStatus

registry = HealthRegistry()

# Register with pre-built status
db_status = HealthStatus(
    name="database",
    status=SubsystemStatus.HEALTHY,
    message="Connected to PostgreSQL 16",
    details={"pool_size": 20, "active_connections": 3},
)
registry.register("database", db_status)

# Register a check function
def check_cache() -> HealthStatus:
    try:
        redis.ping()
        return HealthStatus(
            name="cache",
            status=SubsystemStatus.HEALTHY,
            message="Redis connected",
        )
    except Exception as e:
        return HealthStatus(
            name="cache",
            status=SubsystemStatus.UNHEALTHY,
            message=str(e),
        )

registry.register_check("cache", check_cache)

# Run all checks periodically
await registry.run_checks()

# Get aggregate status
overall = registry.overall()
print(f"Server: {overall.status.value}")

# Update a subsystem status directly
registry.update("database", SubsystemStatus.DEGRADED, "Connection pool at 95%")
```

### Integration with Server

```python
# In AquiliaServer setup:
server.health_registry = registry

# The ASGI adapter's /_health endpoint will automatically pick this up
```

### Custom Health Check (async)

```python
async def check_storage() -> HealthStatus:
    import time
    start = time.monotonic()
    try:
        # Check storage backend
        await storage_client.list_buckets()
        return HealthStatus(
            name="storage",
            status=SubsystemStatus.HEALTHY,
        )
    except Exception as e:
        return HealthStatus(
            name="storage",
            status=SubsystemStatus.UNHEALTHY,
            message=str(e),
        )

registry.register_check("storage", check_storage)

# run_checks() detects coroutine functions automatically
results = await registry.run_checks()
```