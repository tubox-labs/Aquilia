# WebSockets Architecture

## Runtime Role

The WebSocket subsystem with socket controllers, connection model, event envelopes, guards, middleware, compiler, runtime dispatcher, rooms, acknowledgements, streams, and adapters.

The implementation is split across 14 Python files. The module boundary is visible in the file inventory below and the API reference is generated from the same source files.

## Primary Source Files

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

## Internal Dependency Shape

The table below is derived from import statements in the module. It shows which top-level packages this module depends on most often.

| Imported package | Import count |
| --- | --- |
| `__future__` | 10 |
| `typing` | 9 |
| `logging` | 8 |
| `envelope` | 7 |
| `aquilia` | 5 |
| `dataclasses` | 5 |
| `collections` | 4 |
| `base` | 3 |
| `controller` | 3 |
| `faults` | 3 |
| `json` | 3 |
| `adapters` | 2 |
| `asyncio` | 2 |
| `connection` | 2 |
| `contextlib` | 2 |
| `datetime` | 2 |
| `enum` | 2 |
| `guards` | 2 |
| `uuid` | 2 |
| `decorators` | 1 |
| `inmemory` | 1 |
| `inspect` | 1 |
| `middleware` | 1 |
| `os` | 1 |
| `pathlib` | 1 |
| `redis` | 1 |
| `runtime` | 1 |

## Data And Control Flow

1. Configuration or direct construction creates the public service objects, controllers, providers, or helpers for this module.
2. Runtime code imports the registered classes from manifests, workspace integrations, middleware stacks, or direct application code.
3. Public methods perform validation and convert invalid states into typed Aquilia faults where the implementation defines fault classes.
4. Integration points return Python data structures, `Response` objects, provider results, jobs, sessions, connections, or model instances depending on the subsystem.

## Boundary Rules

- Keep application-specific business decisions outside framework classes unless the class is explicitly a service or controller owned by your app.
- Prefer the public exports and typed configuration dataclasses shown in `api-reference.md`.
- When a module supplies both a low-level primitive and a high-level service, use the service in application code and keep primitives for tests, providers, or advanced integrations.
