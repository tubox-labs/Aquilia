"""Static import-graph analysis for Phase 1 (package boundaries + cycles).

Parses every aquilia/*.py with `ast` (no imports executed, so no side effects)
and reports:
  * subpackage-level dependency edges
  * import cycles between subpackages (SCC via Tarjan)
  * count of function-local imports (deferred imports used to break cycles)
  * the modules with the heaviest fan-in / fan-out

Run: python benchmarks/engine/import_graph.py
"""

from __future__ import annotations

import ast
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "aquilia"


def module_name(p: Path) -> str:
    rel = p.relative_to(ROOT).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def subpackage(mod: str) -> str:
    """aquilia.di.core -> aquilia.di ; aquilia.asgi -> aquilia.<root>"""
    parts = mod.split(".")
    if len(parts) <= 2:
        return "aquilia.<root>"
    return ".".join(parts[:2])


def analyse():
    files = sorted(PKG.rglob("*.py"))
    files = [f for f in files if "__pycache__" not in f.parts]

    mod_imports: dict[str, set[str]] = defaultdict(set)
    local_imports: dict[str, int] = defaultdict(int)
    top_imports: dict[str, int] = defaultdict(int)
    parse_fail = []

    for f in files:
        mod = module_name(f)
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
        except SyntaxError as e:
            parse_fail.append((mod, str(e)))
            continue

        # Determine, for each import node, whether it is at module top level
        toplevel_nodes = set()
        for node in tree.body:
            for sub in ast.walk(node):
                if isinstance(sub, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        toplevel_nodes.add(id(sub))

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.level and node.level > 0:
                    continue  # relative import, resolve later if needed
                name = node.module or ""
            elif isinstance(node, ast.Import):
                name = node.names[0].name if node.names else ""
            else:
                continue

            if not name.startswith("aquilia"):
                continue

            mod_imports[mod].add(name)
            if id(node) in toplevel_nodes:
                top_imports[mod] += 1
            else:
                local_imports[mod] += 1

    return mod_imports, local_imports, top_imports, parse_fail, files


def build_sub_graph(mod_imports):
    g: dict[str, set[str]] = defaultdict(set)
    for mod, deps in mod_imports.items():
        a = subpackage(mod)
        for d in deps:
            b = subpackage(d)
            if a != b:
                g[a].add(b)
        g.setdefault(a, set())
    return g


def tarjan(graph: dict[str, set[str]]) -> list[list[str]]:
    index = {}
    low = {}
    on_stack = set()
    stack: list[str] = []
    out: list[list[str]] = []
    counter = [0]
    sys.setrecursionlimit(10000)

    def strong(v):
        index[v] = low[v] = counter[0]
        counter[0] += 1
        stack.append(v)
        on_stack.add(v)
        for w in graph.get(v, ()):
            if w not in index:
                strong(w)
                low[v] = min(low[v], low[w])
            elif w in on_stack:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = []
            while True:
                w = stack.pop()
                on_stack.discard(w)
                comp.append(w)
                if w == v:
                    break
            out.append(comp)

    for v in list(graph):
        if v not in index:
            strong(v)
    return [c for c in out if len(c) > 1 or (len(c) == 1 and c[0] in graph.get(c[0], ()))]


def main():
    mod_imports, local_imports, top_imports, parse_fail, files = analyse()

    print("=" * 78)
    print("AQUILIA IMPORT GRAPH (static AST analysis, no execution)")
    print("=" * 78)
    print(f"  modules parsed        : {len(files)}")
    print(f"  parse failures        : {len(parse_fail)}")
    print(f"  internal import edges : {sum(len(v) for v in mod_imports.values())}")
    tl = sum(top_imports.values())
    dl = sum(local_imports.values())
    print(f"  top-level imports     : {tl}")
    print(f"  function-local imports: {dl}   <-- deferred to break cycles / cost per call")
    print(f"  deferred ratio        : {dl / max(tl + dl, 1) * 100:.1f}%")

    print("\n-- modules with the most function-local (deferred) imports --")
    for mod, n in sorted(local_imports.items(), key=lambda kv: -kv[1])[:18]:
        print(f"  {n:>4}  {mod}")

    g = build_sub_graph(mod_imports)
    print(f"\n-- subpackage graph: {len(g)} nodes, {sum(len(v) for v in g.values())} edges --")

    fan_out = sorted(((len(v), k) for k, v in g.items()), reverse=True)[:12]
    fan_in_c: dict[str, int] = defaultdict(int)
    for _a, deps in g.items():
        for b in deps:
            fan_in_c[b] += 1
    fan_in = sorted(((v, k) for k, v in fan_in_c.items()), reverse=True)[:12]

    print("\n  highest fan-out (depends on most subpackages):")
    for n, k in fan_out:
        print(f"    {n:>3}  {k}")
    print("\n  highest fan-in (most depended upon):")
    for n, k in fan_in:
        print(f"    {n:>3}  {k}")

    cycles = tarjan(g)
    print(f"\n-- subpackage import cycles: {len(cycles)} --")
    for c in sorted(cycles, key=len, reverse=True):
        print(f"  SCC of {len(c)}: {', '.join(sorted(c))}")

    # module-level cycles (finer grained) — report count only, too many to list
    mg = {m: {d for d in deps if d in mod_imports} for m, deps in mod_imports.items()}
    mcycles = tarjan(mg)
    print(f"\n-- module-level import cycles: {len(mcycles)} (largest {max((len(c) for c in mcycles), default=0)}) --")
    for c in sorted(mcycles, key=len, reverse=True)[:5]:
        print(f"  SCC of {len(c)}: {', '.join(sorted(c)[:6])}{' ...' if len(c) > 6 else ''}")

    # cold-start: measure real import time
    print("\n-- cold import cost (subprocess, best of 5) --")
    import subprocess

    best = {}
    for target in ("aquilia", "aquilia.di", "aquilia.controller.router", "aquilia.server"):
        times = []
        for _ in range(5):
            r = subprocess.run(
                [sys.executable, "-X", "importtime", "-c", f"import {target}"],
                capture_output=True,
                text=True,
            )
            last = [ln for ln in r.stderr.splitlines() if ln.strip()]
            if last:
                # cumulative us is the 2nd field of the final line
                try:
                    cum = int(last[-1].split("|")[1].strip())
                    times.append(cum)
                except (ValueError, IndexError):
                    pass
        if times:
            best[target] = min(times)
            print(f"  {target:<28} {min(times) / 1000:>8.1f} ms")


if __name__ == "__main__":
    main()
