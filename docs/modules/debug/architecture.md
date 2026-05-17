# Debug Pages Architecture

## Runtime Role

Development-mode HTML pages for welcome, HTTP errors, version errors, and exception diagnostics.

The implementation is split across 2 Python files. The module boundary is visible in the file inventory below and the API reference is generated from the same source files.

## Primary Source Files

- `aquilia/debug/__init__.py`: Aquilia Debug - Beautiful development-mode error and welcome pages.
- `aquilia/debug/pages.py`: Aquilia Debug Pages -- Tubox Themed (Premium).

## Internal Dependency Shape

The table below is derived from import statements in the module. It shows which top-level packages this module depends on most often.

| Imported package | Import count |
| --- | --- |
| `__future__` | 1 |
| `html` | 1 |
| `linecache` | 1 |
| `logging` | 1 |
| `os` | 1 |
| `pages` | 1 |
| `traceback` | 1 |
| `typing` | 1 |

## Data And Control Flow

1. Configuration or direct construction creates the public service objects, controllers, providers, or helpers for this module.
2. Runtime code imports the registered classes from manifests, workspace integrations, middleware stacks, or direct application code.
3. Public methods perform validation and convert invalid states into typed Aquilia faults where the implementation defines fault classes.
4. Integration points return Python data structures, `Response` objects, provider results, jobs, sessions, connections, or model instances depending on the subsystem.

## Boundary Rules

- Keep application-specific business decisions outside framework classes unless the class is explicitly a service or controller owned by your app.
- Prefer the public exports and typed configuration dataclasses shown in `api-reference.md`.
- When a module supplies both a low-level primitive and a high-level service, use the service in application code and keep primitives for tests, providers, or advanced integrations.
