# Faults Module

> `aquilia.faults` — Structured error handling with fault domains

The Faults module replaces raw exceptions with a typed, structured error system. Every framework-domain error is a `Fault` subclass with a stable `code`, `message`, `domain`, and `severity`. The `FaultEngine` maps faults to HTTP responses, retries recoverable errors, and integrates with middleware.

## When to Use

Use the Faults module when you need:

- Structured error responses instead of raw exceptions
- Context-aware error handling with recovery strategies
- Consistent error codes across your application
- Middleware that converts faults to HTTP responses
- Tracing and debugging via fault domains

## Key Classes

| Class | Purpose |
|---|---|
| `Fault` | Base class for all framework errors |
| `FaultDomain` | Enum of error domains (SECURITY, IO, ROUTING, etc.) |
| `Severity` | Error severity levels (INFO, WARNING, ERROR, CRITICAL) |
| `RecoveryStrategy` | How to handle the fault (PROPAGATE, RETRY, FALLBACK) |
| `FaultEngine` | Maps faults to responses with recovery logic |
| `FaultHandler` | Custom handler for specific fault types |
| `FaultContext` | Contextual information for a fault |

## Quick Example

```python
from aquilia.faults import Fault, FaultDomain, Severity

# Raise a structured fault
class UserNotFoundFault(Fault):
    code = "USR-001"
    message = "User not found"
    domain = FaultDomain.SYSTEM
    severity = Severity.ERROR

raise UserNotFoundFault(detail="User ID 42 does not exist")

# Catch and handle
try:
    await get_user(user_id)
except UserNotFoundFault as f:
    # f.code → "USR-001"
    # f.domain → FaultDomain.SYSTEM
    # f.severity → Severity.ERROR
    return Response.json({"error": f.to_dict()}, status=404)
```

## Built-in Faults (selected)

| Fault | Domain | Purpose |
|---|---|---|
| `NotFoundFault` | ROUTING | Resource not found |
| `UnauthorizedFault` | SECURITY | Authentication required |
| `ForbiddenFault` | SECURITY | Insufficient permissions |
| `ValidationFault` | ROUTING | Request validation failure |
| `DatabaseConnectionFault` | IO | Database connection error |
| `ModelNotFoundFault` | MODEL | ORM record not found |
| `CacheConnectionFault` | CACHE | Cache backend unavailable |
| `MigrationConflictFault` | SYSTEM | Conflicting migrations |
| `ConfigInvalidFault` | CONFIG | Invalid configuration |
| `ManifestInvalidFault` | REGISTRY | Invalid manifest |

## Import Path

```python
from aquilia.faults import (
    Fault,
    FaultDomain,
    FaultEngine,
    FaultHandler,
    FaultContext,
    RecoveryStrategy,
    NotFoundFault,
    UnauthorizedFault,
    ForbiddenFault,
    ValidationFault,
    DatabaseConnectionFault,
)
```

## Related Modules

- [core/middleware](../core/middleware.md) — Exception/Fault middleware
- [core/server](../core/server.md) — FaultEngine configured during boot
- [debug](../debug/index.md) — Debug pages render faults in dev mode