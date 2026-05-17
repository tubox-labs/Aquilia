# Dependency Injection Edge Cases And Limitations

## Fault And Error Types

The following error-oriented classes are present in the implementation and should guide defensive usage.

| Type | Source | Meaning |
| --- | --- | --- |
| `DIError` | `aquilia/di/errors.py` | Base exception for DI errors. |
| `ProviderNotFoundError` | `aquilia/di/errors.py` | Provider not found for requested token. |
| `DependencyCycleError` | `aquilia/di/errors.py` | Circular dependency detected. |
| `ScopeViolationError` | `aquilia/di/errors.py` | Scope violation detected (e.g., request-scoped injected into app-scoped). |
| `AmbiguousProviderError` | `aquilia/di/errors.py` | Multiple providers found for token without tag. |
| `ManifestValidationError` | `aquilia/di/errors.py` | Manifest validation failed. |
| `CrossAppDependencyError` | `aquilia/di/errors.py` | Cross-app dependency not declared in depends_on. |
| `CircularDependencyError` | `aquilia/di/errors.py` | Circular dependency detected in service graph. |
| `MissingDependencyError` | `aquilia/di/errors.py` | Required dependency not found in container. |

## Common Edge Cases

- Optional dependencies may change behavior. Check imports and constructor docs before enabling production features.
- In-memory stores, queues, caches, adapters, and registries are usually process-local. Use durable backends when state must survive restarts or scale across workers.
- Request-scoped data must not be cached globally. Use request state, DI request scopes, or explicit parameters.
- Decorators in Aquilia generally attach metadata at import time. Runtime behavior happens later during compilation, routing, middleware execution, or service startup.
- Many subsystems intentionally convert invalid states into typed faults. Catch the specific fault type when application code can recover.

## Source-Level Limits To Review

Review these files before changing behavior:

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
