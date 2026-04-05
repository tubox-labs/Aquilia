# Aquilia vs FastAPI vs Flask Benchmark Report

Generated at: 2026-04-05T05:30:26.942371+00:00

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
| fastapi | 0.6408 |  |
| flask | 0.2287 |  |

## Aquilia Scenario Results

- Framework run failed: Timed out waiting for aquilia health endpoint

## Fastapi Scenario Results

| Scenario | Requests | Throughput req/s | P50 ms | P95 ms | P99 ms | Failures | Avg CPU % | Peak RSS MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| health | 360 | 586.83 | 38.75 | 127.83 | 206.57 | 0 | 6.97 | 64.73 |
| json_simple | 360 | 620.20 | 33.00 | 129.65 | 196.68 | 0 | 8.13 | 65.20 |
| json_large | 216 | 505.31 | 33.75 | 146.65 | 230.65 | 0 | 19.70 | 72.69 |
| di_chain | 360 | 566.86 | 37.34 | 136.78 | 225.01 | 0 | 11.45 | 77.92 |
| middleware_stack | 324 | 644.04 | 33.84 | 118.30 | 179.58 | 0 | 6.57 | 80.31 |
| route_static | 324 | 1661.39 | 16.66 | 21.03 | 27.39 | 0 | 0.00 | 81.22 |
| route_params | 324 | 630.28 | 32.62 | 131.14 | 196.27 | 0 | 6.77 | 86.56 |
| route_dense | 288 | 632.77 | 31.17 | 152.06 | 218.74 | 0 | 9.10 | 89.33 |
| body_json | 288 | 573.59 | 23.71 | 120.27 | 160.85 | 0 | 9.80 | 91.34 |
| body_form | 216 | 583.08 | 18.75 | 113.53 | 133.55 | 0 | 7.85 | 91.34 |
| body_multipart | 108 | 826.29 | 7.35 | 26.51 | 55.17 | 0 | 0.00 | 91.38 |
| response_text | 324 | 636.49 | 31.66 | 117.79 | 193.32 | 0 | 6.67 | 91.45 |
| response_stream | 108 | 563.76 | 19.05 | 54.26 | 124.02 | 0 | 0.00 | 91.47 |
| response_file | 180 | 591.03 | 19.55 | 84.36 | 111.68 | 0 | 11.20 | 91.58 |
| static_file | 216 | 540.87 | 23.09 | 102.87 | 163.67 | 0 | 14.60 | 91.97 |
| compute_async | 180 | 527.97 | 31.22 | 157.85 | 215.20 | 0 | 6.30 | 91.98 |
| error_handled | 180 | 584.17 | 24.35 | 114.86 | 137.86 | 0 | 4.80 | 91.98 |
| error_unhandled | 144 | 755.09 | 23.46 | 33.57 | 36.93 | 2 | 0.00 | 92.34 |

### WebSocket
- Throughput: 11588.42 msg/s, P95: 0.23 ms, Failures: 0

## Flask Scenario Results

| Scenario | Requests | Throughput req/s | P50 ms | P95 ms | P99 ms | Failures | Avg CPU % | Peak RSS MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| health | 360 | 1609.69 | 17.72 | 19.66 | 21.58 | 0 | 22.15 | 52.41 |
| json_simple | 360 | 1687.59 | 16.93 | 19.09 | 19.71 | 0 | 23.15 | 52.66 |
| json_large | 216 | 644.89 | 38.93 | 41.67 | 47.27 | 0 | 47.70 | 52.95 |
| di_chain | 360 | 1679.19 | 16.59 | 18.96 | 22.02 | 0 | 0.00 | 52.95 |
| middleware_stack | 324 | 1583.00 | 17.86 | 20.36 | 23.33 | 0 | 0.00 | 52.95 |
| route_static | 324 | 1640.41 | 17.21 | 19.92 | 22.23 | 0 | 0.00 | 52.95 |
| route_params | 324 | 1609.49 | 17.17 | 20.13 | 23.11 | 0 | 0.00 | 52.95 |
| route_dense | 288 | 1592.04 | 16.73 | 21.83 | 23.77 | 0 | 0.00 | 53.02 |
| body_json | 288 | 583.86 | 19.54 | 125.04 | 182.74 | 0 | 11.97 | 53.58 |
| body_form | 216 | 553.96 | 17.90 | 116.60 | 161.14 | 0 | 9.65 | 53.78 |
| body_multipart | 108 | 879.20 | 7.38 | 20.88 | 39.22 | 0 | 0.00 | 53.94 |
| response_text | 324 | 1681.06 | 16.72 | 18.49 | 20.96 | 0 | 0.00 | 54.36 |
| response_stream | 108 | 577.69 | 22.45 | 26.22 | 30.61 | 0 | 0.00 | 54.80 |
| response_file | 180 | 601.94 | 17.64 | 88.43 | 126.69 | 0 | 11.40 | 55.14 |
| static_file | 216 | 594.20 | 21.45 | 94.77 | 143.56 | 0 | 12.00 | 55.52 |
| compute_async | 180 | 145.75 | 213.56 | 215.56 | 215.86 | 0 | 8.86 | 55.98 |
| error_handled | 180 | 602.02 | 23.43 | 92.98 | 160.56 | 0 | 10.00 | 55.98 |
| error_unhandled | 144 | 1209.80 | 13.33 | 18.28 | 21.25 | 0 | 0.00 | 56.42 |

### WebSocket
- Skipped: websocket_not_supported_in_stack

## Summary

| Framework | Mean Throughput req/s | Mean P95 ms | Failure Rate % |
|---|---:|---:|---:|
| aquilia | n/a | n/a | n/a |
| fastapi | 668.34 | 104.96 | 0.04 |
| flask | 1081.99 | 55.49 | 0.00 |

## Notes

- Compare both throughput and tail latency together; single-metric ranking is misleading.
- Error-path scenarios are intentionally included because production workloads include failures.
- Use multiple benchmark runs and median-of-runs before making final architecture decisions.