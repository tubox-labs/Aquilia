# di Module

## Purpose

Scoped dependency injection container. Use this module for providers, request scopes, service scopes, lifecycle disposal, diagnostics, dependency graphs, mocks, and test registries.

## Source Coverage

- Python files: 14
- Public classes: 44
- Dataclasses: 9
- Enums: 3
- Public functions: 16

## How It Fits In Aquilia

1. Import the package from `aquilia.di` or its concrete submodules.
2. Configure it through workspace integrations, manifests, or direct service construction depending on the subsystem.
3. Keep business logic outside transport and framework glue so the subsystem stays testable.

## Practical Guidance

- Prefer typed configuration objects and framework helpers over ad hoc dictionaries when they exist.
- Use the tests in `tests/` as behavioral examples when changing this subsystem.

## Public Classes

| Name | Source | Role |
| --- | --- | --- |
| `RequestCtx` | `aquilia/di/compat.py` | Legacy RequestCtx compatibility wrapper. |
| `ProviderMeta` | `aquilia/di/core.py` | Compact, serializable provider metadata. |
| `ResolveCtx` | `aquilia/di/core.py` | Context for resolution operations. |
| `Provider` | `aquilia/di/core.py` | Provider protocol - how to instantiate a dependency. |
| `Container` | `aquilia/di/core.py` | DI Container - manages provider instances and scopes. |
| `Registry` | `aquilia/di/core.py` | Registry - builds and validates provider graph from manifests. |
| `Inject` | `aquilia/di/decorators.py` | Injection metadata marker. |
| `Dep` | `aquilia/di/dep.py` | Dependency descriptor for Annotated[]-based injection. |
| `Header` | `aquilia/di/dep.py` | Extract a header value from the current request. |
| `Query` | `aquilia/di/dep.py` | Extract a query parameter from the current request. |
| `Body` | `aquilia/di/dep.py` | Mark a parameter as coming from the request body. |
| `DIEventType` | `aquilia/di/diagnostics.py` | Types of DI events. |
| `DIEvent` | `aquilia/di/diagnostics.py` | A diagnostic event in the DI system. |
| `DiagnosticListener` | `aquilia/di/diagnostics.py` | Interface for DI diagnostic listeners. |
| `ConsoleDiagnosticListener` | `aquilia/di/diagnostics.py` | Simple diagnostic listener that logs to console/logging. |
| `DIDiagnostics` | `aquilia/di/diagnostics.py` | Coordinator for DI diagnostic listeners. |
| `DIError` | `aquilia/di/errors.py` | Base exception for DI errors. |
| `ProviderNotFoundError` | `aquilia/di/errors.py` | Provider not found for requested token. |
| `DependencyCycleError` | `aquilia/di/errors.py` | Circular dependency detected. |
| `ScopeViolationError` | `aquilia/di/errors.py` | Scope violation detected (e.g., request-scoped injected into app-scoped). |
| `AmbiguousProviderError` | `aquilia/di/errors.py` | Multiple providers found for token without tag. |
| `ManifestValidationError` | `aquilia/di/errors.py` | Manifest validation failed. |
| `CrossAppDependencyError` | `aquilia/di/errors.py` | Cross-app dependency not declared in depends_on. |
| `CircularDependencyError` | `aquilia/di/errors.py` | Circular dependency detected in service graph. |
| `MissingDependencyError` | `aquilia/di/errors.py` | Required dependency not found in container. |
| `DependencyGraph` | `aquilia/di/graph.py` | Build and analyze dependency graph. |
| `DisposalStrategy` | `aquilia/di/lifecycle.py` | Strategy for disposing instances. |
| `LifecycleHook` | `aquilia/di/lifecycle.py` | Lifecycle hook registration. |
| `Lifecycle` | `aquilia/di/lifecycle.py` | Manages lifecycle hooks and deterministic disposal. |
| `LifecycleContext` | `aquilia/di/lifecycle.py` | Context manager for automatic lifecycle management. |
| `ClassProvider` | `aquilia/di/providers.py` | Provider that instantiates a class by resolving constructor dependencies. |
| `FactoryProvider` | `aquilia/di/providers.py` | Provider that calls a factory function to produce instances. |
| `ValueProvider` | `aquilia/di/providers.py` | Provider that returns a pre-bound constant value. |
| `PoolProvider` | `aquilia/di/providers.py` | Provider that manages a pool of instances. |
| `AliasProvider` | `aquilia/di/providers.py` | Provider that aliases one token to another. |
| `LazyProxyProvider` | `aquilia/di/providers.py` | Provider that creates a lazy proxy for cycle resolution. |
| `ScopedProvider` | `aquilia/di/providers.py` | Wrapper provider that enforces scope semantics. |
| `BlueprintProvider` | `aquilia/di/providers.py` | DI Provider that creates Blueprint instances with request context. |
| `RequestDAG` | `aquilia/di/request_dag.py` | Per-request dependency resolution graph. |
| `ServiceScope` | `aquilia/di/scopes.py` | Service lifetime scopes. |
| `Scope` | `aquilia/di/scopes.py` | Scope metadata and rules. |
| `ScopeValidator` | `aquilia/di/scopes.py` | Validates scope rules and relationships. |
| `MockProvider` | `aquilia/di/testing.py` | Mock provider for testing. |
| `TestRegistry` | `aquilia/di/testing.py` | Registry with testing support. |

## Public Functions

| Name | Source | Role |
| --- | --- | --- |
| `load_manifests_from_settings` | `aquilia/di/cli.py` | Load manifests and config from settings file. |
| `cmd_di_check` | `aquilia/di/cli.py` | Validate DI configuration (static analysis). |
| `cmd_di_tree` | `aquilia/di/cli.py` | Show dependency tree. |
| `cmd_di_graph` | `aquilia/di/cli.py` | Export dependency graph as Graphviz DOT. |
| `cmd_di_profile` | `aquilia/di/cli.py` | Benchmark DI performance. |
| `cmd_di_manifest` | `aquilia/di/cli.py` | Generate di_manifest.json for LSP integration. |
| `setup_di_commands` | `aquilia/di/cli.py` | Setup DI subcommands. |
| `get_request_container` | `aquilia/di/compat.py` | Get current request container from context. |
| `set_request_container` | `aquilia/di/compat.py` | Set request container in context. |
| `clear_request_container` | `aquilia/di/compat.py` | Clear request container from context. |
| `inject` | `aquilia/di/decorators.py` | Create injection metadata. |
| `service` | `aquilia/di/decorators.py` | Decorator to mark a class as a DI service. |
| `factory` | `aquilia/di/decorators.py` | Decorator to mark a function as a DI factory. |
| `provides` | `aquilia/di/decorators.py` | Decorator to explicitly declare what a factory provides. |
| `auto_inject` | `aquilia/di/decorators.py` | Decorator to auto-inject dependencies into a function. |
| `override_container` | `aquilia/di/testing.py` | Context manager to temporarily override a provider. |

## Implementation Map

| File | What To Look For |
| --- | --- |
| `aquilia/di/__init__.py` | Aquilia Dependency Injection System |
| `aquilia/di/cli.py` | CLI commands for DI system. |
| `aquilia/di/compat.py` | Compatibility layer with legacy Aquilia DI system. |
| `aquilia/di/core.py` | Core DI types and protocols. |
| `aquilia/di/decorators.py` | Decorators and injection helpers for ergonomic DI usage. |
| `aquilia/di/dep.py` | Dep -- Composable dependency descriptor for annotation-driven DI. |
| `aquilia/di/diagnostics.py` | DI Diagnostics - Observability and event tracking for DI containers. |
| `aquilia/di/errors.py` | DI-specific error types with rich diagnostics. |
| `aquilia/di/graph.py` | Graph analysis and cycle detection for DI system. |
| `aquilia/di/lifecycle.py` | Lifecycle management for providers and containers. |
| `aquilia/di/providers.py` | Provider implementations for different instantiation strategies. |
| `aquilia/di/request_dag.py` | RequestDAG -- Per-request dependency graph resolver. |
| `aquilia/di/scopes.py` | Scope definitions and validation. |
| `aquilia/di/testing.py` | Testing utilities for DI system. |

## Testing Pointers

Search `tests/` for `di` to find behavior-level examples. The test suite is especially useful for edge cases because many modules expose lightweight public APIs but enforce important security and lifecycle behavior internally.
