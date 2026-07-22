# Aquilia v1.3.3 Release Notes — "Analytical Depths"

Aquilia v1.3.3 is a focused ORM release delivering three long-awaited
analytical query capabilities — **Window Functions**, **CTEs**, and
**Recursive CTEs** — implemented as first-class AST nodes in the expression
system, not thin raw-SQL wrappers. The release also ships two ORM bug fixes
discovered and verified during a production-grade audit of the models layer,
plus a follow-up round of security hardening and four new enterprise field
types (**MoneyField**, **EncryptedField**, **PointField**/**GeometryField**,
**GenericForeignKey**) driven by a senior-engineer assessment of the ORM.

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
5. [Security & Concurrency Hardening](security_hardening.md)
   - Widened raw-SQL keyword blocklist on `Q.where()`/`Q.having()`
   - `get_or_create()`/`update_or_create()` non-atomic `RuntimeWarning`
6. [Enterprise Field Types](enterprise_fields.md)
   - `MoneyField` — currency-aware decimal storage
   - `EncryptedField` — transparent field-level encryption
   - `PointField` / `GeometryField` — portable GeoJSON spatial fields
   - `GenericForeignKey` — polymorphic relations without a ContentType table
7. [Backend Compatibility Matrix](backends.md)
8. [Migration Guide](migration.md)

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

### MoneyField + EncryptedField: a wallet with a secret

```python
import os
from aquilia.models import Model, MoneyField, EncryptedField

EncryptedField.configure_encryption_key(os.environ["ENCRYPTION_KEY"])

class Wallet(Model):
    table = "wallets"

    balance = MoneyField(max_digits=12, decimal_places=2, currency="USD")
    recovery_phrase = EncryptedField(null=True)

wallet = await Wallet.create(balance="1000.00", recovery_phrase="correct horse battery staple")
```

### GenericForeignKey: comments on anything

```python
from aquilia.models import Model, AutoField, CharField, GenericForeignKey

class Comment(Model):
    table = "comments"
    id = AutoField(primary_key=True)
    content_type = CharField(max_length=255)
    object_id = CharField(max_length=255)
    target = GenericForeignKey("content_type", "object_id")

comment = Comment(body="Nice post!")
Comment.target.attach(comment, post)
await comment.save()

target = await Comment.target.resolve(comment)  # -> the Post instance
```

### Race-free upsert (and why get_or_create() now warns)

```python
# Warns RuntimeWarning: not atomic under concurrent access
user, created = await User.get_or_create(email="a@test.com", defaults={"name": "Alice"})

# Race-free — INSERT ... ON CONFLICT, no warning
user, created = await User.find_or_create(email="a@test.com", defaults={"name": "Alice"})
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

### New field types (`aquilia.models`)

| Field | Extends | Purpose |
|---|---|---|
| `MoneyField` | `DecimalField` | Currency-aware precise decimal storage |
| `EncryptedField` | `EncryptedMixin` + `TextField` | Transparent field-level encryption at rest |
| `PointField` / `GeometryField` | `JSONField` | Portable GeoJSON-backed spatial data |
| `GenericForeignKey` | *(none — not a `Field`)* | Polymorphic relation via a model-label + PK column pair |

See [Enterprise Field Types](enterprise_fields.md) for full usage.

---

## Fixes Shipped

| Issue | Root cause | Fix |
|---|---|---|
| `UUIDField(auto=True)` inserts NULL | `setdefault` no-op on pre-populated `kwargs` dict | Explicit `UNSET` sentinel check |
| Transaction depth leak / `id()` contamination | `WeakValueDictionary` integer keys never freed; `id()` reuse gives new task stale depth | Replaced with `contextvars.ContextVar[int]` |
| `Q.where()`/`Q.having()` raw-SQL blocklist incomplete/inconsistent | Two separate hand-maintained keyword sets, substring (not word-boundary) matching | One shared word-boundary regex guard; widened keyword set |
| `get_or_create()`/`update_or_create()` race silently possible | SELECT-then-INSERT/UPDATE with no runtime signal | `RuntimeWarning` pointing at `find_or_create()` |
| `EncryptedMixin.to_db()` `TypeError` on real save | Missing `dialect` keyword parameter, never exercised through `Model.save()` | Added `dialect: str = "sqlite"` param |

See [Security & Concurrency Hardening](security_hardening.md) for full root-cause detail on the last three.
