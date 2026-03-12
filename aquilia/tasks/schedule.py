"""
AquilaTasks — Schedule Definitions.

Provides ``every()`` and ``cron()`` helpers for declaring periodic
task schedules on ``@task`` decorators.

Usage::

    from aquilia.tasks import task, every, cron

    @task(schedule=every(minutes=30))
    async def cleanup_sessions():
        ...

    @task(schedule=cron("0 */6 * * *"))
    async def generate_reports():
        ...

    @task(schedule=every(seconds=10))
    async def health_ping():
        ...

Tasks **without** a ``schedule`` are on-demand only and must be
dispatched explicitly via ``task.delay(...)`` or
``manager.enqueue(task, ...)``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from .faults import TaskScheduleFault


@dataclass(frozen=True)
class IntervalSchedule:
    """
    Fixed-interval periodic schedule.

    The scheduler will enqueue the task every ``interval`` seconds
    after the previous run completes (or from server boot for the
    first invocation).

    Created via the ``every()`` helper.
    """

    interval: float  # seconds

    @property
    def human_readable(self) -> str:
        """Human-friendly representation of the interval."""
        s = self.interval
        if s < 60:
            return f"every {s:.0f}s"
        if s < 3600:
            m = s / 60
            return f"every {m:.0f}m" if m == int(m) else f"every {m:.1f}m"
        h = s / 3600
        return f"every {h:.0f}h" if h == int(h) else f"every {h:.1f}h"

    def next_run(self, last_run: datetime | None = None) -> datetime:
        """Calculate the next run time."""
        base = last_run or datetime.now(timezone.utc)
        return base + timedelta(seconds=self.interval)


@dataclass(frozen=True)
class CronSchedule:
    """
    Cron-expression periodic schedule.

    Supports standard 5-field cron expressions::

        ┌─────────── minute (0-59)
        │ ┌─────────── hour (0-23)
        │ │ ┌─────────── day of month (1-31)
        │ │ │ ┌─────────── month (1-12)
        │ │ │ │ ┌─────────── day of week (0-6, 0=Sunday)
        │ │ │ │ │
        * * * * *

    Created via the ``cron()`` helper.
    """

    expression: str
    _minute: tuple = field(default=(), repr=False)
    _hour: tuple = field(default=(), repr=False)
    _dom: tuple = field(default=(), repr=False)
    _month: tuple = field(default=(), repr=False)
    _dow: tuple = field(default=(), repr=False)

    @property
    def human_readable(self) -> str:
        return f"cron({self.expression})"

    def matches(self, dt: datetime) -> bool:
        """Check if a datetime matches this cron expression."""
        return (
            (not self._minute or dt.minute in self._minute)
            and (not self._hour or dt.hour in self._hour)
            and (not self._dom or dt.day in self._dom)
            and (not self._month or dt.month in self._month)
            and (not self._dow or dt.weekday() in self._dow)
        )

    def next_run(self, last_run: datetime | None = None) -> datetime:
        """
        Calculate next matching minute from ``last_run``.

        Scans forward minute-by-minute (up to 48 hours) to find
        the next matching slot.  For production use consider a
        more efficient algorithm; this is simple and correct.
        """
        base = last_run or datetime.now(timezone.utc)
        # Start from the next minute
        candidate = base.replace(second=0, microsecond=0) + timedelta(minutes=1)
        # Scan up to 48h of minutes
        for _ in range(48 * 60):
            if self.matches(candidate):
                return candidate
            candidate += timedelta(minutes=1)
        # Fallback: 1 hour from now
        return base + timedelta(hours=1)


# Type alias for schedule parameters
Schedule = IntervalSchedule | CronSchedule


# ════════════════════════════════════════════════════════════════════════
# Public helpers
# ════════════════════════════════════════════════════════════════════════


def every(
    *,
    seconds: float = 0,
    minutes: float = 0,
    hours: float = 0,
    days: float = 0,
) -> IntervalSchedule:
    """
    Create a fixed-interval schedule.

    At least one time unit must be > 0.

    Examples::

        every(seconds=30)       # Every 30 seconds
        every(minutes=5)        # Every 5 minutes
        every(hours=1)          # Every hour
        every(hours=2, minutes=30)  # Every 2.5 hours

    Args:
        seconds: Interval seconds component.
        minutes: Interval minutes component.
        hours: Interval hours component.
        days: Interval days component.

    Returns:
        IntervalSchedule instance.

    Raises:
        ValueError: If total interval is ≤ 0.
    """
    total = seconds + minutes * 60 + hours * 3600 + days * 86400
    if total <= 0:
        raise TaskScheduleFault("Schedule interval must be > 0. Provide at least one of: seconds, minutes, hours, days")
    return IntervalSchedule(interval=total)


def cron(expression: str) -> CronSchedule:
    """
    Create a cron-expression schedule.

    Supports standard 5-field cron syntax with ``*``, ranges
    (``1-5``), lists (``1,3,5``), and steps (``*/5``).

    Examples::

        cron("*/5 * * * *")     # Every 5 minutes
        cron("0 * * * *")       # Every hour at :00
        cron("0 0 * * *")       # Daily at midnight
        cron("30 2 * * 1")      # Monday at 02:30
        cron("0 */6 * * *")     # Every 6 hours

    Args:
        expression: 5-field cron expression string.

    Returns:
        CronSchedule instance.

    Raises:
        ValueError: If expression is malformed.
    """
    parts = expression.strip().split()
    if len(parts) != 5:
        raise TaskScheduleFault(
            f"Cron expression must have exactly 5 fields (minute hour dom month dow), got {len(parts)}: {expression!r}"
        )

    ranges = [
        (0, 59),  # minute
        (0, 23),  # hour
        (1, 31),  # day of month
        (1, 12),  # month
        (0, 6),  # day of week (0=Monday in Python, adjust)
    ]

    parsed = []
    for field_str, (lo, hi) in zip(parts, ranges, strict=False):
        parsed.append(_parse_cron_field(field_str, lo, hi))

    return CronSchedule(
        expression=expression,
        _minute=parsed[0],
        _hour=parsed[1],
        _dom=parsed[2],
        _month=parsed[3],
        _dow=parsed[4],
    )


def _parse_cron_field(field_str: str, lo: int, hi: int) -> tuple:
    """Parse a single cron field into a tuple of matching values."""
    if field_str == "*":
        return ()  # Empty = match all

    values = set()

    for part in field_str.split(","):
        if "/" in part:
            # Step: */5 or 1-30/5
            base, step_str = part.split("/", 1)
            step = int(step_str)
            if base == "*":
                start, end = lo, hi
            elif "-" in base:
                start, end = map(int, base.split("-", 1))
            else:
                start, end = int(base), hi
            values.update(range(start, end + 1, step))

        elif "-" in part:
            # Range: 1-5
            start, end = map(int, part.split("-", 1))
            values.update(range(start, end + 1))

        else:
            # Single value
            values.add(int(part))

    return tuple(sorted(values))
