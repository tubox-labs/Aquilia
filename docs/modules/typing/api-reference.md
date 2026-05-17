# Typing API Reference

This page is generated from the current Python source using the AST. It lists public classes, public methods, public module-level functions, constants, exports, and source files.

## Source Inventory

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/typing/__init__.py` | 144 | 0 | 0 |  |
| `aquilia/typing/asgi.py` | 151 | 21 | 0 |  |
| `aquilia/typing/common.py` | 24 | 0 | 0 |  |
| `aquilia/typing/config.py` | 121 | 4 | 0 | Configuration type definitions for Aquilia. |
| `aquilia/typing/container.py` | 46 | 7 | 0 |  |
| `aquilia/typing/controller.py` | 30 | 1 | 0 |  |
| `aquilia/typing/effects.py` | 21 | 1 | 0 |  |
| `aquilia/typing/manifest.py` | 26 | 2 | 0 |  |
| `aquilia/typing/middleware.py` | 20 | 1 | 0 |  |
| `aquilia/typing/request_state.py` | 10 | 0 | 0 |  |

## Public Exports

`ASGIApplication`, `ASGIReceive`, `ASGIReceiveEvent`, `ASGIScope`, `ASGISend`, `ASGISendEvent`, `AppContainer`, `AsyncResolvableContainer`, `ConfigDict`, `ConfigPrimitive`, `ConfigSection`, `ConfigSource`, `ConfigValue`, `ControllerReturnValue`, `ControllerRouteMatchLike`, `ControllerStreamChunk`, `ControllerStreamIterator`, `DotEnvPath`, `DotEnvValues`, `EffectMap`, `EffectMetadata`, `EffectMode`, `EffectName`, `EffectProviderProtocol`, `EnvCastType`, `EnvCaster`, `EnvMapping`, `EnvResolvable`, `EnvVarName`, `EnvVarValue`, `HTTPMethod`, `HTTPScope`, `HeaderMap`, `HeaderPair`, `JSONLikeMapping`, `JSONLikeSequence`, `JSONObject`, `JSONPrimitive`, `JSONValue`, `LifespanScope`, `ManifestCollection`, `ManifestDescriptor`, `ManifestLike`, `ManifestMetadata`, `MetadataMap`, `MiddlewareCallable`, `MiddlewareName`, `MiddlewarePriority`, `MiddlewareProtocol`, `MiddlewareScope`, `Milliseconds`, `PathLike`, `PathParams`, `QueryStringMap`, `RawHeaderList`, `RequestContainer`, `RequestHandler`, `RequestState`, `RouteMetadataDict`, `RouteParams`, `RoutePath`, `RouteQuery`, `SecretRevealable`, `SyncResolvableContainer`, `Timestamp`, `WebSocketScope`

## Public Class Summary

| Class | Source | Bases | Summary |
| --- | --- | --- | --- |
| `HTTPScope` | `aquilia/typing/asgi.py` | TypedDict |  |
| `WebSocketScope` | `aquilia/typing/asgi.py` | TypedDict |  |
| `LifespanScope` | `aquilia/typing/asgi.py` | TypedDict |  |
| `HTTPRequestEvent` | `aquilia/typing/asgi.py` | TypedDict |  |
| `HTTPDisconnectEvent` | `aquilia/typing/asgi.py` | TypedDict |  |
| `HTTPResponseStartEvent` | `aquilia/typing/asgi.py` | TypedDict |  |
| `HTTPResponseBodyEvent` | `aquilia/typing/asgi.py` | TypedDict |  |
| `HTTPResponseTrailersEvent` | `aquilia/typing/asgi.py` | TypedDict |  |
| `WebSocketConnectEvent` | `aquilia/typing/asgi.py` | TypedDict |  |
| `WebSocketReceiveEvent` | `aquilia/typing/asgi.py` | TypedDict |  |
| `WebSocketDisconnectEvent` | `aquilia/typing/asgi.py` | TypedDict |  |
| `WebSocketAcceptEvent` | `aquilia/typing/asgi.py` | TypedDict |  |
| `WebSocketSendEvent` | `aquilia/typing/asgi.py` | TypedDict |  |
| `WebSocketCloseEvent` | `aquilia/typing/asgi.py` | TypedDict |  |
| `LifespanStartupEvent` | `aquilia/typing/asgi.py` | TypedDict |  |
| `LifespanShutdownEvent` | `aquilia/typing/asgi.py` | TypedDict |  |
| `LifespanStartupCompleteEvent` | `aquilia/typing/asgi.py` | TypedDict |  |
| `LifespanStartupFailedEvent` | `aquilia/typing/asgi.py` | TypedDict |  |
| `LifespanShutdownCompleteEvent` | `aquilia/typing/asgi.py` | TypedDict |  |
| `LifespanShutdownFailedEvent` | `aquilia/typing/asgi.py` | TypedDict |  |
| `ASGIApplication` | `aquilia/typing/asgi.py` | Protocol |  |
| `ConfigSource` | `aquilia/typing/config.py` | Protocol | Protocol for configuration sources that can be converted to dict. |
| `EnvResolvable` | `aquilia/typing/config.py` | Protocol | Protocol for values that resolve from environment variables. |
| `SecretRevealable` | `aquilia/typing/config.py` | Protocol | Protocol for secret values that can be revealed. |
| `ConfigSection` | `aquilia/typing/config.py` | Protocol | Protocol for config section classes. |
| `SyncResolvableContainer` | `aquilia/typing/container.py` | Protocol |  |
| `AsyncResolvableContainer` | `aquilia/typing/container.py` | Protocol |  |
| `StartupContainer` | `aquilia/typing/container.py` | Protocol |  |
| `ShutdownContainer` | `aquilia/typing/container.py` | Protocol |  |
| `RequestScopeFactory` | `aquilia/typing/container.py` | Protocol |  |
| `RequestContainer` | `aquilia/typing/container.py` | AsyncResolvableContainer, SyncResolvableContainer, ShutdownContainer, Protocol |  |
| `AppContainer` | `aquilia/typing/container.py` | AsyncResolvableContainer, SyncResolvableContainer, StartupContainer, ShutdownContainer, RequestScopeFactory, Protocol |  |
| `ControllerRouteMatchLike` | `aquilia/typing/controller.py` | Protocol |  |
| `EffectProviderProtocol` | `aquilia/typing/effects.py` | Protocol[EffectResourceT] |  |
| `ManifestDescriptor` | `aquilia/typing/manifest.py` | object |  |
| `ManifestLike` | `aquilia/typing/manifest.py` | Protocol |  |
| `MiddlewareProtocol` | `aquilia/typing/middleware.py` | Protocol |  |

## Constants And Module Flags

| Name | Source | Value or Type |
| --- | --- | --- |
| `T` | `aquilia/typing/config.py` | `TypeVar('T')` |
| `T` | `aquilia/typing/container.py` | `TypeVar('T')` |

## Detailed Classes And Methods

### `HTTPScope`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `type` | `Literal['http']` | `` |
| `asgi` | `ASGIVersionInfo` | `` |
| `http_version` | `str` | `` |
| `method` | `str` | `` |
| `scheme` | `str` | `` |
| `path` | `str` | `` |
| `raw_path` | `bytes` | `` |
| `root_path` | `str` | `` |
| `query_string` | `bytes` | `` |
| `headers` | `RawHeaderList` | `` |
| `client` | `ASGIClientAddress` | `` |
| `server` | `ASGIServerAddress` | `` |
| `state` | `dict[str, object]` | `` |

### `WebSocketScope`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `type` | `Literal['websocket']` | `` |
| `asgi` | `ASGIVersionInfo` | `` |
| `http_version` | `str` | `` |
| `scheme` | `str` | `` |
| `path` | `str` | `` |
| `raw_path` | `bytes` | `` |
| `root_path` | `str` | `` |
| `query_string` | `bytes` | `` |
| `headers` | `RawHeaderList` | `` |
| `client` | `ASGIClientAddress` | `` |
| `server` | `ASGIServerAddress` | `` |
| `subprotocols` | `list[str]` | `` |
| `state` | `dict[str, object]` | `` |

### `LifespanScope`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `type` | `Literal['lifespan']` | `` |
| `asgi` | `ASGIVersionInfo` | `` |
| `state` | `dict[str, object]` | `` |

### `HTTPRequestEvent`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `type` | `Literal['http.request']` | `` |
| `body` | `bytes` | `` |
| `more_body` | `bool` | `` |

### `HTTPDisconnectEvent`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `type` | `Literal['http.disconnect']` | `` |

### `HTTPResponseStartEvent`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `type` | `Literal['http.response.start']` | `` |
| `status` | `int` | `` |
| `headers` | `RawHeaderList` | `` |
| `trailers` | `bool` | `` |

### `HTTPResponseBodyEvent`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `type` | `Literal['http.response.body']` | `` |
| `body` | `bytes` | `` |
| `more_body` | `bool` | `` |

### `HTTPResponseTrailersEvent`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `type` | `Literal['http.response.trailers']` | `` |
| `headers` | `RawHeaderList` | `` |
| `more_trailers` | `bool` | `` |

### `WebSocketConnectEvent`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `type` | `Literal['websocket.connect']` | `` |

### `WebSocketReceiveEvent`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `type` | `Literal['websocket.receive']` | `` |
| `bytes` | `bytes` | `` |
| `text` | `str` | `` |

### `WebSocketDisconnectEvent`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `type` | `Literal['websocket.disconnect']` | `` |
| `code` | `int` | `` |
| `reason` | `str` | `` |

### `WebSocketAcceptEvent`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `type` | `Literal['websocket.accept']` | `` |
| `subprotocol` | `str` | `` |
| `headers` | `RawHeaderList` | `` |

### `WebSocketSendEvent`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `type` | `Literal['websocket.send']` | `` |
| `bytes` | `bytes` | `` |
| `text` | `str` | `` |

### `WebSocketCloseEvent`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `type` | `Literal['websocket.close']` | `` |
| `code` | `int` | `` |
| `reason` | `str` | `` |

### `LifespanStartupEvent`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `type` | `Literal['lifespan.startup']` | `` |

### `LifespanShutdownEvent`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `type` | `Literal['lifespan.shutdown']` | `` |

### `LifespanStartupCompleteEvent`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `type` | `Literal['lifespan.startup.complete']` | `` |

### `LifespanStartupFailedEvent`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `type` | `Literal['lifespan.startup.failed']` | `` |
| `message` | `str` | `` |

### `LifespanShutdownCompleteEvent`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `type` | `Literal['lifespan.shutdown.complete']` | `` |

### `LifespanShutdownFailedEvent`

- Source: `aquilia/typing/asgi.py`
- Bases: `TypedDict`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `type` | `Literal['lifespan.shutdown.failed']` | `` |
| `message` | `str` | `` |

### `ASGIApplication`

- Source: `aquilia/typing/asgi.py`
- Bases: `Protocol`

### `ConfigSource`

- Source: `aquilia/typing/config.py`
- Bases: `Protocol`
- Summary: Protocol for configuration sources that can be converted to dict.
- Decorators: `runtime_checkable`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` | Convert this config source to a dictionary. |

### `EnvResolvable`

- Source: `aquilia/typing/config.py`
- Bases: `Protocol`
- Summary: Protocol for values that resolve from environment variables.
- Decorators: `runtime_checkable`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `resolve` | `def resolve(self)` | Resolve the value from the environment. |

### `SecretRevealable`

- Source: `aquilia/typing/config.py`
- Bases: `Protocol`
- Summary: Protocol for secret values that can be revealed.
- Decorators: `runtime_checkable`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `reveal` | `def reveal(self)` | Reveal the secret value. |

### `ConfigSection`

- Source: `aquilia/typing/config.py`
- Bases: `Protocol`
- Summary: Protocol for config section classes.
- Decorators: `runtime_checkable`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(cls)` | Convert this section to a dictionary. |

### `SyncResolvableContainer`

- Source: `aquilia/typing/container.py`
- Bases: `Protocol`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `resolve` | `def resolve(self, name: DIName, optional: DIOptionalFlag=False)` |  |

### `AsyncResolvableContainer`

- Source: `aquilia/typing/container.py`
- Bases: `Protocol`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `resolve_async` | `async def resolve_async(self, name: DIName, optional: DIOptionalFlag=False)` |  |

### `StartupContainer`

- Source: `aquilia/typing/container.py`
- Bases: `Protocol`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `startup` | `async def startup(self)` |  |

### `ShutdownContainer`

- Source: `aquilia/typing/container.py`
- Bases: `Protocol`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `shutdown` | `async def shutdown(self)` |  |

### `RequestScopeFactory`

- Source: `aquilia/typing/container.py`
- Bases: `Protocol`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `create_request_scope` | `def create_request_scope(self)` |  |

### `RequestContainer`

- Source: `aquilia/typing/container.py`
- Bases: `AsyncResolvableContainer, SyncResolvableContainer, ShutdownContainer, Protocol`

### `AppContainer`

- Source: `aquilia/typing/container.py`
- Bases: `AsyncResolvableContainer, SyncResolvableContainer, StartupContainer, ShutdownContainer, RequestScopeFactory, Protocol`

### `ControllerRouteMatchLike`

- Source: `aquilia/typing/controller.py`
- Bases: `Protocol`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `route` | `object` | `` |
| `params` | `RouteParams` | `` |
| `query` | `RouteQuery` | `` |

### `EffectProviderProtocol`

- Source: `aquilia/typing/effects.py`
- Bases: `Protocol[EffectResourceT]`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `initialize` | `async def initialize(self)` |  |
| `acquire` | `async def acquire(self, mode: str \| None=None)` |  |
| `release` | `async def release(self, resource: EffectResourceT, success: bool=True)` |  |
| `finalize` | `async def finalize(self)` |  |

### `ManifestDescriptor`

- Source: `aquilia/typing/manifest.py`
- Bases: `object`
- Decorators: `dataclass(frozen=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `ManifestName` | `` |
| `module` | `ModuleName` | `` |
| `class_path` | `ClassPath` | `` |

### `ManifestLike`

- Source: `aquilia/typing/manifest.py`
- Bases: `Protocol`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |

### `MiddlewareProtocol`

- Source: `aquilia/typing/middleware.py`
- Bases: `Protocol`
