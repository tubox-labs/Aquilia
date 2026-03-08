# Aquilia Blueprint — Validation Engine Design

**Module:** `aquilia/blueprints/`  
**Focus:** Seal/validation system architecture  

---

## 1. Validation Architecture

Aquilia's Blueprint validation engine is a **5-phase, non-short-circuiting**
pipeline that separates concerns into distinct stages.

```
┌─────────────────────────────────────────────────────┐
│                 VALIDATION ENGINE                     │
│                                                      │
│  Phase 1: Cast        (per-facet type coercion)      │
│  Phase 2: Field Seal  (per-facet constraint check)   │
│  Phase 3: Cross-Seal  (inter-field relationships)    │
│  Phase 4: Validate    (object-level custom logic)    │
│  Phase 5: Async Seal  (I/O-bound checks)             │
│                                                      │
│  Error Strategy: Accumulate all, return as dict      │
└─────────────────────────────────────────────────────┘
```

---

## 2. Phase 1 + 2: Per-Facet Validation

### 2.1 Cast Phase

Each Facet implements `cast(value) → typed_value`:

| Facet | Input Type | Output Type | Coercion Logic |
|-------|-----------|-------------|----------------|
| TextFacet | any | str | `str(value)`, trim whitespace |
| IntFacet | any | int | `int(value)`, reject bool |
| FloatFacet | any | float | `float(value)`, reject NaN/Inf (after fix) |
| DecimalFacet | any | Decimal | `Decimal(str(value))` |
| BoolFacet | any | bool | Truthy/falsy string mapping |
| DateFacet | str/date | date | `date.fromisoformat()` |
| DateTimeFacet | str/datetime | datetime | `datetime.fromisoformat()` |
| TimeFacet | str/time | time | `time.fromisoformat()` |
| UUIDFacet | str/UUID | UUID | `uuid.UUID(str(value))` |
| ListFacet | list/tuple | list | Recursive child cast |
| DictFacet | dict | dict | Key validation + value cast |
| JSONFacet | any | any | Pass-through (depth-limited after fix) |
| EmailFacet | str | str | TextFacet cast + lowercase |
| URLFacet | str | str | TextFacet cast |
| ChoiceFacet | any | any | Pass-through (seal validates) |

### 2.2 Seal Phase

Each Facet implements `seal(cast_value) → validated_value`:

| Facet | Constraints Checked |
|-------|-------------------|
| TextFacet | min_length, max_length, pattern, allow_blank |
| IntFacet | min_value, max_value |
| FloatFacet | min_value, max_value |
| DecimalFacet | min_value, max_value, max_digits, decimal_places |
| EmailFacet | Regex pattern match |
| URLFacet | Regex pattern match |
| SlugFacet | `^[-a-zA-Z0-9_]+$` |
| IPFacet | `ipaddress.ip_address()` |
| ListFacet | min_items, max_items + recursive child seal |
| DictFacet | Recursive value seal |
| ChoiceFacet | Value in valid_values set |
| PolymorphicFacet | Try each candidate, first success wins |

Plus: Custom validators from `Facet.validators` list are run in `seal()`.

---

## 3. Phase 3: Cross-Field Seal Methods

Discovered by metaclass via name convention:

```python
class OrderBlueprint(Blueprint):
    # Automatically discovered and called during Phase 3
    def seal_date_range(self, data: dict):
        if data["end"] < data["start"]:
            self.reject("end", "Must be after start")

    def seal_total_matches_items(self, data: dict):
        expected = sum(item["price"] * item["qty"] for item in data["items"])
        if abs(data["total"] - expected) > 0.01:
            self.reject("total", "Total doesn't match item sum")
```

**Discovery mechanism:**
```python
for attr_name in dir(cls):
    if attr_name.startswith("seal_"):
        cls._seal_methods.append(attr_name)
```

**Error reporting:** Cross-field seals use `self.reject(field, message)` which
raises `CastFault`. The pipeline catches it and adds to `self._errors[field]`.

---

## 4. Phase 4: Object-Level Validate

The `validate(data)` method is a hook for custom object-level logic:

```python
class TransferBlueprint(Blueprint):
    def validate(self, data):
        if data["source"] == data["destination"]:
            raise ValueError("Cannot transfer to same account")
        # Must return data (possibly modified)
        return data
```

**Return contract:** Must return the (possibly modified) data dict.
Returning `None` would set `_validated_data` to `None`, breaking imprint.

---

## 5. Phase 5: Async Seal

Only runs when `is_sealed_async()` is called:

```python
class UserBlueprint(Blueprint):
    async def async_seal_unique_email(self, data):
        from myapp.models import User
        if await User.objects.filter(email=data["email"]).exists():
            self.reject("email", "Already in use")
```

**Execution order:** All sync phases (1-4) complete first, then async
seals run. If sync phases fail, async seals are skipped.

---

## 6. Error Accumulation

### 6.1 Error Structure

```python
self._errors = {
    "field_name": ["Error message 1", "Error message 2"],
    "nested[0].field": ["Error for nested item"],
    "__all__": ["Object-level error"],
}
```

### 6.2 Error Response Format

Via `SealFault.as_response_body()`:
```json
{
    "domain": "BLUEPRINT",
    "code": "BP200",
    "message": "Blueprint validation failed",
    "errors": {
        "email": ["Invalid email address"],
        "age": ["Must be at least 0"],
        "__all__": ["At least one contact method required"]
    }
}
```

---

## 7. Validation Engine Improvements

### 7.1 Implemented (Phase 10)

| Improvement | Location | Description |
|------------|----------|-------------|
| NaN/Inf rejection | FloatFacet.cast() | `math.isfinite()` check |
| Unknown field rejection | is_sealed() | `extra_fields="reject"` mode |
| Body size limit | integration.py | `MAX_BODY_SIZE` constant |
| Many items limit | _seal_many() | `MAX_MANY_ITEMS` constant |
| ReDoS protection | TextFacet | Regex timeout + complexity check |
| DictFacet key limit | DictFacet.cast() | `max_keys` parameter |
| JSONFacet depth limit | JSONFacet.cast() | Recursive depth check |
| Nesting depth guard | NestedBlueprintFacet | `_nesting_depth` tracking |

### 7.2 Recommended Future Improvements

1. **Conditional validation**: Skip fields based on other field values
2. **Validation groups**: Named validation groups (e.g., "create" vs "update")
3. **Error codes**: Numeric error codes in addition to messages
4. **Field dependencies**: Declare inter-field dependencies explicitly
5. **Partial seal**: Validate only provided fields (not just skip missing)

---

*End of Validation Engine Design — Phase 10*
