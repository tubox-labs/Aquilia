# Artifacts Documentation

This directory is the professional documentation set for `artifacts`. It is implementation-driven and aligned with the current source files under `aquilia/artifacts`.

## What This Covers

The typed artifact system used for route, registry, migration, template, model, config, code, and graph artifacts with envelope and integrity metadata.

## Source Files Read

- `aquilia/artifacts/__init__.py`: Aquilia Artifacts -- Unified artifact system for the framework.
- `aquilia/artifacts/builder.py`: Artifact Builder -- fluent API for constructing artifacts.
- `aquilia/artifacts/core.py`: Artifact Core -- the foundational types for Aquilia's artifact system.
- `aquilia/artifacts/kinds.py`: Typed Artifact Kinds -- convenience subclasses with kind-specific helpers.
- `aquilia/artifacts/reader.py`: Artifact Reader -- load, inspect, verify, and query artifacts.
- `aquilia/artifacts/store.py`: Artifact Store -- pluggable storage backends for artifacts.

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

- Python files: 6
- Public classes: 19
- Configuration or dataclass-like types: 3
- Public functions: 2
- Constants detected: 1

## Fast Start

```python
from aquilia.artifacts import __version__, ArtifactBuilder, Artifact, ArtifactEnvelope, ArtifactIntegrity, ArtifactKind

# The imported symbols above are public exports from this module.
# See api-reference.md for constructor signatures, methods, and data fields.
```

## Read Next

Start with `architecture.md` if you are learning how the subsystem fits into runtime boot. Use `api-reference.md` when you need exact methods, datatypes, and class fields. Use `examples.md` for copyable patterns that match the current code.
