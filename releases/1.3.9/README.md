# Aquilia v1.3.9 Release Notes — "Database Sentinel"

Aquilia v1.3.9 introduces **Strict `auto_migrate=False` Enforcement**, **Non-Fatal Database Startup Readiness Model (`DatabaseState`)**, **Single-Authority Migration Engine Architecture (`MigrationRunner`, `DDLExecutor`, `MigrationPlanner`)**, and **Atomic Transactional DDL & Migration History Guarantees** across the Aquilia Database, ORM, and Server Startup subsystems.

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
   - Atomic multi-table schema creation (`MigrationRunner.execute_plan()`)
   - Transactional migration execution and rollback guarantees
   - Prevention of partial schema artifacts on DDL failure
4. [Single-Authority Migration Engine Architecture](single_authority_migration_engine.md)
   - Complete removal of `ModelRegistry` as an execution authority
   - Delegation of DDL execution and history tracking to `MigrationRunner`
   - Initial schema creation recorded as `0000_initial_schema` in `aquilia_migrations`
5. [DDL Executor & Migration Planner Architecture](ddl_executor_and_planner.md)
   - Strongly-typed `ExecutableStatement` and `StatementType` intermediate representations
   - Direct initial schema planning via `InitialSchemaPlanner`
   - Encapsulated backend adapter error handling (`DatabaseAdapter.should_ignore_ddl_error()`)
6. [Bug Fixes & Audit](bugfixes.md)
   - Detailed root cause analysis and resolution for Bug 1, Bug 2, and Bug 3
7. [Migration Guide & Upgrade Checklist](migration.md)
   - Upgrade instructions, breaking change analysis, and compatibility notes

---

## Highlights

### 1. Single Execution Authority (`MigrationRunner` & `DDLExecutor`)

`ModelRegistry` has been completely stripped of DDL execution responsibilities. All DDL statement execution, statement compilation, transaction handling, rollback, logging, progress reporting, and history tracking are owned by `MigrationRunner` and `DDLExecutor`.

```python
from aquilia.models import MigrationRunner, MigrationPlanner

# MigrationRunner is the single execution authority for all DDL operations
runner = MigrationRunner(db)
await runner.create_initial_schema()  # Records 0000_initial_schema in aquilia_migrations
await runner.migrate()                # Executes pending migration files atomically
```

### 2. Typed Intermediate Representation (`ExecutableStatement`)

Raw SQL strings (`list[str]`) are replaced by strongly-typed `ExecutableStatement` objects carrying explicit statement categories (`CREATE_TABLE`, `ALTER_TABLE`, `CREATE_INDEX`, `PYTHON_CALLABLE`, `COMMENT`, etc.):

```python
from aquilia.models import DDLExecutor, CreateModel, C

ops = [CreateModel("User", "users", [C.auto("id"), C.varchar("email", 255)])]
statements = DDLExecutor.compile_operations(ops, dialect="postgresql")
res = await DDLExecutor.execute_statements(db, statements, in_transaction=True)
```

### 3. Strict `auto_migrate=False` Schema Lock

When `auto_migrate=False` is set in `DatabaseIntegration` or workspace settings, Aquilia strictly guarantees that **no tables will be created**, **no schema will be modified**, and **no DDL statements will execute** on startup.

```python
workspace.integrate(
    DatabaseIntegration(
        url="sqlite:///db.sqlite3",
        auto_migrate=False,  # Strictly locks schema; NO DDL will run at startup
    )
)
```

### 4. Non-Fatal Diagnostic Warning Banners

If the database is missing or uninitialized when `auto_migrate=False`, the server logs a formatted yellow terminal diagnostic banner detailing the exact `aq db` commands to run, but allows server boot to continue gracefully without raising a fatal `SchemaFault`.

---

## Summary of Subsystem Changes

| Component | File Anchor | Summary of Changes |
|---|---|---|
| DDL Executor | [ddl_executor.py](file:///Users/kuroyami/TuboxLabProject/Aquilia/aquilia/models/ddl_executor.py) | Introduced `DDLExecutor`, `ExecutableStatement`, `StatementType`, `ExecutionResult`. Compiles typed operations and executes statements atomically. |
| Migration Planner | [migration_planner.py](file:///Users/kuroyami/TuboxLabProject/Aquilia/aquilia/models/migration_planner.py) | Introduced `MigrationPlanner` & `InitialSchemaPlanner`. Directly plans initial DDL without empty-snapshot diffing. |
| Migration Runner | [migration_runner.py](file:///Users/kuroyami/TuboxLabProject/Aquilia/aquilia/models/migration_runner.py) | Single execution authority for DDL execution, rollback, tracking, and diagnostics. |
| Model Registry | [registry.py](file:///Users/kuroyami/TuboxLabProject/Aquilia/aquilia/models/registry.py) | Stripped of DDL execution loops and SQL parsing. Delegates `create_tables()` and `drop_tables()` to `MigrationRunner`. |
| Database Adapters | [base.py](file:///Users/kuroyami/TuboxLabProject/Aquilia/aquilia/db/backends/base.py) / [mysql.py](file:///Users/kuroyami/TuboxLabProject/Aquilia/aquilia/db/backends/mysql.py) | Added `DatabaseAdapter.should_ignore_ddl_error()` hook to encapsulate MySQL error 1061/1091 and backend quirks. |
| Startup Guard | [startup_guard.py](file:///Users/kuroyami/TuboxLabProject/Aquilia/aquilia/models/startup_guard.py) | Added `DatabaseState` enum (`READY`, `MISSING_DATABASE`, `PENDING_MIGRATIONS`, `CORRUPTED_HISTORY`). Non-fatal state warnings. |
| Server Startup | [server.py](file:///Users/kuroyami/TuboxLabProject/Aquilia/aquilia/server.py) | Resolved precedence between `auto_migrate` and `auto_create`. Suppressed `SchemaFault` crashes on uninitialized databases. |
