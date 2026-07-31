# CLI Changes — Aquilia v1.3.10

The migration-related `aq db` commands have been updated to use `MigrationEngine` throughout. Legacy `MigrationRunner`, `DSLMigrationRunner`, and `generate_dsl_migration` paths are removed from the CLI layer.

---

## `aq db makemigrations`

### Removed Flags

| Flag | Previous behaviour | Status |
|---|---|---|
| `--use-dsl` / `--no-use-dsl` | Toggle between DSL and legacy raw-SQL generator | **Removed** |
| `--migration-format` | Choose `"json"` or `"python"` output format | **Removed** |

### New Flags

| Flag | Description | Default |
|---|---|---|
| `--slug TEXT` | Human-readable suffix appended to the filename | Derived from affected models |
| `--dry-run` | Compute and print the migration without writing any files | `False` |

### New Behaviour

- The generated migration always uses the new sub-package format (real Python constructors, `MIGRATION_TEMPLATE_VERSION = 3`).
- The snapshot file is now always written alongside the migration at `<migrations_dir>/schema_snapshot.json`.
- `--dry-run` prints what would be generated (including the operation list) without touching the filesystem.

### Examples

```bash
# Generate a migration for all models in the workspace
aq db makemigrations

# Generate a migration for a specific module only
aq db makemigrations --app blog

# Named migration
aq db makemigrations --slug add_biography

# Verbose: see every model that was scanned
aq db makemigrations --verbose

# Dry-run: print operations without writing
aq db makemigrations --dry-run

# Custom migrations directory
aq db makemigrations --migrations-dir src/migrations
```

### Before / After Comparison

```bash
# v1.3.9 (old flags)
aq db makemigrations --use-dsl --migration-format python

# v1.3.10 (removed — equivalent is just)
aq db makemigrations
```

---

## `aq db migrate`

### Changes

The CLI now drives `MigrationEngine` instead of the old `MigrationRunner`:

- `--plan` output now shows `Statement.description` and marks destructive statements in red:
  ```
  -- DESTRUCTIVE: Drop column 'legacy_id' from 'users'
  ALTER TABLE "users" DROP COLUMN "legacy_id";
  ```
- `--verbose` now emits per-migration `ExecutionResult.diagnostics`.
- The return value is now built from `engine.status(db).applied` — a complete, ordered list of all applied revisions — rather than just the revisions applied in the current run.

### Examples

```bash
# Apply all pending migrations
aq db migrate

# Apply against a specific database URL
aq db migrate --database-url postgresql+asyncpg://user:pass@localhost/mydb

# Dry-run: show SQL without executing
aq db migrate --plan

# Roll back to a specific revision
aq db migrate --target 20260720_120000

# Fake: mark migrations as applied without executing DDL
aq db migrate --fake

# Verbose diagnostics
aq db migrate --verbose
```

---

## `aq db showmigrations`

### Changes

Updated to use `MigrationExecutor` and `revision_from_path` from the new sub-package:

```python
# Internal change (not visible to users)
# Old: from aquilia.models.migration_runner import MigrationRunner
# New:
from aquilia.models.migration.executor import MigrationExecutor
from aquilia.models.migration.serializer import revision_from_path
```

Output format and flags are unchanged.

### Example

```bash
aq db showmigrations
# [x] 20260701_120000_initial
# [x] 20260730_120000_add_user
# [ ] 20260801_103000_add_bio      ← pending
```

---

## `aq db diff`

### Changes

The `diff` command now uses `detect_changes` from `migration.autodetect` and `ProjectState.from_database` instead of the old snapshot-diffing machinery from `schema_snapshot`.

**New output format:** Instead of a `difflib` unified-diff text block, `diff` now prints one line per operation:

```
Drift detected -- 2 change(s) needed:

--- database (active)
+++ schema (target)

  + AddField: Add 'biography' (TextField) to 'User'
  + CreateIndex: Create index 'idx_user_biography' on 'User'

Run `aq db makemigrations` to record these changes as a migration.
```

The old format printed raw SQL fragments; the new format prints semantic operation descriptions.

### Rename inference off by default for `diff`

When comparing a live database against the snapshot, rename inference is disabled (`infer_renames=False`). A rename is indistinguishable from a drop-plus-add when one side was introspected; guessing wrong would report data-preserving drift as destructive.

### Examples

```bash
# Compare live database against the snapshot
aq db diff

# Compare live database against model definitions
aq db diff --compare models

# Specify migrations directory
aq db diff --migrations-dir src/migrations
```

---

## `aq db reset`

### Changes

The reset command now correctly handles the case where the tracking table survived the drop:

```python
# v1.3.10: After dropping tables, clear the tracking table if it still exists
# before re-applying migrations — otherwise migrate() sees nothing pending.
engine = MigrationEngine(migrations_dir)
remaining = await db.get_tables()
if "aquilia_migrations" in remaining:
    await db.execute('DELETE FROM "aquilia_migrations"')
results = await engine.migrate(db)
```

This fixes a bug where `reset` on certain dialects (MySQL, some PostgreSQL configurations) could leave the tracking table intact after a drop, causing `migrate()` to report "Nothing to do" on a completely empty database.

### Example

```bash
aq db reset --database-url sqlite:///dev.db
```

---

## `aq db status`

No changes to the CLI interface. The underlying `MigrationStatus` object is now returned by `MigrationEngine.status()`.

---

## Common Migration Workflow

```bash
# 1. Define or modify your models
# 2. Generate a migration
aq db makemigrations --slug describe_your_change

# 3. Review the generated migration
cat migrations/20260801_103000_describe_your_change.py

# 4. Preview the SQL
aq db migrate --plan

# 5. Apply
aq db migrate

# 6. Verify
aq db showmigrations
aq db status
```

---

## Anti-Patterns

```bash
# ❌ Don't edit migration files after applying them to any environment.
# The checksum recorded in aquilia_migrations will no longer match,
# and verify_checksums will report a mismatch.

# ❌ Don't delete migration files that have been applied.
# The engine will report the revision as "missing from disk".

# ✅ To squash migrations, use the replaces metadata:
#    Set node.replaces = ("old_rev_1", "old_rev_2") in your squash migration.
```
