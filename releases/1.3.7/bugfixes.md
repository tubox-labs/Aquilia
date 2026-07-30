# Bug Fixes in Aquilia v1.3.7

Aquilia v1.3.7 resolves key issues identified in model field handling, multi-threaded model registry operations, manager descriptor subclass access, and test assertions.

---

## 1. Missing Dialect Parameter in EnumField & CompositeField

**The Bug:**
When calling `contract.imprint()` on a `Contract` bound to a `Model` containing an `EnumField` or `CompositeField`, the framework passed `dialect="sqlite"` to `field.to_db()`. Because `EnumField.to_db()` and `CompositeField.to_db()` did not accept `dialect`, Python raised a `TypeError`:

```text
TypeError: EnumField.to_db() got an unexpected keyword argument 'dialect'
```

**The Fix:**
Added `dialect: str = "sqlite"` to `EnumField.to_db()` and `CompositeField.to_db()`, aligning their method signatures with `Field.to_db()`.

---

## 2. Race Conditions in ModelRegistry Under Concurrency

**The Bug:**
In multi-threaded ASGI environments or test runners with parallel test execution, concurrent model registration or calls to `ModelRegistry.reset()` could cause data race mutations on `_models` and `_app_models`, occasionally causing `RuntimeError: dictionary changed size during iteration`.

**The Fix:**
Guarded all `ModelRegistry` operations with a re-entrant lock (`threading.RLock`). Added `_clear_reverse_relation_caches()` on `Model` to clear stale `_reverse_fk_cache` and `_reverse_relation_cache` entries when models are registered or reset.

---

## 3. Subclass Manager Descriptor Mutation Race Condition

**The Bug:**
Accessing `SubModel.objects` when `objects = Manager()` was inherited from `ParentModel` mutated `self._model_cls` directly on the shared `BaseManager` instance, causing cross-thread manager state pollution.

**The Fix:**
Refactored `BaseManager.__get__()` to return a bound shallow copy (`copy.copy(self)`) when accessed on a subclass or different owner.

---

## 4. Test Suite HMAC Secret Warning & Envelope Format Assertions

**The Bug:**
Bytecode cache and snapshot tests emitted HMAC secret warning messages during testing and failed envelope dictionary format assertions under strict test runs.

**The Fix:**
Updated test fixtures and envelope dict format assertions in `tests/test_phase15_faults_security.py` and `tests/test_admin_v3.py` to ensure clean test suite execution.
