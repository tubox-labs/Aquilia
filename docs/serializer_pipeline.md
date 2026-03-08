# Aquilia Blueprint — Serializer Pipeline Design

**Module:** `aquilia/blueprints/`  
**Focus:** Cast → Seal → Mold → Imprint pipeline  

---

## 1. Pipeline Overview

The Aquilia Blueprint implements a 4-phase validation pipeline (5 with async):

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│  CAST    │──►│  SEAL    │──►│ VALIDATE │──►│ IMPRINT  │──►│  MODEL   │
│ (coerce) │   │ (check)  │   │ (cross)  │   │ (write)  │   │ (persist)│
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
     ▲                                              │
     │              Inbound (Request)               │
     │                                              ▼
┌──────────┐   ┌──────────┐
│ EXTRACT  │◄──│  MOLD    │
│ (access) │   │ (format) │
└──────────┘   └──────────┘
     ▲              │
     │   Outbound (Response)
     │              ▼
```

---

## 2. Phase Details

### 2.1 Phase 1: Cast (Type Coercion)

**Responsibility:** Convert raw JSON/form values to Python types.  
**Entry Point:** `Facet.cast(value) → typed_value`  
**Error Type:** `CastFault`  

```python
# Example: IntFacet.cast("42") → 42
# Example: DateFacet.cast("2024-01-15") → date(2024, 1, 15)
# Example: ListFacet.cast(["a", "b"]) → ["a", "b"] (with child cast)
```

**Cast Chain for Nested Types:**
```
ListFacet.cast([{...}, {...}])
    └─► for item: NestedBlueprintFacet.cast({...})
            └─► Blueprint(data={...}).is_sealed()
                    └─► TextFacet.cast("value")
                    └─► IntFacet.cast(42)
```

**Current Gaps:**
- No depth tracking in recursive casts
- `str(value)` in TextFacet triggers `__str__`
- No size limit before cast begins

### 2.2 Phase 2: Seal (Field Validation)

**Responsibility:** Validate cast values against field constraints.  
**Entry Point:** `Facet.seal(cast_value) → validated_value`  
**Error Type:** `CastFault` (reused for field-level errors)  

```python
# Example: TextFacet.seal("ab") → CastFault if min_length=3
# Example: IntFacet.seal(200) → CastFault if max_value=100
# Example: EmailFacet.seal("bad") → CastFault
```

**Seal includes custom validators:**
```python
for validator in self.validators:
    validator(value)  # Raises ValueError/TypeError on failure
```

### 2.3 Phase 3: Cross-Field Seal

**Responsibility:** Validate relationships between fields.  
**Entry Point:** `seal_*(validated_dict)` methods on Blueprint  
**Error Type:** `CastFault` (field-specific) or `ValueError` (general)  

```python
class OrderBlueprint(Blueprint):
    def seal_date_range(self, data):
        if data.get("end_date") and data["end_date"] < data["start_date"]:
            self.reject("end_date", "Must be after start date")
```

### 2.4 Phase 4: Object Validate

**Responsibility:** Final validation hook for custom logic.  
**Entry Point:** `Blueprint.validate(data) → data`  
**Error Type:** `SealFault`, `CastFault`, `ValueError`  

```python
class TransferBlueprint(Blueprint):
    def validate(self, data):
        if data["from_account"] == data["to_account"]:
            raise ValueError("Cannot transfer to same account")
        return data
```

### 2.5 Phase 5: Async Seal (Optional)

**Responsibility:** I/O-bound validation (DB checks, external APIs).  
**Entry Point:** `async_seal_*(validated_data)` methods  
**Trigger:** Only via `is_sealed_async()`  

```python
class UserBlueprint(Blueprint):
    async def async_seal_unique_email(self, data):
        exists = await User.objects.filter(email=data["email"]).exists()
        if exists:
            self.reject("email", "Email already in use")
```

---

## 3. Error Accumulation Strategy

The pipeline uses **non-short-circuiting** error accumulation:

```python
# All fields are cast/sealed even if early ones fail
self._errors = {}
for fname, facet in self._bound_facets.items():
    try:
        cast_value = facet.cast(raw)
    except CastFault as exc:
        self._errors.setdefault(fname, []).append(str(exc))
        continue  # Don't short-circuit — collect all errors
```

**Advantages:**
- Client gets all errors in one response (better UX)
- No round-trip validation loops

**Disadvantages:**
- CPU cost: all facets processed even when first fails
- Error dict can grow large with many fields + many items

---

## 4. Facet Lifecycle Hooks

```
Facet.__init__()     ← Configuration (min_length, max_value, etc.)
Facet.clone()        ← Blueprint instantiation (per-instance copy)
Facet.bind()         ← Attach to Blueprint with name
Facet.cast()         ← Inbound: raw → typed
Facet.seal()         ← Inbound: typed → validated
Facet.extract()      ← Outbound: instance → raw value
Facet.mold()         ← Outbound: raw → formatted
Facet.to_schema()    ← Schema: facet → JSON Schema dict
```

---

## 5. Pipeline Optimizations

### Current Performance Characteristics

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Facet clone | O(N) per facet | copy.copy() per field |
| Cast phase | O(N) per field | One pass |
| Seal phase | O(N) per field | One pass |
| Cross-field seal | O(M) methods | M = number of seal_* methods |
| Mold phase | O(N) per field | One pass |
| Projection filter | O(1) per field | frozenset lookup |

### Recommended Optimizations

1. **Lazy facet binding**: Only clone facets that will be used (based on projection)
2. **Cast+Seal fusion**: Combine cast and seal into single pass per facet
3. **Schema caching**: Cache to_schema() results per class+projection+mode
4. **Batch mold**: Vectorize mold operations for many=True lists

---

## 6. Comparison with DRF Pipeline

| Aspect | DRF Serializer | Aquilia Blueprint |
|--------|---------------|-------------------|
| Metaclass | SerializerMetaclass | BlueprintMeta |
| Field base | Field | Facet |
| Validation | is_valid() → 3 phases | is_sealed() → 5 phases |
| Async | No | Yes (Phase 5) |
| Projections | No (manual) | Built-in ProjectionRegistry |
| Lenses | No | Built-in depth-controlled Lens |
| Type annotations | No | Full PEP 604/563 support |
| Write-back | save() | imprint() (async) |
| Schema gen | Via drf-spectacular | Built-in to_schema() |

---

*End of Serializer Pipeline Design — Phase 10*
