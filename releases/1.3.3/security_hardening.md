# Security & Concurrency Hardening — Aquilia v1.3.3

Two ORM hardening fixes came out of a senior-engineer security assessment of
the ORM layer, in the same audit spirit as the [bug fixes](bugfixes.md) also
shipped in this release. Neither is a new vulnerability report — both close
gaps between documented behavior and what the code actually enforced.

---

## Fix 1 — Raw-SQL Keyword Blocklist Was Inconsistent and Incomplete

### Symptom

`Q.where()` and `Q.having()` are documented as low-level, developer-authored
raw-clause APIs — parameter binding (`?` placeholders) is the actual
injection defense, and both methods carry a secondary keyword-blocklist
guardrail on top. But the two guardrails disagreed with each other and both
had real gaps:

```python
# Before fix — all of these were ACCEPTED by .where(), i.e. NOT rejected
await User.objects.where("id = 1; DELETE FROM users")
await User.objects.where("id = 1; INSERT INTO users VALUES (...)")
await User.objects.where("id = 1 -- bypass rest of clause")
```

`.where()` only checked for `DROP`, `ALTER`, `TRUNCATE`, `EXEC`, `EXECUTE` —
via a trailing-space substring match, not even a proper identifier check.
`.having()` had a separate, wider set (`DROP`, `ALTER`, `TRUNCATE`, `EXEC`,
`EXECUTE`, `--`, `;`) but still missed `DELETE`/`INSERT`/`UPDATE`/`MERGE`,
and its substring match could false-positive on legitimate identifiers.

### Root Cause

Two independent, hand-maintained keyword sets, both under-scoped and neither
using word-boundary matching:

```python
# Before fix — query.py, Q.where()
_DANGEROUS_DDL = {"DROP ", "ALTER ", "TRUNCATE ", "EXEC ", "EXECUTE "}
for kw in _DANGEROUS_DDL:
    if kw in _upper:   # naive substring match
        raise SecurityFault(...)

# Before fix — query.py, Q.having() (different set, only when args is empty)
_DANGEROUS = {"DROP", "ALTER", "TRUNCATE", "EXEC", "EXECUTE", "--", ";"}
```

The trailing-space substring match in `.where()` also meant a column or
identifier containing the keyword as a prefix (e.g. a hypothetical
`"AIRDROP "` token) could match by accident — the check was neither
correct nor complete.

### Fix

One shared, word-boundary regex guard, used by both methods:

```python
# After fix — query.py
_UNSAFE_SQL_RE = re.compile(
    r"\b(DROP|ALTER|TRUNCATE|EXEC|EXECUTE|DELETE|INSERT|UPDATE|MERGE)\b|--|/\*|\*/|;",
    re.IGNORECASE,
)

def _reject_unsafe_clause(clause: str, *, code: str, context: str) -> None:
    match = _UNSAFE_SQL_RE.search(clause)
    if match:
        raise SecurityFault(
            code=code,
            message=f"Potentially unsafe {context} clause rejected: contains "
            f"'{match.group(0).strip()}'. Use parameterized values (?) for "
            f"user-supplied data.",
        )
```

`Q.where()` calls it unconditionally (unchanged, stricter behavior);
`Q.having()` calls it only when no bind params were supplied (unchanged
semantics — only the keyword set was widened). Word-boundary matching
(`\b...\b`) means `updated_at`, `deleted_flag`, and similar identifiers are
no longer false positives.

```python
# After fix
await User.objects.where("updated_at > ?", cutoff)         # OK — no false positive
await User.objects.where("id = 1; DELETE FROM users")      # SecurityFault
await User.objects.where("id = 1 -- bypass")                # SecurityFault
await User.objects.having("COUNT(*) > 0 UPDATE users")      # SecurityFault
```

> **Reminder:** this guard is a secondary net, not the injection defense.
> Always bind user-supplied values through `?` placeholders — never
> string-interpolate them into a raw clause, blocklist or not.

**File:** `aquilia/models/query.py`

### Regression Tests — `tests/test_orm_security.py::TestWhereHavingClauseGuard`

| Test | Coverage |
|---|---|
| `test_where_rejects_dml_and_ddl_keywords` | `DELETE`/`INSERT`/`UPDATE`/`MERGE`/`DROP` all rejected |
| `test_where_rejects_comment_markers` | `--`, `/*`, `*/` all rejected |
| `test_where_accepts_identifier_substrings` | `updated_at` passes — no false positive on `UPDATE` |
| `test_having_rejects_dml_keywords_without_params` | Same DML set rejected on `.having()` |
| `test_having_with_params_bypasses_keyword_scan` | Existing semantics preserved: keyword scan only runs when no bind params given |

---

## Fix 2 — `get_or_create()` / `update_or_create()` Silently Non-Atomic

### Symptom

Both methods were already documented as "not atomic" in their docstrings,
but nothing surfaced that fact at runtime. Under concurrent access, two
callers could both miss the initial `SELECT` and both attempt an `INSERT`,
risking a duplicate row or a unique-constraint violation — a classic
time-of-check-to-time-of-use (TOCTOU) race, invisible until it happened in
production.

```python
# Before fix — no signal that this can race under concurrency
user, created = await User.get_or_create(email="a@test.com", defaults={"name": "Alice"})
```

### Root Cause

`get_or_create()`/`update_or_create()` are, and always were, a plain
SELECT-then-INSERT/UPDATE:

```python
# base.py — unchanged control flow
instance = await cls.get_or_none(**lookup)
if instance is not None:
    return instance, False
create_data = {**lookup, **(defaults or {})}
instance = await cls.create(**create_data)
return instance, True
```

`find_or_create()` (already shipped, using `INSERT ... ON CONFLICT`) is the
race-free alternative — but a developer reaching for the more familiar
`get_or_create()` name had no runtime indication that they should reach for
the other one instead.

### Fix

Both methods now emit `RuntimeWarning` on every call:

```python
# After fix — base.py
warnings.warn(
    f"{cls.__name__}.get_or_create() is not atomic (SELECT-then-INSERT). "
    f"Under concurrent access this can race. Use find_or_create() for a "
    f"race-free INSERT ... ON CONFLICT upsert.",
    RuntimeWarning,
    stacklevel=2,
)
```

(`update_or_create()` gets the matching "SELECT-then-UPDATE-or-INSERT"
wording.) Fixed once, in the canonical `Model` classmethods
(`aquilia/models/base.py`) — `Manager.get_or_create()`/`update_or_create()`
and `Q.get_or_create()`/`update_or_create()` both forward into these, so all
three public entry points are covered by the single change.

```python
# After fix
import warnings

with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    user, created = await User.get_or_create(email="a@test.com", defaults={"name": "Alice"})
    assert any(issubclass(w.category, RuntimeWarning) for w in caught)

# Race-free alternative — does NOT warn
user, created = await User.find_or_create(
    email="a@test.com", create_defaults={"name": "Alice"}
)
```

**File:** `aquilia/models/base.py`

### Regression Tests — `tests/test_orm_concurrency_warnings.py`

| Test | Coverage |
|---|---|
| `test_get_or_create_warns` | `RuntimeWarning` raised, message matches "not atomic" |
| `test_update_or_create_warns` | Same, for `update_or_create()` |
| `test_find_or_create_does_not_warn` | Confirms the race-free path stays silent |
