# Flow Pipeline

> `aquilia.flow` — Typed, composable request pipeline system

The Flow system provides typed, ordered, composable request pipelines inspired by Effect-TS. Each pipeline stage declares its required effects (DB, Cache, Queue, etc.), which are automatically acquired before execution and released afterward.

## Architecture

```
Guard → Transform → Handler → Hook
```

| Stage | Purpose | Execution Phase |
|---|---|---|
| **Guard** | Authentication, authorization, rate limiting | Before transform |
| **Transform** | Input validation, data shaping | Before handler |
| **Handler** | Business logic, the actual request handler | Core execution |
| **Hook** | Logging, audit, cleanup | After handler |

## Key Types

### FlowNode

```python
class FlowNode:
    """A typed callable unit in a pipeline."""
    func: Callable           # The actual async function
    node_type: FlowNodeType  # GUARD, TRANSFORM, HANDLER, HOOK
    priority: int            # Execution order within the stage
    required_effects: set[str]  # Effect dependencies
    metadata: dict           # Arbitrary node metadata
```

### FlowNodeType

```python
class FlowNodeType(str, Enum):
    GUARD = "guard"         # Auth/security checks
    TRANSFORM = "transform" # Data transformation
    HANDLER = "handler"     # Business logic
    HOOK = "hook"           # Post-processing side effects
    EFFECT = "effect"       # Effect lifecycle management
    MIDDLEWARE = "middleware"  # Inline middleware
```

### FlowContext

```python
class FlowContext:
    """Typed context threaded through the entire pipeline."""
    request: Any            # The HTTP request
    response: Any           # The response being built
    state: dict             # Mutable pipeline state
    effects: dict           # Acquired effect instances
    metadata: dict          # Pipeline metadata
    correlation_id: str     # Request tracing ID
```

### FlowPipeline

```python
class FlowPipeline:
    """Composable pipeline builder and executor."""
    
    def guard(self, func, priority=50, effects=None): ...
    def transform(self, func, priority=50, effects=None): ...
    def handler(self, func, priority=50, effects=None): ...
    def hook(self, func, priority=50, effects=None): ...
    async def execute(self, context: FlowContext) -> FlowResult: ...
```

### FlowResult

```python
class FlowResult:
    status: FlowStatus      # SUCCESS, GUARDED, ERROR, TIMEOUT, CANCELLED
    context: FlowContext    # The execution context (may be modified)
    error: Exception | None  # Error if status is ERROR
    output: Any             # Handler output (response)
```

### FlowStatus

```python
class FlowStatus(str, Enum):
    SUCCESS = "success"
    GUARDED = "guarded"     # Guard short-circuited
    ERROR = "error"         # Unhandled exception
    TIMEOUT = "timeout"     # Pipeline timed out
    CANCELLED = "cancelled" # Pipeline was cancelled
```

## Priority Bands

```python
PRIORITY_CRITICAL  = 10   # Security guards, rate limiting
PRIORITY_AUTH      = 20   # Authentication / authorization
PRIORITY_VALIDATE  = 30   # Input validation, schema checks
PRIORITY_TRANSFORM = 40   # Data transformation
PRIORITY_DEFAULT   = 50   # Standard handlers
PRIORITY_ENRICH    = 60   # Response enrichment
PRIORITY_LOG       = 70   # Logging, audit hooks
PRIORITY_CLEANUP   = 80   # Cleanup hooks
```

## Decorators

### `@requires`

Declares effect dependencies on handlers and nodes:

```python
from aquilia import requires

@requires("db", "cache")
async def my_handler(ctx: FlowContext):
    db = ctx.effects["db"]
    cache = ctx.effects["cache"]
    # Effects are automatically acquired before this runs
    # and released after
```

### `@guard`

```python
from aquilia import guard

@guard(priority=PRIORITY_AUTH)
async def auth_guard(ctx: FlowContext):
    if not ctx.state.get("authenticated"):
        raise UnauthorizedFault()
```

### `@transform`

```python
from aquilia import transform

@transform(priority=PRIORITY_VALIDATE)
async def validate_input(ctx: FlowContext, body: dict):
    # Validate and transform input
    ctx.state["validated"] = validate_schema(body)
```

### `@handler`

```python
from aquilia import handler

@handler
async def process_order(ctx: FlowContext):
    order = ctx.state["validated"]
    result = await create_order(order)
    ctx.response = {"order_id": result.id}
```

### `@hook`

```python
from aquilia import hook

@hook(priority=PRIORITY_LOG)
async def audit_hook(ctx: FlowContext):
    logger.info(f"Request completed: {ctx.correlation_id}")
```

## Pipeline Composition

```python
from aquilia.flow import pipeline, FlowPipeline

# Build a pipeline
my_pipeline = pipeline("order_creation",
    guard("auth", auth_check, priority=PRIORITY_AUTH),
    transform("validate", validate_order, priority=PRIORITY_VALIDATE),
    handler("process", create_order_handler),
    hook("audit", log_order, priority=PRIORITY_LOG),
    hook("notify", send_notification, priority=PRIORITY_CLEANUP),
)

# Execute
result: FlowResult = await my_pipeline.execute(context)
if result.status == FlowStatus.SUCCESS:
    return result.output
```

## Layer System (Effect-TS Pattern)

```python
from aquilia.flow import Layer, LayerComposition

# Layers compose effect providers
db_layer = Layer("database", provide_db_pool)
cache_layer = Layer("cache", provide_cache)
http_layer = Layer("http", provide_http_client)

# Compose layers into a single application layer
app_layer = LayerComposition(db_layer + cache_layer + http_layer)

# Effects from all layers are available in the pipeline
```

## Integration with Controllers

Flow pipelines integrate directly with controller route decorators:

```python
from aquilia import Controller, POST

class OrderController(Controller):
    @POST("/orders", pipeline=order_pipeline)
    async def create_order(self, ctx):
        # The pipeline executes BEFORE this handler
        # ctx.state contains validated data from transform nodes
        return Response.json({"ok": True})
```

## Related

- [Middleware](middleware.md) — Global middleware vs per-route flow pipelines
- [Effects](effects.md) — Effect providers declared by flow nodes
- [Auth](../auth/index.md) — Auth guards as flow guard nodes