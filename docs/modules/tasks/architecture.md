# Tasks Architecture

## Runtime Role

The async background task system with task descriptors, job states, priority queues, retries, schedules, task manager, worker loops, cleanup, and queue stats.

The implementation is split across 7 Python files. The module boundary is visible in the file inventory below and the API reference is generated from the same source files.

## Primary Source Files

- `aquilia/tasks/__init__.py`: AquilaTasks - Industry-Grade Async Background Task Manager.
- `aquilia/tasks/decorators.py`: AquilaTasks - Task Decorator.
- `aquilia/tasks/engine.py`: AquilaTasks - Task Engine & Backends.
- `aquilia/tasks/faults.py`: AquilaTasks - Fault Classes.
- `aquilia/tasks/job.py`: AquilaTasks - Job Model.
- `aquilia/tasks/schedule.py`: AquilaTasks - Schedule Definitions.
- `aquilia/tasks/worker.py`: AquilaTasks - Worker.

## Internal Dependency Shape

The table below is derived from import statements in the module. It shows which top-level packages this module depends on most often.

| Imported package | Import count |
| --- | --- |
| `__future__` | 6 |
| `faults` | 4 |
| `typing` | 4 |
| `datetime` | 3 |
| `job` | 3 |
| `asyncio` | 2 |
| `collections` | 2 |
| `contextlib` | 2 |
| `dataclasses` | 2 |
| `decorators` | 2 |
| `engine` | 2 |
| `logging` | 2 |
| `abc` | 1 |
| `aquilia` | 1 |
| `enum` | 1 |
| `functools` | 1 |
| `hashlib` | 1 |
| `heapq` | 1 |
| `schedule` | 1 |
| `time` | 1 |
| `traceback` | 1 |
| `uuid` | 1 |
| `worker` | 1 |

## Data And Control Flow

1. Configuration or direct construction creates the public service objects, controllers, providers, or helpers for this module.
2. Runtime code imports the registered classes from manifests, workspace integrations, middleware stacks, or direct application code.
3. Public methods perform validation and convert invalid states into typed Aquilia faults where the implementation defines fault classes.
4. Integration points return Python data structures, `Response` objects, provider results, jobs, sessions, connections, or model instances depending on the subsystem.

## Boundary Rules

- Keep application-specific business decisions outside framework classes unless the class is explicitly a service or controller owned by your app.
- Prefer the public exports and typed configuration dataclasses shown in `api-reference.md`.
- When a module supplies both a low-level primitive and a high-level service, use the service in application code and keep primitives for tests, providers, or advanced integrations.
