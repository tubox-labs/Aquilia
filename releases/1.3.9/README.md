# Aquilia v1.3.9 Release Notes — "Database Sentinel"

Aquilia v1.3.9 introduces **Strict `auto_migrate=False` Enforcement**, **Non-Fatal Database Startup Readiness Model (`DatabaseState`)**, and **Atomic Transactional DDL & Migration Rollback Guarantees** across the Aquilia Database, ORM, and Server Startup lifecycle subsystems.

Before this release, setting `auto_migrate=False` in `DatabaseIntegration` still caused `ModelRegistry.create_tables()` to execute `CREATE TABLE` DDL on startup because `auto_create` defaulted to `True`. Furthermore, when a database file did not exist or had unapplied migrations under `auto_migrate=False`, the server startup process crashed with a fatal `SchemaFault` rather than allowing safe application boot. Finally, multi-table schema creation and legacy migration steps executed statements without an atomic transaction wrapper, allowing partial schema changes to survive mid-execution failures.

This release performs a complete architectural overhaul of database lifecycle initialization, introducing clean state classification (`DatabaseState`), explicit precedence rules for `auto_migrate`, yellow diagnostic warning banners for uninitialized databases, and transactional DDL execution across `ModelRegistry.create_tables()` and `MigrationRunner`.

---

## Table of Contents

1. [Strict `auto_migrate=False` Enforcement](auto_migrate_enforcement.md)
   - Configuration precedence (`explicit_auto_migrate_false`)
   - Complete suppression of startup table creation and migration generation
   - Environment variable controls (`AQUILIA_AUTO_MIGRATE=0`)
2. [Non-Fatal Database Startup Readiness (`DatabaseState`)](non_fatal_startup_guard.md)
   - State classification (`READY`, `MISSING_DATABASE`, `PENDING_MIGRATIONS`, `CORRUPTED_HISTORY`)
   - Diagnostic yellow terminal warning banner
   - Non-fatal boot continuation without process termination
3. [Atomic Transactional DDL Execution](atomic_ddl_transactions.md)
   - Atomic multi-table schema creation (`ModelRegistry.create_tables()`)
   - Transactional legacy migration execution (`MigrationRunner._apply_migration()`)
   - Partial schema prevention and rollback guarantees
4. [Bug Fixes & Audit](bugfixes.md)
   - Detailed root cause analysis for Bug 1, Bug 2, and Bug 3
5. [Migration Guide & Upgrade Checklist](migration.md)
   - Upgrade instructions, breaking change analysis, and compatibility notes

---

## Highlights

### 1. Strict `auto_migrate=False` Schema Lock

When `auto_migrate=False` is set in `DatabaseIntegration` or workspace settings, Aquilia strictly guarantees that **no tables will be created**, **no schema will be modified**, and **no DDL statements will execute** on startup—even if `auto_create=True` is set on the integration.

```python
# workspace.py / app setup
workspace.integrate(
    DatabaseIntegration(
        url="sqlite:///db.sqlite3",
        auto_migrate=False,  # Strictly locks schema; NO CREATE TABLE will run
    )
)
```

### 2. Non-Fatal Diagnostic Warning Banners

If the database is missing or uninitialized when `auto_migrate=False`, the server logs a formatted yellow terminal diagnostic banner detailing the exact `aq db` commands to run, but allows server boot to continue gracefully without raising a fatal `SchemaFault`.

```text
╔════════════════════════════════════════════════════════════╗
║                     DATABASE NOT READY                     ║
╠════════════════════════════════════════════════════════════╣
║ Database file does not exist                               ║
║                                                            ║
║ Database: sqlite:///db.sqlite3                             ║
║                                                            ║
║ Run the following commands to initialize database:         ║
║                                                            ║
║   $ aq db makemigrations                                   ║
║   $ aq db migrate                                          ║
║                                                            ║
║ Or set AQUILIA_AUTO_MIGRATE=1 to auto-create on startup.   ║
╚════════════════════════════════════════════════════════════╝
```

### 3. Atomic DDL Execution & Clean Rollback

`ModelRegistry.create_tables()` and `MigrationRunner._apply_migration()` now execute DDL statements inside an explicit `async with db.transaction():` context. If any statement or constraint fails mid-way, all previously created structures in that operation roll back atomically, leaving 0 partial tables or columns in the database.

```python
# Internal atomic execution guarantee in ModelRegistry.create_tables()
async with target_db.transaction():
    for model_cls in ordered:
        await target_db.execute(model_cls.generate_create_table_sql())
        for idx_sql in model_cls.generate_index_sql():
            await target_db.execute(idx_sql)
```

---

## Summary of Subsystem Changes

| Component | File Anchor | Summary of Changes |
|---|---|---|
| Startup Guard | [startup_guard.py](file:///Users/kuroyami/TuboxLabProject/Aquilia/aquilia/models/startup_guard.py) | Added `DatabaseState` enum (`READY`, `MISSING_DATABASE`, `PENDING_MIGRATIONS`, `CORRUPTED_HISTORY`). Updated `check_db_ready()` to return non-fatal state warnings. |
| Server Startup | [server.py](file:///Users/kuroyami/TuboxLabProject/Aquilia/aquilia/server.py) | Resolved precedence between `auto_migrate` and `auto_create`. Suppressed `SchemaFault` crashes on uninitialized databases. |
| Model Registry | [registry.py](file:///Users/kuroyami/TuboxLabProject/Aquilia/aquilia/models/registry.py) | Wrapped `create_tables()` DDL loops in `async with target_db.transaction():` for atomic table and index creation. |
| Migration Runner | [migration_runner.py](file:///Users/kuroyami/TuboxLabProject/Aquilia/aquilia/models/migration_runner.py) | Wrapped legacy `upgrade()` function calls in `async with self.db.transaction():` for atomic migration execution. |
