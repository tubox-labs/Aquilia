# Aquilia v1.3.10 Release Notes — "Migration Rewrite"

Aquilia v1.3.10 is the most significant migration-subsystem release in the framework's history. Every file that made up the previous multi-layer, multi-authority migration stack (`migration_dsl.py`, `migration_gen.py`, `migration_planner.py`, `migration_runner.py`, `migrations.py`, `schema_snapshot.py`, `ddl_executor.py`) has been **replaced** by a single, coherent `aquilia.models.migration` sub-package — designed ground-up around immutable schema state, typed operations, dialect-aware SQL backends, a dependency-graph planner, and a transactional executor.

---

## Table of Contents

1. [Migration Engine Architecture](migration_engine.md)
   - `aquilia.models.migration` sub-package layout
   - `MigrationEngine` — the unified public entry point
   - `ProjectState` — immutable, field-fidelity schema state
   - `MigrationGraph` / `MigrationNode` — dependency-aware DAG ordering
   - `MigrationExecutor` — transactional application with checksum verification
   - `Autodetector` — deterministic, safe rename detection
   - `Optimizer` — operation folding before file write
   - `SchemaBackend` — dialect isolation layer
   - `Serializer` / `Codegen` — real Python constructor files
2. [Operations Reference](operations.md)
   - Full typed operation catalogue
   - State-forwards / state-backwards protocol
   - Backend compilation contract
3. [CLI Changes](cli.md)
   - `aq db makemigrations` — new flags (`--slug`, `--dry-run`), removed flags
   - `aq db migrate` — `MigrationEngine` integration, diagnostics output
   - `aq db showmigrations` — updated executor/serializer path
   - `aq db diff` — operation-based diff output
   - `aq db reset` — tracking-table aware reset
4. [Field Improvements](fields.md)
   - `EnumField` — dotted-string `enum_class` for migration round-trips
   - `BigAutoField` / `SmallAutoField` — MySQL `BIGINT`/`SMALLINT`
   - `GeneratedField` — `deconstruct()` for snapshotting
   - `compile_schema_expression()` — moved from `schema_snapshot` to `expression`
5. [Breaking Changes & Migration Guide](migration.md)
   - Removed symbols
   - Import path changes
   - Snapshot format upgrade
   - Upgrade checklist
6. [Bug Fixes](bugfixes.md)
   - `_patched_create_tables_new` optional `db` parameter
   - `startup_guard` probe function renames
   - `ModelRegistry.create_tables` unified DDL path
7. [Architecture Deep Dive](architecture.md)
   - Design rationale
   - Determinism guarantees
   - Atomicity model
   - Backward compatibility layers

---

## Highlights

### 1. One Package, One Authority

Six modules (`migration_dsl`, `migration_gen`, `migration_planner`, `migration_runner`, `migrations`, `schema_snapshot`, `ddl_executor`) are replaced by one sub-package:

```
aquilia/models/migration/
├── __init__.py        public API
├── schema.py          ProjectState, TableState, ColumnState, ...
├── operations/        typed, backend-independent operations
├── backends/          SQLite, PostgreSQL, MySQL, Oracle DDL
├── autodetect.py      state-to-state diffing
├── graph.py           MigrationGraph, MigrationNode (dependency DAG)
├── optimizer.py       operation reduction
├── codegen.py         Python source rendering
├── serializer.py      file writing / loading
├── executor.py        transactional application
├── probe.py           pre-connection readiness probes
└── engine.py          MigrationEngine — public entry point
```

### 2. `MigrationEngine` — Single Public Entry Point

```python
from aquilia.models.migration import MigrationEngine

engine = MigrationEngine("migrations")

# Generate a migration from model changes
path = engine.make_migrations([User, Post], slug="add_bio")

# Apply pending migrations
results = await engine.migrate(db)

# Check status
status = await engine.status(db)
print(status.describe())

# Roll back to a specific revision
await engine.migrate(db, target="20260720_120000")

# Dry-run: inspect SQL without applying
statements = await engine.plan(db)
for stmt in statements:
    print(stmt.sql)
```

### 3. Field-Fidelity Schema State

`ProjectState` is built directly from live `Field.deconstruct()` output — not from reduced primitive mappings. Generated-column expressions, M2M relationships, index access methods, operator classes, partial predicates, and all other model semantics survive the snapshot round-trip intact.

### 4. Deterministic, Reproducible Migrations

Every collection in the pipeline is an ordered `tuple`; every mapping is iterated through `sorted()` at construction time. Two runs of `makemigrations` against the same models — in different processes, with different `PYTHONHASHSEED` values — produce byte-identical migration files.

### 5. Real Python Constructor Files

Generated migration files use the same `Field`, index, and constraint classes a developer writes in models — not serialized dictionaries. A reviewer sees exactly the schema they declared:

```python
# migrations/20260801_103000_add_post.py
from aquilia.models.migration import CreateModel, Operation, ProjectState
from aquilia.models.migration.schema import ColumnState, TableState
from aquilia.models import fields

dependencies: tuple[str, ...] = ("20260730_120000",)

operations: list[Operation] = [
    CreateModel(
        model="Post",
        table=TableState.of(
            "Post",
            "posts",
            columns=[
                ColumnState.of("id", fields.AutoField(primary_key=True)),
                ColumnState.of("title", fields.CharField(max_length=200)),
                ColumnState.of("author_id", fields.ForeignKey("User", on_delete="CASCADE")),
            ],
        ),
    ),
]
```

### 6. Operation Optimizer

The autodetector emits a faithful but verbose diff. Before the migration is written, the optimizer folds redundant operations:

```
CreateModel(User) + AddField(User.bio)    → CreateModel(User with bio)
AddField(x) + RemoveField(x)             → nothing
AddField(x) + AlterField(x)              → AddField with final definition
CreateModel(User) + DeleteModel(User)    → nothing
```

### 7. Checksum Tamper Detection

Every applied migration records the SHA-256 digest of its source file. `engine.verify_checksums(db)` reports any migration whose file has been modified since application — enabling post-deployment integrity audits.

---

## Summary of Subsystem Changes

| Component | Status | Summary |
|---|---|---|
| `aquilia.models.migration` | **New** | Unified migration sub-package; public API entry point |
| `aquilia.models.migration.engine` | **New** | `MigrationEngine` — single entry point for generate/apply/rollback |
| `aquilia.models.migration.schema` | **New** | `ProjectState`, `TableState`, `ColumnState`, field-fidelity state |
| `aquilia.models.migration.operations` | **New** | Typed, backend-independent operations with state/database separation |
| `aquilia.models.migration.backends` | **New** | `SchemaBackend` dialect isolation (SQLite, PostgreSQL, MySQL, Oracle) |
| `aquilia.models.migration.autodetect` | **New** | Deterministic state diffing; safe rename inference with confidence scoring |
| `aquilia.models.migration.graph` | **New** | `MigrationGraph`/`MigrationNode` dependency DAG with topological ordering |
| `aquilia.models.migration.optimizer` | **New** | Operation reduction before file write |
| `aquilia.models.migration.codegen` | **New** | Python source rendering (real constructors, not dicts) |
| `aquilia.models.migration.serializer` | **New** | File writing/loading; `MIGRATION_TEMPLATE_VERSION = 3` |
| `aquilia.models.migration.executor` | **New** | Transactional application; checksum recording; MySQL/Oracle warnings |
| `aquilia.models.migration.probe` | **New** | Read-only pre-connection SQLite readiness probes |
| `aquilia.models.ddl_executor` | **Removed** | Replaced by `migration.executor` + `migration.backends` |
| `aquilia.models.migration_dsl` | **Removed** | Replaced by `migration.operations` |
| `aquilia.models.migration_gen` | **Removed** | Replaced by `migration.codegen` + `migration.serializer` |
| `aquilia.models.migration_planner` | **Removed** | Replaced by `migration.graph` + `migration.engine` |
| `aquilia.models.migration_runner` | **Removed** | Replaced by `migration.executor` + `migration.engine` |
| `aquilia.models.migrations` | **Removed** | Replaced by `migration.engine` |
| `aquilia.models.schema_snapshot` | **Removed** | Replaced by `migration.schema` + `migration.autodetect` |
| `aquilia.models.fields.enum_field` | **Improved** | Dotted-string `enum_class` for migration round-trips; `_resolve_enum_class()` |
| `aquilia.models.fields_module` | **Improved** | `BigAutoField`/`SmallAutoField` MySQL types; `GeneratedField.deconstruct()` |
| `aquilia.models.expression` | **Improved** | `compile_schema_expression()` moved here from `schema_snapshot` |
| `aquilia.models.registry` | **Improved** | `create_tables()` uses `ProjectState` + `MigrationExecutor` |
| `aquilia.models.startup_guard` | **Updated** | Uses `migration.probe.database_exists/migrations_applied` |
| `aquilia.server` | **Updated** | Uses `MigrationEngine` for auto-migrate |
| `aquilia.__init__` | **Updated** | Exports `MigrationEngine` instead of `MigrationRunner`/`MigrationOps` |
