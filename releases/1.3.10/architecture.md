# Architecture Deep Dive — Aquilia v1.3.10

This document explains the design decisions, trade-offs, and guarantees behind the new migration subsystem for readers who want to understand the internals or contribute to the framework.

---

## Design Principles

### 1. No Information Loss at the First Hop

Previous systems reduced every `Field` to a handful of primitives (name, SQL type, a few booleans) at snapshotting time. No amount of care downstream can recover a generated-column expression, a partial-index predicate, an operator class, or an M2M relationship from that reduced set.

`ProjectState` therefore captures fields through `Field.deconstruct()` and retains enough to reconstruct them faithfully. SQL generation is deferred to `backends/` — the *only* layer permitted to know about dialects.

### 2. Strict Layering

```
Model classes → schema.py → operations/ → backends/
               state          state deltas    SQL text
```

Nothing in `schema.py` emits SQL. Nothing in `operations/` imports a backend. Nothing in `engine.py` constructs a SQL string. This separation makes operations backend-independent, serialization deterministic, and testing tractable.

### 3. Determinism Above All

A migration is a permanent, reviewable artifact. Two developers generating a migration against the same models on different machines must get the same file. Every collection in the pipeline is an ordered `tuple`; every mapping is iterated through `sorted()`. The `codegen` layer emits sorted key-order, omits default-valued arguments, and accepts no clock or hostname into the rendered body.

Consequence: "No changes detected" is trustworthy. Regenerating from unchanged models produces a byte-identical file.

### 4. Safe Rename Detection

A rename is a destructive guess. Emitting `RENAME COLUMN` when the developer actually dropped one column and added another silently overwrites the wrong column and loses its data.

The autodetector scores rename candidates across multiple independent signals. The `RENAME_CONFIDENCE_THRESHOLD = 0.85` is set so that no single signal — not even an identical type — can clear it alone. The combination of type match, name similarity, position, and constraints must all agree before a rename is inferred automatically. The developer can always provide an explicit `RenameHint` to override the inference.

### 5. File Before Snapshot

`make_migrations` writes the migration file first, then saves the updated snapshot:

```python
path.write_text(source, encoding="utf-8")
self.save_snapshot(after)           # ← snapshot written AFTER file
```

If the snapshot write fails, the file still exists and the snapshot still describes the last successful migration. The next `makemigrations` will compute the same diff and regenerate the same file — the developer just reruns the command.

Writing snapshot first would advance it past a migration file that was never recorded on disk. The next `makemigrations` would see no diff and generate nothing, losing the change entirely.

### 6. Tracking Inside the Transaction

```
┌─ transaction ─────────────────────────────────────┐
│  DDL statement 1                                  │
│  DDL statement 2                                  │
│  ...                                              │
│  INSERT INTO aquilia_migrations (revision, ...)   │
└───────────────────────────────────────────────────┘
```

The tracking `INSERT` is the last statement *inside* the same transaction. Schema and history commit or roll back together, closing the window where a crash could change the schema without recording it.

### 7. Non-transactional Statements

Some DDL cannot participate in a transaction:

- **SQLite table rebuilds** need `PRAGMA foreign_keys` toggled outside any transaction.
- **PostgreSQL `CREATE INDEX CONCURRENTLY`** is rejected inside a transaction.
- **MySQL and Oracle DDL** cannot participate in a transaction at all.

Statements declare their own requirement (`transactional: bool`). The executor splits the batch at non-transactional statements, warns on MySQL/Oracle rather than promising atomicity it cannot deliver, and emits `diagnostics` entries to `ExecutionResult` for both cases.

---

## Atomicity Model

```
Transactional (SQLite, PostgreSQL):
  ✓ DDL rolls back on failure
  ✓ Tracking row commits with DDL or not at all
  ✓ No partial schema artifacts

Non-transactional (MySQL, Oracle):
  ⚠ DDL committed immediately (per statement)
  ⚠ Failure may leave partial schema
  ✓ Tracking row not written on failure
  ✓ Warning logged via ExecutionResult.diagnostics
```

---

## Snapshot Format v2 (STATE_VERSION = 2)

The snapshot stores the current `ProjectState` as a JSON artifact:

```json
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
```

Key differences from the old `"models"` format (v1):

| Feature | v1 (`"models"`) | v2 (`"tables"`) |
|---|---|---|
| Top-level key | `"models"` | `"tables"` |
| Field storage | Primitive strings | `Field.deconstruct()` dicts |
| M2M support | ❌ | ✓ |
| Generated columns | ❌ | ✓ |
| Index methods | ❌ | ✓ |
| Partial predicates | ❌ | ✓ |
| Determinism | Set-ordered | Sorted tuple |
| Format detection | None | `STATE_VERSION` field |

Old snapshots with `"models"` key are detected and discarded: the engine logs an informational message and returns an empty `ProjectState`, triggering a full regeneration on the next `makemigrations`.

---

## Migration File Format v3 (MIGRATION_TEMPLATE_VERSION = 3)

Version 3 files use real constructor calls:

```python
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
```

Version 2 files (old DSL with `Migration`, `C.*`, `ColumnDef`) are **not** loadable by the new engine. Version 1 files (legacy raw-SQL with `upgrade(db)`) are also not loadable. A `MigrationFault` is raised when loading either.

---

## Graph Planning

### Forward Plan

Given the set of applied revisions, `MigrationGraph.forward_plan(applied)` returns pending nodes in topological order:

1. Build the dependency DAG from all nodes on disk.
2. Remove any node already in `applied`.
3. Return nodes in topological order where all dependencies are satisfied.

A node with `replaces = ("a", "b")` is skipped in the forward plan when every revision in `replaces` is in `applied` — the squash migration is treated as already done.

### Backward Plan

`backward_plan(applied, target)` returns the nodes to roll back to reach `target`:

1. Find the path from the current leaves back to `target`.
2. Return nodes in reverse dependency order (deepest first).
3. Each operation must implement `state_backwards` and `database_backwards`; irreversible operations (`RunPython` without `reverse_code`) raise `MigrationFault`.

### Conflict Detection

`check_conflicts()` raises `MigrationConflictFault` when:
- Two migration files claim the same revision.
- Two leaf nodes have no common ancestor (forked history without a merge migration).

Forked history is the expected result of two developers generating migrations on the same branch simultaneously. The resolution is to generate a merge migration that explicitly depends on both leaves.

---

## Optimizer Passes

The optimizer iterates the operation list repeatedly until no pass reduces its length (or `MAX_OPTIMIZER_PASSES = 32` is reached):

```
Pass 1: [CreateModel(U), AddField(U.x), AddField(U.y)] → [CreateModel(U with x, y)]
Pass 2: no further reduction
→ done in 2 passes
```

`RunSQL` and `RunPython` are opaque barriers. The optimizer never merges across them because a data migration may well depend on the exact intermediate schema, and merging across it would silently change what it sees. This is not a safety "nice to have" — it is a correctness requirement.

---

## Checksum Verification

Every `AppliedMigration` row now stores a SHA-256 digest of the migration source file (`MigrationNode.checksum`). `engine.verify_checksums(db)` reads all applied rows from the tracking table and checks each against the corresponding file on disk:

| Mismatch type | Reason |
|---|---|
| File missing from disk | Migration was applied but the file was deleted |
| Checksum mismatch | File was edited after being applied |

This is not a blocking check — the engine does not refuse to run with mismatches — but the output can be used in CI to enforce that production migrations have not been tampered with.
