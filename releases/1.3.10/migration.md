# Breaking Changes & Migration Guide — Aquilia v1.3.10

This guide documents every breaking change introduced in v1.3.10 and provides step-by-step instructions for upgrading.

---

## Summary of Breaking Changes

| Category | Breaking Change |
|---|---|
| **Removed modules** | `migration_dsl`, `migration_gen`, `migration_planner`, `migration_runner`, `migrations`, `schema_snapshot`, `ddl_executor` |
| **Removed public symbols** | `MigrationRunner`, `MigrationOps`, `DSLMigrationRunner`, `Migration`, `DSLCreateModel`, `DSLAddField`, `DSLRemoveField`, `DSLAlterField`, `DSLRenameField`, `DSLDropModel`, `DSLRenameModel`, `DSLCreateIndex`, `DSLDropIndex`, `DSLRunSQL`, `DSLRunPython`, `DSLAddConstraint`, `DSLRemoveConstraint`, `MigrationInfo`, `generate_migration_from_models`, `op`, `generate_dsl_migration`, `InitialSchemaPlanner`, `MigrationPlan`, `MigrationPlanner`, `MigrationStep`, `DDLExecutor`, `ExecutableStatement`, `StatementType`, `C`, `ColumnDef`, `columns`, `create_snapshot`, `save_snapshot`, `load_snapshot`, `compute_diff`, `diff_to_operations`, `SchemaDiff`, `ModelDiff` |
| **CLI flags removed** | `aq db makemigrations --use-dsl`, `--no-use-dsl`, `--migration-format` |
| **Snapshot format** | Old `"models"` key is no longer written; new format uses `"tables"`. Old snapshots are detected and discarded gracefully. |
| **Probe function renames** | `check_db_exists` → `database_exists`; `check_migrations_applied` → `migrations_applied`; `check_db_ready` removed |

---

## Removed Modules

The following modules have been deleted. Any direct import of them will raise `ImportError`:

| Old Module | Replacement |
|---|---|
| `aquilia.models.ddl_executor` | `aquilia.models.migration.executor` + `aquilia.models.migration.backends` |
| `aquilia.models.migration_dsl` | `aquilia.models.migration.operations` |
| `aquilia.models.migration_gen` | `aquilia.models.migration.codegen` + `aquilia.models.migration.serializer` |
| `aquilia.models.migration_planner` | `aquilia.models.migration.graph` + `aquilia.models.migration.engine` |
| `aquilia.models.migration_runner` | `aquilia.models.migration.executor` + `aquilia.models.migration.engine` |
| `aquilia.models.migrations` | `aquilia.models.migration.engine` |
| `aquilia.models.schema_snapshot` | `aquilia.models.migration.schema` + `aquilia.models.migration.autodetect` |

---

## Import Path Changes

### Top-Level `aquilia.models` Exports

**Removed exports:**

```python
# These no longer exist in aquilia.models:
from aquilia.models import (
    MigrationRunner,       # removed
    MigrationOps,          # removed
    MigrationInfo,         # removed
    generate_migration_from_models,  # removed
    op,                    # removed
    Migration,             # removed
    DSLMigrationRunner,    # removed
    DSLCreateModel,        # removed
    DSLAddField,           # removed
    DSLRemoveField,        # removed
    DSLAlterField,         # removed
    DSLRenameField,        # removed
    DSLDropModel,          # removed
    DSLRenameModel,        # removed
    DSLCreateIndex,        # removed
    DSLDropIndex,          # removed
    DSLRunSQL,             # removed
    DSLRunPython,          # removed
    DSLAddConstraint,      # removed
    DSLRemoveConstraint,   # removed
    ColumnDef,             # removed
    columns,               # removed
    C,                     # removed
    create_snapshot,       # removed
    save_snapshot,         # removed
    load_snapshot,         # removed
    compute_diff,          # removed
    diff_to_operations,    # removed
    SchemaDiff,            # removed
    ModelDiff,             # removed
    DDLExecutor,           # removed
    ExecutableStatement,   # removed
    ExecutionResult,       # removed (old one)
    StatementType,         # removed
    InitialSchemaPlanner,  # removed
    MigrationPlan,         # removed
    MigrationPlanner,      # removed
    MigrationStep,         # removed
    check_db_exists,       # removed
    check_migrations_applied,  # removed
    check_db_ready,        # removed
    generate_dsl_migration, # removed
)
```

**New exports (via `aquilia.models`):**

```python
from aquilia.models import (
    MigrationEngine,   # replaces MigrationRunner, DSLMigrationRunner
    MigrationGraph,    # new
    MigrationNode,     # new
    MigrationStatus,   # new
    Operation,         # new unified base (replaces DSL* operations)
    ProjectState,      # replaces SchemaDiff/ModelDiff snapshot machinery
)
```

### Top-Level `aquilia` Exports

```python
# Old
from aquilia import MigrationRunner, MigrationOps

# New
from aquilia import MigrationEngine
```

---

## Code Migration Examples

### Generating Migrations

**Before (v1.3.9 — DSL path):**

```python
from aquilia.models.migration_gen import generate_dsl_migration

result = generate_dsl_migration(
    model_classes=[User, Post],
    migrations_dir="migrations",
)
```

**Before (v1.3.9 — legacy path):**

```python
from aquilia.models.migrations import generate_migration_from_models

result = generate_migration_from_models(
    model_classes=[User, Post],
    migrations_dir="migrations",
)
```

**After (v1.3.10):**

```python
from aquilia.models.migration import MigrationEngine

engine = MigrationEngine("migrations")
path = engine.make_migrations([User, Post])
# path is None when no changes are detected
```

---

### Applying Migrations

**Before (v1.3.9 — MigrationRunner):**

```python
from aquilia.models.migration_runner import MigrationRunner

runner = MigrationRunner(db, "migrations", dialect=db.dialect)
applied_revisions = await runner.migrate()
```

**After (v1.3.10):**

```python
from aquilia.models.migration import MigrationEngine

engine = MigrationEngine("migrations")
results = await engine.migrate(db)
# results is list[ExecutionResult], one per migration
```

---

### Snapshot Operations

**Before (v1.3.9):**

```python
from aquilia.models.schema_snapshot import (
    create_snapshot, save_snapshot, load_snapshot,
    compute_diff, diff_to_operations, SchemaDiff, ModelDiff
)

snapshot = create_snapshot([User, Post])
save_snapshot(snapshot, "migrations/schema_snapshot.json")

old_snap = load_snapshot("migrations/schema_snapshot.json")
diff = compute_diff(old_snap, snapshot)
ops = diff_to_operations(diff)
```

**After (v1.3.10):**

```python
from aquilia.models.migration import MigrationEngine, ProjectState

engine = MigrationEngine("migrations")

# Snapshot is managed automatically by make_migrations.
# For manual access:
state = ProjectState.from_models([User, Post])
engine.save_snapshot(state)

before = engine.load_snapshot()
after = ProjectState.from_models([User, Post])

from aquilia.models.migration import detect_changes
ops = detect_changes(before, after)
```

---

### DDL Executor Usage

**Before (v1.3.9):**

```python
from aquilia.models import DDLExecutor, CreateModel, C

ops = [CreateModel("User", "users", [C.auto("id"), C.varchar("email", 255)])]
statements = DDLExecutor.compile_operations(ops, dialect="postgresql")
result = await DDLExecutor.execute_statements(db, statements, in_transaction=True)
```

**After (v1.3.10):**

```python
from aquilia.models.migration import MigrationEngine

engine = MigrationEngine("migrations")
# Let the engine manage creation; or use MigrationExecutor directly:

from aquilia.models.migration.executor import MigrationExecutor
from aquilia.models.migration.operations import CreateModel
from aquilia.models.migration.schema import ProjectState, TableState, ColumnState
from aquilia.models import fields

executor = MigrationExecutor(db)
result = await executor.apply_operations(
    [CreateModel(model="User", table=TableState.of("User", "users", columns=[
        ColumnState.of("id", fields.AutoField(primary_key=True)),
        ColumnState.of("email", fields.EmailField(unique=True)),
    ]))],
    ProjectState(),
    description="create user table",
)
```

---

### Probe Functions

**Before (v1.3.9 — `migration_runner`):**

```python
from aquilia.models.migration_runner import check_db_exists, check_migrations_applied

if not check_db_exists(db_url):
    ...
if not check_migrations_applied(db_url, migrations_dir):
    ...
```

**After (v1.3.10 — `migration.probe`):**

```python
from aquilia.models.migration.probe import database_exists, migrations_applied
# Also available via:
from aquilia.models.migration import database_exists, migrations_applied

if not database_exists(db_url):
    ...
if not migrations_applied(db_url, migrations_dir):
    ...
```

---

### Direct DSL Operations

**Before (v1.3.9 — DSL prefix):**

```python
from aquilia.models import (
    DSLCreateModel, DSLAddField, DSLRemoveField,
    DSLAlterField, DSLRenameField, DSLRunSQL,
)
```

**After (v1.3.10 — unified operations):**

```python
from aquilia.models.migration import (
    CreateModel, AddField, RemoveField,
    AlterField, RenameField, RunSQL,
)
# or via aquilia.models:
from aquilia.models import Operation
```

---

## Snapshot Format Upgrade

The v1.3.10 snapshot format uses `"tables"` as the top-level key instead of `"models"`. Old snapshots with `"models"` are detected at load time:

```python
# In MigrationEngine.load_snapshot():
if "tables" not in raw and "models" in raw:
    logger.info(
        "Schema snapshot at %s is in a superseded format and cannot describe "
        "many-to-many relations, generated columns, or index methods. It will be "
        "replaced on the next makemigrations.",
        path,
    )
    return ProjectState()
```

**What happens:** The old snapshot is silently discarded, and the engine treats the state as empty. The next `makemigrations` will diff against an empty state, producing a full `CreateModel` for every model — essentially a new initial migration.

**Action required:** If you have an existing `schema_snapshot.json` in the old `"models"` format:

1. Delete `migrations/schema_snapshot.json`
2. Run `aq db makemigrations` — it will regenerate the snapshot in the new format

> [!NOTE]
> Your existing migration *files* are not affected. The snapshot is purely a caching artefact for the autodetector. The migration graph (your `.py` files) remains the authoritative record.

---

## CLI Flag Removal

```bash
# These flags are no longer accepted:
aq db makemigrations --use-dsl          # → error: no such option
aq db makemigrations --no-use-dsl       # → error: no such option
aq db makemigrations --migration-format python  # → error: no such option

# Use instead:
aq db makemigrations                    # always uses new engine
aq db makemigrations --slug my_change   # optional human-readable name
aq db makemigrations --dry-run          # new: preview without writing
```

---

## Upgrade Checklist

- [ ] Update `aquilia` dependency to `v1.3.10`
- [ ] Replace all imports of removed modules (see table above)
- [ ] Replace `MigrationRunner` with `MigrationEngine` throughout application code
- [ ] Replace `DSL*` operation imports with unified `migration.operations` imports
- [ ] Remove `--use-dsl`, `--no-use-dsl`, `--migration-format` from any scripts or CI that call `aq db makemigrations`
- [ ] Replace `check_db_exists`/`check_migrations_applied` with `database_exists`/`migrations_applied`
- [ ] Replace `from aquilia.models.schema_snapshot import _compile_schema_expression` with `from aquilia.models.expression import compile_schema_expression`
- [ ] Delete old `schema_snapshot.json` and regenerate with `aq db makemigrations` (if format was `"models"`)
- [ ] Run `aq db status` to verify the migration tracking table is intact
- [ ] Run `aq db migrate` if any migrations are pending
- [ ] Run your full test suite: `pytest tests/`

---

## Compatibility Notes

- **Generated migration files from v1.3.8 / v1.3.9** that use the old DSL (`Migration`, `C.varchar(...)`, `ColumnDef`, etc.) will **not** be loadable by the new engine. You must either squash and regenerate, or rewrite them to use the new operation format.
- **Migration tracking table** (`aquilia_migrations`) is unchanged. Existing applied-migration rows are preserved.
- **All other Aquilia subsystems** (controllers, contracts, DI, sessions, auth, cache, storage, tasks, WebSockets, mail, templates, admin, artifacts) are unaffected by this release.
- **Python version** requirement unchanged (3.11+).
- **Database support** unchanged: SQLite, PostgreSQL, MySQL, Oracle.
