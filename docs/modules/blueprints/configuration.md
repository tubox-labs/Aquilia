# Contracts Configuration

Model-to-world contracts for request validation, response rendering, schema generation, facets, projections, and lenses.

This page distinguishes direct configuration APIs from indirect runtime wiring. All class names and source files below are extracted from the current source tree.

## Configuration Model

No public config-specific class was detected in this module. It is configured through workspace/module declarations, related integration objects, or direct Python APIs.

## Source Inventory

| File | Lines | Public classes | Public functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/contracts/__init__.py` | 162 | 0 | 0 | Aquilia Contracts -- first-class model↔world contracts. |
| `aquilia/contracts/annotations.py` | 1117 | 3 | 2 | Aquilia Contract Annotations -- type-annotation–driven schema declaration. |
| `aquilia/contracts/core.py` | 1194 | 2 | 0 | Aquilia Contract Core -- the Contract metaclass and base class. |
| `aquilia/contracts/exceptions.py` | 150 | 7 | 0 | Aquilia Contract Exceptions -- Fault-domain-integrated error hierarchy. |
| `aquilia/contracts/facets.py` | 1397 | 27 | 1 | Aquilia Contract Facets -- the field-level primitives of a Contract. |
| `aquilia/contracts/integration.py` | 293 | 0 | 5 | Aquilia Contract Integration -- hooks into Controller, DI, Request/Response. |
| `aquilia/contracts/lenses.py` | 201 | 1 | 0 | Aquilia Contract Lenses -- depth-controlled relational views. |
| `aquilia/contracts/projections.py` | 146 | 1 | 0 | Aquilia Contract Projections -- named, reusable field subsets. |
| `aquilia/contracts/schema.py` | 68 | 0 | 2 | Aquilia Contract Schema -- OpenAPI/JSON Schema generation. |

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
