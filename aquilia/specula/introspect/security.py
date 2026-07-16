"""
Security scheme detection — pipeline guard heuristics.

The canonical implementation lives on :class:`~aquilia.specula.schema.builder.SpeculaBuilder`
(``_detect_all_security_schemes`` / ``_build_operation_security``); this module
exposes the guard-name heuristics for reuse and testing.
"""

from __future__ import annotations

from typing import Any

#: Guard class-name substring → security scheme key.
GUARD_SCHEME_MAP: list[tuple[str, str]] = [
    ("oauth", "oauth2"),
    ("apikey", "apiKeyAuth"),
    ("session", "cookieAuth"),
    ("basic", "basicAuth"),
    ("authguard", "bearerAuth"),
    ("authenticated", "bearerAuth"),
]


def scheme_for_guard(node: Any) -> str | None:
    """Map a pipeline guard (class, instance, or function) to a scheme key."""
    if isinstance(node, type) or callable(node) and hasattr(node, "__name__"):
        name = node.__name__.lower()
    else:
        name = type(node).__name__.lower()
    for needle, scheme in GUARD_SCHEME_MAP:
        if needle in name:
            return scheme
    if name == "auth":
        return "bearerAuth"
    return None
