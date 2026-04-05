# Aquilia vs FastAPI vs Flask Benchmark Report

Generated at: 2026-04-05T05:48:57.379849+00:00

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
| aquilia | 0.4685 |  |
| fastapi | 0.3885 |  |
| flask | 0.2834 |  |

## Aquilia Scenario Results

| Scenario | Requests | Throughput req/s | P50 ms | P95 ms | P99 ms | Failures | Avg CPU % | Peak RSS MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| health | 360 | 389.33 | 54.07 | 207.50 | 313.81 | 0 | 3.00 | 85.16 |
| json_simple | 360 | 404.83 | 56.17 | 191.98 | 311.80 | 0 | 2.64 | 85.17 |
| json_large | 216 | 935.68 | 23.86 | 33.97 | 47.72 | 0 | 47.05 | 85.33 |
| di_chain | 360 | 383.61 | 62.49 | 221.93 | 326.43 | 0 | 2.46 | 85.33 |
| middleware_stack | 324 | 396.73 | 57.44 | 191.48 | 272.39 | 0 | 2.58 | 83.36 |
| route_static | 324 | 394.77 | 53.93 | 223.88 | 329.33 | 0 | 2.67 | 83.36 |
| route_params | 324 | 394.22 | 51.15 | 209.66 | 345.64 | 0 | 2.55 | 83.36 |
| route_dense | 288 | 393.53 | 56.86 | 192.13 | 284.90 | 0 | 2.45 | 83.36 |
| body_json | 288 | 466.53 | 29.18 | 140.81 | 228.92 | 0 | 3.23 | 83.39 |
| body_form | 216 | 480.23 | 24.06 | 130.22 | 199.45 | 0 | 3.43 | 83.39 |
| body_multipart | 108 | 880.88 | 7.16 | 21.64 | 37.20 | 0 | 0.00 | 83.48 |
| response_text | 324 | 373.33 | 56.58 | 220.30 | 351.55 | 0 | 2.42 | 84.30 |
| response_stream | 108 | 489.82 | 19.53 | 76.35 | 97.00 | 0 | 0.00 | 84.31 |
| response_file | 180 | 608.57 | 16.26 | 82.57 | 139.14 | 0 | 11.10 | 85.88 |
| static_file | 216 | 482.66 | 29.73 | 120.48 | 156.35 | 0 | 12.30 | 86.47 |
| compute_async | 180 | 357.81 | 48.06 | 269.74 | 366.50 | 0 | 2.23 | 86.50 |
| error_handled | 180 | 424.42 | 43.84 | 135.51 | 183.93 | 0 | 24.65 | 78.31 |
| error_unhandled | 144 | 522.37 | 33.52 | 67.15 | 86.21 | 0 | 43.15 | 80.20 |

### WebSocket
- Throughput: 6656.70 msg/s, P95: 0.29 ms, Failures: 0

## Fastapi Scenario Results

| Scenario | Requests | Throughput req/s | P50 ms | P95 ms | P99 ms | Failures | Avg CPU % | Peak RSS MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| health | 360 | 398.32 | 53.59 | 218.07 | 340.98 | 0 | 5.48 | 64.94 |
| json_simple | 360 | 382.91 | 50.65 | 237.36 | 360.73 | 0 | 5.64 | 66.45 |
| json_large | 216 | 390.65 | 38.86 | 209.50 | 295.29 | 0 | 15.77 | 73.36 |
| di_chain | 360 | 411.33 | 49.53 | 212.55 | 286.49 | 0 | 9.30 | 78.66 |
| middleware_stack | 324 | 419.92 | 51.22 | 189.92 | 302.60 | 0 | 5.72 | 81.17 |
| route_static | 324 | 413.04 | 52.33 | 199.74 | 309.47 | 0 | 5.15 | 83.83 |
| route_params | 324 | 377.64 | 56.36 | 215.07 | 327.66 | 0 | 5.42 | 87.06 |
| route_dense | 288 | 383.48 | 55.14 | 214.73 | 321.81 | 0 | 7.08 | 89.30 |
| body_json | 288 | 432.15 | 33.38 | 162.54 | 250.88 | 0 | 10.32 | 93.39 |
| body_form | 216 | 451.64 | 24.23 | 145.95 | 198.65 | 0 | 9.17 | 93.39 |
| body_multipart | 108 | 762.73 | 8.03 | 25.28 | 42.54 | 0 | 0.00 | 93.42 |
| response_text | 324 | 335.35 | 70.76 | 233.88 | 351.75 | 0 | 5.56 | 93.52 |
| response_stream | 108 | 524.00 | 18.93 | 71.72 | 120.97 | 0 | 0.00 | 93.53 |
| response_file | 180 | 576.59 | 18.03 | 92.96 | 145.61 | 0 | 11.40 | 93.66 |
| static_file | 216 | 478.22 | 28.85 | 127.22 | 180.16 | 0 | 16.03 | 93.77 |
| compute_async | 180 | 321.29 | 51.69 | 257.78 | 359.15 | 0 | 4.93 | 74.70 |
| error_handled | 180 | 453.69 | 33.85 | 118.19 | 233.20 | 0 | 5.00 | 75.25 |
| error_unhandled | 144 | 561.12 | 20.51 | 107.50 | 139.30 | 0 | 4.70 | 76.73 |

### WebSocket
- Throughput: 11538.74 msg/s, P95: 0.44 ms, Failures: 0

## Flask Scenario Results

| Scenario | Requests | Throughput req/s | P50 ms | P95 ms | P99 ms | Failures | Avg CPU % | Peak RSS MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| health | 360 | 388.06 | 58.97 | 185.40 | 326.51 | 0 | 8.60 | 52.17 |
| json_simple | 360 | 373.90 | 58.61 | 228.41 | 317.60 | 0 | 8.36 | 52.55 |
| json_large | 216 | 623.04 | 39.93 | 44.13 | 51.87 | 0 | 46.65 | 52.91 |
| di_chain | 360 | 398.03 | 53.30 | 213.34 | 298.99 | 0 | 9.12 | 52.91 |
| middleware_stack | 324 | 413.52 | 53.39 | 199.01 | 284.29 | 0 | 9.22 | 52.91 |
| route_static | 324 | 405.57 | 53.92 | 207.68 | 275.86 | 0 | 8.47 | 52.91 |
| route_params | 324 | 407.41 | 51.91 | 208.64 | 305.15 | 0 | 10.32 | 52.91 |
| route_dense | 288 | 412.44 | 48.95 | 200.63 | 319.22 | 0 | 9.72 | 52.91 |
| body_json | 288 | 440.87 | 34.13 | 146.73 | 244.17 | 0 | 11.50 | 52.91 |
| body_form | 216 | 512.24 | 23.09 | 112.39 | 189.22 | 0 | 9.65 | 52.92 |
| body_multipart | 108 | 890.43 | 7.47 | 22.45 | 28.17 | 0 | 0.00 | 53.00 |
| response_text | 324 | 377.65 | 56.91 | 229.93 | 381.82 | 0 | 8.76 | 53.28 |
| response_stream | 108 | 587.69 | 22.68 | 25.09 | 29.62 | 0 | 0.00 | 53.30 |
| response_file | 180 | 662.74 | 16.35 | 74.19 | 132.91 | 0 | 12.60 | 53.30 |
| static_file | 216 | 574.95 | 23.93 | 87.37 | 141.71 | 0 | 12.30 | 53.34 |
| compute_async | 180 | 141.50 | 216.85 | 237.49 | 238.77 | 0 | 9.30 | 53.34 |
| error_handled | 180 | 492.68 | 32.17 | 136.63 | 194.44 | 0 | 7.55 | 53.34 |
| error_unhandled | 144 | 1366.74 | 11.20 | 18.51 | 21.67 | 0 | 0.00 | 53.48 |

### WebSocket
- Skipped: websocket_not_supported_in_stack

## Summary

| Framework | Mean Throughput req/s | Mean P95 ms | Failure Rate % |
|---|---:|---:|---:|
| aquilia | 487.74 | 152.07 | 0.00 |
| fastapi | 448.56 | 168.89 | 0.00 |
| flask | 526.08 | 143.22 | 0.00 |

## Notes

- Compare both throughput and tail latency together; single-metric ranking is misleading.
- Error-path scenarios are intentionally included because production workloads include failures.
- Use multiple benchmark runs and median-of-runs before making final architecture decisions.