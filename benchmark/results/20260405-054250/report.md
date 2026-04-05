# Aquilia vs FastAPI vs Flask Benchmark Report

Generated at: 2026-04-05T05:46:20.896131+00:00

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
| aquilia | 0.4712 |  |
| fastapi | 0.4932 |  |
| flask | 0.2770 |  |

## Aquilia Scenario Results

| Scenario | Requests | Throughput req/s | P50 ms | P95 ms | P99 ms | Failures | Avg CPU % | Peak RSS MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| health | 1200 | 243.90 | 140.86 | 540.45 | 817.68 | 0 | 2.04 | 85.23 |
| json_simple | 1200 | 245.76 | 141.54 | 543.73 | 758.03 | 0 | 2.03 | 85.25 |
| json_large | 720 | 789.83 | 35.51 | 160.53 | 306.04 | 0 | 58.14 | 85.41 |
| di_chain | 1200 | 236.06 | 151.74 | 543.31 | 792.23 | 0 | 2.34 | 85.41 |
| middleware_stack | 1080 | 245.08 | 144.08 | 540.74 | 808.16 | 0 | 2.20 | 85.41 |
| route_static | 1080 | 238.23 | 146.49 | 549.17 | 771.87 | 0 | 2.50 | 85.41 |
| route_params | 1080 | 242.33 | 152.74 | 512.27 | 740.09 | 0 | 2.21 | 85.41 |
| route_dense | 960 | 219.70 | 153.60 | 624.51 | 884.24 | 0 | 2.70 | 46.69 |
| body_json | 960 | 296.51 | 85.07 | 366.33 | 511.01 | 0 | 3.67 | 47.19 |
| body_form | 720 | 318.88 | 62.42 | 297.29 | 505.05 | 0 | 4.49 | 47.77 |
| body_multipart | 360 | 900.60 | 10.43 | 49.80 | 102.85 | 0 | 12.85 | 67.56 |
| response_text | 1080 | 240.17 | 144.38 | 573.64 | 822.85 | 0 | 2.43 | 68.84 |
| response_stream | 360 | 481.92 | 35.98 | 129.62 | 189.53 | 0 | 10.25 | 68.92 |
| response_file | 600 | 446.75 | 43.28 | 160.93 | 232.99 | 0 | 11.81 | 72.72 |
| static_file | 720 | 359.46 | 57.70 | 256.72 | 411.27 | 0 | 10.66 | 72.92 |
| compute_async | 600 | 186.17 | 178.93 | 732.32 | 1202.77 | 0 | 3.29 | 71.86 |
| error_handled | 600 | 292.64 | 92.51 | 351.50 | 546.89 | 0 | 32.51 | 62.34 |
| error_unhandled | 480 | 254.96 | 86.21 | 379.49 | 589.05 | 0 | 47.27 | 62.06 |

### WebSocket
- Throughput: 16918.87 msg/s, P95: 0.47 ms, Failures: 0

## Fastapi Scenario Results

| Scenario | Requests | Throughput req/s | P50 ms | P95 ms | P99 ms | Failures | Avg CPU % | Peak RSS MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| health | 1200 | 240.41 | 149.06 | 518.83 | 772.10 | 0 | 4.27 | 70.75 |
| json_simple | 1200 | 236.08 | 147.34 | 561.44 | 833.89 | 0 | 4.85 | 73.38 |
| json_large | 720 | 215.40 | 119.51 | 613.80 | 875.14 | 0 | 13.56 | 82.92 |
| di_chain | 1200 | 237.65 | 153.44 | 530.60 | 808.03 | 0 | 7.92 | 95.38 |
| middleware_stack | 1080 | 238.64 | 148.38 | 559.50 | 765.09 | 0 | 4.55 | 94.61 |
| route_static | 1080 | 248.65 | 133.27 | 542.60 | 791.04 | 0 | 4.37 | 83.12 |
| route_params | 1080 | 248.19 | 142.74 | 512.96 | 765.11 | 0 | 4.84 | 79.34 |
| route_dense | 960 | 234.84 | 151.46 | 510.02 | 770.80 | 0 | 6.28 | 79.59 |
| body_json | 960 | 284.83 | 89.97 | 392.62 | 575.77 | 0 | 8.10 | 82.66 |
| body_form | 720 | 337.19 | 62.19 | 287.33 | 409.98 | 0 | 10.38 | 82.67 |
| body_multipart | 360 | 864.94 | 10.36 | 54.53 | 85.49 | 0 | 20.75 | 83.59 |
| response_text | 1080 | 200.79 | 155.14 | 710.58 | 1123.24 | 0 | 6.20 | 83.61 |
| response_stream | 360 | 340.35 | 43.22 | 188.03 | 338.90 | 0 | 30.48 | 83.44 |
| response_file | 600 | 313.35 | 60.71 | 249.50 | 350.10 | 0 | 16.80 | 84.69 |
| static_file | 720 | 257.98 | 88.76 | 344.19 | 490.34 | 0 | 17.26 | 87.12 |
| compute_async | 600 | 205.08 | 162.98 | 671.64 | 945.25 | 0 | 4.91 | 85.75 |
| error_handled | 600 | 276.95 | 102.01 | 371.86 | 480.60 | 0 | 5.63 | 85.95 |
| error_unhandled | 480 | 331.21 | 71.69 | 283.34 | 408.96 | 0 | 5.60 | 85.55 |

### WebSocket
- Throughput: 22137.65 msg/s, P95: 0.56 ms, Failures: 0

## Flask Scenario Results

| Scenario | Requests | Throughput req/s | P50 ms | P95 ms | P99 ms | Failures | Avg CPU % | Peak RSS MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| health | 1200 | 218.62 | 146.57 | 658.08 | 933.22 | 0 | 8.80 | 52.91 |
| json_simple | 1200 | 217.75 | 144.33 | 680.38 | 988.67 | 0 | 9.06 | 52.91 |
| json_large | 720 | 423.79 | 100.67 | 108.05 | 111.73 | 0 | 87.74 | 53.20 |
| di_chain | 1200 | 212.92 | 136.76 | 745.46 | 1049.66 | 0 | 9.48 | 53.20 |
| middleware_stack | 1080 | 200.34 | 150.43 | 750.81 | 1081.14 | 0 | 8.61 | 53.20 |
| route_static | 1080 | 198.87 | 160.43 | 680.87 | 1120.87 | 0 | 8.77 | 53.20 |
| route_params | 1080 | 196.20 | 158.07 | 749.98 | 1108.19 | 0 | 9.97 | 38.61 |
| route_dense | 960 | 183.45 | 176.65 | 730.85 | 1142.13 | 0 | 8.18 | 38.62 |
| body_json | 960 | 185.07 | 130.70 | 619.16 | 955.95 | 0 | 11.58 | 39.14 |
| body_form | 720 | 226.06 | 92.37 | 428.19 | 661.37 | 0 | 12.89 | 39.80 |
| body_multipart | 360 | 430.95 | 18.54 | 133.81 | 235.01 | 0 | 34.12 | 41.98 |
| response_text | 1080 | 189.71 | 152.70 | 810.70 | 1177.10 | 0 | 10.13 | 42.41 |
| response_stream | 360 | 243.30 | 82.76 | 194.44 | 205.90 | 0 | 62.86 | 42.64 |
| response_file | 600 | 202.85 | 92.68 | 386.39 | 591.97 | 0 | 16.67 | 42.45 |
| static_file | 720 | 264.55 | 92.85 | 312.90 | 461.79 | 0 | 14.82 | 42.89 |
| compute_async | 600 | 141.06 | 336.00 | 355.30 | 357.36 | 0 | 14.43 | 42.91 |
| error_handled | 600 | 242.25 | 111.56 | 424.39 | 586.08 | 0 | 9.67 | 42.91 |
| error_unhandled | 480 | 442.59 | 29.49 | 231.67 | 370.85 | 0 | 29.95 | 50.86 |

### WebSocket
- Skipped: websocket_not_supported_in_stack

## Summary

| Framework | Mean Throughput req/s | Mean P95 ms | Failure Rate % |
|---|---:|---:|---:|
| aquilia | 346.61 | 406.24 | 0.00 |
| fastapi | 295.14 | 439.08 | 0.00 |
| flask | 245.57 | 500.08 | 0.00 |

## Notes

- Compare both throughput and tail latency together; single-metric ranking is misleading.
- Error-path scenarios are intentionally included because production workloads include failures.
- Use multiple benchmark runs and median-of-runs before making final architecture decisions.