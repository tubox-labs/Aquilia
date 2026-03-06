"""
AquilaTasks — Task Engine & Backends.

TaskManager is the central coordinator:
- Accepts jobs via enqueue()
- Dispatches to the configured backend
- Tracks job lifecycle
- Provides monitoring/stats APIs

Backends:
- MemoryBackend: In-process priority queue (default, no dependencies)
- Can be extended with Redis, PostgreSQL, etc.
"""

from __future__ import annotations

import asyncio
import logging
import time
import traceback as tb_mod
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from heapq import heappop, heappush
from typing import Any, Callable, Dict, List, Optional, Tuple

from .job import Job, JobResult, JobState, Priority
from .decorators import _TaskDescriptor, get_task


logger = logging.getLogger("aquilia.tasks")


# ============================================================================
# Backend ABC
# ============================================================================

class TaskBackend(ABC):
    """Abstract backend for job storage and retrieval."""

    @abstractmethod
    async def push(self, job: Job) -> None:
        """Add job to the queue."""

    @abstractmethod
    async def pop(self, queue: str = "default") -> Optional[Job]:
        """Retrieve highest-priority runnable job from queue."""

    @abstractmethod
    async def get(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""

    @abstractmethod
    async def update(self, job: Job) -> None:
        """Persist job state changes."""

    @abstractmethod
    async def list_jobs(
        self,
        *,
        queue: Optional[str] = None,
        state: Optional[JobState] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Job]:
        """List jobs with optional filters."""

    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Aggregate statistics across all queues."""

    @abstractmethod
    async def get_queue_stats(self) -> Dict[str, Dict[str, int]]:
        """Per-queue breakdown of job counts by state."""

    @abstractmethod
    async def cleanup(self, max_age_seconds: float = 3600) -> int:
        """Remove terminal jobs older than max_age_seconds. Returns count removed."""

    @abstractmethod
    async def cancel(self, job_id: str) -> bool:
        """Cancel a job. Returns True if successfully cancelled."""

    @abstractmethod
    async def retry(self, job_id: str) -> bool:
        """Manually retry a failed/dead job. Returns True if re-queued."""

    @abstractmethod
    async def flush(self, queue: Optional[str] = None) -> int:
        """Remove all jobs (optionally in a specific queue). Returns count removed."""


# ============================================================================
# In-Memory Backend
# ============================================================================

class MemoryBackend(TaskBackend):
    """
    In-process priority queue backend.

    Uses a heap per queue for O(log n) push/pop.
    Stores all jobs in a dict for O(1) lookup.
    Thread-safe via asyncio locks.

    Suitable for single-process deployments, development, and testing.
    """

    def __init__(self):
        self._jobs: Dict[str, Job] = {}
        self._queues: Dict[str, list] = defaultdict(list)  # heap per queue
        self._counter = 0  # Tie-breaker for heap stability
        self._lock = asyncio.Lock()
        self._dead_letter: deque[Job] = deque(maxlen=1000)

    async def push(self, job: Job) -> None:
        async with self._lock:
            self._jobs[job.id] = job
            self._counter += 1
            heappush(
                self._queues[job.queue],
                (job.priority.value, self._counter, job.id),
            )

    async def pop(self, queue: str = "default") -> Optional[Job]:
        async with self._lock:
            heap = self._queues.get(queue, [])
            now = datetime.now(timezone.utc)
            while heap:
                priority_val, counter, job_id = heappop(heap)
                job = self._jobs.get(job_id)
                if job is None:
                    continue
                if job.is_terminal:
                    continue
                # Check scheduled time
                if job.scheduled_at and now < job.scheduled_at:
                    # Push back — not ready yet
                    heappush(heap, (priority_val, counter, job_id))
                    return None
                if job.state in (JobState.PENDING, JobState.RETRYING, JobState.SCHEDULED):
                    return job
            return None

    async def get(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    async def update(self, job: Job) -> None:
        async with self._lock:
            self._jobs[job.id] = job
            if job.state == JobState.DEAD:
                self._dead_letter.append(job)

    async def list_jobs(
        self,
        *,
        queue: Optional[str] = None,
        state: Optional[JobState] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Job]:
        jobs = list(self._jobs.values())
        if queue:
            jobs = [j for j in jobs if j.queue == queue]
        if state:
            jobs = [j for j in jobs if j.state == state]
        # Sort by created_at descending (newest first)
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs[offset: offset + limit]

    async def get_stats(self) -> Dict[str, Any]:
        all_jobs = list(self._jobs.values())
        by_state: Dict[str, int] = defaultdict(int)
        for j in all_jobs:
            by_state[j.state.value] += 1

        completed = [j for j in all_jobs if j.state == JobState.COMPLETED and j.duration_ms is not None]
        failed = [j for j in all_jobs if j.state in (JobState.FAILED, JobState.DEAD)]
        avg_duration = (
            sum(j.duration_ms for j in completed) / len(completed)
            if completed else 0.0
        )

        # ── Duration distribution (histogram buckets in ms) ─────────
        duration_buckets = [0, 10, 50, 100, 250, 500, 1000, 5000, float("inf")]
        duration_histogram = [0] * (len(duration_buckets) - 1)
        duration_labels = ["<10ms", "10-50ms", "50-100ms", "100-250ms",
                           "250-500ms", "0.5-1s", "1-5s", ">5s"]
        for j in completed:
            for i in range(len(duration_buckets) - 1):
                if duration_buckets[i] <= j.duration_ms < duration_buckets[i + 1]:
                    duration_histogram[i] += 1
                    break

        # ── Throughput timeline (hourly, last 24h) ──────────────────
        now = datetime.now(timezone.utc)
        throughput_labels = []
        completed_hourly = []
        failed_hourly = []
        for i in range(24):
            t = now - timedelta(hours=23 - i)
            hour_str = t.strftime("%Y-%m-%d %H:00")
            label = t.strftime("%H:00")
            throughput_labels.append(label)
            # Count completed jobs in this hour
            c_count = sum(
                1 for j in completed
                if j.completed_at and j.completed_at.strftime("%Y-%m-%d %H:00") == hour_str
            )
            f_count = sum(
                1 for j in failed
                if j.completed_at and j.completed_at.strftime("%Y-%m-%d %H:00") == hour_str
            )
            completed_hourly.append(c_count)
            failed_hourly.append(f_count)

        # ── Success rate ────────────────────────────────────────────
        terminal = len(completed) + len(failed)
        success_rate = round((len(completed) / terminal * 100) if terminal else 100, 1)

        # ── P50/P95/P99 latencies ───────────────────────────────────
        sorted_durations = sorted(j.duration_ms for j in completed) if completed else []
        p50 = sorted_durations[len(sorted_durations) // 2] if sorted_durations else 0
        p95 = sorted_durations[int(len(sorted_durations) * 0.95)] if sorted_durations else 0
        p99 = sorted_durations[int(len(sorted_durations) * 0.99)] if sorted_durations else 0

        # ── Per-queue chart data ────────────────────────────────────
        queue_chart_labels = sorted(self._queues.keys()) if self._queues else ["default"]
        queue_pending = []
        queue_running = []
        queue_completed_q = []
        queue_failed_q = []
        for q in queue_chart_labels:
            q_jobs = [j for j in all_jobs if j.queue == q]
            queue_pending.append(sum(1 for j in q_jobs if j.state in (JobState.PENDING, JobState.SCHEDULED)))
            queue_running.append(sum(1 for j in q_jobs if j.state == JobState.RUNNING))
            queue_completed_q.append(sum(1 for j in q_jobs if j.state == JobState.COMPLETED))
            queue_failed_q.append(sum(1 for j in q_jobs if j.state in (JobState.FAILED, JobState.DEAD)))

        # ── Job state doughnut ──────────────────────────────────────
        state_labels = list(by_state.keys()) if by_state else ["No Jobs"]
        state_values = list(by_state.values()) if by_state else [0]

        return {
            "total_jobs": len(all_jobs),
            "by_state": dict(by_state),
            "queues": list(self._queues.keys()),
            "queue_count": len(self._queues),
            "avg_duration_ms": round(avg_duration, 2),
            "dead_letter_count": len(self._dead_letter),
            "completed_count": len(completed),
            "failed_count": by_state.get("failed", 0),
            "active_count": by_state.get("running", 0),
            "pending_count": by_state.get("pending", 0) + by_state.get("scheduled", 0),
            "success_rate": success_rate,
            "p50_ms": round(p50, 2),
            "p95_ms": round(p95, 2),
            "p99_ms": round(p99, 2),
            # ── Chart.js ready data ─────────────────────────────────
            "charts": {
                "throughput": {
                    "labels": throughput_labels,
                    "completed": completed_hourly,
                    "failed": failed_hourly,
                },
                "duration_histogram": {
                    "labels": duration_labels,
                    "values": duration_histogram,
                },
                "state_doughnut": {
                    "labels": state_labels,
                    "values": state_values,
                },
                "queue_breakdown": {
                    "labels": queue_chart_labels,
                    "pending": queue_pending,
                    "running": queue_running,
                    "completed": queue_completed_q,
                    "failed": queue_failed_q,
                },
            },
        }

    async def get_queue_stats(self) -> Dict[str, Dict[str, int]]:
        result: Dict[str, Dict[str, int]] = {}
        for job in self._jobs.values():
            if job.queue not in result:
                result[job.queue] = defaultdict(int)
            result[job.queue][job.state.value] += 1
        return {q: dict(counts) for q, counts in result.items()}

    async def cleanup(self, max_age_seconds: float = 3600) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=max_age_seconds)
        to_remove = [
            jid for jid, j in self._jobs.items()
            if j.is_terminal and j.completed_at and j.completed_at < cutoff
        ]
        for jid in to_remove:
            del self._jobs[jid]
        return len(to_remove)

    async def cancel(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if not job or job.is_terminal:
            return False
        job.state = JobState.CANCELLED
        job.completed_at = datetime.now(timezone.utc)
        return True

    async def retry(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if not job:
            return False
        if job.state not in (JobState.FAILED, JobState.DEAD, JobState.CANCELLED):
            return False
        job.state = JobState.RETRYING
        job.completed_at = None
        job.result = None
        self._counter += 1
        heappush(
            self._queues[job.queue],
            (job.priority.value, self._counter, job.id),
        )
        return True

    async def flush(self, queue: Optional[str] = None) -> int:
        if queue:
            to_remove = [jid for jid, j in self._jobs.items() if j.queue == queue]
            for jid in to_remove:
                del self._jobs[jid]
            self._queues.pop(queue, None)
            return len(to_remove)
        count = len(self._jobs)
        self._jobs.clear()
        self._queues.clear()
        return count


# ============================================================================
# Task Manager
# ============================================================================

class TaskManager:
    """
    Central task coordinator.

    Manages job lifecycle:
    1. Accept task via enqueue()
    2. Store in backend
    3. Workers pull from backend via pop()
    4. Execute and update state
    5. Handle retries on failure
    6. Provide monitoring APIs

    Usage::

        manager = TaskManager()
        await manager.start()  # Start background workers

        job_id = await manager.enqueue(my_task, arg1, arg2, kwarg1="val")
        status = await manager.get_job(job_id)

        await manager.stop()
    """

    def __init__(
        self,
        *,
        backend: Optional[TaskBackend] = None,
        num_workers: int = 4,
        default_queue: str = "default",
        cleanup_interval: float = 300.0,  # 5 minutes
        cleanup_max_age: float = 3600.0,  # 1 hour
        scheduler_tick: float = 15.0,  # Scheduler poll interval in seconds
    ):
        self.backend = backend or MemoryBackend()
        self.num_workers = num_workers
        self.default_queue = default_queue
        self.cleanup_interval = cleanup_interval
        self.cleanup_max_age = cleanup_max_age
        self.scheduler_tick = scheduler_tick

        self._workers: list[asyncio.Task] = []
        self._cleanup_task: Optional[asyncio.Task] = None
        self._scheduler_task: Optional[asyncio.Task] = None
        self._running = False
        self._queues: set[str] = {default_queue}

        # Periodic schedule tracking: task_name → last_enqueued_at
        self._schedule_last_run: Dict[str, datetime] = {}

        # Event listeners
        self._on_complete: list[Callable] = []
        self._on_failure: list[Callable] = []
        self._on_dead_letter: list[Callable] = []

        # Metrics
        self._total_enqueued = 0
        self._total_completed = 0
        self._total_failed = 0
        self._started_at: Optional[datetime] = None

    # ========================================================================
    # Lifecycle
    # ========================================================================

    async def start(self) -> None:
        """Start worker tasks, cleanup loop, and scheduler loop."""
        if self._running:
            return
        self._running = True
        self._started_at = datetime.now(timezone.utc)

        # Bind task manager to all registered task descriptors
        self._bind_task_descriptors()

        # Start workers
        for i in range(self.num_workers):
            worker = asyncio.create_task(
                self._worker_loop(f"worker-{i}"),
                name=f"aquilia-task-worker-{i}",
            )
            self._workers.append(worker)

        # Start cleanup loop
        self._cleanup_task = asyncio.create_task(
            self._cleanup_loop(),
            name="aquilia-task-cleanup",
        )

        # Start scheduler loop for periodic tasks
        self._scheduler_task = asyncio.create_task(
            self._scheduler_loop(),
            name="aquilia-task-scheduler",
        )

        logger.info(
            f"TaskManager started: {self.num_workers} workers, "
            f"backend={self.backend.__class__.__name__}"
        )

    async def stop(self, timeout: float = 10.0) -> None:
        """Gracefully stop all workers."""
        self._running = False

        # Cancel workers
        for w in self._workers:
            w.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()
        if self._scheduler_task:
            self._scheduler_task.cancel()

        # Wait for workers to finish
        await asyncio.gather(*self._workers, return_exceptions=True)
        if self._cleanup_task:
            await asyncio.gather(self._cleanup_task, return_exceptions=True)
        if self._scheduler_task:
            await asyncio.gather(self._scheduler_task, return_exceptions=True)

        self._workers.clear()
        self._cleanup_task = None
        self._scheduler_task = None
        logger.info("TaskManager stopped")

    @property
    def is_running(self) -> bool:
        return self._running

    # ========================================================================
    # Enqueue API
    # ========================================================================

    async def enqueue(
        self,
        func,
        *args,
        queue: Optional[str] = None,
        priority: Optional[Priority] = None,
        delay: Optional[float] = None,
        max_retries: Optional[int] = None,
        timeout: Optional[float] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> str:
        """
        Enqueue a task for background execution.

        Args:
            func: Async callable or @task-decorated function
            *args: Positional arguments
            queue: Queue name (overrides decorator default)
            priority: Priority level (overrides decorator default)
            delay: Delay execution by N seconds
            max_retries: Max retries (overrides decorator default)
            timeout: Execution timeout (overrides decorator default)
            tags: Metadata tags
            metadata: Extra metadata dict
            **kwargs: Keyword arguments

        Returns:
            Job ID string
        """
        # Extract defaults from @task decorator if available
        if isinstance(func, _TaskDescriptor):
            descriptor = func
            func_ref = descriptor.task_name
            _queue = queue or descriptor.queue
            _priority = priority if priority is not None else descriptor.priority
            _max_retries = max_retries if max_retries is not None else descriptor.max_retries
            _timeout = timeout if timeout is not None else descriptor.timeout
            _tags = tags or descriptor.tags
            actual_func = descriptor._fn
        elif callable(func):
            func_ref = f"{func.__module__}:{func.__qualname__}"
            _queue = queue or self.default_queue
            _priority = priority if priority is not None else Priority.NORMAL
            _max_retries = max_retries if max_retries is not None else 3
            _timeout = timeout if timeout is not None else 300.0
            _tags = tags or []
            actual_func = func
        else:
            raise TypeError(f"Expected callable or @task descriptor, got {type(func)}")

        self._queues.add(_queue)

        job = Job(
            name=getattr(func, "task_name", func_ref.split(":")[-1] if ":" in func_ref else func_ref),
            queue=_queue,
            priority=_priority,
            func_ref=func_ref,
            args=args,
            kwargs=kwargs,
            state=JobState.SCHEDULED if delay else JobState.PENDING,
            max_retries=_max_retries,
            retry_delay=getattr(func, "retry_delay", 1.0) if isinstance(func, _TaskDescriptor) else 1.0,
            retry_backoff=getattr(func, "retry_backoff", 2.0) if isinstance(func, _TaskDescriptor) else 2.0,
            retry_max_delay=getattr(func, "retry_max_delay", 300.0) if isinstance(func, _TaskDescriptor) else 300.0,
            timeout=_timeout,
            scheduled_at=datetime.now(timezone.utc) + timedelta(seconds=delay) if delay else None,
            metadata=metadata or {},
            tags=_tags,
            _func=actual_func,
        )

        await self.backend.push(job)
        self._total_enqueued += 1

        logger.debug(f"Enqueued job {job.id} ({job.name}) → queue={_queue}, priority={_priority.name}")
        return job.id

    # ========================================================================
    # Job Query API
    # ========================================================================

    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        return await self.backend.get(job_id)

    async def list_jobs(
        self,
        *,
        queue: Optional[str] = None,
        state: Optional[JobState] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Job]:
        """List jobs with optional filters."""
        return await self.backend.list_jobs(queue=queue, state=state, limit=limit, offset=offset)

    async def cancel(self, job_id: str) -> bool:
        """Cancel a pending/running job."""
        result = await self.backend.cancel(job_id)
        if result:
            logger.info(f"Cancelled job {job_id}")
        return result

    async def retry_job(self, job_id: str) -> bool:
        """Manually retry a failed/dead job."""
        result = await self.backend.retry(job_id)
        if result:
            logger.info(f"Retrying job {job_id}")
        return result

    async def flush(self, queue: Optional[str] = None) -> int:
        """Remove all jobs from a queue (or all queues)."""
        return await self.backend.flush(queue)

    # ========================================================================
    # Monitoring API
    # ========================================================================

    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive task manager statistics."""
        backend_stats = await self.backend.get_stats()
        return {
            **backend_stats,
            "manager": {
                "running": self._running,
                "num_workers": self.num_workers,
                "total_enqueued": self._total_enqueued,
                "total_completed": self._total_completed,
                "total_failed": self._total_failed,
                "uptime_seconds": (
                    (datetime.now(timezone.utc) - self._started_at).total_seconds()
                    if self._started_at else 0
                ),
                "queues": sorted(self._queues),
                "backend": self.backend.__class__.__name__,
            },
        }

    async def get_queue_stats(self) -> Dict[str, Dict[str, int]]:
        """Per-queue breakdown."""
        return await self.backend.get_queue_stats()

    # ========================================================================
    # Event Hooks
    # ========================================================================

    def on_complete(self, callback: Callable) -> None:
        """Register callback for job completion."""
        self._on_complete.append(callback)

    def on_failure(self, callback: Callable) -> None:
        """Register callback for job failure."""
        self._on_failure.append(callback)

    def on_dead_letter(self, callback: Callable) -> None:
        """Register callback for dead-letter jobs."""
        self._on_dead_letter.append(callback)

    # ========================================================================
    # Worker Loop
    # ========================================================================

    async def _worker_loop(self, worker_name: str) -> None:
        """Main worker loop — polls backend for jobs and executes them."""
        logger.debug(f"{worker_name} started")
        while self._running:
            try:
                job = None
                # Try each known queue
                for queue in list(self._queues):
                    job = await self.backend.pop(queue)
                    if job:
                        break

                if job is None:
                    await asyncio.sleep(0.1)  # Idle polling interval
                    continue

                await self._execute_job(job, worker_name)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"{worker_name} loop error: {e}", exc_info=True)
                await asyncio.sleep(1.0)

    async def _execute_job(self, job: Job, worker_name: str) -> None:
        """Execute a single job with timeout, retry, and result tracking."""
        job.state = JobState.RUNNING
        job.started_at = datetime.now(timezone.utc)
        await self.backend.update(job)

        logger.info(f"{worker_name} executing {job.id} ({job.name})")

        start_time = time.monotonic()
        try:
            # Resolve callable
            func = job._func
            if func is None:
                # Try to find from registry
                descriptor = get_task(job.func_ref)
                if descriptor:
                    func = descriptor._fn
                else:
                    raise RuntimeError(f"Cannot resolve task function: {job.func_ref}")

            # Execute with timeout
            result = await asyncio.wait_for(
                func(*job.args, **job.kwargs),
                timeout=job.timeout,
            )

            # Success
            elapsed = (time.monotonic() - start_time) * 1000
            job.state = JobState.COMPLETED
            job.completed_at = datetime.now(timezone.utc)
            job.result = JobResult(
                success=True,
                value=result,
                duration_ms=elapsed,
            )
            await self.backend.update(job)
            self._total_completed += 1

            logger.info(f"{worker_name} completed {job.id} in {elapsed:.1f}ms")

            # Notify listeners
            for cb in self._on_complete:
                try:
                    cb(job)
                except Exception:
                    pass

        except asyncio.TimeoutError:
            elapsed = (time.monotonic() - start_time) * 1000
            await self._handle_failure(
                job, worker_name,
                error=f"Task timed out after {job.timeout}s",
                error_type="TimeoutError",
                traceback_str="",
                elapsed=elapsed,
            )

        except Exception as e:
            elapsed = (time.monotonic() - start_time) * 1000
            await self._handle_failure(
                job, worker_name,
                error=str(e),
                error_type=type(e).__name__,
                traceback_str=tb_mod.format_exc(),
                elapsed=elapsed,
            )

    async def _handle_failure(
        self,
        job: Job,
        worker_name: str,
        *,
        error: str,
        error_type: str,
        traceback_str: str,
        elapsed: float,
    ) -> None:
        """Handle job failure with retry logic."""
        job.retry_count += 1

        if job.can_retry:
            # Schedule retry with backoff
            delay = job.next_retry_delay
            job.state = JobState.RETRYING
            job.scheduled_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
            job.result = JobResult(
                success=False,
                error=error,
                error_type=error_type,
                traceback=traceback_str,
                duration_ms=elapsed,
            )
            await self.backend.update(job)
            # Re-enqueue
            await self.backend.push(job)

            logger.warning(
                f"{worker_name} job {job.id} failed (attempt {job.retry_count}/{job.max_retries}), "
                f"retrying in {delay:.1f}s: {error}"
            )

            for cb in self._on_failure:
                try:
                    cb(job)
                except Exception:
                    pass
        else:
            # Exhausted retries → dead letter
            job.state = JobState.DEAD
            job.completed_at = datetime.now(timezone.utc)
            job.result = JobResult(
                success=False,
                error=error,
                error_type=error_type,
                traceback=traceback_str,
                duration_ms=elapsed,
            )
            await self.backend.update(job)
            self._total_failed += 1

            logger.error(
                f"{worker_name} job {job.id} permanently failed after {job.retry_count} retries: {error}"
            )

            for cb in self._on_dead_letter:
                try:
                    cb(job)
                except Exception:
                    pass

    async def _cleanup_loop(self) -> None:
        """Periodic cleanup of old terminal jobs."""
        while self._running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                removed = await self.backend.cleanup(self.cleanup_max_age)
                if removed:
                    logger.debug(f"Cleaned up {removed} old jobs")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")

    # ========================================================================
    # Scheduler Loop (Celery Beat / ARQ cron equivalent)
    # ========================================================================

    def _bind_task_descriptors(self) -> None:
        """
        Bind this TaskManager to all registered ``@task`` descriptors.

        This enables the ``.delay()`` / ``.send()`` convenience API
        on task descriptors so they can dispatch jobs without a direct
        reference to the TaskManager instance.

        Also logs periodic tasks that will be managed by the scheduler.
        """
        from .decorators import get_registered_tasks, get_periodic_tasks

        for name, descriptor in get_registered_tasks().items():
            descriptor.bind(self)

        periodic = get_periodic_tasks()
        if periodic:
            schedules = ", ".join(
                f"{n} ({d.schedule.human_readable})"
                for n, d in periodic.items()
            )
            logger.info(f"Scheduler bound {len(periodic)} periodic task(s): {schedules}")

    async def _scheduler_loop(self) -> None:
        """
        Periodic task scheduler — the Aquilia equivalent of Celery Beat.

        Runs on a fixed tick interval (default 15s).  On each tick it
        checks all ``@task(schedule=...)`` descriptors and enqueues
        those whose interval/cron has elapsed since their last run.

        This is the **industry-standard** approach: tasks with a
        ``schedule`` are automatically enqueued by the framework;
        tasks without one are on-demand only and dispatched via
        ``.delay()`` or ``manager.enqueue()``.
        """
        from .decorators import get_periodic_tasks

        # Wait a short beat before first tick so workers are ready
        await asyncio.sleep(1.0)

        while self._running:
            try:
                now = datetime.now(timezone.utc)
                periodic = get_periodic_tasks()

                for name, descriptor in periodic.items():
                    last_run = self._schedule_last_run.get(name)

                    if last_run is None:
                        # First tick after startup — enqueue immediately
                        should_enqueue = True
                    else:
                        next_due = descriptor.schedule.next_run(last_run)
                        should_enqueue = now >= next_due

                    if should_enqueue:
                        try:
                            await self.enqueue(descriptor)
                            self._schedule_last_run[name] = now
                            logger.debug(
                                "Scheduler enqueued periodic task: %s (%s)",
                                name, descriptor.schedule.human_readable,
                            )
                        except Exception as e:
                            logger.warning(
                                "Scheduler failed to enqueue %s: %s", name, e
                            )

                await asyncio.sleep(self.scheduler_tick)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}", exc_info=True)
                await asyncio.sleep(self.scheduler_tick)
