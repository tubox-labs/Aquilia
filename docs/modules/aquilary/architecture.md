# Aquilary Architecture

Manifest registry, validation, dependency graph, route table compilation metadata, fingerprinting, and runtime registry construction.

## Source Boundaries

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/aquilary/__init__.py` | 78 | 0 | 0 | Aquilary - Manifest-driven App Registry for Aquilia |
| `aquilia/aquilary/cli.py` | 501 | 0 | 7 | Aquilary CLI commands for manifest validation, inspection, and deployment. |
| `aquilia/aquilary/core.py` | 1498 | 6 | 0 | Core Aquilary types and main registry class. |
| `aquilia/aquilary/errors.py` | 448 | 11 | 0 | Aquilary registry error types with rich diagnostics. |
| `aquilia/aquilary/fingerprint.py` | 424 | 1 | 0 | Fingerprint generator for reproducible deployments. |
| `aquilia/aquilary/graph.py` | 334 | 2 | 0 | Dependency graph analysis with Tarjan's algorithm for cycle detection. |
| `aquilia/aquilary/handler_wrapper.py` | 204 | 2 | 2 | Handler wrapper for dependency injection into controller methods. |
| `aquilia/aquilary/loader.py` | 487 | 2 | 0 | Safe manifest loader with no import-time side effects. |
| `aquilia/aquilary/route_compiler.py` | 249 | 4 | 0 | Route Compiler - Extracts routes from controllers and compiles route table. |
| `aquilia/aquilary/validator.py` | 453 | 1 | 0 | Registry validator for manifests and configuration. |

## Internal Shape

`aquilary` has 10 Python files, 29 public classes, 9 public module-level functions, and 1 constants or module flags detected by AST.

## Runtime Responsibilities

- This module has `aq` command coverage documented in `cli-reference.md`; 12 commands map to this subsystem.

## Internal Imports

| Import | Count |
| --- | ---: |
| `.errors` | 2 |
| `.core` | 1 |
| `.fingerprint` | 1 |
| `.graph` | 1 |
| `.handler_wrapper` | 1 |
| `.loader` | 1 |
| `.validator` | 1 |
| `aquilia._version` | 1 |

## External And Stdlib Imports

| Import root | Count |
| --- | ---: |
| `typing` | 8 |
| `dataclasses` | 5 |
| `importlib` | 3 |
| `json` | 3 |
| `collections` | 2 |
| `inspect` | 2 |
| `pathlib` | 2 |
| `sys` | 2 |
| `argparse` | 1 |
| `contextlib` | 1 |
| `datetime` | 1 |
| `enum` | 1 |
| `functools` | 1 |
| `hashlib` | 1 |
| `logging` | 1 |
| `os` | 1 |

## Lifecycle And Extension Points

| Extension Type | Source | Role |
| --- | --- | --- |
| `RegistryMode` | `aquilia/aquilary/core.py` | Registry operational modes. |
| `RegistryFingerprint` | `aquilia/aquilary/core.py` | Immutable registry fingerprint for deployment gating. |
| `AquilaryRegistry` | `aquilia/aquilary/core.py` | Validated registry metadata (static phase output). |
| `RuntimeRegistry` | `aquilia/aquilary/core.py` | Runtime registry instance (lazy compilation phase). |
| `RegistryError` | `aquilia/aquilary/errors.py` | Base error for all Aquilary registry errors. |
| `ConfigValidationError` | `aquilia/aquilary/errors.py` | Configuration validation failed. |
| `ManifestLoader` | `aquilia/aquilary/loader.py` | Safe manifest loader that NEVER triggers import-time side effects. |
| `RouteCompiler` | `aquilia/aquilary/route_compiler.py` | Compiles routes from controller classes. Extracts @flow decorators and builds routing table. |
| `RegistryValidator` | `aquilia/aquilary/validator.py` | Validates registry manifests and configuration. |

## Error Handling

Fault/error classes defined here:

`ErrorSpan`, `RegistryError`, `DependencyCycleError`, `RouteConflictError`, `ConfigValidationError`, `CrossAppUsageError`, `ManifestValidationError`, `DuplicateAppError`, `FrozenManifestMismatchError`, `HotReloadError`, `DIInjectionError`, `RouteConflictError`
