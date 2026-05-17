# Utilities Architecture

## Runtime Role

Small utilities for package scanning, URL path normalization, joining, and data helper objects.

The implementation is split across 4 Python files. The module boundary is visible in the file inventory below and the API reference is generated from the same source files.

## Primary Source Files

- `aquilia/utils/__init__.py`: Aquilia Utils Package
- `aquilia/utils/data.py`: Data Utilities - Provides flexible data structures for the framework.
- `aquilia/utils/scanner.py`: Package Scanner Utility.
- `aquilia/utils/urls.py`: URL Utilities for Aquilia.

## Internal Dependency Shape

The table below is derived from import statements in the module. It shows which top-level packages this module depends on most often.

| Imported package | Import count |
| --- | --- |
| `typing` | 2 |
| `collections` | 1 |
| `importlib` | 1 |
| `inspect` | 1 |
| `logging` | 1 |
| `pkgutil` | 1 |
| `scanner` | 1 |
| `types` | 1 |
| `urls` | 1 |

## Data And Control Flow

1. Configuration or direct construction creates the public service objects, controllers, providers, or helpers for this module.
2. Runtime code imports the registered classes from manifests, workspace integrations, middleware stacks, or direct application code.
3. Public methods perform validation and convert invalid states into typed Aquilia faults where the implementation defines fault classes.
4. Integration points return Python data structures, `Response` objects, provider results, jobs, sessions, connections, or model instances depending on the subsystem.

## Boundary Rules

- Keep application-specific business decisions outside framework classes unless the class is explicitly a service or controller owned by your app.
- Prefer the public exports and typed configuration dataclasses shown in `api-reference.md`.
- When a module supplies both a low-level primitive and a high-level service, use the service in application code and keep primitives for tests, providers, or advanced integrations.
