# Artifacts Documentation

Typed artifact envelopes, artifact kinds, integrity metadata, readers, builders, and memory/filesystem stores.

## Coverage Snapshot

- Source files: 6
- Source lines: 1859
- Public classes: 19
- Public module functions: 2
- Constants/module flags: 2
- Public exports in `__all__`: 20

## Source Files Read

- `aquilia/artifacts/__init__.py`: Aquilia Artifacts -- Unified artifact system for the framework.
- `aquilia/artifacts/builder.py`: Artifact Builder -- fluent API for constructing artifacts.
- `aquilia/artifacts/core.py`: Artifact Core -- the foundational types for Aquilia's artifact system.
- `aquilia/artifacts/kinds.py`: Typed Artifact Kinds -- convenience subclasses with kind-specific helpers.
- `aquilia/artifacts/reader.py`: Artifact Reader -- load, inspect, verify, and query artifacts.
- `aquilia/artifacts/store.py`: Artifact Store -- pluggable storage backends for artifacts.

## Document Map

- `architecture.md`: module boundaries, dependencies, lifecycle, and extension points.
- `configuration.md`: configuration classes, builders, server wiring, and precedence.
- `api-reference.md`: source-extracted classes, methods, functions, constants, exports, and signatures.
- `integration-guide.md`: how to wire the module into an Aquilia app.
- `cli-reference.md`: mounted `aq` commands for this module, if any.
- `examples.md`: usage examples derived from source and checked example apps.
- `edge-cases-and-limitations.md`: implementation limits and compatibility behavior.
- `troubleshooting.md`: diagnostic commands and common failure patterns.
