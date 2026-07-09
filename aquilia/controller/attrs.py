"""
Controller Attributes Builder

Provides the ``Attributes`` fluent builder for declarative controller-level
configuration.  It uses Python's ``__set_name__`` descriptor protocol to apply
metadata directly to the owner class at class-creation time, with zero overhead
on the request hot path.

Performance:
- ``__slots__`` eliminates per-instance ``__dict__`` (~40% faster attribute access,
  lower memory).
- Each fluent method is O(1): a single slot assignment plus ``return self``.
- ``__set_name__`` runs once per class definition, never per request.
- No allocations in the method chain beyond ``list()`` for variadic arguments.

Example::

    from aquilia import Controller, GET, Attributes, RequestCtx

    class ProductsController(Controller):
        attr = (
            Attributes()
            .prefix("/products")
            .tags("Products")
            .pipeline(AuthPipeline)
            .instantiation_mode("singleton")
            .timeout(30.0)
        )

        @GET("/")
        async def list_products(self, ctx: RequestCtx):
            ...
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from aquilia.controller.base import ExceptionFilter, Interceptor, Throttle

logger = logging.getLogger("aquilia.controller.attrs")

# Module-level sentinel — identical to the idiom used in stdlib (e.g. inspect.Parameter.empty)
_UNSET: object = object()


class Attributes:
    """
    Fluent builder for Controller class-level configuration.

    Assign to a class-level attribute named ``attr`` inside any ``Controller``
    subclass.  Python's ``__set_name__`` protocol applies all configured values
    to the owner class automatically when the class body is evaluated — with no
    runtime overhead and no changes required to the metadata extraction pipeline.

    Each method returns ``self`` (the builder) for chaining.  Attributes that
    are not explicitly set leave the corresponding class-level default intact.
    """

    __slots__ = (
        "_prefix",
        "_pipeline",
        "_tags",
        "_instantiation_mode",
        "_version",
        "_throttle",
        "_interceptors",
        "_exception_filters",
        "_timeout",
        "_max_body_size",
        "_applied",  # bool: True once __set_name__ has fired
        "_owner_name",  # str | None: class name for error messages
    )

    _VALID_MODES: frozenset[str] = frozenset({"per_request", "singleton"})

    def __init__(self) -> None:
        self._prefix: object = _UNSET
        self._pipeline: object = _UNSET
        self._tags: object = _UNSET
        self._instantiation_mode: object = _UNSET
        self._version: object = _UNSET
        self._throttle: object = _UNSET
        self._interceptors: object = _UNSET
        self._exception_filters: object = _UNSET
        self._timeout: object = _UNSET
        self._max_body_size: object = _UNSET
        self._applied: bool = False
        self._owner_name: str | None = None
