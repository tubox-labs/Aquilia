# Tasks API Reference

This page is generated from the current Python source using the AST. It lists public classes, public methods, public module-level functions, constants, exports, and source files.

## Source Inventory

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/tasks/__init__.py` | 82 | 0 | 0 | AquilaTasks — Industry-Grade Async Background Task Manager. |
| `aquilia/tasks/decorators.py` | 218 | 0 | 4 | AquilaTasks — Task Decorator. |
| `aquilia/tasks/engine.py` | 841 | 3 | 0 | AquilaTasks — Task Engine & Backends. |
| `aquilia/tasks/faults.py` | 130 | 5 | 0 | AquilaTasks — Fault Classes. |
| `aquilia/tasks/job.py` | 179 | 4 | 0 | AquilaTasks — Job Model. |
| `aquilia/tasks/schedule.py` | 254 | 2 | 2 | AquilaTasks — Schedule Definitions. |
| `aquilia/tasks/worker.py` | 98 | 1 | 0 | AquilaTasks — Worker. |

## Public Exports

`CronSchedule`, `IntervalSchedule`, `Job`, `JobResult`, `JobState`, `MemoryBackend`, `Priority`, `TASKS_DOMAIN`, `TaskBackend`, `TaskEnqueueFault`, `TaskFault`, `TaskManager`, `TaskNotBoundFault`, `TaskResolutionFault`, `TaskScheduleFault`, `Worker`, `cron`, `every`, `task`

## Public Class Summary

| Class | Source | Bases | Summary |
| --- | --- | --- | --- |
| `TaskBackend` | `aquilia/tasks/engine.py` | ABC | Abstract backend for job storage and retrieval. |
| `MemoryBackend` | `aquilia/tasks/engine.py` | TaskBackend | In-process priority queue backend. |
| `TaskManager` | `aquilia/tasks/engine.py` | object | Central task coordinator. |
| `TaskFault` | `aquilia/tasks/faults.py` | Fault | Base fault for the background task subsystem. |
| `TaskScheduleFault` | `aquilia/tasks/faults.py` | TaskFault | Invalid schedule configuration. |
| `TaskNotBoundFault` | `aquilia/tasks/faults.py` | TaskFault | Task descriptor has no bound TaskManager. |
| `TaskEnqueueFault` | `aquilia/tasks/faults.py` | TaskFault | Invalid callable passed to ``TaskManager.enqueue()``. |
| `TaskResolutionFault` | `aquilia/tasks/faults.py` | TaskFault | Cannot resolve task function from ``func_ref``. |
| `JobState` | `aquilia/tasks/job.py` | str, Enum | Task lifecycle states. |
| `Priority` | `aquilia/tasks/job.py` | int, Enum | Task priority levels (lower value = higher priority). |
| `JobResult` | `aquilia/tasks/job.py` | object | Stores the result or error from a completed/failed job. |
| `Job` | `aquilia/tasks/job.py` | object | Represents a background task job. |
| `IntervalSchedule` | `aquilia/tasks/schedule.py` | object | Fixed-interval periodic schedule. |
| `CronSchedule` | `aquilia/tasks/schedule.py` | object | Cron-expression periodic schedule. |
| `Worker` | `aquilia/tasks/worker.py` | object | Individual task worker. |

## Public Function Summary

| Function | Source | Signature | Summary |
| --- | --- | --- | --- |
| `task` | `aquilia/tasks/decorators.py` | `def task(fn=None, *, name: str \| None=None, queue: str='default', priority: Priority=Priority.NORMAL, max_retries: int=3, retry_delay: float=1.0, retry_backoff: float=2.0, retry_max_delay: float=300.0, timeout: float=300.0, tags: list[str] \| None=None, schedule: Schedule \| None=None)` | Decorator to register an async function as a background task. |
| `get_registered_tasks` | `aquilia/tasks/decorators.py` | `def get_registered_tasks()` | Return all registered task descriptors. |
| `get_task` | `aquilia/tasks/decorators.py` | `def get_task(name: str)` | Look up a registered task by name. |
| `get_periodic_tasks` | `aquilia/tasks/decorators.py` | `def get_periodic_tasks()` | Return only tasks that have a periodic schedule. |
| `every` | `aquilia/tasks/schedule.py` | `def every(*, seconds: float=0, minutes: float=0, hours: float=0, days: float=0)` | Create a fixed-interval schedule. |
| `cron` | `aquilia/tasks/schedule.py` | `def cron(expression: str)` | Create a cron-expression schedule. |

## Constants And Module Flags

| Name | Source | Value or Type |
| --- | --- | --- |
| `TASKS_DOMAIN` | `aquilia/tasks/faults.py` | `FaultDomain.custom('tasks', 'Background task faults')` |

## Detailed Classes And Methods

### `TaskBackend`

- Source: `aquilia/tasks/engine.py`
- Bases: `ABC`
- Summary: Abstract backend for job storage and retrieval.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `push` | `async def push(self, job: Job)` | Add job to the queue. |
| `pop` | `async def pop(self, queue: str='default')` | Retrieve highest-priority runnable job from queue. |
| `get` | `async def get(self, job_id: str)` | Get job by ID. |
| `update` | `async def update(self, job: Job)` | Persist job state changes. |
| `list_jobs` | `async def list_jobs(self, *, queue: str \| None=None, state: JobState \| None=None, limit: int=100, offset: int=0)` | List jobs with optional filters. |
| `get_stats` | `async def get_stats(self)` | Aggregate statistics across all queues. |
| `get_queue_stats` | `async def get_queue_stats(self)` | Per-queue breakdown of job counts by state. |
| `cleanup` | `async def cleanup(self, max_age_seconds: float=3600)` | Remove terminal jobs older than max_age_seconds. Returns count removed. |
| `cancel` | `async def cancel(self, job_id: str)` | Cancel a job. Returns True if successfully cancelled. |
| `retry` | `async def retry(self, job_id: str)` | Manually retry a failed/dead job. Returns True if re-queued. |
| `flush` | `async def flush(self, queue: str \| None=None)` | Remove all jobs (optionally in a specific queue). Returns count removed. |

### `MemoryBackend`

- Source: `aquilia/tasks/engine.py`
- Bases: `TaskBackend`
- Summary: In-process priority queue backend.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `push` | `async def push(self, job: Job)` |  |
| `pop` | `async def pop(self, queue: str='default')` |  |
| `get` | `async def get(self, job_id: str)` |  |
| `update` | `async def update(self, job: Job)` |  |
| `list_jobs` | `async def list_jobs(self, *, queue: str \| None=None, state: JobState \| None=None, limit: int=100, offset: int=0)` |  |
| `get_stats` | `async def get_stats(self)` |  |
| `get_queue_stats` | `async def get_queue_stats(self)` |  |
| `cleanup` | `async def cleanup(self, max_age_seconds: float=3600)` |  |
| `cancel` | `async def cancel(self, job_id: str)` |  |
| `retry` | `async def retry(self, job_id: str)` |  |
| `flush` | `async def flush(self, queue: str \| None=None)` |  |

### `TaskManager`

- Source: `aquilia/tasks/engine.py`
- Bases: `object`
- Summary: Central task coordinator.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `start` | `async def start(self)` | Start worker tasks, cleanup loop, and scheduler loop. |
| `stop` | `async def stop(self, timeout: float=10.0)` | Gracefully stop all workers. |
| `is_running` | `def is_running(self)` |  |
| `enqueue` | `async def enqueue(self, func, *args, queue: str \| None=None, priority: Priority \| None=None, delay: float \| None=None, max_retries: int \| None=None, timeout: float \| None=None, tags: list[str] \| None=None, metadata: dict[str, Any] \| None=None, **kwargs)` | Enqueue a task for background execution. |
| `get_job` | `async def get_job(self, job_id: str)` | Get job by ID. |
| `list_jobs` | `async def list_jobs(self, *, queue: str \| None=None, state: JobState \| None=None, limit: int=100, offset: int=0)` | List jobs with optional filters. |
| `cancel` | `async def cancel(self, job_id: str)` | Cancel a pending/running job. |
| `retry_job` | `async def retry_job(self, job_id: str)` | Manually retry a failed/dead job. |
| `flush` | `async def flush(self, queue: str \| None=None)` | Remove all jobs from a queue (or all queues). |
| `get_stats` | `async def get_stats(self)` | Get comprehensive task manager statistics. |
| `get_queue_stats` | `async def get_queue_stats(self)` | Per-queue breakdown. |
| `on_complete` | `def on_complete(self, callback: Callable)` | Register callback for job completion. |
| `on_failure` | `def on_failure(self, callback: Callable)` | Register callback for job failure. |
| `on_dead_letter` | `def on_dead_letter(self, callback: Callable)` | Register callback for dead-letter jobs. |

### `TaskFault`

- Source: `aquilia/tasks/faults.py`
- Bases: `Fault`
- Summary: Base fault for the background task subsystem.

### `TaskScheduleFault`

- Source: `aquilia/tasks/faults.py`
- Bases: `TaskFault`
- Summary: Invalid schedule configuration.

### `TaskNotBoundFault`

- Source: `aquilia/tasks/faults.py`
- Bases: `TaskFault`
- Summary: Task descriptor has no bound TaskManager.

### `TaskEnqueueFault`

- Source: `aquilia/tasks/faults.py`
- Bases: `TaskFault`
- Summary: Invalid callable passed to ``TaskManager.enqueue()``.

### `TaskResolutionFault`

- Source: `aquilia/tasks/faults.py`
- Bases: `TaskFault`
- Summary: Cannot resolve task function from ``func_ref``.

### `JobState`

- Source: `aquilia/tasks/job.py`
- Bases: `str, Enum`
- Summary: Task lifecycle states.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `PENDING` | `` | `'pending'` |
| `SCHEDULED` | `` | `'scheduled'` |
| `RUNNING` | `` | `'running'` |
| `COMPLETED` | `` | `'completed'` |
| `FAILED` | `` | `'failed'` |
| `RETRYING` | `` | `'retrying'` |
| `CANCELLED` | `` | `'cancelled'` |
| `DEAD` | `` | `'dead'` |

### `Priority`

- Source: `aquilia/tasks/job.py`
- Bases: `int, Enum`
- Summary: Task priority levels (lower value = higher priority).

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `CRITICAL` | `` | `0` |
| `HIGH` | `` | `1` |
| `NORMAL` | `` | `2` |
| `LOW` | `` | `3` |

### `JobResult`

- Source: `aquilia/tasks/job.py`
- Bases: `object`
- Summary: Stores the result or error from a completed/failed job.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `success` | `bool` | `` |
| `value` | `Any` | `None` |
| `error` | `str \| None` | `None` |
| `error_type` | `str \| None` | `None` |
| `traceback` | `str \| None` | `None` |
| `duration_ms` | `float` | `0.0` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `Job`

- Source: `aquilia/tasks/job.py`
- Bases: `object`
- Summary: Represents a background task job.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `id` | `str` | `field(default_factory=lambda: uuid.uuid4().hex[:16])` |
| `name` | `str` | `''` |
| `queue` | `str` | `'default'` |
| `priority` | `Priority` | `Priority.NORMAL` |
| `func_ref` | `str` | `''` |
| `args` | `tuple[Any, ...]` | `field(default_factory=tuple)` |
| `kwargs` | `dict[str, Any]` | `field(default_factory=dict)` |
| `state` | `JobState` | `JobState.PENDING` |
| `result` | `JobResult \| None` | `None` |
| `max_retries` | `int` | `3` |
| `retry_count` | `int` | `0` |
| `retry_delay` | `float` | `1.0` |
| `retry_backoff` | `float` | `2.0` |
| `retry_max_delay` | `float` | `300.0` |
| `created_at` | `datetime` | `field(default_factory=lambda: datetime.now(timezone.utc))` |
| `started_at` | `datetime \| None` | `None` |
| `completed_at` | `datetime \| None` | `None` |
| `scheduled_at` | `datetime \| None` | `None` |
| `timeout` | `float` | `300.0` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict)` |
| `tags` | `list[str]` | `field(default_factory=list)` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `is_terminal` | `def is_terminal(self)` | Check if job is in a terminal state. |
| `is_runnable` | `def is_runnable(self)` | Check if job can be executed now. |
| `next_retry_delay` | `def next_retry_delay(self)` | Calculate next retry delay with exponential backoff + jitter. |
| `can_retry` | `def can_retry(self)` | Check if job has remaining retry attempts. |
| `duration_ms` | `def duration_ms(self)` | Execution duration in milliseconds. |
| `fingerprint` | `def fingerprint(self)` | Stable fingerprint for deduplication. |
| `to_dict` | `def to_dict(self)` | Serialise job for API/admin consumption. |

### `IntervalSchedule`

- Source: `aquilia/tasks/schedule.py`
- Bases: `object`
- Summary: Fixed-interval periodic schedule.
- Decorators: `dataclass(frozen=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `interval` | `float` | `` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `human_readable` | `def human_readable(self)` | Human-friendly representation of the interval. |
| `next_run` | `def next_run(self, last_run: datetime \| None=None)` | Calculate the next run time. |

### `CronSchedule`

- Source: `aquilia/tasks/schedule.py`
- Bases: `object`
- Summary: Cron-expression periodic schedule.
- Decorators: `dataclass(frozen=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `expression` | `str` | `` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `human_readable` | `def human_readable(self)` |  |
| `matches` | `def matches(self, dt: datetime)` | Check if a datetime matches this cron expression. |
| `next_run` | `def next_run(self, last_run: datetime \| None=None)` | Calculate next matching minute from ``last_run``. |

### `Worker`

- Source: `aquilia/tasks/worker.py`
- Bases: `object`
- Summary: Individual task worker.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `start` | `async def start(self)` | Start worker as an asyncio task. |
| `stop` | `async def stop(self)` | Stop the worker gracefully. |
| `is_running` | `def is_running(self)` |  |
| `stats` | `def stats(self)` |  |
