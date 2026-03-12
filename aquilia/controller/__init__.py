"""
Aquilia Controller System

First-class Controller architecture for Aquilia.
Replaces function-based @flow handlers with class-based Controllers.

Key Features:
- Manifest-first: Controllers declared in module.aq
- DI-first: Constructor and method parameter injection
- Pipeline-first: Class-level and method-level pipelines
- Static-first: Metadata extracted at compile time
- Zero import-time side effects

Example:
    from aquilia import Controller, GET, POST, Inject
    from typing import Annotated

    class UsersController(Controller):
        prefix = "/users"
        pipeline = [Auth.guard()]

        def __init__(self, repo: Annotated[UserRepo, Inject(tag="repo")]):
            self.repo = repo

        @GET("/")
        async def list(self, ctx):
            return self.repo.list_all()

        @GET("/«id:int»")
        async def retrieve(self, ctx, id: int):
            return self.repo.get(id)
"""

from .base import Controller, ExceptionFilter, Interceptor, RequestCtx, Throttle
from .compiler import (
    CompiledController,
    CompiledRoute,
    ControllerCompiler,
)
from .decorators import (
    DELETE,
    GET,
    HEAD,
    OPTIONS,
    PATCH,
    POST,
    PUT,
    TRACE,
    VALID_HTTP_METHODS,
    WS,
    route,
)
from .engine import ControllerEngine
from .factory import (
    ControllerFactory,
    InstantiationMode,
)
from .filters import (
    BaseFilterBackend,
    FilterSet,
    FilterSetMeta,
    OrderingFilter,
    SearchFilter,
    apply_filters_to_list,
    apply_ordering_to_list,
    apply_search_to_list,
    filter_data,
    filter_queryset,
)
from .metadata import (
    ControllerMetadata,
    ParameterMetadata,
    RouteMetadata,
    extract_controller_metadata,
)
from .openapi import (
    OpenAPIConfig,
    OpenAPIGenerator,
    generate_redoc_html,
    generate_swagger_html,
)
from .pagination import (
    BasePagination,
    CursorPagination,
    LimitOffsetPagination,
    NoPagination,
    PageNumberPagination,
)
from .renderers import (
    BaseRenderer,
    ContentNegotiator,
    HTMLRenderer,
    JSONRenderer,
    MessagePackRenderer,
    PlainTextRenderer,
    XMLRenderer,
    YAMLRenderer,
    negotiate,
)
from .router import ControllerRouter

__all__ = [
    # Base
    "Controller",
    "RequestCtx",
    "ExceptionFilter",
    "Interceptor",
    "Throttle",
    # Decorators
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "HEAD",
    "OPTIONS",
    "TRACE",
    "WS",
    "route",
    "VALID_HTTP_METHODS",
    # Metadata
    "ControllerMetadata",
    "RouteMetadata",
    "ParameterMetadata",
    "extract_controller_metadata",
    # Factory
    "ControllerFactory",
    "InstantiationMode",
    # Engine
    "ControllerEngine",
    # Compilation
    "ControllerCompiler",
    "CompiledRoute",
    "CompiledController",
    # Routing
    "ControllerRouter",
    # OpenAPI
    "OpenAPIGenerator",
    "OpenAPIConfig",
    "generate_swagger_html",
    "generate_redoc_html",
    # Filtering & Search
    "BaseFilterBackend",
    "FilterSet",
    "FilterSetMeta",
    "SearchFilter",
    "OrderingFilter",
    "filter_queryset",
    "filter_data",
    "apply_filters_to_list",
    "apply_search_to_list",
    "apply_ordering_to_list",
    # Pagination
    "BasePagination",
    "PageNumberPagination",
    "LimitOffsetPagination",
    "CursorPagination",
    "NoPagination",
    # Content Negotiation & Rendering
    "BaseRenderer",
    "JSONRenderer",
    "XMLRenderer",
    "YAMLRenderer",
    "PlainTextRenderer",
    "HTMLRenderer",
    "MessagePackRenderer",
    "ContentNegotiator",
    "negotiate",
]
