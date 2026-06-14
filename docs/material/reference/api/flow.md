# Flow Pipeline

The Flow system provides typed, ordered, composable request pipelines inspired by Effect-TS. Each pipeline stage can declare required effects (DB, Cache, Queue, etc.) which are automatically acquired before execution and released after.

## Concepts

```
Guard → Transform → Handler → Hook
```

- **Guard**: Can short-circuit the pipeline (auth, rate limiting). Returns `False` or a `Response` to stop.
- **Transform**: Modifies context/request data. Can return a new `FlowContext` or dict to merge into state.
- **Handler**: Core business logic. Only one per pipeline.
- **Hook**: Post-handler hooks (audit, logging). Errors are non-fatal.
- **Effect**: Manages resource acquisition (middleware integration).
- **Middleware**: Wraps the entire pipeline.

---

## FlowNodeType

```python
class FlowNodeType(str, Enum):
    GUARD = "guard"
    TRANSFORM = "transform"
    HANDLER = "handler"
    HOOK = "hook"
    EFFECT = "effect"
    MIDDLEWARE = "middleware"
```

---

## FlowStatus

```python
class FlowStatus(str, Enum):
    SUCCESS = "success"        # Pipeline completed successfully
    GUARDED = "guarded"        # Guard short-circuited
    ERROR = "error"            # Unhandled exception
    TIMEOUT = "timeout"        # Pipeline timed out
    CANCELLED = "cancelled"    # Pipeline was cancelled
```

---

## Priority Bands

```python
PRIORITY_CRITICAL = 10   # Security guards, rate limiting
PRIORITY_AUTH = 20       # Authentication / authorization
PRIORITY_VALIDATE = 30   # Input validation, schema checks
PRIORITY_TRANSFORM = 40  # Data transformation
PRIORITY_DEFAULT = 50    # Standard handlers
PRIORITY_ENRICH = 60     # Response enrichment
PRIORITY_LOG = 70        # Logging, audit hooks
PRIORITY_CLEANUP = 80    # Cleanup hooks
```

---

## FlowContext

```python
class FlowContext:
    """
    Typed execution context threaded through the entire flow pipeline.

    Carries request data, identity, acquired effects, and arbitrary state.
    Each pipeline node receives this context and may read/modify it.

    Effects are automatically acquired/released by the pipeline executor
    based on @requires() declarations.
    """

    __slots__ = ("request", "container", "state", "identity", "session",
                  "effects", "metadata", "_cleanup", "_started_at")

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

### Attributes

| Attribute | Type | Description |
|---|---|---|
| `request` | `Any` | The ASGI request object |
| `container` | `Any` | DI container scoped to this request |
| `state` | `dict[str, Any]` | Arbitrary key-value state |
| `identity` | `Any` | Authenticated identity (set by auth guards) |
| `session` | `Any` | Session object |
| `effects` | `dict[str, Any]` | Dict of acquired effect resources |
| `metadata` | `dict[str, Any]` | Pipeline metadata (timing, node trace) |

### Effect Access

```python
def get_effect(self, name: str) -> Any:
    """Get an acquired effect resource. Raises EffectFault if not acquired."""

def has_effect(self, name: str) -> bool:
    """Check if an effect resource is currently acquired."""
```

### State Methods

```python
def get(self, key: str, default: Any = None) -> Any: ...
def set(self, key: str, value: Any) -> None: ...
def __getitem__(self, key: str) -> Any: ...
def __setitem__(self, key: str, value: Any) -> None: ...
def __contains__(self, key: str) -> bool: ...
```

### Cleanup

```python
def add_cleanup(self, callback: Callable[[], Awaitable[None]]) -> None:
    """Register a cleanup callback (LIFO execution order)."""

async def dispose(self) -> None:
    """Run all cleanup callbacks in LIFO order."""
```

### Timing

```python
@property
def elapsed_ms(self) -> float:
    """Time since context creation in milliseconds."""
```

---

## FlowNode

```python
@dataclass
class FlowNode:
    """
    A typed unit in a flow pipeline.
    """

    type: FlowNodeType
    callable: Callable[..., Any]
    name: str
    priority: int = PRIORITY_DEFAULT
    effects: list[str] = field(default_factory=list)
    condition: Callable[[FlowContext], bool] | None = None
    timeout: float | None = None
```

| Attribute | Type | Description |
|---|---|---|
| `type` | `FlowNodeType` | Node type |
| `callable` | `Callable` | The async callable to execute |
| `name` | `str` | Human-readable name for tracing |
| `priority` | `int` | Execution order (lower = earlier) |
| `effects` | `list[str]` | Effect names this node requires |
| `condition` | `Callable \| None` | Optional predicate |
| `timeout` | `float \| None` | Per-node timeout in seconds |

Auto-extracts `@requires` declared effects from the callable during `__post_init__`.

---

## FlowResult

```python
@dataclass
class FlowResult:
    """
    Result of a flow pipeline execution.
    """

    status: FlowStatus
    value: Any = None
    context: FlowContext | None = None
    error: Exception | None = None
    guard: FlowNode | None = None
    timings: dict[str, float] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        return self.status == FlowStatus.SUCCESS

    @property
    def is_guarded(self) -> bool:
        return self.status == FlowStatus.GUARDED
```

---

## FlowPipeline

```python
class FlowPipeline:
    """
    Composable, typed request pipeline with automatic effect management.

    Builds and executes a chain of FlowNodes in priority order:
        Guards → Transforms → Handler → Hooks
    """

    def __init__(self, name: str = "pipeline", *, timeout: float | None = None):
```

### Builder Methods

All builder methods return `self` for chaining.

```python
def guard(self, callable_or_node, *, name=None, priority=PRIORITY_AUTH,
          effects=None, condition=None) -> FlowPipeline:
    """Add a guard node. Guards can short-circuit the pipeline."""

def transform(self, callable_or_node, *, name=None, priority=PRIORITY_TRANSFORM,
              effects=None) -> FlowPipeline:
    """Add a transform node. Transforms modify context/request data."""

def handler(self, callable_or_node, *, name=None, priority=PRIORITY_DEFAULT,
            effects=None) -> FlowPipeline:
    """Set the handler node. Core business logic."""

def hook(self, callable_or_node, *, name=None, priority=PRIORITY_LOG,
         effects=None) -> FlowPipeline:
    """Add a post-handler hook. Runs after the handler."""

def effect(self, callable_or_node, *, name=None, priority=PRIORITY_DEFAULT - 5,
           effects=None) -> FlowPipeline:
    """Add an effect node. Manages resource acquisition."""

def middleware(self, callable_or_node, *, name=None, priority=PRIORITY_CRITICAL) -> FlowPipeline:
    """Add a middleware node. Wraps the entire pipeline."""

def add_node(self, node: FlowNode) -> FlowPipeline:
    """Add a pre-built FlowNode."""

def add_nodes(self, nodes: Sequence[FlowNode]) -> FlowPipeline:
    """Add multiple pre-built FlowNodes."""
```

### Composition

```python
def compose(self, *other: FlowPipeline) -> FlowPipeline:
    """Compose this pipeline with others. Merges and re-sorts nodes by priority."""

def __or__(self, other: FlowPipeline) -> FlowPipeline:
    """Pipeline composition via | operator."""
```

### Execution

```python
async def execute(
    self,
    context: FlowContext,
    effect_registry: EffectRegistry | None = None,
) -> FlowResult:
    """
    Execute the pipeline.

    1. Sort nodes by type band, then by priority.
    2. Collect all required effects across all nodes.
    3. Acquire effects and inject into context.
    4. Execute guards (short-circuit on failure).
    5. Execute transforms.
    6. Execute handler.
    7. Execute hooks.
    8. Release effects.
    9. Return FlowResult.
    """

async def execute_with_timeout(
    self,
    context: FlowContext,
    effect_registry: EffectRegistry | None = None,
    timeout: float | None = None,
) -> FlowResult:
    """Execute pipeline with optional per-call timeout."""
```

### Guard Behavior

1. If a guard **raises**, the pipeline returns `GUARDED` status with the exception
2. If a guard **returns `False`**, the pipeline short-circuits with `GUARDED`
3. If a guard **returns a `Response`**, the pipeline short-circuits with `GUARDED` and that response as `value`

### Execution Phases

Nodes execute in this order (each sorted by priority within its type band):

1. **MIDDLEWARE** (priority band 0)
2. **GUARD** (priority band 1)
3. **TRANSFORM** (priority band 2)
4. **EFFECT** (priority band 3)
5. **HANDLER** (priority band 4) — only the first handler executes
6. **HOOK** (priority band 5) — errors are logged but non-fatal

### Effect Lifecycle

```
acquire → execute handlers → release(success=True on success, False on error)
```

If any effect acquisition fails, all previously acquired effects are released and a `FlowError` is raised.

---

## `@requires` Decorator

```python
def requires(*effect_names: str) -> Callable:
    """
    Decorator declaring effect dependencies on a handler or flow node.

    Effects are automatically acquired before execution and released after.

    Example:
        @requires("DBTx", "Cache")
        async def create_user(ctx: FlowContext):
            db = ctx.get_effect("DBTx")
            cache = ctx.get_effect("Cache")
            ...
    """
```

**Works on:**
- Controller methods (effects injected into ctx)
- Flow node callables
- Standalone async functions

### Helper

```python
def get_required_effects(func: Callable) -> list[str]:
    """Extract declared effect requirements from a callable."""
```

---

## Layer System (Effect-TS Pattern)

### `Layer`

```python
@dataclass
class Layer:
    """
    Composable effect layer — separates effect construction from usage.

    - Layers build EffectProviders (construction phase)
    - Layers declare their own dependencies (other layers)
    - Layers are composed via merge and provide
    - The runtime resolves the full dependency graph at startup
    """

    name: str
    factory: Callable[..., Any]  # (...deps) -> EffectProvider
    deps: list[str] = field(default_factory=list)
    scope: str = "app"  # "app" | "request"
```

```python
async def build(self, resolved_deps: dict[str, Any]) -> Any:
    """Build the effect provider using resolved dependencies."""

@staticmethod
def merge(*layers: Layer) -> LayerComposition:
    """Merge multiple layers into a single composition."""

@staticmethod
def provide(layer: Layer, *providers: Layer) -> LayerComposition:
    """Provide dependencies for a layer from other layers."""
```

### `LayerComposition`

```python
@dataclass
class LayerComposition:
    layers: list[Layer]

    async def build_all(self, initial_deps: dict[str, Any] | None = None) -> dict[str, Any]:
        """Build all layers in dependency order."""

    async def register_with(self, registry: EffectRegistry,
                            initial_deps: dict[str, Any] | None = None) -> None:
        """Build all layers and register providers with the registry."""
```

### Example

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
await app_layer.register_with(effect_registry, {"Config": config})
```

---

## Factory Functions

```python
def pipeline(name: str = "pipeline", *, timeout: float | None = None) -> FlowPipeline:
    """Create a new FlowPipeline."""

def guard(fn, *, name=None, priority=PRIORITY_AUTH, effects=None) -> FlowNode:
    """Create a guard FlowNode."""

def transform(fn, *, name=None, priority=PRIORITY_TRANSFORM, effects=None) -> FlowNode:
    """Create a transform FlowNode."""

def handler(fn, *, name=None, priority=PRIORITY_DEFAULT, effects=None) -> FlowNode:
    """Create a handler FlowNode."""

def hook(fn, *, name=None, priority=PRIORITY_LOG, effects=None) -> FlowNode:
    """Create a hook FlowNode."""
```

### `from_pipeline_list()`

```python
def from_pipeline_list(
    nodes: Sequence[Any],
    *,
    name: str = "controller_pipeline",
) -> FlowPipeline:
    """Convert a controller-style pipeline list to a FlowPipeline.

    Handles:
    - FlowNode instances (used directly)
    - Callables (auto-wrapped as guards — legacy behavior)
    - FlowGuard instances
    - Zero-arg factory references (materialized eagerly)
    """
```

Bridges the controller `pipeline=[]` syntax with the full Flow pipeline executor.

---

## Usage Examples

### Standalone Pipeline

```python
pipeline = (
    FlowPipeline("create_user")
    .guard(auth_guard, priority=20)
    .guard(scope_guard("users:write"), priority=25)
    .transform(validate_body)
    .handler(create_user_handler)
    .hook(audit_log)
)

result = await pipeline.execute(flow_context, effect_registry)
```

### Controller Integration

```python
@POST("/users", pipeline=[
    require_auth(),
    require_scopes("users:write"),
    validate_body,
])
async def create_user(self, ctx):
    ...
```

### With Effects

```python
@requires("DBTx", "Cache")
async def create_user(ctx: FlowContext):
    db = ctx.get_effect("DBTx")
    cache = ctx.get_effect("Cache")
    user = await db.users.create(...)
    await cache.set(f"user:{user.id}", user.to_dict())
    return user
```

---

## `FlowError`

```python
class FlowError(Exception):
    """Raised when a flow pipeline encounters an unrecoverable error."""

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

## Smart Argument Injection

When `_call_node` executes a node, it uses signature inspection to inject arguments automatically:

| Parameter Name | Injected Value |
|---|---|
| `context`, `ctx`, `flow_context`, `flow_ctx` | `FlowContext` or dict proxy |
| `request`, `req` | `context.request` |
| `container`, `di` | `context.container` |
| `identity`, `user` | `context.identity` |
| `session` | `context.session` |
| `effects` | `context.effects` |
| `state` | `context.state` |
| `effect_<name>` | `context.get_effect(name)` |

Also resolves **class tokens** (classes in pipeline lists) via the DI container, supporting constructor injection for pipeline nodes.