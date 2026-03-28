"""
Aquilia Flow -- Typed Pipeline System with Effect Integration.

Inspired by Effect-TS's composable effect architecture, the Flow system
provides typed, ordered, composable request pipelines:

    Guard → Transform → Handler → Hook

Each pipeline stage can declare required effects (DB, Cache, Queue, etc.)
which are automatically acquired before execution and released after.

Architecture:
    FlowNode      -- Typed callable unit (guard, transform, handler, hook)
    FlowContext   -- Typed context threaded through the pipeline
    FlowPipeline  -- Composable pipeline builder and executor
    FlowResult    -- Discriminated union of pipeline outcomes
    FlowError     -- Structured pipeline failure
    @requires     -- Decorator declaring effect dependencies on handlers/nodes
    Layer          -- Composable effect constructor (Effect-TS Layer pattern)

Integration Points:
    - Controller decorators accept ``pipeline=`` for per-route pipelines
    - ControllerEngine executes pipelines via FlowPipeline
    - EffectMiddleware auto-acquires/releases per-request effects
    - Auth guards are FlowNodes (via FlowGuard base class)
    - Subsystem boot wires FlowPipeline into the request lifecycle
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import time
from collections.abc import Awaitable, Callable, Mapping, MutableMapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
)

from .typing.effects import EffectName

if TYPE_CHECKING:
    from .effects import EffectRegistry

logger = logging.getLogger("aquilia.flow")

T = TypeVar("T")
R = TypeVar("R")
E = TypeVar("E")


# ============================================================================
# Enums & Constants
# ============================================================================


class FlowNodeType(str, Enum):
    """Types of nodes in a flow pipeline."""

    GUARD = "guard"
    TRANSFORM = "transform"
    HANDLER = "handler"
    HOOK = "hook"
    EFFECT = "effect"
    MIDDLEWARE = "middleware"


class FlowStatus(str, Enum):
    """Pipeline execution outcome."""

    SUCCESS = "success"
    GUARDED = "guarded"  # Guard short-circuited
    ERROR = "error"  # Unhandled exception
    TIMEOUT = "timeout"  # Pipeline timed out
    CANCELLED = "cancelled"  # Pipeline was cancelled


# Pipeline execution priority bands
PRIORITY_CRITICAL = 10  # Security guards, rate limiting
PRIORITY_AUTH = 20  # Authentication / authorization
PRIORITY_VALIDATE = 30  # Input validation, schema checks
PRIORITY_TRANSFORM = 40  # Data transformation
PRIORITY_DEFAULT = 50  # Standard handlers
PRIORITY_ENRICH = 60  # Response enrichment
PRIORITY_LOG = 70  # Logging, audit hooks
PRIORITY_CLEANUP = 80  # Cleanup hooks


# ============================================================================
# FlowContext -- Typed context threaded through the pipeline
# ============================================================================


class FlowContext:
    """
    Typed execution context threaded through the entire flow pipeline.

    Carries request data, identity, acquired effects, and arbitrary state.
    Each pipeline node receives this context and may read/modify it.

    Effects are automatically acquired/released by the pipeline executor
    based on ``@requires()`` declarations.

    Attributes:
        request:    The ASGI request object.
        container:  DI container scoped to this request.
        state:      Arbitrary key-value state (middleware, guards can add data).
        identity:   Authenticated identity (set by auth guards).
        session:    Session object (if session middleware is active).
        effects:    Dict of acquired effect resources, keyed by effect name.
        metadata:   Pipeline metadata (timing, node trace).
        _cleanup:   LIFO cleanup callbacks (effect releases, etc.).
    """

    __slots__ = (
        "request",
        "container",
        "state",
        "identity",
        "session",
        "effects",
        "metadata",
        "_cleanup",
        "_started_at",
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
        self.request = request
        self.container = container
        self.state: dict[str, Any] = state if state is not None else {}
        self.identity = identity
        self.session = session
        self.effects: dict[str, Any] = {}
        self.metadata: dict[str, Any] = {
            "node_trace": [],
            "timings": {},
            "acquired_effects": [],
        }
        self._cleanup: list[Callable[[], Awaitable[None]]] = []
        self._started_at: float = time.monotonic()

    # -- Effect access shortcuts -------------------------------------------

    def get_effect(self, name: str) -> Any:
        """Get an acquired effect resource by name.

        Raises:
            EffectFault: If the effect has not been acquired.
        """
        if name not in self.effects:
            from .faults.domains import EffectFault

            raise EffectFault(
                code="EFFECT_NOT_ACQUIRED",
                message=(
                    f"Effect '{name}' not acquired. Declare it with @requires('{name}') or add it to the pipeline."
                ),
            )
        return self.effects[name]

    def has_effect(self, name: str) -> bool:
        """Check if an effect resource is currently acquired."""
        return name in self.effects

    # -- State shortcuts ---------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        return self.state.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.state[key] = value

    def __getitem__(self, key: str) -> Any:
        return self.state[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.state[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self.state

    # -- Cleanup -----------------------------------------------------------

    def add_cleanup(self, callback: Callable[[], Awaitable[None]]) -> None:
        """Register a cleanup callback (LIFO execution order)."""
        self._cleanup.append(callback)

    async def dispose(self) -> None:
        """Run all cleanup callbacks in LIFO order."""
        for cb in reversed(self._cleanup):
            try:
                await cb()
            except Exception as exc:
                logger.warning("Flow cleanup error: %s", exc)
        self._cleanup.clear()

    # -- Timing ------------------------------------------------------------

    @property
    def elapsed_ms(self) -> float:
        return (time.monotonic() - self._started_at) * 1000.0

    # -- Dict-like interface for backward compatibility --------------------

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for legacy FlowGuard compatibility."""
        return {
            "request": self.request,
            "container": self.container,
            "identity": self.identity,
            "session": self.session,
            "effects": self.effects,
            **self.state,
        }

    # -- Repr --------------------------------------------------------------

    def __repr__(self) -> str:
        effects = list(self.effects.keys())
        return f"<FlowContext effects={effects} elapsed={self.elapsed_ms:.1f}ms state_keys={list(self.state.keys())}>"


class _FlowContextDictProxy:
    """Dict-style adapter over FlowContext for legacy/context-dict guards."""

    __slots__ = ("_context",)

    def __init__(self, context: FlowContext) -> None:
        self._context = context

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def __getitem__(self, key: str) -> Any:
        if key == "request":
            return self._context.request
        if key == "container":
            return self._context.container
        if key == "identity":
            return self._context.identity
        if key == "session":
            return self._context.session
        if key == "effects":
            return self._context.effects
        return self._context.state[key]

    def __setitem__(self, key: str, value: Any) -> None:
        if key == "request":
            self._context.request = value
            return
        if key == "container":
            self._context.container = value
            return
        if key == "identity":
            self._context.identity = value
            self._context.state["identity"] = value
            return
        if key == "session":
            self._context.session = value
            self._context.state["session"] = value
            return
        if key == "effects":
            self._context.effects = value
            return
        self._context.state[key] = value

    def __contains__(self, key: str) -> bool:
        if key in {"request", "container", "identity", "session", "effects"}:
            return True
        return key in self._context.state


# ============================================================================
# FlowNode -- Typed callable unit in a pipeline
# ============================================================================


@dataclass
class FlowNode:
    """
    A typed unit in a flow pipeline.

    Attributes:
        type:       Node type (guard, transform, handler, hook).
        callable:   The async callable to execute.
        name:       Human-readable name for tracing.
        priority:   Execution order (lower = earlier). Default 50.
        effects:    Effect names this node requires.
        condition:  Optional predicate -- node only runs if True.
        timeout:    Per-node timeout in seconds (None = no limit).
    """

    type: FlowNodeType
    callable: Callable[..., Any]
    name: str
    priority: int = PRIORITY_DEFAULT
    effects: list[str] = field(default_factory=list)
    condition: Callable[[FlowContext], bool] | None = None
    timeout: float | None = None

    def __post_init__(self) -> None:
        # Auto-extract @requires effects from callable
        declared = getattr(self.callable, "__flow_effects__", None)
        if declared and not self.effects:
            self.effects = list(declared)


# ============================================================================
# FlowResult -- Discriminated union of pipeline outcomes
# ============================================================================


@dataclass
class FlowResult:
    """
    Result of a flow pipeline execution.

    Attributes:
        status:   Outcome status (success, guarded, error, timeout).
        value:    Return value from the handler node (if success).
        context:  The final FlowContext (with all state mutations).
        error:    Exception (if status is ERROR).
        guard:    The guard node that short-circuited (if GUARDED).
        timings:  Per-node timing breakdown.
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


# ============================================================================
# FlowError -- Structured pipeline failure
# ============================================================================


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
        super().__init__(message)
        self.node = node
        self.context = context
        self.cause = cause


# ============================================================================
# @requires -- Decorator declaring effect dependencies
# ============================================================================


def requires(*effect_names: str) -> Callable:
    """
    Decorator declaring effect dependencies on a handler or flow node.

    Effects are automatically acquired before execution and released after.

    Example::

        @requires("DBTx", "Cache")
        async def create_user(ctx: FlowContext):
            db = ctx.get_effect("DBTx")
            cache = ctx.get_effect("Cache")
            ...

    Works on:
    - Controller methods (effects injected into ctx)
    - Flow node callables
    - Standalone async functions
    """

    def decorator(func: Callable) -> Callable:
        existing = set(getattr(func, "__flow_effects__", []))
        typed_names = [str(EffectName(name)) for name in effect_names]
        typed_func = func
        casted_func: Any = typed_func
        casted_func.__flow_effects__ = list(existing | set(typed_names))
        return func

    return decorator


def get_required_effects(func: Callable) -> list[str]:
    """Extract declared effect requirements from a callable."""
    return list(getattr(func, "__flow_effects__", []))


# ============================================================================
# Layer -- Composable effect constructor (Effect-TS pattern)
# ============================================================================


@dataclass
class Layer:
    """
    Composable effect layer -- separates effect construction from usage.

    Inspired by Effect-TS's Layer system:
    - Layers build EffectProviders (construction phase)
    - Layers declare their own dependencies (other layers)
    - Layers are composed via ``merge`` and ``provide``
    - The runtime resolves the full dependency graph at startup

    Example::

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

        # Compose layers
        app_layer = Layer.merge(db_layer, cache_layer)
    """

    name: str
    factory: Callable[..., Any]  # (...deps) -> EffectProvider
    deps: list[str] = field(default_factory=list)
    scope: str = "app"  # "app" | "request"
    _built: bool = field(default=False, repr=False)
    _provider: Any | None = field(default=None, repr=False)

    async def build(self, resolved_deps: dict[str, Any]) -> Any:
        """
        Build the effect provider using resolved dependencies.

        Args:
            resolved_deps: Dict of dependency name → resolved value.

        Returns:
            The constructed EffectProvider.
        """
        if self._built and self._provider is not None:
            return self._provider

        # Inject only the deps this layer declared
        kwargs = {dep: resolved_deps[dep] for dep in self.deps if dep in resolved_deps}

        result = self.factory(**kwargs) if kwargs else self.factory()

        if asyncio.iscoroutine(result):
            result = await result

        self._provider = result
        self._built = True
        return result

    @staticmethod
    def merge(*layers: Layer) -> LayerComposition:
        """
        Merge multiple layers into a single composition.

        All layers will be built and their providers registered.
        Dependencies between layers are auto-resolved.
        """
        return LayerComposition(list(layers))

    @staticmethod
    def provide(layer: Layer, *providers: Layer) -> LayerComposition:
        """
        Provide dependencies for a layer from other layers.

        ``providers`` are built first, then ``layer`` is built with
        their outputs as resolved dependencies.
        """
        composition = LayerComposition([*providers, layer])
        composition._dependency_order = [l.name for l in providers] + [layer.name]
        return composition


@dataclass
class LayerComposition:
    """
    A composition of multiple layers, resolved in dependency order.

    The composition builds all layers topologically and registers
    the resulting providers with an EffectRegistry.
    """

    layers: list[Layer]
    _dependency_order: list[str] | None = field(default=None, repr=False)

    async def build_all(
        self,
        initial_deps: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Build all layers in dependency order.

        Args:
            initial_deps: Pre-resolved dependencies (e.g., Config).

        Returns:
            Dict of layer_name → built provider.
        """
        resolved: dict[str, Any] = dict(initial_deps) if initial_deps else {}
        built_order = self._resolve_build_order()

        for layer_name in built_order:
            layer = self._get_layer(layer_name)
            if layer is None:
                continue

            # Check all deps are available
            missing = [d for d in layer.deps if d not in resolved]
            if missing:
                raise FlowError(f"Layer '{layer.name}' has unresolved dependencies: {missing}")

            provider = await layer.build(resolved)
            resolved[layer.name] = provider

        return resolved

    async def register_with(
        self,
        registry: EffectRegistry,
        initial_deps: dict[str, Any] | None = None,
    ) -> None:
        """Build all layers and register providers with the registry."""
        providers = await self.build_all(initial_deps)
        for name, provider in providers.items():
            if name in {l.name for l in self.layers}:
                registry.register(name, provider)

    def _resolve_build_order(self) -> list[str]:
        """Topological sort of layers by dependencies."""
        if self._dependency_order:
            return self._dependency_order

        # Build adjacency graph
        layer_map = {l.name: l for l in self.layers}
        visited: set[str] = set()
        order: list[str] = []

        def visit(name: str, path: set[str]) -> None:
            if name in visited:
                return
            if name in path:
                raise FlowError(f"Circular layer dependency detected: {' → '.join(path)} → {name}")
            path = path | {name}
            layer = layer_map.get(name)
            if layer:
                for dep in layer.deps:
                    if dep in layer_map:
                        visit(dep, path)
            visited.add(name)
            order.append(name)

        for layer in self.layers:
            visit(layer.name, set())

        return order

    def _get_layer(self, name: str) -> Layer | None:
        for layer in self.layers:
            if layer.name == name:
                return layer
        return None


# ============================================================================
# FlowPipeline -- The Pipeline Builder & Executor
# ============================================================================


class FlowPipeline:
    """
    Composable, typed request pipeline with automatic effect management.

    Builds and executes a chain of FlowNodes in priority order:
        Guards → Transforms → Handler → Hooks

    Effect lifecycle:
    1. Collect all declared effects from pipeline nodes
    2. Acquire effects before first node that needs them
    3. Inject effect resources into FlowContext
    4. Execute pipeline
    5. Release effects (success=True on success, False on error)
    6. Run cleanup callbacks

    Usage::

        pipeline = (
            FlowPipeline("create_user")
            .guard(auth_guard, priority=20)
            .guard(scope_guard("users:write"), priority=25)
            .transform(validate_body)
            .handler(create_user_handler)
            .hook(audit_log)
        )

        result = await pipeline.execute(flow_context, effect_registry)

    Or from controller decorator::

        @POST("/users", pipeline=[
            require_auth(),
            require_scopes("users:write"),
            validate_body,
        ])
        async def create_user(self, ctx):
            ...
    """

    def __init__(self, name: str = "pipeline", *, timeout: float | None = None):
        self.name = name
        self.timeout = timeout
        self._nodes: list[FlowNode] = []
        self._logger = logging.getLogger(f"aquilia.flow.{name}")

    # -- Builder API -------------------------------------------------------

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
        node = self._to_node(
            callable_or_node,
            FlowNodeType.GUARD,
            name=name,
            priority=priority,
            effects=effects,
            condition=condition,
        )
        self._nodes.append(node)
        return self

    def transform(
        self,
        callable_or_node: Callable | FlowNode,
        *,
        name: str | None = None,
        priority: int = PRIORITY_TRANSFORM,
        effects: list[str] | None = None,
    ) -> FlowPipeline:
        """Add a transform node. Transforms modify the context/request data."""
        node = self._to_node(
            callable_or_node,
            FlowNodeType.TRANSFORM,
            name=name,
            priority=priority,
            effects=effects,
        )
        self._nodes.append(node)
        return self

    def handler(
        self,
        callable_or_node: Callable | FlowNode,
        *,
        name: str | None = None,
        priority: int = PRIORITY_DEFAULT,
        effects: list[str] | None = None,
    ) -> FlowPipeline:
        """Set the handler node. The handler is the core business logic."""
        node = self._to_node(
            callable_or_node,
            FlowNodeType.HANDLER,
            name=name,
            priority=priority,
            effects=effects,
        )
        self._nodes.append(node)
        return self

    def hook(
        self,
        callable_or_node: Callable | FlowNode,
        *,
        name: str | None = None,
        priority: int = PRIORITY_LOG,
        effects: list[str] | None = None,
    ) -> FlowPipeline:
        """Add a post-handler hook. Hooks run after the handler."""
        node = self._to_node(
            callable_or_node,
            FlowNodeType.HOOK,
            name=name,
            priority=priority,
            effects=effects,
        )
        self._nodes.append(node)
        return self

    def effect(
        self,
        callable_or_node: Callable | FlowNode,
        *,
        name: str | None = None,
        priority: int = PRIORITY_DEFAULT - 5,
        effects: list[str] | None = None,
    ) -> FlowPipeline:
        """Add an effect node. Effect nodes manage resource acquisition."""
        node = self._to_node(
            callable_or_node,
            FlowNodeType.EFFECT,
            name=name,
            priority=priority,
            effects=effects,
        )
        self._nodes.append(node)
        return self

    def middleware(
        self,
        callable_or_node: Callable | FlowNode,
        *,
        name: str | None = None,
        priority: int = PRIORITY_CRITICAL,
    ) -> FlowPipeline:
        """Add a middleware node. Middleware wraps the entire pipeline."""
        node = self._to_node(
            callable_or_node,
            FlowNodeType.MIDDLEWARE,
            name=name,
            priority=priority,
        )
        self._nodes.append(node)
        return self

    def add_node(self, node: FlowNode) -> FlowPipeline:
        """Add a pre-built FlowNode."""
        self._nodes.append(node)
        return self

    def add_nodes(self, nodes: Sequence[FlowNode]) -> FlowPipeline:
        """Add multiple pre-built FlowNodes."""
        self._nodes.extend(nodes)
        return self

    # -- Composition -------------------------------------------------------

    def compose(self, *other: FlowPipeline) -> FlowPipeline:
        """
        Compose this pipeline with others.

        Nodes from all pipelines are merged and re-sorted by priority.
        """
        composed = FlowPipeline(
            name=f"{self.name}+{'|'.join(p.name for p in other)}",
            timeout=self.timeout,
        )
        composed._nodes = list(self._nodes)
        for pipeline in other:
            composed._nodes.extend(pipeline._nodes)
        return composed

    def __or__(self, other: FlowPipeline) -> FlowPipeline:
        """Pipeline composition via ``|`` operator."""
        return self.compose(other)

    # -- Execution ---------------------------------------------------------

    async def execute(
        self,
        context: FlowContext,
        effect_registry: EffectRegistry | None = None,
    ) -> FlowResult:
        """
        Execute the pipeline.

        1. Sort nodes by type priority band, then by node priority.
        2. Collect all required effects across all nodes.
        3. Acquire effects and inject into context.
        4. Execute guards (short-circuit on failure).
        5. Execute transforms.
        6. Execute handler.
        7. Execute hooks.
        8. Release effects.
        9. Return FlowResult.
        """
        timings: dict[str, float] = {}
        pipeline_start = time.monotonic()
        all_effects: set[str] = set()
        execution_success = True

        try:
            # Sort nodes: type band first, then priority within band
            sorted_nodes = self._sort_nodes()

            # Collect all required effects
            all_effects = self._collect_effects(sorted_nodes)

            # Acquire effects
            if all_effects and effect_registry:
                await self._acquire_effects(context, effect_registry, all_effects)

            # Execute by type bands
            handler_result = None

            # Phase 1: Guards
            for node in sorted_nodes:
                if node.type != FlowNodeType.GUARD:
                    continue

                # Check condition
                if node.condition and not node.condition(context):
                    continue

                t0 = time.monotonic()
                try:
                    result = await self._call_node(node, context)
                except Exception as exc:
                    timings[node.name] = (time.monotonic() - t0) * 1000
                    execution_success = False
                    # Guards raising exceptions = guard failure
                    return FlowResult(
                        status=FlowStatus.GUARDED,
                        context=context,
                        error=exc,
                        guard=node,
                        timings=timings,
                    )

                timings[node.name] = (time.monotonic() - t0) * 1000
                context.metadata["node_trace"].append(node.name)

                # Guard short-circuit: if returns False or Response
                if result is False:
                    return FlowResult(
                        status=FlowStatus.GUARDED,
                        context=context,
                        guard=node,
                        timings=timings,
                    )

                # If guard returns a Response, treat as short-circuit with value
                from .response import Response

                if isinstance(result, Response):
                    return FlowResult(
                        status=FlowStatus.GUARDED,
                        value=result,
                        context=context,
                        guard=node,
                        timings=timings,
                    )

            # Phase 2: Transforms
            for node in sorted_nodes:
                if node.type != FlowNodeType.TRANSFORM:
                    continue
                if node.condition and not node.condition(context):
                    continue

                t0 = time.monotonic()
                result = await self._call_node(node, context)
                timings[node.name] = (time.monotonic() - t0) * 1000
                context.metadata["node_trace"].append(node.name)

                # Transforms can update context or return modified data
                if isinstance(result, FlowContext):
                    context = result
                elif isinstance(result, dict):
                    context.state.update(result)

            # Phase 3: Effect nodes
            for node in sorted_nodes:
                if node.type != FlowNodeType.EFFECT:
                    continue
                if node.condition and not node.condition(context):
                    continue

                t0 = time.monotonic()
                await self._call_node(node, context)
                timings[node.name] = (time.monotonic() - t0) * 1000
                context.metadata["node_trace"].append(node.name)

            # Phase 4: Handler
            for node in sorted_nodes:
                if node.type != FlowNodeType.HANDLER:
                    continue
                if node.condition and not node.condition(context):
                    continue

                t0 = time.monotonic()
                handler_result = await self._call_node(node, context)
                timings[node.name] = (time.monotonic() - t0) * 1000
                context.metadata["node_trace"].append(node.name)
                break  # Only one handler

            # Phase 5: Hooks (post-handler)
            for node in sorted_nodes:
                if node.type != FlowNodeType.HOOK:
                    continue
                if node.condition and not node.condition(context):
                    continue

                t0 = time.monotonic()
                try:
                    hook_result = await self._call_node(node, context)
                    # Hooks can modify the handler result
                    if hook_result is not None:
                        handler_result = hook_result
                except Exception as exc:
                    self._logger.warning(
                        "Hook '%s' error (non-fatal): %s",
                        node.name,
                        exc,
                    )
                timings[node.name] = (time.monotonic() - t0) * 1000
                context.metadata["node_trace"].append(node.name)

            timings["__total__"] = (time.monotonic() - pipeline_start) * 1000

            return FlowResult(
                status=FlowStatus.SUCCESS,
                value=handler_result,
                context=context,
                timings=timings,
            )

        except asyncio.CancelledError:
            execution_success = False
            return FlowResult(
                status=FlowStatus.CANCELLED,
                context=context,
                timings=timings,
            )
        except Exception as exc:
            execution_success = False
            timings["__total__"] = (time.monotonic() - pipeline_start) * 1000
            self._logger.error(
                "Pipeline '%s' error: %s",
                self.name,
                exc,
                exc_info=True,
            )
            return FlowResult(
                status=FlowStatus.ERROR,
                context=context,
                error=exc,
                timings=timings,
            )
        finally:
            # Release effects
            if all_effects and effect_registry:
                await self._release_effects(
                    context,
                    effect_registry,
                    all_effects,
                    success=execution_success,
                )

    async def execute_with_timeout(
        self,
        context: FlowContext,
        effect_registry: EffectRegistry | None = None,
        timeout: float | None = None,
    ) -> FlowResult:
        """Execute pipeline with optional timeout."""
        t = timeout or self.timeout
        if t is None:
            return await self.execute(context, effect_registry)

        try:
            return await asyncio.wait_for(
                self.execute(context, effect_registry),
                timeout=t,
            )
        except asyncio.TimeoutError:
            return FlowResult(
                status=FlowStatus.TIMEOUT,
                context=context,
            )

    # -- Internal helpers --------------------------------------------------

    def _sort_nodes(self) -> list[FlowNode]:
        """Sort nodes by type band then by priority."""
        type_order = {
            FlowNodeType.MIDDLEWARE: 0,
            FlowNodeType.GUARD: 1,
            FlowNodeType.TRANSFORM: 2,
            FlowNodeType.EFFECT: 3,
            FlowNodeType.HANDLER: 4,
            FlowNodeType.HOOK: 5,
        }
        return sorted(
            self._nodes,
            key=lambda n: (type_order.get(n.type, 99), n.priority),
        )

    def _collect_effects(self, nodes: list[FlowNode]) -> set[str]:
        """Collect all required effects from all nodes."""
        effects: set[str] = set()
        for node in nodes:
            effects.update(node.effects)
            # Also check for @requires decorator
            declared = getattr(node.callable, "__flow_effects__", None)
            if declared:
                effects.update(declared)
        return effects

    async def _acquire_effects(
        self,
        context: FlowContext,
        registry: EffectRegistry,
        effect_names: set[str],
    ) -> None:
        """Acquire all required effects and inject into context."""
        for name in effect_names:
            if not registry.has_effect(name):
                self._logger.warning(
                    "Effect '%s' required but not registered -- skipping",
                    name,
                )
                continue
            try:
                provider = registry.get_provider(name)
                resource = await provider.acquire()
                context.effects[name] = resource
                context.metadata["acquired_effects"].append(name)
            except Exception as exc:
                self._logger.error(
                    "Failed to acquire effect '%s': %s",
                    name,
                    exc,
                )
                # Release already-acquired effects
                await self._release_effects(
                    context,
                    registry,
                    set(context.effects.keys()),
                    success=False,
                )
                raise FlowError(
                    f"Effect acquisition failed: {name}",
                    cause=exc,
                )

    async def _release_effects(
        self,
        context: FlowContext,
        registry: EffectRegistry,
        effect_names: set[str],
        *,
        success: bool = True,
    ) -> None:
        """Release all acquired effects."""
        for name in list(effect_names):
            resource = context.effects.pop(name, None)
            if resource is None:
                continue
            try:
                provider = registry.get_provider(name)
                await provider.release(resource, success=success)
            except Exception as exc:
                self._logger.warning(
                    "Failed to release effect '%s': %s",
                    name,
                    exc,
                )

    async def _call_node(
        self,
        node: FlowNode,
        context: FlowContext,
    ) -> Any:
        """
        Call a node with smart argument injection.

        Supports multiple signatures:
        - (context: FlowContext)
        - (context: dict)                # Legacy FlowGuard
        - (request, ctx)                 # Controller pipeline compat
        - (request, ctx, controller)     # Controller pipeline compat
        - ()                             # No-arg
        """
        callable_fn = node.callable

        # Class tokens in pipeline lists are first-class: resolve via DI and
        # instantiate per request when needed.
        if inspect.isclass(callable_fn):
            callable_fn = await self._resolve_class_token(callable_fn, context)

        # Handle FlowNode wrapping a class instance (e.g., FlowGuard)
        if callable(callable_fn) and not inspect.isfunction(callable_fn):
            # Instance with __call__ -- use it directly
            pass

        # Determine signature
        try:
            sig = inspect.signature(callable_fn)
            params = sig.parameters
        except (ValueError, TypeError):
            # Can't inspect -- try calling with context
            return await self._safe_call(callable_fn, context)

        param_names = set(params.keys())
        context_proxy = _FlowContextDictProxy(context)

        # Remove 'self' for bound methods
        param_names.discard("self")

        # No parameters
        if not param_names:
            return await self._safe_call(callable_fn)

        # Build kwargs based on parameter names
        kwargs: dict[str, Any] = {}

        for name, param in params.items():
            if name == "self":
                continue

            # Type-hint-based injection
            annotation = param.annotation
            wants_dict_context = False
            if annotation is not inspect.Parameter.empty:
                try:
                    from typing import get_origin

                    origin = get_origin(annotation)
                    if annotation is dict or origin in (dict, Mapping, MutableMapping):
                        wants_dict_context = True
                        kwargs[name] = context_proxy
                        continue
                except Exception:
                    pass

                if isinstance(annotation, str) and ("dict" in annotation.lower() or "mapping" in annotation.lower()):
                    wants_dict_context = True
                    kwargs[name] = context_proxy
                    continue

                if annotation is FlowContext or (isinstance(annotation, str) and "FlowContext" in annotation):
                    kwargs[name] = context
                    continue
                if isinstance(annotation, str) and "Request" in annotation:
                    kwargs[name] = context.request
                    continue

            # Name-based injection
            if name in ("context", "ctx", "flow_context", "flow_ctx"):
                kwargs[name] = context_proxy if wants_dict_context else context
            elif name in ("request", "req"):
                kwargs[name] = context.request
            elif name in ("container", "di"):
                kwargs[name] = context.container
            elif name in ("identity", "user"):
                kwargs[name] = context.identity
            elif name in ("session",):
                kwargs[name] = context.session
            elif name in ("effects",):
                kwargs[name] = context.effects
            elif name in ("state",):
                kwargs[name] = context.state
            elif name.startswith("effect_"):
                # effect_db → get_effect("db") or "DBTx"
                effect_key = name[7:]
                if context.has_effect(effect_key):
                    kwargs[name] = context.get_effect(effect_key)
                elif context.has_effect(effect_key.upper()):
                    kwargs[name] = context.get_effect(effect_key.upper())
            else:
                # Check if it's an effect
                if context.has_effect(name):
                    kwargs[name] = context.get_effect(name)
                # Check state
                elif name in context.state:
                    kwargs[name] = context.state[name]

        return await self._safe_call(callable_fn, **kwargs)

    async def _resolve_class_token(self, class_token: type, context: FlowContext) -> Any:
        """Resolve a class-token pipeline node using request DI context."""
        from .faults.domains import DIResolutionFault

        cache = context.state.setdefault("__flow_class_token_cache__", {})
        if class_token in cache:
            return cache[class_token]

        container = context.container
        token_name = f"{class_token.__module__}.{class_token.__qualname__}"

        # First, honor explicit provider registrations for the class token.
        if container is not None and hasattr(container, "resolve_async"):
            try:
                resolved = await container.resolve_async(class_token, optional=True)
                if resolved is not None:
                    cache[class_token] = resolved
                    return resolved
            except Exception:
                # Fallback to constructor DI below with richer diagnostics.
                pass

        # Fallback: instantiate the class with constructor dependency resolution.
        init_fn = class_token.__init__  # pyright: ignore[reportGeneralTypeIssues]
        try:
            sig = inspect.signature(init_fn)
        except (TypeError, ValueError) as exc:
            raise DIResolutionFault(
                provider=token_name,
                reason=f"Cannot inspect constructor for class-token guard '{class_token.__name__}'",
            ) from exc

        try:
            from typing import get_type_hints

            resolved_hints = get_type_hints(init_fn, include_extras=True)
        except Exception:
            resolved_hints = {}

        kwargs: dict[str, Any] = {}
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue

            has_default = param.default is not inspect.Parameter.empty
            annotation = resolved_hints.get(param_name, param.annotation)

            if annotation is inspect.Parameter.empty:
                if has_default:
                    kwargs[param_name] = param.default
                    continue
                raise DIResolutionFault(
                    provider=token_name,
                    reason=(
                        "Class-token guard constructor parameter "
                        f"'{param_name}' is missing a type annotation. "
                        "Add a type annotation and register a matching DI provider."
                    ),
                )

            if container is None or not hasattr(container, "resolve_async"):
                if has_default:
                    kwargs[param_name] = param.default
                    continue
                raise DIResolutionFault(
                    provider=token_name,
                    reason=(
                        f"No request DI container available while resolving class-token guard parameter '{param_name}'."
                    ),
                )

            try:
                dependency = await container.resolve_async(annotation, optional=has_default)
            except Exception as exc:
                if has_default:
                    kwargs[param_name] = param.default
                    continue
                raise DIResolutionFault(
                    provider=token_name,
                    reason=(
                        "Failed to resolve class-token guard constructor parameter "
                        f"'{param_name}' ({annotation!r}). Ensure the provider is registered."
                    ),
                ) from exc

            if dependency is None and not has_default:
                raise DIResolutionFault(
                    provider=token_name,
                    reason=(
                        "Missing DI provider for class-token guard constructor parameter "
                        f"'{param_name}' ({annotation!r})."
                    ),
                )

            kwargs[param_name] = param.default if dependency is None else dependency

        try:
            instance = class_token(**kwargs)
        except Exception as exc:
            raise DIResolutionFault(
                provider=token_name,
                reason=f"Failed to instantiate class-token guard '{class_token.__name__}': {exc}",
            ) from exc

        cache[class_token] = instance
        return instance

    async def _safe_call(self, fn: Callable, *args: Any, **kwargs: Any) -> Any:
        """Call a function, awaiting if it's a coroutine."""
        try:
            result = fn(*args, **kwargs)
            if asyncio.iscoroutine(result) or asyncio.isfuture(result):
                result = await result
            return result
        except TypeError:
            # Signature mismatch -- try with just the first arg
            if args:
                try:
                    result = fn(args[0])
                    if asyncio.iscoroutine(result):
                        result = await result
                    return result
                except TypeError:
                    pass
            # Try no args
            result = fn()
            if asyncio.iscoroutine(result):
                result = await result
            return result

    def _to_node(
        self,
        callable_or_node: Callable | FlowNode,
        node_type: FlowNodeType,
        *,
        name: str | None = None,
        priority: int = PRIORITY_DEFAULT,
        effects: list[str] | None = None,
        condition: Callable | None = None,
    ) -> FlowNode:
        """Convert a callable or FlowNode to a FlowNode."""
        if isinstance(callable_or_node, FlowNode):
            return callable_or_node

        node_name = str(name or getattr(callable_or_node, "__name__", str(callable_or_node)))
        node_effects = effects or list(getattr(callable_or_node, "__flow_effects__", []))

        return FlowNode(
            type=node_type,
            callable=callable_or_node,
            name=node_name,
            priority=priority,
            effects=node_effects,
            condition=condition,
        )

    # -- Inspection --------------------------------------------------------

    @property
    def nodes(self) -> list[FlowNode]:
        """Return a copy of the node list."""
        return list(self._nodes)

    @property
    def required_effects(self) -> set[str]:
        """All effects required by this pipeline."""
        return self._collect_effects(self._nodes)

    def __repr__(self) -> str:
        node_summary = ", ".join(f"{n.type.value}:{n.name}" for n in self._sort_nodes())
        return f"<FlowPipeline '{self.name}' [{node_summary}]>"

    def __len__(self) -> int:
        return len(self._nodes)


# ============================================================================
# Pipeline Factory Functions
# ============================================================================


def pipeline(
    name: str = "pipeline",
    *,
    timeout: float | None = None,
) -> FlowPipeline:
    """Create a new FlowPipeline."""
    return FlowPipeline(name, timeout=timeout)


def guard(
    fn: Callable,
    *,
    name: str | None = None,
    priority: int = PRIORITY_AUTH,
    effects: list[str] | None = None,
) -> FlowNode:
    """Create a guard FlowNode."""
    return FlowNode(
        type=FlowNodeType.GUARD,
        callable=fn,
        name=str(name or getattr(fn, "__name__", "guard") or "guard"),
        priority=priority,
        effects=effects or list(getattr(fn, "__flow_effects__", [])),
    )


def transform(
    fn: Callable,
    *,
    name: str | None = None,
    priority: int = PRIORITY_TRANSFORM,
    effects: list[str] | None = None,
) -> FlowNode:
    """Create a transform FlowNode."""
    return FlowNode(
        type=FlowNodeType.TRANSFORM,
        callable=fn,
        name=str(name or getattr(fn, "__name__", "transform") or "transform"),
        priority=priority,
        effects=effects or list(getattr(fn, "__flow_effects__", [])),
    )


def handler(
    fn: Callable,
    *,
    name: str | None = None,
    priority: int = PRIORITY_DEFAULT,
    effects: list[str] | None = None,
) -> FlowNode:
    """Create a handler FlowNode."""
    return FlowNode(
        type=FlowNodeType.HANDLER,
        callable=fn,
        name=str(name or getattr(fn, "__name__", "handler") or "handler"),
        priority=priority,
        effects=effects or list(getattr(fn, "__flow_effects__", [])),
    )


def hook(
    fn: Callable,
    *,
    name: str | None = None,
    priority: int = PRIORITY_LOG,
    effects: list[str] | None = None,
) -> FlowNode:
    """Create a hook FlowNode."""
    return FlowNode(
        type=FlowNodeType.HOOK,
        callable=fn,
        name=str(name or getattr(fn, "__name__", "hook") or "hook"),
        priority=priority,
        effects=effects or list(getattr(fn, "__flow_effects__", [])),
    )


# ============================================================================
# from_pipeline_list -- Convert controller pipeline lists to FlowPipeline
# ============================================================================


def from_pipeline_list(
    nodes: Sequence[Any],
    *,
    name: str = "controller_pipeline",
) -> FlowPipeline:
    """
    Convert a controller-style pipeline list to a FlowPipeline.

    Handles:
    - FlowNode instances (used directly)
    - Callables (auto-wrapped as guards -- legacy behavior)
    - FlowGuard instances (wrapped via as_flow_node if available)

    This bridges the controller ``pipeline=[]`` syntax with the
    full Flow pipeline executor.
    """

    def _maybe_materialize_pipeline_factory(item: Any) -> Any:
        """Materialize zero-arg factory references into concrete pipeline items.

        Supports declarative controller pipelines like:
            pipeline = [controller_require_auth, controller_require_scopes("orders:read")]

        Safety constraints:
        - Only plain functions are considered (not classes/instances)
        - No required args and no *args/**kwargs
        - Return annotation must look like a pipeline object
        """
        if not inspect.isfunction(item):
            return item

        try:
            sig = inspect.signature(item)
        except (TypeError, ValueError):
            return item

        for param in sig.parameters.values():
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                return item
            if param.default is inspect.Parameter.empty:
                return item

        return_ann = sig.return_annotation
        if return_ann is inspect.Signature.empty:
            return item

        ann_text = str(return_ann)
        if not any(name in ann_text for name in ("ControllerGuardAdapter", "FlowNode", "FlowPipeline")):
            return item

        try:
            produced = item()
        except Exception:
            # Keep legacy behavior; callable will execute during pipeline runtime.
            return item

        if isinstance(produced, (FlowNode, FlowPipeline)) or hasattr(produced, "as_flow_node") or callable(produced):
            return produced
        return item

    pipe = FlowPipeline(name)

    for item in nodes:
        item = _maybe_materialize_pipeline_factory(item)

        if isinstance(item, FlowNode):
            pipe.add_node(item)
        elif isinstance(item, FlowPipeline):
            pipe._nodes.extend(item._nodes)
        elif hasattr(item, "as_flow_node"):
            # FlowGuard or similar
            pipe.add_node(item.as_flow_node())
        elif callable(item):
            # Legacy: bare callables default to guard type
            pipe.guard(item, name=getattr(item, "__name__", "guard"))
        else:
            logger.warning(
                "Ignoring non-callable pipeline item: %s",
                item,
            )

    return pipe


# ============================================================================
# Scoped Effect Context Manager
# ============================================================================


class EffectScope:
    """
    Async context manager that acquires and releases effects.

    Usage::

        async with EffectScope(registry, ["DBTx", "Cache"]) as effects:
            db = effects["DBTx"]
            cache = effects["Cache"]
            ...

    Integrates with FlowContext if provided::

        async with EffectScope(registry, ["DBTx"], context=flow_ctx) as effects:
            # effects are also available via flow_ctx.get_effect("DBTx")
            ...
    """

    def __init__(
        self,
        registry: EffectRegistry,
        effect_names: Sequence[str],
        *,
        context: FlowContext | None = None,
        modes: dict[str, str] | None = None,
    ):
        self._registry = registry
        self._names = list(effect_names)
        self._context = context
        self._modes = modes or {}
        self._acquired: dict[str, Any] = {}

    async def __aenter__(self) -> dict[str, Any]:
        for name in self._names:
            if not self._registry.has_effect(name):
                raise FlowError(f"Effect '{name}' not registered")
            provider = self._registry.get_provider(name)
            mode = self._modes.get(name)
            resource = await provider.acquire(mode)
            self._acquired[name] = resource
            if self._context is not None:
                self._context.effects[name] = resource
        return self._acquired

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        success = exc_type is None
        for name in reversed(self._names):
            resource = self._acquired.pop(name, None)
            if resource is None:
                continue
            try:
                provider = self._registry.get_provider(name)
                await provider.release(resource, success=success)
            except Exception as exc:
                logger.warning("EffectScope release error for '%s': %s", name, exc)
            finally:
                if self._context is not None:
                    self._context.effects.pop(name, None)
