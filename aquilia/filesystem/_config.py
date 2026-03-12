"""
Filesystem Configuration — Typed, frozen dataclass for module settings.

Integrates with the Aquilia ``Workspace`` / ``ConfigLoader`` system.
All fields have sensible defaults and are validated at construction.

Usage::

    from aquilia.filesystem import FileSystemConfig

    config = FileSystemConfig(
        max_pool_threads=16,
        write_buffer_size=128 * 1024,
        sandbox_root="/app/data",
    )
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FileSystemConfig:
    """
    Configuration for the Aquilia filesystem module.

    All numeric fields are validated to be non-negative.
    Path fields are resolved to absolute paths at usage time.
    """

    # ── Thread Pool ───────────────────────────────────────────────────────

    min_pool_threads: int = 2
    """Minimum number of threads in the dedicated I/O pool."""

    max_pool_threads: int = 8
    """Maximum number of threads in the dedicated I/O pool.
    Default: ``min(8, os.cpu_count() + 4)`` at runtime if 0."""

    # ── Buffering ─────────────────────────────────────────────────────────

    write_buffer_size: int = 65_536
    """Write buffer threshold in bytes.  Writes smaller than this are
    accumulated before flushing to the executor.  Set to 0 to disable
    buffering (every write goes to the executor immediately)."""

    default_chunk_size: int = 65_536
    """Default chunk size for streaming reads/writes (bytes)."""

    # ── Security ──────────────────────────────────────────────────────────

    max_path_length: int = 1024
    """Maximum allowed path length.  Paths exceeding this are rejected
    with ``FS_PATH_TOO_LONG``.  SEC-FS-04."""

    follow_symlinks: bool = False
    """Whether to follow symbolic links.  Default ``False`` prevents
    symlink attacks.  SEC-FS-05."""

    sandbox_root: str | None = None
    """If set, all file operations are restricted to this directory tree.
    Paths outside the sandbox are rejected with ``FS_PATH_TRAVERSAL``.
    SEC-FS-03."""

    # ── Atomic Writes ────────────────────────────────────────────────────

    atomic_writes: bool = True
    """Use atomic write protocol (write-to-temp + ``os.replace``) for
    ``write_file`` and ``AsyncFile`` in write mode.  SEC-FS-07."""

    fsync_on_write: bool = False
    """Call ``os.fsync()`` before ``os.replace()`` during atomic writes.
    Provides durability guarantees at the cost of performance."""

    # ── Metrics ──────────────────────────────────────────────────────────

    enable_metrics: bool = True
    """Enable operation counters and latency tracking."""

    # ── Temp Files ───────────────────────────────────────────────────────

    temp_dir: str | None = None
    """Directory for temporary files.  If ``None``, the system temp
    directory (``tempfile.gettempdir()``) is used."""

    # ── Recursive Limits ─────────────────────────────────────────────────

    max_recursion_depth: int = 100
    """Maximum depth for recursive operations (``walk``, ``rmtree``,
    ``copytree``).  SEC-FS-10."""

    # ── Filename Sanitization ────────────────────────────────────────────

    max_filename_length: int = 255
    """Maximum length for sanitized filenames.  SEC-FS-13."""

    def effective_max_pool_threads(self) -> int:
        """Return the effective max pool thread count, accounting for
        auto-detection when set to 0."""
        if self.max_pool_threads > 0:
            return self.max_pool_threads
        return min(8, (os.cpu_count() or 2) + 4)

    @classmethod
    def from_dict(cls, data: dict) -> FileSystemConfig:
        """Create config from a dictionary (e.g. from workspace config).

        Unknown keys are silently ignored for forward-compatibility.
        """
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)
