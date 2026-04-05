# Aquilia vs FastAPI vs Flask Benchmark Report

Generated at: 2026-04-05T05:32:32.938085+00:00

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
| aquilia | 0.5197 |  |

## Aquilia Scenario Results

| Scenario | Requests | Throughput req/s | P50 ms | P95 ms | P99 ms | Failures | Avg CPU % | Peak RSS MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| health | 360 | 1680.98 | 16.55 | 21.32 | 23.02 | 0 | 0.00 | 84.92 |
| json_simple | 360 | 1774.98 | 16.43 | 18.78 | 18.87 | 0 | 0.00 | 85.05 |
| json_large | 216 | 944.08 | 25.19 | 27.68 | 33.44 | 0 | 47.30 | 85.22 |
| di_chain | 360 | 1667.73 | 16.43 | 20.18 | 22.09 | 0 | 0.00 | 85.22 |
| middleware_stack | 324 | 1076.59 | 17.93 | 76.97 | 122.49 | 0 | 5.40 | 85.22 |
| route_static | 324 | 1658.74 | 16.58 | 21.15 | 24.16 | 0 | 0.00 | 85.22 |
| route_params | 324 | 610.01 | 35.33 | 135.60 | 222.13 | 0 | 3.37 | 85.23 |
| route_dense | 288 | 0.00 | 27.11 | 37.03 | 42.08 | 288 | 46.90 | 88.48 |
| body_json | 288 | 558.04 | 23.81 | 127.25 | 171.64 | 0 | 3.93 | 89.16 |
| body_form | 216 | 578.70 | 18.47 | 107.04 | 165.48 | 0 | 3.40 | 89.16 |
| body_multipart | 108 | 873.57 | 7.01 | 25.46 | 38.15 | 0 | 0.00 | 89.22 |
| response_text | 324 | 624.79 | 35.33 | 125.07 | 172.79 | 0 | 2.80 | 89.80 |
| response_stream | 108 | 543.76 | 18.29 | 60.07 | 70.57 | 0 | 0.00 | 89.81 |
| response_file | 180 | 584.63 | 18.52 | 88.17 | 118.10 | 0 | 8.75 | 90.95 |
| static_file | 216 | 0.00 | 20.15 | 88.59 | 131.64 | 216 | 14.60 | 91.45 |
| compute_async | 180 | 626.49 | 26.01 | 136.27 | 184.74 | 0 | 3.50 | 91.91 |
| error_handled | 180 | 514.99 | 35.02 | 122.49 | 186.83 | 0 | 30.25 | 92.64 |
| error_unhandled | 144 | 484.02 | 33.37 | 94.03 | 132.84 | 0 | 42.35 | 93.66 |

### WebSocket
- Throughput: 8118.56 msg/s, P95: 0.33 ms, Failures: 0

## Summary

| Framework | Mean Throughput req/s | Mean P95 ms | Failure Rate % |
|---|---:|---:|---:|
| aquilia | 822.34 | 74.06 | 11.20 |

## Notes

- Compare both throughput and tail latency together; single-metric ranking is misleading.
- Error-path scenarios are intentionally included because production workloads include failures.
- Use multiple benchmark runs and median-of-runs before making final architecture decisions.