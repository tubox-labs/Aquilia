from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path

# Setup paths
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
BENCH_DIR = WORKSPACE_ROOT / "benchmarks"
TEMP_PAYLOAD = BENCH_DIR / "temp_payload.json"
TEMP_UPLOAD = BENCH_DIR / "temp_upload.txt"
OHA_RESULTS = BENCH_DIR / "oha_temp_results.json"

FRAMEWORKS = {
    "Aquilia": "benchmarks.frameworks.aquilia.main:app",
    "FastAPI": "benchmarks.frameworks.fastapi.main:app",
    "Starlette": "benchmarks.frameworks.starlette.main:app",
    "Litestar": "benchmarks.frameworks.litestar.main:app",
    "Falcon": "benchmarks.frameworks.falcon.main:app",
    "Sanic": "benchmarks.frameworks.sanic.main:app",
    "Quart": "benchmarks.frameworks.quart.main:app",
    "Flask": "benchmarks.frameworks.flask.main:asgi_app",
    "Django": "benchmarks.frameworks.django.main:app",
}

SCENARIOS = [
    "plaintext",
    "json",
    "json_large",
    "db_single",
    "db_queries",
    "db_updates",
    "fortunes",
    "cached",
    "validation",
    "route_static",
    "route_params",
    "di",
    "multipart",
    "stream",
    "middleware_0",
    "middleware_5",
    "middleware_10",
]

def kill_port_8100():
    try:
        cmd = "kill -9 $(lsof -t -i:8100) 2>/dev/null || true"
        subprocess.run(cmd, shell=True)
    except Exception:
        pass

def wait_for_server(url: str, timeout: float = 8.0) -> bool:
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as conn:
                if conn.status == 200:
                    return True
        except Exception:
            time.sleep(0.1)
    return False

def run_scenario(scenario: str, framework: str, duration: str, concurrency: int) -> dict | None:
    url = "http://127.0.0.1:8100"
    method = "GET"
    extra_args = []

    # Configure validation endpoint mapping
    if scenario == "validation":
        method = "POST"
        extra_args += ["-T", "application/json", "-D", str(TEMP_PAYLOAD)]
        if framework == "Aquilia":
            url += "/validation/blueprint"
        elif framework in ["Flask", "Django"]:
            url += "/validation/dataclass"
        else:
            url += "/validation/pydantic"
    elif scenario == "multipart":
        method = "POST"
        extra_args += ["-F", f"file=@{TEMP_UPLOAD}"]
        url += "/body/multipart"
    elif scenario == "plaintext" or scenario.startswith("middleware_"):
        url += "/plaintext"
    elif scenario == "json":
        url += "/json"
    elif scenario == "json_large":
        url += "/json/large"
    elif scenario == "db_single":
        url += "/db"
    elif scenario == "db_queries":
        url += "/queries?queries=5"
    elif scenario == "db_updates":
        url += "/updates?queries=5"
    elif scenario == "fortunes":
        url += "/fortunes"
    elif scenario == "cached":
        url += "/cached?queries=5"
    elif scenario == "route_static":
        url += "/route/static"
    elif scenario == "route_params":
        url += "/route/params/123/orders/456"
    elif scenario == "di":
        url += "/di"
    elif scenario == "stream":
        url += "/response/stream"
    else:
        url += f"/{scenario}"

    # Setup oha arguments
    oha_cmd = [
        "oha",
        "-z", duration,
        "-c", str(concurrency),
        "-m", method,
        "--no-tui",
        "--output-format", "json",
        "-o", str(OHA_RESULTS),
    ] + extra_args + [url]

    # Run oha
    print(f"  -> Testing {scenario} endpoint...")
    res = subprocess.run(oha_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"     [ERROR] oha command failed: {res.stderr}")
        return None

    # Parse JSON results
    try:
        with open(OHA_RESULTS, "r") as f:
            metrics = json.load(f)
        
        summary = metrics.get("summary", {})
        latency = metrics.get("latencyPercentiles", {})
        
        # Calculate stats
        qps = summary.get("requestsPerSec", 0.0)
        avg_ms = (summary.get("average") or 0.0) * 1000.0
        p50_ms = (latency.get("p50") or 0.0) * 1000.0
        p95_ms = (latency.get("p95") or 0.0) * 1000.0
        p99_ms = (latency.get("p99") or 0.0) * 1000.0
        success_rate = summary.get("successRate", 0.0) * 100.0
        
        return {
            "qps": qps,
            "avg_ms": avg_ms,
            "p50_ms": p50_ms,
            "p95_ms": p95_ms,
            "p99_ms": p99_ms,
            "success_rate": success_rate,
        }
    except Exception as exc:
        print(f"     [ERROR] Failed to parse oha output: {exc}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Professional Framework Benchmarking Platform")
    parser.add_argument("--duration", default="5s", help="Duration for each load test run (e.g. 5s, 10s)")
    parser.add_argument("--concurrency", type=int, default=50, help="Concurrency for load tests")
    parser.add_argument("--frameworks", help="Comma-separated list of frameworks to benchmark")
    parser.add_argument("--scenarios", help="Comma-separated list of scenarios to run")
    parser.add_argument("--output", default="benchmarks/report.md", help="Path to write the report markdown")
    args = parser.parse_args()

    # Determine framework list
    target_frameworks = list(FRAMEWORKS.keys())
    if args.frameworks:
        target_frameworks = [f.strip() for f in args.frameworks.split(",") if f.strip() in FRAMEWORKS]

    # Determine scenario list
    target_scenarios = SCENARIOS.copy()
    if args.scenarios:
        target_scenarios = [s.strip() for s in args.scenarios.split(",") if s.strip() in SCENARIOS]

    # Setup temp files
    with open(TEMP_PAYLOAD, "w") as f:
        json.dump({"username": "test_user", "email": "test@example.com", "age": 25, "is_active": True}, f)
    with open(TEMP_UPLOAD, "w") as f:
        f.write("A" * 10240)  # 10KB dummy file

    # Warm up database
    print("Standardizing database state...")
    subprocess.run(["uv", "run", "python3", "benchmarks/techempower/db_init.py"], check=True)

    # Dictionary to store all results
    run_results = {fw: {} for fw in target_frameworks}

    venv_python = WORKSPACE_ROOT / ".venv" / "bin" / "python"

    # Iterate frameworks
    for fw in target_frameworks:
        app_target = FRAMEWORKS[fw]
        print(f"\n========================================\nBENCHMARKING: {fw}\n========================================")
        
        # We need to run scenarios that might require different middleware stacks
        # Group scenarios by middleware layers they require
        scenario_groups = {
            0: [],
            5: [],
            10: [],
        }
        for s in target_scenarios:
            if s == "middleware_5":
                scenario_groups[5].append(s)
            elif s == "middleware_10":
                scenario_groups[10].append(s)
            else:
                scenario_groups[0].append(s)

        for layers, scs in scenario_groups.items():
            if not scs:
                continue
                
            kill_port_8100()
            time.sleep(0.5)

            # Build environment
            env = os.environ.copy()
            env["PYTHONPATH"] = str(WORKSPACE_ROOT)
            env["MIDDLEWARE_LAYERS"] = str(layers)
            
            # Start Uvicorn process
            cmd = [
                "uv", "run", "uvicorn",
                app_target,
                "--host", "127.0.0.1",
                "--port", "8100",
                "--workers", "1",
                "--log-level", "warning"
            ]
            print(f"-> Starting {fw} server with {layers} middleware layers...")
            server_proc = subprocess.Popen(cmd, env=env, cwd=str(WORKSPACE_ROOT))
            
            try:
                # Wait for boot
                if not wait_for_server("http://127.0.0.1:8100/health"):
                    print(f"   [ERROR] Server for {fw} failed to respond to health checks.")
                    continue
                
                # Run scenarios
                for sc in scs:
                    metrics = run_scenario(sc, fw, args.duration, args.concurrency)
                    if metrics:
                        run_results[fw][sc] = metrics
            finally:
                print(f"-> Terminating {fw} server...")
                server_proc.terminate()
                try:
                    server_proc.wait(timeout=3.0)
                except subprocess.TimeoutExpired:
                    server_proc.kill()
                kill_port_8100()
                time.sleep(0.5)

    # Clean up temp files
    for path in [TEMP_PAYLOAD, TEMP_UPLOAD, OHA_RESULTS]:
        if path.exists():
            path.unlink()

    # Run startup benchmarks using hyperfine
    print("\n========================================\nRUNNING COLD STARTUP BENCHMARKS\n========================================")
    startup_script = BENCH_DIR / "startup" / "startup_bench.py"
    subprocess.run(["uv", "run", "python3", str(startup_script)], check=True)
    
    # Read startup results
    startup_results = {}
    startup_json = BENCH_DIR / "startup" / "formatted_results.json"
    if startup_json.exists():
        with open(startup_json, "r") as f:
            startup_results = json.load(f)

    # Write Markdown Report
    report_path = WORKSPACE_ROOT / args.output
    write_report(report_path, target_frameworks, target_scenarios, run_results, startup_results, args.duration, args.concurrency)
    print(f"\nBenchmarking complete! Report written to: {report_path}")

def write_report(path: Path, frameworks: list[str], scenarios: list[str], run_results: dict, startup_results: dict, duration: str, concurrency: int):
    with open(path, "w") as f:
        f.write("# Aquilia Professional Web Framework Benchmarks\n\n")
        f.write("This document presents the objective, reproducible, and statistically valid benchmarks comparing the performance characteristics of Aquilia against major Python web frameworks.\n\n")
        
        f.write("## Benchmark Parameters\n")
        f.write(f"- **Load Testing Utility**: `oha` (Rust-based HTTP/1.1 load generator)\n")
        f.write(f"- **Concurrency Level**: `{concurrency}` simultaneous connections\n")
        f.write(f"- **Duration**: `{duration}` per endpoint run\n")
        f.write(f"- **Server Environment**: Python 3.13 served via Uvicorn (Single worker thread)\n")
        f.write(f"- **Database Engine**: SQLite 3 (Standard 10,000-row TechEmpower Schema)\n\n")

        # 1. Cold Startup / Boot Performance
        if startup_results:
            f.write("## 1. Cold Startup & Importing Overhead\n")
            f.write("Measures the pure framework importing and initialization time. Fast cold start times are critical for Serverless deployments and developer container boot-ups.\n\n")
            f.write("| Rank | Framework | Mean Startup (ms) | StdDev (ms) | Min (ms) | Max (ms) |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
            
            sorted_startup = sorted(startup_results.items(), key=lambda x: x[1]["mean"])
            for rank, (fw, stats) in enumerate(sorted_startup, 1):
                f.write(f"| {rank} | {fw} | {stats['mean']:.2f}ms | ±{stats['stddev']:.2f}ms | {stats['min']:.2f}ms | {stats['max']:.2f}ms |\n")
            f.write("\n")

        # 2. Scenario Comparison Tables
        f.write("## 2. HTTP Throughput and Latency Results\n")
        f.write("The tables below highlight framework performance metrics across various workload scenarios.\n\n")

        for sc in scenarios:
            f.write(f"### Scenario: `{sc}`\n")
            # Description of scenario
            desc = {
                "plaintext": "GET `/plaintext` returning 'Hello, World!' (Measures raw HTTP parsing and serialization throughput).",
                "json": "GET `/json` returning a small JSON dictionary. (Measures JSON encoding overhead).",
                "json_large": "GET `/json/large` returning a nested 100KB JSON payload. (Measures large serialization performance).",
                "db_single": "GET `/db` executing 1 SQL query. (Measures single database retrieval latency).",
                "db_queries": "GET `/queries` executing 5 random SQL queries sequentially.",
                "db_updates": "GET `/updates` executing 5 select-update SQL statements under a database transaction.",
                "fortunes": "GET `/fortunes` fetching fortunes from database, adding a custom fortune, sorting, and rendering to HTML via Jinja2.",
                "cached": "GET `/cached` retrieving 5 random items from memory cache with fallback to DB.",
                "route_static": "GET `/route/static` matched against a large route table containing 500 placeholder routes. (Measures routing lookup performance).",
                "route_params": "GET `/route/params/<user_id>/orders/<order_id>` parsing path variables.",
                "di": "GET `/di` resolving a nested dependency injection hierarchy (Leaf -> Mid -> Top).",
                "multipart": "POST `/body/multipart` uploading a 10KB text file. (Measures multipart parsing).",
                "validation": "POST `/validation` parsing and validating a nested payload (Blueprint vs Pydantic vs Dataclasses).",
                "stream": "GET `/response/stream` sending a 32KB chunked-encoded stream.",
                "middleware_0": "GET `/plaintext` with 0 custom middleware layers.",
                "middleware_5": "GET `/plaintext` with 5 stacked custom middleware layers.",
                "middleware_10": "GET `/plaintext` with 10 stacked custom middleware layers.",
            }.get(sc, "")
            
            f.write(f"{desc}\n\n")
            f.write("| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")
            
            # Sort frameworks by QPS descending
            sc_results = []
            for fw in frameworks:
                if sc in run_results[fw]:
                    sc_results.append((fw, run_results[fw][sc]))
                    
            sorted_sc = sorted(sc_results, key=lambda x: x[1]["qps"], reverse=True)
            for rank, (fw, m) in enumerate(sorted_sc, 1):
                f.write(f"| {rank} | {fw} | {m['qps']:.2f} req/s | {m['avg_ms']:.2f} ms | {m['p50_ms']:.2f} ms | {m['p95_ms']:.2f} ms | {m['success_rate']:.1f}% |\n")
            f.write("\n")

        # 3. Dynamic Chart data or Summary
        f.write("## 3. Key Performance Insights\n")
        f.write("### Middleware Scaling Cost\n")
        f.write("This table summarizes how throughput scales as middleware layers are stacked (0 -> 5 -> 10 layers).\n\n")
        f.write("| Framework | 0 Layers QPS | 5 Layers QPS | 10 Layers QPS | Overhead (10 vs 0) |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- |\n")
        for fw in frameworks:
            q0 = run_results[fw].get("middleware_0", {}).get("qps", 0.0)
            q5 = run_results[fw].get("middleware_5", {}).get("qps", 0.0)
            q10 = run_results[fw].get("middleware_10", {}).get("qps", 0.0)
            overhead = ((q0 - q10) / q0 * 100) if q0 > 0 else 0.0
            f.write(f"| {fw} | {q0:.2f} | {q5:.2f} | {q10:.2f} | {overhead:.1f}% decrease |\n")
        f.write("\n")

if __name__ == "__main__":
    main()
