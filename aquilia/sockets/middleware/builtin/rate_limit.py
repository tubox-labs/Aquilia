"""SocketRateLimitMiddleware — inbound message rate limiting.

Uses the same token bucket as HTTP rate limiting (:mod:`aquilia.middleware.utils.throttling`), so
the two transports cannot drift in enforcement behaviour. Buckets live in a
shared expiry-aware store and are released explicitly on disconnect.

Scope: **inbound messages only.** Outbound sends (``conn.send_event``,
``publish_room``, adapter fan-out) do not traverse any middleware chain and are
not limited here.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aquilia.middleware.utils.throttling import BucketStore, TokenBucket
from aquilia.sockets.middleware.base import SocketMiddleware
from aquilia.sockets.middleware.types import MessageHandler

if TYPE_CHECKING:
    from aquilia.sockets.envelope import MessageEnvelope
    from aquilia.sockets.middleware.context import SocketCtx

logger = logging.getLogger("aquilia.sockets.middleware.rate_limit")


class SocketRateLimitMiddleware(SocketMiddleware):
    """
    Token-bucket rate limiting for inbound WebSocket messages.

    Registered at **priority 12**, matching the HTTP limiter's slot: after
    validation (10), before auth (15). Unlike HTTP there is no ordering hazard
    around identity — a socket's identity is resolved during the handshake, so it
    is already present by the time any message arrives, and per-user keying works
    at any priority.

    Keying (``key_by``):

    - ``"client"`` (default) — identity id when authenticated, connection id
      otherwise. An authenticated user shares one bucket across all their
      connections; anonymous clients are limited per connection.
    - ``"connection"`` — always per connection, even when authenticated.
    - ``"identity"`` — per identity; anonymous connections are not limited.

    Buckets are dropped on disconnect, and the store additionally evicts idle
    entries on a lazy schedule, so neither churn nor long-lived idle connections
    accumulate state.

    State is per-process. Across N workers the effective limit for a key not
    pinned to one worker is ``limit x N``; a socket connection does pin to one
    worker for its lifetime, so per-connection keying is exact and per-identity
    keying is not.

    Args:
        messages_per_second: Sustained refill rate.
        burst: Bucket capacity — how many messages can arrive back to back.
            Defaults to ``messages_per_second`` when not given.
        key_by: ``"client"``, ``"connection"``, or ``"identity"``.
        exempt_events: Event names that bypass the limit entirely. Keep this
            small; anything exempt is an unmetered channel.
    """

    def __init__(
        self,
        messages_per_second: int = 10,
        burst: int | None = None,
        *,
        key_by: str = "client",
        exempt_events: list[str] | None = None,
    ):
        if key_by not in ("client", "connection", "identity"):
            from aquilia.faults.domains import ConfigInvalidFault

            raise ConfigInvalidFault(
                "socket.rate_limit.key_by",
                f"expected 'client', 'connection', or 'identity', got {key_by!r}",
            )

        self.messages_per_second = messages_per_second
        self.burst = burst if burst is not None else messages_per_second
        self.key_by = key_by
        self.exempt_events = set(exempt_events or ())
        self._buckets = BucketStore()

    def _factory(self) -> TokenBucket:
        return TokenBucket(capacity=self.burst, refill_rate=float(self.messages_per_second))

    def _key(self, ctx: SocketCtx) -> str | None:
        if self.key_by == "connection":
            return f"conn:{ctx.connection_id}"
        if self.key_by == "identity":
            identity = ctx.identity
            ident_id = getattr(identity, "id", None) if identity else None
            # No identity means no key: an anonymous connection is simply not
            # covered by an identity-keyed rule.
            return f"user:{ident_id}" if ident_id else None
        return ctx.client_key()

    async def on_message(
        self,
        envelope: MessageEnvelope,
        ctx: SocketCtx,
        next_handler: MessageHandler,
    ) -> dict | None:
        from aquilia.sockets.faults import WS_RATE_LIMIT_EXCEEDED

        if envelope.event in self.exempt_events:
            return await next_handler(envelope, ctx)

        key = self._key(ctx)
        if key is None:
            return await next_handler(envelope, ctx)

        bucket = self._buckets.get_or_create(key, self._factory)
        allowed, _retry_after = bucket.consume()

        if not allowed:
            raise WS_RATE_LIMIT_EXCEEDED(self.messages_per_second)

        return await next_handler(envelope, ctx)

    async def on_disconnect(self, ctx: SocketCtx, reason: str | None) -> None:
        # Only connection-keyed buckets die with the connection. An identity
        # bucket may still be in use by that user's other connections, so it is
        # left to the store's idle eviction.
        if self.key_by == "connection" or (self.key_by == "client" and ctx.identity is None):
            self._buckets.discard(f"conn:{ctx.connection_id}")


__all__ = ["SocketRateLimitMiddleware"]
