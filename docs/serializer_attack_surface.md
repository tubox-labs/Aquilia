# Aquilia Blueprint — Serializer Attack Surface Analysis

**Module:** `aquilia/blueprints/`  
**Focus:** Inbound (Cast/Seal) and Outbound (Mold/Extract) data pathways  

---

## 1. Attack Surface Map

### 1.1 Inbound Pipeline (Untrusted → Framework)

```
HTTP Request
    │
    ▼
bind_blueprint_to_request()          ← Entry Point #1
    │
    ├─► request.json()               ← JSON parsing (no size limit)
    ├─► request.form() → _unflatten  ← Form parsing (no depth limit)
    │
    ▼
Blueprint.__init__(data=...)         ← Raw data injection
    │
    ▼
Blueprint.is_sealed()                ← Validation pipeline
    │
    ├─► Phase 1: Facet.cast()        ← Type coercion per field
    ├─► Phase 2: Facet.seal()        ← Field-level validation
    ├─► Phase 3: seal_*() methods    ← Cross-field validation
    └─► Phase 4: validate()          ← Object-level validation
    │
    ▼
Blueprint.validated_data             ← Trusted data output
    │
    ▼
Blueprint.imprint()                  ← Model write-back
```

### 1.2 Outbound Pipeline (Model → Client)

```
Model Instance
    │
    ▼
Blueprint.__init__(instance=...)     ← Model binding
    │
    ▼
Blueprint.to_dict()                  ← Serialization
    │
    ├─► Facet.extract()              ← Attribute access
    ├─► Facet.mold()                 ← Output formatting
    ├─► Lens.mold()                  ← Relational traversal
    └─► Projection filter            ← Field subsetting
    │
    ▼
Dict/List output                     ← Response data
```

---

## 2. Entry Points

### 2.1 `bind_blueprint_to_request()` — Primary Attack Surface

**File:** `integration.py`  
**Risk Level:** CRITICAL  

This function is the primary integration point between untrusted HTTP input
and the Blueprint validation pipeline. It is called automatically by the
controller engine when a handler parameter is annotated with a Blueprint type.

**Attack vectors:**
- **Payload bomb**: Multi-GB JSON body → OOM before any validation
- **Content-Type confusion**: Non-JSON body interpreted as form data
- **Form key injection**: Dot-notated keys (`a.b.c.d...`) create deep nesting
- **DI parameter injection**: Query/Header facets bypass Blueprint validation

### 2.2 `Blueprint.__init__(data=...)` — Direct Instantiation

**File:** `core.py`  
**Risk Level:** HIGH  

When developers instantiate Blueprints directly (not through the integration
layer), there are zero pre-processing safeguards.

**Attack vectors:**
- **Arbitrary data injection**: No type checking on `data` parameter
- **Context manipulation**: `context` dict is trusted without validation
- **Many-mode abuse**: `many=True` with million-element list

### 2.3 `Blueprint.imprint()` — Write-Back Attack Surface

**File:** `core.py`  
**Risk Level:** HIGH  

The imprint mechanism writes validated data back to ORM models. Even after
validation, the write-back path has risks.

**Attack vectors:**
- **Mass assignment**: Extra fields passed through if no explicit rejection
- **FK manipulation**: `{field}_id` source mapping could write to unexpected columns
- **Batch write amplification**: `_imprint_many()` with large lists

---

## 3. Facet-Level Attack Vectors

### 3.1 TextFacet — String Processing Attacks

| Vector | Mechanism | Impact |
|--------|-----------|--------|
| ReDoS | `pattern` parameter with catastrophic regex | CPU exhaustion |
| Null bytes | `str(value)` doesn't strip `\x00` | DB injection, log injection |
| Unicode normalization | No NFKC normalization | Homograph attacks, bypass |
| Oversized strings | No default max_length | Memory exhaustion |
| `__str__` side effects | `str(value)` on arbitrary objects | Code execution |

### 3.2 IntFacet / FloatFacet — Numeric Attacks

| Vector | Mechanism | Impact |
|--------|-----------|--------|
| NaN injection | `float("nan")` passes cast | Logic bypass, comparison bugs |
| Infinity | `float("inf")` passes cast | Division errors, OOM in math |
| Overflow | Very large integers | Memory/CPU exhaustion |
| Boolean confusion | `True`/`False` as int | Rejected for int, but accepted for float |

### 3.3 ListFacet — Collection Attacks

| Vector | Mechanism | Impact |
|--------|-----------|--------|
| Nested bomb | `[[[[[[...]]]]]]` | Stack overflow |
| Length amplification | Million-element list | Memory exhaustion |
| Type confusion | Non-list iterables | Unexpected behavior |
| Child cast cascade | Error accumulation in large lists | Slow validation |

### 3.4 DictFacet — Object Attacks

| Vector | Mechanism | Impact |
|--------|-----------|--------|
| Hash collision | Many keys with same hash prefix | O(n²) degradation |
| Key explosion | Millions of unique keys | Memory exhaustion |
| Thread-safety race | `value_facet.name` mutation | Cross-request data leakage |
| Deep nesting | Nested dicts via value_facet | Stack overflow |

### 3.5 JSONFacet — Arbitrary Data Attacks

| Vector | Mechanism | Impact |
|--------|-----------|--------|
| Type confusion | Any Python object accepted | Unpredictable downstream behavior |
| Stored XSS | `<script>` in JSON values | Client-side code execution |
| Deep nesting | 10000-level nested structure | Stack overflow in JSON serializer |
| Circular references | Self-referencing objects | Infinite loop in serialization |

### 3.6 NestedBlueprintFacet — Recursive Attacks

| Vector | Mechanism | Impact |
|--------|-----------|--------|
| Depth bomb | Self-referential Blueprint tree | Stack overflow |
| N+1 validation | Nested Blueprints trigger full pipeline | CPU exhaustion |
| Error amplification | Nested errors create large error dicts | Memory exhaustion |

### 3.7 PolymorphicFacet — Ambiguity Attacks

| Vector | Mechanism | Impact |
|--------|-----------|--------|
| Exhaustive matching | Value tried against all choices | CPU waste |
| Error accumulation | All choice errors collected in memory | Memory waste |
| Type confusion | Ambiguous value matches wrong choice | Logic bypass |

---

## 4. Integration-Level Attack Vectors

### 4.1 Controller Auto-Binding

When the controller engine detects a Blueprint type annotation:
```python
@post("/users")
async def create_user(self, user: UserBlueprint):
    ...
```

The engine calls `bind_blueprint_to_request()` automatically. There is
**no opportunity** for the developer to add custom pre-validation logic
between HTTP parsing and Blueprint instantiation.

### 4.2 DI Parameter Injection

`bind_blueprint_to_request()` extracts Query/Header parameters and injects
them into the Blueprint's data dict:

```python
if isinstance(default_val, Query):
    val = request.query_param(param_name)
    data[name] = val
```

This means an attacker can override Blueprint field values through query
parameters or headers, even if those fields are meant to come from the body.

### 4.3 Form Data Unflattening

The `_unflatten_dict()` function converts dot-notated form keys:
```
user.address.city=Paris → {"user": {"address": {"city": "Paris"}}}
```

With no depth limit, an attacker can create keys like:
```
a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a.a=x  (1000 levels)
```

---

## 5. Outbound Attack Vectors

### 5.1 Information Disclosure via Facet.extract()

The `extract()` method uses `getattr()` to traverse dotted paths:
```python
for part in parts:
    obj = getattr(obj, part, None)
```

If the source path is misconfigured or controllable (unlikely but possible
through dynamic Blueprint construction), this could access unintended model
attributes.

### 5.2 Lens Cycle Amplification

Although Lens has cycle detection, the depth limit (default 3) means that
in a deeply connected object graph, each level spawns a full Blueprint
mold operation. This is an amplification vector for response time attacks.

### 5.3 Projection Bypass

If projection names are derived from user input (e.g., `?projection=admin`),
an attacker might access field subsets not intended for their role.

---

## 6. Severity Matrix

| Attack Category | Likelihood | Impact | Overall Risk |
|----------------|------------|--------|--------------|
| Payload bomb (body size) | HIGH | CRITICAL | **CRITICAL** |
| eval() code execution | LOW-MEDIUM | CRITICAL | **CRITICAL** |
| Mass assignment | HIGH | HIGH | **HIGH** |
| NaN/Inf injection | MEDIUM | HIGH | **HIGH** |
| ReDoS | MEDIUM | MEDIUM | **MEDIUM** |
| Thread-safety race | LOW | HIGH | **MEDIUM** |
| Recursive nesting bomb | MEDIUM | MEDIUM | **MEDIUM** |
| Hash collision DoS | LOW | MEDIUM | **LOW-MEDIUM** |
| Information disclosure | LOW | MEDIUM | **LOW** |

---

## 7. Recommendations

### Immediate (Pre-Production)
1. Enforce body size limit in `bind_blueprint_to_request()`
2. Remove `eval()` from annotation introspection
3. Add unknown field rejection capability
4. Add NaN/Infinity rejection in FloatFacet

### Short-Term
5. Add ReDoS protection for TextFacet patterns
6. Add key count limits for DictFacet
7. Add nesting depth limits for NestedBlueprintFacet
8. Fix DictFacet thread-safety issue

### Medium-Term
9. Add JSONFacet depth/type restrictions
10. Add null byte stripping in TextFacet
11. Add Unicode normalization option
12. Add projection access control integration

---

*End of Serializer Attack Surface Analysis — Phase 10*
