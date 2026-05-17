# Sockets Architecture

WebSocket decorators, controllers, runtime, connection state, guards, middleware, message envelopes, compile metadata, and in-memory/Redis adapters.

## Source Boundaries

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

## Internal Shape

`sockets` has 14 Python files, 41 public classes, 18 public module-level functions, and 3 constants or module flags detected by AST.

## Runtime Responsibilities

- This module has `aq` command coverage documented in `cli-reference.md`; 5 commands map to this subsystem.

## Internal Imports

| Import | Count |
| --- | ---: |
| `.envelope` | 4 |
| `..envelope` | 3 |
| `.base` | 3 |
| `.controller` | 3 |
| `.faults` | 3 |
| `.adapters` | 2 |
| `.connection` | 2 |
| `.guards` | 2 |
| `aquilia.faults` | 2 |
| `.decorators` | 1 |
| `.inmemory` | 1 |
| `.middleware` | 1 |
| `.redis` | 1 |
| `.runtime` | 1 |
| `aquilia._version` | 1 |
| `aquilia.auth.core` | 1 |
| `aquilia.sessions.core` | 1 |

## External And Stdlib Imports

| Import root | Count |
| --- | ---: |
| `__future__` | 10 |
| `typing` | 9 |
| `logging` | 8 |
| `dataclasses` | 5 |
| `collections` | 4 |
| `json` | 3 |
| `asyncio` | 2 |
| `contextlib` | 2 |
| `datetime` | 2 |
| `enum` | 2 |
| `uuid` | 2 |
| `inspect` | 1 |
| `os` | 1 |
| `pathlib` | 1 |

## Lifecycle And Extension Points

| Extension Type | Source | Role |
| --- | --- | --- |
| `Adapter` | `aquilia/sockets/adapters/base.py` | Adapter protocol for WebSocket scaling. |
| `InMemoryAdapter` | `aquilia/sockets/adapters/inmemory.py` | In-memory adapter for single-process deployments. |
| `RedisAdapter` | `aquilia/sockets/adapters/redis.py` | Redis-backed adapter for multi-worker deployments. |
| `SocketControllerMetadata` | `aquilia/sockets/compile.py` | Compiled controller metadata. |
| `SocketCompiler` | `aquilia/sockets/compile.py` | Compiler for WebSocket controllers. |
| `SocketController` | `aquilia/sockets/controller.py` | Base class for WebSocket controllers. |
| `Guard` | `aquilia/sockets/decorators.py` | Guard decorator for WebSocket handlers. |
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
| `SocketRouter` | `aquilia/sockets/runtime.py` | Router for WebSocket namespaces. |

## Error Handling

Fault/error classes defined here:

`SocketFault`
