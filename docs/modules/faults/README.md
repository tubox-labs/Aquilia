# Faults Documentation

Structured fault taxonomy, domains, handlers, middleware, response mapping, and subsystem patch integrations.

## Coverage Snapshot

- Source files: 12
- Source lines: 4801
- Public classes: 127
- Public module functions: 23
- Constants/module flags: 4
- Public exports in `__all__`: 132

## Source Files Read

- `aquilia/faults/__init__.py`: AquilaFaults - Production-grade fault handling system.
- `aquilia/faults/core.py`: AquilaFaults - Core types and fault taxonomy.
- `aquilia/faults/default_handlers.py`: AquilaFaults - Default Handlers.
- `aquilia/faults/domains.py`: AquilaFaults - Domain-specific fault types.
- `aquilia/faults/engine.py`: AquilaFaults - Fault Engine.
- `aquilia/faults/handlers.py`: AquilaFaults - Fault handlers.
- `aquilia/faults/integrations/__init__.py`: AquilaFaults - Subsystem Integrations.
- `aquilia/faults/integrations/di.py`: AquilaFaults - DI Integration.
- `aquilia/faults/integrations/flow.py`: AquilaFaults - Flow Engine Integration.
- `aquilia/faults/integrations/models.py`: AquilaFaults - Model/Database Integration.
- `aquilia/faults/integrations/registry.py`: AquilaFaults - Registry Integration.
- `aquilia/faults/integrations/routing.py`: AquilaFaults - Routing Integration.

## Document Map

- `architecture.md`: module boundaries, dependencies, lifecycle, and extension points.
- `configuration.md`: configuration classes, builders, server wiring, and precedence.
- `api-reference.md`: source-extracted classes, methods, functions, constants, exports, and signatures.
- `integration-guide.md`: how to wire the module into an Aquilia app.
- `cli-reference.md`: mounted `aq` commands for this module, if any.
- `examples.md`: usage examples derived from source and checked example apps.
- `edge-cases-and-limitations.md`: implementation limits and compatibility behavior.
- `troubleshooting.md`: diagnostic commands and common failure patterns.
