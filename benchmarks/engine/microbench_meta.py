"""Phase-1 gate benchmark for the proposed ``aquilia.meta`` metadata engine.

Answers one question before any C++ is written: do Aquilia's own metadata
dataclasses have a load-bearing cost that a native engine could remove?

Measures four things the decision actually turns on:

1. Construction throughput of the real classes (``DISettings``, ``ProviderMeta``,
   ``RouteMetadata``, ``ParameterMetadata``, ``AppManifest``) at realistic scale.
2. The ``slots=True`` delta -- the cheap pure-Python fix -- on the unslotted
   routing/manifest classes, so a C++ rewrite is not credited for a win that
   one keyword argument already delivers.
3. Attribute-access cost: slotted dataclass vs. a real nanobind class
   (``aquilia._core.RequestContext``) vs. a plain dict. This is the decisive
   comparison, because attribute reads -- not construction -- are what the
   per-request DI resolve path actually does to these objects.
4. nanobind call-boundary cost via the extensions' purpose-built ``noop()``,
   which bounds how much a native accessor can possibly win.

Run: ``python benchmarks/engine/microbench_meta.py [--json out.json]``
"""

from __future__ import annotations

import argparse
import gc
import json
import statistics
import sys
import timeit
from dataclasses import dataclass, field
from typing import Any

# ---------------------------------------------------------------------------
# Native extensions (optional -- absent on a pure-Python install)
# ---------------------------------------------------------------------------
try:
    import aquilia._core as _core

    HAS_CORE = True
except ImportError:  # pragma: no cover - depends on build
    _core = None  # type: ignore[assignment]
    HAS_CORE = False

try:
    import aquilia._dataengine as _dataengine

    HAS_DATAENGINE = True
except ImportError:  # pragma: no cover - depends on build
    _dataengine = None  # type: ignore[assignment]
    HAS_DATAENGINE = False


# ---------------------------------------------------------------------------
# Timing helper
# ---------------------------------------------------------------------------
def bench(fn, iterations: int, repeat: int = 7) -> float:
    """Return best-of-`repeat` nanoseconds per operation.

    Minimum rather than mean: we want the cost without scheduler noise, and the
    floor is the reproducible number across machines.
    """
    gc.collect()
    samples = timeit.repeat(fn, number=iterations, repeat=repeat)
    return min(samples) / iterations * 1e9


def fmt(ns: float) -> str:
    return f"{ns:>9.1f} ns"


# ---------------------------------------------------------------------------
# 1 + 2. Construction: real classes, and the slots=True cheap-fix delta
# ---------------------------------------------------------------------------
# Faithful clones of the two routing classes, differing only in `slots`. Clones
# rather than the originals because the point is to isolate the one keyword --
# `ParameterMetadata`/`RouteMetadata` carry methods and defaults that would
# otherwise confound the comparison.


@dataclass
class ParamNoSlots:
    name: str
    type: type
    default: Any = None
    source: str = "query"
    required: bool = True
    pattern: str | None = None


@dataclass(slots=True)
class ParamSlots:
    name: str
    type: type
    default: Any = None
    source: str = "query"
    required: bool = True
    pattern: str | None = None


@dataclass
class RouteNoSlots:
    http_method: str
    path_template: str
    full_path: str
    handler_name: str
    parameters: list = field(default_factory=list)
    pipeline: list = field(default_factory=list)
    summary: str = ""
    description: str = ""
    tags: list = field(default_factory=list)
    deprecated: bool = False
    status_code: int = 200
    specificity: int = 0


@dataclass(slots=True)
class RouteSlots:
    http_method: str
    path_template: str
    full_path: str
    handler_name: str
    parameters: list = field(default_factory=list)
    pipeline: list = field(default_factory=list)
    summary: str = ""
    description: str = ""
    tags: list = field(default_factory=list)
    deprecated: bool = False
    status_code: int = 200
    specificity: int = 0


@dataclass(frozen=True, slots=True)
class FrozenSlots:
    """Shape-matched to ``ProviderMeta`` -- the framework's own hot-path idiom."""

    name: str
    token: str
    scope: str
    tags: tuple = ()
    module: str = ""
    qualname: str = ""
    line: int | None = None


def bench_construction() -> dict[str, Any]:
    from aquilia.controller.metadata import ParameterMetadata, RouteMetadata
    from aquilia.di.core import ProviderMeta
    from aquilia.di.settings import DISettings

    results: dict[str, Any] = {}

    print("\n" + "=" * 74)
    print("1. CONSTRUCTION THROUGHPUT -- real Aquilia classes")
    print("=" * 74)

    cases = [
        (
            "DISettings (frozen+slots, __post_init__)",
            lambda: DISettings(),
            "startup x1",
        ),
        (
            "ProviderMeta (frozen+slots)",
            lambda: ProviderMeta(name="UserService", token="UserService", scope="app"),
            "startup x n_providers",
        ),
        (
            "ParameterMetadata (plain)",
            lambda: ParameterMetadata(name="user_id", type=int, source="path"),
            "compile x n_params",
        ),
        (
            "RouteMetadata (plain)",
            lambda: RouteMetadata(
                http_method="GET",
                path_template="/users/<id:int>",
                full_path="/api/users/<id:int>",
                handler_name="get_user",
            ),
            "compile x n_routes",
        ),
    ]

    for label, fn, when in cases:
        ns = bench(fn, 100_000)
        results[label] = ns
        print(f"  {label:<44} {fmt(ns)}   [{when}]")

    print("\n" + "=" * 74)
    print("2. THE slots=True CHEAP FIX -- before reaching for C++")
    print("=" * 74)

    pairs = [
        ("ParameterMetadata-shaped", lambda: ParamNoSlots("user_id", int), lambda: ParamSlots("user_id", int)),
        (
            "RouteMetadata-shaped",
            lambda: RouteNoSlots("GET", "/u/<id>", "/api/u/<id>", "get_user"),
            lambda: RouteSlots("GET", "/u/<id>", "/api/u/<id>", "get_user"),
        ),
    ]

    for label, no_slots, slots in pairs:
        a = bench(no_slots, 100_000)
        b = bench(slots, 100_000)
        gain = (a - b) / a * 100
        results[f"{label} noslots"] = a
        results[f"{label} slots"] = b
        print(f"  {label:<30} noslots {fmt(a)}  slots {fmt(b)}   {gain:+5.1f}%")

    # Memory per instance -- the other half of the slots story.
    print("\n  Memory per instance:")
    for label, ns_obj, s_obj in [
        ("ParameterMetadata-shaped", ParamNoSlots("user_id", int), ParamSlots("user_id", int)),
        (
            "RouteMetadata-shaped",
            RouteNoSlots("GET", "/u/<id>", "/api/u/<id>", "get_user"),
            RouteSlots("GET", "/u/<id>", "/api/u/<id>", "get_user"),
        ),
    ]:
        a = sys.getsizeof(ns_obj) + sys.getsizeof(ns_obj.__dict__)
        b = sys.getsizeof(s_obj)
        results[f"{label} bytes noslots"] = a
        results[f"{label} bytes slots"] = b
        print(f"    {label:<28} noslots {a:>4} B   slots {b:>4} B   {(a - b) / a * 100:+5.1f}%")

    return results


# ---------------------------------------------------------------------------
# 3 + 4. Attribute access, and the nanobind boundary ceiling
# ---------------------------------------------------------------------------
def bench_attribute_access() -> dict[str, Any]:
    """The decisive measurement.

    The DI resolve path reads ``provider.meta.scope`` and three ``DISettings``
    flags per resolution (``di/core.py:555,568-573,630``). Those reads, not
    construction, are the only part of these objects on a per-request path.
    """
    results: dict[str, Any] = {}

    print("\n" + "=" * 74)
    print("3. ATTRIBUTE ACCESS -- slotted dataclass vs. nanobind vs. dict")
    print("=" * 74)

    frozen = FrozenSlots(name="UserService", token="UserService", scope="app")
    plain = RouteNoSlots("GET", "/u/<id>", "/api/u/<id>", "get_user")
    slotted = RouteSlots("GET", "/u/<id>", "/api/u/<id>", "get_user")
    as_dict = {"scope": "app", "name": "UserService", "token": "UserService"}

    ns = bench(lambda: frozen.scope, 1_000_000)
    results["dataclass frozen+slots .scope"] = ns
    print(f"  {'dataclass(frozen,slots) attr':<44} {fmt(ns)}   <- ProviderMeta idiom")

    ns_slot = bench(lambda: slotted.http_method, 1_000_000)
    results["dataclass slots attr"] = ns_slot
    print(f"  {'dataclass(slots) attr':<44} {fmt(ns_slot)}")

    ns_plain = bench(lambda: plain.http_method, 1_000_000)
    results["dataclass plain attr"] = ns_plain
    print(f"  {'dataclass(plain) attr':<44} {fmt(ns_plain)}")

    ns_dict = bench(lambda: as_dict["scope"], 1_000_000)
    results["dict lookup"] = ns_dict
    print(f"  {'dict[key]':<44} {fmt(ns_dict)}")

    if HAS_CORE:
        ctx = _core.RequestContext()
        try:
            ns_native = bench(lambda: ctx.request_id, 1_000_000)
            results["nanobind attr"] = ns_native
            delta = (ns_native - ns) / ns * 100
            print(f"  {'nanobind class attr (RequestContext)':<44} {fmt(ns_native)}   {delta:+5.1f}% vs slots")
        except Exception as exc:  # pragma: no cover
            print(f"  nanobind attr unavailable: {exc}")
    else:
        print("  nanobind attr: extension not built -- skipped")

    print("\n" + "=" * 74)
    print("4. nanobind CALL-BOUNDARY COST -- the native accessor's floor")
    print("=" * 74)

    def py_noop() -> None:
        return None

    ns_py = bench(py_noop, 1_000_000)
    results["python noop call"] = ns_py
    print(f"  {'python def noop()':<44} {fmt(ns_py)}")

    for label, mod, present in (
        ("aquilia._core.noop()", _core, HAS_CORE),
        ("aquilia._dataengine.noop()", _dataengine, HAS_DATAENGINE),
    ):
        if not present:
            print(f"  {label:<44} not built -- skipped")
            continue
        ns_n = bench(mod.noop, 1_000_000)
        results[label] = ns_n
        print(f"  {label:<44} {fmt(ns_n)}")

    return results


# ---------------------------------------------------------------------------
# 5. AppManifest -- the worst case: nested, unslotted, __post_init__ validation
# ---------------------------------------------------------------------------
def bench_manifest(n_services: int = 20, n_controllers: int = 12, n_modules: int = 8) -> dict[str, Any]:
    """Realistic scale per the prompt: dozens of routes/services, not thousands."""
    from aquilia.manifest import AppManifest, ComponentKind, ComponentRef, ServiceConfig

    results: dict[str, Any] = {}

    print("\n" + "=" * 74)
    print(f"5. AppManifest TREE -- {n_modules} modules x ({n_services} services + {n_controllers} controllers)")
    print("=" * 74)

    def build_one(i: int) -> AppManifest:
        return AppManifest(
            name=f"module_{i}",
            version="1.0.0",
            services=[
                ServiceConfig(class_path=f"modules.m{i}.services:Service{j}", scope="app") for j in range(n_services)
            ],
            controllers=[
                ComponentRef(class_path=f"modules.m{i}.controllers:C{j}", kind=ComponentKind.CONTROLLER)
                for j in range(n_controllers)
            ],
            exports=[f"Service{j}" for j in range(4)],
            imports=[f"module_{k}" for k in range(max(0, i - 2), i)],
        )

    ns_one = bench(lambda: build_one(3), 2_000)
    results["build 1 manifest"] = ns_one
    print(f"  {'build 1 manifest (with __post_init__)':<44} {fmt(ns_one)}")

    ns_tree = bench(lambda: [build_one(i) for i in range(n_modules)], 200)
    results["build full tree"] = ns_tree
    print(f"  {'build full tree':<44} {fmt(ns_tree)}   = {ns_tree / 1e6:.3f} ms")

    tree = [build_one(i) for i in range(n_modules)]

    def walk() -> int:
        n = 0
        for m in tree:
            n += len(m.name) + len(m.version)
            for s in m.services:
                n += len(s.class_path) + len(s.scope)
            for c in m.controllers:
                n += len(c.class_path)
            for imp in m.imports:
                n += len(imp)
        return n

    ns_walk = bench(walk, 5_000)
    results["walk full tree"] = ns_walk
    print(f"  {'walk full tree (attr reads)':<44} {fmt(ns_walk)}   = {ns_walk / 1e6:.3f} ms")

    total_objs = n_modules * (1 + n_services + n_controllers)
    print(f"\n  Total objects in tree: {total_objs}")
    print(f"  Whole-tree build is {ns_tree / 1e6:.3f} ms of a once-per-process boot.")

    return results


# ---------------------------------------------------------------------------
# 6. Startup attribution -- is manifest construction even visible in boot?
# ---------------------------------------------------------------------------
def bench_import_cost() -> dict[str, Any]:
    """Import time dwarfs construction; measure it so the report can say so."""
    import subprocess

    results: dict[str, Any] = {}

    print("\n" + "=" * 74)
    print("6. IMPORT COST -- the actual startup budget")
    print("=" * 74)

    for label, mod in [
        ("import aquilia", "aquilia"),
        ("import aquilia.manifest", "aquilia.manifest"),
        ("import aquilia.di.core", "aquilia.di.core"),
        ("import aquilia.server", "aquilia.server"),
    ]:
        times = []
        for _ in range(5):
            out = subprocess.run(
                [sys.executable, "-X", "importtime", "-c", f"import {mod}"],
                capture_output=True,
                text=True,
            )
            total = 0
            for line in out.stderr.splitlines():
                parts = line.split("|")
                if len(parts) == 3 and "cumulative" not in line:
                    try:
                        total = max(total, int(parts[1].strip()))
                    except ValueError:
                        pass
            times.append(total / 1000.0)
        ms = statistics.median(times)
        results[label] = ms
        print(f"  {label:<44} {ms:>8.1f} ms")

    return results


def bench_portable() -> dict[str, Any]:
    """Sections 2+3 with zero ``aquilia`` imports, for cross-interpreter runs.

    Lets the slots-delta and attribute-access numbers be reproduced on every
    CPython in the CI matrix without installing the framework first::

        uv run --python 3.13 --no-project python benchmarks/engine/microbench_meta.py --portable
    """
    p, s = ParamNoSlots("user_id", int), ParamSlots("user_id", int)
    frozen = FrozenSlots("UserService", "UserService", "app")
    as_dict = {"scope": "app"}

    c_plain = bench(lambda: ParamNoSlots("user_id", int), 100_000)
    c_slots = bench(lambda: ParamSlots("user_id", int), 100_000)
    a_plain = bench(lambda: p.name, 1_000_000)
    a_slots = bench(lambda: s.name, 1_000_000)
    a_frozen = bench(lambda: frozen.scope, 1_000_000)
    a_dict = bench(lambda: as_dict["scope"], 1_000_000)
    m_plain = sys.getsizeof(p) + sys.getsizeof(p.__dict__)
    m_slots = sys.getsizeof(s)

    print(
        f"py{sys.version.split()[0]:<9} construct: plain {c_plain:6.1f}ns  slots {c_slots:6.1f}ns  ({(c_plain - c_slots) / c_plain * 100:+.0f}%)"
    )
    print(
        f"{'':<11} attr:      plain {a_plain:6.1f}ns  slots {a_slots:6.1f}ns  frozen+slots {a_frozen:6.1f}ns  dict {a_dict:6.1f}ns"
    )
    print(f"{'':<11} mem:       plain {m_plain:4}B  slots {m_slots:4}B  ({(m_plain - m_slots) / m_plain * 100:+.0f}%)")

    return {
        "construct_plain": c_plain,
        "construct_slots": c_slots,
        "attr_plain": a_plain,
        "attr_slots": a_slots,
        "attr_frozen_slots": a_frozen,
        "attr_dict": a_dict,
        "bytes_plain": m_plain,
        "bytes_slots": m_slots,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=str, help="write results to JSON file")
    parser.add_argument(
        "--portable",
        action="store_true",
        help="run only the aquilia-free slots/attribute checks (for cross-interpreter runs)",
    )
    args = parser.parse_args()

    if args.portable:
        results = {"python": sys.version.split()[0], "portable": bench_portable()}
        if args.json:
            with open(args.json, "w") as fh:
                json.dump(results, fh, indent=2)
        return

    print("=" * 74)
    print("aquilia.meta -- PHASE 1 GATE BENCHMARK (pure Python, pre-C++)")
    print("=" * 74)
    print(f"Python  : {sys.version.split()[0]}")
    print(f"Platform: {sys.platform}")
    print(f"Native  : _core={HAS_CORE}  _dataengine={HAS_DATAENGINE}")

    results = {
        "python": sys.version.split()[0],
        "platform": sys.platform,
        "construction": bench_construction(),
        "attribute_access": bench_attribute_access(),
        "manifest": bench_manifest(),
        "import_cost": bench_import_cost(),
    }

    if args.json:
        with open(args.json, "w") as fh:
            json.dump(results, fh, indent=2)
        print(f"\nWrote {args.json}")


if __name__ == "__main__":
    main()
