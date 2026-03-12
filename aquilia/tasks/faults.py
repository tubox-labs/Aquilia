"""
AquilaTasks — Fault Classes.

Typed, structured fault classes for the background task system.
Replaces raw ValueError / RuntimeError / TypeError raises with
first-class Aquilia Fault objects.

Domains:
    TASKS — Background task scheduling, dispatch, and resolution faults.
"""

from __future__ import annotations

from typing import Any

from aquilia.faults.core import Fault, FaultDomain, Severity

# ============================================================================
# Domain
# ============================================================================

TASKS_DOMAIN = FaultDomain.custom("tasks", "Background task faults")


# ============================================================================
# Base
# ============================================================================


class TaskFault(Fault):
    """Base fault for the background task subsystem."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        severity: Severity = Severity.ERROR,
        retryable: bool = False,
        public: bool = False,
        metadata: dict[str, Any] | None = None,
    ):
        super().__init__(
            code=code,
            message=message,
            domain=TASKS_DOMAIN,
            severity=severity,
            retryable=retryable,
            public=public,
            metadata=metadata,
        )


# ============================================================================
# Concrete Faults
# ============================================================================


class TaskScheduleFault(TaskFault):
    """
    Invalid schedule configuration.

    Raised when ``every()`` or ``cron()`` receives invalid parameters
    (e.g. interval ≤ 0 or malformed cron expression).
    """

    def __init__(self, reason: str, **kwargs):
        super().__init__(
            code="TASK_SCHEDULE_INVALID",
            message=f"Invalid task schedule: {reason}",
            severity=Severity.ERROR,
            retryable=False,
            metadata={"reason": reason, **kwargs.get("metadata", {})},
        )


class TaskNotBoundFault(TaskFault):
    """
    Task descriptor has no bound TaskManager.

    Raised when ``.delay()`` / ``.send()`` is called before the server
    has started and bound the TaskManager to the descriptor.
    """

    def __init__(self, task_name: str, **kwargs):
        super().__init__(
            code="TASK_NOT_BOUND",
            message=(
                f"Task {task_name!r} has no bound TaskManager. Ensure the server is started before calling .delay()."
            ),
            severity=Severity.ERROR,
            retryable=False,
            metadata={"task_name": task_name, **kwargs.get("metadata", {})},
        )


class TaskEnqueueFault(TaskFault):
    """
    Invalid callable passed to ``TaskManager.enqueue()``.

    Raised when the first argument is neither a ``@task`` descriptor
    nor a plain callable.
    """

    def __init__(self, actual_type: str, **kwargs):
        super().__init__(
            code="TASK_ENQUEUE_INVALID",
            message=f"Expected callable or @task descriptor, got {actual_type}",
            severity=Severity.ERROR,
            retryable=False,
            metadata={"actual_type": actual_type, **kwargs.get("metadata", {})},
        )


class TaskResolutionFault(TaskFault):
    """
    Cannot resolve task function from ``func_ref``.

    Raised when the worker cannot find the callable for a stored job,
    typically because the func_ref does not match any registered task.
    """

    def __init__(self, func_ref: str, **kwargs):
        super().__init__(
            code="TASK_RESOLUTION_FAILED",
            message=f"Cannot resolve task function: {func_ref}",
            severity=Severity.ERROR,
            retryable=False,
            metadata={"func_ref": func_ref, **kwargs.get("metadata", {})},
        )
