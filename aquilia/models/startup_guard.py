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


class DatabaseNotReadyError(SystemExit):
    """
    Raised when the database is not ready at server startup.

    This is a SystemExit subclass so the process exits with a
    non-zero code and a human-readable message.  It also inherits
    from ``SchemaFault`` so it flows through the Aquilia fault pipeline
    for logging and auditing before terminating.
    """

    def __init__(self, message: str):
        self.message = message
        # Log through fault system before exiting
        try:
            from ..faults.domains import SchemaFault

            fault = SchemaFault(table="(startup)", reason=message)
            import logging

            logging.getLogger("aquilia.models.startup_guard").error(
                "Database not ready — %s [fault=%s]", message, fault.code
            )
        except Exception:
            pass
        super().__init__(1)


def check_db_ready(
    db_url: str = "sqlite:///db.sqlite3",
    migrations_dir: str | Path = "migrations",
    *,
    auto_migrate: bool | None = None,
) -> bool:
    """
    Check if the database is ready for the application to start.

    This function MUST be called during server startup (before
    any ModelRegistry.create_tables() call).

    Rules:
    1. If AQUILIA_AUTO_MIGRATE=1 (or auto_migrate=True), skip checks.
    2. For SQLite: if the DB file does not exist, warn and return False.
    3. If there are unapplied migrations, warn and return False.

    Args:
        db_url: Database connection URL
        migrations_dir: Path to migrations directory
        auto_migrate: Override for AQUILIA_AUTO_MIGRATE env var

    Returns:
        True if the database is ready, False otherwise.
    """
    from .migration_runner import check_db_exists, check_migrations_applied

    # Check auto-migrate override
    if auto_migrate is None:
        auto_migrate = os.environ.get("AQUILIA_AUTO_MIGRATE", "").strip() in ("1", "true", "yes")

    if auto_migrate:
        return True

    # Check 1: Does the database file exist?
    if not check_db_exists(db_url):
        _warn_not_ready(
            "Database file does not exist",
            db_url=db_url,
            hint="Run the following commands to initialize database:",
        )
        return False

    # Check 2: Are all migrations applied?
    mdir = Path(migrations_dir)
    if mdir.exists() and any(mdir.glob("*.py")) and not check_migrations_applied(db_url, migrations_dir):
        _warn_not_ready(
            "Unapplied migrations detected",
            db_url=db_url,
            hint="Run the following commands to apply migrations:",
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
