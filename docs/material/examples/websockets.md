# WebSockets

The WebSocket example demonstrates a chat-style realtime application with room
membership, connect/disconnect lifecycle hooks, typed subscriptions, acknowledgements,
and presence tracking.

---

## What It Demonstrates

- `SocketController` with `@Socket` decorator for URL binding
- `@OnConnect` and `@OnDisconnect` lifecycle hooks
- `@Subscribe` and `@Unsubscribe` for typed event subscriptions with `Schema` validation
- `@Event` with `ack=True` for acknowledged messages
- `@AckEvent` for request/response-style socket communication
- Room management: `conn.join()`, `conn.leave()`, `publish_room()`
- In-memory presence service tracking room membership
- HTTP controller for inspecting active rooms

## Key Files

| File | Purpose |
| ---- | ------- |
| `workspace.py` | Registers the `chat` module at `/chat` with DI and routing |
| `modules/chat/manifest.py` | Declares both `ChatController` and `ChatSocket` |
| `modules/chat/controllers.py` | HTTP endpoint exposing room membership |
| `modules/chat/sockets.py` | `ChatSocket` — all WebSocket event handlers |
| `modules/chat/services.py` | `ChatPresenceService` — in-memory room/connection tracking |

## ChatSocket Controller

```python
@Socket("/ws/chat/:room", allowed_origins=["*"], message_rate_limit=20, max_message_size=16384)
class ChatSocket(SocketController):
    namespace = "chat"

    def __init__(self, presence: ChatPresenceService | None = None):
        self.presence = presence or ChatPresenceService()

    @OnConnect()
    async def connected(self, conn: Connection):
        room = conn.scope.path_params.get("room", "lobby")
        await conn.join(room)
        await self.presence.join(room, conn.id)
        await conn.send_event("system.welcome", {"room": room, "connection_id": conn.id})

    @OnDisconnect()
    async def disconnected(self, conn: Connection, reason: str | None = None):
        for room in conn.rooms:
            await self.presence.leave(room, conn.id)

    @Subscribe("room.join", schema=Schema({"room": str}))
    async def join_room(self, conn: Connection, payload: dict):
        room = payload["room"]
        await conn.join(room)
        state = await self.presence.join(room, conn.id)
        await conn.send_event("room.joined", state)

    @Unsubscribe("room.leave", schema=Schema({"room": str}))
    async def leave_room(self, conn: Connection, payload: dict):
        room = payload["room"]
        await conn.leave(room)
        state = await self.presence.leave(room, conn.id)
        await conn.send_event("room.left", state)

    @Event("message.send", schema=Schema({"room": str, "text": str}), ack=True)
    async def send_message(self, conn: Connection, payload: dict):
        await self.publish_room(
            payload["room"],
            "message.received",
            {"from": conn.id, "text": payload["text"]},
        )
        return {"delivered": True, "room": payload["room"]}

    @AckEvent("presence.snapshot")
    async def presence_snapshot(self, conn: Connection, payload: dict):
        return await self.presence.snapshot()
```

## Key Concepts

### Socket URL Patterns

The `@Socket` decorator uses colon-prefixed path parameters:

```
/ws/chat/:room          → conn.scope.path_params["room"]
/ws/orders/:tenant/:id  → conn.scope.path_params["tenant"], conn.scope.path_params["id"]
```

### Event Types

| Decorator | Purpose | Response |
| --------- | ------- | -------- |
| `@Subscribe(name)` | Client subscribes to an event stream | No direct response; server emits events to the connection |
| `@Unsubscribe(name)` | Client unsubscribes from a stream | No direct response |
| `@Event(name, ack=True)` | Client sends a message requiring acknowledgement | Returns a dict sent back as acknowledgement |
| `@AckEvent(name)` | Client sends a request expecting a response | Returns the response directly |

### Schema Validation

The `Schema` class provides runtime type enforcement for event payloads:

```python
@Subscribe("room.join", schema=Schema({"room": str}))
async def join_room(self, conn, payload):
    # payload is guaranteed to have {"room": str}
    room = payload["room"]
```

### Publishing to Rooms

Use `publish_room()` to broadcast messages to all connections in a room:

```python
await self.publish_room(
    room_name,
    "event.name",
    {"key": "value"},
    exclude_connection=conn.id,  # Optional: skip the sender
)
```

## Manifest Declaration

Socket controllers must be declared in `AppManifest.socket_controllers`:

```python
from aquilia import AppManifest

manifest = AppManifest(
    name="chat",
    version="1.0.0",
    controllers=["modules.chat.controllers:ChatController"],
    socket_controllers=["modules.chat.sockets:ChatSocket"],
    services=["modules.chat.services:ChatPresenceService"],
)
```

## Running

```bash
cd examples/websocket_app
python -m uvicorn runtime:app --reload --port 8030
```

Connect a WebSocket client:

```bash
# Using wscat or a browser WebSocket
wscat -c ws://127.0.0.1:8030/ws/chat/lobby

# Subscribe to a room
{"event": "room.join", "data": {"room": "tech-talks"}}

# Send a message
{"event": "message.send", "data": {"room": "tech-talks", "text": "Hello!"}, "ack": true}

# Get presence snapshot
{"event": "presence.snapshot"}

# Check HTTP room info
curl http://127.0.0.1:8030/chat/rooms

# Run tests
python -m pytest examples/websocket_app -q
```

## What You'll Learn

- How to define WebSocket endpoints with `@Socket` URL patterns
- How to manage connection lifecycle with `@OnConnect` and `@OnDisconnect`
- How to use typed subscriptions and events with `Schema` validation
- How to implement room-based messaging with `publish_room()`
- How to track presence state across connections
- How to declare socket controllers in `AppManifest`