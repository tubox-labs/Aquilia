"""
Redis task backend — distributed, persistent job execution.

Enables Aquilia's background tasks to run across many worker processes and
many machines, with job state surviving restarts.

Data model::

    {prefix}queues                 SET   every known queue name
    {prefix}ready:{queue}          ZSET  runnable jobs, score = priority rank
    {prefix}delayed:{queue}        ZSET  future jobs, score = due timestamp
    {prefix}running                ZSET  claimed jobs, score = lease deadline
    {prefix}job:{job_id}           STR   JSON job payload
    {prefix}fp:{fingerprint}       STR   idempotency reservation (SET NX + TTL)
    {prefix}dead                   LIST  dead-letter ring, trimmed to a cap
    {prefix}index                  SET   every live job id, for listing/stats

Why a sorted set rather than a Redis list:
    A list gives FIFO but no priority.  Scoring by
    ``priority * 10^12 + monotonic_sequence`` yields strict priority ordering
    with FIFO *within* a priority band, in one O(log n) structure — matching
    :class:`~aquilia.tasks.engine.MemoryBackend` semantics exactly, so
    switching backends does not change dispatch order.

Atomicity:
    Claiming is a Lua script, so promoting due delayed jobs, popping the
    highest-priority member, and writing the lease all happen in one
    round trip that Redis executes without interleaving.  A ``ZRANGE`` then
    ``ZREM`` from Python would let two workers read the same member before
    either removed it, and both would run the job.

Crash recovery:
    A claimed job sits in ``{prefix}running`` scored by its lease deadline.
    :meth:`RedisBackend.reclaim_expired` moves anything past the deadline back
    to its ready set, so a job whose worker was killed is re-run rather than
    lost.  Long-running jobs must call heartbeat to keep their lease alive.

Requires:
    ``pip install redis`` (redis-py with asyncio support).

Examples::

    backend = RedisBackend(url="redis://localhost:6379/0")
    manager = TaskManager(backend=backend, num_workers=8)
    await manager.start()
"""

from __future__ import annotations

import json
import logging
import os
import socket
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from aquilia.tasks.engine import TaskBackend
from aquilia.tasks.faults import TaskBackendFault
from aquilia.tasks.job import Job, JobState

logger = logging.getLogger("aquilia.tasks.backends.redis")

# Priority band width. A job's score is priority * _BAND + sequence, giving
# strict priority ordering with FIFO inside each band. 10^12 is far above any
# realistic sequence counter, so bands cannot overlap.
_BAND = 10**12

# Claim the highest-priority runnable job atomically.
#
# KEYS[1] ready zset, KEYS[2] delayed zset, KEYS[3] running zset
# ARGV[1] now (epoch seconds), ARGV[2] lease deadline, ARGV[3] job key prefix
#
# Promotes every due delayed job first, so a job that just became due competes
# fairly on priority instead of waiting for the next tick.
_CLAIM_LUA = """
local now = tonumber(ARGV[1])
local lease = tonumber(ARGV[2])
local prefix = ARGV[3]

local due = redis.call('ZRANGEBYSCORE', KEYS[2], '-inf', now)
for i = 1, #due do
    local payload = redis.call('GET', prefix .. due[i])
    if payload then
        local decoded = cjson.decode(payload)
        local score = (decoded['priority'] or 2) * 1000000000000 + i
        redis.call('ZADD', KEYS[1], score, due[i])
    end
    redis.call('ZREM', KEYS[2], due[i])
end

local picked = redis.call('ZRANGE', KEYS[1], 0, 0)
if #picked == 0 then
    return nil
end

local job_id = picked[1]
redis.call('ZREM', KEYS[1], job_id)
redis.call('ZADD', KEYS[3], lease, job_id)
return redis.call('GET', prefix .. job_id)
"""

# Extend a lease only while this worker still owns the job.
# KEYS[1] running zset, KEYS[2] job key. ARGV[1] deadline, ARGV[2] owner.
_HEARTBEAT_LUA = """
local payload = redis.call('GET', KEYS[2])
if not payload then
    return 0
end
local decoded = cjson.decode(payload)
if decoded['owner'] ~= ARGV[2] then
    return 0
end
redis.call('ZADD', KEYS[1], tonumber(ARGV[1]), decoded['id'])
return 1
"""

# Release a fingerprint reservation only if this job still holds it.
# KEYS[1] fingerprint key. ARGV[1] job id.
_RELEASE_FP_LUA = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
end
return 0
"""


def _epoch(dt: datetime) -> float:
    """Convert an aware datetime to epoch seconds."""
    return dt.timestamp()


class RedisBackend(TaskBackend):
    """
    Redis-backed task queue for distributed, durable execution.

    Lifecycle:
        :meth:`initialize` opens the connection pool and registers the Lua
        scripts; :meth:`shutdown` closes the pool.  Both are driven by
        :class:`~aquilia.tasks.engine.TaskManager`.

    Concurrency:
        Safe across processes and machines.  Job claiming is atomic (Lua), so
        exactly one worker wins any given job at claim time.  Combined with
        lease reclamation this yields at-least-once delivery: a job whose
        worker dies is retried, and a worker that stalls past its lease may
        see its job re-run elsewhere.  Task functions should be idempotent.

    Args:
        url: Redis connection URL.  Falls back to ``$REDIS_URL``, then
            ``redis://localhost:6379/0``.
        prefix: Key namespace, so several apps can share one Redis instance.
        lease_seconds: How long a claim is valid before another worker may
            reclaim the job.  Should exceed typical job duration; longer jobs
            renew via :meth:`heartbeat`.
        worker_id: Identity recorded as a job's owner.  Defaults to
            ``hostname:pid:random``, which stays unique when several workers
            run on one host.
        dead_letter_max: Dead-letter ring size.
        max_connections: Connection pool size.

    Attributes:
        is_distributed: ``True``.
        is_persistent: ``True``.

    Examples::

        backend = RedisBackend(url="redis://cache:6379/1", lease_seconds=120)
        manager = TaskManager(backend=backend, num_workers=16)
        await manager.start()

        # Two processes running this code cooperate on one queue;
        # each job is claimed by exactly one of them.
    """

    is_distributed = True
    is_persistent = True

    def __init__(
        self,
        url: str | None = None,
        *,
        prefix: str = "aquilia:tasks:",
        lease_seconds: float = 300.0,
        worker_id: str | None = None,
        dead_letter_max: int = 1000,
        max_connections: int = 10,
    ) -> None:
        self.url = url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.prefix = prefix
        self.lease_seconds = lease_seconds
        self.worker_id = worker_id or f"{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:6]}"
        self.dead_letter_max = dead_letter_max
        self.max_connections = max_connections

        self._redis: Any = None
        self._claim: Any = None
        self._heartbeat: Any = None
        self._release_fp: Any = None
        self._sequence = 0

    # ── Key helpers ─────────────────────────────────────────────────

    def _job_key(self, job_id: str) -> str:
        return f"{self.prefix}job:{job_id}"

    def _ready_key(self, queue: str) -> str:
        return f"{self.prefix}ready:{queue}"

    def _delayed_key(self, queue: str) -> str:
        return f"{self.prefix}delayed:{queue}"

    @property
    def _running_key(self) -> str:
        return f"{self.prefix}running"

    @property
    def _queues_key(self) -> str:
        return f"{self.prefix}queues"

    @property
    def _index_key(self) -> str:
        return f"{self.prefix}index"

    @property
    def _dead_key(self) -> str:
        return f"{self.prefix}dead"

    def _fp_key(self, fingerprint: str) -> str:
        return f"{self.prefix}fp:{fingerprint}"

    # ── Lifecycle ───────────────────────────────────────────────────

    async def initialize(self) -> None:
        """
        Open the connection pool and register Lua scripts.

        Raises:
            TaskBackendFault: If ``redis`` is not installed or the server is
                unreachable.  Failing loudly at startup is deliberate: a
                silent fallback to in-memory would look healthy while
                quietly dropping every job on restart.
        """
        if self._redis is not None:
            return
        try:
            import redis.asyncio as aioredis
        except ImportError as e:
            raise TaskBackendFault(
                "RedisBackend",
                "initialize",
                "the 'redis' package is required. Install with: pip install aquilia[tasks-redis]",
            ) from e

        try:
            self._redis = aioredis.from_url(
                self.url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=self.max_connections,
            )
            await self._redis.ping()
        except Exception as e:
            self._redis = None
            raise TaskBackendFault("RedisBackend", "initialize", str(e)) from e

        self._claim = self._redis.register_script(_CLAIM_LUA)
        self._heartbeat = self._redis.register_script(_HEARTBEAT_LUA)
        self._release_fp = self._redis.register_script(_RELEASE_FP_LUA)

    async def shutdown(self) -> None:
        """Close the Redis connection pool.  Safe to call without initialize."""
        if self._redis is not None:
            try:
                await self._redis.aclose()
            except Exception as e:  # pragma: no cover - close is best-effort
                logger.warning("RedisBackend shutdown error: %s", e)
            self._redis = None

    async def _client(self) -> Any:
        """Return a live client, connecting lazily if needed."""
        if self._redis is None:
            await self.initialize()
        return self._redis

    # ── Core queue operations ───────────────────────────────────────

    async def push(self, job: Job) -> None:
        """
        Store a job and make it claimable.

        A job with a future ``scheduled_at`` or unsatisfied dependencies goes
        to the delayed set instead of the ready set; the claim script promotes
        it once due.

        Raises:
            TaskSerializationFault: If the job's arguments are not
                JSON-representable.
            TaskBackendFault: On a Redis transport failure.
        """
        redis = await self._client()
        payload = json.dumps(job.to_payload())
        self._sequence += 1

        try:
            pipe = redis.pipeline()
            pipe.set(self._job_key(job.id), payload)
            pipe.sadd(self._queues_key, job.queue)
            pipe.sadd(self._index_key, job.id)

            if job.scheduled_at and job.scheduled_at > datetime.now(timezone.utc):
                pipe.zadd(self._delayed_key(job.queue), {job.id: _epoch(job.scheduled_at)})
            else:
                score = job.priority.value * _BAND + self._sequence
                pipe.zadd(self._ready_key(job.queue), {job.id: score})
            await pipe.execute()
        except Exception as e:
            raise TaskBackendFault("RedisBackend", "push", str(e)) from e

    async def pop(self, queue: str = "default") -> Job | None:
        """
        Atomically claim the highest-priority runnable job.

        The claimed job is marked ``RUNNING`` with this worker as owner and a
        lease deadline, so no other worker can take it while the lease holds.

        A job whose dependencies are unsatisfied is returned to the queue and
        the scan continues, so a blocked workflow node never stalls unrelated
        work behind it.

        Returns:
            A claimed job, or ``None`` when nothing is runnable.
        """
        redis = await self._client()
        now = datetime.now(timezone.utc)
        deadline = _epoch(now + timedelta(seconds=self.lease_seconds))

        # Bounded scan: a blocked job is re-queued and we look past it, but we
        # never loop forever on a queue made entirely of blocked jobs.
        for _ in range(32):
            try:
                raw = await self._claim(
                    keys=[self._ready_key(queue), self._delayed_key(queue), self._running_key],
                    args=[_epoch(now), deadline, f"{self.prefix}job:"],
                )
            except Exception as e:
                raise TaskBackendFault("RedisBackend", "pop", str(e)) from e

            if not raw:
                return None

            job = Job.from_payload(json.loads(raw))

            if job.is_terminal:
                await redis.zrem(self._running_key, job.id)
                continue

            if job.depends_on and not await self.are_dependencies_satisfied(job):
                job.state = JobState.WAITING
                await redis.zrem(self._running_key, job.id)
                await self._store(job)
                self._sequence += 1
                await redis.zadd(
                    self._ready_key(job.queue),
                    {job.id: job.priority.value * _BAND + self._sequence},
                )
                continue

            job.state = JobState.RUNNING
            job.owner = self.worker_id
            job.lease_expires_at = now + timedelta(seconds=self.lease_seconds)
            job.started_at = now
            await self._store(job)
            return job

        return None

    async def _store(self, job: Job) -> None:
        """Write a job payload without touching queue membership."""
        redis = await self._client()
        await redis.set(self._job_key(job.id), json.dumps(job.to_payload()))

    async def get(self, job_id: str) -> Job | None:
        """Fetch a job by ID, or ``None`` if it is unknown or expired."""
        redis = await self._client()
        try:
            raw = await redis.get(self._job_key(job_id))
        except Exception as e:
            raise TaskBackendFault("RedisBackend", "get", str(e)) from e
        return Job.from_payload(json.loads(raw)) if raw else None

    async def update(self, job: Job) -> None:
        """
        Persist a job's state.

        A job that has become terminal is removed from the running set and its
        fingerprint reservation is released, so identical work can be
        scheduled again.  Dead jobs are appended to the dead-letter ring.

        A job returned to ``RETRYING``/``PENDING`` is re-queued, which is how
        the manager's retry path re-arms a failed job.
        """
        redis = await self._client()
        try:
            await self._store(job)

            if job.is_terminal:
                pipe = redis.pipeline()
                pipe.zrem(self._running_key, job.id)
                if job.state is JobState.DEAD:
                    pipe.lpush(self._dead_key, job.id)
                    pipe.ltrim(self._dead_key, 0, self.dead_letter_max - 1)
                await pipe.execute()
                if job.dedup_key:
                    await self.release_fingerprint(job.dedup_key, job.id)

            elif job.state in (JobState.RETRYING, JobState.PENDING, JobState.SCHEDULED, JobState.WAITING):
                await redis.zrem(self._running_key, job.id)
                self._sequence += 1
                if job.scheduled_at and job.scheduled_at > datetime.now(timezone.utc):
                    await redis.zadd(self._delayed_key(job.queue), {job.id: _epoch(job.scheduled_at)})
                else:
                    await redis.zadd(
                        self._ready_key(job.queue),
                        {job.id: job.priority.value * _BAND + self._sequence},
                    )
        except TaskBackendFault:
            raise
        except Exception as e:
            raise TaskBackendFault("RedisBackend", "update", str(e)) from e

    # ── Leases ──────────────────────────────────────────────────────

    async def heartbeat(self, job: Job, lease_seconds: float) -> bool:
        """
        Extend this worker's lease on a running job.

        Returns:
            ``False`` if the lease already lapsed and another worker took
            ownership — the caller should stop working on the job, since a
            second execution is already under way.
        """
        redis = await self._client()
        deadline = _epoch(datetime.now(timezone.utc) + timedelta(seconds=lease_seconds))
        try:
            result = await self._heartbeat(
                keys=[self._running_key, self._job_key(job.id)],
                args=[deadline, self.worker_id],
            )
        except Exception as e:
            logger.warning("Heartbeat failed for job %s: %s", job.id, e)
            return False

        if not result:
            return False

        job.lease_expires_at = datetime.now(timezone.utc) + timedelta(seconds=lease_seconds)
        await self._store(job)
        return True

    async def reclaim_expired(self, *, limit: int = 100) -> int:
        """
        Re-queue jobs whose worker died without releasing its lease.

        This is what makes worker crashes survivable: without it a claimed job
        would sit in the running set forever, invisible and never retried.

        Args:
            limit: Maximum jobs to reclaim per pass.

        Returns:
            Number of jobs returned to their ready queue.
        """
        redis = await self._client()
        now = datetime.now(timezone.utc)
        try:
            expired = await redis.zrangebyscore(self._running_key, "-inf", _epoch(now), start=0, num=limit)
        except Exception as e:
            raise TaskBackendFault("RedisBackend", "reclaim_expired", str(e)) from e

        reclaimed = 0
        for job_id in expired:
            job = await self.get(job_id)
            if job is None:
                await redis.zrem(self._running_key, job_id)
                continue
            if job.is_terminal:
                await redis.zrem(self._running_key, job_id)
                continue

            job.state = JobState.RETRYING if job.retry_count else JobState.PENDING
            job.owner = None
            job.lease_expires_at = None
            # Bumping the epoch lets a resurrected worker detect that its
            # claim was revoked, so its late write can be discarded.
            job.attempt_epoch += 1
            await self._store(job)

            self._sequence += 1
            pipe = redis.pipeline()
            pipe.zrem(self._running_key, job_id)
            pipe.zadd(self._ready_key(job.queue), {job_id: job.priority.value * _BAND + self._sequence})
            await pipe.execute()
            reclaimed += 1
            logger.warning("Reclaimed job %s from expired lease (owner=%s)", job_id, job.owner)

        return reclaimed

    # ── Idempotency ─────────────────────────────────────────────────

    async def reserve_fingerprint(self, fingerprint: str, job_id: str, ttl: float) -> str | None:
        """
        Reserve a fingerprint across the whole cluster via ``SET NX``.

        Args:
            fingerprint: Content digest from :attr:`Job.fingerprint`.
            job_id: Job claiming the reservation.
            ttl: Reservation lifetime.  Bounds how long a crashed producer can
                block identical work from being scheduled.

        Returns:
            ``None`` if reserved, otherwise the ID of the job already holding
            the fingerprint.
        """
        redis = await self._client()
        try:
            acquired = await redis.set(self._fp_key(fingerprint), job_id, nx=True, px=max(1, int(ttl * 1000)))
            if acquired:
                return None
            holder = await redis.get(self._fp_key(fingerprint))
        except Exception as e:
            raise TaskBackendFault("RedisBackend", "reserve_fingerprint", str(e)) from e
        return holder or None

    async def release_fingerprint(self, fingerprint: str, job_id: str) -> None:
        """Release a reservation, token-checked so it cannot free another job's claim."""
        try:
            await self._release_fp(keys=[self._fp_key(fingerprint)], args=[job_id])
        except Exception as e:  # pragma: no cover - release is best-effort
            logger.warning("Fingerprint release failed for %s: %s", fingerprint, e)

    # ── Queries ─────────────────────────────────────────────────────

    async def _all_jobs(self) -> list[Job]:
        """Load every indexed job.  O(n) — used by stats and listing."""
        redis = await self._client()
        job_ids = await redis.smembers(self._index_key)
        if not job_ids:
            return []
        raw_payloads = await redis.mget([self._job_key(jid) for jid in job_ids])
        jobs = [Job.from_payload(json.loads(raw)) for raw in raw_payloads if raw]

        # Drop index entries whose payload is gone, so the index cannot grow
        # without bound as jobs are cleaned up.
        missing = [jid for jid, raw in zip(job_ids, raw_payloads, strict=False) if not raw]
        if missing:
            await redis.srem(self._index_key, *missing)
        return jobs

    async def list_jobs(
        self,
        *,
        queue: str | None = None,
        state: JobState | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Job]:
        """List jobs newest-first, optionally filtered by queue and state."""
        jobs = await self._all_jobs()
        if queue:
            jobs = [j for j in jobs if j.queue == queue]
        if state:
            jobs = [j for j in jobs if j.state == state]
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs[offset : offset + limit]

    async def get_stats(self) -> dict[str, Any]:
        """
        Aggregate statistics, shaped identically to
        :meth:`MemoryBackend.get_stats` so the admin dashboard renders any
        backend without special-casing.
        """
        redis = await self._client()
        all_jobs = await self._all_jobs()
        queues = sorted(await redis.smembers(self._queues_key))
        dead_count = await redis.llen(self._dead_key)

        by_state: dict[str, int] = defaultdict(int)
        for j in all_jobs:
            by_state[j.state.value] += 1

        completed = [j for j in all_jobs if j.state is JobState.COMPLETED and j.duration_ms is not None]
        failed = [j for j in all_jobs if j.state in (JobState.FAILED, JobState.DEAD)]
        avg_duration = sum(j.duration_ms for j in completed) / len(completed) if completed else 0.0

        duration_buckets = [0, 10, 50, 100, 250, 500, 1000, 5000, float("inf")]
        duration_histogram = [0] * (len(duration_buckets) - 1)
        duration_labels = ["<10ms", "10-50ms", "50-100ms", "100-250ms", "250-500ms", "0.5-1s", "1-5s", ">5s"]
        for j in completed:
            for i in range(len(duration_buckets) - 1):
                if duration_buckets[i] <= j.duration_ms < duration_buckets[i + 1]:
                    duration_histogram[i] += 1
                    break

        now = datetime.now(timezone.utc)
        throughput_labels: list[str] = []
        completed_hourly: list[int] = []
        failed_hourly: list[int] = []
        for i in range(24):
            t = now - timedelta(hours=23 - i)
            hour_str = t.strftime("%Y-%m-%d %H:00")
            throughput_labels.append(t.strftime("%H:00"))
            completed_hourly.append(
                sum(1 for j in completed if j.completed_at and j.completed_at.strftime("%Y-%m-%d %H:00") == hour_str)
            )
            failed_hourly.append(
                sum(1 for j in failed if j.completed_at and j.completed_at.strftime("%Y-%m-%d %H:00") == hour_str)
            )

        terminal = len(completed) + len(failed)
        success_rate = round((len(completed) / terminal * 100) if terminal else 100, 1)

        sorted_durations = sorted(j.duration_ms for j in completed) if completed else []
        p50 = sorted_durations[len(sorted_durations) // 2] if sorted_durations else 0
        p95 = sorted_durations[int(len(sorted_durations) * 0.95)] if sorted_durations else 0
        p99 = sorted_durations[int(len(sorted_durations) * 0.99)] if sorted_durations else 0

        queue_chart_labels = queues or ["default"]
        queue_pending, queue_running, queue_completed_q, queue_failed_q = [], [], [], []
        for q in queue_chart_labels:
            q_jobs = [j for j in all_jobs if j.queue == q]
            queue_pending.append(
                sum(1 for j in q_jobs if j.state in (JobState.PENDING, JobState.SCHEDULED, JobState.WAITING))
            )
            queue_running.append(sum(1 for j in q_jobs if j.state is JobState.RUNNING))
            queue_completed_q.append(sum(1 for j in q_jobs if j.state is JobState.COMPLETED))
            queue_failed_q.append(sum(1 for j in q_jobs if j.state in (JobState.FAILED, JobState.DEAD)))

        state_labels = list(by_state.keys()) if by_state else ["No Jobs"]
        state_values = list(by_state.values()) if by_state else [0]

        return {
            "total_jobs": len(all_jobs),
            "by_state": dict(by_state),
            "queues": queues,
            "queue_count": len(queues),
            "avg_duration_ms": round(avg_duration, 2),
            "dead_letter_count": dead_count,
            "completed_count": len(completed),
            "failed_count": by_state.get("failed", 0),
            "active_count": by_state.get("running", 0),
            "pending_count": by_state.get("pending", 0) + by_state.get("scheduled", 0),
            "success_rate": success_rate,
            "p50_ms": round(p50, 2),
            "p95_ms": round(p95, 2),
            "p99_ms": round(p99, 2),
            "charts": {
                "throughput": {
                    "labels": throughput_labels,
                    "completed": completed_hourly,
                    "failed": failed_hourly,
                },
                "duration_histogram": {"labels": duration_labels, "values": duration_histogram},
                "state_doughnut": {"labels": state_labels, "values": state_values},
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
        """Per-queue job counts, keyed by state value."""
        result: dict[str, dict[str, int]] = {}
        for job in await self._all_jobs():
            result.setdefault(job.queue, defaultdict(int))
            result[job.queue][job.state.value] += 1
        return {q: dict(counts) for q, counts in result.items()}

    # ── Maintenance ─────────────────────────────────────────────────

    async def cleanup(self, max_age_seconds: float = 3600) -> int:
        """Delete terminal jobs older than ``max_age_seconds``.  Returns the count."""
        redis = await self._client()
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=max_age_seconds)
        removed = 0
        for job in await self._all_jobs():
            if job.is_terminal and job.completed_at and job.completed_at < cutoff:
                pipe = redis.pipeline()
                pipe.delete(self._job_key(job.id))
                pipe.srem(self._index_key, job.id)
                await pipe.execute()
                removed += 1
        return removed

    async def cancel(self, job_id: str) -> bool:
        """Cancel a non-terminal job and remove it from every queue."""
        redis = await self._client()
        job = await self.get(job_id)
        if not job or job.is_terminal:
            return False

        job.state = JobState.CANCELLED
        job.completed_at = datetime.now(timezone.utc)
        await self._store(job)

        pipe = redis.pipeline()
        pipe.zrem(self._ready_key(job.queue), job_id)
        pipe.zrem(self._delayed_key(job.queue), job_id)
        pipe.zrem(self._running_key, job_id)
        await pipe.execute()
        return True

    async def retry(self, job_id: str) -> bool:
        """Re-queue a failed, dead, or cancelled job for another attempt."""
        job = await self.get(job_id)
        if not job or job.state not in (JobState.FAILED, JobState.DEAD, JobState.CANCELLED):
            return False

        job.state = JobState.RETRYING
        job.completed_at = None
        job.result = None
        job.owner = None
        job.lease_expires_at = None
        await self.push(job)
        return True

    async def flush(self, queue: str | None = None) -> int:
        """
        Delete jobs — one queue's, or every queue's.

        Only keys under this backend's prefix are touched, so a shared Redis
        instance is never cleared wholesale.
        """
        redis = await self._client()
        jobs = await self._all_jobs()
        targets = [j for j in jobs if queue is None or j.queue == queue]
        if not targets:
            return 0

        pipe = redis.pipeline()
        for job in targets:
            pipe.delete(self._job_key(job.id))
            pipe.srem(self._index_key, job.id)
            pipe.zrem(self._running_key, job.id)
        for q in {j.queue for j in targets}:
            pipe.delete(self._ready_key(q))
            pipe.delete(self._delayed_key(q))
            if queue is not None:
                pipe.srem(self._queues_key, q)
        if queue is None:
            pipe.delete(self._queues_key)
            pipe.delete(self._dead_key)
        await pipe.execute()
        return len(targets)

    def __repr__(self) -> str:
        return f"RedisBackend(url={self.url!r}, prefix={self.prefix!r}, worker={self.worker_id!r})"
