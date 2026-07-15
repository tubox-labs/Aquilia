"""
aquilia.devplatform.diagnostics.sql — N+1 query detector and EXPLAIN runner.

Integrates with aquilia.inspector.trace via current_trace() ContextVar.
Intercepts SQL records from the inspector trace's DATABASE spans and:
  1. Normalizes SQL strings to detect repetitive queries (N+1 pattern)
  2. Detects duplicate queries (same SQL + same params = redundant fetch)
  3. Runs EXPLAIN / EXPLAIN ANALYZE for queries exceeding the slow threshold
  4. Appends analysis results to the active RequestRecord via RuntimeStateStore
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from aquilia.devplatform.core._base import SingletonMixin
from aquilia.devplatform.faults import InspectorFault, report_fault

logger = logging.getLogger("aquilia.devplatform.diagnostics.sql")


# ── SQL normalisation ──────────────────────────────────────────────────────────

_PARAM_RE = re.compile(r"'[^']*'|\b\d+\b|\$\d+|\?|\:[a-z_]\w*", re.IGNORECASE)
_WHITESPACE_RE = re.compile(r"\s+")


def normalize_sql(sql: str) -> str:
    """Strip literals, collapse whitespace, lowercase → stable normalised form."""
    sql = _PARAM_RE.sub("?", sql)
    sql = _WHITESPACE_RE.sub(" ", sql).strip().lower()
    return sql


def sql_hash(normalized: str) -> str:
    return hashlib.sha1(normalized.encode()).hexdigest()[:16]


# ── N+1 warning record ─────────────────────────────────────────────────────────


@dataclass
class N1Warning:
    normalized_sql: str
    hash: str
    execution_count: int
    total_duration_ms: float
    sample_params: list[Any] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "n_plus_one",
            "normalized_sql": self.normalized_sql,
            "hash": self.hash,
            "execution_count": self.execution_count,
            "total_duration_ms": self.total_duration_ms,
            "sample_params": self.sample_params[:3],
        }


@dataclass
class DuplicateQueryWarning:
    sql: str
    params_repr: str
    execution_count: int
    total_duration_ms: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "duplicate_query",
            "sql": self.sql,
            "params_repr": self.params_repr,
            "execution_count": self.execution_count,
            "total_duration_ms": self.total_duration_ms,
        }


# ── Per-request SQL accumulator ─────────────────────────────────────────────────


@dataclass
class SQLQueryRecord:
    sql: str
    normalized: str
    normalized_hash: str
    params: Any
    duration_ms: float


class RequestSQLAccumulator:
    """
    Collects SQL records for a single request and runs analysis at the end.

    Not thread-safe — used per-request from a single coroutine context.
    """

    def __init__(self, n_plus_one_threshold: int = 2) -> None:
        self._records: list[SQLQueryRecord] = []
        self._n_plus_one_threshold = n_plus_one_threshold

    def record(self, sql: str, params: Any, duration_ms: float) -> None:
        normalized = normalize_sql(sql)
        self._records.append(
            SQLQueryRecord(
                sql=sql,
                normalized=normalized,
                normalized_hash=sql_hash(normalized),
                params=params,
                duration_ms=duration_ms,
            )
        )

    def analyze(self) -> tuple[list[N1Warning], list[DuplicateQueryWarning]]:
        """Return N+1 and duplicate query warnings for this request."""
        # N+1: group by normalized hash
        by_hash: dict[str, list[SQLQueryRecord]] = defaultdict(list)
        for rec in self._records:
            by_hash[rec.normalized_hash].append(rec)

        n1_warnings: list[N1Warning] = []
        for h, recs in by_hash.items():
            if len(recs) >= self._n_plus_one_threshold:
                n1_warnings.append(
                    N1Warning(
                        normalized_sql=recs[0].normalized,
                        hash=h,
                        execution_count=len(recs),
                        total_duration_ms=sum(r.duration_ms for r in recs),
                        sample_params=[r.params for r in recs[:3]],
                    )
                )

        # Duplicate: group by (normalized_hash, params_repr)
        by_exact: dict[tuple[str, str], list[SQLQueryRecord]] = defaultdict(list)
        for rec in self._records:
            params_repr = repr(rec.params)
            by_exact[(rec.normalized_hash, params_repr)].append(rec)

        dup_warnings: list[DuplicateQueryWarning] = []
        for (h, params_repr), recs in by_exact.items():
            if len(recs) > 1:
                dup_warnings.append(
                    DuplicateQueryWarning(
                        sql=recs[0].sql,
                        params_repr=params_repr,
                        execution_count=len(recs),
                        total_duration_ms=sum(r.duration_ms for r in recs),
                    )
                )

        return n1_warnings, dup_warnings


# ── SQLQueryAnalyzer ────────────────────────────────────────────────────────────


class SQLQueryAnalyzer(SingletonMixin):
    """
    Global SQL analysis engine.

    Singleton — obtain via SQLQueryAnalyzer.get_instance().

    Wired from ``aquilia.devplatform.core.protocol.ASGIHTTPConnection.execute()``,
    which reads completed ``Lane.DATABASE`` spans off the request's own trace
    (populated by ``aquilia.db.engine.AquiliaDatabase._notify_inspector()``)
    after each request completes and feeds them into ``on_query()``. This
    keeps ``aquilia.db`` free of any dependency on the optional devplatform
    package — devplatform observes, core never imports it.
    Runs EXPLAIN plans asynchronously to avoid blocking request paths.
    """

    def __init__(self, slow_threshold_ms: float = 50.0, n_plus_one_threshold: int = 2) -> None:
        self._slow_threshold_ms = slow_threshold_ms
        self._n_plus_one_threshold = n_plus_one_threshold
        self._explain_queue: asyncio.Queue[tuple[str, Any, Any]] | None = None

    def on_query(
        self,
        sql: str,
        params: Any,
        duration_ms: float,
        db_engine: Any | None = None,
    ) -> None:
        """
        Called by the database engine inspector hook for each executed query.
        Queues slow queries for async EXPLAIN.
        """
        # Add to current request trace if active
        try:
            from aquilia.inspector.trace import current_trace

            trace = current_trace()
            if trace is not None:
                normalized = normalize_sql(sql)
                import time

                from aquilia.inspector.trace import Lane, SpanStatus

                offset_ms = (time.monotonic() - trace.started_monotonic) * 1000.0
                trace.add_span(
                    Lane.DATABASE,
                    label=sql[:120],
                    start_offset_ms=max(0.0, offset_ms - duration_ms),
                    duration_ms=duration_ms,
                    status=SpanStatus.WARNING if duration_ms >= self._slow_threshold_ms else SpanStatus.OK,
                    detail={"normalized_hash": sql_hash(normalized)},
                )
        except ImportError:
            pass
        except Exception as exc:
            report_fault(InspectorFault(f"SQL span emission failed: {exc}"))

        # Enqueue EXPLAIN for slow queries
        if duration_ms >= self._slow_threshold_ms and db_engine is not None:
            if self._explain_queue is not None:
                try:
                    self._explain_queue.put_nowait((sql, params, db_engine))
                except asyncio.QueueFull:
                    pass

    async def start_explain_worker(self) -> None:
        """Start background EXPLAIN worker. Call from async context."""
        self._explain_queue = asyncio.Queue(maxsize=100)
        asyncio.create_task(self._explain_loop(), name="adp-sql-explain")

    async def _explain_loop(self) -> None:
        """Background worker that runs EXPLAIN for queued slow queries."""
        while True:
            try:
                sql, params, db_engine = await self._explain_queue.get()
                try:
                    explain_sql = f"EXPLAIN {sql}"
                    result = await db_engine.fetch_all(explain_sql, params)
                    logger.debug("EXPLAIN for slow query:\n%s\nPlan: %s", sql, result)
                except Exception as exc:
                    logger.debug("EXPLAIN failed: %s", exc)
                finally:
                    self._explain_queue.task_done()
            except Exception:
                await asyncio.sleep(0.1)
