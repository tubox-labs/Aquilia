"""
Aquilia migrations -- escape-hatch operations.

:class:`RunSQL` and :class:`RunPython` cover the changes the typed operations
cannot express: dialect-specific DDL, extension installation, view and trigger
definitions, and data migrations that need application logic.

Both are deliberately opaque to the state layer. They can declare a
``state_operations`` list describing what they do to the schema, which is how a
raw-SQL change stays visible to the autodetector -- without that, the next
``makemigrations`` would see the state and the database disagree and generate a
migration undoing the hand-written one.
"""

from __future__ import annotations

import importlib
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, ClassVar

from aquilia.faults.domains import MigrationFault
from aquilia.models.migration.operations.base import Operation, OperationCategory, register_operation

if TYPE_CHECKING:
    from aquilia.models.migration.backends import SchemaBackend, Statement
    from aquilia.models.migration.schema import ProjectState

__all__ = ["RunSQL", "RunPython"]


@register_operation
@dataclass(frozen=True)
class RunSQL(Operation):
    """Execute raw SQL, forward and optionally in reverse.

    Attributes:
        sql: Statements to run when applying. A single string or a tuple of
            statements executed in order.
        reverse_sql: Statements to run when rolling back. Empty means the
            operation is irreversible, and :attr:`reversible` reflects that
            per-instance rather than for the class.
        state_operations: Typed operations describing this SQL's effect on the
            schema. They are applied to project state but never executed --
            the raw SQL does the actual work. Supplying them keeps the
            autodetector in sync; omitting them means the next
            ``makemigrations`` will not know about the change.
        dialects: Restrict execution to these dialects. Empty means all. Use it
            for genuinely dialect-specific DDL such as ``CREATE EXTENSION``.
        params: Bind parameters, passed to the driver separately rather than
            interpolated into the SQL string.
        atomic_statements: Whether the statements may run inside a transaction.

    Example::

        RunSQL(
            sql="CREATE EXTENSION IF NOT EXISTS pg_trgm;",
            reverse_sql="DROP EXTENSION IF EXISTS pg_trgm;",
            dialects=("postgresql",),
        )

    Warning:
        :attr:`sql` is executed verbatim. Never build it from untrusted input;
        use :attr:`params` for any value that varies.
    """

    category: ClassVar[OperationCategory] = OperationCategory.SPECIAL

    sql: str | tuple[str, ...] = ""
    reverse_sql: str | tuple[str, ...] = ""
    state_operations: tuple[Operation, ...] = ()
    dialects: tuple[str, ...] = ()
    params: tuple[Any, ...] = ()
    atomic_statements: bool = True

    def state_forwards(self, state: ProjectState) -> None:
        """Apply the declared :attr:`state_operations` to *state*.

        Args:
            state: The project state to mutate. Unchanged when no state
                operations were declared.
        """
        for operation in self.state_operations:
            operation.state_forwards(state)

    def database_forwards(self, state: ProjectState, backend: SchemaBackend) -> list[Statement]:
        """Emit the raw statements, unless restricted to other dialects.

        Args:
            state: Project state before this operation. Unused; raw SQL is
                opaque to the state layer.
            backend: The dialect backend, consulted only for its dialect name.

        Returns:
            One statement per SQL string, or none when :attr:`dialects`
            excludes the current backend.
        """
        from aquilia.models.migration.backends import Statement as BackendStatement

        if self.dialects and backend.dialect not in self.dialects:
            return []
        return [
            BackendStatement(
                sql=text,
                params=self.params,
                description="Run SQL",
                transactional=self.atomic_statements,
            )
            for text in _as_tuple(self.sql)
        ]

    def reverse(self) -> Operation | None:
        """Return a :class:`RunSQL` running :attr:`reverse_sql`, or ``None``.

        Returns:
            The inverse operation, or ``None`` when no reverse SQL was supplied.
        """
        if not self.reverse_sql:
            return None
        return RunSQL(
            sql=self.reverse_sql,
            reverse_sql=self.sql,
            state_operations=tuple(
                inverse for inverse in (op.reverse() for op in reversed(self.state_operations)) if inverse is not None
            ),
            dialects=self.dialects,
            atomic_statements=self.atomic_statements,
        )

    def describe(self) -> str:
        """e.g. ``"Run SQL: CREATE EXTENSION IF NOT EXISTS pg_trgm;"`` (truncated)."""
        statements = _as_tuple(self.sql)
        if not statements:
            return "Run SQL (empty)"
        preview = statements[0].strip().replace("\n", " ")
        if len(preview) > 60:
            preview = preview[:57] + "..."
        suffix = f" (+{len(statements) - 1} more)" if len(statements) > 1 else ""
        return f"Run SQL: {preview}{suffix}"

    def references_model(self, model: str) -> bool:
        """Return whether any declared state operation references *model*."""
        return any(operation.references_model(model) for operation in self.state_operations)


@register_operation
@dataclass(frozen=True)
class RunPython(Operation):
    """Execute a Python callable, typically to migrate data.

    The callable receives the live database connection and may be sync or async;
    the executor awaits coroutine functions.

    Attributes:
        code: The callable to run when applying.
        reverse_code: The callable to run when rolling back. ``None`` means the
            operation is irreversible.
        state_operations: Typed operations describing any schema effect, applied
            to state but never executed.
        atomic_statements: Whether the callable may run inside a transaction.
            Set ``False`` for a long backfill that would otherwise hold a
            transaction open across millions of rows.

    Example::

        async def backfill_slugs(db):
            rows = await db.fetch_all('SELECT id, title FROM articles')
            for row in rows:
                await db.execute(
                    'UPDATE articles SET slug = ? WHERE id = ?',
                    [slugify(row["title"]), row["id"]],
                )

        RunPython(code=backfill_slugs, reverse_code=RunPython.noop)

    Note:
        A callable cannot be serialized into a migration file by value. The
        serializer writes a reference to it by qualified name, so the callable
        must be importable -- a module-level function, not a lambda or a closure.
    """

    category: ClassVar[OperationCategory] = OperationCategory.DATA

    code: Callable[..., Any] | None = None
    reverse_code: Callable[..., Any] | None = None
    state_operations: tuple[Operation, ...] = field(default_factory=tuple)
    atomic_statements: bool = True

    @staticmethod
    async def noop(db: Any) -> None:
        """Do nothing.

        Use as :attr:`reverse_code` when a data migration is logically
        reversible but needs no work to undo -- it marks the operation
        reversible without inventing an inverse.

        Args:
            db: The database connection. Unused.
        """

    def state_forwards(self, state: ProjectState) -> None:
        """Apply the declared :attr:`state_operations` to *state*.

        Args:
            state: The project state to mutate.
        """
        for operation in self.state_operations:
            operation.state_forwards(state)

    def database_forwards(self, state: ProjectState, backend: SchemaBackend) -> list[Statement]:
        """Return no SQL -- the executor invokes :attr:`code` directly.

        Args:
            state: Project state before this operation. Unused.
            backend: The dialect backend. Unused.

        Returns:
            An empty list. :class:`RunPython` is recognized by the executor,
            which calls the callable rather than executing SQL.
        """
        return []

    def reverse(self) -> Operation | None:
        """Return a :class:`RunPython` running :attr:`reverse_code`, or ``None``.

        Returns:
            The inverse operation, or ``None`` when no reverse callable was
            supplied. Hardcoding ``reversible = True`` regardless would make an
            irreversible data migration silently do nothing on rollback instead
            of reporting that it cannot be undone.
        """
        if self.reverse_code is None:
            return None
        return RunPython(
            code=self.reverse_code,
            reverse_code=self.code,
            state_operations=tuple(
                inverse for inverse in (op.reverse() for op in reversed(self.state_operations)) if inverse is not None
            ),
            atomic_statements=self.atomic_statements,
        )

    def describe(self) -> str:
        """e.g. ``"Run Python: backfill_slugs"``."""
        name = getattr(self.code, "__name__", None) or "(none)"
        return f"Run Python: {name}"

    def references_model(self, model: str) -> bool:
        """Return whether any declared state operation references *model*."""
        return any(operation.references_model(model) for operation in self.state_operations)

    def to_dict(self) -> dict[str, Any]:
        """Serialize, recording callables by importable qualified name.

        Returns:
            The serialized operation.

        Raises:
            MigrationFault: If a callable is a lambda or a local function, which
                cannot be referenced by name and therefore cannot be reloaded
                when the migration is applied on another machine.
        """
        return {
            "operation": "RunPython",
            "code": _callable_ref(self.code),
            "reverse_code": _callable_ref(self.reverse_code),
            "state_operations": [op.to_dict() for op in self.state_operations],
            "atomic_statements": self.atomic_statements,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RunPython:
        """Rebuild from :meth:`to_dict` output, re-importing the callables.

        The base implementation would assign the ``"module:qualname"`` string
        straight to :attr:`code`, leaving a str where the executor expects a
        callable -- the failure would surface only once the migration ran.

        Args:
            data: Serialized operation data.

        Returns:
            The reconstructed operation.

        Raises:
            MigrationFault: If a referenced callable cannot be imported, or a
                nested state operation cannot be reconstructed.

        Example:
            >>> RunPython.from_dict(op.to_dict()).code is op.code
            True
        """
        return cls(
            code=_resolve_callable(data.get("code")),
            reverse_code=_resolve_callable(data.get("reverse_code")),
            state_operations=tuple(Operation.from_dict(entry) for entry in data.get("state_operations", ())),
            atomic_statements=bool(data.get("atomic_statements", True)),
        )


def _as_tuple(value: str | tuple[str, ...]) -> tuple[str, ...]:
    """Normalize a string-or-tuple of SQL into a tuple, dropping empties."""
    if isinstance(value, str):
        return (value,) if value.strip() else ()
    return tuple(item for item in value if item and item.strip())


def _callable_ref(fn: Callable[..., Any] | None) -> str | None:
    """Render a callable as a ``module:qualname`` reference for serialization.

    Args:
        fn: The callable, or ``None``.

    Returns:
        The reference string, or ``None``.

    Raises:
        MigrationFault: If *fn* is a lambda or defined inside another function,
            neither of which can be imported by name at apply time.
    """
    if fn is None:
        return None
    module = getattr(fn, "__module__", None)
    qualname = getattr(fn, "__qualname__", None)
    if not module or not qualname or "<locals>" in qualname or qualname == "<lambda>":
        raise MigrationFault(
            migration="RunPython",
            reason=(
                f"RunPython callable {fn!r} cannot be serialized: it must be a "
                f"module-level function so the migration can import it when applied. "
                f"Lambdas and nested functions are not importable by name."
            ),
        )
    return f"{module}:{qualname}"


def _resolve_callable(ref: Any) -> Callable[..., Any] | None:
    """Import a callable from a ``module:qualname`` reference.

    Args:
        ref: A reference string, an already-resolved callable, or ``None``.

    Returns:
        The callable, or ``None`` when *ref* is ``None``.

    Raises:
        MigrationFault: If the module cannot be imported, the attribute is
            missing, or the resolved object is not callable.
    """
    if ref is None or callable(ref):
        return ref
    if not isinstance(ref, str) or ":" not in ref:
        raise MigrationFault(
            migration="RunPython",
            reason=f"Cannot resolve RunPython callable from {ref!r}: expected a 'module:qualname' reference.",
        )

    module_name, _, qualname = ref.partition(":")
    try:
        target: Any = importlib.import_module(module_name)
        for part in qualname.split("."):
            target = getattr(target, part)
    except (ImportError, AttributeError) as exc:
        raise MigrationFault(
            migration="RunPython",
            reason=(
                f"Cannot resolve RunPython callable {ref!r}: {exc}. The function must "
                f"still exist and be importable for this migration to apply or roll back."
            ),
        ) from exc

    if not callable(target):
        raise MigrationFault(
            migration="RunPython",
            reason=f"RunPython reference {ref!r} resolved to {target!r}, which is not callable.",
        )
    return target
