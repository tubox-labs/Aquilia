# Producer Migrations

In v1.3.6, all 9 primary artifact producers were migrated from ad-hoc file I/O to the new `ArtifactStore` backend. This ensures uniform atomic writes, consistent formatting, and centralized integrity checking.

Below are the details on how each producer was migrated and backward compatibility notes.

## 1. Discovery Cache (`aquilia/discovery/engine.py`)

**Before:**
`DiscoveryCache.save()` and `load()` used raw `Path.write_text()` with a plain dictionary format. It did not verify integrity on load.

**After:**
Uses `JSONFileBackend.write_sync`/`read_sync` + `ArtifactEnvelope`. Integrity is implicitly checked by the backend when resolving the envelope.

**Backward Compatibility:**
The loader detects the legacy plain dict format and gracefully loads it. It will be seamlessly upgraded to the envelope format on the next save.

## 2. Aquilary Registry (`aquilia/aquilary/core.py`)

**Before:**
`AquilaryRegistry.export_manifest()` used standard file writing to dump the frozen registry.

**After:**
`export_manifest()` and `_from_frozen_manifest()` use `JSONFileBackend(signed=True)` + `ArtifactEnvelope`.

**Backward Compatibility:**
No backward compatibility provided. The frozen registry is ephemeral to the deployment and will be cleanly regenerated on the first boot of a v1.3.6 application.

## 3. Schema Snapshots (`aquilia/models/schema_snapshot.py`)

**Before:**
`save_snapshot()` and `load_snapshot()` wrote a raw JSON dict to disk.

**After:**
Uses `JSONFileBackend` + `ArtifactEnvelope`. 

**Backward Compatibility:**
Like the discovery cache, legacy plain dict files are detected and read seamlessly.

## 4. Template Manifest (`aquilia/templates/manifest_integration.py`)

**Before:**
`generate_template_manifest()` wrote directly to `artifacts/templates.json`.

**After:**
Uses `bare_fingerprint` + `ArtifactEnvelope` + `JSONFileBackend`, writing to `.aquilia/artifacts/templates.json`.

**Backward Compatibility:**
Safe to regenerate. If you rely on the manifest file for external tooling, update the tool to parse the new `payload` key inside the envelope.

## 5. Bytecode Cache (`aquilia/templates/bytecode_cache.py`)

**Before:**
`JSONBytecodeCache._save()`/`_load()` used manual HMAC signing logic with `Path.replace()` (not `os.replace()`), writing to `artifacts/templates.bytecode.json`.

**After:**
Delegates to `self._backend` (`JSONFileBackend` with `signed=True`). `__init__` now accepts `cache_dir: str | None = None`, dynamically resolving the directory.

**Backward Compatibility:**
No backward compatibility for the file format. The cache will be invalidated and regenerated correctly under the new system. Existing code passing `cache_dir="artifacts"` continues to work but gets the new envelope format.

## 6. Socket Compiler (`aquilia/sockets/compile.py`)

**Before:**
`SocketCompiler.generate_artifacts()` wrote directly to `artifacts/ws.json`.

**After:**
Uses `ArtifactEnvelope` + `JSONFileBackend`, writing to `.aquilia/artifacts/ws.json`.

**Backward Compatibility:**
Regenerated on demand.

## 7. MCP Knowledge Index (`aquilia/mcp/context/indexer.py`)

**Before:**
`save_index()` and `load_index()` read/wrote a plain dictionary.

**After:**
Uses `ArtifactEnvelope` + `JSONFileBackend`.

**Backward Compatibility:**
Legacy plain dict formats are still loadable.

## Performance Impact

Despite the additional metadata overhead, there is **no measurable performance degradation**. The previous systems that used atomic writes were already paying the cost of `mkstemp` + `os.replace`. The abstraction simply centralizes this logic. Systems that previously used `write_text` are now slightly slower (on the order of single-digit milliseconds) but gain absolute resilience against partial writes and process crashes.
