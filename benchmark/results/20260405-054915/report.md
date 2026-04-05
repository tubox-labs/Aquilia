# Aquilia vs FastAPI vs Flask Benchmark Report

Generated at: 2026-04-05T05:53:17.967494+00:00

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
| aquilia | 0.4787 |  |
| fastapi | 0.3744 |  |
| flask | 0.4457 |  |

## Aquilia Scenario Results

| Scenario | Requests | Throughput req/s | P50 ms | P95 ms | P99 ms | Failures | Avg CPU % | Peak RSS MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| health | 1200 | 242.66 | 150.15 | 528.71 | 782.34 | 0 | 2.15 | 85.06 |
| json_simple | 1200 | 242.16 | 140.33 | 527.86 | 868.44 | 0 | 2.05 | 76.30 |
| json_large | 720 | 361.02 | 42.17 | 435.86 | 738.22 | 0 | 30.09 | 77.56 |
| di_chain | 1200 | 243.50 | 141.32 | 568.10 | 862.20 | 0 | 2.13 | 77.56 |
| middleware_stack | 1080 | 251.98 | 135.50 | 503.49 | 740.71 | 0 | 2.17 | 64.70 |
| route_static | 1080 | 250.80 | 137.08 | 510.34 | 820.84 | 0 | 2.22 | 64.73 |
| route_params | 1080 | 249.51 | 139.98 | 515.91 | 772.56 | 0 | 2.21 | 64.89 |
| route_dense | 960 | 256.43 | 141.76 | 514.16 | 757.01 | 0 | 2.13 | 64.94 |
| body_json | 960 | 315.50 | 83.41 | 348.81 | 474.79 | 0 | 3.03 | 64.39 |
| body_form | 720 | 367.18 | 56.16 | 261.86 | 388.95 | 0 | 3.53 | 64.61 |
| body_multipart | 360 | 878.15 | 10.29 | 64.61 | 106.70 | 0 | 13.25 | 78.77 |
| response_text | 1080 | 256.88 | 131.92 | 516.96 | 782.53 | 0 | 2.09 | 79.92 |
| response_stream | 360 | 473.10 | 31.41 | 144.74 | 227.74 | 0 | 10.05 | 79.94 |
| response_file | 600 | 465.54 | 41.55 | 173.26 | 253.97 | 0 | 11.34 | 82.88 |
| static_file | 720 | 391.92 | 61.97 | 233.62 | 336.85 | 0 | 10.07 | 83.62 |
| compute_async | 600 | 245.03 | 141.75 | 527.99 | 874.20 | 0 | 2.39 | 83.86 |
| error_handled | 600 | 332.67 | 78.00 | 305.10 | 405.91 | 0 | 32.48 | 88.83 |
| error_unhandled | 480 | 616.71 | 51.34 | 58.37 | 62.33 | 0 | 73.20 | 88.88 |

### WebSocket
- Throughput: 17387.71 msg/s, P95: 0.61 ms, Failures: 0

## Fastapi Scenario Results

| Scenario | Requests | Throughput req/s | P50 ms | P95 ms | P99 ms | Failures | Avg CPU % | Peak RSS MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| health | 1200 | 240.30 | 141.15 | 537.37 | 836.93 | 0 | 4.72 | 69.98 |
| json_simple | 1200 | 256.63 | 134.02 | 508.70 | 746.25 | 0 | 4.18 | 79.12 |
| json_large | 720 | 245.68 | 103.66 | 527.37 | 669.24 | 0 | 12.82 | 92.56 |
| di_chain | 1200 | 251.83 | 141.03 | 511.59 | 741.64 | 0 | 7.14 | 98.67 |
| middleware_stack | 1080 | 255.73 | 132.33 | 507.29 | 796.17 | 0 | 4.19 | 98.67 |
| route_static | 1080 | 256.99 | 142.64 | 503.49 | 772.37 | 0 | 4.20 | 98.67 |
| route_params | 1080 | 222.36 | 154.84 | 585.36 | 874.49 | 0 | 4.62 | 98.67 |
| route_dense | 960 | 185.73 | 156.65 | 851.27 | 1315.99 | 0 | 6.99 | 92.73 |
| body_json | 960 | 280.31 | 89.75 | 384.43 | 529.27 | 0 | 7.51 | 84.66 |
| body_form | 720 | 343.85 | 61.14 | 270.57 | 417.01 | 0 | 10.61 | 84.69 |
| body_multipart | 360 | 867.47 | 10.65 | 54.45 | 105.59 | 0 | 23.05 | 85.31 |
| response_text | 1080 | 208.51 | 155.22 | 670.22 | 1039.84 | 0 | 5.41 | 85.31 |
| response_stream | 360 | 319.12 | 52.16 | 173.43 | 299.10 | 0 | 31.53 | 85.33 |
| response_file | 600 | 328.34 | 60.72 | 236.57 | 346.56 | 0 | 14.19 | 86.64 |
| static_file | 720 | 298.82 | 69.12 | 291.74 | 484.56 | 0 | 17.99 | 87.86 |
| compute_async | 600 | 126.08 | 275.14 | 1072.87 | 1452.00 | 0 | 8.43 | 88.30 |
| error_handled | 600 | 162.09 | 166.86 | 634.28 | 975.21 | 0 | 8.48 | 86.02 |
| error_unhandled | 480 | 216.88 | 104.64 | 418.54 | 542.24 | 0 | 9.00 | 86.03 |

### WebSocket
- Throughput: 15326.73 msg/s, P95: 0.98 ms, Failures: 0

## Flask Scenario Results

| Scenario | Requests | Throughput req/s | P50 ms | P95 ms | P99 ms | Failures | Avg CPU % | Peak RSS MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| health | 1200 | 181.94 | 171.87 | 780.40 | 1274.89 | 0 | 13.70 | 52.88 |
| json_simple | 1200 | 172.24 | 173.43 | 863.71 | 1427.87 | 0 | 16.20 | 52.91 |
| json_large | 720 | 200.13 | 196.09 | 257.47 | 286.31 | 0 | 87.02 | 53.17 |
| di_chain | 1200 | 172.69 | 166.01 | 905.08 | 1399.48 | 0 | 15.35 | 53.17 |
| middleware_stack | 1080 | 139.83 | 230.38 | 1014.84 | 1681.73 | 0 | 16.13 | 53.17 |
| route_static | 1080 | 150.06 | 163.48 | 1186.55 | 1884.01 | 0 | 16.55 | 53.17 |
| route_params | 1080 | 161.28 | 176.15 | 956.83 | 1519.51 | 0 | 14.89 | 53.17 |
| route_dense | 960 | 130.21 | 254.06 | 1074.72 | 1537.92 | 0 | 15.45 | 53.17 |
| body_json | 960 | 137.70 | 158.95 | 873.52 | 1376.27 | 0 | 19.31 | 53.17 |
| body_form | 720 | 118.99 | 164.96 | 861.48 | 1327.82 | 0 | 17.62 | 53.19 |
| body_multipart | 360 | 232.77 | 33.64 | 236.57 | 449.43 | 0 | 41.16 | 44.83 |
| response_text | 1080 | 144.17 | 179.09 | 1148.91 | 1949.84 | 0 | 16.61 | 49.78 |
| response_stream | 360 | 157.31 | 134.02 | 318.33 | 355.83 | 0 | 67.64 | 50.58 |
| response_file | 600 | 130.12 | 149.23 | 567.81 | 918.17 | 0 | 20.93 | 51.22 |
| static_file | 720 | 134.23 | 148.01 | 770.12 | 1283.98 | 0 | 20.08 | 52.12 |
| compute_async | 600 | 140.64 | 333.84 | 346.99 | 348.60 | 0 | 14.81 | 53.14 |
| error_handled | 600 | 134.95 | 188.58 | 800.15 | 1053.90 | 0 | 12.69 | 53.56 |
| error_unhandled | 480 | 189.54 | 107.60 | 468.91 | 689.35 | 0 | 28.37 | 57.75 |

### WebSocket
- Skipped: websocket_not_supported_in_stack

## Summary

| Framework | Mean Throughput req/s | Mean P95 ms | Failure Rate % |
|---|---:|---:|---:|
| aquilia | 357.82 | 374.43 | 0.00 |
| fastapi | 281.49 | 485.53 | 0.00 |
| flask | 157.15 | 746.24 | 0.00 |

## Notes

- Compare both throughput and tail latency together; single-metric ranking is misleading.
- Error-path scenarios are intentionally included because production workloads include failures.
- Use multiple benchmark runs and median-of-runs before making final architecture decisions.