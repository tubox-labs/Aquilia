"""
Resource/ViewSet CRUD Controller Abstraction.

Provides base classes for auto-generating RESTful CRUD routes.
Like Django REST Framework's ViewSet but native to Aquilia.
"""

import inspect
from collections.abc import Callable
from functools import wraps
from typing import Any, Generic, TypeVar

from .base import Controller
from .decorators import DELETE, GET, PATCH, POST, PUT, route

T = TypeVar("T")


def action(
    methods: list[str] | None = None,
    detail: bool = False,
    url_path: str | None = None,
    **kwargs: Any,
) -> Callable[[Any], Any]:
    """
    Mark a method as a custom route action in a Resource.

    Args:
        methods: List of HTTP methods (e.g. ["GET", "POST"]). Defaults to ["GET"].
        detail: If True, path includes the resource ID (e.g. `/<id>/url_path`).
                If False, path is `/url_path`.
        url_path: Path suffix. Defaults to method name.
        **kwargs: Extra arguments passed to the route decorator (e.g., summary, response_model).
    """
    if methods is None:
        methods = ["GET"]

    def decorator(func: Any) -> Any:
        func.__is_action__ = True
        func.__action_methods__ = methods
        func.__action_detail__ = detail
        func.__action_url_path__ = url_path
        func.__action_kwargs__ = kwargs
        return func

    return decorator


class Resource(Controller, Generic[T]):
    """
    Base Resource Controller.

    Automatically registers routes for standard CRUD methods (list, retrieve,
    create, update, partial_update, destroy) and custom methods marked with @action.
    """

    id_param: str = "id"
    id_type: str = "int"
    lookup_field: str = "id"
    actions: set[str] | None = None
    model: type | None = None
    serializer: type | None = None

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        id_p = getattr(cls, "id_param", getattr(cls, "lookup_field", "id"))
        id_t = getattr(cls, "id_type", "int")
        allowed_actions = getattr(cls, "actions", None)

        def _should_register(name: str) -> bool:
            if allowed_actions is not None and name not in allowed_actions:
                return False
            return hasattr(cls, name)

        # 1. Handle @action custom routes
        for name, func in inspect.getmembers(cls, predicate=inspect.isfunction):
            if getattr(func, "__is_action__", False):
                methods = func.__action_methods__
                detail = func.__action_detail__
                url_path = func.__action_url_path__ or name

                if detail:
                    path = f"/{{{id_p}:{id_t}}}/{url_path}"
                else:
                    path = f"/{url_path}"

                @wraps(func)
                async def action_wrapper(self: Any, *args: Any, **kw: Any) -> Any:
                    return await func(self, *args, **kw)

                if hasattr(func, "__route_metadata__"):
                    action_wrapper.__route_metadata__ = [
                        m for m in func.__route_metadata__ if not m.get("is_auto_action")
                    ]

                route(methods, path=path, **func.__action_kwargs__)(action_wrapper)
                if hasattr(action_wrapper, "__route_metadata__"):
                    for m in action_wrapper.__route_metadata__:
                        if "is_auto_action" not in m:
                            m["is_auto_action"] = True
                setattr(cls, name, action_wrapper)

        # 2. Handle standard CRUD routes
        _crud_map = {
            "list": (GET, "/"),
            "retrieve": (GET, f"/{{{id_p}:{id_t}}}"),
            "create": (POST, "/"),
            "update": (PUT, f"/{{{id_p}:{id_t}}}"),
            "partial_update": (PATCH, f"/{{{id_p}:{id_t}}}"),
            "destroy": (DELETE, f"/{{{id_p}:{id_t}}}"),
        }

        for action_name, (DecoratorCls, path) in _crud_map.items():
            if _should_register(action_name):
                func = getattr(cls, action_name)

                @wraps(func)
                async def wrapper(self: Any, *args: Any, **kw: Any) -> Any:
                    return await func(self, *args, **kw)

                if hasattr(func, "__route_metadata__"):
                    wrapper.__route_metadata__ = [m for m in func.__route_metadata__ if not m.get("is_auto_crud")]

                DecoratorCls(path=path)(wrapper)
                if hasattr(wrapper, "__route_metadata__"):
                    for m in wrapper.__route_metadata__:
                        if "is_auto_crud" not in m:
                            m["is_auto_crud"] = True
                setattr(cls, action_name, wrapper)


class ListMixin:
    """Provides a list route."""

    async def list(self, ctx: Any, **kwargs: Any) -> Any:
        raise NotImplementedError


class RetrieveMixin:
    """Provides a retrieve route."""

    async def retrieve(self, ctx: Any, **kwargs: Any) -> Any:
        raise NotImplementedError


class CreateMixin:
    """Provides a create route."""

    async def create(self, ctx: Any, **kwargs: Any) -> Any:
        raise NotImplementedError


class UpdateMixin:
    """Provides update and partial_update routes."""

    async def update(self, ctx: Any, **kwargs: Any) -> Any:
        raise NotImplementedError

    async def partial_update(self, ctx: Any, **kwargs: Any) -> Any:
        raise NotImplementedError


class DestroyMixin:
    """Provides a destroy route."""

    async def destroy(self, ctx: Any, **kwargs: Any) -> Any:
        raise NotImplementedError


class ReadOnlyResource(ListMixin, RetrieveMixin, Resource[T]):
    """Resource with only list and retrieve routes."""

    pass


class CRUDResource(ListMixin, RetrieveMixin, CreateMixin, UpdateMixin, DestroyMixin, Resource[T]):
    """Resource with all standard CRUD routes."""

    pass
