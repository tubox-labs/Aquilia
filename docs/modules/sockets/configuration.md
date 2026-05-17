# WebSockets Configuration

## Configuration Entry Points

The implementation exposes the following configuration-like classes, policies, integrations, or dataclasses.

| Type | Source | Fields | Purpose |
| --- | --- | --- | --- |
| `RoomInfo` | `aquilia/sockets/adapters/base.py` | namespace: str, room: str, member_count: int, members: set[str] | Room metadata. |
| `EventMetadata` | `aquilia/sockets/compile.py` | event: str, handler_name: str, schema: dict[str, Any] &#124; None, ack: bool, handler_type: str | Compiled event handler metadata. |
| `SocketControllerMetadata` | `aquilia/sockets/compile.py` | class_name: str, module_path: str, namespace: str, path_pattern: str, events: list[EventMetadata], guards: list[str], config: dict[str, Any] | Compiled controller metadata. |
| `ConnectionScope` | `aquilia/sockets/connection.py` | namespace: str, path: str, path_params: dict[str, Any], query_params: dict[str, Any], headers: dict[str, str] | Scope metadata for connection. |
| `MessageEnvelope` | `aquilia/sockets/envelope.py` | type: MessageType, event: str, payload: dict[str, Any], id: str &#124; None, ack: bool, meta: dict[str, Any] | Standard message envelope for WebSocket communication. |
| `AckEnvelope` | `aquilia/sockets/envelope.py` | id: str, status: str, data: dict[str, Any] &#124; None, error: str &#124; None, original_id: str &#124; None | Acknowledgement message. |
| `StreamChunk` | `aquilia/sockets/envelope.py` | data: dict[str, Any] &#124; str &#124; bytes, event: str &#124; None, meta: dict[str, Any] | Typed stream chunk payload for websocket event streaming. |
| `RouteMetadata` | `aquilia/sockets/runtime.py` | namespace: str, path_pattern: str, controller_class: type[SocketController], handlers: dict[str, Callable], schemas: dict[str, Any], guards: list[SocketGuard], allowed_origins: list[str] &#124; None, max_connections: int &#124; None, message_rate_limit: int &#124; None, max_message_size: int | Socket route metadata extracted from controller. |

## Common Entry Points

- No dedicated workspace integration was detected from module naming. Configure this module through direct constructors, manifests, or the subsystem that owns it.

## Precedence Model

Aquilia generally resolves configuration in this order:

1. Explicit constructor arguments or typed integration dataclass values.
2. `Workspace` builder methods and `Workspace.integrate(...)` output.
3. `ConfigLoader` defaults and environment overlays.
4. Runtime defaults inside the subsystem service or provider constructor.

When this module is registered through an `AppManifest`, keep component declarations inside `modules/<name>/manifest.py` and keep cross-cutting integration settings in `workspace.py`.

## Datatype Guidance

- Prefer typed dataclasses, policy objects, and config objects listed above when they exist.
- Keep secret values in environment-backed config, not literal strings in committed workspace files.
- Keep runtime-only state in services, stores, providers, or request state rather than static configuration.
- Use `to_dict()` on integration dataclasses when you need to inspect exactly what enters `ConfigLoader`.
