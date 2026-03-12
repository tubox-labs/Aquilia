"""
Controller Metadata Extraction

Static analysis of Controller classes to extract routing metadata.
Used by `aq compile` to generate patterns.crous without runtime imports.
"""

import inspect
from dataclasses import dataclass, field
from typing import Any, get_args, get_origin, get_type_hints


@dataclass
class ParameterMetadata:
    """
    Metadata for a route method parameter.

    Attributes:
        name: Parameter name
        type: Parameter type annotation
        default: Default value if any
        source: Where to get value: 'path', 'query', 'body', 'header', 'di'
        required: Whether parameter is required
        pattern: Regex pattern for validation (path params)
    """

    name: str
    type: type
    default: Any = inspect.Parameter.empty
    source: str = "query"  # 'path', 'query', 'body', 'header', 'di'
    required: bool = True
    pattern: str | None = None

    @property
    def has_default(self) -> bool:
        return self.default is not inspect.Parameter.empty


@dataclass
class RouteMetadata:
    """
    Metadata for a single route (controller method).

    Attributes:
        http_method: GET, POST, etc.
        path_template: URL path with parameters (e.g., "/users/<id:int>")
        full_path: Prefix + path_template
        handler_name: Method name
        parameters: List of method parameters
        pipeline: Method-level pipeline nodes
        summary: OpenAPI summary
        description: OpenAPI description
        tags: OpenAPI tags
        deprecated: Whether route is deprecated
        response_model: Response type
        status_code: Default status code
        specificity: Route specificity score (for conflict resolution)
    """

    http_method: str
    path_template: str
    full_path: str
    handler_name: str
    parameters: list[ParameterMetadata] = field(default_factory=list)
    pipeline: list[Any] = field(default_factory=list)
    summary: str = ""
    description: str = ""
    tags: list[str] = field(default_factory=list)
    deprecated: bool = False
    response_model: type | None = None
    status_code: int = 200
    specificity: int = 0
    version: Any | None = None  # API version: str, list, or sentinel
    _raw_metadata: dict[str, Any] = field(default_factory=dict, repr=False)

    def compute_specificity(self) -> int:
        """
        Compute route specificity for conflict resolution.

        Higher specificity = more specific route.
        Static segments > typed params > untyped params > wildcards.

        Returns:
            Specificity score
        """
        score = 0
        segments = self.full_path.strip("/").split("/")

        for segment in segments:
            if self._is_static(segment):
                score += 100  # Static segment
            elif self._is_typed_param(segment):
                score += 50  # Typed parameter
            elif self._is_param(segment):
                score += 25  # Untyped parameter
            else:
                score += 1  # Wildcard

        self.specificity = score
        return score

    @staticmethod
    def _is_static(segment: str) -> bool:
        """Check if segment is static."""
        return not (segment.startswith("<") or segment.startswith("{"))

    @staticmethod
    def _is_typed_param(segment: str) -> bool:
        """Check if segment is typed parameter."""
        if segment.startswith("<") and segment.endswith(">"):
            return ":" in segment
        if segment.startswith("{") and segment.endswith("}"):
            return ":" in segment
        return False

    @staticmethod
    def _is_param(segment: str) -> bool:
        """Check if segment is parameter."""
        return (segment.startswith("<") and segment.endswith(">")) or (
            segment.startswith("{") and segment.endswith("}")
        )


@dataclass
class ControllerMetadata:
    """
    Complete metadata for a Controller class.

    Attributes:
        class_name: Controller class name
        module_path: Full import path (e.g., "modules.users.flows:UsersController")
        prefix: URL prefix for all routes
        routes: List of route metadata
        pipeline: Class-level pipeline
        tags: Class-level OpenAPI tags
        instantiation_mode: "per_request" or "singleton"
        constructor_params: Constructor DI parameters
    """

    class_name: str
    module_path: str
    prefix: str
    routes: list[RouteMetadata] = field(default_factory=list)
    pipeline: list[Any] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    instantiation_mode: str = "per_request"
    constructor_params: list[ParameterMetadata] = field(default_factory=list)
    version: Any | None = None  # Controller-level API version

    def get_route(self, method: str, path: str) -> RouteMetadata | None:
        """Find route by method and path."""
        for route in self.routes:
            if route.http_method == method and route.full_path == path:
                return route
        return None

    def has_conflict(self, other: "ControllerMetadata") -> tuple | None:
        """
        Check for route conflicts with another controller.

        Returns:
            Tuple of (route1, route2) if conflict exists, None otherwise
        """
        for r1 in self.routes:
            for r2 in other.routes:
                if r1.http_method == r2.http_method and r1.full_path == r2.full_path:
                    return (r1, r2)
        return None


def extract_controller_metadata(
    controller_class: type,
    module_path: str,
) -> ControllerMetadata:
    """
    Extract metadata from a Controller class.

    This is called during `aq compile` to analyze controller structure
    without executing business logic.

    Args:
        controller_class: The Controller class to analyze
        module_path: Full import path

    Returns:
        ControllerMetadata with all routes and configuration

    Example:
        metadata = extract_controller_metadata(
            UsersController,
            "modules.users.flows:UsersController"
        )
    """
    # Get class-level attributes
    prefix = getattr(controller_class, "prefix", "")

    # Robustness: Handle incorrect prefix types
    if isinstance(prefix, list):
        prefix = str(prefix[0]) if prefix else ""
    elif not isinstance(prefix, str) and prefix is not None:
        prefix = str(prefix)

    # Ensure it's not None
    if prefix is None:
        prefix = ""
    pipeline = getattr(controller_class, "pipeline", [])
    tags = getattr(controller_class, "tags", [])
    instantiation_mode = getattr(controller_class, "instantiation_mode", "per_request")
    version = getattr(controller_class, "version", None)

    # Extract constructor parameters for DI
    constructor_params = _extract_constructor_params(controller_class)

    # Extract routes from decorated methods
    routes = []
    for _name, method in inspect.getmembers(controller_class, predicate=inspect.isfunction):
        if hasattr(method, "__route_metadata__"):
            for route_meta in method.__route_metadata__:
                route = _extract_route_metadata(
                    method,
                    route_meta,
                    prefix,
                    pipeline,
                    tags,
                )
                routes.append(route)

    # Compute specificity for all routes
    for route in routes:
        route.compute_specificity()

    return ControllerMetadata(
        class_name=controller_class.__name__,
        module_path=module_path,
        prefix=prefix,
        routes=routes,
        pipeline=pipeline,
        tags=tags,
        instantiation_mode=instantiation_mode,
        constructor_params=constructor_params,
        version=version,
    )


def _extract_constructor_params(controller_class: type) -> list[ParameterMetadata]:
    """Extract constructor parameters for DI injection."""
    params = []

    try:
        sig = inspect.signature(controller_class.__init__)
        type_hints = get_type_hints(controller_class.__init__, include_extras=True)

        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue

            param_type = type_hints.get(param_name, Any)

            # Check if it's Annotated[T, Inject(...)]
            if get_origin(param_type) is not None:
                # Handle Annotated types
                origin = get_origin(param_type)
                if Annotated is not None and origin is Annotated:
                    pass

            params.append(
                ParameterMetadata(
                    name=param_name,
                    type=param_type,
                    default=param.default,
                    source="di",
                    required=param.default == inspect.Parameter.empty,
                )
            )
    except Exception:
        # If signature extraction fails, return empty list
        pass

    return params


def _extract_route_metadata(
    method: Any,
    route_meta: dict[str, Any],
    prefix: str,
    class_pipeline: list[Any],
    class_tags: list[str],
) -> RouteMetadata:
    """Extract route metadata from decorated method."""

    # Get path template
    path_template = route_meta["path"]
    if path_template is None:
        # Derive from method name: list -> /, get -> /<id>
        func_name = route_meta["func_name"]
        path_template = "/" if func_name == "list" or func_name == "index" else "/<id>"

    # Combine prefix and path
    full_path = f"{prefix.rstrip('/')}/{path_template.lstrip('/')}"
    full_path = full_path.rstrip("/") or "/"

    # Extract method parameters
    parameters = _extract_method_params(method, route_meta["signature"], full_path)

    # Merge pipelines and tags
    method_pipeline = route_meta["pipeline"] or []
    merged_pipeline = class_pipeline + method_pipeline
    merged_tags = class_tags + route_meta["tags"]

    return RouteMetadata(
        http_method=route_meta["http_method"],
        path_template=path_template,
        full_path=full_path,
        handler_name=route_meta["func_name"],
        parameters=parameters,
        pipeline=merged_pipeline,
        summary=route_meta["summary"],
        description=route_meta["description"],
        tags=merged_tags,
        deprecated=route_meta["deprecated"],
        response_model=route_meta["response_model"],
        status_code=route_meta["status_code"],
        version=route_meta.get("version"),
        _raw_metadata=route_meta,
    )


def _extract_method_params(
    method: Any,
    signature: inspect.Signature,
    full_path: str,
) -> list[ParameterMetadata]:
    """Extract method parameters for binding."""
    params = []

    try:
        type_hints = get_type_hints(method, include_extras=True)

        # Extract path parameter names from full_path
        path_params = set()
        for segment in full_path.split("/"):
            if segment.startswith("<") and segment.endswith(">"):
                # Parse <name> or <name:type>
                param_spec = segment[1:-1]
                param_name = param_spec.split(":")[0] if ":" in param_spec else param_spec
                path_params.add(param_name)
            elif segment.startswith("{") and segment.endswith("}"):
                param_spec = segment[1:-1]
                param_name = param_spec.split(":")[0] if ":" in param_spec else param_spec
                path_params.add(param_name)

        for param_name, param in signature.parameters.items():
            if param_name in ("self", "cls", "ctx"):
                # Skip self and ctx - they're injected automatically
                continue

            param_type = type_hints.get(param_name, Any)

            # Determine source
            if param_name in path_params:
                source = "path"
            elif _is_blueprint_type(param_type):
                # Blueprint subclass → auto-parse request body
                source = "body"
            elif get_origin(param_type) is not None:
                # Check for Inject/Dep annotation in Annotated types
                origin = get_origin(param_type)
                if Annotated is not None and origin is Annotated:
                    args = get_args(param_type)
                    has_inject_or_dep = False
                    for meta in args[1:]:
                        # Check for Inject marker
                        if hasattr(meta, "_inject_token") or hasattr(meta, "_inject_tag"):
                            has_inject_or_dep = True
                            break
                        # Check for Dep marker
                        try:
                            from aquilia.di.dep import Dep

                            if isinstance(meta, Dep):
                                has_inject_or_dep = True
                                source = "dep"
                                break
                        except ImportError:
                            pass
                    if has_inject_or_dep and source != "dep":
                        source = "di"
                    elif not has_inject_or_dep:
                        # Generic Annotated without DI marker → treat as query
                        source = "query"
                else:
                    # Dict[str, Any] and similar mapping types → treat as body
                    # (raw JSON body injection for POST/PUT/PATCH handlers).
                    # All other non-Annotated generics (List, Optional, etc.) → query.
                    _generic_origin = get_origin(param_type)
                    if _generic_origin is dict:
                        source = "body"
                    else:
                        # Check Optional[Dict[...]] → Optional is Union[X, None],
                        # so unwrap and re-check the first arg.
                        try:
                            from typing import Union

                            if _generic_origin is Union:
                                _inner_args = get_args(param_type)
                                # Optional[X] → Union[X, None]; X may itself be a Dict
                                _non_none = [a for a in _inner_args if a is not type(None)]
                                source = "body" if len(_non_none) == 1 and get_origin(_non_none[0]) is dict else "query"
                            else:
                                source = "query"
                        except Exception:
                            source = "query"
            elif param_name == "session" or (hasattr(param_type, "__name__") and param_type.__name__ == "Session"):
                # Always treat Session as DI source
                source = "di"
            elif param_name == "identity" or (hasattr(param_type, "__name__") and param_type.__name__ == "Identity"):
                # Always treat Identity as DI source
                source = "di"
            else:
                source = "query"

            params.append(
                ParameterMetadata(
                    name=param_name,
                    type=param_type,
                    default=param.default,
                    source=source,
                    required=param.default == inspect.Parameter.empty,
                )
            )
    except Exception:
        pass

    return params


def _is_blueprint_type(annotation: Any) -> bool:
    """
    Check if a type annotation is an Aquilia Blueprint subclass
    or a ProjectedRef (Blueprint["projection"]).

    Used by the metadata extractor to auto-detect handler parameters
    that should be populated from the request body and sealed.
    """
    try:
        from aquilia.blueprints.core import Blueprint
        from aquilia.blueprints.lenses import _ProjectedRef

        if isinstance(annotation, _ProjectedRef):
            return True

        return isinstance(annotation, type) and issubclass(annotation, Blueprint) and annotation is not Blueprint
    except ImportError:
        return False


# For Annotated type checking
try:
    from typing import Annotated
except ImportError:
    Annotated = None  # type: ignore
