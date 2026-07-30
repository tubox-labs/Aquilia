# Migration & Upgrade Guide for Aquilia v1.3.9

This guide provides comprehensive instructions for upgrading your Aquilia application to v1.3.9.

---

## Upgrade Summary

Aquilia v1.3.9 is a fully backward-compatible release at the developer API level. Existing `Model` subclasses, contracts, controllers, services, signals, CLI commands, and database configuration settings continue to function without modification.

Under the hood, v1.3.9 completes a major architecture overhaul:
- **Single Execution Authority**: All schema DDL transformations are executed exclusively by `MigrationRunner` and `DDLExecutor`.
- **`ModelRegistry` Execution Removal**: `ModelRegistry` now acts purely as a model metadata and topology registry. Its DDL methods delegate execution to `MigrationRunner`.
- **Authoritative Revision Zero History**: Initial schema creation records `0000_initial_schema` in `aquilia_migrations`, avoiding databases with missing history rows.

---

## Behavioral & Architectural Changes for Developers

### 1. `auto_migrate=False` Strict Lock
If your project configures `auto_migrate=False`:
* **Previous behavior**: Tables were created automatically on startup due to `auto_create=True` defaults.
* **v1.3.9 behavior**: Absolutely no tables are created automatically on startup. To initialize database schema, run:
  ```bash
  aq db makemigrations
  aq db migrate
  ```
  Or set `AQUILIA_AUTO_MIGRATE=1` in your deployment environment if you want auto-creation on boot.

### 2. Server Startup Diagnostics
If your database is missing or has pending migrations when booting with `auto_migrate=False`, server boot no longer crashes with `SchemaFault`. Instead, a yellow diagnostic warning banner is displayed in `stderr` instructing you on the required `aq db` commands.

### 3. Transactional DDL Safety & Initial Schema History
Failed migrations or initial schema setup calls now automatically roll back cleanly, eliminating partial table artifacts. Initial schema creation is recorded in `aquilia_migrations` tracking table (`0000_initial_schema`).

---

## Code API Migration Examples

### Previous API (v1.3.8)
```python
# ModelRegistry executed DDL string loops directly:
statements = await ModelRegistry.create_tables(db)
```

### New API (v1.3.9)
```python
# ModelRegistry delegates directly to MigrationRunner and InitialSchemaPlanner
statements = await ModelRegistry.create_tables(db)

# Or invoke MigrationRunner directly:
runner = MigrationRunner(db)
exec_stmts = await runner.create_initial_schema()
```

---

## Upgrade Checklist

- [x] Update `aquilia` dependency to `v1.3.9`.
- [x] Run `aq db status` to verify migration tracking history status.
- [x] If deploying in production with `auto_migrate=False`, ensure database schema is applied via `aq db migrate` in deployment CI/CD pipelines.
- [x] Verify test suites pass cleanly with `./.venv/bin/pytest tests/`.
