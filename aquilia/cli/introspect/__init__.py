"""Introspection facade -- the only place the CLI touches framework internals.

Previously six CLI modules reached into private APIs (``WorkspaceGenerator._discover_modules``)
across ~20 call sites. Confining that coupling here means a framework refactor
breaks one module instead of twenty.
"""

from aquilia.cli.introspect.routes import (
    ControllerRoutes,
    RouteInfo,
    collect_routes,
    extract_routes,
)

__all__ = [
    "ControllerRoutes",
    "RouteInfo",
    "collect_routes",
    "extract_routes",
]
