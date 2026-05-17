# WebSockets Edge Cases And Limitations

## Fault And Error Types

The following error-oriented classes are present in the implementation and should guide defensive usage.

| Type | Source | Meaning |
| --- | --- | --- |
| `SocketFault` | `aquilia/sockets/faults.py` | Base fault for WebSocket operations. |

## Common Edge Cases

- Optional dependencies may change behavior. Check imports and constructor docs before enabling production features.
- In-memory stores, queues, caches, adapters, and registries are usually process-local. Use durable backends when state must survive restarts or scale across workers.
- Request-scoped data must not be cached globally. Use request state, DI request scopes, or explicit parameters.
- Decorators in Aquilia generally attach metadata at import time. Runtime behavior happens later during compilation, routing, middleware execution, or service startup.
- Many subsystems intentionally convert invalid states into typed faults. Catch the specific fault type when application code can recover.

## Source-Level Limits To Review

Review these files before changing behavior:

- `aquilia/sockets/__init__.py`: AquilaSockets - WebSocket subsystem for Aquilia
- `aquilia/sockets/adapters/__init__.py`: Adapters Package - WebSocket scaling adapters
- `aquilia/sockets/adapters/base.py`: Adapter Base - Protocol for WebSocket scaling adapters
- `aquilia/sockets/adapters/inmemory.py`: In-Memory Adapter - Single-process WebSocket adapter
- `aquilia/sockets/adapters/redis.py`: Redis Adapter - Production-ready WebSocket adapter using Redis
- `aquilia/sockets/compile.py`: WebSocket Compiler - Compile-time metadata extraction
- `aquilia/sockets/connection.py`: Connection - WebSocket connection abstraction with DI scope
- `aquilia/sockets/controller.py`: Socket Controller - Base class for WebSocket controllers
- `aquilia/sockets/decorators.py`: Socket Controller Decorators - Declarative WebSocket controller syntax
- `aquilia/sockets/envelope.py`: Message Envelope - Typed message protocol for WebSocket communication
- `aquilia/sockets/faults.py`: WebSocket Faults - Structured error handling for WebSocket operations
- `aquilia/sockets/guards.py`: WebSocket Guards - Security and validation guards
- `aquilia/sockets/middleware.py`: WebSocket Middleware - Per-message processing pipeline
- `aquilia/sockets/runtime.py`: WebSocket Runtime - ASGI integration and connection management
