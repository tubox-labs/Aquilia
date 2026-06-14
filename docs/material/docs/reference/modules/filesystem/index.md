# Filesystem Module

> `aquilia.filesystem` — Async file operations with security hardening

The Filesystem module provides async file I/O operations, including streaming reads/writes, file locking, temporary files, path security validation, and atomic writes.

## When to Use

Use the Filesystem module when you need:

- Async file read/write without blocking the event loop
- Streaming large files in chunks
- File locking for concurrent access safety
- Path traversal protection
- Temporary file management

## Key Classes

| Class | Purpose |
|---|---|
| `FilesystemService` | Main async filesystem service |
| `AsyncFileHandle` | Async file handle with read/write/seek |
| `stream_read` | Streaming file reader |
| `stream_write` | Streaming file writer |

## Quick Example

```python
from aquilia.filesystem import FilesystemService

fs = FilesystemService()

# Read a file
content = await fs.read("/path/to/file.txt")

# Write a file atomically
await fs.write("/path/to/file.txt", b"content")

# Stream a large file
async for chunk in fs.stream_read("/path/to/large.bin", chunk_size=65536):
    process(chunk)

# Path security
safe_path = fs.validate_path("/uploads/user_42/file.txt")
# Raises on null bytes, traversal, or suspicious patterns
```

## Security

- **Null byte detection** — Rejects paths containing `\0`
- **Path traversal prevention** — Rejects `..` traversal attempts
- **Symlink safety** — Configurable symlink following policies
- **Permission validation** — Checks read/write permissions before operations

## Related Modules

- [core/response](../core/response.md) — File responses use filesystem operations
- [storage](../storage/index.md) — Cloud storage backends (S3, GCS, Azure)
- [sqlite](../sqlite/index.md) — Native SQLite file operations