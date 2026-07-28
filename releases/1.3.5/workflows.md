# Workflows & DAGs — Aquilia v1.3.5

Jobs can now declare dependencies on other jobs. Sequential chains, parallel groups, fan-in callbacks, and arbitrary directed acyclic graphs are all expressed through the same queue and the same workers — equivalent to Celery Canvas or BullMQ Flows.

Previously there was no way to say "run B after A". Applications either awaited a job's completion inside another job (occupying a worker slot while doing nothing) or polled `get_job()` in application code.

---

## Motivation

Real background work is rarely one isolated function:

- An import pipeline extracts, transforms, then loads.
- A report shards across N workers and merges the results.
- A deploy runs migrations, then warms caches, then notifies.

Without dependency support, each of these had to be orchestrated by a long-lived coroutine that survives for the whole pipeline — which loses everything on restart and does not distribute.

---

## Design Goals

1. **The graph is durable the moment it is submitted.** Every job is created up front with its dependencies recorded, so the workflow survives a restart on a persistent backend.
2. **No orchestrator process.** The backend releases dependent jobs as their dependencies complete. Nothing needs to stay resident.
3. **Reuse the existing queue.** Workflows are ordinary jobs with a `depends_on` field, not a parallel execution system.
4. **A failed step stops its branch.** Downstream jobs must not run on missing input.

---

## Architecture

### `Signature`

A task plus the arguments it will be called with, not yet enqueued — the same concept as Celery's signature, and named the same way.

```python
from aquilia.tasks.workflow import Signature

step = Signature(send_email, ("user@example.com",), {"subject": "Hi"})
```

Or, more idiomatically, from a `@task` descriptor:

```python
step = send_email.s("user@example.com", subject="Hi")
```

`with_parent_results()` returns a copy that receives its dependencies' return values as a `parent_results` keyword at execution time:

```python
merge.s().with_parent_results()   # merge(parent_results=[...])
```

The marker stored in the job's kwargs is a plain string, replaced with real values by the worker at execution time. That keeps the job JSON-serializable and lets results be read after a restart.

### `Workflow`

The graph builder. `add()` returns an index used to declare dependencies:

```python
from aquilia.tasks.workflow import Workflow

wf = Workflow("nightly")
extract = wf.add(extract_rows.s(source))
clean   = wf.add(clean_rows.s(), depends_on=[extract])
enrich  = wf.add(enrich_rows.s(), depends_on=[extract])
wf.add(load_rows.s().with_parent_results(), depends_on=[clean, enrich])

result = await wf.run(manager)
```

`run()` validates the graph, enqueues every node with its dependencies already wired, and returns a `WorkflowResult`. Dependent jobs start in `WAITING` and are released by the backend as their dependencies complete.

### `WorkflowResult`

```python
await result.is_complete(manager)    # every terminal job reached a terminal state
await result.results(manager)        # terminal jobs' return values, in declaration order
await result.failed_jobs(manager)    # jobs that ended FAILED or DEAD
```

`is_complete()` returns `True` for failure as well as success — use `failed_jobs()` to distinguish.

---

## Helpers

### `chain` — sequential

Each step waits for the previous one to complete successfully.

```python
from aquilia.tasks.workflow import chain

await chain(
    extract.s(source),
    transform.s().with_parent_results(),
    load.s().with_parent_results(),
).run(manager)
```

### `group` — parallel

Pure fan-out. Every step runs concurrently with no dependencies between them.

```python
from aquilia.tasks.workflow import group

await group([shard.s(n) for n in range(8)]).run(manager)
```

### `chord` — parallel then fan-in

A `group` header plus a callback that runs once every header job has completed, receiving their results.

```python
from aquilia.tasks.workflow import chord

await chord(
    [shard.s(n) for n in range(8)],
    merge.s().with_parent_results(),
).run(manager)
```

### Arbitrary DAGs

`chain`, `group`, and `chord` are conveniences over `Workflow.add(..., depends_on=[...])`. Any acyclic shape — diamonds, multi-level fan-out/fan-in, mixed widths — is expressible directly.

---

## Validation

Graph errors raise `TaskWorkflowFault` before anything is enqueued, so a malformed workflow never partially executes:

- An empty workflow.
- A cycle — detected by depth-first traversal with a path stack; the fault names the cycle.
- A dependency index that does not exist.

```python
wf = Workflow("bad")
wf.add(step.s(), depends_on=[99])   # TaskWorkflowFault — unknown dependency
```

---

## Edge Cases

**A failed dependency does not release its dependents.** If a step exhausts its retries, everything downstream stays `WAITING` rather than running on missing input. Inspect with `failed_jobs()`. These jobs are not automatically cancelled — a `WAITING` job whose parent is dead will not run and will not complete.

**Result fidelity.** Dependency results arrive as the actual returned value when it is JSON-compatible. A non-JSON return value degrades to its `repr` on a persistent backend, because an arbitrary object cannot be reconstructed from JSON. Return dicts, lists, and primitives from steps whose results are consumed downstream.

**Serialization applies to every step.** `Workflow.run()` enqueues through the normal path, so a step with non-serializable arguments raises `TaskSerializationFault` on a persistent backend — at submission, before any step runs.

**Workflows do not span backends.** Every job in a workflow lives on the manager it was submitted to. To span processes, use a shared durable backend.

**Ordering within a group is not guaranteed.** `results()` returns terminal values in *declaration* order, but execution order and completion order are arbitrary.

---

## Performance Implications

Workflow submission is O(n) enqueues for n steps, performed up front. There is no polling process and no idle worker held open waiting for a dependency — a `WAITING` job occupies no worker slot. Dependency resolution is one lookup per dependency at release time.

For very wide graphs (thousands of parallel steps), submission cost is dominated by the enqueue round trips; on `RedisBackend` these are pipelined by the backend.

---

## Compatibility

Purely additive. `Workflow`, `Signature`, `WorkflowResult`, `chain`, `group`, and `chord` are new exports from `aquilia.tasks`. The `depends_on`, `workflow_id`, and `initial_state` parameters on `TaskManager.enqueue()` are new keyword-only arguments with defaults that preserve prior behavior. No existing API changed.

---

## Related

- [Distributed & Persistent Backends](distributed_tasks.md) — required for workflows that span processes
- [Idempotency & Deduplication](idempotency.md)
- [Migration Guide](migration.md)
