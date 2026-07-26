# Storage & Filesystem Audit Fixes

This document details the fixes applied to the `aquilia.storage` and `aquilia.filesystem` subsystems in Aquilia v1.3.4, addressing findings from the Cache & Storage architectural audit.

Aquilia ships two related but distinct systems here: `aquilia.filesystem` (low-level local async I/O — `AsyncPath`, streaming, locks, tempfiles, a dedicated thread pool, and a sandbox validator) and `aquilia.storage` (a pluggable, cloud-aware abstraction with Local/Memory/S3/GCS/Azure/SFTP/Composite backends). The audit's central finding was that the two halves did not share a path-containment implementation: it had been written twice, correctly once and incorrectly once. This release unifies them.

## §B1 Streaming Path Bypassed Sandbox Validation Entirely (CRITICAL — SECURITY)

**Previous Behavior:**
Every entry point in `aquilia/filesystem/_ops.py` called `validate_path()` before touching disk. `aquilia/filesystem/_streaming.py` — the module built specifically for large-file I/O — did not. `stream_copy()` and `stream_read()` accepted `config` and `sandbox` keyword arguments that visually mirrored the protected helpers, but neither was ever passed to `validate_path`; `_security` was not even imported. `AsyncFileStream` and `AsyncWriteStream` accepted no sandbox parameter at all.

The public `FileSystem` facade exposed the gap directly, with identical method shapes on both sides:

```python
await fs.read_file(path, sandbox=uploads_root)     # validated
async for chunk in fs.stream_read(path, sandbox=uploads_root):
    ...                                            # NOT validated — silently ignored
```

**Root Cause:**
The parameters were added to the streaming signatures for API parity but never wired to the validator. Nothing failed loudly, so no test caught it.

**User Impact (before the fix):**
Complete path-traversal exposure on the code path recommended for the highest-risk feature — large user-uploaded and downloaded files — with no error and no warning. A developer reasonably assuming parity between `read_file(sandbox=...)` and `stream_read(sandbox=...)` got no protection on the second call. This was the most severe finding in the audit.

**Fix:**
`AsyncFileStream` and `AsyncWriteStream` now validate and canonicalise their path at construction, before any descriptor is opened, and expose the resolved path as a `path` property. `stream_read` and `stream_copy` thread `config` and `sandbox` through to them; `stream_copy` validates source and destination independently.

```python
self._path = validate_path(
    path,
    config=cfg,
    sandbox=sandbox or cfg.sandbox_root,
    operation="stream_read",
)
```

**User Impact (after the fix):**
`sandbox=` on streaming methods now does what its name says. Code that streamed outside its declared sandbox — previously silent — now raises `PathTraversalFault`. Review any such call site before upgrading; a raise here indicates the traversal was already happening unchecked.

## §B2 Directory Operations Raised `TypeError` on Every Call (CRITICAL — BUG)

**Previous Behavior:**
`FileSystem.list_dir`, `scan_dir`, `make_dir`, `remove_dir`, and `remove_tree` passed `config=` and `sandbox=` to the `_directory` module, whose functions accepted neither:

```text
TypeError: list_dir() got an unexpected keyword argument 'config'
```

Every directory method on the DI-injectable facade was unusable — not degraded, but unconditionally broken.

**Fix:**
All `_directory` functions now accept `config` and `sandbox` and validate through the shared `validate_path` before touching the OS, closing the same class of hole as §B1. `copy_tree` validates both paths. `walk` validates its root. `FileSystem` gained the missing `copy_tree` and `walk` methods and now forwards `ignore_errors` to `remove_tree`.

**User Impact:**
Directory operations work, and are sandbox-enforced on the same terms as file operations.

## §B3 `LocalStorage` Used a Vulnerable Prefix Containment Check (CRITICAL — SECURITY)

**Previous Behavior:**

```python
def _full_path(self, name: str) -> Path:
    full = (self._root / name).resolve()
    if not str(full).startswith(str(self._root)):
        raise PermissionError(...)
    return full
```

`_normalize_path()` rejected `..` segments and null bytes upstream, blocking naive payloads. The containment check itself was the classic sibling-directory bypass: with a root of `/var/data`, the resolved path `/var/data-private/secret.txt` satisfies `str.startswith("/var/data")` even though it is not inside the root.

**Root Cause:**
The framework's own `aquilia/filesystem/_security.py` already handled this correctly, with a comment naming the exact pitfall. `storage/backends/local.py` did not import it — it reimplemented sandboxing independently, and incorrectly. Duplicated security logic, one copy right and one wrong.

**Fix:**
`LocalStorage` now delegates to the single canonical validator, which resolves symlinks and compares path *components* rather than string prefixes, and translates the resulting fault into the storage error taxonomy:

```python
try:
    return _validate_path(
        self._root / name,
        config=self._fs_config,
        sandbox=self._root,
        operation="storage.local",
    )
except _PathTraversalFault as exc:
    raise PermissionError(
        f"Path traversal blocked: {name}", backend="local", path=str(name)
    ) from exc
```

**User Impact:**
Sibling-directory escape is blocked. Verified: a symlink planted under the root pointing at `/var/data-private` is rejected with `PermissionError`; ordinary nested paths are unaffected. This is the structural fix that prevents the whole bug class from recurring — there is now exactly one containment implementation in the framework.

## §B4 Sandboxing Was Opt-In, Not Secure-by-Default (SECURITY)

**Previous Behavior:**
`FileSystemConfig.sandbox_root` defaulted to `None`, and `validate_path()` skipped containment entirely when it was unset. The framework's default posture was "no traversal protection unless explicitly configured", and an application that forgot to set a root got silence rather than a warning.

**Fix:**
A new `allow_unsandboxed` field (default `True`, preserving current behaviour for CLI and tooling use) makes the insecure combination impossible to ship *accidentally*. Setting `allow_unsandboxed=False` without a `sandbox_root` is rejected at construction with an actionable `ConfigInvalidFault`, and `validate_path` raises `PermissionDeniedFault` if it is ever asked to operate without a sandbox under that setting.

```python
# recommended for any application resolving user-supplied paths
FileSystemConfig(sandbox_root="/srv/uploads", allow_unsandboxed=False)
```

**User Impact:**
Existing code is unaffected by default. Applications can now opt into a fail-loudly posture instead of silently running unprotected.

## §B5 `follow_symlinks` Overlapped Confusingly with Security Resolution (DOCS)

**Previous Behavior:**
`FileSystemConfig.follow_symlinks` controlled whether `stat()` and directory scans described a link or its target. It was never consulted by `validate_path()`, which always resolves via `os.path.realpath` before checking containment. The security behaviour was correct — resolving before containment is mandatory — but the config surface read as though one unified symlink policy existed when there were two independent ones.

**Fix:**
No behaviour change. `validate_path`'s docstring now states explicitly that symlinks are always resolved for the containment check regardless of the flag, and that the flag governs metadata semantics only.

**User Impact:**
Documentation clarity. Verified by test: containment holds identically for `follow_symlinks=True` and `False`.

## §B6 Local and S3 Backends Fully Buffered File Contents (PERF)

**Previous Behavior:**
`storage/base.py` documented the design principle *"Streaming: `save` and `open` accept/return async iterators"* and *"No intermediate full-file materialisation"*. In practice `LocalStorage.open()` called `full.read_bytes()` and `S3Storage.open()` called `response["Body"].read()` — both loading the entire object into memory before returning a `StorageFile` described as supporting `async for chunk in sf`. Multi-gigabyte transfers risked out-of-memory failures under concurrent access, defeating the purpose of the streaming API.

**Fix:**
`LocalStorage` now reads and writes through `aquilia.filesystem`'s streaming primitives, and `S3Storage` iterates the boto3 `StreamingBody` in chunks. Both return a lazily-backed `StorageFile`; content is materialised only if the caller explicitly calls `read()`.

```python
async with await storage.open("large.bin") as f:
    async for chunk in f:        # bounded to one chunk in memory
        await sink.write(chunk)
```

`LocalStorage.save` and `copy` stream as well, and `StorageBackend.copy` forwards the open file as a chunk iterator rather than materialising it.

**User Impact:**
Memory stays bounded for large objects. `StorageFile.size` still reports the correct size before any read, from metadata. Verified: a 200 KB object yields multiple chunks with `content is None` until read.

## §B7 S3 Had No Multipart Upload and Shared the Default Executor (SCALE)

**Previous Behavior:**
`S3Storage` used `put_object` for all uploads — a hard 5 GB limit, no chunking, no resumability. Every operation called `asyncio.get_event_loop().run_in_executor(None, ...)`, placing storage traffic on the interpreter's *shared default* executor alongside unrelated library code, with no way to size or observe it. `asyncio.get_event_loop()` is also the deprecated idiom inside a coroutine.

**Fix:**
Two changes. First, a dedicated bounded pool in the new `aquilia/storage/executor.py`, mirroring the discipline of `FileSystemPool`, with named threads (`aquilia-storage`) and an `AQUILIA_STORAGE_MAX_WORKERS` override. All five SDK-backed backends (S3, GCS, Azure, SFTP) and `StorageBackend._read_content` now route through `run_blocking()`; no `run_in_executor(None, ...)` or `get_event_loop()` remains in the storage tree.

Second, real multipart upload. Payloads at or above `S3Config.multipart_threshold` upload in parts of `multipart_chunk_size`, lifting the single-request limit and bounding peak memory to one part. A failed part aborts the multipart upload before re-raising, so no incomplete upload is left billing.

New configuration: `multipart_threshold` (default 8 MiB) and `multipart_chunk_size` (default 8 MiB, S3 minimum 5 MiB).

**User Impact:**
Objects larger than 5 GB upload successfully. Storage I/O no longer competes with unrelated thread-pool work and can be sized per deployment. The pool is shut down with the server and transparently recreated if used afterwards.

## §B8 Dynamic Backend Import Is a Trust Boundary (DOCS)

**Previous Behavior:**
`StorageRegistry.create_backend()` treats any dotted `backend` value as an importable class path and loads it via `importlib`. This is a legitimate and useful extensibility mechanism, but it is effectively an arbitrary-module-load primitive and that was not stated anywhere.

**Fix:**
No behaviour change — the mechanism is intentional. `create_backend`, `StorageSubsystem`, and `Server._setup_storage` now document explicitly that storage configuration is trusted deployment input and must never be derived from untrusted or request-supplied data.

**User Impact:**
The trust boundary is stated where an integrator will encounter it.

## §B9 Registry Lifecycle Was All-or-Nothing (BUG)

**Previous Behavior:**
`initialize_all()` awaited each backend without error handling, so one unreachable optional backend (a misconfigured CDN bucket, say) aborted the entire storage subsystem and took down every other disk with it. `shutdown_all()` swallowed exceptions with a bare `except Exception: pass`, discarding diagnostics.

**Fix:**
Failure handling now matches the criticality of the backend. A failing **default** backend raises `BackendUnavailableError` — the application cannot serve without it. A failing **non-default** backend is logged and left uninitialised; its `ping` reports unhealthy and the rest of the application starts. Shutdown continues past a failing backend and logs rather than silently swallowing.

**User Impact:**
One bad optional disk no longer prevents boot, and failures are visible in logs and health output instead of vanishing.

## Related Documentation

- [Cache System Audit Fixes](cache_audit.md)
- [Subsystem Lifecycle & Health](subsystem_lifecycle.md)
- [Migration Guide](migration.md)
