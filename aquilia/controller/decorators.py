"""
Controller Method Decorators

HTTP method decorators for controller methods.
Attach metadata without import-time side effects.
"""

import inspect
from collections.abc import Callable
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

# All valid HTTP methods the framework supports
VALID_HTTP_METHODS = frozenset(
    {
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "HEAD",
        "OPTIONS",
        "TRACE",
        "WS",
    }
)


class RouteDecorator:
    """
    Base route decorator.

    Attaches metadata to controller methods for compile-time extraction.
    """

    def __init__(
        self,
        path: str | None = None,
        *,
        method: str | None = None,
        pipeline: list[Any] | None = None,
        summary: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        deprecated: bool = False,
        response_model: type | None = None,
        status_code: int = 200,
        request_blueprint: type | None = None,
        response_blueprint: type | None = None,
        # ── Filtering, Searching, Ordering ───────────────────────────
        filterset_class: type | None = None,
        filterset_fields: list[str] | Any | None = None,
        search_fields: list[str] | None = None,
        ordering_fields: list[str] | None = None,
        # ── Pagination ───────────────────────────────────────────────
        pagination_class: type | None = None,
        # ── Content Negotiation ──────────────────────────────────────
        renderer_classes: list[Any] | None = None,
        # ── Controller-level overrides ───────────────────────────────
        throttle: Any | None = None,
        timeout: float | None = None,
        # ── API Versioning ───────────────────────────────────────────
        version: str | list[str] | None = None,
    ):
        """
        Initialize route decorator.

        Args:
            path: URL path template (e.g., "/", "/«id:int»")
                  If None, derives from method name
            method: HTTP method (GET, POST, etc.) -- set by subclasses
            pipeline: Method-level pipeline nodes (overrides class-level)
            summary: OpenAPI summary
            description: OpenAPI description
            tags: OpenAPI tags (extends class-level)
            deprecated: Mark as deprecated in OpenAPI
            response_model: Response type for OpenAPI
            status_code: Default status code
            request_blueprint: Aquilia Blueprint class for request body
                               casting and sealing
            response_blueprint: Aquilia Blueprint class (or ProjectedRef via
                                Blueprint["projection"]) for response molding
            filterset_class: FilterSet subclass for declarative filtering
            filterset_fields: List of field names (exact-match shorthand)
                              or dict mapping fields to lookup lists
            search_fields: List of field names for text search
                           (activated via ?search=<term>)
            ordering_fields: List of field names allowed for dynamic ordering
                             (activated via ?ordering=<field>)
            pagination_class: Pagination backend class
                              (PageNumberPagination, LimitOffsetPagination,
                              CursorPagination)
            renderer_classes: List of renderer instances/classes for
                              content negotiation
            throttle: Per-route Throttle override
            timeout: Per-route handler timeout override (seconds)
            version: API version binding for this route. Single version
                     string (e.g. ``"2.0"``) or list of versions
                     (e.g. ``["1.0", "2.0"]``). Overrides the
                     controller-level ``version`` attribute.
        """
        self.path = path
        self.method: str | None = method
        self.pipeline = pipeline or []
        self.summary = summary
        self.description = description
        self.tags = tags or []
        self.deprecated = deprecated
        self.response_model = response_model
        self.status_code = status_code
        self.request_blueprint = request_blueprint
        self.response_blueprint = response_blueprint
        self.filterset_class = filterset_class
        self.filterset_fields = filterset_fields
        self.search_fields = search_fields
        self.ordering_fields = ordering_fields
        self.pagination_class = pagination_class
        self.renderer_classes = renderer_classes
        self.throttle = throttle
        self.timeout = timeout
        self.version = version

    def __call__(self, func: F) -> F:
        """
        Decorate controller method.

        Attaches metadata without executing anything.
        """
        # Attach metadata to function
        if not hasattr(func, "__route_metadata__"):
            func.__route_metadata__ = []

        # Deduplicate: don't add the same method+path twice
        for existing in func.__route_metadata__:
            if existing["http_method"] == self.method and existing["path"] == self.path:
                return func

        metadata = {
            "http_method": self.method,
            "path": self.path,
            "pipeline": self.pipeline,
            "summary": self.summary or func.__name__.replace("_", " ").title(),
            "description": self.description or inspect.getdoc(func) or "",
            "tags": self.tags,
            "deprecated": self.deprecated,
            "response_model": self.response_model,
            "status_code": self.status_code,
            "func_name": func.__name__,
            "signature": inspect.signature(func),
            "request_blueprint": self.request_blueprint,
            "response_blueprint": self.response_blueprint,
            "filterset_class": self.filterset_class,
            "filterset_fields": self.filterset_fields,
            "search_fields": self.search_fields,
            "ordering_fields": self.ordering_fields,
            "pagination_class": self.pagination_class,
            "renderer_classes": self.renderer_classes,
            "throttle": self.throttle,
            "timeout": self.timeout,
            "version": self.version,
        }

        func.__route_metadata__.append(metadata)

        # ── Versioning: store __version_metadata__ for server registration
        if self.version is not None:
            if not hasattr(func, "__version_metadata__"):
                func.__version_metadata__ = {}
            versions = self.version if isinstance(self.version, list) else [self.version]
            existing = func.__version_metadata__.get("versions", [])
            func.__version_metadata__["versions"] = list(
                dict.fromkeys(existing + versions),  # deduplicate, preserve order
            )

        return func


class GET(RouteDecorator):
    """GET request decorator."""

    def __init__(
        self,
        path: str | None = None,
        *,
        pipeline: list[Any] | None = None,
        summary: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        deprecated: bool = False,
        response_model: type | None = None,
        status_code: int = 200,
        request_blueprint: type | None = None,
        response_blueprint: type | None = None,
        filterset_class: type | None = None,
        filterset_fields: list[str] | Any | None = None,
        search_fields: list[str] | None = None,
        ordering_fields: list[str] | None = None,
        pagination_class: type | None = None,
        renderer_classes: list[Any] | None = None,
        throttle: Any | None = None,
        timeout: float | None = None,
        version: str | list[str] | None = None,
    ):
        super().__init__(
            path,
            method="GET",
            pipeline=pipeline,
            summary=summary,
            description=description,
            tags=tags,
            deprecated=deprecated,
            response_model=response_model,
            status_code=status_code,
            request_blueprint=request_blueprint,
            response_blueprint=response_blueprint,
            filterset_class=filterset_class,
            filterset_fields=filterset_fields,
            search_fields=search_fields,
            ordering_fields=ordering_fields,
            pagination_class=pagination_class,
            renderer_classes=renderer_classes,
            throttle=throttle,
            timeout=timeout,
            version=version,
        )


class POST(RouteDecorator):
    """POST request decorator."""

    def __init__(
        self,
        path: str | None = None,
        *,
        pipeline: list[Any] | None = None,
        summary: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        deprecated: bool = False,
        response_model: type | None = None,
        status_code: int = 200,
        request_blueprint: type | None = None,
        response_blueprint: type | None = None,
        filterset_class: type | None = None,
        filterset_fields: list[str] | Any | None = None,
        search_fields: list[str] | None = None,
        ordering_fields: list[str] | None = None,
        pagination_class: type | None = None,
        renderer_classes: list[Any] | None = None,
        throttle: Any | None = None,
        timeout: float | None = None,
        version: str | list[str] | None = None,
    ):
        super().__init__(
            path,
            method="POST",
            pipeline=pipeline,
            summary=summary,
            description=description,
            tags=tags,
            deprecated=deprecated,
            response_model=response_model,
            status_code=status_code,
            request_blueprint=request_blueprint,
            response_blueprint=response_blueprint,
            filterset_class=filterset_class,
            filterset_fields=filterset_fields,
            search_fields=search_fields,
            ordering_fields=ordering_fields,
            pagination_class=pagination_class,
            renderer_classes=renderer_classes,
            throttle=throttle,
            timeout=timeout,
            version=version,
        )


class PUT(RouteDecorator):
    """PUT request decorator."""

    def __init__(
        self,
        path: str | None = None,
        *,
        pipeline: list[Any] | None = None,
        summary: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        deprecated: bool = False,
        response_model: type | None = None,
        status_code: int = 200,
        request_blueprint: type | None = None,
        response_blueprint: type | None = None,
        filterset_class: type | None = None,
        filterset_fields: list[str] | Any | None = None,
        search_fields: list[str] | None = None,
        ordering_fields: list[str] | None = None,
        pagination_class: type | None = None,
        renderer_classes: list[Any] | None = None,
        throttle: Any | None = None,
        timeout: float | None = None,
        version: str | list[str] | None = None,
    ):
        super().__init__(
            path,
            method="PUT",
            pipeline=pipeline,
            summary=summary,
            description=description,
            tags=tags,
            deprecated=deprecated,
            response_model=response_model,
            status_code=status_code,
            request_blueprint=request_blueprint,
            response_blueprint=response_blueprint,
            filterset_class=filterset_class,
            filterset_fields=filterset_fields,
            search_fields=search_fields,
            ordering_fields=ordering_fields,
            pagination_class=pagination_class,
            renderer_classes=renderer_classes,
            throttle=throttle,
            timeout=timeout,
            version=version,
        )


class PATCH(RouteDecorator):
    """PATCH request decorator."""

    def __init__(
        self,
        path: str | None = None,
        *,
        pipeline: list[Any] | None = None,
        summary: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        deprecated: bool = False,
        response_model: type | None = None,
        status_code: int = 200,
        request_blueprint: type | None = None,
        response_blueprint: type | None = None,
        filterset_class: type | None = None,
        filterset_fields: list[str] | Any | None = None,
        search_fields: list[str] | None = None,
        ordering_fields: list[str] | None = None,
        pagination_class: type | None = None,
        renderer_classes: list[Any] | None = None,
        throttle: Any | None = None,
        timeout: float | None = None,
        version: str | list[str] | None = None,
    ):
        super().__init__(
            path,
            method="PATCH",
            pipeline=pipeline,
            summary=summary,
            description=description,
            tags=tags,
            deprecated=deprecated,
            response_model=response_model,
            status_code=status_code,
            request_blueprint=request_blueprint,
            response_blueprint=response_blueprint,
            filterset_class=filterset_class,
            filterset_fields=filterset_fields,
            search_fields=search_fields,
            ordering_fields=ordering_fields,
            pagination_class=pagination_class,
            renderer_classes=renderer_classes,
            throttle=throttle,
            timeout=timeout,
            version=version,
        )


class DELETE(RouteDecorator):
    """DELETE request decorator."""

    def __init__(
        self,
        path: str | None = None,
        *,
        pipeline: list[Any] | None = None,
        summary: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        deprecated: bool = False,
        response_model: type | None = None,
        status_code: int = 200,
        request_blueprint: type | None = None,
        response_blueprint: type | None = None,
        filterset_class: type | None = None,
        filterset_fields: list[str] | Any | None = None,
        search_fields: list[str] | None = None,
        ordering_fields: list[str] | None = None,
        pagination_class: type | None = None,
        renderer_classes: list[Any] | None = None,
        throttle: Any | None = None,
        timeout: float | None = None,
        version: str | list[str] | None = None,
    ):
        super().__init__(
            path,
            method="DELETE",
            pipeline=pipeline,
            summary=summary,
            description=description,
            tags=tags,
            deprecated=deprecated,
            response_model=response_model,
            status_code=status_code,
            request_blueprint=request_blueprint,
            response_blueprint=response_blueprint,
            filterset_class=filterset_class,
            filterset_fields=filterset_fields,
            search_fields=search_fields,
            ordering_fields=ordering_fields,
            pagination_class=pagination_class,
            renderer_classes=renderer_classes,
            throttle=throttle,
            timeout=timeout,
            version=version,
        )


class HEAD(RouteDecorator):
    """HEAD request decorator."""

    def __init__(
        self,
        path: str | None = None,
        *,
        pipeline: list[Any] | None = None,
        summary: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        deprecated: bool = False,
        response_model: type | None = None,
        status_code: int = 200,
        request_blueprint: type | None = None,
        response_blueprint: type | None = None,
        filterset_class: type | None = None,
        filterset_fields: list[str] | Any | None = None,
        search_fields: list[str] | None = None,
        ordering_fields: list[str] | None = None,
        pagination_class: type | None = None,
        renderer_classes: list[Any] | None = None,
        throttle: Any | None = None,
        timeout: float | None = None,
        version: str | list[str] | None = None,
    ):
        super().__init__(
            path,
            method="HEAD",
            pipeline=pipeline,
            summary=summary,
            description=description,
            tags=tags,
            deprecated=deprecated,
            response_model=response_model,
            status_code=status_code,
            request_blueprint=request_blueprint,
            response_blueprint=response_blueprint,
            filterset_class=filterset_class,
            filterset_fields=filterset_fields,
            search_fields=search_fields,
            ordering_fields=ordering_fields,
            pagination_class=pagination_class,
            renderer_classes=renderer_classes,
            throttle=throttle,
            timeout=timeout,
            version=version,
        )


class OPTIONS(RouteDecorator):
    """OPTIONS request decorator."""

    def __init__(
        self,
        path: str | None = None,
        *,
        pipeline: list[Any] | None = None,
        summary: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        deprecated: bool = False,
        response_model: type | None = None,
        status_code: int = 200,
        request_blueprint: type | None = None,
        response_blueprint: type | None = None,
        filterset_class: type | None = None,
        filterset_fields: list[str] | Any | None = None,
        search_fields: list[str] | None = None,
        ordering_fields: list[str] | None = None,
        pagination_class: type | None = None,
        renderer_classes: list[Any] | None = None,
        throttle: Any | None = None,
        timeout: float | None = None,
        version: str | list[str] | None = None,
    ):
        super().__init__(
            path,
            method="OPTIONS",
            pipeline=pipeline,
            summary=summary,
            description=description,
            tags=tags,
            deprecated=deprecated,
            response_model=response_model,
            status_code=status_code,
            request_blueprint=request_blueprint,
            response_blueprint=response_blueprint,
            filterset_class=filterset_class,
            filterset_fields=filterset_fields,
            search_fields=search_fields,
            ordering_fields=ordering_fields,
            pagination_class=pagination_class,
            renderer_classes=renderer_classes,
            throttle=throttle,
            timeout=timeout,
            version=version,
        )


class TRACE(RouteDecorator):
    """TRACE request decorator."""

    def __init__(
        self,
        path: str | None = None,
        *,
        pipeline: list[Any] | None = None,
        summary: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        deprecated: bool = False,
        response_model: type | None = None,
        status_code: int = 200,
        request_blueprint: type | None = None,
        response_blueprint: type | None = None,
        filterset_class: type | None = None,
        filterset_fields: list[str] | Any | None = None,
        search_fields: list[str] | None = None,
        ordering_fields: list[str] | None = None,
        pagination_class: type | None = None,
        renderer_classes: list[Any] | None = None,
        throttle: Any | None = None,
        timeout: float | None = None,
        version: str | list[str] | None = None,
    ):
        super().__init__(
            path,
            method="TRACE",
            pipeline=pipeline,
            summary=summary,
            description=description,
            tags=tags,
            deprecated=deprecated,
            response_model=response_model,
            status_code=status_code,
            request_blueprint=request_blueprint,
            response_blueprint=response_blueprint,
            filterset_class=filterset_class,
            filterset_fields=filterset_fields,
            search_fields=search_fields,
            ordering_fields=ordering_fields,
            pagination_class=pagination_class,
            renderer_classes=renderer_classes,
            throttle=throttle,
            timeout=timeout,
            version=version,
        )


class WS(RouteDecorator):
    """WebSocket request decorator."""

    def __init__(
        self,
        path: str | None = None,
        *,
        pipeline: list[Any] | None = None,
        summary: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        deprecated: bool = False,
        response_model: type | None = None,
        status_code: int = 200,
        request_blueprint: type | None = None,
        response_blueprint: type | None = None,
        filterset_class: type | None = None,
        filterset_fields: list[str] | Any | None = None,
        search_fields: list[str] | None = None,
        ordering_fields: list[str] | None = None,
        pagination_class: type | None = None,
        renderer_classes: list[Any] | None = None,
        throttle: Any | None = None,
        timeout: float | None = None,
        version: str | list[str] | None = None,
    ):
        super().__init__(
            path,
            method="WS",
            pipeline=pipeline,
            summary=summary,
            description=description,
            tags=tags,
            deprecated=deprecated,
            response_model=response_model,
            status_code=status_code,
            request_blueprint=request_blueprint,
            response_blueprint=response_blueprint,
            filterset_class=filterset_class,
            filterset_fields=filterset_fields,
            search_fields=search_fields,
            ordering_fields=ordering_fields,
            pagination_class=pagination_class,
            renderer_classes=renderer_classes,
            throttle=throttle,
            timeout=timeout,
            version=version,
        )


def route(
    method: str | list[str],
    path: str | None = None,
    *,
    pipeline: list[Any] | None = None,
    summary: str | None = None,
    description: str | None = None,
    tags: list[str] | None = None,
    deprecated: bool = False,
    response_model: type | None = None,
    status_code: int = 200,
    request_blueprint: type | None = None,
    response_blueprint: type | None = None,
    filterset_class: type | None = None,
    filterset_fields: list[str] | Any | None = None,
    search_fields: list[str] | None = None,
    ordering_fields: list[str] | None = None,
    pagination_class: type | None = None,
    renderer_classes: list[Any] | None = None,
    throttle: Any | None = None,
    timeout: float | None = None,
    version: str | list[str] | None = None,
) -> Callable[[F], F]:
    """
    Generic route decorator.

    Args:
        method: HTTP method or list of methods
        path: URL path template
        pipeline: Method-level pipeline nodes (overrides class-level)
        summary: OpenAPI summary
        description: OpenAPI description
        tags: OpenAPI tags (extends class-level)
        deprecated: Mark as deprecated in OpenAPI
        response_model: Response type for OpenAPI
        status_code: Default status code
        request_blueprint: Aquilia Blueprint class for request body casting and sealing
        response_blueprint: Aquilia Blueprint class for response molding
        filterset_class: FilterSet subclass for declarative filtering
        filterset_fields: List/dict shorthand for filter fields
        search_fields: List of field names for text search
        ordering_fields: List of field names allowed for dynamic ordering
        pagination_class: Pagination backend class
        renderer_classes: List of renderer instances/classes for content negotiation
        throttle: Per-route Throttle override
        timeout: Per-route handler timeout override (seconds)
        version: API version binding for this route

    Example:
        @route("GET", "/users")
        async def get_users(self, ctx):
            ...

        @route(["GET", "POST"], "/items")
        async def handle_items(self, ctx):
            ...
    """
    methods = [method] if isinstance(method, str) else method

    # Validate methods
    _METHOD_MAP = {
        "GET": GET,
        "POST": POST,
        "PUT": PUT,
        "PATCH": PATCH,
        "DELETE": DELETE,
        "HEAD": HEAD,
        "OPTIONS": OPTIONS,
        "TRACE": TRACE,
        "WS": WS,
    }

    def decorator(func: F) -> F:
        for http_method in methods:
            upper = http_method.upper()
            if upper not in VALID_HTTP_METHODS:
                from aquilia.faults.domains import ConfigInvalidFault

                raise ConfigInvalidFault(
                    key="http_method",
                    reason=f"Invalid HTTP method '{http_method}'. "
                    f"Valid methods: {', '.join(sorted(VALID_HTTP_METHODS))}",
                )
            decorator_cls = _METHOD_MAP.get(upper)
            if decorator_cls:
                func = decorator_cls(
                    path,
                    pipeline=pipeline,
                    summary=summary,
                    description=description,
                    tags=tags,
                    deprecated=deprecated,
                    response_model=response_model,
                    status_code=status_code,
                    request_blueprint=request_blueprint,
                    response_blueprint=response_blueprint,
                    filterset_class=filterset_class,
                    filterset_fields=filterset_fields,
                    search_fields=search_fields,
                    ordering_fields=ordering_fields,
                    pagination_class=pagination_class,
                    renderer_classes=renderer_classes,
                    throttle=throttle,
                    timeout=timeout,
                    version=version,
                )(func)

        return func

    return decorator
