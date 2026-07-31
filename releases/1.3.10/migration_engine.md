# Migration Engine Architecture — Aquilia v1.3.10

Aquilia v1.3.10 replaces all previous migration modules with a single, coherent `aquilia.models.migration` sub-package. This document describes every layer, its responsibilities, design rationale, and public API.

---

## Package Layout

```
aquilia/models/migration/
├── __init__.py        # Public API re-exports
├── schema.py          # Immutable schema state (ProjectState, TableState, ColumnState, …)
├── operations/        # Typed, backend-independent operations
│   ├── __init__.py
│   ├── base.py        # Operation ABC, OperationCategory, register_operation
│   ├── models.py      # CreateModel, DeleteModel, RenameModel, AlterModelOptions
│   ├── fields.py      # AddField, RemoveField, AlterField, RenameField
│   ├── indexes.py     # AddIndex, RemoveIndex, AlterIndex
│   ├── constraints.py # AddConstraint, RemoveConstraint, AlterConstraint
│   ├── relations.py   # CreateManyToManyTable, DeleteManyToManyTable
│   └── special.py     # RunSQL, RunPython
├── backends/          # Dialect-aware SQL generation
│   ├── __init__.py    # SchemaBackend ABC, Statement, get_backend()
│   ├── sqlite.py
│   ├── postgresql.py
│   ├── mysql.py
│   └── oracle.py
├── autodetect.py      # State-to-state diffing; RenameHint; Autodetector
├── graph.py           # MigrationGraph, MigrationNode
├── optimizer.py       # Operation reduction
├── codegen.py         # Python source rendering
├── serializer.py      # File writing / loading
├── executor.py        # Transactional application against a live database
├── probe.py           # Pre-connection SQLite readiness probes
└── engine.py          # MigrationEngine — single public entry point
```

---

## `MigrationEngine` — Single Entry Point

`MigrationEngine` is the single class the CLI, the server startup path, and application code all interact with. It delegates to every other layer and owns no SQL itself.

```python
from aquilia.models.migration import MigrationEngine

engine = MigrationEngine("migrations")   # dir that holds .py files + snapshot
```

### `make_migrations(model_classes, *, slug, hints, infer_renames, dry_run) → Path | None`

Generates a migration for the difference between the on-disk snapshot and the given models.

**Process:**
1. Loads the last recorded `ProjectState` from `schema_snapshot.json`
2. Builds a new `ProjectState` from the live model classes
3. Runs the `Autodetector` to compute a raw operation list
4. Passes operations through the `Optimizer` to collapse redundancy
5. Allocates a timestamp revision, stepping past collisions
6. Renders the migration with `codegen` + `serializer` as a real Python file
7. Writes the migration file **first**, then saves the updated snapshot

**Why file before snapshot?** If the write fails, the snapshot still describes the last successful migration and the change can simply be regenerated. Writing the snapshot first would advance it past a migration that was never recorded on disk — the next `makemigrations` would then see no diff.

```python
# Basic usage
path = engine.make_migrations([User, Post])
# → PosixPath('migrations/20260801_103000_user_post.py')

# Named migration
path = engine.make_migrations([User], slug="add_bio")
# → PosixPath('migrations/20260801_103001_add_bio.py')

# Dry-run: compute but write nothing
path = engine.make_migrations([User, Post], dry_run=True)
# → None  (no files written)

# Explicit rename hint
from aquilia.models.migration import RenameHint
hint = RenameHint(model="User", old_name="bio", new_name="biography")
path = engine.make_migrations([User], hints=(hint,))
```

### `async migrate(db, *, target, fake) → list[ExecutionResult]`

Applies pending migrations forward, or rolls back to `target`.

```python
# Apply all pending migrations
results = await engine.migrate(db)
for r in results:
    print(r.statements_executed, r.duration_ms)

# Roll back to a specific revision
await engine.migrate(db, target="20260720_120000")

# Fake: record migrations without executing DDL
await engine.migrate(db, fake=True)
```

### `async status(db) → MigrationStatus`

Reports which migrations are applied and which are pending.

```python
status = await engine.status(db)
print(status.describe())
# Applied: 4
# Pending: 1
#   - 20260801_103000_add_bio
# Last applied: 20260730_120000
```

`MigrationStatus` attributes:
- `applied: tuple[str, ...]` — revisions applied, in application order
- `pending: tuple[MigrationNode, ...]` — pending nodes, in dependency order
- `leaves: tuple[str, ...]` — tips of the graph (> 1 = branched history)
- `is_current: bool` — True when nothing is pending

### `async plan(db, *, target) → list[Statement]`

Compiles pending migrations to SQL without executing anything. Useful for code review and deployment pipelines.

```python
statements = await engine.plan(db)
for stmt in statements:
    if stmt.destructive:
        print(f"DESTRUCTIVE: {stmt.description}")
    print(stmt.sql)
```

### `async verify_checksums(db) → list[dict]`

Reports applied migrations whose source files have changed since they were applied.

```python
mismatches = await engine.verify_checksums(db)
for m in mismatches:
    print(m["revision"], m["reason"])
```

### `state_at(revision) → ProjectState`

Replays migrations from disk up to and including `revision`, reconstructing the schema state without touching the database.

### `state_for(applied) → ProjectState`

Reconstructs the state produced by exactly the given set of applied revisions — the right method when applied and on-disk don't form a linear prefix.

---

## `ProjectState` — Immutable Schema State

`ProjectState` is a fully-typed, immutable description of a database schema. It preserves model semantics — generated-column expressions, M2M relationships, index methods, partial-index predicates, composite PKs — rather than reducing them to primitive column definitions.

### Design Rationale

Reducing every `Field` to a handful of primitives (name, SQL type, a few booleans) destroys information at the very first hop. Nothing downstream can recover a generated-column expression or an operator class from a primitive snapshot. `ProjectState` therefore captures fields through `Field.deconstruct()`, retaining enough to reconstruct them faithfully.

### Construction

```python
from aquilia.models.migration.schema import ProjectState

# From live model classes
state = ProjectState.from_models([User, Post, Comment])

# From a serialised dict (snapshot file)
state = ProjectState.from_dict(raw_dict)

# Empty state (before any migrations)
state = ProjectState()
```

### Key State Objects

| Class | Description |
|---|---|
| `ProjectState` | Top-level container; `tables: dict[str, TableState]` |
| `TableState` | One table; columns, indexes, constraints, M2M relations, db_table, ordering |
| `ColumnState` | One column; field class + deconstruct kwargs + reference |
| `IndexState` | One index; columns, method, unique, condition, include columns |
| `ConstraintState` | Base for check, unique, exclusion, FK, PK constraint states |
| `ManyToManyState` | M2M junction table descriptor |
| `Reference` | A (table, column) pair used for FK wiring |

### `creation_order() → list[str]`

Returns table names topologically sorted so that referenced tables appear before their dependents — the order in which `CREATE TABLE` statements must run.

```python
state = ProjectState.from_models([Post, User, Comment])
order = state.creation_order()
# ['User', 'Post', 'Comment']  — User before Post (FK), Post before Comment (FK)
```

### `from_database(db, model_classes) → ProjectState`

Introspects a live database to reconstruct its current state. Used by `aq db diff`.

---

## `MigrationGraph` and `MigrationNode` — Dependency DAG

Every migration file on disk becomes a `MigrationNode` in a `MigrationGraph`. The graph provides topological ordering, conflict detection, forward and backward planning, and leaf discovery.

### `MigrationNode`

```python
@dataclass(frozen=True)
class MigrationNode:
    revision: str            # e.g. "20260801_103000"
    slug: str                # e.g. "add_bio"
    operations: tuple[Operation, ...]
    dependencies: tuple[str, ...]   # revisions that must come first
    replaces: tuple[str, ...]       # squashed revisions (safe on deployed DBs)
    atomic: bool             # False when any op emits a non-transactional stmt
    source_path: Path | None
    checksum: str            # SHA-256 of the source file

    @property
    def name(self) -> str:   # "20260801_103000_add_bio"
```

### Design: Why a Graph Matters

An earlier design had `dependencies` in every generated file but never read them — ordering came from sorting filenames. That works only while every migration is generated on one machine in one linear sequence. Two developers generating a migration on the same day produce filenames that sort by timestamp into an order neither intended. A graph reads the declared dependencies and plans correctly regardless.

### `MigrationGraph.forward_plan(applied) → tuple[MigrationNode, ...]`

Returns pending nodes in the order they must be applied, respecting all declared dependencies.

### `MigrationGraph.backward_plan(applied, target) → tuple[MigrationNode, ...]`

Returns the nodes to roll back (in reverse dependency order) to reach `target`.

### `MigrationGraph.check_conflicts()`

Raises `MigrationConflictFault` if two migrations share a revision or if two leaf nodes share no common ancestor — i.e. the history has forked without a merge migration.

### Squash Support

A node with `replaces = ("20260701_120000", "20260710_150000")` is treated as already applied when every listed revision is in the applied set. This is how squashing is safe on a deployed database: the squash migration records itself as done without re-running DDL that is already in the schema.

---

## `Autodetector` — Deterministic, Safe Diffing

The autodetector compares two `ProjectState` objects and emits the operations needed to transform one into the other.

### Determinism

Every collection is iterated in sorted order; results are ordered by explicit rules, never by set iteration. Two runs over the same states — in different processes with different `PYTHONHASHSEED` — produce identical operation lists. This is not an accident: iterating a `set` anywhere in the diff path makes the migration order change on every interpreter run.

### Rename Detection

A rename is a destructive guess. Emitting `RENAME COLUMN` when the developer actually dropped one column and added another silently rewrites the wrong column and loses its data. Rename is therefore inferred only from:

1. An explicit `RenameHint` from the developer.
2. A combined confidence score across multiple signals (`RENAME_CONFIDENCE_THRESHOLD = 0.85`). No single signal — not even an identical type — clears this threshold alone.

```python
from aquilia.models.migration import RenameHint, detect_changes

# Explicit rename instruction
hint = RenameHint(model="User", old_name="bio", new_name="biography")
ops = detect_changes(before, after, hints=(hint,))

# Disable inference entirely (safe for db introspection comparisons)
ops = detect_changes(live, target, infer_renames=False)
```

---

## `Optimizer` — Operation Reduction

The optimizer collapses redundant operations before the migration is written:

| Input | Output |
|---|---|
| `CreateModel(U)` + `AddField(U.bio)` | `CreateModel(U with bio)` |
| `AddField(U.bio)` + `RemoveField(U.bio)` | *(nothing)* |
| `AddField(U.bio)` + `AlterField(U.bio)` | `AddField` with final definition |
| `AlterField(x)` + `AlterField(x)` | one `AlterField` |
| `CreateModel(U)` + `DeleteModel(U)` | *(nothing)* |

`RunSQL` and `RunPython` are treated as opaque barriers — a data migration may well depend on the exact intermediate schema, and merging across it would silently change what it sees.

---

## `MigrationExecutor` — Transactional Application

The executor applies and rolls back migrations against a live database.

### Atomicity

Two atomicity hazards are handled:

1. **History recorded outside the transaction** — the tracking `INSERT` is the last statement *inside* the same transaction, so schema and history commit or roll back together.
2. **Non-transactional statements silently mixed in** — statements declare their own transactional requirement. SQLite table rebuilds need `PRAGMA foreign_keys` outside any transaction; PostgreSQL rejects `CREATE INDEX CONCURRENTLY` inside one. The executor splits accordingly.

On MySQL and Oracle, DDL cannot participate in a transaction at all. The executor detects this from the backend's capability flags and warns rather than promising atomicity it cannot deliver.

### `apply(node, state, fake) → ExecutionResult`

Applies one `MigrationNode` forward. When `fake=True`, records the migration without executing any DDL.

### `rollback(node, state, fake) → ExecutionResult`

Rolls back one `MigrationNode`. Requires every operation to implement `state_backwards` and `database_backwards`.

### `ExecutionResult`

```python
@dataclass
class ExecutionResult:
    statements_executed: int
    statements_skipped: int
    duration_ms: float
    diagnostics: list[str]
```

---

## `SchemaBackend` — Dialect Isolation

`backends/` is the **only** layer that knows about SQL dialects. Nothing in `schema.py`, `operations/`, or `engine.py` imports a backend.

```python
from aquilia.models.migration.backends import get_backend, SchemaBackend

backend = get_backend("postgresql")
stmt = backend.create_table(table_state)
print(stmt.sql)
```

Four backends ship: `sqlite`, `postgresql`, `mysql`, `oracle`.

`Statement` carries:
- `sql: str` — the SQL text
- `description: str` — human-readable description for `aq db migrate --plan`
- `destructive: bool` — whether it could cause data loss
- `transactional: bool` — whether it must run inside a transaction

---

## `Codegen` and `Serializer` — Real Python Constructor Files

The generated migration file uses the same `Field`, index, and constraint classes the developer writes in models — not serialized dictionaries.

### Why Not Dicts?

A dict-serialized migration is unreadable and uneditable. No editor completes a dict key, no type checker catches a misspelled one, and a reviewer cannot see whether a column is nullable. A migration is a permanent, reviewable artifact — often the only record of *why* a schema looks the way it does — and it should be written in the same vocabulary as the models it came from.

### `MIGRATION_TEMPLATE_VERSION = 3`

Bumped to 3 when generated files moved to real constructor calls. Both old and new formats load correctly — the version is informational.

### Generated File Format

```python
# Generated by Aquilia Migration Engine v1.3.10 at 2026-08-01T10:30:00+00:00
# Template version: 3

from aquilia.models.migration import CreateModel, AddField, Operation, ProjectState
from aquilia.models.migration.schema import ColumnState, IndexState, TableState
from aquilia.models import fields

# Metadata
revision: str = "20260801_103000"
slug: str = "add_bio"
dependencies: tuple[str, ...] = ("20260730_120000",)
atomic: bool = True

# Schema changes
operations: list[Operation] = [
    AddField(
        model="User",
        field=ColumnState.of("bio", fields.TextField(null=True, blank=True)),
    ),
]
```

---

## `Probe` — Read-Only Readiness Checks

The probe module answers "is this database ready?" **before** the application opens a connection.

### Why Not Just Connect?

Opening a SQLite database creates its `-wal` and `-shm` sidecar files — even when the connection is immediately closed. A startup check that does this has changed the thing it was checking: a developer who ran a check against a non-existent database now has one that half-exists. Probes open SQLite read-only (`mode=ro`), which never creates a file and never writes a journal.

For non-SQLite backends the probe reports "ready" and lets the normal connection path surface any error. A false "not ready" would block a working deployment; a false "ready" costs only the error the application raises anyway.

```python
from aquilia.models.migration.probe import database_exists, migrations_applied

if not database_exists("sqlite:///app.db"):
    print("Run: aq db migrate")

if not migrations_applied("sqlite:///app.db", "migrations"):
    print("Pending migrations — run: aq db migrate")
```

---

## API Reference Summary

| Symbol | Module | Description |
|---|---|---|
| `MigrationEngine` | `migration.engine` | Generate, plan, apply, roll back |
| `MigrationStatus` | `migration.engine` | Applied / pending summary |
| `SNAPSHOT_FILENAME` | `migration.engine` | `"schema_snapshot.json"` |
| `ProjectState` | `migration.schema` | Immutable schema state |
| `TableState` | `migration.schema` | Per-table state |
| `ColumnState` | `migration.schema` | Per-column state |
| `IndexState` | `migration.schema` | Per-index state |
| `MigrationGraph` | `migration.graph` | Dependency DAG |
| `MigrationNode` | `migration.graph` | One migration in the DAG |
| `Autodetector` | `migration.autodetect` | State-to-state diffing |
| `RenameHint` | `migration.autodetect` | Explicit rename instruction |
| `detect_changes` | `migration.autodetect` | Convenience function |
| `optimize` | `migration.optimizer` | Operation reduction |
| `SchemaBackend` | `migration.backends` | Dialect backend ABC |
| `Statement` | `migration.backends` | Compiled SQL statement |
| `get_backend` | `migration.backends` | Backend factory |
| `MigrationExecutor` | `migration.executor` | Transactional application |
| `ExecutionResult` | `migration.executor` | Per-migration outcome |
| `AppliedMigration` | `migration.executor` | One tracking-table row |
| `MIGRATION_TABLE` | `migration.executor` | `"aquilia_migrations"` |
| `compile_operations` | `migration.executor` | Operations → statements |
| `render_migration_module` | `migration.serializer` | MigrationNode → Python source |
| `load_migration_module` | `migration.serializer` | Python file → MigrationNode |
| `serialize_operations` | `migration.serializer` | Operations → source fragment |
| `revision_from_path` | `migration.serializer` | Extract revision from filename |
| `slug_from_path` | `migration.serializer` | Extract slug from filename |
| `database_exists` | `migration.probe` | SQLite existence check |
| `migrations_applied` | `migration.probe` | Pending-migration check |
| `Operation` | `migration.operations` | Base operation ABC |
| `CreateModel` | `migration.operations` | Create a new model/table |
| `DeleteModel` | `migration.operations` | Drop a model/table |
| `RenameModel` | `migration.operations` | Rename a model/table |
| `AlterModelOptions` | `migration.operations` | Change `Meta` options |
| `AddField` | `migration.operations` | Add a column |
| `RemoveField` | `migration.operations` | Remove a column |
| `AlterField` | `migration.operations` | Change a column's definition |
| `RenameField` | `migration.operations` | Rename a column |
| `AddIndex` | `migration.operations` | Add an index |
| `RemoveIndex` | `migration.operations` | Remove an index |
| `AlterIndex` | `migration.operations` | Modify an index |
| `AddConstraint` | `migration.operations` | Add a table constraint |
| `RemoveConstraint` | `migration.operations` | Remove a table constraint |
| `AlterConstraint` | `migration.operations` | Modify a constraint |
| `CreateManyToManyTable` | `migration.operations` | Create M2M junction table |
| `DeleteManyToManyTable` | `migration.operations` | Drop M2M junction table |
| `RunSQL` | `migration.operations` | Execute raw SQL |
| `RunPython` | `migration.operations` | Execute a Python callable |
