# Aquilia v1.3.3 Release Notes — "Analytical Depths"

Aquilia v1.3.3 is a focused ORM release delivering three long-awaited
analytical query capabilities — **Window Functions**, **CTEs**, and
**Recursive CTEs** — implemented as first-class AST nodes in the expression
system, not thin raw-SQL wrappers. The release also ships two ORM bug fixes
discovered and verified during a production-grade audit of the models layer.

---

## Table of Contents

1. [Window Functions](window_functions.md)
   - Ranking, distribution, and offset window functions
   - Aggregate windows (running totals, moving averages)
   - PARTITION BY, ORDER BY, and frame clauses
2. [CTEs — Common Table Expressions](cte.md)
   - Non-recursive CTEs
   - Multiple CTEs and dependency chaining
3. [Recursive CTEs](recursive_cte.md)
   - Tree traversal and hierarchical queries
   - Anchor/recursive API
   - UNION vs UNION ALL
4. [Bug Fixes](bugfixes.md)
   - UUIDField(auto=True) NULL primary key
   - Transaction nesting depth tracker
5. [Backend Compatibility Matrix](backends.md)
6. [Migration Guide](migration.md)

---

## Quick Examples

### Window: rank users by score inside each country

```python
from aquilia.models import Window
from aquilia.models.window import Rank

users = await User.objects.annotate(
    rank=Window(
        Rank(),
        partition_by=["country"],
        order_by="-score",
    )
).all()

for u in users:
    print(u.name, u.rank)
```

### Window: running total of sales

```python
from aquilia.models import Sum, Window

sales = await Sale.objects.annotate(
    running_total=Window(
        Sum("amount"),
        order_by="created_at",
    )
).order("created_at").all()
```

### CTE: active users summary

```python
active_cte = User.objects.filter(is_active=True).cte("active_users")

result = await (
    User.objects
    .with_cte(active_cte)
    .filter(role="admin")
    .all()
)
```

### Recursive CTE: folder tree

```python
tree = await Folder.objects.recursive_cte(
    name="folder_tree",
    anchor=lambda q: q.filter(parent_id__isnull=True),
    recursive=lambda cte: Folder.objects.filter(
        parent_id=cte.col("id")
    ),
).all()
```

---

## What Changed

### New modules

| Module | Purpose |
|---|---|
| `aquilia.models.window` | `Window`, all window functions, `FrameBound`, `WindowFrame`, `FrameType` |
| `aquilia.models.cte` | `CTE`, `RecursiveCTE`, `CTEReference`, `CTECol` |

### Q chain methods added

| Method | Purpose |
|---|---|
| `Q.cte(name)` | Create a named CTE from this queryset |
| `Q.with_cte(*ctes)` | Register CTEs into the query's WITH clause |
| `Q.recursive_cte(name, anchor, recursive, *, union_all)` | Build + register a recursive CTE |

### Expression system additions (`aquilia.models.window`)

`Window`, `Rank`, `DenseRank`, `RowNumber`, `Ntile`, `Lag`, `Lead`,
`FirstValue`, `LastValue`, `NthValue`, `FrameType`, `FrameBound`, `WindowFrame`

All available via `from aquilia.models import Window, Rank, ...`

---

## Fixes Shipped

| Issue | Root cause | Fix |
|---|---|---|
| `UUIDField(auto=True)` inserts NULL | `setdefault` no-op on pre-populated `kwargs` dict | Explicit `UNSET` sentinel check |
| Transaction depth leak / `id()` contamination | `WeakValueDictionary` integer keys never freed; `id()` reuse gives new task stale depth | Replaced with `contextvars.ContextVar[int]` |
