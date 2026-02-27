"""
Aquilia Blueprint Integration — hooks into Controller, DI, Request/Response.

Provides:
    - Controller auto-binding for Blueprint type annotations
    - Response rendering helpers
    - DI container integration
    - Blueprint detection utilities
"""

from __future__ import annotations

import inspect
from typing import Any, Dict, Type, TYPE_CHECKING

from .core import Blueprint, BlueprintMeta
from .lenses import _ProjectedRef

if TYPE_CHECKING:
    from ..request import Request
    from ..response import Response


__all__ = [
    "is_blueprint_class",
    "is_projected_blueprint",
    "resolve_blueprint_from_annotation",
    "bind_blueprint_to_request",
    "render_blueprint_response",
]


def is_blueprint_class(obj: Any) -> bool:
    """Check if an object is a Blueprint class (not instance)."""
    return isinstance(obj, type) and issubclass(obj, Blueprint) and obj is not Blueprint


def is_projected_blueprint(obj: Any) -> bool:
    """Check if an object is a ProjectedRef (Blueprint["projection"])."""
    return isinstance(obj, _ProjectedRef)


def resolve_blueprint_from_annotation(
    annotation: Any,
) -> tuple[Type[Blueprint] | None, str | None]:
    """
    Resolve a Blueprint class and projection from a type annotation.

    Handles:
        - ``MyBlueprint`` → (MyBlueprint, None)
        - ``MyBlueprint["summary"]`` → (MyBlueprint, "summary")
        - Non-Blueprint types → (None, None)

    Returns:
        (blueprint_class, projection_name) tuple
    """
    if is_projected_blueprint(annotation):
        return annotation.blueprint_cls, annotation.projection

    if is_blueprint_class(annotation):
        return annotation, None

    return None, None


def _unflatten_dict(flat_dict: dict) -> dict:
    """Unflatten dot-notated dictionary keys into nested dictionaries."""
    result = {}
    for key, value in flat_dict.items():
        parts = key.split('.')
        current = result
        for part in parts[:-1]:
            current = current.setdefault(part, {})
        current[parts[-1]] = value
    return result


async def bind_blueprint_to_request(
    blueprint_cls: Type[Blueprint],
    request: Any,
    *,
    projection: str | None = None,
    partial: bool = False,
    context: Dict[str, Any] | None = None,
) -> Blueprint:
    """
    Create and validate a Blueprint from an incoming request.

    This is the integration point called by the controller engine
    when it detects a Blueprint type annotation on a handler parameter.

    Args:
        blueprint_cls: The Blueprint class to instantiate
        request: The Aquilia Request object
        projection: Optional projection name
        partial: If True, don't require all fields (PATCH)
        context: Extra context to pass to the Blueprint

    Returns:
        A validated Blueprint instance (is_sealed() has been called)
    """
    # Parse request body
    try:
        body = await request.json()
    except Exception:
        try:
            form_data = await request.form()
            form_dict = form_data.fields.to_dict() if hasattr(form_data, "fields") else dict(form_data)
            body = _unflatten_dict(form_dict)
        except Exception:
            body = {}

    data = dict(body) if isinstance(body, dict) else {}

    # Extract DI parameters (Query, Header) from Facet defaults
    try:
        from ..di.dep import Header, Query
        for name, facet in getattr(blueprint_cls, "_all_facets", {}).items():
            if hasattr(facet, "default"):
                default_val = facet.default
                if isinstance(default_val, Query):
                    param_name = default_val.name or name
                    val = None
                    if hasattr(request, "query_param"):
                        val = request.query_param(param_name)
                    elif hasattr(request, "query_params"):
                        qps = request.query_params
                        val = qps.get(param_name) if isinstance(qps, dict) else None
                    if val is not None:
                        data[name] = val
                    else:
                        if getattr(default_val, "required", False):
                            data[name] = None
                        elif hasattr(default_val, "default") and default_val.default is not ...:
                            data[name] = default_val.default
                        else:
                            data[name] = None
                elif isinstance(default_val, Header):
                    header_key = default_val.header_key
                    val = None
                    if hasattr(request, "headers"):
                        headers = request.headers
                        if isinstance(headers, dict):
                            val = headers.get(header_key)
                        elif hasattr(headers, "get"):
                            val = headers.get(header_key)
                    if val is not None:
                        data[name] = val
                    else:
                        if getattr(default_val, "required", False):
                            data[name] = None
                        elif hasattr(default_val, "default") and default_val.default is not ...:
                            data[name] = default_val.default
                        else:
                            data[name] = None
    except ImportError:
        pass

    # Build context with request info
    bp_context = {
        "request": request,
        **(context or {}),
    }

    # Check for DI container in request state
    state = getattr(request, "state", None)
    if state is not None:
        container = state.get("container") if isinstance(state, dict) else getattr(state, "container", None)
        if container is not None:
            bp_context["container"] = container

    # Instantiate Blueprint
    bp = blueprint_cls(
        data=data,
        partial=partial,
        projection=projection,
        context=bp_context,
    )

    return bp


def render_blueprint_response(
    blueprint_or_cls: Blueprint | Type[Blueprint],
    data: Any = None,
    *,
    projection: str | None = None,
    many: bool = False,
) -> Any:
    """
    Render data through a Blueprint for response output.

    This is used by the controller engine when a ``response_blueprint``
    is specified on a route.

    Args:
        blueprint_or_cls: Blueprint instance or class
        data: The data to render (model instance or list)
        projection: Optional projection name
        many: If True, data is a list of instances

    Returns:
        Dict or list of dicts ready for JSON serialization
    """
    if isinstance(blueprint_or_cls, Blueprint):
        # Already an instance — use it
        bp = blueprint_or_cls
        if data is not None:
            bp.instance = data
            bp.many = many
        return bp.data

    # It's a class — instantiate
    bp_cls = blueprint_or_cls
    proj = projection

    # Handle ProjectedRef
    if isinstance(bp_cls, _ProjectedRef):
        proj = bp_cls.projection
        bp_cls = bp_cls.blueprint_cls

    bp = bp_cls(instance=data, many=many, projection=proj)
    return bp.data
