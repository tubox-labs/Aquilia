# aquilary Module

## Purpose

Manifest-driven registry and runtime graph. Use this module when loading, validating, freezing, fingerprinting, or compiling application manifests into runtime metadata.

## Source Coverage

- Python files: 10
- Public classes: 29
- Dataclasses: 8
- Enums: 1
- Public functions: 9

## How It Fits In Aquilia

1. Import the package from `aquilia.aquilary` or its concrete submodules.
2. Configure it through workspace integrations, manifests, or direct service construction depending on the subsystem.
3. Keep business logic outside transport and framework glue so the subsystem stays testable.

## Practical Guidance

- Prefer typed configuration objects and framework helpers over ad hoc dictionaries when they exist.
- Use the tests in `tests/` as behavioral examples when changing this subsystem.

## Public Classes

| Name | Source | Role |
| --- | --- | --- |
| `RegistryMode` | `aquilia/aquilary/core.py` | Registry operational modes. |
| `AppContext` | `aquilia/aquilary/core.py` | Runtime context for a loaded app. |
| `RegistryFingerprint` | `aquilia/aquilary/core.py` | Immutable registry fingerprint for deployment gating. |
| `AquilaryRegistry` | `aquilia/aquilary/core.py` | Validated registry metadata (static phase output). |
| `Aquilary` | `aquilia/aquilary/core.py` | Main entry point for building registry from manifests. |
| `RuntimeRegistry` | `aquilia/aquilary/core.py` | Runtime registry instance (lazy compilation phase). |
| `ErrorSpan` | `aquilia/aquilary/errors.py` | File location for error context. |
| `RegistryError` | `aquilia/aquilary/errors.py` | Base error for all Aquilary registry errors. |
| `DependencyCycleError` | `aquilia/aquilary/errors.py` | Circular dependency detected in app dependency graph. |
| `RouteConflictError` | `aquilia/aquilary/errors.py` | Multiple controllers claim the same route path. |
| `ConfigValidationError` | `aquilia/aquilary/errors.py` | Configuration validation failed. |
| `CrossAppUsageError` | `aquilia/aquilary/errors.py` | App uses service/controller from another app without declaring dependency. |
| `ManifestValidationError` | `aquilia/aquilary/errors.py` | Manifest structure is invalid. |
| `DuplicateAppError` | `aquilia/aquilary/errors.py` | Multiple manifests declare the same app name. |
| `FrozenManifestMismatchError` | `aquilia/aquilary/errors.py` | Current manifests don't match frozen fingerprint. |
| `HotReloadError` | `aquilia/aquilary/errors.py` | Hot-reload operation failed. |
| `ValidationReport` | `aquilia/aquilary/errors.py` | Aggregated validation report. |
| `FingerprintGenerator` | `aquilia/aquilary/fingerprint.py` | Generates deterministic fingerprints for registry state. |
| `GraphNode` | `aquilia/aquilary/graph.py` | Dependency graph node. |
| `DependencyGraph` | `aquilia/aquilary/graph.py` | Dependency graph with cycle detection and topological sorting. |
| `DIInjectionError` | `aquilia/aquilary/handler_wrapper.py` | Raised when dependency injection fails. |
| `HandlerWrapper` | `aquilia/aquilary/handler_wrapper.py` | Wraps controller handlers to inject dependencies from DI container. |
| `ManifestSource` | `aquilia/aquilary/loader.py` | Manifest source descriptor. |
| `ManifestLoader` | `aquilia/aquilary/loader.py` | Safe manifest loader that NEVER triggers import-time side effects. |
| `RouteInfo` | `aquilia/aquilary/route_compiler.py` | Information about a single route. |
| `RouteTable` | `aquilia/aquilary/route_compiler.py` | Compiled routing table. |
| `RouteConflictError` | `aquilia/aquilary/route_compiler.py` | Raised when route patterns conflict. |
| `RouteCompiler` | `aquilia/aquilary/route_compiler.py` | Compiles routes from controller classes. |
| `RegistryValidator` | `aquilia/aquilary/validator.py` | Validates registry manifests and configuration. |

## Public Functions

| Name | Source | Role |
| --- | --- | --- |
| `load_config` | `aquilia/aquilary/cli.py` | Load config from Python file. |
| `cmd_validate` | `aquilia/aquilary/cli.py` | Validate manifests. |
| `cmd_inspect` | `aquilia/aquilary/cli.py` | Inspect registry and show diagnostics. |
| `cmd_freeze` | `aquilia/aquilary/cli.py` | Freeze manifest for reproducible deploys. |
| `cmd_graph` | `aquilia/aquilary/cli.py` | Visualize dependency graph. |
| `cmd_run` | `aquilia/aquilary/cli.py` | Run application with registry. |
| `main` | `aquilia/aquilary/cli.py` | Main CLI entry point. |
| `wrap_handler` | `aquilia/aquilary/handler_wrapper.py` | Wrap a controller handler for dependency injection. |
| `inject_dependencies` | `aquilia/aquilary/handler_wrapper.py` | Decorator to enable dependency injection for a handler. |

## Implementation Map

| File | What To Look For |
| --- | --- |
| `aquilia/aquilary/__init__.py` | Aquilary - Manifest-driven App Registry for Aquilia |
| `aquilia/aquilary/cli.py` | Aquilary CLI commands for manifest validation, inspection, and deployment. |
| `aquilia/aquilary/core.py` | Core Aquilary types and main registry class. |
| `aquilia/aquilary/errors.py` | Aquilary registry error types with rich diagnostics. |
| `aquilia/aquilary/fingerprint.py` | Fingerprint generator for reproducible deployments. |
| `aquilia/aquilary/graph.py` | Dependency graph analysis with Tarjan's algorithm for cycle detection. |
| `aquilia/aquilary/handler_wrapper.py` | Handler wrapper for dependency injection into controller methods. |
| `aquilia/aquilary/loader.py` | Safe manifest loader with no import-time side effects. |
| `aquilia/aquilary/route_compiler.py` | Route Compiler - Extracts routes from controllers and compiles route table. |
| `aquilia/aquilary/validator.py` | Registry validator for manifests and configuration. |

## Testing Pointers

Search `tests/` for `aquilary` to find behavior-level examples. The test suite is especially useful for edge cases because many modules expose lightweight public APIs but enforce important security and lifecycle behavior internally.
