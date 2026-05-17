# Controller Documentation

Controller base class, route decorators, compiler, router, execution engine, renderers, filters, pagination, and OpenAPI generation.

## Coverage Snapshot

- Source files: 12
- Source lines: 7813
- Public classes: 48
- Public module functions: 10
- Constants/module flags: 21
- Public exports in `__all__`: 55

## Source Files Read

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

## Document Map

- `architecture.md`: module boundaries, dependencies, lifecycle, and extension points.
- `configuration.md`: configuration classes, builders, server wiring, and precedence.
- `api-reference.md`: source-extracted classes, methods, functions, constants, exports, and signatures.
- `integration-guide.md`: how to wire the module into an Aquilia app.
- `cli-reference.md`: mounted `aq` commands for this module, if any.
- `examples.md`: usage examples derived from source and checked example apps.
- `edge-cases-and-limitations.md`: implementation limits and compatibility behavior.
- `troubleshooting.md`: diagnostic commands and common failure patterns.
