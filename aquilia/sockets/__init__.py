"""
AquilaSockets - WebSocket subsystem for Aquilia

Production-grade WebSocket support with:
- Manifest-first & zero import-time effects
- Controller-based declarative syntax
- DI scoped containers per connection
- Auth-first handshake & per-message guards
- Horizontal scaling via adapters (Redis, NATS, Kafka)
- Backpressure & flow control
- Observability & audit
- Secure defaults

Philosophy:
- WebSocket controllers are compiled at build time
- Each connection has its own DI scope
- Messages are typed and validated
- Rooms/namespaces for pub/sub semantics
- Adapter-driven for scale-out
"""

from aquilia._version import __version__  # noqa: F401 — re-exported

from .adapters import (
    Adapter,
    InMemoryAdapter,
    RedisAdapter,
)
from .connection import (
    Connection,
    ConnectionScope,
    ConnectionState,
)
from .controller import (
    SocketController,
)
from .decorators import (
    AckEvent,
    Event,
    Guard,
    OnConnect,
    OnDisconnect,
    Socket,
    Subscribe,
    Unsubscribe,
)
from .envelope import (
    JSONCodec,
    MessageCodec,
    MessageEnvelope,
    MessageType,
    Schema,
)
from .faults import (
    WS_AUTH_REQUIRED,
    WS_CONNECTION_CLOSED,
    WS_HANDSHAKE_FAILED,
    WS_MESSAGE_INVALID,
    WS_PAYLOAD_TOO_LARGE,
    WS_RATE_LIMIT_EXCEEDED,
    WS_ROOM_FULL,
    SocketFault,
)
from .guards import (
    HandshakeAuthGuard,
    MessageAuthGuard,
    OriginGuard,
    RateLimitGuard,
    SocketGuard,
)
from .middleware import (
    MessageValidationMiddleware,
    RateLimitMiddleware,
    SocketMiddleware,
)
from .runtime import (
    AquilaSockets,
    SocketRouter,
)

__all__ = [
    # Core
    "SocketController",
    "Connection",
    # Decorators
    "Socket",
    "OnConnect",
    "OnDisconnect",
    "Event",
    "AckEvent",
    "Subscribe",
    "Unsubscribe",
    "Guard",
    # Envelope
    "MessageEnvelope",
    "MessageType",
    "MessageCodec",
    "JSONCodec",
    "Schema",
    # Connection
    "ConnectionState",
    "ConnectionScope",
    # Runtime
    "AquilaSockets",
    "SocketRouter",
    # Adapters
    "Adapter",
    "InMemoryAdapter",
    "RedisAdapter",
    # Guards
    "SocketGuard",
    "HandshakeAuthGuard",
    "OriginGuard",
    "MessageAuthGuard",
    "RateLimitGuard",
    # Faults
    "SocketFault",
    "WS_HANDSHAKE_FAILED",
    "WS_AUTH_REQUIRED",
    "WS_MESSAGE_INVALID",
    "WS_ROOM_FULL",
    "WS_RATE_LIMIT_EXCEEDED",
    "WS_CONNECTION_CLOSED",
    "WS_PAYLOAD_TOO_LARGE",
    # Middleware
    "SocketMiddleware",
    "MessageValidationMiddleware",
    "RateLimitMiddleware",
]
