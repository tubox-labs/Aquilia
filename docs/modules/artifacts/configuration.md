# Artifacts Configuration

Typed artifact envelopes, artifact kinds, integrity metadata, readers, builders, and memory/filesystem stores.

This page distinguishes direct configuration APIs from indirect runtime wiring. All class names and source files below are extracted from the current source tree.

## Configuration Model

This module exposes config-oriented public classes. Use the table below to locate exact constructors and `to_dict()` behavior in `api-reference.md`.

## Source Inventory

| File | Lines | Public classes | Public functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/artifacts/__init__.py` | 91 | 0 | 0 | Aquilia Artifacts -- Unified artifact system for the framework. |
| `aquilia/artifacts/builder.py` | 240 | 1 | 0 | Artifact Builder -- fluent API for constructing artifacts. |
| `aquilia/artifacts/core.py` | 416 | 5 | 1 | Artifact Core -- the foundational types for Aquilia's artifact system. |
| `aquilia/artifacts/kinds.py` | 413 | 9 | 0 | Typed Artifact Kinds -- convenience subclasses with kind-specific helpers. |
| `aquilia/artifacts/reader.py` | 250 | 1 | 0 | Artifact Reader -- load, inspect, verify, and query artifacts. |
| `aquilia/artifacts/store.py` | 449 | 3 | 1 | Artifact Store -- pluggable storage backends for artifacts. |

## Detected Config-Oriented Classes

| Class | Source | Methods | Summary |
| --- | --- | --- | --- |
| `ArtifactBuilder` | `aquilia/artifacts/builder.py` | `from_artifact`, `set_payload`, `merge_payload`, `set_metadata`, `tag`, `tags`, `set_provenance`, `auto_provenance`, `add_file`, `set_version`, `build` | Fluent builder for creating :class:`Artifact` instances. |
| `ConfigArtifact` | `aquilia/artifacts/kinds.py` | `build`, `config`, `get` | Frozen configuration snapshot. |

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
