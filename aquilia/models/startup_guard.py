"""
Aquilia Safe DB Startup -- guards against implicit database creation.

Prevents the database file and tables from being auto-created when
models change at server startup. If the DB file does not exist or
there are unapplied migrations, the server must fail-start with a
yellow warning instructing the developer to run:

    aquilia makemigrations && aquilia migrate

Behavior can be overridden with the environment variable:
    AQUILIA_AUTO_MIGRATE=1

Configuration:
    db.sqlite.journal_mode  -- "wal" (default for runtime), "delete" for
                              schema-check/dry-run operations to avoid
                              creating -wal/-shm sidecar files.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger("aquilia.db.startup")

# ANSI yellow for terminal warning
_YELLOW = "\033[93m"
_RESET = "\033[0m"
_BOLD = "\033[1m"


from enum import Enum


class DatabaseState(Enum):
    """Clean state model for database startup readiness."""

    READY = "READY"
    MISSING_DATABASE = "MISSING_DATABASE"
    PENDING_MIGRATIONS = "PENDING_MIGRATIONS"
    CORRUPTED_HISTORY = "CORRUPTED_HISTORY"
    SCHEMA_MISMATCH = "SCHEMA_MISMATCH"
    UNAVAILABLE = "UNAVAILABLE"


class DatabaseNotReadyError(SystemExit):
    """
    Raised when the database is not ready at server startup (legacy/explicit check).

    This is a SystemExit subclass so the process exits with a
    non-zero code and a human-readable message.
    """

    def __init__(self, message: str):
        self.message = message
        try:
            import logging

            from aquilia.faults.domains import SchemaFault

            fault = SchemaFault(table="(startup)", reason=message)
            logging.getLogger("aquilia.models.startup_guard").warning(
                "Database not ready warning — %s [fault=%s]", message, fault.code
            )
        except Exception:
            pass
        super().__init__(1)


def get_db_state(
    db_url: str = "sqlite:///db.sqlite3",
    migrations_dir: str | Path = "migrations",
) -> DatabaseState:
    """
    Determine the detailed readiness state of the database.
    """
    from aquilia.models.migration.probe import database_exists, migrations_applied

    if not database_exists(db_url):
        return DatabaseState.MISSING_DATABASE

    mdir = Path(migrations_dir)
    has_migrations = mdir.exists() and any(mdir.glob("*.py"))
    if has_migrations and not migrations_applied(db_url, migrations_dir):
        return DatabaseState.PENDING_MIGRATIONS

    return DatabaseState.READY


def check_db_ready(
    db_url: str = "sqlite:///db.sqlite3",
    migrations_dir: str | Path = "migrations",
    *,
    auto_migrate: bool | None = None,
    auto_create: bool | None = None,
) -> bool:
    """
    Check if the database is ready for the application to start.

    Rules:
    1. If AQUILIA_AUTO_MIGRATE=1 (or auto_migrate=True), skip checks.
    2. If auto_migrate=False: inspect database state.
    3. If state is not READY: log yellow warning instructions and return False.

    Returns:
        True if the database is ready, False otherwise.
    """
    if auto_migrate is None:
        auto_migrate = os.environ.get("AQUILIA_AUTO_MIGRATE", "").strip() in ("1", "true", "yes")

    if auto_migrate:
        return True

    state = get_db_state(db_url, migrations_dir)

    if state == DatabaseState.MISSING_DATABASE:
        _warn_not_ready(
            "Database file does not exist",
            db_url=db_url,
            hint="Run the following commands to initialize database:",
        )
        return False
    elif state == DatabaseState.PENDING_MIGRATIONS:
        _warn_not_ready(
            "Unapplied migrations detected",
            db_url=db_url,
            hint="Run the following commands to apply migrations:",
        )
        return False
    elif state == DatabaseState.CORRUPTED_HISTORY:
        _warn_not_ready(
            "Migration history mismatch or corrupted",
            db_url=db_url,
            hint="Verify migration checksums using 'aq db status'",
        )
        return False

    return True


def _box_line(text: str = "", align: str = "left") -> str:
    """Format a single box line to exactly 58 inner characters (64 total width)."""
    text = text[:58]
    if align == "center":
        return f"║ {text:^58} ║"
    elif align == "right":
        return f"║ {text:>58} ║"
    else:
        return f"║ {text:<58} ║"


def _warn_not_ready(reason: str, *, db_url: str, hint: str) -> None:
    """Print a yellow warning banner (non-fatal)."""
    top = f"{_YELLOW}{_BOLD}╔" + "═" * 60 + "╗"
    sep = "╠" + "═" * 60 + "╣" + _RESET
    bot = f"{_YELLOW}╚" + "═" * 60 + f"╝{_RESET}"

    lines = [
        top,
        f"{_YELLOW}{_BOLD}" + _box_line("DATABASE NOT READY", align="center"),
        sep,
        _YELLOW + _box_line(reason),
        _box_line(),
        _box_line(f"Database: {db_url}"),
        _box_line(),
        _box_line(hint),
        _box_line(),
        _box_line("  $ aq db makemigrations"),
        _box_line("  $ aq db migrate"),
        _box_line(),
        _box_line("Or set AQUILIA_AUTO_MIGRATE=1 to auto-create on startup."),
        bot,
    ]
    print("\n" + "\n".join(lines), file=sys.stderr)


def _fail_start(reason: str, *, db_url: str, hint: str) -> None:
    """Print a yellow warning and raise DatabaseNotReadyError (legacy)."""
    _warn_not_ready(reason, db_url=db_url, hint=hint)
    raise DatabaseNotReadyError(reason)
