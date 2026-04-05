from __future__ import annotations

import argparse
import asyncio
import json
import os
import platform
import signal
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import psutil
import websockets

REPO_ROOT = Path(__file__).resolve().parents[1]
BENCH_ROOT = Path(__file__).resolve().parent
RESULTS_ROOT = BENCH_ROOT / "results"

DEFAULT_FRAMEWORKS = ("aquilia", "fastapi", "flask")

JSON_BODY = {
    "name": "benchmark-request",
    "count": 123,
    "enabled": True,
    "tags": ["bench", "json", "load"],
    "metadata": {"source": "runner", "tier": "baseline"},
}
FORM_BODY = {
    "name": "benchmark-form",
    "category": "load-test",
    "quantity": "7",
}
MULTIPART_BYTES = b"a" * 8192


@dataclass(frozen=True)
class FrameworkConfig:
    name: str
    host: str
    port: int
    command: list[str]
    env: dict[str, str]
    websocket_supported: bool
    websocket_protocol: str

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


@dataclass(frozen=True)
class Scenario:
    name: str
    description: str
    method: str
    path: str
    expected_status: int
    request_weight: float = 1.0
    concurrency_factor: float = 1.0
    body_kind: str = "none"  # none|json|form|multipart


HTTP_SCENARIOS: list[Scenario] = [
    Scenario("health", "Liveness endpoint", "GET", "/health", 200, 1.0, 1.0),
    Scenario("json_simple", "Small JSON response", "GET", "/json/simple", 200, 1.0, 1.0),
    Scenario("json_large", "Large JSON serialization", "GET", "/json/large", 200, 0.6, 0.9),
    Scenario("di_chain", "Dependency resolution path", "GET", "/di", 200, 1.0, 1.0),
    Scenario("middleware_stack", "Path-scoped middleware overhead", "GET", "/middleware/noop", 200, 0.9, 1.0),
    Scenario("route_static", "Static route match", "GET", "/route/static", 200, 0.9, 1.0),
    Scenario("route_params", "Path parameter extraction", "GET", "/route/params/41/orders/99", 200, 0.9, 1.0),
    Scenario("route_dense", "Dense route-table matching", "GET", "/route/filler/r199", 200, 0.8, 1.0),
    Scenario("body_json", "JSON request parsing", "POST", "/body/json", 200, 0.8, 0.8, "json"),
    Scenario("body_form", "Form request parsing", "POST", "/body/form", 200, 0.6, 0.7, "form"),
    Scenario("body_multipart", "Multipart upload parsing", "POST", "/body/multipart", 200, 0.3, 0.35, "multipart"),
    Scenario("response_text", "Plain text response", "GET", "/response/text", 200, 0.9, 1.0),
    Scenario("response_stream", "Chunked streaming response", "GET", "/response/stream", 200, 0.3, 0.5),
    Scenario("response_file", "File response generation", "GET", "/response/file", 200, 0.5, 0.6),
    Scenario("static_file", "Static middleware serving", "GET", "/static/sample.txt", 200, 0.6, 0.7),
    Scenario("compute_async", "Async/sleep concurrency behavior", "GET", "/compute/async?delay_ms=5", 200, 0.5, 1.0),
    Scenario("error_handled", "Handled error path", "GET", "/error/handled", 400, 0.5, 0.8),
    Scenario("error_unhandled", "Unhandled error propagation", "GET", "/error/unhandled", 500, 0.4, 0.7),
]


@dataclass(frozen=True)
class WebSocketScenario:
    name: str = "websocket_echo"
    path: str = "/ws/echo"
    connections: int = 16
    messages_per_connection: int = 80


@dataclass
class ServerHandle:
    process: subprocess.Popen[Any]
    log_path: Path
    log_file: Any


@dataclass
class ProcessStats:
    avg_cpu_percent: float
    peak_cpu_percent: float
    avg_rss_mb: float
    peak_rss_mb: float


@dataclass
class LoadResult:
    requests: int
    successes: int
    failures: int
    duration_seconds: float
    throughput_rps: float
    p50_ms: float | None
    p90_ms: float | None
    p95_ms: float | None
    p99_ms: float | None
    status_counts: dict[str, int]
    process: ProcessStats
    error_samples: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Aquilia/FastAPI/Flask benchmark suite.")
    parser.add_argument("--frameworks", nargs="+", choices=DEFAULT_FRAMEWORKS, default=list(DEFAULT_FRAMEWORKS))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--base-port", type=int, default=8100)
    parser.add_argument("--requests", type=int, default=1800)
    parser.add_argument("--concurrency", type=int, default=64)
    parser.add_argument("--warmup", type=int, default=120)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--startup-timeout", type=float, default=45.0)
    parser.add_argument("--skip-websocket", action="store_true")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--output-dir", default=None)
    return parser.parse_args()


def quantile(sorted_values: list[float], q: float) -> float | None:
    if not sorted_values:
        return None

    if len(sorted_values) == 1:
        return sorted_values[0]

    pos = (len(sorted_values) - 1) * q
    lower = int(pos)
    upper = min(lower + 1, len(sorted_values) - 1)
    fraction = pos - lower
    return sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * fraction


def scale_requests(base: int, weight: float) -> int:
    return max(30, int(base * weight))


def scale_concurrency(base: int, factor: float) -> int:
    return max(1, int(base * factor))


def build_framework_config(name: str, host: str, port: int) -> FrameworkConfig:
    python = sys.executable

    if name == "aquilia":
        command = [
            python,
            "-m",
            "uvicorn",
            "benchmark.apps.aquilia_app.main:app",
            "--host",
            host,
            "--port",
            str(port),
            "--workers",
            "1",
            "--log-level",
            "warning",
        ]
        env = {
            "AQUILIA_ENV": "prod",
            "AQUILIA_WORKSPACE": str((BENCH_ROOT / "apps" / "aquilia_app").resolve()),
        }
        return FrameworkConfig(name, host, port, command, env, websocket_supported=True, websocket_protocol="aquilia")

    if name == "fastapi":
        command = [
            python,
            "-m",
            "uvicorn",
            "benchmark.apps.fastapi_app:app",
            "--host",
            host,
            "--port",
            str(port),
            "--workers",
            "1",
            "--log-level",
            "warning",
        ]
        return FrameworkConfig(name, host, port, command, {}, websocket_supported=True, websocket_protocol="fastapi")

    if name == "flask":
        command = [
            python,
            "-m",
            "uvicorn",
            "benchmark.apps.flask_app:asgi_app",
            "--host",
            host,
            "--port",
            str(port),
            "--workers",
            "1",
            "--log-level",
            "warning",
        ]
        return FrameworkConfig(name, host, port, command, {}, websocket_supported=False, websocket_protocol="none")

    raise ValueError(f"Unknown framework: {name}")


def start_server(config: FrameworkConfig, log_dir: Path) -> ServerHandle:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{config.name}.log"
    log_file = log_path.open("w", encoding="utf-8")

    env = os.environ.copy()
    env.update(config.env)

    process = subprocess.Popen(
        config.command,
        cwd=str(REPO_ROOT),
        stdout=log_file,
        stderr=subprocess.STDOUT,
        env=env,
    )

    return ServerHandle(process=process, log_path=log_path, log_file=log_file)


async def wait_for_health(config: FrameworkConfig, handle: ServerHandle, timeout_s: float) -> float:
    health_url = f"{config.base_url}/health"
    start = time.perf_counter()

    async with httpx.AsyncClient(timeout=1.0) as client:
        while True:
            if handle.process.poll() is not None:
                raise RuntimeError(f"{config.name} exited before becoming healthy")

            elapsed = time.perf_counter() - start
            if elapsed > timeout_s:
                raise TimeoutError(f"Timed out waiting for {config.name} health endpoint")

            try:
                response = await client.get(health_url)
                if response.status_code == 200:
                    return elapsed
            except Exception:
                pass

            await asyncio.sleep(0.05)


def stop_server(handle: ServerHandle) -> None:
    process = handle.process

    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

    handle.log_file.close()


def request_kwargs_for_scenario(scenario: Scenario) -> dict[str, Any]:
    kwargs: dict[str, Any] = {}

    if scenario.body_kind == "json":
        kwargs["json"] = JSON_BODY
    elif scenario.body_kind == "form":
        kwargs["data"] = FORM_BODY
    elif scenario.body_kind == "multipart":
        kwargs["files"] = {
            "file": ("upload.bin", MULTIPART_BYTES, "application/octet-stream"),
        }

    return kwargs


async def sample_process(pid: int, stop_event: asyncio.Event, interval: float = 0.2) -> ProcessStats:
    proc = psutil.Process(pid)
    cpu_samples: list[float] = []
    rss_samples: list[float] = []

    try:
        proc.cpu_percent(interval=None)
    except Exception:
        return ProcessStats(0.0, 0.0, 0.0, 0.0)

    while not stop_event.is_set():
        try:
            cpu_samples.append(float(proc.cpu_percent(interval=None)))
            rss_samples.append(float(proc.memory_info().rss))
        except (psutil.NoSuchProcess, psutil.AccessDenied, ProcessLookupError):
            break

        await asyncio.sleep(interval)

    if not cpu_samples:
        return ProcessStats(0.0, 0.0, 0.0, 0.0)

    avg_cpu = sum(cpu_samples) / len(cpu_samples)
    peak_cpu = max(cpu_samples)
    avg_rss_mb = (sum(rss_samples) / len(rss_samples)) / (1024 * 1024)
    peak_rss_mb = max(rss_samples) / (1024 * 1024)
    return ProcessStats(avg_cpu, peak_cpu, avg_rss_mb, peak_rss_mb)


async def run_http_load(
    config: FrameworkConfig,
    scenario: Scenario,
    total_requests: int,
    concurrency: int,
    timeout_s: float,
) -> LoadResult:
    latencies_ms: list[float] = []
    failures = 0
    status_counts: dict[str, int] = {}
    error_samples: list[str] = []
    lock = asyncio.Lock()
    next_index = 0

    stop_event = asyncio.Event()
    sampler_task = asyncio.create_task(sample_process(pid=config_process_pid(config), stop_event=stop_event))

    start = time.perf_counter()

    limits = httpx.Limits(
        max_connections=max(100, concurrency),
        max_keepalive_connections=max(50, concurrency),
    )

    async with httpx.AsyncClient(base_url=config.base_url, timeout=timeout_s, limits=limits, trust_env=False) as client:
        async def worker() -> None:
            nonlocal next_index, failures
            while True:
                async with lock:
                    if next_index >= total_requests:
                        return
                    request_id = next_index
                    next_index += 1

                kwargs = request_kwargs_for_scenario(scenario)
                t0 = time.perf_counter()
                try:
                    response = await client.request(scenario.method, scenario.path, **kwargs)
                    _ = response.content

                    latency_ms = (time.perf_counter() - t0) * 1000.0
                    latencies_ms.append(latency_ms)

                    key = str(response.status_code)
                    status_counts[key] = status_counts.get(key, 0) + 1

                    if response.status_code != scenario.expected_status:
                        failures += 1
                except Exception as exc:
                    failures += 1
                    if len(error_samples) < 5:
                        error_samples.append(f"{type(exc).__name__}: {exc}")

                    latency_ms = (time.perf_counter() - t0) * 1000.0
                    latencies_ms.append(latency_ms)

        workers = [asyncio.create_task(worker()) for _ in range(concurrency)]
        await asyncio.gather(*workers)

    duration = max(time.perf_counter() - start, 1e-9)
    successes = max(0, total_requests - failures)

    sorted_latencies = sorted(latencies_ms)

    stop_event.set()
    process_stats = await sampler_task

    return LoadResult(
        requests=total_requests,
        successes=successes,
        failures=failures,
        duration_seconds=duration,
        throughput_rps=successes / duration,
        p50_ms=quantile(sorted_latencies, 0.50),
        p90_ms=quantile(sorted_latencies, 0.90),
        p95_ms=quantile(sorted_latencies, 0.95),
        p99_ms=quantile(sorted_latencies, 0.99),
        status_counts=status_counts,
        process=process_stats,
        error_samples=error_samples,
    )


# The active framework process PID is set by run_framework_benchmarks.
_ACTIVE_FRAMEWORK_PID: int | None = None


def config_process_pid(_config: FrameworkConfig) -> int:
    if _ACTIVE_FRAMEWORK_PID is None:
        raise RuntimeError("Framework PID is not initialized")
    return _ACTIVE_FRAMEWORK_PID


async def run_websocket_load(
    config: FrameworkConfig,
    scenario: WebSocketScenario,
    timeout_s: float,
) -> dict[str, Any]:
    if not config.websocket_supported:
        return {
            "supported": False,
            "skipped": True,
            "reason": "websocket_not_supported_in_stack",
        }

    latencies_ms: list[float] = []
    failures = 0

    ws_url = f"ws://{config.host}:{config.port}{scenario.path}"

    stop_event = asyncio.Event()
    sampler_task = asyncio.create_task(sample_process(pid=config_process_pid(config), stop_event=stop_event))

    start = time.perf_counter()

    async def worker(worker_id: int) -> None:
        nonlocal failures

        try:
            async with websockets.connect(ws_url, open_timeout=timeout_s, close_timeout=timeout_s, max_size=2**20) as ws:
                for msg_idx in range(scenario.messages_per_connection):
                    seq = worker_id * 1_000_000 + msg_idx
                    if config.websocket_protocol == "aquilia":
                        payload = {
                            "id": str(seq),
                            "type": "event",
                            "event": "ping",
                            "payload": {
                                "id": str(seq),
                                "payload": "echo",
                            },
                            "ack": True,
                        }
                    else:
                        payload = {
                            "id": str(seq),
                            "event": "ping",
                            "payload": {
                                "id": str(seq),
                                "payload": "echo",
                            },
                        }

                    t0 = time.perf_counter()
                    await ws.send(json.dumps(payload))
                    await ws.recv()
                    latencies_ms.append((time.perf_counter() - t0) * 1000.0)
        except Exception:
            failures += scenario.messages_per_connection

    workers = [asyncio.create_task(worker(worker_id)) for worker_id in range(scenario.connections)]
    await asyncio.gather(*workers)

    duration = max(time.perf_counter() - start, 1e-9)
    total_messages = scenario.connections * scenario.messages_per_connection
    successes = max(0, total_messages - failures)

    stop_event.set()
    process_stats = await sampler_task

    sorted_latencies = sorted(latencies_ms)

    return {
        "supported": True,
        "skipped": False,
        "connections": scenario.connections,
        "messages": total_messages,
        "successes": successes,
        "failures": failures,
        "duration_seconds": duration,
        "throughput_msgs_per_sec": successes / duration,
        "p50_ms": quantile(sorted_latencies, 0.50),
        "p90_ms": quantile(sorted_latencies, 0.90),
        "p95_ms": quantile(sorted_latencies, 0.95),
        "p99_ms": quantile(sorted_latencies, 0.99),
        "process": asdict(process_stats),
    }


async def run_framework_benchmarks(
    config: FrameworkConfig,
    args: argparse.Namespace,
    output_dir: Path,
) -> dict[str, Any]:
    global _ACTIVE_FRAMEWORK_PID

    logs_dir = output_dir / "logs"
    handle = start_server(config, logs_dir)

    framework_result: dict[str, Any] = {
        "framework": config.name,
        "base_url": config.base_url,
        "log_path": str(handle.log_path.relative_to(REPO_ROOT)),
        "startup_seconds": None,
        "scenarios": {},
        "websocket": None,
        "error": None,
    }

    try:
        startup_seconds = await wait_for_health(config, handle, args.startup_timeout)
        framework_result["startup_seconds"] = startup_seconds
        _ACTIVE_FRAMEWORK_PID = handle.process.pid

        for scenario in HTTP_SCENARIOS:
            requests = scale_requests(args.requests, scenario.request_weight)
            concurrency = scale_concurrency(args.concurrency, scenario.concurrency_factor)

            warmup_requests = min(args.warmup, max(5, int(requests * 0.15)))
            if warmup_requests > 0:
                await run_http_load(config, scenario, warmup_requests, max(1, concurrency // 2), args.timeout)

            result = await run_http_load(config, scenario, requests, concurrency, args.timeout)
            framework_result["scenarios"][scenario.name] = asdict(result)

        if args.skip_websocket:
            framework_result["websocket"] = {
                "supported": config.websocket_supported,
                "skipped": True,
                "reason": "skip_websocket_flag",
            }
        else:
            ws_messages_per_connection = 40 if args.quick else 80
            ws_connections = max(6, args.concurrency // 8) if args.quick else max(12, args.concurrency // 4)
            ws_scenario = WebSocketScenario(connections=ws_connections, messages_per_connection=ws_messages_per_connection)
            framework_result["websocket"] = await run_websocket_load(config, ws_scenario, args.timeout)

    except Exception as exc:
        framework_result["error"] = str(exc)
    finally:
        stop_server(handle)
        _ACTIVE_FRAMEWORK_PID = None

    return framework_result


def score_framework(result: dict[str, Any]) -> dict[str, Any]:
    scenarios = result.get("scenarios", {})
    if not scenarios:
        return {
            "throughput_rps_mean": None,
            "p95_ms_mean": None,
            "failure_rate_percent": None,
        }

    throughput_values: list[float] = []
    p95_values: list[float] = []
    failures = 0
    requests = 0

    for payload in scenarios.values():
        throughput_values.append(float(payload["throughput_rps"]))
        p95 = payload.get("p95_ms")
        if p95 is not None:
            p95_values.append(float(p95))
        failures += int(payload["failures"])
        requests += int(payload["requests"])

    return {
        "throughput_rps_mean": sum(throughput_values) / len(throughput_values),
        "p95_ms_mean": (sum(p95_values) / len(p95_values)) if p95_values else None,
        "failure_rate_percent": (failures / requests * 100.0) if requests else None,
    }


def build_markdown_report(results: dict[str, Any]) -> str:
    lines: list[str] = []
    meta = results["meta"]

    lines.append("# Aquilia vs FastAPI vs Flask Benchmark Report")
    lines.append("")
    lines.append(f"Generated at: {meta['timestamp_utc']}")
    lines.append("")
    lines.append("## Methodology")
    lines.append("")
    lines.append("- All frameworks ran with a single server process via Uvicorn on localhost.")
    lines.append("- Each HTTP scenario used scenario-specific warmup, then measured throughput and latency percentiles.")
    lines.append("- CPU and RSS memory were sampled during each scenario.")
    lines.append("- WebSocket benchmark used echo round trips where supported.")
    lines.append("- Flask is treated as WebSocket unsupported in this suite (no extra extension stack).")
    lines.append("")
    lines.append("## Environment")
    lines.append("")
    lines.append(f"- Platform: {meta['environment']['platform']}")
    lines.append(f"- Python: {meta['environment']['python_version']}")
    lines.append(f"- CPU cores: {meta['environment']['cpu_count']}")
    lines.append("")
    lines.append("## Startup")
    lines.append("")
    lines.append("| Framework | Startup (s) | Error |")
    lines.append("|---|---:|---|")

    for framework, payload in results["frameworks"].items():
        startup = payload.get("startup_seconds")
        startup_display = f"{startup:.4f}" if isinstance(startup, (float, int)) else "n/a"
        error = payload.get("error") or ""
        lines.append(f"| {framework} | {startup_display} | {error} |")

    lines.append("")

    for framework, payload in results["frameworks"].items():
        lines.append(f"## {framework.capitalize()} Scenario Results")
        lines.append("")

        if payload.get("error"):
            lines.append(f"- Framework run failed: {payload['error']}")
            lines.append("")
            continue

        lines.append("| Scenario | Requests | Throughput req/s | P50 ms | P95 ms | P99 ms | Failures | Avg CPU % | Peak RSS MB |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")

        for scenario in HTTP_SCENARIOS:
            entry = payload["scenarios"].get(scenario.name)
            if not entry:
                continue
            process = entry["process"]
            lines.append(
                "| "
                + f"{scenario.name} | {entry['requests']} | {entry['throughput_rps']:.2f} | "
                + f"{_fmt(entry['p50_ms'])} | {_fmt(entry['p95_ms'])} | {_fmt(entry['p99_ms'])} | "
                + f"{entry['failures']} | {process['avg_cpu_percent']:.2f} | {process['peak_rss_mb']:.2f} |"
            )

        ws = payload.get("websocket") or {}
        lines.append("")
        lines.append("### WebSocket")
        if ws.get("skipped"):
            lines.append(f"- Skipped: {ws.get('reason', 'unknown')}")
        else:
            lines.append(
                "- "
                + f"Throughput: {ws['throughput_msgs_per_sec']:.2f} msg/s, "
                + f"P95: {_fmt(ws['p95_ms'])} ms, "
                + f"Failures: {ws['failures']}"
            )
        lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append("| Framework | Mean Throughput req/s | Mean P95 ms | Failure Rate % |")
    lines.append("|---|---:|---:|---:|")

    for framework, payload in results["frameworks"].items():
        score = payload.get("score") or {}
        lines.append(
            f"| {framework} | {_fmt(score.get('throughput_rps_mean'))} | {_fmt(score.get('p95_ms_mean'))} | {_fmt(score.get('failure_rate_percent'))} |"
        )

    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- Compare both throughput and tail latency together; single-metric ranking is misleading.")
    lines.append("- Error-path scenarios are intentionally included because production workloads include failures.")
    lines.append("- Use multiple benchmark runs and median-of-runs before making final architecture decisions.")

    return "\n".join(lines)


def _fmt(value: float | int | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.2f}"


async def main() -> int:
    args = parse_args()

    if args.quick:
        args.requests = max(280, args.requests // 5)
        args.concurrency = max(12, args.concurrency // 2)
        args.warmup = min(50, args.warmup)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    output_dir = Path(args.output_dir) if args.output_dir else (RESULTS_ROOT / timestamp)
    output_dir.mkdir(parents=True, exist_ok=True)

    framework_names = list(dict.fromkeys(args.frameworks))

    framework_results: dict[str, Any] = {}
    for offset, framework in enumerate(framework_names):
        config = build_framework_config(framework, args.host, args.base_port + offset)
        print(f"[bench] starting {framework} on {config.base_url}")
        result = await run_framework_benchmarks(config, args, output_dir)
        result["score"] = score_framework(result)
        framework_results[framework] = result
        print(f"[bench] completed {framework}")

    results = {
        "meta": {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "arguments": vars(args),
            "environment": {
                "platform": platform.platform(),
                "python_version": sys.version.split()[0],
                "cpu_count": os.cpu_count(),
            },
            "workspace": str(REPO_ROOT),
        },
        "frameworks": framework_results,
    }

    json_path = output_dir / "results.json"
    markdown_path = output_dir / "report.md"

    json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    markdown_path.write_text(build_markdown_report(results), encoding="utf-8")

    latest_link = RESULTS_ROOT / "latest"
    if latest_link.exists() or latest_link.is_symlink():
        latest_link.unlink()
    latest_link.symlink_to(output_dir.resolve())

    print(f"[bench] wrote JSON results to {json_path}")
    print(f"[bench] wrote markdown report to {markdown_path}")
    print(f"[bench] updated latest symlink: {latest_link} -> {output_dir.resolve()}")

    return 0


if __name__ == "__main__":
    if os.name != "nt":
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    raise SystemExit(asyncio.run(main()))
