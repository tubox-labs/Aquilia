"""
Aquilia migrations -- operation optimizer.

Reduces a list of operations to an equivalent, shorter list. The autodetector
emits a faithful but verbose diff; the optimizer collapses the redundancy before
the migration is written to disk.

Typical reductions::

    CreateModel(User) + AddField(User.bio)        -> CreateModel(User) with bio
    AddField(User.bio) + RemoveField(User.bio)    -> nothing
    AddField(User.bio) + AlterField(User.bio)     -> AddField with final definition
    AlterField(x) + AlterField(x)                 -> one AlterField
    CreateModel(User) + DeleteModel(User)         -> nothing

This matters most when squashing: a project with fifty migrations that each add
a column to the same model squashes to one ``CreateModel`` rather than one
create plus forty-nine adds.

Without this pass, a migration would carry every intermediate step.

Safety
------
Two operations may only be merged when nothing between them observes the
intermediate state. The optimizer therefore never reorders across an operation
that touches the same model, and treats :class:`RunSQL` and :class:`RunPython`
as opaque barriers -- a data migration may well depend on the exact intermediate
schema, and merging across it would silently change what it sees.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .operations import (
    AddField,
    AddIndex,
    AlterField,
    AlterModelOptions,
    CreateModel,
    DeleteModel,
    RemoveField,
    RemoveIndex,
    RenameField,
    RunPython,
    RunSQL,
)

if TYPE_CHECKING:
    from .operations import Operation

__all__ = ["optimize", "MAX_OPTIMIZER_PASSES"]


MAX_OPTIMIZER_PASSES = 32
"""Cap on optimizer passes.

Each pass either shortens the list or stops, so this is a backstop against a
pathological rule interaction rather than an expected limit.
"""


def optimize(operations: list[Operation], *, passes: int = MAX_OPTIMIZER_PASSES) -> list[Operation]:
    """Reduce *operations* to an equivalent, shorter sequence.

    Repeats a single-pass reduction until it reaches a fixed point, since one
    merge often enables another -- collapsing ``AddField`` into ``CreateModel``
    can leave an ``AlterField`` newly adjacent to that same ``CreateModel``.

    Args:
        operations: The operations to reduce, in application order.
        passes: Maximum passes before giving up and returning what it has.

    Returns:
        An equivalent list, never longer than the input.

    Example:
        >>> optimize([AddField(model="U", field=bio), RemoveField(model="U", field=bio)])
        []
    """
    current = list(operations)
    for _ in range(passes):
        reduced = _single_pass(current)
        if len(reduced) == len(current):
            return reduced
        current = reduced
    return current


def _single_pass(operations: list[Operation]) -> list[Operation]:
    """Run one reduction pass, merging the first mergeable pair found."""
    result: list[Operation] = []
    index = 0
    total = len(operations)

    while index < total:
        current = operations[index]

        for lookahead in range(index + 1, total):
            candidate = operations[lookahead]

            replacement = _merge(current, candidate)
            if replacement is not None:
                result.extend(replacement)
                result.extend(operations[index + 1 : lookahead])
                result.extend(operations[lookahead + 1 :])
                return result

            if not _can_reorder_past(current, candidate):
                break

        result.append(current)
        index += 1

    return result


def _merge(first: Operation, second: Operation) -> list[Operation] | None:
    """Return the operations replacing *first* and *second*, or ``None``.

    Args:
        first: The earlier operation.
        second: The later one.

    Returns:
        The replacement list -- possibly empty when the pair cancels out -- or
        ``None`` when the pair cannot be merged.
    """
    for rule in _RULES:
        replacement = rule(first, second)
        if replacement is not None:
            return replacement
    return None


# ── Merge rules ─────────────────────────────────────────────────────────────


def _create_then_delete(first: Operation, second: Operation) -> list[Operation] | None:
    """``CreateModel(X)`` then ``DeleteModel(X)`` cancels out entirely."""
    if isinstance(first, CreateModel) and isinstance(second, DeleteModel) and first.model == second.model:
        return []
    return None


def _create_then_add_field(first: Operation, second: Operation) -> list[Operation] | None:
    """Fold ``AddField(X.f)`` into the ``CreateModel(X)`` that precedes it."""
    if not (isinstance(first, CreateModel) and isinstance(second, AddField)):
        return None
    if first.model != second.model or second.field.name in first.table.columns:
        return None
    return [first.evolve(table=first.table.with_column(second.field))]


def _create_then_alter_field(first: Operation, second: Operation) -> list[Operation] | None:
    """Fold ``AlterField(X.f)`` into the ``CreateModel(X)`` that precedes it."""
    if not (isinstance(first, CreateModel) and isinstance(second, AlterField)):
        return None
    if first.model != second.model or second.new_field.name not in first.table.columns:
        return None
    return [first.evolve(table=first.table.with_column(second.new_field))]


def _create_then_remove_field(first: Operation, second: Operation) -> list[Operation] | None:
    """Drop a column from ``CreateModel(X)`` rather than creating then removing it."""
    if not (isinstance(first, CreateModel) and isinstance(second, RemoveField)):
        return None
    if first.model != second.model or second.field.name not in first.table.columns:
        return None
    return [first.evolve(table=first.table.without_column(second.field.name))]


def _create_then_add_index(first: Operation, second: Operation) -> list[Operation] | None:
    """Fold ``AddIndex(X)`` into the ``CreateModel(X)`` that precedes it."""
    if not (isinstance(first, CreateModel) and isinstance(second, AddIndex)):
        return None
    if first.model != second.model:
        return None
    if any(existing.name == second.index.name for existing in first.table.indexes):
        return None
    indexes = tuple(sorted((*first.table.indexes, second.index), key=lambda i: i.name))
    return [first.evolve(table=first.table.evolve(indexes=indexes))]


def _add_then_remove_field(first: Operation, second: Operation) -> list[Operation] | None:
    """``AddField(X.f)`` then ``RemoveField(X.f)`` cancels out."""
    if not (isinstance(first, AddField) and isinstance(second, RemoveField)):
        return None
    if first.model != second.model or first.field.name != second.field.name:
        return None
    return []


def _add_then_alter_field(first: Operation, second: Operation) -> list[Operation] | None:
    """Collapse ``AddField`` plus a later ``AlterField`` into one add."""
    if not (isinstance(first, AddField) and isinstance(second, AlterField)):
        return None
    if first.model != second.model or first.field.name != second.new_field.name:
        return None
    return [first.evolve(field=second.new_field)]


def _alter_then_alter_field(first: Operation, second: Operation) -> list[Operation] | None:
    """Collapse consecutive alterations of one column into a single alteration."""
    if not (isinstance(first, AlterField) and isinstance(second, AlterField)):
        return None
    if first.model != second.model or first.new_field.name != second.old_field.name:
        return None
    if first.old_field == second.new_field:
        # The second alteration undoes the first.
        return []
    return [first.evolve(new_field=second.new_field)]


def _add_then_rename_field(first: Operation, second: Operation) -> list[Operation] | None:
    """Collapse ``AddField`` plus a later rename into an add under the final name."""
    if not (isinstance(first, AddField) and isinstance(second, RenameField)):
        return None
    if first.model != second.model or first.field.name != second.old_field.name:
        return None
    return [first.evolve(field=second.new_field)]


def _add_then_remove_index(first: Operation, second: Operation) -> list[Operation] | None:
    """``AddIndex`` then ``RemoveIndex`` of the same index cancels out."""
    if not (isinstance(first, AddIndex) and isinstance(second, RemoveIndex)):
        return None
    if first.model != second.model or first.index.name != second.index.name:
        return None
    return []


def _alter_then_alter_options(first: Operation, second: Operation) -> list[Operation] | None:
    """Collapse consecutive option changes on one model."""
    if not (isinstance(first, AlterModelOptions) and isinstance(second, AlterModelOptions)):
        return None
    if first.model != second.model:
        return None
    if first.old_options == second.new_options:
        return []
    return [first.evolve(new_options=second.new_options)]


def _delete_removes_field_ops(first: Operation, second: Operation) -> list[Operation] | None:
    """Discard a field change made redundant by a following ``DeleteModel``."""
    if not isinstance(second, DeleteModel):
        return None
    if not isinstance(first, (AddField, AlterField, RemoveField, RenameField, AddIndex, RemoveIndex)):
        return None
    if getattr(first, "model", None) != second.model:
        return None
    return [second]


_RULES = (
    _create_then_delete,
    _create_then_add_field,
    _create_then_alter_field,
    _create_then_remove_field,
    _create_then_add_index,
    _add_then_remove_field,
    _add_then_alter_field,
    _alter_then_alter_field,
    _add_then_rename_field,
    _add_then_remove_index,
    _alter_then_alter_options,
    _delete_removes_field_ops,
)


# ── Reordering safety ───────────────────────────────────────────────────────


def _can_reorder_past(operation: Operation, other: Operation) -> bool:
    """Return whether *operation* may be merged with something beyond *other*.

    Args:
        operation: The operation looking for a merge partner.
        other: An operation sitting between it and the candidate.

    Returns:
        ``True`` when *other* cannot observe or be affected by the merge.
    """
    # Raw SQL and Python are opaque: either may depend on the exact intermediate
    # schema, so nothing may be merged across them.
    if isinstance(operation, (RunSQL, RunPython)) or isinstance(other, (RunSQL, RunPython)):
        return False

    model = getattr(operation, "model", None) or getattr(operation, "new_model", None)
    if model is None:
        return False
    return not other.references_model(model)
