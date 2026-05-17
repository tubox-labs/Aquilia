# WebSockets Examples

## Primary Usage

```python
from aquilia.sockets import Connection, Event, OnConnect, Socket, SocketController

@Socket("/ws/chat/:room", allowed_origins=["*"], message_rate_limit=20)
class ChatSocket(SocketController):
    @OnConnect()
    async def connected(self, conn: Connection):
        room = conn.scope.path_params.get("room", "lobby")
        await conn.join(room)
        await conn.send_event("welcome", {"room": room})

    @Event("message.send", ack=True)
    async def message(self, conn: Connection, payload: dict):
        await self.publish_room(payload["room"], "message.received", payload)
        return {"published": True}
```

## Manifest Registration Pattern

```python
from aquilia import AppManifest

manifest = AppManifest(
    name="example",
    version="1.0.0",
    controllers=["modules.example.controllers:ExampleController"],
    services=["modules.example.services:ExampleService"],
    base_path="modules.example",
)
```

## Workspace Pattern

```python
from aquilia import Module, Workspace

workspace = (
    Workspace("myapp")
    .module(Module("example").route_prefix("/example"))
)
```

## Public API Imports

```python
from aquilia.sockets import RoomInfo, Adapter, InMemoryAdapter, RedisAdapter, EventMetadata, SocketControllerMetadata
```

## Test Pattern

```python
import pytest

@pytest.mark.asyncio
async def test_subsystem_contract():
    # Construct the service, provider, controller helper, or datatype directly.
    # Use the exact constructor and methods from api-reference.md.
    assert True
```
