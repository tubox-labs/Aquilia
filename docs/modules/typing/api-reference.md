# Typing Contracts API Reference

This page is extracted from the current Python source. It includes public classes, methods, functions, constants, dataclass-like fields, decorators, and notable attributes.

## Public Class Summary

| Name | Source | Bases | Purpose |
| --- | --- | --- | --- |
| `HTTPScope` | `aquilia/typing/asgi.py` | TypedDict | Public class. |
| `WebSocketScope` | `aquilia/typing/asgi.py` | TypedDict | Public class. |
| `LifespanScope` | `aquilia/typing/asgi.py` | TypedDict | Public class. |
| `HTTPRequestEvent` | `aquilia/typing/asgi.py` | TypedDict | Public class. |
| `HTTPDisconnectEvent` | `aquilia/typing/asgi.py` | TypedDict | Public class. |
| `HTTPResponseStartEvent` | `aquilia/typing/asgi.py` | TypedDict | Public class. |
| `HTTPResponseBodyEvent` | `aquilia/typing/asgi.py` | TypedDict | Public class. |
| `HTTPResponseTrailersEvent` | `aquilia/typing/asgi.py` | TypedDict | Public class. |
| `WebSocketConnectEvent` | `aquilia/typing/asgi.py` | TypedDict | Public class. |
| `WebSocketReceiveEvent` | `aquilia/typing/asgi.py` | TypedDict | Public class. |
| `WebSocketDisconnectEvent` | `aquilia/typing/asgi.py` | TypedDict | Public class. |
| `WebSocketAcceptEvent` | `aquilia/typing/asgi.py` | TypedDict | Public class. |
| `WebSocketSendEvent` | `aquilia/typing/asgi.py` | TypedDict | Public class. |
| `WebSocketCloseEvent` | `aquilia/typing/asgi.py` | TypedDict | Public class. |
| `LifespanStartupEvent` | `aquilia/typing/asgi.py` | TypedDict | Public class. |
| `LifespanShutdownEvent` | `aquilia/typing/asgi.py` | TypedDict | Public class. |
| `LifespanStartupCompleteEvent` | `aquilia/typing/asgi.py` | TypedDict | Public class. |
| `LifespanStartupFailedEvent` | `aquilia/typing/asgi.py` | TypedDict | Public class. |
| `LifespanShutdownCompleteEvent` | `aquilia/typing/asgi.py` | TypedDict | Public class. |
| `LifespanShutdownFailedEvent` | `aquilia/typing/asgi.py` | TypedDict | Public class. |
| `ASGIApplication` | `aquilia/typing/asgi.py` | Protocol | Public class. |
| `ConfigSource` | `aquilia/typing/config.py` | Protocol | Protocol for configuration sources that can be converted to dict. |
| `EnvResolvable` | `aquilia/typing/config.py` | Protocol | Protocol for values that resolve from environment variables. |
| `SecretRevealable` | `aquilia/typing/config.py` | Protocol | Protocol for secret values that can be revealed. |
| `ConfigSection` | `aquilia/typing/config.py` | Protocol | Protocol for config section classes. |
| `SyncResolvableContainer` | `aquilia/typing/container.py` | Protocol | Public class. |
| `AsyncResolvableContainer` | `aquilia/typing/container.py` | Protocol | Public class. |
| `StartupContainer` | `aquilia/typing/container.py` | Protocol | Public class. |
| `ShutdownContainer` | `aquilia/typing/container.py` | Protocol | Public class. |
| `RequestScopeFactory` | `aquilia/typing/container.py` | Protocol | Public class. |
| `RequestContainer` | `aquilia/typing/container.py` | AsyncResolvableContainer, SyncResolvableContainer, ShutdownContainer, Protocol | Public class. |
| `AppContainer` | `aquilia/typing/container.py` | AsyncResolvableContainer, SyncResolvableContainer, StartupContainer, ShutdownContainer, RequestScopeFactory, Protocol | Public class. |
| `ControllerRouteMatchLike` | `aquilia/typing/controller.py` | Protocol | Public class. |
| `EffectProviderProtocol` | `aquilia/typing/effects.py` | Protocol[EffectResourceT] | Public class. |
| `ManifestDescriptor` | `aquilia/typing/manifest.py` | object | Public class. |
| `ManifestLike` | `aquilia/typing/manifest.py` | Protocol | Public class. |
| `MiddlewareProtocol` | `aquilia/typing/middleware.py` | Protocol | Public class. |

## Public Function Summary

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| None detected |  |  |  |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `T` | `aquilia/typing/config.py` | `TypeVar('T')` |
| `T` | `aquilia/typing/container.py` | `TypeVar('T')` |

## Detailed Classes And Methods

### Class: `HTTPScope`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `type` | `Literal['http']` |  |
| `asgi` | `ASGIVersionInfo` |  |
| `http_version` | `str` |  |
| `method` | `str` |  |
| `scheme` | `str` |  |
| `path` | `str` |  |
| `raw_path` | `bytes` |  |
| `root_path` | `str` |  |
| `query_string` | `bytes` |  |
| `headers` | `RawHeaderList` |  |
| `client` | `ASGIClientAddress` |  |
| `server` | `ASGIServerAddress` |  |
| `state` | `dict[str, object]` |  |

### Class: `WebSocketScope`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `type` | `Literal['websocket']` |  |
| `asgi` | `ASGIVersionInfo` |  |
| `http_version` | `str` |  |
| `scheme` | `str` |  |
| `path` | `str` |  |
| `raw_path` | `bytes` |  |
| `root_path` | `str` |  |
| `query_string` | `bytes` |  |
| `headers` | `RawHeaderList` |  |
| `client` | `ASGIClientAddress` |  |
| `server` | `ASGIServerAddress` |  |
| `subprotocols` | `list[str]` |  |
| `state` | `dict[str, object]` |  |

### Class: `LifespanScope`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `type` | `Literal['lifespan']` |  |
| `asgi` | `ASGIVersionInfo` |  |
| `state` | `dict[str, object]` |  |

### Class: `HTTPRequestEvent`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `type` | `Literal['http.request']` |  |
| `body` | `bytes` |  |
| `more_body` | `bool` |  |

### Class: `HTTPDisconnectEvent`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `type` | `Literal['http.disconnect']` |  |

### Class: `HTTPResponseStartEvent`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `type` | `Literal['http.response.start']` |  |
| `status` | `int` |  |
| `headers` | `RawHeaderList` |  |
| `trailers` | `bool` |  |

### Class: `HTTPResponseBodyEvent`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `type` | `Literal['http.response.body']` |  |
| `body` | `bytes` |  |
| `more_body` | `bool` |  |

### Class: `HTTPResponseTrailersEvent`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `type` | `Literal['http.response.trailers']` |  |
| `headers` | `RawHeaderList` |  |
| `more_trailers` | `bool` |  |

### Class: `WebSocketConnectEvent`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `type` | `Literal['websocket.connect']` |  |

### Class: `WebSocketReceiveEvent`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `type` | `Literal['websocket.receive']` |  |
| `bytes` | `bytes` |  |
| `text` | `str` |  |

### Class: `WebSocketDisconnectEvent`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `type` | `Literal['websocket.disconnect']` |  |
| `code` | `int` |  |
| `reason` | `str` |  |

### Class: `WebSocketAcceptEvent`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `type` | `Literal['websocket.accept']` |  |
| `subprotocol` | `str` |  |
| `headers` | `RawHeaderList` |  |

### Class: `WebSocketSendEvent`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `type` | `Literal['websocket.send']` |  |
| `bytes` | `bytes` |  |
| `text` | `str` |  |

### Class: `WebSocketCloseEvent`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `type` | `Literal['websocket.close']` |  |
| `code` | `int` |  |
| `reason` | `str` |  |

### Class: `LifespanStartupEvent`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `type` | `Literal['lifespan.startup']` |  |

### Class: `LifespanShutdownEvent`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `type` | `Literal['lifespan.shutdown']` |  |

### Class: `LifespanStartupCompleteEvent`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `type` | `Literal['lifespan.startup.complete']` |  |

### Class: `LifespanStartupFailedEvent`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `type` | `Literal['lifespan.startup.failed']` |  |
| `message` | `str` |  |

### Class: `LifespanShutdownCompleteEvent`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `type` | `Literal['lifespan.shutdown.complete']` |  |

### Class: `LifespanShutdownFailedEvent`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `type` | `Literal['lifespan.shutdown.failed']` |  |
| `message` | `str` |  |

### Class: `ASGIApplication`

- Source: `aquilia/typing/asgi.py`
- Bases: `Protocol`

### Class: `ConfigSource`

- Source: `aquilia/typing/config.py`
- Bases: `Protocol`
- Decorators: `runtime_checkable`
- Summary: Protocol for configuration sources that can be converted to dict.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> ConfigDict` |  | Convert this config source to a dictionary. |

### Class: `EnvResolvable`

- Source: `aquilia/typing/config.py`
- Bases: `Protocol`
- Decorators: `runtime_checkable`
- Summary: Protocol for values that resolve from environment variables.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `resolve` | `def resolve(self) -> ConfigValue` |  | Resolve the value from the environment. |

### Class: `SecretRevealable`

- Source: `aquilia/typing/config.py`
- Bases: `Protocol`
- Decorators: `runtime_checkable`
- Summary: Protocol for secret values that can be revealed.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `reveal` | `def reveal(self) -> str &#124; None` |  | Reveal the secret value. |

### Class: `ConfigSection`

- Source: `aquilia/typing/config.py`
- Bases: `Protocol`
- Decorators: `runtime_checkable`
- Summary: Protocol for config section classes.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(cls) -> ConfigDict` | classmethod | Convert this section to a dictionary. |

### Class: `SyncResolvableContainer`

- Source: `aquilia/typing/container.py`
- Bases: `Protocol`

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `resolve` | `def resolve(self, name: DIName, optional: DIOptionalFlag = False) -> DIResolvedValue` |  | Method. |

### Class: `AsyncResolvableContainer`

- Source: `aquilia/typing/container.py`
- Bases: `Protocol`

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `resolve_async` | `async def resolve_async(self, name: DIName, optional: DIOptionalFlag = False) -> DIResolvedValue` |  | Method. |

### Class: `StartupContainer`

- Source: `aquilia/typing/container.py`
- Bases: `Protocol`

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `startup` | `async def startup(self) -> None` |  | Method. |

### Class: `ShutdownContainer`

- Source: `aquilia/typing/container.py`
- Bases: `Protocol`

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `shutdown` | `async def shutdown(self) -> None` |  | Method. |

### Class: `RequestScopeFactory`

- Source: `aquilia/typing/container.py`
- Bases: `Protocol`

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `create_request_scope` | `def create_request_scope(self) -> RequestContainer` |  | Method. |

### Class: `RequestContainer`

- Source: `aquilia/typing/container.py`
- Bases: `AsyncResolvableContainer, SyncResolvableContainer, ShutdownContainer, Protocol`

### Class: `AppContainer`

- Source: `aquilia/typing/container.py`
- Bases: `AsyncResolvableContainer, SyncResolvableContainer, StartupContainer, ShutdownContainer, RequestScopeFactory, Protocol`

### Class: `ControllerRouteMatchLike`

- Source: `aquilia/typing/controller.py`
- Bases: `Protocol`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `route` | `object` |  |
| `params` | `RouteParams` |  |
| `query` | `RouteQuery` |  |

### Class: `EffectProviderProtocol`

- Source: `aquilia/typing/effects.py`
- Bases: `Protocol[EffectResourceT]`

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `initialize` | `async def initialize(self) -> None` |  | Method. |
| `acquire` | `async def acquire(self, mode: str &#124; None = None) -> EffectResourceT` |  | Method. |
| `release` | `async def release(self, resource: EffectResourceT, success: bool = True) -> None` |  | Method. |
| `finalize` | `async def finalize(self) -> None` |  | Method. |

### Class: `ManifestDescriptor`

- Source: `aquilia/typing/manifest.py`
- Bases: `object`
- Decorators: `dataclass`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `ManifestName` |  |
| `module` | `ModuleName` |  |
| `class_path` | `ClassPath` |  |

### Class: `ManifestLike`

- Source: `aquilia/typing/manifest.py`
- Bases: `Protocol`

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `name` | `str` |  |

### Class: `MiddlewareProtocol`

- Source: `aquilia/typing/middleware.py`
- Bases: `Protocol`


## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `T` | `aquilia/typing/config.py` | `TypeVar('T')` |
| `T` | `aquilia/typing/container.py` | `TypeVar('T')` |
