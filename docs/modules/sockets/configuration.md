# Sockets Configuration

WebSocket decorators, controllers, runtime, connection state, guards, middleware, message envelopes, compile metadata, and in-memory/Redis adapters.

This page distinguishes direct configuration APIs from indirect runtime wiring. All class names and source files below are extracted from the current source tree.

## Configuration Model

This module exposes config-oriented public classes. Use the table below to locate exact constructors and `to_dict()` behavior in `api-reference.md`.

## Source Inventory

| File | Lines | Public classes | Public functions | Purpose |
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

## Detected Config-Oriented Classes

| Class | Source | Methods | Summary |
| --- | --- | --- | --- |
| `MessageValidationMiddleware` | `aquilia/sockets/middleware.py` |  | Message validation middleware. |
| `RateLimitMiddleware` | `aquilia/sockets/middleware.py` |  | Rate limiting middleware. |
| `LoggingMiddleware` | `aquilia/sockets/middleware.py` |  | Logging middleware. |
| `MetricsMiddleware` | `aquilia/sockets/middleware.py` |  | Metrics collection middleware. |
| `MiddlewareChain` | `aquilia/sockets/middleware.py` | `add`, `build` | Middleware chain builder. |

## Runtime Wiring Paths

- `workspace.py` defines workspace-level structure with `Workspace`, `Module`, and `Integration` builders.
- `modules/<name>/manifest.py` defines module internals with `AppManifest`.
- `ConfigLoader.get(...)` resolves dotted configuration paths at runtime.
- `AquiliaServer` consumes resolved config during middleware and subsystem setup.
- Subsystems with optional providers only require optional dependencies when their backend/provider is configured.

## Verification Checklist

1. Run `aq validate` to verify manifests.
2. Run `aq inspect config` to inspect resolved configuration.
3. Run `aq doctor` for workspace and integration diagnostics.
4. For server-only wiring, start via `aq run` and check startup logs plus `GET /_health`.

## Related Pages

- `api-reference.md` for exact class fields, methods, constants, and signatures.
- `integration-guide.md` for the workspace/manifest wiring pattern.
- `edge-cases-and-limitations.md` for fallback and compatibility behavior.
