"""WebSocket middleware type aliases and protocols.

Mirrors the role of ``aquilia/typing/middleware.py`` for the socket transport.
Imports nothing from the rest of the framework at runtime; all types are
forward references resolved under ``TYPE_CHECKING``.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Protocol, TypeAlias

if TYPE_CHECKING:
    from aquilia.sockets.envelope import MessageEnvelope
    from aquilia.sockets.middleware.context import SocketCtx

SocketMiddlewareName: TypeAlias = str
SocketMiddlewareScope: TypeAlias = str  # "global" | "namespace:/chat" | "event:message.send"
SocketMiddlewarePriority: TypeAlias = int

# Connect stage: no per-message payload, so the handler takes context only.
ConnectHandler: TypeAlias = Callable[["SocketCtx"], Awaitable[None]]

# Message stage: payload first, context second, same reading order as HTTP's
# (request, ctx, next_handler). Returns None (no reply) or a dict (ack payload).
MessageHandler: TypeAlias = Callable[["MessageEnvelope", "SocketCtx"], Awaitable["dict | None"]]

# Disconnect stage: notification only, no continuation.
DisconnectHandler: TypeAlias = Callable[["SocketCtx", "str | None"], Awaitable[None]]


class SocketMiddlewareProtocol(Protocol):
    """Structural type for anything the socket stack will accept."""

    async def on_connect(self, ctx: SocketCtx, next_handler: ConnectHandler) -> None: ...

    async def on_message(
        self,
        envelope: MessageEnvelope,
        ctx: SocketCtx,
        next_handler: MessageHandler,
    ) -> dict | None: ...

    async def on_disconnect(self, ctx: SocketCtx, reason: str | None) -> None: ...


__all__ = [
    "SocketMiddlewareName",
    "SocketMiddlewareScope",
    "SocketMiddlewarePriority",
    "ConnectHandler",
    "MessageHandler",
    "DisconnectHandler",
    "SocketMiddlewareProtocol",
]
