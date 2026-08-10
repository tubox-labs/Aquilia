# @computed Facet Precedence Fix

## 1. Executive Summary

This page details the root cause and fixes for a metaclass-level precedence bug in `aquilia.contracts` where `@computed` methods in a parent contract were silently demoted to required `TextFacet` input fields.

## 2. Affected Versions

This bug affects Aquilia versions **v1.0.0 through v1.4.0b3**.

## 3. Root Cause Analysis

An audit identified three root causes that combined to create this bug:

- **Root Cause 1:** Dead code in `introspect_annotations()`. The check `isinstance(ns_value, _ComputedMarker)` was always `False` because `ContractMeta.__new__` had already converted every `_ComputedMarker` to a `Computed` facet instance before calling `introspect_annotations`. Additionally, with `include_explicit_facets=True`, the existing `Facet` guard was bypassed.
- **Root Cause 2:** Flawed merge precedence in `ContractMeta.__new__`. During the class construction phase, `annotated_facets.update()` blindly overwrote `parent_facets` which contained the inherited `Computed` facet.
- **Root Cause 3:** `_derive_model_facets` generated model facets without checking whether the same name was declared as a `Computed` facet in the parent contract.

## 4. Reproduction Scenarios

### Scenario 1: Subclass Annotation Re-declaration (Previously Broken)
A base contract defines a computed field, and a subclass annotates it for IDE support.
**Before:** The subclass overwrote the computed facet with a required `TextFacet`.
**After:** The subclass preserves the inherited computed facet.

```python
# Before (Buggy behavior)
class Base(Contract):
    @computed
    def full_name(self) -> str: return "Test"

class Child(Base):
    full_name: str # Overwrote inherited @computed

bp = Child(data={}) 
# Raised ValidationError: full_name is required
```

### Scenario 2: Subclass ORM Model Binding (Previously Broken)
A base contract defines a computed field, and a subclass binds a model with a matching column name.
**Before:** The model's column implicitly overwrote the computed facet.
**After:** The computed facet takes precedence over the model's column mapping.

```python
# Before (Buggy behavior)
class Base(Contract):
    @computed
    def name(self) -> str: return "Test"

class Child(Base):
    class Spec:
        model = UserModel # Has a 'name' column, overwriting @computed

bp = Child(data={})
# Raised ValidationError: name is required
```

### Scenario 3: Same-Class Annotation Co-declaration (Previously Broken)
A class annotates a field and also declares it as `@computed`.
**Before:** The annotation generated a redundant `TextFacet` which sometimes corrupted subclasses.
**After:** The `@computed` decorator safely overrides the class's own type annotation.

```python
# Before (Buggy behavior)
class UserContract(Contract):
    name: str
    
    @computed
    def name(self) -> str: return "Test"
    
bp = UserContract(data={})
# Unpredictable behavior, sometimes raised ValidationError
```

## 5. The Fixes Applied

1. **Fixed `introspect_annotations()` (aquilia/contracts/annotations.py):**
```python
# Replaced dead code with proper Facet detection
# Before: isinstance(ns_value, _ComputedMarker) — always False after metaclass conversion
# After:
if isinstance(ns_value, (_ComputedMarker, Facet)):
    continue  # Already handled above (Facet covers Computed instances too)
```

2. **Fixed `ann_namespace` building in `ContractMeta.__new__` (aquilia/contracts/core.py):**

The loop building `ann_namespace` excluded names already in `declared_facets`. When a `@computed` method was present, it was converted to a `Computed` instance and placed in `declared_facets`, but the loop condition `fname not in declared_facets` then prevented it from being injected into `ann_namespace`. As a result, when `introspect_annotations()` encountered `full_name: str` in annotations, it found `ns_value = UNSET` for `full_name` and generated a redundant `TextFacet`. The fix explicitly injects `Computed` facets (and only `Computed`) into `ann_namespace` first:

```python
# Only Computed facets are injected. NestedContractFacet and other declared
# facets remain absent so that _merge_nested_annotation_facets can still
# detect annotation/facet type mismatches (e.g., name: NameContract vs
# name = NestedContractFacet(AltContract)).
for fname, facet in declared_facets.items():
    if fname not in ann_namespace and isinstance(facet, Computed):
        ann_namespace[fname] = facet
```

3. **Fixed Merge Precedence (aquilia/contracts/core.py):**
```python
# Prevent annotated and model facets from overwriting inherited Computed facets
for fname, facet in model_facets.items():
    if fname not in declared_facets and isinstance(parent_facets.get(fname), Computed):
        continue  # Protect inherited Computed — model column must not clobber it
    all_facets[fname] = facet
for fname, facet in annotated_facets.items():
    if fname not in declared_facets and isinstance(parent_facets.get(fname), Computed):
        continue  # Protect inherited Computed — bare annotation must not clobber it
    all_facets[fname] = facet
```

4. **Docstring Clarification in `_derive_model_facets`:**
Added documentation stating that callers (like `ContractMeta.__new__`) are responsible for filtering out generated model facets that would overwrite an inherited `Computed` facet.

## 6. Behavioral Changes

- Type annotations (`full_name: str`) on subclasses no longer obliterate inherited `@computed` fields.
- Model columns do not implicitly override inherited `@computed` fields unless explicitly re-declared in the subclass namespace.

## 7. Migration Guide

No migration is needed! Previously broken code now works exactly as you originally intended it to. If you added hacks or workarounds, you can remove them safely.

## 8. What Does NOT Change

Backward compatibility is strictly maintained. The only change is that `@computed` inheritance is no longer broken.

## 9. Examples

Here is the correct pattern that now works seamlessly for mixins and inheritance:

```python
from aquilia.contracts import Contract
from aquilia.contracts.annotations import computed

class UserMixin(Contract):
    first_name: str
    last_name: str

    @computed
    def full_name(self, instance) -> str:
        return f"{instance.first_name} {instance.last_name}"

class AdminContract(UserMixin):
    # Safe to re-annotate for IDE completion
    full_name: str 
    
    class Spec:
        model = AdminModel # 'full_name' column will not break the computed property

bp = AdminContract(data={"first_name": "Ada", "last_name": "Lovelace"})
assert bp.is_sealed() # True!
```
