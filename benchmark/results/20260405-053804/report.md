# Aquilia vs FastAPI vs Flask Benchmark Report

Generated at: 2026-04-05T05:38:20.940691+00:00

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
| fastapi | 0.3749 |  |

## Fastapi Scenario Results

| Scenario | Requests | Throughput req/s | P50 ms | P95 ms | P99 ms | Failures | Avg CPU % | Peak RSS MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| health | 360 | 398.03 | 58.33 | 201.14 | 332.00 | 0 | 5.94 | 64.83 |
| json_simple | 360 | 386.22 | 52.54 | 204.07 | 325.66 | 0 | 6.02 | 66.34 |
| json_large | 216 | 379.78 | 39.56 | 213.50 | 321.19 | 0 | 15.10 | 73.02 |
| di_chain | 360 | 395.91 | 49.96 | 244.87 | 393.21 | 0 | 9.04 | 78.33 |
| middleware_stack | 324 | 400.74 | 53.78 | 195.31 | 288.53 | 0 | 4.92 | 80.78 |
| route_static | 324 | 385.95 | 56.36 | 208.07 | 326.25 | 0 | 5.06 | 83.97 |
| route_params | 324 | 403.12 | 55.90 | 189.62 | 285.98 | 0 | 5.25 | 86.30 |
| route_dense | 288 | 428.94 | 48.28 | 196.24 | 267.64 | 0 | 7.62 | 89.20 |
| body_json | 288 | 473.54 | 31.68 | 141.77 | 229.66 | 0 | 7.70 | 92.70 |
| body_form | 216 | 519.69 | 19.02 | 121.17 | 202.61 | 0 | 7.40 | 93.16 |
| body_multipart | 108 | 890.79 | 7.35 | 18.89 | 26.94 | 0 | 0.00 | 93.19 |
| response_text | 324 | 416.22 | 53.62 | 177.16 | 276.86 | 0 | 5.25 | 93.25 |
| response_stream | 108 | 525.69 | 20.73 | 66.04 | 92.35 | 0 | 0.00 | 93.27 |
| response_file | 180 | 591.66 | 20.94 | 86.54 | 117.94 | 0 | 11.10 | 93.41 |
| static_file | 216 | 566.67 | 25.04 | 94.75 | 138.50 | 0 | 15.20 | 93.77 |
| compute_async | 180 | 392.10 | 37.54 | 229.86 | 320.24 | 0 | 5.43 | 93.47 |
| error_handled | 180 | 533.27 | 26.22 | 121.06 | 178.60 | 0 | 6.60 | 93.47 |
| error_unhandled | 144 | 737.26 | 21.33 | 33.34 | 34.37 | 47 | 0.00 | 93.83 |

### WebSocket
- Throughput: 9138.51 msg/s, P95: 0.41 ms, Failures: 0

## Summary

| Framework | Mean Throughput req/s | Mean P95 ms | Failure Rate % |
|---|---:|---:|---:|
| fastapi | 490.31 | 152.41 | 1.04 |

## Notes

- Compare both throughput and tail latency together; single-metric ranking is misleading.
- Error-path scenarios are intentionally included because production workloads include failures.
- Use multiple benchmark runs and median-of-runs before making final architecture decisions.