# Distributed & Persistent Task Backends — Aquilia v1.3.5

Background tasks now run across multiple worker processes and multiple machines, with job state that survives a restart. Before this release the only backend was `MemoryBackend`: jobs lived in the worker process and were lost on restart, and `backend="redis"` logged a warning and silently fell back to in-memory.

---

## Motivation

The task system was single-process. That is fine for a cron-like cleanup job, but it fails the moment an application scales horizontally:

- Two web workers each ran their own queue, so a periodic task fired twice.
- A deploy dropped every queued job on the floor.
- A worker crash lost whatever that worker was executing, permanently.
- `Integration.tasks(backend="redis")` was accepted by config validation and then ignored at runtime.

---

## Design Goals

1. **Backend choice is configuration, not code.** Task functions, decorators, and `enqueue()` calls are identical on every backend.
2. **No lost work on crash.** A worker that dies mid-job must have that job picked up by a peer.
3. **Fail at enqueue, not on a remote worker.** Anything that cannot cross a process boundary must be rejected at the call site, where the stack trace is useful.
4. **Existing single-process apps unaffected.** `memory` stays the default and behaves exactly as before.

---

## Architecture

### Job serialization

A job that crosses a process boundary cannot carry a live Python callable or arbitrary objects. Two new methods on `Job` define the transport form:

```python
payload = job.to_payload()      # JSON-compatible dict
restored = Job.from_payload(payload)
```

`to_payload()` validates `args` and `kwargs` against `json.dumps` and raises `TaskSerializationFault` if they cannot be represented. `from_payload()` deliberately leaves the callable unset — the worker resolves it from `func_ref` through the `@task` registry, so a queue entry can never name a function the application did not register.

`Job.to_dict()` is unchanged and remains the human-facing view used by the admin dashboard.

### Lease-based claiming

Both durable backends use the same coordination model:

1. A worker claims a job and takes a lease for `lease_seconds` (default `300.0`).
2. While executing, it renews the lease every `heartbeat_interval` seconds (default `30.0`).
3. A background reclaim loop sweeps every `reclaim_interval` seconds (default `60.0`) and returns jobs whose lease lapsed to the runnable pool.

If a worker is killed, its lease expires and a peer reclaims the job instead of the job being lost.

**This is at-least-once delivery.** A worker that stalls past its lease — a long GC pause, a blocked event loop — can have its job reclaimed and executed a second time. Task functions should be idempotent.

### `RedisBackend`

Multi-process and multi-machine, backed by Redis. Claims are atomic through a Lua script against a sorted set; fingerprint reservation uses `SET NX`. Fastest option, and the right default for high throughput.

### `SQLBackend`

Durable state on the database the application already uses — no new infrastructure. Works on SQLite, PostgreSQL, MySQL, and Oracle through Aquilia's existing parameterized query layer.

A claim is a conditional `UPDATE ... WHERE id = ? AND state = ?` inside a transaction; `rowcount == 0` means another worker won the race, so the loser moves on rather than double-running the job. This works on every supported dialect without needing `SELECT ... FOR UPDATE SKIP LOCKED`, which SQLite does not have.

Two tables are created on first `initialize()`:

```
aquilia_tasks(
    id TEXT PRIMARY KEY, queue TEXT, priority INTEGER, state TEXT,
    func_ref TEXT, payload TEXT,             -- full JSON job
    available_at TEXT,                        -- when it may run
    lease_expires_at TEXT, owner TEXT,        -- distributed claim
    dedup_key TEXT, workflow_id TEXT,
    created_at TEXT, completed_at TEXT, sequence INTEGER
)
aquilia_task_locks(fingerprint TEXT PRIMARY KEY, job_id TEXT, expires_at TEXT)
```

The unique primary key on `aquilia_task_locks.fingerprint` is what makes deduplication correct under concurrency: two workers racing to reserve the same fingerprint both attempt an `INSERT`, and the database rejects exactly one.

Redis is faster and scales further. SQL wins when you cannot add a Redis dependency, or when you want jobs to commit in the *same transaction* as the business data that created them, so a rolled-back request cannot leave an orphaned job behind. Above roughly a few hundred jobs/second, prefer Redis.

---

## Configuration

```python
# workspace.py

# Development — single process, non-durable (default, unchanged)
Integration.tasks(num_workers=4)

# Production — distributed workers, durable queue
Integration.tasks(
    backend="redis",
    redis_url="redis://cache:6379/0",
    redis_prefix="aquilia:tasks:",
    num_workers=16,
    lease_seconds=120,
    heartbeat_interval=30,
    reclaim_interval=60,
)

# Durable without extra infrastructure
Integration.tasks(backend="sql", sql_table="aquilia_tasks")
```

### New options

| Option | Default | Purpose |
|---|---|---|
| `backend` | `"memory"` | `"memory"`, `"redis"`, or `"sql"` (aliases: `"database"`, `"db"`) |
| `redis_url` | `None` | Redis connection URL; falls back to `$REDIS_URL` |
| `redis_prefix` | `"aquilia:tasks:"` | Key namespace, so several apps can share one Redis |
| `sql_table` | `"aquilia_tasks"` | Job table name for the SQL backend |
| `lease_seconds` | `300.0` | How long a claimed job stays owned before a peer may reclaim it |
| `heartbeat_interval` | `30.0` | Lease renewal cadence; must be well under `lease_seconds` |
| `reclaim_interval` | `60.0` | How often to sweep for jobs abandoned by crashed workers |
| `dedup_ttl` | `3600.0` | How long a deduplication reservation is held |
| `worker_id` | `None` | Worker identity recorded as a job's owner; defaults to `hostname:pid:random` |

Install the Redis extra with `pip install aquilia[redis]`. The SQL backend requires `Integration.database(...)` and no extra dependency.

---

## Usage

Task code does not change between backends:

```python
from aquilia.tasks import task

@task(queue="reports", max_retries=3)
async def rebuild_report(report_id: int) -> dict:
    return {"rebuilt": report_id}
```

```python
job_id = await tasks.enqueue(rebuild_report, 42)
job = await tasks.get_job(job_id)
```

### Running a dedicated worker process

A process that only consumes work is a normal Aquilia app with `num_workers` set and no enqueueing of its own. The queues it polls are derived from the `@task` descriptors it has imported, plus any queue it discovers on the shared backend — so a worker does not need to know in advance which queues its producers use.

---

## Edge Cases

**Non-serializable arguments.** On a persistent backend, passing an object JSON cannot represent raises `TaskSerializationFault` at `enqueue()`:

```python
await tasks.enqueue(process, open("f.txt"))   # TaskSerializationFault
```

This is deliberate. The alternative is a job that enqueues cleanly and then fails unrecoverably on a remote worker, far from the call site. On `MemoryBackend` live objects still work, because the job never leaves the process.

**Unregistered task names.** A worker resolves `func_ref` through the `@task` registry. If the consumer process has not imported the module that registers the task, the job raises `TaskResolutionFault` rather than executing arbitrary named code. Ensure every worker imports the same task modules.

**Backend unavailable at startup.** A Redis or database that cannot be reached logs an error naming the durability that was lost and falls back to `MemoryBackend`, rather than aborting startup. The application still serves requests; queued jobs are not durable until the backend recovers and the process restarts.

**Unknown backend name.** A typo such as `backend="rabbitmq"` logs a warning listing the valid values and uses `MemoryBackend`. A typo does not take production down.

**Clock skew across machines.** Leases are stored as absolute timestamps. Significant clock skew between workers can cause premature reclaim (duplicate execution) or delayed reclaim. Run NTP.

---

## Performance Implications

- `MemoryBackend` is unchanged; single-process applications see no difference.
- `RedisBackend` claim is one round trip against an in-memory sorted set.
- `SQLBackend` claim is one `UPDATE` inside a transaction. Throughput is bounded by database write capacity; above a few hundred jobs/second prefer Redis.
- The reclaim loop runs once per `reclaim_interval` per process and issues one sweep query. Raising `reclaim_interval` reduces load; lowering it shortens the window during which a crashed worker's job sits idle.

---

## Compatibility

Fully backward compatible. `memory` remains the default, `MemoryBackend` behavior is unchanged, and every existing `@task` and `enqueue()` call works untouched. The new configuration options are additive with defaults matching prior behavior.

---

## Related

- [Workflows & DAGs](workflows.md) — composing jobs, which requires a shared backend to span processes
- [Idempotency & Deduplication](idempotency.md) — the distributed lock built on this coordination layer
- [Mail Delivery Queue](mail_queue.md) — the first framework subsystem to run on it
- [Migration Guide](migration.md)
