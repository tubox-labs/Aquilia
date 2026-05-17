# Aquilary Documentation

Manifest registry, validation, dependency graph, route table compilation metadata, fingerprinting, and runtime registry construction.

## Coverage Snapshot

- Source files: 10
- Source lines: 4676
- Public classes: 29
- Public module functions: 9
- Constants/module flags: 1
- Public exports in `__all__`: 23

## Source Files Read

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

## Document Map

- `architecture.md`: module boundaries, dependencies, lifecycle, and extension points.
- `configuration.md`: configuration classes, builders, server wiring, and precedence.
- `api-reference.md`: source-extracted classes, methods, functions, constants, exports, and signatures.
- `integration-guide.md`: how to wire the module into an Aquilia app.
- `cli-reference.md`: mounted `aq` commands for this module, if any.
- `examples.md`: usage examples derived from source and checked example apps.
- `edge-cases-and-limitations.md`: implementation limits and compatibility behavior.
- `troubleshooting.md`: diagnostic commands and common failure patterns.
