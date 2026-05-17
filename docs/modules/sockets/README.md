# sockets Module

## Purpose

WebSocket controllers, runtime, guards, and adapters. Use this module for socket namespaces, connection lifecycle, event handlers, acknowledgements, rooms, JSON envelopes, middleware, guards, in-memory fanout, and Redis fanout.

## Source Coverage

- Python files: 14
- Public classes: 41
- Dataclasses: 8
- Enums: 2
- Public functions: 18

## How It Fits In Aquilia

1. Decorate a SocketController class with Socket(path).
2. Use OnConnect, OnDisconnect, Event, AckEvent, Subscribe, and Unsubscribe for lifecycle and message handling.
3. Register socket controllers in AppManifest.socket_controllers so AquilaSockets can compile routes.

## Practical Guidance

- WebSocket controllers need an adapter set by runtime for room fanout. Direct controller unit tests can use fake connections.
- Validate event payloads with Schema where message shape matters.

## Public Classes

| Name | Source | Role |
| --- | --- | --- |
| `EventMetadata` | `aquilia/sockets/compile.py` | Compiled event handler metadata. |
| `SocketControllerMetadata` | `aquilia/sockets/compile.py` | Compiled controller metadata. |
| `SocketCompiler` | `aquilia/sockets/compile.py` | Compiler for WebSocket controllers. |
| `ConnectionState` | `aquilia/sockets/connection.py` | Connection lifecycle state. |
| `ConnectionScope` | `aquilia/sockets/connection.py` | Scope metadata for connection. |
| `Connection` | `aquilia/sockets/connection.py` | WebSocket connection with DI scope. |
| `SocketController` | `aquilia/sockets/controller.py` | Base class for WebSocket controllers. |
| `Socket` | `aquilia/sockets/decorators.py` | WebSocket controller decorator. |
| `OnConnect` | `aquilia/sockets/decorators.py` | Handshake handler decorator. |
| `OnDisconnect` | `aquilia/sockets/decorators.py` | Disconnect handler decorator. |
| `Event` | `aquilia/sockets/decorators.py` | Message event handler decorator. |
| `AckEvent` | `aquilia/sockets/decorators.py` | Acknowledgement-enabled event handler. |
| `Subscribe` | `aquilia/sockets/decorators.py` | Room subscription handler. |
| `Unsubscribe` | `aquilia/sockets/decorators.py` | Room unsubscription handler. |
| `Guard` | `aquilia/sockets/decorators.py` | Guard decorator for WebSocket handlers. |
| `MessageType` | `aquilia/sockets/envelope.py` | Message type discriminator. |
| `MessageEnvelope` | `aquilia/sockets/envelope.py` | Standard message envelope for WebSocket communication. |
| `AckEnvelope` | `aquilia/sockets/envelope.py` | Acknowledgement message. |
| `StreamChunk` | `aquilia/sockets/envelope.py` | Typed stream chunk payload for websocket event streaming. |
| `Schema` | `aquilia/sockets/envelope.py` | Simple schema validator for message payloads. |
| `MessageCodec` | `aquilia/sockets/envelope.py` | Protocol for message encoding/decoding. |
| `JSONCodec` | `aquilia/sockets/envelope.py` | JSON message codec. |
| `MsgPackCodec` | `aquilia/sockets/envelope.py` | MessagePack codec for efficient binary encoding. |
| `SocketFault` | `aquilia/sockets/faults.py` | Base fault for WebSocket operations. |
| `SocketGuard` | `aquilia/sockets/guards.py` | Base class for WebSocket guards. |
| `HandshakeAuthGuard` | `aquilia/sockets/guards.py` | Handshake authentication guard. |
| `OriginGuard` | `aquilia/sockets/guards.py` | Origin validation guard. |
| `MessageAuthGuard` | `aquilia/sockets/guards.py` | Per-message authentication guard. |
| `RateLimitGuard` | `aquilia/sockets/guards.py` | Rate limiting guard. |
| `MessageValidationMiddleware` | `aquilia/sockets/middleware.py` | Message validation middleware. |
| `RateLimitMiddleware` | `aquilia/sockets/middleware.py` | Rate limiting middleware. |
| `LoggingMiddleware` | `aquilia/sockets/middleware.py` | Logging middleware. |
| `MetricsMiddleware` | `aquilia/sockets/middleware.py` | Metrics collection middleware. |
| `MiddlewareChain` | `aquilia/sockets/middleware.py` | Middleware chain builder. |
| `RouteMetadata` | `aquilia/sockets/runtime.py` | Socket route metadata extracted from controller. |
| `SocketRouter` | `aquilia/sockets/runtime.py` | Router for WebSocket namespaces. |
| `AquilaSockets` | `aquilia/sockets/runtime.py` | Main WebSocket runtime. |
| `RoomInfo` | `aquilia/sockets/adapters/base.py` | Room metadata. |
| `Adapter` | `aquilia/sockets/adapters/base.py` | Adapter protocol for WebSocket scaling. |
| `InMemoryAdapter` | `aquilia/sockets/adapters/inmemory.py` | In-memory adapter for single-process deployments. |
| `RedisAdapter` | `aquilia/sockets/adapters/redis.py` | Redis-backed adapter for multi-worker deployments. |

## Public Functions

| Name | Source | Role |
| --- | --- | --- |
| `compile_socket_controllers` | `aquilia/sockets/compile.py` | Compile socket controllers to artifacts. |
| `WS_HANDSHAKE_FAILED` | `aquilia/sockets/faults.py` | Public function. |
| `WS_AUTH_REQUIRED` | `aquilia/sockets/faults.py` | Public function. |
| `WS_FORBIDDEN` | `aquilia/sockets/faults.py` | Public function. |
| `WS_ORIGIN_NOT_ALLOWED` | `aquilia/sockets/faults.py` | Public function. |
| `WS_MESSAGE_INVALID` | `aquilia/sockets/faults.py` | Public function. |
| `WS_PAYLOAD_TOO_LARGE` | `aquilia/sockets/faults.py` | Public function. |
| `WS_UNSUPPORTED_EVENT` | `aquilia/sockets/faults.py` | Public function. |
| `WS_CONNECTION_CLOSED` | `aquilia/sockets/faults.py` | Public function. |
| `WS_CONNECTION_TIMEOUT` | `aquilia/sockets/faults.py` | Public function. |
| `WS_RATE_LIMIT_EXCEEDED` | `aquilia/sockets/faults.py` | Public function. |
| `WS_QUOTA_EXCEEDED` | `aquilia/sockets/faults.py` | Public function. |
| `WS_ROOM_NOT_FOUND` | `aquilia/sockets/faults.py` | Public function. |
| `WS_ROOM_FULL` | `aquilia/sockets/faults.py` | Public function. |
| `WS_ALREADY_SUBSCRIBED` | `aquilia/sockets/faults.py` | Public function. |
| `WS_NOT_SUBSCRIBED` | `aquilia/sockets/faults.py` | Public function. |
| `WS_ADAPTER_UNAVAILABLE` | `aquilia/sockets/faults.py` | Public function. |
| `WS_PUBLISH_FAILED` | `aquilia/sockets/faults.py` | Public function. |

## Implementation Map

| File | What To Look For |
| --- | --- |
| `aquilia/sockets/__init__.py` | AquilaSockets - WebSocket subsystem for Aquilia |
| `aquilia/sockets/adapters/__init__.py` | Adapters Package - WebSocket scaling adapters |
| `aquilia/sockets/adapters/base.py` | Adapter Base - Protocol for WebSocket scaling adapters |
| `aquilia/sockets/adapters/inmemory.py` | In-Memory Adapter - Single-process WebSocket adapter |
| `aquilia/sockets/adapters/redis.py` | Redis Adapter - Production-ready WebSocket adapter using Redis |
| `aquilia/sockets/compile.py` | WebSocket Compiler - Compile-time metadata extraction |
| `aquilia/sockets/connection.py` | Connection - WebSocket connection abstraction with DI scope |
| `aquilia/sockets/controller.py` | Socket Controller - Base class for WebSocket controllers |
| `aquilia/sockets/decorators.py` | Socket Controller Decorators - Declarative WebSocket controller syntax |
| `aquilia/sockets/envelope.py` | Message Envelope - Typed message protocol for WebSocket communication |
| `aquilia/sockets/faults.py` | WebSocket Faults - Structured error handling for WebSocket operations |
| `aquilia/sockets/guards.py` | WebSocket Guards - Security and validation guards |
| `aquilia/sockets/middleware.py` | WebSocket Middleware - Per-message processing pipeline |
| `aquilia/sockets/runtime.py` | WebSocket Runtime - ASGI integration and connection management |

## Testing Pointers

Search `tests/` for `sockets` to find behavior-level examples. The test suite is especially useful for edge cases because many modules expose lightweight public APIs but enforce important security and lifecycle behavior internally.
