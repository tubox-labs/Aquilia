# Aquilia Blueprint — Architecture Review

**Module:** `aquilia/blueprints/` (8 files, ~5,000 LOC)  

---

## 1. Architectural Overview

The Blueprint module is Aquilia's native serialization/deserialization system,
designed as a **first-class framework primitive** rather than a bolt-on serializer.
It replaces the traditional Serializer pattern (DRF-style) with a domain-specific
vocabulary: Facets, Casts, Seals, Molds, Imprints, Projections, and Lenses.

### 1.1 Component Map

```
blueprints/
├── core.py          978 LOC   Metaclass, Blueprint base, validation pipeline
├── facets.py       1308 LOC   All Facet types (field-level primitives)
├── annotations.py   963 LOC   Type-annotation introspection, Field descriptor
├── lenses.py        207 LOC   Relational view with depth/cycle control
├── projections.py   200 LOC   Named field subsets
├── schema.py         75 LOC   OpenAPI schema generation
├── integration.py   224 LOC   Controller/DI/Request hooks
├── exceptions.py    130 LOC   Exception hierarchy
└── __init__.py      163 LOC   Public API exports
```

### 1.2 Layer Architecture

```
┌─────────────────────────────────────────────────┐
│              Integration Layer                    │
│  integration.py — Controller/DI binding           │
├─────────────────────────────────────────────────┤
│              Core Layer                           │
│  core.py — BlueprintMeta + Blueprint base         │
├─────────────────────────────────────────────────┤
│              Facet Layer                          │
│  facets.py — 20+ Facet types                      │
│  annotations.py — Type → Facet derivation         │
├─────────────────────────────────────────────────┤
│              View Layer                           │
│  lenses.py — Relational traversal                 │
│  projections.py — Field subsets                   │
├─────────────────────────────────────────────────┤
│              Schema Layer                         │
│  schema.py — OpenAPI generation                   │
├─────────────────────────────────────────────────┤
│              Exception Layer                      │
│  exceptions.py — Fault hierarchy                  │
└─────────────────────────────────────────────────┘
```

---

## 2. Design Principles Assessment

### 2.1 Strengths

1. **Metaclass-driven registration**: `BlueprintMeta` automatically collects facets,
   parses Spec, derives model facets, and registers in the global registry. This
   eliminates boilerplate and ensures consistency.

2. **Dual declaration modes**: Both explicit Facet instantiation and Python type
   annotations are supported, with annotations taking precedence in the merge order.

3. **Clean lifecycle vocabulary**: Cast (inbound type coercion) → Seal (validation)
   → Mold (outbound formatting) → Imprint (write-back) is intuitive and well-separated.

4. **Projection system**: Named field subsets with exclusion syntax and `__all__`/
   `__minimal__` presets provide flexible API versioning and permission-based views.

5. **Lens system**: Depth-controlled relational traversal with cycle detection
   elegantly handles nested object graphs.

6. **Framework integration**: Auto-binding via controller type annotations and DI
   container access creates a seamless developer experience.

### 2.2 Weaknesses

1. **`facets.py` is a monolith** (1308 LOC): All 20+ Facet types in one file makes
   navigation difficult and increases merge conflicts.

2. **Metaclass complexity**: `BlueprintMeta.__new__()` is ~130 lines with 6
   distinct responsibilities. Hard to test individual phases.

3. **Global mutable registry**: `_blueprint_registry` is module-level dict with
   no thread-safety, no namespacing, and no cleanup mechanism.

4. **`annotations.py` eval()**: The PEP 563 annotation resolution uses `eval()`
   with frame-walked globals — a critical security flaw.

5. **No async cast path**: Only `is_sealed_async()` exists for async seals.
   There's no async cast path for I/O-bound type resolution.

6. **Mixed concerns in `integration.py`**: Request parsing, DI extraction, and
   response rendering in one function violates single responsibility.

### 2.3 Architectural Debt

| Area | Debt Type | Impact | Priority |
|------|-----------|--------|----------|
| eval() in annotations | Security debt | Critical vuln | P0 |
| Monolithic facets.py | Structural debt | Maintainability | P2 |
| Global registry | Concurrency debt | Race conditions | P1 |
| No plugin interface | Extensibility debt | Hard to add custom facets | P2 |
| No caching in to_dict | Performance debt | Repeated mold ops | P3 |

---

## 3. Data Flow Architecture

### 3.1 Inbound (Cast + Seal)

```
Input Data (dict)
    │
    ▼ Blueprint.__init__()
    │   ├─ Clone all facets → _bound_facets
    │   └─ Store raw _input_data
    │
    ▼ Blueprint.is_sealed()
    │
    ├─► Phase 1: Cast
    │   └─ For each facet: raw → facet.cast() → typed value
    │
    ├─► Phase 2: Field Seal
    │   └─ For each facet: facet.seal(cast_value) → validated value
    │
    ├─► Phase 3: Cross-Field Seal
    │   └─ For each seal_* method: method(validated_dict)
    │
    ├─► Phase 4: Object Validate
    │   └─ self.validate(validated_dict) → final dict
    │
    └─► Phase 5 (async only): Async Seal
        └─ For each async_seal_* method: await method(validated_data)
    │
    ▼ self._validated_data = DataObject(validated)
```

### 3.2 Outbound (Extract + Mold)

```
Model Instance
    │
    ▼ Blueprint.to_dict()
    │
    ├─► Resolve projection → frozenset of field names
    │
    ├─► For each facet in _bound_facets:
    │   ├─ Skip write_only facets
    │   ├─ Skip facets not in projection
    │   ├─ facet.extract(instance) → raw value
    │   └─ facet.mold(raw_value) → output value
    │
    └─► Return result dict
```

### 3.3 Write-Back (Imprint)

```
Validated Data
    │
    ▼ Blueprint.imprint()
    │
    ├─► _filter_imprint_data() — remove computed/constant/inject facets
    │
    ├─► CREATE: Model(**filtered_data) → model.save()
    │   OR
    └─► UPDATE: setattr(instance, field, value) → instance.save(update_fields)
```

---

## 4. Metaclass Architecture

### 4.1 `BlueprintMeta.__new__()` Phases

```
Phase 1: Collect declared Facets from namespace
Phase 2: Convert @computed markers to Computed facets
Phase 3: Inherit facets from parent Blueprints
Phase 4: Parse Spec inner class → _SpecData
Phase 5: Create class via super().__new__()
Phase 6: Introspect type annotations → annotated_facets
Phase 7: Auto-derive facets from Model fields
Phase 8: Merge all facet sources (parent < annotated < model < declared)
Phase 9: Apply read_only/write_only from Spec
Phase 10: Sort by creation order
Phase 11: Build ProjectionRegistry
Phase 12: Discover seal_*/async_seal_* methods
Phase 13: Register in _blueprint_registry
```

### 4.2 Facet Merge Precedence

```
Lowest Priority                              Highest Priority
     │                                              │
     ▼                                              ▼
parent_facets → annotated_facets → model_facets → declared_facets
```

This means explicitly declared Facets always win, which is correct. However,
there's no warning when annotations and declarations conflict.

---

## 5. Dependency Analysis

### 5.1 Internal Dependencies

```
core.py ──imports──► facets.py, lenses.py, projections.py, annotations.py, exceptions.py
annotations.py ──imports──► facets.py, exceptions.py
integration.py ──imports──► core.py, lenses.py
schema.py ──imports──► core.py
lenses.py ──imports──► (standalone, no blueprint imports)
projections.py ──imports──► (standalone)
exceptions.py ──imports──► (standalone, inherits from faults module)
```

### 5.2 External Dependencies

```
core.py ──imports──► aquilia.utils.data.DataObject
                     aquilia.models.base.Model (TYPE_CHECKING)
                     aquilia.models.fields_module (runtime)
integration.py ──imports──► aquilia.di.dep (Query, Header) (runtime, optional)
```

### 5.3 Circular Dependency Risk

`facets.py` TYPE_CHECKING-imports `core.Blueprint`, and `core.py` imports
from `facets.py`. This is handled correctly via `TYPE_CHECKING` guard,
but creates a tight coupling that limits refactoring.

---

## 6. Recommendations

### 6.1 Immediate (Security)
1. Replace `eval()` with safe annotation resolution
2. Add resource limits (body size, list length, nesting depth)
3. Add unknown field rejection mode

### 6.2 Short-Term (Architecture)
4. Split `facets.py` into submodules: `facets/text.py`, `facets/numeric.py`, etc.
5. Extract metaclass phases into separate functions for testability
6. Add namespacing to `_blueprint_registry`

### 6.3 Medium-Term (Features)
7. Add async cast pipeline for I/O-bound validation
8. Add Facet plugin/registry for custom types
9. Add schema caching for repeated to_schema() calls
10. Add Blueprint composition (mixin support)

---

*End of Architecture Review — Phase 10*
