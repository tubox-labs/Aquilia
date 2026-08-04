# Phase 7 — Testing Strategy

**Status:** design
**Baseline:** 7,850 passing tests. The engine must not require a single one to change.
**Precedent:** the Phase 9 controller engine shipped with 172 parity assertions and a full-suite fallback gate; that gate is what made the native layer safe to ship, and the same structure applies here.

---

## 1. The central principle: the native path must be deletable

Every behavioural test must pass with the engine on **and** off. This is not a nice-to-have — it is the property that makes the whole project low-risk. If the native engine can be disabled at any moment with zero behaviour change, then shipping it is reversible; if it cannot, every bug becomes a production incident with no rollback.

Two mechanisms, both borrowed from the Phase 9 gates that worked:

```bash
AQUILIA_DATAENGINE=0 pytest tests/ -q     # full suite, engine disabled
```

and physically removing the built extension, which exercises the `ImportError` path in the loader rather than the env-var path. Phase 9 found these are **not** the same test: the env var short-circuits before the import, so only the file-removal test proves the `dlopen` failure is actually caught.

---

## 2. Test layers

| Layer | Location | Runner | Proves |
|---|---|---|---|
| C++ unit | `aquilia/_dataengine/tests/*.cpp` | `ctest` | conversion, plan compile, plan execute — no Python |
| Conversion parity | `tests/dataengine/test_convert_parity.py` | pytest | native conversion == CPython conversion, exhaustively |
| Hydration parity | `tests/dataengine/test_hydration_parity.py` | pytest | native `from_row` == Python `from_row` |
| Validation parity | `tests/dataengine/test_validation_parity.py` | pytest | native validate == `Sigil.validate` |
| Eligibility | `tests/dataengine/test_eligibility.py` | pytest | ineligible plans actually fall back |
| Property | `tests/dataengine/test_properties.py` | pytest + Hypothesis | invariants over generated rows/payloads |
| Memory | `tests/dataengine/test_memory.py` | pytest | refcount balance, no growth |
| Concurrency | `tests/dataengine/test_concurrency.py` | pytest-asyncio | plan reuse under `asyncio.gather` |
| Regression | existing 7,850 | pytest | no behaviour change |
| Performance | `tests/dataengine/test_perf_gates.py` | pytest, `slow` | targets from `03`–`05` met |

---

## 3. The highest-risk tests, written first

These are not the most numerous; they are the ones where a defect is silent and expensive. Each corresponds to a specific semantic identified in `04`/`05`.

### 3.1 Dirty tracking → `save()` round-trip ★ highest severity

`04` §3.2: if `_original_values` is wrong, `save()` either writes unchanged columns or **silently skips changed ones**. The second is data loss, and no existing test would catch it, because today's tests hydrate and save through the same code path.

```python
async def test_save_after_native_hydration_emits_identical_sql():
    """A native-hydrated instance must produce the same UPDATE as a
    Python-hydrated one. This is the data-loss gate."""
    row = {...}
    native = plan.execute([row])[0]
    python = Model.from_row(row)

    assert native._original_values == python._original_values

    native.name = "changed"
    python.name = "changed"
    assert native.get_dirty_fields() == python.get_dirty_fields() == {"name": "changed"}
```

Parameterised over: all-columns rows, partial rows, rows with `None` values, rows where the new value equals the old.

### 3.2 `IntFacet` cast semantics

`05` §3.1 documents a table of deliberate, counter-intuitive decisions — `True` rejected, `3.0` accepted, `3.9` **rejected rather than truncated**. A native `strtoll` would get several of these wrong, and the failure mode ("quantity 3.9 silently becomes 3") is exactly the data corruption the Python code was written to prevent.

```python
@pytest.mark.parametrize("value,expected", [
    (3, 3), (3.0, 3), (Decimal("3.0"), 3), ("3", 3),
    (True, CastFault), (False, CastFault),      # bool is an int subclass
    (3.9, CastFault), (Decimal("3.9"), CastFault),  # never truncate
    (float("nan"), CastFault), (float("inf"), CastFault),
    ("3.9", CastFault), ("abc", CastFault), (None, CastFault),
])
def test_int_cast_parity(value, expected):
    """Every row of 05 §3.1. Native and Python must agree exactly."""
```

### 3.3 Missing vs explicit `None`

`05` §3.4/§3.5: a missing key and an explicit `None` follow **different** resolution paths, and `04` §3.3 requires an absent column not to become `None` (indistinguishable from a real SQL NULL).

```python
def test_missing_is_not_none():
    assert validate({}) != validate({"field": None})
    # and for hydration:
    assert "col" not in Model.from_row({}).__dict__
```

### 3.4 Error messages are byte-identical

`05` §3.7: messages appear in HTTP 422 bodies, so they are public API. Equivalent is not sufficient — identical is required.

```python
def test_error_messages_identical():
    for payload in FAILING_PAYLOADS:
        n_err, _ = native_plan.execute(payload)
        p_err, _ = sigil.validate(payload)
        assert n_err == p_err          # exact dict equality, message strings included
```

### 3.5 Deferred fields and FK wrapping

`04` §3.3/§3.4:

```python
def test_deferred_guard_preserved():
    inst = hydrate_natively(partial_row)
    with pytest.raises(DeferredFieldAccessFault):
        inst.excluded_column

def test_fk_wrapping():
    inst = hydrate_natively({"user_id": 42})
    assert isinstance(inst.user, RelatedNotLoaded)
    assert inst.user.pk == 42          # cheap ops work
    assert bool(inst.user) is True
    inst_null = hydrate_natively({"user_id": None})
    assert inst_null.user is None      # None is NOT wrapped
```

### 3.6 No init signals on hydration

`04` §3.1: hydration bypasses `__init__`, so `pre_init`/`post_init` do not fire today. A native path that constructed instances differently could start firing them — 2,000 spurious signal dispatches per 1,000-row page.

```python
def test_hydration_fires_no_init_signals():
    calls = []
    post_init.connect(lambda **kw: calls.append(kw))
    hydrate_natively([row] * 1000)
    assert calls == []
```

---

## 4. Conversion parity — exhaustive, not sampled

Each `TypeCode` gets a corpus of inputs including the adversarial ones. Native and CPython must produce values that are `==` **and** the same `type()`.

| Type | Must include |
|---|---|
| `Int` | 0, negative, `int64` boundaries, values **beyond** int64 (Python ints are unbounded), leading `+`, `_` separators, unicode digits, whitespace |
| `Float` | `inf`, `-inf`, `nan`, `1e308`, `1e-308`, `-0.0`, exponent forms |
| `Decimal` | trailing zeros (`1.10` ≠ `1.1` in `Decimal` **repr** but `==` in value), very high precision, exponent forms, `-0` |
| `Date`/`DateTime` | timezone offsets, `Z` suffix, fractional seconds, leap day, year 1 and 9999 |
| `Uuid` | all versions, uppercase, braces, `urn:uuid:` prefix, invalid hex, wrong length |
| `Json` | nested, unicode escapes, big numbers, duplicate keys, empty containers |
| `Bool` | every accepted token, and rejection of everything else |

**`Decimal` deserves specific attention.** `Decimal("1.10") == Decimal("1.1")` is `True` but their `repr` differs and `as_tuple()` differs. A money value that round-trips through the engine with a changed exponent is a real defect that `==` will not catch:

```python
def test_decimal_preserves_exponent():
    """Decimal("1.10") and Decimal("1.1") compare equal but are not
    interchangeable -- exponent is part of the value for money."""
    assert convert_native("1.10").as_tuple() == Decimal("1.10").as_tuple()
```

**Unbounded integers** matter equally: `int64` overflow must not silently wrap. Python has no integer limit, so a 30-digit id must survive.

---

## 5. Eligibility tests — that fallback actually happens

The Phase 9 router shipped with a test asserting the native tier was *actually being used*, because an eligibility bug that rejected everything would leave the whole parity suite green while the engine sat idle. The inverse risk applies here too: a plan that compiles when it should not.

```python
def test_native_path_is_actually_used():
    """Guard against a green suite that proves nothing."""
    plan = row_plan_for(SimpleModel, KEYS)
    assert plan is not None and plan.eligible

@pytest.mark.parametrize("model", [
    ModelWithCustomToPython,
    ModelWithCustomSet,
    ModelWithUnsupportedFieldType,
    ModelWithCustomNew,
])
def test_ineligible_models_fall_back(model):
    assert row_plan_for(model, keys_for(model)) is None

@pytest.mark.parametrize("contract", [
    ContractWithPipeline, ContractWithValidator, ContractWithNested,
    ContractWithComputed, ContractWithDefaultFactory, ContractWithCustomFacet,
])
def test_ineligible_contracts_fall_back(contract):
    assert field_plan_for(contract) is None
```

Plus per-call eligibility: `MultiDict`/`FormData` payloads, `partial=True`, `strict=True` must all take the Python path (`05` §2.4).

---

## 6. Property-based tests

Hypothesis generates rows and payloads; invariants are asserted rather than specific outputs.

```python
@given(row=model_rows())
def test_hydration_parity(row):
    # I1: native and Python agree on every attribute
    # I2: _original_values agree
    # I3: deferred set agrees
    # I4: repeated execution is deterministic

@given(payload=contract_payloads())
def test_validation_parity(payload):
    # I5: (errors, validated) identical
    # I6: never raises -- Sigil.validate's documented contract (sigil.py:181)
    # I7: a field appears in validated XOR in errors, never both
```

Generators must include: empty payloads, all-`None` payloads, extra keys, wrong types for every field, unicode, very long strings, and values at every numeric boundary.

---

## 7. Memory correctness

The Phase 9 lesson: nanobind's shutdown "leaked N instances" report cannot distinguish a leak from an object still reachable at exit. Growth is the discriminator, so assert on growth.

| Check | Method | Gate |
|---|---|---|
| Refcount balance | `sys.getrefcount` on values bound into instances | net zero over 100k rows |
| Object growth | `len(gc.get_objects())` delta | < 100 over 100k rows |
| Instance release | `weakref` to a hydrated instance | collected after `del` |
| Plan cache bound | plan count after 10k queries | ≤ distinct projections |
| Leaks / UB | ASAN + UBSAN on the C++ tests | zero reports |

```python
def test_no_growth_over_100k_rows():
    gc.collect(); before = len(gc.get_objects())
    for _ in range(1000):
        plan.execute([row] * 100)
    gc.collect()
    assert len(gc.get_objects()) - before < 100
```

---

## 8. Concurrency

Plans are immutable after build (`03` §11), so the risk is in *building* them concurrently and in sharing them across tasks.

```python
async def test_concurrent_hydration_isolation():
    """Concurrent batches must not observe each other's instances."""
    async def worker(i):
        rows = [{"id": i, "name": f"n{i}"}] * 50
        out = plan.execute(rows)
        await asyncio.sleep(0)                 # force interleaving
        assert all(o.id == i for o in out)
    await asyncio.gather(*(worker(i) for i in range(64)))

def test_concurrent_plan_build_is_safe():
    """First-use races may build the same plan twice; both must be valid."""
    with ThreadPoolExecutor(16) as ex:
        plans = list(ex.map(lambda _: row_plan_for(Model, KEYS), range(64)))
    assert all(p is not None for p in plans)
```

Plus a C++ test running `std::thread`s against one frozen plan, TSAN-clean.

---

## 9. Performance gates

Budgets are the *measured* post-native numbers plus headroom — regression detectors, not aspirations. Marked `slow`, run nightly, not per-PR (shared CI is too noisy for a 1 µs measurement).

```python
GATES_NS = {
    "hydrate_row_8col":      1_200,
    "validate_payload_8f":   1_500,
}
GATES_US = {
    "hydrate_100_rows":        120,
    "validate_100_payloads":   120,
}
```

Plus the ratio test that matters more than any absolute:

```python
def test_native_beats_python():
    """Machine-independent: the native path must actually be faster."""
    assert time_native() < time_python()
```

---

## 10. Coverage targets

| Component | Target |
|---|---|
| C++ conversion (`convert.cpp`, `uuid_parse.cpp`) | ≥ 95% line, ≥ 90% branch |
| Plan compilers | 100% of eligibility branches |
| `module.cpp` bindings | 100% line — an unexercised binding is an untested ABI boundary |
| Loader fallback paths | 100% |
| Python integration glue | ≥ 90% |

---

## 11. CI gates — all blocking

| Job | Command | Proves |
|---|---|---|
| build + test | `pip install -e . && pytest tests/ -q` | works natively on 3 OS × 3 Python |
| assert native loaded | `assert DATAENGINE_NATIVE` | a silent build skip cannot leave the suite green |
| sanitizers | `ctest` under ASAN+UBSAN | no leaks, no UB |
| fallback parity | `AQUILIA_DATAENGINE=0 pytest tests/` | the engine is deletable |
| no-extension | delete the `.so`, run the suite | the `ImportError` path works |
| no compiler | install without a toolchain | degrades to pure Python |

The "assert native loaded" job is not redundant with "build + test": without it, a build that silently skipped the extension would skip every engine test and report green — the exact failure mode the Phase 9 CI was written to catch.

---

## 12. What is explicitly not tested natively

These stay in Python and keep their existing tests as the regression gate. If native work breaks them, the change is wrong:

- `@ward` methods and the `validate()` hook (Phases 3–4 of sealing)
- Pipelines, custom validators, custom facets, custom fields
- Nested contracts, `ListFacet`, `DictFacet`
- `MultiDict` / `FormData` payload shapes
- `strict` and `partial` modes
- `select_related` / `prefetch_related` splitting
- Migrations, codegen, introspection, the query builder
- The write path (`save`, `to_db`)
