"""Micro-benchmark: native FieldPlan coverage for the Phase 2 Tier 3 additions.

Measures ``Contract.is_sealed()`` throughput on contracts built from the facets
Tier 3 added -- nested Contracts, ``TextFacet.pattern``, ``DictFacet``, and
``BytesFacet`` -- with the native engine enabled and disabled.

Nested Contracts are the case worth watching: the Python path instantiates the
child Contract per nested field per payload, so eliminating that is a different
kind of saving from the per-field dispatch the scalar cases recover.

The engine is toggled through ``AQUILIA_DATAENGINE`` in a subprocess rather than
in-process, because ``DATAENGINE_NATIVE`` is resolved once at import time and a
reload would leave already-imported modules holding the old decision.

Run::

    python benchmarks/contracts/microbench_tier3.py
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
        "nested_1_field",
        """
class Inner(Contract):
    a: int
    b: str

class C(Contract):
    inner: Inner
    n: int
""",
        {"inner": {"a": 1, "b": "x"}, "n": 5},
    ),
    (
        "nested_wide_child",
        """
class Inner(Contract):
    a: int
    b: str
    c: float
    d: bool
    e: str

class C(Contract):
    inner: Inner
    n: int
""",
        {"inner": {"a": 1, "b": "x", "c": 1.5, "d": True, "e": "y"}, "n": 5},
    ),
    (
        "nested_many_8",
        """
class Inner(Contract):
    a: int
    b: str

class C(Contract):
    items: list[Inner]
    label: str
""",
        {"items": [{"a": i, "b": "x"} for i in range(8)], "label": "L"},
    ),
    (
        "nested_3_levels",
        """
class Deep(Contract):
    x: int

class Middle(Contract):
    deep: Deep
    m: str

class C(Contract):
    middle: Middle
    o: int
""",
        {"middle": {"deep": {"x": 1}, "m": "s"}, "o": 2},
    ),
    (
        "pattern",
        """
class C(Contract):
    code = TextFacet(pattern=r"^[A-Z]{2,8}$")
""",
        {"code": "ABCDE"},
    ),
    (
        "dict_typed_8",
        """
class C(Contract):
    meta = DictFacet(value_facet=IntFacet())
""",
        {"meta": {f"k{i}": i for i in range(8)}},
    ),
    (
        "dict_plain_8",
        """
class C(Contract):
    meta = DictFacet()
""",
        {"meta": {f"k{i}": i for i in range(8)}},
    ),
    (
        "bytes",
        """
class C(Contract):
    blob = BytesFacet(min_length=1, max_length=64)
""",
        {"blob": b"payload-bytes"},
    ),
    (
        "tier3_sink",
        """
class Inner(Contract):
    a: int
    b: str

class C(Contract):
    inner: Inner
    rows: list[Inner]
    code = TextFacet(pattern=r"^[A-Z]{2,}$")
    meta = DictFacet(value_facet=IntFacet(), max_keys=4)
    blob = BytesFacet(min_length=1)
    n: int
""",
        {
            "inner": {"a": 1, "b": "x"},
            "rows": [{"a": 2, "b": "y"}, {"a": 3, "b": "z"}],
            "code": "AB",
            "meta": {"k": 1, "j": 2},
            "blob": b"z",
            "n": 7,
        },
    ),
]

_CHILD = """
import json, sys, timeit
from aquilia.contracts import Contract
from aquilia.contracts.facets import (
    BoolFacet, BytesFacet, DateFacet, DictFacet, FloatFacet, IntFacet,
    ListFacet, TextFacet, UUIDFacet,
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


def _jsonable(value):
    """bytes payloads must survive the JSON round-trip to the child process."""
    if isinstance(value, bytes):
        return {"__bytes__": value.decode("latin-1")}
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonable(v) for v in value]
    return value


_REHYDRATE = """
def _rehydrate(v):
    if isinstance(v, dict):
        if "__bytes__" in v and len(v) == 1:
            return v["__bytes__"].encode("latin-1")
        return {k: _rehydrate(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_rehydrate(x) for x in v]
    return v
payload = _rehydrate(payload)
"""


def measure(source: str, payload: dict, *, native: bool, repeat: int = 7, number: int = 20000) -> dict:
    """Run one case in a child process with the engine forced on or off."""
    env = dict(os.environ)
    env["AQUILIA_DATAENGINE"] = "1" if native else "0"
    env["PYTHONPATH"] = str(REPO_ROOT)
    child = _CHILD.replace('C = ns["C"]', 'C = ns["C"]\n' + _REHYDRATE)
    proc = subprocess.run(
        [sys.executable, "-c", child],
        input=json.dumps([source, _jsonable(payload), repeat, number]),
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
