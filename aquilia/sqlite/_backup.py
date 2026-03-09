"""
Backup — Online SQLite backup API.

Provides an async interface to ``sqlite3.Connection.backup()``,
which is available in Python ≥ 3.7.
"""

from __future__ import annotations

import asyncio
import logging
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Optional

logger = logging.getLogger("aquilia.sqlite.backup")

__all__ = ["backup_database"]


async def backup_database(
    source_path: str,
    target_path: str,
    *,
    pages: int = -1,
    progress: Any = None,
    executor: Optional[ThreadPoolExecutor] = None,
) -> None:
    """
    Perform an online backup of a SQLite database.

    Uses ``sqlite3.Connection.backup()`` which performs a page-level
    copy.  The backup runs in a thread pool executor to avoid blocking
    the event loop.

    Args:
        source_path: Path to the source database.
        target_path: Path to the target (backup) database.
        pages: Number of pages to copy per step.  -1 copies all at once.
        progress: Optional callback ``(status, remaining, total)`` called
                  after each step.
        executor: Thread pool executor.  If None, the default is used.

    Raises:
        sqlite3.Error: If the backup fails.
    """
    loop = asyncio.get_running_loop()

    def _do_backup() -> None:
        source = sqlite3.connect(source_path)
        target = sqlite3.connect(target_path)
        try:
            source.backup(target, pages=pages, progress=progress)
        finally:
            target.close()
            source.close()

    await loop.run_in_executor(executor, _do_backup)
    logger.info("Backup complete: %s → %s", source_path, target_path)
