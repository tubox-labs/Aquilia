# Di Documentation

Scoped dependency injection container, providers, request DAG, decorators, lifecycle disposal, diagnostics, scopes, and testing utilities.

## Coverage Snapshot

- Source files: 14
- Source lines: 4800
- Public classes: 44
- Public module functions: 16
- Constants/module flags: 8
- Public exports in `__all__`: 40

## Source Files Read

- `aquilia/di/__init__.py`: Aquilia Dependency Injection System
- `aquilia/di/cli.py`: CLI commands for DI system.
- `aquilia/di/compat.py`: Compatibility layer with legacy Aquilia DI system.
- `aquilia/di/core.py`: Core DI types and protocols.
- `aquilia/di/decorators.py`: Decorators and injection helpers for ergonomic DI usage.
- `aquilia/di/dep.py`: Dep -- Composable dependency descriptor for annotation-driven DI.
- `aquilia/di/diagnostics.py`: DI Diagnostics - Observability and event tracking for DI containers.
- `aquilia/di/errors.py`: DI-specific error types with rich diagnostics.
- `aquilia/di/graph.py`: Graph analysis and cycle detection for DI system.
- `aquilia/di/lifecycle.py`: Lifecycle management for providers and containers.
- `aquilia/di/providers.py`: Provider implementations for different instantiation strategies.
- `aquilia/di/request_dag.py`: RequestDAG -- Per-request dependency graph resolver.
- `aquilia/di/scopes.py`: Scope definitions and validation.
- `aquilia/di/testing.py`: Testing utilities for DI system.

## Document Map

- `architecture.md`: module boundaries, dependencies, lifecycle, and extension points.
- `configuration.md`: configuration classes, builders, server wiring, and precedence.
- `api-reference.md`: source-extracted classes, methods, functions, constants, exports, and signatures.
- `integration-guide.md`: how to wire the module into an Aquilia app.
- `cli-reference.md`: mounted `aq` commands for this module, if any.
- `examples.md`: usage examples derived from source and checked example apps.
- `edge-cases-and-limitations.md`: implementation limits and compatibility behavior.
- `troubleshooting.md`: diagnostic commands and common failure patterns.
