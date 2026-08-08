"""WebSocket middleware base class — dependency-free leaf module.

Deliberately mirrors ``aquilia/_middleware_base.py``, which exists to break the
``aquilia.middleware`` ↔ ``aquilia.faults.engine`` import cycle. Keeping this
base free of ``aquilia.faults`` means ``SocketFaultMiddleware`` can subclass it
without pulling the fault engine into the ``aquilia.sockets`` import graph, so
the same cycle cannot recur on the socket side.

Import nothing from ``aquilia.faults``, ``aquilia.sockets.runtime``, or
``aquilia.middleware`` here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from aquilia.sockets.middleware.types import ConnectHandler, MessageHandler

if TYPE_CHECKING:
    from aquilia.sockets.envelope import MessageEnvelope
    from aquilia.sockets.middleware.context import SocketCtx


class SocketMiddleware:
    """Base class for all WebSocket middleware.

    A WebSocket connection has three lifecycle stages, not one. Override only
    the hooks you need — the stack detects which are overridden at registration
    time and omits the middleware from chains it does not participate in, so an
    ``on_message``-only middleware adds zero frames to the connect path.

    The parameter order mirrors HTTP middleware (``request, ctx, next_handler``):
    payload first, context second, continuation last.

    Example::

        class PresenceMiddleware(SocketMiddleware):
            async def on_connect(self, ctx, next_handler):
                await ctx.resolve("presence").mark_online(ctx.identity.id)
                await next_handler(ctx)

            async def on_message(self, envelope, ctx, next_handler):
                envelope.meta["sender"] = ctx.identity.id
                return await next_handler(envelope, ctx)

    Short-circuiting:

    - ``on_connect``: raise a ``SocketFault`` to reject the handshake. The
      connection is closed with the fault's ``ws_close_code`` and never accepted.
    - ``on_message``: return without awaiting ``next_handler``. The handler never
      runs; a returned dict becomes the ack payload if one was requested.
    - ``on_disconnect``: cannot short-circuit. Teardown always completes.

    Per-connection state belongs on ``ctx.state``, which is freed when the
    connection closes. Storing it in a ``dict`` keyed by connection id on the
    middleware instance leaks for the lifetime of the process unless you also
    implement ``on_disconnect`` to clean up.
    """

    async def on_connect(self, ctx: SocketCtx, next_handler: ConnectHandler) -> None:
        """Run once, before the handshake is accepted."""
        await next_handler(ctx)

    async def on_message(
        self,
        envelope: MessageEnvelope,
        ctx: SocketCtx,
        next_handler: MessageHandler,
    ) -> dict | None:
        """Run once per inbound message, before the event handler."""
        return await next_handler(envelope, ctx)

    async def on_disconnect(self, ctx: SocketCtx, reason: str | None) -> None:
        """Run once, during teardown. No continuation: this is a notification.

        Disconnect hooks run in reverse registration order (LIFO), so anything
        acquired in ``on_connect`` unwinds with every inner middleware's teardown
        already complete. An exception here is logged and the remaining hooks
        still run.
        """
        return None


# Sentinels used to detect which hooks a subclass actually overrides. Captured
# once at class-definition time rather than looked up per registration.
_BASE_ON_CONNECT = SocketMiddleware.on_connect
_BASE_ON_MESSAGE = SocketMiddleware.on_message
_BASE_ON_DISCONNECT = SocketMiddleware.on_disconnect


def implements_connect(middleware: object) -> bool:
    """True when *middleware* overrides :meth:`SocketMiddleware.on_connect`."""
    return getattr(type(middleware), "on_connect", _BASE_ON_CONNECT) is not _BASE_ON_CONNECT


def implements_message(middleware: object) -> bool:
    """True when *middleware* overrides :meth:`SocketMiddleware.on_message`."""
    return getattr(type(middleware), "on_message", _BASE_ON_MESSAGE) is not _BASE_ON_MESSAGE


def implements_disconnect(middleware: object) -> bool:
    """True when *middleware* overrides :meth:`SocketMiddleware.on_disconnect`."""
    return getattr(type(middleware), "on_disconnect", _BASE_ON_DISCONNECT) is not _BASE_ON_DISCONNECT


__all__ = [
    "SocketMiddleware",
    "implements_connect",
    "implements_message",
    "implements_disconnect",
]
