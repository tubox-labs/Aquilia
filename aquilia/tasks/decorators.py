"""
AquilaTasks — Task Decorator.

Provides the ``@task`` decorator for registering async functions
as background tasks with queue/retry/priority configuration.

Tasks can be dispatched in two ways:

1. **On-demand** — explicitly from controllers, services, or hooks::

       await record_login_attempt.delay(username="admin", ip="1.2.3.4")
       # or
       await manager.enqueue(record_login_attempt, username="admin")

2. **Periodic** — automatically by the scheduler loop::

       @task(schedule=every(hours=1))
       async def cleanup_sessions():
           ...
"""

from __future__ import annotations

import functools
from typing import TYPE_CHECKING, Any

from .faults import TaskNotBoundFault
from .job import Priority

if TYPE_CHECKING:
    from .schedule import Schedule


class _TaskDescriptor:
    """
    Wraps an async function with task metadata.

    When the decorated function is called directly, it executes normally
    (bypass queue).  Use ``.delay()`` / ``.send()`` to dispatch via the
    TaskManager queue, or ``TaskManager.enqueue(fn, ...)`` for full control.
    """

    def __init__(
        self,
        fn,
        *,
        name: str | None = None,
        queue: str = "default",
        priority: Priority = Priority.NORMAL,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        retry_backoff: float = 2.0,
        retry_max_delay: float = 300.0,
        timeout: float = 300.0,
        tags: list[str] | None = None,
        schedule: Schedule | None = None,
    ):
        self._fn = fn
        self.task_name = name or f"{fn.__module__}:{fn.__qualname__}"
        self.queue = queue
        self.priority = priority
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_backoff = retry_backoff
        self.retry_max_delay = retry_max_delay
        self.timeout = timeout
        self.tags = tags or []
        self.schedule = schedule

        # The TaskManager instance is injected at server startup
        self._manager: Any = None

        # Preserve function metadata
        functools.update_wrapper(self, fn)

    async def __call__(self, *args, **kwargs):
        """Direct invocation (bypass task queue)."""
        return await self._fn(*args, **kwargs)

    @property
    def func_ref(self) -> str:
        return self.task_name

    @property
    def is_periodic(self) -> bool:
        """Whether this task has a periodic schedule."""
        return self.schedule is not None

    # ── On-demand dispatch (industry standard) ───────────────────────

    async def delay(self, *args, **kwargs) -> str:
        """
        Enqueue this task for background execution (Celery-style).

        Dispatches the task to the TaskManager with the provided
        arguments.  Returns the job ID.

        This is the **primary API** for on-demand task dispatch::

            job_id = await record_login_attempt.delay(
                username="admin",
                ip_address="192.168.1.1",
                success=True,
            )

        Raises:
            RuntimeError: If no TaskManager is bound (server not started).
        """
        if self._manager is None:
            raise TaskNotBoundFault(self.task_name)
        return await self._manager.enqueue(self, *args, **kwargs)

    async def send(self, *args, **kwargs) -> str:
        """
        Alias for :meth:`delay` — enqueue task for background execution.

        Provided for compatibility with frameworks that use ``.send()``
        (e.g., Dramatiq, Huey).
        """
        return await self.delay(*args, **kwargs)

    def bind(self, manager) -> None:
        """Bind a TaskManager instance for .delay()/.send() dispatch."""
        self._manager = manager


# Registry of all decorated tasks
_task_registry: dict[str, _TaskDescriptor] = {}


def task(
    fn=None,
    *,
    name: str | None = None,
    queue: str = "default",
    priority: Priority = Priority.NORMAL,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    retry_backoff: float = 2.0,
    retry_max_delay: float = 300.0,
    timeout: float = 300.0,
    tags: list[str] | None = None,
    schedule: Schedule | None = None,
):
    """
    Decorator to register an async function as a background task.

    Can be used with or without arguments::

        @task
        async def simple_task():
            ...

        @task(queue="emails", max_retries=5, priority=Priority.HIGH)
        async def send_email(to: str, subject: str):
            ...

    **On-demand dispatch** (from controllers, services, hooks)::

        job_id = await send_email.delay(to="user@example.com", subject="Hi")

    **Periodic scheduling** (automatic, via scheduler loop)::

        @task(schedule=every(minutes=30))
        async def cleanup():
            ...

    Args:
        name: Task name (default: ``module:qualname``)
        queue: Queue name (default: ``"default"``)
        priority: Task priority
        max_retries: Max retry attempts on failure
        retry_delay: Base retry delay in seconds
        retry_backoff: Exponential backoff multiplier
        retry_max_delay: Maximum retry delay cap
        timeout: Max execution time in seconds
        tags: Metadata tags for filtering
        schedule: Periodic schedule (``every(...)`` or ``cron(...)``).
            If set, the scheduler loop auto-enqueues this task at the
            specified interval.  If ``None``, the task is on-demand only.
    """

    def decorator(fn_inner):
        descriptor = _TaskDescriptor(
            fn_inner,
            name=name,
            queue=queue,
            priority=priority,
            max_retries=max_retries,
            retry_delay=retry_delay,
            retry_backoff=retry_backoff,
            retry_max_delay=retry_max_delay,
            timeout=timeout,
            tags=tags,
            schedule=schedule,
        )
        _task_registry[descriptor.task_name] = descriptor
        return descriptor

    if fn is not None:
        # @task without parentheses
        return decorator(fn)
    return decorator


def get_registered_tasks() -> dict[str, _TaskDescriptor]:
    """Return all registered task descriptors."""
    return dict(_task_registry)


def get_task(name: str) -> _TaskDescriptor | None:
    """Look up a registered task by name."""
    return _task_registry.get(name)


def get_periodic_tasks() -> dict[str, _TaskDescriptor]:
    """Return only tasks that have a periodic schedule."""
    return {name: desc for name, desc in _task_registry.items() if desc.is_periodic}
