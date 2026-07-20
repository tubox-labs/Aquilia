"""
Python type → JSON Schema 3.1.0 mapper.

Fully OpenAPI 3.1.0 compliant: uses ``oneOf`` with ``{"type": "null"}`` for
optionals rather than the 3.0-era ``nullable: true``.
"""

from __future__ import annotations

import inspect
import logging
import types as _types
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Annotated, Any, Literal, Union, get_args, get_origin
from uuid import UUID

logger = logging.getLogger("aquilia.specula.types")

_SIMPLE_MAP: dict[Any, dict[str, Any]] = {
    str: {"type": "string"},
    int: {"type": "integer", "format": "int64"},
    float: {"type": "number", "format": "double"},
    bool: {"type": "boolean"},
    bytes: {"type": "string", "format": "binary"},
    type(None): {"type": "null"},
    datetime: {"type": "string", "format": "date-time"},
    date: {"type": "string", "format": "date"},
    time: {"type": "string", "format": "time"},
    timedelta: {"type": "string", "format": "duration"},
    UUID: {"type": "string", "format": "uuid"},
    Decimal: {"type": "string", "format": "decimal"},
}


def python_type_to_schema(tp: Any) -> dict[str, Any]:
    """
    Convert a Python type annotation to a JSON Schema 3.1.0 fragment.

    Args:
        tp: A Python type, typing construct, or annotation.

    Returns:
        A JSON Schema dict. Unknown types map to ``{"type": "object"}``.
    """
    if tp is inspect.Parameter.empty or tp is Any or tp is None:
        return {}

    if tp in _SIMPLE_MAP:
        return dict(_SIMPLE_MAP[tp])

    origin = get_origin(tp)
    args = get_args(tp)

    # Literal["a", "b"] → enum
    if origin is Literal:
        return {"enum": list(args)}

    # Optional[X] / Union[...] / X | Y → oneOf (3.1.0 style, no nullable:true)
    if origin is Union or origin is _types.UnionType:
        return {"oneOf": [python_type_to_schema(a) for a in args]}

    # list[X] / set[X]
    if origin in (list, set, frozenset):
        item = python_type_to_schema(args[0]) if args else {}
        schema: dict[str, Any] = {"type": "array", "items": item}
        if origin in (set, frozenset):
            schema["uniqueItems"] = True
        return schema

    # tuple[X, Y] → prefixItems
    if origin is tuple:
        if args and Ellipsis not in args:
            return {
                "type": "array",
                "prefixItems": [python_type_to_schema(a) for a in args],
                "minItems": len(args),
                "maxItems": len(args),
            }
        item = python_type_to_schema(args[0]) if args else {}
        return {"type": "array", "items": item}

    # dict[str, X]
    if origin is dict:
        val = python_type_to_schema(args[1]) if len(args) > 1 else {}
        return {"type": "object", "additionalProperties": val}

    # Annotated[X, meta] → unwrap, merge recognisable metadata dicts
    if origin is Annotated:
        base = python_type_to_schema(args[0])
        for meta in args[1:]:
            if isinstance(meta, dict):
                base.update(meta)
        return base

    # Dataclass / annotated class → $ref
    if isinstance(tp, type) and hasattr(tp, "__annotations__"):
        return {"$ref": f"#/components/schemas/{tp.__name__}"}

    logger.debug("Specula: unknown type %r mapped to object", tp)
    return {"type": "object"}
