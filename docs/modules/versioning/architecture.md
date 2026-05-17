# Versioning Architecture

## Runtime Role

The API versioning subsystem with decorators, parsers, semantic versions, negotiation, resolvers, middleware, sunset policies, and version graph checks.

The implementation is split across 11 Python files. The module boundary is visible in the file inventory below and the API reference is generated from the same source files.

## Primary Source Files

- `aquilia/versioning/__init__.py`: Aquilia Versioning System - Epoch-Based API Versioning
- `aquilia/versioning/core.py`: Aquilia Versioning - Core Types
- `aquilia/versioning/decorators.py`: Aquilia Versioning - Route-Level Decorators
- `aquilia/versioning/errors.py`: Aquilia Versioning - Version Errors
- `aquilia/versioning/graph.py`: Aquilia Versioning - Version Graph
- `aquilia/versioning/middleware.py`: Aquilia Versioning - Version Middleware
- `aquilia/versioning/negotiation.py`: Aquilia Versioning - Version Negotiation
- `aquilia/versioning/parser.py`: Aquilia Versioning - Version Parser
- `aquilia/versioning/resolvers.py`: Aquilia Versioning - Version Resolvers
- `aquilia/versioning/strategy.py`: Aquilia Versioning - Version Strategy
- `aquilia/versioning/sunset.py`: Aquilia Versioning - Sunset Lifecycle

## Internal Dependency Shape

The table below is derived from import statements in the module. It shows which top-level packages this module depends on most often.

| Imported package | Import count |
| --- | --- |
| `__future__` | 10 |
| `typing` | 9 |
| `core` | 7 |
| `errors` | 5 |
| `dataclasses` | 4 |
| `datetime` | 3 |
| `abc` | 2 |
| `collections` | 2 |
| `enum` | 2 |
| `graph` | 2 |
| `negotiation` | 2 |
| `parser` | 2 |
| `re` | 2 |
| `resolvers` | 2 |
| `strategy` | 2 |
| `sunset` | 2 |
| `decorators` | 1 |
| `faults` | 1 |
| `functools` | 1 |
| `logging` | 1 |
| `middleware` | 1 |

## Data And Control Flow

1. Configuration or direct construction creates the public service objects, controllers, providers, or helpers for this module.
2. Runtime code imports the registered classes from manifests, workspace integrations, middleware stacks, or direct application code.
3. Public methods perform validation and convert invalid states into typed Aquilia faults where the implementation defines fault classes.
4. Integration points return Python data structures, `Response` objects, provider results, jobs, sessions, connections, or model instances depending on the subsystem.

## Boundary Rules

- Keep application-specific business decisions outside framework classes unless the class is explicitly a service or controller owned by your app.
- Prefer the public exports and typed configuration dataclasses shown in `api-reference.md`.
- When a module supplies both a low-level primitive and a high-level service, use the service in application code and keep primitives for tests, providers, or advanced integrations.
