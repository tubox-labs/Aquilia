# Aquilia Professional Web Framework Benchmarks

This document presents the objective, reproducible, and statistically valid benchmarks comparing the performance characteristics of Aquilia against major Python web frameworks.

## Benchmark Parameters
- **Load Testing Utility**: `oha` (Rust-based HTTP/1.1 load generator)
- **Concurrency Level**: `50` simultaneous connections
- **Duration**: `5s` per endpoint run
- **Server Environment**: Python 3.13.14 (CPython) — Darwin arm64 — Uvicorn, single worker — JSON backend: `aquilia._json` — `_core` present — `_dataengine` present — `_json` present
- **Database Engine**: SQLite 3 (Standard 10,000-row TechEmpower Schema)
- **Success Rate**: fraction of responses with a 2xx/3xx status. Endpoints failing a single-request preflight are reported as 0 and excluded from ranking.

## 1. Cold Startup & Importing Overhead
Measures the pure framework importing and initialization time. Fast cold start times are critical for Serverless deployments and developer container boot-ups.

| Rank | Framework | Mean Startup (ms) | StdDev (ms) | Min (ms) | Max (ms) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Starlette | 160.41ms | ±1.95ms | 157.94ms | 163.16ms |
| 2 | Django | 207.52ms | ±4.57ms | 200.76ms | 211.78ms |
| 3 | Flask | 208.19ms | ±4.05ms | 204.55ms | 216.11ms |
| 4 | Aquilia | 213.76ms | ±1.90ms | 211.21ms | 216.31ms |
| 5 | Falcon | 223.51ms | ±5.38ms | 217.21ms | 237.26ms |
| 6 | Sanic | 233.23ms | ±7.88ms | 223.94ms | 246.44ms |
| 7 | Quart | 245.03ms | ±3.62ms | 238.95ms | 250.57ms |
| 8 | FastAPI | 289.82ms | ±5.00ms | 281.14ms | 298.90ms |
| 9 | Litestar | 592.07ms | ±79.34ms | 526.07ms | 736.88ms |

## 2. HTTP Throughput and Latency Results
The tables below highlight framework performance metrics across various workload scenarios.

### Scenario: `plaintext`
GET `/plaintext` returning 'Hello, World!' (Measures raw HTTP parsing and serialization throughput).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 77214.38 req/s | 0.65 ms | 0.71 ms | 0.80 ms | 100.0% |
| 2 | Starlette | 70225.71 req/s | 0.71 ms | 0.74 ms | 0.85 ms | 100.0% |
| 3 | Litestar | 47446.60 req/s | 1.05 ms | 1.04 ms | 1.11 ms | 100.0% |
| 4 | Aquilia | 43243.17 req/s | 1.15 ms | 1.15 ms | 1.22 ms | 100.0% |
| 5 | FastAPI | 38856.05 req/s | 1.29 ms | 1.28 ms | 1.34 ms | 100.0% |
| 6 | Sanic | 38752.53 req/s | 1.29 ms | 1.18 ms | 2.45 ms | 100.0% |
| 7 | Quart | 19697.60 req/s | 2.54 ms | 2.46 ms | 2.68 ms | 100.0% |
| 8 | Django | 4192.29 req/s | 11.93 ms | 11.63 ms | 12.69 ms | 100.0% |
| 9 | Flask | 2182.76 req/s | 22.90 ms | 30.73 ms | 46.19 ms | 59.0% |

### Scenario: `json`
GET `/json` returning a small JSON dictionary. (Measures JSON encoding overhead).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 66609.62 req/s | 0.75 ms | 0.76 ms | 0.87 ms | 100.0% |
| 2 | Starlette | 62609.09 req/s | 0.80 ms | 0.79 ms | 0.83 ms | 100.0% |
| 3 | Litestar | 46666.53 req/s | 1.07 ms | 1.06 ms | 1.13 ms | 100.0% |
| 4 | Aquilia | 42993.21 req/s | 1.16 ms | 1.15 ms | 1.22 ms | 100.0% |
| 5 | Sanic | 38218.61 req/s | 1.31 ms | 1.20 ms | 2.54 ms | 100.0% |
| 6 | FastAPI | 34586.58 req/s | 1.44 ms | 1.44 ms | 1.50 ms | 100.0% |
| 7 | Quart | 18447.11 req/s | 2.71 ms | 2.63 ms | 2.86 ms | 100.0% |
| 8 | Django | 4171.54 req/s | 11.99 ms | 11.77 ms | 12.55 ms | 100.0% |
| 9 | Flask | 2697.80 req/s | 18.53 ms | 23.08 ms | 36.08 ms | 67.2% |

### Scenario: `json_large`
GET `/json/large` returning a nested 100KB JSON payload. (Measures large serialization performance).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Litestar | 6864.71 req/s | 7.28 ms | 7.11 ms | 7.32 ms | 100.0% |
| 2 | Aquilia | 4613.83 req/s | 10.84 ms | 10.54 ms | 10.98 ms | 100.0% |
| 3 | Sanic | 2179.16 req/s | 22.98 ms | 22.21 ms | 24.38 ms | 100.0% |
| 4 | Falcon | 1612.96 req/s | 31.07 ms | 30.17 ms | 32.07 ms | 100.0% |
| 5 | Starlette | 1609.06 req/s | 31.15 ms | 30.11 ms | 31.67 ms | 100.0% |
| 6 | Quart | 1246.74 req/s | 40.25 ms | 40.27 ms | 40.92 ms | 100.0% |
| 7 | Django | 1201.31 req/s | 41.74 ms | 41.23 ms | 44.41 ms | 100.0% |
| 8 | Flask | 1009.45 req/s | 49.61 ms | 47.69 ms | 72.48 ms | 92.8% |
| 9 | FastAPI | 201.09 req/s | 224.75 ms | 166.34 ms | 291.48 ms | 100.0% |

### Scenario: `db_single`
GET `/db` executing 1 SQL query. (Measures single database retrieval latency).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Aquilia | 23929.71 req/s | 2.09 ms | 2.07 ms | 2.18 ms | 100.0% |
| 2 | Falcon | 6343.64 req/s | 7.88 ms | 7.76 ms | 9.52 ms | 100.0% |
| 3 | Starlette | 6301.62 req/s | 7.94 ms | 7.82 ms | 9.49 ms | 100.0% |
| 4 | Litestar | 5991.84 req/s | 8.34 ms | 8.23 ms | 10.01 ms | 100.0% |
| 5 | Sanic | 5650.21 req/s | 8.85 ms | 8.57 ms | 11.26 ms | 100.0% |
| 6 | FastAPI | 5567.03 req/s | 8.98 ms | 8.86 ms | 10.79 ms | 100.0% |
| 7 | Quart | 4774.85 req/s | 10.47 ms | 10.28 ms | 12.57 ms | 100.0% |
| 8 | Flask | 2574.85 req/s | 19.44 ms | 24.42 ms | 31.59 ms | 75.5% |
| 9 | Django | 1551.20 req/s | 32.29 ms | 32.19 ms | 38.97 ms | 100.0% |

### Scenario: `db_queries`
GET `/queries` executing 5 random SQL queries sequentially.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Aquilia | 11623.52 req/s | 4.30 ms | 4.28 ms | 4.44 ms | 100.0% |
| 2 | Falcon | 2651.35 req/s | 18.85 ms | 18.64 ms | 22.02 ms | 100.0% |
| 3 | Starlette | 2572.36 req/s | 19.46 ms | 19.28 ms | 22.73 ms | 100.0% |
| 4 | Litestar | 2519.71 req/s | 19.87 ms | 19.67 ms | 23.17 ms | 100.0% |
| 5 | Flask | 2494.59 req/s | 20.07 ms | 23.95 ms | 31.14 ms | 78.2% |
| 6 | Sanic | 2434.96 req/s | 20.56 ms | 20.20 ms | 24.39 ms | 100.0% |
| 7 | FastAPI | 2361.76 req/s | 21.20 ms | 21.05 ms | 24.69 ms | 100.0% |
| 8 | Quart | 2257.99 req/s | 22.17 ms | 21.85 ms | 25.94 ms | 100.0% |
| 9 | Django | 919.48 req/s | 54.45 ms | 53.62 ms | 65.94 ms | 100.0% |

### Scenario: `db_updates`
GET `/updates` executing 5 select-update SQL statements under a database transaction.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Aquilia | 2259.09 req/s | 22.16 ms | 21.86 ms | 24.03 ms | 100.0% |
| 2 | Flask | 2042.99 req/s | 24.48 ms | 27.66 ms | 35.71 ms | 75.3% |
| 3 | Starlette | 1576.52 req/s | 28.55 ms | 0.69 ms | 88.71 ms | 100.0% |
| 4 | Falcon | 1568.19 req/s | 27.31 ms | 0.68 ms | 85.42 ms | 100.0% |
| 5 | Litestar | 1555.94 req/s | 28.89 ms | 0.71 ms | 84.59 ms | 100.0% |
| 6 | Sanic | 1547.02 req/s | 29.48 ms | 0.72 ms | 85.22 ms | 100.0% |
| 7 | Quart | 1487.86 req/s | 29.68 ms | 1.91 ms | 87.96 ms | 100.0% |
| 8 | FastAPI | 1445.31 req/s | 30.76 ms | 1.83 ms | 86.26 ms | 100.0% |
| 9 | Django | 1038.51 req/s | 48.36 ms | 46.02 ms | 124.81 ms | 13.6% |

### Scenario: `fortunes`
GET `/fortunes` fetching fortunes from database, adding a custom fortune, sorting, and rendering to HTML via Jinja2.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Aquilia | 5109.65 req/s | 9.79 ms | 9.71 ms | 10.74 ms | 100.0% |
| 2 | Starlette | 2811.32 req/s | 17.80 ms | 17.72 ms | 22.41 ms | 100.0% |
| 3 | Litestar | 2729.53 req/s | 18.33 ms | 18.20 ms | 23.07 ms | 100.0% |
| 4 | Falcon | 2652.89 req/s | 18.86 ms | 18.08 ms | 23.91 ms | 100.0% |
| 5 | FastAPI | 2651.88 req/s | 18.88 ms | 18.65 ms | 24.04 ms | 100.0% |
| 6 | Sanic | 2629.32 req/s | 19.03 ms | 18.78 ms | 24.48 ms | 100.0% |
| 7 | Flask | 2596.25 req/s | 19.26 ms | 21.98 ms | 32.35 ms | 79.9% |
| 8 | Quart | 2518.93 req/s | 19.88 ms | 19.61 ms | 25.22 ms | 100.0% |
| 9 | Django | 1222.33 req/s | 41.02 ms | 40.68 ms | 50.04 ms | 100.0% |

### Scenario: `cached`
GET `/cached` retrieving 5 random items from memory cache with fallback to DB.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 50976.27 req/s | 0.98 ms | 0.97 ms | 1.04 ms | 100.0% |
| 2 | Starlette | 44726.18 req/s | 1.12 ms | 1.11 ms | 1.16 ms | 100.0% |
| 3 | Litestar | 38041.31 req/s | 1.31 ms | 1.30 ms | 1.37 ms | 100.0% |
| 4 | Aquilia | 34543.98 req/s | 1.45 ms | 1.44 ms | 1.50 ms | 100.0% |
| 5 | Sanic | 28799.57 req/s | 1.73 ms | 1.51 ms | 3.22 ms | 100.0% |
| 6 | FastAPI | 19379.91 req/s | 2.58 ms | 2.56 ms | 2.65 ms | 100.0% |
| 7 | Quart | 16010.65 req/s | 3.12 ms | 3.05 ms | 3.30 ms | 100.0% |
| 8 | Django | 3845.88 req/s | 13.00 ms | 12.71 ms | 13.67 ms | 100.0% |
| 9 | Flask | 3332.05 req/s | 15.00 ms | 17.13 ms | 27.20 ms | 77.1% |

### Scenario: `validation`
POST `/validation` parsing and validating a nested payload (Contract vs Pydantic vs Dataclasses).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 48898.57 req/s | 1.02 ms | 1.01 ms | 1.08 ms | 100.0% |
| 2 | Starlette | 43647.72 req/s | 1.14 ms | 1.14 ms | 1.20 ms | 100.0% |
| 3 | Litestar | 30684.19 req/s | 1.63 ms | 1.62 ms | 1.70 ms | 100.0% |
| 4 | Sanic | 29639.22 req/s | 1.69 ms | 1.49 ms | 3.20 ms | 100.0% |
| 5 | Aquilia | 22773.82 req/s | 2.19 ms | 2.18 ms | 2.26 ms | 100.0% |
| 6 | FastAPI | 22474.66 req/s | 2.22 ms | 2.21 ms | 2.29 ms | 100.0% |
| 7 | Quart | 15068.78 req/s | 3.32 ms | 3.22 ms | 3.41 ms | 100.0% |
| 8 | Django | 3919.06 req/s | 12.76 ms | 12.57 ms | 13.50 ms | 100.0% |
| 9 | Flask | 3182.62 req/s | 15.73 ms | 16.99 ms | 30.17 ms | 78.3% |

### Scenario: `route_static`
GET `/route/static` matched against a large route table containing 500 placeholder routes. (Measures routing lookup performance).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 64400.63 req/s | 0.78 ms | 0.77 ms | 0.88 ms | 100.0% |
| 2 | Starlette | 56544.43 req/s | 0.88 ms | 0.87 ms | 0.92 ms | 100.0% |
| 3 | Litestar | 46658.91 req/s | 1.07 ms | 1.06 ms | 1.14 ms | 100.0% |
| 4 | Aquilia | 42400.69 req/s | 1.18 ms | 1.17 ms | 1.24 ms | 100.0% |
| 5 | Sanic | 36935.68 req/s | 1.35 ms | 1.21 ms | 2.63 ms | 100.0% |
| 6 | Quart | 18357.83 req/s | 2.72 ms | 2.64 ms | 2.87 ms | 100.0% |
| 7 | FastAPI | 6124.10 req/s | 8.16 ms | 8.14 ms | 8.47 ms | 100.0% |
| 8 | Django | 4081.52 req/s | 12.25 ms | 12.03 ms | 12.96 ms | 100.0% |
| 9 | Flask | 2991.11 req/s | 16.70 ms | 13.55 ms | 39.07 ms | 79.1% |

### Scenario: `route_params`
GET `/route/params/<user_id>/orders/<order_id>` parsing path variables.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 62176.73 req/s | 0.80 ms | 0.80 ms | 0.83 ms | 100.0% |
| 2 | Starlette | 53718.87 req/s | 0.93 ms | 0.92 ms | 0.97 ms | 100.0% |
| 3 | Litestar | 42482.61 req/s | 1.18 ms | 1.17 ms | 1.23 ms | 100.0% |
| 4 | Aquilia | 40907.14 req/s | 1.22 ms | 1.21 ms | 1.28 ms | 100.0% |
| 5 | Sanic | 36651.05 req/s | 1.36 ms | 1.23 ms | 2.68 ms | 100.0% |
| 6 | Quart | 17345.10 req/s | 2.88 ms | 2.80 ms | 3.01 ms | 100.0% |
| 7 | FastAPI | 5574.30 req/s | 8.97 ms | 8.96 ms | 9.26 ms | 100.0% |
| 8 | Django | 4056.30 req/s | 12.33 ms | 12.09 ms | 12.97 ms | 100.0% |
| 9 | Flask | 2973.48 req/s | 17.98 ms | 13.45 ms | 46.05 ms | 80.2% |

### Scenario: `di`
GET `/di` resolving a nested dependency injection hierarchy (Leaf -> Mid -> Top).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 65375.17 req/s | 0.76 ms | 0.77 ms | 0.88 ms | 100.0% |
| 2 | Starlette | 55744.59 req/s | 0.90 ms | 0.88 ms | 0.94 ms | 100.0% |
| 3 | Litestar | 46395.04 req/s | 1.08 ms | 1.07 ms | 1.13 ms | 100.0% |
| 4 | Aquilia | 41870.39 req/s | 1.19 ms | 1.19 ms | 1.25 ms | 100.0% |
| 5 | Sanic | 37560.27 req/s | 1.33 ms | 1.20 ms | 2.61 ms | 100.0% |
| 6 | Quart | 18580.26 req/s | 2.69 ms | 2.62 ms | 2.82 ms | 100.0% |
| 7 | FastAPI | 4166.53 req/s | 12.01 ms | 11.71 ms | 14.28 ms | 100.0% |
| 8 | Django | 4040.93 req/s | 12.37 ms | 12.10 ms | 13.08 ms | 100.0% |
| 9 | Flask | 2860.39 req/s | 18.05 ms | 13.17 ms | 44.64 ms | 81.4% |

### Scenario: `multipart`
POST `/body/multipart` uploading a 10KB text file. (Measures multipart parsing).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Sanic | 24636.69 req/s | 2.03 ms | 1.79 ms | 3.79 ms | 100.0% |
| 2 | Falcon | 23550.04 req/s | 2.12 ms | 1.96 ms | 2.73 ms | 100.0% |
| 3 | Starlette | 18217.14 req/s | 2.74 ms | 2.72 ms | 2.82 ms | 100.0% |
| 4 | Aquilia | 10127.28 req/s | 4.93 ms | 4.85 ms | 5.23 ms | 100.0% |
| 5 | Quart | 7212.59 req/s | 6.93 ms | 6.75 ms | 7.55 ms | 100.0% |
| 6 | FastAPI | 4492.77 req/s | 11.14 ms | 10.91 ms | 11.97 ms | 100.0% |
| 7 | Django | 2998.43 req/s | 16.68 ms | 15.92 ms | 19.20 ms | 100.0% |
| 8 | Flask | 2863.11 req/s | 17.48 ms | 17.00 ms | 28.76 ms | 87.5% |
| 9 | Litestar | 0.00 req/s | 0.00 ms | 0.00 ms | 0.00 ms | 0.0% |

### Scenario: `stream`
GET `/response/stream` sending a 32KB chunked-encoded stream.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 9146.56 req/s | 5.46 ms | 5.34 ms | 6.00 ms | 100.0% |
| 2 | Aquilia | 7788.08 req/s | 6.42 ms | 6.36 ms | 6.67 ms | 100.0% |
| 3 | Litestar | 6885.99 req/s | 7.26 ms | 7.20 ms | 7.49 ms | 100.0% |
| 4 | Starlette | 6781.90 req/s | 7.37 ms | 7.30 ms | 7.60 ms | 100.0% |
| 5 | Quart | 6504.69 req/s | 7.69 ms | 7.56 ms | 8.09 ms | 100.0% |
| 6 | FastAPI | 3161.17 req/s | 15.84 ms | 15.62 ms | 17.58 ms | 100.0% |
| 7 | Django | 1180.79 req/s | 42.49 ms | 41.21 ms | 45.87 ms | 100.0% |
| 8 | Flask | 30.98 req/s | 1806.21 ms | 2337.40 ms | 2420.56 ms | 100.0% |
| 9 | Sanic | 0.00 req/s | 0.00 ms | 0.00 ms | 0.00 ms | 0.0% |

### Scenario: `middleware_0`
GET `/plaintext` with 0 custom middleware layers.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 75697.52 req/s | 0.66 ms | 0.72 ms | 0.83 ms | 100.0% |
| 2 | Starlette | 69055.50 req/s | 0.72 ms | 0.75 ms | 0.87 ms | 100.0% |
| 3 | Litestar | 47644.86 req/s | 1.05 ms | 1.05 ms | 1.14 ms | 100.0% |
| 4 | Aquilia | 42735.63 req/s | 1.17 ms | 1.16 ms | 1.23 ms | 100.0% |
| 5 | FastAPI | 38303.05 req/s | 1.30 ms | 1.28 ms | 1.37 ms | 100.0% |
| 6 | Sanic | 37719.36 req/s | 1.32 ms | 1.19 ms | 2.55 ms | 100.0% |
| 7 | Quart | 19837.23 req/s | 2.52 ms | 2.43 ms | 2.69 ms | 100.0% |
| 8 | Django | 4163.16 req/s | 12.01 ms | 11.80 ms | 12.68 ms | 100.0% |
| 9 | Flask | 2456.13 req/s | 20.30 ms | 12.11 ms | 55.15 ms | 79.9% |

### Scenario: `middleware_5`
GET `/plaintext` with 5 stacked custom middleware layers.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 73882.13 req/s | 0.68 ms | 0.72 ms | 0.83 ms | 100.0% |
| 2 | Starlette | 68162.71 req/s | 0.73 ms | 0.75 ms | 0.87 ms | 100.0% |
| 3 | Litestar | 46152.53 req/s | 1.08 ms | 1.08 ms | 1.14 ms | 100.0% |
| 4 | Aquilia | 42876.92 req/s | 1.16 ms | 1.16 ms | 1.22 ms | 100.0% |
| 5 | Sanic | 36611.79 req/s | 1.36 ms | 1.24 ms | 2.61 ms | 100.0% |
| 6 | Quart | 18114.45 req/s | 2.76 ms | 2.64 ms | 2.97 ms | 100.0% |
| 7 | FastAPI | 3897.00 req/s | 12.84 ms | 12.32 ms | 15.08 ms | 100.0% |
| 8 | Django | 3429.26 req/s | 14.59 ms | 14.37 ms | 16.03 ms | 100.0% |
| 9 | Flask | 2397.60 req/s | 20.85 ms | 12.51 ms | 55.55 ms | 80.4% |

### Scenario: `middleware_10`
GET `/plaintext` with 10 stacked custom middleware layers.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 72313.90 req/s | 0.69 ms | 0.73 ms | 0.84 ms | 100.0% |
| 2 | Starlette | 65689.09 req/s | 0.76 ms | 0.77 ms | 0.87 ms | 100.0% |
| 3 | Litestar | 45183.27 req/s | 1.11 ms | 1.09 ms | 1.16 ms | 100.0% |
| 4 | Aquilia | 42711.10 req/s | 1.17 ms | 1.16 ms | 1.23 ms | 100.0% |
| 5 | Sanic | 35538.70 req/s | 1.41 ms | 1.28 ms | 2.64 ms | 100.0% |
| 6 | Quart | 17620.50 req/s | 2.84 ms | 2.77 ms | 2.97 ms | 100.0% |
| 7 | Django | 3487.09 req/s | 14.35 ms | 14.16 ms | 15.72 ms | 100.0% |
| 8 | FastAPI | 2168.21 req/s | 23.09 ms | 21.97 ms | 25.49 ms | 100.0% |
| 9 | Flask | 2156.74 req/s | 23.24 ms | 12.60 ms | 69.54 ms | 79.4% |

## 3. Key Performance Insights
### Middleware Scaling Cost
This table summarizes how throughput scales as middleware layers are stacked (0 -> 5 -> 10 layers).

| Framework | 0 Layers QPS | 5 Layers QPS | 10 Layers QPS | Overhead (10 vs 0) |
| :--- | :--- | :--- | :--- | :--- |
| Aquilia | 42735.63 | 42876.92 | 42711.10 | 0.1% decrease |
| FastAPI | 38303.05 | 3897.00 | 2168.21 | 94.3% decrease |
| Starlette | 69055.50 | 68162.71 | 65689.09 | 4.9% decrease |
| Litestar | 47644.86 | 46152.53 | 45183.27 | 5.2% decrease |
| Falcon | 75697.52 | 73882.13 | 72313.90 | 4.5% decrease |
| Sanic | 37719.36 | 36611.79 | 35538.70 | 5.8% decrease |
| Quart | 19837.23 | 18114.45 | 17620.50 | 11.2% decrease |
| Flask | 2456.13 | 2397.60 | 2156.74 | 12.2% decrease |
| Django | 4163.16 | 3429.26 | 3487.09 | 16.2% decrease |

