"""
Filesystem Metrics — Lightweight operation counters and latency tracking.

Provides observability into the filesystem module's behavior without
external dependencies.  Metrics are exposed via the ``FileSystemMetrics``
singleton which can be read by health checks, admin endpoints, or
exported to monitoring systems.

Design notes:
    - Lock-free counters (single-threaded async mutation)
    - ``time.monotonic()`` for latency (not wall-clock)
    - Optional (disabled via ``FileSystemConfig.enable_metrics=False``)
"""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class FileSystemMetrics:
    """
    Aggregated filesystem operation metrics.

    All counters are monotonically increasing.  Latency values are
    cumulative (divide by count for average).

    Thread-safety: This class is only mutated from the async event
    loop thread, so no locks are needed.
    """

    # ── Counters ──────────────────────────────────────────────────────────

    reads: int = 0
    """Total number of read operations completed."""

    writes: int = 0
    """Total number of write operations completed."""

    deletes: int = 0
    """Total number of delete operations completed."""

    copies: int = 0
    """Total number of copy operations completed."""

    moves: int = 0
    """Total number of move/rename operations completed."""

    stats: int = 0
    """Total number of stat/exists operations completed."""

    directory_ops: int = 0
    """Total number of directory operations (list, mkdir, rmdir, etc.)."""

    errors: int = 0
    """Total number of failed operations."""

    # ── Byte counters ────────────────────────────────────────────────────

    bytes_read: int = 0
    """Total bytes read from disk."""

    bytes_written: int = 0
    """Total bytes written to disk."""

    # ── Latency (cumulative, nanoseconds) ────────────────────────────────

    read_latency_ns: int = 0
    """Cumulative read latency (nanoseconds)."""

    write_latency_ns: int = 0
    """Cumulative write latency (nanoseconds)."""

    # ── Pool metrics ─────────────────────────────────────────────────────

    pool_submissions: int = 0
    """Total number of operations submitted to the thread pool."""

    pool_peak_active: int = 0
    """Peak number of concurrently active pool operations."""

    # ── Helpers ──────────────────────────────────────────────────────────

    def record_read(self, bytes_count: int, elapsed_ns: int) -> None:
        """Record a completed read operation."""
        self.reads += 1
        self.bytes_read += bytes_count
        self.read_latency_ns += elapsed_ns

    def record_write(self, bytes_count: int, elapsed_ns: int) -> None:
        """Record a completed write operation."""
        self.writes += 1
        self.bytes_written += bytes_count
        self.write_latency_ns += elapsed_ns

    def record_error(self) -> None:
        """Record a failed operation."""
        self.errors += 1

    def to_dict(self) -> dict[str, int]:
        """Export metrics as a dictionary."""
        return {
            "reads": self.reads,
            "writes": self.writes,
            "deletes": self.deletes,
            "copies": self.copies,
            "moves": self.moves,
            "stats": self.stats,
            "directory_ops": self.directory_ops,
            "errors": self.errors,
            "bytes_read": self.bytes_read,
            "bytes_written": self.bytes_written,
            "read_latency_ns": self.read_latency_ns,
            "write_latency_ns": self.write_latency_ns,
            "pool_submissions": self.pool_submissions,
            "pool_peak_active": self.pool_peak_active,
            "avg_read_latency_us": (self.read_latency_ns // (self.reads * 1000) if self.reads > 0 else 0),
            "avg_write_latency_us": (self.write_latency_ns // (self.writes * 1000) if self.writes > 0 else 0),
        }

    def reset(self) -> None:
        """Reset all counters to zero.  Useful for testing."""
        self.reads = 0
        self.writes = 0
        self.deletes = 0
        self.copies = 0
        self.moves = 0
        self.stats = 0
        self.directory_ops = 0
        self.errors = 0
        self.bytes_read = 0
        self.bytes_written = 0
        self.read_latency_ns = 0
        self.write_latency_ns = 0
        self.pool_submissions = 0
        self.pool_peak_active = 0


class _Timer:
    """
    High-resolution timer context manager for measuring operation latency.

    Usage::

        timer = _Timer()
        with timer:
            do_something()
        print(timer.elapsed_ns)
    """

    __slots__ = ("_start", "elapsed_ns")

    def __init__(self) -> None:
        self._start: int = 0
        self.elapsed_ns: int = 0

    def __enter__(self) -> _Timer:
        self._start = time.monotonic_ns()
        return self

    def __exit__(self, *exc: object) -> None:
        self.elapsed_ns = time.monotonic_ns() - self._start
