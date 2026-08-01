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

from aquilia.tasks.faults import TaskScheduleFault


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
        │ │ │ │ ┌─────────── day of week (0-7, 0 and 7 = Sunday)
        │ │ │ │ │
        * * * * *

    Day-of-week follows the standard cron convention (``0``/``7`` = Sunday),
    not Python's :meth:`datetime.weekday` (``0`` = Monday).  ``cron()``
    normalises parsed values to ``0=Sunday`` before storing them in
    ``_dow``, and :meth:`matches` compares against ``isoweekday() % 7``.

    Created via the :func:`cron` helper — the parsed field tuples are
    populated there and should not be constructed by hand.

    Attributes:
        expression: The original 5-field cron string, kept for display.
        _minute: Matching minutes; empty tuple means "every minute".
        _hour: Matching hours; empty tuple means "every hour".
        _dom: Matching days of month; empty tuple means "every day".
        _month: Matching months; empty tuple means "every month".
        _dow: Matching days of week (0=Sunday); empty means "every day".

    Examples::

        schedule = cron("30 2 * * 1")     # Monday 02:30 UTC
        schedule.matches(datetime(2026, 7, 27, 2, 30, tzinfo=timezone.utc))
        # → True (2026-07-27 is a Monday)
    """

    expression: str
    _minute: tuple[int, ...] = field(default=(), repr=False)
    _hour: tuple[int, ...] = field(default=(), repr=False)
    _dom: tuple[int, ...] = field(default=(), repr=False)
    _month: tuple[int, ...] = field(default=(), repr=False)
    _dow: tuple[int, ...] = field(default=(), repr=False)

    @property
    def human_readable(self) -> str:
        """Human-friendly representation of the cron expression."""
        return f"cron({self.expression})"

    def matches(self, dt: datetime) -> bool:
        """
        Check if a datetime matches this cron expression.

        Day-of-week uses the standard cron convention (``0``/``7`` = Sunday),
        which differs from :meth:`datetime.weekday` (``0`` = Monday).  Parsed
        DOW values are normalised to ``0=Sunday`` at parse time, so the
        comparison here uses ``isoweekday() % 7`` (Sunday → 0, Monday → 1).
        """
        return (
            (not self._minute or dt.minute in self._minute)
            and (not self._hour or dt.hour in self._hour)
            and (not self._dom or dt.day in self._dom)
            and (not self._month or dt.month in self._month)
            and (not self._dow or (dt.isoweekday() % 7) in self._dow)
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
        TaskScheduleFault: If the total interval is ≤ 0.
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

    Day-of-week follows the standard cron convention: ``0`` **and** ``7``
    both mean Sunday, ``1`` means Monday.  This matches ``cron(8)``,
    Celery Beat and Quartz — not Python's :meth:`datetime.weekday`.

    Examples::

        cron("*/5 * * * *")     # Every 5 minutes
        cron("0 * * * *")       # Every hour at :00
        cron("0 0 * * *")       # Daily at midnight
        cron("30 2 * * 1")      # Monday at 02:30
        cron("0 0 * * 0")       # Sunday at midnight
        cron("0 */6 * * *")     # Every 6 hours

    Args:
        expression: 5-field cron expression string.

    Returns:
        CronSchedule instance.

    Raises:
        TaskScheduleFault: If the expression is malformed or a field value
            falls outside its allowed range.
    """
    parts = expression.strip().split()
    if len(parts) != 5:
        raise TaskScheduleFault(
            f"Cron expression must have exactly 5 fields (minute hour dom month dow), got {len(parts)}: {expression!r}"
        )

    ranges = [
        (0, 59, "minute"),
        (0, 23, "hour"),
        (1, 31, "day-of-month"),
        (1, 12, "month"),
        (0, 7, "day-of-week"),  # 0 and 7 both mean Sunday (cron convention)
    ]

    parsed = []
    for field_str, (lo, hi, label) in zip(parts, ranges, strict=False):
        parsed.append(_parse_cron_field(field_str, lo, hi, label, expression))

    # Normalise day-of-week to 0=Sunday..6=Saturday (7 → 0)
    dow = tuple(sorted({v % 7 for v in parsed[4]}))

    return CronSchedule(
        expression=expression,
        _minute=parsed[0],
        _hour=parsed[1],
        _dom=parsed[2],
        _month=parsed[3],
        _dow=dow,
    )


def _parse_cron_field(
    field_str: str,
    lo: int,
    hi: int,
    label: str = "field",
    expression: str = "",
) -> tuple[int, ...]:
    """
    Parse a single cron field into a tuple of matching values.

    Args:
        field_str: Raw field text (``*``, ``5``, ``1-5``, ``*/5``, ``1,3,5``).
        lo: Lowest legal value for this field.
        hi: Highest legal value for this field.
        label: Human-readable field name, used in fault messages.
        expression: Full cron expression, used in fault messages.

    Returns:
        Sorted tuple of matching values, or an empty tuple for ``*``
        (meaning "match every value").

    Raises:
        TaskScheduleFault: On non-integer tokens, a non-positive step, or
            any value outside ``[lo, hi]``.
    """
    if field_str == "*":
        return ()  # Empty = match all

    def _int(token: str) -> int:
        try:
            return int(token)
        except ValueError:
            raise TaskScheduleFault(f"Invalid {label} value {token!r} in cron expression {expression!r}") from None

    values: set[int] = set()

    for part in field_str.split(","):
        if "/" in part:
            # Step: */5 or 1-30/5
            base, step_str = part.split("/", 1)
            step = _int(step_str)
            if step <= 0:
                raise TaskScheduleFault(f"Cron {label} step must be > 0, got {step} in {expression!r}")
            if base == "*":
                start, end = lo, hi
            elif "-" in base:
                start_str, end_str = base.split("-", 1)
                start, end = _int(start_str), _int(end_str)
            else:
                start, end = _int(base), hi
            values.update(range(start, end + 1, step))

        elif "-" in part:
            # Range: 1-5
            start_str, end_str = part.split("-", 1)
            start, end = _int(start_str), _int(end_str)
            values.update(range(start, end + 1))

        else:
            values.add(_int(part))

    out_of_range = sorted(v for v in values if v < lo or v > hi)
    if out_of_range:
        raise TaskScheduleFault(
            f"Cron {label} value(s) {out_of_range} outside allowed range {lo}-{hi} in {expression!r}"
        )

    return tuple(sorted(values))
