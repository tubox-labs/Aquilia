"""
AquilaTasks — Task Decorator.

Provides the ``@task`` decorator for registering async functions
as background tasks with queue/retry/priority configuration.
"""

from __future__ import annotations

import functools
from typing import Any, Optional

from .job import Priority


class _TaskDescriptor:
    """
    Wraps an async function with task metadata.

    When the decorated function is called directly, it executes normally.
    Use ``TaskManager.enqueue(fn, ...)`` to dispatch as background job.
    """

    def __init__(
        self,
        fn,
        *,
        name: Optional[str] = None,
        queue: str = "default",
        priority: Priority = Priority.NORMAL,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        retry_backoff: float = 2.0,
        retry_max_delay: float = 300.0,
        timeout: float = 300.0,
        tags: Optional[list[str]] = None,
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

        # Preserve function metadata
        functools.update_wrapper(self, fn)

    async def __call__(self, *args, **kwargs):
        """Direct invocation (bypass task queue)."""
        return await self._fn(*args, **kwargs)

    @property
    def func_ref(self) -> str:
        return self.task_name


# Registry of all decorated tasks
_task_registry: dict[str, _TaskDescriptor] = {}


def task(
    fn=None,
    *,
    name: Optional[str] = None,
    queue: str = "default",
    priority: Priority = Priority.NORMAL,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    retry_backoff: float = 2.0,
    retry_max_delay: float = 300.0,
    timeout: float = 300.0,
    tags: Optional[list[str]] = None,
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


def get_task(name: str) -> Optional[_TaskDescriptor]:
    """Look up a registered task by name."""
    return _task_registry.get(name)
