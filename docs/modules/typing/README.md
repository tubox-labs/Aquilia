# typing Module

## Purpose

Shared framework protocols and aliases. Use this module for ASGI, controller, config, container, manifest, middleware, effects, and common JSON typing contracts.

## Source Coverage

- Python files: 10
- Public classes: 37
- Dataclasses: 1
- Enums: 0
- Public functions: 0

## How It Fits In Aquilia

1. Import the package from `aquilia.typing` or its concrete submodules.
2. Configure it through workspace integrations, manifests, or direct service construction depending on the subsystem.
3. Keep business logic outside transport and framework glue so the subsystem stays testable.

## Practical Guidance

- Prefer typed configuration objects and framework helpers over ad hoc dictionaries when they exist.
- Use the tests in `tests/` as behavioral examples when changing this subsystem.

## Public Classes

| Name | Source | Role |
| --- | --- | --- |
| `HTTPScope` | `aquilia/typing/asgi.py` | Public class. |
| `WebSocketScope` | `aquilia/typing/asgi.py` | Public class. |
| `LifespanScope` | `aquilia/typing/asgi.py` | Public class. |
| `HTTPRequestEvent` | `aquilia/typing/asgi.py` | Public class. |
| `HTTPDisconnectEvent` | `aquilia/typing/asgi.py` | Public class. |
| `HTTPResponseStartEvent` | `aquilia/typing/asgi.py` | Public class. |
| `HTTPResponseBodyEvent` | `aquilia/typing/asgi.py` | Public class. |
| `HTTPResponseTrailersEvent` | `aquilia/typing/asgi.py` | Public class. |
| `WebSocketConnectEvent` | `aquilia/typing/asgi.py` | Public class. |
| `WebSocketReceiveEvent` | `aquilia/typing/asgi.py` | Public class. |
| `WebSocketDisconnectEvent` | `aquilia/typing/asgi.py` | Public class. |
| `WebSocketAcceptEvent` | `aquilia/typing/asgi.py` | Public class. |
| `WebSocketSendEvent` | `aquilia/typing/asgi.py` | Public class. |
| `WebSocketCloseEvent` | `aquilia/typing/asgi.py` | Public class. |
| `LifespanStartupEvent` | `aquilia/typing/asgi.py` | Public class. |
| `LifespanShutdownEvent` | `aquilia/typing/asgi.py` | Public class. |
| `LifespanStartupCompleteEvent` | `aquilia/typing/asgi.py` | Public class. |
| `LifespanStartupFailedEvent` | `aquilia/typing/asgi.py` | Public class. |
| `LifespanShutdownCompleteEvent` | `aquilia/typing/asgi.py` | Public class. |
| `LifespanShutdownFailedEvent` | `aquilia/typing/asgi.py` | Public class. |
| `ASGIApplication` | `aquilia/typing/asgi.py` | Public class. |
| `ConfigSource` | `aquilia/typing/config.py` | Protocol for configuration sources that can be converted to dict. |
| `EnvResolvable` | `aquilia/typing/config.py` | Protocol for values that resolve from environment variables. |
| `SecretRevealable` | `aquilia/typing/config.py` | Protocol for secret values that can be revealed. |
| `ConfigSection` | `aquilia/typing/config.py` | Protocol for config section classes. |
| `SyncResolvableContainer` | `aquilia/typing/container.py` | Public class. |
| `AsyncResolvableContainer` | `aquilia/typing/container.py` | Public class. |
| `StartupContainer` | `aquilia/typing/container.py` | Public class. |
| `ShutdownContainer` | `aquilia/typing/container.py` | Public class. |
| `RequestScopeFactory` | `aquilia/typing/container.py` | Public class. |
| `RequestContainer` | `aquilia/typing/container.py` | Public class. |
| `AppContainer` | `aquilia/typing/container.py` | Public class. |
| `ControllerRouteMatchLike` | `aquilia/typing/controller.py` | Public class. |
| `EffectProviderProtocol` | `aquilia/typing/effects.py` | Public class. |
| `ManifestDescriptor` | `aquilia/typing/manifest.py` | Public class. |
| `ManifestLike` | `aquilia/typing/manifest.py` | Public class. |
| `MiddlewareProtocol` | `aquilia/typing/middleware.py` | Public class. |

## Public Functions

| Name | Source | Role |
| --- | --- | --- |
| None detected |  |  |

## Implementation Map

| File | What To Look For |
| --- | --- |
| `aquilia/typing/__init__.py` | Implementation file. |
| `aquilia/typing/asgi.py` | Implementation file. |
| `aquilia/typing/common.py` | Implementation file. |
| `aquilia/typing/config.py` | Configuration type definitions for Aquilia. |
| `aquilia/typing/container.py` | Implementation file. |
| `aquilia/typing/controller.py` | Implementation file. |
| `aquilia/typing/effects.py` | Implementation file. |
| `aquilia/typing/manifest.py` | Implementation file. |
| `aquilia/typing/middleware.py` | Implementation file. |
| `aquilia/typing/request_state.py` | Implementation file. |

## Testing Pointers

Search `tests/` for `typing` to find behavior-level examples. The test suite is especially useful for edge cases because many modules expose lightweight public APIs but enforce important security and lifecycle behavior internally.
