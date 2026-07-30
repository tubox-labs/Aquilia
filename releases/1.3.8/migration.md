# Aquilia v1.3.8 Migration Guide

## Upgrade Overview

Aquilia v1.3.8 is a **zero-breaking-change patch release** focused on ORM Migration DSL Generator correctness, topological model dependency sorting, and snapshot serialization robustness.

All existing code, model definitions, and applied database migrations remain 100% compatible with v1.3.8.

---

## Upgrade Steps

### 1. Upgrade Package Version

Upgrade Aquilia in your environment via `pip` or `uv`:

```bash
pip install --upgrade aquilia==1.3.8
```

Or using `uv`:

```bash
uv add aquilia==1.3.8
```

### 2. Verify Generated Migrations

If you previously generated migration DSL files with v1.3.7 that experienced syntax errors (such as `default=<UserStatus.ACTIVE: 'active'>`) or character-split indexes (`columns=['t', 'o', 'k', 'e', 'n']`), delete those un-applied migration files and re-run:

```bash
aq db makemigrations
```

The newly generated migration files will automatically incorporate:
- Topological model creation order (`users` created before `email_verification`).
- Resolved target table names (`"users"` instead of `"usersmodel"`).
- Resolved database column names (`"user_id"` instead of `"user"`).
- Clean scalar Enum defaults (`default='active'`).
- Valid index column arrays (`columns=['token']`).

### 3. Apply Pending Migrations

Execute the migration runner:

```bash
aq db migrate
```

---

## Compatibility Summary

| Component | Status | Notes |
|---|---|---|
| Model Definitions | 100% Compatible | No changes required to `Model` or `Field` declarations. |
| Existing Applied Migrations | 100% Compatible | Applied migration files in `migrations/` continue to work without modification. |
| Migration Runner | Enhanced | Fully supports topological model execution and dependencies metadata. |
| Database Engines | 100% Compatible | Verified against SQLite, PostgreSQL, MySQL, and Oracle. |
