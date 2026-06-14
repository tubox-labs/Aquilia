# Storage File Hub

The Storage File Hub example demonstrates a multi-backend file hub using Aquilia's
storage registry with memory storage backends, metadata tracking, tenant partitioning,
and SHA-256 content digests.

---

## What It Demonstrates

- `StorageIntegration` with multiple named backends (`documents`, `quarantine`)
- `StorageRegistry.from_config()` for building a backend registry from configuration
- Memory storage backends with size limits
- Tenant-prefixed storage paths for multi-tenant isolation
- `StorageMetadata` with content type, size, and SHA-256 digest tracking
- Upload, list, download, and delete file operations
- Alias-based backend selection for different storage tiers

## Key Files

| File | Purpose |
| ---- | ------- |
| `workspace.py` | Declares two memory storage aliases with size limits |
| `modules/files/manifest.py` | Declares `FilesController` and `FileHubService` |
| `modules/files/controllers.py` | Upload, list, download, and delete endpoints |
| `modules/files/services.py` | `FileHubService` using `StorageRegistry` |

## Workspace Configuration

```python
from aquilia.integrations import DiIntegration, StorageIntegration

workspace = (
    Workspace("storage-filehub-app", version="1.0.0")
    .runtime(mode="dev", host="127.0.0.1", port=8063, reload=True)
    .module(Module("files", version="1.0.0").route_prefix("/files").tags("storage"))
    .integrate(StorageIntegration(default="documents", backends={
        "documents": {"backend": "memory", "max_size": 1048576},
        "quarantine": {"backend": "memory", "max_size": 262144},
    }))
    .integrate(DiIntegration(auto_wire=True))
)
```

Each backend alias has its own configuration:

| Setting | `documents` | `quarantine` |
| ------- | ----------- | ------------ |
| `backend` | `memory` | `memory` |
| `max_size` | 1,048,576 bytes (1 MB) | 262,144 bytes (256 KB) |

## Storage Service Pattern

```python
class FileHubService:
    def __init__(self, config: dict[str, Any] | None = None):
        config = config or {"documents": {"backend": "memory"}, "quarantine": {"backend": "memory"}}
        self._registry = StorageRegistry.from_config(config)
        self._metadata: dict[str, StorageMetadata] = {}

    async def upload(self, tenant: str, filename: str, content: bytes, content_type: str = "application/octet-stream", *, quarantine: bool = False) -> dict:
        backend_name = "quarantine" if quarantine else "documents"
        path = self._tenant_path(tenant, filename)
        metadata = StorageMetadata(
            path=path,
            content_type=content_type,
            size=len(content),
            digest=hashlib.sha256(content).hexdigest(),
        )
        await self._registry.get(backend_name).store(path, content)
        self._metadata[path] = metadata
        return metadata.to_dict()

    @staticmethod
    def _tenant_path(tenant: str, filename: str) -> str:
        return f"{tenant}/{filename}"
```

## Storage Metadata

Every file operation tracks metadata:

```python
StorageMetadata(
    path="tenant_a/invoice.pdf",          # Tenant-scoped path
    content_type="application/pdf",       # MIME type
    size=245760,                          # File size in bytes
    digest="abc123...",                   # SHA-256 hex digest
    stored_at="2026-06-14T12:00:00Z",    # Timestamp
)
```

## Running

```bash
cd examples/storage_filehub_app
python -m uvicorn runtime:app --reload --port 8063
```

```bash
# Upload a file to documents backend
curl -X POST http://127.0.0.1:8063/files/upload \
  -H "Content-Type: application/json" \
  -d '{"tenant":"acme","filename":"invoice.txt","content":"SGVsbG8gV29ybGQ=","content_type":"text/plain"}'

# Upload to quarantine backend
curl -X POST http://127.0.0.1:8063/files/upload \
  -H "Content-Type: application/json" \
  -d '{"tenant":"acme","filename":"suspect.bin","content":"AAAA","content_type":"application/octet-stream","quarantine":true}'

# List files
curl http://127.0.0.1:8063/files/list

# Download a file
curl http://127.0.0.1:8063/files/download/documents/tenant/invoice.txt

# Run tests
python -m pytest examples/storage_filehub_app -q
```

## What You'll Learn

- How to configure multi-backend storage with `StorageIntegration`
- How to build a `StorageRegistry` from configuration
- How to implement tenant-prefixed paths for multi-tenant isolation
- How to track file metadata including SHA-256 digests
- How to use different backend aliases for different storage tiers (documents vs. quarantine)
- How memory backends work for development and testing