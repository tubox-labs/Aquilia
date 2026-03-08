# Aquilia Blueprint — Threat Model (STRIDE Analysis)

**Module:** `aquilia/blueprints/`  
**Methodology:** STRIDE per-element threat modeling  

---

## 1. System Boundaries

### Trust Boundaries

```
┌─────────────────────────────────────────────────────────┐
│                    UNTRUSTED ZONE                         │
│  HTTP Client → JSON Body / Form Data / Query Params       │
└───────────────────────────┬─────────────────────────────┘
                            │ Trust Boundary #1
┌───────────────────────────▼─────────────────────────────┐
│                  INTEGRATION LAYER                        │
│  bind_blueprint_to_request() — parsing + DI extraction    │
└───────────────────────────┬─────────────────────────────┘
                            │ Trust Boundary #2
┌───────────────────────────▼─────────────────────────────┐
│                  BLUEPRINT PIPELINE                        │
│  Cast → Seal → Validate → validated_data                  │
└───────────────────────────┬─────────────────────────────┘
                            │ Trust Boundary #3
┌───────────────────────────▼─────────────────────────────┐
│                    TRUSTED ZONE                           │
│  Imprint → Model → Database / Outbound Mold → Response    │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Data Flow Diagram (DFD)

### Level 0 — Context

```
[HTTP Client] ──request──► [Blueprint System] ──model ops──► [Database]
              ◄──response──                   ◄──query──
```

### Level 1 — Blueprint System

```
[HTTP Client]
    │
    ▼
(1) bind_blueprint_to_request
    │
    ├──► (2) JSON/Form Parse
    ├──► (3) DI Parameter Extract  
    │
    ▼
(4) Blueprint.__init__
    │
    ▼
(5) Blueprint.is_sealed
    │
    ├──► (5a) Facet.cast()         [per field]
    ├──► (5b) Facet.seal()         [per field]
    ├──► (5c) seal_*()             [cross-field]
    └──► (5d) validate()           [object-level]
    │
    ▼
(6) Blueprint.imprint             
    │
    ├──► (6a) _filter_imprint_data
    ├──► (6b) Model(**data)
    └──► (6c) Model.save()
```

---

## 3. STRIDE Analysis per Element

### 3.1 Element: `bind_blueprint_to_request()`

| Threat | Category | Description | Likelihood | Impact | Risk |
|--------|----------|-------------|------------|--------|------|
| T1 | **Spoofing** | Content-Type header spoofed to bypass JSON parsing path → form parsing with injection | MEDIUM | MEDIUM | MEDIUM |
| T2 | **Tampering** | Body contains extra fields not in Blueprint → mass assignment | HIGH | HIGH | **HIGH** |
| T3 | **Repudiation** | No logging of Blueprint validation failures | MEDIUM | LOW | LOW |
| T4 | **Info Disclosure** | Verbose error messages expose internal field names | LOW | MEDIUM | LOW |
| T5 | **DoS** | Oversized request body → OOM before validation | HIGH | CRITICAL | **CRITICAL** |
| T6 | **EoP** | DI Query/Header params override body fields → privilege escalation | MEDIUM | HIGH | **HIGH** |

### 3.2 Element: `Facet.cast()` — Type Coercion

| Threat | Category | Description | Likelihood | Impact | Risk |
|--------|----------|-------------|------------|--------|------|
| T7 | **Tampering** | NaN/Infinity in FloatFacet bypass range checks | MEDIUM | HIGH | **HIGH** |
| T8 | **Tampering** | `str(obj)` triggers `__str__` side effects | LOW | CRITICAL | MEDIUM |
| T9 | **DoS** | ReDoS via user-supplied regex pattern | MEDIUM | MEDIUM | **MEDIUM** |
| T10 | **DoS** | Extremely long Decimal string → CPU exhaustion | LOW | MEDIUM | LOW |
| T11 | **Tampering** | JSONFacet accepts arbitrary types | HIGH | HIGH | **HIGH** |

### 3.3 Element: `Blueprint.is_sealed()` — Validation

| Threat | Category | Description | Likelihood | Impact | Risk |
|--------|----------|-------------|------------|--------|------|
| T12 | **Tampering** | Extra input fields silently ignored → mass assignment | HIGH | HIGH | **HIGH** |
| T13 | **DoS** | `_seal_many()` with unbounded list → OOM | MEDIUM | HIGH | **HIGH** |
| T14 | **Tampering** | Partial mode skips required field checks | LOW | MEDIUM | LOW |
| T15 | **DoS** | Recursive NestedBlueprintFacet → stack overflow | MEDIUM | MEDIUM | **MEDIUM** |

### 3.4 Element: `Blueprint.imprint()` — Write-Back

| Threat | Category | Description | Likelihood | Impact | Risk |
|--------|----------|-------------|------------|--------|------|
| T16 | **Tampering** | `_filter_imprint_data` passes through unknown attrs | LOW | HIGH | MEDIUM |
| T17 | **EoP** | FK `_id` suffix allows writing to related model PKs | LOW | HIGH | MEDIUM |
| T18 | **DoS** | `_imprint_many()` creates N model instances | MEDIUM | MEDIUM | MEDIUM |

### 3.5 Element: `Blueprint.to_dict()` — Outbound Mold

| Threat | Category | Description | Likelihood | Impact | Risk |
|--------|----------|-------------|------------|--------|------|
| T19 | **Info Disclosure** | Projection name from user input → access hidden fields | MEDIUM | HIGH | **HIGH** |
| T20 | **Info Disclosure** | `extract()` with `getattr()` could traverse unexpected paths | LOW | MEDIUM | LOW |
| T21 | **DoS** | Lens depth amplification with large object graphs | LOW | MEDIUM | LOW |

### 3.6 Element: `introspect_annotations()` — Metaclass

| Threat | Category | Description | Likelihood | Impact | Risk |
|--------|----------|-------------|------------|--------|------|
| T22 | **EoP** | `eval()` on string annotations → arbitrary code execution | LOW-MEDIUM | CRITICAL | **CRITICAL** |
| T23 | **Tampering** | `_blueprint_registry` pollution → LazyBlueprintFacet resolves wrong class | LOW | HIGH | MEDIUM |
| T24 | **Info Disclosure** | Silent `except Exception: pass` hides misconfigurations | MEDIUM | LOW | LOW |

---

## 4. Threat Priority Matrix

### Critical Threats (Immediate Action Required)

| ID | Threat | Element | Mitigation |
|----|--------|---------|------------|
| T22 | eval() code execution | annotations.py | Replace with safe type resolution |
| T5 | Body size DoS | integration.py | Add body size limit |
| T13 | Unbounded list DoS | core.py | Add many items limit |

### High Threats (Pre-Production)

| ID | Threat | Element | Mitigation |
|----|--------|---------|------------|
| T2/T12 | Mass assignment | core.py | Add unknown field rejection |
| T7 | NaN/Infinity bypass | facets.py | Add isfinite() check |
| T11 | JSONFacet any type | facets.py | Add type/depth restrictions |
| T6 | DI param override | integration.py | Separate DI from body data |
| T19 | Projection disclosure | core.py | Validate projection names |

### Medium Threats (Short-Term)

| ID | Threat | Element | Mitigation |
|----|--------|---------|------------|
| T9 | ReDoS | facets.py | Regex complexity check |
| T15 | Recursive nesting | annotations.py | Depth tracking |
| T23 | Registry poisoning | core.py | Registry validation |

---

## 5. Attack Trees

### Tree 1: Remote Code Execution

```
[Achieve RCE]
    ├─► [Inject via eval()] (T22)
    │       ├─► Plugin system allows custom Blueprints
    │       ├─► Admin UI generates Blueprint class definitions
    │       └─► Template injection produces annotation strings
    │
    └─► [Inject via __str__()] (T8)
            └─► Direct Blueprint usage with attacker-controlled objects
```

### Tree 2: Denial of Service

```
[Achieve DoS]
    ├─► [Memory Exhaustion]
    │       ├─► Oversized JSON body (T5)
    │       ├─► Million-item list (T13)
    │       ├─► Million-key dict (DictFacet)
    │       └─► Deep nesting bomb (T15)
    │
    └─► [CPU Exhaustion]
            ├─► ReDoS attack (T9)
            ├─► Long decimal parsing (T10)
            └─► Recursive validation cascade (T15)
```

### Tree 3: Data Tampering

```
[Tamper with Data]
    ├─► [Mass Assignment] (T2/T12)
    │       ├─► Add is_admin=true to request body
    │       ├─► Add price=0 to request body
    │       └─► Override computed/read_only fields
    │
    ├─► [Logic Bypass] (T7)
    │       ├─► NaN in price → comparison always false
    │       └─► Infinity in amount → division by zero
    │
    └─► [Type Confusion] (T11)
            └─► JSONFacet stores executable payloads
```

---

## 6. Residual Risk Assessment

After applying all mitigations:

| Threat Category | Before | After | Residual |
|----------------|--------|-------|----------|
| Spoofing | MEDIUM | LOW | Content-Type check added |
| Tampering | HIGH | LOW | Unknown field rejection, NaN check |
| Repudiation | MEDIUM | MEDIUM | Logging not in scope |
| Info Disclosure | MEDIUM | LOW | Projection validation |
| Denial of Service | CRITICAL | LOW | Size/depth/count limits |
| Elevation of Privilege | CRITICAL | LOW | eval() removed, DI separated |

---

*End of Blueprint Threat Model — Phase 10*
