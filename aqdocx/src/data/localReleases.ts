export const localReleases: Record<string, Record<string, string>> = {
  "1.3.10": {
    "README.md": `# Aquilia v1.3.10 Release Notes — "Migration Rewrite"

Aquilia v1.3.10 is the most significant migration-subsystem release in the framework's history. Every file that made up the previous multi-layer, multi-authority migration stack (\`migration_dsl.py\`, \`migration_gen.py\`, \`migration_planner.py\`, \`migration_runner.py\`, \`migrations.py\`, \`schema_snapshot.py\`, \`ddl_executor.py\`) has been **replaced** by a single, coherent \`aquilia.models.migration\` sub-package — designed ground-up around immutable schema state, typed operations, dialect-aware SQL backends, a dependency-graph planner, and a transactional executor.

---

## Table of Contents

1. [Migration Engine Architecture](migration_engine.md)
   - \`aquilia.models.migration\` sub-package layout
   - \`MigrationEngine\` — the unified public entry point
   - \`ProjectState\` — immutable, field-fidelity schema state
   - \`MigrationGraph\` / \`MigrationNode\` — dependency-aware DAG ordering
   - \`MigrationExecutor\` — transactional application with checksum verification
   - \`Autodetector\` — deterministic, safe rename detection
   - \`Optimizer\` — operation folding before file write
   - \`SchemaBackend\` — dialect isolation layer
   - \`Serializer\` / \`Codegen\` — real Python constructor files
2. [Operations Reference](operations.md)
   - Full typed operation catalogue
   - State-forwards / state-backwards protocol
   - Backend compilation contract
3. [CLI Changes](cli.md)
   - \`aq db makemigrations\` — new flags (\`--slug\`, \`--dry-run\`), removed flags
   - \`aq db migrate\` — \`MigrationEngine\` integration, diagnostics output
   - \`aq db showmigrations\` — updated executor/serializer path
   - \`aq db diff\` — operation-based diff output
   - \`aq db reset\` — tracking-table aware reset
4. [Field Improvements](fields.md)
   - \`EnumField\` — dotted-string \`enum_class\` for migration round-trips
   - \`BigAutoField\` / \`SmallAutoField\` — MySQL \`BIGINT\`/\`SMALLINT\`
   - \`GeneratedField\` — \`deconstruct()\` for snapshotting
   - \`compile_schema_expression()\` — moved from \`schema_snapshot\` to \`expression\`
5. [Breaking Changes & Migration Guide](migration.md)
   - Removed symbols
   - Import path changes
   - Snapshot format upgrade
   - Upgrade checklist
6. [Bug Fixes](bugfixes.md)
   - \`_patched_create_tables_new\` optional \`db\` parameter
   - \`startup_guard\` probe function renames
   - \`ModelRegistry.create_tables\` unified DDL path
7. [Architecture Deep Dive](architecture.md)
   - Design rationale
   - Determinism guarantees
   - Atomicity model
   - Backward compatibility layers

---

## Highlights

### 1. One Package, One Authority

Six modules (\`migration_dsl\`, \`migration_gen\`, \`migration_planner\`, \`migration_runner\`, \`migrations\`, \`schema_snapshot\`, \`ddl_executor\`) are replaced by one sub-package:

\`\`\`
aquilia/models/migration/
├── __init__.py        public API
├── schema.py          ProjectState, TableState, ColumnState, ...
├── operations/        typed, backend-independent operations
├── backends/          SQLite, PostgreSQL, MySQL, Oracle DDL
├── autodetect.py      state-to-state diffing
├── graph.py           MigrationGraph, MigrationNode (dependency DAG)
├── optimizer.py       operation reduction
├── codegen.py         Python source rendering
├── serializer.py      file writing / loading
├── executor.py        transactional application
├── probe.py           pre-connection readiness probes
└── engine.py          MigrationEngine — public entry point
\`\`\`

### 2. \`MigrationEngine\` — Single Public Entry Point

\`\`\`python
from aquilia.models.migration import MigrationEngine

engine = MigrationEngine("migrations")

# Generate a migration from model changes
path = engine.make_migrations([User, Post], slug="add_bio")

# Apply pending migrations
results = await engine.migrate(db)

# Check status
status = await engine.status(db)
print(status.describe())

# Roll back to a specific revision
await engine.migrate(db, target="20260720_120000")

# Dry-run: inspect SQL without applying
statements = await engine.plan(db)
for stmt in statements:
    print(stmt.sql)
\`\`\`

### 3. Field-Fidelity Schema State

\`ProjectState\` is built directly from live \`Field.deconstruct()\` output — not from reduced primitive mappings. Generated-column expressions, M2M relationships, index access methods, operator classes, partial predicates, and all other model semantics survive the snapshot round-trip intact.

### 4. Deterministic, Reproducible Migrations

Every collection in the pipeline is an ordered \`tuple\`; every mapping is iterated through \`sorted()\` at construction time. Two runs of \`makemigrations\` against the same models — in different processes, with different \`PYTHONHASHSEED\` values — produce byte-identical migration files.

### 5. Real Python Constructor Files

Generated migration files use the same \`Field\`, index, and constraint classes a developer writes in models — not serialized dictionaries. A reviewer sees exactly the schema they declared:

\`\`\`python
# migrations/20260801_103000_add_post.py
from aquilia.models.migration import CreateModel, Operation, ProjectState
from aquilia.models.migration.schema import ColumnState, TableState
from aquilia.models import fields

dependencies: tuple[str, ...] = ("20260730_120000",)

operations: list[Operation] = [
    CreateModel(
        model="Post",
        table=TableState.of(
            "Post",
            "posts",
            columns=[
                ColumnState.of("id", fields.AutoField(primary_key=True)),
                ColumnState.of("title", fields.CharField(max_length=200)),
                ColumnState.of("author_id", fields.ForeignKey("User", on_delete="CASCADE")),
            ],
        ),
    ),
]
\`\`\`

### 6. Operation Optimizer

The autodetector emits a faithful but verbose diff. Before the migration is written, the optimizer folds redundant operations:

\`\`\`
CreateModel(User) + AddField(User.bio)    → CreateModel(User with bio)
AddField(x) + RemoveField(x)             → nothing
AddField(x) + AlterField(x)              → AddField with final definition
CreateModel(User) + DeleteModel(User)    → nothing
\`\`\`

### 7. Checksum Tamper Detection

Every applied migration records the SHA-256 digest of its source file. \`engine.verify_checksums(db)\` reports any migration whose file has been modified since application — enabling post-deployment integrity audits.

---

## Summary of Subsystem Changes

| Component | Status | Summary |
|---|---|---|
| \`aquilia.models.migration\` | **New** | Unified migration sub-package; public API entry point |
| \`aquilia.models.migration.engine\` | **New** | \`MigrationEngine\` — single entry point for generate/apply/rollback |
| \`aquilia.models.migration.schema\` | **New** | \`ProjectState\`, \`TableState\`, \`ColumnState\`, field-fidelity state |
| \`aquilia.models.migration.operations\` | **New** | Typed, backend-independent operations with state/database separation |
| \`aquilia.models.migration.backends\` | **New** | \`SchemaBackend\` dialect isolation (SQLite, PostgreSQL, MySQL, Oracle) |
| \`aquilia.models.migration.autodetect\` | **New** | Deterministic state diffing; safe rename inference with confidence scoring |
| \`aquilia.models.migration.graph\` | **New** | \`MigrationGraph\`/\`MigrationNode\` dependency DAG with topological ordering |
| \`aquilia.models.migration.optimizer\` | **New** | Operation reduction before file write |
| \`aquilia.models.migration.codegen\` | **New** | Python source rendering (real constructors, not dicts) |
| \`aquilia.models.migration.serializer\` | **New** | File writing/loading; \`MIGRATION_TEMPLATE_VERSION = 3\` |
| \`aquilia.models.migration.executor\` | **New** | Transactional application; checksum recording; MySQL/Oracle warnings |
| \`aquilia.models.migration.probe\` | **New** | Read-only pre-connection SQLite readiness probes |
| \`aquilia.models.ddl_executor\` | **Removed** | Replaced by \`migration.executor\` + \`migration.backends\` |
| \`aquilia.models.migration_dsl\` | **Removed** | Replaced by \`migration.operations\` |
| \`aquilia.models.migration_gen\` | **Removed** | Replaced by \`migration.codegen\` + \`migration.serializer\` |
| \`aquilia.models.migration_planner\` | **Removed** | Replaced by \`migration.graph\` + \`migration.engine\` |
| \`aquilia.models.migration_runner\` | **Removed** | Replaced by \`migration.executor\` + \`migration.engine\` |
| \`aquilia.models.migrations\` | **Removed** | Replaced by \`migration.engine\` |
| \`aquilia.models.schema_snapshot\` | **Removed** | Replaced by \`migration.schema\` + \`migration.autodetect\` |
| \`aquilia.models.fields.enum_field\` | **Improved** | Dotted-string \`enum_class\` for migration round-trips; \`_resolve_enum_class()\` |
| \`aquilia.models.fields_module\` | **Improved** | \`BigAutoField\`/\`SmallAutoField\` MySQL types; \`GeneratedField.deconstruct()\` |
| \`aquilia.models.expression\` | **Improved** | \`compile_schema_expression()\` moved here from \`schema_snapshot\` |
| \`aquilia.models.registry\` | **Improved** | \`create_tables()\` uses \`ProjectState\` + \`MigrationExecutor\` |
| \`aquilia.models.startup_guard\` | **Updated** | Uses \`migration.probe.database_exists/migrations_applied\` |
| \`aquilia.server\` | **Updated** | Uses \`MigrationEngine\` for auto-migrate |
| \`aquilia.__init__\` | **Updated** | Exports \`MigrationEngine\` instead of \`MigrationRunner\`/\`MigrationOps\` |
`,
    "migration_engine.md": `# Migration Engine Architecture — Aquilia v1.3.10

Aquilia v1.3.10 replaces all previous migration modules with a single, coherent \`aquilia.models.migration\` sub-package. This document describes every layer, its responsibilities, design rationale, and public API.

---

## Package Layout

\`\`\`
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
\`\`\`

---

## \`MigrationEngine\` — Single Entry Point

\`MigrationEngine\` is the single class the CLI, the server startup path, and application code all interact with. It delegates to every other layer and owns no SQL itself.

\`\`\`python
from aquilia.models.migration import MigrationEngine

engine = MigrationEngine("migrations")   # dir that holds .py files + snapshot
\`\`\`

### \`make_migrations(model_classes, *, slug, hints, infer_renames, dry_run) → Path | None\`

Generates a migration for the difference between the on-disk snapshot and the given models.

**Process:**
1. Loads the last recorded \`ProjectState\` from \`schema_snapshot.json\`
2. Builds a new \`ProjectState\` from the live model classes
3. Runs the \`Autodetector\` to compute a raw operation list
4. Passes operations through the \`Optimizer\` to collapse redundancy
5. Allocates a timestamp revision, stepping past collisions
6. Renders the migration with \`codegen\` + \`serializer\` as a real Python file
7. Writes the migration file **first**, then saves the updated snapshot

**Why file before snapshot?** If the write fails, the snapshot still describes the last successful migration and the change can simply be regenerated. Writing the snapshot first would advance it past a migration that was never recorded on disk — the next \`makemigrations\` would then see no diff.

\`\`\`python
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
\`\`\`

### \`async migrate(db, *, target, fake) → list[ExecutionResult]\`

Applies pending migrations forward, or rolls back to \`target\`.

\`\`\`python
# Apply all pending migrations
results = await engine.migrate(db)
for r in results:
    print(r.statements_executed, r.duration_ms)

# Roll back to a specific revision
await engine.migrate(db, target="20260720_120000")

# Fake: record migrations without executing DDL
await engine.migrate(db, fake=True)
\`\`\`

### \`async status(db) → MigrationStatus\`

Reports which migrations are applied and which are pending.

\`\`\`python
status = await engine.status(db)
print(status.describe())
# Applied: 4
# Pending: 1
#   - 20260801_103000_add_bio
# Last applied: 20260730_120000
\`\`\`

\`MigrationStatus\` attributes:
- \`applied: tuple[str, ...]\` — revisions applied, in application order
- \`pending: tuple[MigrationNode, ...]\` — pending nodes, in dependency order
- \`leaves: tuple[str, ...]\` — tips of the graph (> 1 = branched history)
- \`is_current: bool\` — True when nothing is pending

### \`async plan(db, *, target) → list[Statement]\`

Compiles pending migrations to SQL without executing anything. Useful for code review and deployment pipelines.

\`\`\`python
statements = await engine.plan(db)
for stmt in statements:
    if stmt.destructive:
        print(f"DESTRUCTIVE: {stmt.description}")
    print(stmt.sql)
\`\`\`

### \`async verify_checksums(db) → list[dict]\`

Reports applied migrations whose source files have changed since they were applied.

\`\`\`python
mismatches = await engine.verify_checksums(db)
for m in mismatches:
    print(m["revision"], m["reason"])
\`\`\`

### \`state_at(revision) → ProjectState\`

Replays migrations from disk up to and including \`revision\`, reconstructing the schema state without touching the database.

### \`state_for(applied) → ProjectState\`

Reconstructs the state produced by exactly the given set of applied revisions — the right method when applied and on-disk don't form a linear prefix.

---

## \`ProjectState\` — Immutable Schema State

\`ProjectState\` is a fully-typed, immutable description of a database schema. It preserves model semantics — generated-column expressions, M2M relationships, index methods, partial-index predicates, composite PKs — rather than reducing them to primitive column definitions.

### Design Rationale

Reducing every \`Field\` to a handful of primitives (name, SQL type, a few booleans) destroys information at the very first hop. Nothing downstream can recover a generated-column expression or an operator class from a primitive snapshot. \`ProjectState\` therefore captures fields through \`Field.deconstruct()\`, retaining enough to reconstruct them faithfully.

### Construction

\`\`\`python
from aquilia.models.migration.schema import ProjectState

# From live model classes
state = ProjectState.from_models([User, Post, Comment])

# From a serialised dict (snapshot file)
state = ProjectState.from_dict(raw_dict)

# Empty state (before any migrations)
state = ProjectState()
\`\`\`

### Key State Objects

| Class | Description |
|---|---|
| \`ProjectState\` | Top-level container; \`tables: dict[str, TableState]\` |
| \`TableState\` | One table; columns, indexes, constraints, M2M relations, db_table, ordering |
| \`ColumnState\` | One column; field class + deconstruct kwargs + reference |
| \`IndexState\` | One index; columns, method, unique, condition, include columns |
| \`ConstraintState\` | Base for check, unique, exclusion, FK, PK constraint states |
| \`ManyToManyState\` | M2M junction table descriptor |
| \`Reference\` | A (table, column) pair used for FK wiring |

### \`creation_order() → list[str]\`

Returns table names topologically sorted so that referenced tables appear before their dependents — the order in which \`CREATE TABLE\` statements must run.

\`\`\`python
state = ProjectState.from_models([Post, User, Comment])
order = state.creation_order()
# ['User', 'Post', 'Comment']  — User before Post (FK), Post before Comment (FK)
\`\`\`

### \`from_database(db, model_classes) → ProjectState\`

Introspects a live database to reconstruct its current state. Used by \`aq db diff\`.

---

## \`MigrationGraph\` and \`MigrationNode\` — Dependency DAG

Every migration file on disk becomes a \`MigrationNode\` in a \`MigrationGraph\`. The graph provides topological ordering, conflict detection, forward and backward planning, and leaf discovery.

### \`MigrationNode\`

\`\`\`python
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
\`\`\`

### Design: Why a Graph Matters

An earlier design had \`dependencies\` in every generated file but never read them — ordering came from sorting filenames. That works only while every migration is generated on one machine in one linear sequence. Two developers generating a migration on the same day produce filenames that sort by timestamp into an order neither intended. A graph reads the declared dependencies and plans correctly regardless.

### \`MigrationGraph.forward_plan(applied) → tuple[MigrationNode, ...]\`

Returns pending nodes in the order they must be applied, respecting all declared dependencies.

### \`MigrationGraph.backward_plan(applied, target) → tuple[MigrationNode, ...]\`

Returns the nodes to roll back (in reverse dependency order) to reach \`target\`.

### \`MigrationGraph.check_conflicts()\`

Raises \`MigrationConflictFault\` if two migrations share a revision or if two leaf nodes share no common ancestor — i.e. the history has forked without a merge migration.

### Squash Support

A node with \`replaces = ("20260701_120000", "20260710_150000")\` is treated as already applied when every listed revision is in the applied set. This is how squashing is safe on a deployed database: the squash migration records itself as done without re-running DDL that is already in the schema.

---

## \`Autodetector\` — Deterministic, Safe Diffing

The autodetector compares two \`ProjectState\` objects and emits the operations needed to transform one into the other.

### Determinism

Every collection is iterated in sorted order; results are ordered by explicit rules, never by set iteration. Two runs over the same states — in different processes with different \`PYTHONHASHSEED\` — produce identical operation lists. This is not an accident: iterating a \`set\` anywhere in the diff path makes the migration order change on every interpreter run.

### Rename Detection

A rename is a destructive guess. Emitting \`RENAME COLUMN\` when the developer actually dropped one column and added another silently rewrites the wrong column and loses its data. Rename is therefore inferred only from:

1. An explicit \`RenameHint\` from the developer.
2. A combined confidence score across multiple signals (\`RENAME_CONFIDENCE_THRESHOLD = 0.85\`). No single signal — not even an identical type — clears this threshold alone.

\`\`\`python
from aquilia.models.migration import RenameHint, detect_changes

# Explicit rename instruction
hint = RenameHint(model="User", old_name="bio", new_name="biography")
ops = detect_changes(before, after, hints=(hint,))

# Disable inference entirely (safe for db introspection comparisons)
ops = detect_changes(live, target, infer_renames=False)
\`\`\`

---

## \`Optimizer\` — Operation Reduction

The optimizer collapses redundant operations before the migration is written:

| Input | Output |
|---|---|
| \`CreateModel(U)\` + \`AddField(U.bio)\` | \`CreateModel(U with bio)\` |
| \`AddField(U.bio)\` + \`RemoveField(U.bio)\` | *(nothing)* |
| \`AddField(U.bio)\` + \`AlterField(U.bio)\` | \`AddField\` with final definition |
| \`AlterField(x)\` + \`AlterField(x)\` | one \`AlterField\` |
| \`CreateModel(U)\` + \`DeleteModel(U)\` | *(nothing)* |

\`RunSQL\` and \`RunPython\` are treated as opaque barriers — a data migration may well depend on the exact intermediate schema, and merging across it would silently change what it sees.

---

## \`MigrationExecutor\` — Transactional Application

The executor applies and rolls back migrations against a live database.

### Atomicity

Two atomicity hazards are handled:

1. **History recorded outside the transaction** — the tracking \`INSERT\` is the last statement *inside* the same transaction, so schema and history commit or roll back together.
2. **Non-transactional statements silently mixed in** — statements declare their own transactional requirement. SQLite table rebuilds need \`PRAGMA foreign_keys\` outside any transaction; PostgreSQL rejects \`CREATE INDEX CONCURRENTLY\` inside one. The executor splits accordingly.

On MySQL and Oracle, DDL cannot participate in a transaction at all. The executor detects this from the backend's capability flags and warns rather than promising atomicity it cannot deliver.

### \`apply(node, state, fake) → ExecutionResult\`

Applies one \`MigrationNode\` forward. When \`fake=True\`, records the migration without executing any DDL.

### \`rollback(node, state, fake) → ExecutionResult\`

Rolls back one \`MigrationNode\`. Requires every operation to implement \`state_backwards\` and \`database_backwards\`.

### \`ExecutionResult\`

\`\`\`python
@dataclass
class ExecutionResult:
    statements_executed: int
    statements_skipped: int
    duration_ms: float
    diagnostics: list[str]
\`\`\`

---

## \`SchemaBackend\` — Dialect Isolation

\`backends/\` is the **only** layer that knows about SQL dialects. Nothing in \`schema.py\`, \`operations/\`, or \`engine.py\` imports a backend.

\`\`\`python
from aquilia.models.migration.backends import get_backend, SchemaBackend

backend = get_backend("postgresql")
stmt = backend.create_table(table_state)
print(stmt.sql)
\`\`\`

Four backends ship: \`sqlite\`, \`postgresql\`, \`mysql\`, \`oracle\`.

\`Statement\` carries:
- \`sql: str\` — the SQL text
- \`description: str\` — human-readable description for \`aq db migrate --plan\`
- \`destructive: bool\` — whether it could cause data loss
- \`transactional: bool\` — whether it must run inside a transaction

---

## \`Codegen\` and \`Serializer\` — Real Python Constructor Files

The generated migration file uses the same \`Field\`, index, and constraint classes the developer writes in models — not serialized dictionaries.

### Why Not Dicts?

A dict-serialized migration is unreadable and uneditable. No editor completes a dict key, no type checker catches a misspelled one, and a reviewer cannot see whether a column is nullable. A migration is a permanent, reviewable artifact — often the only record of *why* a schema looks the way it does — and it should be written in the same vocabulary as the models it came from.

### \`MIGRATION_TEMPLATE_VERSION = 3\`

Bumped to 3 when generated files moved to real constructor calls. Both old and new formats load correctly — the version is informational.

### Generated File Format

\`\`\`python
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
\`\`\`

---

## \`Probe\` — Read-Only Readiness Checks

The probe module answers "is this database ready?" **before** the application opens a connection.

### Why Not Just Connect?

Opening a SQLite database creates its \`-wal\` and \`-shm\` sidecar files — even when the connection is immediately closed. A startup check that does this has changed the thing it was checking: a developer who ran a check against a non-existent database now has one that half-exists. Probes open SQLite read-only (\`mode=ro\`), which never creates a file and never writes a journal.

For non-SQLite backends the probe reports "ready" and lets the normal connection path surface any error. A false "not ready" would block a working deployment; a false "ready" costs only the error the application raises anyway.

\`\`\`python
from aquilia.models.migration.probe import database_exists, migrations_applied

if not database_exists("sqlite:///app.db"):
    print("Run: aq db migrate")

if not migrations_applied("sqlite:///app.db", "migrations"):
    print("Pending migrations — run: aq db migrate")
\`\`\`

---

## API Reference Summary

| Symbol | Module | Description |
|---|---|---|
| \`MigrationEngine\` | \`migration.engine\` | Generate, plan, apply, roll back |
| \`MigrationStatus\` | \`migration.engine\` | Applied / pending summary |
| \`SNAPSHOT_FILENAME\` | \`migration.engine\` | \`"schema_snapshot.json"\` |
| \`ProjectState\` | \`migration.schema\` | Immutable schema state |
| \`TableState\` | \`migration.schema\` | Per-table state |
| \`ColumnState\` | \`migration.schema\` | Per-column state |
| \`IndexState\` | \`migration.schema\` | Per-index state |
| \`MigrationGraph\` | \`migration.graph\` | Dependency DAG |
| \`MigrationNode\` | \`migration.graph\` | One migration in the DAG |
| \`Autodetector\` | \`migration.autodetect\` | State-to-state diffing |
| \`RenameHint\` | \`migration.autodetect\` | Explicit rename instruction |
| \`detect_changes\` | \`migration.autodetect\` | Convenience function |
| \`optimize\` | \`migration.optimizer\` | Operation reduction |
| \`SchemaBackend\` | \`migration.backends\` | Dialect backend ABC |
| \`Statement\` | \`migration.backends\` | Compiled SQL statement |
| \`get_backend\` | \`migration.backends\` | Backend factory |
| \`MigrationExecutor\` | \`migration.executor\` | Transactional application |
| \`ExecutionResult\` | \`migration.executor\` | Per-migration outcome |
| \`AppliedMigration\` | \`migration.executor\` | One tracking-table row |
| \`MIGRATION_TABLE\` | \`migration.executor\` | \`"aquilia_migrations"\` |
| \`compile_operations\` | \`migration.executor\` | Operations → statements |
| \`render_migration_module\` | \`migration.serializer\` | MigrationNode → Python source |
| \`load_migration_module\` | \`migration.serializer\` | Python file → MigrationNode |
| \`serialize_operations\` | \`migration.serializer\` | Operations → source fragment |
| \`revision_from_path\` | \`migration.serializer\` | Extract revision from filename |
| \`slug_from_path\` | \`migration.serializer\` | Extract slug from filename |
| \`database_exists\` | \`migration.probe\` | SQLite existence check |
| \`migrations_applied\` | \`migration.probe\` | Pending-migration check |
| \`Operation\` | \`migration.operations\` | Base operation ABC |
| \`CreateModel\` | \`migration.operations\` | Create a new model/table |
| \`DeleteModel\` | \`migration.operations\` | Drop a model/table |
| \`RenameModel\` | \`migration.operations\` | Rename a model/table |
| \`AlterModelOptions\` | \`migration.operations\` | Change \`Meta\` options |
| \`AddField\` | \`migration.operations\` | Add a column |
| \`RemoveField\` | \`migration.operations\` | Remove a column |
| \`AlterField\` | \`migration.operations\` | Change a column's definition |
| \`RenameField\` | \`migration.operations\` | Rename a column |
| \`AddIndex\` | \`migration.operations\` | Add an index |
| \`RemoveIndex\` | \`migration.operations\` | Remove an index |
| \`AlterIndex\` | \`migration.operations\` | Modify an index |
| \`AddConstraint\` | \`migration.operations\` | Add a table constraint |
| \`RemoveConstraint\` | \`migration.operations\` | Remove a table constraint |
| \`AlterConstraint\` | \`migration.operations\` | Modify a constraint |
| \`CreateManyToManyTable\` | \`migration.operations\` | Create M2M junction table |
| \`DeleteManyToManyTable\` | \`migration.operations\` | Drop M2M junction table |
| \`RunSQL\` | \`migration.operations\` | Execute raw SQL |
| \`RunPython\` | \`migration.operations\` | Execute a Python callable |
`,
    "operations.md": `# Operations Reference — Aquilia v1.3.10

Every change to a database schema is represented as a typed \`Operation\` object. Operations are backend-independent: they carry semantic intent (e.g. "add a column called \`bio\` to \`User\`"), and a \`SchemaBackend\` turns that intent into SQL at execution time.

---

## Operation Protocol

Every \`Operation\` subclass implements:

| Method | Description |
|---|---|
| \`state_forwards(state)\` | Update \`ProjectState\` as if the operation has been applied. Used to replay history without touching the database. |
| \`state_backwards(state)\` | Update \`ProjectState\` as if the operation has been rolled back. |
| \`database_forwards(executor, state)\` | Apply the operation to a live database. |
| \`database_backwards(executor, state)\` | Roll back the operation from a live database. |
| \`describe() → str\` | Human-readable one-line summary shown in \`aq db makemigrations\` output. |
| \`atomic: bool\` | Whether the operation requires a transaction. |

### \`OperationCategory\`

\`\`\`python
class OperationCategory(str, Enum):
    DDL = "ddl"           # Table/column/index changes
    DATA = "data"         # RunSQL, RunPython with data changes
    MIXED = "mixed"       # Operations that combine DDL and data
\`\`\`

---

## Model Operations

### \`CreateModel\`

Create a new table and all its indexes, constraints, and M2M junction tables.

\`\`\`python
CreateModel(
    model="Post",
    table=TableState.of(
        "Post",
        "posts",
        columns=[
            ColumnState.of("id", fields.AutoField(primary_key=True)),
            ColumnState.of("title", fields.CharField(max_length=200)),
            ColumnState.of("author_id", fields.ForeignKey("User", on_delete="CASCADE")),
        ],
        indexes=[
            IndexState(name="idx_post_author", columns=("author_id",)),
        ],
    ),
)
\`\`\`

**State forward:** Adds \`model\` to \`ProjectState.tables\`.
**State backward:** Removes \`model\` from \`ProjectState.tables\`.

### \`DeleteModel\`

Drop a table and all its indexes, constraints, and M2M junction tables.

\`\`\`python
DeleteModel(model="Post")
\`\`\`

**Irreversible** unless a corresponding \`CreateModel\` is in the rollback plan.

### \`RenameModel\`

Rename a model and its underlying table.

\`\`\`python
RenameModel(model="OldName", new_model="NewName")
\`\`\`

### \`AlterModelOptions\`

Change \`Meta\` options without touching columns (e.g. \`ordering\`, \`verbose_name\`).

\`\`\`python
AlterModelOptions(model="Post", options={"ordering": ["-created_at"]})
\`\`\`

---

## Field Operations

### \`AddField\`

Add a column to an existing table.

\`\`\`python
AddField(
    model="User",
    field=ColumnState.of("bio", fields.TextField(null=True, blank=True)),
)
\`\`\`

**Reversible** via \`RemoveField\`.

### \`RemoveField\`

Remove a column from an existing table.

\`\`\`python
RemoveField(model="User", field_name="bio")
\`\`\`

> [!WARNING]
> Irreversible in the sense that the data is deleted. The operation itself can generate \`ALTER TABLE ... DROP COLUMN\`.

### \`AlterField\`

Change a column's type, constraints, or default.

\`\`\`python
AlterField(
    model="User",
    field_name="bio",
    field=ColumnState.of("bio", fields.CharField(max_length=500)),
)
\`\`\`

**Compatibility note:** Narrowing a type (e.g. \`TextField\` → \`CharField(max_length=100)\`) may truncate data. The backend marks such statements as \`destructive=True\`.

### \`RenameField\`

Rename a column.

\`\`\`python
RenameField(model="User", old_name="bio", new_name="biography")
\`\`\`

---

## Index Operations

### \`AddIndex\`

\`\`\`python
AddIndex(
    model="Post",
    index=IndexState(
        name="idx_post_title",
        columns=("title",),
        unique=False,
    ),
)
\`\`\`

### \`RemoveIndex\`

\`\`\`python
RemoveIndex(model="Post", index_name="idx_post_title")
\`\`\`

### \`AlterIndex\`

Replace an existing index definition (drop + recreate).

\`\`\`python
AlterIndex(
    model="Post",
    old_index=IndexState(name="idx_post_title", columns=("title",)),
    new_index=IndexState(name="idx_post_title", columns=("title",), unique=True),
)
\`\`\`

---

## Constraint Operations

### \`AddConstraint\`

\`\`\`python
from aquilia.models.migration.schema import CheckConstraintState

AddConstraint(
    model="Post",
    constraint=CheckConstraintState(
        name="chk_post_title_nonempty",
        condition="length(title) > 0",
    ),
)
\`\`\`

### \`RemoveConstraint\`

\`\`\`python
RemoveConstraint(model="Post", constraint_name="chk_post_title_nonempty")
\`\`\`

### \`AlterConstraint\`

Drop and recreate a constraint with a new definition.

---

## Relation Operations

### \`CreateManyToManyTable\`

Create the junction table for a \`ManyToManyField\`. Emitted automatically by \`CreateModel\` when the model declares M2M fields; also emitted standalone when a M2M field is added to an existing model.

\`\`\`python
CreateManyToManyTable(
    model="Post",
    relation=ManyToManyState(
        field_name="tags",
        through_table="post_tags",
        source_column="post_id",
        target_column="tag_id",
        target_table="tags",
    ),
)
\`\`\`

### \`DeleteManyToManyTable\`

Drop a M2M junction table.

---

## Special Operations

### \`RunSQL\`

Execute raw SQL forward and (optionally) backward.

\`\`\`python
RunSQL(
    sql="UPDATE posts SET published = TRUE WHERE created_at < '2026-01-01'",
    reverse_sql="UPDATE posts SET published = FALSE WHERE created_at < '2026-01-01'",
    atomic=True,
)
\`\`\`

> [!IMPORTANT]
> \`RunSQL\` and \`RunPython\` act as **optimizer barriers** — the optimizer never merges operations across them, since a data migration may depend on the exact intermediate schema.

### \`RunPython\`

Execute a Python callable.

\`\`\`python
def backfill_slugs(executor, state):
    """Populate slug from title for existing posts."""
    # Access the database through executor
    ...

RunPython(
    code=backfill_slugs,
    reverse_code=None,   # irreversible data migration
    atomic=True,
)
\`\`\`

---

## Custom Operations

Register a custom operation class so the serializer can find it by name when loading generated files:

\`\`\`python
from aquilia.models.migration.operations import register_operation, Operation

class PartitionTable(Operation):
    def __init__(self, model: str, partition_key: str):
        self.model = model
        self.partition_key = partition_key

    def state_forwards(self, state): ...
    def state_backwards(self, state): ...
    def database_forwards(self, executor, state): ...
    def database_backwards(self, executor, state): ...
    def describe(self): return f"Partition {self.model} by {self.partition_key}"

register_operation(PartitionTable)
\`\`\`

\`resolve_operation("PartitionTable")\` will then return the class when loading a migration that uses it.

---

## Operation Interactions with the Optimizer

The optimizer folds operations in multiple passes until no further reduction is possible (capped at \`MAX_OPTIMIZER_PASSES = 32\`):

| Rule | Input | Output |
|---|---|---|
| Fold field into create | \`CreateModel(U)\` + \`AddField(U.x)\` | \`CreateModel(U with x)\` |
| Cancel field add/remove | \`AddField(U.x)\` + \`RemoveField(U.x)\` | *(nothing)* |
| Collapse field alter | \`AddField(U.x)\` + \`AlterField(U.x)\` | \`AddField\` with final definition |
| Collapse double alter | \`AlterField(x)\` + \`AlterField(x)\` | one \`AlterField\` |
| Cancel model create/delete | \`CreateModel(U)\` + \`DeleteModel(U)\` | *(nothing)* |
| Absorb rename into add | \`AddField(U.x)\` + \`RenameField(x→y)\` | \`AddField(U.y)\` |
| Merge option changes | \`AlterModelOptions(a)\` + \`AlterModelOptions(b)\` | one \`AlterModelOptions\` with merged options |
| Collapse index add/remove | \`AddIndex(i)\` + \`RemoveIndex(i)\` | *(nothing)* |
`,
    "cli.md": `# CLI Changes — Aquilia v1.3.10

The migration-related \`aq db\` commands have been updated to use \`MigrationEngine\` throughout. Legacy \`MigrationRunner\`, \`DSLMigrationRunner\`, and \`generate_dsl_migration\` paths are removed from the CLI layer.

---

## \`aq db makemigrations\`

### Removed Flags

| Flag | Previous behaviour | Status |
|---|---|---|
| \`--use-dsl\` / \`--no-use-dsl\` | Toggle between DSL and legacy raw-SQL generator | **Removed** |
| \`--migration-format\` | Choose \`"json"\` or \`"python"\` output format | **Removed** |

### New Flags

| Flag | Description | Default |
|---|---|---|
| \`--slug TEXT\` | Human-readable suffix appended to the filename | Derived from affected models |
| \`--dry-run\` | Compute and print the migration without writing any files | \`False\` |

### New Behaviour

- The generated migration always uses the new sub-package format (real Python constructors, \`MIGRATION_TEMPLATE_VERSION = 3\`).
- The snapshot file is now always written alongside the migration at \`<migrations_dir>/schema_snapshot.json\`.
- \`--dry-run\` prints what would be generated (including the operation list) without touching the filesystem.

### Examples

\`\`\`bash
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
\`\`\`

### Before / After Comparison

\`\`\`bash
# v1.3.9 (old flags)
aq db makemigrations --use-dsl --migration-format python

# v1.3.10 (removed — equivalent is just)
aq db makemigrations
\`\`\`

---

## \`aq db migrate\`

### Changes

The CLI now drives \`MigrationEngine\` instead of the old \`MigrationRunner\`:

- \`--plan\` output now shows \`Statement.description\` and marks destructive statements in red:
  \`\`\`
  -- DESTRUCTIVE: Drop column 'legacy_id' from 'users'
  ALTER TABLE "users" DROP COLUMN "legacy_id";
  \`\`\`
- \`--verbose\` now emits per-migration \`ExecutionResult.diagnostics\`.
- The return value is now built from \`engine.status(db).applied\` — a complete, ordered list of all applied revisions — rather than just the revisions applied in the current run.

### Examples

\`\`\`bash
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
\`\`\`

---

## \`aq db showmigrations\`

### Changes

Updated to use \`MigrationExecutor\` and \`revision_from_path\` from the new sub-package:

\`\`\`python
# Internal change (not visible to users)
# Old: from aquilia.models.migration_runner import MigrationRunner
# New:
from aquilia.models.migration.executor import MigrationExecutor
from aquilia.models.migration.serializer import revision_from_path
\`\`\`

Output format and flags are unchanged.

### Example

\`\`\`bash
aq db showmigrations
# [x] 20260701_120000_initial
# [x] 20260730_120000_add_user
# [ ] 20260801_103000_add_bio      ← pending
\`\`\`

---

## \`aq db diff\`

### Changes

The \`diff\` command now uses \`detect_changes\` from \`migration.autodetect\` and \`ProjectState.from_database\` instead of the old snapshot-diffing machinery from \`schema_snapshot\`.

**New output format:** Instead of a \`difflib\` unified-diff text block, \`diff\` now prints one line per operation:

\`\`\`
Drift detected -- 2 change(s) needed:

--- database (active)
+++ schema (target)

  + AddField: Add 'biography' (TextField) to 'User'
  + CreateIndex: Create index 'idx_user_biography' on 'User'

Run \`aq db makemigrations\` to record these changes as a migration.
\`\`\`

The old format printed raw SQL fragments; the new format prints semantic operation descriptions.

### Rename inference off by default for \`diff\`

When comparing a live database against the snapshot, rename inference is disabled (\`infer_renames=False\`). A rename is indistinguishable from a drop-plus-add when one side was introspected; guessing wrong would report data-preserving drift as destructive.

### Examples

\`\`\`bash
# Compare live database against the snapshot
aq db diff

# Compare live database against model definitions
aq db diff --compare models

# Specify migrations directory
aq db diff --migrations-dir src/migrations
\`\`\`

---

## \`aq db reset\`

### Changes

The reset command now correctly handles the case where the tracking table survived the drop:

\`\`\`python
# v1.3.10: After dropping tables, clear the tracking table if it still exists
# before re-applying migrations — otherwise migrate() sees nothing pending.
engine = MigrationEngine(migrations_dir)
remaining = await db.get_tables()
if "aquilia_migrations" in remaining:
    await db.execute('DELETE FROM "aquilia_migrations"')
results = await engine.migrate(db)
\`\`\`

This fixes a bug where \`reset\` on certain dialects (MySQL, some PostgreSQL configurations) could leave the tracking table intact after a drop, causing \`migrate()\` to report "Nothing to do" on a completely empty database.

### Example

\`\`\`bash
aq db reset --database-url sqlite:///dev.db
\`\`\`

---

## \`aq db status\`

No changes to the CLI interface. The underlying \`MigrationStatus\` object is now returned by \`MigrationEngine.status()\`.

---

## Common Migration Workflow

\`\`\`bash
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
\`\`\`

---

## Anti-Patterns

\`\`\`bash
# ❌ Don't edit migration files after applying them to any environment.
# The checksum recorded in aquilia_migrations will no longer match,
# and verify_checksums will report a mismatch.

# ❌ Don't delete migration files that have been applied.
# The engine will report the revision as "missing from disk".

# ✅ To squash migrations, use the replaces metadata:
#    Set node.replaces = ("old_rev_1", "old_rev_2") in your squash migration.
\`\`\`
`,
    "fields.md": `# Field Improvements — Aquilia v1.3.10

---

## \`EnumField\` — Dotted-String \`enum_class\` for Migration Round-Trips

### Problem

Generated migration files must be valid Python that can be imported by the migration executor. An \`EnumField\` declaration requires the actual \`Enum\` class to be present at import time. When \`EnumField.deconstruct()\` serializes the field for a migration file, it must write the class reference in a form that can be reconstructed.

### Solution: \`_resolve_enum_class()\`

\`EnumField\` now accepts a dotted-string path as \`enum_class\` in addition to the class itself:

\`\`\`python
# Both of these are now valid:
status = EnumField(enum_class=UserStatus)                      # direct class reference
status = EnumField(enum_class="myapp.models.UserStatus")       # dotted-string path
\`\`\`

The dotted-string form is what \`deconstruct()\` writes into generated migration files. At load time, \`_resolve_enum_class()\` imports the module and resolves the class.

### \`_resolve_enum_class()\` Behaviour

| Input | Result |
|---|---|
| \`UserStatus\` (an Enum subclass) | Returns \`UserStatus\` unchanged |
| \`"myapp.models.UserStatus"\` | Imports \`myapp.models\`, returns \`UserStatus\` |
| \`"UserStatus"\` (no module) | Raises \`FieldValidationError\` with clear message |
| \`"myapp.models.NotAnEnum"\` | Raises \`FieldValidationError\` after confirming it is not \`Enum\` |
| Import fails | Raises \`FieldValidationError\` with message including the original \`ImportError\` |

### Error Messages

The error message from \`_resolve_enum_class()\` includes the instruction to keep the enum importable:

\`\`\`
FieldValidationError: enum_class: cannot import 'myapp.models.OldStatus':
No module named 'myapp.models'. The enum must remain importable for any
migration referencing it to load.
\`\`\`

### Migration Round-Trip

\`\`\`python
# Model definition
class Post(Model):
    status = EnumField(enum_class=PostStatus)

# What deconstruct() produces (written to migration file)
{
    "enum_class": "myapp.models.PostStatus",
    "max_length": 50,
    ...
}

# When the migration file is loaded, _resolve_enum_class("myapp.models.PostStatus")
# imports the module and returns the PostStatus class.
\`\`\`

### Breaking Change

\`EnumField(enum_class=...)\` now validates the argument immediately at field construction time. Previously, passing an invalid \`enum_class\` would fail lazily (e.g. when accessing choices). This means invalid declarations fail loudly at import time instead of silently at runtime.

---

## \`BigAutoField\` — MySQL \`BIGINT\`

### Previous Behaviour

\`BigAutoField.sql_type("mysql")\` returned \`"INTEGER"\` (the SQLite fallback), which on MySQL is a 32-bit type — silently losing the 64-bit guarantee the field exists to provide.

### New Behaviour

\`\`\`python
BigAutoField().sql_type("mysql")    # → "BIGINT"
BigAutoField().sql_type("sqlite")   # → "INTEGER"  (unchanged — SQLite INTEGER is 64-bit)
BigAutoField().sql_type("postgresql")  # → "BIGSERIAL"  (unchanged)
BigAutoField().sql_type("oracle")   # → "NUMBER(19)"  (unchanged)
\`\`\`

**Why not \`BIGINT\` on SQLite?** Only the exact type string \`INTEGER\` aliases the 64-bit rowid on SQLite; \`BIGINT\` would silently lose the auto-increment behaviour.

---

## \`SmallAutoField\` — MySQL \`SMALLINT\`

Same fix as \`BigAutoField\`. \`SmallAutoField.sql_type("mysql")\` now returns \`"SMALLINT"\` instead of \`"INTEGER"\`.

\`\`\`python
SmallAutoField().sql_type("mysql")       # → "SMALLINT"
SmallAutoField().sql_type("sqlite")      # → "INTEGER"  (unchanged)
SmallAutoField().sql_type("postgresql")  # → "SMALLSERIAL"  (unchanged)
SmallAutoField().sql_type("oracle")      # → "NUMBER(5)"  (unchanged)
\`\`\`

---

## \`GeneratedField\` — \`deconstruct()\` for Snapshotting

### Problem

\`GeneratedField\` did not override \`deconstruct()\`. Without \`expression\`, \`db_persist\`, and \`output_field\` in the deconstructed dict, migration snapshotting was invisible to generated columns: a change to the expression would not be detected as a schema change, and the \`GENERATED ALWAYS AS (...)\` clause would be dropped from generated DDL entirely.

### Solution

\`GeneratedField\` now overrides \`deconstruct()\` to include:

\`\`\`python
{
    "expression": "UPPER(name)",   # the SQL expression
    "db_persist": True,            # STORED vs VIRTUAL
    "output_field": {              # nested deconstruct() of the output field
        "__class__": "CharField",
        "max_length": 200,
        ...
    },
    ...
}
\`\`\`

\`output_field\` is serialized as its own nested \`deconstruct()\` dict, keeping the result JSON-safe while still naming the concrete field class needed to resolve the column's SQL type.

### Before / After

\`\`\`python
# Before v1.3.10: GeneratedField.deconstruct() returned only base Field fields
# Changes to expression or db_persist were invisible to the migration system

# After v1.3.10:
class Article(Model):
    title = CharField(max_length=200)
    title_upper = GeneratedField(
        expression="UPPER(title)",
        output_field=CharField(max_length=200),
        db_persist=True,
    )

# Running makemigrations now correctly captures the generated column.
# Changing the expression produces an AlterField operation.
\`\`\`

---

## \`compile_schema_expression()\` — Moved to \`expression\` Module

### Change

The function \`_compile_schema_expression\` was previously defined in \`aquilia.models.schema_snapshot\` (now deleted). It has been reimplemented as the public function \`compile_schema_expression\` in \`aquilia.models.expression\`.

### New Import Path

\`\`\`python
# Old (no longer exists)
from aquilia.models.schema_snapshot import _compile_schema_expression

# New
from aquilia.models.expression import compile_schema_expression
\`\`\`

### What It Does

Renders a query-expression object (\`F\`, \`Value\`, \`Func\`, \`CombinedExpression\`, \`RawSQL\`, or any \`Expression\` with \`as_sql\`) as inline SQL text for use in schema artifacts (index/constraint DDL, snapshot diffing).

Unlike normal query compilation, this produces a single self-contained SQL string with parameters inlined (via naive \`'\` doubling) rather than a \`(sql, params)\` pair — appropriate for DDL contexts like \`CREATE INDEX ... (expression)\` where there is no query executor to bind parameters.

\`\`\`python
from aquilia.models.expression import compile_schema_expression, F, Value, Func

compile_schema_expression(F("title"))               # → '"title"'
compile_schema_expression(Value("hello"))           # → "'hello'"
compile_schema_expression(F("author__name"))        # → '"author"."name"'
compile_schema_expression(Func("UPPER", F("title")))  # → 'UPPER("title")'
\`\`\`

This function is used internally by \`base.py\` (unique constraint DDL), \`fields_module.py\` (Index DDL), and the new migration backends.

---

## Summary

| Field / Function | Change | Impact |
|---|---|---|
| \`EnumField.enum_class\` | Accepts dotted-string path for migration round-trips | Enables generated migration files to reconstruct \`EnumField\` |
| \`BigAutoField.sql_type("mysql")\` | Now \`"BIGINT"\` instead of \`"INTEGER"\` | Fixes silent 32-bit truncation on MySQL |
| \`SmallAutoField.sql_type("mysql")\` | Now \`"SMALLINT"\` instead of \`"INTEGER"\` | Fixes incorrect type on MySQL |
| \`GeneratedField.deconstruct()\` | Now includes \`expression\`, \`db_persist\`, \`output_field\` | Makes generated columns visible to migration snapshotting |
| \`compile_schema_expression\` | Moved to \`expression.py\` (public); removed from \`schema_snapshot\` | Updated import path required |
`,
    "migration.md": `# Breaking Changes & Migration Guide — Aquilia v1.3.10

This guide documents every breaking change introduced in v1.3.10 and provides step-by-step instructions for upgrading.

---

## Summary of Breaking Changes

| Category | Breaking Change |
|---|---|
| **Removed modules** | \`migration_dsl\`, \`migration_gen\`, \`migration_planner\`, \`migration_runner\`, \`migrations\`, \`schema_snapshot\`, \`ddl_executor\` |
| **Removed public symbols** | \`MigrationRunner\`, \`MigrationOps\`, \`DSLMigrationRunner\`, \`Migration\`, \`DSLCreateModel\`, \`DSLAddField\`, \`DSLRemoveField\`, \`DSLAlterField\`, \`DSLRenameField\`, \`DSLDropModel\`, \`DSLRenameModel\`, \`DSLCreateIndex\`, \`DSLDropIndex\`, \`DSLRunSQL\`, \`DSLRunPython\`, \`DSLAddConstraint\`, \`DSLRemoveConstraint\`, \`MigrationInfo\`, \`generate_migration_from_models\`, \`op\`, \`generate_dsl_migration\`, \`InitialSchemaPlanner\`, \`MigrationPlan\`, \`MigrationPlanner\`, \`MigrationStep\`, \`DDLExecutor\`, \`ExecutableStatement\`, \`StatementType\`, \`C\`, \`ColumnDef\`, \`columns\`, \`create_snapshot\`, \`save_snapshot\`, \`load_snapshot\`, \`compute_diff\`, \`diff_to_operations\`, \`SchemaDiff\`, \`ModelDiff\` |
| **CLI flags removed** | \`aq db makemigrations --use-dsl\`, \`--no-use-dsl\`, \`--migration-format\` |
| **Snapshot format** | Old \`"models"\` key is no longer written; new format uses \`"tables"\`. Old snapshots are detected and discarded gracefully. |
| **Probe function renames** | \`check_db_exists\` → \`database_exists\`; \`check_migrations_applied\` → \`migrations_applied\`; \`check_db_ready\` removed |

---

## Removed Modules

The following modules have been deleted. Any direct import of them will raise \`ImportError\`:

| Old Module | Replacement |
|---|---|
| \`aquilia.models.ddl_executor\` | \`aquilia.models.migration.executor\` + \`aquilia.models.migration.backends\` |
| \`aquilia.models.migration_dsl\` | \`aquilia.models.migration.operations\` |
| \`aquilia.models.migration_gen\` | \`aquilia.models.migration.codegen\` + \`aquilia.models.migration.serializer\` |
| \`aquilia.models.migration_planner\` | \`aquilia.models.migration.graph\` + \`aquilia.models.migration.engine\` |
| \`aquilia.models.migration_runner\` | \`aquilia.models.migration.executor\` + \`aquilia.models.migration.engine\` |
| \`aquilia.models.migrations\` | \`aquilia.models.migration.engine\` |
| \`aquilia.models.schema_snapshot\` | \`aquilia.models.migration.schema\` + \`aquilia.models.migration.autodetect\` |

---

## Import Path Changes

### Top-Level \`aquilia.models\` Exports

**Removed exports:**

\`\`\`python
# These no longer exist in aquilia.models:
from aquilia.models import (
    MigrationRunner,       # removed
    MigrationOps,          # removed
    MigrationInfo,         # removed
    generate_migration_from_models,  # removed
    op,                    # removed
    Migration,             # removed
    DSLMigrationRunner,    # removed
    DSLCreateModel,        # removed
    DSLAddField,           # removed
    DSLRemoveField,        # removed
    DSLAlterField,         # removed
    DSLRenameField,        # removed
    DSLDropModel,          # removed
    DSLRenameModel,        # removed
    DSLCreateIndex,        # removed
    DSLDropIndex,          # removed
    DSLRunSQL,             # removed
    DSLRunPython,          # removed
    DSLAddConstraint,      # removed
    DSLRemoveConstraint,   # removed
    ColumnDef,             # removed
    columns,               # removed
    C,                     # removed
    create_snapshot,       # removed
    save_snapshot,         # removed
    load_snapshot,         # removed
    compute_diff,          # removed
    diff_to_operations,    # removed
    SchemaDiff,            # removed
    ModelDiff,             # removed
    DDLExecutor,           # removed
    ExecutableStatement,   # removed
    ExecutionResult,       # removed (old one)
    StatementType,         # removed
    InitialSchemaPlanner,  # removed
    MigrationPlan,         # removed
    MigrationPlanner,      # removed
    MigrationStep,         # removed
    check_db_exists,       # removed
    check_migrations_applied,  # removed
    check_db_ready,        # removed
    generate_dsl_migration, # removed
)
\`\`\`

**New exports (via \`aquilia.models\`):**

\`\`\`python
from aquilia.models import (
    MigrationEngine,   # replaces MigrationRunner, DSLMigrationRunner
    MigrationGraph,    # new
    MigrationNode,     # new
    MigrationStatus,   # new
    Operation,         # new unified base (replaces DSL* operations)
    ProjectState,      # replaces SchemaDiff/ModelDiff snapshot machinery
)
\`\`\`

### Top-Level \`aquilia\` Exports

\`\`\`python
# Old
from aquilia import MigrationRunner, MigrationOps

# New
from aquilia import MigrationEngine
\`\`\`

---

## Code Migration Examples

### Generating Migrations

**Before (v1.3.9 — DSL path):**

\`\`\`python
from aquilia.models.migration_gen import generate_dsl_migration

result = generate_dsl_migration(
    model_classes=[User, Post],
    migrations_dir="migrations",
)
\`\`\`

**Before (v1.3.9 — legacy path):**

\`\`\`python
from aquilia.models.migrations import generate_migration_from_models

result = generate_migration_from_models(
    model_classes=[User, Post],
    migrations_dir="migrations",
)
\`\`\`

**After (v1.3.10):**

\`\`\`python
from aquilia.models.migration import MigrationEngine

engine = MigrationEngine("migrations")
path = engine.make_migrations([User, Post])
# path is None when no changes are detected
\`\`\`

---

### Applying Migrations

**Before (v1.3.9 — MigrationRunner):**

\`\`\`python
from aquilia.models.migration_runner import MigrationRunner

runner = MigrationRunner(db, "migrations", dialect=db.dialect)
applied_revisions = await runner.migrate()
\`\`\`

**After (v1.3.10):**

\`\`\`python
from aquilia.models.migration import MigrationEngine

engine = MigrationEngine("migrations")
results = await engine.migrate(db)
# results is list[ExecutionResult], one per migration
\`\`\`

---

### Snapshot Operations

**Before (v1.3.9):**

\`\`\`python
from aquilia.models.schema_snapshot import (
    create_snapshot, save_snapshot, load_snapshot,
    compute_diff, diff_to_operations, SchemaDiff, ModelDiff
)

snapshot = create_snapshot([User, Post])
save_snapshot(snapshot, "migrations/schema_snapshot.json")

old_snap = load_snapshot("migrations/schema_snapshot.json")
diff = compute_diff(old_snap, snapshot)
ops = diff_to_operations(diff)
\`\`\`

**After (v1.3.10):**

\`\`\`python
from aquilia.models.migration import MigrationEngine, ProjectState

engine = MigrationEngine("migrations")

# Snapshot is managed automatically by make_migrations.
# For manual access:
state = ProjectState.from_models([User, Post])
engine.save_snapshot(state)

before = engine.load_snapshot()
after = ProjectState.from_models([User, Post])

from aquilia.models.migration import detect_changes
ops = detect_changes(before, after)
\`\`\`

---

### DDL Executor Usage

**Before (v1.3.9):**

\`\`\`python
from aquilia.models import DDLExecutor, CreateModel, C

ops = [CreateModel("User", "users", [C.auto("id"), C.varchar("email", 255)])]
statements = DDLExecutor.compile_operations(ops, dialect="postgresql")
result = await DDLExecutor.execute_statements(db, statements, in_transaction=True)
\`\`\`

**After (v1.3.10):**

\`\`\`python
from aquilia.models.migration import MigrationEngine

engine = MigrationEngine("migrations")
# Let the engine manage creation; or use MigrationExecutor directly:

from aquilia.models.migration.executor import MigrationExecutor
from aquilia.models.migration.operations import CreateModel
from aquilia.models.migration.schema import ProjectState, TableState, ColumnState
from aquilia.models import fields

executor = MigrationExecutor(db)
result = await executor.apply_operations(
    [CreateModel(model="User", table=TableState.of("User", "users", columns=[
        ColumnState.of("id", fields.AutoField(primary_key=True)),
        ColumnState.of("email", fields.EmailField(unique=True)),
    ]))],
    ProjectState(),
    description="create user table",
)
\`\`\`

---

### Probe Functions

**Before (v1.3.9 — \`migration_runner\`):**

\`\`\`python
from aquilia.models.migration_runner import check_db_exists, check_migrations_applied

if not check_db_exists(db_url):
    ...
if not check_migrations_applied(db_url, migrations_dir):
    ...
\`\`\`

**After (v1.3.10 — \`migration.probe\`):**

\`\`\`python
from aquilia.models.migration.probe import database_exists, migrations_applied
# Also available via:
from aquilia.models.migration import database_exists, migrations_applied

if not database_exists(db_url):
    ...
if not migrations_applied(db_url, migrations_dir):
    ...
\`\`\`

---

### Direct DSL Operations

**Before (v1.3.9 — DSL prefix):**

\`\`\`python
from aquilia.models import (
    DSLCreateModel, DSLAddField, DSLRemoveField,
    DSLAlterField, DSLRenameField, DSLRunSQL,
)
\`\`\`

**After (v1.3.10 — unified operations):**

\`\`\`python
from aquilia.models.migration import (
    CreateModel, AddField, RemoveField,
    AlterField, RenameField, RunSQL,
)
# or via aquilia.models:
from aquilia.models import Operation
\`\`\`

---

## Snapshot Format Upgrade

The v1.3.10 snapshot format uses \`"tables"\` as the top-level key instead of \`"models"\`. Old snapshots with \`"models"\` are detected at load time:

\`\`\`python
# In MigrationEngine.load_snapshot():
if "tables" not in raw and "models" in raw:
    logger.info(
        "Schema snapshot at %s is in a superseded format and cannot describe "
        "many-to-many relations, generated columns, or index methods. It will be "
        "replaced on the next makemigrations.",
        path,
    )
    return ProjectState()
\`\`\`

**What happens:** The old snapshot is silently discarded, and the engine treats the state as empty. The next \`makemigrations\` will diff against an empty state, producing a full \`CreateModel\` for every model — essentially a new initial migration.

**Action required:** If you have an existing \`schema_snapshot.json\` in the old \`"models"\` format:

1. Delete \`migrations/schema_snapshot.json\`
2. Run \`aq db makemigrations\` — it will regenerate the snapshot in the new format

> [!NOTE]
> Your existing migration *files* are not affected. The snapshot is purely a caching artefact for the autodetector. The migration graph (your \`.py\` files) remains the authoritative record.

---

## CLI Flag Removal

\`\`\`bash
# These flags are no longer accepted:
aq db makemigrations --use-dsl          # → error: no such option
aq db makemigrations --no-use-dsl       # → error: no such option
aq db makemigrations --migration-format python  # → error: no such option

# Use instead:
aq db makemigrations                    # always uses new engine
aq db makemigrations --slug my_change   # optional human-readable name
aq db makemigrations --dry-run          # new: preview without writing
\`\`\`

---

## Upgrade Checklist

- [ ] Update \`aquilia\` dependency to \`v1.3.10\`
- [ ] Replace all imports of removed modules (see table above)
- [ ] Replace \`MigrationRunner\` with \`MigrationEngine\` throughout application code
- [ ] Replace \`DSL*\` operation imports with unified \`migration.operations\` imports
- [ ] Remove \`--use-dsl\`, \`--no-use-dsl\`, \`--migration-format\` from any scripts or CI that call \`aq db makemigrations\`
- [ ] Replace \`check_db_exists\`/\`check_migrations_applied\` with \`database_exists\`/\`migrations_applied\`
- [ ] Replace \`from aquilia.models.schema_snapshot import _compile_schema_expression\` with \`from aquilia.models.expression import compile_schema_expression\`
- [ ] Delete old \`schema_snapshot.json\` and regenerate with \`aq db makemigrations\` (if format was \`"models"\`)
- [ ] Run \`aq db status\` to verify the migration tracking table is intact
- [ ] Run \`aq db migrate\` if any migrations are pending
- [ ] Run your full test suite: \`pytest tests/\`

---

## Compatibility Notes

- **Generated migration files from v1.3.8 / v1.3.9** that use the old DSL (\`Migration\`, \`C.varchar(...)\`, \`ColumnDef\`, etc.) will **not** be loadable by the new engine. You must either squash and regenerate, or rewrite them to use the new operation format.
- **Migration tracking table** (\`aquilia_migrations\`) is unchanged. Existing applied-migration rows are preserved.
- **All other Aquilia subsystems** (controllers, contracts, DI, sessions, auth, cache, storage, tasks, WebSockets, mail, templates, admin, artifacts) are unaffected by this release.
- **Python version** requirement unchanged (3.11+).
- **Database support** unchanged: SQLite, PostgreSQL, MySQL, Oracle.
`,
    "bugfixes.md": `# Bug Fixes — Aquilia v1.3.10

---

## Bug 1 — \`_patched_create_tables_new\` — Optional \`db\` Parameter

### Previous Behaviour

In the faults integration module (\`aquilia/faults/integrations/models.py\`), the patched \`_patched_create_tables_new\` function had a signature that did not accept an optional \`db\` parameter. When \`ModelRegistry.create_tables(db=some_db)\` was called with an explicit database argument, the patched version raised a \`TypeError\` because it only accepted no arguments.

### Root Cause

The patch was written against the original \`create_tables()\` signature before the optional \`db\` override was added to \`ModelRegistry\`. The patch was not updated when the parameter was introduced.

### Fix

The \`_patched_create_tables_new\` signature now accepts \`db=None\` as an optional keyword argument, matching the real \`ModelRegistry.create_tables\` signature:

\`\`\`python
# Before
async def _patched_create_tables_new():
    ...

# After
async def _patched_create_tables_new(db=None):
    ...
\`\`\`

### User Impact

Users calling \`ModelRegistry.create_tables(db=my_db)\` explicitly — common in test setups — would have seen an unexpected \`TypeError\`. This is now fixed.

---

## Bug 2 — \`startup_guard.py\` — Probe Function Renames

### Previous Behaviour

\`startup_guard.py\` imported probe functions from \`migration_runner\`:

\`\`\`python
from .migration_runner import check_db_exists, check_migrations_applied
\`\`\`

After \`migration_runner.py\` was deleted in this release, the import raised an \`ImportError\` at runtime, crashing any server boot that reached the startup guard.

### Fix

Updated to import the renamed functions from \`migration.probe\`:

\`\`\`python
# Before
from .migration_runner import check_db_exists, check_migrations_applied

if not check_db_exists(db_url): ...
if not check_migrations_applied(db_url, migrations_dir): ...

# After
from .migration.probe import database_exists, migrations_applied

if not database_exists(db_url): ...
if not migrations_applied(db_url, migrations_dir): ...
\`\`\`

### User Impact

Any application that used \`startup_guard.py\`'s readiness checking (i.e. any application with \`auto_migrate=False\` and a SQLite database) would have seen an \`ImportError\` on server startup. This is now fixed.

---

## Bug 3 — \`ModelRegistry.create_tables()\` — Unified DDL Path

### Previous Behaviour

\`ModelRegistry.create_tables()\` called \`MigrationRunner\` from \`migration_runner.py\`:

\`\`\`python
from .migration_runner import MigrationRunner

runner = MigrationRunner(target_db, dialect=getattr(target_db, "dialect", "sqlite"))
exec_stmts = await runner.create_initial_schema(ordered)
return [s.sql for s in exec_stmts if s.sql and not s.is_comment]
\`\`\`

After \`migration_runner.py\` was deleted, this import raised \`ImportError\`.

### Fix

\`ModelRegistry.create_tables()\` now uses \`ProjectState\` and \`MigrationExecutor\` from the new sub-package:

\`\`\`python
from .migration import ProjectState
from .migration.executor import MigrationExecutor
from .migration.operations import CreateManyToManyTable, CreateModel

target_state = ProjectState.from_models(ordered)
operations = []
for model_name in target_state.creation_order():
    table = target_state.tables[model_name]
    operations.append(CreateModel(model=model_name, table=table))
    for relation in table.m2m:
        operations.append(CreateManyToManyTable(model=model_name, relation=relation))

executor = MigrationExecutor(target_db)
result = await executor.apply_operations(operations, ProjectState(), description="initial schema")
await cls._record_initial_schema(target_db, target_state)
return [statement.sql for statement in result.executed if statement.sql]
\`\`\`

### Additional Improvement

\`create_tables()\` now records \`0000_initial_schema\` in the \`aquilia_migrations\` table (via the new \`_record_initial_schema\` class method), so a subsequent \`aq db migrate\` correctly sees the initial schema as already applied. Previously, running \`create_tables()\` and then \`migrate()\` would attempt to re-apply the initial migration and fail with "table already exists".

### User Impact

Applications using \`auto_create=True\` (the default) or calling \`ModelRegistry.create_tables()\` directly would have seen an \`ImportError\` at startup. This is now fixed, and the initial schema is now properly tracked.

---

## Bug 4 — \`compile_schema_expression\` Import in \`base.py\` and \`fields_module.py\`

### Previous Behaviour

\`base.py\` and \`fields_module.py\` imported \`_compile_schema_expression\` from \`schema_snapshot\`:

\`\`\`python
from .schema_snapshot import _compile_schema_expression
\`\`\`

After \`schema_snapshot.py\` was deleted, these imports raised \`ImportError\`, breaking unique constraint DDL generation and index DDL generation.

### Fix

Updated to import from \`expression.py\`:

\`\`\`python
from .expression import compile_schema_expression as _compile_schema_expression
\`\`\`

The function is now public (\`compile_schema_expression\`) rather than private (\`_compile_schema_expression\`).

### User Impact

Any model with expression-based unique constraints or functional indexes would have raised \`ImportError\` when generating \`CREATE TABLE\` SQL. This is now fixed.

---

## Bug 5 — \`server.py\` — Auto-Migration Path

### Previous Behaviour

\`AquiliaServer\` used \`MigrationRunner\` from \`migration_runner.py\` for auto-migration:

\`\`\`python
from aquilia.models.migration_runner import MigrationRunner

runner = MigrationRunner(db, migrations_dir)
await runner.migrate()
\`\`\`

### Fix

Updated to use \`MigrationEngine\`:

\`\`\`python
from aquilia.models.migration import MigrationEngine

await MigrationEngine(migrations_dir).migrate(db)
\`\`\`

This is a one-line functional change — the behaviour is identical, but the implementation now routes through the new unified engine.

---

## Bug 6 — \`aq db reset\` — Tracking Table Survives Table Drop

### Previous Behaviour

On dialects where the \`DROP TABLE\` loop did not drop the \`aquilia_migrations\` tracking table (MySQL with foreign key checks, certain PostgreSQL configurations), \`reset\` would leave the tracking table intact with all its rows. The subsequent \`migrate()\` call would then see every migration as already applied (because the rows still existed) and do nothing — leaving the database completely empty but reporting itself as fully migrated.

### Fix

After dropping tables, \`reset\` now explicitly checks whether \`aquilia_migrations\` still exists and clears it if so:

\`\`\`python
engine = MigrationEngine(migrations_dir)
remaining = await db.get_tables()
if "aquilia_migrations" in remaining:
    await db.execute('DELETE FROM "aquilia_migrations"')
results = await engine.migrate(db)
\`\`\`

### User Impact

\`aq db reset\` on MySQL or certain PostgreSQL configurations would silently produce an empty database that claimed to be fully migrated. After the reset, the next \`aq db status\` would show everything as applied. Queries against the (empty) database would fail with "table does not exist". This is now fixed.
`,
    "architecture.md": `# Architecture Deep Dive — Aquilia v1.3.10

This document explains the design decisions, trade-offs, and guarantees behind the new migration subsystem for readers who want to understand the internals or contribute to the framework.

---

## Design Principles

### 1. No Information Loss at the First Hop

Previous systems reduced every \`Field\` to a handful of primitives (name, SQL type, a few booleans) at snapshotting time. No amount of care downstream can recover a generated-column expression, a partial-index predicate, an operator class, or an M2M relationship from that reduced set.

\`ProjectState\` therefore captures fields through \`Field.deconstruct()\` and retains enough to reconstruct them faithfully. SQL generation is deferred to \`backends/\` — the *only* layer permitted to know about dialects.

### 2. Strict Layering

\`\`\`
Model classes → schema.py → operations/ → backends/
               state          state deltas    SQL text
\`\`\`

Nothing in \`schema.py\` emits SQL. Nothing in \`operations/\` imports a backend. Nothing in \`engine.py\` constructs a SQL string. This separation makes operations backend-independent, serialization deterministic, and testing tractable.

### 3. Determinism Above All

A migration is a permanent, reviewable artifact. Two developers generating a migration against the same models on different machines must get the same file. Every collection in the pipeline is an ordered \`tuple\`; every mapping is iterated through \`sorted()\`. The \`codegen\` layer emits sorted key-order, omits default-valued arguments, and accepts no clock or hostname into the rendered body.

Consequence: "No changes detected" is trustworthy. Regenerating from unchanged models produces a byte-identical file.

### 4. Safe Rename Detection

A rename is a destructive guess. Emitting \`RENAME COLUMN\` when the developer actually dropped one column and added another silently overwrites the wrong column and loses its data.

The autodetector scores rename candidates across multiple independent signals. The \`RENAME_CONFIDENCE_THRESHOLD = 0.85\` is set so that no single signal — not even an identical type — can clear it alone. The combination of type match, name similarity, position, and constraints must all agree before a rename is inferred automatically. The developer can always provide an explicit \`RenameHint\` to override the inference.

### 5. File Before Snapshot

\`make_migrations\` writes the migration file first, then saves the updated snapshot:

\`\`\`python
path.write_text(source, encoding="utf-8")
self.save_snapshot(after)           # ← snapshot written AFTER file
\`\`\`

If the snapshot write fails, the file still exists and the snapshot still describes the last successful migration. The next \`makemigrations\` will compute the same diff and regenerate the same file — the developer just reruns the command.

Writing snapshot first would advance it past a migration file that was never recorded on disk. The next \`makemigrations\` would see no diff and generate nothing, losing the change entirely.

### 6. Tracking Inside the Transaction

\`\`\`
┌─ transaction ─────────────────────────────────────┐
│  DDL statement 1                                  │
│  DDL statement 2                                  │
│  ...                                              │
│  INSERT INTO aquilia_migrations (revision, ...)   │
└───────────────────────────────────────────────────┘
\`\`\`

The tracking \`INSERT\` is the last statement *inside* the same transaction. Schema and history commit or roll back together, closing the window where a crash could change the schema without recording it.

### 7. Non-transactional Statements

Some DDL cannot participate in a transaction:

- **SQLite table rebuilds** need \`PRAGMA foreign_keys\` toggled outside any transaction.
- **PostgreSQL \`CREATE INDEX CONCURRENTLY\`** is rejected inside a transaction.
- **MySQL and Oracle DDL** cannot participate in a transaction at all.

Statements declare their own requirement (\`transactional: bool\`). The executor splits the batch at non-transactional statements, warns on MySQL/Oracle rather than promising atomicity it cannot deliver, and emits \`diagnostics\` entries to \`ExecutionResult\` for both cases.

---

## Atomicity Model

\`\`\`
Transactional (SQLite, PostgreSQL):
  ✓ DDL rolls back on failure
  ✓ Tracking row commits with DDL or not at all
  ✓ No partial schema artifacts

Non-transactional (MySQL, Oracle):
  ⚠ DDL committed immediately (per statement)
  ⚠ Failure may leave partial schema
  ✓ Tracking row not written on failure
  ✓ Warning logged via ExecutionResult.diagnostics
\`\`\`

---

## Snapshot Format v2 (STATE_VERSION = 2)

The snapshot stores the current \`ProjectState\` as a JSON artifact:

\`\`\`json
{
  "format": "aquilia-artifact",
  "artifact_type": "schema_snapshot",
  "key": "main",
  "schema_version": "2.0",
  "payload": {
    "state_version": 2,
    "tables": {
      "User": {
        "db_table": "users",
        "columns": { ... },
        "indexes": [ ... ],
        "constraints": [ ... ],
        "m2m": [ ... ]
      }
    }
  },
  "fingerprint": "sha256:..."
}
\`\`\`

Key differences from the old \`"models"\` format (v1):

| Feature | v1 (\`"models"\`) | v2 (\`"tables"\`) |
|---|---|---|
| Top-level key | \`"models"\` | \`"tables"\` |
| Field storage | Primitive strings | \`Field.deconstruct()\` dicts |
| M2M support | ❌ | ✓ |
| Generated columns | ❌ | ✓ |
| Index methods | ❌ | ✓ |
| Partial predicates | ❌ | ✓ |
| Determinism | Set-ordered | Sorted tuple |
| Format detection | None | \`STATE_VERSION\` field |

Old snapshots with \`"models"\` key are detected and discarded: the engine logs an informational message and returns an empty \`ProjectState\`, triggering a full regeneration on the next \`makemigrations\`.

---

## Migration File Format v3 (MIGRATION_TEMPLATE_VERSION = 3)

Version 3 files use real constructor calls:

\`\`\`python
# MIGRATION_TEMPLATE_VERSION = 3
from aquilia.models.migration import CreateModel, AddField, Operation, ProjectState
from aquilia.models.migration.schema import ColumnState, TableState
from aquilia.models import fields

revision: str = "20260801_103000"
slug: str = "add_bio"
dependencies: tuple[str, ...] = ("20260730_120000",)
atomic: bool = True

operations: list[Operation] = [
    AddField(
        model="User",
        field=ColumnState.of("bio", fields.TextField(null=True)),
    ),
]
\`\`\`

Version 2 files (old DSL with \`Migration\`, \`C.*\`, \`ColumnDef\`) are **not** loadable by the new engine. Version 1 files (legacy raw-SQL with \`upgrade(db)\`) are also not loadable. A \`MigrationFault\` is raised when loading either.

---

## Graph Planning

### Forward Plan

Given the set of applied revisions, \`MigrationGraph.forward_plan(applied)\` returns pending nodes in topological order:

1. Build the dependency DAG from all nodes on disk.
2. Remove any node already in \`applied\`.
3. Return nodes in topological order where all dependencies are satisfied.

A node with \`replaces = ("a", "b")\` is skipped in the forward plan when every revision in \`replaces\` is in \`applied\` — the squash migration is treated as already done.

### Backward Plan

\`backward_plan(applied, target)\` returns the nodes to roll back to reach \`target\`:

1. Find the path from the current leaves back to \`target\`.
2. Return nodes in reverse dependency order (deepest first).
3. Each operation must implement \`state_backwards\` and \`database_backwards\`; irreversible operations (\`RunPython\` without \`reverse_code\`) raise \`MigrationFault\`.

### Conflict Detection

\`check_conflicts()\` raises \`MigrationConflictFault\` when:
- Two migration files claim the same revision.
- Two leaf nodes have no common ancestor (forked history without a merge migration).

Forked history is the expected result of two developers generating migrations on the same branch simultaneously. The resolution is to generate a merge migration that explicitly depends on both leaves.

---

## Optimizer Passes

The optimizer iterates the operation list repeatedly until no pass reduces its length (or \`MAX_OPTIMIZER_PASSES = 32\` is reached):

\`\`\`
Pass 1: [CreateModel(U), AddField(U.x), AddField(U.y)] → [CreateModel(U with x, y)]
Pass 2: no further reduction
→ done in 2 passes
\`\`\`

\`RunSQL\` and \`RunPython\` are opaque barriers. The optimizer never merges across them because a data migration may well depend on the exact intermediate schema, and merging across it would silently change what it sees. This is not a safety "nice to have" — it is a correctness requirement.

---

## Checksum Verification

Every \`AppliedMigration\` row now stores a SHA-256 digest of the migration source file (\`MigrationNode.checksum\`). \`engine.verify_checksums(db)\` reads all applied rows from the tracking table and checks each against the corresponding file on disk:

| Mismatch type | Reason |
|---|---|
| File missing from disk | Migration was applied but the file was deleted |
| Checksum mismatch | File was edited after being applied |

This is not a blocking check — the engine does not refuse to run with mismatches — but the output can be used in CI to enforce that production migrations have not been tampered with.
`,
  },
  "1.3.9": {
    "README.md": `# Aquilia v1.3.9 Release Notes — "Database Sentinel"

Aquilia v1.3.9 introduces **Strict auto_migrate=False Enforcement**, **Non-Fatal Database Startup Readiness Model (DatabaseState)**, **Single-Authority Migration Engine Architecture (MigrationRunner, DDLExecutor, MigrationPlanner)**, and **Atomic Transactional DDL & Migration History Guarantees** across the Aquilia Database, ORM, and Server Startup subsystems.

---

## Table of Contents

1. [Strict auto_migrate=False Enforcement](auto_migrate_enforcement.md)
2. [Non-Fatal Database Startup Readiness (DatabaseState)](non_fatal_startup_guard.md)
3. [Atomic Transactional DDL Execution](atomic_ddl_transactions.md)
4. [Single-Authority Migration Engine Architecture](single_authority_migration_engine.md)
5. [DDL Executor & Migration Planner Architecture](ddl_executor_and_planner.md)
6. [Bug Fixes & Audit](bugfixes.md)
7. [Migration Guide & Upgrade Checklist](migration.md)
`,
    "auto_migrate_enforcement.md": `# Strict auto_migrate=False Schema Enforcement

In Aquilia v1.3.9, the framework strictly enforces the developer's \`auto_migrate=False\` setting across all startup phases.

When \`auto_migrate=False\` is set, Aquilia strictly guarantees that **no tables will be created**, **no schema will be modified**, and **no DDL statements will execute** on startup—even if \`auto_create=True\` is set on the integration.
`,
    "non_fatal_startup_guard.md": `# Non-Fatal Database Readiness Model (DatabaseState)

In Aquilia v1.3.9, database startup readiness checks no longer treat uninitialized databases as fatal process-crashing exceptions.

Introduced the \`DatabaseState\` enum in \`aquilia.models.startup_guard\`:
- \`READY\`
- \`MISSING_DATABASE\`
- \`PENDING_MIGRATIONS\`
- \`CORRUPTED_HISTORY\`
- \`SCHEMA_MISMATCH\`
- \`UNAVAILABLE\`
`,
    "atomic_ddl_transactions.md": `# Atomic Transactional DDL & Migration Rollback

In Aquilia v1.3.9, table creation (\`ModelRegistry.create_tables()\`) and migration application (\`MigrationRunner.execute_plan()\`) are executed within explicit database transaction blocks (\`async with db.transaction():\`).

If any DDL statement fails, all changes roll back cleanly, guaranteeing 0 partial tables or columns are left behind.
`,
    "single_authority_migration_engine.md": `# Single-Authority Migration Engine Architecture

In Aquilia v1.3.9, the database schema creation and migration execution pipeline is unified under a single authority: the **Migration Engine** (\`MigrationRunner\`, \`MigrationPlanner\`, and \`DDLExecutor\`).

\`ModelRegistry\` has been completely stripped of DDL execution authority. It delegates \`create_tables()\` and \`drop_tables()\` directly to \`MigrationRunner\`. Initial schema creation is recorded as \`0000_initial_schema\` in \`aquilia_migrations\`.
`,
    "ddl_executor_and_planner.md": `# DDL Executor & Migration Planner Architecture

Aquilia v1.3.9 introduces \`DDLExecutor\` and \`MigrationPlanner\` in \`aquilia.models\`.

- \`DDLExecutor\`: Compiles DSL operations into strongly-typed \`ExecutableStatement\` objects with \`StatementType\` categories (\`CREATE_TABLE\`, \`ALTER_TABLE\`, \`CREATE_INDEX\`, etc.) and executes them atomically.
- \`InitialSchemaPlanner\`: Plans zero-revision initial schema creation directly from model descriptors without empty-snapshot diffing.
- \`DatabaseAdapter.should_ignore_ddl_error()\`: Encapsulates dialect-specific DDL error codes (e.g. MySQL 1061/1091).
`,
    "bugfixes.md": `# Bug Fixes & Deep Audit Report (v1.3.9)

Resolved Bug 1 (auto_migrate=False bypassed by auto_create), Bug 2 (Database not ready fatal SchemaFault), and Bug 3 (Partial schema pollution on DDL failure).
`,
    "migration.md": `# Migration & Upgrade Guide for Aquilia v1.3.9

Fully backward-compatible release. Run \`aq db migrate\` in CI/CD pipeline when deploying with \`auto_migrate=False\`. Initial schema creation is tracked cleanly under \`0000_initial_schema\`.
`
  },
  "1.3.8": {
    "README.md": `# Aquilia v1.3.8 Release Notes — "Migration Architect"

Aquilia v1.3.8 introduces **DSL Migration Generator Architectural Overhaul**, **Topological Foreign Key Model Dependency Ordering**, **Character-Split Index Normalization**, **Strict Foreign Key Target Table Resolution**, **Scalar Enum Default Serialization**, and **Comprehensive Migration Dependencies Metadata** across the Aquilia Database and ORM Migration subsystem.

Before this release, auto-generated migration DSL files produced by \`aq db makemigrations\` (and \`generate_dsl_migration()\`) contained critical correctness bugs: index column names were split into single characters (\`columns=['t', 'o', 'k', 'e', 'n']\`), foreign key references targeted raw un-pluralized model class name stubs (\`C.foreign_key("user_id", "usersmodel", "id")\`), Enum field default values emitted stringified enum representation objects (\`default=<UserStatus.ACTIVE: 'active'>\`) breaking Python syntax, model creation operations were ordered arbitrarily rather than by foreign key dependencies, and index/constraint column targets failed to resolve model attribute names to actual database column names (\`"user"\` instead of \`"user_id"\`).

This release addresses all 19 identified migration DSL generator vulnerabilities, implements post-order topological dependency sorting (\`_topologically_sort_models()\`), adds strict foreign key target table resolution (\`_resolve_target_table()\`), normalizes database column resolution (\`_resolve_db_column_name()\`), unwraps Enum defaults to DB-storable primitive scalars, and adds migration dependency tracking metadata (\`dependencies = [...]\`).

---

## Table of Contents

1. [Migration DSL Generator Overhaul](migration_dsl_generator_fixes.md)
   - Index column normalization (fixing character-split index column arrays)
   - Foreign key target table resolution (\`_resolve_target_table()\`)
   - Model attribute to database column name mapping (\`_resolve_db_column_name()\`)
   - Foreign key SQL type inference consistency (\`col_type="VARCHAR(36)"\`)
2. [Topological Model Dependency Ordering](model_dependency_ordering.md)
   - Dependency graph construction for \`CreateModel\` operations
   - Post-order depth-first topological traversal (\`_topologically_sort_models()\`)
   - Self-referential and cyclic foreign key resolution
3. [ORM Field Deconstruction & Serialization](orm_field_deconstruct_serialization.md)
   - Scalar Enum default value unwrapping (\`'active'\` instead of \`<Enum: 'active'>\`)
   - Snapshot serialization (\`create_snapshot()\`) and diffing (\`diff_to_operations()\`)
   - Column definition generator (\`_render_column_def()\`)
4. [Bug Fixes](bugfixes.md)
   - Comprehensive audit of all 19 migration generator issues, root causes, and resolutions
5. [Migration Guide](migration.md)
   - Upgrade checklist, compatibility notes, and zero-breaking-change guarantees

---

## Highlights

### 1. Character-Split Index Column Normalization

Index field declarations—whether provided as strings (\`Index(fields="token")\`), tuples, or list expressions—are strictly normalized into database column arrays (\`columns=['token']\`), eliminating corrupted index column arrays (\`['t', 'o', 'k', 'e', 'n']\`) and index names (\`idx_email_verification_t_o_k_e_n\`).

\`\`\`python
# Generated Migration DSL (v1.3.8)
CreateIndex(
    name='idx_email_verification_token',
    table='email_verification',
    columns=['token'],
    unique=False,
),
\`\`\`

### 2. Foreign Key Target Table Resolution

Foreign key references dynamically resolve to actual database table names (\`"users"\`), taking into account \`_meta.table_name\` overrides, \`ModelRegistry\` lookups, and PascalCase-to-snake_case pluralization fallbacks.

\`\`\`python
# Generated Migration DSL (v1.3.8)
C.foreign_key("user_id", "users", "id", col_type="VARCHAR(36)"),
\`\`\`

### 3. Scalar Enum Default Serialization

Enum defaults are unwrapped during snapshot serialization and code generation to DB-storable primitive scalar literals (\`'active'\` or \`1\`), ensuring generated Python migration files parse cleanly via \`ast.parse()\`.

\`\`\`python
# Generated Migration DSL (v1.3.8)
C.text("status", default='active'),
\`\`\`

### 4. Topological Model Creation Ordering

\`CreateModel\` operations in generated migrations are topologically sorted based on foreign key table dependencies. Referenced tables (\`users\`) are always created before dependent tables (\`email_verification\`, \`user_roles\`).

\`\`\`python
# Generated Migration DSL (v1.3.8 operations list)
operations = [
    CreateModel(name='UserModel', table='users', fields=[...]),
    CreateModel(name='Post', table='posts', fields=[...]),
    CreateModel(name='UserEmailVerificationModel', table='email_verification', fields=[...]),
    CreateModel(name='UserRoleModel', table='user_roles', fields=[...]),
]
\`\`\`

### 5. Migration Dependency Tracking Metadata

Generated migration modules now explicitly include prerequisite revision IDs in \`Meta.dependencies\`.

\`\`\`python
class Meta:
    revision = "20260730_201500"
    slug = "post_useremailverificationmodel_and_2_more"
    models = ['Post', 'UserEmailVerificationModel', 'UserModel', 'UserRoleModel']
    dependencies = ['20260730_143000']
\`\`\`

---

## Summary of Changes

| Subsystem | Change | Impact |
|---|---|---|
| \`aquilia.models.schema_snapshot\` | Added \`_resolve_db_column_name()\`, \`_resolve_target_table()\`, \`_topologically_sort_models()\` | Resolves DB column names, FK target tables, and topological \`CreateModel\` execution order |
| \`aquilia.models.migration_gen\` | Updated \`generate_dsl_migration()\`, \`_render_migration_file()\`, \`_render_column_def()\` | Emits syntactically valid Python source text with dependencies metadata |
| \`aquilia.models.migration_dsl\` | Updated \`_format_default()\` | Unwraps Enum defaults to scalar Python literals in DSL column definitions |
| \`aquilia.models.fields_module\` | Updated \`Index.__init__()\` | Safely normalizes string or tuple \`fields\` parameters into string lists |
| \`aquilia.models.index\` | Updated \`_PostgresOnlyIndex.__init__()\` | Normalizes index column inputs across PostgreSQL index variants |
`,
    "migration_dsl_generator_fixes.md": `# Migration DSL Generator Overhaul

## Overview

In Aquilia v1.3.8, the Migration DSL Generator (\`aquilia.models.migration_gen\` and \`aquilia.models.schema_snapshot\`) underwent a comprehensive architectural overhaul. The generator is responsible for transforming model definitions into schema snapshots (\`create_snapshot()\`), calculating diffs (\`diff_to_operations()\`), and emitting human-readable, executable Python DSL migration files (\`generate_dsl_migration()\`).

---

## Technical Details

### 1. Character-Split Index Column Normalization

#### Previous Behavior
When an index was declared using a single string or when \`Index.deconstruct()\` returned \`fields: "token"\`, \`schema_snapshot.py\` iterated over the string as a sequence (\`list("token")\`), splitting column names into character arrays:

\`\`\`python
# Old Output (v1.3.7 Bug)
CreateIndex(
    name='idx_email_verification_t_o_k_e_n',
    table='email_verification',
    columns=['t', 'o', 'k', 'e', 'n'],
    unique=False,
)
\`\`\`

#### New Implementation
\`Index.__init__()\` and \`_PostgresOnlyIndex.__init__()\` normalize \`fields\` arguments upon instantiation. Furthermore, \`create_snapshot()\` inspects and normalizes string column names into strict \`list[str]\` objects before building auto index names or emitting DSL \`CreateIndex\` operations:

\`\`\`python
# New Output (v1.3.8)
CreateIndex(
    name='idx_email_verification_token',
    table='email_verification',
    columns=['token'],
    unique=False,
)
\`\`\`

---

### 2. Strict Foreign Key Target Table Resolution

#### Previous Behavior
When a \`ForeignKey\` field referenced a model using a string class name (e.g. \`ForeignKey("UserModel")\`), \`_serialize_field()\` fell back to lowercasing the raw string (\`"usersmodel"\`), ignoring \`UserModel._meta.table_name\` (\`"users"\`):

\`\`\`python
# Old Output (v1.3.7 Bug)
C.foreign_key("user_id", "usersmodel", "id")
\`\`\`

#### New Implementation
\`_resolve_target_table(to_ref, model_classes)\` resolves target table names through a multi-pass lookup pipeline:
1. Inspects \`to_ref._meta.table_name\` if \`to_ref\` is a \`Model\` subclass.
2. Scans \`model_classes\` passed to snapshot creation for matching \`__name__\` or \`_meta.table_name\`.
3. Queries \`ModelRegistry\` for registered model class metadata.
4. Applies a PascalCase-to-snake_case pluralization fallback (\`"UserModel"\` -> \`"users"\`).

\`\`\`python
# New Output (v1.3.8)
C.foreign_key("user_id", "users", "id", col_type="VARCHAR(36)")
\`\`\`

---

### 3. Model Attribute Name to Database Column Name Resolution

#### Previous Behavior
When indexes or constraints referenced model attribute names (e.g. \`Index(fields=["user"])\` or \`UniqueConstraint(fields=["user", "role"])\`), the generator emitted the Python attribute name (\`"user"\`) rather than the database column name (\`"user_id"\`):

\`\`\`python
# Old Output (v1.3.7 Bug)
CreateIndex(name='idx_user_roles_user', table='user_roles', columns=['user'])
AddConstraint(table='user_roles', constraint_sql='CONSTRAINT "user_role_unique" UNIQUE ("user", "role")')
\`\`\`

#### New Implementation
\`_resolve_db_column_name(model_cls, field_or_name)\` inspects \`model_cls._fields\` descriptors. If the field is a \`ForeignKey\` or has a custom \`column_name\`/\`db_column\` attribute, it extracts the actual database column name (\`"user"\` -> \`"user_id"\`):

\`\`\`python
# New Output (v1.3.8)
CreateIndex(name='idx_user_roles_user_id', table='user_roles', columns=['user_id'])
AddConstraint(table='user_roles', constraint_sql='CONSTRAINT "user_role_unique" UNIQUE ("user_id", "role")')
\`\`\`

---

### 4. Foreign Key SQL Type Inference Consistency

#### Previous Behavior
If a foreign key target model (e.g., \`UserModel\` with UUID primary key \`id = UUIDField(primary_key=True)\`) was un-resolved at field initialization time, \`_field_to_sql_type()\` returned \`"INTEGER"\` for one model and \`"VARCHAR(36)"\` for another, causing column definition type mismatches in generated migrations.

#### New Implementation
\`_field_to_sql_type(fld, model_classes=model_classes)\` dynamically inspects \`model_classes\` and \`ModelRegistry\` during snapshot creation to determine the exact primary key SQL type of the target model (\`"VARCHAR(36)"\`), emitting \`col_type="VARCHAR(36)"\` consistently across all referencing foreign key column definitions.
`,
    "model_dependency_ordering.md": `# Topological Model Dependency Ordering

## Overview

In Aquilia v1.3.8, \`diff_to_operations()\` implements post-order topological dependency sorting (\`_topologically_sort_models()\`) for \`CreateModel\` operations in generated migrations.

---

## The Problem

Before v1.3.8, added models in a migration diff were processed in simple alphabetical order. For example, given the models:

- \`Post\` (table \`posts\`)
- \`UserEmailVerificationModel\` (table \`email_verification\`, referencing \`users.id\`)
- \`UserModel\` (table \`users\`, primary key \`id\`)
- \`UserRoleModel\` (table \`user_roles\`, referencing \`users.id\`)

Alphabetical iteration produced \`CreateModel\` operations in the following sequence:

1. \`CreateModel(name='Post', table='posts', ...)\`
2. \`CreateModel(name='UserEmailVerificationModel', table='email_verification', fields=[C.foreign_key("user_id", "users", "id"), ...])\`
3. \`CreateModel(name='UserModel', table='users', ...)\`
4. \`CreateModel(name='UserRoleModel', table='user_roles', fields=[C.foreign_key("user_id", "users", "id"), ...])\`

When the migration runner attempted to execute \`CREATE TABLE email_verification\` on PostgreSQL or SQLite with foreign key enforcement active, the execution failed with:

\`\`\`
[MIGRATION_FAILED] Cannot add foreign key constraint: table 'users' does not exist
\`\`\`

---

## Architectural Implementation

### Dependency Graph Construction & Topological Sorting

\`_topologically_sort_models(added_models, models_data)\` constructs a directed dependency graph where:
- Each node represents an added model name.
- A directed edge A -> B indicates that Model A contains a \`ForeignKey\` referencing Model B's database table (B != A).

\`\`\`python
def _topologically_sort_models(
    added_models: list[str],
    models_data: dict[str, Any],
) -> list[str]:
    if len(added_models) <= 1:
        return added_models

    table_to_model = {}
    for m_name in added_models:
        m_info = models_data.get(m_name, {})
        t_name = m_info.get("table", m_name.lower())
        table_to_model[t_name] = m_name

    deps: dict[str, set[str]] = {m: set() for m in added_models}
    for m_name in added_models:
        m_info = models_data.get(m_name, {})
        fields = m_info.get("fields", {})
        for f_info in fields.values():
            ref = f_info.get("references")
            if ref and isinstance(ref, dict):
                ref_table = ref.get("table")
                if ref_table and ref_table in table_to_model:
                    target_m = table_to_model[ref_table]
                    if target_m != m_name:
                        deps[m_name].add(target_m)

    sorted_models: list[str] = []
    visited: set[str] = set()
    visiting: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            return
        if node not in visited:
            visiting.add(node)
            for dep in sorted(deps[node]):
                visit(dep)
            visiting.remove(node)
            visited.add(node)
            sorted_models.append(node)

    for m_name in sorted(added_models):
        if m_name not in visited:
            visit(m_name)

    return sorted_models
\`\`\`

---

## Execution Guarantees

1. **Dependency First**: Tables referenced by foreign keys (\`users\`) are guaranteed to appear in \`CreateModel\` operations before tables that reference them (\`email_verification\`, \`user_roles\`).
2. **Cycle Safety**: Self-referential models (Model A -> Model A) ignore self-loops, and circular dependencies (Model A -> Model B -> Model A) are broken gracefully without recursion errors.
3. **Determinism**: Ties are broken using sorted model names, ensuring byte-for-byte deterministic migration file generation across platforms.
`,
    "orm_field_deconstruct_serialization.md": `# ORM Field Deconstruction & Snapshot Serialization

## Overview

Aquilia v1.3.8 fixes scalar default unwrapping during model field serialization (\`_serialize_field()\`), snapshot generation (\`create_snapshot()\`), and DSL column rendering (\`_render_column_def()\`).

---

## Technical Details

### 1. Enum Default Value Unwrapping

#### Previous Behavior
When a model field used an \`EnumField\` or \`Enum\` default (e.g. \`status = EnumField(enum_class=UserStatus, default=UserStatus.ACTIVE)\`), \`_serialize_field()\` failed to serialize the raw Enum instance into JSON, falling back to string representation:

\`\`\`python
# Snapshot JSON (v1.3.7 Bug)
"default": "<UserStatus.ACTIVE: 'active'>"

# Migration DSL (v1.3.7 Bug - SyntaxError line 61)
status = C.text("status", default=<UserStatus.ACTIVE: 'active'>)
\`\`\`

When Python loaded the migration file, \`ast.parse()\` and \`importlib\` failed with \`SyntaxError: invalid syntax\`.

#### New Implementation
\`_serialize_field()\` now unwrap \`Enum\` defaults through \`fld.to_db(val)\` or by extracting \`.value\` / \`.name\` directly:

\`\`\`python
if hasattr(fld, "default") and fld.default is not None:
    if fld.default is not UNSET:
        val = fld.default
        if isinstance(fld, EnumField):
            val = fld.to_db(val)
        elif isinstance(val, Enum):
            val = val.name if getattr(fld, "store_name", False) else val.value

        try:
            json.dumps(val)
            info["default"] = val
        except (TypeError, ValueError):
            info["default"] = str(val)
\`\`\`

And \`_format_default()\` in \`migration_dsl.py\` formats Enum instances into Python string literals:

\`\`\`python
# Snapshot JSON (v1.3.8)
"default": "active"

# Migration DSL (v1.3.8 - Valid Python)
C.text("status", default='active')
\`\`\`

---

### 2. Snapshot Diffing & Column Definition Generation

\`_snapshot_field_to_column_def()\` converts serialized field dictionaries back into \`ColumnDef\` objects for operation rendering. In v1.3.8, \`_render_column_def()\` formats column helper calls matching the target database column definition:

\`\`\`python
# Primary Key Column
C.varchar("id", 36, primary_key=True)

# Foreign Key Column
C.foreign_key("user_id", "users", "id", null=True, on_delete="CASCADE", col_type="VARCHAR(36)")

# Varchar Column with Default
C.varchar("email", 254, unique=True)
\`\`\`
`,
    "bugfixes.md": `# Comprehensive Bug Fixes in v1.3.8

This document details all 19 bug fixes and correctness improvements implemented in Aquilia v1.3.8.

---

## 1. Character-Split Index Columns (Critical)

- **Previous Behavior**: \`Index(fields="token")\` or tuple inputs converted column strings to character arrays (\`columns=['t', 'o', 'k', 'e', 'n']\`).
- **Root Cause**: \`Index.deconstruct()\` returned \`fields: "token"\`. Snapshot logic called \`list("token")\`, splitting the string into single characters.
- **New Behavior**: Strictly normalizes string fields into string lists (\`columns=['token']\`).

---

## 2. Foreign Key Target Table Name Mismatch (Critical)

- **Previous Behavior**: Foreign key references emitted raw low-cased class stubs (\`C.foreign_key("user_id", "usersmodel", "id")\`).
- **Root Cause**: Unbound string target model names (\`"UserModel"\`) bypassed model registry resolution and fell back to \`to.lower()\`.
- **New Behavior**: \`_resolve_target_table()\` queries model classes, metadata, and registry to resolve actual database table names (\`"users"\`).

---

## 3. Un-serializable Enum Default Repr Syntax Error (Critical)

- **Previous Behavior**: \`default=<UserStatus.ACTIVE: 'active'>\` emitted in migration DSL, causing \`SyntaxError\` on import.
- **Root Cause**: \`_serialize_field()\` stringified Enum objects when \`json.dumps()\` failed instead of unwrapping \`.value\` or calling \`to_db()\`.
- **New Behavior**: Unwraps Enum default instances to scalar primitives (\`default='active'\`).

---

## 4. Wrong Index Name Generation (High)

- **Previous Behavior**: \`_auto_index_name\` produced corrupted names like \`idx_email_verification_t_o_k_e_n\`.
- **Root Cause**: \`_auto_index_name\` joined character-split arrays (\`"_".join(['t', 'o', 'k', 'e', 'n'])\`).
- **New Behavior**: Uses normalized column lists, producing \`idx_email_verification_token\`.

---

## 5. Index Column Field vs. DB Column Name Mismatch (High)

- **Previous Behavior**: \`Index(fields=["user"])\` produced \`columns=['user']\` instead of \`columns=['user_id']\`.
- **Root Cause**: Generator serialized model attribute names directly without mapping through descriptor column names.
- **New Behavior**: \`_resolve_db_column_name()\` maps model attributes to database column names (\`"user"\` -> \`"user_id"\`).

---

## 6. Unique Constraint Field vs. DB Column Name Mismatch (High)

- **Previous Behavior**: \`UniqueConstraint(fields=["user", "role"])\` produced \`UNIQUE ("user", "role")\`.
- **Root Cause**: Constraint fields were not resolved to underlying database column names.
- **New Behavior**: Maps constraint fields to database column names, producing \`UNIQUE ("user_id", "role")\`.

---

## 7. Foreign Key Column Type Inference Inconsistency (High)

- **Previous Behavior**: Foreign key column types defaulted to \`"INTEGER"\` on some models and \`"VARCHAR(36)"\` on others.
- **Root Cause**: \`_field_to_sql_type()\` failed to inspect target model primary key types for string references.
- **New Behavior**: Dynamically resolves target model primary key types (\`"VARCHAR(36)"\`), ensuring type consistency across models.

---

## 8. Table Naming Inconsistency Across Model References (High)

- **Previous Behavior**: String reference targets were inconsistently resolved depending on model declaration order.
- **Root Cause**: Lack of unified target table resolution pipeline.
- **New Behavior**: Unified target table resolution pipeline guarantees consistent table names regardless of declaration order.

---

## 9. Missing Foreign Key Metadata (Medium)

- **Previous Behavior**: \`on_delete\`, \`on_update\`, and \`null=True\` were omitted from generated DSL foreign key calls.
- **Root Cause**: Generator omitted default options from rendered \`C.foreign_key()\` argument strings.
- **New Behavior**: \`_render_column_def()\` renders all non-default foreign key metadata.

---

## 10. Reverse Relation Metadata Leakage in DDL (Medium)

- **Previous Behavior**: Reverse relation descriptors populated metadata into snapshot field maps.
- **Root Cause**: Descriptor scanning did not filter out virtual relation properties.
- **New Behavior**: Virtual relation properties are handled cleanly without polluting DDL operation definitions.

---

## 11. Field Options & Timestamp Metadata Loss (Medium)

- **Previous Behavior**: \`auto_now\` and \`auto_now_add\` flags were omitted from snapshot metadata.
- **Root Cause**: \`_serialize_field()\` did not record timestamp flags.
- **New Behavior**: Captures timestamp metadata cleanly in snapshot definitions.

---

## 12. Case-Insensitive Unique Constraint DDL Generation (Medium)

- **Previous Behavior**: Case-insensitive fields emitted broken constraint DDL.
- **Root Cause**: \`CIEmailField\` expression unique constraints were formatted without parenthesis escaping.
- **New Behavior**: Properly compiles schema expressions for case-insensitive unique constraints.

---

## 13. Redundant Column-Level Uniqueness (Medium)

- **Previous Behavior**: Fields with table-level unique constraints also emitted \`unique=True\` on column definitions.
- **Root Cause**: Generator did not check table-level constraint duplicates.
- **New Behavior**: Suppresses redundant column-level \`unique=True\` when expression-based unique constraints exist.

---

## 14. Arbitrary Model Dependency Creation Ordering (Critical)

- **Previous Behavior**: \`CreateModel\` operations were emitted in alphabetical order, causing foreign key creation crashes.
- **Root Cause**: Added models list was iterated without topological dependency analysis.
- **New Behavior**: \`_topologically_sort_models()\` sorts \`CreateModel\` operations dependency-first.

---

## 15. Migration Revision Dependency Metadata Omission (Medium)

- **Previous Behavior**: \`Meta.dependencies\` was omitted from generated migration source text.
- **Root Cause**: Generator did not collect previous migration revision IDs.
- **New Behavior**: Scans \`migrations_dir\` and includes \`dependencies = ['<prev_rev>']\` in \`Meta\`.

---

## 16. State Operation Support (Low)

- **Previous Behavior**: Migration DSL did not support custom SQL state operations cleanly.
- **Root Cause**: Lack of \`RunSQL\` operation rendering.
- **New Behavior**: Full support for \`RunSQL\` rendering and execution.

---

## 17. Field Options Preservation (Low)

- **Previous Behavior**: Options like \`max_digits\` and \`decimal_places\` were lost during snapshot roundtripping.
- **Root Cause**: Missing parameter serialization in \`_serialize_field()\`.
- **New Behavior**: Preserves all field parameters cleanly.

---

## 18. Nullable Foreign Key Definition Rendering (Low)

- **Previous Behavior**: Nullable foreign keys emitted \`null=False\` in rendered DSL column definitions.
- **Root Cause**: \`nullable\` property was not passed to \`C.foreign_key()\`.
- **New Behavior**: Emits \`C.foreign_key(..., null=True)\` when \`nullable=True\`.

---

## 19. Postgres Index Abstraction Support (Low)

- **Previous Behavior**: Custom Postgres index variants (\`GinIndex\`, \`GistIndex\`) dropped \`condition\` or \`opclasses\`.
- **Root Cause**: Generator omitted index options in snapshot dict.
- **New Behavior**: Preserves condition and operator class overrides in index snapshot metadata.
`,
    "migration.md": `# Aquilia v1.3.8 Migration Guide

## Upgrade Overview

Aquilia v1.3.8 is a **zero-breaking-change patch release** focused on ORM Migration DSL Generator correctness, topological model dependency sorting, and snapshot serialization robustness.

All existing code, model definitions, and applied database migrations remain 100% compatible with v1.3.8.

---

## Upgrade Steps

### 1. Upgrade Package Version

Upgrade Aquilia in your environment via \`pip\` or \`uv\`:

\`\`\`bash
pip install --upgrade aquilia==1.3.8
\`\`\`

Or using \`uv\`:

\`\`\`bash
uv add aquilia==1.3.8
\`\`\`

### 2. Verify Generated Migrations

If you previously generated migration DSL files with v1.3.7 that experienced syntax errors (such as \`default=<UserStatus.ACTIVE: 'active'>\`) or character-split indexes (\`columns=['t', 'o', 'k', 'e', 'n']\`), delete those un-applied migration files and re-run:

\`\`\`bash
aq db makemigrations
\`\`\`

The newly generated migration files will automatically incorporate:
- Topological model creation order (\`users\` created before \`email_verification\`).
- Resolved target table names (\`"users"\` instead of \`"usersmodel"\`).
- Resolved database column names (\`"user_id"\` instead of \`"user"\`).
- Clean scalar Enum defaults (\`default='active'\`).
- Valid index column arrays (\`columns=['token']\`).

### 3. Apply Pending Migrations

Execute the migration runner:

\`\`\`bash
aq db migrate
\`\`\`

---

## Compatibility Summary

| Component | Status | Notes |
|---|---|---|
| Model Definitions | 100% Compatible | No changes required to \`Model\` or \`Field\` declarations. |
| Existing Applied Migrations | 100% Compatible | Applied migration files in \`migrations/\` continue to work without modification. |
| Migration Runner | Enhanced | Fully supports topological model execution and dependencies metadata. |
| Database Engines | 100% Compatible | Verified against SQLite, PostgreSQL, MySQL, and Oracle. |
`
  },
  "1.3.7": {
    "README.md": `# Aquilia v1.3.7 Release Notes — "Thread Sentinel"

Aquilia v1.3.7 introduces **Thread-Safe Model Registration & Descriptor Access**, **Type-Annotated Nested Contract Facets**, **Multi-Dialect Database Field Conversions**, and **Comprehensive 10-Point Standard Docstrings** across core Contract primitives.

Before this release, concurrent multi-threaded execution could experience subtle race conditions when registering models or accessing manager descriptors on model subclasses. Furthermore, imprinting contracts back into ORM models containing \`EnumField\` or \`CompositeField\` raised a \`TypeError\` due to missing dialect parameters, and nested contracts required verbose \`NestedContractFacet\` explicit declarations rather than standard Python type hints.

This release addresses all concurrency vulnerabilities with re-entrant locking (\`threading.RLock\`) in \`ModelRegistry\`, implements thread-isolated descriptor binding copies in \`BaseManager\`, enables type hint introspection for \`NestedContractFacet\`, extends dialect support across all ORM field conversions, and adds industry-grade 10-point documentation to the entire Contracts subsystem.

---

## Table of Contents

1. [Thread-Safe Model Registry](thread_safe_registry.md)
   - \`ModelRegistry\` thread safety via \`threading.RLock\`
   - Re-entrant locking strategy across registration, lookup, reset, and DDL
   - Reverse relation cache invalidation (\`_clear_reverse_relation_caches()\`)
2. [Manager Descriptor Thread Safety](manager_descriptor_thread_safety.md)
   - Subclass manager lookup isolation via bound shallow copies (\`copy.copy\`)
   - Strict descriptor access rules (\`ManagerInstanceAccessFault\`)
3. [Nested Contract Type Hint Annotations](nested_contract_annotations.md)
   - Python type hint introspection for \`NestedContractFacet\`
   - Support for \`NestedContractFacet[SubContract]\`, \`SubContract\`, and \`list[...]\`
4. [Multi-Dialect Field Conversions](field_dialect_support.md)
   - \`dialect\` parameter support in \`EnumField.to_db()\` and \`CompositeField.to_db()\`
   - Seamless contract imprinting (\`contract.imprint()\`) across SQLite, Postgres, MySQL, and Oracle
5. [Contract Standardized Docstrings](contract_docstrings.md)
   - 10-point industry docstring coverage across \`facets.py\`, \`exceptions.py\`, \`integration.py\`, \`lenses.py\`, \`pipeline.py\`, \`projections.py\`, \`schema.py\`, and \`ward.py\`
6. [Bug Fixes](bugfixes.md)
   - Critical fixes in model imprinting, registry concurrency, and manager descriptor binding
7. [Migration Guide](migration.md)
   - Upgrade checklist, compatibility notes, and zero-breaking-change guarantees

---

## Highlights

### Thread-Safe ModelRegistry & Reverse-Relation Invalidation

All global model registry operations are now fully thread-safe, guarded by a re-entrant \`threading.RLock\`. Additionally, registering new models or resetting the registry automatically invalidates lazily-cached reverse foreign key lookups across all registered models.

\`\`\`python
import threading
from aquilia.models import ModelRegistry

def worker_thread(model_cls):
    # Safe concurrent registration across worker threads
    ModelRegistry.register(model_cls)
\`\`\`

### Thread-Isolated Subclass Managers

\`BaseManager.__get__()\` now creates a thread-isolated bound shallow copy when accessed on model subclasses, ensuring concurrent queries on inherited managers never corrupt shared manager state.

\`\`\`python
class BaseItem(Model):
    objects = Manager()

class ConcreteItem(BaseItem):
    pass

# Accessing SubModel.objects dynamically binds to SubModel safely in multi-threaded environments
items = await ConcreteItem.objects.all()
\`\`\`

### Type-Annotated Nested Contracts

Declare nested contract structures cleanly using standard Python type annotations. \`ContractMeta\` automatically wraps direct contract classes or \`NestedContractFacet[...]\` annotations.

\`\`\`python
class NameContract(Contract):
    first_name: typing.Annotated[str, Facet.text(min_length=1) >> strip]
    last_name: typing.Annotated[str, Facet.text(min_length=1) >> strip]

class UserRegistrationContract(Contract[UserModel]):
    # Modern Python type annotation syntax:
    name: NameContract
    aliases: list[NameContract]
\`\`\`

### Multi-Dialect Field Support in Contract Imprinting

\`EnumField.to_db()\` and \`CompositeField.to_db()\` now accept the \`dialect\` keyword argument (defaulting to \`"sqlite"\`), preventing runtime \`TypeError\` exceptions during \`contract.imprint()\`.

\`\`\`python
field = EnumField(enum_class=UserStatus, store_name=False)
field.to_db(UserStatus.ACTIVE, dialect="postgresql")  # -> 'active'
\`\`\`

---

## Summary of Changes

| Subsystem | Change | Impact |
|---|---|---|
| \`aquilia.models.registry\` | \`threading.RLock\` guarding all registry methods; reverse relation cache invalidation | Prevents race conditions during concurrent model registration & reload |
| \`aquilia.models.manager\` | \`BaseManager.__get__\` creates bound shallow copies for subclasses | Guarantees thread isolation when accessing managers on derived models |
| \`aquilia.models.fields\` | \`EnumField\` & \`CompositeField\` accept \`dialect\` in \`to_db()\` | Fixes contract \`imprint()\` crashes on models with Enum/Composite fields |
| \`aquilia.contracts\` | \`ContractMeta\` introspects type hints for \`NestedContractFacet\` | Allows clean Python type hint syntax for nested contract definitions |
| \`aquilia.contracts\` | 10-point standard docstrings across all facet & core contract modules | Full IDE intellisense, architectural clarity, and documentation integrity |

Check the [Migration Guide](migration.md) for full details on upgrading to v1.3.7.
`,
    "thread_safe_registry.md": `# Thread-Safe ModelRegistry & Cache Invalidation

Aquilia v1.3.7 refactors \`ModelRegistry\` (\`aquilia.models.registry.ModelRegistry\`) to introduce **full thread safety** via a re-entrant lock (\`threading.RLock\`) and automated **reverse-relation cache invalidation**.

---

## Why It Changed

In multi-threaded ASGI server configurations, worker threads or background tasks may dynamically import modules, execute testing fixtures, or register models concurrently. 

Previously, \`ModelRegistry\` maintained shared dictionaries (\`_models\` and \`_app_models\`) without thread synchronization:
- Concurrent calls to \`ModelRegistry.register()\` during app startup or dynamic module loading could cause dictionary mutation race conditions (\`RuntimeError: dictionary changed size during iteration\`).
- Foreign key resolution (\`_resolve_relations()\`) running in one thread while another registered a new model could lead to incomplete or corrupted foreign key mapping.
- Models lazily cached their reverse foreign key relationships (\`_reverse_fk_cache\` and \`_reverse_relation_cache\`). When test suites or dynamic reloads registered new models pointing back to existing models, the existing models held onto stale, un-updated reverse relationship caches.

---

## Architecture & Implementation

### 1. Re-Entrant Lock Guard (\`threading.RLock\`)

\`ModelRegistry\` now owns a class-level \`_lock = threading.RLock()\`. Re-entrant locking ensures that nested registry calls (e.g. \`register()\` calling \`_resolve_relations()\`, which queries registered models) can acquire the lock on the same thread without deadlocks.

Thread locks guard every public and internal operation:
- \`ModelRegistry.register(model_cls)\`
- \`ModelRegistry.reset()\`
- \`ModelRegistry.set_database(db)\`
- \`ModelRegistry.get_database()\`
- \`ModelRegistry.get_models(app_label)\`
- \`ModelRegistry.get_model(name, app_label)\`
- \`ModelRegistry._resolve_relations()\`
- \`ModelRegistry.create_tables(db, app_label)\`
- \`ModelRegistry.drop_tables(db, app_label)\`

\`\`\`python
class ModelRegistry:
    _models: dict[str, type[Model]] = {}
    _db: AquiliaDatabase | None = None
    _app_models: dict[str, dict[str, type[Model]]] = {}
    _lock: threading.RLock = threading.RLock()

    @classmethod
    def register(cls, model_cls: type[Model]) -> None:
        with cls._lock:
            # 1. Update global lookups
            # 2. Invalidate reverse relation caches on existing models
            # 3. Resolve pending string foreign keys
            ...
\`\`\`

### 2. Reverse Relation Cache Invalidation

When a new model is registered or the registry is reset, \`ModelRegistry\` automatically calls \`_clear_reverse_relation_caches()\` on all registered \`Model\` subclasses.

\`\`\`python
# In aquilia.models.base.Model
@classmethod
def _clear_reverse_relation_caches(cls) -> None:
    """Clear cached reverse FK references and relation maps on this class."""
    cls._reverse_fk_cache = None
    cls._reverse_relation_cache = None
\`\`\`

---

## Code Examples

### Multi-Threaded Model Registration (Concurrent Safety)

\`\`\`python
import threading
from aquilia.models import Model, ModelRegistry, fields

def define_and_register(name: str):
    class DynamicUser(Model):
        table = f"users_{name}"
        username = fields.TextField()

    # Thread-safe registration under high concurrency
    ModelRegistry.register(DynamicUser)

threads = [
    threading.Thread(target=define_and_register, args=(f"worker_{i}",))
    for i in range(20)
]
for t in threads:
    t.start()
for t in threads:
    t.join()

assert len(ModelRegistry.get_models()) >= 20
\`\`\`

---

## Performance Considerations

The performance impact of \`threading.RLock\` acquisition for model lookups is negligible (sub-microsecond), while completely eliminating data race crashes in multi-threaded application servers or test runners.
`,
    "manager_descriptor_thread_safety.md": `# Manager Descriptor Thread Safety & Subclass Binding

Aquilia v1.3.7 refactors \`BaseManager\` (\`aquilia.models.manager.BaseManager\`) descriptor access to guarantee **thread isolation** when accessing model managers across derived classes.

---

## Why It Changed

Model managers in Aquilia are attached as descriptors to model classes (e.g. \`objects = Manager()\`). In Python's descriptor protocol, accessing \`Model.objects\` calls \`BaseManager.__get__(self, instance, owner)\`.

Prior to v1.3.7:
- When a subclass inherited a manager from a base model (or when multiple worker threads accessed \`SubModel.objects\`), \`__get__\` re-assigned \`self._model_cls = owner\` directly on the shared \`BaseManager\` instance.
- In multi-threaded environments, if Thread A accessed \`ParentModel.objects\` while Thread B accessed \`ChildModel.objects\`, a race condition occurred where \`_model_cls\` on the shared manager instance could be mutated while Thread A was building a query. This caused queries in Thread A to target \`ChildModel\` instead of \`ParentModel\`.

---

## Architecture & Implementation

### 1. Bound Shallow Copy Protocol

In \`BaseManager.__get__()\`:
1. Instance access check: If \`instance is not None\`, raises \`ManagerInstanceAccessFault\` (blocking \`user.objects\` access).
2. Owner matching: If \`owner\` matches \`self._model_cls\` or \`self._model_cls\` is \`None\`, \`self._model_cls\` is set to \`owner\` and \`self\` is returned.
3. Subclass isolation: If accessed from a subclass (\`owner != self._model_cls\`), \`BaseManager.__get__()\` returns a **shallow copy** (\`copy.copy(self)\`) bound to \`owner\`.

\`\`\`python
def __get__(self: M, instance: Any, owner: type) -> M:
    if instance is not None:
        from aquilia.faults.domains import ManagerInstanceAccessFault
        raise ManagerInstanceAccessFault(
            f"Manager '{self.__class__.__name__}' is non-accessible from "
            f"'{instance.__class__.__name__}' instance. Access it from the class instead."
        )

    if self._model_cls is None or self._model_cls is owner:
        self._model_cls = cast("type[TModel]", owner)
        return self

    # Subclass or different owner access -- return a bound copy for thread safety
    bound = copy.copy(self)
    bound._model_cls = cast("type[TModel]", owner)
    return bound
\`\`\`

---

## Code Examples

### Subclass Manager Access in Multi-Threaded Environments

\`\`\`python
import asyncio
from aquilia.models import Model, Manager, fields

class BaseContent(Model):
    table = "base_contents"
    title = fields.TextField()
    objects = Manager()

class Article(BaseContent):
    table = "articles"
    body = fields.TextField()

class Video(BaseContent):
    table = "videos"
    duration = fields.IntField()

async def concurrent_queries():
    # Concurrently query derived models without cross-thread manager state corruption
    article_task = asyncio.create_task(Article.objects.all())
    video_task = asyncio.create_task(Video.objects.all())
    await asyncio.gather(article_task, video_task)
\`\`\`

---

## Behavioral Guarantees

- **Thread Safety**: Accessing managers across inheritance hierarchies produces distinct, thread-bound descriptors.
- **Instance Protection**: Accessing \`instance.objects\` continues to raise \`ManagerInstanceAccessFault\` deterministically.
`,
    "nested_contract_annotations.md": `# Type-Annotated Nested Contract Facets

Aquilia v1.3.7 updates \`ContractMeta\` (\`aquilia.contracts.annotations\`) and \`NestedContractFacet\` to support **standard Python type hint annotations** for nested contracts and nested contract lists.

---

## Why It Changed

Previously, defining nested contracts required explicit facet assignment syntax:

\`\`\`python
class NameContract(Contract):
    first_name: str
    last_name: str

class UserRegistrationContract(Contract):
    # Old explicit syntax:
    name = NestedContractFacet(NameContract)
\`\`\`

While functional, this syntax did not leverage standard Python type annotations (\`typing.Annotated\` or direct class annotations) and required developers to remember two distinct ways of declaring fields on Contracts.

---

## Supported Type Hint Syntaxes

In v1.3.7, \`ContractMeta\` introspects class type annotations and automatically converts nested contract annotations into \`NestedContractFacet\` instances.

### 1. Direct Contract Class Annotation

\`\`\`python
class AuditUserNameContract(Contract):
    first_name: typing.Annotated[str, Facet.text(min_length=1) >> strip]
    last_name: typing.Annotated[str, Facet.text(min_length=1) >> strip]

class RegistrationContract(Contract):
    # Direct Contract class annotation
    name: AuditUserNameContract
\`\`\`

### 2. Explicit \`NestedContractFacet[SubContract]\` Annotation

\`\`\`python
from aquilia.contracts import Contract, NestedContractFacet

class RegistrationContract(Contract):
    # Parameterized NestedContractFacet type annotation
    name: NestedContractFacet[AuditUserNameContract]
\`\`\`

### 3. Nested Contract Lists

\`\`\`python
class OrganizationContract(Contract):
    # List of nested contracts
    members: list[AuditUserNameContract]
    # Or parameterized list:
    teams: list[NestedContractFacet[TeamContract]]
\`\`\`

---

## How It Works Internally

During \`ContractMeta.__new__()\` processing:
1. \`ContractMeta\` iterates over \`__annotations__\`.
2. If an annotation target is a subclass of \`Contract\` (or a \`typing.get_origin()\` matching \`list\` with a \`Contract\` argument), \`ContractMeta\` wraps the target into a \`NestedContractFacet(target_contract, many=is_list)\`.
3. The resulting facet is attached to \`_all_facets\` on the contract class, supporting full validation, sealing, and model imprinting (\`contract.imprint()\`).

---

## Full Code Example

\`\`\`python
import typing
import uuid
from aquilia.contracts import Contract, Facet, NestedContractFacet, ward
from aquilia.contracts.transforms import strip, lower
from aquilia.models import Model
from aquilia.models.fields import UUIDField, TextField

class AddressContract(Contract):
    street: typing.Annotated[str, Facet.text(min_length=1) >> strip]
    city: typing.Annotated[str, Facet.text(min_length=1) >> strip]
    zip_code: typing.Annotated[str, Facet.text(min_length=5, max_length=10) >> strip]

class UserProfileContract(Contract):
    address: AddressContract
    previous_addresses: list[AddressContract]
    email: typing.Annotated[str, Facet.email() >> strip >> lower]

# Sealing and validation work seamlessly:
contract = UserProfileContract(data={
    "address": {"street": "123 Main St", "city": "Metropolis", "zip_code": "10001"},
    "previous_addresses": [
        {"street": "456 Old Rd", "city": "Gotham", "zip_code": "10002"}
    ],
    "email": "USER@EXAMPLE.COM"
})

assert contract.is_sealed()
\`\`\`
`,
    "field_dialect_support.md": `# Multi-Dialect Field Conversion Support

Aquilia v1.3.7 updates \`EnumField.to_db()\` (\`aquilia.models.fields.enum_field\`) and \`CompositeField.to_db()\` (\`aquilia.models.fields.composite\`) to accept the \`dialect\` keyword parameter.

---

## Why It Changed

In the Aquilia ORM, all field classes derive from \`Field\` (\`aquilia.models.fields.base.Field\`), which defines the method signature:

\`\`\`python
def to_db(self, value: Any, dialect: str = "sqlite") -> Any:
    ...
\`\`\`

When contract data is imprinted back onto model instances (\`contract.imprint()\`) or when query engines compile SQL statements across different database backends (SQLite, PostgreSQL, MySQL, Oracle), the database driver invokes \`field.to_db(value, dialect=dialect)\`.

Previously:
- \`EnumField.to_db(self, value)\` and \`CompositeField.to_db(self, value)\` lacked the \`dialect\` parameter in their function signatures.
- Calling \`contract.imprint()\` on a model containing an \`EnumField\` or \`CompositeField\` resulted in a fatal \`TypeError\`:

\`\`\`text
TypeError: EnumField.to_db() got an unexpected keyword argument 'dialect'
\`\`\`

---

## What Changed

\`EnumField.to_db()\` and \`CompositeField.to_db()\` now explicitly include \`dialect: str = "sqlite"\` in their method signatures, matching \`Field.to_db()\`.

### Updated Signatures

\`\`\`python
# EnumField
def to_db(self, value: Any, dialect: str = "sqlite") -> Any:
    if value is None:
        return None
    if isinstance(value, self.enum_class):
        return value.name if self.store_name else value.value
    return value

# CompositeField
def to_db(self, value: Any, dialect: str = "sqlite") -> Any:
    if value is None:
        return None
    if self.strategy == "json":
        return json.dumps(value)
    return value
\`\`\`

---

## Code Examples

### Contract Imprinting with EnumField Models

\`\`\`python
import typing
from aquilia.contracts import Contract, Facet
from aquilia.models import Model
from aquilia.models.enums import TextChoices
from aquilia.models.fields import UUIDField, TextField, EnumField

class UserStatus(TextChoices):
    ACTIVE = "active", "Active"
    SUSPENDED = "suspended", "Suspended"

class UserModel(Model):
    table = "users"
    id = UUIDField(primary_key=True)
    name = TextField()
    status = EnumField(enum_class=UserStatus, default=UserStatus.ACTIVE)

class UserContract(Contract[UserModel]):
    name: typing.Annotated[str, Facet.text()]

    class Spec:
        model = UserModel

# Imprinting works seamlessly across all database dialects
contract = UserContract(data={"name": "Alice"})
assert contract.is_sealed()

user_model = contract.imprint()
assert user_model.status == UserStatus.ACTIVE
\`\`\`
`,
    "contract_docstrings.md": `# Standardized 10-Point Contract Docstrings

Aquilia v1.3.7 completes a major documentation standardization effort across the entire Contracts subsystem (\`aquilia.contracts\`).

Every Facet primitive in \`facets.py\` and core contract module (\`exceptions.py\`, \`integration.py\`, \`lenses.py\`, \`pipeline.py\`, \`projections.py\`, \`schema.py\`, \`ward.py\`) now carries a comprehensive 10-point industry-standard docstring.

---

## The 10-Point Standard Structure

Each public class and method in \`aquilia.contracts\` follows the exact 10-point documentation standard:

1. **Purpose**: High-level architectural role and intent.
2. **Lifecycle**: When and how the component is initialized, invoked, and destroyed.
3. **Execution Order**: Pre-conditions, pipeline step ordering, and post-conditions.
4. **Parameters**: Explicit type signatures, descriptions, and defaults for all arguments.
5. **Return Value**: Precise return types and behavior on success.
6. **Exceptions**: Exhaustive list of raised exceptions and failure conditions.
7. **Notes**: Design rationale, thread safety, and immutability notes.
8. **Edge Cases**: Empty inputs, \`None\` values, overflow handling, and boundary behavior.
9. **Internal Behaviour**: Key implementation details, private helpers, and cache interactions.
10. **Examples**: Executable doctests and real-world usage patterns.

---

## Affected Modules

Docstrings were added or expanded across the following files:

- \`aquilia/contracts/facets.py\` (all \`Facet\` subclasses including \`TextFacet\`, \`IntFacet\`, \`FloatFacet\`, \`DecimalFacet\`, \`BoolFacet\`, \`DateTimeField\`, \`DateField\`, \`TimeField\`, \`UUIDFacet\`, \`EmailFacet\`, \`URLFacet\`, \`EnumFacet\`, \`ListFacet\`, \`DictFacet\`, \`NestedContractFacet\`, \`BytesFacet\`, \`PathFacet\`, \`SecretFacet\`, \`MACAddressFacet\`).
- \`aquilia/contracts/exceptions.py\` (\`ContractFault\`, \`ContractValidationFault\`, \`ContractSealedFault\`, \`LensUnresolvedFault\`, \`NestingDepthFault\`, etc.).
- \`aquilia/contracts/integration.py\` (\`ContractIntegration\`, \`configure_contracts\`).
- \`aquilia/contracts/lenses.py\` (\`Lens\`, \`LensRegistry\`, \`mold_async\`).
- \`aquilia/contracts/pipeline.py\` (\`ContractPipeline\`, \`Sigil\`).
- \`aquilia/contracts/projections.py\` (\`Projection\`, \`ProjectionRegistry\`).
- \`aquilia/contracts/schema.py\` (\`ContractSchema\`, \`OpenAPIGenerator\`).
- \`aquilia/contracts/ward.py\` (\`ward\`, \`WardDescriptor\`).

---

## Benefits for Developers

- **Rich IDE Intellisense**: Hover documentation in VSCode, PyCharm, and language servers displays complete usage examples, parameter descriptions, and edge-case warnings.
- **Zero Ambiguity**: Clear distinction between sync validation (\`is_sealed()\`) and async validation (\`is_sealed_async()\`).
- **Architectural Traceability**: Deep insight into pipeline execution order and ward priority levels.
`,
    "bugfixes.md": `# Bug Fixes in Aquilia v1.3.7

Aquilia v1.3.7 resolves key issues identified in model field handling, multi-threaded model registry operations, manager descriptor subclass access, and test assertions.

---

## 1. Missing Dialect Parameter in EnumField & CompositeField

**The Bug:**
When calling \`contract.imprint()\` on a \`Contract\` bound to a \`Model\` containing an \`EnumField\` or \`CompositeField\`, the framework passed \`dialect="sqlite"\` to \`field.to_db()\`. Because \`EnumField.to_db()\` and \`CompositeField.to_db()\` did not accept \`dialect\`, Python raised a \`TypeError\`:

\`\`\`text
TypeError: EnumField.to_db() got an unexpected keyword argument 'dialect'
\`\`\`

**The Fix:**
Added \`dialect: str = "sqlite"\` to \`EnumField.to_db()\` and \`CompositeField.to_db()\`, aligning their method signatures with \`Field.to_db()\`.

---

## 2. Race Conditions in ModelRegistry Under Concurrency

**The Bug:**
In multi-threaded ASGI environments or test runners with parallel test execution, concurrent model registration or calls to \`ModelRegistry.reset()\` could cause data race mutations on \`_models\` and \`_app_models\`, occasionally causing \`RuntimeError: dictionary changed size during iteration\`.

**The Fix:**
Guarded all \`ModelRegistry\` operations with a re-entrant lock (\`threading.RLock\`). Added \`_clear_reverse_relation_caches()\` on \`Model\` to clear stale \`_reverse_fk_cache\` and \`_reverse_relation_cache\` entries when models are registered or reset.

---

## 3. Subclass Manager Descriptor Mutation Race Condition

**The Bug:**
Accessing \`SubModel.objects\` when \`objects = Manager()\` was inherited from \`ParentModel\` mutated \`self._model_cls\` directly on the shared \`BaseManager\` instance, causing cross-thread manager state pollution.

**The Fix:**
Refactored \`BaseManager.__get__()\` to return a bound shallow copy (\`copy.copy(self)\`) when accessed on a subclass or different owner.

---

## 4. Test Suite HMAC Secret Warning & Envelope Format Assertions

**The Bug:**
Bytecode cache and snapshot tests emitted HMAC secret warning messages during testing and failed envelope dictionary format assertions under strict test runs.

**The Fix:**
Updated test fixtures and envelope dict format assertions in \`tests/test_phase15_faults_security.py\` and \`tests/test_admin_v3.py\` to ensure clean test suite execution.
`,
    "migration.md": `# Migration Guide — Aquilia v1.3.7

Aquilia v1.3.7 is a **100% backward-compatible release**. All existing v1.3.6 applications will run without any code modifications or database migration requirements.

---

## Upgrading

Upgrade Aquilia using \`pip\`:

\`\`\`bash
pip install aquilia==1.3.7
\`\`\`

Or using Poetry / uv / pipenv:

\`\`\`bash
uv pip install aquilia==1.3.7
\`\`\`

---

## Upgrade Checklist

1. **Update Dependency**: Upgrade \`aquilia\` to \`1.3.7\`.
2. **Run Test Suite**: Run \`pytest\` across your application codebase to verify all existing contracts, models, and manager queries pass.
3. **Optional Code Cleanup**: Simplify nested contract declarations by replacing \`NestedContractFacet(SubContract)\` with clean Python type annotations \`name: SubContract\`.

---

## New Capabilities You Can Adopt

### 1. Python Type Annotations for Nested Contracts

\`\`\`python
# Before (v1.3.6 and earlier):
class UserContract(Contract):
    profile = NestedContractFacet(ProfileContract)

# New in v1.3.7:
class UserContract(Contract):
    profile: ProfileContract
\`\`\`

### 2. Multi-Threaded Model Operations

You can safely perform model registration, reset, and dynamic schema inspection across multiple threads without manual locking mechanisms.

---

## Verification

After upgrading, run your test suite:

\`\`\`bash
pytest
\`\`\`

All 7,410+ framework tests continue to pass seamlessly.
`
  },
  "1.3.6": {
    "README.md": `# Aquilia v1.3.6 Release Notes — "Artifact Forge"

Aquilia v1.3.6 introduces the **Artifact Subsystem** — a unified, production-grade infrastructure for all framework-generated metadata, build outputs, indexes, compiled representations, and caches.

Before this release, framework artifacts like template bytecode, discovery caches, and MCP indexes were scattered across different files, sometimes in an \`artifacts/\` directory at the project root, and sometimes wherever the subsystem decided. They used varying file formats and I/O strategies, which occasionally led to inconsistent atomic writes.

This release unifies all of this under a single \`.aquilia/artifacts/\` directory and a standardized \`ArtifactEnvelope\` JSON format. It guarantees atomic writes across all producers, introduces HMAC-SHA256 signatures for integrity (like the bytecode cache), and provides a new \`aq artifacts\` CLI to manage them.

The new artifact infrastructure is entirely transparent to most applications, but if you have tooling that expects artifacts in specific paths or legacy formats, you may need to update them.

---

## Table of Contents

1. [Artifact Store Deep Dive](artifact_store.md)
   - \`aquilia.artifacts\` architecture
   - \`ArtifactStore\` and \`ArtifactEnvelope\` APIs
   - \`JSONFileBackend\` atomic writes and HMAC-SHA256 signing
   - The \`aq artifacts\` CLI commands
2. [Unified Artifact Directory](unified_artifact_directory.md)
   - Consolidation from \`artifacts/\` to \`.aquilia/artifacts/\`
   - Complete directory layout
   - Configuration via \`[aquilia.artifacts]\` and \`AQUILIA_ARTIFACT_ROOT\`
3. [Producer Migrations](producer_migrations.md)
   - How \`DiscoveryCache\`, \`JSONBytecodeCache\`, etc. were migrated
   - Backward compatibility for legacy formats
4. [Bug Fixes](bugfixes.md)
   - Centralized atomic write guarantees
   - HMAC verification fixes
5. [Migration Guide](migration.md)
   - Upgrade checklist and breaking changes
   - Handling the path and format changes

---

## Highlights

### Unified Artifact Directory

All framework artifacts now live under \`.aquilia/artifacts/\` instead of scattering across the project root.

\`\`\`bash
# Before:
# artifacts/templates.bytecode.json
# artifacts/ws.json
# ...

# After:
# .aquilia/artifacts/templates.bytecode.json
# .aquilia/artifacts/ws.json
# .aquilia/artifacts/discovery_cache.json
# ...
\`\`\`

### The \`aq artifacts\` CLI

Manage all your framework artifacts with the new command group:

\`\`\`bash
aq artifacts status           # See what's on disk, sizes, schemas
aq artifacts verify           # Verify HMAC signatures and integrity
aq artifacts clean            # Remove stale/orphaned artifacts
\`\`\`

### Standardized Wire Format

Every artifact now uses the \`ArtifactEnvelope\` canonical format, providing clear schema versioning and traceability.

\`\`\`json
{
  "format": "aquilia-artifact",
  "artifact_type": "discovery_cache",
  "schema_version": "1.0",
  "key": "main",
  "fingerprint": "sha256:...",
  "created_at": "2026-07-29T17:00:00Z",
  "payload": { ... }
}
\`\`\`

### Breaking Changes

1. **Artifact file format changed** — All artifact files now use the \`ArtifactEnvelope\` JSON format. Backward compatibility is provided for some legacy formats on load (\`DiscoveryCache\`, schema snapshots, MCP index), but bytecode cache and frozen registry will be regenerated.
2. **\`JSONBytecodeCache(cache_dir=...)\` parameter now defaults to \`None\`** — Previously defaulted to \`"artifacts"\`. The cache now lives in \`.aquilia/artifacts/\`.
3. **Template manifest default location changed** — Moved from \`artifacts/templates.json\` to \`.aquilia/artifacts/templates.json\`.
4. **WebSocket artifact default location changed** — Moved from \`artifacts/ws.json\` to \`.aquilia/artifacts/ws.json\`.

Check the [Migration Guide](migration.md) for full details on upgrading.
`,
    "artifact_store.md": `# Artifact Store Deep Dive

The **Artifact Subsystem** (\`aquilia.artifacts\`) is a new foundational layer in Aquilia v1.3.6 designed to manage all generated data — from discovery caches to compiled bytecode. 

## Why it was built

Historically, each Aquilia subsystem managed its own caching and file I/O. The discovery engine wrote a JSON file, the template engine wrote a different JSON file and a custom HMAC format for bytecode, and the WebSocket compiler wrote another file. 
This led to:
- Inconsistent file locations (some in \`artifacts/\`, some in project root).
- Varying levels of atomic write guarantees (some used \`mkstemp\` + \`replace\`, some just \`write_text\`).
- No unified way to inspect, verify, or clean up generated data.

The Artifact Store centralizes this, providing a unified API with robust integrity and concurrency guarantees.

## Architecture Overview

The subsystem is composed of several key components:

1. **\`ArtifactStore\`**: The primary async facade for reading, writing, and managing artifacts.
2. **\`ArtifactEnvelope\`**: The canonical JSON wire format that wraps every payload.
3. **\`JSONFileBackend\` & \`MemoryBackend\`**: The physical storage layer.
4. **\`ArtifactRegistry\`**: The central registry of known artifact types.
5. **Canonicalization & Integrity**: Core logic for fingerprinting and HMAC signing.

### ArtifactStore

The \`ArtifactStore\` provides an async interface for all artifact operations.

\`\`\`python
from aquilia.artifacts import provide_artifact_store

store = provide_artifact_store()

# Async API
await store.put("discovery_cache", "main", payload_dict)
envelope = await store.get("discovery_cache", "main")
await store.verify("templates.bytecode")
await store.prune()
\`\`\`

It also supports an **\`ArtifactTransaction\`** for all-or-nothing multi-artifact commits:

\`\`\`python
async with store.transaction() as tx:
    await tx.put("discovery_cache", "main", discovery_data)
    await tx.put("route_index", "main", route_data)
# Both are committed atomically at the end of the block.
\`\`\`

### JSONFileBackend

\`JSONFileBackend\` handles the actual disk I/O, ensuring absolute safety against partial writes and concurrent access.

- **Atomic Writes**: Uses \`tempfile.mkstemp\` to write a temporary file, \`os.fsync\` to flush it to disk, and \`os.replace\` to atomically move it into place.
- **Signed Mode**: If \`signed=True\`, the backend computes an HMAC-SHA256 signature using the active secret key, appending it to the top of the file: \`<64-char-hex-HMAC>\\n<JSON>\`.

### ArtifactEnvelope Wire Format

Every artifact written to disk (except signed files, which prepend the HMAC) is a strict JSON document matching the \`ArtifactEnvelope\` format:

\`\`\`json
{
  "format": "aquilia-artifact",
  "artifact_type": "discovery_cache",
  "schema_version": "1.0",
  "key": "main",
  "fingerprint": "sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
  "created_at": "2026-07-29T17:00:00Z",
  "payload": { 
      "modules": [...],
      "routes": [...]
  }
}
\`\`\`

This ensures that any tool, inside or outside of Aquilia, can safely parse, identify, and verify the age/schema of any artifact.

### ArtifactRegistry

The \`ArtifactRegistry\` keeps track of what artifacts exist and how to handle them.

\`\`\`python
from aquilia.artifacts import register_artifact_type, ArtifactTypeDescriptor

register_artifact_type(ArtifactTypeDescriptor(
    name="my_custom_cache",
    schema_version="1.0",
    signed=False
))
\`\`\`

There are currently 10 registered types in Aquilia: \`discovery_cache\`, \`frozen_registry\`, \`schema_snapshot\`, \`ws_metadata\`, \`template_manifest\`, \`mcp_knowledge_index\`, \`template_bytecode\`, \`di_manifest\`, \`route_index\`, \`migration_file\`.

## Dependency Injection

The store is available via the DI container with an app-scoped provider:

\`\`\`python
from aquilia.artifacts import ArtifactStoreProvider

# Available automatically in controllers/services:
class MyService:
    store: ArtifactStore = Inject(ArtifactStore)
\`\`\`

## CLI: \`aq artifacts\`

A new command group allows you to manage the store from the terminal:

- \`aq artifacts status [--root PATH]\`: Lists all registered artifact types, showing which are present on disk, file size, last modified time, and schema version.
- \`aq artifacts verify [PATH] [--root PATH]\`: Verifies the integrity of one or all artifacts, strictly checking the HMAC for signed types.
- \`aq artifacts clean [--root PATH] [--orphaned-only]\`: Removes stale, corrupted, or orphaned artifacts.

## Configuration

The root directory defaults to \`.aquilia/artifacts\` in your project root. You can override this globally:

\`\`\`toml
# pyproject.toml
[aquilia.artifacts]
root = "/var/lib/myapp/artifacts"
\`\`\`

Or via environment variable:
\`\`\`bash
export AQUILIA_ARTIFACT_ROOT=/var/lib/myapp/artifacts
\`\`\`
`,
    "unified_artifact_directory.md": `# Unified Artifact Directory

A critical path fix in Aquilia v1.3.6 is the consolidation of all framework-generated files into a single, predictable location.

## Before

In previous versions, artifacts were scattered, usually landing in an \`artifacts/\` folder created at the current working directory, or sometimes in the project root directly:

- \`artifacts/templates.bytecode.json\`
- \`artifacts/ws.json\`
- \`artifacts/templates.json\`

This polluted the project root, often conflicted with user folders named "artifacts", and lacked a standardized structure.

## After

**ALL** framework artifacts now live under a unified hidden directory: \`.aquilia/artifacts/\`.

This change is driven by \`resolve_artifact_root()\`, which locates the project root and appends \`.aquilia/artifacts\`.

### Directory Layout

\`\`\`text
<project_root>/
└── .aquilia/
    └── artifacts/
        ├── discovery_cache.json          # auto-discovery engine cache
        ├── schema_snapshot.json          # ORM schema snapshot for migrations
        ├── templates.bytecode.json       # compiled Jinja2 bytecode (HMAC-signed)
        ├── templates.json                # template manifest / inventory
        ├── ws.json                       # WebSocket controller metadata
        ├── mcp_knowledge_index.json      # MCP context knowledge index
        ├── di_manifest.json              # DI provider graph
        └── route_index.json              # compiled route index
\`\`\`

## Breaking Changes & Path Adjustments

Because the default path changed, any tooling or manual scripts that expected files in \`artifacts/\` will need to be updated.

- \`JSONBytecodeCache.__init__(cache_dir: str | None = None)\`: Default changed from \`"artifacts"\` to \`None\` (which dynamically resolves to \`.aquilia/artifacts\`).
- \`create_template_engine_from_config(cache_dir: str | None = None)\`: Default changed to \`None\`.
- \`TemplateManager.compile_all(output_path=None)\`: Default changed from \`"artifacts/templates.json"\` to \`.aquilia/artifacts/templates.json\`.
- \`cmd_compile(output=None)\`: Resolves via \`resolve_artifact_root() / "templates.json"\`.
- \`cmd_clear_cache(cache_dir=None)\`: Resolves via \`resolve_artifact_root()\`.
- \`aq ws inspect --artifacts-dir\`: Default changed from \`"artifacts"\` to \`None\`.
- \`aq ws gen-client --artifacts-dir\`: Default changed from \`"artifacts"\` to \`None\`.

**Backward Compatibility:** If your code explicitly passes \`cache_dir="artifacts"\`, the framework will respect it and continue to use the old directory. 

## Migration Steps

1. **Update \`.gitignore\`**: You should ignore the new directory.
   \`\`\`bash
   echo '.aquilia/artifacts/' >> .gitignore
   \`\`\`

2. **Clean up old artifacts**: You can safely delete the old scattered files.
   \`\`\`bash
   rm -rf artifacts/
   \`\`\`
   The framework will automatically regenerate everything inside \`.aquilia/artifacts/\` on the next run.

3. **Verify**: Run the new CLI command to ensure things are working:
   \`\`\`bash
   aq artifacts status
   \`\`\`

## Custom Configuration

If you deploy to a read-only filesystem and need to direct artifacts to a writable volume (like \`/tmp\` or \`/var/lib/\`), you can override the root path globally:

\`\`\`toml
# pyproject.toml or aquilia.toml
[aquilia.artifacts]
root = "/var/lib/myapp/artifacts"
\`\`\`

Or via environment variable (useful for Docker containers):
\`\`\`bash
export AQUILIA_ARTIFACT_ROOT=/var/lib/myapp/artifacts
\`\`\`
`,
    "producer_migrations.md": `# Producer Migrations

In v1.3.6, all 9 primary artifact producers were migrated from ad-hoc file I/O to the new \`ArtifactStore\` backend. This ensures uniform atomic writes, consistent formatting, and centralized integrity checking.

Below are the details on how each producer was migrated and backward compatibility notes.

## 1. Discovery Cache (\`aquilia/discovery/engine.py\`)

**Before:**
\`DiscoveryCache.save()\` and \`load()\` used raw \`Path.write_text()\` with a plain dictionary format. It did not verify integrity on load.

**After:**
Uses \`JSONFileBackend.write_sync\`/\`read_sync\` + \`ArtifactEnvelope\`. Integrity is implicitly checked by the backend when resolving the envelope.

**Backward Compatibility:**
The loader detects the legacy plain dict format and gracefully loads it. It will be seamlessly upgraded to the envelope format on the next save.

## 2. Aquilary Registry (\`aquilia/aquilary/core.py\`)

**Before:**
\`AquilaryRegistry.export_manifest()\` used standard file writing to dump the frozen registry.

**After:**
\`export_manifest()\` and \`_from_frozen_manifest()\` use \`JSONFileBackend(signed=True)\` + \`ArtifactEnvelope\`.

**Backward Compatibility:**
No backward compatibility provided. The frozen registry is ephemeral to the deployment and will be cleanly regenerated on the first boot of a v1.3.6 application.

## 3. Schema Snapshots (\`aquilia/models/schema_snapshot.py\`)

**Before:**
\`save_snapshot()\` and \`load_snapshot()\` wrote a raw JSON dict to disk.

**After:**
Uses \`JSONFileBackend\` + \`ArtifactEnvelope\`. 

**Backward Compatibility:**
Like the discovery cache, legacy plain dict files are detected and read seamlessly.

## 4. Template Manifest (\`aquilia/templates/manifest_integration.py\`)

**Before:**
\`generate_template_manifest()\` wrote directly to \`artifacts/templates.json\`.

**After:**
Uses \`bare_fingerprint\` + \`ArtifactEnvelope\` + \`JSONFileBackend\`, writing to \`.aquilia/artifacts/templates.json\`.

**Backward Compatibility:**
Safe to regenerate. If you rely on the manifest file for external tooling, update the tool to parse the new \`payload\` key inside the envelope.

## 5. Bytecode Cache (\`aquilia/templates/bytecode_cache.py\`)

**Before:**
\`JSONBytecodeCache._save()\`/\`_load()\` used manual HMAC signing logic with \`Path.replace()\` (not \`os.replace()\`), writing to \`artifacts/templates.bytecode.json\`.

**After:**
Delegates to \`self._backend\` (\`JSONFileBackend\` with \`signed=True\`). \`__init__\` now accepts \`cache_dir: str | None = None\`, dynamically resolving the directory.

**Backward Compatibility:**
No backward compatibility for the file format. The cache will be invalidated and regenerated correctly under the new system. Existing code passing \`cache_dir="artifacts"\` continues to work but gets the new envelope format.

## 6. Socket Compiler (\`aquilia/sockets/compile.py\`)

**Before:**
\`SocketCompiler.generate_artifacts()\` wrote directly to \`artifacts/ws.json\`.

**After:**
Uses \`ArtifactEnvelope\` + \`JSONFileBackend\`, writing to \`.aquilia/artifacts/ws.json\`.

**Backward Compatibility:**
Regenerated on demand.

## 7. MCP Knowledge Index (\`aquilia/mcp/context/indexer.py\`)

**Before:**
\`save_index()\` and \`load_index()\` read/wrote a plain dictionary.

**After:**
Uses \`ArtifactEnvelope\` + \`JSONFileBackend\`.

**Backward Compatibility:**
Legacy plain dict formats are still loadable.

## Performance Impact

Despite the additional metadata overhead, there is **no measurable performance degradation**. The previous systems that used atomic writes were already paying the cost of \`mkstemp\` + \`os.replace\`. The abstraction simply centralizes this logic. Systems that previously used \`write_text\` are now slightly slower (on the order of single-digit milliseconds) but gain absolute resilience against partial writes and process crashes.
`,
    "migration.md": `# Migration Guide — Aquilia v1.3.6

Aquilia v1.3.6 brings the new **Artifact Subsystem**. For most standard web applications, this upgrade is entirely transparent. The framework handles the migration, recreation, and cleanup of generated artifacts automatically.

However, if you maintain CI/CD pipelines, Dockerfiles, or external tooling that interacts with Aquilia's artifact files, you will need to apply a few small changes.

---

## Upgrading

\`\`\`bash
pip install aquilia==1.3.6
\`\`\`

---

## Upgrade Checklist

1. \`pip install aquilia==1.3.6\`
2. **Update \`.gitignore\`**: Add \`.aquilia/artifacts/\` to your \`.gitignore\`.
3. **Delete old artifacts**: Run \`rm -rf artifacts/\` from your project root.
4. **Update CI/CD caches**: If your CI caches the \`artifacts/\` folder, update the path to \`.aquilia/artifacts/\`.
5. **Update Dockerfiles**: If you \`COPY artifacts/ /app/artifacts/\`, update it to \`COPY .aquilia/artifacts/ /app/.aquilia/artifacts/\`.
6. **Update external scripts**: If you have tools parsing \`templates.json\` or \`ws.json\`, update them to read from the new path and parse the \`.payload\` property of the new JSON envelope.

---

## Breaking Changes Summary

### 1. Default Artifact Path Changed
The default path for all artifacts is now \`.aquilia/artifacts/\`.
* \`JSONBytecodeCache(cache_dir=None)\` previously defaulted to \`"artifacts"\`.
* Template compilation commands output to \`.aquilia/artifacts/templates.json\`.
* WebSocket inspect commands read from \`.aquilia/artifacts/ws.json\`.

If your code explicitly provided \`cache_dir="artifacts"\`, that code will continue to work, but the files written inside it will use the new JSON format.

### 2. Artifact File Format Changed
All framework JSON artifacts are now wrapped in an \`ArtifactEnvelope\`.

**Old Format (e.g. \`discovery_cache.json\`):**
\`\`\`json
{
  "modules": ["app.users", "app.billing"],
  "timestamp": 123456789
}
\`\`\`

**New Format:**
\`\`\`json
{
  "format": "aquilia-artifact",
  "artifact_type": "discovery_cache",
  "schema_version": "1.0",
  "key": "main",
  "fingerprint": "...",
  "created_at": "...",
  "payload": {
    "modules": ["app.users", "app.billing"]
  }
}
\`\`\`

The framework automatically handles backward compatibility for reading legacy \`discovery_cache.json\`, \`schema_snapshot.json\`, and \`mcp_knowledge_index.json\`. Other caches (like bytecode) will be regenerated.

---

## Verification

After upgrading, boot your application or run your tests, then use the new CLI tool to verify the store:

\`\`\`bash
aq artifacts status
\`\`\`

You should see a table showing the newly generated artifacts in the \`.aquilia/artifacts/\` directory.

---

## Rollback Procedure

If you need to roll back to v1.3.5:
1. \`pip install aquilia==1.3.5\`
2. Delete the new directory: \`rm -rf .aquilia/artifacts/\`
3. Delete any legacy \`artifacts/\` directory just to be safe.
4. Reboot the application; v1.3.5 will regenerate the artifacts in the old format and old locations.
`,
    "bugfixes.md": `# Bug Fixes

The introduction of the unified \`ArtifactStore\` in v1.3.6 inherently resolves several long-standing, subtle bugs related to file I/O and caching across the framework.

## 1. Centralized Atomic Write Guarantees

**The Bug:**
Different subsystems implemented file writing differently. Some, like the bytecode cache, attempted atomic writes but used \`Path.replace()\` (which is not guaranteed to be atomic across all filesystems/platforms) instead of \`os.replace()\`. Others, like the discovery engine, used a raw \`Path.write_text()\`, meaning a crash during the write could leave a corrupted, partially written JSON file on disk, breaking the app on the next boot.

**The Fix:**
All artifact writing now routes through \`JSONFileBackend.write_sync()\`. This function rigorously employs \`tempfile.mkstemp\` (ensuring the temporary file is on the same filesystem), writes the data, calls \`os.fsync\` to guarantee durability, and then uses \`os.replace\` for a true atomic swap. No partial writes are possible.

## 2. Inconsistent HMAC Verification

**The Bug:**
While the bytecode cache properly verified its HMAC signature on load, other caches (like the discovery cache) did not verify integrity at all. If the \`discovery_cache.json\` file was manually tampered with or corrupted without breaking JSON syntax, the framework would load it blindly.

**The Fix:**
The \`JSONFileBackend\` natively supports a \`signed=True\` mode, and the \`ArtifactEnvelope\` includes a \`fingerprint\` property. The \`ArtifactStore\` verifies signatures on load for all configured artifact types, throwing an \`ArtifactCorruptFault\` if tampering or corruption is detected.

## 3. Directory Clutter & Collisions

**The Bug:**
The framework created an \`artifacts/\` directory in the current working directory of the process. If a developer ran a command from a subdirectory, a second \`artifacts/\` directory would be created there. Furthermore, the generic name \`artifacts/\` often collided with user-created folders or CI output directories.

**The Fix:**
All generated artifacts are now strictly confined to \`.aquilia/artifacts/\` relative to the project root, resolved predictably via \`resolve_artifact_root()\`.
`,
  },
  "1.3.5": {
    "README.md": `# Aquilia v1.3.5 Release Notes — "Distributed Tide"

Aquilia v1.3.5 makes the background task system genuinely distributed and durable, turns the mail subsystem into a production-grade delivery pipeline, and closes a silent validation bypass in Contracts.

Before this release, background tasks ran in a single process on an in-memory queue — jobs were lost on restart, a second web worker meant a second independent queue, and \`backend="redis"\` was accepted by configuration and then silently ignored. Mail was sent inline inside the request handler, with no bounce handling and no suppression list. And a nested Contract's \`@ward\` methods never ran at all: a validation rule declared on a nested Contract enforced nothing.

This release closes all three gaps: jobs now execute across multiple worker processes and multiple machines with lease-based coordination and crash recovery; job state survives restarts on Redis or SQL; jobs compose into chains, groups, chords, and arbitrary DAGs; duplicate enqueues are collapsed by an enforced fingerprint; mail is delivered by background workers with provider webhook processing and automatic suppression of bounced and complaining recipients; and nested Contract validation runs the child's full pipeline.

The tasks and mail work is entirely backward compatible. The Contracts audit ships four deliberate behavioral corrections — each one replacing incorrect behavior — listed under [Breaking Changes](#breaking-changes).

---

## Table of Contents

1. [Distributed & Persistent Task Backends](distributed_tasks.md)
   - \`RedisBackend\` — atomic Lua claim, \`SET NX\` fingerprint reservation
   - \`SQLBackend\` — durable queue on the application's own database
   - Lease-based claiming, heartbeat renewal, and crash recovery
   - \`Job.to_payload()\` / \`Job.from_payload()\` transport serialization
   - Registry-based callable resolution across process boundaries
2. [Workflows & DAGs](workflows.md)
   - \`Signature\`, \`Workflow\`, \`WorkflowResult\`
   - \`chain\` (sequential), \`group\` (parallel), \`chord\` (fan-in)
   - Arbitrary DAGs via \`depends_on\`
   - \`with_parent_results()\` continuation passing
   - Cycle and unknown-dependency validation
3. [Idempotency & Distributed Deduplication](idempotency.md)
   - \`Job.fingerprint\` finally enforced
   - \`dedup="allow" | "skip" | "raise"\`
   - Cross-process locking via Redis \`SET NX\` and a SQL unique constraint
4. [Mail Delivery Queue](mail_queue.md)
   - \`EnvelopeStore\` — \`MemoryEnvelopeStore\` and \`SQLEnvelopeStore\`
   - Background delivery through the existing task scheduler
   - Envelope-ID-only jobs, designed for distributed workers
   - Send-time deduplication by idempotency key and content digest
5. [Bounce Handling, Webhooks & Suppression](bounces_suppression.md)
   - \`parse_ses\`, \`parse_sendgrid\`, \`parse_mailgun\` with signature verification
   - \`process_webhook\` applying bounces and complaints
   - \`SuppressionList\` — permanent and TTL suppression, enforced on send
6. [Mail Security, MIME & Templates](mail_security.md)
   - Shared MIME assembly across every provider
   - Real DKIM signing at the byte level
   - XOAUTH2 authentication, TLS enforcement, PII redaction
   - ATS template filters and autoescaping
7. [Native HTTP Client & Dependency Cleanup](http_native.md)
   - Zero third-party HTTP client dependencies (\`httpx\` removed)
   - \`SendGridProvider\` and \`LiveServerTestCase\` updated to \`aquilia.http\`
8. [Contracts — Nested Validation Pipeline](contracts_pipeline.md)
   - Nested Contracts never ran their wards or \`validate()\` hook (CRITICAL)
   - \`list[Contract]\` annotations bypassed the nested pipeline (CRITICAL)
   - \`has_async_wards\` consulted only the top-level class
   - \`to_dict_async()\` / \`to_dict_many_async()\` / \`Lens.mold_async()\`
   - \`LensUnresolvedFault\` replaces a silent empty list
   - Input adapters for dataclasses, attrs, and \`TypedDict\`
9. [Contracts — Validation Control & Typing](contracts_validation.md)
   - \`@ward(order=..., when=..., groups=...)\`, \`Spec.fail_fast\`
   - \`Spec.frozen\`, \`Contract.__eq__\`, \`copy()\` / \`copy_async()\`
   - \`BytesFacet\`, \`PathFacet\`, \`SecretFacet\`, \`MACAddressFacet\`
   - \`Contract.from_env()\` and \`Contract.from_cli()\`
   - Localized validation messages via \`contract_message()\`
10. [Contracts — Stub Generation & Deprecations](contracts_tooling.md)
    - \`aq contracts stubs\` — \`.pyi\` emission for \`mypy\` and \`pyright\`
    - \`seal_*\` / \`async_seal_*\` prefix convention deprecated
11. [CLI Changes](cli.md)
    - \`aq mail check\` validates DKIM configuration
    - \`aq contracts stubs\` generates Contract type stubs
12. [Bug Fixes](bugfixes.md)
    - Mail delivery task unresolvable across processes (CRITICAL)
    - Consumer-only workers polled nothing (CRITICAL)
    - Job results degraded to \`repr\` strings on persistent backends
    - \`queue.persistent\` had no configuration surface
13. [Migration Guide](migration.md)
    - Upgrade checklist, per-feature migrations, compatibility notes, known issues

---

## Highlights

### Distributed execution with crash recovery

A worker claims a job under a time-bounded lease and renews it by heartbeat. If the worker dies, the lease lapses and a peer reclaims the job instead of the job being lost.

\`\`\`python
# workspace.py — production
Integration.tasks(
    backend="redis",
    redis_url="redis://cache:6379/0",
    num_workers=16,
    lease_seconds=120,
)
\`\`\`

Task code is unchanged between backends. Switching is configuration, not a rewrite.

### Workflows

\`\`\`python
from aquilia.tasks.workflow import chain, chord

# Sequential, each step fed by the previous
await chain(
    extract.s(source),
    transform.s().with_parent_results(),
    load.s().with_parent_results(),
).run(tasks)

# Parallel shards, then a fan-in callback
await chord(
    [shard.s(n) for n in range(8)],
    merge.s().with_parent_results(),
).run(tasks)
\`\`\`

The graph is durable the moment it is submitted. No orchestrator process, and a \`WAITING\` step holds no worker slot.

### Enforced idempotency

\`\`\`python
# Ten identical requests; one job.
await tasks.enqueue(rebuild_index, dedup="skip")
\`\`\`

Correctness comes from the storage layer — Redis \`SET NX\`, or a SQL primary-key constraint — so two racing processes produce one job.

### Background mail delivery

\`\`\`python
Integration.mail(
    default_from="noreply@example.com",
    providers=[...],
    queue_enabled=True,
    queue_persistent=True,
)
\`\`\`

\`asend()\` returns as soon as the envelope is stored. Delivery, retries, and backoff run on a worker — reusing the task scheduler rather than introducing a second queue.

### Automatic bounce suppression

\`\`\`python
events = parse_ses(await ctx.body(), verify_topic_arn=SES_TOPIC_ARN)
await process_webhook(events, suppression=mail.suppression, store=mail.store)
\`\`\`

A hard bounce or spam complaint removes the address from every future send, protecting sender reputation without application code.

### Nested Contract rules are enforced

\`\`\`python
class LineItem(Contract):
    qty = IntFacet()

    @ward
    def qty_positive(self, data):
        if data["qty"] < 1:
            self.reject("qty", "Must be at least 1")

class Order(Contract):
    items: list[LineItem] = None

Order(data={"items": [{"qty": 0}]}).is_sealed()
# v1.3.4: True — the ward never ran
# v1.3.5: False, errors = {"items": {"0": {"qty": ["Must be at least 1"]}}}
\`\`\`

A nested Contract was validated *structurally only*, so every \`@ward\` and every \`validate()\` override on it was silently skipped. See [Nested Validation Pipeline](contracts_pipeline.md).

### Contract fields visible to type checkers

\`\`\`bash
aq contracts stubs myapp.contracts        # writes myapp/contracts.pyi
aq contracts stubs myapp.contracts --check  # CI freshness gate
\`\`\`

\`\`\`python
reveal_type(contract.total)    # decimal.Decimal — was Any
\`\`\`

A portable \`.pyi\` every type checker consumes with no plugin. See [Stub Generation](contracts_tooling.md).

---

## What's New

| Capability | Summary |
|---|---|
| \`RedisBackend\` | Distributed, durable task queue with atomic Lua claim |
| \`SQLBackend\` | Durable task queue on the existing application database |
| \`Job.to_payload()\` / \`from_payload()\` | JSON transport form with fail-at-enqueue validation |
| \`Workflow\`, \`Signature\`, \`WorkflowResult\` | Job graphs with dependencies |
| \`chain\`, \`group\`, \`chord\` | Sequential, parallel, and fan-in composition |
| \`dedup="skip" \\| "raise"\` | Enforced fingerprint deduplication |
| \`TaskDuplicateFault\`, \`TaskSerializationFault\`, \`TaskBackendFault\`, \`TaskWorkflowFault\` | New structured faults |
| \`EnvelopeStore\` | Durable record of accepted mail |
| \`SuppressionList\` | Bounce and complaint suppression, enforced on send |
| \`parse_ses\` / \`parse_sendgrid\` / \`parse_mailgun\` | Provider webhook parsing with signature verification |
| \`process_webhook\` | Applies delivery events to suppression and envelope status |
| \`build_mime_message\` / \`message_to_bytes\` / \`sign_dkim\` | Shared MIME assembly and DKIM signing |
| \`redact_email\` / \`redact_pii\` | PII redaction for mail logs |
| \`MailAuth.oauth2(...)\` | XOAUTH2 bearer-token SMTP authentication |
| \`aquilia[mail-dkim]\` | New optional extra for DKIM signing |
| \`aq contracts stubs\` | \`.pyi\` stub emission so \`mypy\`/\`pyright\` see Contract fields |
| \`Contract.to_dict_async()\` / \`to_dict_many_async()\` | Async serialization that awaits ORM relations |
| \`@ward(order=..., when=..., groups=...)\` | Validator ordering, conditional rules, and validation groups |
| \`Spec.frozen\` / \`Spec.fail_fast\` | Immutable validated data; stop at the first ward error |
| \`Contract.copy()\` / \`copy_async()\` | Derive an updated Contract, re-validating by default |
| \`Contract.from_env()\` / \`from_cli()\` | Build a Contract from environment variables or CLI arguments |
| \`BytesFacet\`, \`PathFacet\`, \`SecretFacet\`, \`MACAddressFacet\` | Strongly-typed primitives that previously fell through to \`TextFacet\` |
| \`aquilia.contracts.messages\` | Localized validation messages via the i18n catalog |
| \`NestingDepthFault\`, \`LensUnresolvedFault\`, \`StubGenerationFault\` | New structured Contract faults |

---

## Major Improvements

- **Backend selection is honest.** \`backend="redis"\` used to log a warning and fall back to in-memory. It now builds a real Redis backend; only an unknown backend name or an unreachable service falls back, and both say so loudly.
- **Serialization fails at the call site.** A non-JSON argument raises \`TaskSerializationFault\` at \`enqueue()\`, not on a remote worker hours later.
- **Queue discovery.** A consumer-only worker polls the queues declared by its \`@task\` descriptors, plus any queue it discovers on the shared backend.
- **Mail providers share one MIME implementation.** Header handling, attachments, and tracking headers no longer drift between SMTP, SES, SendGrid, and the development backends.
- **Graceful degradation everywhere.** An unreachable Redis, database, or DKIM dependency degrades with an error naming exactly what was lost, rather than aborting startup.

---

## Performance Improvements

- Mail moves off the request path entirely: a full SMTP conversation becomes one store write plus one enqueue.
- Workflow steps in \`WAITING\` consume no worker slot, replacing the pattern of a long-lived job blocking on its children.
- \`dedup="skip"\` collapses duplicate work before it executes — the cheapest possible optimization for a burst of identical requests.
- \`MemoryBackend\` is untouched; single-process applications see no change.
- \`SQLBackend\` claim is a single conditional \`UPDATE\` in a transaction; \`RedisBackend\` claim is one round trip against a sorted set.

---

## Developer Experience Improvements

- One mental model for background work: mail delivery is an ordinary task on an ordinary queue, visible in the admin dashboard alongside everything else.
- \`aq mail check\` catches DKIM misconfiguration before the first send fails.
- Structured faults name the failure precisely — \`TaskSerializationFault\` reports which argument, \`TaskWorkflowFault\` names the cycle.
- The \`aquilia.tasks\` package docstring no longer claims distributed backends and workflows are unimplemented.
- **Contract fields are visible to type checkers.** \`aq contracts stubs\` emits a \`.pyi\` so \`contract.total\` resolves to \`decimal.Decimal\` rather than \`Any\`, and a field typo fails CI instead of production.
- **Validation rules carry their own metadata.** Ordering, conditions, and groups live on \`@ward\` rather than inside ward bodies, so a rule's applicability is inspectable.
- **Configuration validates like request data.** \`Contract.from_env()\` runs environment variables through the same facets, so a bad \`PORT\` fails at startup with a field error instead of at first use with a \`ValueError\`.
- **Validation messages localize.** Every built-in message resolves through the i18n catalog's \`contracts.\` namespace, with no change for applications that do not configure i18n.

---

## Security Improvements

- **Webhook signature verification** for SES (topic ARN), SendGrid (ECDSA public key), and Mailgun (HMAC signing key), with replay rejection via a timestamp window. Without it, anyone can forge a bounce and suppress an arbitrary address.
- **DKIM signing** applied at the byte level immediately before transmission, covering exactly what the provider receives. Failures raise rather than shipping unsigned mail.
- **TLS enforcement** on SMTP remains on by default.
- **PII redaction** masks recipient local parts in logs while preserving domains.
- **Registry-only callable resolution** means a queue entry can never name a function the application did not register — a durable queue is not an arbitrary-code-execution channel.
- **Parameterized SQL throughout** the new backends and stores; table and column identifiers are validated against a restricted character set.

---

## Bug Fixes

| Issue | Subsystem | Fix |
|---|---|---|
| Mail delivery task unresolvable across processes | Mail / Tasks | Delivery registered as \`@task(name="aquilia.mail.deliver")\`; workers resolve it by stable name. |
| Consumer-only workers polled nothing | Tasks | Queues seeded from \`@task\` descriptors and refreshed from \`backend.get_queue_stats()\`. |
| Job results degraded to \`repr\` strings | Tasks | JSON-safe values round-trip; only non-serializable values fall back to \`repr\`. |
| \`queue.persistent\` had no config surface | Mail | Threaded through \`Integration.mail\`, \`MailIntegration\`, \`QueueConfigContract\`, and store selection. |
| \`Job.fingerprint\` computed but never read | Tasks | Enforced at enqueue via \`dedup\`. |
| \`MailSuppressedFault\` unreachable | Mail | Now part of a working suppression path. |
| Stale package docstring | Tasks | No longer lists shipped features as "deliberately absent". |
| Nested Contracts never ran wards or \`validate()\` | Contracts | Nested validation runs the child's full pipeline via \`run_nested_contract()\`. |
| \`list[Contract]\` annotations bypassed nested validation | Contracts | Detection looks through container facets, so both spellings route identically. |
| \`has_async_wards\` missed nested async wards | Contracts | Walks the facet tree, memoized, with cycle detection. |
| \`Lens(many=True)\` returned \`[]\` for unresolved relations | Contracts | Raises \`LensUnresolvedFault\` instead of shipping wrong data. |
| No async serialization path existed | Contracts | \`to_dict_async()\`, \`to_dict_many_async()\`, \`Lens.mold_async()\`. |
| Non-mapping input reported every field as missing | Contracts | Reports \`{"__all__": ["Expected an object, got str"]}\`. |
| \`IntFacet\` silently truncated \`3.9\` to \`3\` | Contracts | Fractional floats rejected; integral ones still accepted. |
| \`bytes\` fields were non-functional end to end | Contracts | \`bytes\` annotations route to the new \`BytesFacet\`. |
| \`"__minimal__"\` projection exposed every field | Contracts | Resolves to primary-key plus \`read_only\` facets. |
| Nesting-depth guard unreachable from the real path | Contracts | Depth threaded through \`Sigil.validate()\`; structured error. |
| Depth counter was global mutable state | Contracts | Replaced with a \`contextvars.ContextVar\`. |
| \`@computed\` ran against an uninitialized instance | Contracts | The live Contract instance is threaded in explicitly. |
| \`validate()\` ran up to three times per row in bulk paths | Contracts | Single shared \`_seal_row()\` / \`_seal_row_async()\`. |
| Top-level async wards bypassed groups and ordering | Contracts | \`is_sealed_async()\` uses the shared ward phase. |

Contract fixes are detailed in [Nested Validation Pipeline](contracts_pipeline.md) and [Validation Control & Typing](contracts_validation.md).

---

## Breaking Changes

The tasks, mail, and HTTP work introduces no breaking changes.

The Contracts audit ships **four deliberate behavioral corrections**. Each replaces behavior that was incorrect, so the change is the fix rather than a side effect of it:

| Change | Previously | Now | Who is affected |
|---|---|---|---|
| Nested Contract rules are enforced | A nested \`@ward\` or \`validate()\` override never ran | Runs, and rejects | Anyone whose nested Contracts declare rules. Payloads previously accepted may now be rejected. |
| \`Lens(many=True)\` unresolved relation | Returned \`[]\`, indistinguishable from "no rows" | Raises \`LensUnresolvedFault\` | Anyone serializing a to-many Lens without prefetching. Prefetch, materialize, or use \`to_dict_async()\`. |
| Malformed body error shape | Per-field "This field is required" | \`{"__all__": ["Expected an object, got str"]}\` | Clients parsing a 422 body that assume every key is a field name. |
| \`IntFacet\` fractional input | \`3.9\` silently became \`3\` | Rejected | Anyone relying on silent truncation. \`3.0\` is still accepted. |

\`"__minimal__"\` projections also return a restricted field set now; the previous output — every field — was never correct.

See the [Migration Guide](migration.md) for the review steps.

---

## Deprecated / Removed

**Deprecated:** the \`seal_*\` / \`async_seal_*\` Contract validator naming convention. Deprecated in 1.3.0, removed in 2.0.0. Declaring such a method now emits a \`DeprecationWarning\` naming its exact replacement decorator. Behavior is unchanged in 1.x — these methods continue to run exactly as before.

Migration is mechanical: decorate the method with \`@ward\` (or \`@ward(mode="async")\`); the body does not change. Find every affected method with \`python -W error::DeprecationWarning -c "import myapp.contracts"\`. Full guide in [Stub Generation & Deprecations](contracts_tooling.md#deprecated-the-seal_--async_seal_-prefix-convention).

**Removed:** the third-party \`httpx\` dependency. See [Native HTTP Client](http_native.md).

---

## Internal Refactoring

- MIME assembly extracted from four providers into \`aquilia/mail/mime.py\`.
- PII redaction extracted into \`aquilia/mail/redaction.py\`.
- The \`TaskBackend\` ABC gained \`heartbeat\`, \`reclaim_expired\`, \`reserve_fingerprint\`, \`release_fingerprint\`, and \`get_dependency_results\`, so \`MemoryBackend\` and the durable backends satisfy one contract.
- SMTP provider restructured around shared MIME assembly, byte-level signing, and pluggable authentication.

---

## Compatibility

| Area | Status |
|---|---|
| Python 3.10–3.13 | Supported, unchanged |
| Existing workspaces and manifests | No changes required |
| Existing \`@task\` functions | No changes required |
| Existing mail call sites | No changes required |
| Default behavior | Identical to v1.3.4 |

---

## Known Issues

- The Redis backend has no automated test coverage in this release; the SQL backend carries the durable-path integration tests.
- Mailgun signature verification is opt-in and warns when omitted.
- No built-in webhook route ships; applications wire the parsers into their own controller.
- Workflow steps whose parent failed remain \`WAITING\` rather than being cancelled.

Details and workarounds in the [Migration Guide](migration.md#known-issues).

---

## Testing

\`tests/test_tasks_mail_enterprise.py\` adds 43 tests covering job serialization, deduplication semantics, workflow composition and validation, durable-backend behavior driven against real SQLite (restart survival, cross-process queue discovery, cross-manager deduplication, lease reclaim), the mail delivery queue, suppression, webhook parsing and processing, and template autoescaping.

\`tests/test_audit_tasks_mail.py\` covers the mail provider, DKIM, MIME, redaction, and rate-limiting paths.

The Contracts audit adds 217 tests across six files (\`BP-SEC-014\` … \`BP-SEC-037\`):

| File | Covers |
|---|---|
| \`test_contract_audit_regressions.py\` | First-pass fixes: projections, depth guard, thread isolation, bulk-path \`validate()\` |
| \`test_contract_nested_pipeline.py\` | Nested wards, \`list[Contract]\` routing, async serialization, input adapters |
| \`test_contract_typing_features.py\` | New facets, equality, copy, frozen Contracts |
| \`test_contract_validation_control.py\` | Ward ordering/conditions/groups, fail-fast, i18n messages, \`from_env\`/\`from_cli\` |
| \`test_contract_stubs.py\` | Facet Python types, module stubs, the \`--check\` staleness gate |
| \`test_contract_ward_deprecation.py\` | \`seal_*\` warning content, and that legacy validators still run |

Full suite: 7,403 passing.

---

## Credits

Thanks to everyone who reported that \`backend="redis"\` did not do anything.
`,
    "bounces_suppression.md": `# Bounce Handling, Webhooks & Suppression Lists — Aquilia v1.3.5

Provider delivery events are now parsed, verified, and applied. A hard bounce or spam complaint automatically removes the address from all future sends. Before this release, \`MailSuppressedFault\` existed in the fault taxonomy but nothing raised it — there was no suppression list and no webhook handling at all.

---

## Motivation

Deliverability is reputation, and reputation is destroyed by continuing to mail addresses that bounce. Every ESP tracks bounce and complaint rates; exceed their thresholds and legitimate mail starts landing in spam or being rejected outright.

Handling this correctly requires three things Aquilia did not have: parsing each provider's webhook format, verifying those webhooks are genuine, and a persistent list consulted on every send.

---

## Architecture

\`\`\`
provider webhook (HTTP POST)
        │
        ▼
parse_ses / parse_sendgrid / parse_mailgun    ← verify signature, normalize
        │
        ▼
   list[WebhookEvent]                          ← provider-neutral
        │
        ▼
   process_webhook(events, suppression=..., store=...)
        │
        ├─ suppress the address (permanent or TTL)
        └─ update the envelope's status
        │
        ▼
next send → MailService filters suppressed recipients
\`\`\`

---

## Webhook Parsing

Three provider parsers normalize into one vocabulary:

\`\`\`python
from aquilia.mail import parse_ses, parse_sendgrid, parse_mailgun

parse_ses(payload, *, verify_topic_arn=None)
parse_sendgrid(payload, *, headers=None, public_key=None, max_age_seconds=600.0)
parse_mailgun(payload, *, signing_key=None, max_age_seconds=600.0)
\`\`\`

Each returns \`list[WebhookEvent]\`:

\`\`\`python
@dataclass
class WebhookEvent:
    event_type: EventType
    email: str
    provider: str
    timestamp: datetime
    message_id: str | None = None
    envelope_id: str | None = None   # from the X-Aquilia-Envelope-ID header
    detail: str | None = None        # e.g. the SMTP rejection line
    raw: dict[str, Any]              # original payload, kept for auditing
\`\`\`

\`EventType\` normalizes each provider's vocabulary: \`DELIVERED\`, \`HARD_BOUNCE\`, \`SOFT_BOUNCE\`, \`COMPLAINT\`, \`REJECTED\`, \`OPENED\`, \`CLICKED\`, \`UNSUBSCRIBED\`, \`DEFERRED\`, \`UNKNOWN\`. An unrecognized event becomes \`UNKNOWN\` and is preserved rather than dropped, so a provider adding a new type stays visible.

### Signature verification

**Verify webhooks in production.** An unverified endpoint lets anyone POST a forged bounce and suppress an arbitrary address — a trivial denial-of-service against your own users.

- **SES** — pass \`verify_topic_arn\` to reject notifications from any other SNS topic.
- **SendGrid** — pass \`public_key\` (the ECDSA verification key from your SendGrid settings) with the request \`headers\`. Replays older than \`max_age_seconds\` are rejected.
- **Mailgun** — pass \`signing_key\`. The HMAC signature and timestamp are verified.

Omitting these parameters parses without verification and logs a warning naming the risk.

---

## Suppression Lists

\`\`\`python
from aquilia.mail import SuppressionReason

await suppression.suppress(
    email,
    reason=SuppressionReason.HARD_BOUNCE,
    expires_in=None,      # seconds; ignored for permanent reasons
    provider="ses",
    detail="550 5.1.1 user unknown",
)
await suppression.unsuppress(email)          # -> bool
await suppression.is_suppressed(email)       # -> bool
await suppression.get(email)                 # -> SuppressionEntry | None
await suppression.list_all(limit=100, offset=0)
await suppression.filter_recipients(emails)  # -> (allowed, blocked)
await suppression.cleanup()                  # drop expired entries
\`\`\`

| Reason | Permanence |
|---|---|
| \`HARD_BOUNCE\` | Permanent — the address does not exist |
| \`SOFT_BOUNCE\` | Expires (defaults to 24 hours) — mailbox full, server down |
| \`COMPLAINT\` | Permanent — the most reputation-damaging signal a provider tracks |
| \`UNSUBSCRIBE\` | Permanent |
| \`MANUAL\` | Permanent — operator-added |

Two implementations ship: \`MemorySuppressionList\` (default) and \`SQLSuppressionList\` (table \`aquilia_mail_suppressions\`, selected by \`queue_persistent=True\`).

Addresses are normalized — lowercased and trimmed — before storage and lookup, so \`User@Example.COM\` and \` user@example.com \` are the same entry.

---

## Wiring a Webhook Endpoint

Aquilia does not register a webhook route for you; the path, authentication, and CSRF exemption belong to the application. The handler is a few lines:

\`\`\`python
from aquilia import Controller, POST, RequestCtx, Response
from aquilia.mail import parse_ses, process_webhook

class MailWebhookController(Controller):
    prefix = "/webhooks/mail"

    @POST("/ses")
    async def ses(self, ctx: RequestCtx):
        events = parse_ses(await ctx.body(), verify_topic_arn=SES_TOPIC_ARN)
        summary = await process_webhook(
            events,
            suppression=self.mail.suppression,
            store=self.mail.store,
        )
        return Response.json(summary)   # {"suppressed": 2, "delivered": 5, "ignored": 1}
\`\`\`

Exempt the webhook path from CSRF — providers do not carry your CSRF token. Rely on signature verification for authenticity instead.

---

## Enforcement on Send

\`MailService\` consults the suppression list while preparing every envelope. Suppressed recipients are removed; if *every* recipient is suppressed the envelope is marked \`CANCELLED\` and no delivery is attempted.

\`\`\`python
await mail.suppression.suppress("bounced@example.com", reason=SuppressionReason.HARD_BOUNCE)

envelope_id = await EmailMessage(subject="Hi", body="x", to="bounced@example.com").asend()
envelope = await mail.store.get(envelope_id)
envelope.status    # EnvelopeStatus.CANCELLED
\`\`\`

---

## Edge Cases

**Partial suppression.** An envelope with three recipients where one is suppressed sends to the remaining two. Only an envelope with no deliverable recipients is cancelled.

**Soft bounce TTL.** \`process_webhook\` suppresses soft bounces for \`soft_bounce_ttl\` (default 86,400 seconds) rather than permanently, since the cause is usually transient. Tune it per provider.

**Events with no address.** Counted as \`ignored\` rather than raising — a malformed event should not fail the whole batch.

**Non-suppressing events.** \`DELIVERED\`, \`OPENED\`, \`CLICKED\`, and \`DEFERRED\` update envelope status where applicable but never suppress.

**Malformed payloads.** A body that is not valid JSON raises \`MailFault\`, so a broken request surfaces as a 4xx rather than being silently swallowed.

**Envelope correlation.** Providers that echo custom headers return \`X-Aquilia-Envelope-ID\`, letting an event update the exact envelope. Providers that do not echo headers still suppress by address; the envelope simply is not correlated.

---

## Performance Implications

One suppression lookup per envelope on the send path. \`MemorySuppressionList\` is a dict lookup. \`SQLSuppressionList\` is an indexed primary-key read; \`filter_recipients\` batches a multi-recipient envelope rather than issuing one query per address.

Webhook processing is O(n) in events, with one suppression write per suppressing event.

---

## Compatibility

Purely additive. \`MailService.suppression\` defaults to an empty \`MemorySuppressionList\`, so no address is suppressed until a webhook or an operator adds one — existing applications see no behavioral change. \`MailSuppressedFault\`, previously unreachable, is now part of a working path.

---

## Related

- [Mail Delivery Queue](mail_queue.md)
- [Mail Security & MIME](mail_security.md)
- [Migration Guide](migration.md)
`,
    "bugfixes.md": `# Bug Fixes — Aquilia v1.3.5

Four defects were found and fixed while auditing the enterprise task and mail work. Three would only surface once a durable or distributed backend was in use — which is exactly what this release enables, so each would have been a first-day production failure for anyone adopting the new capability.

---

## 1. Mail delivery task unresolvable across processes

**Severity:** Critical, on any persistent backend.

### Previous behavior

Background mail delivery enqueued a plain module-level function. On \`MemoryBackend\` this worked, because the job carried the live callable in-process.

The moment a durable backend was configured, delivery stopped. The job serialized to a module-path reference, and the consuming worker — which resolves callables through the \`@task\` registry rather than importing arbitrary paths — could not resolve it. Envelopes sat in \`QUEUED\` forever. Nothing crashed loudly; mail simply never arrived.

### Root cause

\`_deliver_envelope_task\` was a bare \`async def\`, never registered with \`@task\`. Worker resolution goes through \`get_task(job.func_ref)\`, which only knows about registered descriptors. This is a deliberate security property — a queue entry must not be able to name arbitrary importable code — but it means an unregistered function is unreachable.

### New behavior

The delivery task is registered under a stable name:

\`\`\`python
@task(name="aquilia.mail.deliver", queue=MailService.retry_queue, max_retries=0)
async def _deliver_envelope_task(envelope_id: str) -> None: ...
\`\`\`

A worker in any process resolves it by name. The name is stable, so a future rename of the Python function does not orphan jobs already in the queue.

### User impact

Anyone enabling \`queue_enabled=True\` together with \`backend="redis"\` or \`backend="sql"\` would have had silently undelivered mail. Fixed before either capability shipped.

---

## 2. Consumer-only workers polled nothing

**Severity:** Critical, for distributed deployments.

### Previous behavior

A dedicated worker process — one that consumes jobs but never enqueues any — processed nothing. Jobs queued by web workers on any queue other than \`default\` were ignored indefinitely.

### Root cause

\`TaskManager._queues\` was populated exclusively as a side effect of \`enqueue()\`. A process that never enqueues therefore knew about exactly one queue: its configured \`default_queue\`. The worker loop iterates the known queue set, so work on \`mail\`, \`reports\`, or any other queue was invisible to it.

This was harmless while everything ran in one process — the enqueuer and the worker were the same object. It becomes fatal the moment producer and consumer are separate processes, which is the entire point of a distributed backend.

### New behavior

Two additions:

1. \`_bind_task_descriptors()\` registers the queue of every \`@task\` descriptor, so importing a task module is enough to poll its queue.
2. On a distributed backend, the manager adopts queues reported by \`backend.get_queue_stats()\` at startup and refreshes them on each reclaim tick — so a queue created by a peer after startup is picked up.

### User impact

Dedicated worker processes now consume the queues their producers use, without needing to be told which those are.

---

## 3. Job results degraded to repr strings on persistent backends

**Severity:** High — silent data corruption in workflows.

### Previous behavior

\`\`\`python
# In-process
job.result.value    # 4  (int)

# Same job on a SQL or Redis backend
job.result.value    # '4'  (str)
\`\`\`

A chord callback consuming \`parent_results\` received \`['4', '6']\` instead of \`[4, 6]\`. Arithmetic silently produced string concatenation or a \`TypeError\` far from the cause.

### Root cause

\`JobResult.to_dict()\` serialized unconditionally with \`repr(self.value)\`. The rationale — an arbitrary return value is not guaranteed to be JSON-compatible — was sound, but the blanket application destroyed values that serialize perfectly well.

### New behavior

JSON-safe values round-trip unchanged; only genuinely non-serializable values fall back to \`repr\`:

\`\`\`python
value = self.value
if value is not None:
    try:
        json.dumps(value)
    except (TypeError, ValueError):
        value = repr(value)
\`\`\`

### User impact

Workflow fan-in receives real values on every backend. Applications that had adapted to the string form — parsing \`repr\` output back — should remove that workaround.

\`\`\`python
# Before — workaround
total = sum(int(r) for r in parent_results)

# After
total = sum(parent_results)
\`\`\`

---

## 4. \`queue.persistent\` had no configuration surface or wiring

**Severity:** Medium — an advertised capability that could not be reached.

### Previous behavior

\`SQLEnvelopeStore\` and \`SQLSuppressionList\` existed and worked, but nothing constructed them from configuration. The only way to get durable mail state was to instantiate the stores by hand and pass them to \`MailService(store=..., suppression=...)\`. The \`queue\` config block had no \`persistent\` key at all, so setting it in \`workspace.py\` was silently dropped by contract validation.

### New behavior

\`persistent\` is a real config field, threaded end to end:

- \`Integration.mail(queue_persistent=True)\`
- \`MailIntegration.queue_persistent\`
- \`QueueConfigContract.persistent\`
- \`MailService._prepare_stores()\` selects SQL-backed stores when set

An unavailable database logs an error naming the durability that was lost and falls back to in-memory stores, rather than aborting startup — mail degrades to non-durable instead of taking the application down.

Explicitly-supplied stores still win: a caller passing \`store=\` meant it, and configuration does not override that.

### User impact

Durable envelope and suppression storage is now reachable from \`workspace.py\`.

---

## Documentation Correctness Fix

The \`aquilia.tasks\` package docstring listed "Persistent or distributed backends", "Job chaining / workflow DAGs" under **"Not implemented today (deliberately absent, not stubbed)"**. All three shipped in this release; the docstring is updated. It now documents the at-least-once delivery contract instead, and the one thing still genuinely absent (per-queue rate limiting).

---

## Related

- [Distributed & Persistent Backends](distributed_tasks.md)
- [Workflows & DAGs](workflows.md)
- [Mail Delivery Queue](mail_queue.md)
- [Contracts — Nested Validation Pipeline](contracts_pipeline.md) — Contract subsystem fixes in this release
- [Migration Guide](migration.md)
`,
    "cli.md": `# CLI Changes — Aquilia v1.3.5

One command group was added (\`aq contracts\`). One existing command gained new validation. Nothing was removed or renamed.

---

## New: \`aq contracts stubs\`

Emits \`.pyi\` type stubs so \`mypy\` and \`pyright\` can see Contract fields.

### Why

A Contract builds its fields at class-body evaluation time and serves them through \`__getattr__\`. Neither is visible to a static analyser, so \`contract.email\` was \`Any\` at best and an attribute error under \`--strict\` at worst. For a team with a type-checking gate in CI, this was the single largest adoption barrier.

A generated \`.pyi\` is a portable artifact: every type checker consumes it with no plugin, no configuration, and no version coupling.

### Usage

\`\`\`bash
aq contracts stubs MODULES... [--check] [--path DIR]
\`\`\`

| Flag | Purpose |
|---|---|
| \`--check\` | Do not write. Exit non-zero if any stub is missing or out of date. |
| \`--path DIR\` | Directory prepended to \`sys.path\` before importing. Default: current directory. |

### Examples

\`\`\`bash
# Write myapp/contracts.pyi
aq contracts stubs myapp.contracts

# Several modules at once
aq contracts stubs myapp.users.contracts myapp.orders.contracts

# CI freshness gate
aq contracts stubs myapp.contracts --check
\`\`\`

### Output

Success:

\`\`\`
$ aq contracts stubs myapp.contracts
  ✔ myapp.contracts: wrote /app/myapp/contracts.pyi
      2 contract(s): AddressContract, OrderContract
\`\`\`

Anything that could not be typed faithfully is emitted as \`Any\` and named, so a lost annotation is reported rather than silently weakening the module's types:

\`\`\`
  ✔ myapp.contracts: wrote /app/myapp/contracts.pyi
      2 contract(s): AddressContract, OrderContract
      REGISTRY: module-level value emitted as Any
\`\`\`

\`--check\` on a stale or missing stub exits \`1\` and prints the fix:

\`\`\`
$ aq contracts stubs myapp.contracts --check
  ✘ myapp.contracts: contracts.pyi is missing or out of date
      2 contract(s): AddressContract, OrderContract

  Stubs are out of date. Regenerate with:
      aq contracts stubs myapp.contracts
\`\`\`

A module that fails to import, or that has no source file, exits \`1\` with the reason.

### Recommended workflow

Commit the generated stubs, then gate on freshness:

\`\`\`bash
# Once, after declaring or changing Contracts
aq contracts stubs myapp.contracts
git add myapp/contracts.pyi
\`\`\`

\`\`\`yaml
# .github/workflows/ci.yml
- name: Check Contract stubs are current
  run: aq contracts stubs myapp.contracts --check

- name: Type check
  run: mypy myapp/
\`\`\`

Generation is deterministic — regenerating unchanged input is a byte-identical no-op, so \`--check\` cannot fail at random.

Full details in [Stub Generation & Deprecations](contracts_tooling.md).

---

## \`aq mail check\`

\`aq mail check\` validates mail configuration without sending anything. It now also validates DKIM configuration.

### Why

DKIM signing failures raise at send time rather than silently shipping an unsigned message — a receiving server treats a missing signature very differently from an invalid one, and an operator who enabled DKIM expects signed mail or a loud error. That is the right runtime behavior, but it means a misconfiguration is not discovered until the first real send, possibly in production.

\`aq mail check\` now surfaces both failure modes up front.

### New checks

When \`dkim_enabled\` is true:

1. **\`dkim_domain\` unset** — signing cannot proceed without a domain.
2. **\`dkimpy\` not installed** — the signing dependency is missing.

### Output

\`\`\`
$ aq mail check
DKIM is enabled but dkim_domain is unset -- sends will fail
DKIM is enabled but 'dkimpy' is not installed -- pip install aquilia[mail-dkim]
\`\`\`

A clean configuration reports no issues, as before.

### Recommended workflow

\`\`\`bash
# After enabling DKIM in workspace.py
pip install aquilia[mail-dkim]
aq mail check                          # verify configuration
aq mail send-test --to you@example.com # verify real delivery
\`\`\`

Add \`aq mail check\` to CI or a deploy preflight step for any application that sends mail.

---

## Unchanged Commands

\`aq mail send-test\` and \`aq mail inspect\` are unchanged. No flags were added, changed, or deprecated, and no output formats changed.

Background task workers are not started by a dedicated CLI command; a worker process is a normal Aquilia application configured with \`num_workers\` and a shared backend. See [Distributed & Persistent Backends](distributed_tasks.md).

---

## Related

- [Contracts — Stub Generation & Deprecations](contracts_tooling.md)
- [Mail Security & MIME](mail_security.md)
- [Migration Guide](migration.md)
`,
    "contracts_pipeline.md": `# Contracts — Nested Validation Pipeline — Aquilia v1.3.5

A deep audit of \`aquilia/contracts/\` found that a nested Contract's business rules never ran. \`Sigil.validate()\` recursed into the child's *structural* pass only — it validated field types and required-ness, then returned. Every \`@ward\` method and every object-level \`validate()\` override declared on a nested Contract was silently skipped.

This is the most severe defect fixed in this release. A nested Contract expressing an authorization check or a cross-field invariant enforced nothing, and the payload was accepted.

---

## 1. Nested Contracts never ran their wards or \`validate()\` hook

**Severity:** Critical — silent validation bypass.

### Previous behavior

\`\`\`python
from aquilia.contracts import Contract, ward
from aquilia.contracts.facets import IntFacet

class LineItem(Contract):
    qty = IntFacet()

    @ward
    def qty_positive(self, data):
        if data["qty"] < 1:
            self.reject("qty", "Must be at least 1")

class Order(Contract):
    items: list[LineItem] = None

order = Order(data={"items": [{"qty": 0}]})
order.is_sealed()   # True  ← the ward never ran
order.errors        # {}
\`\`\`

\`qty=0\` is structurally a valid integer, so the structural pass accepted it. The rule that says it is *business*-invalid never executed.

### Root cause

\`Sigil.validate()\` recursed directly into the child's compiled schema:

\`\`\`python
sub_errors, sub_validated = nested_cls._sigil.validate(raw, ...)
\`\`\`

A \`Sigil\` is the compiled *structural* representation of a Contract — field specs, types, required-ness. It has no knowledge of ward methods, which live on the Contract class and are invoked by \`Contract.is_sealed()\`. Because the nested Contract was never instantiated, \`is_sealed()\` was never called on it, so neither the ward phase nor the \`validate()\` hook ran.

This was not limited to async wards as originally reported. Synchronous wards were dead too.

### New behavior

Nested validation runs the child's full pipeline through a single shared helper, \`run_nested_contract()\`:

\`\`\`python
order = Order(data={"items": [{"qty": 0}]})
order.is_sealed()   # False
order.errors        # {"items": {"0": {"qty": ["Must be at least 1"]}}}
\`\`\`

Errors are reported at the failing field's path. For a to-many relation the row index is preserved rather than flattened away, so a client can point at the offending item.

\`\`\`python
order = Order(data={"items": [{"qty": 5}, {"qty": 0}]})
order.errors
# {"items": {"1": {"qty": ["Must be at least 1"]}}}
\`\`\`

### User impact

**This is a behavioral change.** Payloads that previously passed validation may now be rejected — correctly. If a nested Contract in your application declares a \`@ward\` or overrides \`validate()\`, that rule is now enforced for the first time.

Before upgrading, review nested Contracts for rules that were silently inert. A rule written against an assumption that no longer holds will now start rejecting traffic.

---

## 2. \`list[Contract]\` annotations bypassed the nested pipeline

**Severity:** Critical — the fix above did not reach the most common spelling.

### Previous behavior

A to-many nested relation has two spellings that mean the same thing to a reader:

\`\`\`python
# Spelling A — explicit facet
items = NestedContractFacet(LineItem, many=True)

# Spelling B — type annotation
items: list[LineItem] = None
\`\`\`

They build *different facets*. Spelling A builds a \`NestedContractFacet\` with \`many=True\`. Spelling B builds a \`ListFacet\` whose \`child\` is a \`NestedContractFacet\`.

Nested detection matched only \`NestedContractFacet\`, so spelling B was classified as an ordinary list of values. It ran structural validation alone — meaning the nested-pipeline fix in section 1 did not apply to it, and \`has_async_wards\` reported \`False\` for a Contract whose children declared async wards.

\`\`\`python
class Order(Contract):
    items: list[LineItem] = None       # ← annotated spelling

Order(data={}).has_async_wards          # False, even when LineItem has async wards
\`\`\`

Because \`has_async_wards\` gates which entry point the framework uses, reporting \`False\` sent callers down the synchronous path — where the async ward was skipped silently rather than raising \`ContractAsyncMismatchFault\`.

### Root cause

\`build_sigil()\` set \`is_nested_contract\` with a direct type check:

\`\`\`python
is_nested = isinstance(facet, (NestedContractFacet, LazyContractFacet))
\`\`\`

A \`ListFacet\` wrapping a nested facet is not an instance of either, so the flag was \`False\` and every downstream consumer — validation routing, async-ward detection, JSON Schema generation — treated the field as a plain list.

### New behavior

Detection now looks through container facets. Both spellings route identically:

\`\`\`python
class Order(Contract):
    items: list[LineItem] = None

order = Order(data={"items": [{"qty": 0}]})
order.is_sealed()   # False
order.errors        # {"items": {"0": {"qty": ["Must be at least 1"]}}}
\`\`\`

Async wards are detected through the list, so the sync entry point raises rather than skipping:

\`\`\`python
Order(data={}).has_async_wards          # True
Order(data={"items": [...]}).is_sealed()  # raises ContractAsyncMismatchFault
await Order(data={"items": [...]}).is_sealed_async()   # correct
\`\`\`

JSON Schema also improves, because an annotated list of Contracts is now emitted as an array of \`$ref\` rather than an untyped array:

\`\`\`python
Order._sigil.to_json_schema()["properties"]["items"]
# {"type": "array", "items": {"$ref": "#/$defs/LineItem"}}
\`\`\`

Two functions carry this:

| Function | Purpose |
|---|---|
| \`is_nested_facet(facet)\` | Whether a facet wraps a nested Contract, **without resolving it**. Used at class-body evaluation time, where a forward reference usually names the Contract currently being built. |
| \`resolve_nested(facet)\` | Returns \`(contract_cls, is_many)\`, looking through container facets. Returns \`(None, False)\` for an unresolvable forward reference rather than raising. |

\`get_nested_contract_cls()\` remains, now delegating to \`resolve_nested()\`, so existing callers are unaffected.

### User impact

The same behavioral change as section 1, now applying to the annotated spelling. Since \`items: list[LineItem]\` is the idiomatic form, most applications are affected by this fix rather than by section 1 alone.

---

## 3. \`has_async_wards\` consulted only the top-level class

**Severity:** High — silent skip instead of a clear error.

### Previous behavior

\`\`\`python
class Child(Contract):
    sku = TextFacet()

    @ward(mode="async")
    async def in_stock(self, data):
        if not await lookup(data["sku"]):
            self.reject("sku", "Out of stock")

class Parent(Contract):
    child: Child = None

Parent(data={}).has_async_wards   # False
\`\`\`

The property checked \`self._ward_methods\` — the wards declared on *this* class. A Contract whose nested child declared an async ward reported \`False\`, so callers took the synchronous path and the ward never ran. The intended failure mode was a loud \`ContractAsyncMismatchFault\`; the actual behavior was a silent skip.

### New behavior

The property walks the facet tree:

\`\`\`python
Parent(data={}).has_async_wards   # True
\`\`\`

Implementation notes that matter for correctness:

- **Memoized per class** (\`_async_wards_deep_cache\`) so the walk costs nothing after the first call. Contract classes are compiled once at import, so the answer cannot change at runtime.
- **Cycle detection** via a \`_seen\` set of class IDs, so a self-referential Contract (\`Node\` containing \`list[Node]\`) terminates.
- **Incomplete answers are never cached.** If the walk hits an unresolved forward reference or truncates at a cycle, the result is returned but not memoized — caching \`False\` from a truncated walk would permanently disable async detection for that class.

### User impact

A Contract with async wards nested beneath it now correctly requires \`is_sealed_async()\`. Code that called \`is_sealed()\` and appeared to work was not running the ward at all; it now raises \`ContractAsyncMismatchFault\` naming the problem.

---

## 4. No async serialization path existed

**Severity:** High — an async ORM with a sync-only serializer.

### Previous behavior

Aquilia's ORM relations are async, but every serialization entry point was synchronous. An un-awaited \`RelatedManager\` reaching \`Lens.mold()\` could only raise — there was no path that awaited it.

\`\`\`python
order = await Order.objects.get(pk=1)
OrderContract(instance=order).to_dict()
# LensUnresolvedFault — and no async alternative existed
\`\`\`

The only workaround was to prefetch every relation before serializing.

### New behavior

Three async entry points, mirroring the sync ones:

\`\`\`python
# Single instance
data = await OrderContract.to_dict_async(order)

# Collection
rows = await OrderContract.to_dict_many_async(orders)
\`\`\`

\`Lens.mold_async()\` awaits the relation, so prefetching becomes an optimization rather than a requirement:

\`\`\`python
class OrderContract(Contract):
    items = Lens(ItemContract, many=True)

order = await Order.objects.get(pk=1)          # items not prefetched
data = await OrderContract.to_dict_async(order)  # awaits order.items
\`\`\`

The synchronous path still raises \`LensUnresolvedFault\` — see section 5.

### Design: one field loop, two drivers

Sync and async serialization share a single field-molding generator, \`_mold_steps()\`, which yields \`(facet, raw_value)\` pairs for a driver to resolve:

\`\`\`python
# Sync driver
for facet, raw in self._mold_steps(...):
    result[name] = facet.mold(raw)

# Async driver
for facet, raw in self._mold_steps(...):
    result[name] = await facet.mold_async(raw)
\`\`\`

The field-selection logic — projections, \`write_only\` exclusion, computed fields, source resolution — exists once. A copy-paste async variant would drift from its sync twin at the first bug fix applied to only one of them.

### Performance

\`to_dict_async()\` awaits relations sequentially, one relation at a time. It is not slower than the sync path for prefetched data — awaiting an already-materialized list is close to free. For un-prefetched relations it issues one query per relation, so **prefetching remains the right choice on hot paths**; the async path exists so that forgetting to prefetch degrades performance rather than raising.

---

## 5. \`Lens(many=True)\` silently returned \`[]\` for unresolved relations

**Severity:** High — silent wrong data shipped to clients.

### Previous behavior

\`\`\`python
order = await Order.objects.get(pk=1)   # items NOT prefetched
OrderContract(instance=order).data
# {"items": []}   ← indistinguishable from "this order has no items"
\`\`\`

An un-awaited \`RelatedManager\` produced an empty list with no error. A client could not tell the difference between an order with no line items and an order whose line items failed to load.

### New behavior

\`\`\`python
OrderContract(instance=order).data
# LensUnresolvedFault (BP503): naming the field and the fix
\`\`\`

Three ways to resolve it:

\`\`\`python
# 1. Prefetch (best for hot paths)
order = await Order.objects.prefetch_related("items").get(pk=1)
OrderContract(instance=order).data

# 2. Materialize explicitly
order.items = await order.items.all()
OrderContract(instance=order).data

# 3. Use the async serializer, which awaits for you
await OrderContract.to_dict_async(order)
\`\`\`

### User impact

**This is a behavioral change.** Code relying on the silent empty-list fallback now raises. That fallback produced incorrect API responses — an empty relation and a failed-to-load relation are different facts, and conflating them ships wrong data without any signal.

---

## 6. Non-mapping input reported every field as missing

**Severity:** Medium — a misdiagnosis that cost debugging time.

### Previous behavior

A scalar or list request body was coerced to \`{}\`:

\`\`\`python
UserContract(data="not an object").errors
# {"name": ["This field is required"],
#  "email": ["This field is required"],
#  "age": ["This field is required"]}
\`\`\`

The real problem — the body was a string, not an object — was invisible. Developers chased missing fields that were never missing.

### New behavior

\`\`\`python
UserContract(data="not an object").errors
# {"__all__": ["Expected an object, got str"]}
\`\`\`

### User impact

**This is a behavioral change** in error *shape*, not in accept/reject. A malformed body previously produced per-field errors and now produces a single \`__all__\` entry. Clients that parse the 422 body and assume every key is a field name should treat \`__all__\` as a document-level error.

The same correction applies to the bulk paths:

\`\`\`python
UserContract.seal_many(["not a row"])[0].errors
# {"__all__": ["Expected an object, got str"]}
\`\`\`

---

## 7. Top-level async wards bypassed group and ordering semantics

**Severity:** Medium — inconsistent behavior between entry points.

### Previous behavior

\`is_sealed_async()\` ran async wards through its own inline loop rather than the shared ward phase. The result: \`order\`, \`when\`, \`groups\`, and \`Spec.fail_fast\` applied on the bulk paths (\`seal_many\`, \`seal_stream\`) but not on the single-item async path.

\`\`\`python
class Checkout(Contract):
    @ward(groups=("checkout",), mode="async")
    async def payment_valid(self, data): ...

await Checkout(data=...).is_sealed_async()   # ran the ward regardless of groups
\`\`\`

### Root cause

Duplicated logic. \`_run_ward_phase_async()\` already existed and implemented all four features; \`is_sealed_async()\` predated it and kept its own copy.

### New behavior

The duplicate loop is gone. \`is_sealed_async()\` calls \`_run_ward_phase_async()\`, so every entry point applies identical semantics:

\`\`\`python
await Checkout(data=...).is_sealed_async()                      # grouped ward skipped
await Checkout(data=...).is_sealed_async(groups="checkout")     # grouped ward runs
\`\`\`

---

## Input adapters: dataclasses, attrs, and TypedDict

Contracts now accept dataclass instances, attrs classes, and \`TypedDict\` values as input, at every level:

\`\`\`python
from dataclasses import dataclass

@dataclass
class LineItemDTO:
    qty: int

class Order(Contract):
    items: list[LineItem] = None

Order(data={"items": [LineItemDTO(qty=3)]}).is_sealed()   # True
\`\`\`

Adaptation happens at a single point (\`sigil.adapt_input\`) that feeds the *existing* cast/seal pipeline. There is no parallel validation path for dataclass input, so a dataclass and the equivalent dict validate identically.

Adaptation is **shallow by design**. A dataclass field holding another dataclass is handled by the nested-Contract branch, not by recursive adaptation — the nested Contract knows the target shape, and a blind deep walk would convert values the target facet expects to receive intact.

---

## Depth guard correctness

Two related fixes to the recursion guard:

### The guard was unreachable from the real validation path

\`MAX_NESTING_DEPTH = 32\` was enforced in \`NestedContractFacet.cast()\`. The primary path (\`Contract(data=...).is_sealed()\`) never called \`cast()\` — it recursed through the Sigil — so the guard and its tests were unreachable from ordinary request validation. A few kilobytes of deeply nested JSON against any endpoint accepting a self-referential Contract raised an uncaught \`RecursionError\` inside the request coroutine.

Depth is now threaded through \`Sigil.validate()\` and yields a structured error:

\`\`\`python
Node(data=deeply_nested).errors
# {"child": ["Nested Contract depth exceeds maximum of 32"]}
\`\`\`

\`MAX_NESTING_DEPTH\` moved to \`aquilia/contracts/exceptions.py\` so the Sigil and facet layers cannot disagree about the limit.

### The depth counter was global mutable state

\`NestedContractFacet._current_nesting_depth\` was a plain class attribute mutated with \`+=\`/\`-=\` — shared across every instance, every Contract class, and every thread, despite a source comment claiming thread-locality. Concurrent validation could both reject shallow payloads spuriously *and* undercount deep ones, defeating the guard exactly when it mattered.

It is now a \`contextvars.ContextVar\`, correct for threads and asyncio tasks alike, covered by a 20-thread concurrency test.

---

## Related pages

- [Contracts — Validation Control & Typing](contracts_validation.md) — ward ordering, groups, new facets, i18n messages
- [Contracts — Stub Generation & Deprecations](contracts_tooling.md) — \`aq contracts stubs\`, \`seal_*\` deprecation
- [Migration Guide](migration.md) — upgrade checklist and behavioral-change review
- [Bug Fixes](bugfixes.md) — task and mail subsystem fixes in this release
`,
    "contracts_tooling.md": `# Contracts — Stub Generation & Deprecations — Aquilia v1.3.5

Two developer-experience changes: a new \`aq contracts stubs\` command that makes Contract fields visible to \`mypy\` and \`pyright\`, and a formal deprecation of the \`seal_*\` / \`async_seal_*\` validator naming convention.

---

## \`aq contracts stubs\` — static typing support

### Motivation

A Contract resolves its fields at class-body evaluation time and serves them through \`__getattr__\`. Both are invisible to a static analyser:

\`\`\`python
class UserContract(Contract):
    email = TextFacet()
    age = IntFacet()

contract = UserContract(data=payload)
contract.is_sealed()
reveal_type(contract.email)   # Any — the type checker sees nothing
contract.emial                # typo: no error until runtime
\`\`\`

For a team running \`mypy --strict\` or \`pyright\` in CI, this was the single largest adoption barrier. Every Contract access was an untyped hole, and a field typo survived review to fail in production.

### Design goals

Two approaches were considered:

| Approach | Trade-off |
|---|---|
| A \`mypy\` plugin | Deep integration, but bespoke per type checker. \`pyright\` users get nothing. Plugin APIs are unstable across releases. |
| **Generated \`.pyi\` stubs** | A portable artifact every type checker consumes with no plugin, no configuration, and no version coupling. Checked into the repository like any other generated file. |

Stubs won. The output is inspectable, diffable in review, and works identically under \`mypy\`, \`pyright\`, and any editor's language server.

### Usage

\`\`\`bash
# Write myapp/contracts.pyi
aq contracts stubs myapp.contracts

# Several modules at once
aq contracts stubs myapp.users.contracts myapp.orders.contracts

# CI gate: fail if a stub is missing or stale
aq contracts stubs myapp.contracts --check
\`\`\`

| Flag | Purpose |
|---|---|
| \`--check\` | Do not write. Exit non-zero if any stub is missing or out of date. |
| \`--path\` | Directory prepended to \`sys.path\` before importing. Default: current directory. |

### Example output

Given:

\`\`\`python
# myapp/contracts.py
from __future__ import annotations

import enum

from aquilia.contracts import Contract
from aquilia.contracts.facets import ChoiceFacet, DecimalFacet, IntFacet, ListFacet, TextFacet


class Colour(enum.Enum):
    RED = "red"
    BLUE = "blue"


class AddressContract(Contract):
    city = TextFacet()
    zip = TextFacet(allow_null=True)


class OrderContract(Contract):
    id = IntFacet()
    total = DecimalFacet()
    tags = ListFacet(child=TextFacet())
    status = ChoiceFacet(choices=["new", "paid"])

    async def refresh(self, count: int) -> str: ...
\`\`\`

\`aq contracts stubs myapp.contracts\` produces:

\`\`\`python
# myapp/contracts.pyi
# Generated by \`aq contracts stubs\`. Do not edit by hand.
# Regenerate after changing the Contract declarations in the paired module.

from typing import Any, Literal
import enum
from aquilia.contracts import Contract
from aquilia.contracts.facets import ChoiceFacet, DecimalFacet, IntFacet, ListFacet, TextFacet
import aquilia.contracts.core
import decimal

class Colour(enum.Enum):
    RED = 'red'
    BLUE = 'blue'

class AddressContract(aquilia.contracts.core.Contract):
    city: str
    zip: str | None

class OrderContract(aquilia.contracts.core.Contract):
    id: int
    total: decimal.Decimal
    tags: list[str]
    status: Literal['new', 'paid']
    async def refresh(self, count: int) -> str: ...
\`\`\`

Now the type checker sees the fields:

\`\`\`python
reveal_type(contract.total)    # decimal.Decimal
reveal_type(contract.tags)     # list[str]
reveal_type(contract.status)   # Literal['new'] | Literal['paid']
\`\`\`

### How it works

Stubs are generated **at runtime, after \`ContractMeta\` has compiled the class** — that is what makes the facets inspectable. A purely static generator would have to re-implement annotation resolution and would drift from the real one.

Each facet reports the Python type it *produces*, through a \`python_type()\` method:

\`\`\`python
IntFacet().python_type()                         # "int"
DecimalFacet().python_type()                     # "decimal.Decimal"
ListFacet(child=TextFacet()).python_type()       # "list[str]"
ChoiceFacet(choices=["a", "b"]).python_type()    # "Literal['a', 'b']"
\`\`\`

Facets are the source of truth rather than a parallel mapping table in the generator, so a new facet declares its own type and stub generation picks it up with no second edit.

**The type is the post-cast type, not the wire type.** \`IntFacet\` accepts the string \`"42"\` on the wire but yields \`int\`, and the stub says \`int\` — that is what a caller reading \`contract.qty\` actually receives.

Notable resolutions:

| Facet | Emitted type | Reason |
|---|---|---|
| \`SecretFacet\` | \`Secret\` | \`cast()\` wraps the value. Promising \`str\` would let \`contract.password.lower()\` type-check and fail at runtime. |
| \`PathFacet\` | \`pathlib.PurePosixPath\` | The validated value, not the input string. |
| \`Lens(...)\` | \`dict[str, Any]\` | A Lens molds to a dict. Naming the Contract would let \`order.customer.is_sealed()\` type-check against a dict. |
| Nested Contract | \`dict[str, Any]\` | Same reason — the validated payload is a mapping. |
| \`EnumFacet(Colour)\` | \`myapp.enums.Colour\` | Fully qualified, so the import is derivable from the name. |

**Nullability is widened.** A facet accepting \`None\` — via \`allow_null\`, or by defaulting to it — is annotated optional:

\`\`\`python
zip = TextFacet(allow_null=True)     # → zip: str | None
\`\`\`

Omitting \`| None\` would be worse than emitting no stub at all: it tells the type checker a guard is unnecessary at exactly the points one is required.

### Limitations

**A \`.pyi\` replaces its module for the type checker — it does not augment it.** The generator therefore reproduces the whole module surface, not only its Contracts: import statements are replayed from the source AST, and module-level classes, functions, and constants are emitted with their runtime signatures.

Anything that cannot be rendered faithfully is emitted as \`Any\` and reported:

\`\`\`
  ✔ myapp.contracts: wrote /app/myapp/contracts.pyi
      2 contract(s): AddressContract, OrderContract
      REGISTRY: module-level value emitted as Any
\`\`\`

A lost annotation is named rather than silently weakening the module's types.

Other limits:

- The module must be importable. Import side effects run during generation.
- A module with no \`__file__\` — a namespace package, or a synthetic module — raises \`StubGenerationFault\` (\`BP600\`), since there is nowhere a stub could sit.
- Facets that declare no narrower type emit \`Any\` and appear in the degraded list.

### CI workflow

Commit the generated stubs, then gate on freshness:

\`\`\`yaml
- name: Check Contract stubs are current
  run: aq contracts stubs myapp.contracts myapp.orders.contracts --check
\`\`\`

\`--check\` exits non-zero when a stub is missing or stale, and prints the command to regenerate:

\`\`\`
  ✘ myapp.contracts: contracts.pyi is missing or out of date
      2 contract(s): AddressContract, OrderContract

  Stubs are out of date. Regenerate with:
      aq contracts stubs myapp.contracts
\`\`\`

Generation is deterministic — regenerating unchanged input is a byte-identical no-op, so \`--check\` cannot fail at random.

### Python API

The CLI is a thin wrapper; the same functions are importable:

\`\`\`python
from aquilia.contracts import generate_module_stub, write_module_stub
import myapp.contracts

report = write_module_stub(myapp.contracts)
report.path         # PosixPath('/app/myapp/contracts.pyi')
report.contracts    # ('AddressContract', 'OrderContract')
report.degraded     # () — members emitted as Any
report.is_current   # True

# Build without touching the filesystem
report = write_module_stub(myapp.contracts, dry_run=True)
\`\`\`

---

## Deprecated: the \`seal_*\` / \`async_seal_*\` prefix convention

**Deprecated in 1.3.0 — removed in 2.0.0.**

Before the \`@ward\` decorator existed, a method was registered as a cross-field validator purely because its name began with \`seal_\` or \`async_seal_\`. Declaring one now emits a \`DeprecationWarning\` at class-body evaluation:

\`\`\`
DeprecationWarning: OrderContract.seal_total is registered as a validator by the
deprecated seal_*/async_seal_* prefix convention (deprecated in Aquilia 1.3.0,
removed in 2.0.0). Decorate it with @ward instead — the method body does not need
to change, and you may then rename it freely. After 2.0.0, OrderContract.seal_total
will be treated as an ordinary method and will silently stop validating.
\`\`\`

**Behavior is unchanged in 1.x.** These methods continue to run exactly as before; only the warning is new. Deprecating the convention must not disarm it — a rule that stopped firing in a feature release would ship the exact bug the deprecation warns about.

### Why the convention is going away

Each of these has cost real debugging time:

- **A rename silently disables validation.** Renaming \`seal_total\` to \`check_total\` during a routine cleanup removes the rule with no error, no warning, and no failing test unless one happens to cover that exact rule. The Contract keeps reporting success on payloads it should reject.
- **A name collision silently creates one.** A helper legitimately named \`seal_envelope\` is executed as a validator on every request, its return value discarded and any exception it raises turned into a user-facing field error.
- **Async mode was inferred, not declared.** Mode came from \`inspect.iscoroutinefunction\`, so a validator awaiting the database while written as a sync \`def\` registered as sync — the coroutine was created, never awaited, and the check never ran.
- **No room to grow.** Ordering, conditions, and validation groups have nowhere to live in a naming convention. \`@ward\` carries them as metadata. See [Validation Control](contracts_validation.md#ward-ordering-conditions-and-groups).

### Migration

Mechanical — decorate the method. The body does not change.

\`\`\`python
# Before (deprecated)
class OrderContract(Contract):
    def seal_total(self, data):
        if data["total"] < 0:
            self.reject("total", "Must not be negative")

    async def async_seal_stock(self, data):
        if not await in_stock(data["sku"]):
            self.reject("sku", "Out of stock")

# After
class OrderContract(Contract):
    @ward
    def total_not_negative(self, data):          # rename is now safe
        if data["total"] < 0:
            self.reject("total", "Must not be negative")

    @ward(mode="async")
    async def stock_available(self, data):
        if not await in_stock(data["sku"]):
            self.reject("sku", "Out of stock")
\`\`\`

Two things change beyond the decorator: \`mode="async"\` becomes explicit rather than inferred, and the methods can be renamed to describe the rule rather than to satisfy the scanner.

Adding \`@ward\` without renaming is a valid intermediate step — the decorator is the registration, so the name becomes irrelevant and the warning goes quiet:

\`\`\`python
@ward
def seal_total(self, data): ...    # no warning; rename later at leisure
\`\`\`

### Finding every affected method

Promote the warning to an error and import your Contract modules:

\`\`\`bash
python -W error::DeprecationWarning -c "import myapp.contracts"
\`\`\`

Or fail the test suite on it:

\`\`\`toml
[tool.pytest.ini_options]
filterwarnings = ["error::DeprecationWarning"]
\`\`\`

Both report each legacy method with its class name, its exact replacement decorator, and the file and line that declared it. Because registration happens at class-body evaluation, **importing the module is enough** — no request needs to run.

### Version constants

The deprecation timeline is programmatically available:

\`\`\`python
from aquilia.contracts.ward import (
    DEPRECATED_PREFIX_SINCE,       # "1.3.0"
    DEPRECATED_PREFIX_REMOVED_IN,  # "2.0.0"
)
\`\`\`

---

## Related pages

- [Contracts — Validation Control & Typing](contracts_validation.md) — \`@ward\` ordering, conditions, and groups
- [Contracts — Nested Validation Pipeline](contracts_pipeline.md) — nested wards, async serialization
- [CLI Changes](cli.md) — all CLI changes in this release
- [Migration Guide](migration.md) — upgrade checklist
`,
    "contracts_validation.md": `# Contracts — Validation Control & Typing — Aquilia v1.3.5

The second half of the Contracts audit closed the gaps between what a Contract could express and what real validation needs: rule ordering, conditional rules, validation groups, fail-fast, frozen Contracts, and the strongly-typed primitives that previously fell through to a permissive \`TextFacet\`.

Everything here is additive. A Contract that declares none of it behaves exactly as it did in v1.3.4.

---

## Ward ordering, conditions, and groups

### Motivation

\`@ward\` had exactly one knob: \`mode\`. Real validation needs three more, and without them each was hand-rolled inside ward bodies where it could not be inspected, reordered, or reused.

| Need | Previous workaround |
|---|---|
| Run a cheap check before an expensive one | Rely on definition order and hope nobody reorders the methods |
| A rule that applies only to some payloads | \`if\` at the top of the ward body |
| Different rules for different operations | A separate Contract subclass per operation |

### \`order\` — deterministic sequencing

\`\`\`python
class OrderContract(Contract):
    @ward(order=-10)
    def total_not_negative(self, data):
        if data["total"] < 0:
            self.reject("total", "Must not be negative")

    @ward(order=0)          # default
    async def payment_authorized(self, data):
        ...                  # expensive: hits the payment provider
\`\`\`

Lower runs first. Wards sharing an \`order\` keep definition order — the sort is stable, so a Contract that sets no \`order\` behaves exactly as before.

Use it when one ward's rejection makes another's work redundant or misleading: there is no point authorizing payment on a negative total.

### \`when\` — conditional rules

\`\`\`python
class OrderContract(Contract):
    @ward(when=lambda data: data["kind"] == "physical")
    def needs_shipping_address(self, data):
        if not data.get("shipping_address"):
            self.reject("shipping_address", "Required for physical orders")
\`\`\`

The predicate receives the validated data. Moving the condition into metadata means the rule's applicability is inspectable rather than buried in the body.

**Edge case — a predicate that raises is treated as "does not apply."** The predicate is a routing decision, not a validation rule. A broken predicate must not manufacture a field error attributed to the ward it was gating, because that error would name the wrong field and the wrong cause.

### \`groups\` — per-operation rule sets

\`\`\`python
class UserContract(Contract):
    @ward(groups=("registration",))
    def password_strength(self, data):
        ...

    @ward(groups=("admin",))
    def role_assignable(self, data):
        ...

    @ward
    def email_wellformed(self, data):    # no groups — always runs
        ...
\`\`\`

Select groups per validation pass:

\`\`\`python
contract.is_sealed(groups="registration")
contract.is_sealed(groups=["registration", "admin"])
await contract.is_sealed_async(groups="checkout")
\`\`\`

**An ungrouped ward always runs.** It expresses an invariant that holds regardless of which group the caller asked for — an email must be well-formed whether or not this is a registration. Grouping an invariant would silently disable it for every pass that did not name its group.

Groups propagate to nested Contracts, so a group selected at the top level applies through the whole tree.

### \`Spec.fail_fast\`

\`\`\`python
class OrderContract(Contract):
    class Spec:
        fail_fast = True

    @ward
    def first(self, data): ...
    @ward
    def second(self, data): ...    # never runs if \`first\` rejected
\`\`\`

Stops at the first ward error instead of accumulating all of them. Default is \`False\`, unchanged — accumulating every error is the right default for a form, where a user should see all problems at once. \`fail_fast\` suits pipelines where a later rule's output would be noise once an earlier one has failed.

Applies to the ward phase only; structural field validation always accumulates.

---

## Frozen Contracts, equality, and copy

### \`Spec.frozen\`

\`\`\`python
class ConfigContract(Contract):
    port = IntFacet()

    class Spec:
        frozen = True

config = ConfigContract(data={"port": 8000})
config.is_sealed()
config.validated_data["port"] = 9000     # TypeError
\`\`\`

**Motivation:** \`is_sealed()\` returning \`True\` is a guarantee that the data satisfied every rule. That guarantee expires the moment a caller assigns to a field. Freezing makes the guarantee durable for the lifetime of the object.

### \`Contract.__eq__\`

\`\`\`python
a = UserContract(data={"name": "Ada"})
b = UserContract(data={"name": "Ada"})
a.is_sealed(); b.is_sealed()
a == b     # True
\`\`\`

Two Contracts are equal when they are the same class and carry the same validated data. Unvalidated Contracts compare on their raw input, so a comparison before sealing is still meaningful rather than degrading to identity.

**Contracts remain unhashable:**

\`\`\`python
hash(a)
# TypeError: UserContract is unhashable (its validated data is mutable)
\`\`\`

This is deliberate. Defining \`__eq__\` without \`__hash__\` would make Python set \`__hash__ = None\` silently; an explicit \`__hash__\` that raises names the reason instead. Validated data is mutable by default, so a hash computed at insertion time would go stale and the object would become unfindable in its own dict.

### \`copy(update=...)\`

\`\`\`python
updated = contract.copy(update={"name": "Grace"})
\`\`\`

Derives a new Contract with fields replaced. Keys absent from \`update\` carry over.

**Re-validates by default.** An override can violate a constraint the original satisfied, and skipping validation would produce a Contract whose \`validated_data\` never passed the rules it claims to enforce:

\`\`\`python
contract.copy(update={"age": -5})
# SealFault — the override is validated, not trusted
\`\`\`

Defer validation when building a payload in stages:

\`\`\`python
draft = contract.copy(update={"name": "Grace"}, validate=False)
final = draft.copy(update={"email": "g@example.com"})    # validates here
\`\`\`

For Contracts with async wards, use \`copy_async()\`:

\`\`\`python
updated = await contract.copy_async(update={"sku": "ABC"})
\`\`\`

\`copy()\` on a Contract with async wards raises \`ContractAsyncMismatchFault\` rather than silently skipping them.

---

## New facets

Four types previously fell through to a permissive \`TextFacet\` or had no facet at all.

### \`BytesFacet\`

Binary data over a JSON transport.

\`\`\`python
class UploadContract(Contract):
    payload = BytesFacet()                    # base64 (default)
    checksum = BytesFacet(encoding="hex")

UploadContract(data={"payload": "aGVsbG8=", "checksum": "68656c6c6f"})
# validated_data: {"payload": b"hello", "checksum": b"hello"}
\`\`\`

**Bug fixed:** \`bytes\` annotations previously mapped to \`TextFacet\`, whose cast whitelist *rejects real \`bytes\`*. A \`payload: bytes\` field rejected every genuine value while accepting plain strings — non-functional end to end. \`bytes\` annotations now route to \`BytesFacet\`.

Size constraints apply to the **decoded** length, which is what matters for storage and memory:

\`\`\`python
thumbnail = BytesFacet(max_length=64 * 1024)
\`\`\`

Always bound \`max_length\` on a client-facing binary field. Base64 expands roughly 33%, so a modest request body still decodes to a large allocation — an unbounded field is a memory-exhaustion vector.

JSON Schema emits \`{"type": "string", "format": "byte"}\`.

### \`PathFacet\`

Filesystem paths, validated as \`pathlib.PurePosixPath\`.

\`\`\`python
class UploadContract(Contract):
    destination = PathFacet()

UploadContract(data={"destination": "reports/q3.pdf"})
# validated_data: {"destination": PurePosixPath('reports/q3.pdf')}
\`\`\`

**Security defaults reject the two ways a client-supplied path escapes its root:**

| Input | Result | Why |
|---|---|---|
| \`/etc/passwd\` | \`Path must be relative\` | \`Path("/root") / "/etc/passwd"\` resolves to \`/etc/passwd\`, discarding the root |
| \`../../etc/passwd\` | \`Path may not contain '..' segments\` | Traversal out of the intended directory |
| \`a\\x00b\` | \`Path may not contain null bytes\` | Truncates at the OS layer, so a name passing an extension check can open a different file |

Null bytes are rejected unconditionally. The other two relax only for paths that never originate from a request:

\`\`\`python
destination = PathFacet(must_be_relative=False, allow_traversal=True)
\`\`\`

Windows separators are normalized before the \`..\` check, so a backslash cannot smuggle a segment past it on a POSIX server.

Values are \`PurePosixPath\` so a payload validates identically regardless of server platform. Convert with \`Path(value)\` at the point of filesystem access.

### \`SecretFacet\` and \`Secret\`

Sensitive strings that never appear in output or tracebacks.

\`\`\`python
class LoginContract(Contract):
    password = SecretFacet(min_length=8)

contract = LoginContract(data={"password": "hunter2hunter2"})
contract.is_sealed()

repr(contract.validated_data["password"])       # "Secret('**********')"
str(contract.validated_data["password"])        # "**********"
contract.validated_data["password"].reveal()    # "hunter2hunter2"
\`\`\`

\`write_only\` by default, so the field is accepted inbound and omitted from every serialized representation.

**Equality is constant-time** (\`hmac.compare_digest\`), so comparing a submitted value against a stored one does not leak the shared-prefix length through timing:

\`\`\`python
if contract.validated_data["password"] == stored_secret:   # constant-time
    ...
\`\`\`

**Security scope:** masking defends against *accidental* disclosure — log lines, exception reports, debug pages. It is not a substitute for hashing or encryption at rest. Call \`.reveal()\` only at the point of use.

JSON Schema emits \`{"type": "string", "format": "password", "writeOnly": true}\`.

### \`MACAddressFacet\`

\`\`\`python
class DeviceContract(Contract):
    mac = MACAddressFacet()
\`\`\`

Accepts colon, dash, and Cisco notations, normalizing to lowercase colon-separated form:

| Input | Validated value |
|---|---|
| \`AA:BB:CC:DD:EE:FF\` | \`aa:bb:cc:dd:ee:ff\` |
| \`aa-bb-cc-dd-ee-ff\` | \`aa:bb:cc:dd:ee:ff\` |
| \`aabb.ccdd.eeff\` | \`aa:bb:cc:dd:ee:ff\` |

Normalizing at validation means downstream comparisons and database lookups do not each reimplement it.

### Annotation routing

These types now resolve to the right facet from a plain annotation:

\`\`\`python
import ipaddress, pathlib
from aquilia.contracts.facets import Secret

class DeviceContract(Contract):
    address: ipaddress.IPv4Address    # IPFacet
    config_path: pathlib.Path         # PathFacet
    api_key: Secret                   # SecretFacet
\`\`\`

---

## \`IntFacet\` no longer truncates silently

### Previous behavior

\`\`\`python
class QuantityContract(Contract):
    qty = IntFacet()

QuantityContract(data={"qty": 3.9}).validated_data["qty"]   # 3   ← silently truncated
QuantityContract(data={"qty": "3.9"}).errors                # rejected
\`\`\`

The same logical input behaved differently depending on its wire type. A JSON body with \`3.9\` was accepted and quietly became \`3\`; the string \`"3.9"\` was correctly rejected.

### New behavior

\`\`\`python
QuantityContract(data={"qty": 3.9}).errors
# {"qty": ["Expected integer, got non-integer number 3.9"]}

QuantityContract(data={"qty": 3.0}).is_sealed()   # True — integral float still accepted
\`\`\`

\`NaN\` and \`Infinity\` are rejected explicitly.

**This is a behavioral change.** Payloads previously accepted with silent truncation now fail validation. Silent truncation of a quantity, a price in cents, or a page offset is a data-integrity bug that surfaces far from its cause.

---

## Alternate data sources

### \`Contract.from_env()\`

\`\`\`python
class SettingsContract(Contract):
    port = IntFacet(default=8000)
    database_url = TextFacet()

settings = SettingsContract.from_env(prefix="APP_")
# reads APP_PORT and APP_DATABASE_URL
\`\`\`

Field names map to upper-case variable names. Absent variables are **omitted rather than set empty**, so each field's \`default\` and \`required\` rules decide the outcome exactly as they would for a JSON body.

Every value arrives as a string; normal facet casting turns \`"8000"\` into an \`int\`. Configuration therefore gets the same validation as request data instead of a parallel parsing path.

**Validates by default** — configuration errors should surface at startup, not at first use. Pass \`seal=False\` to defer.

### \`Contract.from_cli()\`

\`\`\`python
class ImportContract(Contract):
    source = TextFacet()
    dry_run = BoolFacet(default=False)
    tags = ListFacet(child=TextFacet(), required=False)

options = ImportContract.from_cli(["--source", "data.csv", "--dry-run",
                                   "--tags", "a", "--tags", "b"])
# {"source": "data.csv", "dry_run": True, "tags": ["a", "b"]}
\`\`\`

Parses \`--flag value\`, \`--flag=value\`, and bare \`--flag\` (boolean). Dashes map to underscores, so \`--database-url\` fills \`database_url\`. A repeated flag collects into a list for a \`ListFacet\` to validate.

**Limitations, deliberately:** a small parser for feeding a Contract, not a replacement for the \`aq\` CLI's Click layer. Unknown flags are ignored so a Contract can read the subset of arguments it cares about from a larger command line. No short flags, no subcommands, no \`--\` terminator.

---

## Localized validation messages

Every built-in validation message now resolves through \`contract_message()\`:

\`\`\`python
from aquilia.contracts.messages import contract_message

contract_message("min_length", min=5)
# "Must be at least 5 characters"
\`\`\`

Resolution order:

1. The active i18n catalog's \`contracts.\` namespace, if an i18n service is bound to the request.
2. The built-in English default, with ICU-style \`{name}\` parameter substitution.

\`\`\`yaml
# locales/fr/messages.yaml
contracts:
  required: "Ce champ est obligatoire"
  min_length: "Doit contenir au moins {min} caractères"
\`\`\`

The service and locale are read from \`contextvars\`, so a request's locale applies to validation errors raised anywhere in its call tree without threading a locale parameter through every facet.

**Applications without i18n configured see byte-identical messages** to v1.3.4.

**Resolution never raises.** A missing key, a malformed template, or a broken i18n service falls back to the built-in text. Failing to render the message for a rejected payload would turn a 422 into a 500 — the client would lose the validation errors entirely because of a translation problem.

33 message keys ship: field presence, type, length, numeric range, collection size, choice, format (email/URL/slug/IP/MAC/UUID), and path safety.

---

## Related pages

- [Contracts — Nested Validation Pipeline](contracts_pipeline.md) — the nested-pipeline and async serialization fixes
- [Contracts — Stub Generation & Deprecations](contracts_tooling.md) — \`aq contracts stubs\`, \`seal_*\` deprecation
- [Migration Guide](migration.md) — upgrade checklist and behavioral-change review
`,
    "distributed_tasks.md": `# Distributed & Persistent Task Backends — Aquilia v1.3.5

Background tasks now run across multiple worker processes and multiple machines, with job state that survives a restart. Before this release the only backend was \`MemoryBackend\`: jobs lived in the worker process and were lost on restart, and \`backend="redis"\` logged a warning and silently fell back to in-memory.

---

## Motivation

The task system was single-process. That is fine for a cron-like cleanup job, but it fails the moment an application scales horizontally:

- Two web workers each ran their own queue, so a periodic task fired twice.
- A deploy dropped every queued job on the floor.
- A worker crash lost whatever that worker was executing, permanently.
- \`Integration.tasks(backend="redis")\` was accepted by config validation and then ignored at runtime.

---

## Design Goals

1. **Backend choice is configuration, not code.** Task functions, decorators, and \`enqueue()\` calls are identical on every backend.
2. **No lost work on crash.** A worker that dies mid-job must have that job picked up by a peer.
3. **Fail at enqueue, not on a remote worker.** Anything that cannot cross a process boundary must be rejected at the call site, where the stack trace is useful.
4. **Existing single-process apps unaffected.** \`memory\` stays the default and behaves exactly as before.

---

## Architecture

### Job serialization

A job that crosses a process boundary cannot carry a live Python callable or arbitrary objects. Two new methods on \`Job\` define the transport form:

\`\`\`python
payload = job.to_payload()      # JSON-compatible dict
restored = Job.from_payload(payload)
\`\`\`

\`to_payload()\` validates \`args\` and \`kwargs\` against \`json.dumps\` and raises \`TaskSerializationFault\` if they cannot be represented. \`from_payload()\` deliberately leaves the callable unset — the worker resolves it from \`func_ref\` through the \`@task\` registry, so a queue entry can never name a function the application did not register.

\`Job.to_dict()\` is unchanged and remains the human-facing view used by the admin dashboard.

### Lease-based claiming

Both durable backends use the same coordination model:

1. A worker claims a job and takes a lease for \`lease_seconds\` (default \`300.0\`).
2. While executing, it renews the lease every \`heartbeat_interval\` seconds (default \`30.0\`).
3. A background reclaim loop sweeps every \`reclaim_interval\` seconds (default \`60.0\`) and returns jobs whose lease lapsed to the runnable pool.

If a worker is killed, its lease expires and a peer reclaims the job instead of the job being lost.

**This is at-least-once delivery.** A worker that stalls past its lease — a long GC pause, a blocked event loop — can have its job reclaimed and executed a second time. Task functions should be idempotent.

### \`RedisBackend\`

Multi-process and multi-machine, backed by Redis. Claims are atomic through a Lua script against a sorted set; fingerprint reservation uses \`SET NX\`. Fastest option, and the right default for high throughput.

### \`SQLBackend\`

Durable state on the database the application already uses — no new infrastructure. Works on SQLite, PostgreSQL, MySQL, and Oracle through Aquilia's existing parameterized query layer.

A claim is a conditional \`UPDATE ... WHERE id = ? AND state = ?\` inside a transaction; \`rowcount == 0\` means another worker won the race, so the loser moves on rather than double-running the job. This works on every supported dialect without needing \`SELECT ... FOR UPDATE SKIP LOCKED\`, which SQLite does not have.

Two tables are created on first \`initialize()\`:

\`\`\`
aquilia_tasks(
    id TEXT PRIMARY KEY, queue TEXT, priority INTEGER, state TEXT,
    func_ref TEXT, payload TEXT,             -- full JSON job
    available_at TEXT,                        -- when it may run
    lease_expires_at TEXT, owner TEXT,        -- distributed claim
    dedup_key TEXT, workflow_id TEXT,
    created_at TEXT, completed_at TEXT, sequence INTEGER
)
aquilia_task_locks(fingerprint TEXT PRIMARY KEY, job_id TEXT, expires_at TEXT)
\`\`\`

The unique primary key on \`aquilia_task_locks.fingerprint\` is what makes deduplication correct under concurrency: two workers racing to reserve the same fingerprint both attempt an \`INSERT\`, and the database rejects exactly one.

Redis is faster and scales further. SQL wins when you cannot add a Redis dependency, or when you want jobs to commit in the *same transaction* as the business data that created them, so a rolled-back request cannot leave an orphaned job behind. Above roughly a few hundred jobs/second, prefer Redis.

---

## Configuration

\`\`\`python
# workspace.py

# Development — single process, non-durable (default, unchanged)
Integration.tasks(num_workers=4)

# Production — distributed workers, durable queue
Integration.tasks(
    backend="redis",
    redis_url="redis://cache:6379/0",
    redis_prefix="aquilia:tasks:",
    num_workers=16,
    lease_seconds=120,
    heartbeat_interval=30,
    reclaim_interval=60,
)

# Durable without extra infrastructure
Integration.tasks(backend="sql", sql_table="aquilia_tasks")
\`\`\`

### New options

| Option | Default | Purpose |
|---|---|---|
| \`backend\` | \`"memory"\` | \`"memory"\`, \`"redis"\`, or \`"sql"\` (aliases: \`"database"\`, \`"db"\`) |
| \`redis_url\` | \`None\` | Redis connection URL; falls back to \`$REDIS_URL\` |
| \`redis_prefix\` | \`"aquilia:tasks:"\` | Key namespace, so several apps can share one Redis |
| \`sql_table\` | \`"aquilia_tasks"\` | Job table name for the SQL backend |
| \`lease_seconds\` | \`300.0\` | How long a claimed job stays owned before a peer may reclaim it |
| \`heartbeat_interval\` | \`30.0\` | Lease renewal cadence; must be well under \`lease_seconds\` |
| \`reclaim_interval\` | \`60.0\` | How often to sweep for jobs abandoned by crashed workers |
| \`dedup_ttl\` | \`3600.0\` | How long a deduplication reservation is held |
| \`worker_id\` | \`None\` | Worker identity recorded as a job's owner; defaults to \`hostname:pid:random\` |

Install the Redis extra with \`pip install aquilia[redis]\`. The SQL backend requires \`Integration.database(...)\` and no extra dependency.

---

## Usage

Task code does not change between backends:

\`\`\`python
from aquilia.tasks import task

@task(queue="reports", max_retries=3)
async def rebuild_report(report_id: int) -> dict:
    return {"rebuilt": report_id}
\`\`\`

\`\`\`python
job_id = await tasks.enqueue(rebuild_report, 42)
job = await tasks.get_job(job_id)
\`\`\`

### Running a dedicated worker process

A process that only consumes work is a normal Aquilia app with \`num_workers\` set and no enqueueing of its own. The queues it polls are derived from the \`@task\` descriptors it has imported, plus any queue it discovers on the shared backend — so a worker does not need to know in advance which queues its producers use.

---

## Edge Cases

**Non-serializable arguments.** On a persistent backend, passing an object JSON cannot represent raises \`TaskSerializationFault\` at \`enqueue()\`:

\`\`\`python
await tasks.enqueue(process, open("f.txt"))   # TaskSerializationFault
\`\`\`

This is deliberate. The alternative is a job that enqueues cleanly and then fails unrecoverably on a remote worker, far from the call site. On \`MemoryBackend\` live objects still work, because the job never leaves the process.

**Unregistered task names.** A worker resolves \`func_ref\` through the \`@task\` registry. If the consumer process has not imported the module that registers the task, the job raises \`TaskResolutionFault\` rather than executing arbitrary named code. Ensure every worker imports the same task modules.

**Backend unavailable at startup.** A Redis or database that cannot be reached logs an error naming the durability that was lost and falls back to \`MemoryBackend\`, rather than aborting startup. The application still serves requests; queued jobs are not durable until the backend recovers and the process restarts.

**Unknown backend name.** A typo such as \`backend="rabbitmq"\` logs a warning listing the valid values and uses \`MemoryBackend\`. A typo does not take production down.

**Clock skew across machines.** Leases are stored as absolute timestamps. Significant clock skew between workers can cause premature reclaim (duplicate execution) or delayed reclaim. Run NTP.

---

## Performance Implications

- \`MemoryBackend\` is unchanged; single-process applications see no difference.
- \`RedisBackend\` claim is one round trip against an in-memory sorted set.
- \`SQLBackend\` claim is one \`UPDATE\` inside a transaction. Throughput is bounded by database write capacity; above a few hundred jobs/second prefer Redis.
- The reclaim loop runs once per \`reclaim_interval\` per process and issues one sweep query. Raising \`reclaim_interval\` reduces load; lowering it shortens the window during which a crashed worker's job sits idle.

---

## Compatibility

Fully backward compatible. \`memory\` remains the default, \`MemoryBackend\` behavior is unchanged, and every existing \`@task\` and \`enqueue()\` call works untouched. The new configuration options are additive with defaults matching prior behavior.

---

## Related

- [Workflows & DAGs](workflows.md) — composing jobs, which requires a shared backend to span processes
- [Idempotency & Deduplication](idempotency.md) — the distributed lock built on this coordination layer
- [Mail Delivery Queue](mail_queue.md) — the first framework subsystem to run on it
- [Migration Guide](migration.md)
`,
    "http_native.md": `# Native HTTP Client & Third-Party HTTP Removal — Aquilia v1.3.5

In Aquilia v1.3.5, all remaining traces of third-party HTTP clients (specifically \`httpx\`) have been completely removed from the framework codebase, dependencies, test suite, and documentation in favor of Aquilia's native zero-dependency \`aquilia.http\` client.

---

## 1. Overview & Motivation

Aquilia features a production-grade, fully asynchronous HTTP client implementation in \`aquilia.http\` built directly on Python standard library primitives (\`asyncio\`, \`ssl\`, \`gzip\`, \`zlib\`).

Previously, optional subsystems like \`SendGridProvider\` and test helpers like \`LiveServerTestCase\` relied on \`httpx\` as a third-party dependency. In v1.3.5:

1. **SendGrid Mail Provider** (\`aquilia.mail.providers.sendgrid.SendGridProvider\`) uses native \`aquilia.http.AsyncHTTPClient\`.
2. **\`LiveServerTestCase\`** (\`aquilia.testing.cases.LiveServerTestCase\`) documentation and usage examples use native \`aquilia.http.AsyncHTTPClient\`.
3. **Dependency Clean-Up**: \`httpx\` has been removed from \`pyproject.toml\`, \`setup.py\`, \`aquilia.egg-info\`, and all extra dependency bundles (\`mail-sendgrid\`, \`testing\`, \`dev\`).

---

## 2. Changes in SendGrid Provider

The \`SendGridProvider\` now initializes \`AsyncHTTPClient\` directly from \`aquilia.http\`:

\`\`\`python
from aquilia.http import AsyncHTTPClient

class SendGridProvider:
    async def initialize(self) -> None:
        self._client = AsyncHTTPClient(
            base_url=self.api_base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "aquilia-mail/1.0",
            },
            timeout=self.timeout,
        )
\`\`\`

Error handling consumes the async \`HTTPClientResponse\` API:

\`\`\`python
body = await response.json()
\`\`\`

---

## 3. Backward Compatibility & \`aclose\` Alias

To ensure smooth transition for any external callers expecting \`aclose()\`, \`aquilia.http.AsyncHTTPClient\` now provides an alias:

\`\`\`python
class AsyncHTTPClient:
    async def close(self) -> None: ...

    aclose = close
\`\`\`

Both \`await client.close()\` and \`await client.aclose()\` work seamlessly.

---

## 4. Dependencies Updated

- \`mail-sendgrid\` extra: no longer installs \`httpx\`.
- \`testing\` extra: no longer installs \`httpx\`.
- \`dev\` extra: no longer installs \`httpx\`.
`,
    "idempotency.md": `# Idempotency & Distributed Deduplication — Aquilia v1.3.5

\`Job.fingerprint\` existed since the task system shipped but nothing ever read it. As of v1.3.5 it is enforced at enqueue time, and on durable backends that enforcement is a real distributed lock: two processes racing to queue the same work produce one job, not two.

---

## Motivation

The classic double-send. A user double-clicks, a retried HTTP request replays, a webhook is delivered twice, two web workers react to the same event — and the same background job is queued twice. Applications worked around this with their own Redis \`SETNX\` guards or a \`processed\` table, reimplementing per project what the framework already had the raw material for.

\`Job.fingerprint\` was computed and stored. It simply had no readers.

---

## How It Works

### The fingerprint

A stable digest over \`func_ref\`, \`queue\`, \`args\`, and \`kwargs\` — two enqueue calls that would do identical work share a fingerprint:

\`\`\`python
job.fingerprint    # 12-hex-character digest
\`\`\`

It is computed from the JSON form when possible, so equal-but-not-identical values agree across processes: a tuple \`(1, 2)\` and a list \`[1, 2]\` produce the same fingerprint. Non-JSON values fall back to \`repr\`, which keeps the in-memory backend working with live objects.

### The \`dedup\` parameter

\`\`\`python
await manager.enqueue(rebuild_index, dedup="allow")   # default — always enqueue
await manager.enqueue(rebuild_index, dedup="skip")    # return the in-flight job's ID
await manager.enqueue(rebuild_index, dedup="raise")   # raise TaskDuplicateFault
\`\`\`

| Mode | Behavior |
|---|---|
| \`"allow"\` | Always enqueue. Preserves historical behavior, so existing code is unaffected. |
| \`"skip"\` | If identical work is already in flight, return that job's ID instead of enqueueing a second copy. |
| \`"raise"\` | Raise \`TaskDuplicateFault\` instead. Use when a duplicate indicates a caller bug. |

A reservation is held for \`dedup_ttl\` seconds (default \`3600.0\`) and released when the job reaches a terminal state.

### Distributed enforcement

The backend owns the reservation, so correctness under concurrency comes from the storage layer, not from application-level check-then-act:

- **\`RedisBackend\`** — \`SET NX\` on the fingerprint key. Exactly one caller wins.
- **\`SQLBackend\`** — \`INSERT\` into \`aquilia_task_locks\`, whose \`fingerprint\` column is the primary key. Two workers racing both attempt the insert and the database rejects exactly one.
- **\`MemoryBackend\`** — an in-process map, correct within a single process.

---

## Examples

### Collapsing a burst

\`\`\`python
# Ten requests arrive; one job runs.
job_id = await tasks.enqueue(rebuild_search_index, dedup="skip")
\`\`\`

### Treating a duplicate as an error

\`\`\`python
from aquilia.tasks import TaskDuplicateFault

try:
    await tasks.enqueue(charge_card, order_id, dedup="raise")
except TaskDuplicateFault:
    return Response.json({"status": "already_processing"}, status=409)
\`\`\`

### Across processes

\`\`\`python
# Web worker A and web worker B, sharing one Redis or SQL backend
a = await tasks.enqueue(send_invoice, order_id, dedup="skip")
b = await tasks.enqueue(send_invoice, order_id, dedup="skip")
assert a == b   # one job
\`\`\`

---

## Before vs After

\`\`\`python
# Before v1.3.5 — hand-rolled guard in every application
lock_key = f"job:invoice:{order_id}"
if await redis.set(lock_key, "1", nx=True, ex=3600):
    await tasks.enqueue(send_invoice, order_id)
\`\`\`

\`\`\`python
# v1.3.5
await tasks.enqueue(send_invoice, order_id, dedup="skip")
\`\`\`

The framework version is also correct in a case the hand-rolled one usually is not: the reservation is released when the job reaches a terminal state, so a failed job can be retried immediately instead of being blocked until the TTL expires.

---

## Edge Cases

**Deduplication suppresses duplicate *enqueues*, not duplicate *execution*.** Distributed backends are at-least-once: a job whose worker stalls past its lease may be reclaimed and run twice. Task functions should still be idempotent. These are two different guarantees and \`dedup\` provides only the first.

**Fingerprints include the queue.** The same function with the same arguments on two different queues is two different fingerprints, and both will be enqueued.

**Argument order matters for positional arguments.** \`f(1, 2)\` and \`f(2, 1)\` are distinct. Keyword arguments are sorted, so \`f(a=1, b=2)\` and \`f(b=2, a=1)\` match.

**Non-JSON arguments still deduplicate in-process.** The \`repr\` fallback means two live objects deduplicate only if their \`repr\` matches. On a persistent backend such arguments raise \`TaskSerializationFault\` before dedup is reached.

**The default is unchanged.** Existing code that never passes \`dedup\` continues to enqueue every call. This is deliberate — silently collapsing jobs in an existing application would be a breaking behavioral change.

---

## Performance Implications

\`dedup="allow"\` (the default) adds no work: no fingerprint reservation is attempted. \`"skip"\` and \`"raise"\` add one reservation operation per enqueue — a single \`SET NX\` on Redis, a single \`INSERT\` on SQL. In exchange, collapsed duplicates avoid an entire job execution.

---

## Compatibility

Fully backward compatible. \`dedup\` is a new keyword-only parameter defaulting to \`"allow"\`, which is exactly the prior behavior. \`TaskDuplicateFault\` is a new fault raised only when explicitly requested via \`dedup="raise"\`.

---

## Related

- [Distributed & Persistent Backends](distributed_tasks.md) — the coordination layer this builds on
- [Workflows & DAGs](workflows.md)
- [Migration Guide](migration.md)
`,
    "mail_queue.md": `# Mail Delivery Queue — Aquilia v1.3.5

Outbound mail can now be delivered by background workers instead of inside the request handler. \`send_message()\` persists an envelope, schedules a delivery job, and returns — the SMTP conversation happens on a worker, with retries, backoff, and delayed sends managed by the task scheduler.

This reuses Aquilia's existing task system. No second queue implementation was introduced.

---

## Motivation

Sending mail inside a request handler ties the response time of a user-facing endpoint to a third party's SMTP latency. A slow provider makes signup slow; an unreachable provider makes signup fail. Retrying meant either blocking the request further or losing the message.

---

## Design Goals

1. **Reuse the scheduler.** Retries, delayed delivery, persistence, and worker execution are the task system's job, not mail's.
2. **Same API whether queued or not.** Enabling the queue is a configuration change; call sites are unchanged.
3. **Survive the jump to distributed workers with no API change.** The delivery job had to be designed for a persistent backend from day one.
4. **Never accept mail that cannot be sent.** Recording an envelope as queued when nothing can deliver it is worse than sending inline.

---

## Architecture

\`\`\`
send_message()
  │
  ├─ build envelope (validate, apply suppression, dedupe)
  ├─ EnvelopeStore.save(envelope)          ← durable record
  └─ enqueue "aquilia.mail.deliver"(envelope_id)
                    │
                    ▼
             task worker (possibly another process)
                    │
                    ├─ EnvelopeStore.get(envelope_id)
                    ├─ provider.send(...)  → SENT
                    └─ on failure → schedule retry with backoff
\`\`\`

### \`EnvelopeStore\`

The durable record of accepted mail. Two implementations ship:

| Class | Durability |
|---|---|
| \`MemoryEnvelopeStore\` | In-process, bounded (\`max_envelopes\`, default 10,000). Default. |
| \`SQLEnvelopeStore\` | Application database, table \`aquilia_mail_envelopes\`. |

The interface covers \`save\`, \`get\`, \`list_by_status\`, \`find_by_digest\`, \`find_by_idempotency_key\`, \`cleanup\`, and \`stats\`.

### The delivery task

Delivery is a registered task named \`aquilia.mail.deliver\`, on queue \`mail\`.

**It takes an envelope ID, not an envelope.** A live \`MailEnvelope\` cannot survive a persistent or distributed backend, which serializes jobs as JSON. The worker — which may be in another process entirely — reloads the envelope from the shared store. This is what lets mail delivery run on another machine without any API change.

It is registered under a stable name rather than enqueued as a bare callable, so a worker in another process resolves it through the \`@task\` registry; a module-path reference would not survive a rename.

Mail owns its own retry policy, so the job is enqueued with \`max_retries=0\` and the mail service schedules its own follow-up attempts with backoff.

---

## Configuration

\`\`\`python
# workspace.py

# Inline delivery (default, unchanged)
Integration.mail(default_from="noreply@example.com", providers=[...])

# Background delivery
Integration.mail(
    default_from="noreply@example.com",
    providers=[...],
    queue_enabled=True,
)

# Background delivery with durable envelopes and suppression
Integration.mail(
    default_from="noreply@example.com",
    providers=[...],
    queue_enabled=True,
    queue_persistent=True,
)
\`\`\`

| Option | Default | Purpose |
|---|---|---|
| \`queue_enabled\` | \`False\` | Deliver via background tasks instead of inside the request |
| \`queue_persistent\` | \`False\` | Keep envelopes and suppression records in the application database |
| \`queue_dedupe_window_seconds\` | \`3600\` | Window in which an identical send is collapsed rather than sent twice |
| \`queue_retention_days\` | \`30\` | How long delivered envelopes are retained |

For an end-to-end durable path, pair \`queue_persistent=True\` with a durable task backend:

\`\`\`python
Integration.tasks(backend="redis", redis_url="redis://cache:6379/0")
Integration.mail(queue_enabled=True, queue_persistent=True, ...)
\`\`\`

\`queue_persistent=True\` requires \`Integration.database(...)\`.

---

## Usage

Call sites are identical whether the queue is on or off:

\`\`\`python
from aquilia.mail import EmailMessage

envelope_id = await EmailMessage(
    subject="Welcome",
    body="Thanks for signing up",
    to=user.email,
).asend()
\`\`\`

With the queue enabled, \`asend()\` returns as soon as the envelope is stored — typically sub-millisecond — and delivery completes on a worker. The returned envelope ID is the handle for checking status:

\`\`\`python
envelope = await mail.store.get(envelope_id)
envelope.status      # QUEUED → SENDING → SENT / FAILED / BOUNCED / CANCELLED
envelope.attempts
\`\`\`

---

## Send-Time Deduplication

Independent of the task system's job-level deduplication, mail collapses duplicate *sends*:

- An explicit \`idempotency_key\` on the message matches first.
- Otherwise a content digest matches within \`queue_dedupe_window_seconds\`.

This guards the classic double-send: a retried request or a double-clicked button producing two identical emails.

---

## Edge Cases

**No task manager, queue enabled.** Delivery falls back to inline sending. Recording an envelope as queued when nothing can deliver it would silently drop mail. The fallback also applies when a manager exists but has not been started — enqueueing into a stopped manager would park the message forever.

**Persistent stores with no database.** If \`queue_persistent=True\` but the database is unavailable, mail logs an error naming the durability that was lost and falls back to in-memory stores rather than aborting startup.

**Every recipient suppressed.** The envelope is marked \`CANCELLED\` and no delivery job is scheduled. See [Bounce Handling & Suppression](bounces_suppression.md).

**Missing envelope at delivery time.** A delivery job whose envelope has been cleaned up or cancelled logs a warning and is treated as success rather than retried forever — no amount of retrying will bring it back.

**Attachments.** Attachment payloads live in envelope metadata as blobs keyed by digest, so an envelope reloaded on another worker still carries its attachments.

---

## Performance Implications

Request-path cost drops from a full SMTP conversation (tens to hundreds of milliseconds, or a provider timeout on failure) to one store write plus one enqueue. Throughput of actual delivery becomes a function of worker count and provider rate limits rather than request concurrency.

\`MemoryEnvelopeStore\` evicts oldest-first past \`max_envelopes\`; an evicted envelope's delivery job will find nothing and give up. Use \`queue_persistent=True\` for any deployment where that matters.

---

## Compatibility

Fully backward compatible. \`queue_enabled\` defaults to \`False\`, so mail continues to send inline exactly as before unless explicitly enabled. \`EmailMessage\`, \`send_message()\`, and \`asend()\` signatures are unchanged. \`MailService.store\` and \`MailService.suppression\` are new attributes; passing explicit \`store=\` / \`suppression=\` to the constructor still overrides configuration.

---

## Related

- [Bounce Handling & Suppression](bounces_suppression.md)
- [Distributed & Persistent Backends](distributed_tasks.md)
- [Mail Security & MIME](mail_security.md)
- [Migration Guide](migration.md)
`,
    "mail_security.md": `# Mail Security, MIME & Templates — Aquilia v1.3.5

The mail subsystem's message construction, signing, logging, and templating were consolidated and hardened. MIME assembly now lives in one place shared by every provider, DKIM signing is real, log output redacts personal data on request, and the ATS template engine gained a documented filter set with autoescaping on by default.

---

## Shared MIME Assembly

Every provider previously built its own MIME message, which meant header handling, attachment encoding, and multipart structure drifted between SMTP, SES, SendGrid, and the file/console backends. \`aquilia/mail/mime.py\` is now the single implementation:

\`\`\`python
from aquilia.mail import build_mime_message, message_to_bytes, sign_dkim

build_mime_message(envelope, *, extra_headers=None)   # -> MIMEMultipart
message_to_bytes(msg, security=None)                  # -> bytes, DKIM-signed if configured
sign_dkim(raw_message, security)                      # -> bytes
\`\`\`

\`build_mime_message()\` produces a \`multipart/mixed\` message with a generated \`Message-ID\` and Aquilia tracking headers — \`X-Aquilia-Envelope-ID\`, plus trace and tenant IDs when set. Attachment payloads are read from envelope metadata, so an envelope reloaded on another worker still carries its attachments. The \`extra_headers\` argument is merged last, letting a provider add its own header (an ESP configuration set, for example) without forking the builder.

\`extract_domain(email)\` is also exported, used for per-domain rate limiting and DKIM domain defaulting.

### Why it matters

Bugs fixed in one provider now apply to all of them, and the \`X-Aquilia-Envelope-ID\` header is emitted consistently — which is what lets provider webhooks correlate a bounce back to the exact envelope. See [Bounce Handling & Suppression](bounces_suppression.md).

---

## DKIM Signing

DKIM signing is applied at the byte level, immediately before transmission, so the signature covers exactly what the provider receives.

\`\`\`python
Integration.mail(
    default_from="noreply@example.com",
    providers=[...],
    dkim_enabled=True,
    dkim_domain="example.com",
    dkim_selector="aquilia",
)
\`\`\`

| Option | Default | Purpose |
|---|---|---|
| \`dkim_enabled\` | \`False\` | Sign outbound mail |
| \`dkim_domain\` | \`None\` | Signing domain (\`d=\`). Required when enabled |
| \`dkim_selector\` | \`"aquilia"\` | Selector (\`s=\`); must match your DNS TXT record |
| \`dkim_private_key_path\` | \`None\` | Path to the PEM private key |
| \`dkim_private_key_env\` | \`"AQUILIA_DKIM_PRIVATE_KEY"\` | Environment variable holding the PEM key |

Signing requires the \`dkimpy\` package:

\`\`\`bash
pip install aquilia[mail-dkim]
\`\`\`

**DKIM failures raise at send time rather than shipping an unsigned message.** Silently sending unsigned mail would defeat the purpose — a receiving server treats a missing signature very differently from an invalid one, and an operator who enabled DKIM expects signed mail or an error.

Because that failure is at send time, \`aq mail check\` now validates the configuration up front:

\`\`\`
$ aq mail check
DKIM is enabled but dkim_domain is unset -- sends will fail
DKIM is enabled but 'dkimpy' is not installed -- pip install aquilia[mail-dkim]
\`\`\`

---

## TLS Enforcement

\`require_tls\` defaults to \`True\`. SMTP delivery negotiates STARTTLS and aborts rather than transmitting credentials or message content in cleartext. Disable only for a local development relay.

---

## XOAUTH2 Authentication

\`MailAuth.oauth2()\` supports SMTP providers that require bearer tokens (Gmail, Microsoft 365):

\`\`\`python
Integration.mail(
    auth=MailAuth.oauth2(
        client_id="...",
        client_secret_env="MAIL_OAUTH_SECRET",
        access_token_env="MAIL_OAUTH_TOKEN",
        token_url="https://oauth2.googleapis.com/token",
        scope="https://mail.google.com/",
    ),
    providers=[...],
)
\`\`\`

Aquilia does not perform the token exchange. Supply a currently valid token — literally or through \`access_token_env\` — from whatever component owns the refresh cycle. \`token_url\`, \`scope\`, and \`refresh_token\` are recorded for that component's use. The token is presented to SMTP via the XOAUTH2 mechanism.

---

## PII Redaction in Logs

Mail logs contain recipient addresses by nature. \`pii_redaction\` masks them:

\`\`\`python
Integration.mail(pii_redaction=True, ...)
\`\`\`

\`\`\`python
from aquilia.mail import redact_email, redact_pii

redact_email("alice@example.com")               # "a***e@example.com"
redact_pii("contact alice@example.com", enabled=True)
\`\`\`

Local parts are masked while the domain is preserved, so logs remain useful for diagnosing a domain-wide delivery problem without recording individual identities. Off by default — enabling it reduces debuggability, which should be a deliberate choice.

---

## ATS Templates

The mail template engine (\`<< expression >>\` syntax, distinct from the Jinja engine used for HTML views) gained a documented public API and filter set.

\`\`\`python
from aquilia.mail.template import configure, register_filter, render_string, render_template, FILTERS

configure(template_dirs=["mail_templates"])
render_string(template_text, context, *, autoescape=True)
render_template(template_name, context, *, template_dirs=None, autoescape=None)
register_filter(name, fn)
\`\`\`

### Autoescaping

**Interpolated values are HTML-escaped by default.** A username containing \`<script>\` cannot inject markup into an HTML mail body.

\`\`\`python
render_string("<p><< name >></p>", {"name": "<script>alert(1)</script>"})
# '<p>&lt;script&gt;alert(1)&lt;/script&gt;</p>'
\`\`\`

Two escape hatches:

- The \`safe\` filter, for a value that is known-good markup: \`<< body|safe >>\`
- \`autoescape=False\`, for plain-text bodies and subject headers, where escaping would corrupt output (\`&amp;\` in a subject line)

Subject rendering uses \`autoescape=False\` internally for exactly this reason.

### Built-in filters

\`currency\`, \`default\`, \`escape\`, \`join\`, \`length\`, \`lower\`, \`safe\`, \`title\`, \`trim\`, \`truncate\`, \`upper\`.

\`\`\`
<< total|currency("EUR") >>        →  EUR 12.50
<< blurb|truncate(5) >>            →  abcde…
<< tags|join(", ") >>
<< nickname|default("friend") >>
<< name|trim|title >>
\`\`\`

Filters compose left to right. Arguments must be literals — no expressions — so a template cannot execute arbitrary code.

Register your own:

\`\`\`python
register_filter("shout", lambda v: f"{v}!!!")
\`\`\`

### Control flow is rejected, loudly

Jinja-style control tags (\`[[% if %]]\`, \`[[% for %]]\`) are **not** supported and raise \`MailTemplateFault\` rather than being passed through. Shipping a raw \`[[% if %]]\` token to a recipient's inbox is worse than failing the render. Build conditional content in Python and pass the result in the context.

### Error behavior

- Unknown filter, malformed filter arguments, or a control-flow tag → \`MailTemplateFault\`
- A missing context variable renders as empty rather than raising, so an optional field does not break a send
- Dotted lookups work against dicts and objects: \`<< user.name >>\`

---

## Provider Changes

All providers now build messages through the shared MIME layer:

- **SMTP** — restructured around shared MIME assembly, byte-level DKIM signing, STARTTLS enforcement, and XOAUTH2 authentication.
- **SES** — sends the fully assembled raw message, preserving custom headers and the DKIM signature.
- **SendGrid** — consistent header handling and attachment encoding.
- **Console / File** — render the same MIME structure as production providers, so what you inspect in development matches what ships.

---

## Compatibility

Backward compatible. \`require_tls\` already defaulted to \`True\`. DKIM, PII redaction, and OAuth2 are opt-in. Template rendering already autoescaped; this release documents the behavior and the filter set rather than changing it. Provider configuration and \`EmailMessage\` signatures are unchanged.

The one behavior worth calling out: with \`dkim_enabled=True\` and a broken configuration, sends now **fail** instead of shipping unsigned mail. Run \`aq mail check\` after enabling DKIM.

---

## Related

- [Mail Delivery Queue](mail_queue.md)
- [Bounce Handling & Suppression](bounces_suppression.md)
- [CLI Changes](cli.md)
- [Migration Guide](migration.md)
`,
    "migration.md": `# Migration Guide — Aquilia v1.3.5

Aquilia v1.3.5 is a feature release with **no API removals or signature changes**. Every workspace, manifest, task, and mail configuration from 1.3.4 continues to work without modification.

The tasks, mail, and HTTP work is fully backward compatible. The **Contracts audit ships four behavioral corrections** — each replacing behavior that was incorrect — which require a review pass if your application uses nested Contracts, to-many Lenses, or integer fields fed by JSON. Those are covered first, since they are the only part of this release that can change how existing code behaves.

---

## Upgrading

\`\`\`bash
pip install aquilia==1.3.5
\`\`\`

Optional extras for the new capabilities:

\`\`\`bash
pip install aquilia[redis]        # distributed task backend
pip install aquilia[mail-dkim]    # DKIM signing for outbound mail
\`\`\`

For tasks and mail, nothing else is required. If you change no configuration, those subsystems behave exactly as in v1.3.4:

- Tasks run on \`MemoryBackend\`, single process.
- Mail sends inline, inside the request.
- No addresses are suppressed.
- No deduplication is applied.

Contracts require a review pass — see [Migration 0](#migration-0--contracts-behavioral-review) below.

---

## Upgrade Checklist

1. \`pip install aquilia==1.3.5\`
2. **Review Contract behavioral changes — see [Migration 0](#migration-0--contracts-behavioral-review).**
3. Run your test suite. Expect failures only where a nested Contract rule was previously inert, or a to-many Lens was serialized without prefetching.
4. *(Optional)* Generate Contract type stubs: \`aq contracts stubs myapp.contracts\`.
5. *(Optional)* Migrate \`seal_*\` validators to \`@ward\` — see [Migration 7](#migration-7--seal_-validators-to-ward).
6. *(Optional)* Move tasks to a durable backend — see below.
7. *(Optional)* Enable background mail delivery — see below.
8. *(Optional)* Wire provider webhooks for bounce handling.
9. If you use SendGrid or testing helpers, note that third-party \`httpx\` is no longer required as Aquilia uses native \`aquilia.http\`.
10. If you use DKIM, run \`aq mail check\` and install \`aquilia[mail-dkim]\`.
11. Remove any hand-rolled job deduplication in favour of \`dedup="skip"\`.
12. Remove any workaround that parsed \`repr\`-form job results.

---

## Migration 0 — Contracts Behavioral Review

**Required if your application uses Contracts.** Four corrections can change whether an existing payload is accepted.

### 0.1 — Nested Contract rules are now enforced

**What changed.** A nested Contract was validated structurally only. Every \`@ward\` method and every \`validate()\` override declared on a nested Contract was silently skipped. They now run.

**Why.** \`Sigil.validate()\` recursed into the child's compiled schema rather than instantiating the child Contract, so the ward phase was never reached. A nested Contract expressing an authorization check enforced nothing.

**How to check.** Find nested Contracts that declare rules:

\`\`\`bash
# Contracts referenced by another Contract's field, that declare a ward
grep -rn "@ward\\|def validate(self" --include="*.py" myapp/
\`\`\`

For each, confirm the rule is one you actually want enforced. A rule written years ago against an assumption that no longer holds will now start rejecting live traffic.

\`\`\`python
class LineItem(Contract):
    qty = IntFacet()

    @ward
    def qty_positive(self, data):
        if data["qty"] < 1:
            self.reject("qty", "Must be at least 1")

class Order(Contract):
    items: list[LineItem] = None

# v1.3.4: True  (the ward never ran)
# v1.3.5: False, errors = {"items": {"0": {"qty": ["Must be at least 1"]}}}
Order(data={"items": [{"qty": 0}]}).is_sealed()
\`\`\`

**Also affected: async wards.** A Contract whose *nested* child declares \`@ward(mode="async")\` now correctly reports \`has_async_wards is True\`, so calling \`is_sealed()\` raises \`ContractAsyncMismatchFault\` instead of skipping the ward. Switch those call sites to \`is_sealed_async()\`.

Details: [Nested Validation Pipeline](contracts_pipeline.md).

### 0.2 — \`Lens(many=True)\` raises on an unresolved relation

**What changed.** An un-awaited related manager produced an empty list. It now raises \`LensUnresolvedFault\` (\`BP503\`).

**Why.** \`[]\` is indistinguishable from "this record genuinely has no related rows", so the previous behavior shipped wrong data to clients with no signal.

**How to fix.** Three options:

\`\`\`python
# 1. Prefetch — best for hot paths
order = await Order.objects.prefetch_related("items").get(pk=1)
OrderContract(instance=order).data

# 2. Materialize explicitly
order.items = await order.items.all()
OrderContract(instance=order).data

# 3. Use the new async serializer, which awaits for you
await OrderContract.to_dict_async(order)
\`\`\`

### 0.3 — Malformed-body error shape changed

**What changed.** A scalar or list request body previously produced a "This field is required" error per field. It now produces one document-level error.

\`\`\`python
# v1.3.4
UserContract(data="not an object").errors
# {"name": ["This field is required"], "email": ["This field is required"]}

# v1.3.5
UserContract(data="not an object").errors
# {"__all__": ["Expected an object, got str"]}
\`\`\`

**Who is affected.** Clients that parse a 422 response body and assume every key is a field name. Treat \`__all__\` as a document-level error and render it separately from field errors.

### 0.4 — \`IntFacet\` rejects fractional input

**What changed.** \`3.9\` was silently truncated to \`3\`. It is now rejected. \`3.0\` is still accepted.

**Why.** \`int(3.9)\` returned \`3\` while the string \`"3.9"\` was correctly rejected — the same logical input behaved differently depending on wire type. Silent truncation of a quantity or a price in cents is a data-integrity bug that surfaces far from its cause.

**How to fix.** If a client legitimately sends fractional values you intend to round, do it explicitly before validation, or use \`FloatFacet\`/\`DecimalFacet\` and round in your handler.

### 0.5 — \`"__minimal__"\` projections return fewer fields

**What changed.** \`"__minimal__"\` stored an empty placeholder that no code resolved. Because an empty set is falsy, the per-field filter passed *every* field. It now resolves to primary-key facets plus every \`read_only\` facet.

**Who is affected.** Anyone using \`"__minimal__"\`. The previous output — all fields, including ones deliberately kept private — was never correct. Verify the new field set matches what the projection was meant to expose.

---

## Migration 7 — \`seal_*\` Validators to \`@ward\`

**Optional in 1.x. Required before 2.0.0.**

Methods named \`seal_*\` or \`async_seal_*\` still register as validators and still run, but now emit a \`DeprecationWarning\`.

### Find every affected method

\`\`\`bash
python -W error::DeprecationWarning -c "import myapp.contracts"
\`\`\`

Or fail the test suite on it:

\`\`\`toml
[tool.pytest.ini_options]
filterwarnings = ["error::DeprecationWarning"]
\`\`\`

Registration happens at class-body evaluation, so importing the module is enough — no request needs to run.

### Before

\`\`\`python
class OrderContract(Contract):
    def seal_total(self, data):
        if data["total"] < 0:
            self.reject("total", "Must not be negative")

    async def async_seal_stock(self, data):
        if not await in_stock(data["sku"]):
            self.reject("sku", "Out of stock")
\`\`\`

The name was the registration. Renaming \`seal_total\` during a cleanup removed the rule with no error and no failing test.

### After

\`\`\`python
class OrderContract(Contract):
    @ward
    def total_not_negative(self, data):          # rename is now safe
        if data["total"] < 0:
            self.reject("total", "Must not be negative")

    @ward(mode="async")
    async def stock_available(self, data):
        if not await in_stock(data["sku"]):
            self.reject("sku", "Out of stock")
\`\`\`

Two things change beyond the decorator: \`mode="async"\` becomes explicit rather than inferred from \`iscoroutinefunction\`, and methods can be renamed to describe the rule.

**Intermediate step:** adding \`@ward\` without renaming silences the warning immediately, since the decorator is the registration and the name becomes irrelevant.

\`\`\`python
@ward
def seal_total(self, data): ...    # no warning; rename later
\`\`\`

Details: [Stub Generation & Deprecations](contracts_tooling.md#deprecated-the-seal_--async_seal_-prefix-convention).

---

## Migration 8 — Adopt Contract Type Stubs

**Optional.** Makes Contract fields visible to \`mypy\` and \`pyright\`.

### Before

\`\`\`python
contract = UserContract(data=payload)
contract.is_sealed()
reveal_type(contract.email)   # Any
contract.emial                # typo survives review
\`\`\`

### After

\`\`\`bash
aq contracts stubs myapp.contracts
git add myapp/contracts.pyi
\`\`\`

\`\`\`python
reveal_type(contract.email)   # str
contract.emial                # error: "UserContract" has no attribute "emial"
\`\`\`

### Keeping stubs honest

\`\`\`yaml
- name: Check Contract stubs are current
  run: aq contracts stubs myapp.contracts --check
\`\`\`

\`--check\` exits non-zero on a missing or stale stub and prints the regeneration command. Generation is deterministic, so it cannot fail at random.

Details: [Stub Generation & Deprecations](contracts_tooling.md).

---

## Migration 1 — Durable, Distributed Tasks

### Before

\`\`\`python
# workspace.py
Integration.tasks(num_workers=4)
\`\`\`

Jobs lived in the web worker process and were lost on restart. Running two web workers meant two independent queues, so a periodic task fired twice.

### After

\`\`\`python
# workspace.py
Integration.tasks(
    backend="redis",
    redis_url="redis://cache:6379/0",
    num_workers=8,
    lease_seconds=120,
)
\`\`\`

Or, with no new infrastructure:

\`\`\`python
Integration.tasks(backend="sql")   # requires Integration.database(...)
\`\`\`

### What you must check

**Task arguments must be JSON-serializable.** On a durable backend, a non-serializable argument raises \`TaskSerializationFault\` at \`enqueue()\`. Audit your enqueue calls for ORM instances, file handles, and custom objects:

\`\`\`python
# Breaks on a durable backend
await tasks.enqueue(send_welcome, user)          # ORM instance

# Correct
await tasks.enqueue(send_welcome, user.id)       # worker re-loads it
\`\`\`

**Every worker must import every task module.** Workers resolve jobs by registered name. A worker process that has not imported the module defining a task raises \`TaskResolutionFault\` for that job. Declaring tasks in your module manifests handles this automatically.

**Task functions should be idempotent.** Distributed backends are at-least-once: a worker that stalls past its lease can have its job reclaimed and run twice.

See [Distributed & Persistent Backends](distributed_tasks.md).

---

## Migration 2 — Replace Hand-Rolled Deduplication

### Before

\`\`\`python
lock_key = f"job:invoice:{order_id}"
if await redis.set(lock_key, "1", nx=True, ex=3600):
    await tasks.enqueue(send_invoice, order_id)
\`\`\`

### After

\`\`\`python
await tasks.enqueue(send_invoice, order_id, dedup="skip")
\`\`\`

The framework version releases the reservation when the job reaches a terminal state, so a failed job can be retried immediately rather than being blocked until the TTL expires.

Use \`dedup="raise"\` where a duplicate indicates a caller bug:

\`\`\`python
from aquilia.tasks import TaskDuplicateFault

try:
    await tasks.enqueue(charge_card, order_id, dedup="raise")
except TaskDuplicateFault:
    return Response.json({"status": "already_processing"}, status=409)
\`\`\`

The default remains \`"allow"\`, so nothing changes until you opt in.

See [Idempotency & Deduplication](idempotency.md).

---

## Migration 3 — Replace Ad-Hoc Job Sequencing

### Before

\`\`\`python
# One long-lived job orchestrating the rest — lost on restart,
# and holding a worker slot while doing nothing
@task(name="pipeline")
async def pipeline(source):
    rows = await extract(source)
    cleaned = await clean(rows)
    await load(cleaned)
\`\`\`

### After

\`\`\`python
from aquilia.tasks.workflow import chain

await chain(
    extract.s(source),
    clean.s().with_parent_results(),
    load.s().with_parent_results(),
).run(tasks)
\`\`\`

Each step is an independent job with its own retry budget. The graph is durable the moment it is submitted, so a restart resumes rather than restarting from the top. A \`WAITING\` step occupies no worker slot.

See [Workflows & DAGs](workflows.md).

---

## Migration 4 — Background Mail Delivery

### Before

\`\`\`python
Integration.mail(default_from="noreply@example.com", providers=[...])
\`\`\`

\`asend()\` performed the SMTP conversation inside the request. Response time was tied to provider latency.

### After

\`\`\`python
Integration.tasks(backend="redis", redis_url="redis://cache:6379/0")

Integration.mail(
    default_from="noreply@example.com",
    providers=[...],
    queue_enabled=True,
    queue_persistent=True,
)
\`\`\`

**Call sites do not change.** \`EmailMessage(...).asend()\` still returns an envelope ID; it now returns before delivery completes.

### What you must check

**Code that assumed mail was sent on return.** With the queue enabled, a returned envelope ID means *accepted*, not *delivered*. Poll status where that distinction matters:

\`\`\`python
envelope = await mail.store.get(envelope_id)
envelope.status   # QUEUED → SENDING → SENT / FAILED / BOUNCED / CANCELLED
\`\`\`

**Tests asserting on a mail outbox.** Tests that send through a queued service must drive the task manager, or configure the mail service without \`queue_enabled\` for that test.

**\`queue_persistent=True\` requires \`Integration.database(...)\`.** Without a reachable database, mail logs an error and falls back to in-memory stores.

See [Mail Delivery Queue](mail_queue.md).

---

## Migration 5 — Bounce Handling

New capability; there is nothing to migrate from. Add a webhook endpoint:

\`\`\`python
from aquilia import Controller, POST, RequestCtx, Response
from aquilia.mail import parse_ses, process_webhook

class MailWebhookController(Controller):
    prefix = "/webhooks/mail"

    @POST("/ses")
    async def ses(self, ctx: RequestCtx):
        events = parse_ses(await ctx.body(), verify_topic_arn=SES_TOPIC_ARN)
        return Response.json(await process_webhook(
            events,
            suppression=self.mail.suppression,
            store=self.mail.store,
        ))
\`\`\`

Two things to get right:

- **Verify signatures.** Pass \`verify_topic_arn\` (SES), \`public_key\` (SendGrid), or \`signing_key\` (Mailgun). An unverified endpoint lets anyone forge a bounce and suppress an arbitrary address.
- **Exempt the path from CSRF.** Providers do not carry your CSRF token; signature verification is the authenticity check.

If you already maintain a suppression list in your own tables, import it:

\`\`\`python
for row in await LegacySuppression.all():
    await mail.suppression.suppress(row.email, reason=SuppressionReason.HARD_BOUNCE)
\`\`\`

See [Bounce Handling & Suppression](bounces_suppression.md).

---

## Migration 6 — Job Result Handling

If you worked around results arriving as \`repr\` strings on a persistent backend, remove the workaround:

\`\`\`python
# Before — parsing the repr form back
total = sum(int(r) for r in parent_results)

# After — JSON-safe values round-trip intact
total = sum(parent_results)
\`\`\`

Values that are not JSON-serializable still arrive as \`repr\` strings, which is unavoidable — return dicts, lists, and primitives from steps whose results are consumed downstream.

See [Bug Fixes](bugfixes.md).

---

## Deprecated Features

**The \`seal_*\` / \`async_seal_*\` Contract validator naming convention.** Deprecated in 1.3.0, removed in 2.0.0.

Behavior is unchanged in 1.x — these methods continue to register and run exactly as before. Declaring one now emits a \`DeprecationWarning\` naming its exact replacement decorator. Migration is mechanical; see [Migration 7](#migration-7--seal_-validators-to-ward).

Nothing else was deprecated.

## Removed Features

The third-party \`httpx\` dependency was removed in favour of the native \`aquilia.http\` client. No public API changed. See [Native HTTP Client](http_native.md).

## Breaking Changes

The tasks, mail, and HTTP work introduces no breaking changes.

**Contracts ships four behavioral corrections**, each replacing behavior that was incorrect:

| Change | Previously | Now | Action |
|---|---|---|---|
| Nested Contract rules enforced | Nested \`@ward\` / \`validate()\` never ran | Runs, and rejects | Review nested Contracts — see [0.1](#01--nested-contract-rules-are-now-enforced) |
| \`Lens(many=True)\` unresolved | Returned \`[]\` | Raises \`LensUnresolvedFault\` | Prefetch, materialize, or use \`to_dict_async()\` — see [0.2](#02--lensmanytrue-raises-on-an-unresolved-relation) |
| Malformed-body errors | Per-field "required" | \`{"__all__": [...]}\` | Update clients that parse 422 bodies — see [0.3](#03--malformed-body-error-shape-changed) |
| \`IntFacet\` fractional input | \`3.9\` became \`3\` | Rejected | Round explicitly, or use \`FloatFacet\` — see [0.4](#04--intfacet-rejects-fractional-input) |

\`"__minimal__"\` projections also return a restricted field set now; the previous output was never correct. See [0.5](#05--__minimal__-projections-return-fewer-fields).

Two further behavior changes worth noting, neither an API break:

- With \`dkim_enabled=True\` and an incomplete configuration, sends now fail rather than shipping unsigned mail. Run \`aq mail check\` after enabling DKIM. See [CLI Changes](cli.md).
- A Contract with async wards *nested* beneath it now correctly raises \`ContractAsyncMismatchFault\` from \`is_sealed()\`. Previously it reported no async wards and skipped them silently.

---

## Compatibility Notes

| Area | Notes |
|---|---|
| Python | 3.10–3.13, unchanged |
| Existing manifests | No changes required |
| \`MemoryBackend\` | Behavior unchanged; still the default |
| Inline mail | Behavior unchanged; still the default |
| \`TaskManager.enqueue()\` | New keyword-only params, all defaulted to prior behavior |
| \`MailService\` | New \`store\` / \`suppression\` attributes; constructor arguments still win |
| Task result values | JSON-safe values now round-trip; previously \`repr\` on persistent backends |
| \`Contract\` public API | No signature changes. \`is_sealed()\` / \`is_sealed_async()\` gained an optional keyword-only \`groups\` parameter, defaulting to prior behavior. |
| \`@ward\` | \`order\`, \`when\`, and \`groups\` are optional; a bare \`@ward\` behaves exactly as before |
| \`Spec\` | \`frozen\` and \`fail_fast\` both default to \`False\` — prior behavior |
| Validation messages | Byte-identical unless an i18n catalog defines the \`contracts.\` namespace |
| \`get_nested_contract_cls()\` | Still present, now delegating to \`resolve_nested()\` |
| Contract \`.pyi\` stubs | Entirely opt-in; not generating them changes nothing |

---

## Known Issues

- **Redis backend lacks automated test coverage** in this release; the SQL backend carries the durable-path integration tests. The Redis implementation is exercised manually and by the shared backend contract.
- **Mailgun signature verification is opt-in.** Omitting \`signing_key\` parses without verification and logs a warning. Treat it as required in production.
- **No built-in webhook route.** Applications wire \`parse_*\` and \`process_webhook\` into their own controller, so path, authentication, and CSRF policy stay under application control.
- **Workflow steps whose parent failed remain \`WAITING\`** rather than being cancelled. They will not run; inspect them with \`failed_jobs()\`.
- **Generic Contracts (\`Contract[T]\`) are not supported.** \`Contract.__class_getitem__\` already means *projection* (\`UserContract["public"]\`), so type parameterization needs an API decision: dispatch on argument type (backward compatible, but one syntax with two meanings), or move projections to an explicit method (cleaner, but breaks every existing subscript call site). \`typing.Self\`, \`Protocol\`, and \`NewType\` resolution are blocked behind the same decision. Deferred rather than guessed.
- **\`.pyi\` stubs replace their module for the type checker.** The generator reproduces the whole module surface, not only its Contracts. Anything it cannot render faithfully is emitted as \`Any\` and named in the command output.
- **\`to_dict_async()\` awaits relations sequentially.** Prefetching remains the right choice on hot paths; the async path exists so a missing prefetch degrades performance rather than raising.

---

## Related

- [Release Overview](README.md)
- [Distributed & Persistent Backends](distributed_tasks.md)
- [Workflows & DAGs](workflows.md)
- [Idempotency & Deduplication](idempotency.md)
- [Mail Delivery Queue](mail_queue.md)
- [Bounce Handling & Suppression](bounces_suppression.md)
- [Mail Security & MIME](mail_security.md)
- [Contracts — Nested Validation Pipeline](contracts_pipeline.md)
- [Contracts — Validation Control & Typing](contracts_validation.md)
- [Contracts — Stub Generation & Deprecations](contracts_tooling.md)
- [CLI Changes](cli.md)
- [Bug Fixes](bugfixes.md)
`,
    "surp_to_json_migration.md": `# SURP Binary Format Removal & JSON Standardization (v1.3.5)

## Overview

In Aquilia v1.3.5, the legacy \`surp\` binary serialization format and library dependency have been completely removed across the entire framework in favor of native, standardized \`json\` format (\`.json\` artifacts, \`JSONBytecodeCache\`, \`JSONCatalog\`, \`JSONAuditStore\`, \`schema_snapshot.json\`, \`credentials.json\`, \`ws.json\`, \`discovery_cache.json\`).

---

## Key Changes

1. **HTTP Core Layer**:
   - \`Request\` no longer has \`is_surp()\`, \`accepts_surp()\`, \`prefers_surp()\`, or \`surp()\` methods. \`request.data()\` returns \`request.json()\`.
   - \`Response\` no longer has \`Response.surp()\` or \`@requires_surp\` decorator. \`Response.negotiated()\` defaults to JSON encoding.
   - Removed \`InvalidSurp\` and \`SurpUnavailable\` fault classes.

2. **Internationalization (i18n)**:
   - \`SurpCatalog\` and \`has_surp()\` removed.
   - \`JSONCatalog\` is the default file catalog backend.
   - Default \`catalog_format\` in \`I18nConfig\` is \`"json"\`.

3. **Template Engine**:
   - \`SurpBytecodeCache\` renamed to \`JSONBytecodeCache\`.
   - Template compilation artifacts default to \`artifacts/templates.json\` with envelope \`"__format__": "json"\`.

4. **Aquilary & Auto-Discovery**:
   - Manifest exports and imports use \`.json\` format (\`frozen.json\`).
   - Discovery cache stored at \`.aquilia/discovery_cache.json\`.

5. **Models & Database**:
   - Migration DSL snapshots use \`schema_snapshot.json\`.
   - Migration CLI commands default \`--format\` option to \`"json"\`.

6. **Admin Audit Trail & Providers**:
   - Audit store updated to \`JSONAuditStore\` saving to \`.aquilia/audit.json\`.
   - Provider credential storage updated to \`credentials.json\`.

7. **Build & CI**:
   - Removed \`surp\` optional dependency from \`pyproject.toml\`, \`setup.py\`, and CI workflows.

---

## Migration Steps for Applications

- **File Extensions**: Rename any \`.surp\` configuration or manifest files in your project workspace to \`.json\`.
- **API Calls**: Replace any calls to \`request.surp()\` or \`Response.surp()\` with \`request.json()\` or \`Response.json()\`. Remove \`@requires_surp\` decorators from controller routes.
- **Imports**: Replace imports of \`SurpCatalog\` or \`SurpBytecodeCache\` with \`JSONCatalog\` and \`JSONBytecodeCache\`.
`,
    "workflows.md": `# Workflows & DAGs — Aquilia v1.3.5

Jobs can now declare dependencies on other jobs. Sequential chains, parallel groups, fan-in callbacks, and arbitrary directed acyclic graphs are all expressed through the same queue and the same workers — equivalent to Celery Canvas or BullMQ Flows.

Previously there was no way to say "run B after A". Applications either awaited a job's completion inside another job (occupying a worker slot while doing nothing) or polled \`get_job()\` in application code.

---

## Motivation

Real background work is rarely one isolated function:

- An import pipeline extracts, transforms, then loads.
- A report shards across N workers and merges the results.
- A deploy runs migrations, then warms caches, then notifies.

Without dependency support, each of these had to be orchestrated by a long-lived coroutine that survives for the whole pipeline — which loses everything on restart and does not distribute.

---

## Design Goals

1. **The graph is durable the moment it is submitted.** Every job is created up front with its dependencies recorded, so the workflow survives a restart on a persistent backend.
2. **No orchestrator process.** The backend releases dependent jobs as their dependencies complete. Nothing needs to stay resident.
3. **Reuse the existing queue.** Workflows are ordinary jobs with a \`depends_on\` field, not a parallel execution system.
4. **A failed step stops its branch.** Downstream jobs must not run on missing input.

---

## Architecture

### \`Signature\`

A task plus the arguments it will be called with, not yet enqueued — the same concept as Celery's signature, and named the same way.

\`\`\`python
from aquilia.tasks.workflow import Signature

step = Signature(send_email, ("user@example.com",), {"subject": "Hi"})
\`\`\`

Or, more idiomatically, from a \`@task\` descriptor:

\`\`\`python
step = send_email.s("user@example.com", subject="Hi")
\`\`\`

\`with_parent_results()\` returns a copy that receives its dependencies' return values as a \`parent_results\` keyword at execution time:

\`\`\`python
merge.s().with_parent_results()   # merge(parent_results=[...])
\`\`\`

The marker stored in the job's kwargs is a plain string, replaced with real values by the worker at execution time. That keeps the job JSON-serializable and lets results be read after a restart.

### \`Workflow\`

The graph builder. \`add()\` returns an index used to declare dependencies:

\`\`\`python
from aquilia.tasks.workflow import Workflow

wf = Workflow("nightly")
extract = wf.add(extract_rows.s(source))
clean   = wf.add(clean_rows.s(), depends_on=[extract])
enrich  = wf.add(enrich_rows.s(), depends_on=[extract])
wf.add(load_rows.s().with_parent_results(), depends_on=[clean, enrich])

result = await wf.run(manager)
\`\`\`

\`run()\` validates the graph, enqueues every node with its dependencies already wired, and returns a \`WorkflowResult\`. Dependent jobs start in \`WAITING\` and are released by the backend as their dependencies complete.

### \`WorkflowResult\`

\`\`\`python
await result.is_complete(manager)    # every terminal job reached a terminal state
await result.results(manager)        # terminal jobs' return values, in declaration order
await result.failed_jobs(manager)    # jobs that ended FAILED or DEAD
\`\`\`

\`is_complete()\` returns \`True\` for failure as well as success — use \`failed_jobs()\` to distinguish.

---

## Helpers

### \`chain\` — sequential

Each step waits for the previous one to complete successfully.

\`\`\`python
from aquilia.tasks.workflow import chain

await chain(
    extract.s(source),
    transform.s().with_parent_results(),
    load.s().with_parent_results(),
).run(manager)
\`\`\`

### \`group\` — parallel

Pure fan-out. Every step runs concurrently with no dependencies between them.

\`\`\`python
from aquilia.tasks.workflow import group

await group([shard.s(n) for n in range(8)]).run(manager)
\`\`\`

### \`chord\` — parallel then fan-in

A \`group\` header plus a callback that runs once every header job has completed, receiving their results.

\`\`\`python
from aquilia.tasks.workflow import chord

await chord(
    [shard.s(n) for n in range(8)],
    merge.s().with_parent_results(),
).run(manager)
\`\`\`

### Arbitrary DAGs

\`chain\`, \`group\`, and \`chord\` are conveniences over \`Workflow.add(..., depends_on=[...])\`. Any acyclic shape — diamonds, multi-level fan-out/fan-in, mixed widths — is expressible directly.

---

## Validation

Graph errors raise \`TaskWorkflowFault\` before anything is enqueued, so a malformed workflow never partially executes:

- An empty workflow.
- A cycle — detected by depth-first traversal with a path stack; the fault names the cycle.
- A dependency index that does not exist.

\`\`\`python
wf = Workflow("bad")
wf.add(step.s(), depends_on=[99])   # TaskWorkflowFault — unknown dependency
\`\`\`

---

## Edge Cases

**A failed dependency does not release its dependents.** If a step exhausts its retries, everything downstream stays \`WAITING\` rather than running on missing input. Inspect with \`failed_jobs()\`. These jobs are not automatically cancelled — a \`WAITING\` job whose parent is dead will not run and will not complete.

**Result fidelity.** Dependency results arrive as the actual returned value when it is JSON-compatible. A non-JSON return value degrades to its \`repr\` on a persistent backend, because an arbitrary object cannot be reconstructed from JSON. Return dicts, lists, and primitives from steps whose results are consumed downstream.

**Serialization applies to every step.** \`Workflow.run()\` enqueues through the normal path, so a step with non-serializable arguments raises \`TaskSerializationFault\` on a persistent backend — at submission, before any step runs.

**Workflows do not span backends.** Every job in a workflow lives on the manager it was submitted to. To span processes, use a shared durable backend.

**Ordering within a group is not guaranteed.** \`results()\` returns terminal values in *declaration* order, but execution order and completion order are arbitrary.

---

## Performance Implications

Workflow submission is O(n) enqueues for n steps, performed up front. There is no polling process and no idle worker held open waiting for a dependency — a \`WAITING\` job occupies no worker slot. Dependency resolution is one lookup per dependency at release time.

For very wide graphs (thousands of parallel steps), submission cost is dominated by the enqueue round trips; on \`RedisBackend\` these are pipelined by the backend.

---

## Compatibility

Purely additive. \`Workflow\`, \`Signature\`, \`WorkflowResult\`, \`chain\`, \`group\`, and \`chord\` are new exports from \`aquilia.tasks\`. The \`depends_on\`, \`workflow_id\`, and \`initial_state\` parameters on \`TaskManager.enqueue()\` are new keyword-only arguments with defaults that preserve prior behavior. No existing API changed.

---

## Related

- [Distributed & Persistent Backends](distributed_tasks.md) — required for workflows that span processes
- [Idempotency & Deduplication](idempotency.md)
- [Migration Guide](migration.md)
`,
  },
  "1.3.4": {
    "README.md": `# Aquilia v1.3.4 Release Notes — "Structural Integrity & Controller Expansion"

Aquilia v1.3.4 is a major architecture audit and feature release focusing on framework stability, registry correctness, controller integrity, workspace discovery robustness, and scalability.

This release combines Phase 1 (registry, workspace, config, and runtime audit fixes) with Phase 2 (controller system audit fixes, strict resolved-import discovery mode, distributed throttle backends, and Resource / ViewSet CRUD controllers).

## Table of Contents

1. [Phase 1: Round 1 Bugfixes](bugfixes_r1.md)
2. [Phase 1: Round 2 Bugfixes](bugfixes_r2.md)
3. [Phase 1: Performance Improvements](performance.md)
4. [Phase 1: Manifest System Changes](manifest_system.md)
5. [Phase 1: Workspace Discovery Enhancements](workspace_discovery.md)
6. [Phase 1: CLI Updates](cli.md)
7. [Phase 2: Controller System Audit Fixes](controller_audit.md)
8. [Phase 2: Strict Resolved-Import Discovery Mode](strict_discovery.md)
9. [Phase 2: Distributed Throttle Backends](distributed_throttle.md)
10. [Phase 2: Resource / ViewSet CRUD Controllers](resource_viewset.md)
11. [Migration Guide](migration.md)
`,
    "controller_audit.md": `# Controller System Audit Fixes

Details of the fixes applied to ControllerEngine, AuthManager, and routing in Aquilia v1.3.4 (§6.1–§8 of architectural audit report).

## §6.1 Lifecycle Hook Bypass (CRITICAL)
is_simple check now consults _has_lifecycle_hooks cache. Simple routes on controllers with custom on_request/on_response execute hooks unconditionally.

## §6.2 Unintended Token Generation (SECURITY)
Added issue_tokens: bool = True to authenticate_password() and SignInProvisionPolicy. Set False for session-only auth without minting JWTs.

## §6.3 Forward-Reference Type Resolution (BUG)
Exact string match replaces substring matching in _extract_method_params(). Fallback to __annotations__ when get_type_hints() raises.

## §6.4 Dynamic Segment Route Conflict False Positives (BUG)
_routes_conflict() compares type castors. /<id:int> and /<slug:str> are no longer flagged as conflicts.

## §5.3 Class-Level Cache Contamination (ARCH)
Added clear_caches() classmethods to ControllerEngine and ControllerFactory to flush id()-keyed caches between test runs.
`,
    "strict_discovery.md": `# Strict Resolved-Import Discovery Mode

Runtime-import-based discovery engine (StrictDiscoveryEngine) using importlib and inspect.getmro().

- Resolves transitive inheritance chains and aliased imports (e.g. Controller as Base)
- CLI usage: aq discover --strict
- Programmatic usage: engine.discover(strict=True)
- Handles ImportError gracefully per file with log warning
`,
    "distributed_throttle.md": `# Distributed Throttle Backends

Pluggable ThrottleBackend architecture supporting single-instance and multi-worker cluster rate limiting.

- MemoryThrottleBackend: sliding window with asyncio.Lock and LRU eviction
- RedisThrottleBackend: Redis sorted set sliding window with fail_open graceful degradation
- Ergonomic factories: Throttle.with_redis() and Throttle.with_memory()
`,
    "resource_viewset.md": `# Resource & ViewSet CRUD Controllers

Declarative CRUD controller abstraction via Resource[T], CRUDResource[T], ReadOnlyResource[T], and @action decorator.

- Auto-registers list (GET /), retrieve (GET /{id}), create (POST /), update (PUT /{id}), partial_update (PATCH /{id}), destroy (DELETE /{id})
- Custom routes via @action(detail=True/False)
`,
    "migration.md": `# Migration Guide — Aquilia v1.3.4

Complete migration instructions for all v1.3.4 changes.

- Secret(env="VAR") explicit environment variable lookup
- AppManifest(imports=[...]) v2 API preference
- AQUILIA_FAIL_FAST=1 startup error option
- authenticate_password(issue_tokens=False) session auth pattern
- Throttle.with_redis() distributed rate limiting upgrade

## Phase 3 - Cache, Storage & Filesystem

Every public API is preserved. Three behaviours change as corrections of clearly-wrong behaviour:

- Cache keys gain a version segment (key_version now reaches the key builder). Expect one cold cache on deploy, or set key_version=0 to keep the old layout.
- @cached no longer drops the first positional argument, so decorated functions stop returning other calls' values. Flush affected namespaces on a distributed backend.
- Authenticated responses are no longer served from the shared HTTP cache. Opt in with cache_authenticated=True plus the identity header in vary_headers.

Optional adoption: Integration.filesystem() for a DI-injectable FileSystem, distributed_stampede_lock for cross-process coalescing, serializer_secret_key for signed pickle, multipart_threshold for large S3 objects, and allow_unsandboxed=False for a fail-loudly sandbox posture.
`,
    "cache_audit.md": `# Cache System Audit Fixes

Fixes applied to aquilia.cache in v1.3.4, from the Cache & Storage architectural audit.

## Critical

- @cached dropped the first positional argument, so all calls to a single-argument function collapsed onto one key and returned another call's value. A silent data-correctness bug, not an error.
- CacheMiddleware cached identity-bearing responses under an identity-independent key, serving the first authenticated user's response to everyone. Requests carrying Cookie or Authorization now bypass the cache, and Set-Cookie responses are never stored, unless cache_authenticated=True is set alongside the identity header in vary_headers.
- The middleware read a nonexistent Response.content, so every cached entry stored an empty body. Response now exposes public content and body() accessors; unmaterialisable content is treated as not cacheable.
- Server._setup_cache() passed an invalid ttl= argument; the TypeError was swallowed and the middleware was silently never installed even when enabled.

## Correctness

- key_version was parsed from config and never reached the key builder, so the documented mass-invalidation workflow did nothing.
- decorators.py held a second key builder pinned at version=0, embedding the namespace twice and ignoring key_prefix. Decorator and service keys now share one layout.
- Functions returning None were never cached and recomputed forever. They are cached now; opt out with condition=lambda r: r is not None.
- Cache-Control no-store/private and the X-Cache-TTL override were read case-sensitively against a lowercase header map and never matched.

## Performance and leaks

- LFU eviction was a linear scan despite documenting O(log n). A real (frequency, key) min-heap now backs it.
- The TTL heap grew without bound when the same TTL'd key was rewritten. Both heaps compact against live entries: 2,000 rewrites now bound the heap to at most 16 entries.

## Redis

- The docstring claimed Lua atomicity that did not exist; increment() was a check-then-act race. It now runs the existence check and INCRBY in one script.
- Tag and namespace sets accumulated members whose keys expired naturally. A Lua prune removes them during ordinary reads.
- get() never returned tags, silently diverging from MemoryBackend. A TTL-matched sidecar restores tags and namespace.
- Stampede prevention was per-process. RedisBackend now offers a leased, token-checked SET NX PX lock so only one worker in the fleet recomputes.

## Configuration

- serializer="pickle" was unreachable because no secret key could be supplied. Added serializer_secret_key.
- CompositeBackend discarded async L2 write tasks, so shutdown could drop them. Tasks are tracked and drained.`,
    "storage_filesystem_audit.md": `# Storage & Filesystem Audit Fixes

Fixes applied to aquilia.storage and aquilia.filesystem in v1.3.4. The central finding was that path containment had been implemented twice - correctly in filesystem, incorrectly in storage. There is now exactly one implementation, used by both.

## Critical

- The streaming path ignored its sandbox entirely. stream_read and stream_copy accepted config and sandbox arguments and never passed them to the validator, while presenting the same method shape as the protected whole-file helpers. Paths are now validated before any descriptor is opened.
- Every FileSystem directory method raised TypeError: list_dir() got an unexpected keyword argument 'config'. The underlying functions now accept and enforce config and sandbox.
- LocalStorage used str.startswith() for containment, so /var/data-private satisfied a root of /var/data. It now delegates to the framework's canonical validate_path, which resolves symlinks and compares path components.

## Performance and scale

- Local and S3 backends buffered whole objects in memory despite documenting a streaming contract. Both stream in chunks now; content materialises only on an explicit read().
- S3 used put_object for everything, capping objects at 5 GB. Multipart upload is used above multipart_threshold, and a failed part aborts the upload.
- All cloud backends used the shared default executor via the deprecated get_event_loop(). A dedicated bounded pool (aquilia-storage threads, AQUILIA_STORAGE_MAX_WORKERS) replaces it.

## Robustness

- StorageRegistry.initialize_all() aborted the whole subsystem if any backend failed. Only a failing default backend is fatal now; optional backends degrade and report unhealthy.
- FileSystemConfig gained allow_unsandboxed. Setting it to False makes an unset sandbox_root a boot-time error instead of silently disabling containment.
- validate_path documents that symlinks are always resolved for containment regardless of follow_symlinks, which governs metadata semantics only.
- StorageRegistry.create_backend() imports any dotted path in configuration; the trust boundary is now documented.`,
    "subsystem_lifecycle.md": `# Subsystem Lifecycle & Health

Boot, health, and DI integration changes for cache, storage, and filesystem in v1.3.4.

## Filesystem is a first-class subsystem

Previously FileSystem required manual construction and DI registration, with no managed pool lifecycle and no health reporting. Integration.filesystem() now registers it in every DI container, starts the pool at startup, and drains it at shutdown. Disabled by default, so existing applications are unaffected.

## Health checks reflect reality

Cache and storage health were registered as literal HEALTHY without probing anything, so an unreachable backend was invisible to /health. The cache now performs a real write/read/delete round trip; storage pings every backend and publishes one storage.alias entry per disk plus a healthy/degraded/unhealthy aggregate naming the failing aliases; the filesystem reports pool state.

## StorageSubsystem clarified, not deleted

StorageSubsystem is the BootContext entry point for embedders, tests, and alternative runners, while AquiliaServer boots storage through its own ordered setup sequence. Both share StorageRegistry, so behaviour cannot diverge - only the orchestration differs. This is now stated in the module docstring rather than left ambiguous.

## DI exception contract restored

patch_di_container() re-raised ProviderNotFoundFault in place of ProviderNotFoundError, so every handler catching ProviderNotFoundError silently stopped working once any server was constructed. The conversion was redundant - ProviderNotFoundError already subclasses DIFault. The original error is now enriched in place and re-raised unchanged, and the patch is idempotent.`
  },
  "1.3.2": {
    "README.md": `# Aquilia v1.3.2 Release Notes — "Specula API Observatory"

Aquilia v1.3.2 introduces **Specula**, a major evolution of the framework's documentation and API exploration subsystem. Specula completely replaces the legacy OpenAPI 3.1.0 generator and static Swagger/ReDoc pages with a compiled, introspective ASGI dashboard (the Specula Observatory), reactive hot-reloading streams, automated security and clearance level mapping, a schema-synthesized mock server, and Postman/Insomnia collection exporters.

## Table of Contents

1. [Specula Observatory UI & Integration](observatory.md)
   * The new dashboard philosophy.
   * Integrating Specula via \`Integration.specula(...)\`.
   * UI branding and Server-Sent Events (SSE) live streams.
2. [Spec Compilation & Schema Inference](compilation.md)
   * The compiler-integrated \`SpeculaBuilder\`.
   * Python-to-JSON Schema type mapping.
   * Multi-strategy request body and response resolution.
3. [Automated Security & Clearance Detection](security.md)
   * Inferred security schemes from pipeline guards.
   * Integrated authorization clearance level detection.
   * Extended metadata (\`x-specula-security\`) vendor extensions.
4. [Mock Server & Collection Exports](mock_exports.md)
   * Interactive mocking engine at \`/specula/mock\`.
   * Schema synthesis with configurable recursion depth limits.
   * Dynamic exports for Postman v2.1 and Insomnia v4.
5. [Migration Guide](migration.md)
   * Removing legacy \`OpenAPIIntegration\` references.
   * Replaced classes, paths, and deprecations.

---

## Key Subsystem Improvements

1. **Compilation over Code Scanning**: No more parsing source files or class matching at runtime. Specula extracts endpoint specs directly from Aquilia's compiled in-memory ASGI routing topology.
2. **Developer Reactivity**: Hot-reloading modules push Specula spec invalidations down active Server-Sent Events (SSE) connections, immediately refreshing the developer's dashboard.
3. **Simulated Sandbox**: Frontends can start testing integration before the backend endpoints are written. The mock server synthesizes response payloads matching the exact JSON schemas defined in Contracts or ORM Models.
4. **Complete Security Transparency**: Exposes exact pipeline guards, role requirements, and AccessLevel clearance levels to ensure complete architectural observability.
`,

    "compilation.md": `# Spec Compilation & Schema Inference

Specula features a compiler-integrated OpenAPI 3.1.0 specification engine (\`SpeculaBuilder\`). Instead of scanning source files at startup, it introspects Aquilia's compiled routing topology in memory, extracting schemas, bindings, parameters, and outputs.

---

## Python-to-JSON Schema Mapping

When generating schema objects, Specula inspects standard type hints and maps them to their OpenAPI 3.1.0 JSON Schema equivalents. 

Specula is fully compliant with the OpenAPI 3.1.0 specification:
* **Option types** use \`oneOf\` blocks combined with \`{"type": "null"}\` instead of the deprecated \`nullable\` property.
* **Complex Python structures** map cleanly to nested schemas.

### Mapping Reference Table

| Python Type Hint | JSON Schema Equivalent |
| :--- | :--- |
| \`str\` | \`{"type": "string"}\` |
| \`int\` | \`{"type": "integer"}\` |
| \`float\` | \`{"type": "number", "format": "double"}\` |
| \`bool\` | \`{"type": "boolean"}\` |
| \`bytes\` | \`{"type": "string", "format": "binary"}\` |
| \`None\` / \`type(None)\` | \`{"type": "null"}\` |
| \`Optional[T]\` / \`T \| None\` | \`{"oneOf": [{"type": T_schema}, {"type": "null"}]}\` |
| \`list[T]\` / \`List[T]\` | \`{"type": "array", "items": T_schema}\` |
| \`dict[str, T]\` / \`Dict[str, T]\` | \`{"type": "object", "additionalProperties": T_schema}\` |
| \`tuple[T1, T2]\` | \`{"type": "array", "prefixItems": [T1_schema, T2_schema], "minItems": 2, "maxItems": 2}\` |
| \`Contract\` / \`Model\` | \`{"\$ref": "#/components/schemas/Name"}\` |

---

## Request Body Inference Strategies

Specula resolves request payloads through a 5-tier inference engine, prioritizing explicit developer configurations over implicit code analysis.

### 1. The \`request_contract\` Parameter
If a route decorator declares a validation contract directly, the builder generates a reference schema:
\`\`\`python
@POST("/users", request_contract=UserCreateContract)
async def create_user(self, ctx: RequestCtx): ...
\`\`\`

### 2. Contract Parameter Type Hints
If a route handler receives a parameter type-hinted with an Aquilia \`Contract\` class, it is automatically mapped as the JSON body payload:
\`\`\`python
@POST("/users")
async def create_user(self, ctx: RequestCtx, payload: UserCreateContract): ...
\`\`\`

### 3. Explicit \`Body\` Metadata Annotations
If a parameter is annotated using standard Python type annotations with \`Body()\`, it is mapped to a properties-based object payload:
\`\`\`python
@POST("/items")
async def create_item(self, ctx: RequestCtx, amount: Annotated[int, Body()] = 1): ...
\`\`\`

### 4. Docstring Body Mappings
The builder parses Google-style docstrings, extracting raw examples from \`Body:\` headers:
\`\`\`python
@POST("/items")
async def create_item(self, ctx: RequestCtx):
    """
    Create an item.

    Body: {"name": "Widget", "count": 10}
    """
    ...
\`\`\`

### 5. Source Code Introspection
As a fallback, Specula scans the compiled handler source code for extraction patterns:
* Finding \`await ctx.json()\` infers a generic \`application/json\` object.
* Finding \`await ctx.form()\` infers an \`application/x-www-form-urlencoded\` form.

---

## Response Shapes Resolution

Specula automatically maps success and error response channels.

### Success Shapes
1. **Model / Contract Mappings**: Declaring \`response_model\` or \`response_contract\` registers the corresponding schema (input contracts map with \`Input\` suffix, output contracts map directly) and binds them under status code \`2xx\`.
2. **Standard Output Fallbacks**: If no return contract is specified, Specula inspects handler code:
   * Calls to \`Response.json(...)\` default to \`application/json\`.
   * Calls to \`Response.html(...)\` or template rendering functions default to \`text/html\`.
   * References to \`SSEResponse(...)\` default to \`text/event-stream\`.

### Error Shapes
* **Raises Docstring Section**: Specula compiles exception details declared in Google-style docstrings into typed status responses:
  \`\`\`python
  @GET("/users/<id:int>")
  async def get_user(self, id: int):
      """
      Get user by ID.

      Raises:
          UserNotFoundFault (404): The user does not exist.
      """
      ...
  \`\`\`
  Specula compiles this raises annotation into a structured \`404 Not Found\` response returning the standard \`AquiliaError\` schema.
* **Auto-Validation Errors**: All write routes (\`POST\`, \`PUT\`, \`PATCH\`) automatically carry a default \`422 Unprocessable Entity\` response mapping returning the structured \`AquiliaValidationError\` schema.
`,

    "migration.md": `# OpenAPI to Specula Migration Guide

Aquilia v1.3.2 deprecates and removes the old static OpenAPI/Swagger engine. This guide outlines how to migrate your configuration, imports, and endpoints.

---

## 1. Configuration & Integration Upgrades

The old \`OpenAPIIntegration\` has been replaced by \`SpeculaIntegration\`. In your \`workspace.py\`, update your registrations:

### Legacy Style (Removed)
\`\`\`python
# Replaced by Specula
workspace.integrate(Integration.openapi(
    title="Store API",
    docs_path="/apidocs",
    swagger_ui_theme="dark"
))
\`\`\`

### New Style (Active)
\`\`\`python
from aquilia.integrations import SpeculaIntegration

# Option A: Direct class registration
workspace.integrate(SpeculaIntegration(
    title="Store API",
    ui_path="/apidocs",
    ui_theme="dark"
))

# Option B: Fluent helper
# workspace.integrate(Integration.specula(
#     title="Store API",
#     ui_path="/apidocs",
#     ui_theme="dark"
# ))
\`\`\`

### Parameter Mapping Table

Use this reference table to map configuration options from legacy OpenAPI attributes to Specula attributes:

| Legacy OpenAPI Option | New Specula Option | Notes |
| :--- | :--- | :--- |
| \`docs_path\` | \`ui_path\` | Default changes from \`/docs\` to \`/specula\`. |
| \`openapi_json_path\` | \`json_path\` | Default changes from \`/openapi.json\` to \`/specula/spec.json\`. |
| \`redoc_path\` | (Removed) | ReDoc is deprecated. Use the unified Specula dashboard. |
| \`swagger_ui_theme\` | \`ui_theme\` | Values: \`"auto"\`, \`"light"\`, \`"dark"\`. |
| \`swagger_ui_config\` | (Removed) | Replaced by direct dashboard configuration. |

---

## 2. Replaced Imports & Engines

If you manually generated specs, update your imports and instantiation:

\`\`\`python
# --- Legacy Imports (Removed) ---
# from aquilia.controller.openapi import OpenAPIConfig, OpenAPIGenerator
# config = OpenAPIConfig(title="API")
# spec = OpenAPIGenerator(config=config).generate(router)

# --- New Imports (Active) ---
from aquilia.specula.config import SpeculaConfig
from aquilia.specula.schema.builder import SpeculaBuilder

config = SpeculaConfig(title="API")
spec = SpeculaBuilder(config=config).build(router)
\`\`\`

---

## 3. Redirects & Endpoint Updates

The automatic redirects mapping legacy paths are no longer registered. Update links:

* **Swagger UI Docs**: Old path \`/docs\` is replaced by \`/specula\`.
* **ReDoc Docs**: Old path \`/redoc\` is deprecated. Use the unified \`/specula\` dashboard.
* **JSON Specification**: Old path \`/openapi.json\` is replaced by \`/specula/spec.json\`.
* **YAML Specification**: Specula now supports rendering YAML natively at \`/specula/spec.yaml\`.
`,

    "mock_exports.md": `# Mock Server & Collection Exports

Specula features a schema-driven Mock Server and dynamic collection exporters to support rapid frontend integration and testing.

---

## Interactive Mock Server (\`/specula/mock\`)

The mock server lets developers call any documented API endpoint and receive a plausible response payload without executing any business logic.

### Enabling the Mock Server
The mock server is disabled by default. Enable it in your workspace configuration:

\`\`\`python
workspace.integrate(Integration.specula(
    title="Customer API",
    mock_server_enabled=True,
    mock_max_depth=4 # limit recursive definitions mapping
))
\`\`\`

### How Payload Synthesis Works
When a request is sent to \`/specula/mock/<path>\`, the mock router matches the path against the compiled API specification. It resolves the success response (\`200\`, \`201\`, or \`202\`) and inspects the JSON Schema:

1. **Explicit Examples**: If the schema or individual fields define an \`example\` or \`examples\` block, those values are returned directly.
2. **Plausible Synthesis**: If no examples are configured, Specula inspects the schema field types and synthesizes logical placeholders:
   * **Formatting Matchers**: String formats like \`email\`, \`uuid\`, \`uri\`, and \`date-time\` map to real formatted values (e.g. \`user@example.com\`, \`550e8400-e29b-41d4-a716-446655440000\`).
   * **Key Name Inference**: If a string field matches common keys (such as \`email\` or \`url\`), appropriate values are auto-injected.
   * **Standard Defaults**: Integers default to \`42\`, numbers to \`3.14\`, booleans to \`True\`, and arrays to single-item arrays.
3. **Recursion Safety**: Self-referencing models (e.g., a node containing a list of children of its own type) are automatically truncated when nesting depth exceeds \`mock_max_depth\` (default \`4\`).

---

## Exporters

Specula exposes dynamic endpoints to download client collections configured with your current workspace routing topology and security schemes.

### 1. Postman Collection v2.1
* **Endpoint**: \`/specula/export/postman\`
* **Output**: A compliant Postman v2.1 collection JSON file.
* **Details**:
  * Groups endpoints into folders based on their tags or manifest module names.
  * Translates route variables like \`/users/<id:int>\` into Postman-compatible environment syntax: \`/users/{{id}}\`.
  * Pre-populates request bodies with JSON examples synthesized from Contract definitions.
  * Embeds default authorization headers mapped to the \`{{access_token}}\` environment variable.

### 2. Insomnia v4 Collection
* **Endpoint**: \`/specula/export/insomnia\`
* **Output**: A standard Insomnia v4 export file.
* **Details**:
  * Includes workspace configuration mapping the current API.
  * Sets up base environment variables referencing \`{{ _.base_url }}\`.
  * Configures HTTP methods, headers, and body payloads automatically.
`,

    "observatory.md": `# Specula Observatory UI & Integration

The Specula Observatory is a built-in interactive dashboard served natively by Aquilia at \`/specula\`. It provides a CDN-free developer sandbox that works entirely offline, inline-cached, and features hot-reload awareness.

## Workspace Integration

Specula is registered at the workspace level inside \`workspace.py\`. You configure it using the \`Integration.specula(...)\` builder method or by importing and instantiating \`SpeculaIntegration\` directly:

\`\`\`python
# workspace.py
from aquilia.workspace import Workspace
from aquilia.integrations import Integration, SpeculaIntegration

workspace = (
    Workspace("user-portal")
    
    # Style A: Fluent Integration helper
    .integrate(Integration.specula(
        title="User Portal API",
        version="1.4.0",
        ui_theme="dark"
    ))
    
    # Style B: Direct Instantiation (provides static checks and autocomplete)
    # .integrate(SpeculaIntegration(
    #     title="User Portal API",
    #     version="1.4.0",
    #     ui_theme="dark"
    # ))
)
\`\`\`

---

## Configuration Reference (\`SpeculaConfig\`)

When you configure Specula, your parameters map to the \`SpeculaConfig\` dataclass. The primary settings available are:

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| **Info / Branding** | | | |
| \`title\` | \`str\` | \`"Aquilia API"\` | Name of the API, visible in the UI header and spec exports. |
| \`version\` | \`str\` | \`"1.0.0"\` | The current API release version. |
| \`description\` | \`str\` | \`""\` | Detailed description of the API. |
| \`ui_theme\` | \`str\` | \`"auto"\` | \`"auto"\` (matches system preferences), \`"light"\`, or \`"dark"\`. |
| \`ui_primary_color\`| \`str\` | \`"#22c55e"\` | Hex code for branding the main interface buttons and tags. |
| **URL Paths** | | | |
| \`ui_path\` | \`str\` | \`"/specula"\` | Browser path to view the Observatory HTML dashboard. |
| \`json_path\` | \`str\` | \`"/specula/spec.json"\`| JSON endpoint serving the raw OpenAPI 3.1.0 spec. |
| \`yaml_path\` | \`str\` | \`"/specula/spec.yaml"\`| YAML endpoint serving the raw OpenAPI 3.1.0 spec. |
| \`stream_path\` | \`str\` | \`"/specula/stream"\`| SSE stream pushing route updates to the UI. |
| \`mock_path\` | \`str\` | \`"/specula/mock"\` | Endpoint path for the mock server router. |
| **Feature Toggles** | | | |
| \`enabled\` | \`bool\` | \`True\` | Master toggle to enable or disable Specula routes. |
| \`include_internal\`| \`bool\` | \`False\` | Whether routes matching \`/_*\` are included in the spec. |
| \`detect_security\` | \`bool\` | \`True\` | Scan route guards and decorators to construct security schemes. |
| \`mock_server_enabled\`| \`bool\` | \`False\` | Set \`True\` to enable schema-synthesized mock responses. |
| \`spec_cache_ttl\` | \`int\` | \`60\` | In-memory cache duration (in seconds) for compiled spec payloads. |

---

## Hot-Reloading SSE Stream (\`/specula/stream\`)

During development, Aquilia runs with file watchers. When you modify controller code, the worker process reloads. 

Specula exposes a native ASGI Server-Sent Events (SSE) stream endpoint at \`/specula/stream\`. When the dashboard is loaded in a browser, it subscribes to this stream. When a reload happens, the server pushes an invalidation event down the pipe:

\`\`\`json
{"event": "update", "data": {"status": "invalidated", "version": "2.0.0"}}
\`\`\`

The Observatory frontend listens to this event and immediately fetches the newly compiled specification and routes dynamically, refreshing the client view with zero hard refreshes.

---

## Production Security Locks

By default, the Specula Observatory is fully open. In production environments, you can lock access down to authenticated users with specific roles:

\`\`\`python
workspace.integrate(Integration.specula(
    title="Corporate Core API",
    docs_auth_required=True,
    docs_roles=["admin", "ops-team"]
))
\`\`\`

When \`docs_auth_required\` is enabled, the Specula controller inspects the request context using the configured \`AuthMiddleware\` pipeline. If the visitor lacks the required roles, they receive a \`403 Forbidden\` response.
`,

    "security.md": `# Automated Security & Clearance Detection

Specula integrates with Aquilia's security pipeline to automatically detect, map, and document authentication configurations. It translates pipeline guards and clearance levels into standard OpenAPI security requirements and rich custom metadata tags.

---

## Inferred Security Schemes

The spec builder scans your controllers' and routes' pipeline nodes and handler decorators to identify authentication mechanisms. It automatically registers and configures security definitions in the OpenAPI \`components.securitySchemes\` catalog:

| Inferred Guard Class Name | Generated Security Scheme | Schema Details |
| :--- | :--- | :--- |
| \`AuthGuard\` / \`Auth\` / \`@authenticated\` | \`bearerAuth\` | HTTP Bearer token (JWT) authentication. |
| \`ApiKeyGuard\` / \`ApiKey\` | \`apiKeyAuth\` | \`X-API-Key\` request header authorization. |
| \`SessionGuard\` / \`Session\` | \`cookieAuth\` | Session-based cookie verification (\`session\`). |
| \`BasicAuthGuard\` / \`Basic\` | \`basicAuth\` | HTTP Basic authentication. |
| \`OAuth2Guard\` / \`OAuth2\` | \`oauth2\` | OAuth2 Authorization Code flow. |

\`\`\`python
# Specula automatically registers bearerAuth with ["read", "write"] scopes
class OrderController(Controller):
    pipeline = [AuthGuard(), ScopeGuard("read", "write")]
    
    @GET("/")
    async def list_orders(self, ctx: RequestCtx): ...
\`\`\`

---

## Integrated Clearance Detection

Specula integrates directly with the \`aquilia.auth.clearance\` system to identify role-based and attribute-based clearance levels. 

The builder resolves the merged clearance level from the controller boundary and individual route overrides:
1. **Public Routes**: If the effective clearance resolves to \`AccessLevel.PUBLIC\` (e.g. via \`@grant(level=AccessLevel.PUBLIC)\`), security requirements are omitted for that route.
2. **Protected Routes**: If the effective clearance is higher than public, \`bearerAuth\` is automatically registered as a requirement.

---

## Rich Metadata Extensions (\`x-specula-security\`)

To support advanced observability and client generation, Specula embeds the full resolved authorization metadata in a custom vendor extension block (\`x-specula-security\`) inside each route's spec operation:

\`\`\`json
"x-specula-security": {
  "authenticated": true,
  "guards": [
    {
      "name": "RoleGuard",
      "type": "instance",
      "roles": ["admin", "compliance"],
      "require_all": false
    }
  ],
  "clearance": {
    "level": "INTERNAL",
    "level_value": 30,
    "entitlements": ["view_audit_logs", "override_fees"],
    "conditions": ["IsDuringOfficeHours", "IPRangeCondition"],
    "compartment": "finance"
  }
}
\`\`\`

This vendor block exposes:
* **\`authenticated\`**: Boolean flag indicating if verification is required.
* **\`guards\`**: Detailed list of active pipeline guard configurations, including roles, scopes, optional tags, resources, and evaluation settings.
* **\`clearance\`**: The full clearance metadata, including \`level\` name, \`level_value\` integer, required \`entitlements\` lists, active \`conditions\` names, and matching resource \`compartment\` boundaries.
`
  },
  "1.3.1": {
    "README.md": `# Aquilia v1.3.1 Release Notes — "Backend Refactoring"

Aquilia v1.3.1 introduces a major rewrite of the authentication (\`aquilia.auth\`) and authorization subsystems. It moves away from rigid string-based strategies and hardcoded guard adapters in favor of a pluggable, class-based backend architecture, a unified permission engine, hardened session serialization, and token clock-skew tolerance.

## Table of Contents

1. [Pluggable Authentication Backends](backends.md)
   * The new \`AuthBackend\` protocol.
   * Built-in backends: \`TokenBackend\`, \`SessionBackend\`, \`PasswordBackend\`, \`ApiKeyBackend\`.
   * The \`resolve_backend\` helper and loading configuration.
2. [Unified Permission & Authorization Engine](guards.md#permissionengine)
   * Role DAG (Directed Acyclic Graph) inheritance.
   * Policy callables and scope checks.
   * Pluggable Flow Guards: \`AuthGuard\`, \`RoleGuard\`, \`ScopeGuard\`, \`PolicyGuard\`.
   * Context-First Decorators: \`@authenticated\`, \`@roles_required\`, \`@scopes_required\`, \`@optional_auth\`.
3. [Session Security Hardening](sessions.md)
   * Elimination of stale permission state in session cookies.
   * The lightweight \`AuthPrincipal\` serialization format.
   * Dynamic resolution of roles and scopes on every request.
4. [Migration Guide](migration.md)
   * Upgrading configuration settings from \`strategies\` to \`backends\`.
   * Replaced classes, decorators, and middleware.

---

## Key Refactoring Goals

1. **Pluggability**: Unify all authentication strategies (Bearer JWTs, Session cookies, Username/Password, API keys) under a single, reusable backend protocol.
2. **Dynamic Privileges**: Resolve permissions, roles, and scopes fresh from the database or cache on every request, preventing privilege escalation through stale session states.
3. **API Simplification**: Consolidate five parallel authorization subsystems (RBAC, ABAC, Clearance, Policy DSL, and custom adapters) into a single, cohesive \`PermissionEngine\`.
4. **Resiliency**: Handle clock drift in distributed clusters by introducing native clock-skew tolerance.
5. **DI Scope Performance**: Deprecate the class/object-based \`ServiceScope\` Enum in favor of high-performance raw string literals backed by \`typing.Literal\` to eliminate import-time namespace scanning and runtime attribute lookup overhead.`,

    "backends.md": `# Pluggable Authentication Backends

In Aquilia v1.3.1, the authentication workflow is decomposed into single-responsibility **Backends**. A backend is a class that conforms to the \`AuthBackend\` protocol. It is responsible for accepting a credential dictionary and resolving it to an \`Identity\`.

## The \`AuthBackend\` Protocol

The \`AuthBackend\` protocol is defined in \`aquilia.auth.backends.base\` using Python's structural subtyping (\`typing.Protocol\`):

\`\`\`python
from typing import Any, Protocol, runtime_checkable
from aquilia.auth.core import Identity

@runtime_checkable
class AuthBackend(Protocol):
    def accepts(self, credentials: dict[str, Any]) -> bool:
        """Return True if the backend supports the provided credentials."""
        ...

    async def authenticate(self, credentials: dict[str, Any]) -> Identity | None:
        """Verify credentials and resolve them to an Identity.
        
        May raise specific auth faults (e.g., AUTH_TOKEN_EXPIRED, AUTH_INVALID_CREDENTIALS).
        """
        ...
\`\`\`

---

## Built-in Backends

Aquilia provides four native backends to cover standard flows:

### 1. \`TokenBackend\`
Validates JWT Bearer tokens. It verifies signatures, checks \`exp\` and \`nbf\` claims (with clock-skew tolerance), and validates token revocation via \`TokenManager\`.
* **Accepted Credentials**: \`{"token": str}\`
* **Constructor**:
  \`\`\`python
  def __init__(self, token_manager: TokenManager, identity_store: IdentityStore)
  \`\`\`

### 2. \`SessionBackend\`
Restores identity from a cookie-backed session. It looks up the \`identity_id\` from the session data or from \`session.principal\`, and fetches the corresponding active identity.
* **Accepted Credentials**: \`{"session": Session}\`
* **Constructor**:
  \`\`\`python
  def __init__(self, identity_store: IdentityStore)
  \`\`\`

### 3. \`PasswordBackend\`
Authenticates user login credentials. It checks for IP/username brute-force lockouts, resolves usernames or email addresses to an identity, compares password hashes, handles password re-hashing when algorithm parameters upgrade, and checks for multi-factor authentication (MFA) requirements.
* **Accepted Credentials**: \`{"username": str, "password": str}\`
* **Constructor**:
  \`\`\`python
  def __init__(
      self,
      identity_store: IdentityStore,
      credential_store: CredentialStore,
      password_hasher: PasswordHasher,
      rate_limiter: RateLimiter | None = None,
      login_attributes: tuple[str, ...] = ("email", "username", "login"),
  )
  \`\`\`

### 4. \`ApiKeyBackend\`
Authenticates API requests via an opaque API key. It hashes the incoming key using \`HMAC-SHA256\` for lookup, checks expiration and revocation status, and verifies that the key carries the required scopes if requested.
* **Accepted Credentials**: \`{"api_key": str, "required_scopes": list[str] | None}\`
* **Constructor**:
  \`\`\`python
  def __init__(self, credential_store: CredentialStore, identity_store: IdentityStore)
  \`\`\`

---

## The Backend Resolver

To simplify instantiation, the \`resolve_backend\` function maps string identifiers, class references, or dotted import paths to their instantiated backends:

\`\`\`python
def resolve_backend(b: Any, auth_manager: Any) -> Any:
    """Resolve a backend reference (instance, class, short name, or dotted path)
    into an instantiated backend object.
    """
    ...
\`\`\`

It maps:
* Short names: \`"token"\` (TokenBackend), \`"session"\` (SessionBackend), \`"password"\` (PasswordBackend), \`"api_key"\` (ApiKeyBackend).
* Class references: \`TokenBackend\`, \`SessionBackend\`, \`PasswordBackend\`, \`ApiKeyBackend\`.
* Dotted paths: \`"my_app.auth.backends.CustomBackend"\`.

### Example Configuration in \`workspace.py\`

\`\`\`python
class auth(AquilaConfig.Auth):
    secret_key = Secret(env="AQ_SECRET_KEY", default="change-me")
    backends = [
        "aquilia.auth.backends.TokenBackend",
        "aquilia.auth.backends.SessionBackend",
        "my_project.auth.CustomBackendClass",  # Dotted class path
    ]
\`\`\``,

    "guards.md": `# Unified Authorization, Middleware & Decorators

Aquilia v1.3.1 unifies identity resolution and request-scoped checks into a single middleware and permission engine.

---

## 1. Unified \`PermissionEngine\`

The \`PermissionEngine\` (defined in \`aquilia.auth.permissions\`) is the central engine for evaluating roles, scopes, and policies. It replaces five separate historical systems and runs check assertions that raise appropriate exceptions on denial.

### Core API Methods

* \`define_role(role: str, *, permissions: list[str] | None = None, inherits: list[str] | None = None) -> None\`: Declare a role and its transitively implied parents.
* \`role_implies(role: str, target: str) -> bool\`: Query the role DAG structure.
* \`register_policy(key: str, policy: PolicyCallable) -> None\`: Define a rule matching the signature \`(identity, resource) -> bool\`.
* \`check_role(identity: Identity, role: str) -> None\`: Asserts role ownership; raises \`AUTHZ_INSUFFICIENT_ROLE\` on failure.
* \`check_scope(identity: Identity, scope: str) -> None\`: Asserts scope ownership; raises \`AUTHZ_INSUFFICIENT_SCOPE\` on failure.
* \`check_policy(key: str, identity: Identity, resource: Any = None) -> None\`: Asserts policy assertion passes; raises \`AUTHZ_POLICY_DENIED\` on failure.
* \`has_role(identity: Identity, role: str) -> bool\`: Returns a boolean indicating role membership.
* \`has_scope(identity: Identity, scope: str) -> bool\`: Returns a boolean indicating scope membership.
* \`evaluate_policy(key: str, identity: Identity, resource: Any = None) -> bool\`: Returns a boolean indicating policy result.

---

## 2. Pluggable Flow Guards

Guards (defined in \`aquilia.auth.guards\`) evaluate context and raise exceptions on denial. They can be placed directly in request pipelines or used as raw classes (for zero-configuration defaults).

### \`AuthGuard\`
Verifies authentication status.
* **Optional Mode**: When \`optional=True\`, anonymous users are allowed.
* **Proactive Auth**: If the identity is not yet resolved, \`AuthGuard\` attempts to proactively extract and authenticate a Bearer token using DI container-resolved \`AuthManager\`.
* **Signature**: \`AuthGuard(auth_manager=None, optional=False)\`

### \`RoleGuard\`
Ensures the identity holds required roles.
* **Resolution**: Uses \`PermissionEngine\` if found in the DI container; otherwise, falls back to direct membership testing of \`identity.get_attribute("roles", [])\`.
* **Signature**: \`RoleGuard(*roles, engine=None, require_all=True)\`

### \`ScopeGuard\`
Ensures the identity holds required scopes.
* **Wildcards**: Supports the wildcard \`"*"\` scope.
* **Signature**: \`ScopeGuard(*scopes, require_all=True)\`

### \`PolicyGuard\`
Evaluates a policy registered in the permission engine.
* **Signature**: \`PolicyGuard(key, engine, resource=None)\`

---

## 3. Context-First Decorators

Decorators (defined in \`aquilia.auth.decorators\`) wrap handlers to execute guard checks and **inject parameters** into the handler's signature (e.g., \`identity\`, \`user\`, \`session\`, \`principal\`).

### \`@authenticated\`
Requires an authenticated identity.
* **Browser Redirection**: If a request is anonymous, has \`redirect_if_html=True\` or \`login_url\` configured, and accepts HTML, it performs a \`303 Redirect\` to the login page with a \`next\` query parameter.
* **Signature**:
  \`\`\`python
  def authenticated(
      func=None,
      *,
      login_url: str | None = None,
      redirect_if_html: bool = False,
      include_next: bool = True,
      next_param: str = "next",
      redirect_status: int = 303,
  )
  \`\`\`

### \`@roles_required\` / \`@scopes_required\`
Evaluates role or scope conditions before executing the controller action.
\`\`\`python
@roles_required("admin", "editor", require_all=False)
async def delete_post(self, ctx: RequestCtx) -> Response:
    ...
\`\`\`

### \`@optional_auth\`
Evaluates the proactive \`AuthGuard(optional=True)\` check. It injects the user if found but does not block anonymous traffic.

### \`@requires\`
Composes multiple guards (both classes and instances) sequentially:
\`\`\`python
@requires(AuthGuard, RoleGuard("admin"))
async def admin_only_action(self, ctx: RequestCtx) -> Response:
    ...
\`\`\`

---

## 4. Unified \`AuthMiddleware\`

The new unified \`AuthMiddleware\` (defined in \`aquilia.auth.middleware\`) coordinates credential resolution from backends on every incoming request.

* **Signatures & Parameters**:
  \`\`\`python
  def __init__(
      self,
      auth_manager: AuthManager,
      session_engine: SessionEngine | None = None,
      *,
      require_auth: bool = False,
      backends: list[AuthBackend] | None = None,
      logger: logging.Logger | None = None,
  )
  \`\`\`
* **Execution Flow**:
  1. **Phase 1: Session Resolution**: If \`session_engine\` is provided, resolves the session and binds it to \`ctx.session\` and \`request.state["session"]\`.
  2. **Phase 2: Credentials Extraction**: Extracts Bearer token, ApiKey, or Session from the request.
  3. **Phase 3: Backend Authentication**: Loops through pluggable \`backends\` (defaults to \`TokenBackend\` and \`SessionBackend\`). The first backend that accepts the credentials and returns an \`Identity\` completes the phase.
  4. **Phase 4: Requirement Enforcement**: If \`require_auth=True\` and no identity is resolved, returns a \`401 Unauthorized\` response immediately.
  5. **Phase 5: Propagation**: Propagates the resolved identity to \`request.state["identity"]\`, \`request.state["authenticated"]\`, and \`ctx.identity\`.
  6. **Phase 6: Downstream Execution**: Calls the next handler in the ASGI middleware chain.
  7. **Phase 7: Session Commitment**: Commits session modifications back to the storage adapter.`,

    "migration.md": `# Migration Guide: v1.3.0 to v1.3.1

Aquilia v1.3.1 consolidates and standardizes authentication and authorization. Follow this guide to upgrade your project.

---

## 1. Upgrading Configuration

The string-based \`strategies\` setting has been removed. You must now configure the list of identity-resolution backends using the \`backends\` parameter. Additionally, the rate-limiting and MFA settings have been promoted to direct configuration parameters on \`AquilaConfig.Auth\`.

### Legacy Configuration (v1.3.0)
\`\`\`python
class auth(AquilaConfig.Auth):
    secret_key = Secret(env="AQ_SECRET_KEY", default="change-me")
    strategies = ["token", "session"]
\`\`\`

### Refactored Configuration (v1.3.1)
\`\`\`python
class auth(AquilaConfig.Auth):
    secret_key = Secret(env="AQ_SECRET_KEY", default="change-me")
    backends = [
        "aquilia.auth.backends.TokenBackend",
        "aquilia.auth.backends.SessionBackend",
    ]
    # Store type: "memory" or "redis"
    store_type = "memory"
    
    # Rate Limiting configuration parameters
    rate_limit_max_attempts = 5
    rate_limit_window_seconds = 900
    rate_limit_lockout_seconds = 3600
    
    # MFA settings
    mfa_enabled = False
    mfa_required = False
    
    # Clock skew tolerance (in seconds) for JWT validations
    clock_skew_seconds = 5
    
    # Audit trail activation
    audit_enabled = True
\`\`\`

---

## 2. Replaced & Removed Decorators

The legacy decorators \`AdminGuard\` and \`VerifiedEmailGuard\` have been removed.

* **\`AdminGuard\`**: Replace with \`@roles_required("admin")\`.
* **\`VerifiedEmailGuard\`**: Handle verification checks in your identity resolution backend (such as deactivating unverified users) or write a simple custom guard.

#### Before:
\`\`\`python
from aquilia.auth import AdminGuard

@AdminGuard
async def delete_item(ctx):
    ...
\`\`\`

#### After:
\`\`\`python
from aquilia.auth import roles_required

@roles_required("admin")
async def delete_item(ctx):
    ...
\`\`\`

---

## 3. Upgrading Flow Pipeline Guards

All legacy guard adapters (historically located in \`flow_guards.py\`) have been removed. Use the new first-class guards directly.

| Legacy Guard Class (v1.3.0) | Refactored Guard Class (v1.3.1) |
|---|---|
| \`RequireAuthGuard\` | \`AuthGuard\` |
| \`RequireRolesGuard\` | \`RoleGuard\` |
| \`RequireScopesGuard\` | \`ScopeGuard\` |
| \`RequirePolicyGuard\` | \`PolicyGuard\` |

### Pipeline Registration Example

#### Before:
\`\`\`python
from aquilia.auth.integration.flow_guards import RequireAuthGuard, RequireRolesGuard

pipeline.guard(RequireAuthGuard())
pipeline.guard(RequireRolesGuard("admin"))
\`\`\`

#### After:
\`\`\`python
from aquilia.auth.guards import AuthGuard, RoleGuard

# Raw classes can be passed if no parameters are required
pipeline.guard(AuthGuard)
pipeline.guard(RoleGuard("admin"))
\`\`\`

---

## 4. Upgrading Session Guards

The legacy \`SessionGuard\` class and \`@requires\` decorator in \`aquilia.sessions.decorators\` have been removed. Switch to the unified \`PermissionEngine\` and the unified \`@requires\` decorator.

#### Before:
\`\`\`python
from aquilia.sessions.decorators import SessionGuard, requires

class CustomSessionGuard(SessionGuard):
    async def check(self, session: Session) -> bool:
        return bool(session.data.get("special_user"))

@requires(CustomSessionGuard())
async def handler(ctx):
    ...
\`\`\`

#### After:
\`\`\`python
from aquilia.auth.guards import requires

class CustomGuard:
    def check(self, ctx: Any) -> None:
        from aquilia.auth.faults import AUTHZ_POLICY_DENIED
        session = getattr(ctx, "session", None)
        if session is None or not session.data.get("special_user"):
            raise AUTHZ_POLICY_DENIED()

@requires(CustomGuard())
async def handler(ctx):
    ...
\`\`\`

---

## 5. Removing the Fluent \`AuthConfig\` Builder

If you set up custom authentication containers in testing or bootstrapping scripts using the \`AuthConfig\` builder, you must remove it. Configure integrations directly using dictionary payloads or the \`AquilaConfig.Auth\` classes.

#### Before:
\`\`\`python
from aquilia.auth.integration.di_providers import AuthConfig

config = (
    AuthConfig()
    .rate_limit(max_attempts=3)
    .strategies(["token"])
    .build()
)
\`\`\`

#### After:
\`\`\`python
config = {
    "rate_limit": {
        "max_attempts": 3,
    },
    "security": {
        "backends": ["aquilia.auth.backends.TokenBackend"],
    }
}
\`\`\`

---

## 6. Deprecated APIs & Relocations

* **\`AuthManager.logout()\`**: Deprecated in favor of \`AuthManager.sign_out()\`. Calling \`logout()\` now raises a \`DeprecationWarning\` but will invoke \`sign_out()\` internally for backward compatibility.
* **\`OptionalAuthMiddleware\`**: Deprecated in favor of \`AquilAuthMiddleware(require_auth=False)\` or the new \`AuthMiddleware\` class.
* **\`RateLimiter\` relocation**: The \`RateLimiter\` class has been moved from the \`manager\` module to \`aquilia.auth.manager_types\` to prevent circular imports. Update imports if you reference it directly.
* **\`ServiceScope\` Enum class**: Deprecated in favor of plain string literals (e.g., \`"singleton"\`, \`"app"\`, \`"request"\`, \`"transient"\`, \`"pooled"\`, \`"ephemeral"\`) paired with \`typing.Literal\` type hints (\`ServiceScopeLiteral\`). Using \`ServiceScope.SINGLETON\` or other members will now emit a \`DeprecationWarning\`.`,

    "sessions.md": `# Session Security, AuthManager & RateLimiting

Aquilia v1.3.1 introduces substantial security improvements to cookie-based and session-based authentication to prevent privilege escalation, alongside a refined \`AuthManager\` API and a standalone \`RateLimiter\` utility.

---

## 1. Session Serialization Hardening

In previous versions of Aquilia, the full set of user roles, scopes, and attributes was serialized and stored directly inside the session store database (or client-side cookie):

\`\`\`python
# Old, insecure v1.3.0 implementation:
session["roles"] = identity.get_attribute("roles", [])
session["scopes"] = identity.get_attribute("scopes", [])
session["status"] = identity.status.value
\`\`\`

This optimization meant that if an administrator modified a user's permissions, suspended their account, or deleted them, the changes **would not take effect** for requests authenticated via session cookies until their session expired.

In Aquilia v1.3.1, session serialization has been hardened. The \`bind_identity\` function only writes core identifiers:

\`\`\`python
# Hardened v1.3.1 implementation:
session.mark_authenticated(AuthPrincipal.from_identity(identity))
session["identity_id"] = identity.id
if identity.tenant_id is not None:
    session["tenant_id"] = identity.tenant_id
\`\`\`

Notice that **roles, scopes, and user attributes are no longer written to the session store**.

### Active Identity Resolution
* The \`SessionBackend\` captures the active session credentials.
* It extracts the \`identity_id\` (either from \`session.principal\` or from \`session.data["identity_id"]\`).
* It fetches a fresh \`Identity\` object directly from the \`IdentityStore\` on **every single request**.
* Authorization guards evaluate roles and scopes against this fresh database/cache state.

---

## 2. Shared Manager Types: \`RateLimiter\`

To protect brute-force paths (such as username/password login), Aquilia v1.3.1 introduces a standalone \`RateLimiter\` class in \`aquilia.auth.manager_types\` (and re-exported in \`aquilia.auth.manager\` for backward compatibility).

* **Constructor & Parameters**:
  \`\`\`python
  def __init__(
      self,
      max_attempts: int = 5,
      window_seconds: int = 900,
      lockout_duration: int = 3600,
  )
  \`\`\`
  Tracks failed authentication attempts per key (typically a username or IP address) within a sliding time window.
* **Core API Methods**:
  * \`record_attempt(key: str) -> None\`: Records a failed attempt. If attempts exceed \`max_attempts\` within the window, locks out the key.
  * \`is_locked_out(key: str) -> bool\`: Checks if the key is currently locked out.
  * \`get_remaining_attempts(key: str) -> int\`: Returns attempts left before lockout.
  * \`reset(key: str) -> None\`: Clears attempt history for the key on successful authentication.

---

## 3. \`AuthManager\` Refactored APIs

The \`AuthManager\` class (defined in \`aquilia.auth.manager\`) is the central coordinator for authentication operations. The following APIs were updated:

### Token Revocation
The token revocation API now supports access tokens by extracting the unique JWT identifier (\`jti\`) and blacklisting it:
* \`async def revoke_token(self, token: str, token_type: str = "refresh") -> None\`:
  * If \`token_type == "refresh"\`, revokes the refresh token directly.
  * If \`token_type == "access"\`, validates the access token, extracts the \`jti\` claim, and revokes it so subsequent validations reject it.

### Deprecated \`logout()\`
* **Signature**: \`async def logout(self, identity_id=None, session_id=None, access_token=None, refresh_token=None) -> None\`
* **Status**: **Deprecated** in favor of \`sign_out()\`. Raises a \`DeprecationWarning\` when called.

---

## 4. \`SessionAuthBridge\`

The \`SessionAuthBridge\` coordinates actions between \`AuthManager\` and \`SessionEngine\`:
* \`create_auth_session(identity, request, token_claims=None)\`: Resolves and binds authentication credentials to a new session.
* \`rotate_on_privilege_escalation(session, response)\`: Rotates the session ID (session fixation protection) after an escalating event (such as completing an MFA challenge).
* \`logout(session, response)\`: Destroys the current session.
* \`logout_all_devices(identity_id)\`: Revokes and purges all active session identifiers linked to a given identity ID across the session store.`
  },
  "1.4.0b1": {
    "README.md": `# Aquilia v1.4.0b1 Release Notes — "Foredeck Watch"

Expands the native engine foundation introduced in v1.4.0b0 with three additional C++ extensions
(\`_json\`, \`_dataengine\`, \`_core\`), a first-party native JSON engine backed by yyjson, a native
Contract validation fast path, per-field eligibility for the FieldPlan engine, a RequestContext
GC leak fix, sweeping hot-path correctness fixes across the controller/validation/DB/ASGI layers,
SQLite inline-execution for bounded index seeks, and a multi-platform binary wheel distribution
pipeline. See [releases/1.4.0b1/](releases/1.4.0b1/README.md) for full documentation.

### Performance

All figures measured with \`oha\`, 50 connections, 5 s, on macOS arm64 (Apple Silicon).

| Scenario | Before | After | Δ |
|---|---|---|---|
| \`db_single\` | 5 797 rps | 19 034 rps | +228% |
| \`db_queries\` | 1 496 rps | 8 759 rps | +485% |
| \`db_updates\` | 744 rps | 1 965 rps | +164% |
| \`validation\` | 1 809 rps (500s) | 15 075 rps (200s) | +733% |
| \`fortunes\` | 4 412 rps | 5 276 rps | +20% |
| \`json_large\` | 2 248 rps | 4 602 rps | +105% |
| ORM \`get()\` | 120.7 µs | 9.3 µs | **13× faster** |
| JSON encode small | — | 0.09 µs | 8.5× vs stdlib |
| JSON encode 100 KB | — | 174.5 µs | 3.9× vs stdlib |
| JSON decode small | — | 0.13 µs | 4.8× vs stdlib |
| DI resolve (scope check) | 66.8 ns | 22.9 ns | 3× faster |
`,
    "native_engines.md": `# Native Engines

- **Build system** (\`scikit-build-core\` + \`nanobind\`): CMake-based build for three optional C++20
  extensions. Extensions are individually optional — \`AQUILIA_ENGINE_OPTIONAL=ON\` means a missing
  C++ toolchain or compiler produces a pure-Python install, not a build failure.
- **\`aquilia/_core\`** — Radix-trie HTTP router and fixed-slot \`RequestContext\` object.
- **Fail-soft extension loaders** (\`aquilia/_core_loader.py\`, \`aquilia/_dataengine_loader.py\`):
  single import gate for each extension; a missing or ABI-mismatched extension degrades to pure
  Python. \`AQUILIA_ENGINE=0\` / \`AQUILIA_DATAENGINE=0\` force the pure-Python path.
- **\`AQUILIA_ENGINE_OPTIONAL\`** CMake variable — when \`ON\`, a missing compiler is a warning, not
  an error.
`,
    "performance.md": `# Performance

- **\`DISettings.strict_scopes\`** is now a plain \`bool\` field computed in \`__post_init__\`, replacing
  the former \`@property\` that read \`_strict_scopes\`. The private \`_strict_scopes\` field is removed.
  The new field is part of the public API (not prefixed with \`_\`).
- **\`DISettings.scope_check_enabled\`** added as a second derived field (was not separately cached
  before — each resolve tested \`scope_enforcement != "off"\` inline). Per-resolve DI cost:
  66.8 ns → 22.9 ns.
- **\`Container.resolve_async()\`**: \`provider.meta\` hoisted to a local variable; all 11 subsequent
  reads become plain slot reads (~19 ns each avoided).
- **\`aquilia/sqlite/_inline.py\`** — Inline SQLite execution for statements the query planner
  proves are bounded index seeks (\`SEARCH\` plan nodes). Thread-hop cost was 27 µs vs. 1.5 µs real
  work. Demotes permanently any statement measured slower than \`inline_max_duration_ms\`. Disable
  with \`inline_fast_queries=False\`.
- **\`aquilia/sqlite/_pool.py\`**: uncontended \`acquire()\` no longer constructs an \`asyncio.wait_for\`
  timer. Timeout semantics under real contention are unchanged.
`,
    "json_engine.md": `# JSON Engine

- **\`aquilia/_json\`** — First-party native JSON engine (Phase 1) backed by vendored
  [yyjson](https://github.com/ibireme/yyjson) 0.10.0 (MIT license).
  - \`decode.cpp\`: yyjson arena parser, no per-node allocation.
  - \`encode.cpp\`: direct emitter with heap work stack (not recursive — hostile deep nesting is a
    clean \`ValueError\`, not a stack overflow / crash).
  - \`escape.hpp\`: SWAR word-at-a-time scan for bytes needing escaping.
  - \`numeric.hpp\`: \`itoa\` for integers, yyjson shortest-round-trip for floats.
  - \`buffer.hpp\`: thread-local buffer pool — steady-state encoding stops allocating after first
    response of a given size.
  - Removable: every test passes with the extension absent (stdlib path).
- **\`aquilia/json\`** — New framework-wide JSON entry point replacing three inconsistent per-module
  fallback chains. \`dumps()\` always returns \`bytes\`; \`loads()\` accepts \`bytes | bytearray |
  memoryview | str\`. \`backend()\` reports the active codec (\`"aquilia._json"\` or \`"stdlib"\`).
  Third-party codecs (\`orjson\`, \`ujson\`) are deliberately not consulted.
`,
    "validation_engine.md": `# Validation Engine

- **\`aquilia/_dataengine\`** — ORM hydration and Contract validation engines.
  - \`FieldPlan\`: native per-field validation for Contract \`Sigil\`. Supports \`TextFacet\`, \`IntFacet\`,
    \`FloatFacet\`, \`BoolFacet\`, \`UUIDFacet\`, \`DateFacet\`, \`DateTimeFacet\`, \`TimeFacet\`,
    \`DecimalFacet\`, \`DurationFacet\`, \`BytesFacet\`, \`ChoiceFacet\`, \`LiteralFacet\`, \`EnumFacet\`
    (plain only), container kinds (\`LIST\`, \`SET\`, \`TUPLE\`, \`DICT\`), regex patterns, and nested
    sub-plans.
  - \`RowPlan\`: native ORM row hydration — field type conversion, UUID parsing, date/time
    construction.
  - Native UUID parser with exhaustive parity tests.
- **Per-field FieldPlan eligibility** (\`aquilia/contracts/_native_plan.py\`): fields the native
  plan cannot represent are individually *escaped* to \`Sigil.validate(..., _only=escaped)\` rather
  than sinking the whole contract. \`CompiledPlan(plan, escaped)\` named-tuple carries both sets.
  Previously one un-representable field disabled native validation for all sibling fields.
- **\`aquilia/contracts/sigil.py\`**: \`Sigil.validate(..., _only=frozenset)\` parameter — runs
  validation only for the named subset of fields (used by the escape path).
`,
    "bug_fixes.md": `# Bug Fixes

- **\`validate_body\` + controller engine double-binding**: both bound the \`body\` parameter →
  \`TypeError: got multiple values for keyword argument 'body'\` on every decorated handler. Fixed
  with \`__aquilia_owned_params__\` ownership protocol. (1809 → 15075 rps on the \`validation\`
  scenario; was returning 500 on every request for an entire release cycle.)
- **\`Response.json()\` double-encoding**: the stdlib path serialised to \`str\`, then
  \`_encode_body()\` encoded it again, traversing and allocating large payloads twice. Now \`bytes\`.
- **\`_check_json_depth\` recursion**: the depth guard itself raised \`RecursionError\` on deeply
  nested input, turning a \`400 Bad Request\` into a \`500 Internal Server Error\`. Now iterative.
- **Benchmark \`successRate\` miscalculation**: \`run.py\` computed success from oha's \`successRate\`
  (any completed exchange), so a scenario returning 500 on every request was published at
  "100.0% success". Success is now derived from the 2xx/3xx status distribution, with a
  single-request preflight per scenario.
- **\`aquilia/_json\` SWAR mask bug**: the first SWAR \`less-than\` check lacked \`& ~w\`, causing
  every byte ≥ 0x80 to be reported as a control character — corrupted the first non-ASCII string
  encountered.
- **\`aquilia/_json\` bignum decoding**: integers > 2**64 were silently decoded as \`float\`, turning
  a 30-digit ID into an approximate value. Now read with \`YYJSON_READ_BIGNUM_AS_RAW\` and
  reconstructed as an exact Python \`int\`.
- **\`aquilia/_json\` nested container key overwrite**: while iterating a nested object's children,
  the parent key was overwritten; \`{"a": {"b": 1}, "c": 2}\` lost \`"a"\`. Key now lives on the
  stack frame.
- **\`RequestContext\` GC leak**: nanobind's \`inst_traverse\` visited only \`__dict__\`, not C++
  fields. A cycle through a slot (e.g. \`ctx.state = {"ctx": ctx}\`) was invisible to the garbage
  collector — 1 leaked \`RequestCtx\` per request (unbounded growth). Fixed with custom
  \`tp_traverse\`/\`tp_clear\` visiting all 7 \`PyObject*\` slots.
- **\`DotEnvLoader.reset()\`**: did not clear configuration state, so test isolation was broken
  between tests that called \`reset()\`. Now fully resets the loader.
- **Windows CI test compatibility**: \`WSAEACCES\` error handling, signal sending, UDS guards
  for cross-platform parity.
- **Python 3.13 Windows thread starvation** in \`test_concurrency_stress\`: now uses a condition
  variable instead of spinning.
`,
    "migration.md": `# Migration Guide — Aquilia v1.4.0b0 → v1.4.0b1

This guide covers all the necessary steps and information to migrate your Aquilia application from version 1.4.0b0 to 1.4.0b1. Although this is a beta release, several critical internal APIs and architectural patterns have evolved.

## 1. DISettings API Change

The \`DISettings.strict_scopes\` property is now a plain \`bool\` field computed during \`__post_init__\`. The private \`_strict_scopes\` field has been completely removed.

**Old Code:**
\`\`\`python
# Previously accessing the private field or relying on the property getter
settings = DISettings(strict_scopes="on")
is_strict = settings._strict_scopes
\`\`\`

**New Code:**
\`\`\`python
# Now a public boolean field directly on the settings object
settings = DISettings(strict_scopes="on")
is_strict = settings.strict_scopes
\`\`\`

## 2. Aquilia JSON Unified Codec

We have introduced a new framework-wide JSON entry point replacing three inconsistent per-module fallback chains. 

If you previously imported \`json\`, \`orjson\`, or \`ujson\` directly in your application code for performance, you should now use the unified Aquilia JSON codec:

**Old Code:**
\`\`\`python
import orjson

def my_handler():
    return orjson.dumps({"key": "value"})
\`\`\`

**New Code:**
\`\`\`python
from aquilia import json

def my_handler():
    # Automatically uses the native \`_json\` engine if available
    return json.dumps({"key": "value"})
\`\`\`

Note: \`dumps()\` always returns \`bytes\`. \`loads()\` accepts \`bytes | bytearray | memoryview | str\`. Third-party codecs like \`orjson\` and \`ujson\` are no longer consulted by the framework.

## 3. validate_body Double-Bind Fix

A major bug where both \`validate_body\` and the controller engine bound the \`body\` parameter has been fixed. This previously resulted in a \`TypeError: got multiple values for keyword argument 'body'\` on decorated handlers.

**No action is needed on your part.** The engine now respects the \`__aquilia_owned_params__\` protocol to avoid double-binding parameters claimed by decorators.

## 4. Native Extensions

Aquilia v1.4.0b1 introduces three native C++ extensions (\`_core\`, \`_dataengine\`, \`_json\`). 

### Verifying Loaded Extensions

You can verify which backend is active by checking the module attributes:

\`\`\`python
from aquilia import json
print(json.backend())  # Output: "aquilia._json" or "stdlib"
\`\`\`

### Disabling Extensions

If you experience issues, you can force the pure-Python fallback path by setting environment variables before starting your application:

\`\`\`bash
export AQUILIA_ENGINE=0
export AQUILIA_DATAENGINE=0
\`\`\`

## 5. SQLite Inline Execution

The query planner now executes bounded index seeks inline, reducing thread-hop cost from 27 µs to 1.5 µs.

If this causes unexpected behavior in your workloads, you can disable it via configuration:

\`\`\`python
# In your database configuration
db_config = SQLiteConfig(
    inline_fast_queries=False,
    # ... other settings
)
\`\`\`

## Upgrade Checklist

1. Review any direct usages of \`_strict_scopes\` and update to \`strict_scopes\`.
2. Migrate direct third-party JSON library imports (\`orjson\`, \`ujson\`) to \`aquilia.json\`.
3. Verify that your application handles \`bytes\` returned from \`json.dumps()\`.
4. (Optional) Remove any workarounds previously implemented for the \`validate_body\` \`TypeError\`.
5. Test your application to ensure native extensions are loading correctly.

## Backward Compatibility Notes

- The removal of the private \`_strict_scopes\` field may break internal plugins that relied on it.
- \`Response.json()\` now consistently returns \`bytes\` (was previously returning \`str\` on the stdlib path). Ensure middleware or custom response handlers are prepared for \`bytes\`.
`,
    "build_and_distribution.md": `# Build & Distribution — Aquilia v1.4.0b1

This release overhauls the build and distribution pipeline for Aquilia, introducing a robust, native C++ extensions build system and a comprehensive multi-platform wheel matrix.

## Build System Overview

Aquilia now utilizes **scikit-build-core** combined with **nanobind** and **CMake** to compile its three optional C++20 extensions (\`_core\`, \`_dataengine\`, \`_json\`). 

This architecture allows us to tightly integrate native code with the Python runtime, achieving significant performance gains without sacrificing the developer experience. The use of \`nanobind\` provides lightweight, fast bindings, while CMake ensures consistent builds across all major operating systems.

## Building from Source

If you need to build Aquilia from source (e.g., for development or unsupported platforms), ensure you have a C++20 compatible compiler installed (GCC 10+, Clang 11+, or MSVC 2019+).

\`\`\`bash
# Clone the repository
git clone https://github.com/tubox-labs/Aquilia.git
cd Aquilia

# Install build dependencies
pip install -r requirements-build.txt

# Build and install the package
pip install -e .
\`\`\`

## The \`AQUILIA_ENGINE_OPTIONAL\` Flag

The C++ extensions are designed to be individually optional. We have introduced the \`AQUILIA_ENGINE_OPTIONAL\` CMake variable to control the build behavior when a compiler is missing.

- When \`AQUILIA_ENGINE_OPTIONAL=ON\` (the default for end-users), a missing C++ toolchain or compiler will produce a warning rather than an error, and the installation will gracefully fall back to a pure-Python build.
- When \`AQUILIA_ENGINE_OPTIONAL=OFF\` (used in CI/CD), the build will strictly fail if the extensions cannot be compiled.

## Multi-Platform Wheel Pipeline

To provide a seamless installation experience, we now distribute pre-compiled binary wheels across multiple architectures and operating systems using \`cibuildwheel\`.

| Platform | Architecture | Python Versions |
|----------|--------------|-----------------|
| Linux | \`x86_64\` | 3.10, 3.11, 3.12, 3.13 |
| Linux | \`aarch64\` | 3.10, 3.11, 3.12, 3.13 |
| macOS | \`x86_64\` | 3.10, 3.11, 3.12, 3.13 |
| macOS | \`arm64\` (Apple Silicon) | 3.10, 3.11, 3.12, 3.13 |
| Windows | \`AMD64\` | 3.10, 3.11, 3.12, 3.13 |

## Installing Pre-Built Wheels vs Source

For the vast majority of users, installing Aquilia via pip will automatically fetch the appropriate pre-built wheel for your system:

\`\`\`bash
pip install aquilia
\`\`\`

This skips the compilation step entirely, providing instant access to the native extensions. If you are on an exotic architecture (e.g., \`ppc64le\`), pip will automatically attempt to build from the source distribution (\`sdist\`).

## Forcing a Pure-Python Install

If you wish to force the installation of the pure-Python version (bypassing native extensions completely), you can set the following environment variable before installing:

\`\`\`bash
export AQUILIA_PURE_PYTHON=1
pip install aquilia
\`\`\`

Alternatively, you can disable the extensions at runtime using \`AQUILIA_ENGINE=0\` and \`AQUILIA_DATAENGINE=0\`.

## \`pyproject.toml\` Changes

Several significant changes were made to \`pyproject.toml\` to support the new build system:

- Added a \`[tool.cibuildwheel]\` table to configure the wheel building matrix.
- Corrected the \`metadata.version\` key path for \`scikit-build-core\` 0.9+ compatibility. The path was updated from \`tool.scikit-build.metadata.version\` to \`tool.scikit-build.metadata.version.*\`.
- Added \`scikit-build-core\` and \`nanobind\` to the \`build-system.requires\` list.

## CI Workflow Overview

Our Continuous Integration has been expanded with a dedicated Wheel Workflow (\`.github/workflows/wheels.yml\`).

This workflow ensures that every commit to the main branch is validated across all matrix targets. It leverages \`cibuildwheel\` to automatically provision the correct build environments (using manylinux Docker images for Linux), compile the C++ extensions, and run the test suite against the generated wheels before they are uploaded as release artifacts.
`,
  },
  "1.4.0b3": {
    "README.md": `# Aquilia v1.4.0b3 Release Notes — "Helmsman's Compass"

Aquilia v1.4.0b3 continues the beta cycle for the 1.4 series with the new **\`aquilia.vectordb\`** subsystem, a comprehensive overhaul of the **CLI architecture**, introduction of the **Unified Health Checks Engine**, single-source **Exit Code contract**, lazy **\`AqContext\` state thread**, a documented and enforced **subsystem boot contract**, and native C++ **router memory leak resolution**.

---

## Table of Contents

1. [Release Overview](#release-overview)
2. [Highlights](#highlights)
3. [Vector Database Subsystem](vectordb.md)
   - \`aquilia.vectordb\` — typed models over embedded elips
   - \`VectorDatabaseIntegration\`, \`Workspace.vectordb()\`, \`AquilaConfig.VectorDB\`
   - \`AppManifest.vector_models\` and \`vector_models/\` discovery
   - \`VectorDBSubsystem\` — priority 28, conditional required-ness
   - SQL-ORM interop: \`Link\`, \`resolve\`, \`mirror\`, \`as_models\`, \`reindex\`
4. [\`aq vectordb\` Command Reference](vectordb_cli.md)
   - \`status\`, \`gpu\`, \`models\`, \`inspect\`, \`stats\`
   - \`compact\`, \`vacuum\`, \`compress\`, \`reindex\`, \`reembed\`
   - Lock discipline and common workflows
5. [CLI Architecture Overhaul](cli_modernization.md)
   - \`aquilia.cli.core\` subsystem layout
   - \`AqContext\` — thread-safe, lazily resolved ambient CLI state
   - \`ExitCode\` — single source of truth for process return codes
   - \`CliFault\` — structured fault domain replacing \`sys.exit()\`
   - \`LoadedWorkspace\` — Python-first workspace loader with regex fallback
   - \`CommandSpec\` — category-driven command registry & help grouping
6. [Unified Health Checks Engine](checks_engine.md)
   - \`Finding\` & \`Check\` protocol (\`@register_check\`)
   - Standardized runners and human/JSON report renderers
   - Config-driven subsystem probes across core framework modules
   - The new \`vectordb.driver\` check
   - Workspace integrity probes & route extraction checking
7. [Subsystem Boot Contract](subsystem_boot_contract.md)
   - \`BootContext.di_containers()\` and \`DI_CONTAINER_KEY\`
   - \`_timeout\` enforcement in \`BaseSubsystem.initialize()\`
   - Live \`/health\` checks replacing the boot-time snapshot
   - Who drives subsystems, and why there is no \`SubsystemOrchestrator\`
8. [Admin Lifecycle & Rate Limiter](admin_lifecycle.md)
   - Admin startup/shutdown hooks wired into \`AquiliaServer\`
   - \`AdminRateLimiter.force_cleanup()\` public sweep API
9. [Native Router Memory Leak Fix](router_memory_leak_fix.md)
   - Native C++ nanobind Router instance cleanup on server shutdown
   - \`ControllerRouter.clear()\` protocol
   - \`ASGIAdapter.shutdown()\` lifecycle hook
10. [Bug Fixes & Refactorings](bug_fixes.md)
    - Silent exit code 0 bug on workspace/DB failures fixed
    - Route count reporting mismatch fixed (real HTTP routes vs controller counts)
    - Non-existent route attribute inspection bug fixed
    - Subsystem DI registration, timeout, and health-check defects fixed
    - Admin lifecycle never invoked; rate-limit sweep no-op on fresh hosts
    - Workspace integration detection returning bound methods
    - Docsite TS2657 React fragment build error fixed
11. [Migration Guide & Breaking Changes](migration.md)
    - Removal of legacy CLI parsers (\`discovery_cli.py\`, \`parsers/\`)
    - Exit code changes for CI/CD pipelines
    - Optional \`vectordb\` extra and the Python 3.10 marker
    - Upgrade checklist & compatibility matrix

---

## Release Overview

Aquilia v1.4.0b3 does two things: it adds a whole new data subsystem, and it pays down operational debt in the layers that boot and diagnose everything else.

**\`aquilia.vectordb\`** is the new surface. Retrieval-augmented workloads previously had no home in the framework — applications bolted a vector client onto a service, hand-rolled serialization between the ORM and the store, and got no boot validation, no health reporting, no CLI, and no fault taxonomy. The subsystem gives vector collections the same declarative shape the SQL ORM gives tables, keeps its driver (\`elips\`) an optional extra, and makes the two failure modes that produce *silently wrong* results — dimension mismatch and embedder-lineage mismatch — hard errors instead of confident nonsense.

The rest is repair. Prior to this release, \`aq doctor\` and \`aq validate\` relied on ~1,000 lines of duplicated, drifting logic that silently caught errors, printed warning banners, and exited with status code \`0\`. Commands scraped \`workspace.py\` with brittle regex patterns and probed non-existent controller attributes. The subsystem layer documented a timeout it never enforced and a DI key nothing ever set. Admin's lifecycle hooks were written, tested, and never called. \`/health\` served a boot-time snapshot that could not notice a dependency dying an hour later.

v1.4.0b3 fixes each of those where it lives: a unified, modular CLI architecture (\`aquilia.cli.core\`, \`aquilia.cli.checks\`, \`aquilia.cli.introspect\`) built around a single source of truth for exit codes, and a subsystem layer whose contract is now written down and enforced by tests.

---

## Highlights

### 1. Vector Database Subsystem

\`aquilia.vectordb\` — 24 modules — brings typed vector models, similarity search, embedders, chunking, GPU policy, quantization, and SQL-ORM interop into the framework:

\`\`\`python
from aquilia.vectordb import VectorModel, KeyField, TextField, VectorField, Field

class Document(VectorModel):
    key:    str         = KeyField(prefix="doc_")
    body:   str         = TextField(embed=True, min_length=1)
    vector: list[float] = VectorField(dimension=384)
    source: str         = Field(default="web", indexed=True)

    class Meta:
        collection = "documents"
        store = "default"

hits = await Document.vectors.query().filter(source="docs").search(text="release notes", limit=10)
\`\`\`

The driver is an optional extra (\`pip install 'aquilia[vectordb]'\`). An install without it behaves exactly as before: importing the package succeeds, and \`VectorNotInstalledFault\` surfaces at first *use*. Discovery imports nothing when no module declares a vector model.

See [vectordb.md](vectordb.md) and [vectordb_cli.md](vectordb_cli.md).

### 2. Unified Health Checks Engine & Single-Source Exit Codes

The fragmented \`doctor.py\` and \`validate.py\` implementations are merged into a single health check registry (\`aquilia.cli.checks\`). Every check yields structured \`Finding\` objects with stable error codes (e.g. \`AQ_DB_MISSING\`, \`AQ_ROUTE_CONFLICT\`), a severity (\`INFO\`, \`WARN\`, \`ERROR\`, \`FATAL\`), a location, and actionable remedies.

Exit codes are governed strictly by \`aquilia.cli.core.exits.exit_code_for()\`:
- \`ExitCode.OK\` (\`0\`) — All checks pass or emit only \`INFO\`/\`WARN\` findings.
- \`ExitCode.FAILED\` (\`1\`) — At least one \`ERROR\` or \`FATAL\` finding was discovered.
- \`ExitCode.USAGE\` (\`2\`) — Argument/invocation error.
- \`ExitCode.CONFIG\` (\`3\`) — Workspace or configuration file could not be loaded.
- \`ExitCode.INTERNAL\` (\`4\`) — Unhandled internal CLI exception.

### 3. \`AqContext\` & Python-First Workspace Loading

Ad-hoc \`ctx.obj\` dictionary manipulation is replaced by \`AqContext\`. Workspace discovery is lazy: non-workspace commands like \`aq init\`, \`aq version\`, and \`aq --help\` execute instantaneously without incurring workspace import overhead.

When loaded, \`workspace.py\` is executed as Python code rather than parsed with regular expressions. Declared starter controllers (\`.starter("name")\`) and module-level \`route_prefix\` definitions are accurately parsed into \`LoadedWorkspace\`. Regex parsing remains solely as an automatic fallback when user code contains import errors.

### 4. Subsystem Coverage Expansion

Framework subsystems totalling ~45,000 lines of code had zero CLI health monitoring in previous releases. \`aquilia.cli.checks.subsystems\` introduces config-driven probes for:
\`tasks\`, \`templates\`, \`storage\`, \`cache\`, \`mail\`, \`i18n\`, \`otel\`, \`sse\`, \`versioning\`, \`http\`, \`auth\`, \`sockets\`, \`contracts\`, \`mlops\`, \`vectordb\`, and \`admin\`.

Probes are strictly config-driven and remain silent for unused subsystems, avoiding noise in minimal applications. \`vectordb\` additionally gets a dedicated \`vectordb.driver\` check that reports \`AQ_VECTORDB_DRIVER_MISSING\` when a workspace declares vector stores on an install without \`elips\`.

### 5. Subsystem Boot Contract Documented and Enforced

\`aquilia.subsystems\` declared a 30-second initialization timeout that nothing read, and a DI \`shared_state\` key that nothing set. Both are fixed:

- \`BaseSubsystem.initialize()\` now wraps \`_do_initialize\` in \`asyncio.wait_for(...)\`, so a subsystem blocking on an unreachable dependency degrades to \`UNHEALTHY\` with a named cause instead of hanging the boot forever.
- \`BootContext.di_containers()\` is the single DI resolution path — explicit container first, then every container in \`registry.di_containers\`. \`StorageSubsystem\` and \`EffectSubsystem\` both use it, so both actually register.
- \`/health\` now calls \`HealthRegistry.run_checks()\` before rendering, so a backend that died an hour after boot is no longer masked by the boot-time snapshot.

The package docstring also states plainly what it is: the entry point for hosts that drive subsystems themselves. \`AquiliaServer\` boots storage, cache, tasks, mail and effects through its own ordered \`_setup_*\` methods, and there is deliberately no \`SubsystemOrchestrator\` to keep in sync with it.

See [subsystem_boot_contract.md](subsystem_boot_contract.md).

### 6. Admin Lifecycle Wired

\`AdminLifecycle.on_startup()\` / \`on_shutdown()\` were written, tested in isolation, and never called by anything. Admin routes worked; the audit log was never flushed, the rate limiter never swept, and the cache service and task manager were never resolved from DI. \`AquiliaServer.startup()\` gained Step 3.25 and \`shutdown()\` its mirror, both gated on \`config["integrations"]["admin"]\` and non-fatal on failure.

See [admin_lifecycle.md](admin_lifecycle.md).

### 7. Native Router Memory Leak Resolution

During server shutdown, ASGI lifespan termination, or test teardown, native C++ \`Router\` instances wrapping nanobind bindings could remain referenced in memory, producing nanobind leak warnings on process termination.

v1.4.0b3 adds \`ControllerRouter.clear()\` and updates \`AquiliaServer.shutdown()\` and \`ASGIAdapter.shutdown()\` to explicitly reset C++ router references and internal route tables, eliminating leak warnings.

---

## Summary of Subsystem Changes

| Subsystem / Module | Status | Summary |
|---|---|---|
| \`aquilia.vectordb\` | **New** | 24-module typed vector layer over embedded elips — models, fields, queries, EQL, embedders, chunking, GPU policy, quantization, ORM interop |
| \`aquilia.vectordb.subsystem\` | **New** | \`VectorDBSubsystem\` — priority 28, 60s timeout, \`_required\` raised when stores are declared |
| \`aquilia.integrations.vectordb\` | **New** | \`VectorDatabaseIntegration\` — typed store declaration, normalizes \`{alias: config}\` into store entries |
| \`aquilia.cli.commands.vectordb\` | **New** | \`aq vectordb\` group — \`status\`, \`gpu\`, \`models\`, \`inspect\`, \`stats\`, \`compact\`, \`vacuum\`, \`compress\`, \`reindex\`, \`reembed\` |
| \`aquilia.pyconfig\` | **Improved** | \`AquilaConfig.VectorDB\` nested config class (disabled by default) |
| \`aquilia.workspace\` | **Improved** | \`Workspace.vectordb()\` builder; \`vectordb\` recognised by \`integrate()\`; emitted into \`to_dict()\` |
| \`aquilia.config._loader\` | **Improved** | \`ConfigLoader.get_vectordb_config()\` with disabled-by-default defaults |
| \`aquilia.manifest\` | **Improved** | \`AppManifest.vector_models\`, \`ComponentKind.VECTOR_MODEL\`, \`vector_models\` in default \`auto_discovery\` |
| \`aquilia.aquilary.core\` | **Improved** | \`AppContext.vector_models\`; \`_discover_vector_models()\` scan and \`_register_vector_models()\` import pass |
| \`aquilia.subsystems.base\` | **Improved** | \`DI_CONTAINER_KEY\`, \`BootContext.di_containers()\`, enforced \`_timeout\`, documented population contract |
| \`aquilia.subsystems.effects\` | **Fixed** | DI registration via \`di_containers()\`; \`health_check()\` uses \`details=\` not the non-existent \`metadata=\` |
| \`aquilia.storage.subsystem\` | **Fixed** | DI registration repaired (dead \`_di_registry\` key); registers a live health check |
| \`aquilia.asgi\` | **Improved** | \`/health\` runs \`HealthRegistry.run_checks()\` before rendering; \`ASGIAdapter.shutdown()\` releases runtime, container & middleware chain |
| \`aquilia.server\` | **Improved** | Admin lifecycle startup (Step 3.25) and shutdown wired; \`shutdown()\` invokes \`controller_router.clear()\` |
| \`aquilia.admin.security\` | **Improved** | \`AdminRateLimiter.force_cleanup()\` public sweep API; \`_sweep()\` returns exact removal counts |
| \`aquilia.admin.subsystems\` | **Fixed** | \`rate_limit_cleanup()\` no longer pokes private state — no-op on hosts up < \`cleanup_interval\` fixed |
| \`aquilia.cli.checks.subsystems\`| **Improved** | \`_integration()\` reads \`Workspace._integrations\` and skips callables; new \`vectordb.driver\` check |
| \`aquilia.cli.core.registry\` | **Improved** | \`vectordb\` categorised under **Database** in \`aq --help\` |
| \`aquilia.cli.core.exits\` | **New** | \`ExitCode\` enum, \`SEVERITY_ORDER\`, \`exit_code_for()\` single source of truth |
| \`aquilia.cli.core.faults\` | **New** | \`CliFault\` hierarchy (\`WorkspaceNotFoundFault\`, \`WorkspaceLoadFault\`, etc.) |
| \`aquilia.cli.core.context\` | **New** | \`AqContext\` lazy state thread replacing \`ctx.obj\` dictionary access |
| \`aquilia.cli.core.workspace\` | **New** | \`LoadedWorkspace\`, \`load_workspace()\`, \`ensure_importable()\` |
| \`aquilia.cli.checks.base\` | **New** | \`Finding\`, \`Check\`, \`CheckResult\`, \`@register_check()\`, \`run_checks()\` |
| \`aquilia.cli.checks.report\` | **New** | \`render_human()\`, \`render_json()\`, \`summarise()\`, \`result_exit_code()\` |
| \`aquilia.cli.checks.workspace\` | **New** | Core health checks (Python version, modules, manifests, routes, DI, DB) |
| \`aquilia.cli.introspect.routes\`| **New** | Route introspection via \`ControllerCompiler\` (replaces legacy attribute probes) |
| \`aquilia.cli.discovery_cli\` | **Removed** | Legacy discovery CLI helper deleted |
| \`aquilia.cli.parsers\` | **Removed** | Legacy manifest regex parsers (\`module.py\`, \`workspace.py\`) deleted |
| \`aquilia.controller.router\` | **Improved** | \`ControllerRouter.clear()\` releases C++ nanobind \`_native\` instance |
| \`pyproject.toml\` | **Improved** | New \`vectordb\` extra (\`elips>=1.1.0; python_version >= '3.11'\`), folded into \`full\` |
| \`aqdocx\` | **Fixed** | Fixed TS2657 JSX single-parent return error in \`MiddlewareOverview.tsx\` |

---

## Performance Improvements

1. **Lazy CLI Execution**: Commands that do not require workspace inspection (\`aq init\`, \`aq version\`, \`aq --help\`, \`aq mcp\`) run in \`<15ms\` by avoiding workspace file discovery and import overhead.
2. **Cached Manifest Resolution**: \`LoadedWorkspace.manifest()\` caches \`AppManifest\` references during multi-check runs, eliminating redundant disk reads.
3. **Native Router Deallocation**: Timely release of native C++ CPython extension structures reduces memory overhead during unit testing and server restarts.
4. **Zero-Cost Vector Layer When Unused**: \`aquilia.vectordb.__init__\` defers \`engine\`, \`gpu\`, \`interop\`, \`embedders\`, \`eql\`, \`chunking\` and \`subsystem\` behind \`_LAZY_ATTRS\`, so nothing reaches \`elips\` on import. Vector-model discovery imports nothing when no module declares one, so an app without vector models pays no import cost at all.
5. **Dedicated Vector Thread Pool**: elips calls run on a named \`aquilia-vdb\` \`ThreadPoolExecutor\` rather than the default executor, so a long \`compact()\` cannot starve unrelated \`run_in_executor\` callers, and a stalled vector operation is identifiable in a stack dump.
6. **Bounded Subsystem Boot**: enforced \`_timeout\` turns an unreachable dependency from an indefinite hang into a bounded \`UNHEALTHY\` result.

---

## Developer Experience Improvements

- **Actionable CLI Diagnostics**: Every health finding displays a stable error code (e.g. \`[AQ_DB_MISSING]\`), source location (\`at: db.sqlite3\`), and a concrete fix (\`fix: Run migrations to create the DB\`).
- **Machine-Readable Output**: \`aq doctor --json\`, \`aq validate --json\`, and every \`aq vectordb\` subcommand's \`--json\` emit standardized payloads structured for CI/CD test runners.
- **Accurate Route Tree**: \`aq inspect routes\` compiles routes using \`ControllerCompiler\`, displaying exact paths served (including module prefixes and starter routes).
- **Vector Slot Introspection**: \`aq vectordb models\` shows how each attribute was routed (key / text / vector / payload / link) — routing is resolved at class creation and is otherwise invisible in the source.
- **Honest \`/health\`**: the endpoint re-runs registered checks per request, so a dead dependency is visible without a restart.

---

## Documentation Improvements

- New \`docs/vectordb.md\` — the complete \`aquilia.vectordb\` reference (fields, codecs, queries, EQL, embedders, chunking, GPU, faults, operations), linked from \`docs/README.md\`.
- New release pages: [vectordb.md](vectordb.md), [vectordb_cli.md](vectordb_cli.md), [subsystem_boot_contract.md](subsystem_boot_contract.md), [admin_lifecycle.md](admin_lifecycle.md).
- \`aquilia.subsystems\` package docstring now states who drives subsystems and why there is no \`SubsystemOrchestrator\`, with a composable ordered-boot example.
- \`BootContext\` carries a field-by-field population contract table naming who sets each field and what happens when it is \`None\`.
- \`BaseSubsystem\` documents that \`required\` may be computed during \`_do_initialize\` and must be read after \`initialize()\` returns.

---

## Upgrade Checklist

- [ ] Update \`aquilia\` to \`1.4.0b3\` in \`pyproject.toml\` / \`requirements.txt\`.
- [ ] Update CI/CD pipelines to expect non-zero exit codes (code \`1\` or \`3\`) when \`aq validate\` or \`aq doctor\` encounters errors.
- [ ] Remove any internal references to deprecated \`aquilia.cli.parsers\` modules.
- [ ] Run \`aq doctor\` to perform a full workspace health check under the new engine.
- [ ] If adopting vector search: \`pip install 'aquilia[vectordb]'\` (Python 3.11+), add \`.vectordb(stores={...})\` to \`workspace.py\`, declare models under \`modules/<app>/vector_models.py\`, then verify with \`aq vectordb status\` and \`aq vectordb models\`.
- [ ] If you build \`BootContext\` by hand: replace \`shared_state["_di_registry"]\` with \`shared_state[DI_CONTAINER_KEY]\`, or pass \`registry=\`.
- [ ] If you subclass \`BaseSubsystem\`: confirm \`_do_initialize\` is cancellation-safe, or set \`_timeout = 0\` to opt out of the bound.
- [ ] If you poke \`AdminRateLimiter\` privates: switch to \`force_cleanup()\`.
- [ ] If \`/health\` is polled aggressively: budget for one check invocation per registered subsystem per request.

---

## Known Issues

- **\`elips\` has no cp310 wheels.** On Python 3.10 the \`vectordb\` extra installs nothing and vector support degrades to \`VectorNotInstalledFault\` at first use. The environment marker is deliberate — without it, \`aquilia[full]\` would be unresolvable on 3.10 rather than simply omitting vector support.
- **Single-writer stores and \`workers > 1\`.** elips takes an exclusive lock per database directory. Multi-worker deployments must give each worker its own store path or mark the shared store \`read_only=True\`. There is no shared-writer mode planned; elips is embedded by design.
- **\`VectorDBSubsystem\` is not driven by \`AquiliaServer\`.** Like every other \`BootContext\` subsystem, it is initialized by the host — an embedder, an alternative runner, a test, or a module lifecycle hook. The \`aq vectordb\` commands configure and shut down \`VectorRegistry\` themselves and need none of this. See [vectordb.md](vectordb.md#wiring-the-store-lifecycle).

---

## Credits

Special thanks to the Aquilia core team and community contributors for auditing CLI failure modes, the subsystem boot layer, and admin lifecycle wiring, and for implementing native C++ lifetime bounds and the vector database subsystem.

`,
    "vectordb.md": `# Vector Database Subsystem — v1.4.0b3

\`aquilia.vectordb\` is a new first-class subsystem: a typed model layer over [elips](https://pypi.org/project/elips/), an embedded vector database. It gives vector collections the same declarative shape Aquilia's SQL ORM gives tables — models, managers, queries, faults, subsystem lifecycle, CLI — without pretending the two storage engines are the same thing.

Full reference: [\`docs/vectordb.md\`](../../docs/vectordb.md).

---

## Overview

| Aspect | Value |
|---|---|
| Package | \`aquilia.vectordb\` (24 modules) |
| Driver | \`elips >= 1.1.0\` — **optional extra** |
| Install | \`pip install 'aquilia[vectordb]'\` |
| Config | \`Workspace.vectordb(...)\`, \`Integration.vectordb(...)\`, \`AquilaConfig.VectorDB\` |
| Manifest | \`AppManifest.vector_models\`, \`ComponentKind.VECTOR_MODEL\` |
| Subsystem | \`VectorDBSubsystem\` — priority 28, timeout 60s |
| CLI | \`aq vectordb\` (10 subcommands) |
| Health check | \`vectordb.driver\` → \`AQ_VECTORDB_DRIVER_MISSING\` |

---

## Motivation

Retrieval-augmented workloads had no home in Aquilia. Applications that wanted similarity search bolted a client library onto a service, hand-rolled serialization between the ORM and the vector store, and had no boot-time validation, no health reporting, no CLI, and no fault taxonomy. Two problems followed:

1. **Silent wrongness.** A vector written under one embedding model and searched under another returns a confidently ranked list of meaningless results. Nothing in a hand-rolled client notices.
2. **No lifecycle.** A store that failed to open answered every search with an empty list, which reads as "no results" rather than "broken".

The subsystem exists to make both loud.

---

## Design goals

- **Optional at every level.** \`elips\` is a C++ extension. Importing \`aquilia.vectordb\` on an install without it succeeds; the fault surfaces at first *use* as \`VectorNotInstalledFault\` carrying the install hint. Nothing in the package imports \`elips\` at module scope.
- **One-way dependency.** \`aquilia.vectordb\` imports \`aquilia.models\`; nothing in \`aquilia.models\` imports \`aquilia.vectordb\`. That arrow is what keeps the extra genuinely optional.
- **Loud over lossy.** Dimension mismatches, embedder-lineage mismatches, nested payloads, and unsupported lookups are rejected — most of them at class-creation time — rather than coerced.
- **Same shapes as the ORM.** \`VectorModel\`/\`Model\`, \`VectorQuery\`/\`Q\`, \`VectorRegistry\`/\`ModelRegistry\`, \`VectorFault\`/\`Fault\`. Nothing new to learn where nothing new is happening.

---

## Architecture

\`\`\`
aquilia/vectordb/
├── __init__.py      # Lazy re-exports (_LAZY_ATTRS) — elips never touched on import
├── _compat.py       # is_available(), require_elips()
├── metaclass.py     # VectorModelMeta — slot routing, registration at class creation
├── base.py          # VectorModel, VectorState
├── fields.py        # KeyField/VectorField/TextField/Field/ScoreField/LinkField
├── annotations.py   # Legacy Annotated markers (Key, Dimension, Text, Payload, …)
├── schema.py        # VectorSchema, VectorOptions, PayloadSpec
├── codecs.py        # Python type ↔ elips MetaValue codecs
├── manager.py       # VectorManager (\`Model.vectors\`)
├── query.py         # VectorQuery, Hit
├── filters.py       # VF trees → CompiledFilter
├── expressions.py   # FieldExpression (Document.views >= 10)
├── eql.py           # parse_eql — string filter grammar
├── embedders.py     # local / sentence-transformers / fastembed / openai / ollama / callable
├── chunking.py      # character / recursive / sentence / token chunkers
├── configs.py       # VectorStoreConfig, GpuOptions, EmbedderOptions, QuantizationConfig
├── engine.py        # VectorEngine — one elips database
├── pool.py          # VectorPool — the \`aquilia-vdb\` thread pool
├── registry.py      # VectorRegistry — models, stores, live engines
├── gpu.py           # probe(): built vs available, DeviceInfo
├── interop.py       # Link, resolve, mirror, as_models, reindex
├── faults.py        # VectorFault hierarchy (21 codes)
├── signals.py       # vector_pre_save / post_save / pre_delete / post_delete
└── subsystem.py     # VectorDBSubsystem — BootContext lifecycle
\`\`\`

### Boot position

\`VectorDBSubsystem\` declares priority **28** — after storage (25), before database (30). Vector stores may live under a storage-managed path, so storage settles first; nothing in the SQL ORM is needed to open one, so it does not wait on the database. \`_timeout\` is **60 seconds** rather than the usual default: opening a store rebuilds its index, which is slower than a socket connect.

### Conditional required-ness

\`_required\` starts \`False\` and is raised to \`True\` inside \`_do_initialize\` **only when stores are actually configured**:

\`\`\`python
stores = config.get("stores") or []
if not stores:
    logger.warning("vectordb is enabled but declares no stores — nothing to open")
    return

# A declared store that fails to open must stop the boot.
self._required = True
\`\`\`

An app with no \`vectordb\` block boots exactly as before. An app that *declared* a store and could not open it fails loudly — see [Edge cases](#edge-cases).

> **\`required\` is only final after \`initialize()\` returns.** Read before that, it holds the class default. \`BaseSubsystem\` now documents this contract explicitly; see [Subsystem boot contract](subsystem_boot_contract.md).

---

## How it works internally

### 1. Declaration → schema

\`VectorModelMeta\` resolves every attribute to exactly one **slot** at class creation: key, vector, text, payload, or score. Two interchangeable declaration styles compile to the same \`VectorSchema\`.

\`\`\`python
from datetime import datetime
from aquilia.vectordb import (
    VectorModel, Field, KeyField, VectorField, TextField, ScoreField,
)

class Document(VectorModel):
    key:        str          = KeyField(prefix="doc_")
    body:       str          = TextField(embed=True, min_length=1, max_length=8192)
    vector:     list[float]  = VectorField(dimension=384)
    source:     str          = Field(default="web", indexed=True, max_length=256)
    views:      int          = Field(default=0, ge=0)
    score:      float | None = ScoreField()
    created_at: datetime     = Field(default_factory=datetime.utcnow)

    class Meta:
        collection = "documents"
        store = "default"
        dimension = 384
\`\`\`

Class access returns the **field** (so \`Document.views >= 10\` builds a filter); instance access returns the **value**. Declaring a field in both the assignment and an \`Annotated[...]\` position for one attribute raises \`VectorSchemaFault\` — there is no principled winner, so the contradiction is rejected rather than resolved by precedence.

### 2. Discovery → registration

\`RuntimeRegistry\` gained a scan and an import pass that mirror the SQL model path:

- \`_discover_vector_models(ctx)\` scans \`modules/<app>/vector_models.py\` and \`modules/<app>/vector_models/*.py\`, appending paths to \`AppContext.vector_models\`.
- \`_register_vector_models()\` imports them so \`VectorModelMeta\` self-registers into \`VectorRegistry\`.

A **separate directory** rather than a marker inside \`models/\` is deliberate: importing a vector model imports \`aquilia.vectordb\`, and scanning \`models/\` for them would drag the optional dependency into every app that has SQL models. Keeping the paths disjoint keeps that cost opt-in.

Nothing is imported at all when no module declares a vector model, so an app without them never touches \`aquilia.vectordb\`.

### 3. Config → stores

\`VectorDatabaseIntegration.to_dict()\` normalizes \`{alias: config}\` into a list of entries each carrying its own \`alias\`, matching \`StorageIntegration.to_dict()\`. Store-level settings win over integration-level defaults: the outer values exist so the common case (one path, one GPU policy) is declared once, not so they override a store that was explicit.

\`VectorRegistry.configure(stores, default=..., pool_threads=...)\` installs that configuration. Engines open lazily, one per alias, on first \`VectorRegistry.engine(alias)\`.

### 4. Binding validation

elips holds \`dimension\` and \`metric\` **database-global**: they are set once at \`connect()\` and every vault inherits them. \`VectorRegistry._validate_binding()\` therefore checks each model against its store's configuration and fails loudly on a mismatch, naming both sides. Coercing the model to the store's dimension would write vectors that search returns in the wrong order, with nothing in the logs.

---

## Usage guide

### Configuration — \`workspace.py\`

\`\`\`python
from aquilia.workspace import Workspace
from aquilia.vectordb import GpuOptions, EmbedderOptions

workspace = (
    Workspace("myapp")
    .vectordb(
        path="./.aquilia/vectors",
        stores={
            "default": {
                "dimension": 384,
                "metric": "cosine",
                "index": "hnsw",
                "embedder": EmbedderOptions(provider="local", model="minilm-l6-v2"),
            },
            "images": {"dimension": 512, "metric": "l2"},
        },
        gpu=GpuOptions(policy="prefer_gpu", fallback="warn"),
    )
)
\`\`\`

\`Workspace.vectordb()\` is shorthand for \`integrate(VectorDatabaseIntegration(...))\`. Both record into \`Workspace._integrations["vectordb"]\` and surface at \`config["vectordb"]\` plus \`config["integrations"]["vectordb"]\`.

### Configuration — \`aquilia.config.py\`

\`\`\`python
from aquilia.pyconfig import AquilaConfig

class BaseEnv(AquilaConfig):
    class vectordb(AquilaConfig.VectorDB):
        enabled   = True
        path      = "./.aquilia/vectors"
        dimension = 384
        embedder  = "sentence-transformers/all-MiniLM-L6-v2"

class ProdEnv(BaseEnv):
    env = "prod"

    class vectordb(BaseEnv.vectordb):
        embedder     = "openai/text-embedding-3-small"
        dimension    = 1536
        auto_create  = False     # a missing store is a boot failure
        quantization = "sq8"     # 4x smaller, approximate distances
\`\`\`

\`AquilaConfig.VectorDB\` defaults to \`enabled = False\`. \`ConfigLoader.get_vectordb_config()\` returns the same defaults, so an absent block never makes the subsystem try to load the extension.

### Manifest declaration

\`\`\`python
# modules/blog/manifest.py
from aquilia.manifest import AppManifest

manifest = AppManifest(
    name="blog",
    version="1.0.0",
    models=["modules.blog.models:Post"],
    vector_models=["modules.blog.vector_models:Document"],
)
\`\`\`

\`vector_models\` is kept separate from \`models\` because the two are bound to different backends — a \`VectorModel\` has no table and never appears in a SQL migration. \`auto_discovery\` now includes \`"vector_models"\` by default.

### Reading and writing

\`\`\`python
doc = Document(vector=[...], body="release notes", source="docs", views=0)
await doc.save()            # key assigned if absent
await doc.refresh()
await doc.delete_instance()

hits = await Document.vectors.query().filter(source="docs").search(vector=q, limit=10)
for hit in hits:
    print(hit.score, hit.body, hit.approximate)
\`\`\`

### Hybrid retrieval with the SQL ORM

\`\`\`python
from aquilia.vectordb import as_models, mirror, resolve

@mirror(into=Document,
        text=lambda p: f"{p.title}\\n\\n{p.body}",
        meta={"post_id": lambda p: p.pk, "kind": "post"},
        when=lambda p: p.published)
class Post(Model):
    ...

hits  = await Document.vectors.query().filter(kind="post").search(text="alpha", limit=20)
posts = await as_models(hits, Post, via="post_id",
                        queryset=Post.query().select_related("author"))
\`\`\`

\`as_models\` issues **one** SQL round trip regardless of hit count: primary keys are collected from the hits and fetched with a single \`pk__in\`, chunked at 999 to respect the SQLite parameter ceiling, then re-sorted in Python by hit index because SQL \`IN\` does not preserve argument order.

---

## CLI

See [\`vectordb_cli.md\`](vectordb_cli.md) for full flag-by-flag coverage.

\`\`\`bash
aq vectordb status        # configured stores + elips availability (opens nothing)
aq vectordb gpu           # capability probe and resolved policy per store
aq vectordb models        # registered models and their slot routing
aq vectordb inspect       # open each store, report live health
aq vectordb stats         # per-collection counts, tombstones, codec, WAL depth
aq vectordb compact       # reclaim space from deleted records
aq vectordb vacuum        # release free pages
aq vectordb compress      # train a quantization codebook and compress
aq vectordb reindex Post  # rebuild a mirrored collection from SQL
aq vectordb reembed       # re-embed a collection under a new model
\`\`\`

---

## Performance implications

| Concern | Behaviour |
|---|---|
| **Import cost on installs without vectordb** | Zero. \`_LAZY_ATTRS\` defers \`engine\`, \`gpu\`, \`interop\`, \`embedders\`, \`eql\`, \`chunking\` and \`subsystem\` to first attribute access. Discovery imports nothing when no module declares a vector model. |
| **Blocking C++ calls** | Offloaded to a dedicated \`ThreadPoolExecutor\` named \`aquilia-vdb\` rather than the default executor, so a long \`compact()\` cannot starve unrelated \`run_in_executor\` callers, and a stalled vector op is identifiable in a stack dump. |
| **\`pool_threads\`** | Defaults to 4. **Not a write-throughput knob** — elips is single-writer per directory and serializes writes inside C++ however many threads submit them. Reads parallelize; that is what the 4 is for. |
| **Store open latency** | Opening rebuilds the index, hence the 60s subsystem timeout. A large \`hnsw\` store dominates boot time; \`flat\` opens near-instantly. |
| **Quantization** | \`sq8\` ≈ 4× smaller, \`pq\`/\`opq\` ≈ 8–32× smaller, both with approximate distances. \`Hit.approximate\` and \`Hit.codec\` surface that to callers applying a score threshold. |
| **\`as_models\`** | O(1) SQL queries per call, not O(hits). |
| **Scan mode** | \`all()\`/\`count()\` filter on metadata only and return insertion order. Key-attribute and \`lineage__*\` lookups are evaluated in Python against hydrated records — correct, but they scan rather than narrow the index. |

---

## Edge cases

**Single-writer lock.** elips takes an exclusive lock per database directory. Running more than one worker against the same store path makes every worker after the first fail to acquire it — a startup fault (\`VectorLockFault\`), not a degradation. This is the practical reason \`_required\` is raised when stores are declared: a degraded boot would hide it.

**\`workers > 1\`.** Either give each worker its own store path, or set \`read_only=True\` on the shared store so workers search without the writer lock. Writes then raise.

**\`auto_create=False\`.** A missing store directory fails the boot instead of serving an empty index. Recommended in production.

**Dimension/metric change on an existing store.** Not a migration. elips persists that identity on disk and refuses a reopen that disagrees. \`aq vectordb reembed\` refuses a dimension change in place and names the store to reconfigure.

**Embedder change.** Vectors from two models occupy incompatible spaces, so mixing them does not degrade results — it makes distances meaningless while still returning a confident-looking ranked list. \`VectorEmbedderMismatchFault\` fires at bind time. Re-embedding is an explicit operator action, never implicit.

**Python 3.10.** \`elips 1.1.0\` publishes no cp310 wheels. The extra carries \`python_version >= '3.11'\`, so on 3.10 it installs nothing and \`aquilia.vectordb\` degrades exactly as on any install without the driver — \`VectorNotInstalledFault\` at first use. Without that marker, \`aquilia[full]\` would become unresolvable on 3.10 rather than simply omitting vector support.

**\`__isnull\` lookups.** Rejected with \`VectorLookupFault\`. elips has no null concept — an absent metadata key simply fails to match any predicate — so neither \`True\` nor \`False\` has a faithful translation. Model absence with a sentinel or a boolean flag.

**Range filters over \`Decimal\`/\`UUID\`/\`bytes\`.** Rejected. These encode to strings where lexicographic order is not value order (\`"9" > "10"\`). Equality and \`__in\` still work.

**Nested \`dict\`/\`list\` payloads.** Rejected at class creation, not on first write — a store half-populated with unreadable values is much harder to recover from than an import error.

**Bulk writes bypass \`@mirror\`.** \`bulk_create\`/\`bulk_update\` fire no signals. \`aq vectordb reindex <Model>\` is the sanctioned repair.

**GPU per-query fallback.** elips falls back to CPU per query even under \`require_gpu\`, so "same API, possibly slower" is the default contract. \`fallback="require"\` inspects the query plan and raises \`VectorGpuFault\` when it ran on CPU; that check is opt-in because it costs an \`explain\` per query.

---

## Wiring the store lifecycle

\`AquiliaServer\` boots storage, cache, tasks, mail and effects through its own ordered \`_setup_*\` methods; it does **not** orchestrate \`BootContext\` subsystems. \`VectorDBSubsystem\` is therefore driven by the host — an embedder, an alternative runner, a test, or a module lifecycle hook:

\`\`\`python
# modules/search/hooks.py
from aquilia.subsystems import BootContext, VectorDBSubsystem

_subsystem = VectorDBSubsystem()

async def on_boot(config, container=None):
    ctx = BootContext(config=config, manifests=[])
    if container is not None:
        ctx.shared_state["container"] = container
    status = await _subsystem.initialize(ctx)
    if status.status.value == "unhealthy" and _subsystem.required:
        raise RuntimeError(f"vectordb failed to boot: {status.message}")

async def on_close(config, container=None):
    await _subsystem.shutdown()
\`\`\`

\`\`\`python
# modules/search/manifest.py
from aquilia.manifest import AppManifest, LifecycleConfig

manifest = AppManifest(
    name="search",
    version="1.0.0",
    vector_models=["modules.search.vector_models"],
    lifecycle=LifecycleConfig(
        on_startup="modules.search.hooks:on_boot",
        on_shutdown="modules.search.hooks:on_close",
    ),
)
\`\`\`

The \`aq vectordb\` commands configure and shut down \`VectorRegistry\` themselves, so they work without any of this.

---

## Backward compatibility

Adoption is **purely additive**. There is no legacy vector API to migrate from, and nothing existing changes:

- An install without \`elips\` behaves exactly as before this release.
- A workspace with no \`vectordb\` block boots with \`VectorDBSubsystem._required = False\` and never imports the driver.
- \`AppManifest.vector_models\` defaults to \`[]\`; \`AppContext.vector_models\` defaults to \`[]\`.
- \`VectorModel\` and \`Model\` coexist in one module and are disjoint under \`isinstance\`.
- The original \`Annotated\` marker syntax (\`Key()\`, \`Dimension(n)\`, \`Text()\`, \`Payload()\`, \`Score()\`, \`MinLength\`, \`MaxValue\`, \`Range\`, …) is fully supported and unchanged; the unified field objects are additive.

---

## Limitations

- **Embedded only.** No networked or distributed vector storage — that is elips's design, not a gap to fill.
- **No vectors in SQL tables.** \`as_models\` hydrates from SQL; it does not mirror vectors into it.
- **No GPU kernels.** Aquilia owns no kernels; elips owns the backend abstraction and the fallback chain.
- **No automatic re-embedding.** \`aq vectordb reembed\` stays an operator action.
- **No ordering in scan mode.** Without a query vector there is nothing to rank by, so \`order_by\` is not offered rather than silently ignored.
- **\`offset()\` rejected on \`search()\`.** A similarity index returns top-k, so paging by offset would re-rank between pages.

---

## Related documentation

- [\`docs/vectordb.md\`](../../docs/vectordb.md) — complete reference (fields, codecs, queries, EQL, embedders, chunking, GPU, faults)
- [\`vectordb_cli.md\`](vectordb_cli.md) — \`aq vectordb\` command reference
- [\`subsystem_boot_contract.md\`](subsystem_boot_contract.md) — \`BootContext\`, DI resolution, timeout enforcement
- [\`checks_engine.md\`](checks_engine.md) — the \`vectordb.driver\` health check
- [\`migration.md\`](migration.md) — upgrade steps and compatibility matrix
- [\`README.md\`](README.md) — release overview
`,
    "vectordb_cli.md": `# \`aq vectordb\` Command Reference — v1.4.0b3

A new CLI group registered in \`aquilia/cli/__main__.py\` and categorised under **Database** in \`aq --help\` (\`aquilia.cli.core.registry._CATEGORIES["vectordb"] = "Database"\`).

\`\`\`bash
aq vectordb --help
\`\`\`

Nothing in this group is a breaking change — the whole group is new.

---

## Lock discipline

elips is **single-writer per database directory**. The commands split cleanly on whether they take that lock:

| Takes no lock | Takes the writer lock |
|---|---|
| \`status\` | \`inspect\`, \`stats\`, \`compact\`, \`vacuum\`, \`compress\`, \`reindex\`, \`reembed\` |
| \`gpu\` (probe only; reads config for policy display) | |
| \`models\` (imports model modules; opens nothing) | |

The lock-taking commands **will fail while a server holds the same store**. That is the lock working, not a bug. Run them during a maintenance window, or point them at a store the server does not own.

---

## \`aq vectordb status\`

Show configured stores and \`elips\` availability. Reads configuration only.

\`\`\`
--json    Output as JSON
\`\`\`

\`\`\`bash
$ aq vectordb status
Vector store status
✔ elips available (version 1.1.0)

 * default
     path       ./.aquilia/vectors/default
     dimension  384   metric cosine   index hnsw
     gpu        prefer_gpu
     embedder   local
   images
     path       ./.aquilia/vectors/images
     dimension  512   metric l2   index flat
     gpu        cpu_only
     embedder   none

* = default store
\`\`\`

Without the driver:

\`\`\`bash
$ aq vectordb status
Vector store status
! elips not installed — vector stores cannot open
  No module named 'elips'
  Install with: pip install 'aquilia[vectordb]'
\`\`\`

Without configuration:

\`\`\`bash
$ aq vectordb status
Vector store status
✔ elips available (version 1.1.0)

i No vector stores configured.
  Add Workspace.vectordb(stores={...}) to your workspace.py
\`\`\`

JSON payload shape:

\`\`\`json
{
  "elips": { "available": true, "version": "1.1.0" },
  "enabled": true,
  "default": "default",
  "stores": [ { "alias": "default", "path": "...", "dimension": 384, "...": "..." } ]
}
\`\`\`

---

## \`aq vectordb gpu\`

Probe GPU capability and show the resolved policy per store.

\`\`\`
-s, --store TEXT   Resolve policy for one store alias
    --json         Output as JSON
\`\`\`

\`built\` (the elips wheel carries GPU bindings — compile-time) and \`available\` (a device is actually present — runtime) are reported **separately**. A GPU-enabled build on a machine with no device is a normal, supported state; collapsing the two into one boolean makes that case impossible to diagnose.

\`\`\`bash
$ aq vectordb gpu
GPU capability
  built      True
  available  True

  [0] NVIDIA RTX A4000  (cuda)
       memory 15.73 GiB   fp16 True   unified False

Configured policy
  default: policy=prefer_gpu fallback=warn — ok
  images: policy=cpu_only fallback=warn — ok
\`\`\`

\`require_gpu\` with no device is called out explicitly, because it is a boot failure rather than a slow path:

\`\`\`
  default: policy=require_gpu fallback=error — BOOT WILL FAIL (require_gpu, no device)
\`\`\`

Exits \`1\` when \`elips\` is not installed — there is nothing to probe.

---

## \`aq vectordb models\`

List registered vector models and their slot routing.

\`\`\`
--json    Output as JSON
\`\`\`

Slot routing is resolved at class creation and is not visible in the source, so this is the fastest way to confirm a \`KeyField\` / \`TextField\` / \`VectorField\` (or a legacy \`Key()\` / \`Text()\` / \`Dimension()\` marker) landed where the author intended.

\`\`\`bash
$ aq vectordb models
Vector models
  modules.blog.vector_models.Document
     collection documents   store default   dim 384
     key=key  text=body  vector=vector
     payloads   created_at, source, views
     links      author_id
\`\`\`

\`\`\`bash
$ aq vectordb models
Vector models
i No vector models registered.
  Declare them in modules/<app>/vector_models.py or a manifest's vector_models list.
\`\`\`

---

## \`aq vectordb inspect [STORE]\`

Open each store and report live health.

\`\`\`
STORE     Optional store alias; all stores when omitted
--json    Output as JSON
\`\`\`

\`\`\`bash
$ aq vectordb inspect default
Vector store inspection
✔ default: healthy
     path            ./.aquilia/vectors/default
     dimension       384
     metric          cosine
     index           hnsw
     collections     ['documents']
     pending_writes  0
     gpu             built=True available=True
\`\`\`

Every store is closed again on the way out, including on failure — the \`finally\` calls \`VectorRegistry.shutdown()\`, so the lock is released even when one store errors.

---

## \`aq vectordb stats [STORE]\`

Per-collection telemetry: record counts, tombstones, codec, WAL depth.

\`\`\`
STORE     Optional store alias
--json    Output as JSON
\`\`\`

\`\`\`bash
$ aq vectordb stats
Vector store statistics
✔ default
     pending_writes  0
     documents
        live=12403  tombstone_ratio=0.04  dim=384  metric=cosine  codec=none
\`\`\`

\`tombstone_ratio\` is the signal for whether \`compact\` is worth running.

---

## \`aq vectordb compact [STORE]\`

Reclaim space held by deleted records.

\`\`\`
STORE     Optional store alias
\`\`\`

\`\`\`bash
$ aq vectordb compact default
compact default ...
✔ Compacted 1 store(s).
\`\`\`

Refuses a \`read_only\` store and exits \`1\`:

\`\`\`
✘ default: store is read_only; refusing to compact
\`\`\`

---

## \`aq vectordb vacuum [STORE]\`

Release free pages back to the filesystem. Same shape and same \`read_only\` refusal as \`compact\`.

\`\`\`bash
$ aq vectordb vacuum
vacuum default ...
✔ Vacuumed 1 store(s).
\`\`\`

---

## \`aq vectordb compress [STORE]\`

Train a quantization codebook and compress a store in place.

\`\`\`
STORE                  Optional store alias
--codec [pq|opq|sq8]   Quantization codec to train and apply  [default: pq]
--sample-size INT      Vectors sampled to train the codebook  [default: 10000]
--pq-dim INT           Sub-quantizer count (pq/opq)
--pq-bits INT          Bits per sub-quantizer code (4-8)
--yes                  Skip the confirmation prompt
\`\`\`

Trades recall for memory: \`sq8\` stores one byte per dimension (≈4× smaller); \`pq\`/\`opq\` store a short code per vector (≈8–32× smaller). Distances become approximate afterwards, which is why every hit carries \`approximate=True\` and its codec.

**Not reversible in place.** Compression frees the full-precision vectors once the codebook is trained, so restoring them means re-ingesting or re-embedding. Hence the confirmation:

\`\`\`bash
$ aq vectordb compress default --codec sq8
Compress with sq8? Full-precision vectors are discarded and distances become approximate. [y/N]: y
compressing default/documents with sq8 ...
✔ Compressed 1 store(s) with sq8.
\`\`\`

Scriptable with \`--yes\`. Refuses a \`read_only\` store.

---

## \`aq vectordb reindex MODEL\`

Rebuild a mirrored collection from its SQL table.

\`\`\`
MODEL                    SQL model class name, e.g. Post  (required)
-b, --batch-size INT     Rows per write batch  [default: 500]
\`\`\`

This is the sanctioned repair for the bulk-write blind spot: \`bulk_create\` and \`bulk_update\` fire no signals, so rows written that way never reach \`@mirror\` and the vector collection silently drifts.

\`\`\`bash
$ aq vectordb reindex Post
✔ Reindexed 8412 record(s) from Post.
\`\`\`

Exits \`1\` with a named reason when the model is unknown or carries no \`@mirror\`:

\`\`\`
✘ Post has no @mirror registered — nothing to reindex.
\`\`\`

---

## \`aq vectordb reembed\`

Re-embed a collection under a different embedding model.

\`\`\`
-m, --model TEXT         Vector model class name, e.g. Document  (required)
    --to-embedder TEXT   Target embedder URI  (required)
-b, --batch-size INT     Records per batch  [default: 200]
    --dry-run            Report what would change, write nothing
\`\`\`

Reads every record's stored text, embeds it with the new model, and writes the vector back **under the same key** — so keys, payloads, and any SQL links survive the migration.

\`\`\`bash
$ aq vectordb reembed --model Document --to-embedder openai/text-embedding-3-large --dry-run
i Dry run: 12403 record(s) would be re-embedded with openai/text-embedding-3-large.

$ aq vectordb reembed --model Document --to-embedder openai/text-embedding-3-large
✔ Re-embedded 12403 record(s) with openai/text-embedding-3-large.
! 17 record(s) had no stored text and were left unchanged.
\`\`\`

Two failure modes it guards against:

1. **A dimension change** (384 → 1536) cannot be applied in place, because elips holds dimension database-global. The command refuses rather than writing vectors the store cannot index, and names the store to reconfigure:

   \`\`\`
   ✘ openai/text-embedding-3-large produces 3072-dimension vectors but store 'default' is configured for 384.
     elips holds dimension database-global, so this cannot be changed in place.
   \`\`\`

2. **A record with no stored text** cannot be re-embedded from anything. Those are counted and reported rather than silently left on the old model, which would leave the collection split across two vector spaces.

\`--to-embedder\` is **required**: re-embedding under whatever happens to be configured is exactly how a collection ends up with two incompatible vector spaces. A model with no text field is rejected outright.

---

## Common workflows

### Bring up vector search on an existing app

\`\`\`bash
pip install 'aquilia[vectordb]'
# add .vectordb(stores={...}) to workspace.py
# add modules/<app>/vector_models.py

aq vectordb status      # driver installed? stores read correctly?
aq vectordb models      # slot routing as intended?
aq doctor               # picks up the vectordb.driver check
aq serve
\`\`\`

### Diagnose an empty search result set

\`\`\`bash
aq vectordb models              # is the model registered at all?
aq vectordb stats               # does the collection hold records?
aq vectordb inspect             # is the store healthy, dimension as expected?
\`\`\`

### Repair drift after a bulk import

\`\`\`bash
aq vectordb reindex Post
aq vectordb stats
\`\`\`

### Maintenance window

\`\`\`bash
aq vectordb stats               # check tombstone_ratio
aq vectordb compact
aq vectordb vacuum
aq vectordb compress --codec sq8 --yes    # only if memory is the constraint
\`\`\`

### Migrate embedding models

\`\`\`bash
# 1. Reconfigure the store's dimension in workspace.py if the new model differs.
# 2. Dry run first.
aq vectordb reembed --model Document --to-embedder openai/text-embedding-3-small --dry-run
# 3. Apply.
aq vectordb reembed --model Document --to-embedder openai/text-embedding-3-small
\`\`\`

---

## Anti-patterns

| Don't | Do |
|---|---|
| Run \`aq vectordb inspect\` against a live server's store | Use \`aq vectordb status\`, which takes no lock |
| Run \`workers > 1\` against one store path | Separate paths per worker, or \`read_only=True\` for search-only workers |
| Change \`dimension\` in config and expect the store to follow | Reconfigure the store, then \`aq vectordb reembed\` |
| \`aq vectordb compress\` on a store you cannot re-ingest | Verify a backup or a re-ingest path exists first — compression is one-way |
| Parse the human output in CI | Every command takes \`--json\` |

---

## Related documentation

- [\`vectordb.md\`](vectordb.md) — subsystem overview, architecture, configuration
- [\`docs/vectordb.md\`](../../docs/vectordb.md) — complete API reference
- [\`cli_modernization.md\`](cli_modernization.md) — \`ExitCode\` contract these commands exit under
- [\`checks_engine.md\`](checks_engine.md) — the \`vectordb.driver\` health check
`,
    "cli_modernization.md": `# CLI Architecture Modernization — v1.4.0b3

## Overview & Motivation

In previous releases, the Aquilia CLI (\`aq\`) contained significant structural debt:
1. **Inconsistent Exit Codes**: Commands printed warning/error banners but returned exit code \`0\` unconditionally. Continuous integration pipelines were unable to rely on \`aq validate\` or \`aq doctor\` to fail broken builds.
2. **Scattered Error Exit Calls**: ~150 scattered \`sys.exit(1)\` invocations were hardcoded into command bodies, making CLI logic impossible to unit test without process termination.
3. **Competing Workspace Guards**: Three different functions (\`_ensure_workspace_root\`, \`_require_workspace\`, and \`ConfigMissingFault\`) checked for \`workspace.py\` using different rules and error messages.
4. **Brittle Regex Workspace Parsing**: \`workspace.py\` and \`manifest.py\` were parsed using regular expressions (e.g. \`re.findall(r'Module\\("([^"]+)"')\`), missing commented-out modules, ignoring \`.starter("name")\` starter routes, and ignoring module-level \`route_prefix\` settings.
5. **Help Category Drift**: \`AquiliaGroup._CATEGORIES\` relied on a manually maintained literal list of command strings. Commands like \`deploy-gen\` vs \`deploy\` caused 7 core commands to silently fall into the "Other" category in \`aq --help\`.

v1.4.0b3 replaces this legacy implementation with a modular architecture under \`aquilia.cli.core\`.

---

## The \`aquilia.cli.core\` Package

\`\`\`
aquilia/cli/core/
├── __init__.py        # Re-exports core primitives
├── exits.py           # ExitCode enum, SEVERITY_ORDER, exit_code_for()
├── faults.py          # CLI_DOMAIN and CliFault hierarchy
├── context.py         # AqContext ambient state thread
├── workspace.py       # LoadedWorkspace, load_workspace(), Python-first loader
└── registry.py        # CommandSpec, CATEGORY_ORDER, single source of help grouping
\`\`\`

---

## 1. Single Source of Truth for Exit Codes (\`exits.py\`)

\`ExitCode\` establishes a strict contract for process return values:

\`\`\`python
from enum import IntEnum

class ExitCode(IntEnum):
    OK = 0          # All checks passed / findings <= WARN
    FAILED = 1      # At least one ERROR or FATAL finding
    USAGE = 2       # Command line argument/invocation error
    CONFIG = 3      # Workspace or configuration file missing / load failure
    INTERNAL = 4    # Unhandled CLI exception (bug in CLI engine)
\`\`\`

### Severity Mapping

Check severities (\`INFO\`, \`WARN\`, \`ERROR\`, \`FATAL\`) map deterministically to process exit codes:

\`\`\`python
from aquilia.cli.core.exits import exit_code_for
from aquilia.faults.core import Severity

# Only ERROR and FATAL cause process failure (ExitCode.FAILED / 1)
exit_code_for([Severity.INFO, Severity.WARN])  # -> ExitCode.OK (0)
exit_code_for([Severity.WARN, Severity.ERROR]) # -> ExitCode.FAILED (1)
\`\`\`

---

## 2. Structured CLI Fault Hierarchy (\`faults.py\`)

Instead of invoking \`sys.exit(1)\` inside command handlers, commands raise typed subclasses of \`CliFault\`. The CLI entrypoint (\`cli\`) catches faults at the process boundary and converts them to exit codes.

\`\`\`python
from aquilia.cli.core.faults import CliFault, WorkspaceNotFoundFault
from aquilia.faults.core import FaultDomain, Severity

CLI_DOMAIN = FaultDomain.custom("CLI", "Aquilia command-line interface faults")

class CliFault(Fault):
    code = "CLI_ERROR"
    message = "CLI operation failed"
    domain = CLI_DOMAIN
    severity = Severity.ERROR

class WorkspaceNotFoundFault(CliFault):
    code = "CLI_WORKSPACE_NOT_FOUND"
    message = "No Aquilia workspace found in the current directory"
    severity = Severity.ERROR
\`\`\`

### Benefit for Testing

Commands can now be tested as normal Python functions without mocking \`sys.exit()\`:

\`\`\`python
# Unit test example
import pytest
from aquilia.cli.core.faults import WorkspaceNotFoundFault

def test_require_workspace_raises_fault(tmp_path):
    ctx = AqContext(cwd=tmp_path)
    with pytest.raises(WorkspaceNotFoundFault):
        ctx.require_workspace()
\`\`\`

---

## 3. Ambient CLI State (\`AqContext\`)

\`AqContext\` replaces ad-hoc \`ctx.obj\` dictionary access. The workspace is resolved lazily upon first access:

\`\`\`python
from dataclasses import dataclass, field
from pathlib import Path
from aquilia.cli.core.workspace import LoadedWorkspace, load_workspace

@dataclass
class AqContext:
    cwd: Path = field(default_factory=Path.cwd)
    verbose: bool = False
    quiet: bool = False
    json_output: bool = False
    no_color: bool = False
    strict: bool = False
    module_filter: str | None = None
    mode: str = field(default_factory=lambda: os.environ.get("AQUILIA_ENV", "dev"))
    _workspace: LoadedWorkspace | None = field(default=None, repr=False)

    @property
    def workspace(self) -> LoadedWorkspace:
        if self._workspace is None:
            self._workspace = load_workspace(self.cwd)
        return self._workspace

    def require_workspace(self) -> LoadedWorkspace:
        ws = self.workspace
        if not ws.exists:
            raise WorkspaceNotFoundFault(path=str(self.cwd))
        return ws
\`\`\`

---

## 4. Python-First Workspace Loader (\`workspace.py\`)

\`workspace.py\` is a Python module, so \`load_workspace()\` imports it cleanly via \`importlib\` instead of scraping source text with regular expressions.

\`\`\`python
from aquilia.cli.core.workspace import load_workspace

ws = load_workspace(Path.cwd())
print(f"Root: {ws.root}")
print(f"Modules: {ws.module_names}")
print(f"Starter Controller: {ws.starter_module}")

# Manifest resolution with caching
manifest = ws.manifest("users")
print(f"Controllers: {manifest.controllers}")
\`\`\`

### Regex Fallback Mechanism

If \`workspace.py\` contains syntax or import errors, \`load_workspace()\` falls back to a non-evaluating regex scan and sets \`ws.used_fallback = True\`. This allows \`aq doctor\` to inspect and report on a broken workspace rather than failing immediately.

---

## 5. Category-Driven Command Registry (\`registry.py\`)

Command categories are maintained in a single registry mapping command names to display categories in \`aq --help\`:

\`\`\`python
CATEGORY_ORDER = (
    "Scaffold", "Develop", "Production", "Database",
    "Admin", "Inspect", "Subsystems", "Deploy",
    "Migration", "Other"
)

# Single source of truth for aq --help
_CATEGORIES = {
    "init": "Scaffold", "add": "Scaffold", "generate": "Scaffold",
    "run": "Develop", "dev": "Develop", "validate": "Develop",
    "test": "Develop", "discover": "Develop", "doctor": "Develop",
    "serve": "Production", "db": "Database", "admin": "Admin",
    "inspect": "Inspect", "manifest": "Inspect", "ws": "Subsystems",
    "cache": "Subsystems", "mail": "Subsystems", "deploy": "Deploy",
    "migrate": "Migration",
}
\`\`\`

Help integrity tests enforce that every registered Click command maps to a category, preventing unassigned commands from drifting into "Other".
`,
    "checks_engine.md": `# Unified Health Checks Engine — v1.4.0b3

## Overview & Architecture

Aquilia v1.4.0b3 introduces a unified health checks engine (\`aquilia.cli.checks\`). It replaces the legacy, separate implementations in \`doctor.py\` (597 lines) and \`validate.py\` (372 lines) with a single registry of extensible, tagged check functions.

\`\`\`
aquilia/cli/checks/
├── __init__.py        # Re-exports check protocol & runner
├── base.py            # Finding, Check, CheckResult, @register_check decorator
├── report.py          # Human and JSON report formatters
├── workspace.py       # Core workspace health checks (modules, manifests, routes, DI, DB)
└── subsystems.py      # Subsystem-specific probes (tasks, templates, storage, etc.)
\`\`\`

---

## 1. The Check Protocol (\`base.py\`)

Checks never print directly to \`stdout\` or \`stderr\`. Instead, a check receives an \`AqContext\` instance and yields structured \`Finding\` objects.

\`\`\`python
from aquilia.cli.checks.base import Finding, register_check
from aquilia.cli.core.context import AqContext
from aquilia.faults.core import Severity

@register_check(
    name="db.reachable",
    summary="Database configuration is valid and reachable",
    tags=["db", "deep"],
    subsystem="db",
)
def check_db_reachable(ctx: AqContext):
    ws = ctx.workspace
    db_cfg = ws.workspace_obj.database
    if db_cfg is None:
        yield Finding(
            code="AQ_DB_NOT_CONFIGURED",
            message="No database integration configured in workspace",
            severity=Severity.WARN,
            remedy="Add DatabaseIntegration to workspace.py if persistence is required",
        )
\`\`\`

### Finding Dataclass

\`\`\`python
@dataclass
class Finding:
    code: str                  # Stable identifier (e.g. "AQ_DB_MISSING")
    message: str               # Human-readable summary
    severity: Severity = Severity.ERROR # Severity level (INFO, WARN, ERROR, FATAL)
    remedy: str | None = None  # Actionable remediation guidance
    location: str | None = None# File path or module location
    detail: str | None = None  # Detailed error or stack trace (shown in -v mode)
\`\`\`

---

## 2. Core Workspace Checks (\`workspace.py\`)

| Check Name | Summary | Severity Range | Tags |
|---|---|---|---|
| \`env.python\` | Interpreter version >= 3.10 | \`FATAL\` | \`env\`, \`quick\` |
| \`workspace.present\` | \`workspace.py\` exists and imports cleanly | \`ERROR\`, \`WARN\` | \`workspace\`, \`quick\` |
| \`workspace.modules\` | Declared modules exist on disk | \`ERROR\`, \`WARN\` | \`workspace\`, \`modules\` |
| \`manifest.loadable\` | Every declared module has an importable \`manifest.py\` | \`ERROR\` | \`manifest\`, \`quick\` |
| \`manifest.references\` | Component references (\`module.path:Class\`) resolve | \`ERROR\` | \`manifest\`, \`deep\` |
| \`routes.parsable\` | Controller route metadata extracts cleanly | \`ERROR\` | \`routes\`, \`deep\` |
| \`routes.conflicts\` | No overlapping HTTP method + path collisions | \`ERROR\` | \`routes\`, \`deep\` |
| \`di.providers\` | DI service providers resolve and import | \`ERROR\`, \`INFO\` | \`di\`, \`deep\` |
| \`db.reachable\` | Database backend configured and reachable | \`ERROR\`, \`WARN\` | \`db\`, \`deep\` |

---

## 3. Config-Driven Subsystem Checks (\`subsystems.py\`)

Subsystem checks inspect the integrations declared on \`workspace.py\` and stay silent when a subsystem is unused:

- **\`tasks.registry\`**: Validates background task references (\`module:task_name\`) and confirms functions carry the \`@task\` decorator.
- **\`templates.dirs\`**: Verifies that configured Jinja template search directories exist on disk.
- **\`vectordb.driver\`**: Confirms \`elips\` is importable when the workspace declares vector stores.
- **\`subsystems.available\`**: Confirms that packages for configured integrations (\`storage\`, \`cache\`, \`mail\`, \`i18n\`, \`otel\`, \`sse\`, \`versioning\`, \`http\`, \`auth\`, \`sockets\`, \`contracts\`, \`mlops\`, \`vectordb\`, \`admin\`) are installed.

### The \`vectordb.driver\` check

\`elips\` is an optional extra, so a workspace can declare vector stores on an install that cannot open them. Without a check, the first symptom is a \`VectorNotInstalledFault\` at request time — long after deploy.

\`\`\`python
@register_check(
    name="vectordb.driver",
    summary="elips driver is installed when vector stores are declared",
    tags=["vectordb", "quick"],
    subsystem="vectordb",
)
def check_vectordb_driver(ctx: AqContext):
    ...
    yield Finding(
        code="AQ_VECTORDB_DRIVER_MISSING",
        message="Vector stores are declared but the elips driver is not installed",
        severity=Severity.ERROR,
        remedy="pip install 'aquilia[vectordb]' (requires Python 3.11+)",
    )
\`\`\`

The check is \`quick\`-tagged: it imports nothing beyond an availability probe and never opens a store, so it does not contend with a running server for the writer lock. It stays silent when no vector stores are declared.

### Integration detection fix

\`_integration()\` previously resolved integrations by attribute lookup (\`getattr(workspace_obj, name)\`). \`Workspace\` exposes builder **methods** named \`storage\`, \`vectordb\`, \`i18n\`, \`tasks\` and \`templates\`, so \`getattr\` returned a truthy bound method and every workspace appeared to declare every one of those subsystems — producing findings for integrations that were never configured.

\`Workspace._integrations\` is now authoritative, since it holds exactly what \`integrate()\` and the builder methods recorded. Attribute lookup remains as a fallback for non-\`Workspace\` objects and skips callables:

\`\`\`python
declared = getattr(obj, "_integrations", None)
if isinstance(declared, dict):
    found = declared.get(name)
    if found is not None:
        return found

for attr in (name, f"{name}_integration", f"_{name}"):
    found = getattr(obj, attr, None)
    if found is not None and not callable(found):
        return found
return None
\`\`\`

---

## 4. Route Introspection Engine (\`aquilia.cli.introspect.routes\`)

Legacy CLI route inspection relied on checking non-existent attributes like \`__controller_routes__\`. v1.4.0b3 uses \`ControllerCompiler\` — the exact same compiler called by \`AquiliaServer\` at boot.

\`\`\`python
from aquilia.cli.introspect.routes import collect_routes, count_routes

# Collect all routes across workspace modules and starter controllers
routes = collect_routes(ws)
for controller in routes:
    print(f"Controller: {controller.controller} (Prefix: {controller.prefix})")
    for r in controller.routes:
        print(f"  {r.http_method:<6} {r.full_path:<30} -> {r.handler}")
\`\`\`

### Accurate Route Counting

\`count_routes()\` counts individual HTTP endpoints rather than controller classes. A controller exposing 5 endpoint methods now correctly reports \`5 routes\` instead of \`1\`.

---

## 5. Report Formatters (\`report.py\`)

### Human Output (\`render_human\`)

\`\`\`
  x  [AQ_DB_MISSING] Database file does not exist: /app/db.sqlite3
        at: /app/db.sqlite3
        fix: Run migrations to create the DB, or check the configured path
  !  [AQ_TASK_NOT_DECORATED] users: 'sync_user' is listed as a task but has no @task decorator
        at: modules/users/tasks.py
        fix: Decorate it with @task so the registry can schedule it

  12 checks run: 1 error, 1 warning
  Result: FAILED
\`\`\`

### JSON Output (\`render_json\`) for CI Pipelines

\`\`\`json
{
  "summary": {
    "checks_run": 12,
    "checks_skipped": 0,
    "checks_errored": 0,
    "findings": {
      "info": 0,
      "warn": 1,
      "error": 1,
      "fatal": 0
    },
    "total_findings": 2,
    "passed": false
  },
  "exit_code": 1,
  "checks": [
    {
      "name": "db.reachable",
      "summary": "Database configuration is valid and reachable",
      "subsystem": "db",
      "tags": ["db", "deep"],
      "skipped": false,
      "findings": [
        {
          "code": "AQ_DB_MISSING",
          "message": "Database file does not exist: /app/db.sqlite3",
          "severity": "error",
          "remedy": "Run migrations to create the DB, or check the configured path",
          "location": "/app/db.sqlite3",
          "detail": null
        }
      ]
    }
  ]
}
\`\`\`

---

## Related documentation

- [cli_modernization.md](cli_modernization.md) — \`AqContext\`, \`ExitCode\`, \`CliFault\`
- [vectordb.md](vectordb.md) — the subsystem behind \`vectordb.driver\`
- [vectordb_cli.md](vectordb_cli.md) — \`aq vectordb status\` for deeper vector diagnostics
- [bug_fixes.md](bug_fixes.md#11-workspace-integration-detection-reported-phantom-integrations) — the integration detection defect
`,
    "subsystem_boot_contract.md": `# Subsystem Boot Contract — v1.4.0b3

The \`aquilia.subsystems\` package gained a documented, enforced contract. Five defects found in the 2026-08-09 subsystem audit are fixed here, and the package's role relative to \`AquiliaServer\` is now stated explicitly instead of implied.

Regression coverage: \`tests/test_subsystem_boot_contract.py\`.

---

## Overview

| Change | Kind |
|---|---|
| \`BootContext.di_containers()\` + \`DI_CONTAINER_KEY\` | New API — single DI resolution path |
| \`_timeout\` actually enforced in \`BaseSubsystem.initialize()\` | Behavioural fix |
| \`BootContext\` population contract documented | Documentation |
| \`StorageSubsystem\` DI registration repaired | Bug fix |
| \`EffectSubsystem\` DI registration repaired | Bug fix |
| \`EffectSubsystem.health_check()\` constructs a valid \`HealthStatus\` | Bug fix |
| \`StorageSubsystem\` / \`VectorDBSubsystem\` register a **live** health check | Bug fix |
| \`required\` computed-after-\`initialize()\` contract documented | Documentation |
| \`aquilia.subsystems\` package role documented; no \`SubsystemOrchestrator\` | Documentation |

---

## Who drives subsystems

Previously the package docstring said "the server orchestrates subsystems in priority order". It does not. \`AquiliaServer\` boots storage, cache, tasks, mail and effects through its own ordered \`_setup_*\` methods, and that is the production path.

\`aquilia.subsystems\` is the entry point for hosts that drive subsystems **themselves** — embedders, alternative runners, and tests — where there is no \`AquiliaServer\` to own the sequence. Both paths share the same underlying registries (\`StorageRegistry\`, \`VectorRegistry\`, \`EffectRegistry\`), so behaviour does not diverge; only the orchestration does.

There is deliberately **no \`SubsystemOrchestrator\`**. Adding one would create a second production boot sequence to keep in sync with the server's. A host that wants ordered boot composes it directly:

\`\`\`python
from aquilia.health import SubsystemStatus
from aquilia.subsystems import BootContext, EffectSubsystem, StorageSubsystem

subsystems = sorted([StorageSubsystem(), EffectSubsystem()], key=lambda s: s.priority)
ctx = BootContext(config=cfg, manifests=[], registry=runtime_registry)

for sub in subsystems:
    status = await sub.initialize(ctx)
    ctx.health.register(sub.name, status)
    # \`required\` is only final after initialize() — see below.
    if status.status is SubsystemStatus.UNHEALTHY and sub.required:
        raise RuntimeError(f"required subsystem {sub.name} failed: {status.message}")

# ... shutdown in reverse priority order
for sub in reversed(subsystems):
    await sub.shutdown()
\`\`\`

---

## 1. \`BootContext.di_containers()\` — one DI resolution path

### Previous API

Each subsystem invented its own \`shared_state\` key and its own resolution rule.

\`\`\`python
# StorageSubsystem._register_di  — BEFORE
registry_obj = ctx.shared_state.get("_di_registry")
if registry_obj and hasattr(registry_obj, "register"):
    provider = ValueProvider(value=self._registry, token=StorageRegistry, scope="app")
    registry_obj.register(provider)
\`\`\`

\`\`\`python
# EffectSubsystem._register_with_di  — BEFORE
container = ctx.shared_state.get("container")
if container:
    self._registry.register_with_container(container)
\`\`\`

**Why it worked (and why it did not).** \`"_di_registry"\` is a key **nothing in the codebase ever sets**. \`StorageRegistry\` was therefore never registered into DI — the branch was permanently dead, silently. \`EffectSubsystem\` used a different key, \`"container"\`, so a host that populated one got exactly one of the two subsystems wired. Neither consulted \`BootContext.registry\`, so a context built with a \`RuntimeRegistry\` — the normal case — registered nothing at all.

### New API

\`\`\`python
DI_CONTAINER_KEY = "container"

@dataclass
class BootContext:
    def di_containers(self) -> list[Any]:
        """Return every DI container a subsystem should register itself into."""
        explicit = self.shared_state.get(DI_CONTAINER_KEY)
        if explicit is not None and hasattr(explicit, "register"):
            return [explicit]

        containers = getattr(self.registry, "di_containers", None)
        if isinstance(containers, dict):
            return [c for c in containers.values() if hasattr(c, "register")]
        if isinstance(containers, (list, tuple)):
            return [c for c in containers if hasattr(c, "register")]
        return []
\`\`\`

\`\`\`python
# StorageSubsystem._register_di  — AFTER
containers = ctx.di_containers()
if not containers:
    self._logger.debug("No DI container in boot context -- skipping StorageRegistry registration")
    return

for container in containers:
    container.register(ValueProvider(value=self._registry, token=StorageRegistry, scope="app"))
\`\`\`

### Why it is better

- **One key, one rule.** Subsystems must not invent their own \`shared_state\` key; they call \`di_containers()\`. A misspelled key can no longer silently disable registration.
- **Explicit container wins.** An embedder can target one container without constructing a \`RuntimeRegistry\`.
- **All containers, not one.** \`registry.di_containers\` holds one container per app. Returning all of them matches how \`AquiliaServer\` registers app-scoped values — into every container, not the first one. Registering into only one made the registry resolvable from some apps and not others.
- **Duck-typed, defensively.** Entries without a \`register\` attribute are filtered out, so a malformed registry degrades to "DI is not wired here" rather than raising mid-boot.

### Behavioural changes

| Context shape | Before | After |
|---|---|---|
| \`shared_state["container"]\` set | Effects wired; storage not | Both wired into that container |
| \`shared_state["_di_registry"]\` set | Nothing (key read only by storage, and never set by anything) | Ignored — not a well-known key |
| \`registry=RuntimeRegistry(...)\` with app containers | Nothing wired | Both wired into **every** app container |
| Neither | Silent no-op | Debug log, then skip |

### Migration

If you built a \`BootContext\` by hand and set \`"_di_registry"\`, rename it:

\`\`\`python
# BEFORE
ctx = BootContext(config=cfg, manifests=[])
ctx.shared_state["_di_registry"] = container   # never actually worked

# AFTER
from aquilia.subsystems import DI_CONTAINER_KEY
ctx = BootContext(config=cfg, manifests=[])
ctx.shared_state[DI_CONTAINER_KEY] = container

# or, when you already have a RuntimeRegistry:
ctx = BootContext(config=cfg, manifests=[], registry=runtime_registry)
\`\`\`

No application code is affected: \`AquiliaServer\` does not use this path, and the key it replaces never worked.

---

## 2. \`_timeout\` is now enforced

### Previous behaviour

\`BaseSubsystem\` declared \`_timeout: float = 30.0\` and documented "timeout-protected initialization". Nothing read the value.

\`\`\`python
# BEFORE
async def initialize(self, ctx: BootContext) -> HealthStatus:
    start = time.monotonic()
    try:
        await self._do_initialize(ctx)      # unbounded
        ...
\`\`\`

A subsystem blocking on an unreachable dependency — an S3 endpoint behind a dropped route, a vector store whose lock holder never exits — hung the boot forever, with no log line and no health status.

### New behaviour

\`\`\`python
# AFTER
if self._timeout and self._timeout > 0:
    await asyncio.wait_for(self._do_initialize(ctx), timeout=self._timeout)
else:
    await self._do_initialize(ctx)
\`\`\`

\`\`\`python
except asyncio.TimeoutError:
    elapsed = (time.monotonic() - start) * 1000
    message = f"Initialization timed out after {self._timeout:g}s"
    self._logger.error("%s %s", self._name, message)
    return HealthStatus(
        name=self._name,
        status=SubsystemStatus.UNHEALTHY,
        latency_ms=elapsed,
        message=message,
    )
\`\`\`

A timeout degrades to \`UNHEALTHY\` with a named cause, exactly like any other initialization failure. A host that treats \`UNHEALTHY + required\` as fatal stops the boot; one that does not carries on degraded.

### Edge cases

- **\`_timeout = 0\` or negative disables the bound.** Deliberate: a subsystem whose init legitimately has no upper bound (a long index rebuild under operator supervision) can opt out rather than pick an arbitrary large number.
- **\`asyncio.wait_for\` cancels the coroutine.** \`_do_initialize\` must be cancellation-safe. Every in-tree subsystem is; a custom subsystem that acquires a resource before its first \`await\` should release it in a \`finally\`.
- **Per-subsystem values.** \`VectorDBSubsystem\` sets \`_timeout = 60.0\` because opening a store rebuilds its index — slower than a socket connect. The base default stays 30s.

### User impact

A misconfigured optional subsystem can no longer wedge a deployment in "starting" forever. Existing subsystems that initialize quickly are unaffected — the wrapper adds one \`wait_for\` frame.

---

## 3. \`required\` is computed, not static

\`_required\` is a class attribute, but \`VectorDBSubsystem\` raises it to \`True\` inside \`_do_initialize\` when stores are declared. \`BaseSubsystem\` now documents the resulting contract:

> \`required\` may be computed from configuration during \`_do_initialize\`. Read it **after** \`initialize()\` returns, never before — beforehand it only holds the class default.

\`\`\`python
# WRONG — reads the class default, always False for vectordb
if subsystem.required:
    ...
status = await subsystem.initialize(ctx)

# RIGHT
status = await subsystem.initialize(ctx)
if status.status is SubsystemStatus.UNHEALTHY and subsystem.required:
    raise RuntimeError(...)
\`\`\`

An orchestrator that checks \`required\` first would treat a declared-but-unopenable vector store as optional and boot into a state where every search returns an empty list.

---

## 4. \`EffectSubsystem.health_check()\` constructed an invalid \`HealthStatus\`

### Previous behaviour

\`\`\`python
# BEFORE
async def health_check(self):
    from aquilia.subsystems.base import HealthStatus, SubsystemStatus   # re-export
    ...
    return HealthStatus(
        name=self._name,
        status=...,
        metadata=health,        # <- no such field
    )
\`\`\`

### Root cause

\`HealthStatus\` (\`aquilia/health.py\`) has fields \`name\`, \`status\`, \`latency_ms\`, \`message\`, \`details\`, \`checked_at\`. There is no \`metadata\`. Every call raised \`TypeError: __init__() got an unexpected keyword argument 'metadata'\`, which the caller's \`except Exception\` turned into an unhealthy status with a confusing message — so the effect subsystem reported unhealthy whenever it was asked, regardless of actual state.

### New behaviour

\`\`\`python
# AFTER
from aquilia.health import HealthStatus, SubsystemStatus   # module-level, canonical import

async def health_check(self) -> HealthStatus:
    ...
    return HealthStatus(
        name=self._name,
        status=...,
        details=health,
    )
\`\`\`

The import moved to module scope and to \`aquilia.health\` directly, and the return type is annotated. \`details\` is the field that \`HealthStatus\` actually carries.

### User impact

\`/health\` and any host calling \`EffectSubsystem.health_check()\` now report the effect registry's real state. Previously the effect entry was permanently unhealthy once checked.

---

## 5. \`/health\` reflects live state, not the boot snapshot

### Previous behaviour

\`StorageSubsystem._register_health()\` published one \`storage.<alias>\` status per backend at boot and stopped there. \`HealthRegistry.register_check()\` existed but nothing used it, and \`ASGIAdapter\`'s \`/health\` handler read \`registry.to_dict()\` — a pure snapshot read.

A backend that went offline an hour after boot kept reporting \`HEALTHY\` until the process restarted.

### New behaviour

Both \`StorageSubsystem\` and \`VectorDBSubsystem\` now register a live aggregate check alongside the per-alias snapshot:

\`\`\`python
# StorageSubsystem._register_health / VectorDBSubsystem._register_health
health.register_check(self._name, self.health_check)
\`\`\`

and \`ASGIAdapter\` refreshes before rendering:

\`\`\`python
# Refresh any subsystem that registered a live check, so a dependency that
# died after boot is not masked by the boot-time snapshot.
await registry.run_checks()
health_report = registry.to_dict()
\`\`\`

### Behavioural changes

- The per-alias \`storage.<alias>\` / \`vectordb.<alias>\` entries remain a **boot-time snapshot** — they name what was configured and how it looked at open.
- The aggregate \`storage\` / \`vectordb\` entries are now **live** and re-evaluated on each \`/health\` request.
- \`run_checks()\` is a **no-op when nothing registered a check**, so an app with no storage or vector subsystem pays nothing.

### Performance implications

\`/health\` now costs one check invocation per registered subsystem per request. For storage that is a backend liveness probe; for vectordb it is \`VectorRegistry.health()\` across configured stores. If \`/health\` is polled aggressively by a load balancer, that cost is real and proportional to the number of registered checks — the trade is a health endpoint that can actually detect a dead dependency.

### Edge cases

- A check that raises is caught by \`HealthRegistry.run_checks()\` and recorded as \`UNHEALTHY\` with the exception message, so one broken probe cannot fail the whole endpoint.
- \`latency_ms\` on a live-checked entry is the check's own duration, not the boot duration.

---

## Compatibility notes

| Surface | Compatibility |
|---|---|
| \`AquiliaServer\` applications | Unaffected — the server does not drive \`BootContext\` subsystems |
| \`BootContext(...)\` constructor | Unchanged; all new fields optional, \`di_containers()\` is additive |
| \`shared_state["_di_registry"]\` | No longer read. It never worked, so nothing can regress |
| \`shared_state["container"]\` | Still honoured, now via \`DI_CONTAINER_KEY\` |
| Custom \`BaseSubsystem\` subclasses | Must be cancellation-safe in \`_do_initialize\`; set \`_timeout = 0\` to opt out |
| \`EffectSubsystem.health_check()\` | Signature unchanged; now returns instead of raising |
| \`/health\` response body | Same shape; values may now differ from the boot snapshot |

---

## Related documentation

- [\`vectordb.md\`](vectordb.md) — \`VectorDBSubsystem\`, which exercises the computed-\`required\` and 60s-timeout paths
- [\`admin_lifecycle.md\`](admin_lifecycle.md) — the server-side lifecycle fix in the same audit
- [\`bug_fixes.md\`](bug_fixes.md) — the full defect list
- [\`migration.md\`](migration.md) — upgrade steps
`,
    "admin_lifecycle.md": `# Admin Lifecycle & Rate Limiter — v1.4.0b3

Two defects in the admin subsystem, both found in the 2026-08-09 audit: admin's lifecycle hooks were never invoked, and the rate-limiter cleanup task reached into private state through a path that silently no-ops on a freshly booted host.

Regression coverage: \`tests/test_subsystem_boot_contract.py\`.

---

## 1. Admin lifecycle hooks never ran

### Previous behaviour

Configuring the admin dashboard produced working routes. Everything behind those routes that needed a lifecycle did not run:

- The audit log was never flushed on shutdown — buffered entries were lost on every restart.
- The rate-limit cleanup sweep never ran, so \`AdminRateLimiter\`'s in-memory attempt records grew for the process lifetime.
- The cache service was never wired from DI, so admin's cache integration ran unbacked.
- The task manager was never wired from DI, so \`AdminTasks.enqueue_*\` fell back to inline execution.
- Admin security DI providers were never registered.
- The security event tracker was never cleared on shutdown.

### Root cause

\`AquiliaServer._wire_admin_integration()\` registered admin's routes and stopped there. \`AdminLifecycle.on_startup()\` / \`on_shutdown()\` — which perform all of the above — were written, tested in isolation, and never called by anything. There was no \`LifecycleCoordinator\` entry for admin, and the server's startup sequence had no admin step.

The symptom was invisible: routes worked, the dashboard rendered, and the missing upkeep only showed as slow memory growth and an audit log that reset on deploy.

### New behaviour

\`AquiliaServer.startup()\` gained **Step 3.25**, gated on the same config key the route wiring reads:

\`\`\`python
# Step 3.25: Start admin lifecycle (audit log, cache, cleanup tasks).
admin_config = self.config.get("integrations", {}).get("admin") if hasattr(self.config, "get") else None
if admin_config is not None:
    try:
        from aquilia.admin import get_admin_subsystems

        self._admin_subsystems = get_admin_subsystems()
        await self._admin_subsystems.lifecycle.on_startup(self.config, self._get_base_container())
    except Exception as e:
        self._admin_subsystems = None
        self.logger.warning(f"Admin lifecycle startup failed: {e}")
        # Non-fatal -- admin routes still serve; background upkeep is off
\`\`\`

and \`AquiliaServer.shutdown()\` mirrors it:

\`\`\`python
# Shutdown admin lifecycle (flush audit log, sweep rate limiter)
if getattr(self, "_admin_subsystems", None) is not None:
    try:
        await self._admin_subsystems.lifecycle.on_shutdown(self.config, self._get_base_container())
    except Exception as e:
        self.logger.warning(f"Error shutting down admin lifecycle: {e}")
\`\`\`

\`self._admin_subsystems\` is initialized to \`None\` in \`__init__\` so the shutdown path is safe whether startup ran, failed, or was never reached.

### Why the placement

- **Step 3.25 — after DI containers exist, before the task manager starts.** \`on_startup\` resolves \`CacheService\` and \`TaskManager\` from the container, so the container must be built; and it wires the task manager into \`AdminTasks\` before background jobs begin, so an enqueued admin job is not dropped.
- **Gated on \`config["integrations"]["admin"]\`**, the same key \`_wire_admin_integration\` reads. An app without admin configured pays nothing and imports nothing.
- **Non-fatal.** A failed admin lifecycle logs a warning and leaves \`_admin_subsystems = None\`. Admin routes still serve; only background upkeep is off. Failing the whole boot because an optional dashboard's cache probe raised would be disproportionate.

### What \`on_startup\` does

1. Initializes the \`AdminSite\` singleton (\`AdminSite.default().initialize()\`).
2. Resolves \`CacheService\` from the DI container and hands it to \`AdminCacheIntegration\`.
3. Resolves \`TaskManager\` from the DI container and hands it to \`AdminTasks\`.
4. Registers admin security DI providers via \`register_security_providers(container, security_config)\`.

It is idempotent: \`self._started\` short-circuits a second call.

### What \`on_shutdown\` does

1. Flushes the audit log (\`await site.audit_log.flush()\` when the log implements \`flush\`).
2. Runs \`AdminTasks.rate_limit_cleanup()\`.
3. Clears the security event tracker.

Each step is independently guarded, so one failure does not skip the rest.

### User impact

| Before | After |
|---|---|
| Buffered audit entries lost on every restart | Flushed on graceful shutdown |
| \`AdminRateLimiter\` records grew unbounded | Swept on shutdown, and periodically once \`cleanup_interval\` elapses |
| \`AdminTasks.enqueue_*\` ran inline | Enqueued through the real \`TaskManager\` |
| Admin cache integration unbacked | Backed by the configured \`CacheService\` |
| Admin security providers absent from DI | Registered |

Applications that do not configure admin are unaffected.

### Migration

None. No API changed and no configuration is required — configuring admin is now sufficient for its lifecycle to run. If you previously called \`AdminLifecycle.on_startup()\` yourself from a module hook as a workaround, you can remove it: \`on_startup\` is idempotent, so leaving it in place is also safe.

---

## 2. \`AdminRateLimiter.force_cleanup()\` — public sweep API

### Previous API

\`AdminTasks.rate_limit_cleanup()\` reached into three private attributes and inferred the result from dictionary lengths:

\`\`\`python
# BEFORE
before_login = len(limiter._login_records)
before_sensitive = len(limiter._sensitive_records)

# Force cleanup by resetting the last_cleanup time
limiter._last_cleanup = 0
limiter._maybe_cleanup()

cleaned_login = before_login - len(limiter._login_records)
cleaned_sensitive = before_sensitive - len(limiter._sensitive_records)

return {
    "cleaned_login": max(0, cleaned_login),
    "cleaned_sensitive": max(0, cleaned_sensitive),
}
\`\`\`

**How it was meant to work.** Setting \`_last_cleanup = 0\` was supposed to make \`_maybe_cleanup()\`'s interval guard fall through, since \`now - 0\` would exceed \`cleanup_interval\`.

### Root cause

\`_maybe_cleanup()\` guards on \`time.monotonic() - self._last_cleanup < self.cleanup_interval\`. \`time.monotonic()\` is **not** wall-clock — on Linux it is time since boot. On a host or container that has been up for less than \`cleanup_interval\` (default **3600s**), \`time.monotonic()\` is itself below 3600, so \`now - 0 < 3600\` held and \`_maybe_cleanup()\` returned immediately.

The sweep therefore did nothing for the first hour of a machine's uptime, and \`rate_limit_cleanup()\` reported \`{"cleaned_login": 0, "cleaned_sensitive": 0}\` — indistinguishable from "there was nothing stale to clean". Fresh containers, which restart constantly, spent a disproportionate share of their life in exactly that window.

The \`max(0, ...)\` clamps were papering over the same fragility from the other end: subtracting lengths cannot distinguish "nothing was stale" from "the sweep never ran", and would go negative if a concurrent request added a record between the two reads.

### New API

The sweep is factored out of the interval check, and exposed:

\`\`\`python
def _maybe_cleanup(self) -> None:
    """Periodically remove stale entries to prevent memory growth."""
    now = time.monotonic()
    if now - self._last_cleanup < self.cleanup_interval:
        return
    self._sweep(now)

def _sweep(self, now: float) -> tuple[int, int]:
    """Drop stale records unconditionally. Returns (login, sensitive) counts."""
    self._last_cleanup = now
    cutoff = now - max(self.login_window, self.sensitive_op_window) * 2

    removed = []
    for store in (self._login_records, self._sensitive_records):
        stale_keys = [
            k for k, v in store.items()
            if v.lockout_until < now and (not v.attempts or v.attempts[-1] < cutoff)
        ]
        for k in stale_keys:
            store.pop(k, None)
        removed.append(len(stale_keys))
    return removed[0], removed[1]

def force_cleanup(self) -> tuple[int, int]:
    """Sweep stale records now, ignoring \`\`cleanup_interval\`\`."""
    return self._sweep(time.monotonic())
\`\`\`

\`\`\`python
# AFTER
cleaned_login, cleaned_sensitive = limiter.force_cleanup()
return {
    "cleaned_login": cleaned_login,
    "cleaned_sensitive": cleaned_sensitive,
}
\`\`\`

### Why it is better

- **Correct on a fresh host.** \`force_cleanup()\` bypasses the interval guard by construction rather than by trying to defeat it with a sentinel value that \`monotonic()\` semantics can invalidate.
- **Exact counts.** \`_sweep\` returns what it actually removed instead of a length diff, so the number is right even under concurrent request traffic.
- **No private access.** \`AdminTasks\` calls one public method. \`_last_cleanup\`, \`_login_records\` and \`_sensitive_records\` are no longer part of any caller's contract.
- **One sweep implementation.** The periodic path and the forced path cannot drift apart.

### Behavioural changes

| Scenario | Before | After |
|---|---|---|
| Cleanup task on a host up < 1 hour | No sweep; reports \`0\` cleaned | Sweeps; reports the real count |
| Cleanup task on a host up > 1 hour | Sweeps; count inferred from lengths | Sweeps; exact count |
| Record added concurrently during the sweep | Count could be clamped to \`0\` | Count unaffected — it counts removals |
| Periodic \`_maybe_cleanup()\` on request paths | Unchanged | Unchanged |

### Edge cases

**An active lockout is never cleared.** \`_sweep\` only removes records that are past their \`lockout_until\` **and** have no attempts newer than \`cutoff\`. \`force_cleanup()\` therefore cannot be used to release a locked-out principal — that is \`clear_login_attempts()\`, and the docstring says so. This matters: a "cleanup" call that silently unlocked brute-force attempts would be a security regression, so the boundary is stated in the API rather than left to the reader.

**\`cutoff\` is \`now - max(login_window, sensitive_op_window) * 2\`.** The 2× margin keeps a record alive for one extra window past expiry, so a client at the edge of a window is not given a fresh budget by a well-timed sweep.

### Migration

Replace any code that poked the privates:

\`\`\`python
# BEFORE
limiter._last_cleanup = 0
limiter._maybe_cleanup()

# AFTER
cleaned_login, cleaned_sensitive = limiter.force_cleanup()
\`\`\`

\`_maybe_cleanup()\` remains for the periodic path and is unchanged in behaviour.

---

## Related documentation

- [\`subsystem_boot_contract.md\`](subsystem_boot_contract.md) — the rest of the same audit
- [\`bug_fixes.md\`](bug_fixes.md) — the full defect list
- [\`migration.md\`](migration.md) — upgrade steps
`,
    "router_memory_leak_fix.md": `# Native Router Memory Leak Fix — v1.4.0b3

## Overview

In Aquilia v1.4.0b1 and v1.4.0b2, native C++ extensions (\`aquilia._core.Router\`) were introduced to accelerate HTTP route matching. During server shutdown, ASGI lifespan termination, or test suite execution, compiled native C++ \`Router\` instances could remain referenced by Python objects, producing nanobind leak warnings on process exit:

\`\`\`
nanobind: leaked 1 instance of type 'aquilia._core.Router'!
\`\`\`

Aquilia v1.4.0b3 resolves these leak warnings by implementing explicit native resource deallocation routines across \`ControllerRouter\`, \`AquiliaServer\`, and \`ASGIAdapter\`.

---

## Root Cause Analysis

1. **\`ControllerRouter\` Ownership**: \`ControllerRouter\` held a long-lived reference to \`_native\` (\`aquilia._core.Router\`). When routes were recompiled or the router was shut down, internal native method arrays (\`_native_methods\`, \`_native_routes\`) were cleared, but the primary \`_native\` C++ object reference was retained.
2. **Server Lifespan Teardown**: \`AquiliaServer.shutdown()\` closed database connections and cancelled tasks, but did not instruct its \`controller_router\` instance to release its native engine handles.
3. **ASGI Lifespan Teardown**: \`ASGIAdapter\` held circular references in \`_cached_middleware_chain\`, \`_default_container\`, and \`_server_runtime\`, preventing the underlying server instance from being garbage collected at the end of ASGI lifespan \`lifespan.shutdown\`.

---

## Technical Solution

### 1. \`ControllerRouter.clear()\` API

\`ControllerRouter\` now exposes an explicit \`.clear()\` method that releases all C++ extension references and resets compiler state:

\`\`\`python
# aquilia/controller/router.py

class ControllerRouter:
    def clear(self) -> None:
        """Clear all route indices and release native engine resources."""
        self.compiled_controllers.clear()
        self.routes_by_method.clear()
        self.matcher = PatternMatcher()
        self._static_routes.clear()
        self._dynamic_routes.clear()
        self._tries.clear()
        self._name_index.clear()
        self._native_methods.clear()
        self._native_routes.clear()
        self._native = None  # Release nanobind C++ extension handle
        self._initialized = False
\`\`\`

\`ControllerRouter.initialize()\` also invokes this cleanup prior to building new native route tables, preventing orphan C++ references during hot-reloads.

---

### 2. \`AquiliaServer.shutdown()\` Integration

\`AquiliaServer.shutdown()\` now invokes \`clear()\` on its \`controller_router\`:

\`\`\`python
# aquilia/server.py

async def shutdown(self) -> None:
    # ... database disconnect & task cancellation ...

    # Clear controller router and release native engine resources
    if hasattr(self, "controller_router") and self.controller_router is not None:
        try:
            self.controller_router.clear()
        except Exception as e:
            self.logger.warning(f"Error clearing controller router: {e}")

    self._startup_complete = False
\`\`\`

---

### 3. \`ASGIAdapter.shutdown()\` Clean Teardown

\`ASGIAdapter\` implements a dedicated \`.shutdown()\` method that is invoked during ASGI \`lifespan.shutdown\`:

\`\`\`python
# aquilia/asgi.py

class ASGIAdapter:
    async def shutdown(self) -> None:
        """Shutdown underlying server and release cached references."""
        if self.server:
            await self.server.shutdown()
        self._cached_middleware_chain = None
        self._default_container = None
        self._server_runtime = None
\`\`\`

---

## Verification & Unit Testing

The fix is verified in \`tests/engine/test_memory.py\`:

\`\`\`python
def test_controller_router_clear_releases_native_instance() -> None:
    router = ControllerRouter()
    router.initialize()
    assert router._native is not None

    router.clear()
    assert router._native is None
    assert not router._initialized

@pytest.mark.asyncio
async def test_server_shutdown_clears_controller_router_native_instance() -> None:
    server = AquiliaServer(manifests=[manifest], config=loader)
    server.controller_router.initialize()
    server._startup_complete = True

    assert server.controller_router._native is not None

    await server.shutdown()
    assert server.controller_router._native is None
\`\`\`

All 49 CLI and engine memory tests pass cleanly without emitting nanobind warnings.
`,
    "bug_fixes.md": `# Bug Fixes & Refactorings — v1.4.0b3

Aquilia v1.4.0b3 resolves several critical bugs across the CLI framework, route introspection engine, subsystem boot layer, admin lifecycle, native C++ bindings, and docsite build infrastructure.

Regression coverage for the subsystem and admin fixes: \`tests/test_subsystem_boot_contract.py\`.

---

## 1. \`aq doctor\` and \`aq validate\` Exited With \`0\` on Broken Workspaces

### Previous Behavior
Running \`aq doctor\` or \`aq validate\` on a workspace with missing databases, unloadable manifests, or broken imports printed red warning/error banners but still exited with process exit code \`0\`. CI/CD pipelines relying on these commands failed to block broken builds.

### Root Cause
Command bodies caught exceptions and printed banners, but concluded execution without calling \`sys.exit()\` or returning a non-zero exit code. \`doctor.py\` and \`validate.py\` had separate, uncoordinated exit code paths.

### New Behavior
All health checks are now managed by \`aquilia.cli.checks\`. Process exit codes are calculated by \`exit_code_for()\`:
- Workspaces with missing files, broken imports, or \`ERROR\`/\`FATAL\` findings exit with status \`1\` (\`ExitCode.FAILED\`).
- Non-existent workspaces exit with status \`3\` (\`ExitCode.CONFIG\`).

### User Impact
CI/CD test suites running \`aq validate\` or \`aq doctor\` now accurately catch configuration errors and halt failing pipeline runs.

---

## 2. \`aq inspect routes\` Displayed Controller Count Instead of Endpoint Count

### Previous Behavior
A module containing a single \`UserController\` with 5 endpoint methods (\`GET /users\`, \`POST /users\`, \`GET /users/:id\`, \`PUT /users/:id\`, \`DELETE /users/:id\`) reported "1 route".

### Root Cause
Legacy inspection logic counted \`len(manifest.controllers)\` as \`route_count\`, confusing controller class instances with individual HTTP route handlers.

### New Behavior
\`aquilia.cli.introspect.routes\` calls \`ControllerCompiler\` (the same compiler used by \`AquiliaServer\` at boot) and sums individual compiled \`RouteInfo\` objects.

\`\`\`bash
$ aq inspect routes
  Route Inspection
  ======================================================================

  users
     UserController  (prefix: /users)
       GET      /users                                 -> index
       POST     /users                                 -> create
       GET      /users/:id                             -> show
       PUT      /users/:id                             -> update
       DELETE   /users/:id                             -> delete

  ----------------------------------------------------------------------
  Total routes: 5
  Modules:      1
\`\`\`

---

## 3. Inspection Probed Non-Existent Controller Attributes

### Previous Behavior
\`aq inspect routes\` attempted to extract routes statically by probing \`__controller_routes__\`, \`__route__\`, and \`_route_meta\`. Every controller failed inspection and printed:
\`\`\`
!  UserController: routes could not be extracted statically
\`\`\`

### Root Cause
None of those attributes existed on controller classes. The actual attribute used by the framework is \`__route_metadata__\`, and proper compilation requires \`ControllerCompiler\`.

### New Behavior
\`extract_routes()\` passes the controller class directly to \`ControllerCompiler().compile_controller()\`, respecting module-level \`route_prefix\` settings and starter controllers (\`.starter("name")\`).

---

## 4. Nanobind Leak Warnings on Server/Router Shutdown

### Previous Behavior
Stopping the dev server or running unit tests produced nanobind memory leak warnings on process exit:
\`\`\`
nanobind: leaked 1 instance of type 'aquilia._core.Router'!
\`\`\`

### Root Cause
\`ControllerRouter\` retained a reference to \`_native\` (\`aquilia._core.Router\`), and neither \`AquiliaServer.shutdown()\` nor \`ASGIAdapter.shutdown()\` cleared router instances during shutdown.

### New Behavior
Added \`ControllerRouter.clear()\`, which resets \`_native = None\`, \`_native_methods.clear()\`, and \`_native_routes.clear()\`. \`AquiliaServer.shutdown()\` and \`ASGIAdapter.shutdown()\` invoke \`clear()\`, releasing native memory cleanly.

---

## 5. \`StorageRegistry\` Was Never Registered Into DI

### Previous Behavior
A host that booted \`StorageSubsystem\` through \`BootContext\` got working storage backends, but \`StorageRegistry\` was not resolvable from DI. Constructor injection of \`StorageRegistry\` failed with a resolution error.

### Root Cause
\`StorageSubsystem._register_di()\` read \`ctx.shared_state.get("_di_registry")\` — a key **nothing in the codebase ever sets**. The branch was permanently dead and failed silently, since the guard was \`if registry_obj and hasattr(registry_obj, "register")\`. \`EffectSubsystem\` used a different key (\`"container"\`), so the two subsystems could never both be wired by the same host. Neither consulted \`BootContext.registry\`, so the normal case — a context carrying a \`RuntimeRegistry\` — registered nothing.

### New Behavior
\`BootContext.di_containers()\` is the single resolution path: \`shared_state[DI_CONTAINER_KEY]\` first, then every container in \`registry.di_containers\`. Both subsystems call it, and both register into **all** app containers rather than one — matching how \`AquiliaServer\` registers app-scoped values.

### User Impact
\`AquiliaServer\` applications are unaffected (the server does not use this path). Embedders and tests that build a \`BootContext\` now get \`StorageRegistry\` and the effect registry actually wired. Anyone who set \`"_di_registry"\` should rename it to \`DI_CONTAINER_KEY\`; it never worked, so nothing can regress.

See [subsystem_boot_contract.md](subsystem_boot_contract.md#1-bootcontextdi_containers--one-di-resolution-path).

---

## 6. \`BaseSubsystem._timeout\` Was Declared But Never Enforced

### Previous Behavior
\`BaseSubsystem\` declared \`_timeout: float = 30.0\` and its docstring promised "timeout-protected initialization". A subsystem blocking on an unreachable dependency — an S3 endpoint behind a dropped route, a vector store whose lock holder never exits — hung the boot indefinitely, with no log line and no health status.

### Root Cause
Nothing read the value. \`initialize()\` awaited \`self._do_initialize(ctx)\` unbounded.

### New Behavior
\`_do_initialize\` is wrapped in \`asyncio.wait_for(..., timeout=self._timeout)\`. A timeout produces \`UNHEALTHY\` with \`Initialization timed out after 30s\` and an \`ERROR\` log line, so a host that treats \`UNHEALTHY + required\` as fatal stops the boot. A non-positive \`_timeout\` disables the bound deliberately, for a subsystem whose init legitimately has no upper limit.

### User Impact
A misconfigured optional subsystem can no longer wedge a deployment in "starting" forever. Custom \`BaseSubsystem\` subclasses must be cancellation-safe in \`_do_initialize\` — \`wait_for\` cancels the coroutine — or opt out with \`_timeout = 0\`.

---

## 7. \`EffectSubsystem.health_check()\` Always Raised \`TypeError\`

### Previous Behavior
Calling \`EffectSubsystem.health_check()\` reported the effect registry as unhealthy with a confusing message, regardless of its actual state.

### Root Cause
The method constructed \`HealthStatus(..., metadata=health)\`. \`HealthStatus\` (\`aquilia/health.py\`) has no \`metadata\` field — its fields are \`name\`, \`status\`, \`latency_ms\`, \`message\`, \`details\`, \`checked_at\`. Every call raised \`TypeError: __init__() got an unexpected keyword argument 'metadata'\`, which the caller's broad \`except Exception\` converted into an unhealthy status.

\`\`\`python
# BEFORE
return HealthStatus(name=self._name, status=..., metadata=health)

# AFTER
return HealthStatus(name=self._name, status=..., details=health)
\`\`\`

The import also moved to module scope and to \`aquilia.health\` directly rather than through the \`aquilia.subsystems.base\` re-export, and the return type is now annotated.

### User Impact
\`/health\` and any host calling \`health_check()\` now report the effect registry's real state.

---

## 8. \`/health\` Served a Boot-Time Snapshot

### Previous Behavior
A storage backend that went offline an hour after boot kept reporting \`HEALTHY\` until the process restarted.

### Root Cause
\`StorageSubsystem._register_health()\` published one \`storage.<alias>\` status per backend at boot and stopped. \`HealthRegistry.register_check()\` existed but nothing used it, and \`ASGIAdapter\`'s \`/health\` handler read \`registry.to_dict()\` — a pure snapshot read with no refresh.

### New Behavior
\`StorageSubsystem\` and \`VectorDBSubsystem\` register a live aggregate check (\`health.register_check(self._name, self.health_check)\`) alongside the per-alias snapshot, and \`ASGIAdapter\` calls \`await registry.run_checks()\` before rendering. Per-alias entries remain a boot snapshot (they describe what was configured); the aggregate entries are live.

### User Impact
\`/health\` can detect a dead dependency without a restart. The cost is one check invocation per registered subsystem per request — \`run_checks()\` is a no-op when nothing registered a check, so apps without storage or vectordb pay nothing. A check that raises is caught and recorded as \`UNHEALTHY\` rather than failing the endpoint.

---

## 9. Admin Lifecycle Hooks Were Never Invoked

### Previous Behavior
Configuring the admin dashboard produced working routes and nothing else. Buffered audit entries were lost on every restart, \`AdminRateLimiter\` records grew for the process lifetime, \`AdminTasks.enqueue_*\` silently ran inline, admin's cache integration ran unbacked, and admin security DI providers were absent.

### Root Cause
\`AquiliaServer._wire_admin_integration()\` registered routes and stopped there. \`AdminLifecycle.on_startup()\` / \`on_shutdown()\` were implemented and tested in isolation but called by nothing — there was no \`LifecycleCoordinator\` entry for admin and no admin step in the server's startup sequence. The symptom was invisible: routes worked, and the missing upkeep showed only as slow memory growth and an audit log that reset on deploy.

### New Behavior
\`AquiliaServer.startup()\` gained Step 3.25 — after DI containers exist, before the task manager starts — gated on \`config["integrations"]["admin"]\`, with a mirror in \`shutdown()\`. Failure is non-fatal: a warning is logged, \`_admin_subsystems\` stays \`None\`, admin routes still serve, and only background upkeep is off.

### User Impact
Audit logs flush on graceful shutdown; the rate limiter is swept; \`TaskManager\` and \`CacheService\` are resolved from DI. Applications that do not configure admin are unaffected. No migration is required.

See [admin_lifecycle.md](admin_lifecycle.md#1-admin-lifecycle-hooks-never-ran).

---

## 10. \`AdminTasks.rate_limit_cleanup()\` No-Opped on Freshly Booted Hosts

### Previous Behavior
\`rate_limit_cleanup()\` returned \`{"cleaned_login": 0, "cleaned_sensitive": 0}\` and removed nothing, for the first hour of a host's uptime — indistinguishable from "there was nothing stale to clean".

### Root Cause
The task set \`limiter._last_cleanup = 0\` and called \`_maybe_cleanup()\`, expecting the interval guard to fall through. But that guard is \`time.monotonic() - self._last_cleanup < self.cleanup_interval\`, and \`time.monotonic()\` is **not** wall-clock — on Linux it is time since boot. On a host up for less than \`cleanup_interval\` (default 3600s), \`time.monotonic()\` is itself below 3600, so \`now - 0 < 3600\` held and the sweep returned immediately. Fresh containers, which restart constantly, spent a disproportionate share of their life inside that window.

The surrounding \`max(0, before - after)\` length arithmetic hid the same fragility from the other end: it cannot distinguish "nothing was stale" from "the sweep never ran", and would go negative if a concurrent request added a record between the two reads.

### New Behavior
The sweep is factored out of the interval check into \`_sweep(now)\`, which returns exact \`(login, sensitive)\` removal counts, and exposed as \`AdminRateLimiter.force_cleanup()\`:

\`\`\`python
# BEFORE
before_login = len(limiter._login_records)
limiter._last_cleanup = 0
limiter._maybe_cleanup()
cleaned_login = max(0, before_login - len(limiter._login_records))

# AFTER
cleaned_login, cleaned_sensitive = limiter.force_cleanup()
\`\`\`

### User Impact
The cleanup task works on a freshly booted host and reports accurate counts. An active lockout is still never cleared — \`_sweep\` only removes records past their \`lockout_until\` with no recent attempts — so \`force_cleanup()\` cannot be used to release a locked-out principal. That remains \`clear_login_attempts()\`.

See [admin_lifecycle.md](admin_lifecycle.md#2-adminratelimiterforce_cleanup--public-sweep-api).

---

## 11. Workspace Integration Detection Reported Phantom Integrations

### Previous Behavior
\`aq doctor\` reported subsystem findings for integrations a workspace had never declared. A workspace with no \`templates\` integration could emit \`AQ_TEMPLATE_DIR_MISSING\`, and the storage/cache/mail probes fired against nothing.

### Root Cause
\`aquilia.cli.checks.subsystems._integration()\` resolved an integration by attribute lookup: \`getattr(workspace_obj, name)\`. But \`Workspace\` exposes builder **methods** named \`storage\`, \`vectordb\`, \`i18n\`, \`tasks\` and \`templates\`. \`getattr\` returned the bound method — truthy — so every workspace looked like it had declared every one of those subsystems.

### New Behavior
\`_integration()\` treats \`Workspace._integrations\` as authoritative, since it holds exactly what \`integrate()\` and the builder methods recorded. Attribute lookup remains only as a fallback for non-\`Workspace\` objects, and it now skips callables:

\`\`\`python
declared = getattr(obj, "_integrations", None)
if isinstance(declared, dict):
    found = declared.get(name)
    if found is not None:
        return found

for attr in (name, f"{name}_integration", f"_{name}"):
    found = getattr(obj, attr, None)
    if found is not None and not callable(found):
        return found
return None
\`\`\`

### User Impact
\`aq doctor\` and \`aq validate\` no longer emit findings for undeclared subsystems. Since findings at \`WARN\` do not affect the exit code, this changes report noise rather than CI outcomes — except where a phantom integration produced an \`ERROR\`.

---

## 12. \`aqdocx\` TS2657 JSX Build Error in \`MiddlewareOverview.tsx\`

### Previous Behavior
Running \`tsc -b\` on the \`aqdocx\` documentation site failed with:
\`\`\`
TS2657: JSX expressions must have one parent element
\`\`\`

### Root Cause
The v1.4.0b2 restructure banner \`<div>\` and the architecture diagram \`<div>\` were placed as direct children inside \`return()\` without a parent fragment, causing TypeScript build failures during static site generation.

### New Behavior
Restored single-root returns and positioned the v1.4.0b2 restructure banner inside \`MiddlewareOverview.tsx\` after the header section. \`tsc -b\` builds cleanly.

---

## Related documentation

- [subsystem_boot_contract.md](subsystem_boot_contract.md) — full detail on fixes 5–8
- [admin_lifecycle.md](admin_lifecycle.md) — full detail on fixes 9–10
- [vectordb.md](vectordb.md) — the new vector subsystem
- [checks_engine.md](checks_engine.md) — the check registry fix 11 lives in
- [migration.md](migration.md) — upgrade steps and compatibility matrix
`,
    "migration.md": `# Migration Guide — 1.4.0b2 → 1.4.0b3

Aquilia v1.4.0b3 is backward-compatible for standard applications, but introduces breaking changes for internal CLI tools, custom health scripts, and CI/CD pipelines expecting legacy exit code behavior. Everything in the new vector database subsystem is additive — nothing existing changes when you do not adopt it.

---

## Quick assessment

| You have… | Action required |
|---|---|
| A standard \`AquiliaServer\` application | Bump the version. Nothing else. |
| CI running \`aq validate\` or \`aq doctor\` | **Yes** — exit codes are now enforced. See §1. |
| Imports from \`aquilia.cli.parsers\` | **Yes** — the package is removed. See §2. |
| Test fixtures instantiating \`ControllerRouter\` / \`AquiliaServer\` | Recommended — call \`.clear()\` / \`.shutdown()\`. See §3. |
| Hand-built \`BootContext\` objects | **Yes** — DI key renamed. See §4. |
| Custom \`BaseSubsystem\` subclasses | Review — \`_timeout\` is now enforced. See §5. |
| Code touching \`AdminRateLimiter\` privates | **Yes** — use \`force_cleanup()\`. See §6. |
| Aggressive \`/health\` polling | Review — the endpoint now runs live checks. See §7. |
| Interest in vector search | Opt-in. See §8. |

---

## 1. Exit Code Contract Changes

In v1.4.0b2 and earlier, \`aq doctor\` and \`aq validate\` returned exit code \`0\` even when findings contained errors. In v1.4.0b3, exit codes are strictly enforced:

- \`ExitCode.OK\` (\`0\`): Command succeeded without errors.
- \`ExitCode.FAILED\` (\`1\`): At least one \`ERROR\` or \`FATAL\` finding was discovered.
- \`ExitCode.CONFIG\` (\`3\`): Workspace file missing or unloadable.

### CI/CD Pipeline Migration

If your CI pipeline relies on \`aq validate\` or \`aq doctor\`, update scripts to handle non-zero exit codes:

\`\`\`bash
# BEFORE (in CI pipeline)
aq validate
# Always returned 0, even on broken manifests

# AFTER (in CI pipeline)
aq validate
# Returns exit code 1 if manifest has errors, failing the build as intended.
\`\`\`

---

## 2. Removed Legacy Parser Modules

The following internal CLI parser modules were removed:
- \`aquilia/cli/discovery_cli.py\`
- \`aquilia/cli/parsers/__init__.py\`
- \`aquilia/cli/parsers/module.py\`
- \`aquilia/cli/parsers/workspace.py\`

### Replacement

If you had custom scripts importing from \`aquilia.cli.parsers\`, migrate to \`aquilia.cli.core.workspace\`:

\`\`\`python
# BEFORE
from aquilia.cli.parsers.workspace import WorkspaceManifest
manifest = WorkspaceManifest.from_file(Path("workspace.py"))

# AFTER
from aquilia.cli.core.workspace import load_workspace
ws = load_workspace(Path.cwd())
print(ws.module_names)
\`\`\`

---

## 3. Router Teardown API

If you maintain custom test fixtures that manually instantiate \`ControllerRouter\` or \`AquiliaServer\`, invoke \`.clear()\` or \`.shutdown()\` during teardown:

\`\`\`python
# BEFORE
router = ControllerRouter()
router.initialize()
# ... test logic ...
# router left in memory

# AFTER
router = ControllerRouter()
router.initialize()
try:
    # ... test logic ...
finally:
    router.clear()
\`\`\`

---

## 4. \`BootContext\` DI Key Renamed

If you build a \`BootContext\` by hand — an embedder, an alternative runner, or a test — the DI container key changed.

\`\`\`python
# BEFORE
ctx = BootContext(config=cfg, manifests=[])
ctx.shared_state["_di_registry"] = container    # read only by StorageSubsystem, and never set by anything

# AFTER — explicit container
from aquilia.subsystems import DI_CONTAINER_KEY
ctx = BootContext(config=cfg, manifests=[])
ctx.shared_state[DI_CONTAINER_KEY] = container

# AFTER — or let the runtime registry supply every app container
ctx = BootContext(config=cfg, manifests=[], registry=runtime_registry)
\`\`\`

\`BootContext.di_containers()\` resolves the explicit container first, then falls back to every container in \`registry.di_containers\`. It returns an empty list when neither is present, and subsystems treat that as "DI is not wired here" and skip registration with a debug log.

**Nothing can regress**, because \`"_di_registry"\` was never set by any code path — it was a dead branch. \`AquiliaServer\` applications are unaffected: the server does not drive \`BootContext\` subsystems.

Full detail: [subsystem_boot_contract.md](subsystem_boot_contract.md#1-bootcontextdi_containers--one-di-resolution-path).

---

## 5. \`BaseSubsystem._timeout\` Is Now Enforced

\`initialize()\` now wraps \`_do_initialize\` in \`asyncio.wait_for(..., timeout=self._timeout)\`. The declared default has always been 30 seconds; it was simply never read.

Two things to check in a custom subsystem:

**Cancellation safety.** \`wait_for\` cancels the coroutine on timeout. If \`_do_initialize\` acquires a resource before its first \`await\`, release it in a \`finally\`:

\`\`\`python
async def _do_initialize(self, ctx: BootContext) -> None:
    handle = acquire_something()
    try:
        await self._connect(handle)
    except asyncio.CancelledError:
        handle.close()
        raise
\`\`\`

**Legitimately unbounded init.** Set \`_timeout = 0\` (or negative) to disable the bound rather than picking an arbitrarily large number:

\`\`\`python
class IndexRebuildSubsystem(BaseSubsystem):
    _name = "index-rebuild"
    _timeout = 0        # operator-supervised; no meaningful upper bound
\`\`\`

A timeout is not an exception — it returns \`HealthStatus(status=UNHEALTHY, message="Initialization timed out after 30s")\`, so a host that treats \`UNHEALTHY + required\` as fatal stops the boot and one that does not carries on degraded.

Related: \`required\` may be computed during \`_do_initialize\` (\`VectorDBSubsystem\` raises it when stores are declared). Read it **after** \`initialize()\` returns:

\`\`\`python
# WRONG — reads the class default
if subsystem.required: ...
status = await subsystem.initialize(ctx)

# RIGHT
status = await subsystem.initialize(ctx)
if status.status is SubsystemStatus.UNHEALTHY and subsystem.required:
    raise RuntimeError(status.message)
\`\`\`

---

## 6. \`AdminRateLimiter\` Cleanup

Replace private-state manipulation with the new public method:

\`\`\`python
# BEFORE
limiter._last_cleanup = 0
limiter._maybe_cleanup()
cleaned = before - len(limiter._login_records)

# AFTER
cleaned_login, cleaned_sensitive = limiter.force_cleanup()
\`\`\`

\`_maybe_cleanup()\` remains for the periodic path and is unchanged. \`force_cleanup()\` never clears an active lockout — only records past their \`lockout_until\` with no recent attempts are removed. Releasing a locked-out principal is still \`clear_login_attempts()\`.

If you configure admin, its lifecycle now runs automatically (audit flush, rate-limit sweep, DI wiring for \`CacheService\` and \`TaskManager\`). If you previously called \`AdminLifecycle.on_startup()\` yourself as a workaround, you can remove it — \`on_startup\` is idempotent, so leaving it is also safe.

Full detail: [admin_lifecycle.md](admin_lifecycle.md).

---

## 7. \`/health\` Runs Live Checks

\`ASGIAdapter\`'s \`/health\` handler now calls \`await registry.run_checks()\` before rendering, so a dependency that died after boot is no longer masked by the boot-time snapshot.

**Response shape is unchanged.** Values may now differ from the boot snapshot — that is the point.

**Cost.** One check invocation per registered subsystem per request. \`StorageSubsystem\` and \`VectorDBSubsystem\` register live checks; for storage that is a backend liveness probe, for vectordb it is \`VectorRegistry.health()\` across configured stores. \`run_checks()\` is a no-op when nothing registered a check, so apps without those subsystems pay nothing.

If a load balancer polls \`/health\` aggressively and you would rather it not touch the backends, point it at a cheaper endpoint and reserve \`/health\` for real health assessment.

---

## 8. Adopting the Vector Database (opt-in)

Nothing here is required. An install without \`elips\`, or a workspace without a \`vectordb\` block, behaves exactly as it did in v1.4.0b2.

\`\`\`bash
pip install 'aquilia[vectordb]'
\`\`\`

> **Python 3.10:** \`elips 1.1.0\` publishes no cp310 wheels, so the extra carries \`python_version >= '3.11'\`. On 3.10 it installs nothing and \`aquilia.vectordb\` degrades exactly as on any install without the driver — \`VectorNotInstalledFault\` at first use. Without the marker, \`aquilia[full]\` would be unresolvable on 3.10 rather than simply omitting vector support.

**Step 1 — declare stores** in \`workspace.py\`:

\`\`\`python
from aquilia.workspace import Workspace

workspace = (
    Workspace("myapp")
    .vectordb(
        path="./.aquilia/vectors",
        stores={"default": {"dimension": 384, "metric": "cosine"}},
    )
)
\`\`\`

or in \`aquilia.config.py\`:

\`\`\`python
class BaseEnv(AquilaConfig):
    class vectordb(AquilaConfig.VectorDB):
        enabled   = True
        dimension = 384
\`\`\`

**Step 2 — declare models** in \`modules/<app>/vector_models.py\` (or a \`vector_models/\` package). The directory is separate from \`models/\` deliberately: importing a vector model imports \`aquilia.vectordb\`, and scanning \`models/\` for them would drag the optional dependency into every app that has SQL models.

\`\`\`python
from aquilia.vectordb import VectorModel, KeyField, TextField, VectorField, Field

class Document(VectorModel):
    key:    str         = KeyField(prefix="doc_")
    body:   str         = TextField(embed=True, min_length=1)
    vector: list[float] = VectorField(dimension=384)
    source: str         = Field(default="web", indexed=True)

    class Meta:
        collection = "documents"
        store = "default"
\`\`\`

**Step 3 — optionally declare them explicitly** in the module manifest:

\`\`\`python
manifest = AppManifest(
    name="blog",
    version="1.0.0",
    vector_models=["modules.blog.vector_models"],
)
\`\`\`

Discovery finds them either way. A manifest-declared ref that fails to import or resolve is a **hard fault** (\`ModelRegistrationFault\`); a discovery-scanned file that fails is logged and skipped. An explicit declaration is a promise, and a silently-missing model would surface later as an empty search rather than an error.

**Step 4 — verify**:

\`\`\`bash
aq vectordb status     # driver installed? stores read correctly?
aq vectordb models     # slot routing as intended?
aq doctor              # includes the new vectordb.driver check
\`\`\`

### Deployment constraints

- **elips is single-writer per directory.** With \`workers > 1\`, every worker after the first fails to acquire the lock — a startup fault, not a degradation. Give each worker its own store path, or set \`read_only=True\` on the shared store so workers search without the writer lock (writes then raise).
- **Set \`auto_create=False\` in production** so a missing store fails the boot instead of serving an empty index.
- **\`VectorDBSubsystem\` is not driven by \`AquiliaServer\`.** Like every \`BootContext\` subsystem, it is initialized by the host. See [vectordb.md](vectordb.md#wiring-the-store-lifecycle) for a module lifecycle-hook example. The \`aq vectordb\` commands need none of this — they configure and shut down \`VectorRegistry\` themselves.

### What is *not* a migration

Changing \`dimension\`, \`metric\`, or the embedder on an existing store. elips persists that identity on disk and refuses a reopen that disagrees, and vectors from two embedding models occupy incompatible spaces — mixing them makes distances meaningless while still returning a confident-looking ranked list. Use \`aq vectordb reembed --model <M> --to-embedder <URI>\`, which refuses an in-place dimension change and names the store to reconfigure.

Full detail: [vectordb.md](vectordb.md) · [vectordb_cli.md](vectordb_cli.md)

---

## Upgrade Checklist

- [ ] Upgrade \`aquilia\` to \`1.4.0b3\` in \`pyproject.toml\` or \`requirements.txt\`.
- [ ] Run \`aq doctor\` to perform a full health audit of your workspace.
- [ ] Remove any imports from \`aquilia.cli.parsers\`.
- [ ] Verify that CI/CD workflows handle non-zero exit codes from \`aq validate\`.
- [ ] Ensure test fixtures call \`server.shutdown()\` or \`router.clear()\` to prevent nanobind leak warnings.
- [ ] Rename \`shared_state["_di_registry"]\` to \`shared_state[DI_CONTAINER_KEY]\` in any hand-built \`BootContext\`.
- [ ] Confirm custom \`BaseSubsystem\` subclasses are cancellation-safe, or set \`_timeout = 0\`.
- [ ] Replace \`AdminRateLimiter\` private-state pokes with \`force_cleanup()\`.
- [ ] If \`/health\` is polled by a load balancer, budget for live check invocations.
- [ ] If adopting vector search: install \`aquilia[vectordb]\`, declare stores and models, verify with \`aq vectordb status\` / \`aq vectordb models\`.

---

## Deprecated Features

None in this release.

## Removed Features

- \`aquilia/cli/discovery_cli.py\`
- \`aquilia/cli/parsers/\` (\`__init__.py\`, \`module.py\`, \`workspace.py\`)

Both were internal CLI helpers with no documented public API. See §2 for the replacement.

---

## Compatibility Matrix

| Component | Minimum | Recommended |
|---|---|---|
| Python | 3.10 | 3.12+ |
| Python (with \`vectordb\` extra) | **3.11** | 3.12+ |
| OS | Linux, macOS 11+, Windows 10+ | Ubuntu 22.04 / macOS 14 |
| SQLite | 3.35.0 | 3.42.0+ |
| \`elips\` (optional) | 1.1.0 | 1.1.0+ |

---

## Related documentation

- [README.md](README.md) — release overview and highlights
- [vectordb.md](vectordb.md) · [vectordb_cli.md](vectordb_cli.md) — the new vector subsystem
- [subsystem_boot_contract.md](subsystem_boot_contract.md) — \`BootContext\`, timeouts, live health
- [admin_lifecycle.md](admin_lifecycle.md) — admin startup/shutdown and rate limiter
- [cli_modernization.md](cli_modernization.md) · [checks_engine.md](checks_engine.md) — CLI architecture
- [bug_fixes.md](bug_fixes.md) — every defect fixed in this release
`
  },
  "1.4.0b2": {
    "README.md": `# Aquilia v1.4.0b2 Release Notes — "Foredeck Watch"

Aquilia v1.4.0b2 continues the "Foredeck Watch" beta cycle, building on the native engine foundation of v1.4.0b1 with three major subsystem improvements: a complete middleware package restructure, a full WebSocket middleware subsystem, and a new \`AquilaConfig.Accelerator\` configuration layer for native C++ engine control. This release also resolves five critical middleware bugs that caused rate limiting to be non-functional and import-order-dependent crashes.

## Table of Contents

1. [Middleware Package Restructure](middleware_restructure.md)
2. [WebSocket Middleware Subsystem](websocket_middleware.md)
3. [Accelerator Configuration](accelerator.md)
4. [Bug Fixes](bug_fixes.md)
5. [Migration Guide](migration.md)

---

## Key Goals

1. **Fix Critical Middleware Bugs.** Rate limiting was non-functional — every rate-limited request returned 500 instead of 429 due to a \`TYPE_CHECKING\`-only \`Response\` import. Per-user rate limiting was a silent no-op because \`RateLimitMiddleware\` ran before \`AquilAuthMiddleware\`. Both are fixed.

2. **Restructure Middleware into a Coherent Package.** The \`aquilia/middleware.py\` monolith is replaced by a structured package that enforces the dependency boundaries that prevented isolated imports from working at all.

3. **Full WebSocket Middleware Parity.** A complete three-hook middleware pipeline (connect/message/disconnect) with seven built-in classes and workspace-level configuration.

4. **Declarative Native Engine Control.** \`AquilaConfig.Accelerator\` and \`aq run --no-engine\`/\`--no-dataengine\` give teams fine-grained, layered control over C++ acceleration.

---

## Breaking Changes Summary

| Change | Scope | Migration |
|--------|-------|-----------|
| \`middleware_ext/\` removed | Breaking | Update import paths; \`aquilia.middleware\` lazy re-exports all names |
| \`build_fast_handler()\` removed | Breaking | Use \`build_handler()\` |
| Security middleware import paths changed | Breaking if importing from \`aquilia.middleware_ext.security\` | Use \`aquilia.middleware.builtin.security.*\` |
| \`SocketGuard.check_message\` deprecated | Non-breaking (warning) | Use \`SocketMiddleware\` instead |
| Rate limit identity priority 12 → 16 | Behavioral | Intentional fix; per-user limits now enforced |
`,
    "middleware_restructure.md": `# Middleware Package Restructure — v1.4.0b2

## Overview

Aquilia v1.4.0b2 replaces the monolithic \`aquilia/middleware.py\` (647 lines) with a structured package at \`aquilia/middleware/\`. The restructure resolves a long-standing circular import, enables isolated middleware imports, and establishes clear dependency boundaries.

## Package Layout

\`\`\`
aquilia/middleware/
├── __init__.py               public API (lazy re-exports)
├── core/                     fault-free leaf zone
│   ├── base.py               Middleware base class + hook sentinels
│   ├── descriptor.py         MiddlewareDescriptor
│   ├── priority.py           Priority constants + sort_key
│   └── types.py              Handler, Scope, MiddlewareCallable
├── stack/                    registration and compilation
│   ├── builder.py            ChainBuilder (closure fold)
│   ├── errors.py             MiddlewareRegistrationFault, MiddlewarePriorityCollisionFault
│   ├── registry.py           MiddlewareStack
│   └── validation.py         startup contract checks
├── instrumentation/          tracing and metrics wrappers
│   ├── base.py               Instrument protocol
│   ├── metrics.py            MetricsInstrument
│   └── tracing.py            TracingInstrument
├── builtin/                  framework-owned middleware
│   ├── compression.py
│   ├── exceptions.py
│   ├── logging.py
│   ├── rate_limit.py
│   ├── request_id.py
│   ├── request_scope.py
│   ├── session.py
│   ├── static.py
│   ├── timeout.py
│   └── security/
│       ├── cors.py
│       ├── csp.py
│       ├── csrf.py
│       ├── headers.py
│       ├── hsts.py
│       ├── https_redirect.py
│       └── proxy_fix.py
└── utils/                    transport-agnostic helpers
    ├── ordering.py
    ├── throttling.py
    ├── negotiation.py
    └── status.py
\`\`\`

## The Circular Import Problem (Fixed)

\`\`\`python
# This crashed in v1.4.0b1 and earlier:
from aquilia import Middleware
\`\`\`

The cycle was: \`aquilia/middleware.py\` → \`aquilia.faults\` → \`aquilia.faults.engine\` → \`aquilia.middleware\`.

The \`Middleware\` base class now lives in \`aquilia/middleware/core/base.py\`, a fault-free leaf module. \`aquilia.middleware\` resolves exports lazily.

## New Middleware Base Class Hooks

\`\`\`python
from aquilia.middleware import Middleware

class TenantMiddleware(Middleware):
    name = "tenant"
    priority = 50
    scope = "global"
    tags = ("multi-tenant",)

    async def before(self, request, ctx) -> Response | None:
        tenant = request.header("x-tenant-id")
        if not tenant:
            return Response.json({"error": "missing tenant"}, status=400)
        ctx.state["tenant"] = tenant
        return None

    async def after(self, request, ctx, response) -> Response:
        response.headers["X-Tenant"] = ctx.state["tenant"]
        return response

    async def should_run(self, request, ctx) -> bool:
        return request.path.startswith("/api/")

    async def setup(self, app) -> None:
        self._db = await connect_tenant_db()

    async def teardown(self, app) -> None:
        await self._db.close()
\`\`\`

## Priority Constants

\`\`\`python
from aquilia.middleware.core.priority import Priority

# Priority.EXCEPTION = 1, FAULTS = 2, PROXY_FIX = 3, HTTPS_REDIRECT = 4
# Priority.REQUEST_SCOPE = 5, STATIC = 6, SECURITY_HEADERS = 7, HSTS = 8
# Priority.CSP = 9, REQUEST_ID = 10, CORS = 11, RATE_LIMIT_ANON = 12
# Priority.INSPECTOR = 13, INSPECTOR_TOOLBAR = 14 (moved from 11/12)
# Priority.AUTH = 15, RATE_LIMIT_IDENTITY = 16, CSRF = 20
# Priority.I18N = 24, TEMPLATES = 25, CACHE = 26
# Priority.APPLICATION_DEFAULT = 50
\`\`\`

## Priority Collision Detection

\`\`\`python
stack = MiddlewareStack(strict_priorities=True)
stack.add(MyMiddlewareA(), priority=50)
stack.add(MyMiddlewareB(), priority=50)  # → MiddlewarePriorityCollisionFault
\`\`\`

## Import Path Migration

| Old | New |
|---|---|
| \`aquilia.middleware_ext.CORSMiddleware\` | \`aquilia.middleware.builtin.security.cors.CORSMiddleware\` |
| \`aquilia.middleware_ext.CSRFMiddleware\` | \`aquilia.middleware.builtin.security.csrf.CSRFMiddleware\` |
| \`aquilia.middleware_ext.RateLimitMiddleware\` | \`aquilia.middleware.builtin.rate_limit.RateLimitMiddleware\` |

Top-level \`from aquilia.middleware import CORSMiddleware\` still works via lazy re-exports.
`,
    "websocket_middleware.md": `# WebSocket Middleware Subsystem — v1.4.0b2

## Overview

A full WebSocket middleware pipeline at \`aquilia/sockets/middleware/\`. Three lifecycle hooks (connect/message/disconnect) with seven built-in classes and workspace-level configuration.

## SocketMiddleware Base Class

\`\`\`python
from aquilia.sockets.middleware import SocketMiddleware

class PresenceMiddleware(SocketMiddleware):
    async def on_connect(self, ctx, next_handler):
        await presence_store.mark_online(ctx.state.get("identity", {}).get("id"))
        await next_handler(ctx)

    async def on_message(self, envelope, ctx, next_handler):
        await last_seen_store.update(ctx.connection_id)
        return await next_handler(envelope, ctx)

    async def on_disconnect(self, ctx, reason):
        await presence_store.mark_offline(ctx.state.get("identity", {}).get("id"))
\`\`\`

## Workspace Configuration

\`\`\`python
from aquilia.sockets.middleware import SocketMiddlewareChain

workspace = (
    Workspace("myapp")
    .socket_middleware(
        SocketMiddlewareChain.production()
    )
)
\`\`\`

## Presets

| Preset | Includes |
|---|---|
| \`minimal()\` | SocketFaultMiddleware (2) |
| \`defaults()\` | + MessageValidationMiddleware (10) |
| \`production()\` | + SocketMetricsMiddleware (6) + SocketRateLimitMiddleware (12) |

## Priority Bands

| Band | Range | Built-ins |
|---|---|---|
| Framework plumbing | 0–9 | SocketFaultMiddleware (2), SocketMetricsMiddleware (6) |
| Framework security | 10–19 | MessageValidationMiddleware (10), SocketRateLimitMiddleware (12), SocketAuthMiddleware, SocketPermissionMiddleware |
| Application | 50–99 | SocketLoggingMiddleware, user middleware |

## Scope System

\`global\` < \`namespace:/chat\` < \`event:message.send\`

## Security Parity Warning

HTTP middleware does **NOT** apply to WebSocket messages. A socket surface is protected only by middleware registered on its own chain.

## Deprecated: SocketGuard.check_message

\`SocketGuard.check_message\` was never called by the runtime. Use \`SocketMiddleware.on_message\` instead. \`check_handshake\` remains supported.
`,
    "accelerator.md": `# Accelerator Configuration — v1.4.0b2

## AquilaConfig.Accelerator

\`\`\`python
class AquilaConfig:
    class Accelerator:
        engine: bool = True       # AQUILIA_ENGINE — C++ router + RequestContext
        dataengine: bool = True   # AQUILIA_DATAENGINE — C++ ORM FieldPlan
\`\`\`

Both engines are fail-soft. These fields add explicit control over the fallback.

## Workspace Configuration

\`\`\`python
class BaseEnv(AquilaConfig):
    class accelerator(AquilaConfig.Accelerator):
        engine = True
        dataengine = True

class CIEnv(BaseEnv):
    env = "ci"
    class accelerator(BaseEnv.accelerator):
        engine = Env("AQUILIA_ENGINE", default=False, cast=bool)
        dataengine = Env("AQUILIA_DATAENGINE", default=False, cast=bool)
\`\`\`

## CLI Flags

\`\`\`bash
aq run --no-engine          # disable C++ router
aq run --no-dataengine      # disable C++ ORM compiler
aq run --no-engine --no-dataengine  # full pure-Python mode
\`\`\`

## Priority Chain (Highest Wins)

1. CLI flag (\`aq run --no-engine\`)
2. Process environment (\`AQUILIA_ENGINE=0\`)
3. \`workspace.py\` \`AquilaConfig.Accelerator\`
4. Framework default (enabled)

A pre-existing environment variable is **never** overwritten by workspace.py.

## run_dev_server() API

\`\`\`python
def run_dev_server(
    ...,
    *,
    engine: bool | None = None,
    dataengine: bool | None = None,
) -> None:
\`\`\`
`,
    "bug_fixes.md": `# Bug Fixes — v1.4.0b2

## 1. Rate Limiting Returned 500 Instead of 429

\`Response\` was imported under \`TYPE_CHECKING\` only. \`_rate_limited_response()\` raised \`NameError\` on every rate-limited request. All keying modes broken. Fixed by runtime import.

## 2. Per-User Rate Limiting Was a Silent No-Op

\`RateLimitMiddleware\` at priority 12 ran before \`AquilAuthMiddleware\` at 15. \`user_key_extractor\` always returned \`None\` — rules silently skipped. Fixed: identity rules now at priority 16 (after AUTH at 15). \`RateLimitRule.requires_identity\` auto-detected for \`user_key_extractor\`.

## 3. Middleware Circular Import Crash

\`from aquilia.middleware import Middleware\` crashed if \`aquilia.faults\` wasn't imported first. Root cause: cycle between \`aquilia/middleware.py\` and \`aquilia/faults/engine.py\`. Fixed: \`Middleware\` base moved to \`aquilia/middleware/core/base.py\`.

## 4. Duplicate Middleware Priorities Silently Reordered

\`MiddlewareStack.add()\` now warns on same-scope/same-priority collisions. \`strict_priorities=True\` raises \`MiddlewarePriorityCollisionFault\`. Inspector moved 11→13, 12→14 to clear collisions with CORS and RATE_LIMIT_ANON.

## 5. WebSocket Parameterized Routes Never Matched

\`@Socket("/chat/:room")\` only matched the literal path. Root cause: \`PatternMatcher.match()\` called without \`await\`, returning a coroutine. Swallowed by bare \`except:\`. Path params now correctly extracted.

## 6. WebSocket Policy Close Code 1003 → 1008

\`WS_AUTH_REQUIRED\`, \`WS_FORBIDDEN\`, \`WS_ORIGIN_NOT_ALLOWED\` now close with code 1008 (policy violation) instead of 1003 (unsupported data).

## 7. EncryptedMixin Crashed With cryptography Installed

\`Fernet(key)\` raises \`ValueError\` for non-base64-encoded keys. Only \`ImportError\` was caught. \`ValueError\`/\`TypeError\` now caught and fall through to \`_StdlibAESGCM\`.

## 8. asyncio.TimeoutError Not Caught on Python 3.10

\`asyncio.TimeoutError\` is separate from \`TimeoutError\` on Python 3.10. Requests exceeding timeout returned 500. Both exception classes now caught.

## 9. TokenBucket ZeroDivisionError for limit=0

\`TokenBucket.consume()\` now guards against zero refill rate, reporting a finite retry-after.

## 10. WebSocket Worker ID Used Unix-Only os.uname()

Replaced with cross-platform \`platform.node()\`.
`,
    "migration.md": `# Migration Guide — 1.4.0b1 → 1.4.0b2

## 1. middleware_ext Import Paths

\`\`\`python
# BEFORE
from aquilia.middleware_ext import RateLimitMiddleware
from aquilia.middleware_ext.security import CORSMiddleware

# AFTER — top-level (recommended)
from aquilia.middleware import RateLimitMiddleware, CORSMiddleware

# AFTER — canonical paths
from aquilia.middleware.builtin.rate_limit import RateLimitMiddleware
from aquilia.middleware.builtin.security.cors import CORSMiddleware
\`\`\`

Update dotted-path strings in workspace.py:
\`\`\`python
# BEFORE
.use("aquilia.middleware_ext.security.CORSMiddleware", priority=11)
# AFTER
.use("aquilia.middleware.builtin.security.cors.CORSMiddleware", priority=11)
\`\`\`

## 2. build_fast_handler() Removed

\`\`\`python
# BEFORE
handler = stack.build_fast_handler(final_handler)
# AFTER
handler = stack.build_handler(final_handler)
\`\`\`

## 3. Rate Limit Ordering Change

Identity-based rules now run at priority 16 (after auth at 15). Per-user limits were not enforced before. Verify your limits before deploying.

## 4. SocketGuard.check_message Deprecated

\`\`\`python
# BEFORE (never executed)
class MyGuard(SocketGuard):
    async def check_message(self, message, ctx):
        return authorized(ctx)

# AFTER
class AuthCheckMiddleware(SocketMiddleware):
    async def on_message(self, envelope, ctx, next_handler):
        if not ctx.state.get("identity"):
            raise PermissionError("Authentication required")
        return await next_handler(envelope, ctx)
\`\`\`

## 5. Add Socket Middleware to Workspace

\`\`\`python
from aquilia.sockets.middleware import SocketMiddlewareChain

workspace = (
    Workspace("myapp")
    .socket_middleware(SocketMiddlewareChain.production())
)
\`\`\`

## Upgrade Checklist

- [ ] Update \`aquilia\` to \`1.4.0b2\`
- [ ] Search for \`aquilia.middleware_ext\` imports and update
- [ ] Search for \`build_fast_handler\` calls, replace with \`build_handler\`
- [ ] Check rate limit configurations — per-user limits now actually enforced
- [ ] Migrate \`SocketGuard.check_message\` to \`SocketMiddleware.on_message\`
- [ ] Add \`SocketMiddlewareChain\` to workspace.py for WebSocket endpoints
- [ ] Run test suite, watch for priority collision warnings at boot

## Compatibility Matrix

| Component | Minimum | Recommended |
|---|---|---|
| Python | 3.10 | 3.12+ |
| OS | Linux, macOS 11+, Windows 10+ | Ubuntu 22.04 / macOS 14 |
| SQLite | 3.35.0 | 3.42.0+ |
`
  }
};

