# Blueprints Architecture

Model-to-world contracts for request validation, response rendering, schema generation, facets, projections, and lenses.

## Source Boundaries

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/blueprints/__init__.py` | 162 | 0 | 0 | Aquilia Blueprints -- first-class model↔world contracts. |
| `aquilia/blueprints/annotations.py` | 1117 | 3 | 2 | Aquilia Blueprint Annotations -- type-annotation–driven schema declaration. |
| `aquilia/blueprints/core.py` | 1194 | 2 | 0 | Aquilia Blueprint Core -- the Blueprint metaclass and base class. |
| `aquilia/blueprints/exceptions.py` | 150 | 7 | 0 | Aquilia Blueprint Exceptions -- Fault-domain-integrated error hierarchy. |
| `aquilia/blueprints/facets.py` | 1397 | 27 | 1 | Aquilia Blueprint Facets -- the field-level primitives of a Blueprint. |
| `aquilia/blueprints/integration.py` | 293 | 0 | 5 | Aquilia Blueprint Integration -- hooks into Controller, DI, Request/Response. |
| `aquilia/blueprints/lenses.py` | 201 | 1 | 0 | Aquilia Blueprint Lenses -- depth-controlled relational views. |
| `aquilia/blueprints/projections.py` | 146 | 1 | 0 | Aquilia Blueprint Projections -- named, reusable field subsets. |
| `aquilia/blueprints/schema.py` | 68 | 0 | 2 | Aquilia Blueprint Schema -- OpenAPI/JSON Schema generation. |

## Internal Shape

`blueprints` has 9 Python files, 41 public classes, 10 public module-level functions, and 15 constants or module flags detected by AST.

## Runtime Responsibilities

- No mounted `aq` command group maps directly to this module; it is used through Python APIs, manifests, workspace integrations, or server startup wiring.

## Internal Imports

| Import | Count |
| --- | ---: |
| `.exceptions` | 7 |
| `.facets` | 4 |
| `.lenses` | 3 |
| `.annotations` | 2 |
| `.core` | 2 |
| `.projections` | 2 |
| `..faults.core` | 1 |
| `..utils.data` | 1 |
| `.integration` | 1 |
| `.schema` | 1 |

## External And Stdlib Imports

| Import root | Count |
| --- | ---: |
| `typing` | 9 |
| `__future__` | 8 |
| `collections` | 2 |
| `contextlib` | 2 |
| `datetime` | 2 |
| `decimal` | 2 |
| `uuid` | 2 |
| `re` | 1 |
| `sys` | 1 |
| `types` | 1 |
| `warnings` | 1 |

## Lifecycle And Extension Points

| Extension Type | Source | Role |
| --- | --- | --- |
| `ProjectionRegistry` | `aquilia/blueprints/projections.py` | Manages named projections for a Blueprint class. |

## Error Handling

Fault/error classes defined here:

`BlueprintFault`, `CastFault`, `SealFault`, `ImprintFault`, `ProjectionFault`, `LensDepthFault`, `LensCycleFault`
