# Aquilia vs FastAPI vs Flask Benchmark Report

Generated at: 2026-04-05T05:42:35.408338+00:00

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
| fastapi | 0.4176 |  |

## Fastapi Scenario Results

| Scenario | Requests | Throughput req/s | P50 ms | P95 ms | P99 ms | Failures | Avg CPU % | Peak RSS MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| health | 360 | 387.10 | 57.59 | 210.79 | 290.75 | 0 | 5.78 | 64.52 |
| json_simple | 360 | 400.01 | 50.88 | 215.16 | 307.14 | 0 | 6.12 | 65.62 |
| json_large | 216 | 384.53 | 39.01 | 225.16 | 315.10 | 0 | 15.67 | 72.33 |
| di_chain | 360 | 373.93 | 56.96 | 220.90 | 432.21 | 0 | 8.60 | 77.78 |
| middleware_stack | 324 | 387.42 | 55.72 | 193.09 | 282.35 | 0 | 4.95 | 80.28 |
| route_static | 324 | 382.22 | 55.63 | 225.98 | 336.32 | 0 | 5.16 | 83.52 |
| route_params | 324 | 397.64 | 60.19 | 190.01 | 302.01 | 0 | 5.22 | 85.84 |
| route_dense | 288 | 401.34 | 51.74 | 200.89 | 285.55 | 0 | 7.10 | 88.66 |
| body_json | 288 | 438.58 | 35.37 | 151.07 | 265.72 | 0 | 8.88 | 93.23 |
| body_form | 216 | 484.62 | 21.27 | 126.13 | 231.51 | 0 | 9.17 | 93.23 |
| body_multipart | 108 | 888.96 | 6.94 | 19.28 | 32.41 | 0 | 0.00 | 93.36 |
| response_text | 324 | 385.81 | 54.35 | 208.81 | 324.58 | 0 | 6.07 | 93.42 |
| response_stream | 108 | 599.07 | 16.61 | 62.38 | 75.67 | 0 | 0.00 | 93.44 |
| response_file | 180 | 572.87 | 19.49 | 83.25 | 149.42 | 0 | 11.10 | 93.56 |
| static_file | 216 | 480.83 | 25.34 | 127.14 | 203.10 | 0 | 15.87 | 93.75 |
| compute_async | 180 | 351.21 | 43.27 | 233.00 | 420.81 | 0 | 5.27 | 93.38 |
| error_handled | 180 | 464.76 | 35.55 | 127.79 | 145.90 | 0 | 6.25 | 93.38 |
| error_unhandled | 144 | 506.90 | 24.34 | 93.18 | 172.64 | 0 | 5.65 | 93.38 |

### WebSocket
- Throughput: 7761.57 msg/s, P95: 0.62 ms, Failures: 0

## Summary

| Framework | Mean Throughput req/s | Mean P95 ms | Failure Rate % |
|---|---:|---:|---:|
| fastapi | 460.43 | 161.89 | 0.00 |

## Notes

- Compare both throughput and tail latency together; single-metric ranking is misleading.
- Error-path scenarios are intentionally included because production workloads include failures.
- Use multiple benchmark runs and median-of-runs before making final architecture decisions.