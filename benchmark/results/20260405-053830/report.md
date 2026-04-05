# Aquilia vs FastAPI vs Flask Benchmark Report

Generated at: 2026-04-05T05:41:35.536617+00:00

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
| aquilia | 0.4556 |  |
| fastapi | 0.3804 |  |
| flask | 0.2816 |  |

## Aquilia Scenario Results

| Scenario | Requests | Throughput req/s | P50 ms | P95 ms | P99 ms | Failures | Avg CPU % | Peak RSS MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| health | 1200 | 238.16 | 141.91 | 572.55 | 804.72 | 0 | 2.05 | 85.14 |
| json_simple | 1200 | 236.82 | 149.32 | 552.77 | 883.50 | 0 | 2.02 | 85.14 |
| json_large | 720 | 1123.82 | 35.44 | 46.00 | 70.43 | 0 | 73.10 | 85.30 |
| di_chain | 1200 | 243.74 | 146.75 | 530.22 | 720.88 | 0 | 2.05 | 85.30 |
| middleware_stack | 1080 | 251.30 | 134.88 | 536.19 | 758.33 | 0 | 2.14 | 85.30 |
| route_static | 1080 | 252.47 | 145.16 | 500.74 | 748.13 | 0 | 2.09 | 85.31 |
| route_params | 1080 | 250.23 | 147.30 | 492.50 | 762.22 | 0 | 2.10 | 85.31 |
| route_dense | 960 | 253.05 | 132.84 | 538.95 | 792.96 | 0 | 2.17 | 85.31 |
| body_json | 960 | 301.81 | 84.19 | 353.88 | 545.39 | 0 | 2.98 | 85.55 |
| body_form | 720 | 364.42 | 60.05 | 256.88 | 396.70 | 0 | 3.42 | 85.55 |
| body_multipart | 360 | 910.55 | 10.17 | 58.39 | 120.08 | 0 | 12.95 | 86.36 |
| response_text | 1080 | 257.15 | 132.47 | 510.32 | 806.80 | 0 | 1.96 | 87.48 |
| response_stream | 360 | 499.72 | 29.42 | 132.82 | 186.76 | 0 | 10.10 | 87.58 |
| response_file | 600 | 455.47 | 40.49 | 177.75 | 236.52 | 0 | 10.97 | 89.20 |
| static_file | 720 | 388.51 | 59.74 | 222.02 | 378.24 | 0 | 9.94 | 89.81 |
| compute_async | 600 | 243.74 | 137.22 | 577.08 | 935.20 | 0 | 2.18 | 90.05 |
| error_handled | 600 | 325.69 | 73.19 | 341.24 | 509.10 | 0 | 30.94 | 94.48 |
| error_unhandled | 480 | 363.12 | 66.10 | 228.81 | 405.85 | 0 | 49.16 | 94.64 |

### WebSocket
- Throughput: 15351.13 msg/s, P95: 0.57 ms, Failures: 0

## Fastapi Scenario Results

| Scenario | Requests | Throughput req/s | P50 ms | P95 ms | P99 ms | Failures | Avg CPU % | Peak RSS MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| health | 1200 | 237.84 | 145.49 | 535.81 | 766.03 | 0 | 4.05 | 69.12 |
| json_simple | 1200 | 236.59 | 148.64 | 557.49 | 842.99 | 0 | 4.02 | 78.20 |
| json_large | 720 | 236.23 | 119.42 | 568.11 | 782.01 | 0 | 12.61 | 91.88 |
| di_chain | 1200 | 242.64 | 147.57 | 532.90 | 796.70 | 0 | 7.02 | 99.25 |
| middleware_stack | 1080 | 236.01 | 142.48 | 563.67 | 837.53 | 0 | 4.16 | 99.30 |
| route_static | 1080 | 252.80 | 131.57 | 540.39 | 744.44 | 0 | 4.08 | 94.80 |
| route_params | 1080 | 245.79 | 138.54 | 515.60 | 868.68 | 0 | 4.42 | 93.80 |
| route_dense | 960 | 227.27 | 148.41 | 606.95 | 810.03 | 0 | 5.93 | 93.81 |
| body_json | 960 | 282.99 | 87.19 | 397.75 | 663.70 | 0 | 6.39 | 92.55 |
| body_form | 720 | 336.81 | 67.94 | 271.48 | 384.96 | 0 | 8.71 | 93.09 |
| body_multipart | 360 | 937.25 | 10.43 | 50.79 | 78.99 | 0 | 21.10 | 93.64 |
| response_text | 1080 | 241.93 | 144.68 | 534.45 | 785.73 | 0 | 4.19 | 91.11 |
| response_stream | 360 | 404.77 | 39.02 | 171.60 | 261.72 | 0 | 25.18 | 88.23 |
| response_file | 600 | 425.48 | 41.18 | 184.66 | 289.04 | 0 | 14.29 | 88.23 |
| static_file | 720 | 353.61 | 67.76 | 252.94 | 389.73 | 0 | 15.23 | 88.50 |
| compute_async | 600 | 211.52 | 158.95 | 619.52 | 1009.46 | 0 | 4.71 | 87.70 |
| error_handled | 600 | 326.56 | 82.81 | 307.24 | 484.06 | 0 | 4.71 | 82.86 |
| error_unhandled | 480 | 820.92 | 32.64 | 44.80 | 50.56 | 193 | 46.15 | 83.78 |

### WebSocket
- Throughput: 25800.12 msg/s, P95: 0.52 ms, Failures: 0

## Flask Scenario Results

| Scenario | Requests | Throughput req/s | P50 ms | P95 ms | P99 ms | Failures | Avg CPU % | Peak RSS MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| health | 1200 | 242.39 | 151.90 | 528.32 | 804.36 | 0 | 6.83 | 52.97 |
| json_simple | 1200 | 244.51 | 148.67 | 524.59 | 763.05 | 0 | 7.01 | 52.97 |
| json_large | 720 | 699.02 | 59.67 | 62.65 | 63.57 | 0 | 81.90 | 53.23 |
| di_chain | 1200 | 241.55 | 145.02 | 540.27 | 841.07 | 0 | 6.93 | 53.23 |
| middleware_stack | 1080 | 241.64 | 149.54 | 520.25 | 756.43 | 0 | 7.10 | 53.23 |
| route_static | 1080 | 251.55 | 140.07 | 505.91 | 778.99 | 0 | 7.01 | 53.25 |
| route_params | 1080 | 250.59 | 140.04 | 500.93 | 732.37 | 0 | 7.26 | 53.25 |
| route_dense | 960 | 249.03 | 140.35 | 526.40 | 833.46 | 0 | 7.08 | 53.25 |
| body_json | 960 | 301.76 | 87.05 | 350.79 | 517.12 | 0 | 9.10 | 53.25 |
| body_form | 720 | 338.69 | 65.77 | 287.97 | 412.97 | 0 | 10.21 | 53.27 |
| body_multipart | 360 | 726.06 | 10.69 | 71.88 | 186.36 | 0 | 26.40 | 54.00 |
| response_text | 1080 | 245.42 | 144.14 | 547.45 | 776.97 | 0 | 6.79 | 54.98 |
| response_stream | 360 | 681.39 | 33.29 | 35.24 | 37.87 | 0 | 49.57 | 55.62 |
| response_file | 600 | 456.36 | 41.13 | 166.83 | 261.35 | 0 | 13.50 | 56.31 |
| static_file | 720 | 378.19 | 64.47 | 228.17 | 332.19 | 0 | 12.74 | 57.27 |
| compute_async | 600 | 146.55 | 322.78 | 327.37 | 334.01 | 0 | 10.32 | 58.03 |
| error_handled | 600 | 331.11 | 81.34 | 310.74 | 420.95 | 0 | 8.88 | 54.42 |
| error_unhandled | 480 | 355.22 | 63.23 | 251.34 | 337.99 | 0 | 19.16 | 56.22 |

### WebSocket
- Skipped: websocket_not_supported_in_stack

## Summary

| Framework | Mean Throughput req/s | Mean P95 ms | Failure Rate % |
|---|---:|---:|---:|
| aquilia | 386.65 | 368.28 | 0.00 |
| fastapi | 347.61 | 403.12 | 1.29 |
| flask | 354.50 | 349.28 | 0.00 |

## Notes

- Compare both throughput and tail latency together; single-metric ranking is misleading.
- Error-path scenarios are intentionally included because production workloads include failures.
- Use multiple benchmark runs and median-of-runs before making final architecture decisions.