# Aquilia vs FastAPI vs Flask Benchmark Report

Generated at: 2026-04-05T05:35:00.740839+00:00

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
| aquilia | 0.3489 |  |
| fastapi | 0.3336 |  |
| flask | 0.1745 |  |

## Aquilia Scenario Results

| Scenario | Requests | Throughput req/s | P50 ms | P95 ms | P99 ms | Failures | Avg CPU % | Peak RSS MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| health | 360 | 1801.10 | 15.93 | 20.00 | 20.57 | 0 | 0.00 | 84.75 |
| json_simple | 360 | 618.55 | 33.51 | 150.73 | 200.66 | 0 | 3.57 | 84.89 |
| json_large | 216 | 954.92 | 25.52 | 28.21 | 32.01 | 0 | 47.65 | 85.09 |
| di_chain | 360 | 1765.51 | 15.98 | 18.27 | 21.54 | 0 | 0.00 | 85.09 |
| middleware_stack | 324 | 1689.95 | 16.14 | 19.64 | 22.55 | 0 | 0.00 | 85.09 |
| route_static | 324 | 591.67 | 35.80 | 135.09 | 207.05 | 0 | 3.10 | 85.09 |
| route_params | 324 | 603.76 | 31.45 | 133.15 | 222.42 | 0 | 3.03 | 85.11 |
| route_dense | 288 | 647.23 | 30.99 | 136.76 | 194.01 | 0 | 3.20 | 85.11 |
| body_json | 288 | 530.01 | 26.95 | 126.82 | 182.30 | 0 | 4.67 | 85.25 |
| body_form | 216 | 589.68 | 21.39 | 108.99 | 160.49 | 0 | 3.50 | 85.25 |
| body_multipart | 108 | 1023.88 | 5.89 | 18.47 | 32.62 | 0 | 0.00 | 85.34 |
| response_text | 324 | 1717.82 | 16.09 | 19.37 | 22.70 | 0 | 0.00 | 85.95 |
| response_stream | 108 | 653.67 | 14.00 | 61.52 | 75.29 | 0 | 0.00 | 86.00 |
| response_file | 180 | 560.67 | 25.56 | 81.29 | 107.63 | 0 | 12.15 | 87.25 |
| static_file | 216 | 566.25 | 22.23 | 109.01 | 152.09 | 0 | 9.90 | 87.59 |
| compute_async | 180 | 585.08 | 27.47 | 114.63 | 166.94 | 0 | 3.15 | 87.64 |
| error_handled | 180 | 546.49 | 36.29 | 104.66 | 140.24 | 0 | 31.00 | 89.81 |
| error_unhandled | 144 | 522.91 | 29.20 | 80.89 | 117.39 | 0 | 43.65 | 91.53 |

### WebSocket
- Throughput: 7301.50 msg/s, P95: 0.52 ms, Failures: 0

## Fastapi Scenario Results

| Scenario | Requests | Throughput req/s | P50 ms | P95 ms | P99 ms | Failures | Avg CPU % | Peak RSS MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| health | 360 | 658.00 | 30.86 | 118.21 | 172.81 | 0 | 6.97 | 64.80 |
| json_simple | 360 | 682.63 | 26.33 | 128.59 | 175.47 | 0 | 7.57 | 66.09 |
| json_large | 216 | 507.14 | 36.05 | 133.75 | 204.75 | 0 | 20.07 | 73.33 |
| di_chain | 360 | 565.98 | 34.91 | 148.59 | 218.02 | 0 | 11.50 | 78.77 |
| middleware_stack | 324 | 602.20 | 34.95 | 130.88 | 205.51 | 0 | 5.97 | 81.05 |
| route_static | 324 | 614.39 | 31.25 | 134.55 | 215.78 | 0 | 6.43 | 83.81 |
| route_params | 324 | 653.23 | 29.91 | 124.41 | 190.09 | 0 | 7.37 | 86.84 |
| route_dense | 288 | 658.42 | 30.36 | 127.74 | 201.40 | 0 | 9.47 | 89.64 |
| body_json | 288 | 574.77 | 25.29 | 120.89 | 162.46 | 0 | 10.80 | 92.78 |
| body_form | 216 | 611.60 | 18.94 | 94.97 | 150.44 | 0 | 8.35 | 92.80 |
| body_multipart | 108 | 835.54 | 7.38 | 23.91 | 27.77 | 0 | 0.00 | 92.83 |
| response_text | 324 | 672.73 | 27.65 | 119.68 | 165.26 | 0 | 6.43 | 92.92 |
| response_stream | 108 | 573.31 | 19.09 | 61.32 | 82.75 | 0 | 0.00 | 92.94 |
| response_file | 180 | 515.14 | 22.02 | 93.88 | 184.15 | 0 | 12.40 | 93.06 |
| static_file | 216 | 619.65 | 23.73 | 88.84 | 154.20 | 0 | 15.50 | 93.41 |
| compute_async | 180 | 544.73 | 28.66 | 150.37 | 237.72 | 0 | 5.95 | 93.42 |
| error_handled | 180 | 660.33 | 23.30 | 89.07 | 116.35 | 0 | 6.05 | 93.42 |
| error_unhandled | 144 | 743.58 | 23.27 | 38.02 | 40.11 | 4 | 0.00 | 93.77 |

### WebSocket
- Throughput: 20359.98 msg/s, P95: 0.21 ms, Failures: 0

## Flask Scenario Results

| Scenario | Requests | Throughput req/s | P50 ms | P95 ms | P99 ms | Failures | Avg CPU % | Peak RSS MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| health | 360 | 1636.44 | 17.21 | 19.21 | 22.66 | 0 | 21.50 | 52.38 |
| json_simple | 360 | 1669.71 | 17.80 | 19.40 | 21.35 | 0 | 22.70 | 52.64 |
| json_large | 216 | 523.37 | 41.82 | 98.13 | 99.65 | 0 | 47.20 | 52.92 |
| di_chain | 360 | 1672.98 | 17.23 | 18.82 | 22.23 | 0 | 22.10 | 52.92 |
| middleware_stack | 324 | 1598.68 | 17.43 | 21.01 | 24.62 | 0 | 0.00 | 52.92 |
| route_static | 324 | 1606.33 | 17.40 | 20.54 | 23.87 | 0 | 0.00 | 52.92 |
| route_params | 324 | 1649.48 | 17.27 | 19.85 | 23.27 | 0 | 0.00 | 52.92 |
| route_dense | 288 | 1611.89 | 17.00 | 21.28 | 23.49 | 0 | 0.00 | 52.92 |
| body_json | 288 | 1496.16 | 14.74 | 16.85 | 19.31 | 0 | 0.00 | 52.94 |
| body_form | 216 | 565.76 | 16.97 | 111.06 | 176.06 | 0 | 10.10 | 53.38 |
| body_multipart | 108 | 875.70 | 7.78 | 26.29 | 38.67 | 0 | 0.00 | 53.53 |
| response_text | 324 | 1632.32 | 16.92 | 19.59 | 22.91 | 0 | 0.00 | 53.98 |
| response_stream | 108 | 608.96 | 22.26 | 24.68 | 29.65 | 0 | 0.00 | 54.41 |
| response_file | 180 | 621.38 | 15.35 | 74.94 | 125.52 | 0 | 11.25 | 54.70 |
| static_file | 216 | 624.66 | 21.50 | 97.84 | 153.13 | 0 | 12.90 | 55.12 |
| compute_async | 180 | 144.27 | 214.28 | 222.97 | 223.46 | 0 | 9.37 | 55.59 |
| error_handled | 180 | 663.90 | 21.32 | 81.52 | 124.73 | 0 | 10.00 | 55.59 |
| error_unhandled | 144 | 1128.11 | 13.11 | 34.32 | 36.03 | 0 | 0.00 | 56.05 |

### WebSocket
- Skipped: websocket_not_supported_in_stack

## Summary

| Framework | Mean Throughput req/s | Mean P95 ms | Failure Rate % |
|---|---:|---:|---:|
| aquilia | 887.17 | 81.53 | 0.00 |
| fastapi | 627.41 | 107.09 | 0.09 |
| flask | 1129.45 | 52.68 | 0.00 |

## Notes

- Compare both throughput and tail latency together; single-metric ranking is misleading.
- Error-path scenarios are intentionally included because production workloads include failures.
- Use multiple benchmark runs and median-of-runs before making final architecture decisions.