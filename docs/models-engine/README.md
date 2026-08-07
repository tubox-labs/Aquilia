# Models / DB / Contracts Native Engine — document set

Audit and design for a native engine covering `aquilia/models/`, `aquilia/db/`,
`aquilia/sqlite/`, and `aquilia/contracts/`.

**This is now implemented.** `10-results.md` records what was measured, which
gates were met and missed, and the three places the design documents below had
to be corrected against reality. Read it alongside `03`–`05`, which are left as
written so the corrections stay visible.

---

## Read in this order

| Doc | Contents |
|---|---|
| [01-architecture-audit.md](01-architecture-audit.md) | Subsystem map, hydration and validation execution flows, metaclass caches, ownership boundaries, the 14 extension points that must survive |
| [02-performance-audit.md](02-performance-audit.md) | Measured bottlenecks B1–B12 with root cause and evidence; the framework-overhead decomposition; the boundary arithmetic |
| [03-engine-design.md](03-engine-design.md) | Batch-boundary architecture, type codes, plan compile-and-replay, memory model, GIL policy |
| [04-hydration-engine-spec.md](04-hydration-engine-spec.md) | `RowPlan`: eligibility, the six semantics that must be preserved exactly, execution |
| [05-validation-engine-spec.md](05-validation-engine-spec.md) | `FieldPlan`: eligibility, `IntFacet` cast semantics, error-shape contract |
| [06-python-fixes.md](06-python-fixes.md) | Six verified Python-only fixes, plus the rejected-components register |
| [07-testing-strategy.md](07-testing-strategy.md) | Parity strategy, the highest-severity tests, memory and concurrency gates |
| [08-benchmark-strategy.md](08-benchmark-strategy.md) | Methodology, missing benchmarks, regression gates |
| [09-implementation-plan.md](09-implementation-plan.md) | Milestones M0–M7 with exit gates, risk register, and stop conditions |
| [10-results.md](10-results.md) | **What actually happened.** Gates met and missed, corrections to `04`/`05`/`06`, honest assessment |
| [11-phase2-coverage-expansion.md](11-phase2-coverage-expansion.md) | **Phase 2.** Choice/Literal/Enum/Set/Tuple/Decimal/Duration coverage, the two-axis type system, and why each addition is exact |

---

## Outcome in one line

**2.08× end-to-end on a real 100-row query** — hydration 3.9×, validation 16.9×
on eligible shapes — with the whole native layer removable via
`AQUILIA_DATAENGINE=0`.

---

## The three findings that shape everything

**1. The cost is interpretation, not conversion.**

| Path | Total | Irreducible conversion | Framework overhead |
|---|---|---|---|
| `from_row`, 8 columns | 3,002 ns | 859 ns | **71%** |
| `Sigil.validate`, 8 fields | 5,034 ns | 499 ns | **90%** |

**2. A per-field native API cannot win.** The Python↔native boundary costs
43.3 ns with real arguments. Six of eight scalar conversions cost *less* than
that, because CPython's `fromisoformat`, `int()`, and `float()` are already C.
Only UUID (354 ns, pure-Python `__init__`) and JSON (379 ns) win per call.

**3. A batch API makes the boundary free.** One crossing over a 100-row page is
0.05 ns per value. Row shape is invariant within a result set, so the
interpretation can be compiled once and replayed — which is the design.

---

## Reproducing the measurements

```bash
python benchmarks/models/profile_baseline.py --json benchmarks/models/baseline.json
```

Run on an idle machine. `benchmarks/models/baseline.json` is the committed
baseline; `06`'s exit gate compares against it.

---

## Relationship to `docs/engine/`

`docs/engine/` covers the **request-path** engine (`aquilia/_core`: router and
request context), which is implemented and shipped. This set covers a proposed
**data-path** engine (`aquilia/_dataengine`). They are independent: separate
loaders, separate env vars (`AQUILIA_ENGINE` vs `AQUILIA_DATAENGINE`), separate
CI gates.

`docs/engine/09-results.md` is worth reading first as precedent. It records a
project that delivered 10–13% against a projected 2.5×, because Python-side
fixes had already captured most of the available gain before any C++ was
written. `09-implementation-plan.md` §6 treats that as a likely outcome here and
defines the gates to discover it early.
