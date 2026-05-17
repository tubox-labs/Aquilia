# Sockets Examples

WebSocket decorators, controllers, runtime, connection state, guards, middleware, message envelopes, compile metadata, and in-memory/Redis adapters.

Examples here use public symbols and checked patterns from the repository. When a module has no safe standalone constructor example, the example focuses on importing and wiring the actual source-backed API.

## Source-Backed Import Examples

```python
from aquilia.sockets.adapters.base import RoomInfo
from aquilia.sockets.adapters.base import Adapter
from aquilia.sockets.adapters.inmemory import InMemoryAdapter
from aquilia.sockets.adapters.redis import RedisAdapter
from aquilia.sockets.compile import EventMetadata
from aquilia.sockets.compile import SocketControllerMetadata
```

## Workspace/Manifest Wiring Example

```python
from aquilia import AppManifest, Integration, Module, Workspace

workspace = (
    Workspace("example", version="1.0.0")
    .runtime(mode="dev", port=8000)
    .module(Module("example").route_prefix("/example"))
    .integrate(Integration.di(auto_wire=True))
)

manifest = AppManifest(
    name="example",
    version="1.0.0",
    controllers=["modules.example.controllers:ExampleController"],
    services=["modules.example.services:ExampleService"],
)
```

## WebSocket Pattern From Checked Examples

```python
from aquilia.sockets import Connection, Event, OnConnect, Schema, Socket, SocketController

@Socket("/ws/chat/:room", allowed_origins=["*"], message_rate_limit=20)
class ChatSocket(SocketController):
    @OnConnect()
    async def connected(self, conn: Connection):
        await conn.join(conn.scope.path_params.get("room", "lobby"))

    @Event("message.send", schema=Schema({"room": str, "text": str}), ack=True)
    async def send_message(self, conn: Connection, payload: dict):
        await self.publish_room(payload["room"], "message.received", payload)
        return {"delivered": True}
```

## Verification

- Run `python -m aquilia.cli.__main__ --help` to confirm CLI availability.
- Run `aq validate` in a workspace to validate manifest paths.
- Run related tests under `tests/` or `examples/*/tests/` for executable behavior.
