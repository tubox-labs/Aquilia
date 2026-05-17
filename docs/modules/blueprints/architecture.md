# Blueprints Architecture

## Runtime Role

The contract system for casting inbound data, sealing validated values, molding outbound data, projections, lenses, and model imprinting.

The implementation is split across 9 Python files. The module boundary is visible in the file inventory below and the API reference is generated from the same source files.

## Primary Source Files

- `aquilia/blueprints/__init__.py`: Aquilia Blueprints -- first-class model↔world contracts.
- `aquilia/blueprints/annotations.py`: Aquilia Blueprint Annotations -- type-annotation-driven schema declaration.
- `aquilia/blueprints/core.py`: Aquilia Blueprint Core -- the Blueprint metaclass and base class.
- `aquilia/blueprints/exceptions.py`: Aquilia Blueprint Exceptions -- Fault-domain-integrated error hierarchy.
- `aquilia/blueprints/facets.py`: Aquilia Blueprint Facets -- the field-level primitives of a Blueprint.
- `aquilia/blueprints/integration.py`: Aquilia Blueprint Integration -- hooks into Controller, DI, Request/Response.
- `aquilia/blueprints/lenses.py`: Aquilia Blueprint Lenses -- depth-controlled relational views.
- `aquilia/blueprints/projections.py`: Aquilia Blueprint Projections -- named, reusable field subsets.
- `aquilia/blueprints/schema.py`: Aquilia Blueprint Schema -- OpenAPI/JSON Schema generation.

## Internal Dependency Shape

The table below is derived from import statements in the module. It shows which top-level packages this module depends on most often.

| Imported package | Import count |
| --- | --- |
| `__future__` | 8 |
| `typing` | 8 |
| `exceptions` | 7 |
| `facets` | 4 |
| `lenses` | 3 |
| `annotations` | 2 |
| `collections` | 2 |
| `contextlib` | 2 |
| `core` | 2 |
| `datetime` | 2 |
| `decimal` | 2 |
| `projections` | 2 |
| `uuid` | 2 |
| `faults` | 1 |
| `integration` | 1 |
| `re` | 1 |
| `schema` | 1 |
| `sys` | 1 |
| `types` | 1 |
| `utils` | 1 |
| `warnings` | 1 |

## Data And Control Flow

1. Configuration or direct construction creates the public service objects, controllers, providers, or helpers for this module.
2. Runtime code imports the registered classes from manifests, workspace integrations, middleware stacks, or direct application code.
3. Public methods perform validation and convert invalid states into typed Aquilia faults where the implementation defines fault classes.
4. Integration points return Python data structures, `Response` objects, provider results, jobs, sessions, connections, or model instances depending on the subsystem.

## Boundary Rules

- Keep application-specific business decisions outside framework classes unless the class is explicitly a service or controller owned by your app.
- Prefer the public exports and typed configuration dataclasses shown in `api-reference.md`.
- When a module supplies both a low-level primitive and a high-level service, use the service in application code and keep primitives for tests, providers, or advanced integrations.
