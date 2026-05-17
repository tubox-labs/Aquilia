# Faults Architecture

## Runtime Role

The structured fault system with domains, severity, recovery strategies, handlers, adapters, and typed subsystem errors.

The implementation is split across 12 Python files. The module boundary is visible in the file inventory below and the API reference is generated from the same source files.

## Primary Source Files

- `aquilia/faults/__init__.py`: AquilaFaults - Production-grade fault handling system.
- `aquilia/faults/core.py`: AquilaFaults - Core types and fault taxonomy.
- `aquilia/faults/default_handlers.py`: AquilaFaults - Default Handlers.
- `aquilia/faults/domains.py`: AquilaFaults - Domain-specific fault types.
- `aquilia/faults/engine.py`: AquilaFaults - Fault Engine.
- `aquilia/faults/handlers.py`: AquilaFaults - Fault handlers.
- `aquilia/faults/integrations/__init__.py`: AquilaFaults - Subsystem Integrations.
- `aquilia/faults/integrations/di.py`: AquilaFaults - DI Integration.
- `aquilia/faults/integrations/flow.py`: AquilaFaults - Flow Engine Integration.
- `aquilia/faults/integrations/models.py`: AquilaFaults - Model/Database Integration.
- `aquilia/faults/integrations/registry.py`: AquilaFaults - Registry Integration.
- `aquilia/faults/integrations/routing.py`: AquilaFaults - Routing Integration.

## Internal Dependency Shape

The table below is derived from import statements in the module. It shows which top-level packages this module depends on most often.

| Imported package | Import count |
| --- | --- |
| `aquilia` | 8 |
| `core` | 6 |
| `typing` | 6 |
| `__future__` | 5 |
| `collections` | 4 |
| `domains` | 4 |
| `handlers` | 4 |
| `asyncio` | 3 |
| `logging` | 3 |
| `dataclasses` | 2 |
| `abc` | 1 |
| `contextvars` | 1 |
| `datetime` | 1 |
| `default_handlers` | 1 |
| `di` | 1 |
| `engine` | 1 |
| `enum` | 1 |
| `hashlib` | 1 |
| `inspect` | 1 |
| `models` | 1 |
| `registry` | 1 |
| `routing` | 1 |
| `sys` | 1 |
| `time` | 1 |
| `traceback` | 1 |

## Data And Control Flow

1. Configuration or direct construction creates the public service objects, controllers, providers, or helpers for this module.
2. Runtime code imports the registered classes from manifests, workspace integrations, middleware stacks, or direct application code.
3. Public methods perform validation and convert invalid states into typed Aquilia faults where the implementation defines fault classes.
4. Integration points return Python data structures, `Response` objects, provider results, jobs, sessions, connections, or model instances depending on the subsystem.

## Boundary Rules

- Keep application-specific business decisions outside framework classes unless the class is explicitly a service or controller owned by your app.
- Prefer the public exports and typed configuration dataclasses shown in `api-reference.md`.
- When a module supplies both a low-level primitive and a high-level service, use the service in application code and keep primitives for tests, providers, or advanced integrations.
