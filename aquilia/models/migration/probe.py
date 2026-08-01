"""
Aquilia migrations -- pre-connection readiness probes.

Answers "is this database ready to serve?" *before* the application opens a
connection, so a startup guard can print instructions rather than crash on the
first query.

Why not just connect
--------------------
Opening a SQLite database creates its ``-wal`` and ``-shm`` sidecar files, and
does so even when the connection is immediately closed. A startup *check* that
does that has changed the thing it was checking: a developer who ran a check
against a database that did not exist now has one that half-exists, and
``aq db migrate`` behaves differently than it would have. These probes open
SQLite read-only (``mode=ro``), which never creates a file and never writes a
journal.

For any non-SQLite backend the probe cannot answer without a real connection --
there is no file to stat -- so it reports "ready" and lets the normal connection
path surface any problem with its own error. Optimism is correct here: a false
"not ready" would block a working deployment, while a false "ready" costs only
the error the application would have raised anyway.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from aquilia.models.migration.executor import MIGRATION_TABLE
from aquilia.models.migration.serializer import revision_from_path

__all__ = ["database_exists", "migrations_applied", "sqlite_path_from_url"]


def sqlite_path_from_url(url: str) -> str:
    """Extract the filesystem path from a SQLite connection URL.

    Args:
        url: A connection URL, e.g. ``"sqlite:///var/db.sqlite3"``.

    Returns:
        The filesystem path, or ``":memory:"`` for an in-memory database.

    Example:
        >>> sqlite_path_from_url("sqlite:///app.db")
        'app.db'
    """
    for prefix in ("sqlite:///", "sqlite://"):
        if url.startswith(prefix):
            return url[len(prefix) :] or ":memory:"
    return url.replace("sqlite:", "").lstrip("/") or ":memory:"


def database_exists(db_url: str) -> bool:
    """Report whether the database exists, without creating or touching it.

    Args:
        db_url: The database URL.

    Returns:
        ``True`` when the database exists, when it is in-memory (and so exists
        by definition once connected), or when the backend is not SQLite and the
        question cannot be answered without connecting.

    Example:
        >>> database_exists("sqlite:///missing.db")
        False
    """
    if not db_url.startswith("sqlite"):
        return True

    path = sqlite_path_from_url(db_url)
    if path == ":memory:":
        return True
    return os.path.exists(path)


def migrations_applied(db_url: str, migrations_dir: str | Path = "migrations") -> bool:
    """Report whether every migration on disk has been applied.

    Reads the tracking table over a read-only connection, so no WAL or SHM file
    is created for a database the caller only meant to inspect.

    Args:
        db_url: The database URL.
        migrations_dir: Directory holding the migration files.

    Returns:
        ``True`` when nothing is pending -- including the vacuous cases: no
        migrations directory, no migration files, an in-memory database, or a
        non-SQLite backend this probe cannot inspect. ``False`` when the
        database is missing, the tracking table does not exist, or at least one
        migration on disk is unapplied.

    Example:
        >>> migrations_applied("sqlite:///app.db", "migrations")
        True
    """
    if not database_exists(db_url):
        return False
    if not db_url.startswith("sqlite"):
        return True

    path = sqlite_path_from_url(db_url)
    if path == ":memory:":
        return True

    directory = Path(migrations_dir)
    if not directory.exists():
        return True

    files = sorted(f for f in directory.glob("*.py") if not f.name.startswith("__"))
    if not files:
        return True

    try:
        connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    except sqlite3.Error:
        return False

    connection.row_factory = sqlite3.Row
    try:
        exists = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            [MIGRATION_TABLE],
        ).fetchone()
        if not exists:
            return False

        applied = {
            row["revision"] for row in connection.execute(f'SELECT "revision" FROM "{MIGRATION_TABLE}" ORDER BY "id"')
        }
        return all(revision_from_path(path_on_disk) in applied for path_on_disk in files)
    except sqlite3.Error:
        return False
    finally:
        connection.close()
