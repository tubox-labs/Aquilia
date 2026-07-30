# Atomic Transactional DDL & Migration Rollback

In Aquilia v1.3.9, table creation (`ModelRegistry.create_tables()`) and migration application (`MigrationRunner._apply_migration()`) are executed within explicit database transaction blocks.

## Overview & Risk Assessment

In database systems that support transactional DDL (such as SQLite and PostgreSQL), executing multiple DDL statements (such as `CREATE TABLE`, `CREATE INDEX`, `ALTER TABLE`) outside a transaction wrapper creates a critical vulnerability:
- If statement 1 (`CREATE TABLE users ...`) succeeds, but statement 2 (`CREATE UNIQUE INDEX ...`) fails due to a constraint or expression error, statement 1 remains committed on disk.
- The database is left in a **partially migrated state** (partial schema pollution).
- Subsequent execution attempts fail with `table "users" already exists`, requiring manual database intervention (`DROP TABLE`) to recover.

## Implementation Details

Aquilia v1.3.9 enforces transaction boundaries across all DDL execution paths.

### 1. Atomic Multi-Table Creation in `ModelRegistry.create_tables()`

In `aquilia/models/registry.py`, the entire topological model table, index, and junction table creation loop is wrapped in `async with target_db.transaction():`:

```python
# aquilia/models/registry.py
@classmethod
async def create_tables(cls, db: AquiliaDatabase | None = None) -> list[str]:
    ...
    dialect = getattr(target_db, "dialect", "sqlite")
    statements: list[str] = []

    async with target_db.transaction():
        for model_cls in ordered:
            if model_cls._meta.abstract or not model_cls._meta.managed:
                continue

            # Create main table
            sql = model_cls.generate_create_table_sql(dialect=dialect)
            await target_db.execute(sql)
            statements.append(sql)

            # Create indexes
            for idx_sql in model_cls.generate_index_sql(dialect=dialect):
                await target_db.execute(idx_sql)
                statements.append(idx_sql)

            # Create M2M junction tables
            for m2m_sql in model_cls.generate_m2m_sql(dialect=dialect):
                await target_db.execute(m2m_sql)
                statements.append(m2m_sql)

    return statements
```

If any exception occurs during the execution of any statement in `create_tables()`, the transaction context triggers `target_db.rollback()`, discarding all created tables and returning the database to its pre-operation state.

### 2. Transactional Legacy Migration Execution in `MigrationRunner`

In `aquilia/models/migration_runner.py`, legacy raw-SQL migration `upgrade(db)` calls are now explicitly wrapped in a transaction block:

```python
# aquilia/models/migration_runner.py
elif hasattr(module, "upgrade"):
    upgrade_fn = module.upgrade
    try:
        async with self.db.transaction():
            if inspect.iscoroutinefunction(upgrade_fn):
                await upgrade_fn(self.db)
            else:
                upgrade_fn(self.db)
    except MigrationFault:
        raise
    except Exception as exc:
        raise MigrationFault(
            migration=rev,
            reason=f"Upgrade failed: {exc}",
        ) from exc
```

### 3. Tracking Table Integrity Guarantee

A migration is recorded in the `aquilia_migrations` tracking table (`INSERT INTO aquilia_migrations ...`) **only after** all DDL statements and Python operations in that migration file have completed and committed successfully. If a migration fails:
1. All changes executed by that migration file roll back cleanly.
2. No row is added to `aquilia_migrations`.
3. The migration system remains clean, allowing the developer to fix the migration script and re-run `aq db migrate` without manual cleanup.
