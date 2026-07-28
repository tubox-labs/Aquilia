"""
AquilaTasks — Async Background Task Manager.

Async-native background task system for Aquilia:

- Priority-based task queues (CRITICAL > HIGH > NORMAL > LOW)
- In-memory backend (:class:`MemoryBackend`) for development, plus durable
  :class:`~aquilia.tasks.backends.RedisBackend` and
  :class:`~aquilia.tasks.backends.SQLBackend` for multi-process and
  multi-machine execution
- Task lifecycle: PENDING → RUNNING → COMPLETED / FAILED / CANCELLED
- Automatic retry with exponential backoff + jitter
- Task result storage and TTL-based cleanup
- Scheduled/delayed tasks, plus interval and cron periodic schedules
- Workflows: :func:`chain`, :func:`group`, :func:`chord`, and arbitrary
  DAGs via ``Workflow.add(..., depends_on=[...])``
- Enqueue deduplication on ``Job.fingerprint`` (``dedup="skip"`` or
  ``"raise"``), enforced across processes on durable backends
- Cancellation support
- Real-time task monitoring (histograms, p50/p95/p99, throughput timeline)
- Dead-letter queue for permanently failed tasks
- Admin dashboard integration

Not implemented today (deliberately absent, not stubbed):

- Per-queue rate limiting.

Distributed backends give **at-least-once** delivery: a worker that stalls
past its lease may have its job reclaimed and run twice, so task functions
should be idempotent.

Usage::

    from aquilia.tasks import TaskManager, task

    manager = TaskManager()

    @task(queue="default", max_retries=3, priority=Priority.NORMAL)
    async def send_email(to: str, subject: str, body: str):
        await smtp.send(to, subject, body)

    # Enqueue
    job_id = await manager.enqueue(send_email, to="user@example.com",
                                    subject="Hello", body="World")

    # Check status
    status = await manager.get_job(job_id)

    # Cancel
    await manager.cancel(job_id)
"""

from .decorators import task
from .engine import (
    MemoryBackend,
    TaskBackend,
    TaskManager,
)
from .faults import (
    TASKS_DOMAIN,
    TaskBackendFault,
    TaskDuplicateFault,
    TaskEnqueueFault,
    TaskFault,
    TaskNotBoundFault,
    TaskResolutionFault,
    TaskScheduleFault,
    TaskSerializationFault,
    TaskWorkflowFault,
)
from .job import (
    Job,
    JobResult,
    JobState,
    Priority,
)
from .schedule import CronSchedule, IntervalSchedule, cron, every
from .worker import Worker
from .workflow import Signature, Workflow, WorkflowResult, chain, chord, group

__all__ = [
    "TaskManager",
    "TaskBackend",
    "MemoryBackend",
    "Job",
    "JobState",
    "Priority",
    "JobResult",
    "Worker",
    "task",
    "every",
    "cron",
    "IntervalSchedule",
    "CronSchedule",
    # Workflows
    "Workflow",
    "WorkflowResult",
    "Signature",
    "chain",
    "group",
    "chord",
    # Faults
    "TASKS_DOMAIN",
    "TaskFault",
    "TaskScheduleFault",
    "TaskNotBoundFault",
    "TaskEnqueueFault",
    "TaskResolutionFault",
    "TaskSerializationFault",
    "TaskBackendFault",
    "TaskDuplicateFault",
    "TaskWorkflowFault",
]
