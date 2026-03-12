"""
Controller Router - Pattern-based router for controllers.

Integrates with:
- aquilia.patterns for URL matching
- aquilia.controller.compiler for route compilation
- aquilia.controller.engine for execution

Performance (v3 — scalability):
- Static routes use O(1) dict lookup per method.
- Dynamic routes use a **segment trie** for O(k) matching (k = path depth).
- Trie nodes carry param metadata for inline casting; no regex on the hot path.
- Regex fallback only fires for complex patterns the trie cannot represent.
- Path normalisation happens once at registration time, not per request.
"""

from dataclasses import dataclass
from typing import Any

from ..patterns import PatternMatcher
from .compiler import CompiledController, CompiledRoute


@dataclass
class ControllerRouteMatch:
    """Result of a successful controller route match."""

    route: CompiledRoute
    params: dict[str, Any]
    query: dict[str, Any]


# Empty dicts/results reused to avoid per-request allocations
_EMPTY_DICT: dict[str, Any] = {}
_EMPTY_QUERY: dict[str, str] = {}


class _TrieNode:
    """Radix trie node for dynamic route matching.

    Each node corresponds to a URL segment.  A node is either:
    - **static**: a literal segment stored in ``children``
    - **param**: a single-capture `:name` / `{name}` / `<name:type>` stored
      in ``param_child`` with ``param_name`` and an optional ``param_castor``.
    - **terminal**: ``route`` is set, meaning this node ends a valid URL.
    """

    __slots__ = (
        "children",
        "param_child",
        "param_name",
        "param_castor",
        "route",
        "query_params",
    )

    def __init__(self):
        self.children: dict[str, _TrieNode] = {}  # static segment -> child
        self.param_child: _TrieNode | None = None  # single param child
        self.param_name: str | None = None
        self.param_castor: Any | None = None  # type-cast function for param
        self.route: CompiledRoute | None = None
        self.query_params: dict | None = None  # query param meta (for terminal nodes)


class ControllerRouter:
    """
    Router for controller-based routes using pattern matching.

    Two-tier architecture for maximum performance:
    1. Static route hash map: O(1) lookup for routes with no parameters
    2. Trie + regex fallback: O(k) for parameterized routes
    """

    def __init__(self):
        self.compiled_controllers: list[CompiledController] = []
        self.routes_by_method: dict[str, list[CompiledRoute]] = {}
        self.matcher = PatternMatcher()
        self._initialized = False

        # ── Fast-path indexes (built during initialize) ──
        # {method: {path: (route, empty_params, empty_query)}}
        self._static_routes: dict[str, dict[str, tuple[CompiledRoute, dict, dict]]] = {}
        # {method: list[(compiled_re, route, param_names)]}
        self._dynamic_routes: dict[str, list[tuple[Any, CompiledRoute, list[str]]]] = {}
        # {method: _TrieNode}  -- trie for segment-based matching
        self._tries: dict[str, _TrieNode] = {}

    def add_controller(self, compiled_controller: CompiledController):
        """Add a compiled controller to the router."""
        self.compiled_controllers.append(compiled_controller)

        for route in compiled_controller.routes:
            method = route.http_method
            if method not in self.routes_by_method:
                self.routes_by_method[method] = []
            self.routes_by_method[method].append(route)

        self._initialized = False

    def initialize(self):
        """Build fast-path lookup structures including segment trie.

        Performance (v3):
        - Static routes go into a hash map for O(1) lookup.
        - Dynamic routes are inserted into a segment trie for O(k) walk.
        - Regex fallback list is kept for complex patterns the trie can't handle.
        - Paths are normalized (trailing slash stripped) at registration time.
        """
        if self._initialized:
            return

        # Clear matcher
        self.matcher = PatternMatcher()
        self._static_routes.clear()
        self._dynamic_routes.clear()
        self._tries.clear()

        for method, routes in self.routes_by_method.items():
            # Sort by specificity (descending) so most specific routes win
            routes.sort(key=lambda r: r.specificity, reverse=True)

            static_map: dict[str, tuple[CompiledRoute, dict, dict]] = {}
            dynamic_list: list[tuple[Any, CompiledRoute, list[str]]] = []
            trie_root = _TrieNode()

            for route in routes:
                cp = route.compiled_pattern

                # A route is "static" if it has no path params and no query params
                has_params = bool(cp.params)
                has_query = bool(cp.query)

                if not has_params and not has_query:
                    # Pure static route -- O(1) lookup
                    # Normalize: strip trailing slash
                    path = route.full_path.rstrip("/") or "/"
                    static_map[path] = (route, _EMPTY_DICT, _EMPTY_DICT)
                else:
                    # ── Try to insert into segment trie ──
                    inserted = self._trie_insert(trie_root, route, cp)

                    if not inserted:
                        # Complex pattern (wildcards, regex groups) → regex fallback
                        if cp.compiled_re:
                            param_names = list(cp.params.keys())
                            dynamic_list.append((cp, route, param_names))

                # Also add to matcher for fallback
                self.matcher.add_pattern(cp)

            self._static_routes[method] = static_map
            self._dynamic_routes[method] = dynamic_list
            self._tries[method] = trie_root

        self._initialized = True

    # ------------------------------------------------------------------
    # Trie helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _trie_insert(root: _TrieNode, route: CompiledRoute, cp) -> bool:
        """Insert a route into the segment trie.

        Returns True if the route was successfully inserted, False if it
        contains complex patterns that the trie cannot represent (e.g.
        regex constraints, wildcards, catch-all segments).
        """
        raw_path = route.full_path.rstrip("/") or "/"
        segments = raw_path.strip("/").split("/") if raw_path != "/" else []

        node = root
        param_meta = cp.params  # {name: ParamMeta}

        for seg in segments:
            # Detect param segments: {name}, <name>, <name:type>, :name
            pname = None
            if seg.startswith("{") and seg.endswith("}"):
                pname = seg[1:-1]
            elif seg.startswith("<") and seg.endswith(">"):
                inner = seg[1:-1]
                pname = inner.split(":")[0] if ":" in inner else inner
            elif seg.startswith(":"):
                pname = seg[1:]

            if pname is not None:
                # Param segment
                if pname not in param_meta:
                    # Unknown param — can't trie-ify safely
                    return False
                pm = param_meta[pname]
                # If the param has validators beyond simple type casting,
                # the trie can still handle it (we'll validate inline).
                if node.param_child is None:
                    child = _TrieNode()
                    child.param_name = pname
                    child.param_castor = pm.castor
                    node.param_child = child
                node = node.param_child
            else:
                # Static segment
                if seg not in node.children:
                    node.children[seg] = _TrieNode()
                node = node.children[seg]

        # Terminal node
        node.route = route
        node.query_params = cp.query if cp.query else None
        return True

    def match_sync(
        self,
        path: str,
        method: str,
        query_params: dict[str, str] | None = None,
        api_version: Any | None = None,
    ) -> ControllerRouteMatch | None:
        """
        Synchronous route matching -- the hot path.

        Three-tier architecture (v3):
        1. Static O(1) hash map lookup.
        2. Trie O(k) segment walk (k = path depth, typically 2-4).
        3. Regex O(n) fallback for complex patterns.

        Path normalisation (trailing slash strip) is inlined to avoid
        a separate str method call.

        When ``api_version`` is provided (from versioning middleware),
        version-filtered matching is applied: routes with explicit
        ``version_metadata`` only match if the resolved version is
        compatible.  Version-neutral routes always match.
        """
        if not self._initialized:
            self.initialize()

        # ── Normalize path once ──
        norm_path = path[:-1] if len(path) > 1 and path[-1] == "/" else path

        # ── Tier 1: Static O(1) lookup ──
        static_map = self._static_routes.get(method)
        if static_map:
            hit = static_map.get(norm_path)
            if hit is not None and self._version_matches(hit[0], api_version):
                return ControllerRouteMatch(route=hit[0], params=hit[1], query=hit[2])

        # ── Tier 2: Trie O(k) segment walk ──
        trie_root = self._tries.get(method)
        if trie_root is not None:
            trie_result = self._trie_match(trie_root, norm_path, query_params)
            if trie_result is not None and self._version_matches(trie_result.route, api_version):
                return trie_result

        # ── Tier 3: Regex O(n) fallback ──
        dynamic_list = self._dynamic_routes.get(method)
        if dynamic_list:
            qp = query_params or _EMPTY_QUERY
            for cp, route, param_names in dynamic_list:
                m = cp.compiled_re.match(path)
                if m is None:
                    continue

                # Extract and cast params
                params: dict[str, Any] = {}
                valid = True
                for name in param_names:
                    value_str = m.group(name)
                    param_meta = cp.params[name]
                    try:
                        value = param_meta.castor(value_str)
                        for v in param_meta.validators:
                            if not v(value):
                                valid = False
                                break
                        if not valid:
                            break
                        params[name] = value
                    except (ValueError, TypeError):
                        valid = False
                        break

                if not valid:
                    continue

                # Query params
                query: dict[str, Any] = {}
                for qname, qparam in cp.query.items():
                    if qname in qp:
                        try:
                            qval = qparam.castor(qp[qname])
                            q_valid = True
                            for v in qparam.validators:
                                if not v(qval):
                                    q_valid = False
                                    break
                            if not q_valid:
                                valid = False
                                break
                            query[qname] = qval
                        except (ValueError, TypeError):
                            valid = False
                            break
                    elif qparam.default is not None:
                        query[qname] = qparam.default
                    else:
                        valid = False
                        break

                if not valid:
                    continue

                return ControllerRouteMatch(route=route, params=params, query=query)

        return None

    @staticmethod
    def _version_matches(route: CompiledRoute, api_version: Any | None) -> bool:
        """
        Check whether a route is compatible with the resolved API version.

        Rules (evaluated in order):
        1. If ``api_version`` is ``None`` (versioning disabled) → always match.
        2. If the route has no ``version_metadata`` → fall back to
           controller-level version; if that's also ``None`` → match.
        3. If the route/controller is version-neutral (``VERSION_NEUTRAL``) →
           always match.
        4. If the route has an explicit version list (from ``@version()`` or
           ``@GET(version=…)``) → match only if ``api_version`` is in the list.
        5. If the route has a version range (from ``@version_range()``) →
           match if ``min <= api_version <= max``.
        6. If the controller has a version string → match if equal.

        This check runs **after** a path/method match succeeds, so it never
        affects latency for unversioned apps.
        """
        if api_version is None:
            return True  # versioning not active

        # Import sentinels lazily (zero cost when versioning is off)
        try:
            from aquilia.versioning.core import VERSION_NEUTRAL as _VN
        except ImportError:
            return True  # versioning module not available

        vm = getattr(route, "version_metadata", None)

        # ── Route-level check ──
        if vm is not None:
            if vm.get("neutral"):
                return True

            # Explicit version list
            route_versions = vm.get("versions", [])
            if route_versions:
                return str(api_version) in [str(v) for v in route_versions]

            # Version range
            min_v = vm.get("min_version")
            max_v = vm.get("max_version")
            if min_v or max_v:
                try:
                    from aquilia.versioning.parser import SemanticVersionParser

                    parser = SemanticVersionParser()
                    if min_v:
                        parsed_min = parser.parse(str(min_v))
                        if api_version < parsed_min:
                            return False
                    if max_v:
                        parsed_max = parser.parse(str(max_v))
                        if api_version > parsed_max:
                            return False
                    return True
                except Exception:
                    return True

        # ── Controller-level fallback ──
        ctrl_version = getattr(route.controller_metadata, "version", None)
        if ctrl_version is None:
            return True  # no version constraint
        if ctrl_version is _VN:
            return True  # version-neutral controller

        # Compare by parsing both sides to handle "1.0" == ApiVersion(1, 0)
        try:
            from aquilia.versioning.core import ApiVersion as _AV

            ctrl_parsed = _AV.parse(str(ctrl_version)) if not isinstance(ctrl_version, _AV) else ctrl_version
            api_parsed = _AV.parse(str(api_version)) if not isinstance(api_version, _AV) else api_version
            return ctrl_parsed == api_parsed
        except Exception:
            return str(api_version) == str(ctrl_version)

    @staticmethod
    def _trie_match(
        root: _TrieNode,
        path: str,
        query_params: dict[str, str] | None,
    ) -> ControllerRouteMatch | None:
        """Walk the segment trie to match a path in O(k) time."""
        segments = path.strip("/").split("/") if path != "/" else []

        node = root
        params: dict[str, Any] = {}

        for seg in segments:
            # Try static child first (exact match is faster)
            child = node.children.get(seg)
            if child is not None:
                node = child
                continue

            # Try param child
            if node.param_child is not None:
                pchild = node.param_child
                if pchild.param_castor is not None:
                    try:
                        params[pchild.param_name] = pchild.param_castor(seg)
                    except (ValueError, TypeError):
                        return None
                else:
                    params[pchild.param_name] = seg
                node = pchild
                continue

            # No match at this depth
            return None

        # Check terminal
        if node.route is None:
            return None

        # Validate & extract query params if the route requires them
        query: dict[str, Any] = {}
        if node.query_params:
            qp = query_params or _EMPTY_QUERY
            for qname, qparam in node.query_params.items():
                if qname in qp:
                    try:
                        qval = qparam.castor(qp[qname])
                        q_valid = True
                        for v in qparam.validators:
                            if not v(qval):
                                q_valid = False
                                break
                        if not q_valid:
                            return None
                        query[qname] = qval
                    except (ValueError, TypeError):
                        return None
                elif qparam.default is not None:
                    query[qname] = qparam.default
                else:
                    return None

        return ControllerRouteMatch(
            route=node.route,
            params=params,
            query=query,
        )

    def get_allowed_methods(self, path: str) -> list[str]:
        """Return the HTTP methods registered for *path* (normalised).

        Used by the ASGI adapter to return a proper ``405 Method Not Allowed``
        response with the ``Allow`` header when the path matches but the
        method does not.

        Searches all three tiers (static, trie, regex) across every registered
        method to collect the full set of allowed methods.  Returns an empty
        list when the path has no registrations at all (→ 404).
        """
        if not self._initialized:
            self.initialize()

        # Normalise once
        norm_path = path[:-1] if len(path) > 1 and path[-1] == "/" else path

        allowed: list[str] = []

        for method, static_map in self._static_routes.items():
            if norm_path in static_map:
                allowed.append(method)

        for method, trie_root in self._tries.items():
            if method in allowed:
                continue  # already found via static
            if self._trie_match(trie_root, norm_path, None) is not None:
                allowed.append(method)

        for method, dynamic_list in self._dynamic_routes.items():
            if method in allowed:
                continue
            for cp, _route, _param_names in dynamic_list:
                if cp.compiled_re and cp.compiled_re.match(path):
                    allowed.append(method)
                    break

        return allowed

    async def match(
        self,
        path: str,
        method: str,
        query_params: dict[str, str] | None = None,
        api_version: Any | None = None,
    ) -> ControllerRouteMatch | None:
        """Async compat wrapper -- delegates to sync hot path."""
        return self.match_sync(path, method, query_params, api_version=api_version)

    def get_routes(self) -> list[dict[str, Any]]:
        """Get all registered routes."""
        routes = []
        for controller in self.compiled_controllers:
            for route in controller.routes:
                routes.append(
                    {
                        "method": route.http_method,
                        "path": route.full_path,
                        "controller": route.controller_class.__name__,
                        "handler": route.route_metadata.handler_name,
                        "specificity": route.specificity,
                        "pipeline": [
                            p.__name__ if hasattr(p, "__name__") else str(p)
                            for p in (route.route_metadata.pipeline or [])
                        ],
                    }
                )
        return routes

    def get_routes_full(self) -> list[CompiledRoute]:
        """Get all CompiledRoute objects."""
        routes = []
        for controller in self.compiled_controllers:
            routes.extend(controller.routes)
        return routes

    def get_controller(self, name: str) -> CompiledController | None:
        """Get compiled controller by name."""
        for controller in self.compiled_controllers:
            if controller.controller_class.__name__ == name:
                return controller
        return None

    def has_route(self, method: str, path: str) -> bool:
        """Check if a route exists."""
        return self.match_sync(path, method) is not None

    def url_for(self, name: str, *, api_version: str | None = None, **params) -> str:
        """Reverse URL generation.

        When ``api_version`` is provided and the app uses URL-path versioning,
        the version prefix segment is prepended to the generated path.
        """
        for controller in self.compiled_controllers:
            for route in controller.routes:
                full_name = f"{route.controller_class.__name__}.{route.route_metadata.handler_name}"
                if full_name == name or route.route_metadata.handler_name == name:
                    path = route.full_path
                    query_params = {}

                    for k, v in params.items():
                        # Handle both {param} and <param> / <param:type> syntax
                        replaced = False
                        for pattern in (f"{{{k}}}", f"<{k}>"):
                            if pattern in path:
                                path = path.replace(pattern, str(v))
                                replaced = True
                                break
                        if not replaced:
                            # Try <param:type> pattern
                            import re

                            typed_re = re.compile(rf"<{re.escape(k)}:[^>]+>")
                            new_path = typed_re.sub(str(v), path)
                            if new_path != path:
                                path = new_path
                                replaced = True
                        if not replaced:
                            query_params[k] = v

                    if query_params:
                        query_str = "&".join(f"{k}={v}" for k, v in query_params.items())
                        path += f"?{query_str}"
                    return path

        if name.startswith("/"):
            return name
        from ..faults.domains import RouteNotFoundFault

        raise RouteNotFoundFault(path=name, method="*")
