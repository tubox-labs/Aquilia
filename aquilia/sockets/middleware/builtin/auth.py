"""SocketAuthMiddleware — identity requirements at connect and message time.

Replaces the never-invoked ``MessageAuthGuard`` from ``aquilia/sockets/guards.py``.
That guard kept a ``dict`` of last-check timestamps keyed by connection id and
never removed an entry; this keeps the same state on ``ctx.state``, which is
freed with the connection.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from aquilia.sockets.middleware.base import SocketMiddleware
from aquilia.sockets.middleware.types import ConnectHandler, MessageHandler

if TYPE_CHECKING:
    from aquilia.sockets.envelope import MessageEnvelope

    from aquilia.sockets.middleware.context import SocketCtx

logger = logging.getLogger("aquilia.sockets.middleware.auth")

_LAST_CHECK_KEY = "_auth_last_check"


class SocketAuthMiddleware(SocketMiddleware):
    """
    Enforces authentication at handshake, and re-validates during the connection.

    Registered at **priority 15**, matching HTTP's auth slot.

    The re-validation matters more here than on HTTP. An HTTP request carries its
    credential every time, so a revoked identity stops working on the next
    request. A WebSocket authenticates once at handshake and can then stay open
    for hours — without a periodic re-check, revoking access has no effect until
    the client happens to reconnect.

    Args:
        require_identity: Reject handshakes with no authenticated identity.
        require_session: Reject handshakes with no session.
        allowed_identity_types: Whitelist of ``identity.type.value`` values.
        recheck_interval: Seconds between per-message identity re-validations.
            Set to ``0`` to disable re-checking (handshake-only auth).
    """

    def __init__(
        self,
        *,
        require_identity: bool = True,
        require_session: bool = False,
        allowed_identity_types: list[str] | None = None,
        recheck_interval: int = 300,
    ):
        self.require_identity = require_identity
        self.require_session = require_session
        self.allowed_identity_types = allowed_identity_types
        self.recheck_interval = recheck_interval

    async def on_connect(self, ctx: SocketCtx, next_handler: ConnectHandler) -> None:
        from aquilia.sockets.faults import WS_AUTH_REQUIRED, WS_FORBIDDEN

        identity = ctx.identity

        if self.require_identity and identity is None:
            raise WS_AUTH_REQUIRED()

        if self.require_session and ctx.session is None:
            raise WS_FORBIDDEN("session required")

        if identity is not None:
            self._assert_identity_usable(identity)

        ctx.state[_LAST_CHECK_KEY] = time.monotonic()
        await next_handler(ctx)

    async def on_message(
        self,
        envelope: MessageEnvelope,
        ctx: SocketCtx,
        next_handler: MessageHandler,
    ) -> dict | None:
        from aquilia.sockets.faults import WS_AUTH_REQUIRED

        if self.recheck_interval > 0:
            now = time.monotonic()
            last = ctx.state.get(_LAST_CHECK_KEY, 0.0)

            if now - last > self.recheck_interval:
                identity = ctx.identity
                if self.require_identity and identity is None:
                    raise WS_AUTH_REQUIRED()
                if identity is not None:
                    self._assert_identity_usable(identity)
                ctx.state[_LAST_CHECK_KEY] = now

        return await next_handler(envelope, ctx)

    def _assert_identity_usable(self, identity: object) -> None:
        from aquilia.sockets.faults import WS_FORBIDDEN

        if self.allowed_identity_types:
            identity_type = getattr(getattr(identity, "type", None), "value", None)
            if identity_type not in self.allowed_identity_types:
                raise WS_FORBIDDEN(f"identity type {identity_type} not allowed")

        is_active = getattr(identity, "is_active", None)
        if callable(is_active) and not is_active():
            raise WS_FORBIDDEN("identity is not active")


__all__ = ["SocketAuthMiddleware"]
