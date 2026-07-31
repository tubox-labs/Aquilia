"""Aquilia migrations.

A typed, immutable, backend-independent migration system built directly on
Aquilia's model layer. Generated migration files are ordinary Python naming
real ``Field``, index, and operation objects -- not serialized dictionaries --
so they read, review, and edit like the models they came from.

Layering::

    schema.py      immutable schema state, built from live Field objects
    operations/    typed operations with state/database separation
    backends/      the only layer that knows about SQL dialects
    autodetect.py  state-to-state diffing
    graph.py       migration dependency DAG
    optimizer.py   operation reduction
    codegen.py     Python source rendering
    serializer.py  migration file writing and loading
    executor.py    transactional application against a database
    probe.py       pre-connection readiness checks
    engine.py      the public entry point
    compat.py      legacy migration-file compatibility

See :mod:`aquilia.models.migration.schema` for the design rationale.

Example::

    from aquilia.models.migration import MigrationEngine

    engine = MigrationEngine("migrations")
    engine.make_migrations([User, Post])
    await engine.migrate(db)
"""

from __future__ import annotations

from .autodetect import Autodetector, RenameHint, detect_changes
from .backends import SchemaBackend, Statement, get_backend
from .engine import SNAPSHOT_FILENAME, MigrationEngine, MigrationStatus
from .executor import (
    MIGRATION_TABLE,
    AppliedMigration,
    ExecutionResult,
    MigrationExecutor,
    compile_operations,
)
from .graph import MigrationGraph, MigrationNode
from .operations import (
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
    Operation,
    OperationCategory,
    RemoveConstraint,
    RemoveField,
    RemoveIndex,
    RenameField,
    RenameModel,
    RunPython,
    RunSQL,
    register_operation,
    registered_operations,
    resolve_operation,
)
from .optimizer import optimize
from .probe import database_exists, migrations_applied
from .schema import (
    NOT_PROVIDED,
    STATE_VERSION,
    CheckConstraintState,
    ColumnState,
    ConstraintState,
    ExclusionConstraintState,
    ForeignKeyConstraintState,
    IndexState,
    ManyToManyState,
    NotProvided,
    PrimaryKeyConstraintState,
    ProjectState,
    Reference,
    TableState,
    UniqueConstraintState,
    auto_index_name,
    normalize_referential_action,
)
from .serializer import (
    MIGRATION_TEMPLATE_VERSION,
    load_migration_module,
    render_migration_module,
    revision_from_path,
    serialize_operations,
    slug_from_path,
)

__all__ = [
    # Schema state
    "STATE_VERSION",
    "NOT_PROVIDED",
    "NotProvided",
    "Reference",
    "ColumnState",
    "IndexState",
    "ConstraintState",
    "CheckConstraintState",
    "UniqueConstraintState",
    "ExclusionConstraintState",
    "PrimaryKeyConstraintState",
    "ForeignKeyConstraintState",
    "ManyToManyState",
    "TableState",
    "ProjectState",
    "auto_index_name",
    "normalize_referential_action",
    # Operations
    "Operation",
    "OperationCategory",
    "register_operation",
    "registered_operations",
    "resolve_operation",
    "CreateModel",
    "DeleteModel",
    "RenameModel",
    "AlterModelOptions",
    "AddField",
    "RemoveField",
    "AlterField",
    "RenameField",
    "AddIndex",
    "RemoveIndex",
    "AlterIndex",
    "AddConstraint",
    "RemoveConstraint",
    "AlterConstraint",
    "CreateManyToManyTable",
    "DeleteManyToManyTable",
    "RunSQL",
    "RunPython",
    # Detection and planning
    "Autodetector",
    "RenameHint",
    "detect_changes",
    "optimize",
    "MigrationGraph",
    "MigrationNode",
    # Backends
    "SchemaBackend",
    "Statement",
    "get_backend",
    # Execution
    "MigrationExecutor",
    "ExecutionResult",
    "AppliedMigration",
    "MIGRATION_TABLE",
    "compile_operations",
    # Files
    "MIGRATION_TEMPLATE_VERSION",
    "render_migration_module",
    "load_migration_module",
    "serialize_operations",
    "revision_from_path",
    "slug_from_path",
    # Readiness probes
    "database_exists",
    "migrations_applied",
    # Engine
    "MigrationEngine",
    "MigrationStatus",
    "SNAPSHOT_FILENAME",
]
