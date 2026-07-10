# Di Architecture

Scoped dependency injection container, providers, request DAG, decorators, lifecycle disposal, diagnostics, scopes, and testing utilities.

## Source Boundaries

| File | Lines | Classes | Functions | Purpose |
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

## Internal Shape

`di` has 14 Python files, 44 public classes, 16 public module-level functions, and 8 constants or module flags detected by AST.

## Runtime Responsibilities

- No mounted `aq` command group maps directly to this module; it is used through Python APIs, manifests, workspace integrations, or server startup wiring.

## Internal Imports

| Import | Count |
| --- | ---: |
| `.core` | 5 |
| `.errors` | 4 |
| `.dep` | 2 |
| `.providers` | 2 |
| `.compat` | 1 |
| `.decorators` | 1 |
| `.graph` | 1 |
| `.lifecycle` | 1 |
| `.request_dag` | 1 |
| `.scopes` | 1 |
| `.testing` | 1 |
| `aquilia._version` | 1 |

## External And Stdlib Imports

| Import root | Count |
| --- | ---: |
| `typing` | 11 |
| `collections` | 7 |
| `dataclasses` | 6 |
| `asyncio` | 5 |
| `inspect` | 4 |
| `contextlib` | 3 |
| `enum` | 3 |
| `logging` | 3 |
| `__future__` | 2 |
| `sys` | 2 |
| `time` | 2 |
| `contextvars` | 1 |
| `functools` | 1 |
| `json` | 1 |
| `pathlib` | 1 |
| `types` | 1 |

## Lifecycle And Extension Points

| Extension Type | Source | Role |
| --- | --- | --- |
| `ProviderMeta` | `aquilia/di/core.py` | Compact, serializable provider metadata. |
| `Provider` | `aquilia/di/core.py` | Provider protocol - how to instantiate a dependency. |
| `Registry` | `aquilia/di/core.py` | Registry - builds and validates provider graph from manifests. |
| `ProviderNotFoundError` | `aquilia/di/errors.py` | Provider not found for requested token. |
| `AmbiguousProviderError` | `aquilia/di/errors.py` | Multiple providers found for token without tag. |
| `LifecycleHook` | `aquilia/di/lifecycle.py` | Lifecycle hook registration. |
| `ClassProvider` | `aquilia/di/providers.py` | Provider that instantiates a class by resolving constructor dependencies. |
| `FactoryProvider` | `aquilia/di/providers.py` | Provider that calls a factory function to produce instances. |
| `ValueProvider` | `aquilia/di/providers.py` | Provider that returns a pre-bound constant value. |
| `PoolProvider` | `aquilia/di/providers.py` | Provider that manages a pool of instances. |
| `AliasProvider` | `aquilia/di/providers.py` | Provider that aliases one token to another. |
| `LazyProxyProvider` | `aquilia/di/providers.py` | Provider that creates a lazy proxy for cycle resolution. |
| `ScopedProvider` | `aquilia/di/providers.py` | Wrapper provider that enforces scope semantics. |
| `ContractProvider` | `aquilia/di/providers.py` | DI Provider that creates Contract instances with request context. |
| `MockProvider` | `aquilia/di/testing.py` | Mock provider for testing. |
| `TestRegistry` | `aquilia/di/testing.py` | Registry with testing support. |

## Error Handling

Fault/error classes defined here:

`DIError`, `ProviderNotFoundError`, `DependencyCycleError`, `ScopeViolationError`, `AmbiguousProviderError`, `ManifestValidationError`, `CrossAppDependencyError`, `CircularDependencyError`, `MissingDependencyError`
