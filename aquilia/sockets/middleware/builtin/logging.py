"""SocketLoggingMiddleware — structured lifecycle and message logging.

The old ``LoggingMiddleware`` in the flat socket middleware module accepted a
``log_payloads`` flag and then logged nothing at all. This one actually logs, and
treats payload logging as the disclosure risk it is.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aquilia.sockets.middleware.base import SocketMiddleware
from aquilia.sockets.middleware.types import ConnectHandler, MessageHandler

if TYPE_CHECKING:
    from aquilia.sockets.envelope import MessageEnvelope

    from aquilia.sockets.middleware.context import SocketCtx

logger = logging.getLogger("aquilia.sockets.middleware.logging")


class SocketLoggingMiddleware(SocketMiddleware):
    """
    Logs connects, messages, and disconnects.

    Registered at **priority 5** — inside fault handling (2) so a fault is logged
    by the fault middleware with its structured code, outside everything else so
    timings cover the whole chain.

    ``log_payloads`` is off by default and should stay off in production. Message
    payloads routinely carry exactly the material you do not want in a log
    aggregator: chat text, credentials in a login event, personal data. When it
    is on, payloads are truncated to ``max_payload_chars``, which bounds the
    volume but does not make the content safe.

    Args:
        level: Level for normal message logs.
        log_payloads: Include (truncated) payloads. Development only.
        max_payload_chars: Truncation limit when payloads are logged.
        log_lifecycle: Log connect and disconnect events.
    """

    def __init__(
        self,
        *,
        level: int = logging.DEBUG,
        log_payloads: bool = False,
        max_payload_chars: int = 512,
        log_lifecycle: bool = True,
    ):
        self.level = level
        self.log_payloads = log_payloads
        self.max_payload_chars = max_payload_chars
        self.log_lifecycle = log_lifecycle

    async def on_connect(self, ctx: SocketCtx, next_handler: ConnectHandler) -> None:
        if self.log_lifecycle:
            identity = ctx.identity
            logger.info(
                "WS connect ns=%s conn=%s identity=%s",
                ctx.namespace,
                ctx.connection_id,
                getattr(identity, "id", "anonymous"),
            )
        await next_handler(ctx)

    async def on_message(
        self,
        envelope: MessageEnvelope,
        ctx: SocketCtx,
        next_handler: MessageHandler,
    ) -> dict | None:
        result = await next_handler(envelope, ctx)

        if logger.isEnabledFor(self.level):
            logger.log(
                self.level,
                "WS message ns=%s conn=%s event=%s duration_ms=%.2f%s",
                ctx.namespace,
                ctx.connection_id,
                envelope.event,
                ctx.message_elapsed_ms,
                self._payload_suffix(envelope),
            )

        # The socket stack cannot detect a middleware that forgot to return the
        # way HTTP does, because None is a legal handler result. A requested ack
        # that ended up with no payload is the observable symptom, so surface it.
        if result is None and envelope.ack and logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "WS event=%s requested an ack but the chain produced no payload; "
                "a middleware may have returned without returning next_handler's result",
                envelope.event,
            )

        return result

    async def on_disconnect(self, ctx: SocketCtx, reason: str | None) -> None:
        if self.log_lifecycle:
            logger.info(
                "WS disconnect ns=%s conn=%s reason=%s sent=%d received=%d",
                ctx.namespace,
                ctx.connection_id,
                reason,
                ctx.connection.messages_sent,
                ctx.connection.messages_received,
            )

    def _payload_suffix(self, envelope: MessageEnvelope) -> str:
        if not self.log_payloads:
            return ""
        text = repr(envelope.payload)
        if len(text) > self.max_payload_chars:
            text = f"{text[: self.max_payload_chars]}...(truncated)"
        return f" payload={text}"


__all__ = ["SocketLoggingMiddleware"]
