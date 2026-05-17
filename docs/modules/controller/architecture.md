# Controller Architecture

Controller base class, route decorators, compiler, router, execution engine, renderers, filters, pagination, and OpenAPI generation.

## Source Boundaries

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/controller/__init__.py` | 169 | 0 | 0 | Aquilia Controller System |
| `aquilia/controller/base.py` | 650 | 5 | 0 | Controller Base Class |
| `aquilia/controller/compiler.py` | 381 | 3 | 0 | Controller Compiler - Compiles controllers to patterns and routes. |
| `aquilia/controller/decorators.py` | 739 | 10 | 1 | Controller Method Decorators |
| `aquilia/controller/engine.py` | 1386 | 1 | 0 | Controller Engine - Executes controller methods with full integration. |
| `aquilia/controller/factory.py` | 403 | 3 | 0 | Controller Factory |
| `aquilia/controller/filters.py` | 766 | 5 | 5 | Aquilia Filter System -- declarative filtering, searching, and ordering. |
| `aquilia/controller/metadata.py` | 461 | 3 | 1 | Controller Metadata Extraction |
| `aquilia/controller/openapi.py` | 1089 | 3 | 2 | OpenAPI 3.1.0 Generation for Aquilia Controllers. |
| `aquilia/controller/pagination.py` | 724 | 5 | 0 | Aquilia Pagination System -- declarative pagination backends. |
| `aquilia/controller/renderers.py` | 453 | 8 | 1 | Aquilia Content Negotiation & Renderer System. |
| `aquilia/controller/router.py` | 592 | 2 | 0 | Controller Router - Pattern-based router for controllers. |

## Internal Shape

`controller` has 12 Python files, 48 public classes, 10 public module-level functions, and 21 constants or module flags detected by AST.

## Runtime Responsibilities

- No mounted `aq` command group maps directly to this module; it is used through Python APIs, manifests, workspace integrations, or server startup wiring.

## Internal Imports

| Import | Count |
| --- | ---: |
| `.compiler` | 4 |
| `..patterns` | 2 |
| `.base` | 2 |
| `.factory` | 2 |
| `.metadata` | 2 |
| `.router` | 2 |
| `..di` | 1 |
| `..patterns.openapi` | 1 |
| `..request` | 1 |
| `..response` | 1 |
| `.decorators` | 1 |
| `.engine` | 1 |
| `.filters` | 1 |
| `.openapi` | 1 |
| `.pagination` | 1 |
| `.renderers` | 1 |
| `aquilia._datastructures` | 1 |
| `aquilia._uploads` | 1 |

## External And Stdlib Imports

| Import root | Count |
| --- | ---: |
| `typing` | 11 |
| `inspect` | 6 |
| `logging` | 5 |
| `__future__` | 4 |
| `dataclasses` | 4 |
| `asyncio` | 2 |
| `collections` | 2 |
| `json` | 2 |
| `re` | 2 |
| `base64` | 1 |
| `contextlib` | 1 |
| `contextvars` | 1 |
| `datetime` | 1 |
| `enum` | 1 |
| `hashlib` | 1 |
| `hmac` | 1 |
| `html` | 1 |
| `math` | 1 |
| `os` | 1 |
| `time` | 1 |
| `urllib` | 1 |

## Lifecycle And Extension Points

| Extension Type | Source | Role |
| --- | --- | --- |
| `Controller` | `aquilia/controller/base.py` | Base Controller class. |
| `CompiledController` | `aquilia/controller/compiler.py` | A fully compiled controller with all routes. |
| `ControllerCompiler` | `aquilia/controller/compiler.py` | Compiles controllers into executable routes with pattern matching. |
| `ControllerEngine` | `aquilia/controller/engine.py` | Executes controller methods with complete integration. |
| `ControllerFactory` | `aquilia/controller/factory.py` | Factory for creating controller instances. |
| `BaseFilterBackend` | `aquilia/controller/filters.py` | Abstract base for pluggable filter backends. |
| `ControllerMetadata` | `aquilia/controller/metadata.py` | Complete metadata for a Controller class. |
| `OpenAPIConfig` | `aquilia/controller/openapi.py` | Configuration for OpenAPI spec generation. |
| `ControllerRouteMatch` | `aquilia/controller/router.py` | Result of a successful controller route match. |
| `ControllerRouter` | `aquilia/controller/router.py` | Router for controller-based routes using pattern matching. |

## Error Handling

Fault/error classes defined here:

`ScopeViolationError`
