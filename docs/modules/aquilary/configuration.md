# Aquilary Configuration

Manifest registry, validation, dependency graph, route table compilation metadata, fingerprinting, and runtime registry construction.

This page distinguishes direct configuration APIs from indirect runtime wiring. All class names and source files below are extracted from the current source tree.

## Configuration Model

This module exposes config-oriented public classes. Use the table below to locate exact constructors and `to_dict()` behavior in `api-reference.md`.

## Source Inventory

| File | Lines | Public classes | Public functions | Purpose |
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

## Detected Config-Oriented Classes

| Class | Source | Methods | Summary |
| --- | --- | --- | --- |
| `ConfigValidationError` | `aquilia/aquilary/errors.py` |  | Configuration validation failed. |

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
