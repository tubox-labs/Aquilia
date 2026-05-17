# Aquilary Registry Documentation

This directory is the professional documentation set for `aquilary`. It is implementation-driven and aligned with the current source files under `aquilia/aquilary`.

## What This Covers

The manifest-driven registry layer that validates app manifests, detects dependency cycles, fingerprints runtime graphs, and feeds metadata to the runtime registry.

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

- `architecture.md`: Runtime architecture and module boundaries
- `configuration.md`: Configuration entry points, datatypes, and precedence
- `api-reference.md`: Classes, methods, functions, constants, and data fields extracted from source
- `integration-guide.md`: How to wire the module into a real Aquilia application
- `cli-reference.md`: Command line surface and operational commands
- `edge-cases-and-limitations.md`: Known edge cases and implementation limits
- `troubleshooting.md`: Common failures and diagnosis steps
- `examples.md`: Code examples and usage patterns

## Public Surface Snapshot

- Python files: 10
- Public classes: 29
- Configuration or dataclass-like types: 8
- Public functions: 9
- Constants detected: 0

## Fast Start

```python
from aquilia.aquilary import __version__, AppContext, Aquilary, AquilaryRegistry, RegistryFingerprint, RegistryMode

# The imported symbols above are public exports from this module.
# See api-reference.md for constructor signatures, methods, and data fields.
```

## Read Next

Start with `architecture.md` if you are learning how the subsystem fits into runtime boot. Use `api-reference.md` when you need exact methods, datatypes, and class fields. Use `examples.md` for copyable patterns that match the current code.
