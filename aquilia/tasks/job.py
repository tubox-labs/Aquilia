"""
AquilaTasks — Job Model.

Defines the Job dataclass and all enumerations for task lifecycle management.
"""

from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional, Tuple


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


class Priority(int, Enum):
    """Task priority levels (lower value = higher priority)."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass
class JobResult:
    """Stores the result or error from a completed/failed job."""
    success: bool
    value: Any = None
    error: Optional[str] = None
    error_type: Optional[str] = None
    traceback: Optional[str] = None
    duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "value": repr(self.value) if self.value is not None else None,
            "error": self.error,
            "error_type": self.error_type,
            "traceback": self.traceback,
            "duration_ms": round(self.duration_ms, 2),
        }


@dataclass
class Job:
    """
    Represents a background task job.

    Immutable ID, mutable state. Tracks full lifecycle including
    retries, timing, and results.
    """

    # Identity
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    name: str = ""
    queue: str = "default"
    priority: Priority = Priority.NORMAL

    # Callable reference (module:function format for serialisation)
    func_ref: str = ""
    args: Tuple[Any, ...] = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)

    # State
    state: JobState = JobState.PENDING
    result: Optional[JobResult] = None

    # Retry policy
    max_retries: int = 3
    retry_count: int = 0
    retry_delay: float = 1.0  # Base delay in seconds
    retry_backoff: float = 2.0  # Exponential backoff multiplier
    retry_max_delay: float = 300.0  # Max delay cap (5 minutes)

    # Timing
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None  # For delayed/scheduled tasks
    timeout: float = 300.0  # Max execution time in seconds (5 min default)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)

    # Internal
    _func: Any = field(default=None, repr=False, compare=False)

    @property
    def is_terminal(self) -> bool:
        """Check if job is in a terminal state."""
        return self.state in (
            JobState.COMPLETED,
            JobState.FAILED,
            JobState.CANCELLED,
            JobState.DEAD,
        )

    @property
    def is_runnable(self) -> bool:
        """Check if job can be executed now."""
        if self.state not in (JobState.PENDING, JobState.RETRYING, JobState.SCHEDULED):
            return False
        if self.scheduled_at and datetime.now(timezone.utc) < self.scheduled_at:
            return False
        return True

    @property
    def next_retry_delay(self) -> float:
        """Calculate next retry delay with exponential backoff + jitter."""
        import random
        delay = self.retry_delay * (self.retry_backoff ** self.retry_count)
        delay = min(delay, self.retry_max_delay)
        # Add jitter (±25%)
        jitter = delay * 0.25 * (2 * random.random() - 1)
        return max(0.1, delay + jitter)

    @property
    def can_retry(self) -> bool:
        """Check if job has remaining retry attempts."""
        return self.retry_count < self.max_retries

    @property
    def duration_ms(self) -> Optional[float]:
        """Execution duration in milliseconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() * 1000
        return None

    @property
    def fingerprint(self) -> str:
        """Stable fingerprint for deduplication."""
        data = f"{self.func_ref}:{self.queue}:{repr(self.args)}:{repr(sorted(self.kwargs.items()))}"
        return hashlib.sha256(data.encode()).hexdigest()[:12]

    def to_dict(self) -> Dict[str, Any]:
        """Serialise job for API/admin consumption."""
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
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "timeout": self.timeout,
            "duration_ms": self.duration_ms,
            "is_terminal": self.is_terminal,
            "can_retry": self.can_retry,
            "metadata": self.metadata,
            "tags": self.tags,
            "fingerprint": self.fingerprint,
        }

    def __repr__(self) -> str:
        return f"<Job {self.id} [{self.state.value}] {self.name or self.func_ref}>"
