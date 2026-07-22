# PAGE: /docs/models/window-functions
## Title: Window Functions

Window functions allow you to perform calculations across a set of table rows that are somehow related to the current row. Unlike aggregate functions (like `SUM` or `COUNT` with a `GROUP BY`), window functions do not collapse the result set into a single output row. Instead, the result is appended to each original row.

### The Window() Wrapper

In Aquilia, you apply a window function using the `Window` class inside an `.annotate()` call.

```python
from aquilia.models.window import Window, Rank, RowNumber
from aquilia.models import Sum, F

# Rank users by score within each country
users = await User.objects.annotate(
    rank=Window(Rank(), partition_by='country', order_by='-score')
).all()
```

### Supported Window Functions

Aquilia provides wrappers for standard SQL window functions out-of-the-box:

- `Rank()` - Ranks items (allows ties and skips ranks, e.g. 1, 2, 2, 4)
- `DenseRank()` - Ranks items without skipping (e.g. 1, 2, 2, 3)
- `RowNumber()` - Generates a unique sequential number for each row
- `Ntile(n)` - Divides the partition into `n` buckets
- `Lag(expression, offset=1, default=None)` - Accesses data from a previous row
- `Lead(expression, offset=1, default=None)` - Accesses data from a subsequent row
- `FirstValue(expression)` - Returns the first value in the window frame
- `LastValue(expression)` - Returns the last value in the window frame
- `NthValue(expression, n)` - Returns the Nth value in the window frame

You can also use standard aggregates like `Sum()`, `Avg()`, and `Count()` as window expressions.

```python
# Moving average of sales
sales = await DailySale.objects.annotate(
    moving_avg=Window(Avg('amount'), order_by='date')
).all()
```

### Partitioning and Ordering

The `Window` object takes optional arguments:
- `partition_by`: Defines the groups of rows the function is applied to. It accepts a string field name, an `F()` expression, or a list of them.
- `order_by`: Determines the order in which rows are processed within a partition. It accepts string field names (prefix `-` for descending) or `OrderBy` objects.

```python
from aquilia.models.expression import F

Window(
    RowNumber(),
    partition_by=[F('department'), 'team'],
    order_by=['-salary']
)
```

### Frames

A frame defines a sliding subset of rows within the partition. You specify a frame using `WindowFrame`, `FrameType`, and `FrameBound`.

`FrameType` options are:
- `ROWS`: Based on physical offset of rows.
- `RANGE`: Based on logical value offsets.
- `GROUPS`: Based on peer groups.

`FrameBound` defines the start or end of the frame:
- `FrameBound.unbounded_preceding()`
- `FrameBound.current_row()`
- `FrameBound.unbounded_following()`
- `FrameBound.preceding(n)`
- `FrameBound.following(n)`

```python
from aquilia.models.window import WindowFrame, FrameType, FrameBound

# Frame from 2 rows before current row to current row
frame = WindowFrame(
    frame_type=FrameType.ROWS,
    start=FrameBound.preceding(2),
    end=FrameBound.current_row()
)

qs = await Sale.objects.annotate(
    rolling_sum=Window(Sum('amount'), order_by='date', frame=frame)
).all()
```

### Limitations

- **Filtering:** You cannot generally filter on a window function annotation directly in the `WHERE` clause, because SQL window functions are evaluated *after* `WHERE`. You often need to use CTEs or subqueries to achieve this.
- **Compatibility:** Requires SQLite 3.25+, PostgreSQL 8.4+, or MySQL 8.0+.

---

# PAGE: /docs/models/cte  
## Title: Common Table Expressions

Common Table Expressions (CTEs) are named temporary result sets that exist within the scope of a single SQL statement. They are often used to simplify complex queries by breaking them down into more readable components, or to reuse a subquery multiple times.

### Defining CTEs

In Aquilia, you can turn any QuerySet into a CTE using `.cte(name)`.

```python
# Create a CTE for active users
active_users_qs = User.objects.filter(is_active=True)
active_users_cte = active_users_qs.cte('active_users')
```

### Using CTEs

To use a CTE in your main query, register it with `.with_cte()`.

```python
# Use the CTE in a subsequent query
qs = await User.objects.with_cte(active_users_cte).filter(
    id__in=active_users_cte.queryset.values('id')
).all()
```

You can register multiple CTEs at once:

```python
Q.with_cte(cte1, cte2)
```

### Referencing CTE Columns

When writing raw expressions or advanced queries against a CTE, you can reference its columns using `CTECol`:

```python
col = active_users_cte.col('id')
# Renders as: "active_users"."id"
```

### Common Patterns

A common use case for CTEs is the "Rank and Filter" pattern to work around window function limitations (e.g. selecting the "Top N" items per group).

```python
from aquilia.models.window import Window, Rank

# 1. Annotate ranks
ranked_qs = Item.objects.annotate(
    rank=Window(Rank(), partition_by='category', order_by='-price')
)

# 2. Make it a CTE
ranked_cte = ranked_qs.cte('ranked_items')

# 3. Filter on the rank in the outer query
# (Requires referencing the CTE directly or using raw SQL as Aquilia evolves full CTE ORM mapping)
```

**Compatibility:** Requires SQLite 3.8.3+, PostgreSQL 8.4+, or MySQL 8.0+.

---

# PAGE: /docs/models/recursive-cte
## Title: Recursive CTEs

Recursive CTEs are a powerful SQL feature used to query hierarchical data such as organizational charts, file system trees, or threaded comments. 

They consist of two parts:
1. **Anchor:** The base query that starts the recursion.
2. **Recursive term:** A query that references the CTE itself to find the next level of data.

### Using Q.recursive_cte()

Aquilia provides `.recursive_cte()` to build these structures:

```python
# Find all descendants of a comment (comment_id=1)
qs = Comment.objects.recursive_cte(
    name='comment_tree',
    anchor=lambda q: q.filter(id=1),
    recursive=lambda cte: Comment.objects.filter(parent_id=cte.col('id')),
    union_all=True
)

tree = await qs.all()
```

### How It Works

- `name`: The alias given to the recursive CTE.
- `anchor`: A lambda function taking a QuerySet builder, expected to return the base dataset.
- `recursive`: A lambda function that receives a `CTEReference` object. You use `cte.col('field')` to join the recursive term against the results accumulated so far.
- `union_all`: Defaults to `True` (`UNION ALL`). If `False`, uses `UNION` (which removes duplicates but is generally slower).

### Examples

**Folder Hierarchy / Paths:**

```python
# Getting all folders in a path recursively
folders = await Folder.objects.recursive_cte(
    'path_cte',
    anchor=lambda q: q.filter(parent_id__isnull=True),
    recursive=lambda cte: Folder.objects.filter(parent_id=cte.col('id'))
).all()
```

### Considerations

- **Depth Limits:** Infinite loops are possible if data contains cycles. Be careful with hierarchical data, or consider depth limiters.
- **Performance:** Recursive queries can be heavy on the database. Ensure appropriate indexes are on the join columns (e.g., `parent_id`).

---

# PAGE: /docs/models/bulk-operations
## Title: Bulk Operations

Bulk operations allow you to manipulate or fetch large amounts of data efficiently, minimizing database roundtrips and memory overhead.

### Bulk Creation

To insert multiple objects in a single query, use `.bulk_create()`. You can specify a `batch_size` to split massive lists into smaller, manageable INSERT statements.

```python
users = [User(name=f"User {i}") for i in range(10000)]
await User.objects.bulk_create(users, batch_size=1000)
```

### Bulk Update

You can update all rows matching a QuerySet in one go using `.update()`. This is significantly faster than saving objects individually. You can also use `F()` expressions for atomic updates.

```python
from aquilia.models import F

# Give everyone an active status
await User.objects.filter(last_login__gte=cutoff).update(is_active=True)

# Increment points using F() expressions
await User.objects.filter(team='A').update(points=F('points') + 10)
```

### Bulk Delete

`.delete()` removes all matching rows directly in the database. 

> [!WARNING]
> Bulk `delete()` and `update()` do **not** trigger `pre_save`, `post_save`, `pre_delete`, or `post_delete` signals. If you rely on signals, you must iterate and call `.save()` or `.delete_instance()` individually.

```python
deleted_count = await User.objects.filter(is_active=False).delete()
```

### Safe Creation and Fetching

Aquilia offers several methods to safely fetch or create records without race conditions:

- **`get_or_create(defaults, **lookup)`**: Tries to get the object; if it doesn't exist, creates it.
- **`update_or_create(defaults, **lookup)`**: Tries to get the object and updates it with `defaults`; if not found, creates it.
- **`find_or_create(defaults, create_defaults, **lookup)`**: Uses `INSERT ON CONFLICT DO NOTHING`. It is fully atomic and safe against Time-of-Check to Time-of-Use (TOCTOU) race conditions. Highly recommended over `get_or_create` for concurrent environments.

```python
# Atomic insert if not exists
user, created = await User.objects.find_or_create(
    username="alice",
    create_defaults={"email": "alice@co.com"}
)
```

### Identity Map and Unit of Work

Aquilia's ORM deliberately does **not** implement an identity map or a
deferred-flush unit of work, unlike session-oriented ORMs such as
SQLAlchemy (`Session`), Hibernate (`Persistence Context`), or Entity
Framework Core (`DbContext`).

**No identity map.** Fetching the same row twice returns two distinct
Python objects with independent state:

```python
user_a = await User.get(id=1)
user_b = await User.get(id=1)

assert user_a is not user_b
```

Mutating `user_a` has no effect on `user_b` until the change is saved and
`user_b` is re-fetched.

**No unit of work.** Each `.save()` persists immediately — there is no
deferred change batching or cross-entity flush planning:

```python
await user.save()
await profile.save()
await settings.save()
# each of the above is a separate, immediate write
```

`atomic()` gives you transactional consistency (all-or-nothing), but not
`Session.flush()`/`SaveChanges()`-style batching:

```python
async with atomic():
    await user.save()
    await profile.save()
```

This is a deliberate tradeoff, not a missing feature: a session-scoped
identity map and unit of work would require task-affinity tracking,
session lifecycle management, and cross-request state — all at odds with
an async-first framework where request handling routinely spans
concurrent tasks. Explicit, immediate persistence keeps behavior
predictable regardless of how your async code is scheduled.

### Fetching Large Datasets

When working with huge tables, `.all()` can consume too much memory by loading everything into RAM at once.

**`in_bulk(id_list, batch_size=999)`**
Fetches a list of IDs and returns a dictionary mapping the primary key to the model instance. Automatically batches queries.

```python
# Efficiently fetch a specific subset mapping
user_dict = await User.objects.in_bulk([1, 5, 20, 99])
print(user_dict[5].name)
```

**`iterator(chunk_size=1000)`**
Streams results asynchronously, only holding one chunk in memory at a time.

```python
# Memory-efficient iteration over millions of rows
async for user in User.objects.iterator(chunk_size=2000):
    await process_user(user)
```
