"""
Aquilia DDL Executor -- Single authority for typed DDL compilation and execution.

Replaces raw SQL string arrays with strongly-typed executable statements,
abstracting database execution, transaction handling, comment filtering,
Python-op execution, and backend-specific error tolerance.
"""

from __future__ import annotations

import inspect
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..db.engine import AquiliaDatabase
    from .migration_dsl import Operation

logger = logging.getLogger("aquilia.models.ddl_executor")

__all__ = [
    "StatementType",
    "ExecutableStatement",
    "ExecutionResult",
    "DDLExecutor",
]


class StatementType(Enum):
    """Classification of executable schema statements."""

    CREATE_TABLE = "CREATE_TABLE"
    DROP_TABLE = "DROP_TABLE"
    ALTER_TABLE = "ALTER_TABLE"
    CREATE_INDEX = "CREATE_INDEX"
    DROP_INDEX = "DROP_INDEX"
    ADD_CONSTRAINT = "ADD_CONSTRAINT"
    REMOVE_CONSTRAINT = "REMOVE_CONSTRAINT"
    RAW_SQL = "RAW_SQL"
    PYTHON_CALLABLE = "PYTHON_CALLABLE"
    COMMENT = "COMMENT"
    DIAGNOSTIC = "DIAGNOSTIC"


@dataclass
class ExecutableStatement:
    """A strongly-typed, executable DDL statement or action.

    Replaces raw SQL strings as the primary intermediate representation
    between migration planning and database execution.

    Attributes:
        sql: Target SQL text to execute against the database adapter.
        statement_type: Semantic categorization of the DDL action.
        description: Human-readable summary of the action.
        is_comment: Whether this statement is a non-executable comment annotation.
        python_op: Callable reference when statement_type is PYTHON_CALLABLE.
        operation: Source DSL Operation object that produced this statement.
        migration_rev: Revision ID of the parent migration, if applicable.
    """

    sql: str = ""
    statement_type: StatementType = StatementType.RAW_SQL
    description: str = ""
    is_comment: bool = False
    python_op: Any = None
    operation: Operation | None = None
    migration_rev: str | None = None

    def __post_init__(self) -> None:
        """Auto-detect comment statements from SQL prefix if not set explicitly."""
        if self.sql and self.sql.strip().startswith("--"):
            self.is_comment = True
            self.statement_type = StatementType.COMMENT


@dataclass
class ExecutionResult:
    """Summary metrics and diagnostic output of a DDL execution run.

    Attributes:
        statements_executed: Count of SQL/Python operations successfully executed.
        statements_skipped: Count of comments or safely-ignored statements.
        duration_ms: Total elapsed execution time in milliseconds.
        executed_statements: List of ExecutableStatement instances processed.
        diagnostics: List of human-readable execution logs or diagnostic notes.
    """

    statements_executed: int = 0
    statements_skipped: int = 0
    duration_ms: float = 0.0
    executed_statements: list[ExecutableStatement] = field(default_factory=list)
    diagnostics: list[str] = field(default_factory=list)


class DDLExecutor:
    """Execution authority for compiling DSL operations and executing typed statements.

    All schema DDL execution -- whether initial table creation, incremental
    migrations, or rollbacks -- is processed through DDLExecutor.

    Key Responsibilities:
    1. Lazy SQL/Statement compilation from typed DSL Operation objects.
    2. Explicit StatementType discrimination (no string prefix checking).
    3. Delegated backend error handling via ``db.adapter.should_ignore_ddl_error()``.
    4. Async Python execution for ``RunPython`` operations.
    5. Atomic transaction execution with detailed diagnostics.
    """

    @classmethod
    def compile_operations(
        cls,
        operations: list[Operation],
        dialect: str = "sqlite",
        *,
        reverse: bool = False,
        migration_rev: str | None = None,
    ) -> list[ExecutableStatement]:
        """Compile a sequence of DSL operations into typed ExecutableStatement objects.

        Args:
            operations: List of DSL Operation instances.
            dialect: Target SQL dialect ("sqlite", "postgresql", "mysql", "oracle").
            reverse: If True, compile downgrade/reverse SQL instead of forward.
            migration_rev: Revision ID associated with these operations.

        Returns:
            list[ExecutableStatement]: Ordered list of typed statements ready for execution.
        """
        compiled: list[ExecutableStatement] = []

        from .migration_dsl import (
            RunPython,
        )

        for op in operations:
            if isinstance(op, RunPython):
                callable_fn = op.reverse if reverse else op.forward
                desc = f"RunPython({op.describe()})"
                compiled.append(
                    ExecutableStatement(
                        statement_type=StatementType.PYTHON_CALLABLE,
                        description=desc,
                        python_op=callable_fn,
                        operation=op,
                        migration_rev=migration_rev,
                    )
                )
                continue

            try:
                sql_list = op.reverse_sql(dialect) if reverse else op.to_sql(dialect)
            except Exception as exc:
                desc = f"-- Operation {op.describe()} failed compilation: {exc}"
                compiled.append(
                    ExecutableStatement(
                        sql=desc,
                        statement_type=StatementType.COMMENT,
                        description=desc,
                        is_comment=True,
                        operation=op,
                        migration_rev=migration_rev,
                    )
                )
                continue

            for sql in sql_list:
                stmt_type = cls._infer_statement_type(op, sql)
                is_comment = sql.strip().startswith("--") or stmt_type == StatementType.COMMENT
                compiled.append(
                    ExecutableStatement(
                        sql=sql,
                        statement_type=stmt_type,
                        description=op.describe(),
                        is_comment=is_comment,
                        operation=op,
                        migration_rev=migration_rev,
                    )
                )

        return compiled

    @classmethod
    def _infer_statement_type(cls, op: Operation, sql: str) -> StatementType:
        """Infer statement type from operation subclass and SQL text."""
        if sql.strip().startswith("--"):
            return StatementType.COMMENT

        from .migration_dsl import (
            AddConstraint,
            AddField,
            AlterField,
            CreateIndex,
            CreateModel,
            DropIndex,
            DropModel,
            RemoveConstraint,
            RemoveField,
            RenameField,
            RenameModel,
            RunSQL,
        )

        if isinstance(op, CreateModel):
            return StatementType.CREATE_TABLE
        elif isinstance(op, DropModel):
            return StatementType.DROP_TABLE
        elif isinstance(op, (AddField, RemoveField, AlterField, RenameField, RenameModel)):
            return StatementType.ALTER_TABLE
        elif isinstance(op, CreateIndex):
            return StatementType.CREATE_INDEX
        elif isinstance(op, DropIndex):
            return StatementType.DROP_INDEX
        elif isinstance(op, AddConstraint):
            return StatementType.ADD_CONSTRAINT
        elif isinstance(op, RemoveConstraint):
            return StatementType.REMOVE_CONSTRAINT
        elif isinstance(op, RunSQL):
            return StatementType.RAW_SQL
        return StatementType.RAW_SQL

    @classmethod
    async def execute_statement(
        cls,
        db: AquiliaDatabase,
        statement: ExecutableStatement,
    ) -> bool:
        """Execute a single ExecutableStatement against an AquiliaDatabase engine.

        Delegates database-specific ignorable error logic to the database adapter
        (e.g., MySQL error 1061/1091).

        Args:
            db: Target AquiliaDatabase instance.
            statement: The ExecutableStatement to execute.

        Returns:
            bool: True if executed, False if skipped/ignored.

        Raises:
            Exception: Re-raises unhandled database execution exceptions.
        """
        if statement.is_comment or not statement.sql and not statement.python_op:
            logger.debug("Skipping comment/empty statement: %s", statement.description)
            return False

        if statement.statement_type == StatementType.PYTHON_CALLABLE:
            if statement.python_op:
                if inspect.iscoroutinefunction(statement.python_op):
                    await statement.python_op(db)
                else:
                    statement.python_op(db)
                return True
            return False

        try:
            await db.execute(statement.sql)
            return True
        except Exception as exc:
            # Consult database adapter for backend-specific error tolerance
            adapter = getattr(db, "_adapter", None)
            if adapter and hasattr(adapter, "should_ignore_ddl_error"):
                res = adapter.should_ignore_ddl_error(exc, statement)
                if inspect.iscoroutine(res):
                    res = await res
                if res is True:
                    logger.warning(
                        "Ignored backend DDL error on %s [%s]: %s",
                        statement.statement_type.value,
                        getattr(db, "dialect", "base"),
                        exc,
                    )
                    return False

            # Fallback dialect check if adapter is not present or didn't handle
            dialect = getattr(db, "dialect", "sqlite")
            if dialect == "mysql":
                cause = getattr(exc, "__cause__", exc) or exc
                code = getattr(cause, "errno", None)
                if code is None:
                    args = getattr(cause, "args", ())
                    if args:
                        first = args[0]
                        if isinstance(first, int):
                            code = first
                        elif isinstance(first, (tuple, list)) and first and isinstance(first[0], int):
                            code = first[0]
                if code in (1061, 1091):
                    logger.warning("Ignored MySQL DDL error %s: %s", code, exc)
                    return False

            raise

    @classmethod
    async def execute_statements(
        cls,
        db: AquiliaDatabase,
        statements: list[ExecutableStatement],
        *,
        in_transaction: bool = True,
    ) -> ExecutionResult:
        """Execute a batch of ExecutableStatement objects against a database.

        Args:
            db: Target AquiliaDatabase instance.
            statements: List of ExecutableStatement instances.
            in_transaction: If True, execute all statements inside a single transaction.

        Returns:
            ExecutionResult: Summary of execution metrics and diagnostics.
        """
        start_time = time.monotonic()
        res = ExecutionResult()

        async def _run_loop():
            for stmt in statements:
                if stmt.is_comment:
                    res.statements_skipped += 1
                    continue
                executed = await cls.execute_statement(db, stmt)
                if executed:
                    res.statements_executed += 1
                    res.executed_statements.append(stmt)
                else:
                    res.statements_skipped += 1

        if in_transaction:
            async with db.transaction():
                await _run_loop()
        else:
            await _run_loop()

        res.duration_ms = round((time.monotonic() - start_time) * 1000, 2)
        res.diagnostics.append(
            f"Executed {res.statements_executed} statements, skipped {res.statements_skipped} in {res.duration_ms}ms"
        )
        return res
