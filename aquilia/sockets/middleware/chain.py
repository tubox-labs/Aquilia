"""Fluent configuration builder for the WebSocket middleware chain.

Mirrors :class:`aquilia.integrations.mw.MiddlewareChain` so the two subsystems
read the same way in ``workspace.py``. Produces a serialisable list of dicts that
``AquiliaServer`` instantiates at boot — the builder itself never imports or
constructs a middleware, keeping ``workspace.py`` free of import-time effects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

_BUILTIN = "aquilia.sockets.middleware.builtin"


@dataclass
class SocketMiddlewareEntry:
    """A single middleware entry in the socket chain."""

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


class SocketMiddlewareChain(list):
    """
    Fluent WebSocket middleware chain builder.

    Example::

        chain = (
            SocketMiddlewareChain.chain()
            .use("aquilia.sockets.middleware.builtin.SocketFaultMiddleware", priority=2)
            .use("modules.chat.middleware.PresenceMiddleware", priority=50)
        )

    Priority bands (lower runs first):

    ===========  ============================================
    0-9          framework plumbing (faults, logging, metrics)
    10-19        framework security (validation, rate limit, auth)
    20-49        reserved for future framework use
    50-99        application middleware (default 50)
    ===========  ============================================
    """

    def use(
        self,
        path: str,
        *,
        priority: int = 50,
        scope: str = "global",
        name: str | None = None,
        **kwargs: Any,
    ) -> SocketMiddlewareChain:
        """Append a middleware by dotted path.

        Args:
            path: Import path, e.g. ``"modules.chat.middleware.PresenceMiddleware"``.
            priority: Lower runs first. See the band table above.
            scope: ``"global"``, ``"namespace:<path>"``, or ``"event:<name>"``.
            name: Display name; defaults to the class name.
            **kwargs: Constructor keyword arguments.
        """
        self.append(
            SocketMiddlewareEntry(
                path=path,
                priority=priority,
                scope=scope,
                name=name,
                kwargs=kwargs,
            )
        )
        return self

    def to_list(self) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self]

    # ── Presets ───────────────────────────────────────────────────────

    @classmethod
    def chain(cls) -> SocketMiddlewareChain:
        """Create an empty chain."""
        return cls()

    @classmethod
    def defaults(cls) -> SocketMiddlewareChain:
        """Fault handling and message validation — the safe minimum.

        Without ``SocketFaultMiddleware`` a fault raised in a handler is logged
        and the client is told nothing, so it is in every preset.
        """
        return (
            cls()
            .use(f"{_BUILTIN}.SocketFaultMiddleware", priority=2)
            .use(f"{_BUILTIN}.MessageValidationMiddleware", priority=10)
        )

    @classmethod
    def production(cls) -> SocketMiddlewareChain:
        """Fault handling, metrics, validation, and rate limiting.

        Rate limiting is included because an unlimited inbound message rate on a
        long-lived connection is a denial-of-service surface that HTTP rate
        limiting does not cover.
        """
        return (
            cls()
            .use(f"{_BUILTIN}.SocketFaultMiddleware", priority=2)
            .use(f"{_BUILTIN}.SocketMetricsMiddleware", priority=6)
            .use(f"{_BUILTIN}.MessageValidationMiddleware", priority=10, max_payload_size=32768)
            .use(f"{_BUILTIN}.SocketRateLimitMiddleware", priority=12, messages_per_second=10, burst=20)
        )

    @classmethod
    def minimal(cls) -> SocketMiddlewareChain:
        """Fault handling only."""
        return cls().use(f"{_BUILTIN}.SocketFaultMiddleware", priority=2)


__all__ = ["SocketMiddlewareChain", "SocketMiddlewareEntry"]
