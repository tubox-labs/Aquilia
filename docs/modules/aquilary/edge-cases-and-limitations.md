# Aquilary Registry Edge Cases And Limitations

## Fault And Error Types

The following error-oriented classes are present in the implementation and should guide defensive usage.

| Type | Source | Meaning |
| --- | --- | --- |
| `RegistryError` | `aquilia/aquilary/errors.py` | Base error for all Aquilary registry errors. |
| `DependencyCycleError` | `aquilia/aquilary/errors.py` | Circular dependency detected in app dependency graph. |
| `RouteConflictError` | `aquilia/aquilary/errors.py` | Multiple controllers claim the same route path. |
| `ConfigValidationError` | `aquilia/aquilary/errors.py` | Configuration validation failed. |
| `CrossAppUsageError` | `aquilia/aquilary/errors.py` | App uses service/controller from another app without declaring dependency. |
| `ManifestValidationError` | `aquilia/aquilary/errors.py` | Manifest structure is invalid. |
| `DuplicateAppError` | `aquilia/aquilary/errors.py` | Multiple manifests declare the same app name. |
| `FrozenManifestMismatchError` | `aquilia/aquilary/errors.py` | Current manifests don't match frozen fingerprint. |
| `HotReloadError` | `aquilia/aquilary/errors.py` | Hot-reload operation failed. |
| `DIInjectionError` | `aquilia/aquilary/handler_wrapper.py` | Raised when dependency injection fails. |
| `RouteConflictError` | `aquilia/aquilary/route_compiler.py` | Raised when route patterns conflict. |

## Common Edge Cases

- Optional dependencies may change behavior. Check imports and constructor docs before enabling production features.
- In-memory stores, queues, caches, adapters, and registries are usually process-local. Use durable backends when state must survive restarts or scale across workers.
- Request-scoped data must not be cached globally. Use request state, DI request scopes, or explicit parameters.
- Decorators in Aquilia generally attach metadata at import time. Runtime behavior happens later during compilation, routing, middleware execution, or service startup.
- Many subsystems intentionally convert invalid states into typed faults. Catch the specific fault type when application code can recover.

## Source-Level Limits To Review

Review these files before changing behavior:

- `aquilia/aquilary/__init__.py`: Aquilary - Manifest-driven App Registry for Aquilia
- `aquilia/aquilary/cli.py`: Aquilary CLI commands for manifest validation, inspection, and deployment.
- `aquilia/aquilary/core.py`: Core Aquilary types and main registry class.
- `aquilia/aquilary/errors.py`: Aquilary registry error types with rich diagnostics.
- `aquilia/aquilary/fingerprint.py`: Fingerprint generator for reproducible deployments.
- `aquilia/aquilary/graph.py`: Dependency graph analysis with Tarjan's algorithm for cycle detection.
- `aquilia/aquilary/handler_wrapper.py`: Handler wrapper for dependency injection into controller methods.
- `aquilia/aquilary/loader.py`: Safe manifest loader with no import-time side effects.
- `aquilia/aquilary/route_compiler.py`: Route Compiler - Extracts routes from controllers and compiles route table.
- `aquilia/aquilary/validator.py`: Registry validator for manifests and configuration.
