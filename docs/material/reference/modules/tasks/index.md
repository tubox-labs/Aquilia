# Tasks Module

> `aquilia.tasks` — Background job system

The Tasks module provides a background job system with priority queues, retries, timeouts, cron schedules, and pluggable backends. Worker loops run concurrently with the HTTP server.

## When to Use

Use the Tasks module when you need:

- Background processing outside the request/response cycle
- Scheduled jobs with cron expressions
- Retry logic with exponential backoff
- Priority-based queue processing
- Async task workflows

## Key Classes

| Class | Purpose |
|---|---|
| `TaskManager` | Central task queue manager |
| `TaskBackend` | Backend interface for task storage |
| `MemoryBackend` | In-memory task backend (dev) |
| `Worker` | Background worker processing loop |
| `Job` | Individual job with status and result |
| `JobResult` | Completed job result |
| `JobState` | Job lifecycle states |

## Quick Example

```python
from aquilia.tasks import task, TaskManager, MemoryBackend, TaskPriority

manager = TaskManager(MemoryBackend())
worker = Worker(manager, concurrency=4)
await worker.start()

# Define a task
@task(priority=TaskPriority.HIGH, retries=3, timeout=30)
async def send_welcome_email(user_id: str):
    user = await get_user(user_id)
    await send_mail(to=[user.email], subject="Welcome!")
    return {"sent": True}

# Enqueue
job = await manager.enqueue(send_welcome_email, user_id="42")
result = await job.wait()  # Block until complete (or timeout)

# Get status
status = await manager.get_job(job.id)
print(status.state)  # JobState.COMPLETED
```

## Import Path

```python
from aquilia.tasks import (
    TaskManager,
    TaskBackend,
    MemoryBackend,
    Worker,
    Job,
    JobResult,
    JobState,
    task,
    TaskPriority,
)
```

## Related Modules

- [integrations](../integrations/index.md) — `TasksIntegration` config builder
- [core/effects](../core/effects.md) — QueueEffect for pipeline integration
- [mail](../mail/index.md) — Background email delivery