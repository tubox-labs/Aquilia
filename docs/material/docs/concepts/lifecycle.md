# Application Lifecycle

Aquilia manages application state through a well-defined lifecycle with explicit phases, hooks, and coordination across all modules. Every phase is observable, and failures are handled gracefully with rollback support.

## Lifecycle State Machine

```mermaid
stateDiagram-v2
    [*] --> CREATED
    CREATED --> CONFIGURING : configure()
    CONFIGURING --> DISCOVERING : discover()
    DISCOVERING --> BOOTSTRAPPING : bootstrap()
    BOOTSTRAPPING --> READY : server construction complete
    READY --> RUNNING : ASGI lifespan startup
    RUNNING --> SHUTTING_DOWN : ASGI lifespan shutdown / signal
    SHUTTING_DOWN --> STOPPED : all resources released

    CONFIGURING --> FAILED : config error
    DISCOVERING --> FAILED : manifest import error
    BOOTSTRAPPING --> FAILED : registry / DI error
    RUNNING --> FAILED : unrecoverable runtime error

    note right of RUNNING : Requests are being served
    note right of READY : App constructed but not accepting requests
    note right of SHUTTING_DOWN : Draining in-flight requests
```

## Runtime Phases

### CREATED

The initial state. No configuration has been loaded, no modules discovered. The runtime is a blank slate.

### CONFIGURING

`configure()` loads environment variables, sets up logging, imports `workspace.py`, and loads configuration via `ConfigLoader`. This phase verifies that the workspace file exists and is valid before proceeding.

```
AQUILIA_WORKSPACE=/app → workspace.py found → ConfigLoader merges .env + AQ_* vars
```

### DISCOVERING

`discover()` imports module manifests, resolves component references, performs dynamic module discovery, and rebuilds namespace configuration. Every `ComponentRef` with a `"module.path:ClassName"` format is validated for importability.

### BOOTSTRAPPING

`bootstrap()` constructs `AquiliaServer` with the compiled registry, builds DI containers, creates the lifecycle coordinator, initializes the middleware stack, compiles controller routes, and prepares the ASGI adapter.

### READY

The server is fully constructed and validated. The ASGI application exists but the lifespan startup event has not yet been received. Routes are compiled and middleware is built.

### RUNNING

The ASGI lifespan `startup` event has been received. `AquiliaServer.startup()` has executed all `on_startup` hooks. Requests are being accepted and served.

### SHUTTING_DOWN

The ASGI lifespan `shutdown` event was received OR a `SIGTERM`/`SIGINT` signal was caught. New requests are rejected. In-flight requests are drained up to a configurable grace period. `on_shutdown` hooks execute in reverse dependency order.

### STOPPED

All resources are released. DI containers are disposed. Database connections are closed. Cache connections are terminated. The process is ready to exit.

### FAILED

An unrecoverable error occurred. The runtime logs the failure with full context and transitions to this terminal state.

## ASGI Lifespan Protocol

```mermaid
sequenceDiagram
    participant PM as Process Manager<br/>(uvicorn/gunicorn)
    participant ASGI as ASGIAdapter
    participant S as AquiliaServer
    participant LC as LifecycleCoordinator
    participant DI as DI Containers
    participant Sub as Subsystems
    participant CR as ControllerRouter

    PM->>ASGI: lifespan.startup
    ASGI->>S: startup()
    activate S

    rect rgb(230, 240, 255)
        Note over S,LC: Phase 1: Lifecycle Hooks
        S->>LC: execute_startup()
        LC->>LC: Resolve dependency order
        LC->>LC: Run on_startup hooks
        LC-->>S: All hooks complete
    end

    rect rgb(230, 255, 230)
        Note over S,DI: Phase 2: DI Setup
        S->>DI: Build app containers
        DI->>DI: Register providers
        DI->>DI: Validate scopes
        DI-->>S: Containers ready
    end

    rect rgb(255, 245, 230)
        Note over S,Sub: Phase 3: Subsystem Initialization
        S->>Sub: Connect database
        S->>Sub: Start cache backend
        S->>Sub: Initialize storage
        S->>Sub: Start task workers
        S->>Sub: Start mail transport
        S->>Sub: Initialize effects
        Sub-->>S: All subsystems healthy
    end

    rect rgb(255, 230, 245)
        Note over S,CR: Phase 4: Route Compilation
        S->>CR: Load controller classes
        S->>CR: Compile route decorators
        S->>CR: Build segment trie
        S->>CR: Register admin/docs routes
        CR-->>S: Routes compiled
    end

    deactivate S
    ASGI-->>PM: lifespan.startup.complete

    Note over PM,ASGI: --- Server is RUNNING, handling requests ---

    PM->>ASGI: lifespan.shutdown
    ASGI->>S: graceful_shutdown()

    rect rgb(245, 230, 230)
        Note over S,ASGI: Shutdown Sequence
        S->>S: Stop accepting new requests
        S->>S: Drain in-flight requests (timeout)
        S->>LC: execute_shutdown() (reverse order)
        S->>Sub: Shutdown tasks, mail, cache, storage
        S->>DI: Dispose containers
    end

    ASGI-->>PM: lifespan.shutdown.complete
```

## Lifecycle Hooks

Lifecycle hooks allow modules to execute startup and shutdown logic. Hooks execute in **dependency order** on startup and **reverse dependency order** on shutdown.

```mermaid
flowchart TD
    subgraph Startup["Startup Order"]
        direction TB
        S1["Module A on_startup<br/>(no dependencies)"]
        S2["Module B on_startup<br/>(depends on A)"]
        S3["Module C on_startup<br/>(depends on A, B)"]
        S1 --> S2
        S2 --> S3
    end

    subgraph Shutdown["Shutdown Order (Reverse)"]
        direction TB
        SH1["Module C on_shutdown"]
        SH2["Module B on_shutdown"]
        SH3["Module A on_shutdown"]
        SH1 --> SH2
        SH2 --> SH3
    end
```

### Defining Hooks in Manifests

```python
# modules/database/manifest.py
manifest = AppManifest(
    name="database",
    on_startup="modules.database.lifecycle:setup_pool",
    on_shutdown="modules.database.lifecycle:teardown_pool",
)

# modules/database/lifecycle.py
async def setup_pool(app):
    app.state.db_pool = await create_pool(app.config.get("database.url"))
    logger.info("Database pool created")

async def teardown_pool(app):
    await app.state.db_pool.close()
    logger.info("Database pool closed")
```

### Hooks via Decorators

```python
from aquilia.lifecycle import on_startup, on_shutdown

@on_startup
async def initialize_cache(app):
    app.state.cache = await create_cache_client(app.config.get("cache.url"))

@on_shutdown
async def close_cache(app):
    await app.state.cache.close()
```

### Hook Execution Guarantees

| Guarantee | Description |
|---|---|
| **Dependency order** | Hooks from dependent modules run after their dependencies' hooks on startup |
| **Reverse order** | Shutdown runs in reverse dependency order |
| **Error isolation** | One hook failing does not prevent others from running (errors are collected) |
| **Rollback** | If a startup hook fails, already-executed hooks are rolled back |
| **Timeout** | Hooks have a configurable timeout (default 30s) |
| **Observability** | Hook execution is traced with OpenTelemetry spans |

## Request-Scoped Lifecycle

Individual requests have their own lifecycle within the running server:

```mermaid
sequenceDiagram
    participant ASGI as ASGIAdapter
    participant MW as Middleware Stack
    participant DI as Request DI Container
    participant CTX as RequestCtx Pool
    participant CE as Controller Engine
    participant EF as Effect System

    ASGI->>ASGI: Receive HTTP scope

    rect rgb(230, 240, 255)
        Note over ASGI,DI: Request Setup
        ASGI->>DI: Create request-scoped container
        DI->>DI: Clone from app container
        DI->>DI: Register request-scoped providers
        ASGI->>CTX: acquire() pooled RequestCtx
        CTX->>CTX: Reset fields in-place
        CTX-->>ASGI: RequestCtx ready
    end

    rect rgb(255, 245, 230)
        Note over ASGI,EF: Middleware + Handler Pipeline
        ASGI->>MW: Execute middleware chain
        MW->>MW: Global → App → Controller → Route
        MW->>CE: ControllerEngine.execute()
        CE->>EF: Acquire declared effects
        EF-->>CE: Resources ready
        CE->>CE: Execute controller method
        CE->>EF: Release effects
        CE-->>MW: Response
        MW-->>ASGI: Response
    end

    rect rgb(230, 255, 230)
        Note over ASGI,CTX: Request Teardown
        ASGI->>ASGI: Record metrics
        ASGI->>CTX: release() RequestCtx
        ASGI->>DI: Dispose request container
        ASGI->>ASGI: Send ASGI response events
    end
```

## Health & Liveness

The built-in `/_health` endpoint provides liveness, readiness, and subsystem status:

```json
{
    "status": "healthy",
    "uptime": 3600.5,
    "version": "1.1.0",
    "subsystems": {
        "database": {"status": "healthy", "latency_ms": 2.3},
        "cache": {"status": "healthy", "latency_ms": 0.8},
        "storage": {"status": "healthy", "latency_ms": 5.1},
        "tasks": {"status": "healthy", "workers": 4},
        "mail": {"status": "healthy"},
        "effects": {"status": "healthy", "registered": 12}
    },
    "metrics": {
        "requests_total": 15042,
        "requests_active": 3,
        "avg_response_time_ms": 12.4,
        "error_rate": 0.001
    }
}
```

### Health Status States

```mermaid
flowchart LR
    HEALTHY["Healthy<br/>All checks pass"] --> DEGRADED["Degraded<br/>Non-critical failure"]
    HEALTHY --> UNHEALTHY["Unhealthy<br/>Critical failure"]
    UNHEALTHY --> HEALTHY["Recovery"]
    DEGRADED --> HEALTHY["Recovery"]
    DEGRADED --> UNHEALTHY["Escalation"]
```

## Lifecycle Events

The `LifecycleCoordinator` emits events at every phase transition. These are consumed by logging, metrics, and the health registry:

```python
from aquilia.lifecycle import LifecyclePhase, LifecycleEvent

# Events emitted during lifecycle:
# LifecyclePhase.INIT      → "Initializing..."
# LifecyclePhase.STARTING  → "Starting module: users"
# LifecyclePhase.READY     → "Server ready on :8000"
# LifecyclePhase.STOPPING  → "Shutting down..."
# LifecyclePhase.STOPPED   → "Server stopped"
# LifecyclePhase.ERROR     → "Startup failed: ..."
```

## Subsystem Lifecycle Integration

```mermaid
flowchart TD
    STARTUP["startup()"] --> CHECKS["Pre-startup Checks"]

    CHECKS --> DB["Database<br/>connect + validate migrations"]
    CHECKS --> CACHE["Cache<br/>connect + ping"]
    CHECKS --> STORAGE["Storage<br/>connect + verify bucket"]
    CHECKS --> TASKS["Tasks<br/>start workers + schedules"]
    CHECKS --> MAIL["Mail<br/>verify transport"]
    CHECKS --> EFFECTS["Effects<br/>initialize providers"]

    DB --> HEALTH["Health Registry<br/>Register statuses"]
    CACHE --> HEALTH
    STORAGE --> HEALTH
    TASKS --> HEALTH
    MAIL --> HEALTH
    EFFECTS --> HEALTH

    HEALTH --> ACCEPT["Begin accepting requests"]

    SHUTDOWN["shutdown()"] --> DRAIN["Drain in-flight"]
    DRAIN --> SD_TASKS["Stop task workers"]
    SD_TASKS --> SD_MAIL["Close mail transport"]
    SD_MAIL --> SD_CACHE["Close cache connections"]
    SD_CACHE --> SD_STORAGE["Close storage connections"]
    SD_STORAGE --> SD_DB["Disconnect databases"]
    SD_DB --> SD_DI["Dispose DI containers"]
```

## Graceful Shutdown

```mermaid
sequenceDiagram
    participant SIG as Signal Handler
    participant S as AquiliaServer
    participant LB as Load Balancer
    participant R as In-Flight Requests

    SIG->>S: SIGTERM / SIGINT
    activate S

    S->>S: Set _accepting = False
    S->>LB: Start failing health checks
    LB->>LB: Stop routing new traffic

    S->>S: Wait for in-flight requests
    loop While _inflight_requests > 0
        S->>R: Drain requests
        R-->>S: Requests complete
    end

    alt Timeout reached
        S->>R: Force-close remaining connections
    end

    S->>S: Run on_shutdown hooks
    S->>S: Dispose all resources
    S-->>SIG: Ready to exit
    deactivate S
```

The graceful shutdown period is configurable:

```python
# workspace.py
workspace = (
    Workspace("myapp", version="1.0.0")
    .runtime(
        shutdown_timeout=30,  # seconds to drain requests
        shutdown_grace=5,     # seconds after health check fails
    )
)
```