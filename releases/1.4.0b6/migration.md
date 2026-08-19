# Migration and Upgrade Guide — v1.4.0b5 → v1.4.0b6

## Upgrade

```bash
python -m pip install --upgrade --no-cache-dir "aquilia==1.4.0b6"
```

No migration files need to be regenerated. Existing generated migrations that
contain dotted workspace references load with the new runner.

## Workspace requirements

The loader identifies a Python-native workspace by `workspace.py` or
`aquilia.py`. Keep the migration directory below that workspace root when using
the standard project layout. A command launched from the workspace root also
continues to work when a custom migration directory is outside the usual
`migrations/` name, provided the path can be associated with the workspace.

## Before and after

```text
Before: aq db makemigrations succeeds, but aq db migrate fails with
        No module named 'modules' for an EnumField migration.
After:  the migration loader bootstraps the workspace root before it resolves
        modules.users.models.UserStatus, so the migration applies normally.
```

## Application changes

No application code changes are required. Enum classes referenced by generated
migrations must still remain importable at their recorded dotted path; moving or
renaming such a class requires the same compatibility handling as before.

## Verification

Run the migration commands from a workspace containing an EnumField migration:

```bash
aq --version
aq db migrate
aq db sqlmigrate <migration-name>
aq db showmigrations
```

The release includes a regression test that starts with no cached `modules.*`
imports and applies an EnumField migration through the Click CLI entry point.
