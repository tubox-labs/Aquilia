"""Python <-> native boundary cost, measured against the installed _core module.

``docs/models-engine/02`` section 3 measures 43.3 ns for a two-string-argument call on
macOS arm64, and the entire per-field-vs-batch decision hinges on that number:
six of eight scalar conversions cost less than one crossing, which is what
refuted a per-field native API. ``08`` section 2.3 requires it be re-measured per
platform rather than assumed, because the Phase 9 project got burned by exactly
this -- it assumed ~60 ns, measured 7.7 ns, and three component decisions
inverted.

This measures the *existing* ``aquilia._core`` extension, so it needs no new
build. If ``_core`` is absent the script says so and exits cleanly rather than
failing: a pure-Python install legitimately has no boundary to measure.

Run:  python benchmarks/models/boundary.py
      python benchmarks/models/boundary.py --json out.json
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import timeit
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

REPEAT = 5


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()

    print("=" * 78)
    print("PYTHON <-> NATIVE BOUNDARY COST")
    print("=" * 78)
    print(f"\n  platform : {platform.system()} {platform.machine()}")
    print(f"  python   : {platform.python_version()}")

    try:
        from aquilia import _core  # type: ignore[attr-defined]
    except ImportError as exc:
        print(f"\n  aquilia._core not importable ({exc}).")
        print("  Nothing to measure -- a pure-Python install has no boundary.")
        return 0

    results: dict[str, float] = {}

    # A bare call: the floor of crossing at all, with no argument marshalling.
    if hasattr(_core, "noop"):
        noop = _core.noop
        n = 2_000_000
        results["noop_ns"] = min(timeit.repeat(lambda: noop(), repeat=REPEAT, number=n)) / n * 1e9
        print(f"\n  noop() bare call                 {results['noop_ns']:8.1f} ns")
    else:
        print("\n  _core.noop() absent -- skipping the bare-call measurement")

    # A call with two string arguments: the realistic shape, since marshalling
    # is most of the cost. This is the number the design decisions use.
    router = None
    if hasattr(_core, "Router"):
        try:
            router = _core.Router()
            router.add_static("GET", "/bench/path", 0)
            router.freeze()
        except Exception as exc:  # pragma: no cover - depends on _core's API
            print(f"  Router setup failed ({exc}) -- skipping the 2-arg measurement")
            router = None

    if router is not None and hasattr(router, "match"):
        n = 1_000_000
        match = router.match
        results["call_2str_ns"] = (
            min(timeit.repeat(lambda: match("GET", "/bench/path"), repeat=REPEAT, number=n)) / n * 1e9
        )
        print(f"  match() with 2 string args       {results['call_2str_ns']:8.1f} ns")

    if "call_2str_ns" in results:
        b = results["call_2str_ns"]
        print("\n  amortised over a batch (one crossing per result set):")
        for rows, fields in ((1, 8), (10, 8), (100, 8), (1000, 8)):
            per_value = b / (rows * fields)
            print(f"    {rows:5d} rows x {fields} fields = {rows * fields:6d} values  ->  {per_value:8.3f} ns/value")
        print("\n  At page-sized batches the boundary is free. This is why the engine")
        print("  crosses once per result set and never once per field.")

    if args.json:
        args.json.write_text(json.dumps(results, indent=2, sort_keys=True))
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
