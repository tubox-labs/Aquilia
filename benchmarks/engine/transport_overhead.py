"""Compare in-process ASGI cost across frameworks.

The HTTP benchmarks fold two very different costs into one number: what the
framework spends per request, and what uvicorn spends moving bytes on and off a
socket. A framework can look slow because its pipeline is slow, or because
every framework in the table is paying a large constant it does not control --
and the HTTP number alone cannot tell those apart.

This driver calls each ASGI app directly, with no socket and no uvicorn, so the
difference between two rows here is the difference between two pipelines.
Subtracting this from the HTTP result gives the transport constant.

Usage:
    python benchmarks/engine/transport_overhead.py
    python benchmarks/engine/transport_overhead.py --iterations 20000
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

# Measured QPS from the last full HTTP run (benchmarks/report.md, plaintext).
# Used only to derive the transport constant for the report; the in-process
# numbers below are measured fresh on every invocation.
HTTP_QPS_PLAINTEXT: dict[str, float] = {
    "Aquilia": 34222.54,
    "Starlette": 58748.74,
    "Falcon": 69826.11,
    "Litestar": 43211.64,
    "FastAPI": 32914.32,
}

# Framework -> import path of its ASGI app. Only frameworks with a native ASGI
# entry point are included: Flask and Django are WSGI behind an adapter, so
# their in-process cost is not comparable to the rest.
APPS: dict[str, str] = {
    "Aquilia": "benchmarks.frameworks.aquilia.main:app",
    "Starlette": "benchmarks.frameworks.starlette.main:app",
    "Litestar": "benchmarks.frameworks.litestar.main:app",
    "FastAPI": "benchmarks.frameworks.fastapi.main:app",
}


def build_scope(path: str = "/plaintext") -> dict[str, Any]:
    """Construct a minimal ASGI HTTP scope for a GET request.

    Args:
        path: Request path to place in the scope.

    Returns:
        An ASGI ``http`` scope dict.
    """
    return {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "root_path": "",
        "headers": [
            (b"host", b"127.0.0.1:8100"),
            (b"accept", b"*/*"),
            (b"user-agent", b"aquilia-transport-probe"),
        ],
        "client": ("127.0.0.1", 54321),
        "server": ("127.0.0.1", 8100),
    }


async def drive(app: Any, scope: dict[str, Any]) -> int:
    """Send one request through an ASGI app and return its status code.

    Args:
        app: The ASGI callable.
        scope: The HTTP scope to send.

    Returns:
        The HTTP status the app responded with, or 0 if it never started a
        response.
    """
    status = 0
    delivered = False

    async def receive() -> dict[str, Any]:
        nonlocal delivered
        if delivered:
            return {"type": "http.disconnect"}
        delivered = True
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: dict[str, Any]) -> None:
        nonlocal status
        if message.get("type") == "http.response.start":
            status = int(message["status"])

    await app(scope, receive, send)
    return status


async def start_lifespan(app: Any) -> Any:
    """Run the ASGI lifespan startup handshake if the app supports one.

    Aquilia builds its route table, DI containers and middleware chain during
    startup; measuring without it would measure an app with no routes. Apps
    that do not implement lifespan raise, which is not an error here.

    Args:
        app: The ASGI callable.

    Returns:
        The lifespan task if one started, else None.
    """
    inbox: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
    outbox: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

    async def receive() -> dict[str, Any]:
        return await inbox.get()

    async def send(message: dict[str, Any]) -> None:
        await outbox.put(message)

    task = asyncio.ensure_future(app({"type": "lifespan"}, receive, send))
    await inbox.put({"type": "lifespan.startup"})
    try:
        await asyncio.wait_for(outbox.get(), timeout=30.0)
    except (asyncio.TimeoutError, Exception):
        return None
    return task


async def measure_app(name: str, target: str, iterations: int, warmup: int) -> dict[str, float] | None:
    """Import one framework's app and time it in process.

    Args:
        name: Framework display name.
        target: ``module:attr`` path to the ASGI app.
        iterations: Number of timed requests.
        warmup: Number of untimed requests run first.

    Returns:
        Timing statistics, or None if the app could not be loaded or its
        ``/plaintext`` endpoint did not return a 2xx.
    """
    module_path, _, attr = target.partition(":")
    try:
        module = __import__(module_path, fromlist=[attr])
        app = getattr(module, attr)
    except Exception as exc:
        print(f"  {name}: skipped ({type(exc).__name__}: {exc})", file=sys.stderr)
        return None

    task = await start_lifespan(app)

    scope = build_scope()
    status = await drive(app, dict(scope))
    if not (200 <= status < 400):
        print(f"  {name}: skipped (/plaintext returned HTTP {status})", file=sys.stderr)
        if task is not None:
            task.cancel()
        return None

    for _ in range(warmup):
        await drive(app, dict(scope))

    samples: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        await drive(app, dict(scope))
        samples.append((time.perf_counter() - start) * 1e6)

    if task is not None:
        task.cancel()

    samples.sort()
    mean = statistics.fmean(samples)
    return {
        "framework_us": mean,
        "p50_us": samples[len(samples) // 2],
        "min_us": samples[0],
        "framework_qps": 1e6 / mean if mean else 0.0,
    }


def report(results: dict[str, dict[str, float]]) -> None:
    """Print the in-process comparison and the derived transport constant.

    Args:
        results: Framework name -> timing statistics from :func:`measure_app`.
    """
    print()
    print("=" * 78)
    print("In-process ASGI cost (no socket, no uvicorn) — GET /plaintext")
    print("=" * 78)
    print(f"{'framework':<12} {'framework µs':>13} {'framework QPS':>14} {'HTTP QPS':>10} {'transport µs':>13}")
    print("-" * 78)

    for name, stats in sorted(results.items(), key=lambda kv: kv[1]["framework_us"]):
        http_qps = HTTP_QPS_PLAINTEXT.get(name, 0.0)
        if http_qps > 0:
            http_us = 1e6 / http_qps
            transport_us = http_us - stats["framework_us"]
            transport = f"{transport_us:>13.2f}"
        else:
            transport = f"{'—':>13}"
        print(
            f"{name:<12} {stats['framework_us']:>13.2f} {stats['framework_qps']:>14.0f} "
            f"{http_qps:>10.0f} {transport}"
        )

    print("-" * 78)
    print("transport µs = (1e6 / HTTP QPS) - framework µs, i.e. everything uvicorn")
    print("and the socket cost that the framework itself does not.")
    print()


async def amain(args: argparse.Namespace) -> None:
    """Measure every framework in :data:`APPS` and report."""
    results: dict[str, dict[str, float]] = {}
    for name, target in APPS.items():
        stats = await measure_app(name, target, args.iterations, args.warmup)
        if stats is not None:
            results[name] = stats

    if not results:
        raise SystemExit("no framework app could be measured")

    report(results)

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(results, indent=2))
        print(f"wrote {args.json_out}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=5000)
    parser.add_argument("--warmup", type=int, default=500)
    parser.add_argument("--json-out", default="", help="Optional path to write raw results as JSON")
    args = parser.parse_args()
    asyncio.run(amain(args))


if __name__ == "__main__":
    main()
