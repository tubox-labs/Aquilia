# Aquilia Fault System

The Fault System provides structured, type-safe error management for Aquilia applications. Instead of relying on bare, unformatted Python exceptions, Aquilia treats errors as first-class structured values called **Faults**. Inheriting from Python's base `Exception` class, every `Fault` is enriched with stable identifiers, severity ratings, classification domains, and recovery strategies.

---

## Core Concepts & Classes

The system relies on four core elements:

1. **Fault Base Class (`Fault`)**:
   Subclasses `Exception` but carries rich metadata. Unlike normal exceptions, it contains stable error codes (e.g. `USER_NOT_FOUND`), human-readable messages, severity levels, domains, and public exposure controls.
2. **Fault Domain (`FaultDomain`)**:
   Groups errors taxonomically by subsystem (e.g. `CONFIG`, `ROUTING`, `DI`, `MODEL`, `CACHE`, `SECURITY`, `HTTP`). Domains establish default severity and retryability behaviors.
3. **Fault Context (`FaultContext`)**:
   Wraps a `Fault` with runtime variables captured during error propagation (e.g. `trace_id`, `request_id`, `app`, `route`, and the original stack trace).
4. **Fault Result (`FaultResult`)**:
   Determines the resolution state of a fault after traversing a handler:
   * `Resolved(response)`: The error was handled; execution stops and returns the response.
   * `Transformed(fault)`: The error was converted to another fault type and continues propagation.
   * `Escalate`: The handler declined to process this fault; it bubbles up to the next handler.

---

## Fault Severity & Recovery Strategies

### Severity Levels (`Severity`)
* `INFO`: Informational, logged but requires no recovery action.
* `WARN`: Warning, indicators of potential issues that should be reviewed.
* `ERROR`: Error, immediate attention needed (default for custom/scoped errors).
* `FATAL` (or `CRITICAL`): Unrecoverable error. Aborts processing immediately.

### Recovery Strategies (`RecoveryStrategy`)
* `PROPAGATE`: Bubble up to the next scope handler.
* `RETRY`: Retry the failed operation (with optional backoff).
* `FALLBACK`: Return a pre-configured fallback value.
* `MASK`: Suppress the error from the response (log it only).
* `CIRCUIT_BREAK`: Trip the circuit breaker for downstream requests.

---

## Fault Lifecycle Execution Flow

For every raised exception or structured fault, the framework coordinates a 6-step lifecycle:

```
[Raised Exception / Fault]
           │
           ▼
     [1. Origin]         ◄─── Exception caught & transformed to Fault
           │
           ▼
   [2. Annotation]       ◄─── Wrapped in FaultContext (trace_id & stack trace)
           │
           ▼
    [3. Emission]        ◄─── Logged & dispatched to event_listeners
           │
           ▼
   [4. Propagation]      ◄─── Routed through: Route ➔ Controller ➔ App ➔ Global
           │
           ▼
    [5. Resolution]      ◄─── Resolved, Transformed, or Escalated
           │
           ▼
     [6. Response]       ◄─── FaultMiddleware serializes to clean JSON HTTP response
```

---

## Workspace Integration: Fault Middleware

Register the `FaultMiddleware` in your `workspace.py` to catch uncaught exceptions, process them, and transform them to clean API responses.

```python
from aquilia.workspace import Workspace
from aquilia.middleware import MiddlewareChain
from aquilia.faults.engine import get_default_engine

app = (
    Workspace.new("my-project")
    .middleware(
        MiddlewareChain.chain()
        .defaults()
        # Binds the global FaultEngine bridge
        .use("aquilia.faults.engine.FaultMiddleware", engine=get_default_engine())
    )
)
```

---

## Practical Code Examples

### 1. Declaring and Raising Structured Faults

Arbitrary keyword arguments passed to the constructor are automatically merged into the `metadata` dictionary:

```python
from aquilia.faults import Fault, FaultDomain, Severity

raise Fault(
    code="OUT_OF_STOCK",
    message="Requested inventory quantity exceeds active stock",
    domain=FaultDomain.MODEL,
    severity=Severity.ERROR,
    public=True,
    product_id="prod_9982",
    requested_qty=5
)
```

### 2. Preserving Causality: Transform Chain (`>>`)

Faults override the right-shift operator (`>>`). This converts a lower-level technical exception (e.g. database connection timeout) to a higher-level public API fault while keeping track of the causal chain under the `_cause` and `_transform_chain` metadata keys:

```python
from sqlite3 import OperationalError
from aquilia.faults.domains import DatabaseFault, ApiFault

try:
    await db.execute("UPDATE accounts SET balance = balance - 100")
except OperationalError as err:
    # Converts DB exception to public API fault, preserving origin logs
    raise DatabaseFault(code="DB_QUERY_FAILED", message=str(err)) >> ApiFault("CHECKOUT_FAILED")
```

### 3. Writing Scoped Fault Handlers

Define custom error handlers and register them with the engine to resolve specific faults:

```python
from aquilia.faults.handlers import FaultHandler
from aquilia.faults.core import FaultContext, FaultResult, Resolved

class ProductOutOfStockHandler(FaultHandler):
    def can_handle(self, ctx: FaultContext) -> bool:
        return ctx.fault.code == "OUT_OF_STOCK"

    async def handle(self, ctx: FaultContext) -> FaultResult:
        # Resolve error cleanly by returning a user-friendly payload
        return Resolved(
            response={
                "error": "INVENTORY_SHORTAGE",
                "message": ctx.fault.message,
                "product_id": ctx.fault.metadata.get("product_id")
            }
        )

# Register with global fault engine
engine = get_default_engine()
engine.register_global(ProductOutOfStockHandler())
```
