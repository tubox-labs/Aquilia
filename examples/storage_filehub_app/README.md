# Storage File Hub App

## Purpose

Demonstrates a multi-backend file hub using Aquilia storage registry and memory storage backends.

## Architecture

- `workspace.py` declares two memory storage aliases, `documents` and `quarantine`.
- `FileHubService` uses `StorageRegistry.from_config()`.
- The service stores metadata, content type, tenant partitioning, and SHA-256 digests.

## Setup

```bash
python -m pip install -e ".[dev]"
python -m pytest examples/storage_filehub_app -q
```

## Run

```bash
cd examples/storage_filehub_app
python -m uvicorn runtime:app --reload --port 8063
```

## Expected Behavior

Uploads are stored under tenant-prefixed paths and can be listed or downloaded from the configured alias.

## Common Pitfalls

- Storage configs consumed by `StorageRegistry` need a `backend` key.
- Memory storage is intentionally ephemeral; configure local, S3, GCS, Azure, or SFTP for durability.

## Extension Ideas

Add virus scanning, signed URLs, local storage, cloud object storage, and lifecycle archival.

## Related APIs

`StorageRegistry`, `MemoryStorage`, `MemoryConfig`, `StorageMetadata`, `Integration.storage`.
