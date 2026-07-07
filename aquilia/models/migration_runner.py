"""
Aquilia Migration Runner -- executes DSL and raw-SQL migrations.

Compiles DSL operations to backend SQL, runs migrations transactionally
where possible, and records applied migrations in ``aquilia_migrations``.

Features:
- DSL migration support (operations list)
- Legacy raw-SQL migration support (upgrade/downgrade functions)
- Transactional execution (per-migration)
- --fake flag (mark as applied without running)
- --plan flag (dry-run SQL preview)
- Safe SQLite probing (no WAL/SHM creation)
"""

from __future__ import annotations

import hashlib
import importlib.util
import inspect
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..db.engine import AquiliaDatabase
from ..faults.domains import MigrationFault
from .migration_dsl import Migration

logger = logging.getLogger("aquilia.models.migration_runner")

# Name of the tracking table this runner creates and reads in the target database.
MIGRATION_TABLE = "aquilia_migrations"


@dataclass
class MigrationRecord:
    """A single applied-migration record, as read from the ``aquilia_migrations`` table.

    Attributes:
        revision: The migration's timestamp-based revision ID.
        slug: The human-readable slug portion of the migration filename.
        checksum: SHA-256 (truncated to 16 hex chars) of the migration file's
            contents at the time it was applied, used by ``verify_checksums``
            to detect post-apply edits. May be an empty string for very old
            rows recorded before checksum tracking existed.
        applied_at: Timestamp string of when the migration was applied, as
            returned by the database driver (format is driver/dialect-dependent).
    """

    revision: str
    slug: str
    checksum: str
    applied_at: str | None = None


class MigrationRunner:
    """
    Applies and tracks DSL migrations against a live ``AquiliaDatabase``.

    This is the primary, actively-maintained migration runner (paired with
    ``migration_dsl.py`` and ``migration_gen.py``). It supports both new DSL
    migrations (files exposing a module-level ``operations`` list) and
    legacy raw-SQL migrations (files exposing ``upgrade``/``downgrade``
    functions, as produced by the older ``migrations.py`` system) so that
    both migration styles can coexist in the same ``migrations/`` directory
    during a transition period.

    Usage:
        runner = MigrationRunner(db, "migrations/")
        await runner.migrate()              # Apply all pending
        await runner.migrate(fake=True)     # Mark applied without executing
        stmts = await runner.plan()         # Preview SQL
        await runner.migrate(target="rev")  # Rollback to revision
    """

    def __init__(
        self,
        db: AquiliaDatabase,
        migrations_dir: str | Path = "migrations",
        *,
        dialect: str = "sqlite",
    ):
        """
        Args:
            db: Connected ``AquiliaDatabase`` instance to run migrations against.
            migrations_dir: Directory containing migration ``.py`` files,
                sorted and applied by filename order.
            dialect: SQL dialect used to compile DSL operations (``"sqlite"``,
                ``"postgresql"``, ``"mysql"``, ``"oracle"``). Should match
                ``db``'s actual backend.
        """
        self.db = db
        self.migrations_dir = Path(migrations_dir)
        self.dialect = dialect

    async def ensure_tracking_table(self) -> None:
        """Create the ``aquilia_migrations`` tracking table if it doesn't exist.

        Called at the start of every public method that reads or writes
        migration state, so callers never need to invoke this directly.
        The primary-key column definition is dialect-specific (``SERIAL``
        on PostgreSQL, ``AUTO_INCREMENT`` on MySQL, ``GENERATED ALWAYS AS
        IDENTITY`` on Oracle, ``AUTOINCREMENT`` on SQLite/other), everything
        else is dialect-neutral.
        """
        if self.dialect == "postgresql":
            pk_def = '"id" SERIAL PRIMARY KEY'
        elif self.dialect == "mysql":
            pk_def = '"id" INTEGER PRIMARY KEY AUTO_INCREMENT'
        elif self.dialect == "oracle":
            pk_def = '"id" NUMBER(10) GENERATED ALWAYS AS IDENTITY PRIMARY KEY'
        else:
            pk_def = '"id" INTEGER PRIMARY KEY AUTOINCREMENT'

        sql = f"""
        CREATE TABLE IF NOT EXISTS "{MIGRATION_TABLE}" (
            {pk_def},
            "revision" VARCHAR(50) NOT NULL UNIQUE,
            "slug" VARCHAR(200) NOT NULL,
            "checksum" VARCHAR(64),
            "applied_at" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
        await self.db.execute(sql)

    async def get_applied(self) -> list[str]:
        """Get list of applied revision IDs, ordered by application time."""
        await self.ensure_tracking_table()
        rows = await self.db.fetch_all(f'SELECT "revision" FROM "{MIGRATION_TABLE}" ORDER BY "id"')
        return [r["revision"] for r in rows]

    async def get_applied_records(self) -> list[MigrationRecord]:
        """Get list of applied migration records, ordered by application time."""
        await self.ensure_tracking_table()
        rows = await self.db.fetch_all(
            f'SELECT "revision", "slug", "checksum", "applied_at" FROM "{MIGRATION_TABLE}" ORDER BY "id"'
        )
        return [
            MigrationRecord(
                revision=r["revision"],
                slug=r["slug"],
                checksum=r.get("checksum") or "",
                applied_at=r.get("applied_at"),
            )
            for r in rows
        ]

    async def get_pending(self) -> list[Path]:
        """Get migration files that haven't been applied yet."""
        applied = set(await self.get_applied())
        pending: list[Path] = []

        if not self.migrations_dir.exists():
            return pending

        for path in sorted(self.migrations_dir.glob("*.py")):
            if path.name.startswith("__"):
                continue
            rev = _extract_revision(path)
            if rev and rev not in applied:
                pending.append(path)

        return pending

    async def status(self) -> dict[str, Any]:
        """Get migration status -- applied, pending, and total counts.

        Returns:
            Dict with keys: ``applied`` (list of applied revision IDs),
            ``pending`` (list of pending migration file stems),
            ``last_applied`` (last applied revision, or ``None``),
            ``applied_count``, ``pending_count``, ``total``.
        """
        applied = await self.get_applied()
        pending = await self.get_pending()
        return {
            "applied": applied,
            "pending": [p.stem for p in pending],
            "last_applied": applied[-1] if applied else None,
            "applied_count": len(applied),
            "pending_count": len(pending),
            "total": len(applied) + len(pending),
        }

    async def show_status(self) -> str:
        """Return a human-readable status string."""
        info = await self.status()
        lines = [
            f"Migration Status ({self.migrations_dir})",
            f"  Applied: {info['applied_count']}",
            f"  Pending: {info['pending_count']}",
            f"  Total:   {info['total']}",
        ]
        if info["last_applied"]:
            lines.append(f"  Last applied: {info['last_applied']}")
        if info["pending"]:
            lines.append("  Pending migrations:")
            for name in info["pending"]:
                lines.append(f"    - {name}")
        return "\n".join(lines)

    async def plan(self, target: str | None = None) -> list[str]:
        """
        Preview pending migrations without executing them (``--plan`` / dry-run).

        For each pending migration file (in application order), emits a
        ``-- Migration: <revision> (<filename>)`` header followed by either
        its compiled-forward SQL statements (DSL migrations) or a
        ``-- (Legacy: runs upgrade() from ...)`` placeholder (legacy
        migrations, whose ``upgrade()`` body executes arbitrary Python and
        can't be statically previewed).

        Args:
            target: Currently unused -- accepted for interface symmetry
                with ``migrate()``/``sqlmigrate()`` but ``plan()`` always
                previews the full set of pending (forward) migrations.

        Returns:
            A flat list of SQL/comment lines suitable for printing to the
            console or a file.
        """
        statements: list[str] = []
        pending = await self.get_pending()

        for path in pending:
            rev = _extract_revision(path) or path.stem
            statements.append(f"-- Migration: {rev} ({path.name})")
            module = _load_migration_module(path, rev)

            # Check for DSL migration
            if hasattr(module, "operations"):
                migration_obj = _build_migration_from_module(module)
                for sql in migration_obj.compile_upgrade(self.dialect):
                    statements.append(sql)
            elif hasattr(module, "upgrade"):
                statements.append(f"-- (Legacy: runs upgrade() from {path.name})")

        return statements

    async def sqlmigrate(self, revision: str) -> list[str]:
        """
        Get the forward SQL for a single migration, by revision (``aq db sqlmigrate``).

        Unlike ``plan()``, this targets one specific migration (applied or
        not) and returns its actual SQL rather than a summary. For DSL
        migrations this is the compiled ``operations`` list; for legacy
        migrations it falls back to best-effort regex extraction of
        ``execute(...)`` calls from the file's source (see
        ``_extract_sql_from_source``), since legacy ``upgrade()`` functions
        aren't statically compilable to SQL.

        Args:
            revision: Revision ID (or unique filename prefix) to look up.

        Returns:
            List of SQL statement strings for that migration.

        Raises:
            MigrationFault: If no migration file matches ``revision``.
        """
        path = self._find_migration_file(revision)
        if not path:
            raise MigrationFault(
                migration=revision,
                reason=f"Migration file not found for revision '{revision}'",
            )

        module = _load_migration_module(path, revision)

        if hasattr(module, "operations"):
            migration_obj = _build_migration_from_module(module)
            return migration_obj.compile_upgrade(self.dialect)
        else:
            # Legacy -- try to extract SQL from source
            return _extract_sql_from_source(path)

    async def migrate(
        self,
        *,
        target: str | None = None,
        fake: bool = False,
        database: str | None = None,
    ) -> list[str]:
        """
        Apply all pending migrations.

        Args:
            target: Target revision for rollback (None = forward all)
            fake: If True, mark as applied without executing SQL
            database: Database alias (for multi-db, currently unused)

        Returns:
            List of applied revision IDs
        """
        from .signals import post_migrate, pre_migrate

        await self.ensure_tracking_table()

        if target is not None:
            return await self._rollback_to(target, fake=fake)

        pending = await self.get_pending()
        applied: list[str] = []

        # Signal: pre_migrate
        await pre_migrate.send(sender=self.__class__, db=self.db)

        for path in pending:
            await self._apply_migration(path, fake=fake)
            rev = _extract_revision(path) or path.stem
            applied.append(rev)

        # Signal: post_migrate
        await post_migrate.send(sender=self.__class__, db=self.db)

        return applied

    async def _apply_migration(self, path: Path, *, fake: bool = False) -> None:
        """Apply a single migration file and record it as applied.

        Dispatches to ``_execute_dsl_migration`` for DSL migrations
        (modules exposing ``operations``) or runs the legacy ``upgrade()``
        function directly otherwise (sync or async). If neither is present,
        logs a warning and records the migration as applied without running
        anything. When ``fake`` is ``True``, execution is skipped entirely
        but the migration is still recorded in ``aquilia_migrations`` --
        this is what lets ``--fake`` mark migrations as applied without
        touching the schema (e.g. when the schema was already created by
        other means).

        Args:
            path: Path to the migration file.
            fake: If ``True``, skip execution but still record as applied.

        Raises:
            MigrationFault: If a legacy ``upgrade()`` function raises.
        """
        rev = _extract_revision(path) or path.stem
        slug = _extract_slug(path)
        checksum = _file_checksum(path)

        module = _load_migration_module(path, rev)

        if not fake:
            if hasattr(module, "operations"):
                # DSL migration
                migration_obj = _build_migration_from_module(module)
                await self._execute_dsl_migration(migration_obj)
            elif hasattr(module, "upgrade"):
                # Legacy raw-SQL migration
                upgrade_fn = module.upgrade
                try:
                    if inspect.iscoroutinefunction(upgrade_fn):
                        await upgrade_fn(self.db)
                    else:
                        upgrade_fn(self.db)
                except MigrationFault:
                    raise
                except Exception as exc:
                    raise MigrationFault(
                        migration=rev,
                        reason=f"Upgrade failed: {exc}",
                    ) from exc
            else:
                logger.warning(f"Migration {rev} has no operations or upgrade(): skipping execution")

        # Record migration
        await self.db.execute(
            f'INSERT INTO "{MIGRATION_TABLE}" ("revision", "slug", "checksum") VALUES (?, ?, ?)',
            [rev, slug, checksum],
        )

    async def _execute_dsl_migration(self, migration: Migration) -> None:
        """Execute a DSL migration's SQL and Python operations inside one transaction.

        Runs all compiled SQL statements (skipping ``--`` comments) followed
        by all ``RunPython`` callables (sync or async), all within a single
        ``self.db.transaction()`` block so the migration applies atomically
        where the backend supports transactional DDL.

        MySQL-specific tolerance: error 1061 (duplicate key name) is
        swallowed during index creation, since tables may already have been
        created directly via ``create_tables()`` before this migration ran
        (e.g. during initial app bootstrap), leaving indexes that the
        migration also tries to create.

        Args:
            migration: The ``Migration`` to execute.

        Raises:
            MigrationFault: Wraps any non-``MigrationFault`` exception raised
                during SQL execution or Python-op execution, tagged with
                ``migration.revision``.
        """
        stmts = migration.compile_upgrade(self.dialect)
        python_ops = migration.get_python_ops()

        try:
            async with self.db.transaction():
                for sql in stmts:
                    if sql.startswith("--"):
                        continue  # Skip comments
                    try:
                        await self.db.execute(sql)
                    except Exception as idx_exc:
                        # MySQL error 1061: duplicate key name — index already
                        # exists (e.g. tables were created by ``create_tables``
                        # before the migration was recorded).  Skip silently.
                        cause = getattr(idx_exc, "__cause__", idx_exc)
                        if self.dialect == "mysql" and getattr(cause, "args", (None,))[0] == 1061:
                            continue
                        raise

                for py_op in python_ops:
                    if py_op.forward:
                        if inspect.iscoroutinefunction(py_op.forward):
                            await py_op.forward(self.db)
                        else:
                            py_op.forward(self.db)
        except MigrationFault:
            raise
        except Exception as exc:
            raise MigrationFault(
                migration=migration.revision,
                reason=f"DSL migration failed: {exc}",
            ) from exc

    async def _rollback_to(self, target: str, *, fake: bool = False) -> list[str]:
        """Roll back all applied migrations after ``target``, in reverse order.

        Each migration to roll back is downgraded via its DSL
        ``compile_downgrade`` (inside a transaction, tolerating MySQL error
        codes 1061/1091 -- duplicate key / index doesn't exist -- the same
        way forward execution tolerates 1061) or its legacy ``downgrade()``
        function, then removed from the ``aquilia_migrations`` tracking
        table regardless of ``fake``.

        Args:
            target: Revision to roll back to (exclusive -- migrations after
                this one are undone; ``target`` itself stays applied), or
                the special value ``"zero"`` to roll back everything.
            fake: If ``True``, skip running downgrade SQL/functions but
                still remove the tracking rows.

        Returns:
            List of revision IDs that were rolled back, in the order they
            were undone (newest first).

        Raises:
            MigrationFault: If ``target`` isn't a currently-applied
                revision, or if a downgrade step fails.
        """
        applied = await self.get_applied()
        if target == "zero":
            to_rollback = list(reversed(applied))
        else:
            if target not in applied:
                raise MigrationFault(
                    migration=target,
                    reason=f"Target revision '{target}' not in applied migrations",
                )

            target_idx = applied.index(target)
            to_rollback = list(reversed(applied[target_idx + 1 :]))

        rolled_back: list[str] = []
        for rev in to_rollback:
            path = self._find_migration_file(rev)

            if not fake and path:
                module = _load_migration_module(path, rev)
                if hasattr(module, "operations"):
                    migration_obj = _build_migration_from_module(module)
                    stmts = migration_obj.compile_downgrade(self.dialect)
                    try:
                        async with self.db.transaction():
                            for sql in stmts:
                                if sql.startswith("--"):
                                    continue
                                try:
                                    await self.db.execute(sql)
                                except Exception as idx_exc:
                                    # MySQL 1091: Can't DROP index; check that
                                    # it exists.  Skip silently during rollback.
                                    cause = getattr(idx_exc, "__cause__", idx_exc)
                                    code = getattr(cause, "args", (None,))[0]
                                    if self.dialect == "mysql" and code in (1061, 1091):
                                        continue
                                    raise
                    except Exception as exc:
                        raise MigrationFault(migration=rev, reason=f"Rollback failed: {exc}") from exc
                elif hasattr(module, "downgrade"):
                    downgrade_fn = module.downgrade
                    try:
                        if inspect.iscoroutinefunction(downgrade_fn):
                            await downgrade_fn(self.db)
                        else:
                            downgrade_fn(self.db)
                    except Exception as exc:
                        raise MigrationFault(migration=rev, reason=f"Rollback failed: {exc}") from exc

            # Remove from tracking
            await self.db.execute(
                f'DELETE FROM "{MIGRATION_TABLE}" WHERE "revision" = ?',
                [rev],
            )
            rolled_back.append(rev)

        return rolled_back

    def _find_migration_file(self, revision: str) -> Path | None:
        """Find the migration file whose name starts with ``revision``.

        Args:
            revision: Full or partial revision/filename prefix (e.g.
                ``"20260217_210454"``).

        Returns:
            The first matching ``Path``, or ``None`` if the migrations
            directory doesn't exist or no file matches.
        """
        if not self.migrations_dir.exists():
            return None
        candidates = list(self.migrations_dir.glob(f"{revision}*.py"))
        return candidates[0] if candidates else None

    async def verify_checksums(self) -> list[dict[str, str]]:
        """Verify that applied migration files haven't been tampered with since being applied.

        Recomputes each applied migration's SHA-256 checksum and compares it
        against the value stored at apply time. Migrations recorded without
        a checksum (pre-checksum-tracking rows) are skipped rather than
        flagged.

        Returns:
            A list of ``{"revision": ..., "reason": ...}`` dicts, one per
            mismatch -- either ``"File not found on disk"`` or
            ``"File modified since applied"``. Empty list means everything
            checks out.
        """
        await self.ensure_tracking_table()
        rows = await self.db.fetch_all(f'SELECT "revision", "checksum" FROM "{MIGRATION_TABLE}" ORDER BY "id"')
        mismatches: list[dict[str, str]] = []
        for row in rows:
            rev = row["revision"]
            stored = row.get("checksum")
            if not stored:
                continue
            path = self._find_migration_file(rev)
            if not path:
                mismatches.append({"revision": rev, "reason": "File not found on disk"})
                continue
            current = _file_checksum(path)
            if current != stored:
                mismatches.append({"revision": rev, "reason": "File modified since applied"})
        return mismatches


# ── Safe SQLite probing ─────────────────────────────────────────────────────


def check_db_exists(db_url: str) -> bool:
    """
    Check if a SQLite database file exists WITHOUT creating WAL/SHM files.

    Uses os.path.exists() for file-based SQLite databases.
    Returns True for :memory: and non-SQLite databases.
    """
    if not db_url.startswith("sqlite"):
        return True  # Non-SQLite databases are assumed to exist

    path = _extract_sqlite_path(db_url)
    if path == ":memory:":
        return True

    return os.path.exists(path)


def check_migrations_applied(db_url: str, migrations_dir: str | Path = "migrations") -> bool:
    """
    Check if there are unapplied migrations WITHOUT creating WAL/SHM.

    For SQLite, uses file:...?mode=ro URI to read-only probe.
    For non-SQLite databases (PostgreSQL, MySQL, Oracle), the synchronous
    startup guard cannot probe the async adapter, so we return True and
    let the async MigrationRunner handle tracking at runtime.

    Returns True if all migrations are applied (or no migrations exist).
    """

    if not check_db_exists(db_url):
        return False

    # Non-SQLite databases: the sync startup guard cannot probe async
    # adapters.  The MigrationRunner (async) already tracks state via
    # the aquilia_migrations table during `aq db migrate`.
    if not db_url.startswith("sqlite"):
        return True

    path = _extract_sqlite_path(db_url)
    if path == ":memory:":
        return True

    mdir = Path(migrations_dir)
    if not mdir.exists():
        return True  # No migrations directory = nothing to apply

    migration_files = sorted(f for f in mdir.glob("*.py") if not f.name.startswith("__"))
    if not migration_files:
        return True

    # Read-only probe using sqlite3 (synchronous, not via pool) to avoid WAL
    try:
        import sqlite3

        # Use mode=ro to prevent WAL/SHM creation
        ro_uri = f"file:{path}?mode=ro"
        conn = sqlite3.connect(ro_uri, uri=True)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                [MIGRATION_TABLE],
            )
            if not cursor.fetchone():
                conn.close()
                return False  # No migration table → not migrated

            cursor = conn.execute(f'SELECT "revision" FROM "{MIGRATION_TABLE}" ORDER BY "id"')
            applied = {row["revision"] for row in cursor.fetchall()}

            for path in migration_files:
                rev = _extract_revision(path)
                if rev and rev not in applied:
                    conn.close()
                    return False
            conn.close()
            return True
        except sqlite3.OperationalError:
            conn.close()
            return False
    except Exception:
        return False


def _extract_sqlite_path(url: str) -> str:
    """Extract the file path from a ``sqlite:///`` or ``sqlite://`` URL.

    Args:
        url: A SQLite connection URL, e.g. ``"sqlite:///db.sqlite3"``.

    Returns:
        The bare filesystem path, or ``":memory:"`` if the URL has no path
        component (in-memory database).
    """
    for prefix in ("sqlite:///", "sqlite://"):
        if url.startswith(prefix):
            return url[len(prefix) :] or ":memory:"
    return url.replace("sqlite:", "").lstrip("/") or ":memory:"


# ── Helper functions ─────────────────────────────────────────────────────────


def _extract_revision(path: Path) -> str | None:
    """Extract the revision ID from a migration filename.

    Filenames follow the ``YYYYMMDD_HHMMSS_slug.py`` convention; the
    revision is the first two underscore-separated segments (date and time).

    Args:
        path: Migration file path.

    Returns:
        The revision string (e.g. ``"20260217_210454"``), or ``None`` if the
        filename stem has fewer than two ``_``-separated segments.
    """
    parts = path.stem.split("_", 2)
    if len(parts) >= 2:
        return f"{parts[0]}_{parts[1]}"
    return None


def _extract_slug(path: Path) -> str:
    """Extract the slug portion of a migration filename (everything after the revision).

    Args:
        path: Migration file path.

    Returns:
        The slug (e.g. ``"create_users_table"`` from
        ``"20260217_210454_create_users_table.py"``), or the full filename
        stem if it doesn't have a third ``_``-separated segment.
    """
    parts = path.stem.split("_", 2)
    if len(parts) >= 3:
        return parts[2]
    return path.stem


def _file_checksum(path: Path) -> str:
    """Compute a truncated SHA-256 checksum of a migration file's contents.

    Args:
        path: Migration file path.

    Returns:
        The first 16 hex characters of the file's SHA-256 digest -- short
        enough to store compactly, long enough to make accidental
        collisions between distinct migration files effectively impossible.
    """
    content = path.read_bytes()
    return hashlib.sha256(content).hexdigest()[:16]


def _load_migration_module(path: Path, rev: str) -> Any:
    """Load a migration file as a standalone Python module (not via normal import).

    Uses ``importlib.util`` to execute the file directly by path (migration
    files live outside any package, so they can't be imported by dotted
    name). The resulting module is not registered in ``sys.modules``.

    Args:
        path: Path to the migration ``.py`` file.
        rev: Revision ID, used only to build a synthetic module name
            (``f"migration_{rev}"``) for error messages/introspection.

    Returns:
        The executed module object, exposing whatever top-level names the
        migration file defines (``operations``, ``Meta``, ``upgrade``,
        ``downgrade``, etc.).

    Raises:
        MigrationFault: If the module spec can't be created, or if
            executing the module's top-level code raises.
    """
    spec = importlib.util.spec_from_file_location(f"migration_{rev}", path)
    if not spec or not spec.loader:
        raise MigrationFault(
            migration=rev,
            reason=f"Cannot load migration module: {path}",
        )
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        raise MigrationFault(
            migration=rev,
            reason=f"Failed to load migration: {exc}",
        ) from exc
    return module


def _build_migration_from_module(module: Any) -> Migration:
    """Build a ``Migration`` instance from a loaded DSL migration module.

    Reads ``revision``/``slug``/``models`` from the module's ``Meta`` class
    if present, falling back to same-named module-level attributes for
    compatibility with older/hand-written migration files that don't use a
    ``Meta`` class. ``dependencies`` is only read from ``Meta`` (defaults to
    ``[]``). ``operations`` is always read as a module-level list.

    Args:
        module: A module object as returned by ``_load_migration_module``.

    Returns:
        A ``Migration`` populated from the module's metadata and operations.
    """
    meta = getattr(module, "Meta", None)
    revision = getattr(meta, "revision", "") if meta else getattr(module, "revision", "")
    slug = getattr(meta, "slug", "") if meta else getattr(module, "slug", "")
    models = getattr(meta, "models", []) if meta else getattr(module, "models", [])
    deps = getattr(meta, "dependencies", []) if meta else []
    operations = getattr(module, "operations", [])

    return Migration(
        revision=revision,
        slug=slug,
        models=models,
        dependencies=deps,
        operations=operations,
    )


def _extract_sql_from_source(path: Path) -> list[str]:
    """Best-effort extraction of SQL text from a legacy migration's source.

    Legacy migrations (``migrations.py``-style, with ``upgrade()``/
    ``downgrade()`` functions) execute SQL via arbitrary ``conn.execute(...)``
    Python calls rather than a declarative list, so there's no reliable way
    to get "the SQL" without running the function. As a preview-only
    fallback for ``sqlmigrate()``, this scans the raw file text with regexes
    for ``execute(...)`` calls whose argument is a triple-double-quoted,
    triple-single-quoted, or plain single-quoted string literal, and
    returns whatever string literals they capture.

    Limitations: only recognizes the exact ``execute(...)`` call shapes
    matched by these three patterns (e.g. multi-line f-strings, variables,
    or ``execute("...")`` with plain double quotes are not captured); this
    is a readability aid for previewing legacy migrations, not a reliable
    SQL extractor.

    Args:
        path: Path to the legacy migration file.

    Returns:
        List of extracted SQL strings, in source order (may be incomplete
        or empty depending on how the migration's SQL was written).
    """
    import re

    source = path.read_text(encoding="utf-8")
    stmts: list[str] = []

    # Triple-quoted SQL
    for match in re.findall(r'execute\s*\(\s*"""(.*?)"""\s*\)', source, re.DOTALL):
        stmts.append(match.strip())
    for match in re.findall(r"execute\s*\(\s*'''(.*?)'''\s*\)", source, re.DOTALL):
        stmts.append(match.strip())
    # Single-quoted SQL
    for match in re.findall(r"execute\s*\(\s*'(.*?)'\s*\)", source, re.DOTALL):
        stmts.append(match.strip())

    return stmts
