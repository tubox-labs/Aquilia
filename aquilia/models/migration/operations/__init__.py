"""
Aquilia migrations -- operations.

An :class:`Operation` is a single, immutable, fully-typed schema change. Every
operation implements two independent halves:

``state_forwards(state)``
    Update the in-memory :class:`~aquilia.models.migration.schema.ProjectState`
    to reflect this change. Touches no database.

``database_forwards(state, backend)``
    Emit the :class:`~aquilia.models.migration.backends.Statement` objects that
    apply the change to a real database.

Why the two halves are separate
-------------------------------
The planner must know what the schema looks like *partway through* a
migration -- before ``AddField`` can render a column it needs to know the
table exists, and before ``CreateModel`` can be ordered it needs to know which
tables it references. Replaying state without touching a database is what makes
that possible, and it is also what makes a migration inspectable offline: ``aq
db plan`` produces the full SQL for a migration that has never been run.

Without a state layer, operations would go straight from a diff to SQL strings:
nothing would know the intermediate schema, and ordering would be left to
whatever the diff loop happened to emit.

Reversibility
-------------
Every destructive operation carries the state it destroys. ``DeleteModel``
holds the full :class:`~aquilia.models.migration.schema.TableState` it removes;
``RemoveField`` holds the removed
:class:`~aquilia.models.migration.schema.ColumnState`; ``AlterField`` holds
both old and new. Reversal is therefore mechanical and exact.

Storing only names -- ``RemoveField(model_name, table, column_name)`` -- makes
reversal impossible in principle: there is nothing to restore the column *from*.
An operation that genuinely cannot be reversed returns ``None`` from
:meth:`Operation.reverse` rather than raising, so a rollback plan annotates the
gap and continues instead of aborting.

Example
-------
::

    from aquilia.models.migration.operations import AddField, CreateModel

    operations = [
        CreateModel(model="User", table=user_table_state),
        AddField(model="User", field=bio_column_state),
    ]
"""

from __future__ import annotations

from .base import Operation, OperationCategory, register_operation, registered_operations, resolve_operation
from .constraints import AddConstraint, AlterConstraint, RemoveConstraint
from .fields import AddField, AlterField, RemoveField, RenameField
from .indexes import AddIndex, AlterIndex, RemoveIndex
from .models import AlterModelOptions, CreateModel, DeleteModel, RenameModel
from .relations import CreateManyToManyTable, DeleteManyToManyTable
from .special import RunPython, RunSQL

__all__ = [
    "Operation",
    "OperationCategory",
    "register_operation",
    "registered_operations",
    "resolve_operation",
    # Models
    "CreateModel",
    "DeleteModel",
    "RenameModel",
    "AlterModelOptions",
    # Fields
    "AddField",
    "RemoveField",
    "AlterField",
    "RenameField",
    # Indexes
    "AddIndex",
    "RemoveIndex",
    "AlterIndex",
    # Constraints
    "AddConstraint",
    "RemoveConstraint",
    "AlterConstraint",
    # Relations
    "CreateManyToManyTable",
    "DeleteManyToManyTable",
    # Escape hatches
    "RunSQL",
    "RunPython",
]
