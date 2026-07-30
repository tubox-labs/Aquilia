# Migration & Upgrade Guide for Aquilia v1.3.9

This guide provides instructions for upgrading your Aquilia application to v1.3.9.

---

## Upgrade Summary

Aquilia v1.3.9 is a fully backward-compatible release. Existing code, models, contracts, controllers, services, and CLI commands continue to function without modification.

---

## What Changed for Developers?

### 1. `auto_migrate=False` Behavior
If your project configures `auto_migrate=False`:
* **Previous behavior**: Tables were created automatically on startup due to `auto_create=True` defaults.
* **v1.3.9 behavior**: Absolutely no tables are created automatically on startup. To initialize database schema, run:
  ```bash
  aq db makemigrations
  aq db migrate
  ```
  Or set `AQUILIA_AUTO_MIGRATE=1` in your deployment environment if you want auto-creation on boot.

### 2. Server Startup Diagnostics
If your database is missing or has pending migrations when booting with `auto_migrate=False`, server boot no longer crashes with `SchemaFault`. Instead, a yellow diagnostic warning banner is displayed in stderr instructing you on the required `aq db` commands.

### 3. Transactional DDL Safety
Failed migrations or `create_tables()` calls now automatically roll back cleanly, eliminating partial table artifacts.

---

## Upgrade Checklist

- [x] Update `aquilia` dependency to `v1.3.9`.
- [x] Run `aq db status` to verify migration tracking history status.
- [x] If deploying in production with `auto_migrate=False`, ensure database schema is applied via `aq db migrate` in deployment CI/CD pipelines.
- [x] Verify test suites pass cleanly with `./.venv/bin/pytest tests/`.
