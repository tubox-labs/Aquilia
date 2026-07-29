# Bug Fixes

The introduction of the unified `ArtifactStore` in v1.3.6 inherently resolves several long-standing, subtle bugs related to file I/O and caching across the framework.

## 1. Centralized Atomic Write Guarantees

**The Bug:**
Different subsystems implemented file writing differently. Some, like the bytecode cache, attempted atomic writes but used `Path.replace()` (which is not guaranteed to be atomic across all filesystems/platforms) instead of `os.replace()`. Others, like the discovery engine, used a raw `Path.write_text()`, meaning a crash during the write could leave a corrupted, partially written JSON file on disk, breaking the app on the next boot.

**The Fix:**
All artifact writing now routes through `JSONFileBackend.write_sync()`. This function rigorously employs `tempfile.mkstemp` (ensuring the temporary file is on the same filesystem), writes the data, calls `os.fsync` to guarantee durability, and then uses `os.replace` for a true atomic swap. No partial writes are possible.

## 2. Inconsistent HMAC Verification

**The Bug:**
While the bytecode cache properly verified its HMAC signature on load, other caches (like the discovery cache) did not verify integrity at all. If the `discovery_cache.json` file was manually tampered with or corrupted without breaking JSON syntax, the framework would load it blindly.

**The Fix:**
The `JSONFileBackend` natively supports a `signed=True` mode, and the `ArtifactEnvelope` includes a `fingerprint` property. The `ArtifactStore` verifies signatures on load for all configured artifact types, throwing an `ArtifactCorruptFault` if tampering or corruption is detected.

## 3. Directory Clutter & Collisions

**The Bug:**
The framework created an `artifacts/` directory in the current working directory of the process. If a developer ran a command from a subdirectory, a second `artifacts/` directory would be created there. Furthermore, the generic name `artifacts/` often collided with user-created folders or CI output directories.

**The Fix:**
All generated artifacts are now strictly confined to `.aquilia/artifacts/` relative to the project root, resolved predictably via `resolve_artifact_root()`.
