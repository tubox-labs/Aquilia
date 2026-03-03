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

Usage:
    Automatically registered by EffectSubsystem during startup.
    Can also be manually added to the middleware stack:

        from aquilia.middleware_ext.effect_middleware import EffectMiddleware
        app.middleware_stack.add(EffectMiddleware(registry), priority=15)
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from ..effects import EffectRegistry
    from ..request import Request
    from ..response import Response
    from ..middleware import Handler

logger = logging.getLogger("aquilia.middleware.effects")


class EffectMiddleware:
    """
    ASGI middleware that manages per-request effect lifecycle.

    For each request:
    1. Extract required effects from route metadata / handler decorators
    2. Acquire effect resources before handler execution
    3. Make resources available via ``request.state["effects"]``
    4. Release resources after handler (success=True/False)

    This ensures DB transactions are committed on success and
    rolled back on failure, cache handles are properly cleaned up,
    and queue connections are returned to their pools.
    """

    def __init__(
        self,
        effect_registry: "EffectRegistry",
        *,
        auto_detect: bool = True,
    ):
        """
        Args:
            effect_registry: The EffectRegistry containing all providers.
            auto_detect: If True, automatically detect @requires() on handlers.
        """
        self._registry = effect_registry
        self._auto_detect = auto_detect

    async def __call__(
        self,
        request: "Request",
        handler: "Handler",
    ) -> "Response":
        """
        Middleware entry point.

        Wraps the handler with effect acquire/release lifecycle.
        """
        # Determine required effects for this request
        required = self._detect_required_effects(request)

        if not required:
            # No effects needed -- pass through without overhead
            return await handler(request)

        # Acquire effects
        acquired: Dict[str, Any] = {}
        success = True

        try:
            for effect_name in required:
                if not self._registry.has_effect(effect_name):
                    logger.warning(
                        "Effect '%s' required by handler but not registered",
                        effect_name,
                    )
                    continue

                mode = self._get_effect_mode(request, effect_name)
                resource = await self._registry.acquire(effect_name, mode)
                acquired[effect_name] = resource

            # Inject effects into request state
            if not hasattr(request, "state") or request.state is None:
                request.state = {}
            request.state["effects"] = acquired
            request.state["_effect_middleware_active"] = True

            # Also inject as FlowContext-compatible dict
            existing_flow_ctx = request.state.get("flow_context")
            if existing_flow_ctx is not None and hasattr(existing_flow_ctx, "effects"):
                existing_flow_ctx.effects.update(acquired)

            # Execute handler
            response = await handler(request)
            return response

        except Exception:
            success = False
            raise

        finally:
            # Release all acquired effects
            for effect_name, resource in acquired.items():
                try:
                    await self._registry.release(
                        effect_name, resource, success=success,
                    )
                except Exception as exc:
                    logger.warning(
                        "Error releasing effect '%s': %s",
                        effect_name, exc,
                    )

            # Clean up state
            if hasattr(request, "state") and isinstance(request.state, dict):
                request.state.pop("effects", None)
                request.state.pop("_effect_middleware_active", None)

    def _detect_required_effects(self, request: "Request") -> Set[str]:
        """
        Detect required effects from route/handler metadata.

        Checks:
        1. ``request.state["route_effects"]`` -- set by router
        2. ``request.state["handler"].__flow_effects__`` -- @requires decorator
        3. ``request.state["pipeline_effects"]`` -- from pipeline nodes
        """
        required: Set[str] = set()

        if not hasattr(request, "state") or not isinstance(request.state, dict):
            return required

        # From router metadata
        route_effects = request.state.get("route_effects")
        if route_effects:
            if isinstance(route_effects, (list, set, tuple)):
                required.update(route_effects)

        # From handler @requires
        if self._auto_detect:
            handler_fn = request.state.get("handler")
            if handler_fn is not None:
                declared = getattr(handler_fn, "__flow_effects__", None)
                if declared:
                    required.update(declared)

            # Check controller method
            route_meta = request.state.get("route_metadata")
            if route_meta is not None:
                handler_name = getattr(route_meta, "handler_name", None)
                controller_cls = request.state.get("controller_class")
                if handler_name and controller_cls:
                    method = getattr(controller_cls, handler_name, None)
                    if method:
                        declared = getattr(method, "__flow_effects__", None)
                        if declared:
                            required.update(declared)

        # From pipeline nodes
        pipeline_effects = request.state.get("pipeline_effects")
        if pipeline_effects:
            if isinstance(pipeline_effects, (list, set, tuple)):
                required.update(pipeline_effects)

        return required

    def _get_effect_mode(
        self,
        request: "Request",
        effect_name: str,
    ) -> Optional[str]:
        """
        Determine the mode for an effect acquisition.

        For DB effects: infer read/write from HTTP method.
        For Cache effects: use namespace from route metadata.
        """
        if effect_name in ("DBTx", "db"):
            # Infer read/write from HTTP method
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


class FlowContextMiddleware:
    """
    Middleware that creates a FlowContext for each request.

    Bridges the ASGI request lifecycle with the Flow pipeline system.
    Ensures every request has a FlowContext available for pipeline nodes,
    guards, and effect-aware handlers.

    The FlowContext is stored in ``request.state["flow_context"]``.
    """

    def __init__(
        self,
        effect_registry: Optional["EffectRegistry"] = None,
    ):
        self._registry = effect_registry

    async def __call__(
        self,
        request: "Request",
        handler: "Handler",
    ) -> "Response":
        from ..flow import FlowContext

        # Create FlowContext for this request
        flow_ctx = FlowContext(
            request=request,
            container=getattr(request, "_container", None) or (
                request.state.get("container") if hasattr(request, "state") else None
            ),
            identity=request.state.get("identity") if hasattr(request, "state") else None,
            session=request.state.get("session") if hasattr(request, "state") else None,
        )

        # Store in request state
        if not hasattr(request, "state") or request.state is None:
            request.state = {}
        request.state["flow_context"] = flow_ctx

        try:
            response = await handler(request)
            return response
        finally:
            await flow_ctx.dispose()
