# Aquilia Blueprint — Upgrade Plan

**Module:** `aquilia/blueprints/`  
**Scope:** Security fixes + architecture improvements  

---

## 1. Implementation Phases

### Phase A: Critical Security Fixes (Immediate)

| # | Fix | File | Risk | Tests |
|---|-----|------|------|-------|
| A1 | Replace `eval()` with safe annotation resolution | annotations.py | CRITICAL | 6 |
| A2 | Add request body size limit | integration.py | CRITICAL | 4 |
| A3 | Add many items limit in `_seal_many()` | core.py | CRITICAL | 3 |
| A4 | Add NaN/Infinity rejection in FloatFacet | facets.py | HIGH | 3 |
| A5 | Fix DictFacet thread-safety (value_facet.name) | facets.py | HIGH | 2 |
| A6 | Add JSONFacet depth/type restrictions | facets.py | HIGH | 3 |
| A7 | Add unknown field rejection mode | core.py | HIGH | 4 |

**Estimated effort:** 4-6 hours  
**Test count:** 25 new tests  
**Risk:** Low (all fixes are additive, backward compatible)  

### Phase B: Medium Security Fixes (Short-Term)

| # | Fix | File | Risk | Tests |
|---|-----|------|------|-------|
| B1 | ReDoS protection for TextFacet patterns | facets.py | MEDIUM | 3 |
| B2 | Unflatten depth limit | integration.py | MEDIUM | 2 |
| B3 | Nesting depth guard for NestedBlueprintFacet | annotations.py | MEDIUM | 3 |
| B4 | DictFacet key count limit | facets.py | MEDIUM | 2 |
| B5 | Metaclass warning instead of silent pass | core.py | LOW | 1 |
| B6 | Content-Type validation | integration.py | LOW | 2 |

**Estimated effort:** 2-3 hours  
**Test count:** 13 new tests  
**Risk:** Very low  

### Phase C: Architecture Improvements (Medium-Term)

| # | Improvement | File(s) | Impact |
|---|------------|---------|--------|
| C1 | Split facets.py into submodules | facets/ | Maintainability |
| C2 | Schema caching | core.py | Performance |
| C3 | Blueprint registry namespacing | core.py | Concurrency |
| C4 | Before/after hooks | core.py | Features |
| C5 | Discriminated unions | annotations.py | Features |
| C6 | Strict mode | core.py | Features |

**Estimated effort:** 2-3 weeks  
**Risk:** Medium (structural changes)  

---

## 2. Backward Compatibility

### 2.1 Breaking Changes: NONE

All security fixes are designed to be backward compatible:

- `extra_fields` defaults to `"ignore"` (current behavior)
- Body size limit defaults to 10MB (generous)
- Many items limit defaults to 10,000
- DictFacet max_keys defaults to 1,000
- JSONFacet max_depth defaults to 32
- ReDoS protection silently allows safe patterns

### 2.2 Deprecation Notices

- `eval()` path in `introspect_annotations()` → deprecated, replaced with safe resolution
- `JSONFacet` accepting arbitrary objects → deprecated in favor of restricted mode

---

## 3. Migration Guide

### 3.1 For Framework Users (Application Developers)

No action required. All fixes are backward compatible.

**Recommended opt-in changes:**
```python
class MyBlueprint(Blueprint):
    class Spec:
        model = MyModel
        fields = ["name", "email"]
        extra_fields = "reject"  # NEW: Reject unknown fields
```

### 3.2 For Framework Contributors

- Review any custom Facet subclasses for `eval()` usage
- Review any `JSONFacet` usage and add type restrictions if needed
- Test with `extra_fields = "reject"` to find mass assignment risks

---

## 4. Testing Strategy

### 4.1 New Security Tests

All security fixes include dedicated tests in `tests/test_blueprint_security.py`:

| Category | Test Count | Coverage |
|----------|-----------|----------|
| eval() removal | 6 | annotation resolution safety |
| Body size limit | 4 | integration layer |
| Many items limit | 3 | core validation |
| NaN/Inf rejection | 3 | float facet |
| Thread-safety | 2 | DictFacet |
| JSONFacet depth | 3 | structured facet |
| Unknown fields | 4 | core validation |
| ReDoS protection | 3 | text facet |
| Unflatten depth | 2 | integration |
| Nesting depth | 3 | annotations |
| DictFacet keys | 2 | structured facet |
| Content-Type | 2 | integration |
| Metaclass warning | 1 | core |
| **Total** | **38** | |

### 4.2 Regression Testing

All 4,530 existing tests must continue passing after changes.

---

## 5. Rollout Plan

```
Day 1: Implement Phase A (critical fixes)
        Run full test suite — must be green
        
Day 2: Implement Phase B (medium fixes)  
        Run full test suite — must be green
        
Day 3: Security review of all changes
        Performance benchmarking
        Documentation review
        
Day 4: Merge to develop branch
        Integration testing with myapp/
        
Day 5: Merge to master
        Tag release
```

---

*End of Blueprint Upgrade Plan — Phase 10*
