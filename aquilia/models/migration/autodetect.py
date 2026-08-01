"""
Aquilia migrations -- schema autodetection.

Compares two :class:`~aquilia.models.migration.schema.ProjectState` objects and
emits the operations that turn the first into the second.

Determinism
-----------
Every collection is iterated in sorted order and every result is ordered by an
explicit rule, never by set iteration. Two runs over the same states -- in
different processes, with different ``PYTHONHASHSEED`` values -- produce
identical operation lists.

Building a work list from ``old_names & new_names`` and iterating the resulting
``set`` directly would make operation order change on every interpreter run:
generated migration files would not be reproducible, and two developers running
``makemigrations`` on the same models would get different diffs.

Rename detection
----------------
A rename is a *destructive guess*: emitting ``RENAME COLUMN`` when the developer
actually dropped one column and added another silently rewrites the wrong
column and loses the dropped one's data. A rename is therefore only inferred
from an explicit instruction or a match strong enough that coincidence is
implausible.

The scoring must not let any single signal clear the threshold on its own.
Scoring ``(same_type * 0.7) + (name_similarity * 0.3)`` against a threshold of
``0.6``, for instance, is unusable: ``same_type`` alone contributes ``0.7``, so
*every* pair of same-typed columns matches, and dropping ``legacy_zzz`` while
adding an unrelated ``brand_new_field`` of the same type reads as a rename. See
:data:`RENAME_CONFIDENCE_THRESHOLD` for the weighting used instead.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import TYPE_CHECKING

from aquilia.models.migration.operations import (
    AddConstraint,
    AddField,
    AddIndex,
    AlterConstraint,
    AlterField,
    AlterIndex,
    AlterModelOptions,
    CreateManyToManyTable,
    CreateModel,
    DeleteManyToManyTable,
    DeleteModel,
    RemoveConstraint,
    RemoveField,
    RemoveIndex,
    RenameField,
    RenameModel,
)
from aquilia.models.migration.schema import ForeignKeyConstraintState

if TYPE_CHECKING:
    from aquilia.models.migration.operations import Operation
    from aquilia.models.migration.schema import ColumnState, ProjectState, TableState

__all__ = ["RenameHint", "Autodetector", "detect_changes"]


# Minimum combined score for an *inferred* rename. Reaching it requires
# agreement across several independent signals; a single matching signal
# cannot.
RENAME_CONFIDENCE_THRESHOLD = 0.85


@dataclass(frozen=True, slots=True)
class RenameHint:
    """An explicit instruction that something was renamed rather than replaced.

    Supplied by the developer -- interactively at the ``makemigrations`` prompt,
    or programmatically -- to remove the guesswork from a rename the detector
    would otherwise see as a drop plus an add.

    Attributes:
        model: Model whose field was renamed. ``None`` for a model rename.
        old_name: Previous name.
        new_name: New name.

    Example::

        RenameHint(model="User", old_name="name", new_name="full_name")
        RenameHint(model=None, old_name="Account", new_name="User")
    """

    old_name: str
    new_name: str
    model: str | None = None


@dataclass
class Autodetector:
    """Computes the operations that transform one project state into another.

    Attributes:
        before: The starting state, typically loaded from the last snapshot.
        after: The target state, typically built from the current models.
        hints: Explicit rename instructions. Anything not covered by a hint is
            only inferred when the evidence is overwhelming; see
            :data:`RENAME_CONFIDENCE_THRESHOLD`.
        infer_renames: Whether to attempt inference at all. Setting this
            ``False`` makes every unmatched pair a drop plus an add -- more
            operations, zero chance of silently rewriting the wrong column.

    Example::

        detector = Autodetector(before=old_state, after=new_state)
        operations = detector.detect()
    """

    before: ProjectState
    after: ProjectState
    hints: tuple[RenameHint, ...] = ()
    infer_renames: bool = True

    _model_renames: dict[str, str] = field(default_factory=dict, init=False, repr=False)

    # ── Entry point ─────────────────────────────────────────────────────

    def detect(self) -> list[Operation]:
        """Return the operations transforming :attr:`before` into :attr:`after`.

        Operations are emitted in a dependency-safe order:

        1. Model renames, so later operations refer to current names.
        2. Table creations, topologically sorted so a referenced table always
           exists before the table referencing it.
        3. Per-model field, index, and constraint changes.
        4. Many-to-many junction table changes.
        5. Table deletions, in reverse topological order so a referenced table
           is dropped only after its dependents.

        Returns:
            The operations, in application order. Empty when the states match.

        Example:
            >>> Autodetector(before=empty, after=current).detect()
            [CreateModel(model='User', ...), CreateModel(model='Post', ...)]
        """
        operations: list[Operation] = []
        operations.extend(self._detect_model_renames())
        operations.extend(self._detect_created_models())
        operations.extend(self._detect_altered_models())
        operations.extend(self._detect_deleted_models())
        return operations

    # ── Model-level detection ───────────────────────────────────────────

    def _detect_model_renames(self) -> list[Operation]:
        """Emit :class:`RenameModel` for models identified as renamed.

        A model rename is inferred only when the two models share a table name,
        which is near-conclusive: a table name is an explicit, developer-chosen
        identifier, and two unrelated models rarely claim the same one. Field
        similarity alone is not sufficient, since
        two models built from the same base class share every inherited field.

        Returns:
            The rename operations, ordered by old model name.
        """
        added = set(self.after.tables) - set(self.before.tables)
        removed = set(self.before.tables) - set(self.after.tables)
        if not added or not removed:
            return []

        operations: list[Operation] = []
        claimed: set[str] = set()

        for hint in self.hints:
            if hint.model is not None:
                continue
            if hint.old_name in removed and hint.new_name in added:
                operations.append(self._rename_model_op(hint.old_name, hint.new_name))
                claimed.add(hint.old_name)
                claimed.add(hint.new_name)

        if self.infer_renames:
            for old_name in sorted(removed - claimed):
                old_table = self.before.tables[old_name].db_table
                for new_name in sorted(added - claimed):
                    if self.after.tables[new_name].db_table == old_table:
                        operations.append(self._rename_model_op(old_name, new_name))
                        claimed.add(old_name)
                        claimed.add(new_name)
                        break

        return operations

    def _rename_model_op(self, old_name: str, new_name: str) -> Operation:
        """Build a :class:`RenameModel` and record the mapping for later lookups."""
        self._model_renames[new_name] = old_name
        return RenameModel(
            old_model=old_name,
            new_model=new_name,
            old_table=self.before.tables[old_name].db_table,
            new_table=self.after.tables[new_name].db_table,
        )

    def _detect_created_models(self) -> list[Operation]:
        """Emit :class:`CreateModel` for genuinely new models, dependency-ordered.

        Creation order follows :meth:`ProjectState.creation_order`, so a table
        holding a foreign key is always created after its target. Junction
        tables for any many-to-many relationships follow their owning model.

        When two new models reference each other, no order can satisfy both
        inline foreign keys. The key that would point at a not-yet-created table
        is deferred: its column is created without the inline ``REFERENCES``,
        and an :class:`AddConstraint` adds it once both tables exist.

        Returns:
            The creation operations, in dependency order, followed by any
            deferred foreign-key constraints.
        """
        created = set(self.after.tables) - set(self.before.tables) - set(self._model_renames)
        if not created:
            return []

        order = [model for model in self.after.creation_order() if model in created]
        position = {model: index for index, model in enumerate(order)}
        table_to_model = {self.after.tables[name].db_table: name for name in self.after.tables}
        existing_tables = {table.db_table for table in self.before.tables.values()}

        operations: list[Operation] = []
        deferred: list[Operation] = []

        for model in order:
            table = self.after.tables[model]

            # A reference is only a problem when its target is *also* being
            # created in this migration and comes later in the order.
            defer: list[str] = []
            for column in table.columns.values():
                reference = column.reference
                if reference is None or reference.table in existing_tables:
                    continue
                target = table_to_model.get(reference.table)
                if target is None or target not in position:
                    continue
                if position[target] > position[model]:
                    defer.append(column.column)
                    deferred.append(
                        AddConstraint(
                            model=model,
                            constraint=ForeignKeyConstraintState(
                                name=f"fk_{table.db_table}_{column.column}",
                                columns=(column.column,),
                                target=reference.table,
                                target_columns=(reference.column,),
                                on_delete=reference.on_delete,
                                on_update=reference.on_update,
                            ),
                        )
                    )

            operations.append(CreateModel(model=model, table=table, deferred_references=tuple(sorted(defer))))
            for relation in table.m2m:
                operations.append(CreateManyToManyTable(model=model, relation=relation))

        return operations + deferred

    def _detect_deleted_models(self) -> list[Operation]:
        """Emit :class:`DeleteModel` for removed models, in reverse dependency order.

        Junction tables are dropped before their owning model, and a referenced
        table only after everything referencing it. Dropping in alphabetical order
        instead fails whenever a parent table sorts before its child.

        Returns:
            The deletion operations, in dependency-safe order.
        """
        renamed_away = set(self._model_renames.values())
        deleted = set(self.before.tables) - set(self.after.tables) - renamed_away
        if not deleted:
            return []

        operations: list[Operation] = []
        for model in self.before.deletion_order():
            if model not in deleted:
                continue
            table = self.before.tables[model]
            for relation in table.m2m:
                operations.append(DeleteManyToManyTable(model=model, relation=relation))
            operations.append(DeleteModel(model=model, table=table))
        return operations

    # ── Per-model detection ─────────────────────────────────────────────

    def _detect_altered_models(self) -> list[Operation]:
        """Emit field, index, constraint, and relation changes for surviving models.

        Returns:
            The operations, grouped by model in sorted order and, within each
            model, ordered so that renames precede additions, additions precede
            alterations, and removals come last.
        """
        operations: list[Operation] = []

        for new_model in sorted(self.after.tables):
            old_model = self._model_renames.get(new_model, new_model)
            old_table = self.before.tables.get(old_model)
            if old_table is None:
                continue
            new_table = self.after.tables[new_model]

            operations.extend(self._detect_fields(new_model, old_table, new_table))
            operations.extend(self._detect_indexes(new_model, old_table, new_table))
            operations.extend(self._detect_constraints(new_model, old_table, new_table))
            operations.extend(self._detect_relations(new_model, old_table, new_table))
            operations.extend(self._detect_options(new_model, old_table, new_table))

        return operations

    def _detect_fields(self, model: str, old: TableState, new: TableState) -> list[Operation]:
        """Emit column additions, removals, renames, and alterations for one model.

        Returns:
            The operations, ordered renames, additions, alterations, removals.
            Removals last so that a column being replaced by a differently-named
            one is added before the old one disappears, keeping a backfill
            possible in between.
        """
        added_names = sorted(set(new.columns) - set(old.columns))
        removed_names = sorted(set(old.columns) - set(new.columns))

        renames = self._match_renames(model, old, new, removed_names, added_names)
        renamed_old = {pair[0] for pair in renames}
        renamed_new = {pair[1] for pair in renames}

        rename_ops: list[Operation] = [
            RenameField(model=model, old_field=old.columns[old_name], new_field=new.columns[new_name])
            for old_name, new_name in renames
        ]

        add_ops: list[Operation] = [
            AddField(model=model, field=new.columns[name]) for name in added_names if name not in renamed_new
        ]

        remove_ops: list[Operation] = [
            RemoveField(model=model, field=old.columns[name]) for name in removed_names if name not in renamed_old
        ]

        alter_ops: list[Operation] = []
        for name in sorted(set(old.columns) & set(new.columns)):
            if old.columns[name] != new.columns[name]:
                alter_ops.append(AlterField(model=model, old_field=old.columns[name], new_field=new.columns[name]))
        # A renamed column may also have changed definition; compare under the
        # new name so the alteration is not lost.
        for old_name, new_name in renames:
            renamed = old.columns[old_name].evolve(name=new_name, column=new.columns[new_name].column)
            if renamed != new.columns[new_name]:
                alter_ops.append(AlterField(model=model, old_field=renamed, new_field=new.columns[new_name]))

        return [*rename_ops, *add_ops, *alter_ops, *remove_ops]

    def _detect_indexes(self, model: str, old: TableState, new: TableState) -> list[Operation]:
        """Emit index additions, removals, and redefinitions for one model.

        An index whose name is unchanged but whose definition differs becomes a
        single :class:`AlterIndex` rather than a remove/add pair, which keeps the
        intent legible in plan output.

        Returns:
            The operations, ordered additions, alterations, removals.
        """
        old_by_name = {index.name: index for index in old.indexes}
        new_by_name = {index.name: index for index in new.indexes}

        add_ops: list[Operation] = [
            AddIndex(model=model, index=new_by_name[name]) for name in sorted(set(new_by_name) - set(old_by_name))
        ]
        remove_ops: list[Operation] = [
            RemoveIndex(model=model, index=old_by_name[name]) for name in sorted(set(old_by_name) - set(new_by_name))
        ]
        alter_ops: list[Operation] = [
            AlterIndex(model=model, old_index=old_by_name[name], new_index=new_by_name[name])
            for name in sorted(set(old_by_name) & set(new_by_name))
            if old_by_name[name] != new_by_name[name]
        ]
        return [*add_ops, *alter_ops, *remove_ops]

    def _detect_constraints(self, model: str, old: TableState, new: TableState) -> list[Operation]:
        """Emit constraint additions, removals, and redefinitions for one model.

        Returns:
            The operations, ordered removals, alterations, additions. Removals
            first here -- unlike fields -- because a replacement constraint may
            conflict with the one it replaces while both exist.
        """
        old_by_name = {c.name: c for c in old.constraints}
        new_by_name = {c.name: c for c in new.constraints}

        remove_ops: list[Operation] = [
            RemoveConstraint(model=model, constraint=old_by_name[name])
            for name in sorted(set(old_by_name) - set(new_by_name))
        ]
        alter_ops: list[Operation] = [
            AlterConstraint(model=model, old_constraint=old_by_name[name], new_constraint=new_by_name[name])
            for name in sorted(set(old_by_name) & set(new_by_name))
            if old_by_name[name] != new_by_name[name]
        ]
        add_ops: list[Operation] = [
            AddConstraint(model=model, constraint=new_by_name[name])
            for name in sorted(set(new_by_name) - set(old_by_name))
        ]
        return [*remove_ops, *alter_ops, *add_ops]

    def _detect_relations(self, model: str, old: TableState, new: TableState) -> list[Operation]:
        """Emit junction-table creations and deletions for one model.

        Returns:
            The operations, additions before removals.
        """
        old_by_name = {relation.name: relation for relation in old.m2m}
        new_by_name = {relation.name: relation for relation in new.m2m}

        add_ops: list[Operation] = [
            CreateManyToManyTable(model=model, relation=new_by_name[name])
            for name in sorted(set(new_by_name) - set(old_by_name))
        ]
        remove_ops: list[Operation] = [
            DeleteManyToManyTable(model=model, relation=old_by_name[name])
            for name in sorted(set(old_by_name) - set(new_by_name))
        ]
        return [*add_ops, *remove_ops]

    def _detect_options(self, model: str, old: TableState, new: TableState) -> list[Operation]:
        """Emit an :class:`AlterModelOptions` when table options changed.

        Returns:
            One operation, or none.
        """
        if old.options == new.options:
            return []
        return [AlterModelOptions(model=model, old_options=dict(old.options), new_options=dict(new.options))]

    # ── Rename matching ─────────────────────────────────────────────────

    def _match_renames(
        self,
        model: str,
        old: TableState,
        new: TableState,
        removed: list[str],
        added: list[str],
    ) -> list[tuple[str, str]]:
        """Pair removed columns with added ones that are the same column renamed.

        Explicit hints are honoured unconditionally. Beyond those, a pair is
        matched only when :meth:`_rename_confidence` clears
        :data:`RENAME_CONFIDENCE_THRESHOLD`, and only when that best candidate is
        unambiguous -- if two added columns score equally well against the same
        removed column, neither is chosen, because picking either would be a
        coin flip that destroys data half the time.

        Args:
            model: The model being diffed.
            old: Its previous table state.
            new: Its current table state.
            removed: Names present only in *old*, sorted.
            added: Names present only in *new*, sorted.

        Returns:
            ``(old_name, new_name)`` pairs, ordered by old name.
        """
        if not removed or not added:
            return []

        pairs: list[tuple[str, str]] = []
        claimed_old: set[str] = set()
        claimed_new: set[str] = set()

        for hint in self.hints:
            if hint.model != model:
                continue
            if hint.old_name in removed and hint.new_name in added:
                pairs.append((hint.old_name, hint.new_name))
                claimed_old.add(hint.old_name)
                claimed_new.add(hint.new_name)

        if not self.infer_renames:
            return sorted(pairs)

        for old_name in removed:
            if old_name in claimed_old:
                continue
            scored = sorted(
                (
                    (self._rename_confidence(old.columns[old_name], new.columns[new_name]), new_name)
                    for new_name in added
                    if new_name not in claimed_new
                ),
                key=lambda item: (-item[0], item[1]),
            )
            if not scored:
                continue
            best_score, best_name = scored[0]
            if best_score < RENAME_CONFIDENCE_THRESHOLD:
                continue
            # Refuse an ambiguous match rather than guessing between equals.
            if len(scored) > 1 and abs(scored[1][0] - best_score) < 1e-9:
                continue
            pairs.append((old_name, best_name))
            claimed_old.add(old_name)
            claimed_new.add(best_name)

        return sorted(pairs)

    @staticmethod
    def _rename_confidence(old: ColumnState, new: ColumnState) -> float:
        """Score how likely it is that *new* is *old* renamed, in ``[0, 1]``.

        Independent signals are combined, each weighted so that no single one
        can clear the threshold alone:

        * Same field class (0.30) -- necessary but far from sufficient.
        * Identical field arguments, e.g. ``max_length`` (0.20).
        * Matching nullability, uniqueness, and primary-key flags (0.15).
        * Identical foreign-key target (0.15) -- strong, since it means both
          columns point at the same table and column.
        * Name similarity (0.20, scaled) -- a real rename usually keeps some of
          the name (``name`` to ``full_name``), whereas two unrelated columns
          rarely resemble each other.

        A same-typed pair with an unrelated name scores about 0.65, safely below
        the 0.85 threshold. Weighting the field class at 0.70 against a 0.60
        threshold instead would make any two same-typed columns match.

        Args:
            old: The removed column.
            new: The added column.

        Returns:
            The confidence score.
        """
        if old.field_class != new.field_class:
            return 0.0

        score = 0.30
        if old.field_kwargs == new.field_kwargs:
            score += 0.20
        if (old.null, old.unique, old.primary_key) == (new.null, new.unique, new.primary_key):
            score += 0.15
        if old.reference is not None and new.reference is not None:
            if (old.reference.table, old.reference.column) == (new.reference.table, new.reference.column):
                score += 0.15
        elif old.reference is None and new.reference is None:
            score += 0.05

        similarity = SequenceMatcher(None, old.name, new.name).ratio()
        score += 0.20 * similarity
        return score


def detect_changes(
    before: ProjectState,
    after: ProjectState,
    *,
    hints: tuple[RenameHint, ...] = (),
    infer_renames: bool = True,
) -> list[Operation]:
    """Return the operations transforming *before* into *after*.

    Convenience wrapper around :class:`Autodetector`.

    Args:
        before: The starting state.
        after: The target state.
        hints: Explicit rename instructions.
        infer_renames: Whether to attempt rename inference at all.

    Returns:
        The operations, in application order.

    Example:
        >>> detect_changes(old_state, new_state)
        [AddField(model='User', ...)]
    """
    return Autodetector(before=before, after=after, hints=hints, infer_renames=infer_renames).detect()
