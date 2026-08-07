# Micro-Benchmark Results

All measurements run in-process with stdlib `timeit`, minimum across 5 repeats, on the same hardware as the HTTP suite. These isolate the native engines from transport overhead so coverage and speedup are visible without dilution.

---

## JSON Engine (`aquilia._json`)

**File**: `benchmarks/engine/microbench_json.py`

| Operation | Python (µs) | Native (µs) | Speedup |
|-----------|-------------|-------------|---------|
| encode    | 2.75        | 0.54        | 5.1x    |
| decode    | 3.12        | 1.15        | 2.7x    |

Payload: 138-byte nested dict with str/int/float/bool/null/list.

Native engine is `aquilia._json` (nanobind + simdjson/yyjson). Python baseline is `import json`.

---

## Contract Validation Engine (`aquilia._dataengine.FieldPlan`)

**File**: `benchmarks/engine/microbench_contracts.py`

| Case               | Python (µs) | Native (µs) | Speedup | Coverage |
|--------------------|-------------|-------------|---------|----------|
| flat_4_scalars     | 2.00        | 0.24        | 8.3x    | 4/4      |
| lists              | 2.63        | 0.24        | 11.2x   | 2/2      |
| lists_w_factory    | 2.64        | 2.64        | 1.0x    | 0/2      |
| nested_1_level     | 3.66        | 2.79        | 1.3x    | 2/3      |

- **flat_4_scalars**: str/int/float/bool, the shape the native plan covers completely.
- **lists**: `list[str]` and `list[int]`, declared without `default_factory`.
- **lists_w_factory**: Same list types, but with `default_factory=list`. A factory is a Python callable the engine cannot invoke, so these fields escape to Python by design. Included to keep the cost visible.
- **nested_1_level**: 2 scalars + 1 nested contract. The nested field escapes the outer plan but gets its own native plan recursively, so acceleration still applies.

Native path: `aquilia.contracts._native_plan.field_plan_for()` → `FieldPlan` → `Sigil.validate` wired at `aquilia/contracts/sigil.py:1456`.

Python baseline: `Sigil.validate` with the compiled plan temporarily detached and nested plans suppressed.

---

## ORM Hydration Engine (`aquilia._dataengine.RowPlan`)

**File**: `benchmarks/engine/microbench_orm.py`

| Batch | Python (µs) | Native (µs) | Speedup | Native ns/row |
|-------|-------------|-------------|---------|---------------|
| 1     | 0.95        | 0.18        | 5.4x    | 175.7         |
| 100   | 87.96       | 13.60       | 6.5x    | 136.0         |
| 1000  | 887.26      | 147.35      | 6.0x    | 147.4         |

Model: 4 fields (CharField, IntegerField, FloatField, BooleanField) + auto-generated BigAutoField pk.

Native path: `aquilia.models._native_plan.row_plan_for()` → `RowPlan.execute()`, wired at `aquilia/models/query.py:1448`.

Python baseline: `Model.from_row()` list comprehension.

Per-row cost falls from 175ns (singleton) to 136ns (batch of 100) because the nanobind boundary crossing amortizes across the batch.

---

## Field-Type Coverage

### Contracts (`FieldPlan`)

**Covered (accelerated)**:
- Scalars: `str`, `int`, `float`, `bool`
- Homogeneous lists: `list[str]`, `list[int]`, `list[float]`, `list[bool]`
- Nested contracts (recursive acceleration — outer plan dispatches to inner plan)

**Escaped (falls back to Python)**:
- Fields with `default` or `default_factory` (engine cannot invoke Python callables)
- `datetime`, `date`, `time` (TypeCode exists but no Python-side compiler yet)
- Heterogeneous lists, tuples, dicts, sets, unions, optionals beyond `T | None`

### ORM (`RowPlan`)

**Covered (12 base types + CI/Positive variants = 20 total)**:
- **Str-like**: `CharField`, `TextField`, `EmailField`, `SlugField`, `URLField`, `VarcharField`, `CICharField`, `CIEmailField`, `CITextField`
- **Int-like**: `IntegerField`, `BigIntegerField`, `SmallIntegerField`, `PositiveIntegerField`, `PositiveSmallIntegerField`, `PositiveBigIntegerField`, `AutoField`, `BigAutoField`, `SmallAutoField`
- **Scalars**: `FloatField`, `BooleanField`

**Not yet covered (28 field types remain)**:
- Temporal: `DateField`, `DateTimeField`, `TimeField`, `TimestampField`
- JSON/Binary: `JSONField`, `BinaryField`, `UUIDField`
- Numeric: `DecimalField`
- Relational: `ForeignKey`, `ManyToManyField`, `OneToOneField`
- All other specialized fields

All covered fields have `to_python()` implementations that pass through the raw driver value without transformation — that's the eligibility criterion. Fields requiring Python-side conversion (e.g., `date.fromisoformat`, `Decimal()`) are correctly escaped.

---

## Interpreting Coverage

**100% coverage** means every field compiles into the native plan. Speedup approaches the engine's theoretical maximum.

**Partial coverage** (e.g., 2/3) means one field escaped. The native plan handles the covered fields; Python handles escaped fields. Speedup is bounded by the fraction of work that remains in Python.

**0% coverage** means the plan rejected the contract at compile time. Common reasons:
- A field has a `default_factory`
- A field type has no TypeCode mapping
- The contract uses a facet the engine cannot represent

A plan reporting 0/N coverage is **not an error** — it means the ORM or validation layer will use its Python fallback, which is correct and tested, just slower.

---

## How to Run

```bash
# All three microbenchmarks:
python benchmarks/engine/microbench_json.py
python benchmarks/engine/microbench_contracts.py
python benchmarks/engine/microbench_orm.py

# HTTP suite (includes regression gates):
uv run python benchmarks/run.py
```

These are measurement tools, not gates. Exit code is always 0. Regression gates live in `benchmarks/run.py`.
