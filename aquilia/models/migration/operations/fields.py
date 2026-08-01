"""
Aquilia migrations -- field-level operations.

Adds, drops, alters, and renames columns. Three failure modes are structurally
impossible here, each because of what the operations carry:

* **Wrong column name.** An operation holding only the Python *attribute* name
  emits ``DROP COLUMN "author"`` for a column actually called ``author_id``.
  Every operation here carries a
  :class:`~aquilia.models.migration.schema.ColumnState`, which holds both names,
  and SQL is always rendered from :attr:`ColumnState.column`.
* **Discarded alterations.** An ``AlterField`` carrying only a new *type* would
  silently drop detected changes to nullability, default, uniqueness, and
  references. Here both the old and new column states travel with the
  operation, and the backend diffs them clause by clause.
* **Irreversible drops.** A ``RemoveField`` that retained nothing could not be
  reversed. Here the removed column state is retained, so rollback restores it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from aquilia.faults.domains import MigrationFault
from aquilia.models.migration.operations.base import Operation, OperationCategory, register_operation

if TYPE_CHECKING:
    from aquilia.models.migration.backends import SchemaBackend, Statement
    from aquilia.models.migration.schema import ColumnState, ProjectState

__all__ = ["AddField", "RemoveField", "AlterField", "RenameField"]


@register_operation
@dataclass(frozen=True)
class AddField(Operation):
    """Add a column to an existing table.

    Attributes:
        model: Model class name.
        field: The column to add, carrying its originating field class so the
            SQL type is resolved from the real field rather than a stored string.
        preserve_default: Whether the column's default is permanent. When
            ``False``, the default exists only to backfill existing rows and is
            dropped afterwards -- the standard way to add a ``NOT NULL`` column
            to a populated table without leaving a default the application does
            not want.

    Example::

        AddField(model="User", field=bio_column)
    """

    category: ClassVar[OperationCategory] = OperationCategory.FIELD
    reversible: ClassVar[bool] = True

    model: str
    field: ColumnState
    preserve_default: bool = True

    def state_forwards(self, state: ProjectState) -> None:
        """Add the column to the model's table state.

        Args:
            state: The project state to mutate.

        Raises:
            MigrationFault: If the model does not exist, or already has a column
                by this name.
        """
        key = state.key_for(self.model) or self.model
        table = state.resolve(self.model)
        if table is None:
            raise MigrationFault(
                migration="AddField",
                reason=(
                    f"Cannot add field {self.field.name!r}: model {self.model!r} does not "
                    f"exist in schema state. The CreateModel for it must come first."
                ),
            )
        if self.field.name in table.columns:
            raise MigrationFault(
                migration="AddField",
                reason=f"Model {self.model!r} already has a field named {self.field.name!r}.",
            )
        state.tables[key] = table.with_column(self.field)

    def database_forwards(self, state: ProjectState, backend: SchemaBackend) -> list[Statement]:
        """Emit ``ADD COLUMN``, plus an index and a default-drop where called for.

        Args:
            state: Project state before this operation.
            backend: The dialect backend.

        Returns:
            Statements in execution order.

        Raises:
            MigrationFault: If the model is not in state, or -- from the
                backend -- if the column is ``NOT NULL`` with no default and
                could not be added to a populated table.
        """
        from aquilia.models.migration.backends import Statement as BackendStatement
        from aquilia.models.migration.schema import NOT_PROVIDED, IndexState, auto_index_name

        key = state.key_for(self.model) or self.model

        table = state.resolve(self.model)
        if table is None:
            raise MigrationFault(
                migration="AddField",
                reason=f"Cannot add field to unknown model {self.model!r}.",
            )

        statements = list(backend.add_column(table.db_table, self.field))

        if self.field.db_index and not self.field.primary_key and not self.field.unique:
            statements.extend(
                backend.create_index(
                    table.db_table,
                    IndexState(
                        name=auto_index_name(table.db_table, (self.field.column,)),
                        columns=(self.field.column,),
                    ),
                )
            )

        if not self.preserve_default and self.field.default is not NOT_PROVIDED:
            statements.append(
                BackendStatement(
                    sql=(
                        f"ALTER TABLE {backend.quote(table.db_table)} ALTER COLUMN "
                        f"{backend.quote(self.field.column)} DROP DEFAULT;"
                    ),
                    description=f"Drop backfill default on {table.db_table}.{self.field.column}",
                )
            )

        return statements

    def reverse(self) -> Operation:
        """Return the :class:`RemoveField` that drops this column."""
        return RemoveField(model=self.model, field=self.field)

    def describe(self) -> str:
        """e.g. ``"Add field User.bio"``."""
        return f"Add field {self.model}.{self.field.name}"

    def references_model(self, model: str) -> bool:
        """Return whether this touches *model* or adds a reference to it."""
        if self.model == model:
            return True
        return self.field.reference is not None and self.field.reference.model == model


@register_operation
@dataclass(frozen=True)
class RemoveField(Operation):
    """Drop a column, retaining its state so the drop can be reversed.

    Reversal restores the column's *definition*. The values it held are gone
    once the ``DROP`` commits, which is why :attr:`destructive` is set.

    Attributes:
        model: Model class name.
        field: The column being removed, retained in full for reversal.
    """

    category: ClassVar[OperationCategory] = OperationCategory.FIELD
    reversible: ClassVar[bool] = True
    destructive: ClassVar[bool] = True

    model: str
    field: ColumnState

    def state_forwards(self, state: ProjectState) -> None:
        """Remove the column from the model's table state.

        Args:
            state: The project state to mutate. Removing an absent column is a
                no-op, keeping replay idempotent.
        """
        key = state.key_for(self.model) or self.model
        table = state.resolve(self.model)
        if table is None:
            return
        state.tables[key] = table.without_column(self.field.name)

    def database_forwards(self, state: ProjectState, backend: SchemaBackend) -> list[Statement]:
        """Emit ``DROP COLUMN``, or a table rebuild where the dialect requires one.

        Args:
            state: Project state before this operation.
            backend: The dialect backend.

        Returns:
            Statements in execution order.

        Raises:
            MigrationFault: If the model is not in state.
        """
        key = state.key_for(self.model) or self.model
        table = state.resolve(self.model)
        if table is None:
            raise MigrationFault(
                migration="RemoveField",
                reason=f"Cannot remove field from unknown model {self.model!r}.",
            )
        if not backend.capabilities.drop_column:
            return backend.rebuild_table(  # type: ignore[attr-defined]
                table.without_column(self.field.name),
                copy_from=table,
                description=f"Remove field {self.model}.{self.field.name}",
            )
        # Always the database column name, never the Python attribute name --
        # the classic bug: emitting DROP COLUMN "author" for a column named
        # "author_id".
        return backend.drop_column(table.db_table, self.field.column)

    def reverse(self) -> Operation:
        """Return the :class:`AddField` that restores this column's definition."""
        return AddField(model=self.model, field=self.field)

    def describe(self) -> str:
        """e.g. ``"Remove field User.legacy_flag"``."""
        return f"Remove field {self.model}.{self.field.name}"


@register_operation
@dataclass(frozen=True)
class AlterField(Operation):
    """Change a column's definition, carrying both its old and new state.

    Every difference between the two states is applied: type, nullability,
    default, uniqueness, collation, and generated expression. The backend
    decides how -- separate ``ALTER COLUMN`` clauses on PostgreSQL, a single
    ``MODIFY COLUMN`` on MySQL, a table rebuild on SQLite.

    Attributes:
        model: Model class name.
        old_field: The column's current state.
        new_field: Its desired state.
        preserve_default: Whether a newly-added default is permanent; see
            :attr:`AddField.preserve_default`.
    """

    category: ClassVar[OperationCategory] = OperationCategory.FIELD
    reversible: ClassVar[bool] = True

    model: str
    old_field: ColumnState
    new_field: ColumnState
    preserve_default: bool = True

    def __post_init__(self) -> None:
        """Validate that both states describe the same column.

        Raises:
            MigrationFault: If the two states name different columns. That would
                mean a rename disguised as an alteration, and the emitted SQL
                would target whichever name the backend happened to read.
        """
        if self.old_field.name != self.new_field.name:
            raise MigrationFault(
                migration="AlterField",
                reason=(
                    f"AlterField cannot rename a column: old field is "
                    f"{self.old_field.name!r} but new field is {self.new_field.name!r}. "
                    f"Use RenameField, optionally followed by AlterField."
                ),
            )

    def state_forwards(self, state: ProjectState) -> None:
        """Replace the column in the model's table state.

        Args:
            state: The project state to mutate.

        Raises:
            MigrationFault: If the model does not exist.
        """
        key = state.key_for(self.model) or self.model
        table = state.resolve(self.model)
        if table is None:
            raise MigrationFault(
                migration="AlterField",
                reason=f"Cannot alter field on unknown model {self.model!r}.",
            )
        state.tables[key] = table.with_column(self.new_field)

    def database_forwards(self, state: ProjectState, backend: SchemaBackend) -> list[Statement]:
        """Emit the statements that bring the column to its new definition.

        Args:
            state: Project state before this operation.
            backend: The dialect backend.

        Returns:
            Statements in execution order. Also emits index changes when the
            column's ``db_index`` flag flipped, since an index is not part of
            the column definition itself.

        Raises:
            MigrationFault: If the model is not in state, or -- from the
                backend -- if the dialect cannot make a required change.
        """
        from aquilia.models.migration.schema import IndexState, auto_index_name

        key = state.key_for(self.model) or self.model

        table = state.resolve(self.model)
        if table is None:
            raise MigrationFault(
                migration="AlterField",
                reason=f"Cannot alter field on unknown model {self.model!r}.",
            )

        statements = list(backend.alter_column(table, self.old_field, self.new_field))

        if self.old_field.db_index != self.new_field.db_index:
            index = IndexState(
                name=auto_index_name(table.db_table, (self.new_field.column,)),
                columns=(self.new_field.column,),
            )
            if self.new_field.db_index:
                statements.extend(backend.create_index(table.db_table, index))
            else:
                statements.extend(backend.drop_index(table.db_table, index.name))

        return statements

    def reverse(self) -> Operation:
        """Return the operation restoring the column's previous definition."""
        return AlterField(
            model=self.model,
            old_field=self.new_field,
            new_field=self.old_field,
        )

    def describe(self) -> str:
        """e.g. ``"Alter field User.email"``."""
        return f"Alter field {self.model}.{self.new_field.name}"

    def references_model(self, model: str) -> bool:
        """Return whether this touches *model* or either version's reference target."""
        if self.model == model:
            return True
        for column in (self.old_field, self.new_field):
            if column.reference is not None and column.reference.model == model:
                return True
        return False


@register_operation
@dataclass(frozen=True)
class RenameField(Operation):
    """Rename a column, preserving its data.

    Attributes:
        model: Model class name.
        old_field: The column's state under its previous name.
        new_field: Its state under the new name.

    Warning:
        A rename that the autodetector infers rather than being told about is a
        guess, and a wrong guess silently destroys a column. The autodetector will
        not infer a rename without a strong multi-signal match -- inferring one
        whenever a dropped and an added column share a type would match almost
        every schema change.
    """

    category: ClassVar[OperationCategory] = OperationCategory.FIELD
    reversible: ClassVar[bool] = True

    model: str
    old_field: ColumnState
    new_field: ColumnState

    def state_forwards(self, state: ProjectState) -> None:
        """Replace the old column with the new one, preserving declaration order.

        Args:
            state: The project state to mutate.

        Raises:
            MigrationFault: If the model does not exist.
        """
        key = state.key_for(self.model) or self.model
        table = state.resolve(self.model)
        if table is None:
            raise MigrationFault(
                migration="RenameField",
                reason=f"Cannot rename field on unknown model {self.model!r}.",
            )
        columns = {}
        for name, column in table.columns.items():
            if name == self.old_field.name:
                columns[self.new_field.name] = self.new_field
            else:
                columns[name] = column
        state.tables[key] = table.evolve(columns=columns)

    def database_forwards(self, state: ProjectState, backend: SchemaBackend) -> list[Statement]:
        """Emit ``RENAME COLUMN``, or nothing when only the attribute name changed.

        A model attribute can be renamed while ``db_column`` pins the database
        column, in which case there is nothing for the database to do.

        Args:
            state: Project state before this operation.
            backend: The dialect backend.

        Returns:
            One statement, or none.

        Raises:
            MigrationFault: If the model is not in state.
        """
        key = state.key_for(self.model) or self.model
        table = state.resolve(self.model)
        if table is None:
            raise MigrationFault(
                migration="RenameField",
                reason=f"Cannot rename field on unknown model {self.model!r}.",
            )
        if self.old_field.column == self.new_field.column:
            return []
        return backend.rename_column(table.db_table, self.old_field.column, self.new_field.column)

    def reverse(self) -> Operation:
        """Return the symmetric rename."""
        return RenameField(
            model=self.model,
            old_field=self.new_field,
            new_field=self.old_field,
        )

    def describe(self) -> str:
        """e.g. ``"Rename field User.name to full_name"``."""
        return f"Rename field {self.model}.{self.old_field.name} to {self.new_field.name}"
