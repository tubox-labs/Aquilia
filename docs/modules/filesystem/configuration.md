# Filesystem Configuration

## Configuration Entry Points

The implementation exposes the following configuration-like classes, policies, integrations, or dataclasses.

| Type | Source | Fields | Purpose |
| --- | --- | --- | --- |
| `FileSystemConfig` | `aquilia/filesystem/_config.py` | min_pool_threads: int, max_pool_threads: int, write_buffer_size: int, default_chunk_size: int, max_path_length: int, follow_symlinks: bool, sandbox_root: str &#124; None, atomic_writes: bool, fsync_on_write: bool, enable_metrics: bool, temp_dir: str &#124; None, max_recursion_depth: int, ... | Configuration for the Aquilia filesystem module. |
| `DirEntry` | `aquilia/filesystem/_directory.py` | name: str, path: str, is_file_cached: bool, is_dir_cached: bool, is_symlink_cached: bool, inode: int | Async-friendly directory entry (mirrors ``os.DirEntry``). |
| `FileSystemMetrics` | `aquilia/filesystem/_metrics.py` | reads: int, writes: int, deletes: int, copies: int, moves: int, stats: int, directory_ops: int, errors: int, bytes_read: int, bytes_written: int, read_latency_ns: int, write_latency_ns: int, ... | Aggregated filesystem operation metrics. |
| `FileStat` | `aquilia/filesystem/_ops.py` | size: int, mode: int, uid: int, gid: int, atime_ns: int, mtime_ns: int, ctime_ns: int, is_file: bool, is_dir: bool, is_symlink: bool | File status information. |

## Common Entry Points

- No dedicated workspace integration was detected from module naming. Configure this module through direct constructors, manifests, or the subsystem that owns it.

## Precedence Model

Aquilia generally resolves configuration in this order:

1. Explicit constructor arguments or typed integration dataclass values.
2. `Workspace` builder methods and `Workspace.integrate(...)` output.
3. `ConfigLoader` defaults and environment overlays.
4. Runtime defaults inside the subsystem service or provider constructor.

When this module is registered through an `AppManifest`, keep component declarations inside `modules/<name>/manifest.py` and keep cross-cutting integration settings in `workspace.py`.

## Datatype Guidance

- Prefer typed dataclasses, policy objects, and config objects listed above when they exist.
- Keep secret values in environment-backed config, not literal strings in committed workspace files.
- Keep runtime-only state in services, stores, providers, or request state rather than static configuration.
- Use `to_dict()` on integration dataclasses when you need to inspect exactly what enters `ConfigLoader`.
