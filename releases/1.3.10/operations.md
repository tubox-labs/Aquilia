# Operations Reference — Aquilia v1.3.10

Every change to a database schema is represented as a typed `Operation` object. Operations are backend-independent: they carry semantic intent (e.g. "add a column called `bio` to `User`"), and a `SchemaBackend` turns that intent into SQL at execution time.

---

## Operation Protocol

Every `Operation` subclass implements:

| Method | Description |
|---|---|
| `state_forwards(state)` | Update `ProjectState` as if the operation has been applied. Used to replay history without touching the database. |
| `state_backwards(state)` | Update `ProjectState` as if the operation has been rolled back. |
| `database_forwards(executor, state)` | Apply the operation to a live database. |
| `database_backwards(executor, state)` | Roll back the operation from a live database. |
| `describe() → str` | Human-readable one-line summary shown in `aq db makemigrations` output. |
| `atomic: bool` | Whether the operation requires a transaction. |

### `OperationCategory`

```python
class OperationCategory(str, Enum):
    DDL = "ddl"           # Table/column/index changes
    DATA = "data"         # RunSQL, RunPython with data changes
    MIXED = "mixed"       # Operations that combine DDL and data
```

---

## Model Operations

### `CreateModel`

Create a new table and all its indexes, constraints, and M2M junction tables.

```python
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
```

**State forward:** Adds `model` to `ProjectState.tables`.
**State backward:** Removes `model` from `ProjectState.tables`.

### `DeleteModel`

Drop a table and all its indexes, constraints, and M2M junction tables.

```python
DeleteModel(model="Post")
```

**Irreversible** unless a corresponding `CreateModel` is in the rollback plan.

### `RenameModel`

Rename a model and its underlying table.

```python
RenameModel(model="OldName", new_model="NewName")
```

### `AlterModelOptions`

Change `Meta` options without touching columns (e.g. `ordering`, `verbose_name`).

```python
AlterModelOptions(model="Post", options={"ordering": ["-created_at"]})
```

---

## Field Operations

### `AddField`

Add a column to an existing table.

```python
AddField(
    model="User",
    field=ColumnState.of("bio", fields.TextField(null=True, blank=True)),
)
```

**Reversible** via `RemoveField`.

### `RemoveField`

Remove a column from an existing table.

```python
RemoveField(model="User", field_name="bio")
```

> [!WARNING]
> Irreversible in the sense that the data is deleted. The operation itself can generate `ALTER TABLE ... DROP COLUMN`.

### `AlterField`

Change a column's type, constraints, or default.

```python
AlterField(
    model="User",
    field_name="bio",
    field=ColumnState.of("bio", fields.CharField(max_length=500)),
)
```

**Compatibility note:** Narrowing a type (e.g. `TextField` → `CharField(max_length=100)`) may truncate data. The backend marks such statements as `destructive=True`.

### `RenameField`

Rename a column.

```python
RenameField(model="User", old_name="bio", new_name="biography")
```

---

## Index Operations

### `AddIndex`

```python
AddIndex(
    model="Post",
    index=IndexState(
        name="idx_post_title",
        columns=("title",),
        unique=False,
    ),
)
```

### `RemoveIndex`

```python
RemoveIndex(model="Post", index_name="idx_post_title")
```

### `AlterIndex`

Replace an existing index definition (drop + recreate).

```python
AlterIndex(
    model="Post",
    old_index=IndexState(name="idx_post_title", columns=("title",)),
    new_index=IndexState(name="idx_post_title", columns=("title",), unique=True),
)
```

---

## Constraint Operations

### `AddConstraint`

```python
from aquilia.models.migration.schema import CheckConstraintState

AddConstraint(
    model="Post",
    constraint=CheckConstraintState(
        name="chk_post_title_nonempty",
        condition="length(title) > 0",
    ),
)
```

### `RemoveConstraint`

```python
RemoveConstraint(model="Post", constraint_name="chk_post_title_nonempty")
```

### `AlterConstraint`

Drop and recreate a constraint with a new definition.

---

## Relation Operations

### `CreateManyToManyTable`

Create the junction table for a `ManyToManyField`. Emitted automatically by `CreateModel` when the model declares M2M fields; also emitted standalone when a M2M field is added to an existing model.

```python
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
```

### `DeleteManyToManyTable`

Drop a M2M junction table.

---

## Special Operations

### `RunSQL`

Execute raw SQL forward and (optionally) backward.

```python
RunSQL(
    sql="UPDATE posts SET published = TRUE WHERE created_at < '2026-01-01'",
    reverse_sql="UPDATE posts SET published = FALSE WHERE created_at < '2026-01-01'",
    atomic=True,
)
```

> [!IMPORTANT]
> `RunSQL` and `RunPython` act as **optimizer barriers** — the optimizer never merges operations across them, since a data migration may depend on the exact intermediate schema.

### `RunPython`

Execute a Python callable.

```python
def backfill_slugs(executor, state):
    """Populate slug from title for existing posts."""
    # Access the database through executor
    ...

RunPython(
    code=backfill_slugs,
    reverse_code=None,   # irreversible data migration
    atomic=True,
)
```

---

## Custom Operations

Register a custom operation class so the serializer can find it by name when loading generated files:

```python
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
```

`resolve_operation("PartitionTable")` will then return the class when loading a migration that uses it.

---

## Operation Interactions with the Optimizer

The optimizer folds operations in multiple passes until no further reduction is possible (capped at `MAX_OPTIMIZER_PASSES = 32`):

| Rule | Input | Output |
|---|---|---|
| Fold field into create | `CreateModel(U)` + `AddField(U.x)` | `CreateModel(U with x)` |
| Cancel field add/remove | `AddField(U.x)` + `RemoveField(U.x)` | *(nothing)* |
| Collapse field alter | `AddField(U.x)` + `AlterField(U.x)` | `AddField` with final definition |
| Collapse double alter | `AlterField(x)` + `AlterField(x)` | one `AlterField` |
| Cancel model create/delete | `CreateModel(U)` + `DeleteModel(U)` | *(nothing)* |
| Absorb rename into add | `AddField(U.x)` + `RenameField(x→y)` | `AddField(U.y)` |
| Merge option changes | `AlterModelOptions(a)` + `AlterModelOptions(b)` | one `AlterModelOptions` with merged options |
| Collapse index add/remove | `AddIndex(i)` + `RemoveIndex(i)` | *(nothing)* |
