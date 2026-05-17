# Tasks Documentation

This directory is the professional documentation set for `tasks`. It is implementation-driven and aligned with the current source files under `aquilia/tasks`.

## What This Covers

The async background task system with task descriptors, job states, priority queues, retries, schedules, task manager, worker loops, cleanup, and queue stats.

## Source Files Read

- `aquilia/tasks/__init__.py`: AquilaTasks - Industry-Grade Async Background Task Manager.
- `aquilia/tasks/decorators.py`: AquilaTasks - Task Decorator.
- `aquilia/tasks/engine.py`: AquilaTasks - Task Engine & Backends.
- `aquilia/tasks/faults.py`: AquilaTasks - Fault Classes.
- `aquilia/tasks/job.py`: AquilaTasks - Job Model.
- `aquilia/tasks/schedule.py`: AquilaTasks - Schedule Definitions.
- `aquilia/tasks/worker.py`: AquilaTasks - Worker.

## Document Map

- `architecture.md`: Runtime architecture and module boundaries
- `configuration.md`: Configuration entry points, datatypes, and precedence
- `api-reference.md`: Classes, methods, functions, constants, and data fields extracted from source
- `integration-guide.md`: How to wire the module into a real Aquilia application
- `cli-reference.md`: Command line surface and operational commands
- `edge-cases-and-limitations.md`: Known edge cases and implementation limits
- `troubleshooting.md`: Common failures and diagnosis steps
- `examples.md`: Code examples and usage patterns

## Public Surface Snapshot

- Python files: 7
- Public classes: 15
- Configuration or dataclass-like types: 4
- Public functions: 6
- Constants detected: 1

## Fast Start

```python
from aquilia.tasks import Priority, TaskManager, every, task

@task(queue="mail", priority=Priority.HIGH, max_retries=5, schedule=every(minutes=30))
async def send_digest(email: str) -> dict:
    return {"sent": True, "email": email}

manager = TaskManager(num_workers=2)
await manager.start()
job_id = await send_digest.delay(email="user@example.com")
job = await manager.get_job(job_id)
await manager.stop()
```

## Read Next

Start with `architecture.md` if you are learning how the subsystem fits into runtime boot. Use `api-reference.md` when you need exact methods, datatypes, and class fields. Use `examples.md` for copyable patterns that match the current code.
