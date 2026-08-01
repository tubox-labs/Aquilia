"""
Aquilia migrations -- top-level engine.

The single entry point for generating, planning, applying, and rolling back
migrations. Everything the CLI and the server startup path need is here.

Responsibilities are delegated, not duplicated:

* :mod:`~aquilia.models.migration.schema` builds state from models.
* :mod:`~aquilia.models.migration.autodetect` diffs two states.
* :mod:`~aquilia.models.migration.optimizer` reduces the resulting operations.
* :mod:`~aquilia.models.migration.serializer` writes and reads migration files.
* :mod:`~aquilia.models.migration.graph` orders migrations.
* :mod:`~aquilia.models.migration.executor` runs them.

Snapshot handling
-----------------
The last known state is stored as a snapshot artifact beside the migrations.
Writing the snapshot *before* the migration file means a failure to write the
file left the snapshot advanced and the change unrecoverable -- the next
``makemigrations`` would see no diff and generate nothing. Here the file is
written first and the snapshot only after it lands.
"""

from __future__ import annotations

import datetime
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from aquilia.artifacts.backends.json_file import JSONFileBackend
from aquilia.artifacts.canonical import bare_fingerprint
from aquilia.artifacts.envelope import ArtifactEnvelope
from aquilia.faults.domains import MigrationFault
from aquilia.models.migration.autodetect import RenameHint, detect_changes
from aquilia.models.migration.graph import MigrationGraph, MigrationNode
from aquilia.models.migration.optimizer import optimize
from aquilia.models.migration.schema import ProjectState
from aquilia.models.migration.serializer import load_migration_module, render_migration_module

if TYPE_CHECKING:
    from collections.abc import Iterable

    from aquilia.db.engine import AquiliaDatabase
    from aquilia.models.base import Model
    from aquilia.models.migration.backends import Statement
    from aquilia.models.migration.executor import ExecutionResult

logger = logging.getLogger("aquilia.models.migration.engine")

__all__ = ["MigrationEngine", "MigrationStatus", "SNAPSHOT_FILENAME"]

SNAPSHOT_FILENAME = "schema_snapshot.json"
"""Filename of the state snapshot stored alongside migration files."""


@dataclass
class MigrationStatus:
    """A summary of applied and pending migrations.

    Attributes:
        applied: Revisions already applied, in application order.
        pending: Migrations not yet applied, in dependency order.
        leaves: Tips of the migration graph. More than one means the history
            has branched.
    """

    applied: tuple[str, ...] = ()
    pending: tuple[MigrationNode, ...] = ()
    leaves: tuple[str, ...] = ()

    @property
    def is_current(self) -> bool:
        """Whether every migration on disk has been applied."""
        return not self.pending

    def describe(self) -> str:
        """Return a human-readable multi-line summary."""
        lines = [
            f"Applied: {len(self.applied)}",
            f"Pending: {len(self.pending)}",
        ]
        if self.applied:
            lines.append(f"Last applied: {self.applied[-1]}")
        for node in self.pending:
            lines.append(f"  - {node.name}")
        if len(self.leaves) > 1:
            lines.append(f"WARNING: migration history has branched: {', '.join(self.leaves)}")
        return "\n".join(lines)


class MigrationEngine:
    """Generates, plans, applies, and rolls back migrations.

    Attributes:
        migrations_dir: Directory holding migration files and the snapshot.

    Example::

        engine = MigrationEngine("migrations")
        path = engine.make_migrations([User, Post])
        await engine.migrate(db)
    """

    def __init__(self, migrations_dir: str | Path = "migrations") -> None:
        """Bind the engine to a migrations directory.

        Args:
            migrations_dir: Where migration files and the snapshot live.
        """
        self.migrations_dir = Path(migrations_dir)

    # ── Generation ──────────────────────────────────────────────────────

    def make_migrations(
        self,
        model_classes: list[type[Model]],
        *,
        slug: str | None = None,
        hints: tuple[RenameHint, ...] = (),
        infer_renames: bool = True,
        dry_run: bool = False,
    ) -> Path | None:
        """Generate a migration for the difference between the snapshot and the models.

        Args:
            model_classes: The models to snapshot.
            slug: Filename suffix. Derived from the affected models when omitted.
            hints: Explicit rename instructions; see
                :class:`~aquilia.models.migration.autodetect.RenameHint`.
            infer_renames: Whether to attempt rename inference at all.
            dry_run: Compute the migration but write nothing.

        Returns:
            The path written, or ``None`` when the models already match the
            snapshot or *dry_run* was set.

        Raises:
            MigrationFault: If the models cannot be snapshotted, or an operation
                cannot be serialized.

        Example:
            >>> engine.make_migrations([User, Post], slug="add_bio")
            PosixPath('migrations/20260730_143000_add_bio.py')
        """
        before = self.load_snapshot()
        after = ProjectState.from_models(model_classes)

        operations = optimize(detect_changes(before, after, hints=hints, infer_renames=infer_renames))
        if not operations:
            return None

        revision = self._next_revision()
        node = MigrationNode(
            revision=revision,
            slug=slug or self._derive_slug(operations),
            operations=tuple(operations),
            dependencies=self._current_leaves(),
            atomic=all(op.atomic for op in operations),
        )

        if dry_run:
            return None

        self.migrations_dir.mkdir(parents=True, exist_ok=True)
        path = self.migrations_dir / f"{node.name}.py"
        source = render_migration_module(
            node,
            generated_at=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        )

        # Write the migration first, snapshot second. If the write fails, the
        # snapshot still describes the last successfully generated migration and
        # the change can simply be regenerated. Writing them the other way
        # round, which lost the diff on any failure.
        path.write_text(source, encoding="utf-8")
        self.save_snapshot(after)
        return path

    def _derive_slug(self, operations: list) -> str:
        """Build a filename slug from the models an operation list touches."""
        models = sorted(
            {
                model
                for operation in operations
                for model in (
                    getattr(operation, "model", None),
                    getattr(operation, "new_model", None),
                )
                if model
            }
        )
        if not models:
            return "migration"
        if len(models) <= 3:
            return "_".join(name.lower() for name in models)
        return "_".join(name.lower() for name in models[:3]) + f"_and_{len(models) - 3}_more"

    def _next_revision(self) -> str:
        """Generate a timestamp revision, stepping past any collision.

        Two migrations generated in the same second would otherwise share a
        revision, which the graph rejects as ambiguous.
        """
        existing = {node.revision for node in self.load_graph().nodes.values()}
        stamp = datetime.datetime.now(datetime.timezone.utc)
        for _ in range(100):
            candidate = stamp.strftime("%Y%m%d_%H%M%S")
            if candidate not in existing:
                return candidate
            stamp += datetime.timedelta(seconds=1)
        raise MigrationFault(
            migration="engine",
            reason="Could not allocate a unique migration revision after 100 attempts.",
        )

    def _current_leaves(self) -> tuple[str, ...]:
        """Return the revisions a newly generated migration should depend on."""
        graph = self.load_graph()
        return graph.leaves() if graph.nodes else ()

    # ── Snapshot ────────────────────────────────────────────────────────

    @property
    def snapshot_path(self) -> Path:
        """Path to the state snapshot artifact."""
        return self.migrations_dir / SNAPSHOT_FILENAME

    def load_snapshot(self) -> ProjectState:
        """Load the last recorded project state.

        Returns:
            The stored state, or an empty state when no snapshot exists yet.

        Raises:
            MigrationFault: If the snapshot exists but its version is newer than
                this release understands.
        """
        path = self.snapshot_path
        if not path.exists():
            return ProjectState()

        try:
            raw = JSONFileBackend().read_sync(path)
        except Exception as exc:
            logger.warning("Cannot read schema snapshot %s: %s. Treating as empty.", path, exc)
            return ProjectState()

        if raw is None:
            return ProjectState()
        if isinstance(raw, dict) and raw.get("format") == "aquilia-artifact":
            raw = ArtifactEnvelope.from_dict(raw).payload
        if not isinstance(raw, dict):
            return ProjectState()

        # A pre-rewrite snapshot has a "models" mapping where this format has "tables".
        if "tables" not in raw and "models" in raw:
            logger.info(
                "Schema snapshot at %s is in a superseded format and cannot describe "
                "many-to-many relations, generated columns, or index methods. It will be "
                "replaced on the next makemigrations.",
                path,
            )
            return ProjectState()

        return ProjectState.from_dict(raw)

    def save_snapshot(self, state: ProjectState) -> None:
        """Write *state* to the snapshot artifact.

        Args:
            state: The state to record.
        """

        payload = state.to_dict()
        self.migrations_dir.mkdir(parents=True, exist_ok=True)
        envelope = ArtifactEnvelope.build(
            artifact_type="schema_snapshot",
            key="main",
            schema_version="2.0",
            payload=payload,
            fingerprint=bare_fingerprint(payload),
        )
        JSONFileBackend().write_sync(self.snapshot_path, envelope.to_dict())

    # ── Graph ───────────────────────────────────────────────────────────

    def load_graph(self) -> MigrationGraph:
        """Load every migration file into a dependency graph.

        Returns:
            The graph. Empty when the directory does not exist.

        Raises:
            MigrationFault: If a migration file cannot be imported, or two files
                claim the same revision.
        """
        graph = MigrationGraph()
        if not self.migrations_dir.exists():
            return graph
        for path in sorted(self.migrations_dir.glob("*.py")):
            if path.name.startswith("__"):
                continue
            graph.add(load_migration_module(path))
        return graph

    def state_at(self, revision: str | None = None) -> ProjectState:
        """Replay migrations to reconstruct the state at a given point.

        Rebuilding state from the migration files -- rather than trusting the
        snapshot -- is what makes it possible to verify that the two agree, and
        to recover when a snapshot is lost or corrupt.

        Args:
            revision: Replay up to and including this revision. ``None`` replays
                everything.

        Returns:
            The reconstructed state.

        Raises:
            MigrationFault: If the graph is invalid, or *revision* is unknown.
        """
        graph = self.load_graph()
        order = graph.order()
        if revision is not None and revision not in order:
            raise MigrationFault(
                migration=revision,
                reason=f"Revision {revision!r} is not present in the migration graph.",
            )

        state = ProjectState()
        for candidate in order:
            for operation in graph.nodes[candidate].operations:
                operation.state_forwards(state)
            if candidate == revision:
                break
        return state

    def state_for(self, applied: Iterable[str]) -> ProjectState:
        """Reconstruct the state produced by exactly the *applied* revisions.

        Differs from :meth:`state_at` in that it replays a *set* rather than a
        prefix: a revision on disk but not applied is skipped even when it sorts
        before an applied one, which is what happens whenever a branch is merged
        or a migration is added out of order.

        Args:
            applied: Revisions recorded as applied, in any order.

        Returns:
            The reconstructed state.

        Raises:
            MigrationFault: If the graph is invalid.

        Example:
            >>> state = engine.state_for(await executor.applied_revisions())
        """
        graph = self.load_graph()
        wanted = set(applied)
        state = ProjectState()
        for candidate in graph.order():
            if candidate not in wanted:
                continue
            for operation in graph.nodes[candidate].operations:
                operation.state_forwards(state)
        return state

    # ── Planning and execution ──────────────────────────────────────────

    async def status(self, db: AquiliaDatabase) -> MigrationStatus:
        """Report which migrations are applied and which are pending.

        Args:
            db: The database to inspect.

        Returns:
            The status summary.
        """
        from aquilia.models.migration.executor import MigrationExecutor

        executor = MigrationExecutor(db)
        applied = await executor.applied_revisions()
        graph = self.load_graph()
        return MigrationStatus(
            applied=tuple(applied),
            pending=graph.forward_plan(set(applied)) if graph.nodes else (),
            leaves=graph.leaves() if graph.nodes else (),
        )

    async def plan(self, db: AquiliaDatabase, *, target: str | None = None) -> list[Statement]:
        """Compile the pending migrations to SQL without executing anything.

        Args:
            db: The database, consulted for its dialect and applied revisions.
            target: Plan a rollback to this revision instead of a forward run.

        Returns:
            The statements that would run, in execution order.

        Raises:
            MigrationFault: If the plan cannot be compiled -- for instance an
                irreversible operation in a rollback plan.
        """
        from aquilia.models.migration.executor import MigrationExecutor, compile_operations

        executor = MigrationExecutor(db)
        applied = await executor.applied_revisions()
        graph = self.load_graph()

        statements: list[Statement] = []
        if target is not None:
            for node in graph.backward_plan(applied, target):
                state = self.state_at(node.revision)
                statements.extend(compile_operations(node.operations, state, executor.backend, reverse=True))
            return statements

        state = self.state_for(applied)
        for node in graph.forward_plan(set(applied)):
            statements.extend(compile_operations(node.operations, state, executor.backend))
        return statements

    async def migrate(
        self,
        db: AquiliaDatabase,
        *,
        target: str | None = None,
        fake: bool = False,
    ) -> list[ExecutionResult]:
        """Apply pending migrations, or roll back to *target*.

        Args:
            db: The database to migrate.
            target: Roll back everything applied after this revision. ``None``
                applies pending migrations forward.
            fake: Record or unrecord migrations without executing them.

        Returns:
            One result per migration processed.

        Raises:
            MigrationFault: If a migration fails, or the graph is invalid.

        Example:
            >>> await engine.migrate(db)
            [ExecutionResult(statements_executed=4, ...)]
        """
        from aquilia.models.migration.executor import MigrationExecutor

        executor = MigrationExecutor(db)
        await executor.ensure_tracking_table()
        applied = await executor.applied_revisions()
        graph = self.load_graph()
        if not graph.nodes:
            return []
        graph.check_conflicts()

        results: list[ExecutionResult] = []

        if target is not None:
            for node in graph.backward_plan(applied, target):
                state = self.state_at(node.revision)
                results.append(await executor.rollback(node, state, fake=fake))
            return results

        state = self.state_for(applied)
        for node in graph.forward_plan(set(applied)):
            results.append(await executor.apply(node, state, fake=fake))
        return results

    async def verify_checksums(self, db: AquiliaDatabase) -> list[dict[str, str]]:
        """Report applied migrations whose files no longer match what was applied.

        Args:
            db: The database to inspect.

        Returns:
            One entry per mismatch, with ``revision`` and ``reason``.
        """
        from aquilia.models.migration.executor import MigrationExecutor

        executor = MigrationExecutor(db)
        await executor.ensure_tracking_table()
        rows = await db.fetch_all(
            f"SELECT {executor.backend.quote('revision')}, {executor.backend.quote('checksum')} "
            f"FROM {executor.backend.quote(executor.table)} ORDER BY {executor.backend.quote('id')}"
        )
        graph = self.load_graph()

        mismatches: list[dict[str, str]] = []
        for row in rows:
            revision = row["revision"]
            recorded = row.get("checksum")
            if not recorded:
                continue
            node = graph.nodes.get(revision)
            if node is None:
                mismatches.append({"revision": revision, "reason": "Migration file is missing from disk"})
            elif node.checksum != recorded:
                mismatches.append({"revision": revision, "reason": "File has changed since it was applied"})
        return mismatches
