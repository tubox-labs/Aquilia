# Filesystem Configuration

Native async filesystem API, file handles, directory operations, streaming, locks, temporary files, path security, metrics, and service facade.

This page distinguishes direct configuration APIs from indirect runtime wiring. All class names and source files below are extracted from the current source tree.

## Configuration Model

This module exposes config-oriented public classes. Use the table below to locate exact constructors and `to_dict()` behavior in `api-reference.md`.

## Source Inventory

| File | Lines | Public classes | Public functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/filesystem/__init__.py` | 269 | 0 | 0 | Aquilia Filesystem — High-performance native async file I/O. |
| `aquilia/filesystem/_config.py` | 114 | 1 | 0 | Filesystem Configuration — Typed, frozen dataclass for module settings. |
| `aquilia/filesystem/_directory.py` | 356 | 1 | 7 | Directory Operations — Async wrappers for directory manipulation. |
| `aquilia/filesystem/_errors.py` | 281 | 11 | 1 | Filesystem Errors — Typed fault hierarchy for file operations. |
| `aquilia/filesystem/_handle.py` | 357 | 1 | 0 | Async File Handle — Core I/O primitive for the Aquilia filesystem module. |
| `aquilia/filesystem/_lock.py` | 252 | 2 | 0 | Async File Locking — Advisory file locks for concurrent access safety. |
| `aquilia/filesystem/_metrics.py` | 163 | 1 | 0 | Filesystem Metrics — Lightweight operation counters and latency tracking. |
| `aquilia/filesystem/_ops.py` | 573 | 1 | 9 | Convenience Filesystem Operations — High-level async file I/O functions. |
| `aquilia/filesystem/_path.py` | 525 | 1 | 0 | Async Path — Async equivalent of ``pathlib.Path``. |
| `aquilia/filesystem/_pool.py` | 170 | 1 | 0 | Filesystem Thread Pool — Dedicated executor for blocking file I/O. |
| `aquilia/filesystem/_security.py` | 244 | 0 | 3 | Filesystem Security — Path validation, sanitization, and sandbox enforcement. |
| `aquilia/filesystem/_service.py` | 495 | 1 | 0 | FileSystem Service — DI-injectable facade for async file operations. |
| `aquilia/filesystem/_streaming.py` | 308 | 2 | 2 | Streaming Pipeline — High-performance async file streaming. |
| `aquilia/filesystem/_tempfile.py` | 210 | 2 | 0 | Async Temporary Files — Secure temporary file and directory management. |

## Detected Config-Oriented Classes

| Class | Source | Methods | Summary |
| --- | --- | --- | --- |
| `FileSystemConfig` | `aquilia/filesystem/_config.py` | `effective_max_pool_threads`, `from_dict` | Configuration for the Aquilia filesystem module. |

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
