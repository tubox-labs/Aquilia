"""SocketCtx — the context object threaded through every middleware hook.

The socket analogue of ``RequestCtx``. One instance per connection, reused
across messages, with ``event`` reassigned before each message chain run.

``SocketCtx`` wraps :class:`~aquilia.sockets.connection.Connection` rather than
copying from it. In particular ``ctx.state`` **is** ``connection.state``, not a
second bag — a middleware and an event handler writing "the same" key must not
end up writing two different dicts.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aquilia.auth.core import Identity
    from aquilia.di import Container
    from aquilia.sessions.core import Session
    from aquilia.sockets.connection import Connection, ConnectionScope


class SocketCtx:
    """Per-connection middleware context.

    Attributes:
        connection: The live connection this context belongs to.
        namespace: Socket namespace (the ``@Socket`` path pattern).
        event: Event name of the message currently in flight; ``None`` during
            the connect and disconnect stages.
        started_monotonic: ``time.monotonic()`` at context creation, used as the
            zero point for inspector span offsets.
    """

    __slots__ = ("connection", "namespace", "event", "started_monotonic", "_message_started")

    def __init__(self, connection: Connection, namespace: str | None = None):
        self.connection = connection
        self.namespace = namespace or connection.namespace
        self.event: str | None = None
        self.started_monotonic = time.monotonic()
        self._message_started: float | None = None

    # ── Connection passthroughs ──────────────────────────────────────────
    # Properties rather than copied attributes: identity and session can be
    # reassigned on the connection mid-lifetime (a re-auth middleware), and a
    # snapshot taken at connect time would silently go stale.

    @property
    def state(self) -> dict[str, Any]:
        """Mutable per-connection state. Freed when the connection closes.

        This is the canonical place for middleware to stash per-connection data.
        Prefer it over a ``dict`` keyed by connection id on the middleware
        instance, which leaks unless you also clean up in ``on_disconnect``.
        """
        return self.connection.state

    @property
    def identity(self) -> Identity | None:
        """Authenticated identity resolved during the handshake, if any."""
        return self.connection.identity

    @property
    def session(self) -> Session | None:
        """Session resolved during the handshake, if any."""
        return self.connection.session

    @property
    def container(self) -> Container:
        """Connection-scoped DI container."""
        return self.connection.container

    @property
    def connection_id(self) -> str:
        return self.connection.connection_id

    @property
    def scope(self) -> ConnectionScope:
        """Handshake-derived metadata: path, path_params, query_params, headers."""
        return self.connection.scope

    @property
    def is_connected(self) -> bool:
        return self.connection.is_connected

    # ── Convenience ──────────────────────────────────────────────────────

    async def resolve(self, name: str, optional: bool = False) -> Any:
        """Resolve a dependency from the connection-scoped DI container."""
        return await self.connection.resolve(name, optional=optional)

    def client_key(self) -> str:
        """Best available stable key for this client.

        Identity id when authenticated, else the connection id. Used by the
        rate limiter so an authenticated user shares one bucket across their
        connections while anonymous clients are limited per connection.
        """
        identity = self.identity
        if identity is not None and getattr(identity, "id", None):
            return f"user:{identity.id}"
        return f"conn:{self.connection_id}"

    # ── Message framing (used by the stack, not by middleware) ───────────

    def begin_message(self, event: str | None) -> None:
        self.event = event
        self._message_started = time.monotonic()

    def end_message(self) -> None:
        self.event = None
        self._message_started = None

    @property
    def message_elapsed_ms(self) -> float:
        """Milliseconds since the current message entered the chain (0 if none)."""
        if self._message_started is None:
            return 0.0
        return (time.monotonic() - self._message_started) * 1000.0

    def __repr__(self) -> str:
        return f"SocketCtx(connection_id={self.connection_id}, namespace={self.namespace}, event={self.event})"


__all__ = ["SocketCtx"]
