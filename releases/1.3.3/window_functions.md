# Window Functions — Aquilia v1.3.3

Window functions compute a value for each row relative to a *window* of
related rows, without collapsing rows the way `GROUP BY` aggregates do.
They appear as `FUNC() OVER (PARTITION BY ... ORDER BY ...)` in SQL.

---

## Core API

### `Window(expression, *, partition_by, order_by, frame)`

The top-level wrapper. Takes any window function or aggregate and attaches an
`OVER (...)` clause to it.

```python
from aquilia.models import Window, Sum
from aquilia.models.window import Rank, DenseRank, RowNumber
```

**Arguments**

| Argument | Type | Description |
|---|---|---|
| `expression` | `Expression` | Window function (`Rank()`) or aggregate (`Sum("amount")`) |
| `partition_by` | `str \| F \| list[str \| F] \| None` | Columns to partition by |
| `order_by` | `str \| OrderBy \| list \| None` | Ordering inside the window (prefix `-` for DESC) |
| `frame` | `WindowFrame \| None` | Optional ROWS/RANGE frame clause |

---

## Window Functions

### Ranking

```python
# RANK() — gaps after ties
rank = Window(Rank(), partition_by=["dept"], order_by="-salary")

# DENSE_RANK() — no gaps
dense = Window(DenseRank(), partition_by=["dept"], order_by="-salary")

# ROW_NUMBER() — unique sequential integers
row_num = Window(RowNumber(), order_by="created_at")
```

Generated SQL:
```sql
RANK() OVER (PARTITION BY "dept" ORDER BY "salary" DESC)
DENSE_RANK() OVER (PARTITION BY "dept" ORDER BY "salary" DESC)
ROW_NUMBER() OVER (ORDER BY "created_at" ASC)
```

### Distribution

```python
from aquilia.models.window import Ntile

# Divide into 4 quartiles
quartile = Window(Ntile(4), order_by="-score")
```

```sql
NTILE(4) OVER (ORDER BY "score" DESC)
```

### Offset Functions

```python
from aquilia.models.window import Lag, Lead

# Previous row's value (1 row behind)
prev_score = Window(Lag("score"), order_by="created_at")

# Previous row with offset and default
prev_score = Window(Lag("score", offset=2, default=0), order_by="created_at")

# Next row's value (1 row ahead)
next_score = Window(Lead("score"), order_by="created_at")
```

```sql
LAG("score", 1) OVER (ORDER BY "created_at" ASC)
LAG("score", 2, ?) OVER (ORDER BY "created_at" ASC)  -- [0]
LEAD("score", 1) OVER (ORDER BY "created_at" ASC)
```

### Value Functions

```python
from aquilia.models.window import FirstValue, LastValue, NthValue

# First value in the window
first = Window(FirstValue("salary"), partition_by=["dept"], order_by="salary")

# Last value in the window
last = Window(LastValue("salary"), partition_by=["dept"], order_by="salary")

# Nth value (2nd highest in partition)
second = Window(NthValue("salary", 2), partition_by=["dept"], order_by="-salary")
```

### Aggregate Windows (Running Totals / Moving Averages)

Any existing Aquilia aggregate works inside `Window(...)`:

```python
from aquilia.models import Sum, Avg, Count, Max, Min

# Running total
running_total = Window(Sum("amount"), order_by="created_at")

# Cumulative average
cum_avg = Window(Avg("score"), partition_by=["country"], order_by="created_at")

# Count of rows so far in partition
cnt = Window(Count("id"), partition_by=["dept"], order_by="hired_at")
```

---

## Frame Clauses

Control exactly which rows fall in the window via `WindowFrame`.

```python
from aquilia.models.window import WindowFrame, FrameType, FrameBound

# Rows from start of partition to current row (default for running totals)
frame = WindowFrame(
    FrameType.ROWS,
    start=FrameBound.unbounded_preceding(),
    end=FrameBound.current_row(),
)

# 3-row moving window (1 before + current + 1 after)
frame = WindowFrame(
    FrameType.ROWS,
    start=FrameBound.preceding(1),
    end=FrameBound.following(1),
)

# Full partition (useful for LAST_VALUE correctness)
frame = WindowFrame(
    FrameType.ROWS,
    start=FrameBound.unbounded_preceding(),
    end=FrameBound.unbounded_following(),
)

sales = await Sale.objects.annotate(
    running=Window(
        Sum("amount"),
        order_by="created_at",
        frame=frame,
    )
).all()
```

Generated SQL:
```sql
SUM("amount") OVER (
  ORDER BY "created_at" ASC
  ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
)
```

---

## Practical Examples

### Leaderboard with rank per category

```python
from aquilia.models.window import Rank

products = await Product.objects.annotate(
    category_rank=Window(
        Rank(),
        partition_by=["category"],
        order_by="-revenue",
    )
).filter(category_rank__lte=3).order("category", "category_rank").all()
```

> Note: filtering on window annotations requires wrapping in a subquery on
> databases that evaluate `WHERE` before `SELECT`. Use `values()` + Python
> filtering, or a CTE, for cross-engine safety.

### 7-day moving average

```python
from aquilia.models import Avg
from aquilia.models.window import WindowFrame, FrameType, FrameBound

frame = WindowFrame(
    FrameType.ROWS,
    start=FrameBound.preceding(6),
    end=FrameBound.current_row(),
)

daily = await DailyMetric.objects.annotate(
    moving_avg=Window(
        Avg("value"),
        order_by="date",
        frame=frame,
    )
).order("date").all()
```

### Year-over-year comparison with Lag

```python
from aquilia.models.window import Lag

annual = await Revenue.objects.annotate(
    prev_year=Window(Lag("total", offset=1, default=0), order_by="year"),
).order("year").all()

for row in annual:
    pct = (row.total - row.prev_year) / max(row.prev_year, 1) * 100
    print(f"{row.year}: {pct:+.1f}%")
```

---

## Backend Compatibility

| Feature | SQLite | PostgreSQL | MySQL |
|---|---|---|---|
| `RANK`, `DENSE_RANK`, `ROW_NUMBER` | ≥ 3.25 | ≥ 8.4 | ≥ 8.0 |
| `NTILE` | ≥ 3.25 | ≥ 8.4 | ≥ 8.0 |
| `LAG`, `LEAD` | ≥ 3.25 | ≥ 8.4 | ≥ 8.0 |
| `FIRST_VALUE`, `LAST_VALUE` | ≥ 3.25 | ≥ 8.4 | ≥ 8.0 |
| `NTH_VALUE` | ≥ 3.25 | ≥ 11 | ≥ 8.0.2 |
| Frame clauses | ≥ 3.25 | ≥ 8.4 | ≥ 8.0 |
| `GROUPS` frame type | ≥ 3.28 | ≥ 11 | — |
