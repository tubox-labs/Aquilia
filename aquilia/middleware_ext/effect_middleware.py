"""
Effect Middleware -- Per-request effect lifecycle management.

This middleware integrates the Effect system into the ASGI request lifecycle:

1. Before handler: Inspects route metadata for ``@requires()`` declarations
2. Acquires declared effects from the EffectRegistry
3. Injects effect resources into ``request.state["effects"]``
4. After handler: Releases all acquired effects
5. On error: Releases with ``success=False`` (triggers rollback for DB)

Architecture:
    EffectMiddleware sits in the middleware stack and wraps every request.
    It works in concert with:
    - FlowPipeline (which also acquires effects for pipeline nodes)
    - EffectRegistry (central effect provider registry)
    - Controller engine (which passes effects via RequestCtx)
    - @requires() decorator (declares handler effect dependencies)

Lifecycle:
    The middleware uses a *lazy registry* model. Instead of requiring a
    fully-populated ``EffectRegistry`` at construction time (which is not
    possible because providers are registered during the ASGI lifespan
    startup event — *after* the middleware stack is built), the
    ``_DeferredEffectRegistry`` proxy object defers all provider lookups
    to the ``registry_source`` callable. This means you can construct
    ``EffectMiddleware`` with an empty registry and it will automatically
    use the live, fully-populated registry on every real request.

Error Handling:
    If the middleware is active but the registry has no providers registered,
    OR if a required effect is declared but no provider is found, a detailed
    ``EffectNotAcquiredFault`` is raised with:
    - The effect name that could not be acquired
    - Whether EffectMiddleware was detected as active
    - The list of registered effects (for debugging)
    - Actionable remediation hints

Decorator Order:
    ``@requires()`` must be applied **before** (i.e., listed *below* in the
    source) any HTTP method decorator::

        # CORRECT — @requires runs on the raw function first
        @POST("/items")
        @requires("DBTx", "Cache")
        async def create_item(self, ctx: RequestCtx): ...

        # INCORRECT — @requires would wrap the already-decorated function
        @requires("DBTx", "Cache")
        @POST("/items")
        async def create_item(self, ctx: RequestCtx): ...

Usage:
    Automatically registered by EffectSubsystem during startup.
    Can also be manually added to the middleware stack via workspace.py::

        .middleware(
            MiddlewareChain.chain()
            .defaults()
            .use("aquilia.middleware_ext.EffectMiddleware")
        )

    When added via the string import path the server automatically injects
    the live ``EffectRegistry`` at request time -- no manual wiring needed.

Examples:
    # Minimal: rely on auto-registration (server wires registry at startup)
    @POST("/orders")
    @requires("DBTx")
    async def create_order(self, ctx: RequestCtx):
        db = ctx.get_effect("DBTx")
        ...

    # Advanced: explicit provider configuration in workspace.py
    Integration.effects(
        providers={
            "DBTx": {"class": "aquilia.effects.DBTxProvider",
                     "args": {"connection_string": "postgresql://..."}},
        }
    )
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from aquilia.middleware import Middleware

if TYPE_CHECKING:
    from ..controller.base import RequestCtx
    from ..effects import EffectRegistry
    from ..middleware import Handler
    from ..request import Request
    from ..response import Response

logger = logging.getLogger("aquilia.middleware.effects")


# ---------------------------------------------------------------------------
# Deferred registry proxy
# ---------------------------------------------------------------------------


class _DeferredEffectRegistry:
    """
    Lazy proxy that forwards all ``EffectRegistry`` method calls to a live
    registry returned by ``registry_source()``.

    This solves the fundamental bootstrap ordering problem:

        Server.__init__()          → builds middleware stack (too early)
        ASGI lifespan on_startup() → populates effect providers (too late)

    By deferring provider lookup to request time, ``EffectMiddleware`` can be
    constructed before providers are registered without sacrificing
    correctness.

    Args:
        registry_source: Zero-argument callable that returns the live
            ``EffectRegistry``.  May return ``None`` if the effect subsystem
            has not been initialized yet (the middleware will pass through
            silently in that case).

    Thread-safety:
        Reads through to the source on every call -- no internal state is
        mutated, so concurrent async tasks are safe.
    """

    __slots__ = ("_source",)

    def __init__(self, registry_source) -> None:
        object.__setattr__(self, "_source", registry_source)

    def _registry(self) -> EffectRegistry | None:
        try:
            return object.__getattribute__(self, "_source")()
        except Exception:
            return None

    # ── EffectRegistry public API (delegated) ────────────────────────────

    def has_effect(self, effect_name: str) -> bool:
        reg = self._registry()
        return reg.has_effect(effect_name) if reg is not None else False

    async def acquire(self, effect_name: str, mode: str | None = None) -> Any:
        reg = self._registry()
        if reg is None:
            from ..faults.domains import EffectNotAcquiredFault

            raise EffectNotAcquiredFault(
                effect_name=effect_name,
                reason="EffectRegistry is not yet initialized",
                registered_effects=[],
                middleware_active=True,
            )
        return await reg.acquire(effect_name, mode)

    async def release(
        self,
        effect_name: str,
        resource: Any,
        *,
        success: bool = True,
    ) -> None:
        reg = self._registry()
        if reg is not None:
            await reg.release(effect_name, resource, success=success)

    @property
    def providers(self) -> dict:
        reg = self._registry()
        return reg.providers if reg is not None else {}


# ---------------------------------------------------------------------------
# EffectMiddleware
# ---------------------------------------------------------------------------


class EffectMiddleware(Middleware):
    """
    ASGI middleware that manages per-request effect lifecycle.

    For each request:

    1. Inspect route metadata and handler ``__flow_effects__`` attributes to
       discover which effects are required.
    2. Acquire effect resources from ``EffectRegistry`` before the handler
       runs.
    3. Store acquired resources in ``request.state["effects"]`` so that
       ``ctx.get_effect(name)`` (and ``request.get_effect(name)``) work
       correctly.
    4. Release all resources after the handler finishes (``success=True``
       on normal exit, ``success=False`` on exception — this triggers DB
       rollback).

    The middleware also propagates acquired effects into an existing
    ``FlowContext`` (if one is present) so that pipeline nodes using
    ``@requires()`` see the same resource handles.

    Configuration:
        effect_registry:
            An ``EffectRegistry`` instance **or** any object that exposes
            the same interface (``has_effect``, ``acquire``, ``release``,
            ``providers``).  The ``_DeferredEffectRegistry`` proxy satisfies
            this contract and is used when the middleware is wired from the
            workspace string-path API.
        auto_detect:
            When ``True`` (default), the middleware inspects
            ``__flow_effects__`` on the resolved handler method and on
            ``request.state["route_metadata"]`` to discover required effects
            automatically.  When ``False``, only ``request.state
            ["route_effects"]`` is consulted (useful for programmatic control).

    Decorator Ordering:
        ``@requires()`` must be applied **closer to the function** than the
        HTTP method decorator::

            @POST("/users")          # outer decorator — applied last
            @requires("DBTx")       # inner decorator — applied first
            async def create(self, ctx): ...

        Python applies decorators from bottom to top: ``@requires`` runs on
        the raw ``create`` function and attaches ``__flow_effects__``, then
        ``@POST`` wraps it and copies the metadata into
        ``__route_metadata__``.

    Examples:
        Basic DB + Cache route::

            from aquilia.flow import requires
            from aquilia import POST, RequestCtx

            class OrdersController(Controller):
                prefix = "/orders"

                @POST("/")
                @requires("DBTx", "Cache")
                async def create(self, ctx: RequestCtx):
                    db    = ctx.get_effect("DBTx")
                    cache = ctx.get_effect("Cache")
                    # db   → DBTxProvider resource handle
                    # cache → CacheProvider resource handle
                    return {"status": "created"}

        DB rollback on failure::

            @POST("/transfer")
            @requires("DBTx")
            async def transfer(self, ctx: RequestCtx):
                db = ctx.get_effect("DBTx")
                # Any exception raised here → DBTx released with success=False
                # → provider calls rollback()
                raise ValueError("insufficient funds")  # rolls back
    """

    def __init__(
        self,
        effect_registry: EffectRegistry | _DeferredEffectRegistry | None = None,
        *,
        auto_detect: bool = True,
    ):
        """
        Initialise the effect middleware.

        Args:
            effect_registry:
                The ``EffectRegistry`` that holds all registered providers.
                May be a live registry or a ``_DeferredEffectRegistry`` proxy
                that resolves the live registry lazily at request time.
                If ``None``, effect acquisition is silently skipped (no-op).
            auto_detect:
                When ``True``, automatically discover ``@requires()``
                declarations from handler ``__flow_effects__`` attributes.
                Defaults to ``True``.
        """
        self._registry = effect_registry
        self._auto_detect = auto_detect

    async def __call__(
        self,
        request: Request,
        ctx: RequestCtx,
        next_handler: Handler,
    ) -> Response:
        """
        Middleware entry point.

        Wraps the handler with effect acquire/release lifecycle.

        Execution order:

        1. ``_detect_required_effects(request)`` — O(1) lookup in
           ``request.state``.
        2. For each required effect: ``registry.acquire(name, mode)``
           (async, may open a DB connection / get a cache handle).
        3. Inject results into ``request.state["effects"]`` and any
           present ``FlowContext``.
        4. ``await next_handler(request, ctx)`` — the actual controller.
        5. ``registry.release(name, resource, success=...)`` for every
           acquired effect (always, even on error).

        Args:
            request:    The current HTTP request.
            ctx:        The request context (carries identity, session, etc.).
            next_handler: The next middleware / final handler in the chain.

        Returns:
            The ``Response`` produced by the downstream handler.

        Raises:
            ``EffectNotAcquiredFault`` if an effect is required but the
            provider is missing from the registry.
        """
        # ── Guard: no registry configured ───────────────────────────────
        if self._registry is None:
            return await next_handler(request, ctx)

        # ── Determine required effects for this request ──────────────────
        required = self._detect_required_effects(request)

        if not required:
            # No effects needed — pass through without overhead
            return await next_handler(request, ctx)

        # ── Acquire effects ──────────────────────────────────────────────
        acquired: dict[str, Any] = {}
        success = True

        try:
            for effect_name in required:
                if not self._registry.has_effect(effect_name):
                    # Log a clear diagnostic so operators can act on it
                    registered = list(getattr(self._registry, "providers", {}).keys())
                    logger.warning(
                        "Effect '%s' is required by handler but is not registered in the "
                        "EffectRegistry. Registered effects: %s. "
                        "Add the provider to your workspace effects configuration or use "
                        "Integration.effects(providers={...}).",
                        effect_name,
                        registered or "(none)",
                    )
                    continue

                mode = self._get_effect_mode(request, effect_name)
                resource = await self._registry.acquire(effect_name, mode)
                acquired[effect_name] = resource

            # ── Inject effects into request state ────────────────────────
            if not hasattr(request, "state") or request.state is None:
                request.state = {}
            request.state["effects"] = acquired
            request.state["_effect_middleware_active"] = True

            # ── Propagate into FlowContext (if present) ──────────────────
            existing_flow_ctx = request.state.get("flow_context")
            if existing_flow_ctx is not None and hasattr(existing_flow_ctx, "effects"):
                existing_flow_ctx.effects.update(acquired)

            # ── Execute handler ──────────────────────────────────────────
            response = await next_handler(request, ctx)
            return response

        except Exception:
            success = False
            raise

        finally:
            # ── Release all acquired effects (always) ────────────────────
            for effect_name, resource in acquired.items():
                try:
                    await self._registry.release(
                        effect_name,
                        resource,
                        success=success,
                    )
                except Exception as exc:
                    logger.warning(
                        "Error releasing effect '%s': %s",
                        effect_name,
                        exc,
                    )

            # ── Clean up state ───────────────────────────────────────────
            if hasattr(request, "state") and isinstance(request.state, dict):
                request.state.pop("effects", None)
                request.state.pop("_effect_middleware_active", None)

    def _detect_required_effects(self, request: Request) -> set[str]:
        """
        Detect required effects from route/handler metadata.

        The detection strategy uses four sources, evaluated in priority order:

        1. ``request.state["route_effects"]`` — set programmatically by
           the router (highest priority, explicit override).
        2. ``__flow_effects__`` on the *bound* controller method, resolved
           via ``controller_class`` + ``route_metadata.handler_name`` from
           ``request.state`` (set by the ASGI adapter before the middleware
           chain runs — always available for controller routes).
        3. ``__flow_effects__`` on ``request.state["handler"]`` — legacy
           support for raw function handlers and manual routes.
        4. ``request.state["pipeline_effects"]`` — effects declared by
           pipeline nodes in a ``FlowPipeline``.

        Notes:
            - The ASGI adapter populates ``request.state["route_metadata"]``
              and ``request.state["controller_class"]`` *before* calling the
              middleware chain, so effect detection at step 2 is reliable for
              all controller routes.
            - ``@requires()`` must be applied below (i.e. closer to the
              function body than) the HTTP method decorator so that
              ``__flow_effects__`` is present on the raw function before
              ``@POST`` / ``@GET`` wraps it.

        Args:
            request: The current HTTP request.

        Returns:
            A set of effect names required for this request.
        """
        required: set[str] = set()

        if not hasattr(request, "state") or not isinstance(request.state, dict):
            return required

        # ── Source 1: Explicit route effects (programmatic override) ─────
        route_effects = request.state.get("route_effects")
        if route_effects and isinstance(route_effects, (list, set, tuple)):
            required.update(route_effects)

        # ── Source 2 + 3: Handler @requires declarations ─────────────────
        if self._auto_detect:
            # Source 2 (preferred): controller class + route_metadata
            route_meta = request.state.get("route_metadata")
            controller_cls = request.state.get("controller_class")
            if route_meta is not None and controller_cls is not None:
                handler_name = getattr(route_meta, "handler_name", None)
                if handler_name:
                    method = getattr(controller_cls, handler_name, None)
                    if method is not None:
                        declared = getattr(method, "__flow_effects__", None)
                        if declared:
                            required.update(declared)
                        # Also check the underlying function (for wrapped/decorated methods)
                        fn = getattr(method, "__func__", method)
                        declared_fn = getattr(fn, "__flow_effects__", None)
                        if declared_fn:
                            required.update(declared_fn)

            # Source 3 (legacy): raw handler function stored in state
            handler_fn = request.state.get("handler")
            if handler_fn is not None:
                declared = getattr(handler_fn, "__flow_effects__", None)
                if declared:
                    required.update(declared)

        # ── Source 4: Pipeline effects ───────────────────────────────────
        pipeline_effects = request.state.get("pipeline_effects")
        if pipeline_effects and isinstance(pipeline_effects, (list, set, tuple)):
            required.update(pipeline_effects)

        return required

    def _get_effect_mode(
        self,
        request: Request,
        effect_name: str,
    ) -> str | None:
        """
        Determine the acquisition mode for a given effect.

        Mode selection rules:

        - **DB effects** (``"DBTx"``, ``"db"``): inferred from the HTTP
          method.  ``POST``, ``PUT``, ``PATCH``, and ``DELETE`` request a
          ``"write"`` transaction; all other methods request ``"read"``.
        - **Cache effects**: the namespace, if explicitly provided via
          ``request.state["effect_modes"]``.
        - **All other effects**: use explicit mode from
          ``request.state["effect_modes"]`` if available, otherwise
          ``None`` (provider uses its own default).

        Args:
            request:     The current HTTP request.
            effect_name: The effect to determine the mode for.

        Returns:
            A mode string (e.g. ``"read"``, ``"write"``, a cache namespace)
            or ``None`` when no explicit mode is needed.

        Examples:
            ``POST /orders`` with ``DBTx`` → ``"write"``
            ``GET /users``  with ``DBTx`` → ``"read"``
            ``GET /``       with ``Cache`` → ``None`` (uses provider default)
        """
        if effect_name in ("DBTx", "db"):
            method = getattr(request, "method", "GET")
            if method in ("POST", "PUT", "PATCH", "DELETE"):
                return "write"
            return "read"

        # Check for explicit mode in state
        if hasattr(request, "state") and isinstance(request.state, dict):
            modes = request.state.get("effect_modes", {})
            if isinstance(modes, dict):
                return modes.get(effect_name)

        return None


# ---------------------------------------------------------------------------
# FlowContextMiddleware
# ---------------------------------------------------------------------------


class FlowContextMiddleware(Middleware):
    """
    Middleware that creates a ``FlowContext`` for each request.

    Bridges the ASGI request lifecycle with the Flow pipeline system.
    Ensures every request has a ``FlowContext`` available for pipeline
    nodes, guards, and effect-aware handlers.

    The ``FlowContext`` is stored in ``request.state["flow_context"]``
    and is disposed (releasing any held resources) in the ``finally``
    block, guaranteeing cleanup even if the handler raises.

    Registration:
        Automatically registered by ``EffectSubsystem`` during startup.
        Can be added explicitly via the workspace middleware chain::

            .middleware(
                MiddlewareChain.chain()
                .defaults()
                .use("aquilia.middleware_ext.FlowContextMiddleware")
                .use("aquilia.middleware_ext.EffectMiddleware")
            )

        ``FlowContextMiddleware`` must come **before** ``EffectMiddleware``
        in the chain (lower priority number = runs first) so that the
        ``FlowContext`` exists when ``EffectMiddleware`` tries to propagate
        acquired effects into it.

    Args:
        effect_registry:
            Optional ``EffectRegistry`` to attach to the ``FlowContext``.
            Can be ``None`` — the FlowContext will still be created without
            an effect registry reference.

    Examples:
        Middleware chain ordering (correct)::

            MiddlewareChain.chain()
            .defaults()                                          # priority 1, 10
            .use("aquilia.middleware_ext.FlowContextMiddleware", priority=14)
            .use("aquilia.middleware_ext.EffectMiddleware",      priority=15)

        Accessing the FlowContext from a pipeline node::

            from aquilia.flow import FlowContext

            async def my_guard(ctx: FlowContext) -> None:
                flow_ctx = ctx.request.state.get("flow_context")
                if flow_ctx and flow_ctx.has_effect("DBTx"):
                    db = flow_ctx.get_effect("DBTx")
    """

    def __init__(
        self,
        effect_registry: EffectRegistry | _DeferredEffectRegistry | None = None,
    ):
        """
        Initialise the FlowContext middleware.

        Args:
            effect_registry:
                Optional registry to attach to the ``FlowContext``.
                Accepts a live ``EffectRegistry`` or a
                ``_DeferredEffectRegistry`` proxy.
        """
        self._registry = effect_registry

    async def __call__(
        self,
        request: Request,
        ctx: RequestCtx,
        next_handler: Handler,
    ) -> Response:
        """
        Create a ``FlowContext``, attach it to ``request.state``, and
        dispose it after the handler returns (or raises).

        Args:
            request:      The current HTTP request.
            ctx:          The request context.
            next_handler: The next middleware / final handler.

        Returns:
            The ``Response`` produced by the downstream handler.
        """
        from ..flow import FlowContext

        # Build FlowContext for this request
        flow_ctx = FlowContext(
            request=request,
            container=getattr(ctx, "container", None)
            or getattr(request, "_container", None)
            or (request.state.get("container") if hasattr(request, "state") else None),
            identity=request.state.get("identity") if hasattr(request, "state") else None,
            session=request.state.get("session") if hasattr(request, "state") else None,
        )

        # Store in request state
        if not hasattr(request, "state") or request.state is None:
            request.state = {}
        request.state["flow_context"] = flow_ctx

        try:
            response = await next_handler(request, ctx)
            return response
        finally:
            await flow_ctx.dispose()
