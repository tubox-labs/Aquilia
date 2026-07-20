"""
Compatibility layer with legacy Aquilia DI system.
"""

import warnings
from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Optional

from .core import Container
from .errors import DIError

# Context variable for request container (legacy support)
_request_container_var: ContextVar[Container | None] = ContextVar(
    "request_container",
    default=None,
)


class RequestCtx:
    """
    Legacy RequestCtx compatibility wrapper.

    Maps to new Container-based system.
    """

    def __init__(self, container: Container):
        self._container = container

    @property
    def container(self) -> Container:
        """Get underlying container."""
        return self._container

    @container.setter
    def container(self, value: Container):
        """Set underlying container."""
        self._container = value

    def get(self, token, *, tag: str | None = None, default=None):
        """
        Get service from container (legacy API).

        Args:
            token: Service token/type
            tag: Optional tag
            default: Default value if not found

        Returns:
            Service instance or default
        """
        try:
            return self._container.resolve(token, tag=tag, optional=default is not None)
        except DIError:
            # SEC-DI-11: Only catch DI-specific errors, not arbitrary exceptions
            return default

    async def get_async(self, token, *, tag: str | None = None, default=None):
        """Async version of get."""
        try:
            return await self._container.resolve_async(token, tag=tag, optional=default is not None)
        except DIError:
            # SEC-DI-11: Only catch DI-specific errors, not arbitrary exceptions
            return default

    @classmethod
    def from_container(cls, container: Container) -> "RequestCtx":
        """Create RequestCtx from container."""
        return cls(container)

    @classmethod
    def set_current(cls, ctx: "RequestCtx") -> Token:
        """Set current request context. Returns a reset Token (nesting-safe)."""
        return _request_container_var.set(ctx._container)

    @classmethod
    def get_current(cls) -> Optional["RequestCtx"]:
        """Get current request context."""
        container = _request_container_var.get()
        if container:
            return cls(container)
        return None


def get_request_container() -> Container | None:
    """
    Get current request container from context.

    Returns:
        Container or None if no request context
    """
    return _request_container_var.get()


def set_request_container(container: Container) -> Token:
    """
    Set request container in context.

    Args:
        container: Container to set

    Returns:
        The reset Token — pass it to ``reset_request_container`` to restore
        the previous value (safe under nesting, unlike a hardcoded clear).
    """
    return _request_container_var.set(container)


def reset_request_container(token: Token) -> None:
    """Restore the previous request container using a Token from ``set``."""
    _request_container_var.reset(token)


@contextmanager
def request_container_scope(container: Container | None):
    """Bind *container* as the current request container for the block.

    Nesting-safe: on exit the previous value is restored via the reset
    Token, not hard-cleared to ``None`` — so nested scopes unwind correctly.

    Example::

        with request_container_scope(req_container):
            svc = get_request_container().resolve(Service)
    """
    token = _request_container_var.set(container)
    try:
        yield container
    finally:
        _request_container_var.reset(token)


def clear_request_container() -> None:
    """Clear request container from context.

    .. deprecated::
        Hard-resets to ``None`` and cannot restore a nested prior value. Use
        :func:`reset_request_container` with a token, or
        :func:`request_container_scope`, which unwind correctly under nesting.
    """
    warnings.warn(
        "clear_request_container() is deprecated and nesting-unsafe; use "
        "reset_request_container(token) or request_container_scope(...).",
        DeprecationWarning,
        stacklevel=2,
    )
    _request_container_var.set(None)
