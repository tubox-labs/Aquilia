# Flow Pipeline

## Overview

The **Flow Pipeline** system provides typed, composable request pipelines with automatic effect management. Inspired by Effect-TS, each pipeline is a chain of nodes (guards → transforms → handler → hooks) executed in priority order with declared effect dependencies auto-acquired and released.

---

## Enums & Constants

### `FlowNodeType`

```python
class FlowNodeType(str, Enum):
    GUARD = "guard"           # Auth, rate limiting — can short-circuit
    TRANSFORM = "transform"   # Data transformation, validation
    HANDLER = "handler"       # Core business logic
    HOOK = "hook"             # Post-handler hooks (logging, audit)
    EFFECT = "effect"         # Resource acquisition/release
    MIDDLEWARE = "middleware"  # Pipeline-level middleware
```

### `FlowStatus`

```python
class FlowStatus(str, Enum):
    SUCCESS = "success"
    GUARDED = "guarded"       # Guard short-circuited
    ERROR = "error"           # Unhandled exception
    TIMEOUT = "timeout"       # Pipeline timed out
    CANCELLED = "cancelled"   # Pipeline was cancelled
```

### Priority Band Constants

```python
PRIORITY_CRITICAL  = 10    # Security guards, rate limiting
PRIORITY_AUTH      = 20    # Authentication / authorization
PRIORITY_VALIDATE  = 30    # Input validation, schema checks
PRIORITY_TRANSFORM = 40    # Data transformation
PRIORITY_DEFAULT   = 50    # Standard handlers
PRIORITY_ENRICH    = 60    # Response enrichment
PRIORITY_LOG       = 70    # Logging, audit hooks
PRIORITY_CLEANUP   = 80    # Cleanup hooks
```

---

## `FlowContext`

!!! abstract "`aquilia.flow.FlowContext`"
    `__slots__`-optimized

```python
class FlowContext:
    __slots__ = (
        "request", "container", "state", "identity",
        "session", "effects", "metadata", "_cleanup", "_started_at",
    )

    def __init__(
        self,
        request: Any = None,
        container: Any = None,
        *,
        state: dict[str, Any] | None = None,
        identity: Any = None,
        session: Any = None,
    ) -> None:
```

### Properties

| Property/Slot | Type | Description |
|---|---|---|
| `request` | `Any` | ASGI request object |
| `container` | `Any` | DI container |
| `state` | `dict[str, Any]` | Arbitrary mutable state |
| `identity` | `Any` | Authenticated identity |
| `session` | `Any` | Session object |
| `effects` | `dict[str, Any]` | Acquired effect resources |
| `metadata` | `dict[str, Any]` | Pipeline metadata (`node_trace`, `timings`, `acquired_effects`) |
| `elapsed_ms` | `float` (property) | Milliseconds since context creation |

### Effect Access

```python
def get_effect(self, name: str) -> Any:
    """Get an acquired effect. Raises EffectFault if not acquired."""

def has_effect(self, name: str) -> bool:
    """Check if effect is acquired."""
```

### State Shortcuts

```python
def get(self, key: str, default: Any = None) -> Any:
    """Get state value with default."""

def set(self, key: str, value: Any) -> None:
    """Set state value."""

def __getitem__(self, key: str) -> Any: ...
def __setitem__(self, key: str, value: Any) -> None: ...
def __contains__(self, key: str) -> bool: ...
```

### Cleanup

```python
def add_cleanup(self, callback: Callable[[], Awaitable[None]]) -> None:
    """Register a cleanup callback (LIFO execution)."""

async def dispose(self) -> None:
    """Run all cleanup callbacks in LIFO order."""
```

---

## `FlowNode`

!!! abstract "`aquilia.flow.FlowNode`"
    Dataclass

```python
@dataclass
class FlowNode:
    type: FlowNodeType
    callable: Callable[..., Any]
    name: str
    priority: int = PRIORITY_DEFAULT
    effects: list[str] = field(default_factory=list)
    condition: Callable[[FlowContext], bool] | None = None
    timeout: float | None = None
```

Auto-extracts `__flow_effects__` from the callable (set by `@requires`).

---

## `FlowResult`

!!! abstract "`aquilia.flow.FlowResult`"
    Discriminated union of pipeline outcomes.

```python
@dataclass
class FlowResult:
    status: FlowStatus
    value: Any = None
    context: FlowContext | None = None
    error: Exception | None = None
    guard: FlowNode | None = None           # The guard that short-circuited
    timings: dict[str, float] = field(default_factory=dict)

    @property
    def is_success(self) -> bool: ...
    @property
    def is_guarded(self) -> bool: ...
```

---

## `FlowError`

```python
class FlowError(Exception):
    def __init__(
        self,
        message: str,
        *,
        node: FlowNode | None = None,
        context: FlowContext | None = None,
        cause: Exception | None = None,
    ):
```

---

## `FlowPipeline`

!!! abstract "`aquilia.flow.FlowPipeline`"

The main pipeline builder and executor.

```python
class FlowPipeline:
    def __init__(self, name: str = "pipeline", *, timeout: float | None = None):
        self.name = name
        self.timeout = timeout
        self._nodes: list[FlowNode] = []
```

### Builder API

All builder methods return `self` for chaining.

```python
def guard(
    self,
    callable_or_node: Callable | FlowNode,
    *,
    name: str | None = None,
    priority: int = PRIORITY_AUTH,
    effects: list[str] | None = None,
    condition: Callable | None = None,
) -> FlowPipeline:
    """Add a guard node. Guards can short-circuit the pipeline."""

def transform(
    self,
    callable_or_node: Callable | FlowNode,
    *,
    name: str | None = None,
    priority: int = PRIORITY_TRANSFORM,
    effects: list[str] | None = None,
) -> FlowPipeline:
    """Add a transform node. Modifies context/request data."""

def handler(
    self,
    callable_or_node: Callable | FlowNode,
    *,
    name: str | None = None,
    priority: int = PRIORITY_DEFAULT,
    effects: list[str] | None = None,
) -> FlowPipeline:
    """Set the handler node (core business logic)."""

def hook(
    self,
    callable_or_node: Callable | FlowNode,
    *,
    name: str | None = None,
    priority: int = PRIORITY_LOG,
    effects: list[str] | None = None,
) -> FlowPipeline:
    """Add a post-handler hook."""

def effect(
    self,
    callable_or_node: Callable | FlowNode,
    *,
    name: str | None = None,
    priority: int = PRIORITY_DEFAULT - 5,
    effects: list[str] | None = None,
) -> FlowPipeline:
    """Add an effect node (resource management)."""

def middleware(
    self,
    callable_or_node: Callable | FlowNode,
    *,
    name: str | None = None,
    priority: int = PRIORITY_CRITICAL,
) -> FlowPipeline:
    """Add a middleware node (wraps entire pipeline)."""

def add_node(self, node: FlowNode) -> FlowPipeline: ...
def add_nodes(self, nodes: Sequence[FlowNode]) -> FlowPipeline: ...
```

### Composition

```python
def compose(self, *other: FlowPipeline) -> FlowPipeline:
    """Merge nodes from multiple pipelines, re-sorted by priority."""

def __or__(self, other: FlowPipeline) -> FlowPipeline:
    """Pipeline composition via ``|`` operator."""
```

```python
user_pipeline = auth_pipeline | validation_pipeline | handler_pipeline
```

### Execution

```python
async def execute(
    self,
    context: FlowContext,
    effect_registry: EffectRegistry | None = None,
) -> FlowResult:
```

Effect lifecycle during execution:

1. Collect all declared effects from all nodes
2. Acquire effects before the first node that needs them
3. Inject into `FlowContext.effects`
4. Execute nodes in priority order (guards → transforms → handler → hooks)
5. Guards return `False` → short-circuit with `FlowStatus.GUARDED`
6. Release effects (`success=True` on success, `False` on error)
7. Run cleanup callbacks (`ctx.dispose()`)

---

## `@requires` Decorator

```python
def requires(*effect_names: str) -> Callable:
    """Declare effect dependencies on a handler or flow node."""
```

Works on controller methods, flow node callables, and standalone async functions.

```python
@requires("DBTx", "Cache")
async def create_user(ctx: FlowContext):
    db = ctx.get_effect("DBTx")
    cache = ctx.get_effect("Cache")
    user_id = await db.create_user(...)
    await cache.set(f"user:{user_id}", ...)
    return user_id
```

Effect names are collected via `__flow_effects__` attribute and auto-extracted by `FlowNode`.

### Helper

```python
def get_required_effects(func: Callable) -> list[str]:
    """Extract declared effect requirements from a callable."""
```

---

## `Layer` and `LayerComposition`

Effect constructors separated from usage (Effect-TS pattern).

### `Layer`

```python
@dataclass
class Layer:
    name: str
    factory: Callable[..., Any]       # (...deps) -> EffectProvider
    deps: list[str] = field(default_factory=list)
    scope: str = "app"                # "app" | "request"

    async def build(self, resolved_deps: dict[str, Any]) -> Any: ...

    @staticmethod
    def merge(*layers: Layer) -> LayerComposition: ...

    @staticmethod
    def provide(layer: Layer, *providers: Layer) -> LayerComposition: ...
```

```python
db_layer = Layer(
    name="DBTx",
    factory=lambda cfg: DBTxProvider(cfg.database_url),
    deps=["Config"],
)

cache_layer = Layer(
    name="Cache",
    factory=lambda cfg: CacheProvider("redis"),
    deps=["Config"],
)

app_layer = Layer.merge(db_layer, cache_layer)
```

### `LayerComposition`

```python
@dataclass
class LayerComposition:
    layers: list[Layer]

    async def build_all(
        self,
        initial_deps: dict[str, Any] | None = None,
    ) -> dict[str, Any]: ...

    async def register_with(
        self,
        registry: EffectRegistry,
        initial_deps: dict[str, Any] | None = None,
    ) -> None: ...
```

Topological sort resolves layers in dependency order; detects circular dependencies.

---

## `EffectScope`

```python
class EffectScope:
    """Scoped lifecycle manager for effects."""
    def __init__(self, registry: EffectRegistry): ...
    async def acquire(self, name: str) -> Any: ...
    async def release_all(self, success: bool = True) -> None: ...
```

---

## Factory Functions

```python
def pipeline(name: str = "pipeline", *, timeout: float | None = None) -> FlowPipeline:
    """Create a new FlowPipeline."""

def guard(
    callable_or_node: Callable | FlowNode,
    *, name=None, priority=PRIORITY_AUTH, effects=None, condition=None,
) -> FlowNode: ...

def transform(
    callable_or_node: Callable | FlowNode,
    *, name=None, priority=PRIORITY_TRANSFORM, effects=None,
) -> FlowNode: ...

def handler(
    callable_or_node: Callable | FlowNode,
    *, name=None, priority=PRIORITY_DEFAULT, effects=None,
) -> FlowNode: ...

def hook(
    callable_or_node: Callable | FlowNode,
    *, name=None, priority=PRIORITY_LOG, effects=None,
) -> FlowNode: ...
```

---

## Full Example

```python
from aquilia.flow import (
    FlowPipeline, FlowContext, FlowResult, FlowStatus,
    requires, pipeline, guard, transform, handler, hook,
    PRIORITY_AUTH, PRIORITY_VALIDATE, PRIORITY_DEFAULT,
)

# ── Define nodes ──────────────────────────────────────────────

async def auth_guard(ctx: FlowContext) -> bool:
    """Return False to short-circuit."""
    token = ctx.state.get("token")
    if not token:
        ctx.state["auth_error"] = "No token"
        return False
    ctx.identity = await verify_token(token)
    return True

@requires("DBTx")
async def validate_input(ctx: FlowContext):
    data = ctx.state.get("raw_input", {})
    if not data.get("email"):
        raise FlowError("Email is required")
    ctx.state["validated"] = data

@requires("DBTx", "Cache")
async def create_user_handler(ctx: FlowContext):
    db = ctx.get_effect("DBTx")
    cache = ctx.get_effect("Cache")
    data = ctx.state["validated"]
    user = await db.create_user(data)
    await cache.set(f"user:{user['id']}", user, ttl=3600)
    return user

async def audit_hook(ctx: FlowContext):
    logger.info("User created by %s", ctx.identity.get("id"))

# ── Build pipeline ────────────────────────────────────────────

create_user_pipe = (
    FlowPipeline("create_user", timeout=30.0)
    .guard(auth_guard, priority=PRIORITY_AUTH, name="AuthGate")
    .transform(validate_input, priority=PRIORITY_VALIDATE, name="ValidateInput")
    .handler(create_user_handler, priority=PRIORITY_DEFAULT, name="CreateUser")
    .hook(audit_hook, name="AuditLog")
)

# ── Compose with another pipeline ─────────────────────────────

notify_pipe = (
    FlowPipeline("notify")
    .hook(send_welcome_email, name="WelcomeEmail")
    .hook(update_analytics, name="Analytics")
)

full_pipe = create_user_pipe | notify_pipe

# ── Execute ───────────────────────────────────────────────────

ctx = FlowContext(request=req, container=di_container)
ctx.state["token"] = req.headers.get("Authorization")
ctx.state["raw_input"] = await req.json()

result: FlowResult = await full_pipe.execute(ctx, effect_registry)

if result.is_success:
    return Response.json(result.value, status=201)
elif result.is_guarded:
    return Response.json({"error": ctx.state["auth_error"]}, status=401)
else:
    # ERROR / TIMEOUT / CANCELLED
    return Response.json({"error": str(result.error)}, status=500)
```

### Controller-Level Usage

```python
class UsersController(Controller):
    prefix = "/users"

    @POST("/", pipeline=[
        guard(auth_guard, priority=PRIORITY_AUTH),
        transform(validate_input, priority=PRIORITY_VALIDATE),
    ])
    async def create_user(self, ctx: RequestCtx):
        ...
```