"""MessageValidationMiddleware — envelope shape and payload size limits.

Replaces the never-invoked ``MessageValidationMiddleware`` from the old flat
``aquilia/sockets/middleware.py``, adapted to the three-hook base class.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from aquilia.sockets.middleware.base import SocketMiddleware
from aquilia.sockets.middleware.types import MessageHandler

if TYPE_CHECKING:
    from aquilia.sockets.envelope import MessageEnvelope
    from aquilia.sockets.middleware.context import SocketCtx

logger = logging.getLogger("aquilia.sockets.middleware.validation")

DEFAULT_MAX_MESSAGE_SIZE = 65536  # 64 KiB
DEFAULT_MAX_PAYLOAD_SIZE = 32768  # 32 KiB


class MessageValidationMiddleware(SocketMiddleware):
    """
    Validates envelope structure and payload size.

    Registered at **priority 10**, so it runs before rate limiting and auth:
    a structurally invalid message should be rejected before anything spends
    effort deciding who sent it.

    Note on ``max_message_size``: the *whole-frame* size limit is enforced by the
    runtime against the raw bytes, before decode — you cannot safely decode a
    frame to discover it was too large to decode. What this middleware enforces
    is the size of the already-decoded ``payload``, which is the limit that
    protects handlers rather than the parser.

    Args:
        max_payload_size: Maximum serialised payload size in bytes.
        allowed_events: Optional whitelist of event names. When set, anything
            else is rejected before dispatch. Useful for namespaces with a small
            fixed protocol.
        require_event: Reject envelopes with no event name.
    """

    def __init__(
        self,
        max_payload_size: int = DEFAULT_MAX_PAYLOAD_SIZE,
        *,
        max_message_size: int = DEFAULT_MAX_MESSAGE_SIZE,
        allowed_events: list[str] | None = None,
        require_event: bool = True,
    ):
        self.max_payload_size = max_payload_size
        # Kept so a runtime that enforces frame size can read the configured
        # value off the middleware rather than needing a second config source.
        self.max_message_size = max_message_size
        self.allowed_events = set(allowed_events) if allowed_events else None
        self.require_event = require_event

    async def on_message(
        self,
        envelope: MessageEnvelope,
        ctx: SocketCtx,
        next_handler: MessageHandler,
    ) -> dict | None:
        from aquilia.sockets.faults import (
            WS_MESSAGE_INVALID,
            WS_PAYLOAD_TOO_LARGE,
            WS_UNSUPPORTED_EVENT,
        )

        if self.require_event and not envelope.event:
            raise WS_MESSAGE_INVALID("missing event name")

        if self.allowed_events is not None and envelope.event not in self.allowed_events:
            raise WS_UNSUPPORTED_EVENT(envelope.event)

        payload_size = self._payload_size(envelope)
        if payload_size > self.max_payload_size:
            raise WS_PAYLOAD_TOO_LARGE(payload_size, self.max_payload_size)

        return await next_handler(envelope, ctx)

    def _payload_size(self, envelope: MessageEnvelope) -> int:
        """Serialised payload size in bytes.

        A payload that cannot be serialised at all is treated as invalid rather
        than as size zero — silently passing something the codec will choke on
        later just moves the failure somewhere with less context.
        """
        from aquilia.sockets.faults import WS_MESSAGE_INVALID

        try:
            return len(json.dumps(envelope.payload).encode("utf-8"))
        except (TypeError, ValueError) as exc:
            raise WS_MESSAGE_INVALID(f"payload is not JSON-serialisable: {exc}") from exc


__all__ = ["MessageValidationMiddleware", "DEFAULT_MAX_MESSAGE_SIZE", "DEFAULT_MAX_PAYLOAD_SIZE"]
