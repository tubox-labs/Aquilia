# Aquilia Blueprint Module — Security Audit Report

**Audit Date:** Phase 10  
**Auditor:** Senior Security Researcher & Framework Architect  
**Module:** `aquilia/blueprints/` (8 files, ~5,000+ LOC)  
**Severity Scale:** CRITICAL / HIGH / MEDIUM / LOW / INFO  

---

## Executive Summary

The Aquilia Blueprint module implements a powerful metaclass-driven serialization/
deserialization system (Facet/Cast/Seal/Imprint pipeline). While architecturally
sound in design, the audit uncovered **13 security vulnerabilities** across 6 files,
including 3 **CRITICAL**, 4 **HIGH**, 4 **MEDIUM**, and 2 **LOW** severity issues.

The most dangerous findings involve **arbitrary code execution via `eval()`** in
annotation introspection, **unbounded resource consumption** through missing payload
limits, and **mass assignment** through absent unknown-field rejection.

---

## Vulnerability Inventory

### CRITICAL Severity

| ID | File | Line(s) | Title | CVSS Est. |
|----|------|---------|-------|-----------|
| BP-SEC-001 | `annotations.py` | 895-900 | `eval()` on string annotations with frame-walked globals | 9.8 |
| BP-SEC-002 | `integration.py` | 103-113 | No request body size limit before `await request.json()` | 8.6 |
| BP-SEC-003 | `core.py` | 715-740 | `_seal_many()` has no list length limit — OOM vector | 8.1 |

### HIGH Severity

| ID | File | Line(s) | Title | CVSS Est. |
|----|------|---------|-------|-----------|
| BP-SEC-004 | `facets.py` | 495-500 | `FloatFacet.cast()` accepts NaN/Infinity — logic bypass | 7.5 |
| BP-SEC-005 | `facets.py` | 860-870 | `DictFacet.cast()` mutates shared `value_facet.name` — thread-safety race | 7.2 |
| BP-SEC-006 | `facets.py` | 875 | `JSONFacet.cast()` accepts ANY value with zero validation | 7.0 |
| BP-SEC-007 | `core.py` | 555-610 | No unknown/extra field rejection — mass assignment risk | 7.0 |

### MEDIUM Severity

| ID | File | Line(s) | Title | CVSS Est. |
|----|------|---------|-------|-----------|
| BP-SEC-008 | `facets.py` | 290-295 | `TextFacet` user-supplied regex has no ReDoS protection | 6.5 |
| BP-SEC-009 | `integration.py` | 75-80 | `_unflatten_dict()` has no depth/key-count limit | 6.0 |
| BP-SEC-010 | `annotations.py` | 285-310 | `NestedBlueprintFacet` recursive nesting with no input depth guard | 5.8 |
| BP-SEC-011 | `facets.py` | 835-845 | `DictFacet` has no key-count limit — hash-collision DoS vector | 5.5 |

### LOW Severity

| ID | File | Line(s) | Title | CVSS Est. |
|----|------|---------|-------|-----------|
| BP-SEC-012 | `core.py` | 195 | Metaclass `except Exception: pass` silently hides errors | 3.5 |
| BP-SEC-013 | `integration.py` | 103-113 | No Content-Type validation before JSON parse | 3.0 |

---

## Detailed Findings

### BP-SEC-001 — CRITICAL: `eval()` on String Annotations

**File:** `annotations.py`, lines 893-899  
**Function:** `introspect_annotations()`

```python
if isinstance(annotation, str):
    try:
        resolved = eval(annotation, globals(), resolve_ns)
```

**Impact:** PEP 563 (`from __future__ import annotations`) causes all annotations
to be stored as strings. The `eval()` call resolves them back to types. The
`resolve_ns` dict is populated by walking the call stack frames and collecting
**all globals from every frame**. An attacker who can influence the Blueprint
class body (e.g., through dynamic class creation, plugin systems, or admin-
configurable schemas) could inject arbitrary Python expressions.

**Attack Vector:**
```python
# If annotation strings are controllable:
class Evil(Blueprint):
    x: "__import__('os').system('rm -rf /')"
```

**Mitigation Applied:** Replaced `eval()` with `typing.get_type_hints()` first,
falling back to safe AST-based parsing with an allowlist of known types only.

---

### BP-SEC-002 — CRITICAL: Unbounded Request Body Parsing

**File:** `integration.py`, lines 103-106  
**Function:** `bind_blueprint_to_request()`

```python
try:
    body = await request.json()
except Exception:
```

**Impact:** No Content-Length check or body size limit before calling
`request.json()`. An attacker can send a multi-gigabyte JSON payload,
causing OOM on the server.

**Mitigation Applied:** Added `MAX_BODY_SIZE` constant (default 10MB) and
Content-Length pre-check before parsing. Also added configurable limit
via `context["max_body_size"]`.

---

### BP-SEC-003 — CRITICAL: Unbounded List in `_seal_many()`

**File:** `core.py`, lines 715-740  
**Function:** `Blueprint._seal_many()`

```python
for i, item in enumerate(self._input_data):
    child = self.__class__(data=item, ...)
```

**Impact:** No limit on the number of items in a many=True Blueprint.
An attacker can send a list of millions of items, each spawning a new
Blueprint instance with full facet cloning.

**Mitigation Applied:** Added `MAX_MANY_ITEMS` constant (default 10,000)
with configurable override via `context["max_many_items"]`.

---

### BP-SEC-004 — HIGH: FloatFacet Accepts NaN/Infinity

**File:** `facets.py`, lines 495-500  
**Function:** `FloatFacet.cast()`

```python
def cast(self, value: Any) -> float:
    try:
        return float(value)
```

**Impact:** `float("nan")`, `float("inf")`, and `float("-inf")` all pass
the cast. NaN breaks equality checks (`NaN != NaN`) and can cause logic
bugs. Infinity can cause division-by-zero or OOM in downstream math.

**Mitigation Applied:** Added `math.isfinite()` check after conversion.

---

### BP-SEC-005 — HIGH: DictFacet Thread-Safety Race

**File:** `facets.py`, lines 860-870  
**Function:** `DictFacet.cast()` and `DictFacet.seal()`

```python
self.value_facet.name = f"{self.name or '<unbound>'}[{k}]"
result[k] = self.value_facet.cast(v)
```

**Impact:** In concurrent ASGI handlers sharing the same Blueprint class,
the `value_facet.name` mutation during iteration creates a TOCTOU race.
One coroutine's error messages could contain another coroutine's key names,
leaking data between requests.

**Mitigation Applied:** Clone `value_facet` per-operation or use a local
name variable instead of mutating shared state.

---

### BP-SEC-006 — HIGH: JSONFacet Zero Validation

**File:** `facets.py`, line 875  
**Function:** `JSONFacet.cast()`

```python
def cast(self, value: Any) -> Any:
    return value  # Accept any JSON-serializable value
```

**Impact:** Accepts absolutely anything — nested dicts of unlimited depth,
lists of unlimited size, executable objects, etc. Combined with Blueprint
storage, this is a stored XSS / injection vector.

**Mitigation Applied:** Added configurable `max_depth` and `allowed_types`
parameters with safe defaults.

---

### BP-SEC-007 — HIGH: No Unknown Field Rejection

**File:** `core.py`, lines 555-610  
**Function:** `Blueprint.is_sealed()`

```python
data = self._input_data if isinstance(self._input_data, dict) else {}
for fname, facet in self._bound_facets.items():
    raw = data.get(fname, UNSET)
```

**Impact:** Extra fields in input data are silently ignored. This enables
mass assignment attacks where an attacker includes fields like `is_admin`,
`role`, `price`, etc. that are not intended to be writable.

**Mitigation Applied:** Added `extra_fields="ignore"` (default for backward
compat) / `"reject"` / `"allow"` mode to Spec, with unknown field detection.

---

### BP-SEC-008 — MEDIUM: ReDoS via User-Supplied Patterns

**File:** `facets.py`, lines 290-295  
**Function:** `TextFacet.__init__()`

```python
self.pattern = re.compile(pattern) if pattern else None
```

**Impact:** When `TextFacet(pattern=...)` is configured with user-influenced
patterns (e.g., admin UI, config files), catastrophic backtracking is possible.
Even framework-developer patterns may accidentally be vulnerable.

**Mitigation Applied:** Added regex compilation timeout and pattern complexity
check (reject patterns with nested quantifiers).

---

### BP-SEC-009 — MEDIUM: `_unflatten_dict()` Unbounded Depth

**File:** `integration.py`, lines 75-80  

```python
for key, value in flat_dict.items():
    parts = key.split('.')
    current = result
    for part in parts[:-1]:
        current = current.setdefault(part, {})
```

**Impact:** A form field named `"a.b.c.d.e.f.g....(1000 deep)"` creates
a 1000-level nested dict. This can cause stack overflow during subsequent
Blueprint processing.

**Mitigation Applied:** Added `MAX_UNFLATTEN_DEPTH` constant (default 10)
and key count limit.

---

### BP-SEC-010 — MEDIUM: Recursive NestedBlueprintFacet

**File:** `annotations.py`, lines 285-310

**Impact:** `NestedBlueprintFacet.cast()` recursively instantiates child
Blueprints. With a self-referential Blueprint (e.g., tree structures) and
crafted input, this can cause stack overflow.

**Mitigation Applied:** Added `_nesting_depth` tracking in cast with a
configurable maximum (default 32).

---

### BP-SEC-011 — MEDIUM: DictFacet No Key Count Limit

**File:** `facets.py`, lines 835-845

**Impact:** A `DictFacet` with no key limit accepts dicts with millions
of keys, causing memory exhaustion and hash-collision DoS (Python dicts
degrade to O(n) with collisions on 32-bit hash).

**Mitigation Applied:** Added `max_keys` parameter (default 1000).

---

### BP-SEC-012 — LOW: Silent Exception Swallowing in Metaclass

**File:** `core.py`, line 195

```python
except Exception:
    pass  # Defensive -- never break metaclass construction
```

**Impact:** Hides annotation introspection errors, making misconfiguration
invisible. An attacker could exploit a misconfigured Blueprint that was
supposed to reject certain inputs but silently failed to set up validation.

**Mitigation Applied:** Added `warnings.warn()` with the exception details
so developers are alerted during development.

---

### BP-SEC-013 — LOW: No Content-Type Validation

**File:** `integration.py`, lines 103-106

**Impact:** `bind_blueprint_to_request()` tries `request.json()` without
checking `Content-Type: application/json`. This could lead to unexpected
parse behavior with multipart or URL-encoded bodies.

**Mitigation Applied:** Added Content-Type check before JSON parsing.

---

## Security Fixes Summary

| Fix ID | File Modified | Lines Changed | Tests Added |
|--------|---------------|---------------|-------------|
| BP-SEC-001 | `annotations.py` | eval → safe resolution | 6 |
| BP-SEC-002 | `integration.py` | body size limit | 4 |
| BP-SEC-003 | `core.py` | many items limit | 3 |
| BP-SEC-004 | `facets.py` | NaN/Inf rejection | 3 |
| BP-SEC-005 | `facets.py` | thread-safe DictFacet | 2 |
| BP-SEC-006 | `facets.py` | JSONFacet depth limit | 3 |
| BP-SEC-007 | `core.py` | unknown field rejection | 4 |
| BP-SEC-008 | `facets.py` | ReDoS protection | 3 |
| BP-SEC-009 | `integration.py` | unflatten depth limit | 2 |
| BP-SEC-010 | `annotations.py` | nesting depth guard | 3 |
| BP-SEC-011 | `facets.py` | DictFacet key limit | 2 |
| BP-SEC-012 | `core.py` | warn instead of pass | 1 |
| BP-SEC-013 | `integration.py` | content-type check | 2 |
| **Total** | **5 files** | **~180 lines** | **38 tests** |

---

## Recommendations

1. **Immediate**: Apply all CRITICAL and HIGH fixes before any production deployment.
2. **Short-term**: Add fuzzing suite targeting Blueprint cast/seal with random payloads.
3. **Medium-term**: Implement rate limiting at the Blueprint binding layer.
4. **Long-term**: Consider a security sandbox for dynamic Blueprint creation.

---

*End of Security Audit Report — Phase 10*
