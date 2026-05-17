# tasks Module

## Purpose

Async background job system. Use this module for task decorators, queues, priority jobs, retries, schedules, worker loops, backend stats, and task controllers.

## Source Coverage

- Python files: 7
- Public classes: 15
- Dataclasses: 4
- Enums: 2
- Public functions: 6

## How It Fits In Aquilia

1. Decorate async functions with task, optionally with queue, priority, retry, timeout, tags, and schedule.
2. Start TaskManager so descriptors bind and workers begin consuming jobs.
3. Dispatch with descriptor.delay, descriptor.send, or manager.enqueue, then inspect jobs and queue stats.

## Practical Guidance

- The memory backend is process-local. Use it for development, tests, or single-worker deployments only.
- Only registered task descriptors are resolved by the worker. This prevents arbitrary function execution.

## Public Classes

| Name | Source | Role |
| --- | --- | --- |
| `TaskBackend` | `aquilia/tasks/engine.py` | Abstract backend for job storage and retrieval. |
| `MemoryBackend` | `aquilia/tasks/engine.py` | In-process priority queue backend. |
| `TaskManager` | `aquilia/tasks/engine.py` | Central task coordinator. |
| `TaskFault` | `aquilia/tasks/faults.py` | Base fault for the background task subsystem. |
| `TaskScheduleFault` | `aquilia/tasks/faults.py` | Invalid schedule configuration. |
| `TaskNotBoundFault` | `aquilia/tasks/faults.py` | Task descriptor has no bound TaskManager. |
| `TaskEnqueueFault` | `aquilia/tasks/faults.py` | Invalid callable passed to ``TaskManager.enqueue()``. |
| `TaskResolutionFault` | `aquilia/tasks/faults.py` | Cannot resolve task function from ``func_ref``. |
| `JobState` | `aquilia/tasks/job.py` | Task lifecycle states. |
| `Priority` | `aquilia/tasks/job.py` | Task priority levels (lower value = higher priority). |
| `JobResult` | `aquilia/tasks/job.py` | Stores the result or error from a completed/failed job. |
| `Job` | `aquilia/tasks/job.py` | Represents a background task job. |
| `IntervalSchedule` | `aquilia/tasks/schedule.py` | Fixed-interval periodic schedule. |
| `CronSchedule` | `aquilia/tasks/schedule.py` | Cron-expression periodic schedule. |
| `Worker` | `aquilia/tasks/worker.py` | Individual task worker. |

## Public Functions

| Name | Source | Role |
| --- | --- | --- |
| `task` | `aquilia/tasks/decorators.py` | Decorator to register an async function as a background task. |
| `get_registered_tasks` | `aquilia/tasks/decorators.py` | Return all registered task descriptors. |
| `get_task` | `aquilia/tasks/decorators.py` | Look up a registered task by name. |
| `get_periodic_tasks` | `aquilia/tasks/decorators.py` | Return only tasks that have a periodic schedule. |
| `every` | `aquilia/tasks/schedule.py` | Create a fixed-interval schedule. |
| `cron` | `aquilia/tasks/schedule.py` | Create a cron-expression schedule. |

## Implementation Map

| File | What To Look For |
| --- | --- |
| `aquilia/tasks/__init__.py` | AquilaTasks - Industry-Grade Async Background Task Manager. |
| `aquilia/tasks/decorators.py` | AquilaTasks - Task Decorator. |
| `aquilia/tasks/engine.py` | AquilaTasks - Task Engine & Backends. |
| `aquilia/tasks/faults.py` | AquilaTasks - Fault Classes. |
| `aquilia/tasks/job.py` | AquilaTasks - Job Model. |
| `aquilia/tasks/schedule.py` | AquilaTasks - Schedule Definitions. |
| `aquilia/tasks/worker.py` | AquilaTasks - Worker. |

## Testing Pointers

Search `tests/` for `tasks` to find behavior-level examples. The test suite is especially useful for edge cases because many modules expose lightweight public APIs but enforce important security and lifecycle behavior internally.
