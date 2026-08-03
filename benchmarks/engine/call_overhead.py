"""Measure nanobind per-call overhead against the Python operations the engine
would replace.

This is the number that decides Phases 9E (native DI resolver) and 9G (native
binding cache). Both target code paths that are already a single Python dict
lookup after the Phase 9A fixes:

    di/core.py       self._cache.get(cache_key, _CACHE_SENTINEL)
    controller/engine.py  ControllerEngine._type_hints_cache.get(fid)

A native replacement can only win if crossing the binding boundary costs less
than the dict lookup it removes. Crossing costs at minimum one `noop()` call.

Run:  python benchmarks/engine/call_overhead.py
"""

from __future__ import annotations

import timeit

REPEAT = 7
NUMBER = 200_000


def _ns(stmt: str, setup: str) -> float:
    """Best-of-REPEAT nanoseconds per operation.

    Minimum, not mean: this measures a CPU-bound operation where every source of
    noise (scheduling, turbo, other processes) only ever adds time.
    """
    timer = timeit.Timer(stmt, setup=setup)
    return min(timer.repeat(REPEAT, NUMBER)) / NUMBER * 1e9


def main() -> int:
    try:
        from aquilia import _core
    except ImportError:
        print("native engine not built -- nothing to measure")
        return 1

    results: dict[str, float] = {}

    results["nanobind noop() call"] = _ns("noop()", "from aquilia._core import noop")

    results["python dict .get() hit"] = _ns(
        "d.get(k)", "d = {f'k{i}': i for i in range(64)}; k = 'k32'"
    )

    results["python dict [] hit"] = _ns(
        "d[k]", "d = {f'k{i}': i for i in range(64)}; k = 'k32'"
    )

    results["native router static match"] = _ns(
        "m('GET', '/users')",
        "from aquilia import _core\n"
        "r = _core.Router()\n"
        "[r.add_static('GET', f'/r{i}', i) for i in range(200)]\n"
        "r.add_static('GET', '/users', 999)\n"
        "r.freeze()\n"
        "m = r.match",
    )

    results["native router dynamic match"] = _ns(
        "m('GET', '/users/42')",
        "from aquilia import _core\n"
        "r = _core.Router()\n"
        "r.add_route('GET', '/users/{id}', {'id': _core.ParamKind.INT}, 1)\n"
        "r.freeze()\n"
        "m = r.match",
    )

    results["native router miss"] = _ns(
        "m('GET', '/nope')",
        "from aquilia import _core\n"
        "r = _core.Router()\n"
        "[r.add_static('GET', f'/r{i}', i) for i in range(200)]\n"
        "r.freeze()\n"
        "m = r.match",
    )

    results["native ctx construct"] = _ns(
        "RequestContext()", "from aquilia._core import RequestContext"
    )

    results["native ctx slot write"] = _ns(
        "c.request = v", "from aquilia._core import RequestContext\nc = RequestContext()\nv = object()"
    )

    width = max(len(k) for k in results)
    print(f"{'operation':<{width}}   ns/op")
    print("-" * (width + 10))
    for name, ns in results.items():
        print(f"{name:<{width}}   {ns:7.1f}")

    noop = results["nanobind noop() call"]
    dict_get = results["python dict .get() hit"]
    print()
    print(f"Binding floor: {noop:.1f} ns. Python dict hit: {dict_get:.1f} ns.")
    if noop >= dict_get:
        print(
            f"=> A native replacement for a dict lookup costs at least "
            f"{noop - dict_get:+.1f} ns MORE than the Python it replaces.\n"
            f"   Phases 9E and 9G target exactly such lookups and cannot win."
        )
    else:
        print("=> A native cache could beat the Python dict; 9E/9G worth building.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
