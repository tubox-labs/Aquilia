# Contracts Documentation

Model-to-world contracts for request validation, response rendering, schema generation, facets, projections, and lenses.

## Coverage Snapshot

- Source files: 9
- Source lines: 4728
- Public classes: 41
- Public module functions: 10
- Constants/module flags: 15
- Public exports in `__all__`: 55

## Source Files Read

- `aquilia/contracts/__init__.py`: Aquilia Contracts -- first-class model↔world contracts.
- `aquilia/contracts/annotations.py`: Aquilia Contract Annotations -- type-annotation–driven schema declaration.
- `aquilia/contracts/core.py`: Aquilia Contract Core -- the Contract metaclass and base class.
- `aquilia/contracts/exceptions.py`: Aquilia Contract Exceptions -- Fault-domain-integrated error hierarchy.
- `aquilia/contracts/facets.py`: Aquilia Contract Facets -- the field-level primitives of a Contract.
- `aquilia/contracts/integration.py`: Aquilia Contract Integration -- hooks into Controller, DI, Request/Response.
- `aquilia/contracts/lenses.py`: Aquilia Contract Lenses -- depth-controlled relational views.
- `aquilia/contracts/projections.py`: Aquilia Contract Projections -- named, reusable field subsets.
- `aquilia/contracts/schema.py`: Aquilia Contract Schema -- OpenAPI/JSON Schema generation.

## Document Map

- `architecture.md`: module boundaries, dependencies, lifecycle, and extension points.
- `configuration.md`: configuration classes, builders, server wiring, and precedence.
- `api-reference.md`: source-extracted classes, methods, functions, constants, exports, and signatures.
- `integration-guide.md`: how to wire the module into an Aquilia app.
- `cli-reference.md`: mounted `aq` commands for this module, if any.
- `examples.md`: usage examples derived from source and checked example apps.
- `edge-cases-and-limitations.md`: implementation limits and compatibility behavior.
- `troubleshooting.md`: diagnostic commands and common failure patterns.
