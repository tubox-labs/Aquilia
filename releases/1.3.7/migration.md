# Migration Guide — Aquilia v1.3.7

Aquilia v1.3.7 is a **100% backward-compatible release**. All existing v1.3.6 applications will run without any code modifications or database migration requirements.

---

## Upgrading

Upgrade Aquilia using `pip`:

```bash
pip install aquilia==1.3.7
```

Or using Poetry / uv / pipenv:

```bash
uv pip install aquilia==1.3.7
```

---

## Upgrade Checklist

1. **Update Dependency**: Upgrade `aquilia` to `1.3.7`.
2. **Run Test Suite**: Run `pytest` across your application codebase to verify all existing contracts, models, and manager queries pass.
3. **Optional Code Cleanup**: Simplify nested contract declarations by replacing `NestedContractFacet(SubContract)` with clean Python type annotations `name: SubContract`.

---

## New Capabilities You Can Adopt

### 1. Python Type Annotations for Nested Contracts

```python
# Before (v1.3.6 and earlier):
class UserContract(Contract):
    profile = NestedContractFacet(ProfileContract)

# New in v1.3.7:
class UserContract(Contract):
    profile: ProfileContract
```

### 2. Multi-Threaded Model Operations

You can safely perform model registration, reset, and dynamic schema inspection across multiple threads without manual locking mechanisms.

---

## Verification

After upgrading, run your test suite:

```bash
pytest
```

All 7,410+ framework tests continue to pass seamlessly.
