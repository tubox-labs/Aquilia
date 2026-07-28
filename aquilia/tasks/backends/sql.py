"""
SQL task backend — durable job execution on the application's own database.

Gives background tasks crash-survivable state without adding infrastructure:
if the app already has Postgres, MySQL, or SQLite configured, that database
can hold the queue.

Trade-off versus :class:`~aquilia.tasks.backends.redis.RedisBackend`:
    Redis is faster and scales further — its claim path is one round trip
    against an in-memory sorted set.  SQL wins when you cannot add a Redis
    dependency, or when you want jobs to commit in the *same transaction*
    as the business data that created them, so a rolled-back request cannot
    leave an orphaned job behind.  For throughput above roughly a few hundred
    jobs/second, prefer Redis.

Schema (created on first :meth:`initialize`)::

    aquilia_tasks(
        id TEXT PRIMARY KEY, queue TEXT, priority INTEGER, state TEXT,
        func_ref TEXT, payload TEXT,            -- full JSON job
        available_at TEXT,                       -- ISO; when it may run
        lease_expires_at TEXT, owner TEXT,       -- distributed claim
        dedup_key TEXT, workflow_id TEXT,
        created_at TEXT, completed_at TEXT, sequence INTEGER
    )
    aquilia_task_locks(fingerprint TEXT PRIMARY KEY, job_id TEXT, expires_at TEXT)

The unique primary key on ``aquilia_task_locks.fingerprint`` is what makes
idempotency correct under concurrency: two workers racing to reserve the same
fingerprint both attempt an INSERT, and the database rejects exactly one.

Claiming:
    A claim is a conditional ``UPDATE ... WHERE id = ? AND state = ?`` inside a
    transaction.  ``rowcount == 0`` means another worker won the race, so the
    loser moves on rather than double-running the job.  This works on every
    supported dialect without needing ``SELECT ... FOR UPDATE SKIP LOCKED``,
    which SQLite does not have.

Examples::

    from aquilia.tasks.backends import SQLBackend

    backend = SQLBackend(database=app_db)
    manager = TaskManager(backend=backend)
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

from ..engine import TaskBackend
from ..faults import TaskBackendFault
from ..job import Job, JobState

logger = logging.getLogger("aquilia.tasks.backends.sql")

_TABLE = "aquilia_tasks"
_LOCK_TABLE = "aquilia_task_locks"

# States a job can be claimed from.
_CLAIMABLE = (JobState.PENDING.value, JobState.RETRYING.value, JobState.SCHEDULED.value, JobState.WAITING.value)


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def _parse(raw: Any) -> datetime | None:
    if not raw:
        return None
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
    parsed = datetime.fromisoformat(raw)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


class SQLBackend(TaskBackend):
    """
    Database-backed task queue.

    Lifecycle:
        :meth:`initialize` creates the tables if absent, so a job store needs
        no separate migration step — the framework owns this schema, not the
        application's model layer.

    Concurrency:
        Safe across processes sharing one database.  Claims are conditional
        updates, so exactly one worker wins each job.  Combined with lease
        reclamation this gives at-least-once delivery; task functions should
        be idempotent.

    Args:
        database: An :class:`~aquilia.db.engine.AquiliaDatabase`.  When
            omitted, the backend resolves the application database lazily on
            first use, which lets it be constructed before the DB subsystem
            has started.
        table: Job table name, for deployments that namespace their schema.
        lease_seconds: Claim lifetime before another worker may reclaim.
        worker_id: Owner identity recorded on claimed jobs.
        dead_letter_max: Dead-letter retention count.

    Attributes:
        is_distributed: ``True`` — any process pointed at the same database
            participates.
        is_persistent: ``True``.

    Examples::

        backend = SQLBackend(database=db, lease_seconds=120)
        await backend.initialize()
        manager = TaskManager(backend=backend)
    """

    is_distributed = True
    is_persistent = True

    def __init__(
        self,
        database: Any = None,
        *,
        table: str = _TABLE,
        lease_seconds: float = 300.0,
        worker_id: str | None = None,
        dead_letter_max: int = 1000,
    ) -> None:
        self._db = database
        # Identifiers are interpolated into DDL/DML, so restrict them to a
        # safe character set rather than trusting the caller.
        if not table.replace("_", "").isalnum():
            raise TaskBackendFault("SQLBackend", "__init__", f"Invalid table name: {table!r}")
        self.table = table
        self.lock_table = f"{table}_locks"
        self.lease_seconds = lease_seconds
        self.worker_id = worker_id or f"{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:6]}"
        self.dead_letter_max = dead_letter_max
        self._initialized = False
        self._sequence = 0

    # ── Lifecycle ───────────────────────────────────────────────────

    async def _database(self) -> Any:
        """Resolve the database handle, falling back to the app-wide instance."""
        if self._db is not None:
            return self._db
        try:
            from aquilia.db import get_database

            self._db = get_database()
        except Exception as e:
            raise TaskBackendFault(
                "SQLBackend",
                "connect",
                f"no database available ({e}). Pass database=... or enable Integration.database().",
            ) from e
        if self._db is None:
            raise TaskBackendFault(
                "SQLBackend",
                "connect",
                "no database configured. Pass database=... or enable Integration.database().",
            )
        return self._db

    async def initialize(self) -> None:
        """
        Create the job and lock tables if they do not exist.

        Raises:
            TaskBackendFault: If the schema cannot be created.
        """
        if self._initialized:
            return
        db = await self._database()
        try:
            await db.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.table} (
                    id TEXT PRIMARY KEY,
                    queue TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    state TEXT NOT NULL,
                    func_ref TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    available_at TEXT,
                    lease_expires_at TEXT,
                    owner TEXT,
                    dedup_key TEXT,
                    workflow_id TEXT,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    sequence INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            # Claim path filters on (queue, state, priority); without this
            # index every pop degrades to a full scan as the table grows.
            await db.execute(
                f"CREATE INDEX IF NOT EXISTS idx_{self.table}_claim ON {self.table} (queue, state, priority, sequence)"
            )
            await db.execute(f"CREATE INDEX IF NOT EXISTS idx_{self.table}_lease ON {self.table} (lease_expires_at)")
            await db.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.lock_table} (
                    fingerprint TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
                """
            )
        except Exception as e:
            raise TaskBackendFault("SQLBackend", "initialize", str(e)) from e
        self._initialized = True

    async def shutdown(self) -> None:
        """Release backend state.  The database connection is owned by the app."""
        self._initialized = False

    async def _ready(self) -> Any:
        """Return a database handle, initialising the schema on first use."""
        if not self._initialized:
            await self.initialize()
        return await self._database()

    # ── Row mapping ─────────────────────────────────────────────────

    def _row_to_job(self, row: dict[str, Any]) -> Job:
        """Rebuild a job from its stored JSON payload."""
        return Job.from_payload(json.loads(row["payload"]))

    async def _write(self, db: Any, job: Job, *, sequence: int | None = None) -> None:
        """Insert or update a job row (portable upsert: UPDATE, then INSERT)."""
        payload = json.dumps(job.to_payload())
        available_at = _iso(job.scheduled_at or job.created_at)

        result = await db.execute(
            f"""
            UPDATE {self.table}
               SET queue = ?, priority = ?, state = ?, func_ref = ?, payload = ?,
                   available_at = ?, lease_expires_at = ?, owner = ?,
                   dedup_key = ?, workflow_id = ?, completed_at = ?
             WHERE id = ?
            """,
            [
                job.queue,
                job.priority.value,
                job.state.value,
                job.func_ref,
                payload,
                available_at,
                _iso(job.lease_expires_at),
                job.owner,
                job.dedup_key,
                job.workflow_id,
                _iso(job.completed_at),
                job.id,
            ],
        )
        if getattr(result, "rowcount", 0):
            return

        self._sequence += 1
        await db.execute(
            f"""
            INSERT INTO {self.table}
                (id, queue, priority, state, func_ref, payload, available_at,
                 lease_expires_at, owner, dedup_key, workflow_id, created_at,
                 completed_at, sequence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                job.id,
                job.queue,
                job.priority.value,
                job.state.value,
                job.func_ref,
                payload,
                available_at,
                _iso(job.lease_expires_at),
                job.owner,
                job.dedup_key,
                job.workflow_id,
                _iso(job.created_at),
                _iso(job.completed_at),
                sequence if sequence is not None else self._sequence,
            ],
        )

    # ── Core queue operations ───────────────────────────────────────

    async def push(self, job: Job) -> None:
        """
        Persist a job and make it claimable.

        Raises:
            TaskSerializationFault: If the job's arguments are not JSON-safe.
            TaskBackendFault: On a database failure.
        """
        db = await self._ready()
        try:
            await self._write(db, job)
        except TaskBackendFault:
            raise
        except Exception as e:
            raise TaskBackendFault("SQLBackend", "push", str(e)) from e

    async def pop(self, queue: str = "default") -> Job | None:
        """
        Claim the highest-priority runnable job in ``queue``.

        Candidates are read in priority order, then claimed with a conditional
        update.  A losing racer sees ``rowcount == 0`` and tries the next
        candidate, so concurrent workers never both claim one job.

        Jobs with unsatisfied dependencies are skipped and left queued.
        """
        db = await self._ready()
        now = datetime.now(timezone.utc)
        try:
            rows = await db.fetch_all(
                f"""
                SELECT * FROM {self.table}
                 WHERE queue = ?
                   AND state IN (?, ?, ?, ?)
                   AND (available_at IS NULL OR available_at <= ?)
                 ORDER BY priority ASC, sequence ASC
                 LIMIT 32
                """,
                [queue, *_CLAIMABLE, _iso(now)],
            )
        except Exception as e:
            raise TaskBackendFault("SQLBackend", "pop", str(e)) from e

        for row in rows:
            job = self._row_to_job(row)

            if job.depends_on and not await self.are_dependencies_satisfied(job):
                if job.state is not JobState.WAITING:
                    job.state = JobState.WAITING
                    await self._write(db, job)
                continue

            claimed = await db.execute(
                f"""
                UPDATE {self.table}
                   SET state = ?, owner = ?, lease_expires_at = ?
                 WHERE id = ? AND state = ?
                """,
                [
                    JobState.RUNNING.value,
                    self.worker_id,
                    _iso(now + timedelta(seconds=self.lease_seconds)),
                    job.id,
                    row["state"],
                ],
            )
            if not getattr(claimed, "rowcount", 0):
                continue  # another worker won this row

            job.state = JobState.RUNNING
            job.owner = self.worker_id
            job.lease_expires_at = now + timedelta(seconds=self.lease_seconds)
            job.started_at = now
            await self._write(db, job)
            return job

        return None

    async def get(self, job_id: str) -> Job | None:
        """Fetch a job by ID."""
        db = await self._ready()
        try:
            row = await db.fetch_one(f"SELECT * FROM {self.table} WHERE id = ?", [job_id])
        except Exception as e:
            raise TaskBackendFault("SQLBackend", "get", str(e)) from e
        return self._row_to_job(row) if row else None

    async def update(self, job: Job) -> None:
        """
        Persist job state, releasing the fingerprint once terminal.

        A terminal job's reservation is dropped so identical work can be
        scheduled again later.
        """
        db = await self._ready()
        try:
            await self._write(db, job)
            if job.is_terminal:
                if job.dedup_key:
                    await self.release_fingerprint(job.dedup_key, job.id)
                if job.state is JobState.DEAD:
                    await self._trim_dead_letter(db)
        except TaskBackendFault:
            raise
        except Exception as e:
            raise TaskBackendFault("SQLBackend", "update", str(e)) from e

    async def _trim_dead_letter(self, db: Any) -> None:
        """Keep the dead-letter set bounded so a failing task cannot fill the table."""
        rows = await db.fetch_all(
            f"SELECT id FROM {self.table} WHERE state = ? ORDER BY completed_at DESC",
            [JobState.DEAD.value],
        )
        excess = [r["id"] for r in rows[self.dead_letter_max :]]
        for job_id in excess:
            await db.execute(f"DELETE FROM {self.table} WHERE id = ?", [job_id])

    # ── Leases ──────────────────────────────────────────────────────

    async def heartbeat(self, job: Job, lease_seconds: float) -> bool:
        """
        Extend the lease while this worker still owns the job.

        Returns:
            ``False`` when ownership was lost — the caller should abandon the
            job, because another worker has already reclaimed it.
        """
        db = await self._ready()
        deadline = datetime.now(timezone.utc) + timedelta(seconds=lease_seconds)
        try:
            result = await db.execute(
                f"UPDATE {self.table} SET lease_expires_at = ? WHERE id = ? AND owner = ? AND state = ?",
                [_iso(deadline), job.id, self.worker_id, JobState.RUNNING.value],
            )
        except Exception as e:
            logger.warning("Heartbeat failed for job %s: %s", job.id, e)
            return False

        if not getattr(result, "rowcount", 0):
            return False
        job.lease_expires_at = deadline
        return True

    async def reclaim_expired(self, *, limit: int = 100) -> int:
        """
        Return jobs abandoned by dead workers to the runnable pool.

        Returns:
            Number of jobs reclaimed.
        """
        db = await self._ready()
        now = datetime.now(timezone.utc)
        try:
            rows = await db.fetch_all(
                f"""
                SELECT * FROM {self.table}
                 WHERE state = ? AND lease_expires_at IS NOT NULL AND lease_expires_at <= ?
                 LIMIT {int(limit)}
                """,
                [JobState.RUNNING.value, _iso(now)],
            )
        except Exception as e:
            raise TaskBackendFault("SQLBackend", "reclaim_expired", str(e)) from e

        reclaimed = 0
        for row in rows:
            job = self._row_to_job(row)
            previous_owner = job.owner
            job.state = JobState.RETRYING if job.retry_count else JobState.PENDING
            job.owner = None
            job.lease_expires_at = None
            job.attempt_epoch += 1
            await self._write(db, job)
            reclaimed += 1
            logger.warning("Reclaimed job %s from expired lease (owner=%s)", job.id, previous_owner)
        return reclaimed

    # ── Idempotency ─────────────────────────────────────────────────

    async def reserve_fingerprint(self, fingerprint: str, job_id: str, ttl: float) -> str | None:
        """
        Reserve a fingerprint using the lock table's primary key.

        Concurrent reservations of the same fingerprint collide on the primary
        key, so the database decides the winner — no read-then-write race.

        Returns:
            ``None`` if reserved, otherwise the job ID already holding it.
        """
        db = await self._ready()
        now = datetime.now(timezone.utc)
        expires = now + timedelta(seconds=ttl)

        try:
            # Clear a lapsed reservation so a crashed producer cannot block
            # this work forever.
            await db.execute(f"DELETE FROM {self.lock_table} WHERE expires_at <= ?", [_iso(now)])
            try:
                await db.execute(
                    f"INSERT INTO {self.lock_table} (fingerprint, job_id, expires_at) VALUES (?, ?, ?)",
                    [fingerprint, job_id, _iso(expires)],
                )
                return None
            except Exception:
                row = await db.fetch_one(
                    f"SELECT job_id FROM {self.lock_table} WHERE fingerprint = ?",
                    [fingerprint],
                )
                if row is None:
                    return None
                return None if row["job_id"] == job_id else row["job_id"]
        except Exception as e:
            raise TaskBackendFault("SQLBackend", "reserve_fingerprint", str(e)) from e

    async def release_fingerprint(self, fingerprint: str, job_id: str) -> None:
        """Release a reservation, only if ``job_id`` still owns it."""
        db = await self._ready()
        try:
            await db.execute(
                f"DELETE FROM {self.lock_table} WHERE fingerprint = ? AND job_id = ?",
                [fingerprint, job_id],
            )
        except Exception as e:  # pragma: no cover - release is best-effort
            logger.warning("Fingerprint release failed for %s: %s", fingerprint, e)

    # ── Queries ─────────────────────────────────────────────────────

    async def list_jobs(
        self,
        *,
        queue: str | None = None,
        state: JobState | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Job]:
        """List jobs newest-first, optionally filtered by queue and state."""
        db = await self._ready()
        clauses: list[str] = []
        params: list[Any] = []
        if queue:
            clauses.append("queue = ?")
            params.append(queue)
        if state:
            clauses.append("state = ?")
            params.append(state.value)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""

        rows = await db.fetch_all(
            f"SELECT * FROM {self.table}{where} ORDER BY created_at DESC LIMIT {int(limit)} OFFSET {int(offset)}",
            params,
        )
        return [self._row_to_job(r) for r in rows]

    async def _all_jobs(self) -> list[Job]:
        db = await self._ready()
        rows = await db.fetch_all(f"SELECT * FROM {self.table}")
        return [self._row_to_job(r) for r in rows]

    async def get_stats(self) -> dict[str, Any]:
        """
        Aggregate statistics in the same shape as
        :meth:`MemoryBackend.get_stats`, so dashboards work unchanged.
        """
        all_jobs = await self._all_jobs()
        queues = sorted({j.queue for j in all_jobs})

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
            "dead_letter_count": by_state.get("dead", 0),
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
        db = await self._ready()
        rows = await db.fetch_all(f"SELECT queue, state, COUNT(*) AS n FROM {self.table} GROUP BY queue, state")
        result: dict[str, dict[str, int]] = {}
        for row in rows:
            result.setdefault(row["queue"], {})[row["state"]] = int(row["n"])
        return result

    # ── Maintenance ─────────────────────────────────────────────────

    async def cleanup(self, max_age_seconds: float = 3600) -> int:
        """Delete terminal jobs older than ``max_age_seconds``."""
        db = await self._ready()
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=max_age_seconds)
        terminal = (
            JobState.COMPLETED.value,
            JobState.FAILED.value,
            JobState.CANCELLED.value,
            JobState.DEAD.value,
        )
        result = await db.execute(
            f"""
            DELETE FROM {self.table}
             WHERE state IN (?, ?, ?, ?)
               AND completed_at IS NOT NULL
               AND completed_at < ?
            """,
            [*terminal, _iso(cutoff)],
        )
        return int(getattr(result, "rowcount", 0) or 0)

    async def cancel(self, job_id: str) -> bool:
        """Cancel a non-terminal job."""
        job = await self.get(job_id)
        if not job or job.is_terminal:
            return False
        job.state = JobState.CANCELLED
        job.completed_at = datetime.now(timezone.utc)
        job.owner = None
        job.lease_expires_at = None
        await self.update(job)
        return True

    async def retry(self, job_id: str) -> bool:
        """Re-queue a failed, dead, or cancelled job."""
        job = await self.get(job_id)
        if not job or job.state not in (JobState.FAILED, JobState.DEAD, JobState.CANCELLED):
            return False
        job.state = JobState.RETRYING
        job.completed_at = None
        job.result = None
        job.owner = None
        job.lease_expires_at = None
        await self.update(job)
        return True

    async def flush(self, queue: str | None = None) -> int:
        """Delete jobs — one queue's, or all of them."""
        db = await self._ready()
        if queue:
            row = await db.fetch_one(f"SELECT COUNT(*) AS n FROM {self.table} WHERE queue = ?", [queue])
            await db.execute(f"DELETE FROM {self.table} WHERE queue = ?", [queue])
        else:
            row = await db.fetch_one(f"SELECT COUNT(*) AS n FROM {self.table}")
            await db.execute(f"DELETE FROM {self.table}")
            await db.execute(f"DELETE FROM {self.lock_table}")
        return int(row["n"]) if row else 0

    def __repr__(self) -> str:
        return f"SQLBackend(table={self.table!r}, worker={self.worker_id!r})"
