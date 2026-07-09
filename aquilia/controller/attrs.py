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

    def __set_name__(self, owner: type, name: str) -> None:
        """
        Apply buffered configuration to *owner* at class-definition time.

        Called by Python's type machinery (``type.__new__``) after the class
        namespace is applied but before the metaclass post-processing loop.
        ``_ControllerMeta.__new__`` then copies the lists we set here, which is
        correct behaviour (it gets a fresh defensive copy of each list).

        Args:
            owner: The Controller subclass being defined.
            name:  The attribute name (conventionally ``"attr"``).
        """
        self._owner_name = owner.__name__

        # Validate first so errors appear at class-definition time
        self._validate(owner)

        # Apply only the fields that were explicitly configured
        if self._prefix is not _UNSET:
            owner.prefix = self._prefix  # type: ignore[attr-defined]

        if self._pipeline is not _UNSET:
            owner.pipeline = list(self._pipeline)  # type: ignore[attr-defined]

        if self._tags is not _UNSET:
            owner.tags = list(self._tags)  # type: ignore[attr-defined]

        if self._instantiation_mode is not _UNSET:
            owner.instantiation_mode = self._instantiation_mode  # type: ignore[attr-defined]

        if self._version is not _UNSET:
            owner.version = self._version  # type: ignore[attr-defined]

        if self._throttle is not _UNSET:
            owner.throttle = self._throttle  # type: ignore[attr-defined]

        if self._interceptors is not _UNSET:
            owner.interceptors = list(self._interceptors)  # type: ignore[attr-defined]

        if self._exception_filters is not _UNSET:
            owner.exception_filters = list(self._exception_filters)  # type: ignore[attr-defined]

        if self._timeout is not _UNSET:
            owner.timeout = self._timeout  # type: ignore[attr-defined]

        if self._max_body_size is not _UNSET:
            owner.max_body_size = self._max_body_size  # type: ignore[attr-defined]

        self._applied = True

    def _validate(self, owner: type) -> None:
        """
        Validate all configured values.  Raises ``ConfigInvalidFault`` on
        the first validation failure.  Called inside ``__set_name__`` so
        errors surface at class-definition time, not at request dispatch time.
        """
        from aquilia.faults.domains import ConfigInvalidFault

        ctx = f"Attributes() on {owner.__name__}"

        # --- prefix ---
        if self._prefix is not _UNSET:
            v = self._prefix
            if not isinstance(v, str):
                raise ConfigInvalidFault(
                    key="prefix",
                    reason=f"{ctx}: prefix must be a str, got {type(v).__name__!r}",
                )
            # Allow "" (no prefix) or a path starting with "/"
            if v != "" and not v.startswith("/"):
                raise ConfigInvalidFault(
                    key="prefix",
                    reason=f"{ctx}: prefix must start with '/' or be empty, got {v!r}",
                )

        # --- pipeline ---
        if self._pipeline is not _UNSET:
            items = self._pipeline
            if not hasattr(items, "__iter__"):
                raise ConfigInvalidFault(
                    key="pipeline",
                    reason=f"{ctx}: pipeline must be iterable",
                )
            # pipeline items can be any callable or guard object — just verify iterable.
            # Deeper type checking would require importing guard classes (circular import risk).

        # --- tags ---
        if self._tags is not _UNSET:
            items = self._tags
            for i, t in enumerate(items):
                if not isinstance(t, str):
                    raise ConfigInvalidFault(
                        key="tags",
                        reason=f"{ctx}: tags[{i}] must be a str, got {type(t).__name__!r}",
                    )

        # --- instantiation_mode ---
        if self._instantiation_mode is not _UNSET:
            v = self._instantiation_mode
            if v not in self._VALID_MODES:
                raise ConfigInvalidFault(
                    key="instantiation_mode",
                    reason=(f"{ctx}: instantiation_mode must be one of {sorted(self._VALID_MODES)}, got {v!r}"),
                )

        # --- version ---
        if self._version is not _UNSET:
            v = self._version
            if isinstance(v, list):
                for i, item in enumerate(v):
                    if not isinstance(item, str):
                        raise ConfigInvalidFault(
                            key="version",
                            reason=(f"{ctx}: version list item [{i}] must be a str, got {type(item).__name__!r}"),
                        )
            elif not isinstance(v, str):
                raise ConfigInvalidFault(
                    key="version",
                    reason=f"{ctx}: version must be a str or list[str], got {type(v).__name__!r}",
                )

        # --- timeout ---
        if self._timeout is not _UNSET:
            v = self._timeout
            if not isinstance(v, (int, float)):
                raise ConfigInvalidFault(
                    key="timeout",
                    reason=f"{ctx}: timeout must be a number (seconds), got {type(v).__name__!r}",
                )
            if v < 0:
                raise ConfigInvalidFault(
                    key="timeout",
                    reason=f"{ctx}: timeout must be >= 0, got {v!r}",
                )

        # --- max_body_size ---
        if self._max_body_size is not _UNSET:
            v = self._max_body_size
            if not isinstance(v, int):
                raise ConfigInvalidFault(
                    key="max_body_size",
                    reason=f"{ctx}: max_body_size must be an int (bytes), got {type(v).__name__!r}",
                )
            if v < 0:
                raise ConfigInvalidFault(
                    key="max_body_size",
                    reason=f"{ctx}: max_body_size must be >= 0, got {v!r}",
                )

    # ─── Fluent API ───────────────────────────────────────────────────────

    def prefix(self, value: str) -> Attributes:
        """Set URL prefix for all routes in this controller.

        Args:
            value: URL prefix string (e.g. ``"/products"``).
                   Use ``""`` for no prefix.
        """
        self._prefix = value
        return self

    def pipeline(self, *nodes: Any) -> Attributes:
        """Set the class-level pipeline (guards, hooks, middleware).

        Args:
            *nodes: Pipeline node instances (guards, hooks, etc.).
                    Passed as positional variadic args: ``.pipeline(AuthGuard, LogHook)``.
        """
        self._pipeline = nodes  # tuple — converted to list in __set_name__
        return self

    def tags(self, *tag_values: str) -> Attributes:
        """Set OpenAPI tags for all routes in this controller.

        Args:
            *tag_values: Tag strings. ``.tags("Products", "Public")``.
        """
        self._tags = tag_values  # tuple — converted to list in __set_name__
        return self

    def instantiation_mode(self, mode: Literal["per_request", "singleton"]) -> Attributes:
        """Set controller instantiation mode.

        Args:
            mode: ``"per_request"`` (new instance per request, default) or
                  ``"singleton"`` (single shared instance for the app lifetime).
        """
        self._instantiation_mode = mode
        return self

    def version(self, v: str | list[str]) -> Attributes:
        """Set API version binding for this controller.

        Args:
            v: Single version string (e.g. ``"v1"``) or list of version
               strings (e.g. ``["v1", "v2"]``).
        """
        self._version = v
        return self

    def throttle(self, t: Throttle) -> Attributes:
        """Set rate limiting for this controller.

        Args:
            t: ``Throttle`` instance (e.g. ``Throttle(limit=100, window=60)``).
        """
        self._throttle = t
        return self

    def interceptors(self, *items: Interceptor) -> Attributes:
        """Set interceptors (before/after handler hooks).

        Args:
            *items: ``Interceptor`` instances.
        """
        self._interceptors = items
        return self

    def exception_filters(self, *items: ExceptionFilter) -> Attributes:
        """Set exception filters (structured error handling).

        Args:
            *items: ``ExceptionFilter`` instances.
        """
        self._exception_filters = items
        return self

    def timeout(self, seconds: float) -> Attributes:
        """Set handler execution timeout.

        Args:
            seconds: Timeout in seconds. ``0`` means no timeout (default).
        """
        self._timeout = seconds
        return self

    def max_body_size(self, bytes_size: int) -> Attributes:
        """Set maximum request body size.

        Args:
            bytes_size: Max body in bytes. ``0`` means no limit (default).
        """
        self._max_body_size = bytes_size
        return self

    # ─── Introspection ────────────────────────────────────────────────────

    def __repr__(self) -> str:  # noqa: D105
        parts = []
        if self._prefix is not _UNSET:
            parts.append(f"prefix={self._prefix!r}")
        if self._pipeline is not _UNSET:
            parts.append(f"pipeline={list(self._pipeline)!r}")
        if self._tags is not _UNSET:
            parts.append(f"tags={list(self._tags)!r}")
        if self._instantiation_mode is not _UNSET:
            parts.append(f"instantiation_mode={self._instantiation_mode!r}")
        if self._version is not _UNSET:
            parts.append(f"version={self._version!r}")
        if self._throttle is not _UNSET:
            parts.append(f"throttle={self._throttle!r}")
        if self._interceptors is not _UNSET:
            parts.append(f"interceptors={list(self._interceptors)!r}")
        if self._exception_filters is not _UNSET:
            parts.append(f"exception_filters={list(self._exception_filters)!r}")
        if self._timeout is not _UNSET:
            parts.append(f"timeout={self._timeout!r}")
        if self._max_body_size is not _UNSET:
            parts.append(f"max_body_size={self._max_body_size!r}")
        state = "applied" if self._applied else "pending"
        return f"Attributes({', '.join(parts)}) [{state}]"
