# Aquilia vs FastAPI vs Flask Benchmark Report

Generated at: 2026-04-05T05:33:34.602139+00:00

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
| aquilia | 0.4939 |  |

## Aquilia Scenario Results

| Scenario | Requests | Throughput req/s | P50 ms | P95 ms | P99 ms | Failures | Avg CPU % | Peak RSS MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| health | 360 | 640.74 | 31.81 | 135.62 | 242.36 | 0 | 3.53 | 84.98 |
| json_simple | 360 | 610.78 | 35.42 | 136.15 | 212.29 | 0 | 3.23 | 84.98 |
| json_large | 216 | 913.13 | 26.48 | 29.45 | 33.41 | 0 | 47.00 | 85.12 |
| di_chain | 360 | 621.39 | 32.64 | 132.52 | 254.86 | 0 | 3.13 | 85.12 |
| middleware_stack | 324 | 1675.96 | 16.42 | 19.21 | 20.86 | 0 | 0.00 | 85.12 |
| route_static | 324 | 1702.31 | 16.28 | 18.78 | 20.93 | 0 | 0.00 | 85.12 |
| route_params | 324 | 598.50 | 37.48 | 132.13 | 201.38 | 0 | 3.17 | 85.12 |
| route_dense | 288 | 585.33 | 34.44 | 145.04 | 200.56 | 0 | 2.90 | 85.14 |
| body_json | 288 | 536.36 | 24.61 | 133.88 | 200.46 | 0 | 3.73 | 85.16 |
| body_form | 216 | 547.86 | 21.12 | 98.99 | 159.09 | 0 | 3.25 | 85.16 |
| body_multipart | 108 | 893.92 | 6.87 | 23.93 | 42.87 | 0 | 0.00 | 85.22 |
| response_text | 324 | 691.03 | 27.31 | 118.28 | 160.49 | 0 | 3.43 | 85.97 |
| response_stream | 108 | 630.06 | 14.75 | 53.03 | 75.38 | 0 | 0.00 | 85.98 |
| response_file | 180 | 576.19 | 19.38 | 85.86 | 132.49 | 0 | 9.25 | 87.31 |
| static_file | 216 | 0.00 | 20.64 | 96.34 | 145.66 | 216 | 12.45 | 89.11 |
| compute_async | 180 | 605.15 | 27.31 | 155.60 | 212.58 | 0 | 3.45 | 89.72 |
| error_handled | 180 | 575.63 | 30.52 | 113.40 | 151.33 | 0 | 33.55 | 90.56 |
| error_unhandled | 144 | 447.24 | 40.87 | 97.48 | 130.18 | 0 | 39.20 | 92.05 |

### WebSocket
- Throughput: 8059.10 msg/s, P95: 0.34 ms, Failures: 0

## Summary

| Framework | Mean Throughput req/s | Mean P95 ms | Failure Rate % |
|---|---:|---:|---:|
| aquilia | 713.98 | 95.87 | 4.80 |

## Notes

- Compare both throughput and tail latency together; single-metric ranking is misleading.
- Error-path scenarios are intentionally included because production workloads include failures.
- Use multiple benchmark runs and median-of-runs before making final architecture decisions.