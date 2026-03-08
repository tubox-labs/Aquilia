"""
Aquilia Blueprint Integration -- hooks into Controller, DI, Request/Response.

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
from .exceptions import SealFault

if TYPE_CHECKING:
    from ..request import Request
    from ..response import Response


# ── Security Constants ──────────────────────────────────────────────────

# Maximum request body size (bytes) before Blueprint parsing.
# Can be overridden via context["max_body_size"].
MAX_BODY_SIZE: int = 10 * 1024 * 1024  # 10 MB

# Maximum depth for unflattening dot-notated form keys.
MAX_UNFLATTEN_DEPTH: int = 10

# Maximum number of form keys to process.
MAX_UNFLATTEN_KEYS: int = 1000


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


def _unflatten_dict(flat_dict: dict, *, max_depth: int | None = None, max_keys: int | None = None) -> dict:
    """Unflatten dot-notated dictionary keys into nested dictionaries.
    
    Security: Limits nesting depth and key count to prevent resource
    exhaustion from crafted form field names.
    """
    _max_depth = max_depth if max_depth is not None else MAX_UNFLATTEN_DEPTH
    _max_keys = max_keys if max_keys is not None else MAX_UNFLATTEN_KEYS

    if len(flat_dict) > _max_keys:
        raise SealFault(
            message=f"Too many form keys ({len(flat_dict)} > {_max_keys})",
            errors={"__all__": [f"Form key count {len(flat_dict)} exceeds limit of {_max_keys}"]},
        )

    result = {}
    for key, value in flat_dict.items():
        parts = key.split('.')
        if len(parts) > _max_depth:
            raise SealFault(
                message=f"Form key nesting depth ({len(parts)}) exceeds maximum of {_max_depth}",
                errors={"__all__": [f"Form key '{key[:50]}...' nesting too deep ({len(parts)} > {_max_depth})"]},
            )
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
    # ── Security: Body size check ────────────────────────────────────
    max_body = MAX_BODY_SIZE
    if context and context.get("max_body_size"):
        max_body = context["max_body_size"]

    content_length = None
    if hasattr(request, "headers"):
        headers = request.headers
        if isinstance(headers, dict):
            cl = headers.get("content-length") or headers.get("Content-Length")
        elif hasattr(headers, "get"):
            cl = headers.get("content-length")
        else:
            cl = None
        if cl is not None:
            try:
                content_length = int(cl)
            except (ValueError, TypeError):
                pass

    if content_length is not None and content_length > max_body:
        raise SealFault(
            message=f"Request body too large ({content_length} bytes). "
                    f"Maximum allowed: {max_body} bytes",
            errors={"__all__": [f"Request body exceeds {max_body} byte limit"]},
        )

    # ── Content-Type detection ───────────────────────────────────────
    content_type = ""
    if hasattr(request, "headers"):
        headers = request.headers
        if isinstance(headers, dict):
            content_type = headers.get("content-type", "") or headers.get("Content-Type", "")
        elif hasattr(headers, "get"):
            content_type = headers.get("content-type", "")

    # Parse request body
    body = {}
    if "application/json" in content_type or not content_type:
        try:
            body = await request.json()
        except Exception:
            body = {}

    if not body and ("multipart/form-data" in content_type or "application/x-www-form-urlencoded" in content_type or not content_type):
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
        # Already an instance -- use it
        bp = blueprint_or_cls
        if data is not None:
            bp.instance = data
            bp.many = many
        return bp.data

    # It's a class -- instantiate
    bp_cls = blueprint_or_cls
    proj = projection

    # Handle ProjectedRef
    if isinstance(bp_cls, _ProjectedRef):
        proj = bp_cls.projection
        bp_cls = bp_cls.blueprint_cls

    bp = bp_cls(instance=data, many=many, projection=proj)
    return bp.data
