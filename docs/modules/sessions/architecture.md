# Sessions Architecture

## Runtime Role

The session subsystem with policy builders, stores, transports, guards, decorators, state objects, session engine, lifecycle rules, and typed session faults.

The implementation is split across 9 Python files. The module boundary is visible in the file inventory below and the API reference is generated from the same source files.

## Primary Source Files

- `aquilia/sessions/__init__.py`: AquilaSessions - Production-grade session management for Aquilia.
- `aquilia/sessions/core.py`: AquilaSessions - Core types.
- `aquilia/sessions/decorators.py`: Unique Session Decorators for Aquilia.
- `aquilia/sessions/engine.py`: AquilaSessions - Session Engine.
- `aquilia/sessions/faults.py`: AquilaSessions - Fault definitions.
- `aquilia/sessions/policy.py`: AquilaSessions - Policy types.
- `aquilia/sessions/state.py`: Typed Session State for Aquilia.
- `aquilia/sessions/store.py`: AquilaSessions - Session storage abstraction.
- `aquilia/sessions/transport.py`: AquilaSessions - Transport adapters.

## Internal Dependency Shape

The table below is derived from import statements in the module. It shows which top-level packages this module depends on most often.

| Imported package | Import count |
| --- | --- |
| `typing` | 7 |
| `__future__` | 5 |
| `datetime` | 5 |
| `core` | 4 |
| `aquilia` | 3 |
| `dataclasses` | 3 |
| `faults` | 3 |
| `collections` | 2 |
| `contextlib` | 2 |
| `hashlib` | 2 |
| `asyncio` | 1 |
| `base64` | 1 |
| `decorators` | 1 |
| `engine` | 1 |
| `enum` | 1 |
| `functools` | 1 |
| `inspect` | 1 |
| `json` | 1 |
| `logging` | 1 |
| `pathlib` | 1 |
| `policy` | 1 |
| `re` | 1 |
| `secrets` | 1 |
| `state` | 1 |
| `store` | 1 |
| `transport` | 1 |

## Data And Control Flow

1. Configuration or direct construction creates the public service objects, controllers, providers, or helpers for this module.
2. Runtime code imports the registered classes from manifests, workspace integrations, middleware stacks, or direct application code.
3. Public methods perform validation and convert invalid states into typed Aquilia faults where the implementation defines fault classes.
4. Integration points return Python data structures, `Response` objects, provider results, jobs, sessions, connections, or model instances depending on the subsystem.

## Boundary Rules

- Keep application-specific business decisions outside framework classes unless the class is explicitly a service or controller owned by your app.
- Prefer the public exports and typed configuration dataclasses shown in `api-reference.md`.
- When a module supplies both a low-level primitive and a high-level service, use the service in application code and keep primitives for tests, providers, or advanced integrations.
