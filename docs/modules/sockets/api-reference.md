# Sockets API Reference

This page is generated from the current Python source using the AST. It lists public classes, public methods, public module-level functions, constants, exports, and source files.

## Source Inventory

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/sockets/__init__.py` | 131 | 0 | 0 | AquilaSockets - WebSocket subsystem for Aquilia |
| `aquilia/sockets/adapters/__init__.py` | 14 | 0 | 0 | Adapters Package - WebSocket scaling adapters |
| `aquilia/sockets/adapters/base.py` | 203 | 2 | 0 | Adapter Base - Protocol for WebSocket scaling adapters |
| `aquilia/sockets/adapters/inmemory.py` | 227 | 1 | 0 | In-Memory Adapter - Single-process WebSocket adapter |
| `aquilia/sockets/adapters/redis.py` | 338 | 1 | 0 | Redis Adapter - Production-ready WebSocket adapter using Redis |
| `aquilia/sockets/compile.py` | 280 | 3 | 1 | WebSocket Compiler - Compile-time metadata extraction |
| `aquilia/sockets/connection.py` | 344 | 3 | 0 | Connection - WebSocket connection abstraction with DI scope |
| `aquilia/sockets/controller.py` | 211 | 1 | 0 | Socket Controller - Base class for WebSocket controllers |
| `aquilia/sockets/decorators.py` | 303 | 8 | 0 | Socket Controller Decorators - Declarative WebSocket controller syntax |
| `aquilia/sockets/envelope.py` | 274 | 8 | 0 | Message Envelope - Typed message protocol for WebSocket communication |
| `aquilia/sockets/faults.py` | 200 | 1 | 17 | WebSocket Faults - Structured error handling for WebSocket operations |
| `aquilia/sockets/guards.py` | 272 | 5 | 0 | WebSocket Guards - Security and validation guards |
| `aquilia/sockets/middleware.py` | 234 | 5 | 0 | WebSocket Middleware - Per-message processing pipeline |
| `aquilia/sockets/runtime.py` | 656 | 3 | 0 | WebSocket Runtime - ASGI integration and connection management |

## Public Exports

`AckEvent`, `Adapter`, `AquilaSockets`, `Connection`, `ConnectionScope`, `ConnectionState`, `Event`, `Guard`, `HandshakeAuthGuard`, `InMemoryAdapter`, `JSONCodec`, `MessageAuthGuard`, `MessageCodec`, `MessageEnvelope`, `MessageType`, `MessageValidationMiddleware`, `OnConnect`, `OnDisconnect`, `OriginGuard`, `RateLimitGuard`, `RateLimitMiddleware`, `RedisAdapter`, `RoomInfo`, `Schema`, `Socket`, `SocketController`, `SocketFault`, `SocketGuard`, `SocketMiddleware`, `SocketRouter`, `StreamChunk`, `Subscribe`, `Unsubscribe`, `WS_AUTH_REQUIRED`, `WS_CONNECTION_CLOSED`, `WS_HANDSHAKE_FAILED`, `WS_MESSAGE_INVALID`, `WS_PAYLOAD_TOO_LARGE`, `WS_RATE_LIMIT_EXCEEDED`, `WS_ROOM_FULL`

## Public Class Summary

| Class | Source | Bases | Summary |
| --- | --- | --- | --- |
| `RoomInfo` | `aquilia/sockets/adapters/base.py` | object | Room metadata. |
| `Adapter` | `aquilia/sockets/adapters/base.py` | Protocol | Adapter protocol for WebSocket scaling. |
| `InMemoryAdapter` | `aquilia/sockets/adapters/inmemory.py` | Adapter | In-memory adapter for single-process deployments. |
| `RedisAdapter` | `aquilia/sockets/adapters/redis.py` | Adapter | Redis-backed adapter for multi-worker deployments. |
| `EventMetadata` | `aquilia/sockets/compile.py` | object | Compiled event handler metadata. |
| `SocketControllerMetadata` | `aquilia/sockets/compile.py` | object | Compiled controller metadata. |
| `SocketCompiler` | `aquilia/sockets/compile.py` | object | Compiler for WebSocket controllers. |
| `ConnectionState` | `aquilia/sockets/connection.py` | str, Enum | Connection lifecycle state. |
| `ConnectionScope` | `aquilia/sockets/connection.py` | object | Scope metadata for connection. |
| `Connection` | `aquilia/sockets/connection.py` | object | WebSocket connection with DI scope. |
| `SocketController` | `aquilia/sockets/controller.py` | object | Base class for WebSocket controllers. |
| `Socket` | `aquilia/sockets/decorators.py` | object | WebSocket controller decorator. |
| `OnConnect` | `aquilia/sockets/decorators.py` | object | Handshake handler decorator. |
| `OnDisconnect` | `aquilia/sockets/decorators.py` | object | Disconnect handler decorator. |
| `Event` | `aquilia/sockets/decorators.py` | object | Message event handler decorator. |
| `AckEvent` | `aquilia/sockets/decorators.py` | object | Acknowledgement-enabled event handler. |
| `Subscribe` | `aquilia/sockets/decorators.py` | object | Room subscription handler. |
| `Unsubscribe` | `aquilia/sockets/decorators.py` | object | Room unsubscription handler. |
| `Guard` | `aquilia/sockets/decorators.py` | object | Guard decorator for WebSocket handlers. |
| `MessageType` | `aquilia/sockets/envelope.py` | str, Enum | Message type discriminator. |
| `MessageEnvelope` | `aquilia/sockets/envelope.py` | object | Standard message envelope for WebSocket communication. |
| `AckEnvelope` | `aquilia/sockets/envelope.py` | object | Acknowledgement message. |
| `StreamChunk` | `aquilia/sockets/envelope.py` | object | Typed stream chunk payload for websocket event streaming. |
| `Schema` | `aquilia/sockets/envelope.py` | object | Simple schema validator for message payloads. |
| `MessageCodec` | `aquilia/sockets/envelope.py` | Protocol | Protocol for message encoding/decoding. |
| `JSONCodec` | `aquilia/sockets/envelope.py` | object | JSON message codec. |
| `MsgPackCodec` | `aquilia/sockets/envelope.py` | object | MessagePack codec for efficient binary encoding. |
| `SocketFault` | `aquilia/sockets/faults.py` | Fault | Base fault for WebSocket operations. |
| `SocketGuard` | `aquilia/sockets/guards.py` | object | Base class for WebSocket guards. |
| `HandshakeAuthGuard` | `aquilia/sockets/guards.py` | SocketGuard | Handshake authentication guard. |
| `OriginGuard` | `aquilia/sockets/guards.py` | SocketGuard | Origin validation guard. |
| `MessageAuthGuard` | `aquilia/sockets/guards.py` | SocketGuard | Per-message authentication guard. |
| `RateLimitGuard` | `aquilia/sockets/guards.py` | SocketGuard | Rate limiting guard. |
| `MessageValidationMiddleware` | `aquilia/sockets/middleware.py` | object | Message validation middleware. |
| `RateLimitMiddleware` | `aquilia/sockets/middleware.py` | object | Rate limiting middleware. |
| `LoggingMiddleware` | `aquilia/sockets/middleware.py` | object | Logging middleware. |
| `MetricsMiddleware` | `aquilia/sockets/middleware.py` | object | Metrics collection middleware. |
| `MiddlewareChain` | `aquilia/sockets/middleware.py` | object | Middleware chain builder. |
| `RouteMetadata` | `aquilia/sockets/runtime.py` | object | Socket route metadata extracted from controller. |
| `SocketRouter` | `aquilia/sockets/runtime.py` | object | Router for WebSocket namespaces. |
| `AquilaSockets` | `aquilia/sockets/runtime.py` | object | Main WebSocket runtime. |

## Public Function Summary

| Function | Source | Signature | Summary |
| --- | --- | --- | --- |
| `compile_socket_controllers` | `aquilia/sockets/compile.py` | `def compile_socket_controllers(controller_classes: list[type[SocketController]], output_dir: Path)` | Compile socket controllers to artifacts. |
| `WS_HANDSHAKE_FAILED` | `aquilia/sockets/faults.py` | `def WS_HANDSHAKE_FAILED(reason='')` |  |
| `WS_AUTH_REQUIRED` | `aquilia/sockets/faults.py` | `def WS_AUTH_REQUIRED()` |  |
| `WS_FORBIDDEN` | `aquilia/sockets/faults.py` | `def WS_FORBIDDEN(reason='')` |  |
| `WS_ORIGIN_NOT_ALLOWED` | `aquilia/sockets/faults.py` | `def WS_ORIGIN_NOT_ALLOWED(origin='')` |  |
| `WS_MESSAGE_INVALID` | `aquilia/sockets/faults.py` | `def WS_MESSAGE_INVALID(reason='')` |  |
| `WS_PAYLOAD_TOO_LARGE` | `aquilia/sockets/faults.py` | `def WS_PAYLOAD_TOO_LARGE(size=0, limit=0)` |  |
| `WS_UNSUPPORTED_EVENT` | `aquilia/sockets/faults.py` | `def WS_UNSUPPORTED_EVENT(event='')` |  |
| `WS_CONNECTION_CLOSED` | `aquilia/sockets/faults.py` | `def WS_CONNECTION_CLOSED(reason='')` |  |
| `WS_CONNECTION_TIMEOUT` | `aquilia/sockets/faults.py` | `def WS_CONNECTION_TIMEOUT()` |  |
| `WS_RATE_LIMIT_EXCEEDED` | `aquilia/sockets/faults.py` | `def WS_RATE_LIMIT_EXCEEDED(limit=0)` |  |
| `WS_QUOTA_EXCEEDED` | `aquilia/sockets/faults.py` | `def WS_QUOTA_EXCEEDED(quota='')` |  |
| `WS_ROOM_NOT_FOUND` | `aquilia/sockets/faults.py` | `def WS_ROOM_NOT_FOUND(room='')` |  |
| `WS_ROOM_FULL` | `aquilia/sockets/faults.py` | `def WS_ROOM_FULL(room='', capacity=0)` |  |
| `WS_ALREADY_SUBSCRIBED` | `aquilia/sockets/faults.py` | `def WS_ALREADY_SUBSCRIBED(room='')` |  |
| `WS_NOT_SUBSCRIBED` | `aquilia/sockets/faults.py` | `def WS_NOT_SUBSCRIBED(room='')` |  |
| `WS_ADAPTER_UNAVAILABLE` | `aquilia/sockets/faults.py` | `def WS_ADAPTER_UNAVAILABLE(adapter='')` |  |
| `WS_PUBLISH_FAILED` | `aquilia/sockets/faults.py` | `def WS_PUBLISH_FAILED(reason='')` |  |

## Constants And Module Flags

| Name | Source | Value or Type |
| --- | --- | --- |
| `F` | `aquilia/sockets/decorators.py` | `TypeVar('F', bound=Callable[..., Any])` |

## Detailed Classes And Methods

### `RoomInfo`

- Source: `aquilia/sockets/adapters/base.py`
- Bases: `object`
- Summary: Room metadata.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `namespace` | `str` | `` |
| `room` | `str` | `` |
| `member_count` | `int` | `` |
| `members` | `set[str]` | `` |

### `Adapter`

- Source: `aquilia/sockets/adapters/base.py`
- Bases: `Protocol`
- Summary: Adapter protocol for WebSocket scaling.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `initialize` | `async def initialize(self)` | Initialize adapter (connect to backend). |
| `shutdown` | `async def shutdown(self)` | Shutdown adapter (close connections). |
| `publish` | `async def publish(self, namespace: str, room: str, envelope: MessageEnvelope, exclude_connection: str \| None=None)` | Publish message to room. |
| `broadcast` | `async def broadcast(self, namespace: str, envelope: MessageEnvelope, exclude_connection: str \| None=None)` | Broadcast message to all connections in namespace. |
| `join_room` | `async def join_room(self, namespace: str, room: str, connection_id: str)` | Register connection as room member. |
| `leave_room` | `async def leave_room(self, namespace: str, room: str, connection_id: str)` | Unregister connection from room. |
| `get_room_members` | `async def get_room_members(self, namespace: str, room: str)` | Get connection IDs in room. |
| `get_room_info` | `async def get_room_info(self, namespace: str, room: str)` | Get room metadata. |
| `list_rooms` | `async def list_rooms(self, namespace: str)` | List all rooms in namespace. |
| `register_connection` | `async def register_connection(self, namespace: str, connection_id: str, worker_id: str)` | Register active connection. |
| `unregister_connection` | `async def unregister_connection(self, namespace: str, connection_id: str)` | Unregister connection. |
| `get_connection_count` | `async def get_connection_count(self, namespace: str)` | Get active connection count. |

### `InMemoryAdapter`

- Source: `aquilia/sockets/adapters/inmemory.py`
- Bases: `Adapter`
- Summary: In-memory adapter for single-process deployments.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `initialize` | `async def initialize(self)` | Initialize adapter. |
| `shutdown` | `async def shutdown(self)` | Shutdown adapter. |
| `register_send_callback` | `def register_send_callback(self, namespace: str, connection_id: str, callback: callable)` | Register send callback for connection. |
| `unregister_send_callback` | `def unregister_send_callback(self, namespace: str, connection_id: str)` | Unregister send callback. |
| `publish` | `async def publish(self, namespace: str, room: str, envelope: MessageEnvelope, exclude_connection: str \| None=None)` | Publish message to room. |
| `broadcast` | `async def broadcast(self, namespace: str, envelope: MessageEnvelope, exclude_connection: str \| None=None)` | Broadcast message to all connections in namespace. |
| `join_room` | `async def join_room(self, namespace: str, room: str, connection_id: str)` | Register connection as room member. |
| `leave_room` | `async def leave_room(self, namespace: str, room: str, connection_id: str)` | Unregister connection from room. |
| `get_room_members` | `async def get_room_members(self, namespace: str, room: str)` | Get connection IDs in room. |
| `get_room_info` | `async def get_room_info(self, namespace: str, room: str)` | Get room metadata. |
| `list_rooms` | `async def list_rooms(self, namespace: str)` | List all rooms in namespace. |
| `register_connection` | `async def register_connection(self, namespace: str, connection_id: str, worker_id: str)` | Register active connection. |
| `unregister_connection` | `async def unregister_connection(self, namespace: str, connection_id: str)` | Unregister connection. |
| `get_connection_count` | `async def get_connection_count(self, namespace: str)` | Get active connection count. |

### `RedisAdapter`

- Source: `aquilia/sockets/adapters/redis.py`
- Bases: `Adapter`
- Summary: Redis-backed adapter for multi-worker deployments.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `initialize` | `async def initialize(self)` | Initialize Redis connection and subscriber. |
| `shutdown` | `async def shutdown(self)` | Shutdown Redis connection. |
| `register_send_callback` | `def register_send_callback(self, namespace: str, connection_id: str, callback: callable)` | Register send callback for connection. |
| `unregister_send_callback` | `def unregister_send_callback(self, namespace: str, connection_id: str)` | Unregister send callback. |
| `publish` | `async def publish(self, namespace: str, room: str, envelope: MessageEnvelope, exclude_connection: str \| None=None)` | Publish message to room via Redis pub/sub. |
| `broadcast` | `async def broadcast(self, namespace: str, envelope: MessageEnvelope, exclude_connection: str \| None=None)` | Broadcast message to all connections in namespace. |
| `join_room` | `async def join_room(self, namespace: str, room: str, connection_id: str)` | Add connection to room (Redis sorted set). |
| `leave_room` | `async def leave_room(self, namespace: str, room: str, connection_id: str)` | Remove connection from room. |
| `get_room_members` | `async def get_room_members(self, namespace: str, room: str)` | Get all connection IDs in room. |
| `get_room_info` | `async def get_room_info(self, namespace: str, room: str)` | Get room metadata. |
| `list_rooms` | `async def list_rooms(self, namespace: str)` | List all rooms in namespace. |
| `register_connection` | `async def register_connection(self, namespace: str, connection_id: str, worker_id: str)` | Register connection in Redis hash. |
| `unregister_connection` | `async def unregister_connection(self, namespace: str, connection_id: str)` | Unregister connection. |
| `get_connection_count` | `async def get_connection_count(self, namespace: str)` | Get active connection count. |

### `EventMetadata`

- Source: `aquilia/sockets/compile.py`
- Bases: `object`
- Summary: Compiled event handler metadata.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `event` | `str` | `` |
| `handler_name` | `str` | `` |
| `schema` | `dict[str, Any] \| None` | `` |
| `ack` | `bool` | `` |
| `handler_type` | `str` | `` |

### `SocketControllerMetadata`

- Source: `aquilia/sockets/compile.py`
- Bases: `object`
- Summary: Compiled controller metadata.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `class_name` | `str` | `` |
| `module_path` | `str` | `` |
| `namespace` | `str` | `` |
| `path_pattern` | `str` | `` |
| `events` | `list[EventMetadata]` | `` |
| `guards` | `list[str]` | `` |
| `config` | `dict[str, Any]` | `` |

### `SocketCompiler`

- Source: `aquilia/sockets/compile.py`
- Bases: `object`
- Summary: Compiler for WebSocket controllers.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `compile_controller` | `def compile_controller(self, controller_class: type[SocketController])` | Compile controller to metadata. |
| `generate_artifacts` | `def generate_artifacts(self, output_path: Path)` | Generate artifacts/ws.crous. |
| `validate` | `def validate(self)` | Validate compiled controllers. |

### `ConnectionState`

- Source: `aquilia/sockets/connection.py`
- Bases: `str, Enum`
- Summary: Connection lifecycle state.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `CONNECTING` | `` | `'connecting'` |
| `CONNECTED` | `` | `'connected'` |
| `CLOSING` | `` | `'closing'` |
| `CLOSED` | `` | `'closed'` |

### `ConnectionScope`

- Source: `aquilia/sockets/connection.py`
- Bases: `object`
- Summary: Scope metadata for connection.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `namespace` | `str` | `` |
| `path` | `str` | `` |
| `path_params` | `dict[str, Any]` | `` |
| `query_params` | `dict[str, Any]` | `` |
| `headers` | `dict[str, str]` | `` |

### `Connection`

- Source: `aquilia/sockets/connection.py`
- Bases: `object`
- Summary: WebSocket connection with DI scope.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `id` | `def id(self)` | Alias for connection_id for convenience. |
| `is_connected` | `def is_connected(self)` | Check if connection is active. |
| `rooms` | `def rooms(self)` | Get subscribed rooms. |
| `mark_connected` | `def mark_connected(self)` | Mark connection as connected. |
| `mark_closing` | `def mark_closing(self)` | Mark connection as closing. |
| `mark_closed` | `def mark_closed(self)` | Mark connection as closed. |
| `send_event` | `async def send_event(self, event: str, payload: dict[str, Any], ack: bool=False)` | Send event message to client. |
| `send_envelope` | `async def send_envelope(self, envelope: MessageEnvelope)` | Send message envelope to client. |
| `send_json` | `async def send_json(self, data: dict[str, Any])` | Send a raw JSON dict to the client. |
| `join_room` | `async def join_room(self, room: str)` | Alias for :meth:`join` – kept for readability in controllers. |
| `leave_room` | `async def leave_room(self, room: str)` | Alias for :meth:`leave` – kept for readability in controllers. |
| `send_raw` | `async def send_raw(self, data: bytes)` | Send raw bytes to client. |
| `send_ack` | `async def send_ack(self, message_id: str, status: str='ok', data: dict[str, Any] \| None=None, error: str \| None=None)` | Send acknowledgement message. |
| `join` | `async def join(self, room: str)` | Join a room (subscribe). |
| `leave` | `async def leave(self, room: str)` | Leave a room (unsubscribe). |
| `leave_all` | `async def leave_all(self)` | Leave all rooms. |
| `disconnect` | `async def disconnect(self, reason: str \| None=None, code: int=1000)` | Disconnect the connection. |
| `record_received` | `def record_received(self, size: int)` | Record received message stats. |
| `resolve` | `async def resolve(self, name: str, optional: bool=False)` | Resolve dependency from container. |

### `SocketController`

- Source: `aquilia/sockets/controller.py`
- Bases: `object`
- Summary: Base class for WebSocket controllers.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `namespace` | `str \| None` | `None` |
| `adapter` | `Adapter \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `publish_room` | `async def publish_room(self, room: str, event: str, payload: dict[str, Any], *, namespace: str \| None=None, exclude_connection: str \| None=None)` | Publish message to all connections in a room. |
| `broadcast` | `async def broadcast(self, event: str, payload: dict[str, Any], *, namespace: str \| None=None, exclude_connection: str \| None=None)` | Broadcast message to all connections in namespace. |
| `on_connect` | `async def on_connect(self, conn: Connection)` | Called when connection is established. |
| `on_disconnect` | `async def on_disconnect(self, conn: Connection, reason: str \| None=None)` | Called when connection is closed. |
| `get_room_members` | `def get_room_members(self, room: str, namespace: str \| None=None)` | Get connection IDs in a room. |

### `Socket`

- Source: `aquilia/sockets/decorators.py`
- Bases: `object`
- Summary: WebSocket controller decorator.

### `OnConnect`

- Source: `aquilia/sockets/decorators.py`
- Bases: `object`
- Summary: Handshake handler decorator.

### `OnDisconnect`

- Source: `aquilia/sockets/decorators.py`
- Bases: `object`
- Summary: Disconnect handler decorator.

### `Event`

- Source: `aquilia/sockets/decorators.py`
- Bases: `object`
- Summary: Message event handler decorator.

### `AckEvent`

- Source: `aquilia/sockets/decorators.py`
- Bases: `object`
- Summary: Acknowledgement-enabled event handler.

### `Subscribe`

- Source: `aquilia/sockets/decorators.py`
- Bases: `object`
- Summary: Room subscription handler.

### `Unsubscribe`

- Source: `aquilia/sockets/decorators.py`
- Bases: `object`
- Summary: Room unsubscription handler.

### `Guard`

- Source: `aquilia/sockets/decorators.py`
- Bases: `object`
- Summary: Guard decorator for WebSocket handlers.

### `MessageType`

- Source: `aquilia/sockets/envelope.py`
- Bases: `str, Enum`
- Summary: Message type discriminator.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `EVENT` | `` | `'event'` |
| `ACK` | `` | `'ack'` |
| `SYSTEM` | `` | `'system'` |
| `CONTROL` | `` | `'control'` |

### `MessageEnvelope`

- Source: `aquilia/sockets/envelope.py`
- Bases: `object`
- Summary: Standard message envelope for WebSocket communication.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `type` | `MessageType` | `` |
| `event` | `str` | `` |
| `payload` | `dict[str, Any]` | `` |
| `id` | `str \| None` | `None` |
| `ack` | `bool` | `False` |
| `meta` | `dict[str, Any]` | `field(default_factory=dict)` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` | Serialize to dictionary. |
| `from_dict` | `def from_dict(cls, data: dict[str, Any])` | Deserialize from dictionary. |
| `create_ack` | `def create_ack(self, status: str='ok', data: dict[str, Any] \| None=None, error: str \| None=None)` | Create acknowledgement response. |

### `AckEnvelope`

- Source: `aquilia/sockets/envelope.py`
- Bases: `object`
- Summary: Acknowledgement message.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `id` | `str` | `` |
| `status` | `str` | `` |
| `data` | `dict[str, Any] \| None` | `None` |
| `error` | `str \| None` | `None` |
| `original_id` | `str \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_envelope` | `def to_envelope(self, event: str='ack')` | Convert to message envelope. |

### `StreamChunk`

- Source: `aquilia/sockets/envelope.py`
- Bases: `object`
- Summary: Typed stream chunk payload for websocket event streaming.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `data` | `dict[str, Any] \| str \| bytes` | `` |
| `event` | `str \| None` | `None` |
| `meta` | `dict[str, Any]` | `field(default_factory=dict)` |

### `Schema`

- Source: `aquilia/sockets/envelope.py`
- Bases: `object`
- Summary: Simple schema validator for message payloads.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate` | `def validate(self, data: dict[str, Any])` | Validate data against schema. |

### `MessageCodec`

- Source: `aquilia/sockets/envelope.py`
- Bases: `Protocol`
- Summary: Protocol for message encoding/decoding.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `encode` | `def encode(self, envelope: MessageEnvelope)` | Encode envelope to bytes. |
| `decode` | `def decode(self, data: bytes)` | Decode bytes to envelope. |

### `JSONCodec`

- Source: `aquilia/sockets/envelope.py`
- Bases: `object`
- Summary: JSON message codec.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `encode` | `def encode(self, envelope: MessageEnvelope)` | Encode envelope to JSON bytes. |
| `decode` | `def decode(self, data: bytes)` | Decode JSON bytes to envelope. |

### `MsgPackCodec`

- Source: `aquilia/sockets/envelope.py`
- Bases: `object`
- Summary: MessagePack codec for efficient binary encoding.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `encode` | `def encode(self, envelope: MessageEnvelope)` | Encode envelope to MessagePack bytes. |
| `decode` | `def decode(self, data: bytes)` | Decode MessagePack bytes to envelope. |

### `SocketFault`

- Source: `aquilia/sockets/faults.py`
- Bases: `Fault`
- Summary: Base fault for WebSocket operations.

### `SocketGuard`

- Source: `aquilia/sockets/guards.py`
- Bases: `object`
- Summary: Base class for WebSocket guards.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `check_handshake` | `async def check_handshake(self, scope: ConnectionScope, identity: Identity \| None, session: Session \| None)` | Check handshake authorization. |
| `check_message` | `async def check_message(self, conn: Connection, envelope: MessageEnvelope)` | Check message authorization. |

### `HandshakeAuthGuard`

- Source: `aquilia/sockets/guards.py`
- Bases: `SocketGuard`
- Summary: Handshake authentication guard.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `check_handshake` | `async def check_handshake(self, scope: ConnectionScope, identity: Identity \| None, session: Session \| None)` | Check handshake authentication. |

### `OriginGuard`

- Source: `aquilia/sockets/guards.py`
- Bases: `SocketGuard`
- Summary: Origin validation guard.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `check_handshake` | `async def check_handshake(self, scope: ConnectionScope, identity: Identity \| None, session: Session \| None)` | Check origin header. |

### `MessageAuthGuard`

- Source: `aquilia/sockets/guards.py`
- Bases: `SocketGuard`
- Summary: Per-message authentication guard.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `check_message` | `async def check_message(self, conn: Connection, envelope: MessageEnvelope)` | Check message authentication. |

### `RateLimitGuard`

- Source: `aquilia/sockets/guards.py`
- Bases: `SocketGuard`
- Summary: Rate limiting guard.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `check_message` | `async def check_message(self, conn: Connection, envelope: MessageEnvelope)` | Check rate limit. |

### `MessageValidationMiddleware`

- Source: `aquilia/sockets/middleware.py`
- Bases: `object`
- Summary: Message validation middleware.

### `RateLimitMiddleware`

- Source: `aquilia/sockets/middleware.py`
- Bases: `object`
- Summary: Rate limiting middleware.

### `LoggingMiddleware`

- Source: `aquilia/sockets/middleware.py`
- Bases: `object`
- Summary: Logging middleware.

### `MetricsMiddleware`

- Source: `aquilia/sockets/middleware.py`
- Bases: `object`
- Summary: Metrics collection middleware.

### `MiddlewareChain`

- Source: `aquilia/sockets/middleware.py`
- Bases: `object`
- Summary: Middleware chain builder.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `add` | `def add(self, middleware: SocketMiddleware)` | Add middleware to chain. |
| `build` | `def build(self, final_handler: MessageHandler)` | Build middleware chain. |

### `RouteMetadata`

- Source: `aquilia/sockets/runtime.py`
- Bases: `object`
- Summary: Socket route metadata extracted from controller.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `namespace` | `str` | `` |
| `path_pattern` | `str` | `` |
| `controller_class` | `type[SocketController]` | `` |
| `handlers` | `dict[str, Callable]` | `` |
| `schemas` | `dict[str, Any]` | `` |
| `guards` | `list[SocketGuard]` | `` |
| `allowed_origins` | `list[str] \| None` | `` |
| `max_connections` | `int \| None` | `` |
| `message_rate_limit` | `int \| None` | `` |
| `max_message_size` | `int` | `` |

### `SocketRouter`

- Source: `aquilia/sockets/runtime.py`
- Bases: `object`
- Summary: Router for WebSocket namespaces.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `register` | `def register(self, namespace: str, metadata: RouteMetadata)` | Register socket controller. |
| `match` | `def match(self, path: str)` | Match path to namespace. |

### `AquilaSockets`

- Source: `aquilia/sockets/runtime.py`
- Bases: `object`
- Summary: Main WebSocket runtime.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `initialize` | `async def initialize(self)` | Initialize runtime. |
| `shutdown` | `async def shutdown(self)` | Shutdown runtime. |
| `handle_websocket` | `async def handle_websocket(self, scope: dict, receive: callable, send: callable)` | Handle WebSocket connection (ASGI entry point). |
