"""
TasksIntegration — typed background task configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TasksIntegration:
    """
    Typed background tasks configuration.

    Backends:
        ``"memory"``
            Single-process, non-durable.  The default; right for development
            and for apps whose jobs can be safely lost on restart.
        ``"redis"``
            Multi-process and multi-machine, durable.  Requires
            ``pip install aquilia[tasks-redis]`` and ``redis_url``.
        ``"sql"``
            Durable on the application's existing database.  Requires
            ``Integration.database(...)``.  Slower than Redis, but adds no
            new infrastructure.

    Notes:
        Switching backends is configuration only — task code is unchanged.
        Distributed backends give **at-least-once** delivery, so task
        functions should be idempotent; see ``dedup`` on
        :meth:`~aquilia.tasks.engine.TaskManager.enqueue` to suppress
        duplicate enqueues.

    Examples::

        # Development
        TasksIntegration(num_workers=4)

        # Production: distributed workers, durable queue
        TasksIntegration(
            backend="redis",
            redis_url="redis://cache:6379/0",
            num_workers=16,
            lease_seconds=120,
        )

        # Durable without extra infrastructure
        TasksIntegration(backend="sql")
    """

    _integration_type: str = field(default="tasks", init=False, repr=False)

    backend: str = "memory"
    num_workers: int = 4
    default_queue: str = "default"
    cleanup_interval: float = 300.0
    cleanup_max_age: float = 3600.0
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_backoff: float = 2.0
    retry_max_delay: float = 300.0
    default_timeout: float = 300.0
    auto_start: bool = True
    dead_letter_max: int = 1000
    scheduler_tick: float = 15.0
    enabled: bool = True

    # ── Distributed backends ────────────────────────────────────────

    #: Redis connection URL. Falls back to ``$REDIS_URL`` when unset.
    redis_url: str | None = None
    #: Key namespace, so several apps can share one Redis instance.
    redis_prefix: str = "aquilia:tasks:"
    #: Job table name for the SQL backend.
    sql_table: str = "aquilia_tasks"
    #: How long a claimed job stays owned before another worker may reclaim it.
    lease_seconds: float = 300.0
    #: How often a running job renews its lease. Must be well under
    #: ``lease_seconds`` or long jobs get reclaimed mid-flight.
    heartbeat_interval: float = 30.0
    #: How often to sweep for jobs abandoned by crashed workers.
    reclaim_interval: float = 60.0
    #: How long a deduplication reservation is held.
    dedup_ttl: float = 3600.0
    #: Worker identity recorded as a job's owner. Defaults to hostname:pid.
    worker_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "_integration_type": "tasks",
            "enabled": self.enabled,
            "backend": self.backend,
            "num_workers": self.num_workers,
            "default_queue": self.default_queue,
            "cleanup_interval": self.cleanup_interval,
            "cleanup_max_age": self.cleanup_max_age,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "retry_backoff": self.retry_backoff,
            "retry_max_delay": self.retry_max_delay,
            "default_timeout": self.default_timeout,
            "auto_start": self.auto_start,
            "dead_letter_max": self.dead_letter_max,
            "scheduler_tick": self.scheduler_tick,
            "redis_url": self.redis_url,
            "redis_prefix": self.redis_prefix,
            "sql_table": self.sql_table,
            "lease_seconds": self.lease_seconds,
            "heartbeat_interval": self.heartbeat_interval,
            "reclaim_interval": self.reclaim_interval,
            "dedup_ttl": self.dedup_ttl,
            "worker_id": self.worker_id,
        }
