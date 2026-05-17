# artifacts Module

## Purpose

Typed artifact envelopes and stores. Use this module to persist generated routes, migrations, templates, model packs, registries, graphs, and other framework artifacts with integrity metadata.

## Source Coverage

- Python files: 6
- Public classes: 19
- Dataclasses: 3
- Enums: 1
- Public functions: 2

## How It Fits In Aquilia

1. Import the package from `aquilia.artifacts` or its concrete submodules.
2. Configure it through workspace integrations, manifests, or direct service construction depending on the subsystem.
3. Keep business logic outside transport and framework glue so the subsystem stays testable.

## Practical Guidance

- Prefer typed configuration objects and framework helpers over ad hoc dictionaries when they exist.
- Use the tests in `tests/` as behavioral examples when changing this subsystem.

## Public Classes

| Name | Source | Role |
| --- | --- | --- |
| `ArtifactBuilder` | `aquilia/artifacts/builder.py` | Fluent builder for creating :class:`Artifact` instances. |
| `ArtifactKind` | `aquilia/artifacts/core.py` | Standard artifact kinds recognised by the framework. |
| `ArtifactIntegrity` | `aquilia/artifacts/core.py` | Content-addressed integrity proof. |
| `ArtifactProvenance` | `aquilia/artifacts/core.py` | Where and when the artifact was produced. |
| `ArtifactEnvelope` | `aquilia/artifacts/core.py` | The outer envelope that wraps every artifact's serialised form. |
| `Artifact` | `aquilia/artifacts/core.py` | First-class Aquilia artifact. |
| `ConfigArtifact` | `aquilia/artifacts/kinds.py` | Frozen configuration snapshot. |
| `CodeArtifact` | `aquilia/artifacts/kinds.py` | Compiled module / controller / service artifact. |
| `ModelArtifact` | `aquilia/artifacts/kinds.py` | ML model artifact. |
| `TemplateArtifact` | `aquilia/artifacts/kinds.py` | Compiled template artifact. |
| `MigrationArtifact` | `aquilia/artifacts/kinds.py` | Database migration checkpoint artifact. |
| `RegistryArtifact` | `aquilia/artifacts/kinds.py` | Module registry catalog artifact. |
| `RouteArtifact` | `aquilia/artifacts/kinds.py` | Compiled routing table artifact. |
| `DIGraphArtifact` | `aquilia/artifacts/kinds.py` | Compiled dependency injection graph artifact. |
| `BundleArtifact` | `aquilia/artifacts/kinds.py` | Artifact bundle -- a container that holds multiple artifacts. |
| `ArtifactReader` | `aquilia/artifacts/reader.py` | High-level artifact reader / inspector. |
| `ArtifactStoreProtocol` | `aquilia/artifacts/store.py` | Minimal interface every store must implement. |
| `MemoryArtifactStore` | `aquilia/artifacts/store.py` | Ephemeral in-memory artifact store. |
| `FilesystemArtifactStore` | `aquilia/artifacts/store.py` | Persistent filesystem artifact store. |

## Public Functions

| Name | Source | Role |
| --- | --- | --- |
| `register_artifact_kind` | `aquilia/artifacts/core.py` | Register a typed subclass so ``Artifact.from_dict`` auto-resolves. |
| `ArtifactStore` | `aquilia/artifacts/store.py` | Convenience constructor -- returns a :class:`FilesystemArtifactStore`. |

## Implementation Map

| File | What To Look For |
| --- | --- |
| `aquilia/artifacts/__init__.py` | Aquilia Artifacts -- Unified artifact system for the framework. |
| `aquilia/artifacts/builder.py` | Artifact Builder -- fluent API for constructing artifacts. |
| `aquilia/artifacts/core.py` | Artifact Core -- the foundational types for Aquilia's artifact system. |
| `aquilia/artifacts/kinds.py` | Typed Artifact Kinds -- convenience subclasses with kind-specific helpers. |
| `aquilia/artifacts/reader.py` | Artifact Reader -- load, inspect, verify, and query artifacts. |
| `aquilia/artifacts/store.py` | Artifact Store -- pluggable storage backends for artifacts. |

## Testing Pointers

Search `tests/` for `artifacts` to find behavior-level examples. The test suite is especially useful for edge cases because many modules expose lightweight public APIs but enforce important security and lifecycle behavior internally.
