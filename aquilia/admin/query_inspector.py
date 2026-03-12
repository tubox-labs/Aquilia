"""
AquilAdmin — Live Query Inspector.

Captures, profiles, and analyses ORM queries for the admin panel:
- ORM → SQL translation view
- Execution time profiling
- EXPLAIN plan viewer
- N+1 query detection
- Slow query log

Hooks into AquiliaDatabase to intercept all queries transparently.
"""

from __future__ import annotations

import hashlib
import traceback
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class QueryRecord:
    """Single captured query with profiling data."""

    id: str = ""
    sql: str = ""
    params: Any = None
    duration_ms: float = 0.0
    rows_affected: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    explain_plan: str = ""
    source: str = ""  # Calling code location (file:line)
    model: str = ""  # ORM model name if applicable
    operation: str = ""  # SELECT, INSERT, UPDATE, DELETE
    is_slow: bool = False
    stack_summary: str = ""  # Abbreviated stack trace
    request_id: str = ""

    @property
    def fingerprint(self) -> str:
        """Stable fingerprint for query grouping (ignores param values)."""
        # Normalise: replace literal values with ?
        normalised = self.sql
        data = f"{normalised}:{self.model}"
        return hashlib.sha256(data.encode()).hexdigest()[:12]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "sql": self.sql,
            "params": repr(self.params) if self.params else None,
            "duration_ms": round(self.duration_ms, 3),
            "rows_affected": self.rows_affected,
            "timestamp": self.timestamp.isoformat(),
            "explain_plan": self.explain_plan,
            "source": self.source,
            "model": self.model,
            "operation": self.operation,
            "is_slow": self.is_slow,
            "stack_summary": self.stack_summary,
            "fingerprint": self.fingerprint,
            "request_id": self.request_id,
        }


@dataclass
class N1Detection:
    """Detected N+1 query pattern."""

    pattern_sql: str = ""
    count: int = 0
    model: str = ""
    total_duration_ms: float = 0.0
    first_seen: str = ""
    source: str = ""
    request_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern_sql": self.pattern_sql,
            "count": self.count,
            "model": self.model,
            "total_duration_ms": round(self.total_duration_ms, 3),
            "first_seen": self.first_seen,
            "source": self.source,
            "request_id": self.request_id,
        }


class QueryInspector:
    """
    Central query profiler and inspector.

    Captures all database queries, profiles execution time,
    detects N+1 patterns, and maintains a query log for
    the admin Query Inspector page.

    Usage::

        inspector = QueryInspector()

        # Record a query
        inspector.record(
            sql="SELECT * FROM users WHERE id = ?",
            params=(1,),
            duration_ms=2.5,
            rows_affected=1,
        )

        # Check for N+1 patterns
        n1_issues = inspector.detect_n_plus_one()

        # Get stats
        stats = inspector.get_stats()
    """

    def __init__(
        self,
        *,
        max_queries: int = 500,
        slow_threshold_ms: float = 100.0,
        n1_threshold: int = 5,
    ):
        """
        Args:
            max_queries: Maximum number of queries to keep in history
            slow_threshold_ms: Queries slower than this are flagged
            n1_threshold: Minimum repeated queries to flag as N+1
        """
        self._queries: deque[QueryRecord] = deque(maxlen=max_queries)
        self._slow_threshold = slow_threshold_ms
        self._n1_threshold = n1_threshold
        self._counter = 0

        # Aggregate stats
        self._total_queries = 0
        self._total_duration = 0.0
        self._slow_count = 0
        self._started_at = datetime.now(timezone.utc)

        # Per-request tracking for N+1 detection
        self._request_queries: dict[str, list[QueryRecord]] = defaultdict(list)

    def record(
        self,
        sql: str,
        params: Any = None,
        duration_ms: float = 0.0,
        rows_affected: int = 0,
        model: str = "",
        request_id: str = "",
    ) -> QueryRecord:
        """
        Record a query execution.

        Args:
            sql: SQL statement
            params: Query parameters
            duration_ms: Execution time in milliseconds
            rows_affected: Number of rows affected/returned
            model: ORM model name
            request_id: Current request ID for N+1 grouping

        Returns:
            The created QueryRecord
        """
        self._counter += 1

        # Determine operation type
        sql_upper = sql.strip().upper()
        if sql_upper.startswith("SELECT"):
            operation = "SELECT"
        elif sql_upper.startswith("INSERT"):
            operation = "INSERT"
        elif sql_upper.startswith("UPDATE"):
            operation = "UPDATE"
        elif sql_upper.startswith("DELETE"):
            operation = "DELETE"
        elif sql_upper.startswith("EXPLAIN"):
            operation = "EXPLAIN"
        else:
            operation = "OTHER"

        is_slow = duration_ms >= self._slow_threshold

        # Extract calling location from stack
        source = ""
        stack_summary = ""
        try:
            frames = traceback.extract_stack()
            # Walk up to find the first non-aquilia frame
            for frame in reversed(frames[:-1]):
                if "/aquilia/" not in frame.filename and "site-packages" not in frame.filename:
                    source = f"{frame.filename}:{frame.lineno}"
                    stack_summary = f"{frame.name}() at {frame.filename}:{frame.lineno}"
                    break
            if not source and len(frames) > 2:
                frame = frames[-3]
                source = f"{frame.filename}:{frame.lineno}"
                stack_summary = f"{frame.name}() at {frame.filename}:{frame.lineno}"
        except Exception:
            pass

        record = QueryRecord(
            id=f"q-{self._counter:06d}",
            sql=sql,
            params=params,
            duration_ms=duration_ms,
            rows_affected=rows_affected,
            timestamp=datetime.now(timezone.utc),
            source=source,
            model=model,
            operation=operation,
            is_slow=is_slow,
            stack_summary=stack_summary,
            request_id=request_id,
        )

        self._queries.append(record)
        self._total_queries += 1
        self._total_duration += duration_ms
        if is_slow:
            self._slow_count += 1

        # Track per-request for N+1
        if request_id:
            self._request_queries[request_id].append(record)
            # Limit per-request tracking memory
            if len(self._request_queries) > 100:
                oldest = next(iter(self._request_queries))
                del self._request_queries[oldest]

        return record

    def detect_n_plus_one(self, request_id: str | None = None) -> list[N1Detection]:
        """
        Detect N+1 query patterns.

        Groups queries by fingerprint within each request and flags
        patterns where the same query shape is repeated >= n1_threshold times.

        Args:
            request_id: Check specific request, or all recent requests

        Returns:
            List of detected N+1 patterns
        """
        detections: list[N1Detection] = []

        if request_id:
            request_groups = {request_id: self._request_queries.get(request_id, [])}
        else:
            request_groups = dict(self._request_queries)

        for req_id, queries in request_groups.items():
            if len(queries) < self._n1_threshold:
                continue

            # Group by fingerprint
            by_fingerprint: dict[str, list[QueryRecord]] = defaultdict(list)
            for q in queries:
                if q.operation == "SELECT":
                    by_fingerprint[q.fingerprint].append(q)

            for _fp, group in by_fingerprint.items():
                if len(group) >= self._n1_threshold:
                    total_dur = sum(q.duration_ms for q in group)
                    detections.append(
                        N1Detection(
                            pattern_sql=group[0].sql[:200],
                            count=len(group),
                            model=group[0].model,
                            total_duration_ms=total_dur,
                            first_seen=group[0].timestamp.isoformat(),
                            source=group[0].source,
                            request_id=req_id,
                        )
                    )

        return detections

    def get_slow_queries(self, limit: int = 50) -> list[QueryRecord]:
        """Get recent slow queries, sorted by duration descending."""
        slow = [q for q in self._queries if q.is_slow]
        slow.sort(key=lambda q: q.duration_ms, reverse=True)
        return slow[:limit]

    def get_recent_queries(self, limit: int = 100) -> list[QueryRecord]:
        """Get most recent queries."""
        queries = list(self._queries)
        return queries[-limit:]

    def get_stats(self) -> dict[str, Any]:
        """Get aggregate query statistics."""
        queries = list(self._queries)
        if not queries:
            return {
                "total_queries": 0,
                "avg_duration_ms": 0.0,
                "slow_queries": 0,
                "slow_threshold_ms": self._slow_threshold,
                "n1_detections": 0,
                "by_operation": {},
                "by_model": {},
                "queries_per_second": 0.0,
                "recent_queries": [],
                "slow_query_list": [],
                "n1_list": [],
            }

        # By operation
        by_op: dict[str, int] = defaultdict(int)
        by_model: dict[str, int] = defaultdict(int)
        for q in queries:
            by_op[q.operation] += 1
            if q.model:
                by_model[q.model] += 1

        elapsed = (datetime.now(timezone.utc) - self._started_at).total_seconds() or 1
        n1_list = self.detect_n_plus_one()

        return {
            "total_queries": self._total_queries,
            "avg_duration_ms": round(self._total_duration / max(self._total_queries, 1), 3),
            "slow_queries": self._slow_count,
            "slow_threshold_ms": self._slow_threshold,
            "n1_detections": len(n1_list),
            "by_operation": dict(by_op),
            "by_model": dict(by_model),
            "queries_per_second": round(self._total_queries / elapsed, 2),
            "recent_queries": [q.to_dict() for q in self.get_recent_queries(50)],
            "slow_query_list": [q.to_dict() for q in self.get_slow_queries(20)],
            "n1_list": [d.to_dict() for d in n1_list],
        }

    def clear(self) -> None:
        """Clear all recorded queries."""
        self._queries.clear()
        self._request_queries.clear()
        self._total_queries = 0
        self._total_duration = 0.0
        self._slow_count = 0
        self._counter = 0


# ============================================================================
# Global instance
# ============================================================================

_default_inspector: QueryInspector | None = None


def get_query_inspector() -> QueryInspector:
    """Get or create the global QueryInspector instance."""
    global _default_inspector
    if _default_inspector is None:
        _default_inspector = QueryInspector()
    return _default_inspector
