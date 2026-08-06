"""Profile the Aquilia ASGI request pipeline in-process.

The HTTP benchmarks measure the whole stack through a socket, which means a
regression anywhere -- uvicorn, the event loop, the middleware chain, the
response encoder -- shows up as one number and points at nothing. This driver
calls the ASGI app directly with a synthetic scope so the profile attributes
cost to the frame that actually spends it.

Usage:
    python benchmarks/engine/pipeline_profile.py --scenario plaintext
    python benchmarks/engine/pipeline_profile.py --scenario plaintext --profile
"""

from __future__ import annotations

import argparse
import asyncio
import cProfile
import io
import pstats
import statistics
import sys
import time
from pathlib import Path
from typing import Any

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))


# Scenario -> (method, path, body). Kept in lockstep with benchmarks/run.py so
# an in-process profile and an HTTP run describe the same request.
SCENARIOS: dict[str, tuple[str, str, bytes]] = {
    "plaintext": ("GET", "/plaintext", b""),
    "json": ("GET", "/json", b""),
    "route_static": ("GET", "/route/static", b""),
    "route_params": ("GET", "/route/params/123/orders/456", b""),
    "di": ("GET", "/di", b""),
}


def build_scope(method: str, path: str, body: bytes) -> dict[str, Any]:
    """Construct a minimal but realistic ASGI HTTP scope.

    Args:
        method: HTTP method.
        path: Request path (no query string).
        body: Request body, used to set content-length.

    Returns:
        An ASGI ``http`` scope dict.
    """
    headers = [
        (b"host", b"127.0.0.1:8100"),
        (b"accept", b"*/*"),
        (b"user-agent", b"aquilia-profile"),
    ]
    if body:
        headers.append((b"content-type", b"application/json"))
        headers.append((b"content-length", str(len(body)).encode()))
    return {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "root_path": "",
        "headers": headers,
        "client": ("127.0.0.1", 54321),
        "server": ("127.0.0.1", 8100),
    }


async def drive(app: Any, scope: dict[str, Any], body: bytes) -> int:
    """Send one request through the ASGI app and return its status.

    Args:
        app: The ASGI callable.
        scope: The HTTP scope to send.
        body: Request body bytes.

    Returns:
        The HTTP status code the app responded with.
    """
    sent: list[dict[str, Any]] = []
    delivered = False

    async def receive() -> dict[str, Any]:
        nonlocal delivered
        if delivered:
            return {"type": "http.disconnect"}
        delivered = True
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message: dict[str, Any]) -> None:
        sent.append(message)

    await app(scope, receive, send)
    for message in sent:
        if message.get("type") == "http.response.start":
            return int(message["status"])
    return 0


async def lifespan_startup(app: Any) -> Any:
    """Run the ASGI lifespan startup handshake.

    Route tables, DI containers and the middleware chain are all built during
    startup. Profiling without it measures an app that has no routes.

    Args:
        app: The ASGI callable.

    Returns:
        The lifespan task, kept alive so shutdown can be requested later.
    """
    inbox: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
    outbox: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

    async def receive() -> dict[str, Any]:
        return await inbox.get()

    async def send(message: dict[str, Any]) -> None:
        await outbox.put(message)

    task = asyncio.ensure_future(app({"type": "lifespan"}, receive, send))
    await inbox.put({"type": "lifespan.startup"})
    await outbox.get()
    return task


async def measure(app: Any, scenario: str, iterations: int, warmup: int) -> dict[str, float]:
    """Time repeated requests through the app.

    Args:
        app: The ASGI callable.
        scenario: Key into :data:`SCENARIOS`.
        iterations: Number of timed requests.
        warmup: Number of untimed requests run first.

    Returns:
        Timing statistics in microseconds plus derived single-thread QPS.
    """
    method, path, body = SCENARIOS[scenario]
    scope = build_scope(method, path, body)

    status = await drive(app, dict(scope), body)
    if not (200 <= status < 400):
        raise SystemExit(f"scenario {scenario!r} returned HTTP {status}; profile would measure an error path")

    for _ in range(warmup):
        await drive(app, dict(scope), body)

    samples: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        await drive(app, dict(scope), body)
        samples.append((time.perf_counter() - start) * 1e6)

    samples.sort()
    mean = statistics.fmean(samples)
    return {
        "mean_us": mean,
        "p50_us": samples[len(samples) // 2],
        "p95_us": samples[int(len(samples) * 0.95)],
        "min_us": samples[0],
        "qps_single_thread": 1e6 / mean if mean else 0.0,
    }


async def profile(app: Any, scenario: str, iterations: int) -> str:
    """Run cProfile over repeated requests and return the top frames.

    Args:
        app: The ASGI callable.
        scenario: Key into :data:`SCENARIOS`.
        iterations: Number of profiled requests.

    Returns:
        A formatted pstats table sorted by cumulative time.
    """
    method, path, body = SCENARIOS[scenario]
    scope = build_scope(method, path, body)

    for _ in range(200):
        await drive(app, dict(scope), body)

    loop = asyncio.get_running_loop()
    profiler = cProfile.Profile()

    # cProfile does not follow await boundaries across the loop, so each
    # request is driven to completion inside the profiled region via
    # run_until_complete-equivalent stepping on the running loop.
    profiler.enable()
    for _ in range(iterations):
        await drive(app, dict(scope), body)
    profiler.disable()
    del loop

    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats("tottime").print_stats(35)
    return stream.getvalue()


async def amain(args: argparse.Namespace) -> None:
    """Load the benchmark app, then measure or profile it."""
    from benchmarks.frameworks.aquilia.main import app

    task = await lifespan_startup(app)

    if args.profile:
        print(await profile(app, args.scenario, args.iterations))
    else:
        stats = await measure(app, args.scenario, args.iterations, args.warmup)
        print(f"scenario: {args.scenario}")
        for key, value in stats.items():
            print(f"  {key:<20} {value:>12.2f}")

    task.cancel()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", default="plaintext", choices=sorted(SCENARIOS))
    parser.add_argument("--iterations", type=int, default=5000)
    parser.add_argument("--warmup", type=int, default=500)
    parser.add_argument("--profile", action="store_true", help="Emit a cProfile table instead of timings")
    args = parser.parse_args()
    asyncio.run(amain(args))


if __name__ == "__main__":
    main()
