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

    Example::

        TasksIntegration(num_workers=8, max_retries=5)
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
        }
