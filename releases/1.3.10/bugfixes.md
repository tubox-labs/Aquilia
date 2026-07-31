# Bug Fixes — Aquilia v1.3.10

---

## Bug 1 — `_patched_create_tables_new` — Optional `db` Parameter

### Previous Behaviour

In the faults integration module (`aquilia/faults/integrations/models.py`), the patched `_patched_create_tables_new` function had a signature that did not accept an optional `db` parameter. When `ModelRegistry.create_tables(db=some_db)` was called with an explicit database argument, the patched version raised a `TypeError` because it only accepted no arguments.

### Root Cause

The patch was written against the original `create_tables()` signature before the optional `db` override was added to `ModelRegistry`. The patch was not updated when the parameter was introduced.

### Fix

The `_patched_create_tables_new` signature now accepts `db=None` as an optional keyword argument, matching the real `ModelRegistry.create_tables` signature:

```python
# Before
async def _patched_create_tables_new():
    ...

# After
async def _patched_create_tables_new(db=None):
    ...
```

### User Impact

Users calling `ModelRegistry.create_tables(db=my_db)` explicitly — common in test setups — would have seen an unexpected `TypeError`. This is now fixed.

---

## Bug 2 — `startup_guard.py` — Probe Function Renames

### Previous Behaviour

`startup_guard.py` imported probe functions from `migration_runner`:

```python
from .migration_runner import check_db_exists, check_migrations_applied
```

After `migration_runner.py` was deleted in this release, the import raised an `ImportError` at runtime, crashing any server boot that reached the startup guard.

### Fix

Updated to import the renamed functions from `migration.probe`:

```python
# Before
from .migration_runner import check_db_exists, check_migrations_applied

if not check_db_exists(db_url): ...
if not check_migrations_applied(db_url, migrations_dir): ...

# After
from .migration.probe import database_exists, migrations_applied

if not database_exists(db_url): ...
if not migrations_applied(db_url, migrations_dir): ...
```

### User Impact

Any application that used `startup_guard.py`'s readiness checking (i.e. any application with `auto_migrate=False` and a SQLite database) would have seen an `ImportError` on server startup. This is now fixed.

---

## Bug 3 — `ModelRegistry.create_tables()` — Unified DDL Path

### Previous Behaviour

`ModelRegistry.create_tables()` called `MigrationRunner` from `migration_runner.py`:

```python
from .migration_runner import MigrationRunner

runner = MigrationRunner(target_db, dialect=getattr(target_db, "dialect", "sqlite"))
exec_stmts = await runner.create_initial_schema(ordered)
return [s.sql for s in exec_stmts if s.sql and not s.is_comment]
```

After `migration_runner.py` was deleted, this import raised `ImportError`.

### Fix

`ModelRegistry.create_tables()` now uses `ProjectState` and `MigrationExecutor` from the new sub-package:

```python
from .migration import ProjectState
from .migration.executor import MigrationExecutor
from .migration.operations import CreateManyToManyTable, CreateModel

target_state = ProjectState.from_models(ordered)
operations = []
for model_name in target_state.creation_order():
    table = target_state.tables[model_name]
    operations.append(CreateModel(model=model_name, table=table))
    for relation in table.m2m:
        operations.append(CreateManyToManyTable(model=model_name, relation=relation))

executor = MigrationExecutor(target_db)
result = await executor.apply_operations(operations, ProjectState(), description="initial schema")
await cls._record_initial_schema(target_db, target_state)
return [statement.sql for statement in result.executed if statement.sql]
```

### Additional Improvement

`create_tables()` now records `0000_initial_schema` in the `aquilia_migrations` table (via the new `_record_initial_schema` class method), so a subsequent `aq db migrate` correctly sees the initial schema as already applied. Previously, running `create_tables()` and then `migrate()` would attempt to re-apply the initial migration and fail with "table already exists".

### User Impact

Applications using `auto_create=True` (the default) or calling `ModelRegistry.create_tables()` directly would have seen an `ImportError` at startup. This is now fixed, and the initial schema is now properly tracked.

---

## Bug 4 — `compile_schema_expression` Import in `base.py` and `fields_module.py`

### Previous Behaviour

`base.py` and `fields_module.py` imported `_compile_schema_expression` from `schema_snapshot`:

```python
from .schema_snapshot import _compile_schema_expression
```

After `schema_snapshot.py` was deleted, these imports raised `ImportError`, breaking unique constraint DDL generation and index DDL generation.

### Fix

Updated to import from `expression.py`:

```python
from .expression import compile_schema_expression as _compile_schema_expression
```

The function is now public (`compile_schema_expression`) rather than private (`_compile_schema_expression`).

### User Impact

Any model with expression-based unique constraints or functional indexes would have raised `ImportError` when generating `CREATE TABLE` SQL. This is now fixed.

---

## Bug 5 — `server.py` — Auto-Migration Path

### Previous Behaviour

`AquiliaServer` used `MigrationRunner` from `migration_runner.py` for auto-migration:

```python
from aquilia.models.migration_runner import MigrationRunner

runner = MigrationRunner(db, migrations_dir)
await runner.migrate()
```

### Fix

Updated to use `MigrationEngine`:

```python
from aquilia.models.migration import MigrationEngine

await MigrationEngine(migrations_dir).migrate(db)
```

This is a one-line functional change — the behaviour is identical, but the implementation now routes through the new unified engine.

---

## Bug 6 — `aq db reset` — Tracking Table Survives Table Drop

### Previous Behaviour

On dialects where the `DROP TABLE` loop did not drop the `aquilia_migrations` tracking table (MySQL with foreign key checks, certain PostgreSQL configurations), `reset` would leave the tracking table intact with all its rows. The subsequent `migrate()` call would then see every migration as already applied (because the rows still existed) and do nothing — leaving the database completely empty but reporting itself as fully migrated.

### Fix

After dropping tables, `reset` now explicitly checks whether `aquilia_migrations` still exists and clears it if so:

```python
engine = MigrationEngine(migrations_dir)
remaining = await db.get_tables()
if "aquilia_migrations" in remaining:
    await db.execute('DELETE FROM "aquilia_migrations"')
results = await engine.migrate(db)
```

### User Impact

`aq db reset` on MySQL or certain PostgreSQL configurations would silently produce an empty database that claimed to be fully migrated. After the reset, the next `aq db status` would show everything as applied. Queries against the (empty) database would fail with "table does not exist". This is now fixed.
