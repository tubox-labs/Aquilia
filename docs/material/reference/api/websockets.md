# WebSockets

Aquilia provides a full WebSocket subsystem with `SocketController`, declarative decorators, event handling, room management, guards, and DI integration.

## SocketController

```python
class SocketController:
    """
    Base class for WebSocket controllers.

    Controllers handle WebSocket connections with:
    - Constructor DI injection
    - Lifecycle hooks (@OnConnect, @OnDisconnect)
    - Message handlers (@Event, @AckEvent)
    - Room subscription handlers (@Subscribe, @Unsubscribe)
    - Guards (@Guard)
    """

    namespace: str | None = None
    adapter: Adapter | None = None

    def __init__(self):
        """Override in subclasses for DI injection."""
```

### Class-Level Configuration

| Attribute | Type | Default | Description |
|---|---|---|---|
| `namespace` | `str \| None` | `None` | WebSocket namespace |
| `adapter` | `Adapter \| None` | `None` | Adapter for cross-worker fanout |

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
    """
    Publish message to all connections in a room.

    Args:
        room: Room identifier
        event: Event name
        payload: Event data
        namespace: Optional namespace override
        exclude_connection: Optional connection ID to exclude
    """

async def broadcast(
    self,
    event: str,
    payload: dict[str, Any],
    *,
    namespace: str | None = None,
    exclude_connection: str | None = None,
):
    """
    Broadcast message to all connections in namespace.

    Args:
        event: Event name
        payload: Event data
        namespace: Optional namespace override
        exclude_connection: Optional connection ID to exclude
    """
```

### Lifecycle Hooks (base)

```python
async def on_connect(self, conn: Connection):
    """Called when connection is established. Override with @OnConnect()."""

async def on_disconnect(self, conn: Connection, reason: str | None = None):
    """Called when connection is closed. Override with @OnDisconnect()."""

def get_room_members(self, room: str, namespace: str | None = None) -> set[str]:
    """Get connection IDs in a room."""
```

---

## Decorators

### `@Socket` — Class Decorator

```python
class Socket:
    """WebSocket controller decorator. Declares a namespace and path pattern."""

    def __init__(
        self,
        path: str,
        *,
        allowed_origins: list[str] | None = None,
        max_connections: int | None = None,
        message_rate_limit: int | None = None,  # messages per second
        max_message_size: int = 65536,  # 64KB default
        compression: bool = True,
        subprotocols: list[str] | None = None,
    ):
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `path` | `str` | (required) | URL path pattern (supports Aquilia patterns like `/:id`) |
| `allowed_origins` | `list[str] \| None` | `None` | Whitelist of allowed origins |
| `max_connections` | `int \| None` | `None` | Max concurrent connections per namespace |
| `message_rate_limit` | `int \| None` | `None` | Max messages per second per connection |
| `max_message_size` | `int` | `65536` | Max message size in bytes |
| `compression` | `bool` | `True` | Enable WebSocket compression |
| `subprotocols` | `list[str] \| None` | `None` | Supported WebSocket subprotocols |

**Attaches:** `cls.__socket_metadata__` dict with all configuration.

### `@OnConnect` — Connection Handler

```python
class OnConnect:
    """
    Handshake handler decorator.

    Called when connection is established (after auth).
    Can accept or reject connection by raising Fault.
    """

    def __call__(self, func: F) -> F:
        func.__socket_handler__ = {"type": "on_connect"}
```

**Attaches:** `func.__socket_handler__ = {"type": "on_connect"}`

### `@OnDisconnect` — Disconnection Handler

```python
class OnDisconnect:
    """
    Disconnect handler decorator.

    Called when connection is closed.
    """

    def __call__(self, func: F) -> F:
        func.__socket_handler__ = {"type": "on_disconnect"}
```

**Attaches:** `func.__socket_handler__ = {"type": "on_disconnect"}`

### `@Event` — Message Handler

```python
class Event:
    """Message event handler decorator. Binds incoming event type to handler method."""

    def __init__(
        self,
        event: str,
        *,
        schema: Schema | None = None,
        ack: bool = False,
    ):
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `event` | `str` | (required) | Event name to handle |
| `schema` | `Schema \| None` | `None` | Optional payload schema for validation |
| `ack` | `bool` | `False` | Automatically send ack on success |

**Attaches:** `func.__socket_handler__ = {"type": "event", "event": <event>, "schema": <schema>, "ack": <ack>}`

### `@AckEvent` — Acknowledgement Handler

```python
class AckEvent:
    """
    Acknowledgement-enabled event handler.

    Automatically sends ack on completion. The handler's return value
    is sent as the ack payload.
    """

    def __init__(self, event: str, *, schema: Schema | None = None):
```

**Attaches:** `func.__socket_handler__ = {"type": "event", "event": <event>, "schema": <schema>, "ack": True}`

### `@Subscribe` — Room Join Handler

```python
class Subscribe:
    """Room subscription handler. Sugar for joining rooms."""

    def __init__(self, event: str, *, schema: Schema | None = None):
```

**Attaches:** `func.__socket_handler__ = {"type": "subscribe", "event": <event>, "schema": <schema>}`

### `@Unsubscribe` — Room Leave Handler

```python
class Unsubscribe:
    """Room unsubscription handler. Sugar for leaving rooms."""

    def __init__(self, event: str, *, schema: Schema | None = None):
```

**Attaches:** `func.__socket_handler__ = {"type": "unsubscribe", "event": <event>, "schema": <schema>}`

### `@Guard` — Security Guard

```python
class Guard:
    """
    Guard decorator for WebSocket handlers.

    Can be applied at class level or method level.
    """

    def __init__(self, *, priority: int = 50):
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `priority` | `int` | `50` | Execution priority (lower = earlier) |

**Attaches:** `func.__socket_handler__ = {"type": "guard", "priority": <priority>}`

---

## Complete Example

```python
from aquilia.sockets import (
    SocketController, Socket, OnConnect, OnDisconnect,
    Event, AckEvent, Subscribe, Unsubscribe, Guard,
    Connection, Schema,
)
from aquilia.di import Inject

@Socket("/chat/:namespace", max_connections=1000, message_rate_limit=10)
class ChatSocket(SocketController):

    def __init__(self, presence=Inject(tag="presence")):
        self.presence = presence

    @Guard()
    async def auth_guard(self, conn: Connection):
        if not conn.identity:
            raise WS_AUTH_REQUIRED()

    @OnConnect()
    async def handle_connect(self, conn: Connection):
        await self.presence.join(conn.identity.id)
        await conn.send_event("system.welcome", {
            "msg": f"Welcome {conn.identity.id}"
        })

    @OnDisconnect()
    async def handle_disconnect(self, conn: Connection, reason: str | None = None):
        await self.presence.leave(conn.identity.id)

    @Event("message.send", schema=Schema({"room": str, "text": str}))
    async def handle_message(self, conn: Connection, payload):
        room = payload["room"]
        await self.publish_room(room, "message.receive", {
            "from": conn.identity.id,
            "text": payload["text"]
        })

    @AckEvent("data.request", schema=Schema({"id": str}))
    async def handle_data_request(self, conn: Connection, payload):
        data = await self.fetch_data(payload["id"])
        return {"data": data}  # Sent as ack payload

    @Subscribe("room.join")
    async def join_room(self, conn: Connection, payload):
        room = payload["room"]
        await conn.join(room)
        await conn.send_event("room.joined", {"room": room})

    @Unsubscribe("room.leave")
    async def leave_room(self, conn: Connection, payload):
        room = payload["room"]
        await conn.leave(room)
        await conn.send_event("room.left", {"room": room})
```

---

## Connection Lifecycle

1. **Connection attempt** — `ASGIAdapter.handle_websocket()` delegates to `socket_runtime`
2. **Handshake** — Origin validation, subprotocol negotiation, auth guards
3. **`@OnConnect()`** — Handler is called after successful authentication
4. **Message loop** — `@Event()`, `@AckEvent()`, `@Subscribe()`, `@Unsubscribe()` handlers fire based on incoming message type
5. **`@OnDisconnect()`** — Handler is called when the connection is closed (client disconnect, error, or server close)

## Guards

Guards execute before the actual handler and can short-circuit:
- Applied at **class level** (runs before any handler)
- Applied at **method level** (runs before that specific handler)
- Guards raise `Fault` subclasses to reject
- Ordered by `priority` (lower = earlier)

## Message Envelope

Internally, messages use `MessageEnvelope` from `aquilia.sockets.envelope`:

```python
class MessageType(str, Enum):
    EVENT = "event"
    ACK = "ack"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    SYSTEM = "system"

class MessageEnvelope:
    type: MessageType
    event: str
    payload: dict[str, Any]
    ack_id: str | None  # For acknowledgement correlation
```

## Adapters

Adapters enable cross-worker message fanout. The `SocketController.adapter` attribute controls the adapter (in-memory, Redis, etc.). The adapter interface:

```python
class Adapter:
    async def publish(self, namespace: str, room: str, envelope: MessageEnvelope,
                      exclude_connection: str | None = None): ...

    async def broadcast(self, namespace: str, envelope: MessageEnvelope,
                        exclude_connection: str | None = None): ...
```