"""Shipped WebSocket middleware.

One concern per module. Import from here (or from
``aquilia.sockets.middleware``) rather than reaching into the submodules, so the
layout can change without breaking configuration that names these by dotted path.
"""

from aquilia.sockets.middleware.builtin.auth import SocketAuthMiddleware
from aquilia.sockets.middleware.builtin.authorization import SocketPermissionMiddleware
from aquilia.sockets.middleware.builtin.faults import SocketFaultMiddleware
from aquilia.sockets.middleware.builtin.logging import SocketLoggingMiddleware
from aquilia.sockets.middleware.builtin.metrics import SocketMetricsMiddleware
from aquilia.sockets.middleware.builtin.rate_limit import SocketRateLimitMiddleware
from aquilia.sockets.middleware.builtin.validation import (
    DEFAULT_MAX_MESSAGE_SIZE,
    DEFAULT_MAX_PAYLOAD_SIZE,
    MessageValidationMiddleware,
)

__all__ = [
    "SocketFaultMiddleware",
    "SocketLoggingMiddleware",
    "SocketMetricsMiddleware",
    "MessageValidationMiddleware",
    "SocketRateLimitMiddleware",
    "SocketAuthMiddleware",
    "SocketPermissionMiddleware",
    "DEFAULT_MAX_MESSAGE_SIZE",
    "DEFAULT_MAX_PAYLOAD_SIZE",
]
