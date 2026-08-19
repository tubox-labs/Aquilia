# Bug Fixes — v1.4.0b6

## Workspace modules were not importable while loading migrations

### Symptoms

`aq db makemigrations` succeeded for a model using an enum declared in a
workspace module, but `aq db migrate` failed with an error like:

```text
[FIELD_VALIDATION_FAILED] Field 'enum_class': cannot import
'modules.users.models.UserStatus': No module named 'modules'
```

The same issue affected commands that load migration files for planning or
inspection, including `aq db sqlmigrate`.

### Root cause

Model discovery already inserted the workspace root into `sys.path`. Migration
loading used `spec_from_file_location()` directly and did not perform that
bootstrap. A console-script process therefore had no import path for the
workspace's `modules/` package when `EnumField` resolved its serialized enum
class path.

### Fix

`load_migration_module()` now locates the workspace that owns the migration by
walking upward from the migration directory, with a current-working-directory
fallback. When it finds `workspace.py` or `aquilia.py`, it inserts that resolved
root into `sys.path` once before executing the migration module.

The behavior is shared by `MigrationEngine`, `aq db migrate`, `aq db sqlmigrate`,
and other callers of the migration loader. Enum classes and other application
references remain required to exist at their serialized dotted paths; the fix
only restores the import path that the CLI previously established during model
discovery.

## VectorDB declaration documentation was stale

The package documentation led with the older `typing.Annotated` marker syntax,
even though the implementation supports a unified descriptor API with defaults,
validation, aliases, embedding options, and field query expressions. The
VectorDB docstrings now show the descriptor form first and include equivalent
`Annotated` examples as supported compatibility syntax.
