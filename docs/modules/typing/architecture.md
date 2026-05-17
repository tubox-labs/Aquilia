# Typing Contracts Architecture

## Runtime Role

Shared type aliases and protocols for ASGI, config, containers, controllers, request state, effects, manifests, middleware, and JSON-like values.

The implementation is split across 10 Python files. The module boundary is visible in the file inventory below and the API reference is generated from the same source files.

## Primary Source Files

- `aquilia/typing/__init__.py`: Implementation file.
- `aquilia/typing/asgi.py`: Implementation file.
- `aquilia/typing/common.py`: Implementation file.
- `aquilia/typing/config.py`: Configuration type definitions for Aquilia.
- `aquilia/typing/container.py`: Implementation file.
- `aquilia/typing/controller.py`: Implementation file.
- `aquilia/typing/effects.py`: Implementation file.
- `aquilia/typing/manifest.py`: Implementation file.
- `aquilia/typing/middleware.py`: Implementation file.
- `aquilia/typing/request_state.py`: Implementation file.

## Internal Dependency Shape

The table below is derived from import statements in the module. It shows which top-level packages this module depends on most often.

| Imported package | Import count |
| --- | --- |
| `__future__` | 9 |
| `typing` | 9 |
| `collections` | 6 |
| `common` | 4 |
| `asgi` | 1 |
| `config` | 1 |
| `container` | 1 |
| `controller` | 1 |
| `dataclasses` | 1 |
| `datetime` | 1 |
| `effects` | 1 |
| `manifest` | 1 |
| `middleware` | 1 |
| `pathlib` | 1 |
| `request_state` | 1 |

## Data And Control Flow

1. Configuration or direct construction creates the public service objects, controllers, providers, or helpers for this module.
2. Runtime code imports the registered classes from manifests, workspace integrations, middleware stacks, or direct application code.
3. Public methods perform validation and convert invalid states into typed Aquilia faults where the implementation defines fault classes.
4. Integration points return Python data structures, `Response` objects, provider results, jobs, sessions, connections, or model instances depending on the subsystem.

## Boundary Rules

- Keep application-specific business decisions outside framework classes unless the class is explicitly a service or controller owned by your app.
- Prefer the public exports and typed configuration dataclasses shown in `api-reference.md`.
- When a module supplies both a low-level primitive and a high-level service, use the service in application code and keep primitives for tests, providers, or advanced integrations.
