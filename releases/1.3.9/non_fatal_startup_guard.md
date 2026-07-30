# Non-Fatal Database Readiness Model (`DatabaseState`)

In Aquilia v1.3.9, database startup readiness checks no longer treat uninitialized databases as fatal process-crashing exceptions.

## Overview & Motivation

Prior to v1.3.9, when an application booted with `auto_migrate=False` and either the SQLite database file did not exist or pending migrations were detected, `startup_guard.py` raised a fatal `SchemaFault` (`DatabaseNotReadyError`). This caused the ASGI application server (such as Uvicorn or Hypercorn) to fail startup immediately with a process exit code.

In modern web applications:
- Applications should be able to boot and serve static assets or non-database routes even if database initialization is pending.
- Diagnostic information should instruct developers on the precise commands needed to migrate the database without aborting application process creation.

## `DatabaseState` Enum Model

Aquilia v1.3.9 introduces the `DatabaseState` enum in `aquilia.models.startup_guard` to explicitly categorize database readiness:

```python
from enum import Enum

class DatabaseState(Enum):
    READY = "READY"                      # Database exists and all migrations are applied
    MISSING_DATABASE = "MISSING_DATABASE"  # Target SQLite file or database does not exist
    PENDING_MIGRATIONS = "PENDING_MIGRATIONS" # Unapplied migration files detected
    CORRUPTED_HISTORY = "CORRUPTED_HISTORY"  # Migration tracking checksum mismatch
    SCHEMA_MISMATCH = "SCHEMA_MISMATCH"   # ORM models differ from snapshot
    UNAVAILABLE = "UNAVAILABLE"          # Database connection refused
```

### Inspection Helper: `get_db_state()`

Developers can programmatically inspect database readiness state using `get_db_state()`:

```python
from aquilia.models.startup_guard import get_db_state, DatabaseState

state = get_db_state("sqlite:///db.sqlite3", migrations_dir="migrations")

if state == DatabaseState.MISSING_DATABASE:
    print("Database file is missing! Run 'aq db migrate'.")
elif state == DatabaseState.PENDING_MIGRATIONS:
    print("Pending migrations detected.")
```

## Non-Fatal Terminal Diagnostic Banner

When `check_db_ready()` detects that the database is not in `DatabaseState.READY` under `auto_migrate=False`, it outputs a formatted, human-readable yellow terminal banner and returns `False`. The server logs a warning and proceeds with process boot.

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

## Request-Time Error Handling

If a request or operation attempts to perform a query against an uninitialized database (e.g. `User.objects.all()`), the backend database driver will raise a standard `QueryFault` or `SchemaFault` at request time. This ensures that application startup is non-blocking while preserving safety for database operations.
