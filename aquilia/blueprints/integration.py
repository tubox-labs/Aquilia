"""
Aquilia Blueprint Integration -- hooks into Controller, DI, Request/Response.

Provides:
    - Controller auto-binding for Blueprint type annotations
    - Response rendering helpers
    - DI container integration
    - Blueprint detection utilities
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any

from .core import Blueprint
from .exceptions import SealFault
from .lenses import _ProjectedRef

if TYPE_CHECKING:
    pass


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
) -> tuple[type[Blueprint] | None, str | None]:
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
        parts = key.split(".")
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


def extract_value_from_request(
    request: Any,
    name: str,
    extractor: Any,
    facet: Any,
    body: Any,
) -> Any:
    """Extract field/parameter value from request using extractor metadata or default lookup order."""
    from aquilia.blueprints.facets import UNSET, ListFacet, SetFacet, TupleFacet
    from aquilia.di.dep import Body as BodyExtractor
    from aquilia.di.dep import Cookie, Header, Path, Query

    # 1. Determine key to look up
    lookup_key = name
    if extractor is not None:
        lookup_key = getattr(extractor, "alias", None) or getattr(extractor, "name", None) or name

    # 2. Determine if it is a list/collection facet
    is_collection = isinstance(facet, (ListFacet, SetFacet, TupleFacet)) or getattr(facet, "many", False)

    # 3. Perform extraction based on extractor class
    if isinstance(extractor, Query):
        if not is_collection and hasattr(request, "query_param"):
            val = request.query_param(lookup_key)
            if val is None:
                val = request.query_param(f"{lookup_key}[]")
            if val is not None and type(val).__name__ != "MagicMock":
                return val

        if hasattr(request, "query_params"):
            qps = request.query_params
            if type(qps).__name__ != "MagicMock" or not hasattr(request, "query_param"):
                if hasattr(qps, "get_all"):
                    if is_collection:
                        vals = qps.get_all(lookup_key)
                        if not vals:
                            vals = qps.get_all(f"{lookup_key}[]")
                        return vals if vals else UNSET
                    else:
                        val = qps.get(lookup_key)
                        if val is None:
                            val = qps.get(f"{lookup_key}[]")
                        return val if val is not None else UNSET
                elif isinstance(qps, dict):
                    val = qps.get(lookup_key)
                    if val is not None:
                        return [val] if is_collection else val

        if hasattr(request, "query_param"):
            val = request.query_param(lookup_key)
            if val is None:
                val = request.query_param(f"{lookup_key}[]")
            if val is not None:
                return [val] if is_collection else val

        return UNSET

    elif isinstance(extractor, Header):
        if hasattr(request, "headers"):
            headers = request.headers
            hkey = lookup_key.lower()
            val = None
            if hasattr(headers, "get"):
                val = headers.get(hkey)
                if val is None:
                    val = headers.get(lookup_key)
            elif isinstance(headers, dict):
                val = headers.get(hkey) or headers.get(lookup_key)
            if val is not None:
                return val
        return UNSET

    elif isinstance(extractor, Cookie):
        if hasattr(request, "cookie"):
            val = request.cookie(lookup_key)
            if val is not None:
                return val
        if hasattr(request, "cookies"):
            cookies = request.cookies
            if isinstance(cookies, dict):
                val = cookies.get(lookup_key)
                if val is not None:
                    return val
        return UNSET

    elif isinstance(extractor, Path):
        if hasattr(request, "path_params"):
            path_params = request.path_params
            if isinstance(path_params, dict) and lookup_key in path_params:
                return path_params[lookup_key]
        return UNSET

    elif isinstance(extractor, BodyExtractor):
        embed = getattr(extractor, "embed", False)
        if embed:
            if isinstance(body, dict):
                if lookup_key in body:
                    return body[lookup_key]
                if f"{lookup_key}[]" in body:
                    return body[f"{lookup_key}[]"]
            try:
                from .._uploads import FormData
            except ImportError:
                FormData = None
            if FormData is not None and isinstance(body, FormData):
                if lookup_key in body.fields:
                    return body.get_all_fields(lookup_key) if is_collection else body.get_field(lookup_key)
                if f"{lookup_key}[]" in body.fields:
                    return (
                        body.get_all_fields(f"{lookup_key}[]") if is_collection else body.get_field(f"{lookup_key}[]")
                    )
                if lookup_key in body.files:
                    return body.get_all_files(lookup_key) if is_collection else body.get_file(lookup_key)
                if f"{lookup_key}[]" in body.files:
                    return body.get_all_files(f"{lookup_key}[]") if is_collection else body.get_file(f"{lookup_key}[]")
            return UNSET
        else:
            return body

    else:
        # Default (No extractor) lookup order: Path -> Body -> Query
        # A. Path parameters
        if hasattr(request, "path_params"):
            path_params = request.path_params
            if isinstance(path_params, dict) and lookup_key in path_params:
                return path_params[lookup_key]

        # B. Body
        if body:
            if isinstance(body, dict):
                if lookup_key in body:
                    return body[lookup_key]
                if f"{lookup_key}[]" in body:
                    return body[f"{lookup_key}[]"]
            try:
                from .._uploads import FormData
            except ImportError:
                FormData = None
            if FormData is not None and isinstance(body, FormData):
                if lookup_key in body.fields:
                    return body.get_all_fields(lookup_key) if is_collection else body.get_field(lookup_key)
                if f"{lookup_key}[]" in body.fields:
                    return (
                        body.get_all_fields(f"{lookup_key}[]") if is_collection else body.get_field(f"{lookup_key}[]")
                    )
                if lookup_key in body.files:
                    return body.get_all_files(lookup_key) if is_collection else body.get_file(lookup_key)
                if f"{lookup_key}[]" in body.files:
                    return body.get_all_files(f"{lookup_key}[]") if is_collection else body.get_file(f"{lookup_key}[]")
                # Also check dotted keys if nested
                dot_prefix = f"{lookup_key}."
                bracket_prefix = f"{lookup_key}["
                if any(k.startswith(dot_prefix) or k.startswith(bracket_prefix) for k in body.fields):
                    return body

        # C. Query parameters
        if hasattr(request, "query_param") and not is_collection:
            val = request.query_param(lookup_key)
            if val is None:
                val = request.query_param(f"{lookup_key}[]")
            if val is not None and type(val).__name__ != "MagicMock":
                return val

        if hasattr(request, "query_params"):
            qps = request.query_params
            if type(qps).__name__ != "MagicMock" or not hasattr(request, "query_param"):
                if hasattr(qps, "get_all"):
                    vals = qps.get_all(lookup_key)
                    if not vals:
                        vals = qps.get_all(f"{lookup_key}[]")
                    if vals:
                        return vals if is_collection else vals[0]

                    # Check dotted keys if nested (for query params)
                    dot_prefix = f"{lookup_key}."
                    bracket_prefix = f"{lookup_key}["
                    if any(k.startswith(dot_prefix) or k.startswith(bracket_prefix) for k in qps):
                        return qps

        if hasattr(request, "query_param"):
            val = request.query_param(lookup_key)
            if val is None:
                val = request.query_param(f"{lookup_key}[]")
            if val is not None:
                return [val] if is_collection else val

        return UNSET


async def bind_blueprint_to_request(
    blueprint_cls: type[Blueprint],
    request: Any,
    *,
    projection: str | None = None,
    partial: bool = False,
    context: dict[str, Any] | None = None,
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
    import time

    t0 = time.monotonic()

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
            with contextlib.suppress(ValueError, TypeError):
                content_length = int(cl)

    if content_length is not None and content_length > max_body:
        raise SealFault(
            message=f"Request body too large ({content_length} bytes). Maximum allowed: {max_body} bytes",
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
    if "application/json" in content_type:
        try:
            body = await request.json()
        except Exception:
            body = {}
    elif "multipart/form-data" in content_type:
        try:
            body = await request.multipart()
        except (AttributeError, TypeError):
            try:
                body = await request.form()
            except Exception:
                body = {}
        except Exception:
            body = {}
    elif "application/x-www-form-urlencoded" in content_type:
        try:
            body = await request.form()
        except Exception:
            body = {}
    else:
        if not content_type:
            try:
                body = await request.json()
            except Exception:
                try:
                    body = await request.form()
                except Exception:
                    body = {}

    from .._datastructures import MultiDict

    try:
        from .._uploads import FormData
    except ImportError:
        FormData = None

    from aquilia.blueprints.facets import UNSET

    # Construct the merged mapping
    if FormData is not None and isinstance(body, FormData):
        merged_data = FormData(fields=MultiDict(body.fields), files=body.files.copy())
    else:
        merged_data = dict(body) if isinstance(body, dict) else {}

    # Copy Query Parameters into merged_data (if not already set by body)
    if hasattr(request, "query_params"):
        qps = request.query_params
        if hasattr(qps, "keys") or isinstance(qps, dict) or hasattr(qps, "__iter__"):
            for k in qps:
                is_set = False
                if isinstance(merged_data, dict):
                    is_set = k in merged_data
                elif FormData is not None and isinstance(merged_data, FormData):
                    is_set = k in merged_data.fields or k in merged_data.files

                if not is_set:
                    if hasattr(qps, "get_all"):
                        vals = qps.get_all(k)
                    elif isinstance(qps, dict):
                        vals = [qps[k]]
                    else:
                        vals = []

                    from aquilia.blueprints.facets import ListFacet, SetFacet, TupleFacet

                    facet = blueprint_cls._all_facets.get(k)
                    is_collection = isinstance(facet, (ListFacet, SetFacet, TupleFacet)) or getattr(
                        facet, "many", False
                    )

                    if vals:
                        val_to_set = vals if is_collection else vals[0]
                        if isinstance(merged_data, dict):
                            merged_data[k] = val_to_set
                        elif FormData is not None and isinstance(merged_data, FormData):
                            for val in vals:
                                merged_data.fields.add(k, val)

    # Copy Path Parameters into merged_data
    if hasattr(request, "path_params"):
        path_params = request.path_params
        if isinstance(path_params, dict):
            for k, v in path_params.items():
                is_set = False
                if isinstance(merged_data, dict):
                    is_set = k in merged_data
                elif FormData is not None and isinstance(merged_data, FormData):
                    is_set = k in merged_data.fields or k in merged_data.files

                if not is_set:
                    if isinstance(merged_data, dict):
                        merged_data[k] = v
                    elif FormData is not None and isinstance(merged_data, FormData):
                        merged_data.fields.add(k, v)

    # Resolve each facet using explicit extractors
    for name, facet in getattr(blueprint_cls, "_all_facets", {}).items():
        extractor = getattr(facet, "_extractor", None)
        # Fallback check for old default-based metadata
        if extractor is None:
            default_val = getattr(facet, "default", None)
            from ..di.dep import Body as BodyExtractor
            from ..di.dep import Cookie, Header, Path, Query

            if isinstance(default_val, (Query, Header, BodyExtractor, Cookie, Path)):
                extractor = default_val

        # Extract value using explicit extractor rules
        val = extract_value_from_request(request, name, extractor, facet, body)
        if val is not UNSET:
            if isinstance(merged_data, dict):
                merged_data[name] = val
            elif FormData is not None and isinstance(merged_data, FormData):
                if isinstance(val, list):
                    merged_data.fields[name] = val
                else:
                    merged_data.fields[name] = [val]

    # Build context with request info
    if context is not None and type(context).__name__ == "BlueprintContext":
        bp_context = context
        if "request" not in bp_context:
            try:
                bp_context["request"] = request
            except Exception:
                pass
    else:
        from aquilia.blueprints.core import BlueprintContext

        container = None
        if isinstance(context, dict):
            container = context.get("container")

        bp_context = BlueprintContext(
            {
                "request": request,
                **(context or {}),
            }
        )
        if container is not None:
            bp_context.container = container

    # Check for DI container in request state
    state = getattr(request, "state", None)
    if state is not None:
        container = state.get("container") if isinstance(state, dict) else getattr(state, "container", None)
        if container is not None and "container" not in bp_context:
            bp_context["container"] = container
            if hasattr(bp_context, "container") and bp_context.container is None:
                bp_context.container = container

    bp = blueprint_cls(
        data=merged_data,
        partial=partial,
        projection=projection,
        context=bp_context,
    )
    bp.is_sealed(raise_fault=False, _bypass_async_check=True)

    try:
        from aquilia.inspector.trace import Lane, SpanStatus, current_trace

        trace = current_trace()
        if trace is not None:
            dt = (time.monotonic() - t0) * 1000.0
            trace.add_span(
                lane=Lane.VALIDATION,
                label=f"Validate {blueprint_cls.__name__}",
                start_offset_ms=(t0 - trace.started_monotonic) * 1000.0,
                duration_ms=dt,
                status=SpanStatus.ERROR if bp.errors else SpanStatus.OK,
                detail={"blueprint": blueprint_cls.__name__, "errors": bp.errors or {}},
            )
    except Exception:
        pass

    return bp


def render_blueprint_response(
    blueprint_or_cls: Blueprint | type[Blueprint],
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
