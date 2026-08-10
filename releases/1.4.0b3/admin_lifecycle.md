# Admin Lifecycle & Rate Limiter — v1.4.0b3

Two defects in the admin subsystem, both found in the 2026-08-09 audit: admin's lifecycle hooks were never invoked, and the rate-limiter cleanup task reached into private state through a path that silently no-ops on a freshly booted host.

Regression coverage: `tests/test_subsystem_boot_contract.py`.

---

## 1. Admin lifecycle hooks never ran

### Previous behaviour

Configuring the admin dashboard produced working routes. Everything behind those routes that needed a lifecycle did not run:

- The audit log was never flushed on shutdown — buffered entries were lost on every restart.
- The rate-limit cleanup sweep never ran, so `AdminRateLimiter`'s in-memory attempt records grew for the process lifetime.
- The cache service was never wired from DI, so admin's cache integration ran unbacked.
- The task manager was never wired from DI, so `AdminTasks.enqueue_*` fell back to inline execution.
- Admin security DI providers were never registered.
- The security event tracker was never cleared on shutdown.

### Root cause

`AquiliaServer._wire_admin_integration()` registered admin's routes and stopped there. `AdminLifecycle.on_startup()` / `on_shutdown()` — which perform all of the above — were written, tested in isolation, and never called by anything. There was no `LifecycleCoordinator` entry for admin, and the server's startup sequence had no admin step.

The symptom was invisible: routes worked, the dashboard rendered, and the missing upkeep only showed as slow memory growth and an audit log that reset on deploy.

### New behaviour

`AquiliaServer.startup()` gained **Step 3.25**, gated on the same config key the route wiring reads:

```python
# Step 3.25: Start admin lifecycle (audit log, cache, cleanup tasks).
admin_config = self.config.get("integrations", {}).get("admin") if hasattr(self.config, "get") else None
if admin_config is not None:
    try:
        from aquilia.admin import get_admin_subsystems

        self._admin_subsystems = get_admin_subsystems()
        await self._admin_subsystems.lifecycle.on_startup(self.config, self._get_base_container())
    except Exception as e:
        self._admin_subsystems = None
        self.logger.warning(f"Admin lifecycle startup failed: {e}")
        # Non-fatal -- admin routes still serve; background upkeep is off
```

and `AquiliaServer.shutdown()` mirrors it:

```python
# Shutdown admin lifecycle (flush audit log, sweep rate limiter)
if getattr(self, "_admin_subsystems", None) is not None:
    try:
        await self._admin_subsystems.lifecycle.on_shutdown(self.config, self._get_base_container())
    except Exception as e:
        self.logger.warning(f"Error shutting down admin lifecycle: {e}")
```

`self._admin_subsystems` is initialized to `None` in `__init__` so the shutdown path is safe whether startup ran, failed, or was never reached.

### Why the placement

- **Step 3.25 — after DI containers exist, before the task manager starts.** `on_startup` resolves `CacheService` and `TaskManager` from the container, so the container must be built; and it wires the task manager into `AdminTasks` before background jobs begin, so an enqueued admin job is not dropped.
- **Gated on `config["integrations"]["admin"]`**, the same key `_wire_admin_integration` reads. An app without admin configured pays nothing and imports nothing.
- **Non-fatal.** A failed admin lifecycle logs a warning and leaves `_admin_subsystems = None`. Admin routes still serve; only background upkeep is off. Failing the whole boot because an optional dashboard's cache probe raised would be disproportionate.

### What `on_startup` does

1. Initializes the `AdminSite` singleton (`AdminSite.default().initialize()`).
2. Resolves `CacheService` from the DI container and hands it to `AdminCacheIntegration`.
3. Resolves `TaskManager` from the DI container and hands it to `AdminTasks`.
4. Registers admin security DI providers via `register_security_providers(container, security_config)`.

It is idempotent: `self._started` short-circuits a second call.

### What `on_shutdown` does

1. Flushes the audit log (`await site.audit_log.flush()` when the log implements `flush`).
2. Runs `AdminTasks.rate_limit_cleanup()`.
3. Clears the security event tracker.

Each step is independently guarded, so one failure does not skip the rest.

### User impact

| Before | After |
|---|---|
| Buffered audit entries lost on every restart | Flushed on graceful shutdown |
| `AdminRateLimiter` records grew unbounded | Swept on shutdown, and periodically once `cleanup_interval` elapses |
| `AdminTasks.enqueue_*` ran inline | Enqueued through the real `TaskManager` |
| Admin cache integration unbacked | Backed by the configured `CacheService` |
| Admin security providers absent from DI | Registered |

Applications that do not configure admin are unaffected.

### Migration

None. No API changed and no configuration is required — configuring admin is now sufficient for its lifecycle to run. If you previously called `AdminLifecycle.on_startup()` yourself from a module hook as a workaround, you can remove it: `on_startup` is idempotent, so leaving it in place is also safe.

---

## 2. `AdminRateLimiter.force_cleanup()` — public sweep API

### Previous API

`AdminTasks.rate_limit_cleanup()` reached into three private attributes and inferred the result from dictionary lengths:

```python
# BEFORE
before_login = len(limiter._login_records)
before_sensitive = len(limiter._sensitive_records)

# Force cleanup by resetting the last_cleanup time
limiter._last_cleanup = 0
limiter._maybe_cleanup()

cleaned_login = before_login - len(limiter._login_records)
cleaned_sensitive = before_sensitive - len(limiter._sensitive_records)

return {
    "cleaned_login": max(0, cleaned_login),
    "cleaned_sensitive": max(0, cleaned_sensitive),
}
```

**How it was meant to work.** Setting `_last_cleanup = 0` was supposed to make `_maybe_cleanup()`'s interval guard fall through, since `now - 0` would exceed `cleanup_interval`.

### Root cause

`_maybe_cleanup()` guards on `time.monotonic() - self._last_cleanup < self.cleanup_interval`. `time.monotonic()` is **not** wall-clock — on Linux it is time since boot. On a host or container that has been up for less than `cleanup_interval` (default **3600s**), `time.monotonic()` is itself below 3600, so `now - 0 < 3600` held and `_maybe_cleanup()` returned immediately.

The sweep therefore did nothing for the first hour of a machine's uptime, and `rate_limit_cleanup()` reported `{"cleaned_login": 0, "cleaned_sensitive": 0}` — indistinguishable from "there was nothing stale to clean". Fresh containers, which restart constantly, spent a disproportionate share of their life in exactly that window.

The `max(0, ...)` clamps were papering over the same fragility from the other end: subtracting lengths cannot distinguish "nothing was stale" from "the sweep never ran", and would go negative if a concurrent request added a record between the two reads.

### New API

The sweep is factored out of the interval check, and exposed:

```python
def _maybe_cleanup(self) -> None:
    """Periodically remove stale entries to prevent memory growth."""
    now = time.monotonic()
    if now - self._last_cleanup < self.cleanup_interval:
        return
    self._sweep(now)

def _sweep(self, now: float) -> tuple[int, int]:
    """Drop stale records unconditionally. Returns (login, sensitive) counts."""
    self._last_cleanup = now
    cutoff = now - max(self.login_window, self.sensitive_op_window) * 2

    removed = []
    for store in (self._login_records, self._sensitive_records):
        stale_keys = [
            k for k, v in store.items()
            if v.lockout_until < now and (not v.attempts or v.attempts[-1] < cutoff)
        ]
        for k in stale_keys:
            store.pop(k, None)
        removed.append(len(stale_keys))
    return removed[0], removed[1]

def force_cleanup(self) -> tuple[int, int]:
    """Sweep stale records now, ignoring ``cleanup_interval``."""
    return self._sweep(time.monotonic())
```

```python
# AFTER
cleaned_login, cleaned_sensitive = limiter.force_cleanup()
return {
    "cleaned_login": cleaned_login,
    "cleaned_sensitive": cleaned_sensitive,
}
```

### Why it is better

- **Correct on a fresh host.** `force_cleanup()` bypasses the interval guard by construction rather than by trying to defeat it with a sentinel value that `monotonic()` semantics can invalidate.
- **Exact counts.** `_sweep` returns what it actually removed instead of a length diff, so the number is right even under concurrent request traffic.
- **No private access.** `AdminTasks` calls one public method. `_last_cleanup`, `_login_records` and `_sensitive_records` are no longer part of any caller's contract.
- **One sweep implementation.** The periodic path and the forced path cannot drift apart.

### Behavioural changes

| Scenario | Before | After |
|---|---|---|
| Cleanup task on a host up < 1 hour | No sweep; reports `0` cleaned | Sweeps; reports the real count |
| Cleanup task on a host up > 1 hour | Sweeps; count inferred from lengths | Sweeps; exact count |
| Record added concurrently during the sweep | Count could be clamped to `0` | Count unaffected — it counts removals |
| Periodic `_maybe_cleanup()` on request paths | Unchanged | Unchanged |

### Edge cases

**An active lockout is never cleared.** `_sweep` only removes records that are past their `lockout_until` **and** have no attempts newer than `cutoff`. `force_cleanup()` therefore cannot be used to release a locked-out principal — that is `clear_login_attempts()`, and the docstring says so. This matters: a "cleanup" call that silently unlocked brute-force attempts would be a security regression, so the boundary is stated in the API rather than left to the reader.

**`cutoff` is `now - max(login_window, sensitive_op_window) * 2`.** The 2× margin keeps a record alive for one extra window past expiry, so a client at the edge of a window is not given a fresh budget by a well-timed sweep.

### Migration

Replace any code that poked the privates:

```python
# BEFORE
limiter._last_cleanup = 0
limiter._maybe_cleanup()

# AFTER
cleaned_login, cleaned_sensitive = limiter.force_cleanup()
```

`_maybe_cleanup()` remains for the periodic path and is unchanged in behaviour.

---

## Related documentation

- [`subsystem_boot_contract.md`](subsystem_boot_contract.md) — the rest of the same audit
- [`bug_fixes.md`](bug_fixes.md) — the full defect list
- [`migration.md`](migration.md) — upgrade steps
