"""Conversion floors: the cheapest possible Python that produces each object.

Promoted from a scratch prototype per ``docs/models-engine/08`` section 2.2.

This is the measurement that refuted the per-field native API in ``02`` section 3, so
it belongs in the committed harness rather than in /tmp. The floor is what any
implementation -- native or not -- must pay to produce an identical Python
object. A native conversion can only win if its floor exceeds the boundary
crossing cost measured by ``boundary.py``.

The verdict column is computed against the *measured* boundary cost rather than
the 43.3 ns arm64 figure hardcoded in the docs, so this stays honest on other
platforms.

Run:  python benchmarks/models/conversion_floors.py
      python benchmarks/models/conversion_floors.py --json out.json
"""

from __future__ import annotations

import argparse
import json
import timeit
import uuid
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path

REPEAT = 5

# (label, callable, iterations) -- each produces the exact object the ORM would.
CASES = [
    ("str_passthrough", lambda: "hello world", 2_000_000),
    ("int_from_str", lambda: int("12345"), 1_000_000),
    ("float_from_str", lambda: float("1.5"), 1_000_000),
    ("bool_from_int", lambda: bool(1), 2_000_000),
    ("date_fromisoformat", lambda: date.fromisoformat("2026-01-15"), 1_000_000),
    ("datetime_fromisoformat", lambda: datetime.fromisoformat("2026-01-15T10:30:00"), 1_000_000),
    ("time_fromisoformat", lambda: time.fromisoformat("10:30:00"), 1_000_000),
    ("decimal_from_str", lambda: Decimal("19.99"), 500_000),
    ("uuid_from_str", lambda: uuid.UUID("550e8400-e29b-41d4-a716-446655440000"), 200_000),
    ("bytes_from_str", lambda: b"abcdefgh", 2_000_000),
]


def _json_case():
    import json as _json

    return _json.loads('{"k": "v"}')


CASES.append(("json_loads", _json_case, 200_000))


def measure() -> dict[str, float]:
    results: dict[str, float] = {}
    for label, fn, number in CASES:
        per_op = min(timeit.repeat(fn, repeat=REPEAT, number=number)) / number
        results[label] = per_op * 1e9
    return results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path)
    ap.add_argument(
        "--boundary-ns",
        type=float,
        default=None,
        help="measured boundary cost; defaults to reading boundary.json if present",
    )
    args = ap.parse_args()

    boundary = args.boundary_ns
    if boundary is None:
        bj = Path(__file__).with_name("boundary.json")
        if bj.exists():
            boundary = json.loads(bj.read_text()).get("call_2str_ns")
    if boundary is None:
        boundary = 43.3  # the arm64 figure from 02 section 3, clearly labelled below

    print("=" * 78)
    print("CONVERSION FLOORS -- cheapest Python producing an identical object")
    print("=" * 78)
    print(f"\nboundary cost used for the verdict: {boundary:.1f} ns")
    print("(a native per-field conversion only wins if its floor exceeds this)\n")

    results = measure()
    for label, ns in results.items():
        verdict = "WIN" if ns > boundary else ("marginal" if ns > boundary * 0.9 else "LOSS")
        print(f"  {label:26} {ns:8.1f} ns   {verdict}")

    wins = [k for k, v in results.items() if v > boundary]
    print(f"\n  native-viable conversions: {', '.join(wins) if wins else 'none'}")
    print("  everything else costs less than one boundary crossing -> batch API only")

    if args.json:
        args.json.write_text(json.dumps(results, indent=2, sort_keys=True))
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
