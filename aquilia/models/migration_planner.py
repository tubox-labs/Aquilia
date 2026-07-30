"""
Aquilia Migration Planner -- Planning authority for initial schema and incremental migrations.

Separates migration planning from ModelRegistry metadata ownership and
DDLExecutor statement execution.

Features:
- Dedicated InitialSchemaPlanner for constructing clean initial DDL plans
  directly from model metadata without synthetic empty-snapshot diffing.
- Incremental MigrationPlanner for snapshot diffing and pending migration files.
- Strongly-typed MigrationPlan and MigrationStep intermediate structures.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .base import Model
    from .migration_dsl import Operation

logger = logging.getLogger("aquilia.models.migration_planner")

__all__ = [
    "MigrationStep",
    "MigrationPlan",
    "InitialSchemaPlanner",
    "MigrationPlanner",
]


@dataclass
class MigrationStep:
    """A single logical migration step within an overall execution plan.

    Attributes:
        revision: Timestamp or revision identifier for this step.
        slug: Human-readable slug describing the step.
        operations: List of typed DSL Operation objects to execute.
        models: List of model class names affected by this step.
        dependencies: List of revision IDs required before this step.
        checksum: Truncated SHA-256 digest of the source migration file (if file-backed).
        is_initial: True if this step represents the zero-revision initial schema creation.
        source_path: Path to the underlying migration file on disk, if applicable.
    """

    revision: str
    slug: str
    operations: list[Operation] = field(default_factory=list)
    models: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    checksum: str = ""
    is_initial: bool = False
    source_path: Path | None = None


@dataclass
class MigrationPlan:
    """An ordered collection of migration steps to be executed by MigrationRunner.

    Attributes:
        steps: Ordered list of MigrationStep objects.
        target_db: Database alias or connection identifier, if specified.
        is_initial: True if this plan represents an initial schema setup.
    """

    steps: list[MigrationStep] = field(default_factory=list)
    target_db: str | None = None
    is_initial: bool = False

    @property
    def is_empty(self) -> bool:
        """Return True if the plan contains no steps or operations."""
        return not self.steps or all(len(s.operations) == 0 for s in self.steps)

    def all_operations(self) -> list[Operation]:
        """Flatten and return all operations across all steps in order."""
        ops: list[Operation] = []
        for step in self.steps:
            ops.extend(step.operations)
        return ops


class InitialSchemaPlanner:
    """Dedicated planner for constructing initial schema plans directly from model metadata.

    Eliminates the historical split-brain pattern where initial schema creation
    diffed against a synthetic empty snapshot.
    """

    @classmethod
    def plan_from_models(cls, model_classes: list[type[Model]]) -> MigrationStep:
        """Construct a clean, single-step MigrationStep creating all tables for the given models.

        Args:
            model_classes: Dependency-ordered list of concrete Model subclasses
                (typically from ``ModelRegistry._topological_sort()``).

        Returns:
            MigrationStep: Initial schema creation step with CreateModel, CreateIndex,
            and AddConstraint operations.
        """
        from .fields_module import ForeignKey, OneToOneField
        from .migration_dsl import (
            _SENTINEL,
            AddConstraint,
            ColumnDef,
            CreateIndex,
            CreateModel,
        )

        operations: list[Operation] = []
        model_names: list[str] = []

        for model_cls in model_classes:
            meta = model_cls._meta
            if meta.abstract or not meta.managed:
                continue

            name = model_cls.__name__
            table = meta.table_name
            model_names.append(name)

            col_defs: list[ColumnDef] = []
            indexes: list[CreateIndex] = []

            # 1. Build ColumnDefs for model fields
            for field_name, fld in model_cls._fields.items():
                col_name = getattr(fld, "column_name", None) or getattr(fld, "db_column", None) or field_name
                sql_type = cls._resolve_field_sql_type(fld)

                is_pk = getattr(fld, "primary_key", False)
                is_auto = is_pk and type(fld).__name__ in ("AutoField", "BigAutoField")
                is_uniq = getattr(fld, "unique", False)
                is_null = getattr(fld, "null", False)

                default_val = _SENTINEL
                if hasattr(fld, "default") and fld.default is not None:
                    from .fields_module import UNSET

                    if fld.default is not UNSET:
                        default_val = fld.default

                ref_tuple = None
                on_del = "CASCADE"
                on_upd = "CASCADE"
                if isinstance(fld, (ForeignKey, OneToOneField)):
                    ref_table = cls._resolve_ref_table(fld.to, model_classes)
                    target_col = "id"
                    ref_tuple = (ref_table, target_col)
                    on_del = getattr(fld, "on_delete", "CASCADE")
                    on_upd = getattr(fld, "on_update", "CASCADE")

                col_defs.append(
                    ColumnDef(
                        name=col_name,
                        col_type=sql_type,
                        primary_key=is_pk,
                        autoincrement=is_auto,
                        unique=is_uniq,
                        nullable=is_null,
                        default=default_val,
                        references=ref_tuple,
                        on_delete=on_del,
                        on_update=on_upd,
                    )
                )

                # Track db_index=True
                if getattr(fld, "db_index", False) and not is_pk:
                    idx_name = f"idx_{table}_{col_name}"
                    indexes.append(CreateIndex(name=idx_name, table=table, columns=[col_name], unique=is_uniq))

            # Add CreateModel operation
            operations.append(CreateModel(name=name, table=table, fields=col_defs))

            # Add Table-level indexes from Meta
            for idx in getattr(meta, "indexes", []):
                idx_name = getattr(idx, "name", None)
                idx_fields = getattr(idx, "fields", [])
                if isinstance(idx_fields, (tuple, set)):
                    idx_fields = list(idx_fields)
                if not idx_name:
                    idx_name = f"idx_{table}_{'_'.join(str(f) for f in idx_fields)}"
                indexes.append(
                    CreateIndex(
                        name=idx_name,
                        table=table,
                        columns=[str(f) for f in idx_fields],
                        unique=getattr(idx, "unique", False),
                    )
                )

            # Deduplicate and add index operations
            seen_idx_names = set()
            for idx_op in indexes:
                if idx_op.name not in seen_idx_names:
                    operations.append(idx_op)
                    seen_idx_names.add(idx_op.name)

            # Table-level constraints from Meta
            for constraint in getattr(meta, "constraints", []):
                c_name = getattr(constraint, "name", f"c_{table}")
                operations.append(AddConstraint(table=table, name=c_name, constraint_def=str(constraint)))

        return MigrationStep(
            revision="0000_initial_schema",
            slug="initial_schema",
            operations=operations,
            models=model_names,
            dependencies=[],
            checksum="0000000000000000",
            is_initial=True,
        )

    @staticmethod
    def _resolve_field_sql_type(fld: Any) -> str:
        """Map a model field descriptor to its basic SQL type string."""
        type_name = type(fld).__name__

        if type_name in ("AutoField", "IntegerField"):
            return "INTEGER"
        elif type_name in ("BigAutoField", "BigIntegerField"):
            return "BIGINT"
        elif type_name == "CharField":
            length = getattr(fld, "max_length", 255) or 255
            return f"VARCHAR({length})"
        elif type_name in ("TextField", "JSONField"):
            return "TEXT"
        elif type_name == "BooleanField":
            return "BOOLEAN"
        elif type_name in ("DateTimeField", "TimestampField"):
            return "TIMESTAMP"
        elif type_name == "DateField":
            return "DATE"
        elif type_name == "TimeField":
            return "TIME"
        elif type_name == "FloatField":
            return "REAL"
        elif type_name == "DecimalField":
            digits = getattr(fld, "max_digits", 10) or 10
            places = getattr(fld, "decimal_places", 2) or 2
            return f"DECIMAL({digits},{places})"
        elif type_name == "BinaryField":
            return "BLOB"
        elif type_name == "UUIDField":
            return "VARCHAR(36)"

        if hasattr(fld, "sql_type") and callable(fld.sql_type):
            return fld.sql_type()

        return "VARCHAR(255)"

    @staticmethod
    def _resolve_ref_table(to_ref: Any, model_classes: list[type[Model]]) -> str:
        """Resolve a foreign key target reference to table name."""
        if isinstance(to_ref, type) and hasattr(to_ref, "_meta"):
            return getattr(to_ref._meta, "table_name", to_ref.__name__.lower())
        if isinstance(to_ref, str):
            target = to_ref.split(".")[-1]
            for m in model_classes:
                if m.__name__ == target:
                    return getattr(m._meta, "table_name", target.lower())
        return str(to_ref).lower()


class MigrationPlanner:
    """Primary planning authority for generating MigrationPlan structures."""

    @classmethod
    def plan_initial_schema(
        cls,
        model_classes: list[type[Model]] | None = None,
    ) -> MigrationPlan:
        """Generate a MigrationPlan for initial schema creation.

        Args:
            model_classes: Optional explicit list of model classes to plan for.
                If None, fetches registered models from ModelRegistry.

        Returns:
            MigrationPlan: Initial schema migration plan.
        """
        if model_classes is None:
            from .registry import ModelRegistry

            model_classes = ModelRegistry._topological_sort()

        step = InitialSchemaPlanner.plan_from_models(model_classes)
        return MigrationPlan(steps=[step], is_initial=True)

    @classmethod
    def plan_incremental(
        cls,
        old_snapshot: dict[str, Any],
        new_snapshot: dict[str, Any],
        *,
        revision: str = "",
        slug: str = "",
    ) -> MigrationPlan:
        """Generate an incremental MigrationPlan by diffing two schema snapshots.

        Args:
            old_snapshot: Previous schema snapshot dict.
            new_snapshot: Current schema snapshot dict.
            revision: Revision timestamp string.
            slug: Migration slug description.

        Returns:
            MigrationPlan: Incremental migration plan containing the diff operations.
        """
        from .schema_snapshot import compute_diff, diff_to_operations

        diff = compute_diff(old_snapshot, new_snapshot)
        operations = diff_to_operations(diff, old_snapshot, new_snapshot)

        checksum_bytes = f"{revision}:{slug}:{len(operations)}".encode()
        checksum = hashlib.sha256(checksum_bytes).hexdigest()[:16]

        step = MigrationStep(
            revision=revision,
            slug=slug,
            operations=operations,
            checksum=checksum,
            is_initial=False,
        )
        return MigrationPlan(steps=[step], is_initial=False)
