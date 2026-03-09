"""
PRAGMA Builder — Build and apply SQLite PRAGMA statements from config.

All PRAGMA values are validated before formatting into SQL to prevent
injection.  User-supplied strings are checked against allowlists.
"""

from __future__ import annotations

import sqlite3
import logging
from typing import Sequence

from ._config import SqlitePoolConfig, JOURNAL_MODES, SYNC_MODES, TEMP_STORE_MODES

logger = logging.getLogger("aquilia.sqlite.pragma")

__all__ = ["build_pragmas", "apply_pragmas"]


def build_pragmas(
    config: SqlitePoolConfig,
    *,
    readonly: bool = False,
) -> list[str]:
    """
    Build a list of PRAGMA SQL strings for a connection.

    Args:
        config: Pool configuration with PRAGMA knobs.
        readonly: If True, appends ``PRAGMA query_only = 1``.

    Returns:
        List of PRAGMA SQL strings ready for execution.
    """
    pragmas: list[str] = []

    # journal_mode — only for writer (readers inherit WAL from the file)
    if not readonly:
        jm = config.journal_mode.upper()
        assert jm in JOURNAL_MODES  # validated in config
        pragmas.append(f"PRAGMA journal_mode = {jm}")

    # busy_timeout
    pragmas.append(f"PRAGMA busy_timeout = {int(config.busy_timeout)}")

    # foreign_keys
    fk = "ON" if config.foreign_keys else "OFF"
    pragmas.append(f"PRAGMA foreign_keys = {fk}")

    # synchronous
    sm = config.synchronous.upper()
    assert sm in SYNC_MODES
    pragmas.append(f"PRAGMA synchronous = {sm}")

    # cache_size
    pragmas.append(f"PRAGMA cache_size = {int(config.cache_size)}")

    # mmap_size
    pragmas.append(f"PRAGMA mmap_size = {int(config.mmap_size)}")

    # temp_store
    ts = config.temp_store.upper()
    assert ts in TEMP_STORE_MODES
    pragmas.append(f"PRAGMA temp_store = {ts}")

    # wal_autocheckpoint — only for writer
    if not readonly:
        pragmas.append(f"PRAGMA wal_autocheckpoint = {int(config.wal_autocheckpoint)}")

    # query_only — for reader connections
    if readonly:
        pragmas.append("PRAGMA query_only = 1")

    return pragmas


def apply_pragmas(
    conn: sqlite3.Connection,
    pragmas: Sequence[str],
) -> None:
    """
    Execute a sequence of PRAGMA statements on a raw ``sqlite3.Connection``.

    This runs synchronously and is intended to be called from a worker thread.

    Args:
        conn: An open sqlite3 connection.
        pragmas: PRAGMA SQL strings (from :func:`build_pragmas`).
    """
    for pragma in pragmas:
        try:
            conn.execute(pragma)
            logger.debug("Applied: %s", pragma)
        except sqlite3.Error as exc:
            logger.warning("Failed to apply %s: %s", pragma, exc)
