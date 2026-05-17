---
name: aquilia-task-worker-scheduler
description: "Build Aquilia background task workflows. Use for @task, TaskManager, TaskBackend, MemoryBackend, Worker, intervals, cron schedules, retries, queues, startup task registration, and task-related module manifests/CLI behavior."
---

# Aquilia Task Worker Scheduler

## Purpose
Implement background jobs and periodic work using Aquilia's task registry, manager, scheduler, and workers.

## Trigger Conditions
Use for async background jobs, queues, priorities, retries, scheduled tasks, module `tasks.py`, `BackgroundTaskConfig`, and testing task execution.

## Inputs
- Task function name, queue, priority, retry count, timeout, and schedule.
- Backend choice and worker count.
- Module ownership and whether tasks should be auto-discovered.

## Execution Flow
1. Define task functions with `@task(...)` in a module `tasks.py` or explicit path.
2. Configure workspace tasks with `Workspace.tasks(...)` or `Integration.tasks(...)`.
3. Add module-level `BackgroundTaskConfig` when manifest visibility is needed.
4. Use `TaskManager` to enqueue and `Worker` to process jobs.
5. Use `every(...)` and `cron(...)` from task schedules for periodic work.

## Constraints
- Aquilia tasks execute registered tasks only; do not add arbitrary function reference resolution.
- Keep task payloads serializable and small enough for the backend.
- Long-running tasks need explicit timeout/retry policy.

## Implementation Anchors
`aquilia/tasks/decorators.py`, `aquilia/tasks/engine.py`, `aquilia/tasks/job.py`, `aquilia/tasks/schedule.py`, `aquilia/tasks/worker.py`, `aquilia/manifest.py`, `examples/background_jobs/`, `tests/test_tasks_system.py`.

## Examples
- Add `@task(name="send_digest", queue="mail", retries=3)`.
- Configure `.tasks(num_workers=4, backend="memory", scheduler_tick=15.0)`.
- Add `background_tasks=BackgroundTaskConfig(tasks=["modules.jobs.tasks:cleanup"])`.

## Failure Handling
Unknown task names should raise task resolution faults. Enqueue/backend failures map to task faults. Periodic schedule parse errors should be handled before worker startup.
