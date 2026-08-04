"""Inline-execution eligibility: decide which statements may run on the event loop.

Why this exists
---------------
``AsyncConnection`` dispatches every statement to a ``ThreadPoolExecutor``. For a
write or a large scan that is correct -- the work is long enough that blocking the
event loop would hurt more than the hop costs. For an indexed point lookup it is
indefensible: the hop measures ~27us against ~1.5us of actual SQLite work, so
the framework spends 18x the query's cost avoiding a 1.5us block.

This module owns the decision, and only the safe half of it. A statement is
eligible only when SQLite's own query planner says every table access is an index
seek. That is a much stronger guarantee than pattern-matching the SQL text, which
cannot tell ``WHERE id = ?`` on an indexed column from the same clause on an
unindexed one.

The risk, stated plainly
------------------------
Inline execution blocks the event loop for the statement's duration. That is only
acceptable because the plan proves the statement is O(1). A plan can stop being
true -- a table grows, an index is dropped, ``ANALYZE`` changes the planner's
mind. Two independent backstops:

1. **Compile time (here).** Anything the planner does not describe as pure index
   access is rejected, as is anything non-SELECT, anything multi-statement, and
   anything whose plan could not be obtained.
2. **Run time (:func:`record_duration`).** A statement that was admitted but
   measured slower than ``inline_max_duration_ms`` is demoted permanently. The
   plan being wrong costs one slow request, not a stalled server.

``inline_fast_queries=False`` disables the whole mechanism.
"""

from __future__ import annotations

import re
import sqlite3
from typing import Any, Final

__all__ = ["InlinePolicy"]

# sqlite3 reports the required binding count in its ProgrammingError text:
#   "Incorrect number of bindings supplied. The current statement uses 1, ..."
# Reading it from there is more reliable than counting '?' in the SQL, which
# would also count question marks inside string literals and comments.
_BINDING_COUNT_RE: Final[re.Pattern[str]] = re.compile(r"statement uses (\d+)")


def _placeholder_count(raw: sqlite3.Connection, sql: str) -> int | None:
    """Return how many positional parameters ``sql`` requires.

    Args:
        raw: Connection used to prepare the statement.
        sql: Statement text.

    Returns:
        The parameter count, or None when it could not be determined (named
        parameters, or an unparseable statement).
    """
    try:
        raw.execute(f"EXPLAIN QUERY PLAN {sql}")
    except sqlite3.ProgrammingError as exc:
        match = _BINDING_COUNT_RE.search(str(exc))
        if match:
            return int(match.group(1))
        return None
    except sqlite3.Error:
        return None
    return 0


# Plan operations that guarantee bounded work. SQLite's EXPLAIN QUERY PLAN emits
# a human-readable "detail" column; these are the forms that mean "index seek"
# rather than "walk the table".
#
# "SEARCH" is the seek form. "SCAN CONSTANT ROW" is a constant-only result --
# it contains the substring "SCAN" but touches no table, so it is matched here
# explicitly rather than being caught by the unsafe markers below.
_SAFE_PREFIXES: Final[tuple[str, ...]] = (
    "SEARCH",
    "SCAN CONSTANT ROW",
)

# Substrings that disqualify a plan regardless of the leading verb: a subquery or
# a temp b-tree can hide unbounded work behind a SEARCH on the outer table.
#
# A bare "SCAN <table>" needs no entry here -- it fails the safe-prefix test.
_UNSAFE_MARKERS: Final[tuple[str, ...]] = (
    "TEMP B-TREE",
    "CORRELATED",
    "SUBQUERY",
)


class InlinePolicy:
    """Per-connection cache of which statements may run inline.

    One instance per :class:`AsyncConnection`. Not thread-safe by design: a
    connection is owned by one task at a time (enforced by the pool), and the
    cache holds only immutable bools keyed by SQL text.

    Args:
        raw: The underlying sqlite3 connection, used to run the planner probe.
        enabled: When False every statement is reported ineligible and no probe
            is ever run.
        max_duration_ms: Measured runtime above which an admitted statement is
            demoted permanently.
    """

    __slots__ = ("_raw", "_enabled", "_max_duration_ms", "_eligible", "_probe_failures")

    def __init__(
        self,
        raw: sqlite3.Connection,
        *,
        enabled: bool = True,
        max_duration_ms: float = 1.0,
    ) -> None:
        self._raw = raw
        self._enabled = enabled
        self._max_duration_ms = max_duration_ms
        # SQL text -> may run inline. Bounded by the number of distinct
        # statements an application issues, which is a property of its source
        # code, not of its traffic.
        self._eligible: dict[str, bool] = {}
        self._probe_failures = 0

    @property
    def enabled(self) -> bool:
        """Whether inline execution is permitted at all on this connection."""
        return self._enabled

    def cache_size(self) -> int:
        """Number of distinct statements classified. Used by the bound test."""
        return len(self._eligible)

    def may_run_inline(self, sql: str) -> bool:
        """Report whether ``sql`` may execute on the event loop.

        The planner probe runs at most once per distinct statement; every later
        call is a dict hit.

        Args:
            sql: The statement text, exactly as it will be executed.

        Returns:
            True only when the planner proved every table access is an index
            seek.
        """
        if not self._enabled:
            return False
        cached = self._eligible.get(sql)
        if cached is not None:
            return cached
        verdict = self._probe(sql)
        self._eligible[sql] = verdict
        return verdict

    def record_duration(self, sql: str, duration_ms: float) -> None:
        """Demote a statement that ran slower than the configured ceiling.

        The planner's verdict is a prediction. This is the correction: a
        statement admitted inline that turns out to be slow is moved to the
        thread pool for the rest of the process's life. One slow request is the
        entire cost of a stale plan.

        Args:
            sql: The statement that just ran.
            duration_ms: Its measured wall-clock duration.
        """
        if duration_ms > self._max_duration_ms and self._eligible.get(sql):
            self._eligible[sql] = False

    def _probe(self, sql: str) -> bool:
        """Ask SQLite whether ``sql`` is a pure index-seek SELECT.

        Args:
            sql: Statement text.

        Returns:
            True when eligible. Any doubt -- a write, multiple statements, a
            plan containing a scan, or a probe that raised -- returns False.
        """
        stripped = sql.lstrip()
        # Only reads. A write must serialise through the writer connection and
        # may block on the WAL, neither of which belongs on the event loop.
        if stripped[:6].upper() != "SELECT":
            return False
        # `EXPLAIN QUERY PLAN` describes the first statement only, so a batch
        # could smuggle unplanned work past the probe. Reject anything with an
        # inner semicolon (trailing one is fine).
        if ";" in stripped.rstrip().rstrip(";"):
            return False

        try:
            rows = self._plan(sql)
        except sqlite3.Error:
            # Cannot plan it -> cannot vouch for it.
            self._probe_failures += 1
            return False

        if not rows:
            return False

        for row in rows:
            detail = row["detail"] if isinstance(row, sqlite3.Row) else row[-1]
            if not isinstance(detail, str):
                return False
            upper = detail.upper()
            if not upper.startswith(_SAFE_PREFIXES):
                return False
            if any(marker in upper for marker in _UNSAFE_MARKERS):
                return False
        return True

    def _plan(self, sql: str) -> list[Any]:
        """Return the planner's rows for ``sql``.

        ``EXPLAIN QUERY PLAN`` still type-checks bindings, so a parameterised
        statement raises "Incorrect number of bindings supplied" unless we supply
        placeholders. The planner does not look at the *values* -- it only needs
        the right count -- so NULLs are sufficient and cannot affect the plan.

        Args:
            sql: Statement text.

        Returns:
            The planner rows.

        Raises:
            sqlite3.Error: The statement could not be prepared or planned.
        """
        explain = f"EXPLAIN QUERY PLAN {sql}"
        try:
            return self._raw.execute(explain).fetchall()
        except sqlite3.ProgrammingError:
            # Parameterised: retry with the right number of NULL placeholders.
            count = _placeholder_count(self._raw, sql)
            if count is None:
                raise
            return self._raw.execute(explain, (None,) * count).fetchall()
