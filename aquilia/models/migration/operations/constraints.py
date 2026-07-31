"""
Aquilia migrations -- constraint operations.

Adds, drops, and alters table-level constraints. Each operation carries a typed
:class:`~aquilia.models.migration.schema.ConstraintState` rather than a SQL
string.

Passing constraints around as raw SQL text (``constraint_sql``) forces the
system to
regex-parsed that text downstream to decide whether it could be rewritten as an
index on SQLite. Three consequences followed: constraints could not be diffed
(a whitespace change read as a modification), could not be reversed (nothing
structured to invert), and could not be validated (a malformed fragment only
failed at apply time, against a real database).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from ....faults.domains import MigrationFault
from .base import Operation, OperationCategory, register_operation

if TYPE_CHECKING:
    from ..backends import SchemaBackend, Statement
    from ..schema import ConstraintState, ProjectState

__all__ = ["AddConstraint", "RemoveConstraint", "AlterConstraint"]


@register_operation
@dataclass(frozen=True)
class AddConstraint(Operation):
    """Add a table-level constraint.

    The backend decides how to express it: an inline ``ALTER TABLE ... ADD
    CONSTRAINT`` where supported, or a unique index where the constraint is
    partial or expression-based and no dialect accepts the table-constraint
    form.

    Attributes:
        model: Model class name.
        constraint: The constraint to add.

    Example::

        AddConstraint(
            model="Product",
            constraint=CheckConstraintState(name="ck_price", check="price > 0"),
        )
    """

    category: ClassVar[OperationCategory] = OperationCategory.CONSTRAINT
    reversible: ClassVar[bool] = True

    model: str
    constraint: ConstraintState

    def state_forwards(self, state: ProjectState) -> None:
        """Add the constraint to the model's table state, keeping them name-sorted.

        Args:
            state: The project state to mutate.

        Raises:
            MigrationFault: If the model does not exist, or already carries a
                constraint by this name.
        """
        key = state.key_for(self.model) or self.model
        table = state.resolve(self.model)
        if table is None:
            raise MigrationFault(
                migration="AddConstraint",
                reason=(f"Cannot add constraint {self.constraint.name!r} to unknown model {self.model!r}."),
            )
        if any(existing.name == self.constraint.name for existing in table.constraints):
            raise MigrationFault(
                migration="AddConstraint",
                reason=(
                    f"Constraint {self.constraint.name!r} already exists on model "
                    f"{self.model!r}. Constraint names must be unique."
                ),
            )
        constraints = tuple(sorted((*table.constraints, self.constraint), key=lambda c: c.name))
        state.tables[key] = table.evolve(constraints=constraints)

    def database_forwards(self, state: ProjectState, backend: SchemaBackend) -> list[Statement]:
        """Emit the statements that add this constraint.

        Args:
            state: Project state before this operation.
            backend: The dialect backend.

        Returns:
            Statements in execution order.

        Raises:
            MigrationFault: If the model is not in state, or -- from the
                backend -- if the dialect can neither add the constraint nor
                express an equivalent. SQLite raises here for ``CHECK``
                constraints, rather than emitting a comment and reporting success.
        """
        from ..schema import UniqueConstraintState

        key = state.key_for(self.model) or self.model
        table = state.resolve(self.model)
        if table is None:
            raise MigrationFault(
                migration="AddConstraint",
                reason=f"Cannot add constraint to unknown model {self.model!r}.",
            )
        # A partial or expression-based unique constraint is a unique index on
        # every dialect -- including the ones that do support ADD CONSTRAINT --
        # so it never needs a rebuild. Checking this first also mirrors
        # RemoveConstraint, which drops the index rather than rebuilding.
        if isinstance(self.constraint, UniqueConstraintState) and self.constraint.requires_index:
            return backend.add_constraint(table.db_table, self.constraint)

        if not backend.capabilities.add_constraint and backend.capabilities.table_rebuild_required:
            # SQLite: no ALTER TABLE ADD CONSTRAINT. Rebuild the table with the
            # constraint present rather than silently skipping it.
            constraints = tuple(sorted((*table.constraints, self.constraint), key=lambda c: c.name))
            return backend.rebuild_table(  # type: ignore[attr-defined]
                table.evolve(constraints=constraints),
                copy_from=table,
                description=f"Add constraint {self.constraint.name} on {table.db_table}",
            )
        return backend.add_constraint(table.db_table, self.constraint)

    def reverse(self) -> Operation:
        """Return the :class:`RemoveConstraint` that drops this constraint."""
        return RemoveConstraint(model=self.model, constraint=self.constraint)

    def describe(self) -> str:
        """e.g. ``"Add constraint ck_price on Product"``."""
        return f"Add constraint {self.constraint.name} on {self.model}"


@register_operation
@dataclass(frozen=True)
class RemoveConstraint(Operation):
    """Drop a constraint, retaining its definition so the drop can be reversed.

    Attributes:
        model: Model class name.
        constraint: The dropped constraint's definition, retained for reversal.
    """

    category: ClassVar[OperationCategory] = OperationCategory.CONSTRAINT
    reversible: ClassVar[bool] = True

    model: str
    constraint: ConstraintState

    def state_forwards(self, state: ProjectState) -> None:
        """Remove the constraint from the model's table state.

        Args:
            state: The project state to mutate. Removing an absent constraint is
                a no-op, keeping replay idempotent.
        """
        key = state.key_for(self.model) or self.model
        table = state.resolve(self.model)
        if table is None:
            return
        constraints = tuple(c for c in table.constraints if c.name != self.constraint.name)
        state.tables[key] = table.evolve(constraints=constraints)

    def database_forwards(self, state: ProjectState, backend: SchemaBackend) -> list[Statement]:
        """Emit the statements that drop this constraint.

        A unique constraint that was materialized as an index must be dropped as
        an index, since no dialect will drop it as a constraint.

        Args:
            state: Project state before this operation.
            backend: The dialect backend.

        Returns:
            Statements in execution order.

        Raises:
            MigrationFault: If the model is not in state, or -- from the
                backend -- if the dialect cannot drop constraints and no
                rebuild path applies.
        """
        from ..schema import UniqueConstraintState

        key = state.key_for(self.model) or self.model

        table = state.resolve(self.model)
        if table is None:
            raise MigrationFault(
                migration="RemoveConstraint",
                reason=f"Cannot remove constraint from unknown model {self.model!r}.",
            )

        if isinstance(self.constraint, UniqueConstraintState) and self.constraint.requires_index:
            return backend.drop_index(table.db_table, self.constraint.name)

        if not backend.capabilities.drop_constraint and backend.capabilities.table_rebuild_required:
            constraints = tuple(c for c in table.constraints if c.name != self.constraint.name)
            return backend.rebuild_table(  # type: ignore[attr-defined]
                table.evolve(constraints=constraints),
                copy_from=table,
                description=f"Remove constraint {self.constraint.name} on {table.db_table}",
            )

        return backend.drop_constraint(table.db_table, self.constraint.name)

    def reverse(self) -> Operation:
        """Return the :class:`AddConstraint` that restores this constraint."""
        return AddConstraint(model=self.model, constraint=self.constraint)

    def describe(self) -> str:
        """e.g. ``"Remove constraint ck_price from Product"``."""
        return f"Remove constraint {self.constraint.name} from {self.model}"


@register_operation
@dataclass(frozen=True)
class AlterConstraint(Operation):
    """Redefine a constraint.

    No dialect alters a constraint in place, so this drops and re-adds it.
    Keeping it as one operation preserves the intent in plan output and makes
    reversal exact.

    Attributes:
        model: Model class name.
        old_constraint: The constraint's current definition.
        new_constraint: Its desired definition.
    """

    category: ClassVar[OperationCategory] = OperationCategory.CONSTRAINT
    reversible: ClassVar[bool] = True

    model: str
    old_constraint: ConstraintState
    new_constraint: ConstraintState

    def state_forwards(self, state: ProjectState) -> None:
        """Replace the constraint in the model's table state.

        Args:
            state: The project state to mutate.

        Raises:
            MigrationFault: If the model does not exist.
        """
        key = state.key_for(self.model) or self.model
        table = state.resolve(self.model)
        if table is None:
            raise MigrationFault(
                migration="AlterConstraint",
                reason=f"Cannot alter constraint on unknown model {self.model!r}.",
            )
        remaining = [c for c in table.constraints if c.name != self.old_constraint.name]
        constraints = tuple(sorted((*remaining, self.new_constraint), key=lambda c: c.name))
        state.tables[key] = table.evolve(constraints=constraints)

    def database_forwards(self, state: ProjectState, backend: SchemaBackend) -> list[Statement]:
        """Emit a drop followed by an add.

        Args:
            state: Project state before this operation.
            backend: The dialect backend.

        Returns:
            Statements in execution order.
        """
        remove = RemoveConstraint(model=self.model, constraint=self.old_constraint)
        statements = list(remove.database_forwards(state, backend))

        intermediate = state.clone()
        remove.state_forwards(intermediate)
        add = AddConstraint(model=self.model, constraint=self.new_constraint)
        statements.extend(add.database_forwards(intermediate, backend))
        return statements

    def reverse(self) -> Operation:
        """Return the operation restoring the previous constraint definition."""
        return AlterConstraint(
            model=self.model,
            old_constraint=self.new_constraint,
            new_constraint=self.old_constraint,
        )

    def describe(self) -> str:
        """e.g. ``"Alter constraint ck_price on Product"``."""
        return f"Alter constraint {self.new_constraint.name} on {self.model}"
