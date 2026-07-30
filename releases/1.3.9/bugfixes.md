# Bug Fixes & Deep Audit Report (v1.3.9)

Aquilia v1.3.9 resolves three critical production issues in the database lifecycle subsystem.

---

## Bug 1 — `auto_migrate=False` Still Executed Table Creation

### Previous Behavior
When a developer configured `DatabaseIntegration(url="sqlite:///db.sqlite3", auto_migrate=False)`, `ModelRegistry.create_tables()` was still invoked on startup, creating tables and modifying the database schema.

### Root Cause
In `aquilia/server.py`, Phase 4 evaluated `if auto_create:` without checking whether `auto_migrate` was explicitly configured as `False`. Because `DatabaseIntegration` sets `auto_create=True` by default, `auto_create` bypassed `auto_migrate=False`.

### Resolution
Updated configuration resolution in `aquilia/server.py` to set `explicit_auto_migrate_false = True` when `auto_migrate=False` is set in configuration or `AQUILIA_AUTO_MIGRATE=0` is set in environment variables. When `explicit_auto_migrate_false` is `True`, all startup DDL execution and table creation is completely suppressed.

---

## Bug 2 — Database Not Ready Should Be Warning, Not Fatal Error

### Previous Behavior
When starting an application with `auto_migrate=False` on an uninitialized database (missing file or pending migrations), server startup raised a fatal `SchemaFault` (`DatabaseNotReadyError`), causing ASGI server startup to crash and terminate process execution.

### Root Cause
In `aquilia/models/startup_guard.py` and `aquilia/server.py`, the readiness check threw a process-terminating exception (`SchemaFault`) when `check_db_ready` returned `False`.

### Resolution
Introduced the `DatabaseState` enum (`READY`, `MISSING_DATABASE`, `PENDING_MIGRATIONS`, `CORRUPTED_HISTORY`, `SCHEMA_MISMATCH`, `UNAVAILABLE`) in `aquilia/models/startup_guard.py`. Updated `check_db_ready()` and `aquilia/server.py` to output a yellow diagnostic terminal warning banner explaining how to run `aq db makemigrations` and `aq db migrate`, and allow server boot to proceed non-fatally.

---

## Bug 3 — Failed Migration / Schema Creation Leaves Partial Schema

### Previous Behavior
If an error occurred during `ModelRegistry.create_tables()` or migration application (e.g., duplicate column, invalid constraint, syntax error in index), tables created prior to the failing statement remained committed on disk in a partially applied state.

### Root Cause
Statements in `ModelRegistry.create_tables()` and legacy `upgrade()` calls in `MigrationRunner` were executed sequentially outside a single atomic database transaction wrapper.

### Resolution
Wrapped `ModelRegistry.create_tables()` in `aquilia/models/registry.py` and legacy `upgrade()` calls in `aquilia/models/migration_runner.py` inside `async with db.transaction():`. Any statement failure now triggers an automatic transaction rollback, leaving zero partial tables or columns on disk.
