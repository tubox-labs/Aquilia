"""
AquilaTasks — Task Engine & Backends.

TaskManager is the central coordinator:
- Accepts jobs via enqueue()
- Dispatches to the configured backend
- Tracks job lifecycle
- Provides monitoring/stats APIs

Backends:
- :class:`MemoryBackend` — in-process priority queue, the only backend
  shipped with Aquilia.  Jobs do not survive a process restart.
- :class:`TaskBackend` — ABC for custom persistent or distributed
  backends (Redis, PostgreSQL, …).  None ship in-tree; a backend that
  persists jobs must also choose a safe serialization format, since
  ``Job.args``/``Job.kwargs`` hold live Python objects today.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import time
import traceback as tb_mod
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from heapq import heappop, heappush
from typing import Any

from aquilia.tasks.decorators import _TaskDescriptor, get_task
from aquilia.tasks.faults import TaskDuplicateFault, TaskEnqueueFault, TaskResolutionFault
from aquilia.tasks.job import Job, JobResult, JobState, Priority

logger = logging.getLogger("aquilia.tasks")

#: Sentinel a workflow stores in kwargs, swapped for real dependency results
#: at execution time.  Kept in sync with :mod:`aquilia.tasks.workflow`.
_PARENT_RESULTS_MARKER = "__aquilia_parent_results__"


# ============================================================================
# Backend ABC
# ============================================================================


class TaskBackend(ABC):
    """
    Storage and retrieval contract for background jobs.

    A backend owns the queue: it decides which job a worker gets next, holds
    job state, and — for distributed backends — coordinates ownership so two
    workers never run the same job concurrently.

    Implementing a backend:
        The abstract methods below are the minimum.  The *capability* methods
        that follow (leases, deduplication, dependency gating) ship with
        working single-process defaults, so a backend written against an
        earlier version of Aquilia keeps functioning unchanged — it simply
        reports the newer capabilities as unavailable.

    Capability flags:
        :attr:`is_distributed` and :attr:`is_persistent` let the manager and
        the admin dashboard describe honestly what guarantees are in force,
        rather than implying durability the store cannot provide.

    Delivery semantics:
        Distributed backends provide **at-least-once** delivery.  A worker
        claims a job under a time-bounded lease and renews it by heartbeat;
        if the worker dies the lease lapses and another worker reclaims the
        job.  A job may therefore run twice if a worker stalls past its lease
        and then recovers, so task functions should be idempotent.  Use
        ``dedup`` on :meth:`TaskManager.enqueue` to suppress duplicate
        *enqueues*; that is a distinct guarantee from duplicate *execution*.

    See Also:
        :class:`MemoryBackend`, :class:`~aquilia.tasks.backends.RedisBackend`,
        :class:`~aquilia.tasks.backends.SQLBackend`.
    """

    #: Whether jobs are visible to workers in other processes or machines.
    is_distributed: bool = False

    #: Whether jobs survive a process restart.
    is_persistent: bool = False

    @abstractmethod
    async def push(self, job: Job) -> None:
        """Add job to the queue."""

    @abstractmethod
    async def pop(self, queue: str = "default") -> Job | None:
        """Retrieve highest-priority runnable job from queue."""

    @abstractmethod
    async def get(self, job_id: str) -> Job | None:
        """Get job by ID."""

    @abstractmethod
    async def update(self, job: Job) -> None:
        """Persist job state changes."""

    @abstractmethod
    async def list_jobs(
        self,
        *,
        queue: str | None = None,
        state: JobState | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Job]:
        """List jobs with optional filters."""

    @abstractmethod
    async def get_stats(self) -> dict[str, Any]:
        """Aggregate statistics across all queues."""

    @abstractmethod
    async def get_queue_stats(self) -> dict[str, dict[str, int]]:
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
    async def flush(self, queue: str | None = None) -> int:
        """Remove all jobs (optionally in a specific queue). Returns count removed."""

    # ── Lifecycle (optional) ────────────────────────────────────────

    async def initialize(self) -> None:
        """
        Prepare the backend for use — connect, create schema, warm pools.

        Called once by :meth:`TaskManager.start`.  The default is a no-op so
        in-memory backends need not implement it.
        """
        return None

    async def shutdown(self) -> None:
        """
        Release backend resources.  Called by :meth:`TaskManager.stop`.

        The default is a no-op.  Implementations must tolerate being called
        without a preceding :meth:`initialize`.
        """
        return None

    # ── Leases (optional; required for safe distribution) ───────────

    async def heartbeat(self, job: Job, lease_seconds: float) -> bool:
        """
        Extend the lease on a job this worker is executing.

        Long-running jobs must renew their lease or another worker will
        assume the holder died and reclaim the job — producing exactly the
        duplicate execution leases exist to prevent.

        Args:
            job: The job currently being executed.
            lease_seconds: New lease duration measured from now.

        Returns:
            ``True`` if the lease was extended.  ``False`` means this worker
            no longer owns the job (its lease already lapsed and another
            worker took over), and the caller should abandon the work.

        Notes:
            The default implementation returns ``True`` unconditionally:
            without cross-process visibility there is no competing owner, so
            the lease is trivially still held.
        """
        return True

    async def reclaim_expired(self, *, limit: int = 100) -> int:
        """
        Return jobs whose lease lapsed to the runnable pool.

        This is what makes a crashed worker recoverable rather than a source
        of silently lost jobs.

        Args:
            limit: Maximum number of jobs to reclaim in one pass.

        Returns:
            Number of jobs re-queued.  The default returns ``0`` — an
            in-process backend loses its jobs on crash regardless, so there
            is nothing to reclaim.
        """
        return 0

    # ── Idempotency (optional) ──────────────────────────────────────

    async def reserve_fingerprint(self, fingerprint: str, job_id: str, ttl: float) -> str | None:
        """
        Claim a content fingerprint so duplicate work is not enqueued twice.

        Args:
            fingerprint: Content digest from :attr:`Job.fingerprint`.
            job_id: Job attempting the reservation.
            ttl: Seconds the reservation is held, bounding how long a crashed
                producer can block later enqueues of the same work.

        Returns:
            ``None`` when the reservation succeeded, otherwise the ID of the
            job already holding it.

        Notes:
            The default returns ``None`` (always succeeds), so backends that
            cannot offer atomic reservation never *silently* suppress work —
            they fall back to the historical allow-everything behaviour.
        """
        return None

    async def release_fingerprint(self, fingerprint: str, job_id: str) -> None:
        """
        Release a fingerprint reservation once the job reaches a terminal state.

        Args:
            fingerprint: The reserved digest.
            job_id: Job that holds the reservation.  Implementations must
                verify ownership so a late release cannot free a reservation
                a *different* job has since taken.
        """
        return None

    # ── Workflows (optional) ────────────────────────────────────────

    async def are_dependencies_satisfied(self, job: Job) -> bool:
        """
        Whether every job in ``job.depends_on`` has completed successfully.

        Args:
            job: Job awaiting its dependencies.

        Returns:
            ``True`` when the job may proceed.  A job with no dependencies is
            always satisfied.

        Notes:
            A dependency that reached a terminal *failure* state never becomes
            satisfied, so dependents stay ``WAITING`` and are surfaced by
            :meth:`fail_orphaned_dependents` rather than running on incomplete
            input.
        """
        if not job.depends_on:
            return True
        for dep_id in job.depends_on:
            dep = await self.get(dep_id)
            if dep is None or dep.state is not JobState.COMPLETED:
                return False
        return True

    async def get_dependency_results(self, job: Job) -> list[Any]:
        """
        Collect the results of a job's dependencies, in declaration order.

        Enables the fan-in half of a workflow: a chord's callback receives
        what the parallel group produced.

        Args:
            job: Job whose dependency results are needed.

        Returns:
            One entry per dependency; ``None`` where a result is unavailable.
        """
        results: list[Any] = []
        for dep_id in job.depends_on:
            dep = await self.get(dep_id)
            results.append(dep.result.value if dep and dep.result else None)
        return results


# ============================================================================
# In-Memory Backend
# ============================================================================


class MemoryBackend(TaskBackend):
    """
    In-process priority queue backend.

    Uses a heap per queue for O(log n) push/pop.
    Stores all jobs in a dict for O(1) lookup.
    Concurrency-safe via an ``asyncio.Lock`` (single-event-loop only —
    this backend is not safe to share across threads or processes).

    Suitable for single-process deployments, development, and testing.
    Jobs live only in memory: a restart loses every queued job.  For
    durability or multi-process execution use
    :class:`~aquilia.tasks.backends.RedisBackend` or
    :class:`~aquilia.tasks.backends.SQLBackend`, which expose the same
    interface.

    Workflow support:
        Dependency gating is honoured — a job whose ``depends_on`` set is
        unsatisfied is skipped by :meth:`pop` and left queued, so chains and
        DAGs work identically here and in the distributed backends.

    Idempotency:
        Fingerprint reservation is process-local.  It correctly suppresses
        duplicate enqueues within this process, which is the only scope that
        exists for an in-memory queue.

    Args:
        dead_letter_max: Maximum number of dead-lettered jobs retained for
            inspection.  Oldest entries are evicted first.

    Examples::

        backend = MemoryBackend(dead_letter_max=5000)
        manager = TaskManager(backend=backend)
    """

    is_distributed = False
    is_persistent = False

    def __init__(self, *, dead_letter_max: int = 1000) -> None:
        self._jobs: dict[str, Job] = {}
        self._queues: dict[str, list] = defaultdict(list)  # heap per queue
        self._counter = 0  # Tie-breaker for heap stability
        self._lock = asyncio.Lock()
        self.dead_letter_max = dead_letter_max
        self._dead_letter: deque[Job] = deque(maxlen=dead_letter_max)
        self._fingerprints: dict[str, str] = {}  # fingerprint → job_id

    async def push(self, job: Job) -> None:
        async with self._lock:
            self._jobs[job.id] = job
            self._counter += 1
            heappush(
                self._queues[job.queue],
                (job.priority.value, self._counter, job.id),
            )

    async def pop(self, queue: str = "default") -> Job | None:
        """
        Return the highest-priority job in ``queue`` that is ready to run.

        Jobs are skipped over, not blocked on, when they are not yet due
        (``scheduled_at`` in the future) or still waiting on workflow
        dependencies.  Skipped entries are pushed back after the scan, so a
        delayed or blocked high-priority job never starves ready lower-priority
        work behind it.

        Complexity: O(k log n) where ``k`` is the number of entries scanned.
        """
        deferred: list[tuple] = []
        found: Job | None = None

        async with self._lock:
            heap = self._queues.get(queue, [])
            now = datetime.now(timezone.utc)
            blocked: list[tuple] = []
            while heap:
                entry = heappop(heap)
                _priority_val, _counter, job_id = entry
                job = self._jobs.get(job_id)
                if job is None or job.is_terminal:
                    continue
                if job.scheduled_at and now < job.scheduled_at:
                    deferred.append(entry)
                    continue
                if job.state in (JobState.PENDING, JobState.RETRYING, JobState.SCHEDULED, JobState.WAITING):
                    if job.depends_on:
                        blocked.append((entry, job))
                        continue
                    found = job
                    break
            for entry in deferred:
                heappush(heap, entry)

        # Dependency checks re-enter get(); done outside the lock to keep the
        # critical section free of nested acquisition.
        if found is None:
            for entry, job in blocked:
                if found is None and await self.are_dependencies_satisfied(job):
                    found = job
                    continue
                async with self._lock:
                    heappush(self._queues[job.queue], entry)
        else:
            async with self._lock:
                for entry, job in blocked:
                    heappush(self._queues[job.queue], entry)

        return found

    async def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    async def update(self, job: Job) -> None:
        """
        Persist job state.

        A job that has reached a terminal state releases its fingerprint
        reservation, so identical work can be scheduled again later.
        """
        async with self._lock:
            self._jobs[job.id] = job
            if job.state == JobState.DEAD:
                self._dead_letter.append(job)
        if job.is_terminal and job.dedup_key:
            await self.release_fingerprint(job.dedup_key, job.id)

    async def list_jobs(
        self,
        *,
        queue: str | None = None,
        state: JobState | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Job]:
        jobs = list(self._jobs.values())
        if queue:
            jobs = [j for j in jobs if j.queue == queue]
        if state:
            jobs = [j for j in jobs if j.state == state]
        # Sort by created_at descending (newest first)
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs[offset : offset + limit]

    async def get_stats(self) -> dict[str, Any]:
        all_jobs = list(self._jobs.values())
        by_state: dict[str, int] = defaultdict(int)
        for j in all_jobs:
            by_state[j.state.value] += 1

        completed = [j for j in all_jobs if j.state == JobState.COMPLETED and j.duration_ms is not None]
        failed = [j for j in all_jobs if j.state in (JobState.FAILED, JobState.DEAD)]
        avg_duration = sum(j.duration_ms for j in completed) / len(completed) if completed else 0.0

        # ── Duration distribution (histogram buckets in ms) ─────────
        duration_buckets = [0, 10, 50, 100, 250, 500, 1000, 5000, float("inf")]
        duration_histogram = [0] * (len(duration_buckets) - 1)
        duration_labels = ["<10ms", "10-50ms", "50-100ms", "100-250ms", "250-500ms", "0.5-1s", "1-5s", ">5s"]
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
                1 for j in completed if j.completed_at and j.completed_at.strftime("%Y-%m-%d %H:00") == hour_str
            )
            f_count = sum(1 for j in failed if j.completed_at and j.completed_at.strftime("%Y-%m-%d %H:00") == hour_str)
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

    async def get_queue_stats(self) -> dict[str, dict[str, int]]:
        result: dict[str, dict[str, int]] = {}
        for job in self._jobs.values():
            if job.queue not in result:
                result[job.queue] = defaultdict(int)
            result[job.queue][job.state.value] += 1
        return {q: dict(counts) for q, counts in result.items()}

    async def cleanup(self, max_age_seconds: float = 3600) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=max_age_seconds)
        to_remove = [
            jid for jid, j in self._jobs.items() if j.is_terminal and j.completed_at and j.completed_at < cutoff
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

    async def flush(self, queue: str | None = None) -> int:
        if queue:
            to_remove = [jid for jid, j in self._jobs.items() if j.queue == queue]
            for jid in to_remove:
                del self._jobs[jid]
            self._queues.pop(queue, None)
            self._fingerprints = {fp: jid for fp, jid in self._fingerprints.items() if jid not in set(to_remove)}
            return len(to_remove)
        count = len(self._jobs)
        self._jobs.clear()
        self._queues.clear()
        self._fingerprints.clear()
        return count

    # ── Idempotency ─────────────────────────────────────────────────

    async def reserve_fingerprint(self, fingerprint: str, job_id: str, ttl: float) -> str | None:
        """
        Claim a fingerprint within this process.

        A reservation held by a job that has since reached a terminal state is
        treated as stale and taken over, so a completed job never blocks the
        same work from being scheduled again.

        Args:
            fingerprint: Content digest to claim.
            job_id: Job making the claim.
            ttl: Accepted for interface parity; in-process reservations are
                released deterministically on completion rather than expiring.

        Returns:
            ``None`` when the claim succeeded, otherwise the ID of the live
            job already holding it.
        """
        async with self._lock:
            holder_id = self._fingerprints.get(fingerprint)
            if holder_id and holder_id != job_id:
                holder = self._jobs.get(holder_id)
                if holder is not None and not holder.is_terminal:
                    return holder_id
            self._fingerprints[fingerprint] = job_id
            return None

    async def release_fingerprint(self, fingerprint: str, job_id: str) -> None:
        """Release a reservation, but only if ``job_id`` still owns it."""
        async with self._lock:
            if self._fingerprints.get(fingerprint) == job_id:
                del self._fingerprints[fingerprint]


# ============================================================================
# Task Manager
# ============================================================================


class TaskManager:
    """
    Central task coordinator.

    Manages job lifecycle:
    1. Accept task via :meth:`enqueue`
    2. Store in the backend
    3. Workers pull from the backend via ``pop()``
    4. Execute and update state
    5. Handle retries on failure, dead-letter on exhaustion
    6. Provide monitoring APIs

    Lifecycle:
        :meth:`start` spawns ``num_workers`` worker tasks plus a cleanup loop
        and a periodic scheduler; :meth:`stop` cancels them under a bounded
        wait.  Both are idempotent, and a stopped manager can restart.

    Async-safety:
        All state lives on one event loop.  Concurrent workers are serialised
        by the backend's own lock, so a job is never handed out twice.

    Args:
        backend: Job store; defaults to a fresh :class:`MemoryBackend`.
        num_workers: Worker loops to spawn on :meth:`start`.  Zero is valid
            and useful for tests that drive :meth:`drain_once` by hand.
        default_queue: Queue used when a job names none.
        cleanup_interval: Seconds between terminal-job cleanup passes.
        cleanup_max_age: Age after which a terminal job is discarded.
        scheduler_tick: Seconds between periodic-schedule evaluations.
        default_timeout: Per-job execution timeout for callables that carry
            no ``@task`` timeout of their own.
        default_max_retries: Retry budget for plain callables.
        default_retry_delay: First retry delay, in seconds.
        default_retry_backoff: Multiplier applied per retry attempt.
        default_retry_max_delay: Ceiling on the computed retry delay.
        lease_seconds: How long a claimed job stays owned before another
            worker may reclaim it.  Only meaningful on distributed backends.
        heartbeat_interval: How often a running job renews its lease.  Must be
            well under ``lease_seconds`` or long jobs will be reclaimed while
            still running.
        reclaim_interval: How often to sweep for jobs abandoned by dead
            workers.  No-op on in-memory backends, which have nothing to
            reclaim after a crash.
        dedup_ttl: How long a fingerprint reservation is held, bounding how
            long a crashed producer can block identical work.

    Attributes:
        backend: The active :class:`TaskBackend`.
        is_running: Whether background loops are live.

    Examples::

        manager = TaskManager()
        await manager.start()

        job_id = await manager.enqueue(my_task, arg1, kwarg1="val")
        status = await manager.get_job(job_id)

        await manager.stop()

        # Deterministic, worker-free execution (tests)
        manager = TaskManager(num_workers=0)
        await manager.enqueue(my_task)
        job = await manager.drain_once("test")
    """

    def __init__(
        self,
        *,
        backend: TaskBackend | None = None,
        num_workers: int = 4,
        default_queue: str = "default",
        cleanup_interval: float = 300.0,  # 5 minutes
        cleanup_max_age: float = 3600.0,  # 1 hour
        scheduler_tick: float = 15.0,  # Scheduler poll interval in seconds
        default_timeout: float = 300.0,
        default_max_retries: int = 3,
        default_retry_delay: float = 1.0,
        default_retry_backoff: float = 2.0,
        default_retry_max_delay: float = 300.0,
        lease_seconds: float = 300.0,
        heartbeat_interval: float = 30.0,
        reclaim_interval: float = 60.0,
        dedup_ttl: float = 3600.0,
    ):
        self.backend = backend or MemoryBackend()
        self.num_workers = num_workers
        self.default_queue = default_queue
        self.cleanup_interval = cleanup_interval
        self.cleanup_max_age = cleanup_max_age
        self.scheduler_tick = scheduler_tick
        self.default_timeout = default_timeout
        self.default_max_retries = default_max_retries
        self.default_retry_delay = default_retry_delay
        self.default_retry_backoff = default_retry_backoff
        self.default_retry_max_delay = default_retry_max_delay
        self.lease_seconds = lease_seconds
        self.heartbeat_interval = heartbeat_interval
        self.reclaim_interval = reclaim_interval
        self.dedup_ttl = dedup_ttl

        self._workers: list[asyncio.Task] = []
        self._cleanup_task: asyncio.Task | None = None
        self._scheduler_task: asyncio.Task | None = None
        self._reclaim_task: asyncio.Task | None = None
        self._running = False
        self._queues: set[str] = {default_queue}

        # Periodic schedule tracking: task_name → last_enqueued_at
        self._schedule_last_run: dict[str, datetime] = {}

        # Event listeners
        self._on_complete: list[Callable] = []
        self._on_failure: list[Callable] = []
        self._on_dead_letter: list[Callable] = []

        # Metrics
        self._total_enqueued = 0
        self._total_completed = 0
        self._total_failed = 0
        self._started_at: datetime | None = None

    # ========================================================================
    # Lifecycle
    # ========================================================================

    async def start(self) -> None:
        """
        Start the backend, worker loops, cleanup, scheduler, and lease reclaim.

        The backend is initialised first so a misconfigured Redis or database
        fails at startup rather than on the first enqueue.

        Raises:
            TaskBackendFault: If the backend cannot be initialised.
        """
        if self._running:
            return
        await self.backend.initialize()
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

        # Reclaim jobs abandoned by crashed workers. Only distributed backends
        # can lose jobs this way; in-memory ones lose everything on crash and
        # have nothing to recover.
        if self.backend.is_distributed:
            # A shared queue may already hold work in queues this process has
            # never named, so adopt them before the first poll.
            with contextlib.suppress(Exception):
                self._queues.update(await self.backend.get_queue_stats())
            self._reclaim_task = asyncio.create_task(
                self._reclaim_loop(),
                name="aquilia-task-reclaim",
            )

    async def stop(self, timeout: float = 10.0) -> None:
        """
        Gracefully stop workers, cleanup loop, and scheduler.

        Every background task is cancelled, then awaited under a single
        bounded ``asyncio.wait_for``.  If a job function swallows
        ``CancelledError`` (e.g. it is blocked in CPU-bound work), the wait
        expires and shutdown proceeds anyway rather than hanging forever;
        the stuck task is left detached and a warning is logged.

        Args:
            timeout: Maximum seconds to wait for tasks to unwind.  Values
                ≤ 0 skip waiting entirely.

        Side effects:
            Clears the worker list and drops references to the cleanup and
            scheduler tasks, so :meth:`start` can be called again.
        """
        self._running = False

        pending = [*self._workers]
        if self._cleanup_task:
            pending.append(self._cleanup_task)
        if self._scheduler_task:
            pending.append(self._scheduler_task)
        if self._reclaim_task:
            pending.append(self._reclaim_task)

        for t in pending:
            t.cancel()

        if pending and timeout > 0:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*pending, return_exceptions=True),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                stuck = [t.get_name() for t in pending if not t.done()]
                logger.warning(
                    "TaskManager.stop timed out after %.1fs; %d task(s) still running: %s",
                    timeout,
                    len(stuck),
                    ", ".join(stuck),
                )

        self._workers.clear()
        self._cleanup_task = None
        self._scheduler_task = None
        self._reclaim_task = None
        await self.backend.shutdown()

    @property
    def is_running(self) -> bool:
        """Whether background loops are live."""
        return self._running

    @property
    def is_distributed(self) -> bool:
        """Whether the configured backend spans processes/machines."""
        return self.backend.is_distributed

    @property
    def is_persistent(self) -> bool:
        """Whether queued jobs survive a process restart."""
        return self.backend.is_persistent

    # ========================================================================
    # Enqueue API
    # ========================================================================

    async def enqueue(
        self,
        func,
        *args,
        queue: str | None = None,
        priority: Priority | None = None,
        delay: float | None = None,
        max_retries: int | None = None,
        timeout: float | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        job_id: str | None = None,
        depends_on: list[str] | None = None,
        workflow_id: str | None = None,
        initial_state: JobState | None = None,
        dedup: str = "allow",
        **kwargs,
    ) -> str:
        """
        Enqueue a task for background execution.

        Precedence for every tunable is: explicit argument, then the
        ``@task`` decorator's value, then this manager's configured default.
        That ordering is what makes ``Integration.tasks(default_timeout=...)``
        actually reach a plain callable enqueued without a decorator.

        Args:
            func: Async callable or ``@task``-decorated descriptor.
            *args: Positional arguments passed to the callable.
            queue: Queue name override.
            priority: Priority override.
            delay: Delay execution by N seconds (job starts ``SCHEDULED``).
            max_retries: Retry-budget override.
            timeout: Execution-timeout override, in seconds.
            tags: Metadata tags.
            metadata: Extra metadata dict stored on the job.
            job_id: Pre-assigned ID.  Workflows use this to wire dependencies
                before any job exists.
            depends_on: Job IDs that must complete before this job may run.
            workflow_id: Groups jobs belonging to one workflow.
            initial_state: Override the starting state; workflows pass
                ``JobState.WAITING`` for dependent steps.
            dedup: Duplicate-enqueue policy, matched on
                :attr:`Job.fingerprint`:

                - ``"allow"`` (default) — always enqueue.  Preserves the
                  historical behaviour, so existing code is unaffected.
                - ``"skip"`` — if identical work is already in flight, return
                  that job's ID instead of enqueueing a second copy.
                - ``"raise"`` — raise :class:`TaskDuplicateFault` instead.

            **kwargs: Keyword arguments passed to the callable.

        Returns:
            The new job's ID — or, under ``dedup="skip"``, the ID of the
            already-queued job doing the same work.

        Raises:
            TaskEnqueueFault: If ``func`` is neither callable nor a task
                descriptor.
            TaskDuplicateFault: Under ``dedup="raise"`` when identical work is
                already in flight.
            TaskSerializationFault: On a persistent backend, if the arguments
                cannot be represented as JSON.

        Side effects:
            Registers the queue name so workers begin polling it, and emits
            an inspector span on the ``TASKS`` lane when a trace is active.

        Notes:
            Deduplication suppresses duplicate *enqueues*.  It is not a
            guarantee against duplicate *execution*: distributed backends are
            at-least-once, so a job whose worker stalls past its lease may run
            twice.  Task functions should still be idempotent.

        Examples::

            job_id = await manager.enqueue(send_email, to="a@b.co")
            job_id = await manager.enqueue(cleanup, delay=60, priority=Priority.LOW)

            # Collapse a burst of identical requests into one job
            await manager.enqueue(rebuild_index, dedup="skip")
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
            _max_retries = max_retries if max_retries is not None else self.default_max_retries
            _timeout = timeout if timeout is not None else self.default_timeout
            _tags = tags or []
            actual_func = func
        else:
            raise TaskEnqueueFault(str(type(func)))

        self._queues.add(_queue)

        t0 = None
        trace = None
        try:
            import time

            from aquilia.inspector.trace import current_trace

            trace = current_trace()
            if trace is not None:
                t0 = time.monotonic()
        except ImportError:
            pass

        is_descriptor = isinstance(func, _TaskDescriptor)

        if depends_on:
            state = initial_state or JobState.WAITING
        elif delay:
            state = initial_state or JobState.SCHEDULED
        else:
            state = initial_state or JobState.PENDING

        job = Job(
            name=getattr(func, "task_name", func_ref.split(":")[-1] if ":" in func_ref else func_ref),
            queue=_queue,
            priority=_priority,
            func_ref=func_ref,
            args=args,
            kwargs=kwargs,
            state=state,
            max_retries=_max_retries,
            retry_delay=(
                getattr(func, "retry_delay", self.default_retry_delay) if is_descriptor else self.default_retry_delay
            ),
            retry_backoff=(
                getattr(func, "retry_backoff", self.default_retry_backoff)
                if is_descriptor
                else self.default_retry_backoff
            ),
            retry_max_delay=(
                getattr(func, "retry_max_delay", self.default_retry_max_delay)
                if is_descriptor
                else self.default_retry_max_delay
            ),
            timeout=_timeout,
            scheduled_at=datetime.now(timezone.utc) + timedelta(seconds=delay) if delay else None,
            depends_on=list(depends_on or []),
            workflow_id=workflow_id,
            metadata=metadata or {},
            tags=_tags,
            _func=actual_func,
        )
        if job_id:
            job.id = job_id

        if dedup != "allow":
            fingerprint = job.fingerprint
            holder = await self.backend.reserve_fingerprint(fingerprint, job.id, self.dedup_ttl)
            if holder is not None and holder != job.id:
                if dedup == "raise":
                    raise TaskDuplicateFault(fingerprint, holder)
                logger.debug(
                    "Skipping duplicate enqueue of %s; job %s already in flight",
                    job.name,
                    holder,
                )
                return holder
            job.dedup_key = fingerprint

        await self.backend.push(job)
        self._total_enqueued += 1

        if trace is not None and t0 is not None:
            try:
                import time

                from aquilia.inspector.trace import Lane, SpanStatus

                now_offset = (time.monotonic() - trace.started_monotonic) * 1000.0
                duration_ms = (time.monotonic() - t0) * 1000.0

                trace.add_span(
                    lane=Lane.TASKS,
                    label=f"Enqueue Task: {job.name}",
                    start_offset_ms=max(0.0, now_offset - duration_ms),
                    duration_ms=duration_ms,
                    status=SpanStatus.OK,
                    detail={
                        "job_id": job.id,
                        "task_name": job.name,
                        "queue": job.queue,
                        "priority": str(job.priority.value) if hasattr(job.priority, "value") else str(job.priority),
                        "args": list(job.args),
                        "kwargs": job.kwargs,
                    },
                )
            except Exception:
                pass

        return job.id

    # ========================================================================
    # Job Query API
    # ========================================================================

    async def get_job(self, job_id: str) -> Job | None:
        """Get job by ID."""
        return await self.backend.get(job_id)

    async def list_jobs(
        self,
        *,
        queue: str | None = None,
        state: JobState | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Job]:
        """List jobs with optional filters."""
        return await self.backend.list_jobs(queue=queue, state=state, limit=limit, offset=offset)

    async def cancel(self, job_id: str) -> bool:
        """Cancel a pending/running job."""
        result = await self.backend.cancel(job_id)
        return result

    async def retry_job(self, job_id: str) -> bool:
        """Manually retry a failed/dead job."""
        result = await self.backend.retry(job_id)
        return result

    async def flush(self, queue: str | None = None) -> int:
        """Remove all jobs from a queue (or all queues)."""
        return await self.backend.flush(queue)

    # ========================================================================
    # Monitoring API
    # ========================================================================

    async def get_stats(self) -> dict[str, Any]:
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
                    (datetime.now(timezone.utc) - self._started_at).total_seconds() if self._started_at else 0
                ),
                "queues": sorted(self._queues),
                "backend": self.backend.__class__.__name__,
            },
        }

    async def get_queue_stats(self) -> dict[str, dict[str, int]]:
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

    async def drain_once(self, worker_name: str = "worker") -> Job | None:
        """
        Pop and execute at most one ready job across all known queues.

        This is the single unit of work shared by :meth:`_worker_loop` and
        :class:`aquilia.tasks.worker.Worker`, so polling, queue iteration,
        and execution semantics live in exactly one place.  It is also the
        supported hook for driving a manager deterministically from tests
        without starting background workers.

        Args:
            worker_name: Label recorded in log lines for this execution.

        Returns:
            The executed :class:`Job` (already in its post-run state:
            ``COMPLETED``, ``RETRYING``, or ``DEAD``), or ``None`` when no
            queue had a runnable job.

        Notes:
            Job failures are handled internally by :meth:`_handle_failure`
            and do **not** propagate — inspect the returned job's ``state``
            to detect them.

        Examples::

            manager = TaskManager()
            await manager.enqueue(my_task)
            job = await manager.drain_once("test")
            assert job.state is JobState.COMPLETED
        """
        for queue in list(self._queues):
            job = await self.backend.pop(queue)
            if job:
                await self._execute_job(job, worker_name)
                return job
        return None

    async def _worker_loop(self, worker_name: str) -> None:
        """Main worker loop — polls the backend for jobs and executes them."""
        while self._running:
            try:
                job = await self.drain_once(worker_name)
                if job is None:
                    await asyncio.sleep(0.1)  # Idle polling interval

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"{worker_name} loop error: {e}", exc_info=True)
                await asyncio.sleep(1.0)

    async def _execute_job(self, job: Job, worker_name: str) -> None:
        """
        Execute one job with timeout, lease renewal, retry, and result tracking.

        A heartbeat task runs alongside the job on distributed backends,
        renewing the lease so a long-running job is not reclaimed and executed
        a second time elsewhere.

        Workflow steps declared with ``with_parent_results()`` have their
        dependencies' return values substituted into ``parent_results`` here,
        at execution time — the values are read from the backend rather than
        captured at enqueue time, so they are correct even after a restart.
        """
        job.state = JobState.RUNNING
        job.started_at = datetime.now(timezone.utc)
        await self.backend.update(job)

        heartbeat: asyncio.Task | None = None
        if self.backend.is_distributed:
            heartbeat = asyncio.create_task(self._heartbeat_loop(job), name=f"aquilia-heartbeat-{job.id}")

        start_time = time.monotonic()
        try:
            # Resolve callable
            func = job._func
            if func is None:
                # Try to find from registry (allowlist check)
                descriptor = get_task(job.func_ref)
                if descriptor:
                    func = descriptor._fn
                else:
                    raise TaskResolutionFault(job.func_ref)

            call_kwargs = dict(job.kwargs)
            if call_kwargs.get("parent_results") == _PARENT_RESULTS_MARKER:
                call_kwargs["parent_results"] = await self.backend.get_dependency_results(job)

            # Execute with timeout
            result = await asyncio.wait_for(
                func(*job.args, **call_kwargs),
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

            # Notify listeners
            for cb in self._on_complete:
                with contextlib.suppress(Exception):
                    cb(job)

        except asyncio.TimeoutError:
            elapsed = (time.monotonic() - start_time) * 1000
            await self._handle_failure(
                job,
                worker_name,
                error=f"Task timed out after {job.timeout}s",
                error_type="TimeoutError",
                traceback_str="",
                elapsed=elapsed,
            )

        except Exception as e:
            elapsed = (time.monotonic() - start_time) * 1000
            await self._handle_failure(
                job,
                worker_name,
                error=str(e),
                error_type=type(e).__name__,
                traceback_str=tb_mod.format_exc(),
                elapsed=elapsed,
            )

        finally:
            if heartbeat is not None:
                heartbeat.cancel()
                with contextlib.suppress(asyncio.CancelledError, Exception):
                    await heartbeat

    async def _heartbeat_loop(self, job: Job) -> None:
        """
        Renew a running job's lease until the job finishes.

        Stops early if the backend reports ownership was lost — at that point
        another worker has already reclaimed the job, and continuing to renew
        would only mask the duplicate execution.
        """
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                if not await self.backend.heartbeat(job, self.lease_seconds):
                    logger.warning(
                        "Lost lease on job %s while executing; another worker has reclaimed it",
                        job.id,
                    )
                    return
            except asyncio.CancelledError:
                return
            except Exception as e:  # pragma: no cover - heartbeat is best-effort
                logger.warning("Heartbeat error for job %s: %s", job.id, e)
                return

    async def _reclaim_loop(self) -> None:
        """
        Periodically return jobs abandoned by crashed workers to the queue.

        Also refreshes the polled queue set from the backend: on a shared
        queue another process can create a queue this one never named, and a
        worker only polls queues it knows about.
        """
        while self._running:
            try:
                await asyncio.sleep(self.reclaim_interval)
                reclaimed = await self.backend.reclaim_expired()
                if reclaimed:
                    logger.info("Reclaimed %d job(s) from expired leases", reclaimed)
                self._queues.update(await self.backend.get_queue_stats())
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Reclaim loop error: %s", e)

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
                with contextlib.suppress(Exception):
                    cb(job)
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

            logger.error(f"{worker_name} job {job.id} permanently failed after {job.retry_count} retries: {error}")

            for cb in self._on_dead_letter:
                with contextlib.suppress(Exception):
                    cb(job)

    async def _cleanup_loop(self) -> None:
        """Periodic cleanup of old terminal jobs."""
        while self._running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self.backend.cleanup(self.cleanup_max_age)
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

        Each descriptor's queue is also registered for polling.  A
        consumer-only process never calls :meth:`enqueue`, so without this
        it would poll only ``default_queue`` and silently ignore work another
        process queued elsewhere.

        Also logs periodic tasks that will be managed by the scheduler.
        """
        from aquilia.tasks.decorators import get_periodic_tasks, get_registered_tasks

        for _name, descriptor in get_registered_tasks().items():
            descriptor.bind(self)
            self._queues.add(descriptor.queue)

        get_periodic_tasks()

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
        from aquilia.tasks.decorators import get_periodic_tasks

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
                        except Exception as e:
                            logger.warning("Scheduler failed to enqueue %s: %s", name, e)

                await asyncio.sleep(self.scheduler_tick)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}", exc_info=True)
                await asyncio.sleep(self.scheduler_tick)
