"""Scaling shape along the rows / columns / fields axes.

``docs/models-engine/08`` section 3 requires costs be checked for *shape*, not just
magnitude: a per-row cost that is O(columns^2) would be invisible at the 8
columns the rest of the harness measures, and would only surface in production
on a wide table.

The rows axis doubles as the validation of the batch-amortisation claim in
``02`` section 3. If per-row cost does not flatten by ~10 rows, the boundary is not
being amortised the way the engine design assumes.

Reported as cost-per-unit at each point plus a growth ratio between adjacent
points. A linear cost holds the per-unit number flat; anything trending upward
is superlinear and worth investigating before it reaches a native plan.

Run:  python benchmarks/models/scaling.py
      python benchmarks/models/scaling.py --json out.json
"""

from __future__ import annotations

import argparse
import json
import sys
import timeit
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

REPEAT = 5

ROW_TEMPLATE = {
    "name": "alice",
    "count": 42,
    "ratio": 1.5,
    "active": 1,
    "created": "2026-01-15T10:30:00",
    "price": "19.99",
    "ident": "550e8400-e29b-41d4-a716-446655440000",
    "payload": '{"k": "v"}',
}


def _bench(fn, number: int) -> float:
    return min(timeit.repeat(fn, repeat=REPEAT, number=number)) / number


def build_model_ncols(n_cols: int):
    """A model with `n_cols` cheap CharFields, to isolate the columns axis."""
    from aquilia.models import Model
    from aquilia.models.fields_module import CharField

    ns = {f"c{i}": CharField(max_length=50) for i in range(n_cols)}
    meta = type("Meta", (), {"table_name": f"scale{n_cols}", "app_label": "bench"})
    ns["Meta"] = meta
    return type(f"Scale{n_cols}", (Model,), ns)


def build_contract_nfields(n: int):
    """A contract with `n` str fields, to isolate the fields axis."""
    from aquilia.contracts import Contract

    ns = {"__annotations__": {f"f{i}": str for i in range(n)}}
    return type(f"Payload{n}", (Contract,), ns)


def axis_rows(results: dict) -> None:
    from benchmarks.models.profile_baseline import build_model

    Wide = build_model()  # noqa: N806
    from_row = Wide.from_row
    print("\n-- rows per batch (validates batch amortisation) --")
    prev = None
    for n in (1, 10, 100, 1000, 10000):
        rows = [ROW_TEMPLATE] * n
        number = max(5, 2000 // n)
        total = _bench(lambda rows=rows: [from_row(r) for r in rows], number)
        per_row = total / n * 1e9
        results[f"rows_{n}_per_row_ns"] = per_row
        delta = "" if prev is None else f"  ({per_row / prev:+.2f}x vs previous)"
        print(f"  {n:6d} rows   {per_row:8.1f} ns/row{delta}")
        prev = per_row


def axis_columns(results: dict) -> None:
    print("\n-- columns per row (expect linear: flat ns/column) --")
    prev = None
    for n in (4, 8, 16, 32, 64):
        model = build_model_ncols(n)
        row = {f"c{i}": f"v{i}" for i in range(n)}
        from_row = model.from_row
        total = _bench(lambda from_row=from_row, row=row: from_row(row), 20_000)
        per_col = total / n * 1e9
        results[f"cols_{n}_per_col_ns"] = per_col
        delta = "" if prev is None else f"  ({per_col / prev:+.2f}x vs previous)"
        print(f"  {n:6d} cols   {per_col:8.1f} ns/col   (row: {total * 1e9:8.1f} ns){delta}")
        prev = per_col


def axis_fields(results: dict) -> None:
    print("\n-- fields per payload (expect linear: flat ns/field) --")
    prev = None
    for n in (4, 8, 16, 32):
        contract = build_contract_nfields(n)
        sigil = contract._sigil
        payload = {f"f{i}": f"v{i}" for i in range(n)}
        total = _bench(lambda sigil=sigil, payload=payload: sigil.validate(payload), 10_000)
        per_field = total / n * 1e9
        results[f"fields_{n}_per_field_ns"] = per_field
        delta = "" if prev is None else f"  ({per_field / prev:+.2f}x vs previous)"
        print(f"  {n:6d} fields {per_field:8.1f} ns/field (payload: {total * 1e9:8.1f} ns){delta}")
        prev = per_field


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()

    print("=" * 78)
    print("SCALING SHAPE -- rows / columns / fields")
    print("=" * 78)

    results: dict[str, float] = {}
    axis_rows(results)
    axis_columns(results)
    axis_fields(results)

    print("\n  A flat per-unit column means linear. A rising one means superlinear")
    print("  cost that 8-column measurements would never have surfaced.")

    if args.json:
        args.json.write_text(json.dumps(results, indent=2, sort_keys=True))
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
