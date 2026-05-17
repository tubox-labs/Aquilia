---
name: aquilia-cache-storage-filesystem
description: "Build Aquilia cache, storage, and native filesystem workflows. Use for CacheService/backends/decorators, StorageConfig/backends/registry/effects, local/S3/GCS/Azure/SFTP/memory storage, and aquilia.filesystem async file operations/security."
---

# Aquilia Cache Storage Filesystem

## Purpose
Use Aquilia's implemented cache, storage, and filesystem layers for data, blobs, and async file operations.

## Trigger Conditions
Use for cache configuration, `@cached`, invalidation, memory/redis/composite cache, storage backends, file uploads/downloads, path traversal protection, async open/read/write/copy/move/delete, or storage effects.

## Inputs
- Cache backend, TTL, namespace, key builder, serializer, and secret key if needed.
- Storage backend config: local, memory, S3, GCS, Azure Blob, SFTP, or composite.
- File paths, roots, streaming requirements, and security constraints.

## Execution Flow
1. Configure cache through `Integration.cache(...)` or cache-specific config; use `CacheService` and decorators for app code.
2. Configure storage through `Workspace.storage(...)` or `Integration.storage(...)`; create backends via storage registry.
3. Use `aquilia.filesystem` async helpers for local filesystem work with validation.
4. For user-controlled paths, validate/sanitize with filesystem and storage security helpers.
5. Test with memory/local backends before cloud backends.

## Constraints
- Do not bypass path validation for user-controlled names.
- Redis cache/socket backends require optional redis dependencies.
- Cloud storage providers require credentials and optional SDKs; keep credentials out of generated code.

## Implementation Anchors
`aquilia/cache/`, `aquilia/storage/`, `aquilia/filesystem/`, `aquilia/storage/backends/`, `aquilia/cache/backends/`, `tests/test_storage_system.py`, `tests/test_filesystem_comprehensive.py`, `examples/cache_http_edge_app/`, `examples/storage_filehub_app/`.

## Examples
- Add `Integration.cache(backend="memory", default_ttl=300)`.
- Configure local storage with root `var/uploads`.
- Use `await write_file(path, data)` after validating relative paths.

## Failure Handling
Cache serialization failures map to cache faults. Storage missing files use storage faults, not builtin exceptions. Path traversal and null byte attempts should be rejected before I/O.
