"""
Multi-version OpenAPI spec generation.

Integrates with ``aquilia.versioning`` to filter routes by their version
binding. VERSION_NEUTRAL routes appear in every version's spec. Degrades
gracefully to a single "latest" spec when versioning is inactive.
"""

from __future__ import annotations

import logging
from typing import Any

from aquilia.controller.compiler import CompiledRoute
from aquilia.controller.router import ControllerRouter

from ..config import SpeculaConfig
from ..schema.builder import SpeculaBuilder

logger = logging.getLogger("aquilia.specula.versions")


class VersionedSpecBuilder:
    """
    Produces one OpenAPI 3.1.0 spec per declared API version.

    Usage::

        vsb = VersionedSpecBuilder(config, version_strategy)
        specs = vsb.build_all(router)
        # {"1.0": {...}, "2.0": {...}, "latest": {...}}
    """

    def __init__(self, config: SpeculaConfig, version_strategy: Any = None):
        self.config = config
        self.version_strategy = version_strategy

    # ── Public API ─────────────────────────────────────────────────────

    def declared_versions(self) -> list[str]:
        """All version strings declared in the version graph (empty if inactive)."""
        strategy = self.version_strategy
        if strategy is None:
            return []
        graph = getattr(strategy, "graph", None)
        versions = getattr(graph, "versions", None) if graph is not None else None
        if versions is None:
            versions = getattr(strategy, "versions", None)
        if not versions:
            return []
        return [str(v) for v in versions]

    def build_all(self, router: ControllerRouter) -> dict[str, dict[str, Any]]:
        """Build specs for all declared versions plus a ``latest`` alias."""
        specs: dict[str, dict[str, Any]] = {}
        for version in self.declared_versions():
            specs[version] = self.build_for_version(router, version)
        # 'latest' is always available — the unfiltered spec
        specs["latest"] = SpeculaBuilder(self.config).build(router)
        return specs

    def build_for_version(self, router: ControllerRouter, version: str) -> dict[str, Any]:
        """Build a spec filtered to routes that serve the given version."""
        from ..faults import VersionNotFoundFault

        declared = self.declared_versions()
        if version not in ("latest", *declared):
            raise VersionNotFoundFault(
                f"API version '{version}' not found in the version graph",
                detail={"version": version, "declared": declared},
            )

        routes = router.get_routes_full()
        if version != "latest":
            routes = [r for r in routes if self._is_route_in_version(r, version)]

        builder = SpeculaBuilder(self.config)
        spec = builder.build(router, routes=routes)
        spec["info"]["x-specula-api-version"] = version
        return spec

    # ── Filtering ──────────────────────────────────────────────────────

    def _is_route_in_version(self, route: CompiledRoute, version: str) -> bool:
        """True if the route should appear in the given version's spec."""
        # Route-level @version() / @version_neutral metadata
        version_meta = getattr(route, "version_metadata", None)
        if version_meta:
            if version_meta.get("neutral"):
                return True
            versions = [str(v) for v in version_meta.get("versions", [])]
            if versions:
                return version in versions
            min_v = version_meta.get("min_version")
            max_v = version_meta.get("max_version")
            if min_v or max_v:
                return self._in_range(version, min_v, max_v)

        # RouteMetadata.version
        route_version = getattr(route.route_metadata, "version", None)
        if route_version is not None:
            return str(route_version) == version

        # Controller-level version
        ctrl_version = getattr(route.controller_class, "version", None)
        if ctrl_version is not None:
            try:
                from aquilia.versioning.core import VERSION_NEUTRAL

                if ctrl_version is VERSION_NEUTRAL:
                    return True
            except ImportError:
                pass
            return str(ctrl_version) == version

        # No binding = version-neutral: appears everywhere
        return True

    @staticmethod
    def _in_range(version: str, min_v: Any, max_v: Any) -> bool:
        """Numeric-tuple range comparison; falls back to string equality."""

        def parse(v: Any) -> tuple[int, ...] | None:
            try:
                return tuple(int(part) for part in str(v).split("."))
            except ValueError:
                return None

        target = parse(version)
        if target is None:
            return str(version) in (str(min_v), str(max_v))
        low = parse(min_v) if min_v else None
        high = parse(max_v) if max_v else None
        if low and target < low:
            return False
        return not (high and target > high)
