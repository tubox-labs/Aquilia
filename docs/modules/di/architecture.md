# Dependency Injection Architecture

## Runtime Role

The scoped dependency injection container, provider model, lifecycle disposal, dependency graph, request DAG, and testing overrides.

The implementation is split across 14 Python files. The module boundary is visible in the file inventory below and the API reference is generated from the same source files.

## Primary Source Files

- `aquilia/di/__init__.py`: Aquilia Dependency Injection System
- `aquilia/di/cli.py`: CLI commands for DI system.
- `aquilia/di/compat.py`: Compatibility layer with legacy Aquilia DI system.
- `aquilia/di/core.py`: Core DI types and protocols.
- `aquilia/di/decorators.py`: Decorators and injection helpers for ergonomic DI usage.
- `aquilia/di/dep.py`: Dep -- Composable dependency descriptor for annotation-driven DI.
- `aquilia/di/diagnostics.py`: DI Diagnostics - Observability and event tracking for DI containers.
- `aquilia/di/errors.py`: DI-specific error types with rich diagnostics.
- `aquilia/di/graph.py`: Graph analysis and cycle detection for DI system.
- `aquilia/di/lifecycle.py`: Lifecycle management for providers and containers.
- `aquilia/di/providers.py`: Provider implementations for different instantiation strategies.
- `aquilia/di/request_dag.py`: RequestDAG -- Per-request dependency graph resolver.
- `aquilia/di/scopes.py`: Scope definitions and validation.
- `aquilia/di/testing.py`: Testing utilities for DI system.

## Internal Dependency Shape

The table below is derived from import statements in the module. It shows which top-level packages this module depends on most often.

| Imported package | Import count |
| --- | --- |
| `typing` | 11 |
| `collections` | 7 |
| `dataclasses` | 6 |
| `asyncio` | 5 |
| `core` | 5 |
| `errors` | 4 |
| `inspect` | 4 |
| `contextlib` | 3 |
| `enum` | 3 |
| `logging` | 3 |
| `__future__` | 2 |
| `dep` | 2 |
| `providers` | 2 |
| `sys` | 2 |
| `time` | 2 |
| `aquilia` | 1 |
| `compat` | 1 |
| `contextvars` | 1 |
| `decorators` | 1 |
| `functools` | 1 |
| `graph` | 1 |
| `json` | 1 |
| `lifecycle` | 1 |
| `pathlib` | 1 |
| `request_dag` | 1 |
| `scopes` | 1 |
| `testing` | 1 |
| `types` | 1 |

## Data And Control Flow

1. Configuration or direct construction creates the public service objects, controllers, providers, or helpers for this module.
2. Runtime code imports the registered classes from manifests, workspace integrations, middleware stacks, or direct application code.
3. Public methods perform validation and convert invalid states into typed Aquilia faults where the implementation defines fault classes.
4. Integration points return Python data structures, `Response` objects, provider results, jobs, sessions, connections, or model instances depending on the subsystem.

## Boundary Rules

- Keep application-specific business decisions outside framework classes unless the class is explicitly a service or controller owned by your app.
- Prefer the public exports and typed configuration dataclasses shown in `api-reference.md`.
- When a module supplies both a low-level primitive and a high-level service, use the service in application code and keep primitives for tests, providers, or advanced integrations.
