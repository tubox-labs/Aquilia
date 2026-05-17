# Sqlite CLI Reference

This page is derived from the mounted Click command tree. If a source file has CLI helper functions but they are not mounted under `aq`, this page states that explicitly.

## Relationship To The `aq` CLI

The following mounted commands map to this subsystem.

| Command | Syntax | Purpose |
| --- | --- | --- |
| `aq db makemigrations` | `aq db makemigrations [--app VALUE] [--migrations-dir VALUE] [--dsl VALUE] [--format VALUE]` | Generate migration files from Python Model definitions. |
| `aq db migrate` | `aq db migrate [--migrations-dir VALUE] [--database-url VALUE] [--database VALUE] [--target VALUE] [--fake] [--plan]` | Apply pending migrations to the database. |
| `aq db dump` | `aq db dump [--emit VALUE] [--output-dir VALUE]` | Dump model schema -- annotated Python overview or raw SQL DDL. |
| `aq db shell` | `aq db shell [--database-url VALUE]` | Open an async REPL with models pre-loaded. |
| `aq db inspectdb` | `aq db inspectdb [--database-url VALUE] [--table VALUE] [--output VALUE]` | Introspect database and generate Model definitions. |
| `aq db showmigrations` | `aq db showmigrations [--migrations-dir VALUE] [--database-url VALUE] [--database VALUE]` | Show all migrations and their applied/pending status. |
| `aq db sqlmigrate` | `aq db sqlmigrate MIGRATION_NAME [--migrations-dir VALUE] [--database VALUE]` | Display SQL statements for a specific migration. |
| `aq db status` | `aq db status [--database-url VALUE]` | Show database status -- tables, row counts, columns. |

## Detailed Commands

### `aq db makemigrations`

Generate migration files from Python Model definitions.

```bash
aq db makemigrations [--app VALUE] [--migrations-dir VALUE] [--dsl VALUE] [--format VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `app` | `--app` | False | `` | Restrict to specific module/app |
| Option | `migrations_dir` | `--migrations-dir` | False | `migrations` | Migrations directory |
| Option | `dsl` | `--dsl, --no-dsl` | False | `True` | Use new DSL format (default: True) |
| Option | `fmt` | `--format` | False | `crous` | Migration file format -- crous (binary, default) or python |

### `aq db migrate`

Apply pending migrations to the database.

```bash
aq db migrate [--migrations-dir VALUE] [--database-url VALUE] [--database VALUE] [--target VALUE] [--fake] [--plan]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `migrations_dir` | `--migrations-dir` | False | `migrations` | Migrations directory |
| Option | `database_url` | `--database-url` | False | `` | Database URL (auto-detected from workspace.py) |
| Option | `database` | `--database` | False | `` | Database alias (for multi-db) |
| Option | `target` | `--target` | False | `` | Target revision (or "zero" to rollback all) |
| Option | `fake` | `--fake` | False | `False` | Mark migrations as applied without running SQL |
| Option | `plan` | `--plan` | False | `False` | Preview SQL without executing (dry-run) |

### `aq db dump`

Dump model schema -- annotated Python overview or raw SQL DDL.

```bash
aq db dump [--emit VALUE] [--output-dir VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `emit` | `--emit` | False | `python` | Output format |
| Option | `output_dir` | `--output-dir` | False | `` | Output directory |

### `aq db shell`

Open an async REPL with models pre-loaded.

```bash
aq db shell [--database-url VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `database_url` | `--database-url` | False | `` | Database URL (auto-detected from workspace.py) |

### `aq db inspectdb`

Introspect database and generate Model definitions.

```bash
aq db inspectdb [--database-url VALUE] [--table VALUE] [--output VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `database_url` | `--database-url` | False | `` | Database URL (auto-detected from workspace.py) |
| Option | `table` | `--table` | False | `not set` | Specific tables to inspect |
| Option | `output` | `--output` | False | `` | Output file path |

### `aq db showmigrations`

Show all migrations and their applied/pending status.

```bash
aq db showmigrations [--migrations-dir VALUE] [--database-url VALUE] [--database VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `migrations_dir` | `--migrations-dir` | False | `migrations` | Migrations directory |
| Option | `database_url` | `--database-url` | False | `` | Database URL (auto-detected from workspace.py) |
| Option | `database` | `--database` | False | `` | Database alias |

### `aq db sqlmigrate`

Display SQL statements for a specific migration.

```bash
aq db sqlmigrate MIGRATION_NAME [--migrations-dir VALUE] [--database VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Argument | `migration_name` | `migration_name` | True | `not set` |  |
| Option | `migrations_dir` | `--migrations-dir` | False | `migrations` | Migrations directory |
| Option | `database` | `--database` | False | `` | Database alias |

### `aq db status`

Show database status -- tables, row counts, columns.

```bash
aq db status [--database-url VALUE]
```

| Kind | Name | Flags | Required | Default | Help |
| --- | --- | --- | --- | --- | --- |
| Option | `database_url` | `--database-url` | False | `` | Database URL (auto-detected from workspace.py) |

## General Commands Useful For This Module

| Command | Why it matters |
| --- | --- |
| `aq validate` | Validates workspace manifests and catches invalid component paths. |
| `aq doctor` | Runs environment, workspace, manifest, registry, integration, and deployment diagnostics. |
| `aq inspect config` | Shows resolved config after workspace/env merging. |
| `aq inspect modules` | Lists discovered modules. |
| `aq inspect routes` | Shows compiled routes when the module contributes controllers. |
| `aq run` | Starts the dev server and executes startup wiring. |

## Error Behavior

- Click handles missing required arguments and invalid options before command callbacks run.
- Most operational commands require `workspace.py`; the root CLI guard allows help/version/init/doctor without it.
- Commands that touch external providers, databases, or files can fail with subsystem-specific faults or provider errors.
