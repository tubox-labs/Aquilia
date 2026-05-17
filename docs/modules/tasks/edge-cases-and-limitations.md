# Tasks Edge Cases And Limitations

## Fault And Error Types

The following error-oriented classes are present in the implementation and should guide defensive usage.

| Type | Source | Meaning |
| --- | --- | --- |
| `TaskFault` | `aquilia/tasks/faults.py` | Base fault for the background task subsystem. |
| `TaskScheduleFault` | `aquilia/tasks/faults.py` | Invalid schedule configuration. |
| `TaskNotBoundFault` | `aquilia/tasks/faults.py` | Task descriptor has no bound TaskManager. |
| `TaskEnqueueFault` | `aquilia/tasks/faults.py` | Invalid callable passed to ``TaskManager.enqueue()``. |
| `TaskResolutionFault` | `aquilia/tasks/faults.py` | Cannot resolve task function from ``func_ref``. |

## Common Edge Cases

- Optional dependencies may change behavior. Check imports and constructor docs before enabling production features.
- In-memory stores, queues, caches, adapters, and registries are usually process-local. Use durable backends when state must survive restarts or scale across workers.
- Request-scoped data must not be cached globally. Use request state, DI request scopes, or explicit parameters.
- Decorators in Aquilia generally attach metadata at import time. Runtime behavior happens later during compilation, routing, middleware execution, or service startup.
- Many subsystems intentionally convert invalid states into typed faults. Catch the specific fault type when application code can recover.

## Source-Level Limits To Review

Review these files before changing behavior:

- `aquilia/tasks/__init__.py`: AquilaTasks - Industry-Grade Async Background Task Manager.
- `aquilia/tasks/decorators.py`: AquilaTasks - Task Decorator.
- `aquilia/tasks/engine.py`: AquilaTasks - Task Engine & Backends.
- `aquilia/tasks/faults.py`: AquilaTasks - Fault Classes.
- `aquilia/tasks/job.py`: AquilaTasks - Job Model.
- `aquilia/tasks/schedule.py`: AquilaTasks - Schedule Definitions.
- `aquilia/tasks/worker.py`: AquilaTasks - Worker.
