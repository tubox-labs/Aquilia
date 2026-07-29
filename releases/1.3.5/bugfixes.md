# Bug Fixes — Aquilia v1.3.5

Four defects were found and fixed while auditing the enterprise task and mail work. Three would only surface once a durable or distributed backend was in use — which is exactly what this release enables, so each would have been a first-day production failure for anyone adopting the new capability.

---

## 1. Mail delivery task unresolvable across processes

**Severity:** Critical, on any persistent backend.

### Previous behavior

Background mail delivery enqueued a plain module-level function. On `MemoryBackend` this worked, because the job carried the live callable in-process.

The moment a durable backend was configured, delivery stopped. The job serialized to a module-path reference, and the consuming worker — which resolves callables through the `@task` registry rather than importing arbitrary paths — could not resolve it. Envelopes sat in `QUEUED` forever. Nothing crashed loudly; mail simply never arrived.

### Root cause

`_deliver_envelope_task` was a bare `async def`, never registered with `@task`. Worker resolution goes through `get_task(job.func_ref)`, which only knows about registered descriptors. This is a deliberate security property — a queue entry must not be able to name arbitrary importable code — but it means an unregistered function is unreachable.

### New behavior

The delivery task is registered under a stable name:

```python
@task(name="aquilia.mail.deliver", queue=MailService.retry_queue, max_retries=0)
async def _deliver_envelope_task(envelope_id: str) -> None: ...
```

A worker in any process resolves it by name. The name is stable, so a future rename of the Python function does not orphan jobs already in the queue.

### User impact

Anyone enabling `queue_enabled=True` together with `backend="redis"` or `backend="sql"` would have had silently undelivered mail. Fixed before either capability shipped.

---

## 2. Consumer-only workers polled nothing

**Severity:** Critical, for distributed deployments.

### Previous behavior

A dedicated worker process — one that consumes jobs but never enqueues any — processed nothing. Jobs queued by web workers on any queue other than `default` were ignored indefinitely.

### Root cause

`TaskManager._queues` was populated exclusively as a side effect of `enqueue()`. A process that never enqueues therefore knew about exactly one queue: its configured `default_queue`. The worker loop iterates the known queue set, so work on `mail`, `reports`, or any other queue was invisible to it.

This was harmless while everything ran in one process — the enqueuer and the worker were the same object. It becomes fatal the moment producer and consumer are separate processes, which is the entire point of a distributed backend.

### New behavior

Two additions:

1. `_bind_task_descriptors()` registers the queue of every `@task` descriptor, so importing a task module is enough to poll its queue.
2. On a distributed backend, the manager adopts queues reported by `backend.get_queue_stats()` at startup and refreshes them on each reclaim tick — so a queue created by a peer after startup is picked up.

### User impact

Dedicated worker processes now consume the queues their producers use, without needing to be told which those are.

---

## 3. Job results degraded to repr strings on persistent backends

**Severity:** High — silent data corruption in workflows.

### Previous behavior

```python
# In-process
job.result.value    # 4  (int)

# Same job on a SQL or Redis backend
job.result.value    # '4'  (str)
```

A chord callback consuming `parent_results` received `['4', '6']` instead of `[4, 6]`. Arithmetic silently produced string concatenation or a `TypeError` far from the cause.

### Root cause

`JobResult.to_dict()` serialized unconditionally with `repr(self.value)`. The rationale — an arbitrary return value is not guaranteed to be JSON-compatible — was sound, but the blanket application destroyed values that serialize perfectly well.

### New behavior

JSON-safe values round-trip unchanged; only genuinely non-serializable values fall back to `repr`:

```python
value = self.value
if value is not None:
    try:
        json.dumps(value)
    except (TypeError, ValueError):
        value = repr(value)
```

### User impact

Workflow fan-in receives real values on every backend. Applications that had adapted to the string form — parsing `repr` output back — should remove that workaround.

```python
# Before — workaround
total = sum(int(r) for r in parent_results)

# After
total = sum(parent_results)
```

---

## 4. `queue.persistent` had no configuration surface or wiring

**Severity:** Medium — an advertised capability that could not be reached.

### Previous behavior

`SQLEnvelopeStore` and `SQLSuppressionList` existed and worked, but nothing constructed them from configuration. The only way to get durable mail state was to instantiate the stores by hand and pass them to `MailService(store=..., suppression=...)`. The `queue` config block had no `persistent` key at all, so setting it in `workspace.py` was silently dropped by contract validation.

### New behavior

`persistent` is a real config field, threaded end to end:

- `Integration.mail(queue_persistent=True)`
- `MailIntegration.queue_persistent`
- `QueueConfigContract.persistent`
- `MailService._prepare_stores()` selects SQL-backed stores when set

An unavailable database logs an error naming the durability that was lost and falls back to in-memory stores, rather than aborting startup — mail degrades to non-durable instead of taking the application down.

Explicitly-supplied stores still win: a caller passing `store=` meant it, and configuration does not override that.

### User impact

Durable envelope and suppression storage is now reachable from `workspace.py`.

---

## Documentation Correctness Fix

The `aquilia.tasks` package docstring listed "Persistent or distributed backends", "Job chaining / workflow DAGs" under **"Not implemented today (deliberately absent, not stubbed)"**. All three shipped in this release; the docstring is updated. It now documents the at-least-once delivery contract instead, and the one thing still genuinely absent (per-queue rate limiting).

---

## Related

- [Distributed & Persistent Backends](distributed_tasks.md)
- [Workflows & DAGs](workflows.md)
- [Mail Delivery Queue](mail_queue.md)
- [Contracts — Nested Validation Pipeline](contracts_pipeline.md) — Contract subsystem fixes in this release
- [Migration Guide](migration.md)
