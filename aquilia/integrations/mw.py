"""
Middleware chain integration — typed middleware configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MiddlewareEntry:
    """A single middleware entry in the chain."""

    path: str
    priority: int = 50
    scope: str = "global"
    name: str | None = None
    kwargs: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "priority": self.priority,
            "scope": self.scope,
            "name": self.name or self.path.rsplit(".", 1)[-1],
            "kwargs": self.kwargs,
        }


class MiddlewareChain(list):
    """
    Fluent middleware chain builder.

    Example::

        chain = (
            MiddlewareChain()
            .use("aquilia.middleware.ExceptionMiddleware", priority=1)
            .use("aquilia.middleware.RequestIdMiddleware", priority=10)
        )
    """

    def use(
        self,
        path: str,
        *,
        priority: int = 50,
        scope: str = "global",
        name: str | None = None,
        **kwargs: Any,
    ) -> MiddlewareChain:
        entry = MiddlewareEntry(
            path=path,
            priority=priority,
            scope=scope,
            name=name,
            kwargs=kwargs,
        )
        self.append(entry)
        return self

    def to_list(self) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self]

    # ── Presets ───────────────────────────────────────────────────────

    @classmethod
    def chain(cls) -> MiddlewareChain:
        """Create an empty chain."""
        return cls()

    @classmethod
    def defaults(cls) -> MiddlewareChain:
        """Standard development middleware chain."""
        return (
            cls()
            .use("aquilia.middleware.ExceptionMiddleware", priority=1)
            .use("aquilia.middleware.RequestIdMiddleware", priority=10)
        )

    @classmethod
    def production(cls) -> MiddlewareChain:
        """Production-grade middleware chain."""
        return (
            cls()
            .use("aquilia.middleware.ExceptionMiddleware", priority=1, debug=False)
            .use("aquilia.middleware.RequestIdMiddleware", priority=10)
            .use("aquilia.middleware.CompressionMiddleware", priority=15, minimum_size=500)
            .use("aquilia.middleware.TimeoutMiddleware", priority=18, timeout_seconds=30.0)
        )

    @classmethod
    def minimal(cls) -> MiddlewareChain:
        """Minimal middleware chain."""
        return (
            cls()
            .use("aquilia.middleware.ExceptionMiddleware", priority=1)
            .use("aquilia.middleware.RequestIdMiddleware", priority=10)
        )
