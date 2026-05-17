# Controllers Architecture

## Runtime Role

The HTTP controller system with route decorators, compiler, router, factory, engine, filters, pagination, renderers, throttles, interceptors, exception filters, and OpenAPI generation.

The implementation is split across 12 Python files. The module boundary is visible in the file inventory below and the API reference is generated from the same source files.

## Primary Source Files

- `aquilia/controller/__init__.py`: Aquilia Controller System
- `aquilia/controller/base.py`: Controller Base Class
- `aquilia/controller/compiler.py`: Controller Compiler - Compiles controllers to patterns and routes.
- `aquilia/controller/decorators.py`: Controller Method Decorators
- `aquilia/controller/engine.py`: Controller Engine - Executes controller methods with full integration.
- `aquilia/controller/factory.py`: Controller Factory
- `aquilia/controller/filters.py`: Aquilia Filter System -- declarative filtering, searching, and ordering.
- `aquilia/controller/metadata.py`: Controller Metadata Extraction
- `aquilia/controller/openapi.py`: OpenAPI 3.1.0 Generation for Aquilia Controllers.
- `aquilia/controller/pagination.py`: Aquilia Pagination System -- declarative pagination backends.
- `aquilia/controller/renderers.py`: Aquilia Content Negotiation & Renderer System.
- `aquilia/controller/router.py`: Controller Router - Pattern-based router for controllers.

## Internal Dependency Shape

The table below is derived from import statements in the module. It shows which top-level packages this module depends on most often.

| Imported package | Import count |
| --- | --- |
| `typing` | 11 |
| `inspect` | 6 |
| `logging` | 5 |
| `__future__` | 4 |
| `compiler` | 4 |
| `dataclasses` | 4 |
| `patterns` | 3 |
| `aquilia` | 2 |
| `asyncio` | 2 |
| `base` | 2 |
| `collections` | 2 |
| `factory` | 2 |
| `json` | 2 |
| `metadata` | 2 |
| `re` | 2 |
| `router` | 2 |
| `base64` | 1 |
| `contextlib` | 1 |
| `contextvars` | 1 |
| `datetime` | 1 |
| `decorators` | 1 |
| `di` | 1 |
| `engine` | 1 |
| `enum` | 1 |
| `filters` | 1 |
| `hashlib` | 1 |
| `hmac` | 1 |
| `html` | 1 |
| `math` | 1 |
| `openapi` | 1 |

## Data And Control Flow

1. Configuration or direct construction creates the public service objects, controllers, providers, or helpers for this module.
2. Runtime code imports the registered classes from manifests, workspace integrations, middleware stacks, or direct application code.
3. Public methods perform validation and convert invalid states into typed Aquilia faults where the implementation defines fault classes.
4. Integration points return Python data structures, `Response` objects, provider results, jobs, sessions, connections, or model instances depending on the subsystem.

## Boundary Rules

- Keep application-specific business decisions outside framework classes unless the class is explicitly a service or controller owned by your app.
- Prefer the public exports and typed configuration dataclasses shown in `api-reference.md`.
- When a module supplies both a low-level primitive and a high-level service, use the service in application code and keep primitives for tests, providers, or advanced integrations.
