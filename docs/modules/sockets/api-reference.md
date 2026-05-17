# WebSockets API Reference

This page is extracted from the current Python source. It includes public classes, methods, functions, constants, dataclass-like fields, decorators, and notable attributes.

## Public Class Summary

| Name | Source | Bases | Purpose |
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

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `compile_socket_controllers` | `aquilia/sockets/compile.py` | `def compile_socket_controllers(controller_classes: list[type[SocketController]], output_dir: Path) -> Path` | Compile socket controllers to artifacts. |
| `WS_HANDSHAKE_FAILED` | `aquilia/sockets/faults.py` | `def WS_HANDSHAKE_FAILED(reason = '')` | Public function. |
| `WS_AUTH_REQUIRED` | `aquilia/sockets/faults.py` | `def WS_AUTH_REQUIRED()` | Public function. |
| `WS_FORBIDDEN` | `aquilia/sockets/faults.py` | `def WS_FORBIDDEN(reason = '')` | Public function. |
| `WS_ORIGIN_NOT_ALLOWED` | `aquilia/sockets/faults.py` | `def WS_ORIGIN_NOT_ALLOWED(origin = '')` | Public function. |
| `WS_MESSAGE_INVALID` | `aquilia/sockets/faults.py` | `def WS_MESSAGE_INVALID(reason = '')` | Public function. |
| `WS_PAYLOAD_TOO_LARGE` | `aquilia/sockets/faults.py` | `def WS_PAYLOAD_TOO_LARGE(size = 0, limit = 0)` | Public function. |
| `WS_UNSUPPORTED_EVENT` | `aquilia/sockets/faults.py` | `def WS_UNSUPPORTED_EVENT(event = '')` | Public function. |
| `WS_CONNECTION_CLOSED` | `aquilia/sockets/faults.py` | `def WS_CONNECTION_CLOSED(reason = '')` | Public function. |
| `WS_CONNECTION_TIMEOUT` | `aquilia/sockets/faults.py` | `def WS_CONNECTION_TIMEOUT()` | Public function. |
| `WS_RATE_LIMIT_EXCEEDED` | `aquilia/sockets/faults.py` | `def WS_RATE_LIMIT_EXCEEDED(limit = 0)` | Public function. |
| `WS_QUOTA_EXCEEDED` | `aquilia/sockets/faults.py` | `def WS_QUOTA_EXCEEDED(quota = '')` | Public function. |
| `WS_ROOM_NOT_FOUND` | `aquilia/sockets/faults.py` | `def WS_ROOM_NOT_FOUND(room = '')` | Public function. |
| `WS_ROOM_FULL` | `aquilia/sockets/faults.py` | `def WS_ROOM_FULL(room = '', capacity = 0)` | Public function. |
| `WS_ALREADY_SUBSCRIBED` | `aquilia/sockets/faults.py` | `def WS_ALREADY_SUBSCRIBED(room = '')` | Public function. |
| `WS_NOT_SUBSCRIBED` | `aquilia/sockets/faults.py` | `def WS_NOT_SUBSCRIBED(room = '')` | Public function. |
| `WS_ADAPTER_UNAVAILABLE` | `aquilia/sockets/faults.py` | `def WS_ADAPTER_UNAVAILABLE(adapter = '')` | Public function. |
| `WS_PUBLISH_FAILED` | `aquilia/sockets/faults.py` | `def WS_PUBLISH_FAILED(reason = '')` | Public function. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `F` | `aquilia/sockets/decorators.py` | `TypeVar('F', bound=Callable[..., Any])` |

## Detailed Classes And Methods

### Class: `RoomInfo`

- Source: `aquilia/sockets/adapters/base.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Room metadata.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `namespace` | `str` |  |
| `room` | `str` |  |
| `member_count` | `int` |  |
| `members` | `set[str]` |  |

### Class: `Adapter`

- Source: `aquilia/sockets/adapters/base.py`
- Bases: `Protocol`
- Summary: Adapter protocol for WebSocket scaling.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `initialize` | `async def initialize(self) -> None` |  | Initialize adapter (connect to backend). |
| `shutdown` | `async def shutdown(self) -> None` |  | Shutdown adapter (close connections). |
| `publish` | `async def publish(self, namespace: str, room: str, envelope: MessageEnvelope, exclude_connection: str &#124; None = None) -> None` |  | Publish message to room. |
| `broadcast` | `async def broadcast(self, namespace: str, envelope: MessageEnvelope, exclude_connection: str &#124; None = None) -> None` |  | Broadcast message to all connections in namespace. |
| `join_room` | `async def join_room(self, namespace: str, room: str, connection_id: str) -> None` |  | Register connection as room member. |
| `leave_room` | `async def leave_room(self, namespace: str, room: str, connection_id: str) -> None` |  | Unregister connection from room. |
| `get_room_members` | `async def get_room_members(self, namespace: str, room: str) -> set[str]` |  | Get connection IDs in room. |
| `get_room_info` | `async def get_room_info(self, namespace: str, room: str) -> RoomInfo &#124; None` |  | Get room metadata. |
| `list_rooms` | `async def list_rooms(self, namespace: str) -> set[str]` |  | List all rooms in namespace. |
| `register_connection` | `async def register_connection(self, namespace: str, connection_id: str, worker_id: str) -> None` |  | Register active connection. |
| `unregister_connection` | `async def unregister_connection(self, namespace: str, connection_id: str) -> None` |  | Unregister connection. |
| `get_connection_count` | `async def get_connection_count(self, namespace: str) -> int` |  | Get active connection count. |

### Class: `InMemoryAdapter`

- Source: `aquilia/sockets/adapters/inmemory.py`
- Bases: `Adapter`
- Summary: In-memory adapter for single-process deployments.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `initialize` | `async def initialize(self) -> None` |  | Initialize adapter. |
| `shutdown` | `async def shutdown(self) -> None` |  | Shutdown adapter. |
| `register_send_callback` | `def register_send_callback(self, namespace: str, connection_id: str, callback: callable)` |  | Register send callback for connection. |
| `unregister_send_callback` | `def unregister_send_callback(self, namespace: str, connection_id: str)` |  | Unregister send callback. |
| `publish` | `async def publish(self, namespace: str, room: str, envelope: MessageEnvelope, exclude_connection: str &#124; None = None) -> None` |  | Publish message to room. |
| `broadcast` | `async def broadcast(self, namespace: str, envelope: MessageEnvelope, exclude_connection: str &#124; None = None) -> None` |  | Broadcast message to all connections in namespace. |
| `join_room` | `async def join_room(self, namespace: str, room: str, connection_id: str) -> None` |  | Register connection as room member. |
| `leave_room` | `async def leave_room(self, namespace: str, room: str, connection_id: str) -> None` |  | Unregister connection from room. |
| `get_room_members` | `async def get_room_members(self, namespace: str, room: str) -> set[str]` |  | Get connection IDs in room. |
| `get_room_info` | `async def get_room_info(self, namespace: str, room: str) -> RoomInfo &#124; None` |  | Get room metadata. |
| `list_rooms` | `async def list_rooms(self, namespace: str) -> set[str]` |  | List all rooms in namespace. |
| `register_connection` | `async def register_connection(self, namespace: str, connection_id: str, worker_id: str) -> None` |  | Register active connection. |
| `unregister_connection` | `async def unregister_connection(self, namespace: str, connection_id: str) -> None` |  | Unregister connection. |
| `get_connection_count` | `async def get_connection_count(self, namespace: str) -> int` |  | Get active connection count. |

### Class: `RedisAdapter`

- Source: `aquilia/sockets/adapters/redis.py`
- Bases: `Adapter`
- Summary: Redis-backed adapter for multi-worker deployments.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `initialize` | `async def initialize(self) -> None` |  | Initialize Redis connection and subscriber. |
| `shutdown` | `async def shutdown(self) -> None` |  | Shutdown Redis connection. |
| `register_send_callback` | `def register_send_callback(self, namespace: str, connection_id: str, callback: callable)` |  | Register send callback for connection. |
| `unregister_send_callback` | `def unregister_send_callback(self, namespace: str, connection_id: str)` |  | Unregister send callback. |
| `publish` | `async def publish(self, namespace: str, room: str, envelope: MessageEnvelope, exclude_connection: str &#124; None = None) -> None` |  | Publish message to room via Redis pub/sub. |
| `broadcast` | `async def broadcast(self, namespace: str, envelope: MessageEnvelope, exclude_connection: str &#124; None = None) -> None` |  | Broadcast message to all connections in namespace. |
| `join_room` | `async def join_room(self, namespace: str, room: str, connection_id: str) -> None` |  | Add connection to room (Redis sorted set). |
| `leave_room` | `async def leave_room(self, namespace: str, room: str, connection_id: str) -> None` |  | Remove connection from room. |
| `get_room_members` | `async def get_room_members(self, namespace: str, room: str) -> set[str]` |  | Get all connection IDs in room. |
| `get_room_info` | `async def get_room_info(self, namespace: str, room: str) -> RoomInfo &#124; None` |  | Get room metadata. |
| `list_rooms` | `async def list_rooms(self, namespace: str) -> set[str]` |  | List all rooms in namespace. |
| `register_connection` | `async def register_connection(self, namespace: str, connection_id: str, worker_id: str) -> None` |  | Register connection in Redis hash. |
| `unregister_connection` | `async def unregister_connection(self, namespace: str, connection_id: str) -> None` |  | Unregister connection. |
| `get_connection_count` | `async def get_connection_count(self, namespace: str) -> int` |  | Get active connection count. |

### Class: `EventMetadata`

- Source: `aquilia/sockets/compile.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Compiled event handler metadata.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `event` | `str` |  |
| `handler_name` | `str` |  |
| `schema` | `dict[str, Any] &#124; None` |  |
| `ack` | `bool` |  |
| `handler_type` | `str` |  |

### Class: `SocketControllerMetadata`

- Source: `aquilia/sockets/compile.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Compiled controller metadata.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `class_name` | `str` |  |
| `module_path` | `str` |  |
| `namespace` | `str` |  |
| `path_pattern` | `str` |  |
| `events` | `list[EventMetadata]` |  |
| `guards` | `list[str]` |  |
| `config` | `dict[str, Any]` |  |

### Class: `SocketCompiler`

- Source: `aquilia/sockets/compile.py`
- Bases: `object`
- Summary: Compiler for WebSocket controllers.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `compile_controller` | `def compile_controller(self, controller_class: type[SocketController]) -> SocketControllerMetadata` |  | Compile controller to metadata. |
| `generate_artifacts` | `def generate_artifacts(self, output_path: Path)` |  | Generate artifacts/ws.crous. |
| `validate` | `def validate(self) -> list[str]` |  | Validate compiled controllers. |

### Class: `ConnectionState`

- Source: `aquilia/sockets/connection.py`
- Bases: `str, Enum`
- Summary: Connection lifecycle state.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `CONNECTING` |  | `'connecting'` |
| `CONNECTED` |  | `'connected'` |
| `CLOSING` |  | `'closing'` |
| `CLOSED` |  | `'closed'` |

### Class: `ConnectionScope`

- Source: `aquilia/sockets/connection.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Scope metadata for connection.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `namespace` | `str` |  |
| `path` | `str` |  |
| `path_params` | `dict[str, Any]` |  |
| `query_params` | `dict[str, Any]` |  |
| `headers` | `dict[str, str]` |  |

### Class: `Connection`

- Source: `aquilia/sockets/connection.py`
- Bases: `object`
- Summary: WebSocket connection with DI scope.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `id` | `def id(self) -> str` | property | Alias for connection_id for convenience. |
| `is_connected` | `def is_connected(self) -> bool` | property | Check if connection is active. |
| `rooms` | `def rooms(self) -> set[str]` | property | Get subscribed rooms. |
| `mark_connected` | `def mark_connected(self)` |  | Mark connection as connected. |
| `mark_closing` | `def mark_closing(self)` |  | Mark connection as closing. |
| `mark_closed` | `def mark_closed(self)` |  | Mark connection as closed. |
| `send_event` | `async def send_event(self, event: str, payload: dict[str, Any], ack: bool = False) -> str &#124; None` |  | Send event message to client. |
| `send_envelope` | `async def send_envelope(self, envelope: MessageEnvelope)` |  | Send message envelope to client. |
| `send_json` | `async def send_json(self, data: dict[str, Any])` |  | Send a raw JSON dict to the client. |
| `join_room` | `async def join_room(self, room: str) -> bool` |  | Alias for :meth:`join` - kept for readability in controllers. |
| `leave_room` | `async def leave_room(self, room: str) -> bool` |  | Alias for :meth:`leave` - kept for readability in controllers. |
| `send_raw` | `async def send_raw(self, data: bytes)` |  | Send raw bytes to client. |
| `send_ack` | `async def send_ack(self, message_id: str, status: str = 'ok', data: dict[str, Any] &#124; None = None, error: str &#124; None = None)` |  | Send acknowledgement message. |
| `join` | `async def join(self, room: str) -> bool` |  | Join a room (subscribe). |
| `leave` | `async def leave(self, room: str) -> bool` |  | Leave a room (unsubscribe). |
| `leave_all` | `async def leave_all(self)` |  | Leave all rooms. |
| `disconnect` | `async def disconnect(self, reason: str &#124; None = None, code: int = 1000)` |  | Disconnect the connection. |
| `record_received` | `def record_received(self, size: int)` |  | Record received message stats. |
| `resolve` | `async def resolve(self, name: str, optional: bool = False) -> Any` |  | Resolve dependency from container. |

### Class: `SocketController`

- Source: `aquilia/sockets/controller.py`
- Bases: `object`
- Summary: Base class for WebSocket controllers.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `namespace` | `str &#124; None` | `None` |
| `adapter` | `Adapter &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `publish_room` | `async def publish_room(self, room: str, event: str, payload: dict[str, Any], *, namespace: str &#124; None = None, exclude_connection: str &#124; None = None)` |  | Publish message to all connections in a room. |
| `broadcast` | `async def broadcast(self, event: str, payload: dict[str, Any], *, namespace: str &#124; None = None, exclude_connection: str &#124; None = None)` |  | Broadcast message to all connections in namespace. |
| `on_connect` | `async def on_connect(self, conn: Connection)` |  | Called when connection is established. |
| `on_disconnect` | `async def on_disconnect(self, conn: Connection, reason: str &#124; None = None)` |  | Called when connection is closed. |
| `get_room_members` | `def get_room_members(self, room: str, namespace: str &#124; None = None) -> set[str]` |  | Get connection IDs in a room. |

### Class: `Socket`

- Source: `aquilia/sockets/decorators.py`
- Bases: `object`
- Summary: WebSocket controller decorator.

### Class: `OnConnect`

- Source: `aquilia/sockets/decorators.py`
- Bases: `object`
- Summary: Handshake handler decorator.

### Class: `OnDisconnect`

- Source: `aquilia/sockets/decorators.py`
- Bases: `object`
- Summary: Disconnect handler decorator.

### Class: `Event`

- Source: `aquilia/sockets/decorators.py`
- Bases: `object`
- Summary: Message event handler decorator.

### Class: `AckEvent`

- Source: `aquilia/sockets/decorators.py`
- Bases: `object`
- Summary: Acknowledgement-enabled event handler.

### Class: `Subscribe`

- Source: `aquilia/sockets/decorators.py`
- Bases: `object`
- Summary: Room subscription handler.

### Class: `Unsubscribe`

- Source: `aquilia/sockets/decorators.py`
- Bases: `object`
- Summary: Room unsubscription handler.

### Class: `Guard`

- Source: `aquilia/sockets/decorators.py`
- Bases: `object`
- Summary: Guard decorator for WebSocket handlers.

### Class: `MessageType`

- Source: `aquilia/sockets/envelope.py`
- Bases: `str, Enum`
- Summary: Message type discriminator.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `EVENT` |  | `'event'` |
| `ACK` |  | `'ack'` |
| `SYSTEM` |  | `'system'` |
| `CONTROL` |  | `'control'` |

### Class: `MessageEnvelope`

- Source: `aquilia/sockets/envelope.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Standard message envelope for WebSocket communication.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `type` | `MessageType` |  |
| `event` | `str` |  |
| `payload` | `dict[str, Any]` |  |
| `id` | `str &#124; None` | `None` |
| `ack` | `bool` | `False` |
| `meta` | `dict[str, Any]` | `field(default_factory=dict)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialize to dictionary. |
| `from_dict` | `def from_dict(cls, data: dict[str, Any]) -> MessageEnvelope` | classmethod | Deserialize from dictionary. |
| `create_ack` | `def create_ack(self, status: str = 'ok', data: dict[str, Any] &#124; None = None, error: str &#124; None = None) -> MessageEnvelope` |  | Create acknowledgement response. |

### Class: `AckEnvelope`

- Source: `aquilia/sockets/envelope.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Acknowledgement message.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `id` | `str` |  |
| `status` | `str` |  |
| `data` | `dict[str, Any] &#124; None` | `None` |
| `error` | `str &#124; None` | `None` |
| `original_id` | `str &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_envelope` | `def to_envelope(self, event: str = 'ack') -> MessageEnvelope` |  | Convert to message envelope. |

### Class: `StreamChunk`

- Source: `aquilia/sockets/envelope.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Typed stream chunk payload for websocket event streaming.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `data` | `dict[str, Any] &#124; str &#124; bytes` |  |
| `event` | `str &#124; None` | `None` |
| `meta` | `dict[str, Any]` | `field(default_factory=dict)` |

### Class: `Schema`

- Source: `aquilia/sockets/envelope.py`
- Bases: `object`
- Summary: Simple schema validator for message payloads.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate` | `def validate(self, data: dict[str, Any]) -> tuple[bool, str &#124; None]` |  | Validate data against schema. |

### Class: `MessageCodec`

- Source: `aquilia/sockets/envelope.py`
- Bases: `Protocol`
- Summary: Protocol for message encoding/decoding.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `encode` | `def encode(self, envelope: MessageEnvelope) -> bytes` |  | Encode envelope to bytes. |
| `decode` | `def decode(self, data: bytes) -> MessageEnvelope` |  | Decode bytes to envelope. |

### Class: `JSONCodec`

- Source: `aquilia/sockets/envelope.py`
- Bases: `object`
- Summary: JSON message codec.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `encode` | `def encode(self, envelope: MessageEnvelope) -> bytes` |  | Encode envelope to JSON bytes. |
| `decode` | `def decode(self, data: bytes) -> MessageEnvelope` |  | Decode JSON bytes to envelope. |

### Class: `MsgPackCodec`

- Source: `aquilia/sockets/envelope.py`
- Bases: `object`
- Summary: MessagePack codec for efficient binary encoding.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `encode` | `def encode(self, envelope: MessageEnvelope) -> bytes` |  | Encode envelope to MessagePack bytes. |
| `decode` | `def decode(self, data: bytes) -> MessageEnvelope` |  | Decode MessagePack bytes to envelope. |

### Class: `SocketFault`

- Source: `aquilia/sockets/faults.py`
- Bases: `Fault`
- Summary: Base fault for WebSocket operations.

### Class: `SocketGuard`

- Source: `aquilia/sockets/guards.py`
- Bases: `object`
- Summary: Base class for WebSocket guards.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `check_handshake` | `async def check_handshake(self, scope: ConnectionScope, identity: Identity &#124; None, session: Session &#124; None) -> bool` |  | Check handshake authorization. |
| `check_message` | `async def check_message(self, conn: Connection, envelope: MessageEnvelope) -> bool` |  | Check message authorization. |

### Class: `HandshakeAuthGuard`

- Source: `aquilia/sockets/guards.py`
- Bases: `SocketGuard`
- Summary: Handshake authentication guard.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `check_handshake` | `async def check_handshake(self, scope: ConnectionScope, identity: Identity &#124; None, session: Session &#124; None) -> bool` |  | Check handshake authentication. |

### Class: `OriginGuard`

- Source: `aquilia/sockets/guards.py`
- Bases: `SocketGuard`
- Summary: Origin validation guard.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `check_handshake` | `async def check_handshake(self, scope: ConnectionScope, identity: Identity &#124; None, session: Session &#124; None) -> bool` |  | Check origin header. |

### Class: `MessageAuthGuard`

- Source: `aquilia/sockets/guards.py`
- Bases: `SocketGuard`
- Summary: Per-message authentication guard.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `check_message` | `async def check_message(self, conn: Connection, envelope: MessageEnvelope) -> bool` |  | Check message authentication. |

### Class: `RateLimitGuard`

- Source: `aquilia/sockets/guards.py`
- Bases: `SocketGuard`
- Summary: Rate limiting guard.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `check_message` | `async def check_message(self, conn: Connection, envelope: MessageEnvelope) -> bool` |  | Check rate limit. |

### Class: `MessageValidationMiddleware`

- Source: `aquilia/sockets/middleware.py`
- Bases: `object`
- Summary: Message validation middleware.

### Class: `RateLimitMiddleware`

- Source: `aquilia/sockets/middleware.py`
- Bases: `object`
- Summary: Rate limiting middleware.

### Class: `LoggingMiddleware`

- Source: `aquilia/sockets/middleware.py`
- Bases: `object`
- Summary: Logging middleware.

### Class: `MetricsMiddleware`

- Source: `aquilia/sockets/middleware.py`
- Bases: `object`
- Summary: Metrics collection middleware.

### Class: `MiddlewareChain`

- Source: `aquilia/sockets/middleware.py`
- Bases: `object`
- Summary: Middleware chain builder.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `add` | `def add(self, middleware: SocketMiddleware)` |  | Add middleware to chain. |
| `build` | `def build(self, final_handler: MessageHandler) -> MessageHandler` |  | Build middleware chain. |

### Class: `RouteMetadata`

- Source: `aquilia/sockets/runtime.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Socket route metadata extracted from controller.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `namespace` | `str` |  |
| `path_pattern` | `str` |  |
| `controller_class` | `type[SocketController]` |  |
| `handlers` | `dict[str, Callable]` |  |
| `schemas` | `dict[str, Any]` |  |
| `guards` | `list[SocketGuard]` |  |
| `allowed_origins` | `list[str] &#124; None` |  |
| `max_connections` | `int &#124; None` |  |
| `message_rate_limit` | `int &#124; None` |  |
| `max_message_size` | `int` |  |

### Class: `SocketRouter`

- Source: `aquilia/sockets/runtime.py`
- Bases: `object`
- Summary: Router for WebSocket namespaces.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `register` | `def register(self, namespace: str, metadata: RouteMetadata)` |  | Register socket controller. |
| `match` | `def match(self, path: str) -> tuple[str, RouteMetadata, dict[str, Any]] &#124; None` |  | Match path to namespace. |

### Class: `AquilaSockets`

- Source: `aquilia/sockets/runtime.py`
- Bases: `object`
- Summary: Main WebSocket runtime.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `initialize` | `async def initialize(self)` |  | Initialize runtime. |
| `shutdown` | `async def shutdown(self)` |  | Shutdown runtime. |
| `handle_websocket` | `async def handle_websocket(self, scope: dict, receive: callable, send: callable)` |  | Handle WebSocket connection (ASGI entry point). |

## Functions

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `compile_socket_controllers` | `aquilia/sockets/compile.py` | `def compile_socket_controllers(controller_classes: list[type[SocketController]], output_dir: Path) -> Path` | Compile socket controllers to artifacts. |
| `WS_HANDSHAKE_FAILED` | `aquilia/sockets/faults.py` | `def WS_HANDSHAKE_FAILED(reason = '')` | Public function. |
| `WS_AUTH_REQUIRED` | `aquilia/sockets/faults.py` | `def WS_AUTH_REQUIRED()` | Public function. |
| `WS_FORBIDDEN` | `aquilia/sockets/faults.py` | `def WS_FORBIDDEN(reason = '')` | Public function. |
| `WS_ORIGIN_NOT_ALLOWED` | `aquilia/sockets/faults.py` | `def WS_ORIGIN_NOT_ALLOWED(origin = '')` | Public function. |
| `WS_MESSAGE_INVALID` | `aquilia/sockets/faults.py` | `def WS_MESSAGE_INVALID(reason = '')` | Public function. |
| `WS_PAYLOAD_TOO_LARGE` | `aquilia/sockets/faults.py` | `def WS_PAYLOAD_TOO_LARGE(size = 0, limit = 0)` | Public function. |
| `WS_UNSUPPORTED_EVENT` | `aquilia/sockets/faults.py` | `def WS_UNSUPPORTED_EVENT(event = '')` | Public function. |
| `WS_CONNECTION_CLOSED` | `aquilia/sockets/faults.py` | `def WS_CONNECTION_CLOSED(reason = '')` | Public function. |
| `WS_CONNECTION_TIMEOUT` | `aquilia/sockets/faults.py` | `def WS_CONNECTION_TIMEOUT()` | Public function. |
| `WS_RATE_LIMIT_EXCEEDED` | `aquilia/sockets/faults.py` | `def WS_RATE_LIMIT_EXCEEDED(limit = 0)` | Public function. |
| `WS_QUOTA_EXCEEDED` | `aquilia/sockets/faults.py` | `def WS_QUOTA_EXCEEDED(quota = '')` | Public function. |
| `WS_ROOM_NOT_FOUND` | `aquilia/sockets/faults.py` | `def WS_ROOM_NOT_FOUND(room = '')` | Public function. |
| `WS_ROOM_FULL` | `aquilia/sockets/faults.py` | `def WS_ROOM_FULL(room = '', capacity = 0)` | Public function. |
| `WS_ALREADY_SUBSCRIBED` | `aquilia/sockets/faults.py` | `def WS_ALREADY_SUBSCRIBED(room = '')` | Public function. |
| `WS_NOT_SUBSCRIBED` | `aquilia/sockets/faults.py` | `def WS_NOT_SUBSCRIBED(room = '')` | Public function. |
| `WS_ADAPTER_UNAVAILABLE` | `aquilia/sockets/faults.py` | `def WS_ADAPTER_UNAVAILABLE(adapter = '')` | Public function. |
| `WS_PUBLISH_FAILED` | `aquilia/sockets/faults.py` | `def WS_PUBLISH_FAILED(reason = '')` | Public function. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `F` | `aquilia/sockets/decorators.py` | `TypeVar('F', bound=Callable[..., Any])` |
