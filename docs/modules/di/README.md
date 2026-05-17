# Dependency Injection Documentation

This directory is the professional documentation set for `di`. It is implementation-driven and aligned with the current source files under `aquilia/di`.

## What This Covers

The scoped dependency injection container, provider model, lifecycle disposal, dependency graph, request DAG, and testing overrides.

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

- `architecture.md`: Runtime architecture and module boundaries
- `configuration.md`: Configuration entry points, datatypes, and precedence
- `api-reference.md`: Classes, methods, functions, constants, and data fields extracted from source
- `integration-guide.md`: How to wire the module into a real Aquilia application
- `cli-reference.md`: Command line surface and operational commands
- `edge-cases-and-limitations.md`: Known edge cases and implementation limits
- `troubleshooting.md`: Common failures and diagnosis steps
- `examples.md`: Code examples and usage patterns

## Public Surface Snapshot

- Python files: 14
- Public classes: 44
- Configuration or dataclass-like types: 8
- Public functions: 16
- Constants detected: 7

## Fast Start

```python
from aquilia.di import Container, ValueProvider

container = Container(scope="app")
container.register(ValueProvider(token="settings", value={"debug": True}, scope="app"))
settings = await container.resolve_async("settings")
```

## Read Next

Start with `architecture.md` if you are learning how the subsystem fits into runtime boot. Use `api-reference.md` when you need exact methods, datatypes, and class fields. Use `examples.md` for copyable patterns that match the current code.
