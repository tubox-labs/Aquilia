# Storage Module

> `aquilia.storage` — Multi-backend async file storage

The Storage module provides async file storage with multiple backends — local filesystem, S3, GCS, Azure Blob, SFTP, in-memory, and composite storage for multi-backend routing.

## When to Use

Use the Storage module when you need:

- File uploads to cloud storage (S3, GCS, Azure)
- Local file system storage for development
- Multi-backend routing (e.g., images to S3, logs to local)
- Async streaming uploads and downloads
- Signed URLs for secure access

## Key Classes

| Class | Purpose |
|---|---|
| `StorageRegistry` | Central registry of storage backends |
| `StorageBackend` | Base class for all backends |
| `StorageFile` | File representation with metadata |
| `StorageMetadata` | File metadata (size, type, hash) |
| `LocalStorage` | Local filesystem backend |
| `MemoryStorage` | In-memory backend (testing) |
| `S3Storage` | AWS S3 backend |
| `GCSStorage` | Google Cloud Storage backend |
| `AzureBlobStorage` | Azure Blob Storage backend |
| `SFTPStorage` | SFTP remote storage backend |
| `CompositeStorage` | Multi-backend router |

## Quick Example

```python
from aquilia.storage import (
    StorageRegistry, S3Storage, S3Config,
    LocalStorage, LocalConfig,
)

registry = StorageRegistry()
registry.register("avatars", S3Storage(S3Config(
    bucket="my-app-avatars",
    region="us-east-1",
)))
registry.register("local", LocalStorage(LocalConfig(
    root="/data/uploads",
)))

# Store a file
storage = registry.get("avatars")
path = await storage.store("user_42/photo.jpg", image_bytes)

# Stream a file
async for chunk in storage.stream(path):
    send(chunk)

# Get a signed URL
url = await storage.signed_url(path, expires_in=3600)
```

## Import Path

```python
from aquilia.storage import (
    StorageRegistry,
    StorageBackend,
    StorageFile,
    StorageMetadata,
    StorageConfig,
    LocalStorage,
    MemoryStorage,
    S3Storage,
    GCSStorage,
    AzureBlobStorage,
    SFTPStorage,
    CompositeStorage,
    LocalConfig,
    MemoryConfig,
    S3Config,
    GCSConfig,
    AzureBlobConfig,
    SFTPConfig,
    CompositeConfig,
)
```

## Related Modules

- [filesystem](../filesystem/index.md) — Local filesystem operations
- [core/effects](../core/effects.md) — StorageEffect for pipeline integration
- [integrations](../integrations/index.md) — StorageIntegration config builder