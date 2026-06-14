# aq db

Database ORM commands for migration management, schema introspection, and an interactive shell.

## Usage

```bash
aq db <SUBCOMMAND> [OPTIONS]
```

## aq db makemigrations

Generate migration files from Python Model definitions.

```bash
aq db makemigrations [OPTIONS]
```

| Option              | Description                                                | Default        |
| ------------------- | ---------------------------------------------------------- | -------------- |
| `--app`             | Restrict to a specific module/app                          | `None`         |
| `--migrations-dir`  | Migrations directory                                       | `migrations`   |
| `--dsl` / `--no-dsl`| Use DSL format (default: `True`)                           | `True`         |
| `--format`          | Migration format: `surp` (binary) or `python` (readable)   | `surp`         |

Model discovery searches:

1. `modules/*/models/` packages
2. `modules/*/models.py` files
3. `models/` at workspace root

When admin integration is enabled, admin models (`AdminUser`, `AdminAuditEntry`, `AdminAPIKey`, `AdminPreference`) are automatically included.

```bash
aq db makemigrations
aq db makemigrations --app=products
aq db makemigrations --format=python
aq db makemigrations --no-dsl
```

## aq db migrate

Apply pending migrations to the database.

```bash
aq db migrate [OPTIONS]
```

| Option             | Description                                                | Default         |
| ------------------ | ---------------------------------------------------------- | --------------- |
| `--migrations-dir` | Migrations directory                                       | `migrations`    |
| `--database-url`   | Database URL (auto-detected from `workspace.py`)           | auto-detected   |
| `--database`       | Database alias for multi-db setups                         | `None`          |
| `--target`         | Target revision (or `"zero"` to rollback all)              | `None` (latest) |
| `--fake`           | Mark as applied without executing SQL                      | `False`         |
| `--plan`           | Preview SQL without executing (dry-run)                    | `False`         |

The database URL is auto-detected from `workspace.py` by scanning for `.database(url="...")` or typed config patterns (`MysqlConfig`, `PostgresConfig`, `OracleConfig`). Falls back to `sqlite:///db.sqlite3`.

```bash
aq db migrate
aq db migrate --plan
aq db migrate --fake
aq db migrate --target=zero
aq db migrate --database-url=sqlite:///prod.db
```

## aq db showmigrations

Show all migrations and their applied/pending status.

```bash
aq db showmigrations [OPTIONS]
```

```bash
aq db showmigrations
aq db showmigrations --migrations-dir=db/migrations
```

Output:

```
  [X] 20260217_210454_initial
  [X] 20260218_091530_add_users_table
  [ ] 20260218_142800_add_products_table
```

## aq db sqlmigrate

Display SQL statements for a specific migration.

```bash
aq db sqlmigrate <MIGRATION_NAME> [OPTIONS]
```

For DSL migrations, compiles operations to SQL for the current dialect. For legacy migrations, extracts SQL from the source.

```bash
aq db sqlmigrate 20260217_210454
aq db sqlmigrate 0002 --migrations-dir=db/migrations
```

## aq db inspectdb

Introspect an existing database and generate Model class definitions.

```bash
aq db inspectdb [OPTIONS]
```

| Option           | Description                                                | Default       |
| ---------------- | ---------------------------------------------------------- | ------------- |
| `--database-url` | Database URL (auto-detected)                               | auto-detected |
| `--table`        | Specific tables to inspect (repeatable)                    | all tables    |
| `--output`       | Output file path for generated models                      | stdout        |

Generates Python `Model` subclasses with field type mapping from SQL column types.

```bash
aq db inspectdb
aq db inspectdb --table=users --table=orders
aq db inspectdb --output=models/generated.py
```

## aq db status

Show database status — tables, row counts, column counts.

```bash
aq db status [OPTIONS]
```

```bash
aq db status
aq db status --database-url=sqlite:///prod.db
```

Output:

```
  users                             42 rows  (5 columns)
  products                         156 rows  (8 columns)
  orders                          1024 rows  (12 columns)

  Total: 3 table(s), 1222 row(s)
```

## aq db dump

Dump model schema as annotated Python overview or raw SQL DDL.

```bash
aq db dump [OPTIONS]
```

| Option        | Description                | Default   |
| ------------- | -------------------------- | --------- |
| `--emit`      | Format: `python` or `sql`  | `python`  |
| `--output-dir`| Output directory           | stdout    |

```bash
aq db dump
aq db dump --emit=sql
aq db dump --output-dir=generated/
```

## aq db shell

Open an async REPL with all discovered models pre-loaded.

```bash
aq db shell [OPTIONS]
```

Available in the shell namespace:

- All discovered `Model` subclasses
- `Q` query builder
- `ModelRegistry`
- `db` database connection
- `asyncio` and `loop`

```bash
aq db shell
aq db shell --database-url=sqlite:///prod.db
```

!!! tip "Async Operations"
    Use `loop.run_until_complete()` for async operations in the shell:
    ```python
    loop.run_until_complete(User.get(pk=1))
    loop.run_until_complete(User.filter(name="John"))
    ```

## Database URL Auto-Detection

The CLI auto-detects the database URL from `workspace.py` in this order:

1. `.database(url="...")` or `Integration.database(url="...")`
2. Typed config: `MysqlConfig(...)`, `PostgresConfig(...)`, `OracleConfig(...)`
3. Fallback: `sqlite:///db.sqlite3`

## See Also

- [`aq migrate`](#) — Legacy project migration (different from DB migrations)
- [`aq admin`](admin.md) — Admin dashboard and superuser management