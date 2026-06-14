# Background Jobs

The Background Jobs example demonstrates controller-triggered job dispatch, priority
queues, retry metadata, scheduled periodic tasks, and job status inspection using
Aquilia's task subsystem.

---

## What It Demonstrates

- `@task` decorator for defining background job functions
- Queue-based task routing with `queue="mail"`, `queue="reports"`, `queue="maintenance"`
- `Priority.HIGH` and `Priority.NORMAL` enqueue ordering
- `max_retries` and `retry_delay` for automatic retry behavior
- `every()` scheduler for periodic tasks (`every(minutes=30)`)
- `TaskManager` lifecycle: start, bind, enqueue, inspect
- `MemoryBackend` for development and testing
- Controller-triggered dispatch via HTTP endpoints
- Job status and stats inspection endpoints

## Key Files

| File | Purpose |
| ---- | ------- |
| `workspace.py` | Enables tasks integration with 2 workers and memory backend |
| `modules/jobs/manifest.py` | Declares `JobsController`, `JobsService`, and task modules |
| `modules/jobs/controllers.py` | HTTP endpoints for triggering jobs and reading status |
| `modules/jobs/services.py` | `JobsService` owning `TaskManager` lifecycle |
| `modules/jobs/tasks.py` | Three `@task` functions: mail, reports, maintenance |

## Task Definitions

```python
from aquilia.tasks import Priority, every, task

@task(queue="mail", priority=Priority.HIGH, max_retries=5, retry_delay=2.0, tags=["mail", "user"])
async def send_welcome_email(email: str, name: str) -> dict:
    return {"sent": True, "email": email, "name": name}

@task(queue="reports", priority=Priority.NORMAL, timeout=120.0, tags=["reports"])
async def rebuild_daily_report(date: str) -> dict:
    return {"rebuilt": True, "date": date}

@task(queue="maintenance", schedule=every(minutes=30), tags=["maintenance"])
async def cleanup_old_jobs() -> dict:
    return {"cleaned": True}
```

### Task Configuration Options

| Option | Purpose |
| ------ | ------- |
| `queue` | Named queue for workload isolation |
| `priority` | `Priority.HIGH` or `Priority.NORMAL` — high-priority tasks dequeued first |
| `max_retries` | Automatic retry count on failure |
| `retry_delay` | Seconds between retry attempts |
| `timeout` | Maximum execution time before cancellation |
| `schedule` | `every()` expression for periodic execution |
| `tags` | Metadata labels for filtering and monitoring |

### Schedule Expressions

```python
every(seconds=5)       # Every 5 seconds
every(minutes=30)      # Every 30 minutes
every(hours=1)         # Every 1 hour
every(days=1)          # Every 1 day
```

## Dispatching Jobs

Jobs are dispatched from controllers through the `JobsService`:

```python
class JobsController(Controller):
    prefix = "/"
    tags = ["jobs"]

    @POST("/mail/welcome")
    async def trigger_welcome_email(self, ctx: RequestCtx):
        body = await ctx.json()
        job = await self.service.enqueue_welcome_email(body["email"], body["name"])
        return Response.json({"job_id": job.id, "status": "accepted"}, status=202)

    @GET("/jobs/<job_id:str>")
    async def job_status(self, ctx: RequestCtx, job_id: str):
        status = await self.service.get_job(job_id)
        return Response.json(status.to_dict())

    @GET("/stats")
    async def job_stats(self, ctx: RequestCtx):
        return Response.json(await self.service.get_stats())
```

## TaskManager Lifecycle

The `JobsService` manages the `TaskManager`:

```python
class JobsService:
    def __init__(self):
        self._manager: TaskManager | None = None
        self._backend = MemoryBackend()

    async def _ensure_manager(self):
        if self._manager is None:
            self._manager = TaskManager(backend=self._backend, num_workers=2)
            await self._manager.start()
        return self._manager

    async def enqueue_welcome_email(self, email: str, name: str) -> TaskRecord:
        manager = await self._ensure_manager()
        return await manager.enqueue("send_welcome_email", email=email, name=name)
```

Key lifecycle points:

1. `TaskManager(backend, num_workers)` creates the manager with a backend
2. `.start()` begins worker processing and binds registered `@task` descriptors
3. `.enqueue(func_name, **kwargs)` dispatches a named task with arguments
4. Only tasks registered via `@task` are enqueueable (allowlist security)

## Workspace Tasks Configuration

```python
workspace = Workspace("jobs-app", version="1.0.0")
    .tasks(num_workers=4, backend="memory", scheduler_tick=15.0)
```

| Setting | Default | Purpose |
| ------- | ------- | ------- |
| `num_workers` | 2 | Number of concurrent task worker coroutines |
| `backend` | `"memory"` | Task backend (`"memory"` or `"redis"`) |
| `scheduler_tick` | 30.0 | Seconds between schedule checks for periodic tasks |

## Running

```bash
cd examples/background_jobs
python -m uvicorn runtime:app --reload --port 8040
```

Trigger jobs and inspect status:

```bash
# Enqueue a welcome email
curl -X POST http://127.0.0.1:8040/jobs/mail/welcome \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","name":"Alice"}'

# Check job status (use the job_id from the response)
curl http://127.0.0.1:8040/jobs/jobs/<job_id>

# View queue stats
curl http://127.0.0.1:8040/jobs/stats

# Run tests
python -m pytest examples/background_jobs -q
```

## What You'll Learn

- How to define background tasks with the `@task` decorator
- How to configure queue routing, priorities, retries, and timeouts
- How to schedule periodic maintenance tasks with `every()`
- How to manage `TaskManager` lifecycle within a service
- How to enqueue tasks from controller methods
- How to inspect job status and queue statistics
- How the task allowlist security model prevents arbitrary code execution