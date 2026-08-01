"""
Aquilia migrations -- model-level operations.

Creates, drops, renames, and reconfigures tables. These are the operations that
carry the most state, because a table is the largest unit the migration system
manipulates -- and carrying the full state is precisely what makes
:class:`DeleteModel` reversible; a name-only equivalent would not be.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, ClassVar

from aquilia.faults.domains import MigrationFault
from aquilia.models.migration.operations.base import Operation, OperationCategory, register_operation

if TYPE_CHECKING:
    from aquilia.models.migration.backends import SchemaBackend, Statement
    from aquilia.models.migration.schema import ProjectState, TableState

__all__ = ["CreateModel", "DeleteModel", "RenameModel", "AlterModelOptions"]


@register_operation
@dataclass(frozen=True)
class CreateModel(Operation):
    """Create a table from a complete :class:`~aquilia.models.migration.schema.TableState`.

    The whole table definition travels with the operation: columns with their
    originating field classes, indexes with their access methods and partial
    predicates, constraints as typed objects. A migration file containing this
    operation fully describes the table it creates, with no reference to the
    model classes -- which is what lets an old migration still apply correctly
    after the model has since changed.

    Attributes:
        model: Model class name.
        table: The table's full immutable state.
        deferred_references: Database column names whose foreign keys must be
            added afterwards by a separate :class:`~aquilia.models.migration.operations.constraints.AddConstraint`.
            Set by the planner when two tables reference each other and one
            reference must be broken to order them at all.

    Example::

        CreateModel(
            model="User",
            table=TableState(
                model="User",
                db_table="users",
                columns={"id": id_column, "email": email_column},
            ),
        )
    """

    category: ClassVar[OperationCategory] = OperationCategory.MODEL
    reversible: ClassVar[bool] = True

    model: str
    table: TableState
    deferred_references: tuple[str, ...] = ()

    def state_forwards(self, state: ProjectState) -> None:
        """Add this table to *state*.

        Args:
            state: The project state to mutate.

        Raises:
            MigrationFault: If a table for this model already exists. Silently
                overwriting would let two migrations both claim to create the
                same model, and the resulting state would depend on apply order.
        """
        if self.model in state.tables:
            raise MigrationFault(
                migration="CreateModel",
                reason=(
                    f"Model {self.model!r} already exists in schema state. A model "
                    f"cannot be created twice; check for a duplicate CreateModel in "
                    f"your migration history."
                ),
            )
        state.tables[self.model] = self.table

    def database_forwards(self, state: ProjectState, backend: SchemaBackend) -> list[Statement]:
        """Emit ``CREATE TABLE``, then its indexes and index-backed constraints.

        Args:
            state: Project state before this operation.
            backend: The dialect backend.

        Returns:
            Statements in execution order: table, indexes, then any unique
            constraint that had to become a unique index.
        """
        from aquilia.models.migration.schema import UniqueConstraintState

        statements = list(backend.create_table(self.table, deferred_columns=frozenset(self.deferred_references)))
        for index in self.table.indexes:
            statements.extend(backend.create_index(self.table.db_table, index))
        for constraint in self.table.constraints:
            # A partial or expression-based unique constraint cannot live in the
            # CREATE TABLE body on any dialect, so the backend skipped it there
            # and it is emitted here as a unique index instead.
            if isinstance(constraint, UniqueConstraintState) and constraint.requires_index:
                statements.extend(backend.add_constraint(self.table.db_table, constraint))
        return statements

    def reverse(self) -> Operation:
        """Return the :class:`DeleteModel` that drops this table."""
        return DeleteModel(model=self.model, table=self.table)

    def describe(self) -> str:
        """e.g. ``"Create model User (users, 6 fields)"``."""
        return f"Create model {self.model} ({self.table.db_table}, {len(self.table.columns)} fields)"

    def references_model(self, model: str) -> bool:
        """Return whether this creates *model* or a table referencing it."""
        if self.model == model:
            return True
        return any(
            column.reference is not None and column.reference.model == model for column in self.table.columns.values()
        )


@register_operation
@dataclass(frozen=True)
class DeleteModel(Operation):
    """Drop a table, retaining its full state so the drop can be reversed.

    Storing only a name and a table string leaves nothing to rebuild a
    ``CREATE TABLE`` from, making reversal impossible. Carrying the
    :class:`TableState` makes it mechanical.

    Reversal restores the table's *structure*. It cannot restore rows: the data
    is gone once the ``DROP`` commits. :attr:`destructive` is set so plan output
    flags it before anyone approves the migration.

    Attributes:
        model: Model class name.
        table: The dropped table's state, retained for reversal.
    """

    category: ClassVar[OperationCategory] = OperationCategory.MODEL
    reversible: ClassVar[bool] = True
    destructive: ClassVar[bool] = True

    model: str
    table: TableState

    def state_forwards(self, state: ProjectState) -> None:
        """Remove this table from *state*.

        Args:
            state: The project state to mutate. Removing an absent model is a
                no-op, so replaying a partially-applied migration is safe.
        """
        state.tables.pop(self.model, None)

    def database_forwards(self, state: ProjectState, backend: SchemaBackend) -> list[Statement]:
        """Emit ``DROP TABLE``.

        Args:
            state: Project state before this operation.
            backend: The dialect backend.

        Returns:
            A single destructive statement. Indexes and constraints belonging to
            the table are dropped with it by every supported database, so they
            need no separate statements.
        """
        return backend.drop_table(self.table.db_table)

    def reverse(self) -> Operation:
        """Return the :class:`CreateModel` that recreates this table's structure."""
        return CreateModel(model=self.model, table=self.table)

    def describe(self) -> str:
        """e.g. ``"Delete model User (users)"``."""
        return f"Delete model {self.model} ({self.table.db_table})"


@register_operation
@dataclass(frozen=True)
class RenameModel(Operation):
    """Rename a model, and its table when the table name changes too.

    A model rename and a table rename are independent: renaming the class while
    ``Meta.table_name`` pins the table produces no SQL at all, only a state
    change. Conflating the two and emitting nothing in that case leaves the
    snapshot and the database describing the model under different names.

    Attributes:
        old_model: Previous model class name.
        new_model: New model class name.
        old_table: Previous database table name.
        new_table: New database table name. Equal to *old_table* when only the
            class was renamed.
    """

    category: ClassVar[OperationCategory] = OperationCategory.MODEL
    reversible: ClassVar[bool] = True

    old_model: str
    new_model: str
    old_table: str
    new_table: str

    def state_forwards(self, state: ProjectState) -> None:
        """Move the table state under its new model name, updating every reference.

        Foreign keys held by *other* tables point at this one by both model name
        and table name, so both must be rewritten -- otherwise a later
        ``CreateModel`` would emit a ``REFERENCES`` clause naming a table that
        no longer exists.

        Args:
            state: The project state to mutate.

        Raises:
            MigrationFault: If the model being renamed is not present.
        """
        from aquilia.models.migration.schema import ForeignKeyConstraintState

        table = state.tables.pop(self.old_model, None)
        if table is None:
            raise MigrationFault(
                migration="RenameModel",
                reason=(
                    f"Cannot rename model {self.old_model!r}: it does not exist in "
                    f"schema state. Check that an earlier migration created it."
                ),
            )
        state.tables[self.new_model] = table.evolve(model=self.new_model, db_table=self.new_table)

        for name, other in list(state.tables.items()):
            columns = dict(other.columns)
            changed = False
            for attr, column in columns.items():
                ref = column.reference
                if ref is not None and (ref.model == self.old_model or ref.table == self.old_table):
                    columns[attr] = column.evolve(
                        reference=type(ref)(
                            model=self.new_model,
                            table=self.new_table,
                            column=ref.column,
                            on_delete=ref.on_delete,
                            on_update=ref.on_update,
                            deferrable=ref.deferrable,
                            db_constraint=ref.db_constraint,
                        )
                    )
                    changed = True

            constraints = []
            for constraint in other.constraints:
                if isinstance(constraint, ForeignKeyConstraintState) and constraint.target == self.old_table:
                    constraints.append(
                        ForeignKeyConstraintState(
                            name=constraint.name,
                            columns=constraint.columns,
                            target=self.new_table,
                            target_columns=constraint.target_columns,
                            on_delete=constraint.on_delete,
                            on_update=constraint.on_update,
                            deferrable=constraint.deferrable,
                        )
                    )
                    changed = True
                else:
                    constraints.append(constraint)

            if changed:
                state.tables[name] = other.evolve(columns=columns, constraints=tuple(constraints))

    def database_forwards(self, state: ProjectState, backend: SchemaBackend) -> list[Statement]:
        """Emit ``ALTER TABLE ... RENAME TO``, or nothing when the table is unchanged.

        Args:
            state: Project state before this operation.
            backend: The dialect backend.

        Returns:
            One statement, or none for a model-only rename.
        """
        if self.old_table == self.new_table:
            return []
        return backend.rename_table(self.old_table, self.new_table)

    def reverse(self) -> Operation:
        """Return the symmetric rename."""
        return RenameModel(
            old_model=self.new_model,
            new_model=self.old_model,
            old_table=self.new_table,
            new_table=self.old_table,
        )

    def describe(self) -> str:
        """e.g. ``"Rename model OldUser to User (table users -> people)"``."""
        if self.old_table == self.new_table:
            return f"Rename model {self.old_model} to {self.new_model}"
        return f"Rename model {self.old_model} to {self.new_model} (table {self.old_table} -> {self.new_table})"

    def references_model(self, model: str) -> bool:
        """Return whether this renames *model*, under either name."""
        return model in (self.old_model, self.new_model)


@register_operation
@dataclass(frozen=True)
class AlterModelOptions(Operation):
    """Change table-level options that affect DDL.

    Covers ``Meta`` settings the database itself cares about -- tablespace and
    table comment. Purely Python-side options such as ``ordering`` are recorded
    in state so the snapshot stays faithful, but emit no SQL.

    Attributes:
        model: Model class name.
        old_options: The previous option mapping, retained for reversal.
        new_options: The desired option mapping.
    """

    category: ClassVar[OperationCategory] = OperationCategory.MODEL
    reversible: ClassVar[bool] = True

    model: str
    old_options: dict[str, Any] = field(default_factory=dict)
    new_options: dict[str, Any] = field(default_factory=dict)

    def state_forwards(self, state: ProjectState) -> None:
        """Replace the table's options in *state*.

        Args:
            state: The project state to mutate.

        Raises:
            MigrationFault: If the model is not present.
        """
        key = state.key_for(self.model) or self.model
        table = state.resolve(self.model)
        if table is None:
            raise MigrationFault(
                migration="AlterModelOptions",
                reason=f"Cannot alter options for unknown model {self.model!r}.",
            )
        state.tables[key] = table.evolve(options=dict(self.new_options))

    def database_forwards(self, state: ProjectState, backend: SchemaBackend) -> list[Statement]:
        """Emit a comment update where the change is one the database can see.

        Args:
            state: Project state before this operation.
            backend: The dialect backend.

        Returns:
            Statements for the DDL-visible option changes. Empty when only
            Python-side options differ.
        """
        from aquilia.models.migration.backends import Statement as BackendStatement

        key = state.key_for(self.model) or self.model

        table = state.resolve(self.model)
        if table is None:
            return []

        statements: list[BackendStatement] = []
        old_comment = self.old_options.get("comment", "")
        new_comment = self.new_options.get("comment", "")
        if old_comment != new_comment and backend.capabilities.table_comments:
            literal = backend._string_literal(new_comment) if new_comment else "NULL"
            statements.append(
                BackendStatement(
                    sql=f"COMMENT ON TABLE {backend.quote(table.db_table)} IS {literal};",
                    description=f"Set comment on {table.db_table}",
                )
            )
        return statements

    def reverse(self) -> Operation:
        """Return the operation restoring the previous options."""
        return AlterModelOptions(
            model=self.model,
            old_options=dict(self.new_options),
            new_options=dict(self.old_options),
        )

    def describe(self) -> str:
        """e.g. ``"Alter options on User"``."""
        return f"Alter options on {self.model}"
