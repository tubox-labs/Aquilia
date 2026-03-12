"""
AquilaTasks — Worker.

Standalone worker class for more granular control over task execution.
Typically used internally by TaskManager, but can be instantiated
directly for custom worker pools.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging

from .engine import TaskManager

logger = logging.getLogger("aquilia.tasks")


class Worker:
    """
    Individual task worker.

    Pulls jobs from the TaskManager's backend and executes them.
    Provides per-worker metrics and lifecycle control.
    """

    def __init__(
        self,
        manager: TaskManager,
        name: str = "worker",
        *,
        poll_interval: float = 0.1,
    ):
        self.manager = manager
        self.name = name
        self.poll_interval = poll_interval

        self._task: asyncio.Task | None = None
        self._running = False
        self._jobs_processed = 0
        self._jobs_failed = 0

    async def start(self) -> None:
        """Start worker as an asyncio task."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(
            self._loop(),
            name=f"aquilia-{self.name}",
        )

    async def stop(self) -> None:
        """Stop the worker gracefully."""
        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def stats(self) -> dict:
        return {
            "name": self.name,
            "running": self._running,
            "jobs_processed": self._jobs_processed,
            "jobs_failed": self._jobs_failed,
        }

    async def _loop(self) -> None:
        """Main worker loop."""
        while self._running:
            try:
                job = None
                for queue in list(self.manager._queues):
                    job = await self.manager.backend.pop(queue)
                    if job:
                        break

                if not job:
                    await asyncio.sleep(self.poll_interval)
                    continue

                await self.manager._execute_job(job, self.name)
                self._jobs_processed += 1

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._jobs_failed += 1
                logger.error(f"{self.name} error: {e}", exc_info=True)
                await asyncio.sleep(1.0)
