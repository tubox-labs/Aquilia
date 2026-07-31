"""
Aquilia migrations -- execution.

Applies and rolls back migrations against a live database, and records what was
applied.

Atomicity
---------
Two atomicity hazards are handled here:

* **History recorded outside the transaction.** Running a migration's DDL in a
  transaction and inserting the tracking row *after* it commits leaves a window
  where a crash changes the schema without recording it -- the next run then
  reapplies the migration to a database that already has it. Here the tracking
  insert is the last statement *inside* the same transaction, so schema and
  history commit or roll back together.
* **Non-transactional statements silently mixed in.** A SQLite table rebuild
  needs ``PRAGMA foreign_keys`` toggled outside any transaction, and PostgreSQL
  rejects ``CREATE INDEX CONCURRENTLY`` inside one. Statements declare their own
  transactional requirement and the executor splits the batch accordingly.

On MySQL and Oracle, DDL cannot participate in a transaction at all. The
executor detects this from the backend's capability flags and warns rather than
promising an atomicity it cannot deliver.
"""

from __future__ import annotations

import inspect
import logging
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ...faults.domains import MigrationFault
from .backends import Statement, get_backend
from .operations import RunPython

if TYPE_CHECKING:
    from ...db.engine import AquiliaDatabase
    from .backends import SchemaBackend
    from .graph import MigrationNode
    from .operations import Operation
    from .schema import ProjectState

logger = logging.getLogger("aquilia.models.migration.executor")

__all__ = ["MIGRATION_TABLE", "AppliedMigration", "ExecutionResult", "MigrationExecutor", "compile_operations"]

MIGRATION_TABLE = "aquilia_migrations"
"""Default name of the applied-migrations tracking table."""


@dataclass(frozen=True)
class AppliedMigration:
    """One row of the applied-migrations tracking table.

    Attributes:
        revision: The migration's revision identifier.
        slug: Its human-readable slug.
        checksum: Checksum of the source file as of when it was applied. An
            empty string for rows written before checksums were recorded.
        applied_at: When it was applied, as the database rendered it. ``None``
            when the column is null.
    """

    revision: str
    slug: str
    checksum: str = ""
    applied_at: str | None = None


@dataclass
class ExecutionResult:
    """Outcome of executing a batch of statements.

    Attributes:
        statements_executed: Statements successfully run.
        statements_skipped: Statements the backend reported as safely ignorable
            (an index that already exists, for instance).
        python_operations: :class:`RunPython` callables invoked.
        duration_ms: Wall-clock time taken.
        executed: The statements that ran, for logging and plan verification.
        diagnostics: Human-readable notes about the run.
    """

    statements_executed: int = 0
    statements_skipped: int = 0
    python_operations: int = 0
    duration_ms: float = 0.0
    executed: list[Statement] = field(default_factory=list)
    diagnostics: list[str] = field(default_factory=list)


def compile_operations(
    operations: tuple[Operation, ...] | list[Operation],
    state: ProjectState,
    backend: SchemaBackend,
    *,
    reverse: bool = False,
) -> list[Statement]:
    """Compile operations to statements, replaying state as it goes.

    State must advance operation by operation: ``AddField`` needs the table to
    exist in state before it can render, and that table may have been created by
    the ``CreateModel`` two operations earlier in the same migration. Compiling
    every operation against the same static input cannot express any
    intra-migration dependency.

    Args:
        operations: The operations to compile, in application order.
        state: Project state before the batch. Mutated as compilation proceeds;
            clone it first if the original is needed.
        backend: The dialect backend.
        reverse: Compile the inverse of each operation, in reverse order, for a
            rollback.

    Returns:
        The statements, in execution order.

    Raises:
        MigrationFault: If an operation cannot be reversed while *reverse* is
            set, or if the backend cannot express a required change.
    """
    sequence = list(operations)
    if reverse:
        inverted: list[Operation] = []
        for operation in reversed(sequence):
            inverse = operation.reverse()
            if inverse is None:
                raise MigrationFault(
                    migration=type(operation).__name__,
                    reason=(
                        f"Operation {operation.describe()!r} cannot be reversed, so this "
                        f"migration cannot be rolled back. Supply reverse_sql/reverse_code, "
                        f"or roll back to a revision before it."
                    ),
                )
            inverted.append(inverse)
        sequence = inverted

    statements: list[Statement] = []
    for operation in sequence:
        if isinstance(operation, RunPython):
            operation.state_forwards(state)
            continue
        statements.extend(operation.database_forwards(state, backend))
        operation.state_forwards(state)
    return statements


class MigrationExecutor:
    """Applies migrations to a database and records what was applied.

    Attributes:
        db: The database to execute against.
        backend: The dialect backend, derived from the database.
        table: Name of the applied-migrations tracking table.

    Example::

        executor = MigrationExecutor(db)
        await executor.ensure_tracking_table()
        await executor.apply(node, state)
    """

    def __init__(
        self,
        db: AquiliaDatabase,
        *,
        dialect: str | None = None,
        table: str = MIGRATION_TABLE,
    ) -> None:
        """Bind an executor to a database.

        Args:
            db: The database to execute against.
            dialect: Override the dialect. Defaults to the database's own.
            table: Name of the tracking table.
        """
        self.db = db
        self.backend = get_backend(dialect or getattr(db, "dialect", "sqlite"))
        self.table = table

    # ── Tracking table ──────────────────────────────────────────────────

    async def ensure_tracking_table(self) -> None:
        """Create the applied-migrations table if it does not exist.

        The table records the revision, its slug, the source file's checksum,
        and when it was applied. The checksum is what lets
        :meth:`verify_checksums` detect a migration edited after being applied.
        """
        quoted = self.backend.quote(self.table)
        if self.backend.dialect == "postgresql":
            pk = f"{self.backend.quote('id')} SERIAL PRIMARY KEY"
        elif self.backend.dialect == "mysql":
            pk = f"{self.backend.quote('id')} INTEGER PRIMARY KEY AUTO_INCREMENT"
        elif self.backend.dialect == "oracle":
            pk = f"{self.backend.quote('id')} NUMBER(10) GENERATED ALWAYS AS IDENTITY PRIMARY KEY"
        else:
            pk = f"{self.backend.quote('id')} INTEGER PRIMARY KEY AUTOINCREMENT"

        ine = "IF NOT EXISTS " if self.backend.capabilities.table_if_not_exists else ""
        await self.db.execute(
            f"CREATE TABLE {ine}{quoted} (\n"
            f"  {pk},\n"
            f"  {self.backend.quote('revision')} VARCHAR(64) NOT NULL UNIQUE,\n"
            f"  {self.backend.quote('slug')} VARCHAR(200) NOT NULL,\n"
            f"  {self.backend.quote('checksum')} VARCHAR(64),\n"
            f"  {self.backend.quote('applied_at')} TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP\n"
            f")"
        )

    async def applied_revisions(self) -> list[str]:
        """Return applied revisions, in the order they were applied."""
        await self.ensure_tracking_table()
        rows = await self.db.fetch_all(
            f"SELECT {self.backend.quote('revision')} FROM {self.backend.quote(self.table)} "
            f"ORDER BY {self.backend.quote('id')}"
        )
        return [row["revision"] for row in rows]

    async def applied_records(self) -> list[AppliedMigration]:
        """Return the full tracking rows, in the order they were applied.

        Where :meth:`applied_revisions` answers *which* migrations ran, this
        answers *when* and *against what file* -- the checksum recorded at apply
        time is what :meth:`MigrationEngine.verify_checksums` compares against.

        Returns:
            One record per applied migration.

        Example:
            >>> for record in await executor.applied_records():
            ...     print(record.revision, record.applied_at)
        """
        await self.ensure_tracking_table()
        quote = self.backend.quote
        rows = await self.db.fetch_all(
            f"SELECT {quote('revision')}, {quote('slug')}, {quote('checksum')}, {quote('applied_at')} "
            f"FROM {quote(self.table)} ORDER BY {quote('id')}"
        )
        return [
            AppliedMigration(
                revision=row["revision"],
                slug=row["slug"],
                checksum=row["checksum"] or "",
                applied_at=str(row["applied_at"]) if row["applied_at"] is not None else None,
            )
            for row in rows
        ]

    # ── Application ─────────────────────────────────────────────────────

    async def apply(
        self,
        node: MigrationNode,
        state: ProjectState,
        *,
        fake: bool = False,
    ) -> ExecutionResult:
        """Apply one migration and record it, atomically where the database allows.

        Args:
            node: The migration to apply.
            state: Project state before this migration. Mutated to reflect it.
            fake: Record the migration as applied without executing its
                statements. Used when a schema change was made out of band.

        Returns:
            The execution result.

        Raises:
            MigrationFault: If any statement fails. On a backend with
                transactional DDL nothing is left applied; elsewhere the
                partial state is reported in the message.
        """
        await self.ensure_tracking_table()

        statements = compile_operations(node.operations, state, self.backend)
        python_ops = [op for op in node.operations if isinstance(op, RunPython)]

        if fake:
            await self._record(node)
            return ExecutionResult(diagnostics=[f"Migration {node.name} recorded as applied without executing."])

        return await self._run(node, statements, python_ops)

    async def rollback(
        self,
        node: MigrationNode,
        state: ProjectState,
        *,
        fake: bool = False,
    ) -> ExecutionResult:
        """Roll one migration back and remove its tracking row.

        Args:
            node: The migration to reverse.
            state: Project state including this migration. Mutated to exclude it.
            fake: Remove the tracking row without executing anything.

        Returns:
            The execution result.

        Raises:
            MigrationFault: If any operation in the migration is irreversible,
                or if a statement fails.
        """
        await self.ensure_tracking_table()

        if fake:
            await self._unrecord(node)
            return ExecutionResult(diagnostics=[f"Migration {node.name} unrecorded without executing."])

        statements = compile_operations(node.operations, state, self.backend, reverse=True)
        python_ops = [
            inverse
            for inverse in (op.reverse() for op in reversed(node.operations) if isinstance(op, RunPython))
            if isinstance(inverse, RunPython)
        ]
        return await self._run(node, statements, python_ops, rolling_back=True)

    async def apply_operations(
        self,
        operations: list[Operation],
        state: ProjectState,
        *,
        description: str = "schema",
    ) -> ExecutionResult:
        """Execute a bare operation list against the database, without history.

        Used for schema creation that is not itself a tracked migration -- most
        notably :meth:`ModelRegistry.create_tables`, which builds every table
        directly from the models. Routing it through here rather than looping
        over statements at the call site keeps all DDL execution, error
        tolerance, and transaction handling in one place.

        Args:
            operations: The operations to execute, in order.
            state: Project state before the batch. Mutated as execution proceeds.
            description: Label used in the diagnostic message.

        Returns:
            The execution result.

        Raises:
            MigrationFault: If any statement fails.
        """
        started = time.monotonic()
        result = ExecutionResult()
        statements = compile_operations(operations, state, self.backend)

        try:
            for group, transactional in _group_by_transactionality(statements, True):
                if transactional and self.backend.capabilities.transactional_ddl:
                    async with self.db.transaction():
                        await self._execute_group(group, result)
                else:
                    await self._execute_group(group, result)
        except MigrationFault:
            raise
        except Exception as exc:
            raise MigrationFault(
                migration=description,
                reason=f"Creating {description} failed: {exc}",
            ) from exc

        result.duration_ms = round((time.monotonic() - started) * 1000, 2)
        result.diagnostics.append(
            f"Created {description}: {result.statements_executed} statement(s) in {result.duration_ms}ms"
        )
        return result

    # ── Internals ───────────────────────────────────────────────────────

    async def _run(
        self,
        node: MigrationNode,
        statements: list[Statement],
        python_ops: list[RunPython],
        *,
        rolling_back: bool = False,
    ) -> ExecutionResult:
        """Execute a migration's statements and record the result.

        Statements are split at transactional boundaries: a run of
        transaction-safe statements executes inside one transaction, and any
        statement marked non-transactional runs on its own outside it.
        """
        started = time.monotonic()
        result = ExecutionResult()

        if not self.backend.capabilities.transactional_ddl:
            logger.warning(
                "%s does not support transactional DDL. If migration %s fails partway, "
                "earlier statements will remain applied and must be reverted by hand.",
                self.backend.dialect,
                node.name,
            )

        try:
            groups = _group_by_transactionality(statements, node.atomic)
            transactional_ddl = self.backend.capabilities.transactional_ddl

            # History is written inside the final transactional group so that
            # the schema change and its tracking row commit together. If the
            # final group is not transactional -- or the backend has no
            # transactional DDL at all -- it is written separately afterwards.
            history_index = -1
            if transactional_ddl:
                for index in range(len(groups) - 1, -1, -1):
                    if groups[index][1]:
                        history_index = index
                        break

            for index, (group, transactional) in enumerate(groups):
                if transactional and transactional_ddl:
                    async with self.db.transaction():
                        await self._execute_group(group, result)
                        if index == history_index:
                            await self._write_history(node, rolling_back)
                else:
                    await self._execute_group(group, result)

            for operation in python_ops:
                if operation.code is None:
                    continue
                await _invoke(operation.code, self.db)
                result.python_operations += 1

            if history_index == -1:
                await self._write_history(node, rolling_back)

        except MigrationFault:
            raise
        except Exception as exc:
            verb = "Rollback" if rolling_back else "Migration"
            recovery = (
                "The transaction was rolled back; the database is unchanged."
                if self.backend.capabilities.transactional_ddl
                else (
                    f"{self.backend.dialect} cannot roll back DDL, so the "
                    f"{result.statements_executed} statement(s) already executed remain "
                    f"applied and must be reverted by hand."
                )
            )
            raise MigrationFault(
                migration=node.revision,
                reason=f"{verb} of {node.name} failed: {exc}. {recovery}",
            ) from exc

        result.duration_ms = round((time.monotonic() - started) * 1000, 2)
        result.diagnostics.append(
            f"{'Rolled back' if rolling_back else 'Applied'} {node.name}: "
            f"{result.statements_executed} statement(s), "
            f"{result.python_operations} python operation(s), "
            f"{result.duration_ms}ms"
        )
        return result

    async def _execute_group(self, group: list[Statement], result: ExecutionResult) -> None:
        """Execute one group of statements, tolerating backend-ignorable errors."""
        for statement in group:
            if not statement.sql:
                continue
            try:
                if statement.params:
                    await self.db.execute(statement.sql, list(statement.params))
                else:
                    await self.db.execute(statement.sql)
                result.statements_executed += 1
                result.executed.append(statement)
            except Exception as exc:
                if await self._is_ignorable(exc, statement):
                    logger.warning("Ignoring benign DDL error on %s: %s", statement.description, exc)
                    result.statements_skipped += 1
                    continue
                raise

    async def _is_ignorable(self, exc: Exception, statement: Statement) -> bool:
        """Ask the database adapter whether an error is safely ignorable.

        Covers cases like "index already exists" on a backend without
        ``IF NOT EXISTS``, where the desired end state is already true.
        """
        adapter = getattr(self.db, "_adapter", None)
        checker = getattr(adapter, "should_ignore_ddl_error", None)
        if checker is None:
            return False
        outcome = checker(exc, statement)
        if inspect.isawaitable(outcome):
            outcome = await outcome
        return bool(outcome)

    async def _write_history(self, node: MigrationNode, rolling_back: bool) -> None:
        """Insert or delete this migration's tracking row."""
        if rolling_back:
            await self._unrecord(node)
        else:
            await self._record(node)

    async def _record(self, node: MigrationNode) -> None:
        """Insert this migration's tracking row."""
        await self.db.execute(
            f"INSERT INTO {self.backend.quote(self.table)} "
            f"({self.backend.quote('revision')}, {self.backend.quote('slug')}, "
            f"{self.backend.quote('checksum')}) VALUES (?, ?, ?)",
            [node.revision, node.slug, node.checksum],
        )

    async def _unrecord(self, node: MigrationNode) -> None:
        """Delete this migration's tracking row."""
        await self.db.execute(
            f"DELETE FROM {self.backend.quote(self.table)} WHERE {self.backend.quote('revision')} = ?",
            [node.revision],
        )


# ── Statement grouping ──────────────────────────────────────────────────────


def _group_by_transactionality(
    statements: list[Statement],
    atomic: bool,
) -> list[tuple[list[Statement], bool]]:
    """Split statements into consecutive runs sharing a transactional mode.

    A SQLite table rebuild brackets its work with ``PRAGMA foreign_keys``
    statements that are no-ops inside a transaction, and PostgreSQL rejects
    ``CREATE INDEX CONCURRENTLY`` inside one. Grouping lets each run execute in
    the mode it requires instead of forcing one mode on the whole migration.

    Args:
        statements: The statements to group, in execution order.
        atomic: Whether the migration requested atomic execution at all. When
            ``False`` every statement runs outside a transaction.

    Returns:
        ``(group, transactional)`` pairs, in execution order.

    Example:
        >>> _group_by_transactionality([pragma_off, create, pragma_on], True)
        [([pragma_off], False), ([create], True), ([pragma_on], False)]
    """
    if not statements:
        return []
    if not atomic:
        return [(list(statements), False)]

    groups: list[tuple[list[Statement], bool]] = []
    current: list[Statement] = [statements[0]]
    mode = statements[0].transactional

    for statement in statements[1:]:
        if statement.transactional == mode:
            current.append(statement)
        else:
            groups.append((current, mode))
            current = [statement]
            mode = statement.transactional
    groups.append((current, mode))
    return groups


async def _invoke(fn: Any, db: AquiliaDatabase) -> None:
    """Call a sync or async migration callable with the database connection."""
    outcome = fn(db)
    if inspect.isawaitable(outcome):
        await outcome
