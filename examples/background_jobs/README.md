# Background Jobs Starter

## Purpose

Background job example with controller-triggered dispatch, priority queues, retry metadata, scheduled cleanup, and job status inspection.

## Architecture

- `workspace.py` enables the tasks integration with two workers.
- `tasks.py` declares `@task` functions for mail, reports, and scheduled maintenance.
- `JobsService` owns a local `TaskManager` and starts it lazily for local development.
- `JobsController` enqueues work and exposes status/stats endpoints.

## Run

```bash
cd examples/background_jobs
python -m uvicorn runtime:app --reload --port 8040
```

Expected behavior: POST routes return accepted job IDs, and status routes read from the task manager.

## Test

```bash
python -m pytest examples/background_jobs -q
```

## Common Pitfalls

- `.delay()` works after a `TaskManager` has started and bound registered task descriptors.
- The memory backend does not survive restarts.
- Long-running jobs should use explicit timeouts and durable backend configuration in production.

## Extension Ideas

Move manager startup into lifecycle hooks, add Redis-backed queues, add dead-letter monitoring, and emit WebSocket notifications when jobs complete.

## Related APIs

`TaskManager`, `TaskBackend`, `MemoryBackend`, `@task`, `Priority`, `every`, `BackgroundTaskConfig`.
