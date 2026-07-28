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


class TaskSerializationFault(TaskFault):
    """
    A job could not be serialised for a persistent backend.

    Raised when ``Job.to_payload()`` encounters an argument that cannot be
    represented as JSON.  Persistent and distributed backends must move jobs
    across process boundaries, so live Python objects (ORM instances, open
    connections, closures) cannot be carried in ``args``/``kwargs``.

    The fix is to pass an identifier and re-load the object inside the task::

        # Breaks under a persistent backend
        await send_welcome.delay(user_object)

        # Correct
        await send_welcome.delay(user_id=user.id)

    Notes:
        JSON is deliberate: unlike ``pickle`` it cannot instantiate arbitrary
        classes on the worker, so a compromised queue cannot escalate into
        remote code execution.

    Args:
        func_ref: Task whose payload failed to serialise.
        reason: Underlying serialisation error.
        path: Argument path that failed, e.g. ``kwargs['user']``.
    """

    def __init__(self, func_ref: str, reason: str, *, path: str = "", **kwargs):
        location = f" at {path}" if path else ""
        super().__init__(
            code="TASK_SERIALIZATION_FAILED",
            message=(
                f"Job {func_ref!r} cannot be serialised for a persistent backend{location}: {reason}. "
                f"Pass JSON-compatible values (ids, dicts, lists) and re-load objects inside the task."
            ),
            severity=Severity.ERROR,
            retryable=False,
            metadata={"func_ref": func_ref, "reason": reason, "path": path, **kwargs.get("metadata", {})},
        )


class TaskBackendFault(TaskFault):
    """
    A task backend operation failed.

    Raised for transport-level failures in persistent backends — an
    unreachable Redis, a failed SQL statement, a missing driver package.
    Marked retryable because the caller may reasonably re-attempt once the
    dependency recovers.

    Args:
        backend: Backend class or configured name.
        operation: Backend method that failed, e.g. ``"pop"``.
        reason: Underlying error text.
    """

    def __init__(self, backend: str, operation: str, reason: str, **kwargs):
        super().__init__(
            code="TASK_BACKEND_ERROR",
            message=f"Task backend {backend!r} failed during {operation!r}: {reason}",
            severity=Severity.ERROR,
            retryable=True,
            metadata={
                "backend": backend,
                "operation": operation,
                "reason": reason,
                **kwargs.get("metadata", {}),
            },
        )


class TaskDuplicateFault(TaskFault):
    """
    A job with the same fingerprint is already in flight.

    Raised by :meth:`~aquilia.tasks.engine.TaskManager.enqueue` when
    ``dedup="raise"`` and an identical job (same ``func_ref``, queue, args and
    kwargs) is already queued or running.

    Notes:
        The default ``dedup`` policy is ``"allow"``, preserving the historical
        behaviour of enqueueing every request.  Use ``"skip"`` to silently
        return the existing job ID instead of raising.

    Args:
        fingerprint: Content fingerprint that collided.
        existing_job_id: ID of the job already in flight.
    """

    def __init__(self, fingerprint: str, existing_job_id: str, **kwargs):
        super().__init__(
            code="TASK_DUPLICATE",
            message=(
                f"A job with fingerprint {fingerprint!r} is already in flight as {existing_job_id!r}. "
                f"Use dedup='skip' to reuse it, or dedup='allow' to enqueue anyway."
            ),
            severity=Severity.WARN,
            retryable=False,
            metadata={
                "fingerprint": fingerprint,
                "existing_job_id": existing_job_id,
                **kwargs.get("metadata", {}),
            },
        )


class TaskWorkflowFault(TaskFault):
    """
    A workflow definition is invalid.

    Raised when building a :mod:`~aquilia.tasks.workflow` graph that cannot
    execute — an empty chain, a dependency on an unknown node, or a cycle.

    Notes:
        Cycles are rejected at build time rather than at execution time: a
        cyclic DAG would deadlock silently, with every node waiting on an
        unsatisfiable dependency and no worker ever making progress.

    Args:
        reason: What is structurally wrong with the workflow.
    """

    def __init__(self, reason: str, **kwargs):
        super().__init__(
            code="TASK_WORKFLOW_INVALID",
            message=f"Invalid workflow: {reason}",
            severity=Severity.ERROR,
            retryable=False,
            metadata={"reason": reason, **kwargs.get("metadata", {})},
        )
