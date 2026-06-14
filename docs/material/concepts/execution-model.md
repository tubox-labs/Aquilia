# Execution Model

Aquilia's execution model is **fully asynchronous** from the ASGI socket to the controller response. This page details how requests flow through the system, how concurrency is managed, and how each subsystem participates in request processing.

## Async Architecture

```mermaid
flowchart TD
    subgraph EventLoop["asyncio Event Loop"]
        direction TB

        subgraph Protocol["ASGI Protocol"]
            HTTP_S["HTTP Scopes"]
            WS_S["WebSocket Scopes"]
            LS_S["Lifespan Scopes"]
        end

        subgraph Adapter["ASGIAdapter"]
            DISPATCH["scope dispatch<br/>__call__()"]
        end

        subgraph Pipeline["Request Pipeline"]
            MW_C["Middleware Chain<br/>async callables"]
            ROUTE["Route Matching<br/>sync O(1)/O(k)"]
            CE["Controller Engine<br/>async execution"]
        end

        subgraph Effects["Effect System"]
            DB_P["Database<br/>async connection pool"]
            CACHE_P["Cache<br/>async Redis/Memory"]
            HTTP_P["HTTP<br/>async client pool"]
            QUEUE_P["Queue<br/>async message broker"]
        end

        subgraph DI["Dependency Injection"]
            SINGLETON["Singleton scope<br/>process-lifetime"]
            APP_S["App scope<br/>module-lifetime"]
            REQ_S["Request scope<br/>request-lifetime"]
        end
    end

    Protocol --> Adapter
    Adapter --> Pipeline
    Pipeline --> Effects
    Pipeline --> DI
```

## Request Pipeline (Detailed)

```mermaid
sequenceDiagram
    participant UV as uvicorn
    participant ASGI as ASGIAdapter
    participant REQ as Request
    participant RTR as ControllerRouter
    participant DI as DI Container
    participant CTX as RequestCtx Pool
    participant MW as MiddlewareStack
    participant CE as ControllerEngine
    participant EFX as Effect System
    participant RESP as Response

    UV->>ASGI: send http.request events
    Note over ASGI: handle_http()

    ASGI->>ASGI: Check /_health fast path
    ASGI->>REQ: Wrap ASGI scope + receive

    ASGI->>RTR: match_sync(method, path)
    Note over RTR: Static: O(1) dict<br/>Dynamic: O(k) trie<br/>Complex: regex fallback
    RTR-->>ASGI: ControllerRouteMatch

    ASGI->>DI: create_request_scope()
    DI->>DI: Clone from app container
    DI->>DI: Register request providers
    DI-->>ASGI: Request container

    ASGI->>CTX: acquire()
    Note over CTX: Reset fields in-place<br/>No heap allocation
    CTX-->>ASGI: RequestCtx

    ASGI->>MW: Execute chain
    Note over MW: Global → App → Controller → Route

    MW->>CE: ControllerEngine.execute(route, ctx)
    activate CE

    CE->>EFX: acquire effects
    Note over EFX: @requires effects resolved
    CE->>CE: Resolve controller params via DI
    CE->>CE: Execute controller method
    CE-->>CE: result / fault

    alt Success
        CE-->>MW: Response
    else Fault raised
        MW->>MW: FaultMiddleware catches
        MW-->>MW: Map to HTTP response
    end

    deactivate CE

    MW-->>ASGI: Response

    ASGI->>ASGI: Record engine metrics
    ASGI->>CTX: release()
    ASGI->>DI: Dispose request container
    ASGI->>RESP: send_asgi()
    RESP->>UV: http.response.start + body
```

## DI Resolution Model

```mermaid
flowchart TD
    RESOLVE["Resolve request"] --> CHECK_SCOPE{"Check scope<br/>validity"}
    CHECK_SCOPE -->|Request scope<br/>accessing singleton| ALLOW["Allowed"]
    CHECK_SCOPE -->|Singleton scope<br/>accessing request| DENY["REJECT<br/>ScopeViolationError"]

    ALLOW --> CACHEHIT{"Cached in<br/>current scope?"}
    CACHEHIT -->|Yes| RETURN_CACHED["Return cached instance"]
    CACHEHIT -->|No| FIND_PROVIDER["Lookup provider"]

    FIND_PROVIDER --> RESOLVE_DEPS["Resolve dependencies<br/>(recursive)"]
    RESOLVE_DEPS --> INSTANTIATE["Instantiate class<br/>or call factory"]
    INSTANTIATE --> CACHE["Cache in scope"]
    CACHE --> RETURN["Return instance"]
```

### Scope Rules

| Parent Scope | Can Resolve From | Example |
|---|---|---|
| `request` | `request`, `app`, `singleton` | Controller constructor can inject an `app`-scoped repo |
| `app` | `app`, `singleton` | An `app`-scoped service can inject a `singleton`-scoped pool |
| `singleton` | `singleton` only | A singleton cannot depend on request-scoped providers |

Attempting to resolve a narrower scope from a wider scope raises `ScopeViolationError`:

```python
# This will fail at startup:
@service(scope="singleton")
class BadService:
    def __init__(self, request_metrics: RequestMetrics):  # RequestMetrics is request-scoped!
        ...
# Error: ScopeViolationError: singleton cannot depend on request-scoped provider
```

## Middleware Execution Chain

```mermaid
flowchart LR
    subgraph "Request →"
        direction LR
        MW1["FaultMiddleware<br/>Priority: 0, Global"]
        MW2["RequestScopeMiddleware<br/>Priority: 1, Global"]
        MW3["SecurityMiddleware<br/>Priority: 10, Global"]
        MW4["SessionMiddleware<br/>Priority: 20, Global"]
        MW5["AuthMiddleware<br/>Priority: 30, Global"]
        MW6["Custom App MW<br/>Priority: 150, app:users"]
        MW7["Controller MW<br/>Priority: 250, controller:Admin"]
        MW8["Route MW<br/>Priority: 350, route:/secure"]
    end

    subgraph "← Response"
        direction RL
        MW8R["Route MW<br/>post-processing"]
        MW7R["Controller MW<br/>post-processing"]
        MW6R["Custom App MW<br/>post-processing"]
        MW5R["AuthMiddleware<br/>post-processing"]
        MW4R["SessionMiddleware<br/>post-processing"]
        MW3R["SecurityMiddleware<br/>post-processing"]
        MW2R["RequestScopeMiddleware<br/>dispose scope"]
        MW1R["FaultMiddleware<br/>catch faults"]
    end

    MW1 --> MW2 --> MW3 --> MW4 --> MW5 --> MW6 --> MW7 --> MW8 --> HANDLER["Controller Handler"]
    HANDLER --> MW8R --> MW7R --> MW6R --> MW5R --> MW4R --> MW3R --> MW2R --> MW1R
```

### Middleware Function Signature

Every middleware follows the onion pattern:

```python
from aquilia.request import Request
from aquilia.response import Response
from aquilia.middleware import Handler

async def my_middleware(request: Request, next_handler: Handler) -> Response:
    # Pre-processing (before the handler)
    print(f"→ {request.method} {request.url.path}")

    # Call the next middleware or the final controller handler
    response = await next_handler(request)

    # Post-processing (after the handler)
    print(f"← {response.status}")

    return response
```

### Fast Path Optimization

For latency-sensitive routes, `build_fast_handler()` constructs a minimal middleware chain that skips non-essential middleware (Logging, Timeout):

```python
@GET("/health-check")
async def health_check(self, ctx: RequestCtx):
    return Response.json({"status": "ok"})
```

## Concurrency Model

```mermaid
flowchart TD
    subgraph Server["Aquilia Server"]
        EVENT_LOOP["asyncio Event Loop"]
    end

    subgraph Workers["ASGI Workers"]
        W1["Worker 1<br/>Event Loop"]
        W2["Worker 2<br/>Event Loop"]
        W3["Worker N<br/>Event Loop"]
    end

    subgraph Tasks["Concurrent Tasks"]
        T1["Request Handler A<br/>coroutine"]
        T2["Request Handler B<br/>coroutine"]
        T3["Request Handler C<br/>coroutine"]
        T4["Background Task<br/>coroutine"]
        T5["WebSocket Handler<br/>coroutine"]
    end

    subgraph ThreadPool["Thread Pool<br/>(blocking I/O offload)"]
        TP1["gzip.compress()"]
        TP2["bcrypt.hash()"]
        TP3["File stat() on NFS"]
    end

    W1 --> T1
    W1 --> T2
    W2 --> T3
    W2 --> T4
    W3 --> T5

    T1 -.->|blocking call| TP1
    T3 -.->|blocking call| TP2
```

### Concurrency Key Points

1. **One event loop per worker** — Each ASGI worker runs its own asyncio event loop. Multiple workers provide process-level parallelism.

2. **Cooperative concurrency** — All framework code uses `await` for I/O. There are no blocking calls on the event loop. Heavy CPU work should be offloaded.

3. **Blocking I/O offload** — The `CompressionMiddleware` offloads `gzip.compress()` to a thread pool via `loop.run_in_executor()` to avoid event loop stalls.

4. **No shared mutable state** — The `singleton` scope is process-local (not shared across workers). Request-scoped state is strictly per-request.

5. **In-flight tracking** — `EngineMetrics` tracks active request count for graceful shutdown draining.

## Effect Resolution

```mermaid
sequenceDiagram
    participant Handler as Controller Handler
    participant Pipeline as FlowPipeline
    participant Registry as EffectRegistry
    participant Scope as EffectScope
    participant Provider as EffectProvider

    Handler->>Pipeline: Execute handler
    Pipeline->>Pipeline: Inspect @requires annotations

    loop For each declared effect
        Pipeline->>Registry: Resolve provider for Effect(name, mode)
        Registry->>Scope: Get or create scope
        Scope->>Provider: acquire(effect)
        Provider-->>Scope: Resource handle
        Scope-->>Registry: Resource
        Registry-->>Pipeline: Resource
    end

    Pipeline->>Pipeline: Inject resources as handler kwargs
    Pipeline->>Handler: Call handler(db=conn, cache=client)

    Handler-->>Pipeline: Result

    loop For each acquired effect (reverse)
        Pipeline->>Registry: Release effect
        Registry->>Scope: release(effect, resource)
        Scope->>Provider: release(effect, resource)
        Provider-->>Scope: Done
    end
```

### Effect Lifecycle

```python
from aquilia.effects import EffectProvider, Effect

class DatabaseProvider(EffectProvider):
    async def acquire(self, effect: Effect):
        # Called before the handler executes
        conn = await self.pool.acquire()
        await conn.begin()
        return conn

    async def release(self, effect: Effect, resource):
        # Called after the handler returns (or raises)
        try:
            await resource.commit()
        except Exception:
            await resource.rollback()
        finally:
            await self.pool.release(resource)
```

## Route Matching Performance

```mermaid
flowchart TD
    PATH["Incoming path<br/>(e.g., /users/42/profile)"] --> NORMALIZE["Normalize path<br/>(strip trailing slashes, lowercase)"]

    NORMALIZE --> CHECK_STATIC{"Static route<br/>dict lookup?"}
    CHECK_STATIC -->|"GET /users"| STATIC_HIT["O(1)<br/>Dict lookup by method"]
    CHECK_STATIC -->|Dynamic path| TRIE["Segment Trie<br/>Split by '/'"]

    STATIC_HIT --> MATCH["Route + params"]

    TRIE --> SEG1["Segment: 'users'"]
    SEG1 --> SEG2["Segment: ':id'"]
    SEG2 --> CAST["Cast '42' → int<br/>(inline, no regex)"]
    SEG2 --> SEG3["Segment: 'profile'"]
    SEG3 --> TERMINAL["Terminal node<br/>with CompiledRoute"]
    TERMINAL --> MATCH["Route + params"]

    TRIE -.->|"Unmatchable pattern<br/>(e.g., {file}.{ext})"| REGEX["Regex fallback<br/>(compiled at registration)"]
    REGEX --> MATCH
```

### Trie Structure

```
/users                              → static node (GET, POST, PUT)
    /:id                            → param node
        /profile                    → static node (GET)
        /orders                     → static node (GET)
    /search                         → static node (GET)
    /export                         → static node (POST)
/products                           → static node (GET)
    /:slug                          → param node (GET)
```

Static routes (`/users`, `/products`) use `O(1)` dict lookups keyed by HTTP method. Dynamic routes (`/users/42/profile`) walk `O(k)` trie segments where `k` is the path depth (typically 2–4 for REST APIs).

## Content Negotiation & Serialization

```mermaid
flowchart LR
    REQ["Request<br/>Accept: application/json"] --> NEG["ContentNegotiator"]

    NEG --> CHECK{"Available<br/>renderers?"}
    CHECK --> JSON["JSONRenderer<br/>application/json"]
    CHECK --> XML["XMLRenderer<br/>application/xml"]
    CHECK --> YAML["YAMLRenderer<br/>application/x-yaml"]
    CHECK --> HTML["HTMLRenderer<br/>text/html"]
    CHECK --> MSGPACK["MessagePackRenderer<br/>application/msgpack"]

    JSON --> RENDER["Render response"]
    XML --> RENDER
    YAML --> RENDER
    HTML --> RENDER
    MSGPACK --> RENDER

    RENDER --> RESP["Response<br/>Content-Type header set"]
```

Controllers can specify preferred renderers:

```python
class APIController(Controller):
    prefix = "/api"
    __renderers__ = [JSONRenderer(), XMLRenderer()]

    @GET("/data")
    async def get_data(self, ctx: RequestCtx):
        data = await self.service.fetch()
        return data  # Renderer serializes based on Accept header
```

## Error Handling Flow

```mermaid
flowchart TD
    ERROR["Exception raised<br/>in handler"] --> CHECK_TYPE{"Is it a Fault?"}

    CHECK_TYPE -->|Yes| FAULT_MW["FaultMiddleware"]
    CHECK_TYPE -->|No| WRAP["Wrap in InternalFault<br/>(hide details in prod)"]
    WRAP --> FAULT_MW

    FAULT_MW --> LOG["Log with trace_id, domain, severity"]
    FAULT_MW --> MAP["Map to HTTP status"]
    FAULT_MW --> FORMAT{"Client format?"}

    FORMAT -->|Accept: application/json| JSON["JSON error body"]
    FORMAT -->|Accept: text/html| HTML["Debug/error HTML page"]
    FORMAT -->|Other| JSON

    JSON --> STATUS["Status code<br/>400, 401, 403, 404, 422, 500, 503"]

    HTML --> STATUS
    STATUS --> RESP["Send response"]
```

### Fault to HTTP Status Mapping

| Fault Domain | Default Status | Overridable |
|---|---|---|
| `config` | 500 | No (server error) |
| `registry` | 500 | No (server error) |
| `di` | 500 | No (server error) |
| `routing` | 404 | Yes (per fault code) |
| `flow` | 403 / 500 | Yes |
| `effect` | 503 | Yes |
| `security` | 401 / 403 | Yes |
| `http` | 400 / 415 / 422 | Yes |
| `model` | 500 | Yes |
| `io` | 500 | Yes |

## Metrics & Observability

The execution model is instrumented throughout:

```python
from aquilia.engine import get_engine_metrics

metrics = get_engine_metrics()
# {
#     "requests_total": 15042,
#     "requests_active": 3,
#     "responses_2xx": 14800,
#     "responses_4xx": 200,
#     "responses_5xx": 42,
#     "avg_response_time_ms": 12.4,
#     "p50_ms": 8.2,
#     "p95_ms": 34.7,
#     "p99_ms": 120.3,
# }
```

OpenTelemetry integration provides distributed tracing across the entire execution path:

- **Span per request** — HTTP method, path, status code
- **Span per middleware** — Timing for each middleware layer
- **Span per DI resolution** — Provider lookup and instantiation
- **Span per effect** — Acquire/release timing
- **Span per DB query** — Query text and timing (parameterized, no data leakage)