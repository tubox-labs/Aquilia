# Strict `auto_migrate=False` Schema Enforcement

In Aquilia v1.3.9, the framework strictly enforces the developer's `auto_migrate=False` setting across all startup phases.

## Overview & Problem Statement

Prior to v1.3.9, configuring `DatabaseIntegration(url="sqlite:///db.sqlite3", auto_migrate=False)` did not prevent schema creation. Because `DatabaseIntegration` sets `auto_create=True` by default, `AquiliaServer` evaluated `auto_create` independently of `auto_migrate`, leading to:
- Implicit execution of `ModelRegistry.create_tables()` during server startup.
- Creation of database tables and indexes on disk without explicit migration commands (`aq db migrate`).
- Inconsistency between production configurations (`auto_migrate=False`) and actual runtime DDL execution.

## Architectural Solution in v1.3.9

Aquilia v1.3.9 introduces explicit configuration tracking (`explicit_auto_migrate_false`) during server startup in `aquilia/server.py`.

### Configuration Resolution Flow

```
1. Read configuration dictionary (Workspace / DatabaseIntegration)
2. Resolve auto_migrate and auto_create values
3. Check AQUILIA_AUTO_MIGRATE environment variable override
4. If auto_migrate is explicitly False (or AQUILIA_AUTO_MIGRATE=0):
   └── explicit_auto_migrate_false = True
5. On Server Startup Phase 4:
   ├── If explicit_auto_migrate_false:
   │   └── PASS (Execute 0 CREATE TABLE, 0 ALTER TABLE, 0 migrations)
   ├── Else If auto_migrate:
   │   └── Run MigrationRunner.migrate() (or create_tables if initial)
   └── Else If auto_create:
       └── Run ModelRegistry.create_tables() (for dev/test setups)
```

## Before vs After Comparison

### Previous Behavior (v1.3.8 and earlier)

```python
# workspace.py
workspace.integrate(
    DatabaseIntegration(
        url="sqlite:///prod.db",
        auto_migrate=False,  # Developer requested NO migrations/schema changes
    )
)

# Startup execution in v1.3.8:
# -> ModelRegistry.create_tables() was executed because auto_create defaulted to True!
# -> Database tables were created on disk implicitly!
```

### New Behavior (v1.3.9)

```python
# workspace.py
workspace.integrate(
    DatabaseIntegration(
        url="sqlite:///prod.db",
        auto_migrate=False,  # Developer requested NO migrations/schema changes
    )
)

# Startup execution in v1.3.9:
# -> explicit_auto_migrate_false is set to True.
# -> NO CREATE TABLE statements execute.
# -> NO schema changes occur.
# -> Startup completes safely with a yellow diagnostic warning if DB is uninitialized.
```

## Environment Variable Overrides

The `auto_migrate` behavior can be explicitly controlled via environment variables without editing Python code:

| Environment Variable | Value | Effect |
|---|---|---|
| `AQUILIA_AUTO_MIGRATE` | `1`, `true`, `yes` | Forces `auto_migrate=True`. Automatically executes pending migrations or creates initial tables on startup. |
| `AQUILIA_AUTO_MIGRATE` | `0`, `false`, `no` | Forces `auto_migrate=False`. Strictly suppresses all startup DDL execution and table creation. |

## Edge Cases & Compatibility

1. **In-Memory & Test Databases**: Testing harnesses that do not specify `auto_migrate=False` and use `auto_create=True` (e.g. `sqlite:///:memory:`) continue to invoke `ModelRegistry.create_tables()` automatically.
2. **Explicit CLI Execution**: CLI commands (`aq db migrate`, `aq db makemigrations`) operate independently of the runtime startup guard, allowing developers to manage migrations manually at deployment time.
