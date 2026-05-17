# Discovery Architecture

## Runtime Role

The AST-based scanner and manifest sync tooling used to find controllers, services, middleware, models, tasks, and other module components.

The implementation is split across 2 Python files. The module boundary is visible in the file inventory below and the API reference is generated from the same source files.

## Primary Source Files

- `aquilia/discovery/__init__.py`: Aquilia Discovery - Component auto-discovery subsystem.
- `aquilia/discovery/engine.py`: Auto-Discovery Engine -- AST-based component classification and manifest sync.

## Internal Dependency Shape

The table below is derived from import statements in the module. It shows which top-level packages this module depends on most often.

| Imported package | Import count |
| --- | --- |
| `__future__` | 1 |
| `aquilia` | 1 |
| `ast` | 1 |
| `dataclasses` | 1 |
| `engine` | 1 |
| `logging` | 1 |
| `manifest` | 1 |
| `pathlib` | 1 |
| `re` | 1 |

## Data And Control Flow

1. Configuration or direct construction creates the public service objects, controllers, providers, or helpers for this module.
2. Runtime code imports the registered classes from manifests, workspace integrations, middleware stacks, or direct application code.
3. Public methods perform validation and convert invalid states into typed Aquilia faults where the implementation defines fault classes.
4. Integration points return Python data structures, `Response` objects, provider results, jobs, sessions, connections, or model instances depending on the subsystem.

## Boundary Rules

- Keep application-specific business decisions outside framework classes unless the class is explicitly a service or controller owned by your app.
- Prefer the public exports and typed configuration dataclasses shown in `api-reference.md`.
- When a module supplies both a low-level primitive and a high-level service, use the service in application code and keep primitives for tests, providers, or advanced integrations.
