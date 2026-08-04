"""End-to-end query decomposition: what fraction of a real read is hydration?

This is the benchmark that decides whether a native data engine is worth
building at all. Every ROI argument in ``docs/models-engine/02`` rests on
component numbers -- ``from_row`` costs 2.9 us for 8 columns, a 100-row page
costs ~300 us -- but a component number has no denominator. If a real 100-row
query spends 90% of its time in the sqlite driver and the event loop, then
halving hydration buys 5% end-to-end and the second C++ extension is not worth
its build, CI, and maintenance cost.

``docs/models-engine/09-implementation-plan.md`` M1 states the gate:

    hydration must be >= 25% of a real 100-row query. If it is not, STOP.

So this script reports a percentage breakdown of the real async path:

    QuerySet.all()
      -> adapter.fetch_all       driver: sqlite3 execute + fetchall,
                                 dispatched to a thread pool executor
           -> row_factory        Row construction (B1 + B2)
      -> _hydrate_rows           from_row per row (B3-B6)

The driver stage is measured *including* the executor round-trip, because that
is what a request actually pays. Measuring raw ``sqlite3`` in-thread would
flatter hydration's share by hiding real cost in the denominator, which is the
opposite of what this gate is for.

Run:  python benchmarks/models/e2e_query.py
      python benchmarks/models/e2e_query.py --json out.json --rows 100
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# Import aquilia.db before aquilia.sqlite: the package has a pre-existing
# import cycle (sqlite -> db -> backends.sqlite -> sqlite) recorded in
# docs/models-engine/06-python-fixes.md section 6. Importing db first resolves it.
# isort/I001 is suppressed because this order is load-bearing, not stylistic --
# sorting these two imports makes the script crash on a fresh interpreter.
import aquilia.db  # noqa: E402, F401, I001

from aquilia.sqlite._rows import row_factory  # noqa: E402

REPEAT = 7

COLUMNS = ("name", "count", "ratio", "active", "created", "price", "ident", "payload")
SQL = f"SELECT id, {', '.join(COLUMNS)} FROM wide LIMIT ?"


def build_model():
    """Same field mix as profile_baseline.py, so numbers are comparable."""
    from aquilia.models import Model
    from aquilia.models.fields_module import (
        BooleanField,
        CharField,
        DateTimeField,
        DecimalField,
        FloatField,
        IntegerField,
        JSONField,
        UUIDField,
    )

    class Wide(Model):
        name = CharField(max_length=100)
        count = IntegerField()
        ratio = FloatField()
        active = BooleanField()
        created = DateTimeField(null=True)
        price = DecimalField(max_digits=10, decimal_places=2, null=True)
        ident = UUIDField(null=True)
        payload = JSONField(null=True)

        class Meta:
            table_name = "wide"
            app_label = "bench"

    return Wide


def seed(conn: sqlite3.Connection, rows: int) -> None:
    conn.execute(
        "CREATE TABLE wide (id INTEGER PRIMARY KEY, name TEXT, count INTEGER, "
        "ratio REAL, active INTEGER, created TEXT, price TEXT, ident TEXT, payload TEXT)"
    )
    conn.executemany(
        "INSERT INTO wide (name, count, ratio, active, created, price, ident, payload) VALUES (?,?,?,?,?,?,?,?)",
        [
            (
                f"user{i}",
                i,
                i * 1.5,
                i % 2,
                "2026-01-15T10:30:00",
                "19.99",
                "550e8400-e29b-41d4-a716-446655440000",
                '{"k": "v"}',
            )
            for i in range(rows)
        ],
    )
    conn.commit()


def _min_of(fn, iterations: int) -> float:
    """Best-of-REPEAT seconds per call. Minimum for the same reason the rest of
    the harness uses it: this is CPU-bound, so noise only ever adds time."""
    best = float("inf")
    for _ in range(REPEAT):
        t0 = time.perf_counter()
        for _ in range(iterations):
            fn()
        best = min(best, (time.perf_counter() - t0) / iterations)
    return best


async def _amin_of(fn, iterations: int) -> float:
    best = float("inf")
    for _ in range(REPEAT):
        t0 = time.perf_counter()
        for _ in range(iterations):
            await fn()
        best = min(best, (time.perf_counter() - t0) / iterations)
    return best


async def measure(rows: int, iterations: int) -> dict[str, float]:
    """Decompose a real `rows`-row read into driver / row-build / hydration."""
    Wide = build_model()  # noqa: N806

    conn = sqlite3.connect(":memory:", check_same_thread=False)
    seed(conn, rows)

    loop = asyncio.get_running_loop()

    # -- Stage 1: driver only, no row_factory, dispatched to the executor.
    # This is the honest denominator component: an async request pays the
    # thread-pool round-trip, so it belongs in the total.
    conn.row_factory = None

    async def driver_only():
        return await loop.run_in_executor(None, lambda: conn.execute(SQL, (rows,)).fetchall())

    t_driver = await _amin_of(driver_only, iterations)

    # -- Stage 2: driver + row_factory (adds B1 key tuple + B2 Row construction)
    conn.row_factory = row_factory

    async def driver_and_rows():
        return await loop.run_in_executor(None, lambda: conn.execute(SQL, (rows,)).fetchall())

    t_driver_rows = await _amin_of(driver_and_rows, iterations)

    # -- Stage 3: hydration of those same rows (B3-B6)
    row_objs = await driver_and_rows()
    assert len(row_objs) == rows, f"expected {rows} rows, got {len(row_objs)}"
    from_row = Wide.from_row
    t_hydrate = _min_of(lambda: [from_row(r) for r in row_objs], iterations)

    # -- Stage 3b: the same hydration through the native RowPlan, when the shape
    # is eligible. Reported alongside rather than instead of the Python number,
    # so the end-to-end effect is measured rather than inferred by arithmetic.
    t_hydrate_native = None
    try:
        from aquilia.models._native_plan import row_plan_for

        plan = row_plan_for(Wide, tuple(row_objs[0].keys()))
        if plan is not None and plan.execute(list(row_objs)) is not None:
            rows_list = list(row_objs)
            t_hydrate_native = _min_of(lambda: plan.execute(rows_list), iterations)
    except Exception:
        # The native engine is optional; its absence is not a benchmark failure.
        t_hydrate_native = None

    conn.close()

    t_rowbuild = max(t_driver_rows - t_driver, 0.0)
    total = t_driver_rows + t_hydrate

    result = {
        "rows": float(rows),
        "driver_us": t_driver * 1e6,
        "rowbuild_us": t_rowbuild * 1e6,
        "hydrate_us": t_hydrate * 1e6,
        "total_us": total * 1e6,
        "hydrate_pct": t_hydrate / total * 100.0,
        # Row construction is hydration-adjacent: it is framework cost on the
        # read path that a native engine could also remove (04 section 6), so the
        # gate is reported both ways rather than only the flattering one.
        "hydrate_plus_rowbuild_pct": (t_hydrate + t_rowbuild) / total * 100.0,
    }
    if t_hydrate_native is not None:
        native_total = t_driver_rows + t_hydrate_native
        result["hydrate_native_us"] = t_hydrate_native * 1e6
        result["total_native_us"] = native_total * 1e6
        result["hydrate_speedup"] = t_hydrate / t_hydrate_native
        result["end_to_end_speedup"] = total / native_total
    return result


def report(res: dict[str, float]) -> None:
    rows = int(res["rows"])
    print(f"\n-- real query, {rows} rows x {len(COLUMNS) + 1} columns (async, in-memory sqlite) --")
    for label, key in (
        ("driver (execute+fetchall+executor)", "driver_us"),
        ("row_factory + Row construction", "rowbuild_us"),
        ("hydration (from_row)", "hydrate_us"),
    ):
        pct = res[key] / res["total_us"] * 100.0
        print(f"  {label:36} {res[key]:9.1f} us  {pct:5.1f}%")
    print(f"  {'TOTAL':36} {res['total_us']:9.1f} us  100.0%")
    print(f"\n  hydration alone            {res['hydrate_pct']:5.1f}%")
    print(f"  hydration + row build      {res['hydrate_plus_rowbuild_pct']:5.1f}%")
    if "hydrate_native_us" in res:
        print("\n  with the native RowPlan:")
        print(f"    {'hydration (native)':34} {res['hydrate_native_us']:9.1f} us  ({res['hydrate_speedup']:.2f}x)")
        print(
            f"    {'TOTAL (native)':34} {res['total_native_us']:9.1f} us  ({res['end_to_end_speedup']:.2f}x end-to-end)"
        )
    else:
        print("\n  (native RowPlan unavailable or shape ineligible -- Python path only)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=100)
    ap.add_argument("--iterations", type=int, default=200)
    ap.add_argument("--json", type=Path)
    ap.add_argument("--all-sizes", action="store_true", help="sweep 1/10/100/1000 rows")
    args = ap.parse_args()

    print("=" * 78)
    print("END-TO-END QUERY DECOMPOSITION  (M1 gate: hydration >= 25% of a real query)")
    print("=" * 78)

    sizes = [1, 10, 100, 1000] if args.all_sizes else [args.rows]
    out = {}
    for n in sizes:
        iters = max(20, args.iterations // max(1, n // 50))
        res = asyncio.run(measure(n, iters))
        report(res)
        out[f"rows_{n}"] = res

    gate = out.get(f"rows_{args.rows}") or out[f"rows_{sizes[-1]}"]
    print("\n" + "=" * 78)
    verdict = "PASS" if gate["hydrate_pct"] >= 25.0 else "FAIL"
    print(f"M1 GATE: hydration {gate['hydrate_pct']:.1f}% of a {int(gate['rows'])}-row query -> {verdict}")
    if verdict == "FAIL":
        print("  Per 09 section 2 M1 this is a STOP condition: driver and I/O dominate,")
        print("  and the M0 Python fixes are the whole deliverable.")
        print(f"  (hydration + row build together: {gate['hydrate_plus_rowbuild_pct']:.1f}%)")
    print("=" * 78)

    if args.json:
        args.json.write_text(json.dumps(out, indent=2, sort_keys=True))
        print(f"wrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
