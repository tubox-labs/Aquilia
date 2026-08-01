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

        @GET("/{id:int}")
        async def retrieve(self, ctx, id: int):
            return self.repo.get(id)
"""

from aquilia.controller.attrs import Attributes
from aquilia.controller.base import Controller, ExceptionFilter, Interceptor, RequestCtx, Throttle
from aquilia.controller.compiler import CompiledController, CompiledRoute, ControllerCompiler
from aquilia.controller.decorators import (
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
from aquilia.controller.engine import ControllerEngine
from aquilia.controller.factory import ControllerFactory, InstantiationMode
from aquilia.controller.filters import (
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
from aquilia.controller.metadata import (
    ControllerMetadata,
    ParameterMetadata,
    RouteMetadata,
    extract_controller_metadata,
)
from aquilia.controller.pagination import (
    BasePagination,
    CursorPagination,
    LimitOffsetPagination,
    NoPagination,
    PageNumberPagination,
)
from aquilia.controller.renderers import (
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
from aquilia.controller.resource import CRUDResource, ReadOnlyResource, Resource, action
from aquilia.controller.router import ControllerRouter
from aquilia.controller.throttle import (
    MemoryThrottleBackend,
    RedisThrottleBackend,
    ThrottleBackend,
    ThrottleBackendFactory,
)
from aquilia.controller.validation import RequestBodyValidationFault, ValidationFault, validate_body

__all__ = [
    # Base
    "Controller",
    "Attributes",
    "RequestCtx",
    "ExceptionFilter",
    "Interceptor",
    "Throttle",
    "ThrottleBackend",
    "MemoryThrottleBackend",
    "RedisThrottleBackend",
    "ThrottleBackendFactory",
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
    # Resources
    "Resource",
    "ReadOnlyResource",
    "CRUDResource",
    "action",
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
    # Validation
    "validate_body",
    "ValidationFault",
    "RequestBodyValidationFault",
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
