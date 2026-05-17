# Sockets Documentation

WebSocket decorators, controllers, runtime, connection state, guards, middleware, message envelopes, compile metadata, and in-memory/Redis adapters.

## Coverage Snapshot

- Source files: 14
- Source lines: 3687
- Public classes: 41
- Public module functions: 18
- Constants/module flags: 3
- Public exports in `__all__`: 40

## Source Files Read

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

## Document Map

- `architecture.md`: module boundaries, dependencies, lifecycle, and extension points.
- `configuration.md`: configuration classes, builders, server wiring, and precedence.
- `api-reference.md`: source-extracted classes, methods, functions, constants, exports, and signatures.
- `integration-guide.md`: how to wire the module into an Aquilia app.
- `cli-reference.md`: mounted `aq` commands for this module, if any.
- `examples.md`: usage examples derived from source and checked example apps.
- `edge-cases-and-limitations.md`: implementation limits and compatibility behavior.
- `troubleshooting.md`: diagnostic commands and common failure patterns.
