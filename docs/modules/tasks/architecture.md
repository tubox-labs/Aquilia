# Tasks Architecture

Async background job manager, task decorator registry, jobs, schedules, memory backend, worker loops, retries, and faults.

## Source Boundaries

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/tasks/__init__.py` | 82 | 0 | 0 | AquilaTasks — Industry-Grade Async Background Task Manager. |
| `aquilia/tasks/decorators.py` | 218 | 0 | 4 | AquilaTasks — Task Decorator. |
| `aquilia/tasks/engine.py` | 841 | 3 | 0 | AquilaTasks — Task Engine & Backends. |
| `aquilia/tasks/faults.py` | 130 | 5 | 0 | AquilaTasks — Fault Classes. |
| `aquilia/tasks/job.py` | 179 | 4 | 0 | AquilaTasks — Job Model. |
| `aquilia/tasks/schedule.py` | 254 | 2 | 2 | AquilaTasks — Schedule Definitions. |
| `aquilia/tasks/worker.py` | 98 | 1 | 0 | AquilaTasks — Worker. |

## Internal Shape

`tasks` has 7 Python files, 15 public classes, 6 public module-level functions, and 2 constants or module flags detected by AST.

## Runtime Responsibilities

- No mounted `aq` command group maps directly to this module; it is used through Python APIs, manifests, workspace integrations, or server startup wiring.

## Internal Imports

| Import | Count |
| --- | ---: |
| `.faults` | 4 |
| `.job` | 3 |
| `.decorators` | 2 |
| `.engine` | 2 |
| `.schedule` | 1 |
| `.worker` | 1 |
| `aquilia.faults.core` | 1 |

## External And Stdlib Imports

| Import root | Count |
| --- | ---: |
| `__future__` | 6 |
| `typing` | 4 |
| `datetime` | 3 |
| `asyncio` | 2 |
| `collections` | 2 |
| `contextlib` | 2 |
| `dataclasses` | 2 |
| `logging` | 2 |
| `abc` | 1 |
| `enum` | 1 |
| `functools` | 1 |
| `hashlib` | 1 |
| `heapq` | 1 |
| `time` | 1 |
| `traceback` | 1 |
| `uuid` | 1 |

## Lifecycle And Extension Points

| Extension Type | Source | Role |
| --- | --- | --- |
| `TaskBackend` | `aquilia/tasks/engine.py` | Abstract backend for job storage and retrieval. |
| `MemoryBackend` | `aquilia/tasks/engine.py` | In-process priority queue backend. |
| `TaskManager` | `aquilia/tasks/engine.py` | Central task coordinator. |

## Error Handling

Fault/error classes defined here:

`TaskFault`, `TaskScheduleFault`, `TaskNotBoundFault`, `TaskEnqueueFault`, `TaskResolutionFault`
