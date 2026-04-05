# Aquilia vs FastAPI vs Flask Benchmark Report

Generated at: 2026-04-05T05:34:08.376856+00:00

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
| aquilia | 0.3566 |  |

## Aquilia Scenario Results

| Scenario | Requests | Throughput req/s | P50 ms | P95 ms | P99 ms | Failures | Avg CPU % | Peak RSS MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| health | 360 | 616.68 | 35.46 | 142.48 | 215.04 | 0 | 3.47 | 84.97 |
| json_simple | 360 | 617.36 | 34.73 | 144.05 | 192.02 | 0 | 3.47 | 85.02 |
| json_large | 216 | 997.17 | 25.52 | 26.93 | 28.09 | 0 | 48.05 | 85.22 |
| di_chain | 360 | 623.87 | 33.17 | 137.97 | 218.72 | 0 | 3.97 | 85.22 |
| middleware_stack | 324 | 589.16 | 35.06 | 144.43 | 204.10 | 0 | 3.43 | 85.22 |
| route_static | 324 | 613.53 | 34.00 | 132.15 | 181.10 | 0 | 3.27 | 85.22 |
| route_params | 324 | 623.96 | 33.09 | 145.70 | 199.31 | 0 | 3.20 | 85.22 |
| route_dense | 288 | 617.28 | 33.03 | 130.94 | 225.17 | 0 | 3.27 | 85.22 |
| body_json | 288 | 532.93 | 24.88 | 142.08 | 208.15 | 0 | 4.20 | 85.36 |
| body_form | 216 | 515.05 | 24.02 | 132.87 | 162.13 | 0 | 3.05 | 85.36 |
| body_multipart | 108 | 1059.64 | 6.26 | 17.21 | 30.11 | 0 | 0.00 | 85.44 |
| response_text | 324 | 628.01 | 32.40 | 136.34 | 215.04 | 0 | 3.37 | 86.09 |
| response_stream | 108 | 470.39 | 27.47 | 68.25 | 81.57 | 0 | 7.65 | 86.12 |
| response_file | 180 | 545.66 | 21.60 | 86.71 | 139.75 | 0 | 10.05 | 87.38 |
| static_file | 216 | 598.78 | 21.76 | 101.56 | 159.73 | 0 | 11.60 | 87.94 |
| compute_async | 180 | 1282.79 | 21.53 | 29.64 | 32.52 | 0 | 0.00 | 87.94 |
| error_handled | 180 | 419.10 | 39.23 | 168.58 | 319.85 | 0 | 35.40 | 90.59 |
| error_unhandled | 144 | 445.01 | 34.48 | 124.84 | 177.08 | 0 | 38.70 | 91.70 |

### WebSocket
- Throughput: 8804.63 msg/s, P95: 0.46 ms, Failures: 0

## Summary

| Framework | Mean Throughput req/s | Mean P95 ms | Failure Rate % |
|---|---:|---:|---:|
| aquilia | 655.35 | 111.82 | 0.00 |

## Notes

- Compare both throughput and tail latency together; single-metric ranking is misleading.
- Error-path scenarios are intentionally included because production workloads include failures.
- Use multiple benchmark runs and median-of-runs before making final architecture decisions.