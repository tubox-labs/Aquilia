"""
Aquilia migrations -- index operations.

Adds, drops, and alters indexes. Each operation carries a full
:class:`~aquilia.models.migration.schema.IndexState`, so an index's access
method, partial predicate, operator classes, and covering columns survive into
the migration file and back out again.

Storing only ``{name, table, columns, unique}`` is not enough. A partial GIN index with
operator classes was silently emitted as a plain B-tree index over every row,
and a ``DropIndex`` could not be reversed at all because the column list was
not retained.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from ....faults.domains import MigrationFault
from .base import Operation, OperationCategory, register_operation

if TYPE_CHECKING:
    from ..backends import SchemaBackend, Statement
    from ..schema import IndexState, ProjectState

__all__ = ["AddIndex", "RemoveIndex", "AlterIndex"]


@register_operation
@dataclass(frozen=True)
class AddIndex(Operation):
    """Create an index on an existing table.

    Attributes:
        model: Model class name.
        index: The index definition in full.

    Example::

        AddIndex(
            model="Post",
            index=IndexState(
                name="idx_posts_title_gin",
                columns=("title",),
                method="GIN",
                opclasses=("gin_trgm_ops",),
                condition="published",
            ),
        )
    """

    category: ClassVar[OperationCategory] = OperationCategory.INDEX
    reversible: ClassVar[bool] = True

    model: str
    index: IndexState

    def state_forwards(self, state: ProjectState) -> None:
        """Add the index to the model's table state, keeping indexes name-sorted.

        Args:
            state: The project state to mutate.

        Raises:
            MigrationFault: If the model does not exist, or already carries an
                index by this name.
        """
        key = state.key_for(self.model) or self.model
        table = state.resolve(self.model)
        if table is None:
            raise MigrationFault(
                migration="AddIndex",
                reason=f"Cannot add index {self.index.name!r} to unknown model {self.model!r}.",
            )
        if any(existing.name == self.index.name for existing in table.indexes):
            raise MigrationFault(
                migration="AddIndex",
                reason=(
                    f"Index {self.index.name!r} already exists on model {self.model!r}. Index names must be unique."
                ),
            )
        indexes = tuple(sorted((*table.indexes, self.index), key=lambda i: i.name))
        state.tables[key] = table.evolve(indexes=indexes)

    def database_forwards(self, state: ProjectState, backend: SchemaBackend) -> list[Statement]:
        """Emit ``CREATE INDEX``.

        Args:
            state: Project state before this operation.
            backend: The dialect backend.

        Returns:
            A single statement.

        Raises:
            MigrationFault: If the model is not in state, or -- from the
                backend -- if the dialect cannot express this index.
        """
        key = state.key_for(self.model) or self.model
        table = state.resolve(self.model)
        if table is None:
            raise MigrationFault(
                migration="AddIndex",
                reason=f"Cannot add index to unknown model {self.model!r}.",
            )
        return backend.create_index(table.db_table, self.index)

    def reverse(self) -> Operation:
        """Return the :class:`RemoveIndex` that drops this index."""
        return RemoveIndex(model=self.model, index=self.index)

    def describe(self) -> str:
        """e.g. ``"Add index idx_posts_title on Post"``."""
        return f"Add index {self.index.name} on {self.model}"


@register_operation
@dataclass(frozen=True)
class RemoveIndex(Operation):
    """Drop an index, retaining its definition so the drop can be reversed.

    Attributes:
        model: Model class name.
        index: The dropped index's definition, retained for reversal.
    """

    category: ClassVar[OperationCategory] = OperationCategory.INDEX
    reversible: ClassVar[bool] = True

    model: str
    index: IndexState

    def state_forwards(self, state: ProjectState) -> None:
        """Remove the index from the model's table state.

        Args:
            state: The project state to mutate. Removing an absent index is a
                no-op, keeping replay idempotent.
        """
        key = state.key_for(self.model) or self.model
        table = state.resolve(self.model)
        if table is None:
            return
        indexes = tuple(i for i in table.indexes if i.name != self.index.name)
        state.tables[key] = table.evolve(indexes=indexes)

    def database_forwards(self, state: ProjectState, backend: SchemaBackend) -> list[Statement]:
        """Emit ``DROP INDEX``.

        Args:
            state: Project state before this operation.
            backend: The dialect backend.

        Returns:
            A single statement.

        Raises:
            MigrationFault: If the model is not in state.
        """
        key = state.key_for(self.model) or self.model
        table = state.resolve(self.model)
        if table is None:
            raise MigrationFault(
                migration="RemoveIndex",
                reason=f"Cannot remove index from unknown model {self.model!r}.",
            )
        return backend.drop_index(table.db_table, self.index.name)

    def reverse(self) -> Operation:
        """Return the :class:`AddIndex` that recreates this index."""
        return AddIndex(model=self.model, index=self.index)

    def describe(self) -> str:
        """e.g. ``"Remove index idx_posts_title from Post"``."""
        return f"Remove index {self.index.name} from {self.model}"


@register_operation
@dataclass(frozen=True)
class AlterIndex(Operation):
    """Redefine an index.

    No SQL dialect can alter an index in place, so this drops and recreates it.
    Modelling it as one operation rather than two keeps the intent visible in
    plan output, keeps reversal exact, and lets the optimizer recognize a
    drop-then-add pair as a single redefinition.

    Attributes:
        model: Model class name.
        old_index: The index's current definition.
        new_index: Its desired definition.
    """

    category: ClassVar[OperationCategory] = OperationCategory.INDEX
    reversible: ClassVar[bool] = True

    model: str
    old_index: IndexState
    new_index: IndexState

    def state_forwards(self, state: ProjectState) -> None:
        """Replace the index in the model's table state.

        Args:
            state: The project state to mutate.

        Raises:
            MigrationFault: If the model does not exist.
        """
        key = state.key_for(self.model) or self.model
        table = state.resolve(self.model)
        if table is None:
            raise MigrationFault(
                migration="AlterIndex",
                reason=f"Cannot alter index on unknown model {self.model!r}.",
            )
        remaining = [i for i in table.indexes if i.name != self.old_index.name]
        indexes = tuple(sorted((*remaining, self.new_index), key=lambda i: i.name))
        state.tables[key] = table.evolve(indexes=indexes)

    def database_forwards(self, state: ProjectState, backend: SchemaBackend) -> list[Statement]:
        """Emit ``DROP INDEX`` followed by ``CREATE INDEX``.

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
                migration="AlterIndex",
                reason=f"Cannot alter index on unknown model {self.model!r}.",
            )
        statements = list(backend.drop_index(table.db_table, self.old_index.name))
        statements.extend(backend.create_index(table.db_table, self.new_index))
        return statements

    def reverse(self) -> Operation:
        """Return the operation restoring the previous index definition."""
        return AlterIndex(model=self.model, old_index=self.new_index, new_index=self.old_index)

    def describe(self) -> str:
        """e.g. ``"Alter index idx_posts_title on Post"``."""
        return f"Alter index {self.new_index.name} on {self.model}"
