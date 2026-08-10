# Aquilia v1.4.0b4 Release Notes — "Resolved Fields"

This release is focused entirely on fixing the `@computed` decorator inheritance and facet precedence bug.

---

## Table of Contents

1. [Release Overview](#release-overview)
2. [Highlights](#highlights)
3. [Summary of Changes](#summary-of-changes)
4. [Bug Fixes & Refactorings](#bug-fixes--refactorings)
5. [Migration Guide & Breaking Changes](#migration-guide--breaking-changes)

---

## Release Overview

Aquilia v1.4.0b4 is a patch release focused on fixing a significant framework-level correctness bug regarding `@computed` decorator inheritance and facet precedence. Prior to this release, `@computed` methods in a parent contract were silently demoted to required `TextFacet` input fields under certain subclassing conditions. This is a pure correctness fix: previously broken code now works correctly, with no breaking changes.

---

## Highlights

### 1. `@computed` Facet Precedence Fix

The metaclass-level precedence bug in `aquilia.contracts` has been completely resolved. `@computed` methods defined on a base contract now survive all standard subclassing patterns. Previously, they would be overwritten if a subclass redeclared the same field as a type annotation (e.g. for IDE autocompletion) or bound an ORM model with a matching column name. They also failed if a same-class type annotation was co-declared with `@computed`. These scenarios now work natively without workarounds.

See [@computed Facet Precedence Fix](computed_fix.md) for full technical details.

---

## Summary of Changes

| Subsystem / Module | Status | Summary |
|---|---|---|
| `aquilia.contracts.annotations` | **Fixed** | `introspect_annotations()` now recognizes already-converted `Computed` (and any `Facet`) instances in the namespace and skips them, preventing a `TextFacet` from being generated for `@computed` fields that share a type annotation. |
| `aquilia.contracts.core` | **Fixed** | Facet merge in `ContractMeta.__new__` now protects inherited `Computed` facets — `model_facets` and `annotated_facets` cannot overwrite a parent contract's `@computed` field unless the subclass explicitly re-declares it in its own body. |
| `aquilia.contracts.core` | **Improved** | `_derive_model_facets()` docstring clarifies that callers manage Computed-protection filtering during the merge phase. |
| `tests/test_computed_inheritance_regression.py` | **New** | Four-scenario regression test suite covering the isolated class case, subclass annotation re-declaration, ORM model binding, and same-class annotation+computed co-declaration. |

---

## Performance Improvements

None. This is a pure Python metaclass path fix. One dictionary lookup was added per facet during the merge phase, with no measurable performance impact.

---

## Developer Experience Improvements

- **Computed Contract Inheritance**: `@computed` methods in inherited contracts now work correctly without requiring manual workarounds. You can safely re-declare annotations for IDE autocompletion in subclasses or bind ORM models without destroying the inherited computed facets.

---

## Bug Fixes & Refactorings

For detailed root cause analysis and reproduction scenarios regarding the `@computed` facet bug, please read the [computed_fix.md](computed_fix.md) deep-dive page.

---

## Migration Guide & Breaking Changes

There are no breaking changes in this release. Previously broken code now works correctly, and previously working code is unaffected. 

If your application relied on workarounds for the bug (e.g. manually declaring `full_name = TextFacet(read_only=True)` instead of using `@computed`), you can now safely switch to the `@computed` decorator.

See the [Migration Guide](migration.md) for more details.

---

## Upgrade Checklist

- [ ] Update `aquilia` to `1.4.0b4` in `pyproject.toml` / `requirements.txt`.
- [ ] Remove any manual `TextFacet(read_only=True)` workarounds in subclasses and replace them with inherited `@computed` decorators.

---

## Known Issues

This is a patch release targeting a specific bug with the `@computed` decorator. There are no new known issues beyond those present in v1.4.0b3.
