---
name: aquilia-websocket-builder
description: "Build Aquilia WebSocket and realtime features. Use for SocketController, @Socket, OnConnect/OnDisconnect/Event/AckEvent/Subscribe/Unsubscribe/Guard decorators, adapters, envelopes, middleware, client generation, and aq ws commands."
---

# Aquilia Websocket Builder

## Purpose
Implement realtime channels with Aquilia socket controllers and runtime adapters.

## Trigger Conditions
Use for WebSocket endpoints, rooms, events, acknowledgements, subscriptions, presence, Redis/in-memory adapters, message validation, rate limits, and `aq ws` commands.

## Inputs
- Socket path, namespace, allowed origins, message limits, event names, schemas, rooms, and adapter choice.
- Whether generated TypeScript client output is needed.

## Execution Flow
1. Create a class decorated with `@Socket("/ws/path/:param", ...)` that subclasses `SocketController`.
2. Implement lifecycle methods with `@OnConnect()` and `@OnDisconnect()`.
3. Implement events with `@Event`, `@AckEvent`, `@Subscribe`, and `@Unsubscribe`; validate payloads with `Schema`.
4. Register the socket controller in `AppManifest.socket_controllers` or rely on socket auto-discovery.
5. Use `aq ws inspect`, `broadcast`, `gen-client`, `purge-room`, and `kick` for operational workflows.

## Constraints
- Do not invent a Socket.IO protocol; use Aquilia envelopes/runtime classes.
- Respect `allowed_origins`, `message_rate_limit`, and `max_message_size`.
- Redis adapter requires redis optional dependency and URL configuration.

## Implementation Anchors
`aquilia/sockets/decorators.py`, `aquilia/sockets/runtime.py`, `aquilia/sockets/connection.py`, `aquilia/sockets/envelope.py`, `aquilia/sockets/adapters/`, `aquilia/cli/commands/ws.py`, `examples/websocket_app/modules/chat/sockets.py`.

## Examples
- Create `@Socket("/ws/chat/:room", allowed_origins=["*"], message_rate_limit=20)`.
- Add `@Event("message.send", schema=Schema({"room": str, "text": str}), ack=True)`.
- Generate a TypeScript client with `aq ws gen-client --out client.ts`.

## Failure Handling
Handshake/auth/origin failures should map to socket faults. Invalid payloads should fail schema validation. If events do not register, inspect `socket_controllers` and `SocketCompiler` metadata.
