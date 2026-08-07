"""Micro-benchmarks for the ORM hydration engine.

Isolates row-to-model hydration from SQL execution so the native ``RowPlan``
speedup is measured directly. The database is never touched: rows are
synthesised as dicts in exactly the shape the driver returns, because the goal
is to measure the interpretation loop, not the disk.

Each case reports:

``python_us``
    Hydration via ``Model.from_row`` per row, the fallback path.
``native_us``
    Hydration via one ``RowPlan.execute`` call for the whole batch.
``per_row_ns``
    Native cost per row, which is the number that matters for large pages.

A case reporting ``plan=None`` means the plan was rejected at compile time and
the ORM would run the Python path -- that is a coverage finding, not an error.

Run directly::

    python benchmarks/engine/microbench_orm.py
"""

from __future__ import annotations

import timeit
from typing import Any

from aquilia.models import Model
from aquilia.models import fields_module as fm
from aquilia.models._native_plan import _PLAN_CACHE, row_plan_for

REPEATS = 5
# Batch sizes chosen to bracket a realistic page: a detail view, a normal page,
# and a large export. The per-row cost should fall as the batch grows, because
# the boundary crossing amortises.
BATCH_SIZES = (1, 100, 1000)


class Row(Model):
    """Scalar-only model -- the shape the native plan covers completely."""

    table = "microbench_row"

    name = fm.CharField(max_length=100)
    count = fm.IntegerField()
    ratio = fm.FloatField()
    enabled = fm.BooleanField()


def _make_rows(n: int) -> list[dict[str, Any]]:
    """Build ``n`` driver-shaped row dicts.

    Values vary per row so the measurement cannot benefit from the interpreter
    caching one identical object.
    """
    return [
        {"id": i, "name": f"row-{i}", "count": i, "ratio": i * 1.5, "enabled": i % 2 == 0}
        for i in range(n)
    ]


def _time(fn: Any, iterations: int) -> float:
    """Return the minimum per-call time in microseconds across repeats."""
    samples = timeit.repeat(fn, number=iterations, repeat=REPEATS)
    return min(samples) / iterations * 1e6


def main() -> None:
    """Measure native vs Python hydration across batch sizes."""
    cols = tuple(Row._col_to_attr.keys())
    _PLAN_CACHE.clear()
    plan = row_plan_for(Row, cols)

    print("=" * 78)
    print("ORM hydration -- native RowPlan vs Model.from_row")
    print("=" * 78)
    print(f"columns: {cols}")
    print(f"plan   : {'compiled' if plan is not None else 'None (rejected -- Python path)'}")
    print()
    print(f"{'batch':>8}{'python us':>12}{'native us':>12}{'speedup':>10}{'native ns/row':>16}")
    print("-" * 78)

    for size in BATCH_SIZES:
        rows = _make_rows(size)
        # Larger batches need fewer iterations to stay within a sane runtime.
        iterations = max(20, 20_000 // size)

        py_us = _time(lambda: [Row.from_row(r) for r in rows], iterations)

        if plan is None:
            print(f"{size:>8}{py_us:>12.2f}{'—':>12}{'—':>10}{'—':>16}")
            continue

        # A None return means the plan declined this batch at runtime; timing it
        # would report the Python fallback as if it were the native path.
        if plan.execute(rows) is None:
            print(f"{size:>8}{py_us:>12.2f}{'declined':>12}{'—':>10}{'—':>16}")
            continue

        nat_us = _time(lambda: plan.execute(rows), iterations)
        speedup = py_us / nat_us if nat_us > 0 else 0.0
        per_row_ns = nat_us * 1000.0 / size
        print(f"{size:>8}{py_us:>12.2f}{nat_us:>12.2f}{speedup:>9.2f}x{per_row_ns:>16.1f}")

    print("-" * 78)
    print("per-row cost should fall as the batch grows: the boundary crossing amortises.")


if __name__ == "__main__":
    main()
