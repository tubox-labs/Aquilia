"""
Aquilia Versioning — Route-Level Decorators

Decorators for binding API versions to individual routes,
independent of (or overriding) the controller-level version.

Usage::

    class ItemsController(Controller):
        prefix = "/items"
        version = "2.0"  # Controller-level version

        @GET("/")
        @version("2.1")  # This route only serves v2.1
        async def list_v21(self, ctx):
            ...

        @GET("/")
        async def list(self, ctx):  # Inherits controller v2.0
            ...

        @GET("/health")
        @version_neutral  # Responds to any version
        async def health(self, ctx):
            ...

        @GET("/beta-feature")
        @version_range("2.0", "3.0")  # Serves v2.0 through v2.x
        async def beta(self, ctx):
            ...
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from .core import VERSION_NEUTRAL, ApiVersion

F = TypeVar("F", bound=Callable[..., Any])


def version(
    ver: str | list[str] | ApiVersion | list[ApiVersion],
) -> Callable[[F], F]:
    """
    Bind a specific version (or list of versions) to a route.

    This overrides the controller-level ``version`` for this route only.

    Args:
        ver: Version string, ``ApiVersion``, or list of either.

    Example::

        @GET("/users")
        @version("2.1")
        async def list_users_v21(self, ctx):
            ...

        @GET("/users")
        @version(["1.0", "2.0"])  # Serves both v1.0 and v2.0
        async def list_users(self, ctx):
            ...
    """

    def decorator(func: F) -> F:
        # Normalize to list
        versions = [ver] if isinstance(ver, (str, ApiVersion)) else list(ver)

        # Store as metadata on the function
        if not hasattr(func, "__version_metadata__"):
            func.__version_metadata__ = {}

        func.__version_metadata__["versions"] = versions
        func.__version_metadata__["neutral"] = False
        return func

    return decorator


def version_neutral(func: F) -> F:
    """
    Mark a route as version-neutral.

    Version-neutral routes respond to ALL versions and to unversioned
    requests. Ideal for health checks, metrics, and discovery endpoints.

    Example::

        @GET("/health")
        @version_neutral
        async def health(self, ctx):
            return {"status": "ok"}
    """
    if not hasattr(func, "__version_metadata__"):
        func.__version_metadata__ = {}

    func.__version_metadata__["neutral"] = True
    func.__version_metadata__["versions"] = [VERSION_NEUTRAL]
    return func


def version_range(
    min_version: str | ApiVersion,
    max_version: str | ApiVersion | None = None,
) -> Callable[[F], F]:
    """
    Bind a version range to a route.

    The route will serve requests for any version >= min_version
    and < max_version (exclusive). If max_version is None, serves
    all versions >= min_version.

    Args:
        min_version: Minimum version (inclusive).
        max_version: Maximum version (exclusive). None = no upper bound.

    Example::

        @GET("/beta")
        @version_range("2.0", "3.0")
        async def beta_feature(self, ctx):
            ...  # Serves v2.0, v2.1, ..., v2.x
    """

    def decorator(func: F) -> F:
        if not hasattr(func, "__version_metadata__"):
            func.__version_metadata__ = {}

        func.__version_metadata__["range"] = {
            "min": min_version,
            "max": max_version,
        }
        func.__version_metadata__["neutral"] = False
        return func

    return decorator
