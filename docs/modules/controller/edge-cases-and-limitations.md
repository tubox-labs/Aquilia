# Controllers Edge Cases And Limitations

## Fault And Error Types

The following error-oriented classes are present in the implementation and should guide defensive usage.

| Type | Source | Meaning |
| --- | --- | --- |
| `ScopeViolationError` | `aquilia/controller/factory.py` | Raised when a scope rule is violated. |

## Common Edge Cases

- Optional dependencies may change behavior. Check imports and constructor docs before enabling production features.
- In-memory stores, queues, caches, adapters, and registries are usually process-local. Use durable backends when state must survive restarts or scale across workers.
- Request-scoped data must not be cached globally. Use request state, DI request scopes, or explicit parameters.
- Decorators in Aquilia generally attach metadata at import time. Runtime behavior happens later during compilation, routing, middleware execution, or service startup.
- Many subsystems intentionally convert invalid states into typed faults. Catch the specific fault type when application code can recover.

## Source-Level Limits To Review

Review these files before changing behavior:

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
