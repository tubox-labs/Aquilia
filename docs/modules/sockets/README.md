# WebSockets Documentation

This directory is the professional documentation set for `sockets`. It is implementation-driven and aligned with the current source files under `aquilia/sockets`.

## What This Covers

The WebSocket subsystem with socket controllers, connection model, event envelopes, guards, middleware, compiler, runtime dispatcher, rooms, acknowledgements, streams, and adapters.

## Source Files Read

- `aquilia/sockets/__init__.py`: AquilaSockets - WebSocket subsystem for Aquilia
- `aquilia/sockets/adapters/__init__.py`: Adapters Package - WebSocket scaling adapters
- `aquilia/sockets/adapters/base.py`: Adapter Base - Protocol for WebSocket scaling adapters
- `aquilia/sockets/adapters/inmemory.py`: In-Memory Adapter - Single-process WebSocket adapter
- `aquilia/sockets/adapters/redis.py`: Redis Adapter - Production-ready WebSocket adapter using Redis
- `aquilia/sockets/compile.py`: WebSocket Compiler - Compile-time metadata extraction
- `aquilia/sockets/connection.py`: Connection - WebSocket connection abstraction with DI scope
- `aquilia/sockets/controller.py`: Socket Controller - Base class for WebSocket controllers
- `aquilia/sockets/decorators.py`: Socket Controller Decorators - Declarative WebSocket controller syntax
- `aquilia/sockets/envelope.py`: Message Envelope - Typed message protocol for WebSocket communication
- `aquilia/sockets/faults.py`: WebSocket Faults - Structured error handling for WebSocket operations
- `aquilia/sockets/guards.py`: WebSocket Guards - Security and validation guards
- `aquilia/sockets/middleware.py`: WebSocket Middleware - Per-message processing pipeline
- `aquilia/sockets/runtime.py`: WebSocket Runtime - ASGI integration and connection management

## Document Map

- `architecture.md`: Runtime architecture and module boundaries
- `configuration.md`: Configuration entry points, datatypes, and precedence
- `api-reference.md`: Classes, methods, functions, constants, and data fields extracted from source
- `integration-guide.md`: How to wire the module into a real Aquilia application
- `cli-reference.md`: Command line surface and operational commands
- `edge-cases-and-limitations.md`: Known edge cases and implementation limits
- `troubleshooting.md`: Common failures and diagnosis steps
- `examples.md`: Code examples and usage patterns

## Public Surface Snapshot

- Python files: 14
- Public classes: 41
- Configuration or dataclass-like types: 8
- Public functions: 18
- Constants detected: 1

## Fast Start

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

## Read Next

Start with `architecture.md` if you are learning how the subsystem fits into runtime boot. Use `api-reference.md` when you need exact methods, datatypes, and class fields. Use `examples.md` for copyable patterns that match the current code.
