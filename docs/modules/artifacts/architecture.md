# Artifacts Architecture

Typed artifact envelopes, artifact kinds, integrity metadata, readers, builders, and memory/filesystem stores.

## Source Boundaries

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/artifacts/__init__.py` | 91 | 0 | 0 | Aquilia Artifacts -- Unified artifact system for the framework. |
| `aquilia/artifacts/builder.py` | 240 | 1 | 0 | Artifact Builder -- fluent API for constructing artifacts. |
| `aquilia/artifacts/core.py` | 416 | 5 | 1 | Artifact Core -- the foundational types for Aquilia's artifact system. |
| `aquilia/artifacts/kinds.py` | 413 | 9 | 0 | Typed Artifact Kinds -- convenience subclasses with kind-specific helpers. |
| `aquilia/artifacts/reader.py` | 250 | 1 | 0 | Artifact Reader -- load, inspect, verify, and query artifacts. |
| `aquilia/artifacts/store.py` | 449 | 3 | 1 | Artifact Store -- pluggable storage backends for artifacts. |

## Internal Shape

`artifacts` has 6 Python files, 19 public classes, 2 public module-level functions, and 2 constants or module flags detected by AST.

## Runtime Responsibilities

- This module has `aq` command coverage documented in `cli-reference.md`; 11 commands map to this subsystem.

## Internal Imports

| Import | Count |
| --- | ---: |
| `.core` | 6 |
| `.builder` | 2 |
| `.store` | 2 |
| `.kinds` | 1 |
| `.reader` | 1 |
| `aquilia._version` | 1 |

## External And Stdlib Imports

| Import root | Count |
| --- | ---: |
| `__future__` | 5 |
| `json` | 4 |
| `typing` | 4 |
| `logging` | 2 |
| `dataclasses` | 1 |
| `datetime` | 1 |
| `enum` | 1 |
| `hashlib` | 1 |
| `pathlib` | 1 |
| `subprocess` | 1 |

## Lifecycle And Extension Points

| Extension Type | Source | Role |
| --- | --- | --- |
| `ConfigArtifact` | `aquilia/artifacts/kinds.py` | Frozen configuration snapshot. |
| `RegistryArtifact` | `aquilia/artifacts/kinds.py` | Module registry catalog artifact. |
| `ArtifactStoreProtocol` | `aquilia/artifacts/store.py` | Minimal interface every store must implement. |
| `MemoryArtifactStore` | `aquilia/artifacts/store.py` | Ephemeral in-memory artifact store. |
| `FilesystemArtifactStore` | `aquilia/artifacts/store.py` | Persistent filesystem artifact store. |

## Error Handling

This module does not define public `Fault` or `Error` classes in its own files. Errors are usually raised through shared `aquilia.faults` domains or consuming subsystems.
