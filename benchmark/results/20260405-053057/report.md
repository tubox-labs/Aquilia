# Aquilia vs FastAPI vs Flask Benchmark Report

Generated at: 2026-04-05T05:31:42.439883+00:00

## Methodology

- All frameworks ran with a single server process via Uvicorn on localhost.
- Each HTTP scenario used scenario-specific warmup, then measured throughput and latency percentiles.
- CPU and RSS memory were sampled during each scenario.
- WebSocket benchmark used echo round trips where supported.
- Flask is treated as WebSocket unsupported in this suite (no extra extension stack).

## Environment

- Platform: macOS-26.3.1-arm64-arm-64bit-Mach-O
- Python: 3.14.3
- CPU cores: 10

## Startup

| Framework | Startup (s) | Error |
|---|---:|---|
| aquilia | n/a | Timed out waiting for aquilia health endpoint |

## Aquilia Scenario Results

- Framework run failed: Timed out waiting for aquilia health endpoint

## Summary

| Framework | Mean Throughput req/s | Mean P95 ms | Failure Rate % |
|---|---:|---:|---:|
| aquilia | n/a | n/a | n/a |

## Notes

- Compare both throughput and tail latency together; single-metric ranking is misleading.
- Error-path scenarios are intentionally included because production workloads include failures.
- Use multiple benchmark runs and median-of-runs before making final architecture decisions.