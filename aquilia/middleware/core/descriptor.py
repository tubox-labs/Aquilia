"""Registration records — what the stack stores for one ``add()`` call.

Dependency-free leaf: the descriptor is a plain record, so diagnostics, the
chain builder, and instruments can all read it without importing the registry.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aquilia.middleware.core.base import (
    Middleware,
    implements_lifespan,
    implements_should_run,
    resolve_entrypoint,
)
from aquilia.middleware.core.types import MiddlewareCallable, Scope


@dataclass(frozen=True, slots=True)
class MiddlewareMeta:
    """Declarative defaults read off a middleware class.

    Lets ``stack.add(TenantMiddleware())`` pick up the priority and name the
    class already declares, instead of every call site repeating them.
    """

    name: str | None = None
    priority: int | None = None
    scope: str = "global"
    tags: tuple[str, ...] = ()

    @classmethod
    def of(cls, middleware: Any) -> MiddlewareMeta:
        """Read metadata off *middleware*, falling back to sane defaults.

        Plain functions carry no class attributes, so they get the name from
        ``__name__`` and defaults for everything else.
        """
        if not isinstance(middleware, Middleware):
            return cls(name=getattr(middleware, "__name__", None))
        return cls(
            name=middleware.name or type(middleware).__name__,
            priority=middleware.priority,
            scope=middleware.scope,
            tags=tuple(middleware.tags),
        )


@dataclass(frozen=True, slots=True)
class MiddlewareDescriptor:
    """One registered middleware, with everything the chain builder needs.

    ``entrypoint`` is bound at registration so the request path never does an
    attribute lookup. ``conditional`` and ``lifespan`` record which optional
    hooks the middleware actually overrides, so the builder can skip wrappers
    for capabilities that are not in use.
    """

    middleware: Any
    entrypoint: MiddlewareCallable
    scope: Scope
    priority: int
    name: str
    tags: tuple[str, ...] = ()
    conditional: bool = False
    lifespan: bool = False
    metadata: dict[str, Any] = field(default_factory=dict, compare=False)

    @classmethod
    def build(
        cls,
        middleware: Any,
        *,
        scope: Scope,
        priority: int,
        name: str,
        tags: tuple[str, ...] = (),
        metadata: dict[str, Any] | None = None,
    ) -> MiddlewareDescriptor:
        """Create a descriptor, resolving the entrypoint and hook flags once."""
        return cls(
            middleware=middleware,
            entrypoint=resolve_entrypoint(middleware),
            scope=scope,
            priority=priority,
            name=name,
            tags=tags,
            conditional=implements_should_run(middleware),
            lifespan=implements_lifespan(middleware),
            metadata=metadata or {},
        )

    def describe(self) -> dict[str, Any]:
        """Diagnostic view, used by ``MiddlewareStack.describe()`` and ``aq inspect``."""
        return {
            "name": self.name,
            "scope": str(self.scope),
            "priority": self.priority,
            "tags": list(self.tags),
            "conditional": self.conditional,
            "lifespan": self.lifespan,
            "type": type(self.middleware).__name__,
        }


__all__ = ["MiddlewareDescriptor", "MiddlewareMeta"]
