"""
AquilaTasks — Worker.

Standalone worker class for granular control over task execution.

:class:`TaskManager` spawns its own worker loops internally; ``Worker``
exists for the cases where you want individually addressable, separately
startable workers — custom pools, per-worker metrics, or draining a single
worker without stopping the manager.

Execution itself is **not** re-implemented here: every worker delegates to
:meth:`TaskManager.drain_once`, so queue polling, priority ordering, retry
and dead-lettering behave identically no matter which loop pulled the job.

Usage::

    manager = TaskManager(num_workers=0)   # no built-in workers
    worker = Worker(manager, name="mailer-1")
    await worker.start()
    ...
    await worker.stop()
    print(worker.stats)   # {'jobs_processed': 12, 'jobs_failed': 1, ...}
"""

from __future__ import annotations

import asyncio
import contextlib
import logging

from aquilia.tasks.engine import TaskManager
from aquilia.tasks.job import Job, JobState

logger = logging.getLogger("aquilia.tasks")


class Worker:
    """
    Individual task worker.

    Pulls jobs from the manager's backend via :meth:`TaskManager.drain_once`
    and executes them, tracking per-worker counters.

    Lifecycle:
        :meth:`start` creates a background ``asyncio.Task`` running the poll
        loop; :meth:`stop` cancels it and awaits unwinding.  A stopped worker
        can be started again.

    Async-safety:
        A single ``Worker`` drives one ``asyncio.Task``; counters are only
        mutated from that task.  Multiple workers may share one manager and
        backend — :class:`~aquilia.tasks.engine.MemoryBackend` serialises
        pops behind an ``asyncio.Lock``, so no job is handed to two workers.

    Args:
        manager: Task manager owning the backend and execution pipeline.
        name: Worker label, used in log lines and the asyncio task name.
        poll_interval: Seconds to sleep when every queue is empty.

    Attributes:
        stats: Live counter snapshot — see :attr:`stats`.

    Examples::

        worker = Worker(manager, name="reports", poll_interval=0.05)
        await worker.start()
        await asyncio.sleep(5)
        await worker.stop()
    """

    def __init__(
        self,
        manager: TaskManager,
        name: str = "worker",
        *,
        poll_interval: float = 0.1,
    ) -> None:
        self.manager = manager
        self.name = name
        self.poll_interval = poll_interval

        self._task: asyncio.Task | None = None
        self._running = False
        self._jobs_processed = 0
        self._jobs_failed = 0

    async def start(self) -> None:
        """Start the worker as a background asyncio task (idempotent)."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(
            self._loop(),
            name=f"aquilia-{self.name}",
        )

    async def stop(self) -> None:
        """
        Stop the worker.

        Cancels the poll loop and awaits it.  A job already mid-execution
        receives ``CancelledError`` at its next await point.
        """
        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    @property
    def is_running(self) -> bool:
        """True while the poll loop task is active."""
        return self._running

    @property
    def stats(self) -> dict[str, object]:
        """
        Per-worker counters.

        Keys:
            name: Worker label.
            running: Whether the poll loop is active.
            jobs_processed: Jobs this worker executed to a terminal or
                retry-scheduled state.
            jobs_failed: Jobs whose execution ended in failure —
                ``FAILED``, ``DEAD``, or scheduled for retry
                (``RETRYING``).  Loop-level errors (a backend raising)
                also count here.
        """
        return {
            "name": self.name,
            "running": self._running,
            "jobs_processed": self._jobs_processed,
            "jobs_failed": self._jobs_failed,
        }

    async def _loop(self) -> None:
        """
        Poll-and-execute loop.

        Delegates each iteration to :meth:`TaskManager.drain_once`.  Job
        failures never propagate out of that call (the manager converts them
        into retries or dead-letters), so failure counting is driven by the
        returned job's post-run state rather than by an ``except`` block.
        """
        while self._running:
            try:
                job: Job | None = await self.manager.drain_once(self.name)

                if job is None:
                    await asyncio.sleep(self.poll_interval)
                    continue

                self._jobs_processed += 1
                if job.state in (JobState.FAILED, JobState.DEAD, JobState.RETRYING):
                    self._jobs_failed += 1

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._jobs_failed += 1
                logger.error(f"{self.name} error: {e}", exc_info=True)
                await asyncio.sleep(1.0)
