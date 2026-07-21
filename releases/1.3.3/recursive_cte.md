# Recursive CTEs — Aquilia v1.3.3

Recursive CTEs use `WITH RECURSIVE` to traverse hierarchical or graph
structures in a single SQL query. They consist of:

1. **Anchor term** — the base case (e.g., root nodes)
2. **Recursive term** — references the CTE itself to walk to the next level
3. **UNION / UNION ALL** — combines both terms

```sql
WITH RECURSIVE "folder_tree" AS (
    SELECT * FROM "folders" WHERE ("parent_id" IS NULL)
    UNION ALL
    SELECT f.* FROM "folders" f
    INNER JOIN "folder_tree" ft ON f."parent_id" = ft."id"
)
SELECT * FROM "folder_tree"
```

---

## API

### `Q.recursive_cte(name, anchor, recursive, *, union_all=True) → Q`

Builds and registers a recursive CTE, returning a queryset that selects
from the named CTE table.

```python
tree = await Folder.objects.recursive_cte(
    name="folder_tree",
    anchor=lambda q: q.filter(parent_id__isnull=True),
    recursive=lambda cte: Folder.objects.filter(
        parent_id=cte.col("id")
    ),
).all()
```

**Arguments**

| Argument | Type | Description |
|---|---|---|
| `name` | `str` | SQL identifier for the CTE (validated against `_SAFE_FIELD_RE`) |
| `anchor` | `Callable[[Q], Q]` | Receives a fresh queryset; return the base case |
| `recursive` | `Callable[[CTEReference], Q]` | Receives a `CTEReference`; return the recursive term |
| `union_all` | `bool` | `True` (default) = `UNION ALL`; `False` = `UNION` (deduplication) |

**Returns** a `Q` queryset with `_table = name` and the `RecursiveCTE`
registered. Call terminal methods (`.all()`, `.filter().all()`, etc.)
on the returned queryset.

---

## CTEReference

Inside the `recursive` lambda, the parameter is a `CTEReference` that
represents the partially-built CTE from the previous iteration.

```python
lambda cte: Folder.objects.filter(parent_id=cte.col("id"))
#                                             ^^^^^^^^^^^
#                                    CTECol("folder_tree", "id")
#                                    renders: "folder_tree"."id"
```

`cte.col("field")` returns a `CTECol` expression that renders as
`"cte_name"."field"`, safe for use in any filter or annotation.

---

## Practical Examples

### Folder / category tree

```python
class Folder(Model):
    table = "folders"
    name = CharField(max_length=255)
    parent_id = ForeignKey("Folder", null=True, on_delete=SET_NULL)

# All folders under root (no parent)
tree = await Folder.objects.recursive_cte(
    name="folder_tree",
    anchor=lambda q: q.filter(parent_id__isnull=True),
    recursive=lambda cte: Folder.objects.filter(
        parent_id=cte.col("id")
    ),
).all()
```

### Employee org chart (subtree from manager)

```python
# All direct and indirect reports under employee id=42
subtree = await Employee.objects.recursive_cte(
    name="org_chart",
    anchor=lambda q: q.filter(id=42),
    recursive=lambda cte: Employee.objects.filter(
        manager_id=cte.col("id")
    ),
).all()
```

### Comment thread (nested replies)

```python
# All replies under a top-level comment
thread = await Comment.objects.recursive_cte(
    name="comment_thread",
    anchor=lambda q: q.filter(id=root_comment_id),
    recursive=lambda cte: Comment.objects.filter(
        parent_id=cte.col("id")
    ),
).order("depth").all()
```

### Dependency graph — transitive closure

```python
# All packages that depend (directly or transitively) on package "base"
deps = await Package.objects.recursive_cte(
    name="dep_graph",
    anchor=lambda q: q.filter(name="base"),
    recursive=lambda cte: Package.objects.filter(
        depends_on=cte.col("name")
    ),
    union_all=False,  # UNION deduplicates circular dependencies
).all()
```

---

## UNION vs UNION ALL

| Mode | Use when |
|---|---|
| `union_all=True` (default) | Tree structures with no cycles (folder trees, org charts) — faster, avoids dedup overhead |
| `union_all=False` | Graph structures where cycles are possible (dependency graphs, network routes) — deduplication prevents infinite loops |

> **Note:** `UNION` deduplication prevents infinite traversal loops in
> directed graphs, but only if duplicates are meaningful. For deep trees,
> prefer `UNION ALL` and add a depth limit via a counter column if needed.

---

## Adding Depth / Path Tracking

For depth tracking, use `annotate()` on the anchor and a computed field:

```python
# This requires a depth column — add it to your model or use values()
# The anchor starts at depth=0; recursive adds 1 each level.
# Best achieved with RawSQL or a custom expression on the recursive branch.
# See the SQL reference for your database for depth-tracking patterns.
```

---

## RecursiveCTE Object

`Q.recursive_cte(...)` internally constructs a `RecursiveCTE` instance:

```python
from aquilia.models.cte import RecursiveCTE

rcte = RecursiveCTE(
    name="folder_tree",
    anchor_qs=Folder.objects.filter(parent_id__isnull=True),
    recursive_qs=Folder.objects.filter(parent_id=CTECol("folder_tree", "id")),
    union_all=True,
)
rcte.as_sql("sqlite")
# → ('"folder_tree" AS (SELECT ... UNION ALL SELECT ...)', [...params...])
```

---

## Backend Compatibility

| Feature | SQLite | PostgreSQL | MySQL | MariaDB |
|---|---|---|---|---|
| `WITH RECURSIVE` | ≥ 3.8.3 | ≥ 8.4 | ≥ 8.0 | ≥ 10.2 |
| `UNION ALL` in recursive | ≥ 3.8.3 | ≥ 8.4 | ≥ 8.0 | ≥ 10.2 |
| `UNION` dedup in recursive | ≥ 3.8.3 | ≥ 8.4 | ≥ 8.0 | ≥ 10.2 |
