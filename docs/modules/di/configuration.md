# Di Configuration

Scoped dependency injection container, providers, request DAG, decorators, lifecycle disposal, diagnostics, scopes, and testing utilities.

This page distinguishes direct configuration APIs from indirect runtime wiring. All class names and source files below are extracted from the current source tree.

## Configuration Model

This module exposes config-oriented public classes. Use the table below to locate exact constructors and `to_dict()` behavior in `api-reference.md`.

## Source Inventory

| File | Lines | Public classes | Public functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/di/__init__.py` | 132 | 0 | 0 | Aquilia Dependency Injection System |
| `aquilia/di/cli.py` | 479 | 0 | 7 | CLI commands for DI system. |
| `aquilia/di/compat.py` | 105 | 1 | 3 | Compatibility layer with legacy Aquilia DI system. |
| `aquilia/di/core.py` | 1034 | 5 | 0 | Core DI types and protocols. |
| `aquilia/di/decorators.py` | 242 | 1 | 5 | Decorators and injection helpers for ergonomic DI usage. |
| `aquilia/di/dep.py` | 398 | 4 | 0 | Dep -- Composable dependency descriptor for annotation-driven DI. |
| `aquilia/di/diagnostics.py` | 122 | 5 | 0 | DI Diagnostics - Observability and event tracking for DI containers. |
| `aquilia/di/errors.py` | 239 | 9 | 0 | DI-specific error types with rich diagnostics. |
| `aquilia/di/graph.py` | 261 | 1 | 0 | Graph analysis and cycle detection for DI system. |
| `aquilia/di/lifecycle.py` | 241 | 4 | 0 | Lifecycle management for providers and containers. |
| `aquilia/di/providers.py` | 822 | 8 | 0 | Provider implementations for different instantiation strategies. |
| `aquilia/di/request_dag.py` | 431 | 1 | 0 | RequestDAG -- Per-request dependency graph resolver. |
| `aquilia/di/scopes.py` | 99 | 3 | 0 | Scope definitions and validation. |
| `aquilia/di/testing.py` | 195 | 2 | 1 | Testing utilities for DI system. |

## Detected Config-Oriented Classes

| Class | Source | Methods | Summary |
| --- | --- | --- | --- |
| `ProviderMeta` | `aquilia/di/core.py` | `to_dict` | Compact, serializable provider metadata. |
| `Provider` | `aquilia/di/core.py` | `meta`, `instantiate`, `shutdown` | Provider protocol - how to instantiate a dependency. |
| `ProviderNotFoundError` | `aquilia/di/errors.py` |  | Provider not found for requested token. |
| `AmbiguousProviderError` | `aquilia/di/errors.py` |  | Multiple providers found for token without tag. |
| `ClassProvider` | `aquilia/di/providers.py` | `meta`, `instantiate`, `shutdown` | Provider that instantiates a class by resolving constructor dependencies. |
| `FactoryProvider` | `aquilia/di/providers.py` | `meta`, `instantiate`, `shutdown` | Provider that calls a factory function to produce instances. |
| `ValueProvider` | `aquilia/di/providers.py` | `meta`, `instantiate`, `shutdown` | Provider that returns a pre-bound constant value. |
| `PoolProvider` | `aquilia/di/providers.py` | `meta`, `instantiate`, `release`, `acquire`, `shutdown` | Provider that manages a pool of instances. |
| `AliasProvider` | `aquilia/di/providers.py` | `meta`, `instantiate`, `shutdown` | Provider that aliases one token to another. |
| `LazyProxyProvider` | `aquilia/di/providers.py` | `meta`, `instantiate`, `shutdown` | Provider that creates a lazy proxy for cycle resolution. |
| `ScopedProvider` | `aquilia/di/providers.py` | `meta`, `instantiate`, `shutdown` | Wrapper provider that enforces scope semantics. |
| `ContractProvider` | `aquilia/di/providers.py` | `meta`, `instantiate`, `shutdown` | DI Provider that creates Contract instances with request context. |
| `MockProvider` | `aquilia/di/testing.py` | `instantiate`, `reset` | Mock provider for testing. |

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
