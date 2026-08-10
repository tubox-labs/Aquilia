# Migration Guide — v1.4.0b3 → v1.4.0b4

Aquilia v1.4.0b4 is a patch release focused on fixing a correctness bug in the `@computed` decorator inheritance.

---

## Upgrade Instructions

Update your `aquilia` dependency to `1.4.0b4` in your `pyproject.toml` or `requirements.txt`:

```bash
pip install aquilia==1.4.0b4
```

## No Breaking Changes

This release is a **pure correctness fix**. 
- Previously broken code (subclassing a contract with a `@computed` field) now works correctly.
- Previously working code is unaffected.
- No public APIs have been removed, renamed, or altered in behavior.

## Workaround Removal Guide

If your application previously used workarounds to circumvent the `@computed` inheritance bug, you can now remove them.

**Before (Workaround):**
```python
from aquilia.contracts import Contract
from aquilia.contracts.facets import TextFacet

class BaseUserContract(Contract):
    pass

class ChildUserContract(BaseUserContract):
    # Hack: Manually defining read-only TextFacet because @computed broke in subclasses
    full_name = TextFacet(read_only=True) 
```

**After (Correct usage):**
```python
from aquilia.contracts import Contract
from aquilia.contracts.annotations import computed

class BaseUserContract(Contract):
    @computed
    def full_name(self, instance) -> str:
        return f"{instance.first_name} {instance.last_name}"

class ChildUserContract(BaseUserContract):
    full_name: str # Purely for IDE hinting; does not break the @computed facet
```

## Compatibility Matrix

| Component | Minimum | Recommended |
|---|---|---|
| Python | 3.10 | 3.12+ |
| OS | Linux, macOS 11+, Windows 10+ | Ubuntu 22.04 / macOS 14 |

## Upgrade Checklist

- [ ] Update `aquilia` version to `1.4.0b4`
- [ ] Audit your codebase for manual `TextFacet(read_only=True)` declarations that were acting as stand-ins for `@computed` and replace them with standard `@computed` methods.
