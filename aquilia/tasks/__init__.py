"""
AquilaTasks — Industry-Grade Async Background Task Manager.

Provides a robust, production-ready background task system for Aquilia:
- Priority-based task queues (CRITICAL > HIGH > NORMAL > LOW)
- Multiple backends: in-memory (default), Redis
- Task lifecycle: PENDING → RUNNING → COMPLETED / FAILED / CANCELLED
- Automatic retry with exponential backoff + jitter
- Task result storage and TTL-based cleanup
- Scheduled/delayed tasks
- Cancellation support
- Real-time task monitoring
- Rate limiting per-queue
- Dead-letter queue for permanently failed tasks
- Admin dashboard integration

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

from .engine import (
    TaskManager,
    TaskBackend,
    MemoryBackend,
)
from .job import (
    Job,
    JobState,
    Priority,
    JobResult,
)
from .decorators import task
from .schedule import every, cron, IntervalSchedule, CronSchedule
from .worker import Worker

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
]
