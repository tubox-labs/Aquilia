# Subsystem Lifecycle & Health

This document covers the boot, health, and DI-integration changes made to the cache, storage, and filesystem subsystems in Aquilia v1.3.4, plus a DI fault-contract fix uncovered while validating them.

## §C1 Three Subsystems, Three Different Integration Stories (ARCH)

**Previous Behavior:**
The audit found three inconsistent boot patterns:

- **Cache** — ad hoc `Server._setup_cache()` only. No health check registration reflecting real backend state.
- **Storage** — *two* competing implementations. `Server._setup_storage()` was the live path; `storage/subsystem.py:StorageSubsystem` was fully built, publicly exported, documented with exact boot priority (`_priority = 25`), and wired to health checks — but `server.py` never referenced it. The live path lacked the per-backend health registration the orphaned class described.
- **Filesystem** — neither. A bare class the application developer had to remember to instantiate and register by hand, with no server integration, no health check, and no boot priority.

**Fix:**
All three now have a first-class story on the live boot path, and the relationship between the two storage paths is documented rather than left ambiguous.

`StorageSubsystem` is retained deliberately, not deleted. It is the entry point for hosts that drive subsystems through a `BootContext` — embedders, tests, and alternative runners — while `AquiliaServer` boots storage through its own ordered `_setup_*` sequence. Both share `StorageRegistry`, so behaviour cannot diverge; only the orchestration differs. This is now stated in the module docstring so the next reader does not mistake it for dead code.

**User Impact:**
Consistent lifecycle semantics across all three subsystems. No API removals.

## §C2 Filesystem Is Now a First-Class Subsystem (FEATURE)

**Previous Behavior:**
Using `FileSystem` required manual construction and manual DI registration in application code, per its own docstring. There was no configuration section, no pool lifecycle management, and no health reporting.

**Fix:**
A new `Server._setup_filesystem()` reads an `Integration.filesystem()` configuration section, constructs the facade over a dedicated pool, and registers it in every DI container. The pool starts during `startup()` and drains during `shutdown()`.

```python
# workspace.py
Integration.filesystem(
    enabled=True,
    sandbox_root="/srv/uploads",
    allow_unsandboxed=False,     # fail loudly if the root is ever unset
    max_pool_threads=8,
)
```

```python
# any controller or service
class ReportController(Controller):
    def __init__(self, fs: FileSystem):
        self.fs = fs
```

New configuration keys: `enabled`, `sandbox_root`, `allow_unsandboxed`, `max_pool_threads`, `max_path_length`, `follow_symlinks`, `atomic_writes`. The subsystem is **disabled by default**, so existing applications are unaffected; manual registration continues to work unchanged.

**User Impact:**
`FileSystem` is injectable without boilerplate, and its thread pool is managed by the server lifecycle instead of leaking.

## §C3 Health Checks Reported Hardcoded `HEALTHY` (BUG)

**Previous Behavior:**
`Server.startup()` registered cache and storage health as literal `SubsystemStatus.HEALTHY` without probing anything. Storage reported a single aggregate entry whose message counted configured backends. A cache backend that could not be reached, or one storage disk out of five being down, was invisible to `/health` — the endpoint load balancers and orchestrators consult.

**Fix:**
Health now reflects reality:

- **Cache** — probes `CacheService.health_check()` (a real write/read/delete round trip) and reports the backend name.
- **Storage** — a new `_register_storage_health()` pings every backend and registers one `storage.<alias>` entry per disk plus an aggregate. The aggregate is `healthy` when all pass, `degraded` when some fail, `unhealthy` when all fail, and names the failing aliases in its message. A probe that raises reports `unhealthy` rather than aborting startup.
- **Filesystem** — reports pool state and configured thread count.

```json
{
  "storage":         { "status": "degraded",  "message": "unhealthy: cdn" },
  "storage.default": { "status": "healthy",   "message": "Backend 'default' healthy" },
  "storage.cdn":     { "status": "unhealthy", "message": "Backend 'cdn' unhealthy" },
  "cache":           { "status": "healthy",   "message": "backend=memory" },
  "filesystem":      { "status": "healthy",   "message": "pool_max_threads=8" }
}
```

**User Impact:**
`/health` distinguishes a fully-healthy deployment from a partially-degraded one. Orchestrators can act on per-disk failures. Verified end-to-end on a booted server.

## §C4 Storage Executor Shutdown (BUG)

**Previous Behavior:**
Storage backends used the interpreter's shared default thread pool, which the server never shut down; threads outlived the application.

**Fix:**
The dedicated storage pool introduced in §B7 is shut down in `Server.shutdown()`, in a `finally` so it runs even if backend shutdown raises. A later call transparently recreates it, so a restarted server in the same process works.

**User Impact:**
No thread leak across server lifecycles.

## §C5 DI Patch Broke the Public Exception Contract (CRITICAL — BUG)

**Previous Behavior:**
`patch_di_container()` — applied whenever a server is constructed — caught `ProviderNotFoundError` and re-raised a *different* type, `ProviderNotFoundFault`. Since `ProviderNotFoundError` is not a subclass of it, every existing handler stopped working the moment any server booted in the process:

```python
try:
    svc = container.resolve("optional.service")
except ProviderNotFoundError:
    svc = None          # silently stopped catching after a server was constructed
```

The patch was also non-idempotent: each server construction re-wrapped the already-wrapped methods, stacking wrappers without bound.

**Root Cause:**
`ProviderNotFoundError` already subclasses `DIFault` — it *was* already a structured fault. The conversion added nothing and destroyed type compatibility. The bug was latent because it only manifests when a server boots before DI-error-handling code runs in the same process; the new audit tests booting real servers surfaced it immediately.

**Fix:**
The lossy re-raise is gone. The original error is enriched in place with resolution context (`provider`, `tag`, `candidates`) and re-raised unchanged, preserving both the structured-fault metadata and the exception type. The patch is now guarded by an idempotency marker.

**User Impact:**
`except ProviderNotFoundError` works again, and the error still carries full structured metadata. Handlers catching `ProviderNotFoundFault` continue to work, since the raised error is a `DIFault`. Repeated server construction no longer stacks wrappers.

## §C6 Server Cache Wiring (BUG)

Covered in detail in [§A16 of the cache audit](cache_audit.md). In summary: `_setup_cache()` passed a nonexistent `ttl=` argument to `CacheMiddleware`, the resulting `TypeError` was swallowed by a broad `except`, and the response cache was silently never installed even when explicitly enabled. Configured `cacheable_methods`, `vary_headers`, and `stale_while_revalidate` were also dropped. All are now threaded through, and `set_default_cache_service()` is invoked so decorator-based caching resolves the configured service.

## Related Documentation

- [Cache System Audit Fixes](cache_audit.md)
- [Storage & Filesystem Audit Fixes](storage_filesystem_audit.md)
- [Migration Guide](migration.md)
