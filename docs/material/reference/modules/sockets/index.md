# Sockets Module

> `aquilia.sockets` — WebSocket support with controllers and pub/sub

The Sockets module provides first-class WebSocket support with `SocketController`, decorators for connection lifecycle events, room-based pub/sub with acknowledgements, and an in-memory adapter.

## When to Use

Use the Sockets module when you need:

- Real-time bidirectional communication
- Room-based broadcasting (pub/sub)
- WebSocket authentication and guards
- Connection lifecycle management
- Client message acknowledgments

## Key Classes

| Class | Purpose |
|---|---|
| `SocketController` | Base class for WebSocket controllers |
| `AquilaSockets` | WebSocket runtime manager |
| `SocketRouter` | Routes WebSocket connections to controllers |
| `SocketGuard` | Per-connection authorization guard |
| `InMemoryAdapter` | In-memory pub/sub adapter |

## Decorators

| Decorator | Purpose |
|---|---|
| `@Socket("/path")` | Register a WebSocket handler |
| `@OnConnect` | Handle new connections |
| `@OnDisconnect` | Handle disconnections |
| `@Event("name")` | Handle named events from clients |
| `@AckEvent("name")` | Handle events with acknowledgment |
| `@Subscribe("room")` | Subscribe to a room |
| `@Unsubscribe("room")` | Unsubscribe from a room |
| `@Guard` | Apply authorization guard |

## Quick Example

```python
from aquilia.sockets import SocketController, OnConnect, OnDisconnect, Event, Socket

class ChatController(SocketController):
    prefix = "/ws/chat"

    @OnConnect
    async def on_connect(self, ctx):
        ctx.join("lobby")
        await ctx.emit("welcome", {"message": "Connected!"})

    @Event("message")
    async def on_message(self, ctx, data):
        # Broadcast to room
        await ctx.emit("broadcast", data, room="lobby")

    @OnDisconnect
    async def on_disconnect(self, ctx):
        ctx.leave("lobby")
```

## Client Generation

```bash
# Generate typed WebSocket client
aq ws generate
```

## Import Path

```python
from aquilia.sockets import (
    SocketController,
    Socket,
    OnConnect,
    OnDisconnect,
    Event,
    AquilaSockets,
    SocketRouter,
    SocketGuard,
)
```

## Related Modules

- [sse](../sse/index.md) — Server-Sent Events for unidirectional streaming
- [core/asgi](../core/asgi.md) — WebSocket protocol handling in ASGI adapter
- [cli](../cli/index.md) — `aq ws` commands