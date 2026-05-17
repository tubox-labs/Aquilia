---
name: aquilia-database-orm-migrations
description: "Build Aquilia database, sqlite, ORM model, query, transaction, and migration workflows. Use for DatabaseIntegration, typed DB configs, AquiliaDatabase, native sqlite, Model fields/managers, makemigrations/migrate/sqlmigrate/inspectdb/status, and schema snapshots."
---

# Aquilia Database Orm Migrations

## Purpose
Implement and debug Aquilia database and model workflows from typed config through migrations.

## Trigger Conditions
Use for `Workspace.database`, `Integration.database`, `SqliteConfig`/`PostgresConfig`/`MysqlConfig`/`OracleConfig`, `AquiliaDatabase`, native sqlite, `Model` subclasses, fields, querysets, transactions, and `aq db` commands.

## Inputs
- Database URL or typed config.
- Model classes and fields.
- Migration directory, app filter, database alias, and whether to emit DSL or SQL.

## Execution Flow
1. Configure DB globally through `Workspace.database(...)` or `Integration.database(config=...)`.
2. Define models as Python `Model` subclasses with fields from `aquilia.models`.
3. Use async query APIs such as `Model.objects.filter(...).all()`, `Model.create(...)`, and transaction helpers.
4. Generate migrations with `aq db makemigrations`; apply with `aq db migrate`; inspect with `showmigrations`, `sqlmigrate`, `status`, or `inspectdb`.
5. For sqlite internals, use native `aquilia.sqlite` rather than deprecated aiosqlite paths.

## Constraints
- Use parameterized query APIs; do not construct SQL with untrusted field/table names.
- Manifest-level database config is deprecated and ignored at runtime.
- Migration snapshots use Crous binary where available; do not hand-edit unless necessary.

## Implementation Anchors
`aquilia/db/configs.py`, `aquilia/db/engine.py`, `aquilia/sqlite/`, `aquilia/models/base.py`, `aquilia/models/fields_module.py`, `aquilia/models/migration_gen.py`, `aquilia/cli/commands/model_cmds.py`, `examples/sqlite_inventory_app/`.

## Examples
- Add `SqliteConfig(path="runtime/app.db", auto_create=True)` to a workspace.
- Create `class Project(Model): key = CharField(max_length=64, unique=True)`.
- Run `aq db makemigrations --app inventory` then `aq db migrate --plan`.

## Failure Handling
Unsupported URLs raise database connection faults. Field validation raises `FieldValidationFault`. If startup guard complains about migrations, generate/apply migrations or set an explicit development auto-migration policy.
