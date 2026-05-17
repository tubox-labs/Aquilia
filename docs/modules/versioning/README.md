# Versioning Documentation

API version parsing, resolvers, decorators, negotiation, graph, sunset policy/enforcement, middleware, and route registration integration.

## Coverage Snapshot

- Source files: 11
- Source lines: 2844
- Public classes: 30
- Public module functions: 3
- Constants/module flags: 6
- Public exports in `__all__`: 33

## Source Files Read

- `aquilia/versioning/__init__.py`: Aquilia Versioning System — Epoch-Based API Versioning
- `aquilia/versioning/core.py`: Aquilia Versioning — Core Types
- `aquilia/versioning/decorators.py`: Aquilia Versioning — Route-Level Decorators
- `aquilia/versioning/errors.py`: Aquilia Versioning — Version Errors
- `aquilia/versioning/graph.py`: Aquilia Versioning — Version Graph
- `aquilia/versioning/middleware.py`: Aquilia Versioning — Version Middleware
- `aquilia/versioning/negotiation.py`: Aquilia Versioning — Version Negotiation
- `aquilia/versioning/parser.py`: Aquilia Versioning — Version Parser
- `aquilia/versioning/resolvers.py`: Aquilia Versioning — Version Resolvers
- `aquilia/versioning/strategy.py`: Aquilia Versioning — Version Strategy
- `aquilia/versioning/sunset.py`: Aquilia Versioning — Sunset Lifecycle

## Document Map

- `architecture.md`: module boundaries, dependencies, lifecycle, and extension points.
- `configuration.md`: configuration classes, builders, server wiring, and precedence.
- `api-reference.md`: source-extracted classes, methods, functions, constants, exports, and signatures.
- `integration-guide.md`: how to wire the module into an Aquilia app.
- `cli-reference.md`: mounted `aq` commands for this module, if any.
- `examples.md`: usage examples derived from source and checked example apps.
- `edge-cases-and-limitations.md`: implementation limits and compatibility behavior.
- `troubleshooting.md`: diagnostic commands and common failure patterns.
