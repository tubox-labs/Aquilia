"""
Aquilia migrations -- migration graph.

Models the set of migrations on disk as a directed acyclic graph and computes
the order in which they must be applied or rolled back.

An earlier design had no graph. ``Migration.dependencies`` existed and was written into every
generated file, but nothing read it -- ordering came from sorting filenames,
and the field's own docstring conceded it was "currently informational
bookkeeping". That works only while every migration is generated on one machine
in one linear sequence. Two developers each generating a migration on the same
day produce filenames that sort by timestamp into an order neither intended, and
a migration depending on another from a different module has no way to say so.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ...faults.domains import MigrationConflictFault, MigrationFault

if TYPE_CHECKING:
    from pathlib import Path

    from .operations import Operation

__all__ = ["MigrationNode", "MigrationGraph"]


@dataclass(frozen=True)
class MigrationNode:
    """One migration in the graph.

    Attributes:
        revision: Unique revision identifier, normally ``YYYYMMDD_HHMMSS``.
        slug: Human-readable description used in the filename.
        operations: The operations this migration applies, in order.
        dependencies: Revisions that must be applied before this one.
        replaces: Revisions this migration squashes. When every replaced
            revision is already applied, this one is recorded as applied without
            executing, which is what makes squashing safe on a deployed database.
        atomic: Whether the whole migration runs in one transaction. Forced off
            when any operation emits a non-transactional statement.
        source_path: The file this was loaded from, if any.
        checksum: Digest of the source file, for tamper detection.
    """

    revision: str
    slug: str = ""
    operations: tuple[Operation, ...] = ()
    dependencies: tuple[str, ...] = ()
    replaces: tuple[str, ...] = ()
    atomic: bool = True
    source_path: Path | None = None
    checksum: str = ""

    @property
    def name(self) -> str:
        """The migration's filename stem, e.g. ``"20260730_120000_add_user"``."""
        return f"{self.revision}_{self.slug}" if self.slug else self.revision

    def describe(self) -> str:
        """Return a multi-line summary of this migration and its operations."""
        lines = [f"Migration {self.name}"]
        if self.dependencies:
            lines.append(f"  Depends on: {', '.join(self.dependencies)}")
        if self.replaces:
            lines.append(f"  Replaces: {', '.join(self.replaces)}")
        for operation in self.operations:
            lines.append(f"    - {operation.describe()}")
        return "\n".join(lines)


@dataclass
class MigrationGraph:
    """A dependency graph over migrations, with topological planning.

    Attributes:
        nodes: Migrations by revision.

    Example::

        graph = MigrationGraph()
        graph.add(MigrationNode(revision="0001", slug="initial"))
        graph.add(MigrationNode(revision="0002", slug="add_bio", dependencies=("0001",)))
        graph.forward_plan(applied=set())
    """

    nodes: dict[str, MigrationNode] = field(default_factory=dict)

    # ── Construction ────────────────────────────────────────────────────

    def add(self, node: MigrationNode) -> None:
        """Add a migration to the graph.

        Args:
            node: The migration to add.

        Raises:
            MigrationFault: If a different migration already uses this revision.
                Two migrations sharing a revision makes the applied-migrations
                table ambiguous -- there is no way to tell which one ran.
        """
        existing = self.nodes.get(node.revision)
        if existing is not None and existing != node:
            raise MigrationFault(
                migration=node.revision,
                reason=(
                    f"Duplicate migration revision {node.revision!r}: both "
                    f"{existing.name!r} and {node.name!r} claim it. Revisions must be "
                    f"unique; rename one of the files."
                ),
            )
        self.nodes[node.revision] = node

    def validate(self) -> None:
        """Check that every dependency resolves and no cycle exists.

        Raises:
            MigrationFault: If a migration depends on a revision that is not in
                the graph -- usually a deleted file or a missing merge.
            MigrationConflictFault: If the dependencies form a cycle, which
                cannot be applied in any order.
        """
        for node in self.nodes.values():
            for dependency in node.dependencies:
                if dependency not in self.nodes:
                    raise MigrationFault(
                        migration=node.revision,
                        reason=(
                            f"Migration {node.name!r} depends on revision {dependency!r}, "
                            f"which does not exist. The file may have been deleted or "
                            f"never committed."
                        ),
                    )
        cycle = self._find_cycle()
        if cycle:
            raise MigrationConflictFault(conflicting=list(cycle))

    def _find_cycle(self) -> tuple[str, ...] | None:
        """Return a dependency cycle if one exists, otherwise ``None``."""
        WHITE, GREY, BLACK = 0, 1, 2
        colour = dict.fromkeys(self.nodes, WHITE)
        stack: list[str] = []

        def visit(revision: str) -> tuple[str, ...] | None:
            colour[revision] = GREY
            stack.append(revision)
            for dependency in sorted(self.nodes[revision].dependencies):
                if dependency not in colour:
                    continue
                if colour[dependency] == GREY:
                    start = stack.index(dependency)
                    return tuple(stack[start:])
                if colour[dependency] == WHITE:
                    found = visit(dependency)
                    if found:
                        return found
            stack.pop()
            colour[revision] = BLACK
            return None

        for revision in sorted(self.nodes):
            if colour[revision] == WHITE:
                found = visit(revision)
                if found:
                    return found
        return None

    # ── Planning ────────────────────────────────────────────────────────

    def order(self) -> tuple[str, ...]:
        """Return every revision in dependency order.

        Migrations with no dependency relationship between them are ordered by
        revision, so the result is fully deterministic rather than dependent on
        insertion order.

        Returns:
            Revisions, dependencies first.

        Raises:
            MigrationFault: If a dependency is missing.
            MigrationConflictFault: If the graph contains a cycle.
        """
        self.validate()

        ordered: list[str] = []
        visited: set[str] = set()

        def visit(revision: str) -> None:
            if revision in visited:
                return
            visited.add(revision)
            for dependency in sorted(self.nodes[revision].dependencies):
                visit(dependency)
            ordered.append(revision)

        for revision in sorted(self.nodes):
            visit(revision)
        return tuple(ordered)

    def forward_plan(self, applied: set[str]) -> tuple[MigrationNode, ...]:
        """Return the migrations to apply, in order.

        A squashing migration is skipped when the migrations it replaces are all
        already applied, since the schema already reflects them.

        Args:
            applied: Revisions already recorded as applied.

        Returns:
            The pending migrations, in dependency order.
        """
        plan: list[MigrationNode] = []
        for revision in self.order():
            if revision in applied:
                continue
            node = self.nodes[revision]
            if node.replaces and all(replaced in applied for replaced in node.replaces):
                continue
            plan.append(node)
        return tuple(plan)

    def backward_plan(self, applied: list[str], target: str | None) -> tuple[MigrationNode, ...]:
        """Return the migrations to roll back, in order.

        Args:
            applied: Revisions currently applied, in application order.
            target: Roll back everything applied *after* this revision. ``None``
                or ``"zero"`` rolls back everything.

        Returns:
            The migrations to reverse, most recent first.

        Raises:
            MigrationFault: If *target* is not among the applied revisions.
        """
        if target in (None, "zero"):
            to_reverse = list(reversed(applied))
        else:
            if target not in applied:
                raise MigrationFault(
                    migration=str(target),
                    reason=(
                        f"Cannot roll back to revision {target!r}: it is not applied. "
                        f"Applied revisions: {', '.join(applied) or '(none)'}."
                    ),
                )
            to_reverse = list(reversed(applied[applied.index(target) + 1 :]))

        plan: list[MigrationNode] = []
        for revision in to_reverse:
            node = self.nodes.get(revision)
            if node is None:
                raise MigrationFault(
                    migration=revision,
                    reason=(
                        f"Cannot roll back revision {revision!r}: its migration file is "
                        f"missing, so the operations to reverse are unknown. Restore the "
                        f"file, or mark the revision unapplied manually."
                    ),
                )
            plan.append(node)
        return tuple(plan)

    def leaves(self) -> tuple[str, ...]:
        """Return revisions nothing depends on -- the graph's tips.

        More than one leaf means the history has branched, typically because two
        developers generated a migration from the same parent. Applying both is
        safe only if they touch different models; otherwise a merge migration is
        needed.

        Returns:
            The leaf revisions, sorted.
        """
        depended_upon = {dep for node in self.nodes.values() for dep in node.dependencies}
        return tuple(sorted(set(self.nodes) - depended_upon))

    def check_conflicts(self) -> None:
        """Raise if the history has branched into conflicting leaves.

        Raises:
            MigrationConflictFault: If two or more leaves touch the same model,
                which means applying both in either order gives a different
                result. Independent branches are left alone.
        """
        leaves = self.leaves()
        if len(leaves) < 2:
            return

        touched: dict[str, set[str]] = {}
        for revision in leaves:
            models: set[str] = set()
            for operation in self.nodes[revision].operations:
                model = getattr(operation, "model", None) or getattr(operation, "new_model", None)
                if model:
                    models.add(model)
            touched[revision] = models

        for index, first in enumerate(leaves):
            for second in leaves[index + 1 :]:
                if touched[first] & touched[second]:
                    raise MigrationConflictFault(conflicting=[first, second])
