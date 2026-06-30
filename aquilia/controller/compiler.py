"""
Controller Compiler - Compiles controllers to patterns and routes.

Integrates with:
- aquilia.patterns for URL pattern compilation
- aquilia.controller.metadata for controller introspection
- aquilia.router for route registration
"""

import inspect
from dataclasses import dataclass
from typing import Any

from ..patterns import (
    CompiledPattern,
    PatternCompiler,
    PatternSemanticError,
    parse_pattern,
)
from .metadata import (
    ControllerMetadata,
    RouteMetadata,
    extract_controller_metadata,
)


@dataclass
class CompiledRoute:
    """A compiled controller route with pattern and handler."""

    controller_class: type
    controller_metadata: ControllerMetadata
    route_metadata: RouteMetadata
    compiled_pattern: CompiledPattern
    full_path: str
    http_method: str
    specificity: int
    app_name: str | None = None
    version_metadata: dict[str, Any] | None = None
    bound_version: Any | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for caching."""
        return {
            "controller": f"{self.controller_class.__module__}:{self.controller_class.__name__}",
            "route_name": self.route_metadata.handler_name,
            "path": self.full_path,
            "method": self.http_method,
            "specificity": self.specificity,
            "pattern": self.compiled_pattern.to_dict(),
            "bound_version": str(self.bound_version) if self.bound_version else None,
        }


@dataclass
class CompiledController:
    """A fully compiled controller with all routes."""

    controller_class: type
    metadata: ControllerMetadata
    routes: list[CompiledRoute]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "controller": f"{self.controller_class.__module__}:{self.controller_class.__name__}",
            "prefix": self.metadata.prefix,
            "routes": [r.to_dict() for r in self.routes],
        }


class ControllerCompiler:
    """
    Compiles controllers into executable routes with pattern matching.

    This is the bridge between:
    - Controller metadata extraction
    - Pattern compilation (aquilia.patterns)
    - Route registration
    """

    def __init__(self):
        self.pattern_compiler = PatternCompiler()
        self.compiled_controllers: dict[str, CompiledController] = {}
        self.route_conflicts: list[tuple[str, str]] = []

    def compile_controller(
        self,
        controller_class: type,
        base_prefix: str | None = None,
        version_strategy: Any | None = None,
        module_versioning: dict[str, Any] | None = None,
    ) -> CompiledController:
        """
        Compile a controller class into routes.

        Args:
            controller_class: Controller class to compile
            base_prefix: Optional base prefix from module/app
            version_strategy: Optional VersionStrategy for URL baking
            module_versioning: Optional per-module versioning configuration override

        Returns:
            CompiledController with all routes

        Raises:
            PatternSemanticError: If patterns are invalid
        """
        # Extract metadata
        module_path = f"{controller_class.__module__}:{controller_class.__name__}"
        metadata = extract_controller_metadata(controller_class, module_path)

        # Compile each route
        compiled_routes = []

        is_structural = False
        if version_strategy is not None:
            if version_strategy.is_structural_url_versioning:
                mod_enabled = True
                if module_versioning is not None:
                    mod_enabled = module_versioning.get("enabled", True)
                if mod_enabled:
                    is_structural = True

        for route_meta in metadata.routes:
            try:
                if is_structural:
                    constraint = self._extract_version_constraint(controller_class, metadata, route_meta)
                    if constraint[0] == "neutral":
                        compiled_route = self._compile_route(
                            controller_class,
                            metadata,
                            route_meta,
                            base_prefix=base_prefix,
                        )
                        compiled_route.bound_version = None
                        compiled_routes.append(compiled_route)
                    else:
                        versions_to_compile = []
                        if constraint[0] == "none" and module_versioning and module_versioning.get("auto_version_unmarked", False):
                            versions_to_compile = list(version_strategy.graph.active_versions)
                        elif constraint[0] != "none":
                            versions_to_compile = self._expand_versions(constraint, version_strategy)
                            if not versions_to_compile and constraint[0] == "range":
                                import logging
                                logger = logging.getLogger("aquilia.controller.compiler")
                                logger.warning(
                                    f"Range constraint {constraint[1]} for route {route_meta.handler_name} in "
                                    f"{controller_class.__name__} expanded to empty active versions list."
                                )
                        
                        if not versions_to_compile and constraint[0] == "none":
                            # Compile once, unprefixed
                            compiled_route = self._compile_route(
                                controller_class,
                                metadata,
                                route_meta,
                                base_prefix=base_prefix,
                            )
                            compiled_route.bound_version = None
                            compiled_routes.append(compiled_route)
                        else:
                            for v in versions_to_compile:
                                position_override = None
                                if module_versioning is not None:
                                    position_override = module_versioning.get("position")
                                effective_base_prefix = version_strategy.build_version_prefix(
                                    base_prefix or "", v, position=position_override
                                )
                                compiled_route = self._compile_route(
                                    controller_class,
                                    metadata,
                                    route_meta,
                                    base_prefix=effective_base_prefix,
                                )
                                compiled_route.bound_version = v
                                compiled_routes.append(compiled_route)
                else:
                    compiled_route = self._compile_route(
                        controller_class,
                        metadata,
                        route_meta,
                        base_prefix=base_prefix,
                    )
                    compiled_route.bound_version = None
                    compiled_routes.append(compiled_route)
            except Exception as e:
                raise PatternSemanticError(
                    f"Failed to compile route {route_meta.handler_name} in {controller_class.__name__}: {e}",
                    file=inspect.getfile(controller_class),
                )

        # Sort routes by specificity (descending)
        compiled_routes.sort(key=lambda r: r.specificity, reverse=True)

        compiled_controller = CompiledController(
            controller_class=controller_class,
            metadata=metadata,
            routes=compiled_routes,
        )

        # Cache it
        controller_key = f"{controller_class.__module__}:{controller_class.__name__}"
        self.compiled_controllers[controller_key] = compiled_controller

        return compiled_controller

    def _compile_route(
        self,
        controller_class: type,
        controller_metadata: ControllerMetadata,
        route_metadata: RouteMetadata,
        base_prefix: str | None = None,
    ) -> CompiledRoute:
        """Compile a single route."""
        from aquilia.utils.urls import join_paths

        # Build components
        base = base_prefix or ""
        ctrl_prefix = controller_metadata.prefix or ""
        route_path = route_metadata.path_template or ""

        # Robust join
        full_path = join_paths(base, ctrl_prefix, route_path)

        # Convert to pattern format (< > style)
        pattern_path = self._convert_to_pattern_syntax(full_path, route_metadata)

        # Parse pattern
        try:
            ast = parse_pattern(pattern_path, inspect.getfile(controller_class))
        except Exception as e:
            raise PatternSemanticError(
                f"Failed to parse pattern '{pattern_path}': {e}",
                file=inspect.getfile(controller_class),
            )

        # Compile pattern
        compiled_pattern = self.pattern_compiler.compile(ast)

        # Calculate specificity
        specificity = route_metadata.specificity

        return CompiledRoute(
            controller_class=controller_class,
            controller_metadata=controller_metadata,
            route_metadata=route_metadata,
            compiled_pattern=compiled_pattern,
            full_path=full_path,
            http_method=route_metadata.http_method,
            specificity=specificity,
        )

    def _convert_to_pattern_syntax(
        self,
        path: str,
        route_metadata: RouteMetadata,
    ) -> str:
        """
        Convert path with parameters to pattern syntax.

        Converts:
        - /users/{id} -> /users/<id:int>
        - /posts/{slug} -> /posts/<slug:str>

        Uses parameter metadata to determine types.
        """
        pattern = path

        # Extract path parameters from metadata
        param_map = {}
        for param in route_metadata.parameters:
            if param.source == "path":
                # Determine pattern type
                type_str = self._python_type_to_pattern_type(param.type)
                param_map[param.name] = type_str

        # Replace {param} with <param:type>
        import re

        def replace_param(match):
            param_name = match.group(1)
            # Check for type annotation in original: {id:int}
            if ":" in param_name:
                name, type_hint = param_name.split(":", 1)
                return f"<{name}:{type_hint}>"
            else:
                # Use type from metadata
                param_type = param_map.get(param_name, "str")
                return f"<{param_name}:{param_type}>"

        pattern = re.sub(r"\{([^}]+)\}", replace_param, pattern)

        return pattern

    def _python_type_to_pattern_type(self, annotation: Any) -> str:
        """Convert Python type annotation to pattern type string."""
        if annotation is int or annotation == "int":
            return "int"
        elif annotation is float or annotation == "float":
            return "float"
        elif annotation is bool or annotation == "bool":
            return "bool"
        elif annotation is str or annotation == "str":
            return "str"
        else:
            # Default to string
            return "str"

    def validate_route_tree(self, compiled_controllers: list[CompiledController]) -> list[dict[str, Any]]:
        """
        Validate the entire compiled route tree for conflicts.

        This is the preferred validation method as it accounts for
        applied prefixes and mounted locations.

        Args:
            compiled_controllers: List of already compiled controllers

        Returns:
            List of conflict descriptions
        """
        conflicts = []
        routes_by_method: dict[str, list[CompiledRoute]] = {}

        # Group by method
        for compiled in compiled_controllers:
            for route in compiled.routes:
                key = route.http_method
                if key not in routes_by_method:
                    routes_by_method[key] = []
                routes_by_method[key].append(route)

        # Check each method's routes for conflicts
        for method, routes in routes_by_method.items():
            for i, route1 in enumerate(routes):
                for route2 in routes[i + 1 :]:
                    if self._routes_conflict(route1, route2):
                        conflicts.append(
                            {
                                "method": method,
                                "route1": {
                                    "controller": route1.controller_class.__name__,
                                    "path": route1.full_path,
                                    "handler": route1.route_metadata.handler_name,
                                    "module": route1.controller_class.__module__,
                                },
                                "route2": {
                                    "controller": route2.controller_class.__name__,
                                    "path": route2.full_path,
                                    "handler": route2.route_metadata.handler_name,
                                    "module": route2.controller_class.__module__,
                                },
                                "reason": "Ambiguous patterns could match same request",
                            }
                        )
        return conflicts

    def check_conflicts(self, controllers: list[type]) -> list[dict[str, Any]]:
        """
        Check for route conflicts across controllers (Legacy).

        WARNING: This assumes NO module prefixes. For robust checking,
        use validate_route_tree() with compiled controllers.

        Args:
            controllers: List of controller classes

        Returns:
            List of conflict descriptions
        """
        # Compile all controllers (without prefixes)
        compiled_list = [self.compile_controller(ctrl) for ctrl in controllers]
        return self.validate_route_tree(compiled_list)

    def _extract_version_constraint(
        self,
        controller_class: type,
        controller_metadata: ControllerMetadata,
        route_metadata: RouteMetadata,
    ) -> tuple[str, Any]:
        """
        Extract version constraint for a route.
        Returns:
            ("neutral", None)
            ("set", frozenset[str])
            ("range", (min_str_or_None, max_str_or_None))
            ("none", None)
        """
        from aquilia.versioning.core import VERSION_NEUTRAL
        
        handler = getattr(controller_class, route_metadata.handler_name, None)
        version_meta = getattr(handler, "__version_metadata__", None) if handler else None
        
        if version_meta is not None:
            if version_meta.get("neutral") is True:
                return "neutral", None
            if "range" in version_meta:
                r = version_meta["range"]
                return "range", (r.get("min"), r.get("max"))
            if "versions" in version_meta:
                versions = version_meta["versions"]
                if len(versions) == 1 and versions[0] is VERSION_NEUTRAL:
                    return "neutral", None
                versions_str = [str(v) for v in versions if v is not VERSION_NEUTRAL]
                if versions_str:
                    return "set", frozenset(versions_str)
                    
        if route_metadata.version is not None:
            v = route_metadata.version
            if v is VERSION_NEUTRAL:
                return "neutral", None
            if isinstance(v, (list, tuple, set, frozenset)):
                versions_str = [str(x) for x in v if x is not VERSION_NEUTRAL]
                return "set", frozenset(versions_str)
            return "set", frozenset([str(v)])
            
        if controller_metadata.version is not None:
            v = controller_metadata.version
            if v is VERSION_NEUTRAL:
                return "neutral", None
            if isinstance(v, (list, tuple, set, frozenset)):
                versions_str = [str(x) for x in v if x is not VERSION_NEUTRAL]
                return "set", frozenset(versions_str)
            return "set", frozenset([str(v)])
            
        return "none", None

    def _versions_overlap(self, c1: tuple[str, Any], c2: tuple[str, Any]) -> bool:
        kind1, payload1 = c1
        kind2, payload2 = c2
        if kind1 in ("none", "neutral") or kind2 in ("none", "neutral"):
            return True
            
        from aquilia.versioning.parser import SemanticVersionParser
        parser = SemanticVersionParser()
        
        def as_set(c):
            kind, payload = c
            if kind == "set":
                return {parser.parse(v) for v in payload}
            return None
            
        if kind1 == "set" and kind2 == "set":
            return bool(as_set(c1) & as_set(c2))
            
        # Range <-> Set
        if (kind1 == "range" and kind2 == "set") or (kind1 == "set" and kind2 == "range"):
            rng = payload1 if kind1 == "range" else payload2
            st = payload2 if kind2 == "set" else payload1
            
            min_v, max_v = rng
            parsed_min = parser.parse(min_v) if min_v else None
            parsed_max = parser.parse(max_v) if max_v else None
            
            parsed_set = {parser.parse(v) for v in st}
            for v in parsed_set:
                if parsed_min and v < parsed_min:
                    continue
                if parsed_max and v >= parsed_max:
                    continue
                return True
            return False
            
        # Range <-> Range
        if kind1 == "range" and kind2 == "range":
            min1, max1 = payload1
            min2, max2 = payload2
            
            parsed_min1 = parser.parse(min1) if min1 else None
            parsed_max1 = parser.parse(max1) if max1 else None
            parsed_min2 = parser.parse(min2) if min2 else None
            parsed_max2 = parser.parse(max2) if max2 else None
            
            if parsed_min1 is None:
                intersect_start = parsed_min2
            elif parsed_min2 is None:
                intersect_start = parsed_min1
            else:
                intersect_start = max(parsed_min1, parsed_min2)
                
            if parsed_max1 is None:
                intersect_end = parsed_max2
            elif parsed_max2 is None:
                intersect_end = parsed_max1
            else:
                intersect_end = min(parsed_max1, parsed_max2)
                
            if intersect_start is None or intersect_end is None:
                return True
                
            return intersect_start < intersect_end
            
        return True

    def _expand_versions(self, constraint: tuple[str, Any], version_strategy: Any) -> list[Any]:
        kind, payload = constraint
        if kind == "none" or kind == "neutral":
            return []
            
        active_versions = version_strategy.graph.active_versions
        parser = version_strategy.parser
        
        matched = []
        if kind == "set":
            parsed_set = {parser.parse(v) for v in payload}
            for v in active_versions:
                if v in parsed_set:
                    matched.append(v)
        elif kind == "range":
            min_v, max_v = payload
            parsed_min = parser.parse(min_v) if min_v else None
            parsed_max = parser.parse(max_v) if max_v else None
            for v in active_versions:
                if parsed_min and v < parsed_min:
                    continue
                if parsed_max and v >= parsed_max:
                    continue
                matched.append(v)
        return matched

    def _routes_conflict(self, route1: CompiledRoute, route2: CompiledRoute) -> bool:
        """Check if two routes conflict (ambiguous matching)."""
        # Check version overlap first
        c1 = self._extract_version_constraint(route1.controller_class, route1.controller_metadata, route1.route_metadata)
        c2 = self._extract_version_constraint(route2.controller_class, route2.controller_metadata, route2.route_metadata)
        if not self._versions_overlap(c1, c2):
            return False

        # Same exact path
        if route1.full_path == route2.full_path:
            return True

        # Check if patterns could overlap
        parts1 = list(filter(None, route1.full_path.split("/")))
        parts2 = list(filter(None, route2.full_path.split("/")))

        if len(parts1) != len(parts2):
            return False

        # Helper to extract type from "<name:type>" or return None if static
        def get_segment_info(segment):
            if segment.startswith("<") and segment.endswith(">"):
                content = segment[1:-1]
                if ":" in content:
                    _, type_str = content.split(":", 1)
                    return "dynamic", type_str
                return "dynamic", "str"
            return "static", segment

        has_mixed_static_dynamic = False

        # Check each segment
        for p1, p2 in zip(parts1, parts2, strict=False):
            kind1, info1 = get_segment_info(p1)
            kind2, info2 = get_segment_info(p2)

            # Both static
            if kind1 == "static" and kind2 == "static":
                if info1 != info2:
                    return False  # Distinct static paths

            # One static, one dynamic -- these are NOT true conflicts.
            # The router should prefer static matches over dynamic ones.
            elif kind1 == "static" and kind2 == "dynamic":
                if info2 == "int" and not info1.isdigit():
                    return False  # Static is not int -- no overlap
                has_mixed_static_dynamic = True

            elif kind1 == "dynamic" and kind2 == "static":
                if info1 == "int" and not info2.isdigit():
                    return False  # Static is not int
                has_mixed_static_dynamic = True

            # Both dynamic
            else:
                pass

        # If ambiguity comes from static-vs-dynamic segments, it's not a
        # true conflict -- the router resolves it via static-first priority.
        if has_mixed_static_dynamic:
            return False

        # If we got here, all segments potentially overlap (both-dynamic)
        return True

    def export_routes(self, controllers: list[CompiledController]) -> dict[str, Any]:
        """
        Export all compiled routes for inspection/debugging.

        Args:
            controllers: List of CompiledController

        Returns:
            Dict with controllers and routes
        """
        return {
            "controllers": [c.to_dict() for c in controllers],
            "total_routes": sum(len(c.routes) for c in controllers),
            "conflicts": self.validate_route_tree(controllers),
        }
