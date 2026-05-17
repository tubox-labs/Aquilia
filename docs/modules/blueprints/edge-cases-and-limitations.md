# Blueprints Edge Cases And Limitations

## Fault And Error Types

The following error-oriented classes are present in the implementation and should guide defensive usage.

| Type | Source | Meaning |
| --- | --- | --- |
| `BlueprintFault` | `aquilia/blueprints/exceptions.py` | Base fault for all Blueprint errors. |
| `CastFault` | `aquilia/blueprints/exceptions.py` | Raised when incoming data cannot be cast to the expected type. |
| `SealFault` | `aquilia/blueprints/exceptions.py` | Raised when a validation seal is broken. |
| `ImprintFault` | `aquilia/blueprints/exceptions.py` | Raised when a write (imprint) operation fails. |
| `ProjectionFault` | `aquilia/blueprints/exceptions.py` | Raised when an invalid projection is requested. |
| `LensDepthFault` | `aquilia/blueprints/exceptions.py` | Raised when Lens traversal exceeds maximum depth. |
| `LensCycleFault` | `aquilia/blueprints/exceptions.py` | Raised when a circular Lens reference is detected. |

## Common Edge Cases

- Optional dependencies may change behavior. Check imports and constructor docs before enabling production features.
- In-memory stores, queues, caches, adapters, and registries are usually process-local. Use durable backends when state must survive restarts or scale across workers.
- Request-scoped data must not be cached globally. Use request state, DI request scopes, or explicit parameters.
- Decorators in Aquilia generally attach metadata at import time. Runtime behavior happens later during compilation, routing, middleware execution, or service startup.
- Many subsystems intentionally convert invalid states into typed faults. Catch the specific fault type when application code can recover.

## Source-Level Limits To Review

Review these files before changing behavior:

- `aquilia/blueprints/__init__.py`: Aquilia Blueprints -- first-class model↔world contracts.
- `aquilia/blueprints/annotations.py`: Aquilia Blueprint Annotations -- type-annotation-driven schema declaration.
- `aquilia/blueprints/core.py`: Aquilia Blueprint Core -- the Blueprint metaclass and base class.
- `aquilia/blueprints/exceptions.py`: Aquilia Blueprint Exceptions -- Fault-domain-integrated error hierarchy.
- `aquilia/blueprints/facets.py`: Aquilia Blueprint Facets -- the field-level primitives of a Blueprint.
- `aquilia/blueprints/integration.py`: Aquilia Blueprint Integration -- hooks into Controller, DI, Request/Response.
- `aquilia/blueprints/lenses.py`: Aquilia Blueprint Lenses -- depth-controlled relational views.
- `aquilia/blueprints/projections.py`: Aquilia Blueprint Projections -- named, reusable field subsets.
- `aquilia/blueprints/schema.py`: Aquilia Blueprint Schema -- OpenAPI/JSON Schema generation.
