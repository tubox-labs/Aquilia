"""Micro-benchmark: native FieldPlan coverage before and after Phase 2.

Measures ``Contract.is_sealed()`` throughput on contracts built from the facets
Phase 2 added, with the native engine enabled and disabled. The engine is
toggled through ``AQUILIA_DATAENGINE`` in a subprocess rather than in-process,
because ``DATAENGINE_NATIVE`` is resolved once at import time and a reload would
leave already-imported modules holding the old decision.

Run::

    python benchmarks/contracts/microbench_tier2.py
"""

from __future__ import annotations

import json
import os
import statistics
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Each case is (name, contract source, payload). The contract bodies are text so
# the child process can build them without importing this module.
CASES = [
    (
        "choice",
        """
class C(Contract):
    status = ChoiceFacet(choices=["pending", "active", "done"])
""",
        {"status": "active"},
    ),
    (
        "enum",
        """
class Colour(Enum):
    RED = "red"
    GREEN = "green"

class C(Contract):
    colour = EnumFacet(enum_class=Colour)
""",
        {"colour": "red"},
    ),
    (
        "decimal",
        """
class C(Contract):
    price = DecimalFacet(max_digits=6, decimal_places=2)
""",
        {"price": "19.99"},
    ),
    (
        "set",
        """
class C(Contract):
    tags = SetFacet(child=TextFacet(), max_items=8)
""",
        {"tags": ["a", "b", "c", "d"]},
    ),
    (
        "tuple",
        """
class C(Contract):
    coords = TupleFacet(child=FloatFacet())
""",
        {"coords": [1.0, 2.5, 3.75]},
    ),
    (
        "duration",
        """
class C(Contract):
    span = DurationFacet()
""",
        {"span": 90},
    ),
    (
        "list_int_bounded",
        """
class C(Contract):
    values = ListFacet(child=IntFacet(), min_items=1, max_items=16)
""",
        {"values": [1, 2, 3, 4, 5, 6, 7, 8]},
    ),
    (
        "kitchen_sink",
        """
class Colour(Enum):
    RED = "red"
    GREEN = "green"

class C(Contract):
    name = TextFacet(min_length=2, max_length=20)
    count = IntFacet(min_value=0, multiple_of=5)
    colour = EnumFacet(enum_class=Colour)
    price = DecimalFacet(max_digits=6, decimal_places=2)
    tags = SetFacet(child=TextFacet(), max_items=3)
    coords = TupleFacet(child=FloatFacet())
    when = DateFacet()
    span = DurationFacet()
    active = BoolFacet()
""",
        {
            "name": "Widget",
            "count": 10,
            "colour": "red",
            "price": "19.99",
            "tags": ["a", "b"],
            "coords": [1.0, 2.5],
            "when": "2026-01-15",
            "span": 90,
            "active": True,
        },
    ),
]

_CHILD = """
import json, sys, timeit
from enum import Enum
from aquilia.contracts import Contract
from aquilia.contracts.facets import (
    BoolFacet, ChoiceFacet, DateFacet, DecimalFacet, DurationFacet, EnumFacet,
    FloatFacet, IntFacet, ListFacet, SetFacet, TextFacet, TupleFacet, UUIDFacet,
)
from aquilia.contracts._native_plan import field_plan_for
from aquilia._dataengine_loader import DATAENGINE_NATIVE

source, payload, repeat, number = json.loads(sys.stdin.read())
ns = dict(globals())
exec(source, ns)
C = ns["C"]

compiled = field_plan_for(C)
covered = len(compiled.plan) if compiled else 0
escaped = sorted(compiled.escaped) if compiled else None

def run():
    C(data=payload).is_sealed()

run()  # warm the plan cache and any lazy imports
timings = timeit.repeat(run, repeat=repeat, number=number)
print(json.dumps({
    "native": DATAENGINE_NATIVE,
    "covered": covered,
    "escaped": escaped,
    "best_ns": min(timings) / number * 1e9,
}))
"""


def measure(source: str, payload: dict, *, native: bool, repeat: int = 7, number: int = 20000) -> dict:
    """Run one case in a child process with the engine forced on or off."""
    env = dict(os.environ)
    env["AQUILIA_DATAENGINE"] = "1" if native else "0"
    env["PYTHONPATH"] = str(REPO_ROOT)
    proc = subprocess.run(
        [sys.executable, "-c", _CHILD],
        input=json.dumps([source, payload, repeat, number]),
        capture_output=True,
        text=True,
        env=env,
        cwd=REPO_ROOT,
        check=True,
    )
    return json.loads(proc.stdout.strip().splitlines()[-1])


def main() -> int:
    print(f"{'case':<20} {'python (ns)':>12} {'native (ns)':>12} {'speedup':>9}  coverage")
    print("-" * 74)

    speedups = []
    for name, source, payload in CASES:
        py = measure(source, payload, native=False)
        nat = measure(source, payload, native=True)

        if not nat["native"]:
            print(f"{name:<20} {'-':>12} {'-':>12} {'-':>9}  native engine not built")
            continue

        speedup = py["best_ns"] / nat["best_ns"]
        speedups.append(speedup)
        coverage = f"{nat['covered']} field(s)"
        if nat["escaped"]:
            coverage += f", escaped={nat['escaped']}"
        print(f"{name:<20} {py['best_ns']:>12.1f} {nat['best_ns']:>12.1f} {speedup:>8.2f}x  {coverage}")

    if speedups:
        print("-" * 74)
        print(f"{'median':<20} {'':>12} {'':>12} {statistics.median(speedups):>8.2f}x")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
