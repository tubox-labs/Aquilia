# aq model / aq db

Model and database commands for ORM operations, migrations, schema introspection, and interactive REPL. All commands are accessed via the `aq db` command group.

## Usage

All commands are under the `aq db` group:

```bash
aq db <SUBCOMMAND> [OPTIONS]
```

## Commands Overview

| Command                | Description                                              |
| ---------------------- | -------------------------------------------------------- |
| `aq db makemigrations` | Generate migration files from Model definitions          |
| `aq db migrate`        | Apply pending migrations to the database                 |
| `aq db showmigrations` | Show migration status (applied/pending)                  |
| `aq db sqlmigrate`     | Display SQL for a specific migration                     |
| `aq db inspectdb`      | Introspect database and generate Model definitions       |
| `aq db status`         | Show database tables, row counts, and columns            |
| `aq db dump`           | Dump model schema as annotated Python or raw SQL         |
| `aq db shell`          | Open async REPL with all models pre-loaded               |

For full details, see the [aq db reference page](migrate.md).

## Interactive Shell

```bash
aq db shell
```

The shell provides an async REPL with:

- All discovered `Model` subclasses in the namespace
- `Q` query builder for constructing queries
- `ModelRegistry` for model introspection
- `db` — the active database connection
- `asyncio` and `loop` for running async operations

### Shell Operations

```python
# Fetch by primary key
loop.run_until_complete(User.get(pk=1))

# Filter with conditions
loop.run_until_complete(User.filter(name="John"))

# Query builder
q = Q().eq(User.name, "John").gt(User.age, 18)
loop.run_until_complete(User.filter(q))

# Create
loop.run_until_complete(User.create(name="Jane", email="jane@example.com"))

# Count
loop.run_until_complete(User.count())
```

## Model Discovery

Models are discovered from:

1. `modules/*/models/` packages (directory with `__init__.py`)
2. `modules/*/models.py` single-file modules
3. `models/` at workspace root
4. Admin models (auto-included when admin integration is enabled)

## See Also

- [`aq db`](migrate.md) — Full database command reference
- [Model Class Reference](/reference/classes/model/) — Model API reference