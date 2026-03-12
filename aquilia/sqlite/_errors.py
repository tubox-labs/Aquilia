"""
SQLite Errors — Exception hierarchy and fault mapping.

Maps ``sqlite3`` exceptions to Aquilia fault types and provides a clean
error hierarchy for the native SQLite module.

Fault mapping:
    sqlite3.OperationalError  → DatabaseConnectionFault / QueryFault
    sqlite3.IntegrityError    → QueryFault (retryable=False)
    sqlite3.ProgrammingError  → QueryFault (retryable=False)
    sqlite3.DatabaseError     → QueryFault (retryable=True)
"""

from __future__ import annotations

import sqlite3

from aquilia.faults.core import Fault
from aquilia.faults.domains import (
    DatabaseConnectionFault,
    QueryFault,
    SchemaFault,
)

__all__ = [
    "SqliteError",
    "SqliteConnectionError",
    "PoolExhaustedError",
    "SqliteQueryError",
    "SqliteIntegrityError",
    "SqliteSchemaError",
    "SqliteTimeoutError",
    "SqliteSecurityError",
    "map_sqlite_error",
]


# ═══════════════════════════════════════════════════════════════════════════
# Exception Hierarchy
# ═══════════════════════════════════════════════════════════════════════════


class SqliteError(Exception):
    """Base exception for all aquilia.sqlite errors."""

    def __init__(self, message: str = "", *, original: Exception | None = None) -> None:
        self.original = original
        super().__init__(message)


class SqliteConnectionError(SqliteError):
    """Connection open / close failed."""

    pass


class PoolExhaustedError(SqliteError):
    """All connections in the pool are busy and the wait timed out."""

    pass


class SqliteQueryError(SqliteError):
    """Query execution failed."""

    pass


class SqliteIntegrityError(SqliteQueryError):
    """Integrity constraint violated (UNIQUE, FK, CHECK, NOT NULL)."""

    pass


class SqliteSchemaError(SqliteError):
    """Schema-level error (missing table, missing column)."""

    pass


class SqliteTimeoutError(SqliteError):
    """Query or connection timed out."""

    pass


class SqliteSecurityError(SqliteError):
    """Security violation (path traversal, sandbox escape)."""

    pass


# ═══════════════════════════════════════════════════════════════════════════
# Fault Mapping
# ═══════════════════════════════════════════════════════════════════════════

_SCHEMA_PATTERNS = (
    "no such table",
    "no such column",
    "table already exists",
    "no such index",
    "duplicate column name",
)

_CONNECTION_PATTERNS = (
    "database is locked",
    "unable to open",
    "disk I/O error",
    "database disk image is malformed",
    "attempt to write a readonly database",
)


def map_sqlite_error(
    exc: Exception,
    *,
    operation: str = "",
    sql: str = "",
    url: str = "",
) -> SqliteError:
    """
    Convert a ``sqlite3`` exception to an ``aquilia.sqlite`` exception.

    Also logs the fault mapping for observability.

    Args:
        exc: The original sqlite3 exception.
        operation: Logical operation name (e.g. "execute", "connect").
        sql: The SQL text that triggered the error (for diagnostics).
        url: Database URL (for connection faults).

    Returns:
        An appropriate ``SqliteError`` subclass instance.
    """
    msg = str(exc).lower()

    # ── Schema faults ────────────────────────────────────────────────
    if isinstance(exc, sqlite3.OperationalError):
        for pattern in _SCHEMA_PATTERNS:
            if pattern in msg:
                return SqliteSchemaError(
                    f"Schema error during {operation}: {exc}",
                    original=exc,
                )

    # ── Connection faults ────────────────────────────────────────────
    if isinstance(exc, sqlite3.OperationalError):
        for pattern in _CONNECTION_PATTERNS:
            if pattern in msg:
                return SqliteConnectionError(
                    f"Connection error during {operation}: {exc}",
                    original=exc,
                )

    # ── Integrity faults ─────────────────────────────────────────────
    if isinstance(exc, sqlite3.IntegrityError):
        return SqliteIntegrityError(
            f"Integrity error during {operation}: {exc}",
            original=exc,
        )

    # ── Programming faults ───────────────────────────────────────────
    if isinstance(exc, sqlite3.ProgrammingError):
        return SqliteQueryError(
            f"Programming error during {operation}: {exc}",
            original=exc,
        )

    # ── Generic database error ───────────────────────────────────────
    if isinstance(exc, sqlite3.DatabaseError):
        return SqliteQueryError(
            f"Database error during {operation}: {exc}",
            original=exc,
        )

    # ── Fallback ─────────────────────────────────────────────────────
    return SqliteError(
        f"Unexpected error during {operation}: {exc}",
        original=exc,
    )


def to_aquilia_fault(
    exc: SqliteError,
    *,
    url: str = "",
    model: str = "<sqlite>",
    operation: str = "",
) -> Fault:
    """
    Convert an ``aquilia.sqlite`` exception into an Aquilia fault object.

    This bridges the module-local error hierarchy with the framework-wide
    fault system used by ``AquiliaDatabase``.

    Args:
        exc: The aquilia.sqlite exception.
        url: Database URL for connection fault metadata.
        model: Model name for query fault metadata.
        operation: Operation name for fault metadata.

    Returns:
        An Aquilia ``Fault`` subclass (``DatabaseConnectionFault``,
        ``QueryFault``, or ``SchemaFault``).
    """
    reason = str(exc)

    if isinstance(exc, SqliteConnectionError):
        return DatabaseConnectionFault(url=url, reason=reason)

    if isinstance(exc, SqliteSchemaError):
        return SchemaFault(table=model, reason=reason)

    if isinstance(exc, (SqliteQueryError, SqliteIntegrityError)):
        return QueryFault(
            model=model,
            operation=operation,
            reason=reason,
        )

    if isinstance(exc, SqliteTimeoutError):
        return QueryFault(
            model=model,
            operation=operation,
            reason=f"Timeout: {reason}",
        )

    # Default to QueryFault for anything else
    return QueryFault(
        model=model,
        operation=operation,
        reason=reason,
    )
