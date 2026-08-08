"""
WebSocket Middleware — per-connection and per-message processing pipeline.

Mirrors the ergonomics of :mod:`aquilia.middleware` so HTTP intuition transfers:
same ``(scope, priority)`` ordering with ascending priority meaning outermost,
same ``next_handler`` idiom, same fluent chain builder in ``workspace.py``.

What differs is forced by the transport. HTTP has one lifecycle stage and every
handler owes a ``Response``; a WebSocket has three stages and a handler may
legitimately reply with nothing::

    class PresenceMiddleware(SocketMiddleware):
        async def on_connect(self, ctx, next_handler):
            ...
            await next_handler(ctx)

        async def on_message(self, envelope, ctx, next_handler):
            ...
            return await next_handler(envelope, ctx)

        async def on_disconnect(self, ctx, reason):
            ...

Override only the hooks you need — the stack omits a middleware from the chains
whose hook it does not implement.

Security parity warning
-----------------------
This is a **separate** middleware system from :mod:`aquilia.middleware`. HTTP
middleware configured through ``Workspace.security(...)`` — CORS, rate limiting,
CSRF, auth — does **not** apply to WebSocket messages. A socket surface is
protected only by the middleware registered on its own chain. Configure it with
``Workspace.socket_middleware(SocketMiddlewareChain...)``.

Algorithms with real drift risk are shared rather than reimplemented: the socket
rate limiter uses the same token bucket as the HTTP one (:mod:`aquilia._ratelimit`).
The *pipeline* stays separate, because the signatures and lifecycles genuinely
differ and a shared generic would fit neither.
"""

from aquilia.sockets.middleware.base import (
    SocketMiddleware,
    implements_connect,
    implements_disconnect,
    implements_message,
)
from aquilia.sockets.middleware.builtin import (
    MessageValidationMiddleware,
    SocketAuthMiddleware,
    SocketFaultMiddleware,
    SocketLoggingMiddleware,
    SocketMetricsMiddleware,
    SocketPermissionMiddleware,
    SocketRateLimitMiddleware,
)
from aquilia.sockets.middleware.chain import SocketMiddlewareChain, SocketMiddlewareEntry
from aquilia.sockets.middleware.context import SocketCtx
from aquilia.sockets.middleware.stack import (
    SCOPE_ORDER,
    SocketMiddlewareDescriptor,
    SocketMiddlewareStack,
)
from aquilia.sockets.middleware.types import (
    ConnectHandler,
    DisconnectHandler,
    MessageHandler,
    SocketMiddlewareProtocol,
)

# ── Backward compatibility ───────────────────────────────────────────────
# The previous flat module exported RateLimitMiddleware. The class moved and was
# renamed for symmetry with the other socket middleware; the old name still
# resolves so existing imports and dotted-path config keep working.
RateLimitMiddleware = SocketRateLimitMiddleware

# Names that existed on the old flat module and have no drop-in replacement.
# Surfaced through __getattr__ so the import fails with a migration path instead
# of a bare AttributeError.
_REMOVED = {
    "MiddlewareChain": (
        "MiddlewareChain was never invoked by the socket runtime. Use "
        "SocketMiddlewareStack (programmatic) or SocketMiddlewareChain "
        "(workspace.py configuration) instead."
    ),
    "LoggingMiddleware": "Renamed to SocketLoggingMiddleware, and it now actually logs.",
    "MetricsMiddleware": "Renamed to SocketMetricsMiddleware; call snapshot() for the counters.",
}


def __getattr__(name: str):
    guidance = _REMOVED.get(name)
    if guidance is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    raise ImportError(f"'{name}' was removed from aquilia.sockets.middleware. {guidance}")


__all__ = [
    # Base + context
    "SocketMiddleware",
    "SocketCtx",
    # Stack
    "SocketMiddlewareStack",
    "SocketMiddlewareDescriptor",
    "SCOPE_ORDER",
    # Config builder
    "SocketMiddlewareChain",
    "SocketMiddlewareEntry",
    # Builtin middleware
    "SocketFaultMiddleware",
    "SocketLoggingMiddleware",
    "SocketMetricsMiddleware",
    "MessageValidationMiddleware",
    "SocketRateLimitMiddleware",
    "SocketAuthMiddleware",
    "SocketPermissionMiddleware",
    # Types
    "ConnectHandler",
    "MessageHandler",
    "DisconnectHandler",
    "SocketMiddlewareProtocol",
    # Hook introspection
    "implements_connect",
    "implements_message",
    "implements_disconnect",
    # Deprecated alias
    "RateLimitMiddleware",
]
