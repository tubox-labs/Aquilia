# Aquilia Blueprint — Deserialization Vulnerabilities

**Module:** `aquilia/blueprints/`  
**Focus:** Inbound data path — Cast + Seal phases  

---

## 1. Overview

Deserialization vulnerabilities occur when untrusted data is converted into
internal Python objects without adequate validation. In Aquilia's Blueprint
system, the **Cast** phase is the deserialization boundary — it converts raw
JSON/form values into typed Python objects.

This document catalogs every deserialization vulnerability in the Blueprint
module with proof-of-concept payloads and mitigation strategies.

---

## 2. Vulnerability Catalog

### DESER-001: Arbitrary Code Execution via `eval()` in Annotation Resolution

**Severity:** CRITICAL  
**File:** `annotations.py:895`  
**OWASP:** A03:2021 — Injection  

**Description:**
`introspect_annotations()` uses `eval()` to resolve PEP 563 string annotations.
The evaluation namespace includes all globals from every frame in the call stack.

**Proof of Concept:**
```python
# If an attacker can influence class annotations:
evil_annotation = "__import__('subprocess').check_output('id', shell=True)"

# This gets eval'd during class creation
class VulnerableBlueprint(Blueprint):
    __annotations__ = {"cmd": evil_annotation}
```

**Attack Prerequisite:** Attacker must be able to define or influence Blueprint
class annotations. This is realistic in:
- Plugin/extension systems that allow user-defined schemas
- Admin interfaces that generate Blueprints from configuration
- Template engines that produce Python class definitions

**Mitigation:**
- Replace `eval()` with `typing.get_type_hints()` (safe, built-in)
- Fall back to AST-based parsing with type allowlist
- Never execute arbitrary strings as Python code

---

### DESER-002: Unbounded JSON Deserialization (Memory Exhaustion)

**Severity:** CRITICAL  
**File:** `integration.py:103`  
**OWASP:** A05:2021 — Security Misconfiguration  

**Description:**
`bind_blueprint_to_request()` calls `await request.json()` without any body
size limit. The entire request body is loaded into memory before any Blueprint
validation occurs.

**Proof of Concept:**
```bash
# 1GB JSON payload
python -c "print('[' + ','.join(['1']*100000000) + ']')" | \
  curl -X POST http://target/api/users \
    -H 'Content-Type: application/json' \
    --data-binary @-
```

**Impact:** Server OOM, process crash, denial of service.

**Mitigation:**
- Check `Content-Length` header before parsing
- Implement streaming JSON parser with size limit
- Default max body size: 10MB (configurable)

---

### DESER-003: Type Confusion via `str()` Coercion

**Severity:** MEDIUM  
**File:** `facets.py:275`  
**OWASP:** A03:2021 — Injection  

**Description:**
`TextFacet.cast()` calls `str(value)` on non-string inputs. If an attacker
can pass a Python object with a malicious `__str__()` method (possible in
direct Blueprint usage, less likely via HTTP JSON), this triggers arbitrary
code execution.

**Proof of Concept:**
```python
class Evil:
    def __str__(self):
        import os
        os.system("id")
        return "innocent"

bp = UserBlueprint(data={"name": Evil()})
bp.is_sealed()  # Triggers Evil.__str__()
```

**Attack Prerequisite:** Attacker must be able to inject Python objects
(not just JSON primitives) into Blueprint data. This is possible when
Blueprints are used internally (not just for HTTP parsing).

**Mitigation:**
- Check `isinstance(value, (str, int, float, bool))` before `str()` coercion
- Reject non-primitive types in TextFacet.cast()

---

### DESER-004: NaN/Infinity Injection

**Severity:** HIGH  
**File:** `facets.py:495`  
**OWASP:** A03:2021 — Injection  

**Description:**
`FloatFacet.cast()` converts values to float without checking for special
IEEE 754 values. JSON doesn't define NaN/Infinity, but some JSON parsers
accept them, and direct Blueprint usage allows them.

**Proof of Concept:**
```python
bp = PriceBlueprint(data={"price": float("nan")})
bp.is_sealed()  # Passes!

# Downstream:
price = bp.validated_data["price"]
assert price == price  # FALSE! NaN != NaN
```

**Impact:**
- Comparison logic breaks (`NaN != NaN`)
- Sum/average calculations produce NaN
- Database may reject or silently store invalid values
- Division by infinity produces 0.0, breaking business logic

**Mitigation:**
- Add `math.isfinite()` check after `float()` conversion
- Reject NaN, Infinity, and -Infinity

---

### DESER-005: Recursive Nesting Bomb

**Severity:** MEDIUM  
**File:** `annotations.py:285`  
**OWASP:** A05:2021 — Security Misconfiguration  

**Description:**
`NestedBlueprintFacet.cast()` recursively instantiates child Blueprints.
Self-referential schemas (e.g., tree/comment threads) allow crafted input
to cause deep recursion.

**Proof of Concept:**
```python
class TreeBlueprint(Blueprint):
    name: str
    children: list["TreeBlueprint"] = Field(default_factory=list)

# Deeply nested payload:
payload = {"name": "root"}
current = payload
for _ in range(1000):
    child = {"name": "child", "children": []}
    current["children"] = [child]
    current = child

bp = TreeBlueprint(data=payload)
bp.is_sealed()  # RecursionError!
```

**Mitigation:**
- Track nesting depth during cast operations
- Default max depth: 32 (configurable per Blueprint)

---

### DESER-006: Dict Key Explosion

**Severity:** MEDIUM  
**File:** `facets.py:835`  
**OWASP:** A05:2021 — Security Misconfiguration  

**Description:**
`DictFacet.cast()` accepts dictionaries with unlimited key counts. Each key
triggers a `value_facet.cast()` call if configured.

**Proof of Concept:**
```python
payload = {"metadata": {f"key_{i}": f"val_{i}" for i in range(1_000_000)}}
bp = ConfigBlueprint(data=payload)
bp.is_sealed()  # 1M facet.cast() calls, massive memory
```

**Mitigation:**
- Add `max_keys` parameter to DictFacet (default 1000)

---

### DESER-007: List Length Amplification

**Severity:** HIGH  
**File:** `core.py:715`  
**OWASP:** A05:2021 — Security Misconfiguration  

**Description:**
`Blueprint._seal_many()` iterates over all input items, creating a full
Blueprint instance per item with facet cloning.

**Proof of Concept:**
```python
payload = [{"name": f"user_{i}", "email": f"u{i}@x.com"} for i in range(100_000)]
bp = UserBlueprint(data=payload, many=True)
bp.is_sealed()  # 100K Blueprint instances, each with N facet clones
```

**Memory amplification:** If a Blueprint has 20 facets, 100K items creates
2M facet clones.

**Mitigation:**
- Add `MAX_MANY_ITEMS` limit (default 10,000)
- Configurable via `context["max_many_items"]`

---

### DESER-008: Form Data Unflatten Depth Bomb

**Severity:** MEDIUM  
**File:** `integration.py:75`  
**OWASP:** A05:2021 — Security Misconfiguration  

**Description:**
`_unflatten_dict()` splits form keys on `.` and creates nested dicts
without depth limits.

**Proof of Concept:**
```bash
curl -X POST http://target/api/users \
  -d "$(python -c "print('a' + '.a'*500 + '=x')")"
```

This creates a 500-level nested dictionary.

**Mitigation:**
- Limit unflatten depth to 10 levels (configurable)

---

### DESER-009: JSONFacet Unrestricted Types

**Severity:** HIGH  
**File:** `facets.py:875`  
**OWASP:** A04:2021 — Insecure Design  

**Description:**
`JSONFacet.cast()` accepts any value without type checking, depth checking,
or size checking. When used to store "flexible" data, this becomes a vector
for stored payloads.

**Proof of Concept:**
```python
# Deeply nested structure → stack overflow on JSON serialization
payload = {"data": {"a": None}}
current = payload["data"]
for _ in range(10000):
    current["a"] = {"b": None}
    current = current["a"]

bp = FlexBlueprint(data=payload)
bp.is_sealed()  # Passes!
json.dumps(bp.validated_data)  # RecursionError!
```

**Mitigation:**
- Add `max_depth` parameter (default 32)
- Add `allowed_types` parameter (default: JSON primitives only)
- Recursive depth check during cast

---

### DESER-010: Decimal Precision Attack

**Severity:** LOW  
**File:** `facets.py:555`  

**Description:**
`DecimalFacet.cast()` converts strings to Decimal. Extremely long decimal
strings consume disproportionate CPU time.

**Proof of Concept:**
```python
bp = PriceBlueprint(data={"price": "0." + "1" * 100000})
bp.is_sealed()  # Slow — Decimal parsing of 100K chars
```

**Mitigation:**
- Limit input string length before Decimal conversion (default 1000 chars)

---

## 3. Deserialization Defense Layers

### Current State (Before Fixes)

```
HTTP Input → JSON parse (NO LIMIT) → Blueprint init (NO CHECK) → 
  Cast (PARTIAL CHECK) → Seal (VALIDATION) → Validated Data
```

### Target State (After Fixes)

```
HTTP Input → Size Check → Content-Type Check → JSON parse (LIMITED) → 
  Unknown Field Check → Cast (TYPE SAFE) → Depth Check → 
  Seal (VALIDATION) → Sanitize → Validated Data
```

---

## 4. Cross-Reference Matrix

| Vuln ID | OWASP 2021 | CWE | Blueprint Component |
|---------|------------|-----|---------------------|
| DESER-001 | A03:Injection | CWE-94 | annotations.py |
| DESER-002 | A05:Misconfig | CWE-400 | integration.py |
| DESER-003 | A03:Injection | CWE-704 | facets.py (TextFacet) |
| DESER-004 | A03:Injection | CWE-20 | facets.py (FloatFacet) |
| DESER-005 | A05:Misconfig | CWE-674 | annotations.py |
| DESER-006 | A05:Misconfig | CWE-400 | facets.py (DictFacet) |
| DESER-007 | A05:Misconfig | CWE-400 | core.py |
| DESER-008 | A05:Misconfig | CWE-674 | integration.py |
| DESER-009 | A04:Design | CWE-20 | facets.py (JSONFacet) |
| DESER-010 | A05:Misconfig | CWE-400 | facets.py (DecimalFacet) |

---

*End of Deserialization Vulnerabilities Analysis — Phase 10*
