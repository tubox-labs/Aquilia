# SocketController (WebSocket)

## Overview

`SocketController` provides class-based, declarative WebSocket handling with DI integration, room-based pub/sub, auth guards, and horizontal scaling via adapters. Controllers are declared with `@Socket(path)` and methods are decorated for lifecycle hooks and message handlers.

```python
from aquilia.sockets import (
    SocketController, Socket, OnConnect, Event,
    Connection, Schema,
)

@Socket("/chat/:namespace")
class ChatSocket(SocketController):
    def __init__(self, presence=Inject(tag="presence")):
        self.presence = presence

    @OnConnect()
    async def on_connect(self, conn: Connection):
        await conn.send_event("system.welcome", {"msg": "Connected"})

    @Event("message.send", schema=Schema({"room": str, "text": str}))
    async def handle_message(self, conn: Connection, payload):
        await self.publish_room(payload["room"], "message.receive", {
            "from": conn.identity.id,
            "text": payload["text"],
        })
```

---

## `SocketController` Base Class

!!! abstract "`aquilia.sockets.SocketController`"

### Class Attributes

| Attribute | Type | Default | Description |
|---|---|---|---|
| `namespace` | `str \| None` | `None` | Default namespace for rooms |
| `adapter` | `Adapter \| None` | `None` | Pub/sub adapter (set by runtime) |

### Constructor

```python
class SocketController:
    def __init__(self):
        """Override for DI injection:
            def __init__(self, service=Inject()):
                self.service = service
        """
```

### Publishing Methods

```python
async def publish_room(
    self,
    room: str,
    event: str,
    payload: dict[str, Any],
    *,
    namespace: str | None = None,
    exclude_connection: str | None = None,
):
    """Publish to all connections in a room via adapter."""

async def broadcast(
    self,
    event: str,
    payload: dict[str, Any],
    *,
    namespace: str | None = None,
    exclude_connection: str | None = None,
):
    """Broadcast to all connections in namespace via adapter."""
```

---

## Decorators

### `@Socket`

!!! abstract "`aquilia.sockets.Socket`"
    Class decorator

```python
class Socket:
    def __init__(
        self,
        path: str,
        *,
        allowed_origins: list[str] | None = None,
        max_connections: int | None = None,
        message_rate_limit: int | None = None,  # msgs/sec per connection
        max_message_size: int = 65536,           # 64KB
        compression: bool = True,
        subprotocols: list[str] | None = None,
    ):
```

Attaches `__socket_metadata__` dict to the class.

### `@OnConnect`

```python
class OnConnect:
    def __call__(self, func: F) -> F: ...
```

Called after handshake auth passes. Attaches `__socket_handler__ = {"type": "on_connect"}`.

```python
@OnConnect()
async def on_connect(self, conn: Connection):
    await conn.send_event("system.welcome", {"msg": "Hello"})
```

### `@OnDisconnect`

```python
class OnDisconnect:
    def __call__(self, func: F) -> F: ...
```

Attaches `__socket_handler__ = {"type": "on_disconnect"}`.

```python
@OnDisconnect()
async def on_disconnect(self, conn: Connection, reason: str | None):
    await self.presence.leave(conn.identity.id)
```

### `@Event`

```python
class Event:
    def __init__(
        self,
        event: str,
        *,
        schema: Schema | None = None,
        ack: bool = False,          # auto-send ack on success
    ):
```

Attaches `__socket_handler__ = {"type": "event", "event": ..., "schema": ..., "ack": ...}`.

```python
@Event("message.send", schema=Schema({"room": str, "text": str}))
async def handle_message(self, conn: Connection, payload):
    ...
```

### `@AckEvent`

```python
class AckEvent:
    def __init__(
        self,
        event: str,
        *,
        schema: Schema | None = None,
    ):
```

Acknowledgement-enabled: client expects `{status: "ok", data: ...}` or `{status: "error", message: ...}`.

### `@Subscribe`

```python
class Subscribe:
    def __init__(self, event: str):
    def __call__(self, func: F) -> F: ...
```

```python
@Subscribe("room.join")
async def on_join_room(self, conn: Connection, payload):
    await self.adapter.join_room(conn.id, payload["room"])
```

### `@Unsubscribe`

```python
class Unsubscribe:
    def __init__(self, event: str):
    def __call__(self, func: F) -> F: ...
```

### `@Guard`

```python
class Guard:
    def __init__(
        self,
        guard_instance: SocketGuard | None = None,
        *,
        type: str = "handshake",  # "handshake" | "message"
    ):
```

---

## Connection Lifecycle

```
Client connects
     │
     ▼
@Socket handshake (Origin validation, subprotocol negotiation)
     │
     ▼
HandshakeAuthGuard → authenticate (reject = raise WS_AUTH_REQUIRED)
     │
     ▼
@OnConnect() handler
     │
     ▼
connection.send_event("system.welcome", {...})
     │
     ▼
── Message Loop ──
  │ @Event("...")  handlers
  │ @Subscribe()   room management
  │ @MessageAuthGuard per-message auth
  │ @RateLimitGuard per-connection rate limiting
  └─►
     │
     ▼
@OnDisconnect() handler (cleanup)
     │
     ▼
Connection closed
```

---

## `Connection`

!!! abstract "`aquilia.sockets.Connection`"

Represents a single WebSocket connection.

```python
class Connection:
    id: str
    identity: Identity | None
    scope: dict[str, Any]
    namespace: str
    state: dict[str, Any]

    async def send_event(self, event: str, payload: dict[str, Any]) -> None: ...
    async def send_json(self, data: dict[str, Any]) -> None: ...
    async def send_raw(self, data: bytes) -> None: ...
    async def close(self, code: int = 1000, reason: str = "") -> None: ...
    async def ack(self, message_id: str, data: dict | None = None) -> None: ...
    async def error(self, message_id: str, error: str, code: str | None = None) -> None: ...
```

### `ConnectionState` Enum

```python
class ConnectionState(str, Enum):
    CONNECTING = "connecting"
    AUTHENTICATING = "authenticating"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    CLOSED = "closed"
```

### `ConnectionScope`

```python
class ConnectionScope:
    """Request-scoped DI container for this connection."""
    container: Any
    services: dict[str, Any]
```

---

## Envelope System

### `MessageEnvelope`

```python
@dataclass
class MessageEnvelope:
    type: MessageType
    event: str | None = None
    payload: dict[str, Any] | None = None
    message_id: str | None = None
    timestamp: float | None = None
```

### `MessageType` Enum

```python
class MessageType(str, Enum):
    EVENT = "event"
    ACK = "ack"
    ERROR = "error"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    SYSTEM = "system"
```

### `Schema`

```python
class Schema:
    def __init__(self, shape: dict[str, type]):
```

### `MessageCodec` (ABC)

```python
class MessageCodec(ABC):
    @abstractmethod
    async def encode(self, envelope: MessageEnvelope) -> bytes: ...
    @abstractmethod
    async def decode(self, data: bytes) -> MessageEnvelope: ...
```

### `JSONCodec`

```python
class JSONCodec(MessageCodec):
    async def encode(self, envelope: MessageEnvelope) -> bytes: ...
    async def decode(self, data: bytes) -> MessageEnvelope: ...
```

### `StreamChunk`

```python
@dataclass
class StreamChunk:
    data: Any
    index: int
    is_last: bool = False
```

---

## Guards

### `SocketGuard` (ABC)

```python
class SocketGuard(ABC):
    name: str

    @abstractmethod
    async def check(self, connection: Connection) -> bool: ...
```

### `HandshakeAuthGuard`

```python
class HandshakeAuthGuard(SocketGuard):
    async def check(self, connection: Connection) -> bool: ...
```

### `OriginGuard`

```python
class OriginGuard(SocketGuard):
    def __init__(self, allowed_origins: list[str]):
    async def check(self, connection: Connection) -> bool: ...
```

### `MessageAuthGuard`

```python
class MessageAuthGuard(SocketGuard):
    async def check(self, connection: Connection) -> bool: ...
```

Per-message auth check (e.g., JWT expiry on each message).

### `RateLimitGuard`

```python
class RateLimitGuard(SocketGuard):
    def __init__(self, max_messages: int, window_seconds: int):
    async def check(self, connection: Connection) -> bool: ...
```

---

## Adapters

For horizontal scaling across workers.

### `Adapter` (ABC)

```python
class Adapter(ABC):
    @abstractmethod
    async def publish(self, namespace: str, room: str, envelope: MessageEnvelope,
                      *, exclude_connection: str | None = None) -> None: ...
    @abstractmethod
    async def join_room(self, connection_id: str, room: str) -> None: ...
    @abstractmethod
    async def leave_room(self, connection_id: str, room: str) -> None: ...
    @abstractmethod
    async def disconnect(self, connection_id: str) -> None: ...
```

### `InMemoryAdapter`

Single-worker adapter using in-memory dicts.

```python
class InMemoryAdapter(Adapter):
    def __init__(self): ...
```

### `RedisAdapter`

Multi-worker adapter using Redis pub/sub.

```python
class RedisAdapter(Adapter):
    def __init__(self, redis_url: str = "redis://localhost:6379/0", *,
                 channel_prefix: str = "aquilia:sockets:"): ...
```

---

## Runtime

### `AquilaSockets`

```python
class AquilaSockets:
    """Server-level WebSocket runtime."""
    def __init__(self, *, adapter: Adapter | None = None): ...
    async def handle_connection(self, scope, receive, send): ...
```

### `SocketRouter`

```python
class SocketRouter:
    """Compiled route table for socket controllers."""
    def register(self, controller_cls: type): ...
    def match(self, path: str) -> tuple[type[SocketController], dict[str, str]]: ...
```

---

## Middleware

### `SocketMiddleware`

```python
class SocketMiddleware(ABC):
    @abstractmethod
    async def process(self, connection: Connection, envelope: MessageEnvelope,
                      next_handler: Callable) -> Any: ...
```

### `MessageValidationMiddleware`

```python
class MessageValidationMiddleware(SocketMiddleware):
    async def process(self, connection: Connection, envelope: MessageEnvelope,
                      next_handler: Callable) -> Any: ...
```

### `RateLimitMiddleware` (socket)

```python
class RateLimitMiddleware(SocketMiddleware):
    def __init__(self, max_messages: int = 100, window_seconds: int = 60):
```

---

## Faults

```python
class SocketFault(Fault):                    # domain=SOCKET
WS_HANDSHAKE_FAILED:   SocketFault           # code="WS_HANDSHAKE_FAILED"
WS_AUTH_REQUIRED:      SocketFault           # code="WS_AUTH_REQUIRED"
WS_MESSAGE_INVALID:    SocketFault           # code="WS_MESSAGE_INVALID"
WS_ROOM_FULL:          SocketFault           # code="WS_ROOM_FULL"
WS_RATE_LIMIT_EXCEEDED: SocketFault          # code="WS_RATE_LIMIT_EXCEEDED"
WS_CONNECTION_CLOSED:  SocketFault           # code="WS_CONNECTION_CLOSED"
WS_PAYLOAD_TOO_LARGE:  SocketFault           # code="WS_PAYLOAD_TOO_LARGE"
```

---

## CLI

```bash
aq ws gen-client    # Generate typed WebSocket client stubs
aq ws routes        # List registered WebSocket routes
aq ws stats         # Show connection/message stats
```

---

## Full Example

```python
from aquilia.sockets import (
    SocketController, Socket, OnConnect, OnDisconnect,
    Event, AckEvent, Subscribe, Unsubscribe, Guard,
    Connection, Schema, ConnectionState,
)
from aquilia.sockets.guards import HandshakeAuthGuard, RateLimitGuard

@Socket(
    "/chat/:namespace",
    allowed_origins=["https://app.example.com"],
    max_connections=1000,
    message_rate_limit=50,
    max_message_size=65536,
)
@Guard(HandshakeAuthGuard())
class ChatController(SocketController):
    def __init__(self, presence=Inject(tag="presence"), chat_service=Inject()):
        self.presence = presence
        self.chat_service = chat_service

    @OnConnect()
    async def on_connect(self, conn: Connection):
        identity = conn.identity
        if not identity:
            raise WS_AUTH_REQUIRED("Authentication required")

        await conn.send_event("system.welcome", {
            "msg": f"Welcome, {identity.get_attribute('name')}",
            "channels": await self.chat_service.list_channels(identity.id),
        })
        await self.presence.join(conn.id, identity.id)

    @OnDisconnect()
    async def on_disconnect(self, conn: Connection, reason: str | None):
        await self.presence.leave(conn.id)
        await self.broadcast("presence.offline", {
            "user_id": conn.identity.id if conn.identity else "unknown",
        }, exclude_connection=conn.id)

    @Event("message.send",
           schema=Schema({"room": str, "text": str, "reply_to": (str, None)}))
    async def handle_message(self, conn: Connection, payload):
        message = await self.chat_service.save_message(
            sender=conn.identity.id,
            room=payload["room"],
            text=payload["text"],
        )
        await self.publish_room(
            payload["room"],
            "message.receive",
            {"from": conn.identity.id, "text": payload["text"], "id": message.id},
            exclude_connection=conn.id,
        )

    @AckEvent("message.edit")
    async def handle_edit(self, conn: Connection, payload):
        await self.chat_service.edit_message(
            message_id=payload["id"],
            text=payload["text"],
            user_id=conn.identity.id,
        )
        return {"status": "updated", "id": payload["id"]}

    @Subscribe("room.join")
    async def on_join_room(self, conn: Connection, payload):
        await self.publish_room(payload["room"], "presence.join", {
            "user_id": conn.identity.id,
            "user_name": conn.identity.get_attribute("name"),
        })

    @Unsubscribe("room.leave")
    async def on_leave_room(self, conn: Connection, payload):
        await self.publish_room(payload["room"], "presence.leave", {
            "user_id": conn.identity.id,
        })
```