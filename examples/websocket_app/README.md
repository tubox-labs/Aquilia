# WebSocket App Starter

## Purpose

Chat-style WebSocket app with room membership, connect/disconnect hooks, subscriptions, acknowledgements, and HTTP presence inspection.

## Architecture

- `workspace.py` registers the `chat` module at `/chat`.
- `manifest.py` declares both `ChatController` and `ChatSocket`.
- `sockets.py` uses `@Socket`, `@OnConnect`, `@OnDisconnect`, `@Subscribe`, `@Unsubscribe`, `@Event`, and `@AckEvent`.
- `ChatPresenceService` tracks room membership in memory.

## Run

```bash
cd examples/websocket_app
python -m uvicorn runtime:app --reload --port 8030
```

Expected behavior: `GET /chat/rooms` reports room membership, and socket clients can connect to `/ws/chat/:room`.

## Test

```bash
python -m pytest examples/websocket_app -q
```

## Common Pitfalls

- In-memory presence is per process. Use the Redis adapter for multi-worker fanout.
- Message schemas are enforced by `Schema` on subscribed events.
- Socket controllers must be declared in `socket_controllers` in the manifest.

## Extension Ideas

Generate a TypeScript client with `aq ws gen-client`, add auth guards, add Redis adapter config, and publish job/order events into rooms.

## Related APIs

`SocketController`, `Socket`, `Connection`, `Schema`, `Event`, `AckEvent`, `Subscribe`, `Unsubscribe`, `OnConnect`, `OnDisconnect`, `SocketRouter`.
