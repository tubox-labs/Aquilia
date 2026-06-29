from __future__ import annotations

import json
import subprocess
from pathlib import Path

def run_startup_bench():
    # Workspace root directory
    workspace_root = Path(__file__).resolve().parents[2]
    venv_python = workspace_root / ".venv" / "bin" / "python"
    
    # Output file path
    results_json = Path(__file__).resolve().parent / "startup_results.json"
    
    frameworks = {
        "Aquilia": "benchmarks.frameworks.aquilia.main",
        "FastAPI": "benchmarks.frameworks.fastapi.main",
        "Starlette": "benchmarks.frameworks.starlette.main",
        "Litestar": "benchmarks.frameworks.litestar.main",
        "Falcon": "benchmarks.frameworks.falcon.main",
        "Sanic": "benchmarks.frameworks.sanic.main",
        "Quart": "benchmarks.frameworks.quart.main",
        "Flask": "benchmarks.frameworks.flask.main",
        "Django": "benchmarks.frameworks.django.main"
    }
    
    hyperfine_cmd = [
        "hyperfine",
        "--warmup", "3",
        "--runs", "10",
        "--export-json", str(results_json),
    ]
    
    # Build command targets
    for name, module in frameworks.items():
        cmd_str = f"PYTHONPATH=. {venv_python} -c 'from {module} import app'"
        hyperfine_cmd.append(cmd_str)
        
    print("Running startup benchmarking with hyperfine...")
    print(f"Command: {' '.join(hyperfine_cmd)}")
    
    # Run hyperfine
    subprocess.run(hyperfine_cmd, cwd=str(workspace_root), check=True)
    
    # Read and parse results
    with open(results_json, "r") as f:
        data = json.load(f)
        
    results = {}
    for idx, (name, _) in enumerate(frameworks.items()):
        run_data = data["results"][idx]
        mean_ms = run_data["mean"] * 1000
        stddev_ms = run_data["stddev"] * 1000
        min_ms = run_data["min"] * 1000
        max_ms = run_data["max"] * 1000
        
        results[name] = {
            "mean": mean_ms,
            "stddev": stddev_ms,
            "min": min_ms,
            "max": max_ms
        }
        
    print("\n=== STARTUP BENCHMARK RESULTS ===")
    print(f"{'Framework':<15} | {'Mean (ms)':<10} | {'StdDev (ms)':<12} | {'Min (ms)':<10} | {'Max (ms)':<10}")
    print("-" * 67)
    for name, stats in sorted(results.items(), key=lambda x: x[1]["mean"]):
        print(f"{name:<15} | {stats['mean']:<10.2f} | {stats['stddev']:<12.2f} | {stats['min']:<10.2f} | {stats['max']:<10.2f}")
        
    # Save formatted results
    with open(Path(__file__).resolve().parent / "formatted_results.json", "w") as out:
        json.dump(results, out, indent=2)

if __name__ == "__main__":
    run_startup_bench()
