# Controller Configuration

Controller base class, route decorators, compiler, router, execution engine, renderers, filters, pagination, and OpenAPI generation.

This page distinguishes direct configuration APIs from indirect runtime wiring. All class names and source files below are extracted from the current source tree.

## Configuration Model

This module exposes config-oriented public classes. Use the table below to locate exact constructors and `to_dict()` behavior in `api-reference.md`.

## Source Inventory

| File | Lines | Public classes | Public functions | Purpose |
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

## Detected Config-Oriented Classes

| Class | Source | Methods | Summary |
| --- | --- | --- | --- |
| `OpenAPIConfig` | `aquilia/controller/openapi.py` | `from_dict` | Configuration for OpenAPI spec generation. |

## Runtime Wiring Paths

- `workspace.py` defines workspace-level structure with `Workspace`, `Module`, and `Integration` builders.
- `modules/<name>/manifest.py` defines module internals with `AppManifest`.
- `ConfigLoader.get(...)` resolves dotted configuration paths at runtime.
- `AquiliaServer` consumes resolved config during middleware and subsystem setup.
- Subsystems with optional providers only require optional dependencies when their backend/provider is configured.

## Verification Checklist

1. Run `aq validate` to verify manifests.
2. Run `aq inspect config` to inspect resolved configuration.
3. Run `aq doctor` for workspace and integration diagnostics.
4. For server-only wiring, start via `aq run` and check startup logs plus `GET /_health`.

## Related Pages

- `api-reference.md` for exact class fields, methods, constants, and signatures.
- `integration-guide.md` for the workspace/manifest wiring pattern.
- `edge-cases-and-limitations.md` for fallback and compatibility behavior.
