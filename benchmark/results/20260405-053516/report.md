# Aquilia vs FastAPI vs Flask Benchmark Report

Generated at: 2026-04-05T05:36:29.020046+00:00

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
| aquilia | 0.4100 |  |
| fastapi | 2.6513 |  |
| flask | 0.2288 |  |

## Aquilia Scenario Results

| Scenario | Requests | Throughput req/s | P50 ms | P95 ms | P99 ms | Failures | Avg CPU % | Peak RSS MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| health | 1800 | 1904.37 | 32.94 | 36.19 | 36.94 | 0 | 11.48 | 85.27 |
| json_simple | 1800 | 1938.26 | 31.91 | 34.92 | 39.99 | 0 | 11.18 | 85.27 |
| json_large | 1080 | 1049.22 | 52.77 | 57.81 | 60.33 | 0 | 79.90 | 85.44 |
| di_chain | 1800 | 1975.26 | 31.75 | 33.69 | 35.09 | 0 | 10.64 | 85.44 |
| middleware_stack | 1620 | 1907.74 | 32.23 | 35.43 | 39.06 | 0 | 10.48 | 85.44 |
| route_static | 1620 | 1938.53 | 31.85 | 34.15 | 37.11 | 0 | 10.05 | 85.44 |
| route_params | 1620 | 1890.51 | 33.23 | 34.89 | 36.01 | 0 | 11.24 | 85.44 |
| route_dense | 1440 | 1925.62 | 32.40 | 34.46 | 35.95 | 0 | 10.40 | 85.44 |
| body_json | 1440 | 1830.23 | 26.56 | 28.65 | 34.23 | 0 | 10.47 | 85.75 |
| body_form | 1080 | 523.54 | 54.77 | 249.69 | 370.20 | 0 | 5.28 | 85.75 |
| body_multipart | 540 | 586.69 | 16.39 | 130.44 | 282.68 | 0 | 14.90 | 83.70 |
| response_text | 1620 | 1257.72 | 37.38 | 45.45 | 49.64 | 405 | 8.66 | 84.41 |
| response_stream | 540 | 0.00 | 16.89 | 22.16 | 22.67 | 540 | 0.05 | 84.41 |
| response_file | 900 | 0.00 | 19.47 | 23.96 | 24.32 | 900 | 0.03 | 84.41 |
| static_file | 1080 | 0.00 | 23.04 | 28.74 | 30.24 | 1080 | 0.03 | 84.38 |
| compute_async | 900 | 0.00 | 36.24 | 42.67 | 46.61 | 900 | 0.03 | 84.38 |
| error_handled | 900 | 0.00 | 30.09 | 34.27 | 35.71 | 900 | 0.00 | 84.38 |
| error_unhandled | 720 | 0.00 | 21.79 | 26.15 | 26.65 | 720 | 0.05 | 84.38 |

### WebSocket
- Throughput: 0.00 msg/s, P95: n/a ms, Failures: 1280

## Fastapi Scenario Results

| Scenario | Requests | Throughput req/s | P50 ms | P95 ms | P99 ms | Failures | Avg CPU % | Peak RSS MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| health | 1800 | 0.98 | 34.12 | 46.04 | 68.17 | 1799 | 0.10 | 63.28 |
| json_simple | 1800 | 0.00 | 31.23 | 39.12 | 43.98 | 1800 | 0.02 | 63.28 |
| json_large | 1080 | 0.00 | 28.78 | 34.37 | 35.35 | 1080 | 0.03 | 63.28 |
| di_chain | 1800 | 0.00 | 33.21 | 40.70 | 136.39 | 1800 | 0.06 | 63.28 |
| middleware_stack | 1620 | 0.00 | 31.77 | 36.25 | 37.73 | 1620 | 0.03 | 63.28 |
| route_static | 1620 | 144.82 | 31.90 | 40.76 | 57.77 | 1499 | 2.52 | 65.92 |
| route_params | 1620 | 0.00 | 29.09 | 30.98 | 34.20 | 1620 | 0.03 | 65.92 |
| route_dense | 1440 | 990.48 | 34.20 | 209.22 | 374.63 | 0 | 17.44 | 73.83 |
| body_json | 1440 | 530.32 | 65.71 | 264.46 | 392.65 | 0 | 11.59 | 81.14 |
| body_form | 1080 | 567.88 | 51.69 | 216.15 | 323.97 | 0 | 12.91 | 84.80 |
| body_multipart | 540 | 741.06 | 14.21 | 116.30 | 216.94 | 0 | 24.38 | 85.12 |
| response_text | 1620 | 597.53 | 74.28 | 302.82 | 421.40 | 0 | 7.97 | 85.12 |
| response_stream | 540 | 548.48 | 38.48 | 149.82 | 219.20 | 0 | 30.56 | 86.73 |
| response_file | 900 | 683.68 | 34.44 | 161.29 | 224.04 | 0 | 19.50 | 92.59 |
| static_file | 1080 | 614.22 | 46.00 | 194.58 | 265.39 | 0 | 24.13 | 94.31 |
| compute_async | 900 | 1703.15 | 33.49 | 45.40 | 59.74 | 0 | 16.00 | 94.34 |
| error_handled | 900 | 1936.10 | 25.31 | 27.10 | 27.88 | 0 | 16.57 | 94.34 |
| error_unhandled | 720 | 883.62 | 47.73 | 53.94 | 58.16 | 0 | 78.38 | 94.70 |

### WebSocket
- Throughput: 20120.55 msg/s, P95: 0.89 ms, Failures: 0

## Flask Scenario Results

| Scenario | Requests | Throughput req/s | P50 ms | P95 ms | P99 ms | Failures | Avg CPU % | Peak RSS MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| health | 1800 | 1758.65 | 35.17 | 38.99 | 41.13 | 0 | 32.00 | 52.80 |
| json_simple | 1800 | 1802.16 | 34.80 | 36.56 | 36.81 | 0 | 32.86 | 52.81 |
| json_large | 1080 | 685.71 | 81.35 | 84.36 | 85.50 | 0 | 86.46 | 53.55 |
| di_chain | 1800 | 1777.65 | 34.70 | 38.02 | 42.56 | 0 | 33.30 | 53.55 |
| middleware_stack | 1620 | 1768.07 | 35.06 | 39.38 | 41.74 | 0 | 33.72 | 53.56 |
| route_static | 1620 | 1767.70 | 34.85 | 39.97 | 40.85 | 0 | 32.62 | 53.56 |
| route_params | 1620 | 1715.47 | 35.19 | 38.45 | 46.64 | 43 | 33.84 | 53.56 |
| route_dense | 1440 | 18.92 | 30.81 | 35.28 | 35.44 | 1426 | 0.42 | 53.56 |
| body_json | 1440 | 1090.07 | 28.75 | 31.78 | 63.58 | 547 | 28.60 | 53.56 |
| body_form | 1080 | 0.00 | 21.07 | 24.24 | 26.56 | 1080 | 0.00 | 53.56 |
| body_multipart | 540 | 238.46 | 12.07 | 18.06 | 26.41 | 462 | 10.40 | 54.11 |
| response_text | 1620 | 0.00 | 29.79 | 33.55 | 35.37 | 1620 | 0.00 | 54.11 |
| response_stream | 540 | 0.00 | 15.13 | 18.40 | 19.15 | 540 | 0.00 | 54.11 |
| response_file | 900 | 6.87 | 17.81 | 19.13 | 19.29 | 897 | 0.27 | 54.11 |
| static_file | 1080 | 34.27 | 19.66 | 20.74 | 60.10 | 1063 | 0.97 | 54.14 |
| compute_async | 900 | 0.00 | 29.81 | 34.24 | 34.86 | 900 | 0.03 | 54.14 |
| error_handled | 900 | 0.00 | 24.43 | 29.13 | 30.07 | 900 | 0.00 | 54.14 |
| error_unhandled | 720 | 355.41 | 20.02 | 26.55 | 33.22 | 586 | 0.05 | 54.14 |

### WebSocket
- Skipped: websocket_not_supported_in_stack

## Summary

| Framework | Mean Throughput req/s | Mean P95 ms | Failure Rate % |
|---|---:|---:|---:|
| aquilia | 1040.43 | 51.87 | 24.20 |
| fastapi | 552.35 | 111.63 | 49.86 |
| flask | 723.30 | 33.71 | 44.73 |

## Notes

- Compare both throughput and tail latency together; single-metric ranking is misleading.
- Error-path scenarios are intentionally included because production workloads include failures.
- Use multiple benchmark runs and median-of-runs before making final architecture decisions.