# Artifact Store Deep Dive

The **Artifact Subsystem** (`aquilia.artifacts`) is a new foundational layer in Aquilia v1.3.6 designed to manage all generated data — from discovery caches to compiled bytecode. 

## Why it was built

Historically, each Aquilia subsystem managed its own caching and file I/O. The discovery engine wrote a JSON file, the template engine wrote a different JSON file and a custom HMAC format for bytecode, and the WebSocket compiler wrote another file. 
This led to:
- Inconsistent file locations (some in `artifacts/`, some in project root).
- Varying levels of atomic write guarantees (some used `mkstemp` + `replace`, some just `write_text`).
- No unified way to inspect, verify, or clean up generated data.

The Artifact Store centralizes this, providing a unified API with robust integrity and concurrency guarantees.

## Architecture Overview

The subsystem is composed of several key components:

1. **`ArtifactStore`**: The primary async facade for reading, writing, and managing artifacts.
2. **`ArtifactEnvelope`**: The canonical JSON wire format that wraps every payload.
3. **`JSONFileBackend` & `MemoryBackend`**: The physical storage layer.
4. **`ArtifactRegistry`**: The central registry of known artifact types.
5. **Canonicalization & Integrity**: Core logic for fingerprinting and HMAC signing.

### ArtifactStore

The `ArtifactStore` provides an async interface for all artifact operations.

```python
from aquilia.artifacts import provide_artifact_store

store = provide_artifact_store()

# Async API
await store.put("discovery_cache", "main", payload_dict)
envelope = await store.get("discovery_cache", "main")
await store.verify("templates.bytecode")
await store.prune()
```

It also supports an **`ArtifactTransaction`** for all-or-nothing multi-artifact commits:

```python
async with store.transaction() as tx:
    await tx.put("discovery_cache", "main", discovery_data)
    await tx.put("route_index", "main", route_data)
# Both are committed atomically at the end of the block.
```

### JSONFileBackend

`JSONFileBackend` handles the actual disk I/O, ensuring absolute safety against partial writes and concurrent access.

- **Atomic Writes**: Uses `tempfile.mkstemp` to write a temporary file, `os.fsync` to flush it to disk, and `os.replace` to atomically move it into place.
- **Signed Mode**: If `signed=True`, the backend computes an HMAC-SHA256 signature using the active secret key, appending it to the top of the file: `<64-char-hex-HMAC>\n<JSON>`.

### ArtifactEnvelope Wire Format

Every artifact written to disk (except signed files, which prepend the HMAC) is a strict JSON document matching the `ArtifactEnvelope` format:

```json
{
  "format": "aquilia-artifact",
  "artifact_type": "discovery_cache",
  "schema_version": "1.0",
  "key": "main",
  "fingerprint": "sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
  "created_at": "2026-07-29T17:00:00Z",
  "payload": { 
      "modules": [...],
      "routes": [...]
  }
}
```

This ensures that any tool, inside or outside of Aquilia, can safely parse, identify, and verify the age/schema of any artifact.

### ArtifactRegistry

The `ArtifactRegistry` keeps track of what artifacts exist and how to handle them.

```python
from aquilia.artifacts import register_artifact_type, ArtifactTypeDescriptor

register_artifact_type(ArtifactTypeDescriptor(
    name="my_custom_cache",
    schema_version="1.0",
    signed=False
))
```

There are currently 10 registered types in Aquilia: `discovery_cache`, `frozen_registry`, `schema_snapshot`, `ws_metadata`, `template_manifest`, `mcp_knowledge_index`, `template_bytecode`, `di_manifest`, `route_index`, `migration_file`.

## Dependency Injection

The store is available via the DI container with an app-scoped provider:

```python
from aquilia.artifacts import ArtifactStoreProvider

# Available automatically in controllers/services:
class MyService:
    store: ArtifactStore = Inject(ArtifactStore)
```

## CLI: `aq artifacts`

A new command group allows you to manage the store from the terminal:

- `aq artifacts status [--root PATH]`: Lists all registered artifact types, showing which are present on disk, file size, last modified time, and schema version.
- `aq artifacts verify [PATH] [--root PATH]`: Verifies the integrity of one or all artifacts, strictly checking the HMAC for signed types.
- `aq artifacts clean [--root PATH] [--orphaned-only]`: Removes stale, corrupted, or orphaned artifacts.

## Configuration

The root directory defaults to `.aquilia/artifacts` in your project root. You can override this globally:

```toml
# pyproject.toml
[aquilia.artifacts]
root = "/var/lib/myapp/artifacts"
```

Or via environment variable:
```bash
export AQUILIA_ARTIFACT_ROOT=/var/lib/myapp/artifacts
```
