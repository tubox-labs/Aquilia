"""
SQLite Metrics — Observable counters for the native SQLite module.

Follows the same pattern as ``aquilia.filesystem._metrics``:
lock-free counters mutated only from the async event loop thread.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["SqliteMetrics"]


@dataclass
class SqliteMetrics:
    """
    Aggregated metrics for the SQLite connection pool.

    All counters are monotonically increasing.  Pool gauges may
    go up and down.  Thread-safety: mutated only from the event
    loop thread — no locks needed.
    """

    # ── Pool gauges ──────────────────────────────────────────────────
    pool_size: int = 0
    """Current number of open connections (readers + writer)."""

    pool_idle: int = 0
    """Connections idle in the pool right now."""

    pool_waiting: int = 0
    """Tasks currently waiting for a connection."""

    # ── Query counters ───────────────────────────────────────────────
    queries_total: int = 0
    """Total queries executed."""

    query_errors_total: int = 0
    """Total queries that raised an error."""

    query_rows_total: int = 0
    """Total rows returned across all fetch queries."""

    # ── Latency (cumulative nanoseconds) ─────────────────────────────
    query_latency_ns: int = 0
    """Cumulative query latency (nanoseconds)."""

    # ── Transaction counters ─────────────────────────────────────────
    transactions_total: int = 0
    """Total transactions started."""

    transaction_commits: int = 0
    """Total transactions committed."""

    transaction_rollbacks: int = 0
    """Total transactions rolled back."""

    transaction_latency_ns: int = 0
    """Cumulative transaction latency (nanoseconds)."""

    # ── Statement cache ──────────────────────────────────────────────
    cache_hits: int = 0
    """Total statement cache hits (across all connections)."""

    cache_misses: int = 0
    """Total statement cache misses (across all connections)."""

    # ── Helpers ──────────────────────────────────────────────────────

    def record_query(self, elapsed_ns: int, row_count: int = 0) -> None:
        """Record a successful query execution."""
        self.queries_total += 1
        self.query_latency_ns += elapsed_ns
        self.query_rows_total += row_count

    def record_query_error(self) -> None:
        """Record a failed query."""
        self.queries_total += 1
        self.query_errors_total += 1

    def record_transaction(self, elapsed_ns: int, *, committed: bool) -> None:
        """Record a completed transaction."""
        self.transactions_total += 1
        self.transaction_latency_ns += elapsed_ns
        if committed:
            self.transaction_commits += 1
        else:
            self.transaction_rollbacks += 1

    def record_cache_access(self, *, hit: bool) -> None:
        """Record a statement cache access."""
        if hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1

    def snapshot(self) -> dict[str, int | float]:
        """Return a JSON-friendly snapshot of all metrics."""
        return {
            "pool_size": self.pool_size,
            "pool_idle": self.pool_idle,
            "pool_waiting": self.pool_waiting,
            "queries_total": self.queries_total,
            "query_errors_total": self.query_errors_total,
            "query_rows_total": self.query_rows_total,
            "query_latency_ns": self.query_latency_ns,
            "transactions_total": self.transactions_total,
            "transaction_commits": self.transaction_commits,
            "transaction_rollbacks": self.transaction_rollbacks,
            "transaction_latency_ns": self.transaction_latency_ns,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
        }

    def reset(self) -> None:
        """Reset all counters to zero (useful in tests)."""
        self.pool_size = 0
        self.pool_idle = 0
        self.pool_waiting = 0
        self.queries_total = 0
        self.query_errors_total = 0
        self.query_rows_total = 0
        self.query_latency_ns = 0
        self.transactions_total = 0
        self.transaction_commits = 0
        self.transaction_rollbacks = 0
        self.transaction_latency_ns = 0
        self.cache_hits = 0
        self.cache_misses = 0
