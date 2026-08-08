"""SocketFaultMiddleware — turn faults into structured replies instead of silence.

The socket analogue of :class:`aquilia.faults.engine.FaultMiddleware`, and for
the same reason: without it, an exception raised in an event handler is caught by
the message loop, written to the log, and the client is told nothing at all.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aquilia.faults import Fault
from aquilia.sockets.middleware.base import SocketMiddleware
from aquilia.sockets.middleware.types import MessageHandler

if TYPE_CHECKING:
    from aquilia.sockets.envelope import MessageEnvelope
    from aquilia.sockets.middleware.context import SocketCtx

logger = logging.getLogger("aquilia.sockets.middleware.faults")

# Close code used when a fault carries no ws_close_code of its own.
# 1011 = "internal error" per RFC 6455 §7.4.1.
_DEFAULT_CLOSE_CODE = 1011


class SocketFaultMiddleware(SocketMiddleware):
    """
    Converts faults raised downstream into error acks.

    Registered at **priority 2**, mirroring HTTP's ``FaultMiddleware``, so it sits
    outside everything that might raise and inside nothing that needs to see the
    raw exception.

    Behaviour:

    - A :class:`~aquilia.faults.Fault` becomes an error ack carrying its ``code``
      and ``message`` — structured, client-parseable, and safe to show.
    - An unexpected ``Exception`` becomes a generic error ack. The message is
      **not** included unless ``debug`` is set, because an arbitrary exception
      string can carry connection strings, file paths, or row data.
    - Either way the exception does not propagate, so one bad message does not
      tear down a connection that is otherwise healthy.

    Connect-stage faults are deliberately *not* caught: rejecting a handshake is
    the correct response to a connect fault, and the runtime already translates
    it into a close frame with the fault's ``ws_close_code``.

    Args:
        debug: Include exception detail for non-Fault errors. Never enable in
            production — it is the socket equivalent of a stack trace in an
            HTTP response body.
        send_error_ack: Send the error back to the client. Disable only if you
            have another mechanism and want faults purely logged.
    """

    def __init__(self, *, debug: bool = False, send_error_ack: bool = True):
        self.debug = debug
        self.send_error_ack = send_error_ack

    async def on_message(
        self,
        envelope: MessageEnvelope,
        ctx: SocketCtx,
        next_handler: MessageHandler,
    ) -> dict | None:
        try:
            return await next_handler(envelope, ctx)
        except Fault as fault:
            logger.warning(
                "Socket fault on %s (%s): %s",
                envelope.event,
                fault.code,
                fault.message,
            )
            await self._send_error(ctx, envelope, code=fault.code, message=fault.message)
            return None
        except Exception as exc:  # noqa: BLE001 — the whole point is to not propagate
            logger.error(
                "Unhandled error in socket event '%s': %s",
                envelope.event,
                exc,
                exc_info=True,
            )
            await self._send_error(
                ctx,
                envelope,
                code="WS_INTERNAL_ERROR",
                message=str(exc) if self.debug else "Internal server error",
            )
            return None

    async def _send_error(
        self,
        ctx: SocketCtx,
        envelope: MessageEnvelope,
        *,
        code: str,
        message: str,
    ) -> None:
        if not self.send_error_ack or not ctx.is_connected:
            return

        try:
            if envelope.id:
                # The client is waiting on this id; reply on the ack channel.
                await ctx.connection.send_ack(envelope.id, status="error", error=message)
            else:
                await ctx.connection.send_event(
                    "error",
                    {"code": code, "message": message, "event": envelope.event},
                )
        except Exception as exc:  # noqa: BLE001 — the socket may already be gone
            logger.debug("Could not deliver socket error ack: %s", exc)


__all__ = ["SocketFaultMiddleware"]
