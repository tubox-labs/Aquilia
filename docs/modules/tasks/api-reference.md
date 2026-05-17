# Tasks API Reference

This page is extracted from the current Python source. It includes public classes, methods, functions, constants, dataclass-like fields, decorators, and notable attributes.

## Public Class Summary

| Name | Source | Bases | Purpose |
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

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `task` | `aquilia/tasks/decorators.py` | `def task(fn = None, *, name: str &#124; None = None, queue: str = 'default', priority: Priority = Priority.NORMAL, max_retries: int = 3, retry_delay: float = 1.0, retry_backoff: float = 2.0, retry_max_delay: float = 300.0, timeout: float = 300.0, tags: list[str] &#124; None = None, schedule: Schedule &#124; None = None)` | Decorator to register an async function as a background task. |
| `get_registered_tasks` | `aquilia/tasks/decorators.py` | `def get_registered_tasks() -> dict[str, _TaskDescriptor]` | Return all registered task descriptors. |
| `get_task` | `aquilia/tasks/decorators.py` | `def get_task(name: str) -> _TaskDescriptor &#124; None` | Look up a registered task by name. |
| `get_periodic_tasks` | `aquilia/tasks/decorators.py` | `def get_periodic_tasks() -> dict[str, _TaskDescriptor]` | Return only tasks that have a periodic schedule. |
| `every` | `aquilia/tasks/schedule.py` | `def every(*, seconds: float = 0, minutes: float = 0, hours: float = 0, days: float = 0) -> IntervalSchedule` | Create a fixed-interval schedule. |
| `cron` | `aquilia/tasks/schedule.py` | `def cron(expression: str) -> CronSchedule` | Create a cron-expression schedule. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `TASKS_DOMAIN` | `aquilia/tasks/faults.py` | `FaultDomain.custom('tasks', 'Background task faults')` |

## Detailed Classes And Methods

### Class: `TaskBackend`

- Source: `aquilia/tasks/engine.py`
- Bases: `ABC`
- Summary: Abstract backend for job storage and retrieval.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `push` | `async def push(self, job: Job) -> None` | abstractmethod | Add job to the queue. |
| `pop` | `async def pop(self, queue: str = 'default') -> Job &#124; None` | abstractmethod | Retrieve highest-priority runnable job from queue. |
| `get` | `async def get(self, job_id: str) -> Job &#124; None` | abstractmethod | Get job by ID. |
| `update` | `async def update(self, job: Job) -> None` | abstractmethod | Persist job state changes. |
| `list_jobs` | `async def list_jobs(self, *, queue: str &#124; None = None, state: JobState &#124; None = None, limit: int = 100, offset: int = 0) -> list[Job]` | abstractmethod | List jobs with optional filters. |
| `get_stats` | `async def get_stats(self) -> dict[str, Any]` | abstractmethod | Aggregate statistics across all queues. |
| `get_queue_stats` | `async def get_queue_stats(self) -> dict[str, dict[str, int]]` | abstractmethod | Per-queue breakdown of job counts by state. |
| `cleanup` | `async def cleanup(self, max_age_seconds: float = 3600) -> int` | abstractmethod | Remove terminal jobs older than max_age_seconds. Returns count removed. |
| `cancel` | `async def cancel(self, job_id: str) -> bool` | abstractmethod | Cancel a job. Returns True if successfully cancelled. |
| `retry` | `async def retry(self, job_id: str) -> bool` | abstractmethod | Manually retry a failed/dead job. Returns True if re-queued. |
| `flush` | `async def flush(self, queue: str &#124; None = None) -> int` | abstractmethod | Remove all jobs (optionally in a specific queue). Returns count removed. |

### Class: `MemoryBackend`

- Source: `aquilia/tasks/engine.py`
- Bases: `TaskBackend`
- Summary: In-process priority queue backend.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `push` | `async def push(self, job: Job) -> None` |  | Method. |
| `pop` | `async def pop(self, queue: str = 'default') -> Job &#124; None` |  | Method. |
| `get` | `async def get(self, job_id: str) -> Job &#124; None` |  | Method. |
| `update` | `async def update(self, job: Job) -> None` |  | Method. |
| `list_jobs` | `async def list_jobs(self, *, queue: str &#124; None = None, state: JobState &#124; None = None, limit: int = 100, offset: int = 0) -> list[Job]` |  | Method. |
| `get_stats` | `async def get_stats(self) -> dict[str, Any]` |  | Method. |
| `get_queue_stats` | `async def get_queue_stats(self) -> dict[str, dict[str, int]]` |  | Method. |
| `cleanup` | `async def cleanup(self, max_age_seconds: float = 3600) -> int` |  | Method. |
| `cancel` | `async def cancel(self, job_id: str) -> bool` |  | Method. |
| `retry` | `async def retry(self, job_id: str) -> bool` |  | Method. |
| `flush` | `async def flush(self, queue: str &#124; None = None) -> int` |  | Method. |

### Class: `TaskManager`

- Source: `aquilia/tasks/engine.py`
- Bases: `object`
- Summary: Central task coordinator.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `start` | `async def start(self) -> None` |  | Start worker tasks, cleanup loop, and scheduler loop. |
| `stop` | `async def stop(self, timeout: float = 10.0) -> None` |  | Gracefully stop all workers. |
| `is_running` | `def is_running(self) -> bool` | property | Method. |
| `enqueue` | `async def enqueue(self, func, *args, queue: str &#124; None = None, priority: Priority &#124; None = None, delay: float &#124; None = None, max_retries: int &#124; None = None, timeout: float &#124; None = None, tags: list[str] &#124; None = None, metadata: dict[str, Any] &#124; None = None, **kwargs) -> str` |  | Enqueue a task for background execution. |
| `get_job` | `async def get_job(self, job_id: str) -> Job &#124; None` |  | Get job by ID. |
| `list_jobs` | `async def list_jobs(self, *, queue: str &#124; None = None, state: JobState &#124; None = None, limit: int = 100, offset: int = 0) -> list[Job]` |  | List jobs with optional filters. |
| `cancel` | `async def cancel(self, job_id: str) -> bool` |  | Cancel a pending/running job. |
| `retry_job` | `async def retry_job(self, job_id: str) -> bool` |  | Manually retry a failed/dead job. |
| `flush` | `async def flush(self, queue: str &#124; None = None) -> int` |  | Remove all jobs from a queue (or all queues). |
| `get_stats` | `async def get_stats(self) -> dict[str, Any]` |  | Get comprehensive task manager statistics. |
| `get_queue_stats` | `async def get_queue_stats(self) -> dict[str, dict[str, int]]` |  | Per-queue breakdown. |
| `on_complete` | `def on_complete(self, callback: Callable) -> None` |  | Register callback for job completion. |
| `on_failure` | `def on_failure(self, callback: Callable) -> None` |  | Register callback for job failure. |
| `on_dead_letter` | `def on_dead_letter(self, callback: Callable) -> None` |  | Register callback for dead-letter jobs. |

### Class: `TaskFault`

- Source: `aquilia/tasks/faults.py`
- Bases: `Fault`
- Summary: Base fault for the background task subsystem.

### Class: `TaskScheduleFault`

- Source: `aquilia/tasks/faults.py`
- Bases: `TaskFault`
- Summary: Invalid schedule configuration.

### Class: `TaskNotBoundFault`

- Source: `aquilia/tasks/faults.py`
- Bases: `TaskFault`
- Summary: Task descriptor has no bound TaskManager.

### Class: `TaskEnqueueFault`

- Source: `aquilia/tasks/faults.py`
- Bases: `TaskFault`
- Summary: Invalid callable passed to ``TaskManager.enqueue()``.

### Class: `TaskResolutionFault`

- Source: `aquilia/tasks/faults.py`
- Bases: `TaskFault`
- Summary: Cannot resolve task function from ``func_ref``.

### Class: `JobState`

- Source: `aquilia/tasks/job.py`
- Bases: `str, Enum`
- Summary: Task lifecycle states.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `PENDING` |  | `'pending'` |
| `SCHEDULED` |  | `'scheduled'` |
| `RUNNING` |  | `'running'` |
| `COMPLETED` |  | `'completed'` |
| `FAILED` |  | `'failed'` |
| `RETRYING` |  | `'retrying'` |
| `CANCELLED` |  | `'cancelled'` |
| `DEAD` |  | `'dead'` |

### Class: `Priority`

- Source: `aquilia/tasks/job.py`
- Bases: `int, Enum`
- Summary: Task priority levels (lower value = higher priority).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `CRITICAL` |  | `0` |
| `HIGH` |  | `1` |
| `NORMAL` |  | `2` |
| `LOW` |  | `3` |

### Class: `JobResult`

- Source: `aquilia/tasks/job.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Stores the result or error from a completed/failed job.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `success` | `bool` |  |
| `value` | `Any` | `None` |
| `error` | `str &#124; None` | `None` |
| `error_type` | `str &#124; None` | `None` |
| `traceback` | `str &#124; None` | `None` |
| `duration_ms` | `float` | `0.0` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `Job`

- Source: `aquilia/tasks/job.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Represents a background task job.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `id` | `str` | `field(default_factory=lambda: uuid.uuid4().hex[:16])` |
| `name` | `str` | `''` |
| `queue` | `str` | `'default'` |
| `priority` | `Priority` | `Priority.NORMAL` |
| `func_ref` | `str` | `''` |
| `args` | `tuple[Any, ...]` | `field(default_factory=tuple)` |
| `kwargs` | `dict[str, Any]` | `field(default_factory=dict)` |
| `state` | `JobState` | `JobState.PENDING` |
| `result` | `JobResult &#124; None` | `None` |
| `max_retries` | `int` | `3` |
| `retry_count` | `int` | `0` |
| `retry_delay` | `float` | `1.0` |
| `retry_backoff` | `float` | `2.0` |
| `retry_max_delay` | `float` | `300.0` |
| `created_at` | `datetime` | `field(default_factory=lambda: datetime.now(timezone.utc))` |
| `started_at` | `datetime &#124; None` | `None` |
| `completed_at` | `datetime &#124; None` | `None` |
| `scheduled_at` | `datetime &#124; None` | `None` |
| `timeout` | `float` | `300.0` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict)` |
| `tags` | `list[str]` | `field(default_factory=list)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `is_terminal` | `def is_terminal(self) -> bool` | property | Check if job is in a terminal state. |
| `is_runnable` | `def is_runnable(self) -> bool` | property | Check if job can be executed now. |
| `next_retry_delay` | `def next_retry_delay(self) -> float` | property | Calculate next retry delay with exponential backoff + jitter. |
| `can_retry` | `def can_retry(self) -> bool` | property | Check if job has remaining retry attempts. |
| `duration_ms` | `def duration_ms(self) -> float &#124; None` | property | Execution duration in milliseconds. |
| `fingerprint` | `def fingerprint(self) -> str` | property | Stable fingerprint for deduplication. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialise job for API/admin consumption. |

### Class: `IntervalSchedule`

- Source: `aquilia/tasks/schedule.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Fixed-interval periodic schedule.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `interval` | `float` |  |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `human_readable` | `def human_readable(self) -> str` | property | Human-friendly representation of the interval. |
| `next_run` | `def next_run(self, last_run: datetime &#124; None = None) -> datetime` |  | Calculate the next run time. |

### Class: `CronSchedule`

- Source: `aquilia/tasks/schedule.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Cron-expression periodic schedule.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `expression` | `str` |  |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `human_readable` | `def human_readable(self) -> str` | property | Method. |
| `matches` | `def matches(self, dt: datetime) -> bool` |  | Check if a datetime matches this cron expression. |
| `next_run` | `def next_run(self, last_run: datetime &#124; None = None) -> datetime` |  | Calculate next matching minute from ``last_run``. |

### Class: `Worker`

- Source: `aquilia/tasks/worker.py`
- Bases: `object`
- Summary: Individual task worker.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `start` | `async def start(self) -> None` |  | Start worker as an asyncio task. |
| `stop` | `async def stop(self) -> None` |  | Stop the worker gracefully. |
| `is_running` | `def is_running(self) -> bool` | property | Method. |
| `stats` | `def stats(self) -> dict` | property | Method. |

## Functions

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `task` | `aquilia/tasks/decorators.py` | `def task(fn = None, *, name: str &#124; None = None, queue: str = 'default', priority: Priority = Priority.NORMAL, max_retries: int = 3, retry_delay: float = 1.0, retry_backoff: float = 2.0, retry_max_delay: float = 300.0, timeout: float = 300.0, tags: list[str] &#124; None = None, schedule: Schedule &#124; None = None)` | Decorator to register an async function as a background task. |
| `get_registered_tasks` | `aquilia/tasks/decorators.py` | `def get_registered_tasks() -> dict[str, _TaskDescriptor]` | Return all registered task descriptors. |
| `get_task` | `aquilia/tasks/decorators.py` | `def get_task(name: str) -> _TaskDescriptor &#124; None` | Look up a registered task by name. |
| `get_periodic_tasks` | `aquilia/tasks/decorators.py` | `def get_periodic_tasks() -> dict[str, _TaskDescriptor]` | Return only tasks that have a periodic schedule. |
| `every` | `aquilia/tasks/schedule.py` | `def every(*, seconds: float = 0, minutes: float = 0, hours: float = 0, days: float = 0) -> IntervalSchedule` | Create a fixed-interval schedule. |
| `cron` | `aquilia/tasks/schedule.py` | `def cron(expression: str) -> CronSchedule` | Create a cron-expression schedule. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `TASKS_DOMAIN` | `aquilia/tasks/faults.py` | `FaultDomain.custom('tasks', 'Background task faults')` |
