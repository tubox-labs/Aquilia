# Idempotency & Distributed Deduplication — Aquilia v1.3.5

`Job.fingerprint` existed since the task system shipped but nothing ever read it. As of v1.3.5 it is enforced at enqueue time, and on durable backends that enforcement is a real distributed lock: two processes racing to queue the same work produce one job, not two.

---

## Motivation

The classic double-send. A user double-clicks, a retried HTTP request replays, a webhook is delivered twice, two web workers react to the same event — and the same background job is queued twice. Applications worked around this with their own Redis `SETNX` guards or a `processed` table, reimplementing per project what the framework already had the raw material for.

`Job.fingerprint` was computed and stored. It simply had no readers.

---

## How It Works

### The fingerprint

A stable digest over `func_ref`, `queue`, `args`, and `kwargs` — two enqueue calls that would do identical work share a fingerprint:

```python
job.fingerprint    # 12-hex-character digest
```

It is computed from the JSON form when possible, so equal-but-not-identical values agree across processes: a tuple `(1, 2)` and a list `[1, 2]` produce the same fingerprint. Non-JSON values fall back to `repr`, which keeps the in-memory backend working with live objects.

### The `dedup` parameter

```python
await manager.enqueue(rebuild_index, dedup="allow")   # default — always enqueue
await manager.enqueue(rebuild_index, dedup="skip")    # return the in-flight job's ID
await manager.enqueue(rebuild_index, dedup="raise")   # raise TaskDuplicateFault
```

| Mode | Behavior |
|---|---|
| `"allow"` | Always enqueue. Preserves historical behavior, so existing code is unaffected. |
| `"skip"` | If identical work is already in flight, return that job's ID instead of enqueueing a second copy. |
| `"raise"` | Raise `TaskDuplicateFault` instead. Use when a duplicate indicates a caller bug. |

A reservation is held for `dedup_ttl` seconds (default `3600.0`) and released when the job reaches a terminal state.

### Distributed enforcement

The backend owns the reservation, so correctness under concurrency comes from the storage layer, not from application-level check-then-act:

- **`RedisBackend`** — `SET NX` on the fingerprint key. Exactly one caller wins.
- **`SQLBackend`** — `INSERT` into `aquilia_task_locks`, whose `fingerprint` column is the primary key. Two workers racing both attempt the insert and the database rejects exactly one.
- **`MemoryBackend`** — an in-process map, correct within a single process.

---

## Examples

### Collapsing a burst

```python
# Ten requests arrive; one job runs.
job_id = await tasks.enqueue(rebuild_search_index, dedup="skip")
```

### Treating a duplicate as an error

```python
from aquilia.tasks import TaskDuplicateFault

try:
    await tasks.enqueue(charge_card, order_id, dedup="raise")
except TaskDuplicateFault:
    return Response.json({"status": "already_processing"}, status=409)
```

### Across processes

```python
# Web worker A and web worker B, sharing one Redis or SQL backend
a = await tasks.enqueue(send_invoice, order_id, dedup="skip")
b = await tasks.enqueue(send_invoice, order_id, dedup="skip")
assert a == b   # one job
```

---

## Before vs After

```python
# Before v1.3.5 — hand-rolled guard in every application
lock_key = f"job:invoice:{order_id}"
if await redis.set(lock_key, "1", nx=True, ex=3600):
    await tasks.enqueue(send_invoice, order_id)
```

```python
# v1.3.5
await tasks.enqueue(send_invoice, order_id, dedup="skip")
```

The framework version is also correct in a case the hand-rolled one usually is not: the reservation is released when the job reaches a terminal state, so a failed job can be retried immediately instead of being blocked until the TTL expires.

---

## Edge Cases

**Deduplication suppresses duplicate *enqueues*, not duplicate *execution*.** Distributed backends are at-least-once: a job whose worker stalls past its lease may be reclaimed and run twice. Task functions should still be idempotent. These are two different guarantees and `dedup` provides only the first.

**Fingerprints include the queue.** The same function with the same arguments on two different queues is two different fingerprints, and both will be enqueued.

**Argument order matters for positional arguments.** `f(1, 2)` and `f(2, 1)` are distinct. Keyword arguments are sorted, so `f(a=1, b=2)` and `f(b=2, a=1)` match.

**Non-JSON arguments still deduplicate in-process.** The `repr` fallback means two live objects deduplicate only if their `repr` matches. On a persistent backend such arguments raise `TaskSerializationFault` before dedup is reached.

**The default is unchanged.** Existing code that never passes `dedup` continues to enqueue every call. This is deliberate — silently collapsing jobs in an existing application would be a breaking behavioral change.

---

## Performance Implications

`dedup="allow"` (the default) adds no work: no fingerprint reservation is attempted. `"skip"` and `"raise"` add one reservation operation per enqueue — a single `SET NX` on Redis, a single `INSERT` on SQL. In exchange, collapsed duplicates avoid an entire job execution.

---

## Compatibility

Fully backward compatible. `dedup` is a new keyword-only parameter defaulting to `"allow"`, which is exactly the prior behavior. `TaskDuplicateFault` is a new fault raised only when explicitly requested via `dedup="raise"`.

---

## Related

- [Distributed & Persistent Backends](distributed_tasks.md) — the coordination layer this builds on
- [Workflows & DAGs](workflows.md)
- [Migration Guide](migration.md)
