# Aquilia ORM — Security Patterns

**Version**: 1.0.1 | Phase 9 Security Audit  

---

## 1. Parameterized Query Pattern

**Principle**: All user values MUST flow through parameterized `?` placeholders.

### ✅ Correct Pattern

```python
# Via QuerySet (automatic)
await User.objects.filter(email=user_input).all()

# Via where() with params
await User.objects.where('"age" > ?', user_age).all()

# Via F() + Value() expressions
await Product.objects.update(price=F("price") * Value(1.1))
```

### ❌ Anti-Pattern

```python
# NEVER interpolate user input into SQL strings
await User.objects.where(f'"email" = \'{user_input}\'').all()  # INJECTION!

# NEVER use f-strings for SQL construction
sql = f'SELECT * FROM users WHERE email = "{user_input}"'  # INJECTION!
```

---

## 2. Identifier Validation Pattern

**Principle**: All identifiers (field names, column names, function names)
MUST be validated before inclusion in SQL.

### Implementation

```python
import re

_SAFE_FIELD_RE = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')

def _validate_field_name(name: str, context: str) -> None:
    if not _SAFE_FIELD_RE.match(name):
        raise QueryFault(
            model="<query>",
            operation=context,
            reason=f"Invalid field name: {name!r}. "
                   "Field names must be alphanumeric with underscores only.",
        )
```

### Coverage

All ORM methods that accept field/column names now validate them:
- `filter()`, `exclude()` — validate kwargs keys
- `order()` — already validated (pre-Phase 9)
- `group_by()`, `values()`, `only()`, `defer()` — newly validated
- `Q.update()` — validate column keys
- `Model.get(**filters)` — validate filter keys

---

## 3. LIKE Escape Pattern

**Principle**: LIKE metacharacters (`%`, `_`) in user values MUST be escaped
to prevent wildcard injection.

### Implementation

```python
def _escape_like(value: str) -> str:
    """Escape LIKE metacharacters for safe pattern matching."""
    return (
        value
        .replace('\\', '\\\\')  # Escape the escape char first
        .replace('%', '\\%')     # Escape percent
        .replace('_', '\\_')     # Escape underscore
    )
```

### Usage in Lookups

```python
class Contains(Lookup):
    def as_sql(self):
        escaped = _escape_like(str(self.value))
        return f'"{self.field}" LIKE ? ESCAPE \'\\\'', [f"%{escaped}%"]
```

---

## 4. DDL Guard Pattern

**Principle**: Raw SQL entry points MUST block DDL/DCL keywords to prevent
schema modification.

### Implementation

```python
_DANGEROUS_KEYWORDS_RE = re.compile(
    r'\b(DROP|ALTER|TRUNCATE|GRANT|REVOKE|EXEC|EXECUTE)\b',
    re.IGNORECASE
)

def _guard_ddl(sql: str, context: str) -> None:
    if _DANGEROUS_KEYWORDS_RE.search(sql):
        raise QueryFault(
            model="<raw>",
            operation=context,
            reason="DDL/DCL statements are not allowed. "
                   "Use database engine directly for schema operations.",
        )
```

### Coverage

- `Q.where()` — guards clause
- `Q.having()` — guards clause (when no params)
- `Model.raw()` — guards entire SQL
- `RawSQL.__init__()` — raises instead of warning

---

## 5. Expression Type Safety Pattern

**Principle**: SQL function names and type names MUST be validated against
whitelists.

### Function Name Validation

```python
_SAFE_FUNC_RE = re.compile(r'^[A-Z_][A-Z0-9_]*$', re.IGNORECASE)

class Func(Expression):
    def __init__(self, function: str, *args):
        if not _SAFE_FUNC_RE.match(function):
            raise QueryFault(
                model="<expression>",
                operation="Func",
                reason=f"Invalid function name: {function!r}",
            )
```

### SQL Type Validation

```python
_SAFE_TYPE_RE = re.compile(
    r'^[A-Z][A-Z0-9_ ]*(?:\([0-9]+(?:\s*,\s*[0-9]+)?\))?$',
    re.IGNORECASE
)

class Cast(Expression):
    def __init__(self, expression, output_type: str):
        if not _SAFE_TYPE_RE.match(output_type):
            raise QueryFault(
                model="<expression>",
                operation="Cast",
                reason=f"Invalid SQL type: {output_type!r}",
            )
```

---

## 6. Transaction Safety Pattern

**Principle**: Transaction configuration parameters MUST be whitelisted.

```python
_ALLOWED_ISOLATION_LEVELS = {
    "READ UNCOMMITTED",
    "READ COMMITTED",
    "REPEATABLE READ",
    "SERIALIZABLE",
}

class Atomic:
    async def __aenter__(self):
        if self._isolation:
            upper = self._isolation.upper().strip()
            if upper not in _ALLOWED_ISOLATION_LEVELS:
                raise QueryFault(
                    model="(transaction)",
                    operation="atomic",
                    reason=f"Invalid isolation level: {self._isolation!r}",
                )
```

---

## 7. Signal Safety Pattern

**Principle**: Security-critical signal handlers MUST NOT silently fail.

```python
# For audit-critical signals, use raise_on_error=True
@pre_delete.connect
async def audit_delete(sender, instance, **kwargs):
    # This MUST succeed for compliance
    await AuditLog.create(
        action="delete",
        model=sender.__name__,
        pk=instance.pk,
    )
```

---

## 8. Serialization Safety Pattern

**Principle**: Use `to_dict(exclude=[...])` to prevent sensitive field leakage.

```python
class User(Model):
    name = CharField(max_length=150)
    email = EmailField()
    password_hash = CharField(max_length=255)
    
    def to_api_dict(self):
        return self.to_dict(exclude=["password_hash"])
```

---

## 9. Bulk Operation Safety Pattern

**Principle**: Bulk operations skip validation. Use with caution.

```python
# ✅ Correct: Validate before bulk_create
validated = []
for data in raw_data:
    instance = User(**data)
    instance.full_clean()  # Validates
    validated.append(data)
await User.bulk_create(validated)

# ❌ Risky: Skip validation
await User.bulk_create(raw_data)  # No validation!
```

---

## 10. Query Complexity Safety Pattern

**Principle**: Limit result set sizes for user-facing queries.

```python
# Always use limit() for user-facing endpoints
MAX_PAGE_SIZE = 100

async def list_users(page: int = 1, size: int = 20):
    size = min(size, MAX_PAGE_SIZE)
    return await User.objects.filter(active=True) \
        .order("-created_at") \
        .limit(size) \
        .offset((page - 1) * size) \
        .all()
```

---

*End of Security Patterns*
