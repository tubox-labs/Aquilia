"""
Aquilia Migration Runner -- Single execution authority for database schema operations.

MigrationRunner owns all execution responsibilities including:
- Initial schema creation and table teardown
- Transaction lifecycle and atomic rollback
- SQL compilation and operation execution via DDLExecutor
- Migration history tracking in ``aquilia_migrations``
- Dry-run planning, diagnostics, and checksum verification
- Backend-specific error handling via database adapters
"""

from __future__ import annotations

import hashlib
import importlib.util
import inspect
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..db.engine import AquiliaDatabase
from ..faults.domains import MigrationFault
from .ddl_executor import DDLExecutor, ExecutableStatement, StatementType
from .migration_planner import MigrationPlan, MigrationPlanner, MigrationStep

if TYPE_CHECKING:
    from .base import Model
    from .migration_dsl import Migration

logger = logging.getLogger("aquilia.models.migration_runner")

# Name of the tracking table created and managed by this runner in the target database.
MIGRATION_TABLE = "aquilia_migrations"


@dataclass
class MigrationRecord:
    """A single applied-migration record as read from ``aquilia_migrations``.

    Attributes:
        revision: Timestamp-based revision ID.
        slug: Human-readable slug portion of filename.
        checksum: SHA-256 (truncated) of the migration file at apply time.
        applied_at: Timestamp string of when the migration was recorded.
    """

    revision: str
    slug: str
    checksum: str
    applied_at: str | None = None


class MigrationRunner:
    """Single execution authority for all schema DDL operations and migration lifecycle.

    Usage:
        runner = MigrationRunner(db, "migrations/")
        await runner.create_initial_schema() # Execute initial schema plan
        await runner.migrate()              # Apply pending migrations
        await runner.migrate(fake=True)     # Mark applied without executing
        stmts = await runner.plan()         # Preview SQL plan
        await runner.migrate(target="rev")  # Rollback to target revision
        await runner.drop_all_tables()      # Teardown schema
    """

    def __init__(
        self,
        db: AquiliaDatabase,
        migrations_dir: str | Path = "migrations",
        *,
        dialect: str | None = None,
    ):
        """
        Args:
            db: Connected ``AquiliaDatabase`` engine to run operations against.
            migrations_dir: Path to directory containing migration files.
            dialect: SQL dialect name (defaults to ``db.dialect``).
        """
        self.db = db
        self.migrations_dir = Path(migrations_dir)
        self.dialect = dialect or getattr(db, "dialect", "sqlite")

    async def ensure_tracking_table(self) -> None:
        """Create the ``aquilia_migrations`` tracking table if it doesn't exist.

        Primary-key definition is dialect-specific; everything else is dialect-neutral.
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
        stmt = ExecutableStatement(
            sql=sql,
            statement_type=StatementType.CREATE_TABLE,
            description="Create aquilia_migrations tracking table",
        )
        await DDLExecutor.execute_statement(self.db, stmt)

    async def create_initial_schema(
        self,
        model_classes: list[type[Model]] | None = None,
        *,
        record_history: bool = True,
    ) -> list[ExecutableStatement]:
        """Execute initial schema creation using the unified MigrationPlan execution pipeline.

        Args:
            model_classes: Optional list of dependency-ordered models.
            record_history: If True, records initial schema in ``aquilia_migrations``.

        Returns:
            list[ExecutableStatement]: Executed statements.
        """
        plan = MigrationPlanner.plan_initial_schema(model_classes)
        return await self.execute_plan(plan, record_history=record_history)

    async def drop_all_tables(
        self,
        model_classes: list[type[Model]] | None = None,
    ) -> list[str]:
        """Drop all registered model tables transactionally using DDLExecutor.

        Args:
            model_classes: Optional list of models to drop. If None, queries ModelRegistry.

        Returns:
            list[str]: Executed DROP TABLE SQL statements.
        """
        from .migration_dsl import DropModel
        from .registry import ModelRegistry

        if model_classes is None:
            models_snapshot = list(ModelRegistry.all_models().values())
        else:
            models_snapshot = list(model_classes)

        drop_ops = []
        for model_cls in reversed(models_snapshot):
            if getattr(model_cls._meta, "abstract", False):
                continue
            drop_ops.append(DropModel(name=model_cls.__name__, table=model_cls._meta.table_name))

        statements = DDLExecutor.compile_operations(drop_ops, self.dialect)
        await DDLExecutor.execute_statements(self.db, statements, in_transaction=True)
        return [s.sql for s in statements if s.sql and not s.is_comment]

    async def execute_plan(
        self,
        plan: MigrationPlan,
        *,
        record_history: bool = True,
        fake: bool = False,
    ) -> list[ExecutableStatement]:
        """Execute a MigrationPlan atomically through DDLExecutor.

        Args:
            plan: The MigrationPlan to execute.
            record_history: Whether to update ``aquilia_migrations``.
            fake: If True, skip DDL execution but record history.

        Returns:
            list[ExecutableStatement]: Executed statement objects.
        """
        from .signals import post_migrate, pre_migrate

        if record_history:
            await self.ensure_tracking_table()
        await pre_migrate.send(sender=self.__class__, db=self.db)

        executed_statements: list[ExecutableStatement] = []

        for step in plan.steps:
            compiled = DDLExecutor.compile_operations(
                step.operations,
                self.dialect,
                migration_rev=step.revision,
            )

            if not fake:
                try:
                    res = await DDLExecutor.execute_statements(self.db, compiled, in_transaction=True)
                    executed_statements.extend(res.executed_statements)
                except MigrationFault:
                    raise
                except Exception as exc:
                    raise MigrationFault(
                        migration=step.revision,
                        reason=f"DSL migration failed: {exc}",
                    ) from exc

            if record_history:
                await self.db.execute(
                    f'INSERT INTO "{MIGRATION_TABLE}" ("revision", "slug", "checksum") VALUES (?, ?, ?)',
                    [step.revision, step.slug, step.checksum],
                )

        await post_migrate.send(sender=self.__class__, db=self.db)
        return executed_statements

    async def _execute_dsl_migration(self, migration: Migration) -> None:
        """Execute a Migration object via execute_plan for backward compatibility."""
        step = MigrationStep(
            revision=getattr(migration, "revision", ""),
            slug=getattr(migration, "slug", ""),
            operations=getattr(migration, "operations", []),
            models=getattr(migration, "models", []),
            dependencies=getattr(migration, "dependencies", []),
        )
        plan = MigrationPlan(steps=[step])
        await self.execute_plan(plan, record_history=False, fake=False)


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
        """Get migration status summary."""
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
        """Return human-readable migration status string."""
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
        """Preview pending migrations as compiled SQL/comment lines (dry-run)."""
        statements: list[str] = []
        pending = await self.get_pending()

        for path in pending:
            rev = _extract_revision(path) or path.stem
            statements.append(f"-- Migration: {rev} ({path.name})")
            module = _load_migration_module(path, rev)

            if hasattr(module, "operations"):
                migration_obj = _build_migration_from_module(module)
                compiled = DDLExecutor.compile_operations(
                    migration_obj.operations, self.dialect, migration_rev=rev
                )
                for stmt in compiled:
                    if stmt.sql:
                        statements.append(stmt.sql)
            elif hasattr(module, "upgrade"):
                statements.append(f"-- (Legacy: runs upgrade() from {path.name})")

        return statements

    async def sqlmigrate(self, revision: str) -> list[str]:
        """Get forward SQL statements for a single migration revision."""
        path = self._find_migration_file(revision)
        if not path:
            raise MigrationFault(
                migration=revision,
                reason=f"Migration file not found for revision '{revision}'",
            )

        module = _load_migration_module(path, revision)

        if hasattr(module, "operations"):
            migration_obj = _build_migration_from_module(module)
            compiled = DDLExecutor.compile_operations(
                migration_obj.operations, self.dialect, migration_rev=revision
            )
            return [s.sql for s in compiled if s.sql and not s.is_comment]
        else:
            return _extract_sql_from_source(path)

    async def migrate(
        self,
        *,
        target: str | None = None,
        fake: bool = False,
        database: str | None = None,
    ) -> list[str]:
        """Apply all pending migrations or roll back to target revision.

        Args:
            target: Target revision for rollback (None = forward all).
            fake: If True, mark applied without executing SQL.
            database: Database alias (multi-db support).

        Returns:
            list[str]: Applied revision IDs.
        """
        await self.ensure_tracking_table()

        if target is not None:
            return await self._rollback_to(target, fake=fake)

        pending = await self.get_pending()
        applied: list[str] = []

        for path in pending:
            await self._apply_migration(path, fake=fake)
            rev = _extract_revision(path) or path.stem
            applied.append(rev)

        return applied

    async def _apply_migration(self, path: Path, *, fake: bool = False) -> None:
        """Apply a single migration file and record it as applied."""
        rev = _extract_revision(path) or path.stem
        slug = _extract_slug(path)
        checksum = _file_checksum(path)

        module = _load_migration_module(path, rev)

        if not fake:
            if hasattr(module, "operations"):
                migration_obj = _build_migration_from_module(module)
                step = MigrationStep(
                    revision=rev,
                    slug=slug,
                    operations=migration_obj.operations,
                    checksum=checksum,
                    source_path=path,
                )
                plan = MigrationPlan(steps=[step])
                await self.execute_plan(plan, record_history=False, fake=False)
            elif hasattr(module, "upgrade"):
                upgrade_fn = module.upgrade
                try:
                    async with self.db.transaction():
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

    async def _rollback_to(self, target: str, *, fake: bool = False) -> list[str]:
        """Roll back all applied migrations after ``target`` in reverse order."""
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
                    compiled = DDLExecutor.compile_operations(
                        migration_obj.operations,
                        self.dialect,
                        reverse=True,
                        migration_rev=rev,
                    )
                    try:
                        await DDLExecutor.execute_statements(self.db, compiled, in_transaction=True)
                    except Exception as exc:
                        raise MigrationFault(migration=rev, reason=f"Rollback failed: {exc}") from exc
                elif hasattr(module, "downgrade"):
                    downgrade_fn = module.downgrade
                    try:
                        async with self.db.transaction():
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
        """Find the migration file whose name starts with ``revision``."""
        if not self.migrations_dir.exists():
            return None
        candidates = list(self.migrations_dir.glob(f"{revision}*.py"))
        return candidates[0] if candidates else None

    async def verify_checksums(self) -> list[dict[str, str]]:
        """Verify that applied migration files haven't been tampered with since being applied."""
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
    """Check if a SQLite database file exists WITHOUT creating WAL/SHM files."""
    if not db_url.startswith("sqlite"):
        return True

    path = _extract_sqlite_path(db_url)
    if path == ":memory:":
        return True

    return os.path.exists(path)


def check_migrations_applied(db_url: str, migrations_dir: str | Path = "migrations") -> bool:
    """Check if there are unapplied migrations WITHOUT creating WAL/SHM."""
    if not check_db_exists(db_url):
        return False

    if not db_url.startswith("sqlite"):
        return True

    path = _extract_sqlite_path(db_url)
    if path == ":memory:":
        return True

    mdir = Path(migrations_dir)
    if not mdir.exists():
        return True

    migration_files = sorted(f for f in mdir.glob("*.py") if not f.name.startswith("__"))
    if not migration_files:
        return True

    try:
        import sqlite3

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
                return False

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
    """Extract filesystem path from a SQLite connection URL."""
    for prefix in ("sqlite:///", "sqlite://"):
        if url.startswith(prefix):
            return url[len(prefix) :] or ":memory:"
    return url.replace("sqlite:", "").lstrip("/") or ":memory:"


def _extract_revision(path: Path) -> str | None:
    """Extract revision ID from migration filename."""
    parts = path.stem.split("_", 2)
    if len(parts) >= 2:
        return f"{parts[0]}_{parts[1]}"
    return None


def _extract_slug(path: Path) -> str:
    """Extract slug portion of a migration filename."""
    parts = path.stem.split("_", 2)
    if len(parts) >= 3:
        return parts[2]
    return path.stem


def _file_checksum(path: Path) -> str:
    """Compute truncated SHA-256 checksum of a file."""
    content = path.read_bytes()
    return hashlib.sha256(content).hexdigest()[:16]


def _load_migration_module(path: Path, rev: str) -> Any:
    """Load a migration file as a standalone Python module."""
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
    """Build a Migration instance from a loaded migration module."""
    from .migration_dsl import Migration

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
    """Best-effort extraction of SQL text from legacy migration source."""
    import re

    content = path.read_text(encoding="utf-8")
    pattern = r"execute\(\s*([\"']{3}|[\"'])(.*?)\1\s*\)"
    matches = re.findall(pattern, content, re.DOTALL)
    return [m[1].strip() for m in matches if m[1].strip()]
