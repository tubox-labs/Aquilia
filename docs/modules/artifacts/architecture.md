# Artifacts Architecture

## Runtime Role

The typed artifact system used for route, registry, migration, template, model, config, code, and graph artifacts with envelope and integrity metadata.

The implementation is split across 6 Python files. The module boundary is visible in the file inventory below and the API reference is generated from the same source files.

## Primary Source Files

- `aquilia/artifacts/__init__.py`: Aquilia Artifacts -- Unified artifact system for the framework.
- `aquilia/artifacts/builder.py`: Artifact Builder -- fluent API for constructing artifacts.
- `aquilia/artifacts/core.py`: Artifact Core -- the foundational types for Aquilia's artifact system.
- `aquilia/artifacts/kinds.py`: Typed Artifact Kinds -- convenience subclasses with kind-specific helpers.
- `aquilia/artifacts/reader.py`: Artifact Reader -- load, inspect, verify, and query artifacts.
- `aquilia/artifacts/store.py`: Artifact Store -- pluggable storage backends for artifacts.

## Internal Dependency Shape

The table below is derived from import statements in the module. It shows which top-level packages this module depends on most often.

| Imported package | Import count |
| --- | --- |
| `__future__` | 5 |
| `core` | 5 |
| `json` | 4 |
| `typing` | 4 |
| `builder` | 2 |
| `logging` | 2 |
| `store` | 2 |
| `aquilia` | 1 |
| `dataclasses` | 1 |
| `datetime` | 1 |
| `enum` | 1 |
| `hashlib` | 1 |
| `kinds` | 1 |
| `pathlib` | 1 |
| `reader` | 1 |
| `subprocess` | 1 |

## Data And Control Flow

1. Configuration or direct construction creates the public service objects, controllers, providers, or helpers for this module.
2. Runtime code imports the registered classes from manifests, workspace integrations, middleware stacks, or direct application code.
3. Public methods perform validation and convert invalid states into typed Aquilia faults where the implementation defines fault classes.
4. Integration points return Python data structures, `Response` objects, provider results, jobs, sessions, connections, or model instances depending on the subsystem.

## Boundary Rules

- Keep application-specific business decisions outside framework classes unless the class is explicitly a service or controller owned by your app.
- Prefer the public exports and typed configuration dataclasses shown in `api-reference.md`.
- When a module supplies both a low-level primitive and a high-level service, use the service in application code and keep primitives for tests, providers, or advanced integrations.
