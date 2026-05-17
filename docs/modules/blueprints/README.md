# Blueprints Documentation

Model-to-world contracts for request validation, response rendering, schema generation, facets, projections, and lenses.

## Coverage Snapshot

- Source files: 9
- Source lines: 4728
- Public classes: 41
- Public module functions: 10
- Constants/module flags: 15
- Public exports in `__all__`: 55

## Source Files Read

- `aquilia/blueprints/__init__.py`: Aquilia Blueprints -- first-class model↔world contracts.
- `aquilia/blueprints/annotations.py`: Aquilia Blueprint Annotations -- type-annotation–driven schema declaration.
- `aquilia/blueprints/core.py`: Aquilia Blueprint Core -- the Blueprint metaclass and base class.
- `aquilia/blueprints/exceptions.py`: Aquilia Blueprint Exceptions -- Fault-domain-integrated error hierarchy.
- `aquilia/blueprints/facets.py`: Aquilia Blueprint Facets -- the field-level primitives of a Blueprint.
- `aquilia/blueprints/integration.py`: Aquilia Blueprint Integration -- hooks into Controller, DI, Request/Response.
- `aquilia/blueprints/lenses.py`: Aquilia Blueprint Lenses -- depth-controlled relational views.
- `aquilia/blueprints/projections.py`: Aquilia Blueprint Projections -- named, reusable field subsets.
- `aquilia/blueprints/schema.py`: Aquilia Blueprint Schema -- OpenAPI/JSON Schema generation.

## Document Map

- `architecture.md`: module boundaries, dependencies, lifecycle, and extension points.
- `configuration.md`: configuration classes, builders, server wiring, and precedence.
- `api-reference.md`: source-extracted classes, methods, functions, constants, exports, and signatures.
- `integration-guide.md`: how to wire the module into an Aquilia app.
- `cli-reference.md`: mounted `aq` commands for this module, if any.
- `examples.md`: usage examples derived from source and checked example apps.
- `edge-cases-and-limitations.md`: implementation limits and compatibility behavior.
- `troubleshooting.md`: diagnostic commands and common failure patterns.
