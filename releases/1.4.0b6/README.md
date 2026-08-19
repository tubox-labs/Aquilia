# Aquilia v1.4.0b6 Release Notes — "Safe Passage"

Aquilia v1.4.0b6 fixes migration deserialization when generated migration files
refer to application code in workspace modules. This is especially visible with
`EnumField`, whose generated `enum_class` value is a dotted path such as
`modules.users.models.UserStatus`.

## Highlights

- Migration loading discovers the owning workspace from `workspace.py` or
  `aquilia.py`.
- The workspace root is added to `sys.path` before migration code executes.
- `aq db migrate`, `aq db sqlmigrate`, migration status/check flows, and direct
  `MigrationEngine` loads use the same import bootstrap.
- A CLI regression test reproduces the installed `aq` process conditions and
  verifies that an EnumField migration applies successfully.
- VectorDB documentation now presents `Field(...)`, `KeyField`, `TextField`,
  `VectorField`, and `ScoreField` as the recommended declaration surface while
  retaining the PEP 593 `Annotated` form for compatibility.

## Compatibility

There are no public API or migration-file format changes. Existing migrations
continue to load. The import bootstrap is idempotent and only affects processes
that load a migration while a Python-native workspace marker is available.

See [Bug Fixes](bug_fixes.md) and the [Migration Guide](migration.md) for the
root cause and upgrade notes.
