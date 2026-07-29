# Aquilia v1.3.6 Release Notes — "Artifact Forge"

Aquilia v1.3.6 introduces the **Artifact Subsystem** — a unified, production-grade infrastructure for all framework-generated metadata, build outputs, indexes, compiled representations, and caches.

Before this release, framework artifacts like template bytecode, discovery caches, and MCP indexes were scattered across different files, sometimes in an `artifacts/` directory at the project root, and sometimes wherever the subsystem decided. They used varying file formats and I/O strategies, which occasionally led to inconsistent atomic writes.

This release unifies all of this under a single `.aquilia/artifacts/` directory and a standardized `ArtifactEnvelope` JSON format. It guarantees atomic writes across all producers, introduces HMAC-SHA256 signatures for integrity (like the bytecode cache), and provides a new `aq artifacts` CLI to manage them.

The new artifact infrastructure is entirely transparent to most applications, but if you have tooling that expects artifacts in specific paths or legacy formats, you may need to update them.

---

## Table of Contents

1. [Artifact Store Deep Dive](artifact_store.md)
   - `aquilia.artifacts` architecture
   - `ArtifactStore` and `ArtifactEnvelope` APIs
   - `JSONFileBackend` atomic writes and HMAC-SHA256 signing
   - The `aq artifacts` CLI commands
2. [Unified Artifact Directory](unified_artifact_directory.md)
   - Consolidation from `artifacts/` to `.aquilia/artifacts/`
   - Complete directory layout
   - Configuration via `[aquilia.artifacts]` and `AQUILIA_ARTIFACT_ROOT`
3. [Producer Migrations](producer_migrations.md)
   - How `DiscoveryCache`, `JSONBytecodeCache`, etc. were migrated
   - Backward compatibility for legacy formats
4. [Bug Fixes](bugfixes.md)
   - Centralized atomic write guarantees
   - HMAC verification fixes
5. [Migration Guide](migration.md)
   - Upgrade checklist and breaking changes
   - Handling the path and format changes

---

## Highlights

### Unified Artifact Directory

All framework artifacts now live under `.aquilia/artifacts/` instead of scattering across the project root.

```bash
# Before:
# artifacts/templates.bytecode.json
# artifacts/ws.json
# ...

# After:
# .aquilia/artifacts/templates.bytecode.json
# .aquilia/artifacts/ws.json
# .aquilia/artifacts/discovery_cache.json
# ...
```

### The `aq artifacts` CLI

Manage all your framework artifacts with the new command group:

```bash
aq artifacts status           # See what's on disk, sizes, schemas
aq artifacts verify           # Verify HMAC signatures and integrity
aq artifacts clean            # Remove stale/orphaned artifacts
```

### Standardized Wire Format

Every artifact now uses the `ArtifactEnvelope` canonical format, providing clear schema versioning and traceability.

```json
{
  "format": "aquilia-artifact",
  "artifact_type": "discovery_cache",
  "schema_version": "1.0",
  "key": "main",
  "fingerprint": "sha256:...",
  "created_at": "2026-07-29T17:00:00Z",
  "payload": { ... }
}
```

### Breaking Changes

1. **Artifact file format changed** — All artifact files now use the `ArtifactEnvelope` JSON format. Backward compatibility is provided for some legacy formats on load (`DiscoveryCache`, schema snapshots, MCP index), but bytecode cache and frozen registry will be regenerated.
2. **`JSONBytecodeCache(cache_dir=...)` parameter now defaults to `None`** — Previously defaulted to `"artifacts"`. The cache now lives in `.aquilia/artifacts/`.
3. **Template manifest default location changed** — Moved from `artifacts/templates.json` to `.aquilia/artifacts/templates.json`.
4. **WebSocket artifact default location changed** — Moved from `artifacts/ws.json` to `.aquilia/artifacts/ws.json`.

Check the [Migration Guide](migration.md) for full details on upgrading.
