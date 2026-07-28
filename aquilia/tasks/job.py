"""
AquilaTasks — Job Model.

Defines the :class:`Job` dataclass and the enumerations describing task
lifecycle, plus the JSON payload codec that lets a job cross a process
boundary into a persistent or distributed backend.

Serialisation contract:
    :meth:`Job.to_payload` / :meth:`Job.from_payload` round-trip a job through
    plain JSON.  ``args``/``kwargs`` must therefore hold JSON-compatible
    values; the callable itself is never serialised, only its ``func_ref``,
    which the worker resolves through the ``@task`` registry allowlist.

Security:
    JSON is used rather than ``pickle`` deliberately.  A queue is an
    attacker-reachable data store in many deployments, and ``pickle.loads``
    on queue contents is a remote-code-execution primitive.  Resolving
    ``func_ref`` through the registry means a queue entry can only ever name
    a function the application already chose to register.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from .faults import TaskSerializationFault


class JobState(str, Enum):
    """Task lifecycle states."""

    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"
    DEAD = "dead"  # Permanently failed (exhausted retries → dead-letter)
    WAITING = "waiting"  # Blocked on unfinished workflow dependencies


class Priority(int, Enum):
    """Task priority levels (lower value = higher priority)."""

    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


def _to_iso(dt: datetime | None) -> str | None:
    """Serialise a datetime to ISO-8601, preserving ``None``."""
    return dt.isoformat() if dt else None


def _from_iso(raw: Any) -> datetime | None:
    """Parse an ISO-8601 string back to an aware datetime, preserving ``None``."""
    if not raw:
        return None
    if isinstance(raw, datetime):
        return raw
    parsed = datetime.fromisoformat(raw)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


@dataclass
class JobResult:
    """
    Outcome of a finished job.

    Attributes:
        success: Whether the callable returned without raising.
        value: The returned value.  Survives serialisation intact when it is
            JSON-compatible; anything else degrades to its ``repr``, since an
            arbitrary return value cannot be reconstructed from JSON.
        error: Error message when ``success`` is False.
        error_type: Exception class name.
        traceback: Formatted traceback, for the admin error view.
        duration_ms: Wall-clock execution time.
    """

    success: bool
    value: Any = None
    error: str | None = None
    error_type: str | None = None
    traceback: str | None = None
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        # JSON-safe values round-trip unchanged so a workflow's fan-in step
        # receives the real value on a persistent backend, not "4" for 4.
        value: Any = self.value
        if value is not None:
            try:
                json.dumps(value)
            except (TypeError, ValueError):
                value = repr(value)

        return {
            "success": self.success,
            "value": value,
            "error": self.error,
            "error_type": self.error_type,
            "traceback": self.traceback,
            "duration_ms": round(self.duration_ms, 2),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> JobResult:
        """Rebuild a result from its serialised form (a non-JSON ``value`` stays a repr string)."""
        return cls(
            success=bool(data.get("success", False)),
            value=data.get("value"),
            error=data.get("error"),
            error_type=data.get("error_type"),
            traceback=data.get("traceback"),
            duration_ms=float(data.get("duration_ms", 0.0)),
        )


@dataclass
class Job:
    """
    A unit of background work.

    Immutable ID, mutable state.  Carries the full lifecycle: retry policy,
    timing, workflow dependencies, worker lease, and result.

    Lifecycle:
        ``PENDING``/``SCHEDULED``/``WAITING`` → ``RUNNING`` → ``COMPLETED``,
        or → ``RETRYING`` → ``RUNNING`` … → ``DEAD`` once retries are spent.
        ``WAITING`` jobs are held until every ID in ``depends_on`` reaches
        ``COMPLETED``.

    Distribution:
        ``lease_expires_at`` and ``owner`` support at-least-once delivery
        across workers: a worker claims a job by taking a time-bounded lease
        and renews it via heartbeat.  If the worker dies, the lease lapses and
        another worker reclaims the job rather than losing it.  This is why
        task functions should be idempotent — see ``dedup`` on
        :meth:`~aquilia.tasks.engine.TaskManager.enqueue`.

    Serialisation:
        ``_func`` is process-local and never persisted.  Workers resolve the
        callable from ``func_ref`` through the ``@task`` registry.

    Attributes:
        id: Stable 16-hex identifier.
        name: Human-readable label for dashboards.
        queue: Queue this job belongs to.
        priority: Dispatch priority; lower runs first.
        func_ref: Registered task name, or ``module:qualname``.
        args: Positional arguments; must be JSON-compatible to persist.
        kwargs: Keyword arguments; must be JSON-compatible to persist.
        state: Current :class:`JobState`.
        result: Populated once terminal.
        depends_on: Job IDs that must complete before this one may run.
        workflow_id: Groups every job belonging to one workflow.
        dedup_key: Fingerprint reserved for idempotency, when deduplicating.
        owner: Worker ID currently holding the lease.
        lease_expires_at: When an unrenewed lease lapses and the job is
            reclaimable.
        attempt_epoch: Increments on each reclaim, so a resurrected zombie
            worker's late write can be detected and discarded.
    """

    # Identity
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    name: str = ""
    queue: str = "default"
    priority: Priority = Priority.NORMAL

    # Callable reference (module:function format for serialisation)
    func_ref: str = ""
    args: tuple[Any, ...] = field(default_factory=tuple)
    kwargs: dict[str, Any] = field(default_factory=dict)

    # State
    state: JobState = JobState.PENDING
    result: JobResult | None = None

    # Retry policy
    max_retries: int = 3
    retry_count: int = 0
    retry_delay: float = 1.0  # Base delay in seconds
    retry_backoff: float = 2.0  # Exponential backoff multiplier
    retry_max_delay: float = 300.0  # Max delay cap (5 minutes)

    # Timing
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    scheduled_at: datetime | None = None  # For delayed/scheduled tasks
    timeout: float = 300.0  # Max execution time in seconds (5 min default)

    # Workflow / DAG
    depends_on: list[str] = field(default_factory=list)
    workflow_id: str | None = None

    # Idempotency
    dedup_key: str | None = None

    # Distributed execution
    owner: str | None = None
    lease_expires_at: datetime | None = None
    attempt_epoch: int = 0

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)

    # Internal
    _func: Any = field(default=None, repr=False, compare=False)

    @property
    def is_terminal(self) -> bool:
        """Whether the job has reached a state it will never leave."""
        return self.state in (
            JobState.COMPLETED,
            JobState.FAILED,
            JobState.CANCELLED,
            JobState.DEAD,
        )

    @property
    def is_runnable(self) -> bool:
        """
        Whether the job may execute right now.

        A job is runnable when its state is dispatchable and its
        ``scheduled_at`` has passed.  ``WAITING`` is excluded: dependency
        satisfaction is the backend's responsibility, since only the backend
        can see the other jobs' states.
        """
        if self.state not in (JobState.PENDING, JobState.RETRYING, JobState.SCHEDULED):
            return False
        return not (self.scheduled_at and datetime.now(timezone.utc) < self.scheduled_at)

    @property
    def next_retry_delay(self) -> float:
        """Next retry delay: exponential backoff, capped, with ±25% jitter."""
        import random

        delay = self.retry_delay * (self.retry_backoff**self.retry_count)
        delay = min(delay, self.retry_max_delay)
        # Add jitter (±25%)
        jitter = delay * 0.25 * (2 * random.random() - 1)
        return max(0.1, delay + jitter)

    @property
    def can_retry(self) -> bool:
        """Whether retry attempts remain."""
        return self.retry_count < self.max_retries

    @property
    def duration_ms(self) -> float | None:
        """Execution duration in milliseconds, or ``None`` if unfinished."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() * 1000
        return None

    @property
    def is_lease_expired(self) -> bool:
        """
        Whether a claimed job's lease has lapsed.

        True only for ``RUNNING`` jobs whose lease deadline has passed —
        the signal a backend uses to reclaim work from a dead worker.
        """
        if self.state is not JobState.RUNNING or self.lease_expires_at is None:
            return False
        return datetime.now(timezone.utc) >= self.lease_expires_at

    @property
    def fingerprint(self) -> str:
        """
        Stable content fingerprint used for deduplication.

        Derived from ``func_ref``, queue, and the arguments — two enqueue
        calls that would do identical work share a fingerprint.  Computed
        from the JSON form when possible so that equal-but-not-identical
        values (a tuple and a list of the same items) agree across processes;
        falls back to ``repr`` for non-JSON values, which keeps the in-memory
        backend working with live objects.

        Returns:
            12-hex-character digest.
        """
        try:
            canonical = json.dumps(
                {"f": self.func_ref, "q": self.queue, "a": list(self.args), "k": self.kwargs},
                sort_keys=True,
                default=repr,
            )
        except (TypeError, ValueError):
            canonical = f"{self.func_ref}:{self.queue}:{self.args!r}:{sorted(self.kwargs.items())!r}"
        return hashlib.sha256(canonical.encode()).hexdigest()[:12]

    # ── Persistence ─────────────────────────────────────────────────

    def to_payload(self) -> dict[str, Any]:
        """
        Serialise this job to a JSON-compatible dict for a persistent backend.

        Returns:
            A dict safe to pass to :func:`json.dumps`.

        Raises:
            TaskSerializationFault: If ``args`` or ``kwargs`` contain a value
                JSON cannot represent.  Failing here is deliberate: the
                alternative is a job that enqueues cleanly and then fails
                unrecoverably on a remote worker, far from the call site.

        Examples::

            payload = job.to_payload()
            restored = Job.from_payload(payload)
            assert restored.id == job.id
        """
        for label, value in (("args", list(self.args)), ("kwargs", self.kwargs)):
            try:
                json.dumps(value)
            except (TypeError, ValueError) as e:
                raise TaskSerializationFault(self.func_ref, str(e), path=label) from e

        return {
            "id": self.id,
            "name": self.name,
            "queue": self.queue,
            "priority": self.priority.value,
            "func_ref": self.func_ref,
            "args": list(self.args),
            "kwargs": self.kwargs,
            "state": self.state.value,
            "result": self.result.to_dict() if self.result else None,
            "max_retries": self.max_retries,
            "retry_count": self.retry_count,
            "retry_delay": self.retry_delay,
            "retry_backoff": self.retry_backoff,
            "retry_max_delay": self.retry_max_delay,
            "created_at": _to_iso(self.created_at),
            "started_at": _to_iso(self.started_at),
            "completed_at": _to_iso(self.completed_at),
            "scheduled_at": _to_iso(self.scheduled_at),
            "timeout": self.timeout,
            "depends_on": list(self.depends_on),
            "workflow_id": self.workflow_id,
            "dedup_key": self.dedup_key,
            "owner": self.owner,
            "lease_expires_at": _to_iso(self.lease_expires_at),
            "attempt_epoch": self.attempt_epoch,
            "metadata": self.metadata,
            "tags": list(self.tags),
        }

    @classmethod
    def from_payload(cls, data: dict[str, Any]) -> Job:
        """
        Rebuild a job from :meth:`to_payload` output.

        ``_func`` is left unset; the worker resolves the callable from
        ``func_ref`` through the ``@task`` registry, so a queue entry can
        never name a function the application did not register.

        Args:
            data: Payload dict, typically decoded from JSON.

        Returns:
            The reconstructed :class:`Job`.

        Examples::

            job = Job.from_payload(json.loads(raw))
        """
        result_data = data.get("result")
        return cls(
            id=data.get("id", uuid.uuid4().hex[:16]),
            name=data.get("name", ""),
            queue=data.get("queue", "default"),
            priority=Priority(data.get("priority", Priority.NORMAL.value)),
            func_ref=data.get("func_ref", ""),
            args=tuple(data.get("args", ())),
            kwargs=data.get("kwargs", {}) or {},
            state=JobState(data.get("state", JobState.PENDING.value)),
            result=JobResult.from_dict(result_data) if result_data else None,
            max_retries=data.get("max_retries", 3),
            retry_count=data.get("retry_count", 0),
            retry_delay=data.get("retry_delay", 1.0),
            retry_backoff=data.get("retry_backoff", 2.0),
            retry_max_delay=data.get("retry_max_delay", 300.0),
            created_at=_from_iso(data.get("created_at")) or datetime.now(timezone.utc),
            started_at=_from_iso(data.get("started_at")),
            completed_at=_from_iso(data.get("completed_at")),
            scheduled_at=_from_iso(data.get("scheduled_at")),
            timeout=data.get("timeout", 300.0),
            depends_on=list(data.get("depends_on", [])),
            workflow_id=data.get("workflow_id"),
            dedup_key=data.get("dedup_key"),
            owner=data.get("owner"),
            lease_expires_at=_from_iso(data.get("lease_expires_at")),
            attempt_epoch=data.get("attempt_epoch", 0),
            metadata=data.get("metadata", {}) or {},
            tags=list(data.get("tags", [])),
        )

    def is_serializable(self) -> bool:
        """
        Whether this job could be stored in a persistent backend.

        Useful for diagnostics and for tests that assert a task is
        distribution-ready without actually enqueueing it.

        Examples::

            assert Job(func_ref="app:send", kwargs={"id": 1}).is_serializable()
            assert not Job(func_ref="app:send", kwargs={"conn": object()}).is_serializable()
        """
        try:
            self.to_payload()
        except TaskSerializationFault:
            return False
        return True

    def to_dict(self) -> dict[str, Any]:
        """Serialise for API / admin dashboard consumption (human-facing view)."""
        return {
            "id": self.id,
            "name": self.name,
            "queue": self.queue,
            "priority": self.priority.name,
            "priority_value": self.priority.value,
            "func_ref": self.func_ref,
            "state": self.state.value,
            "result": self.result.to_dict() if self.result else None,
            "max_retries": self.max_retries,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat(),
            "started_at": _to_iso(self.started_at),
            "completed_at": _to_iso(self.completed_at),
            "scheduled_at": _to_iso(self.scheduled_at),
            "timeout": self.timeout,
            "duration_ms": self.duration_ms,
            "is_terminal": self.is_terminal,
            "can_retry": self.can_retry,
            "depends_on": list(self.depends_on),
            "workflow_id": self.workflow_id,
            "owner": self.owner,
            "lease_expires_at": _to_iso(self.lease_expires_at),
            "metadata": self.metadata,
            "tags": self.tags,
            "fingerprint": self.fingerprint,
        }

    def __repr__(self) -> str:
        return f"<Job {self.id} [{self.state.value}] {self.name or self.func_ref}>"
