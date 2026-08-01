"""
Aquilia migrations -- many-to-many relation operations.

Creates and drops the junction tables that back
:class:`~aquilia.models.fields_module.ManyToManyField` relationships.

Many-to-many tables need both an operation and a state representation:
``ManyToManyField`` was absent from ``create_snapshot`` and from the
initial-schema planner, so a database built entirely from generated migrations
had no junction table and every many-to-many relationship failed at runtime.
The only reason this was not noticed sooner is that
``ModelRegistry.create_tables()`` took a different code path that called
``Model.generate_m2m_sql()`` directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from aquilia.faults.domains import MigrationFault
from aquilia.models.migration.operations.base import Operation, OperationCategory, register_operation

if TYPE_CHECKING:
    from aquilia.models.migration.backends import SchemaBackend, Statement
    from aquilia.models.migration.schema import ManyToManyState, ProjectState

__all__ = ["CreateManyToManyTable", "DeleteManyToManyTable"]


def _junction_table_state(relation: ManyToManyState):
    """Build a synthetic :class:`TableState` describing a junction table.

    The junction table is not declared by any model, so no ``TableState`` exists
    for it in project state. One is synthesized here so the same backend code
    path that creates ordinary tables also creates this one -- rather than the
    hand-written, dialect-branching SQL string that
    ``Model.generate_m2m_sql()`` uses.

    The table has a surrogate auto-increment primary key, two non-null foreign
    keys, and a unique constraint over the pair so a link cannot be duplicated.

    Args:
        relation: The relationship to build a junction table for.

    Returns:
        A :class:`~aquilia.models.migration.schema.TableState` for the junction
        table.
    """
    from aquilia.models.migration.schema import ColumnState, Reference, TableState, UniqueConstraintState

    identifier = ColumnState(
        name="id",
        column="id",
        field_class="AutoField",
        primary_key=True,
        auto_increment=True,
    )
    source = ColumnState(
        name=relation.source_column,
        column=relation.source_column,
        field_class="IntegerField",
        reference=Reference(
            model=relation.source_table,
            table=relation.source_table,
            column=relation.source_target_column,
            on_delete="CASCADE",
            on_update="CASCADE",
        ),
    )
    target = ColumnState(
        name=relation.target_column,
        column=relation.target_column,
        field_class="IntegerField",
        reference=Reference(
            model=relation.target_table,
            table=relation.target_table,
            column=relation.target_target_column,
            on_delete="CASCADE",
            on_update="CASCADE",
        ),
    )
    return TableState(
        model=relation.table,
        db_table=relation.table,
        columns={"id": identifier, relation.source_column: source, relation.target_column: target},
        constraints=(
            UniqueConstraintState(
                name=f"uidx_{relation.table}_{relation.source_column}_{relation.target_column}",
                columns=(relation.source_column, relation.target_column),
            ),
        ),
    )


@register_operation
@dataclass(frozen=True)
class CreateManyToManyTable(Operation):
    """Create the junction table backing a many-to-many relationship.

    Only implicit relationships produce a table here. When the model declares
    ``through=``, the developer owns that table's schema and it is created by
    the ordinary :class:`~aquilia.models.migration.operations.models.CreateModel`
    for the through-model instead.

    Attributes:
        model: The owning model's class name.
        relation: The relationship's full state.
    """

    category: ClassVar[OperationCategory] = OperationCategory.RELATION
    reversible: ClassVar[bool] = True

    model: str
    relation: ManyToManyState

    def state_forwards(self, state: ProjectState) -> None:
        """Record the relationship on the owning model's table state.

        Args:
            state: The project state to mutate.

        Raises:
            MigrationFault: If the owning model does not exist.
        """
        key = state.key_for(self.model) or self.model
        table = state.resolve(self.model)
        if table is None:
            raise MigrationFault(
                migration="CreateManyToManyTable",
                reason=(
                    f"Cannot create many-to-many table for unknown model {self.model!r}. "
                    f"The CreateModel for it must come first."
                ),
            )
        if any(existing.name == self.relation.name for existing in table.m2m):
            return
        relations = tuple(sorted((*table.m2m, self.relation), key=lambda m: m.name))
        state.tables[key] = table.evolve(m2m=relations)

    def database_forwards(self, state: ProjectState, backend: SchemaBackend) -> list[Statement]:
        """Emit the junction table's ``CREATE TABLE``.

        Args:
            state: Project state before this operation.
            backend: The dialect backend.

        Returns:
            Statements in execution order, or none for a ``through=``
            relationship whose table the developer owns.
        """
        if not self.relation.implicit:
            return []
        return list(backend.create_table(_junction_table_state(self.relation)))

    def reverse(self) -> Operation:
        """Return the :class:`DeleteManyToManyTable` that drops this junction table."""
        return DeleteManyToManyTable(model=self.model, relation=self.relation)

    def describe(self) -> str:
        """e.g. ``"Create M2M table posts_tags for Post.tags"``."""
        return f"Create M2M table {self.relation.table} for {self.model}.{self.relation.name}"

    def references_model(self, model: str) -> bool:
        """Return whether this touches *model* or either end of the relationship."""
        return model in (self.model, self.relation.source_table, self.relation.target_table)


@register_operation
@dataclass(frozen=True)
class DeleteManyToManyTable(Operation):
    """Drop the junction table backing a many-to-many relationship.

    Reversal recreates the table's structure. The link rows it held are gone,
    which is why :attr:`destructive` is set.

    Attributes:
        model: The owning model's class name.
        relation: The relationship's state, retained for reversal.
    """

    category: ClassVar[OperationCategory] = OperationCategory.RELATION
    reversible: ClassVar[bool] = True
    destructive: ClassVar[bool] = True

    model: str
    relation: ManyToManyState

    def state_forwards(self, state: ProjectState) -> None:
        """Remove the relationship from the owning model's table state.

        Args:
            state: The project state to mutate. Removing an absent relationship
                is a no-op, keeping replay idempotent.
        """
        key = state.key_for(self.model) or self.model
        table = state.resolve(self.model)
        if table is None:
            return
        relations = tuple(m for m in table.m2m if m.name != self.relation.name)
        state.tables[key] = table.evolve(m2m=relations)

    def database_forwards(self, state: ProjectState, backend: SchemaBackend) -> list[Statement]:
        """Emit the junction table's ``DROP TABLE``.

        Args:
            state: Project state before this operation.
            backend: The dialect backend.

        Returns:
            A single destructive statement, or none for a ``through=``
            relationship whose table the developer owns.
        """
        if not self.relation.implicit:
            return []
        return backend.drop_table(self.relation.table)

    def reverse(self) -> Operation:
        """Return the :class:`CreateManyToManyTable` that recreates this table."""
        return CreateManyToManyTable(model=self.model, relation=self.relation)

    def describe(self) -> str:
        """e.g. ``"Delete M2M table posts_tags for Post.tags"``."""
        return f"Delete M2M table {self.relation.table} for {self.model}.{self.relation.name}"
