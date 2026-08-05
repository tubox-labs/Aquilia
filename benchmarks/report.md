# Aquilia Professional Web Framework Benchmarks

This document presents the objective, reproducible, and statistically valid benchmarks comparing the performance characteristics of Aquilia against major Python web frameworks.

## Benchmark Parameters
- **Load Testing Utility**: `oha` (Rust-based HTTP/1.1 load generator)
- **Concurrency Level**: `50` simultaneous connections
- **Duration**: `5s` per endpoint run
- **Server Environment**: Python 3.13 served via Uvicorn (Single worker thread)
- **Database Engine**: SQLite 3 (Standard 10,000-row TechEmpower Schema)

## 1. Cold Startup & Importing Overhead
Measures the pure framework importing and initialization time. Fast cold start times are critical for Serverless deployments and developer container boot-ups.

| Rank | Framework | Mean Startup (ms) | StdDev (ms) | Min (ms) | Max (ms) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Starlette | 181.57ms | ±3.15ms | 177.34ms | 186.53ms |
| 2 | Django | 215.76ms | ±2.72ms | 212.41ms | 219.47ms |
| 3 | Flask | 218.40ms | ±2.37ms | 215.53ms | 221.66ms |
| 4 | Aquilia | 231.52ms | ±2.77ms | 226.00ms | 235.52ms |
| 5 | Falcon | 232.94ms | ±2.62ms | 228.61ms | 237.65ms |
| 6 | Quart | 247.48ms | ±3.24ms | 244.00ms | 252.65ms |
| 7 | Sanic | 253.06ms | ±3.40ms | 248.87ms | 256.67ms |
| 8 | FastAPI | 302.05ms | ±3.59ms | 295.13ms | 307.73ms |
| 9 | Litestar | 382.63ms | ±3.85ms | 375.56ms | 387.71ms |

## 2. HTTP Throughput and Latency Results
The tables below highlight framework performance metrics across various workload scenarios.

### Scenario: `plaintext`
GET `/plaintext` returning 'Hello, World!' (Measures raw HTTP parsing and serialization throughput).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 70092.96 req/s | 0.71 ms | 0.74 ms | 0.84 ms | 100.0% |
| 2 | Starlette | 58013.94 req/s | 0.86 ms | 0.84 ms | 0.91 ms | 100.0% |
| 3 | Litestar | 43148.89 req/s | 1.16 ms | 1.15 ms | 1.22 ms | 100.0% |
| 4 | Aquilia | 35312.29 req/s | 1.41 ms | 1.40 ms | 1.48 ms | 100.0% |
| 5 | Sanic | 34642.07 req/s | 1.44 ms | 1.20 ms | 1.87 ms | 100.0% |
| 6 | FastAPI | 33314.37 req/s | 1.50 ms | 1.49 ms | 1.56 ms | 100.0% |
| 7 | Quart | 16242.67 req/s | 3.08 ms | 2.74 ms | 3.04 ms | 100.0% |
| 8 | Django | 3772.61 req/s | 13.26 ms | 11.94 ms | 27.23 ms | 100.0% |
| 9 | Flask | 2602.70 req/s | 19.20 ms | 13.47 ms | 46.57 ms | 100.0% |

### Scenario: `json`
GET `/json` returning a small JSON dictionary. (Measures JSON encoding overhead).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 60346.86 req/s | 0.83 ms | 0.82 ms | 0.86 ms | 100.0% |
| 2 | Starlette | 54070.68 req/s | 0.92 ms | 0.92 ms | 0.98 ms | 100.0% |
| 3 | Litestar | 42276.71 req/s | 1.18 ms | 1.17 ms | 1.24 ms | 100.0% |
| 4 | Aquilia | 34415.78 req/s | 1.45 ms | 1.44 ms | 1.51 ms | 100.0% |
| 5 | Sanic | 33977.07 req/s | 1.47 ms | 1.23 ms | 1.93 ms | 100.0% |
| 6 | FastAPI | 29188.55 req/s | 1.71 ms | 1.68 ms | 1.77 ms | 100.0% |
| 7 | Quart | 15606.76 req/s | 3.20 ms | 2.88 ms | 3.33 ms | 100.0% |
| 8 | Django | 3609.83 req/s | 13.86 ms | 13.00 ms | 27.49 ms | 100.0% |
| 9 | Flask | 2624.78 req/s | 19.04 ms | 12.45 ms | 47.61 ms | 100.0% |

### Scenario: `json_large`
GET `/json/large` returning a nested 100KB JSON payload. (Measures large serialization performance).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Litestar | 6775.60 req/s | 7.38 ms | 7.19 ms | 7.50 ms | 100.0% |
| 2 | Sanic | 2319.82 req/s | 21.58 ms | 20.82 ms | 22.45 ms | 100.0% |
| 3 | Aquilia | 2248.87 req/s | 22.26 ms | 21.04 ms | 29.06 ms | 100.0% |
| 4 | Falcon | 1333.99 req/s | 37.59 ms | 36.78 ms | 37.08 ms | 100.0% |
| 5 | Starlette | 1313.40 req/s | 38.18 ms | 37.17 ms | 38.71 ms | 100.0% |
| 6 | Quart | 1127.13 req/s | 44.55 ms | 43.43 ms | 53.73 ms | 100.0% |
| 7 | Django | 984.31 req/s | 51.06 ms | 50.28 ms | 64.48 ms | 100.0% |
| 8 | Flask | 930.45 req/s | 53.96 ms | 58.44 ms | 63.67 ms | 100.0% |
| 9 | FastAPI | 169.50 req/s | 244.11 ms | 184.50 ms | 361.02 ms | 100.0% |

### Scenario: `db_single`
GET `/db` executing 1 SQL query. (Measures single database retrieval latency).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 6511.66 req/s | 7.68 ms | 7.58 ms | 9.02 ms | 100.0% |
| 2 | Starlette | 6111.35 req/s | 8.18 ms | 8.02 ms | 9.70 ms | 100.0% |
| 3 | Litestar | 5978.70 req/s | 8.36 ms | 8.20 ms | 9.64 ms | 100.0% |
| 4 | Aquilia | 5796.97 req/s | 8.63 ms | 8.28 ms | 10.54 ms | 100.0% |
| 5 | Sanic | 5719.43 req/s | 8.74 ms | 8.41 ms | 10.36 ms | 100.0% |
| 6 | FastAPI | 4994.19 req/s | 10.01 ms | 9.22 ms | 11.72 ms | 100.0% |
| 7 | Quart | 4836.56 req/s | 10.34 ms | 9.96 ms | 12.04 ms | 100.0% |
| 8 | Flask | 2784.00 req/s | 17.95 ms | 15.81 ms | 40.97 ms | 100.0% |
| 9 | Django | 1507.83 req/s | 33.26 ms | 31.19 ms | 49.26 ms | 100.0% |

### Scenario: `db_queries`
GET `/queries` executing 5 random SQL queries sequentially.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 2784.42 req/s | 17.98 ms | 17.86 ms | 20.49 ms | 100.0% |
| 2 | Starlette | 2633.34 req/s | 19.00 ms | 18.86 ms | 21.75 ms | 100.0% |
| 3 | Litestar | 2627.91 req/s | 19.05 ms | 18.74 ms | 21.95 ms | 100.0% |
| 4 | Flask | 2596.20 req/s | 19.28 ms | 17.51 ms | 40.73 ms | 100.0% |
| 5 | Sanic | 2587.46 req/s | 19.35 ms | 19.03 ms | 22.15 ms | 100.0% |
| 6 | FastAPI | 2408.77 req/s | 20.79 ms | 20.49 ms | 23.88 ms | 100.0% |
| 7 | Quart | 2349.90 req/s | 21.31 ms | 20.97 ms | 24.49 ms | 100.0% |
| 8 | Aquilia | 1496.11 req/s | 33.52 ms | 32.83 ms | 36.86 ms | 100.0% |
| 9 | Django | 915.34 req/s | 54.91 ms | 52.24 ms | 71.32 ms | 100.0% |

### Scenario: `db_updates`
GET `/updates` executing 5 select-update SQL statements under a database transaction.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Flask | 1767.33 req/s | 28.36 ms | 22.07 ms | 47.46 ms | 100.0% |
| 2 | Falcon | 1595.17 req/s | 28.57 ms | 0.69 ms | 86.33 ms | 100.0% |
| 3 | Sanic | 1557.03 req/s | 28.74 ms | 0.73 ms | 85.43 ms | 100.0% |
| 4 | Litestar | 1553.42 req/s | 29.68 ms | 0.72 ms | 86.64 ms | 100.0% |
| 5 | FastAPI | 1508.64 req/s | 29.75 ms | 1.83 ms | 87.85 ms | 100.0% |
| 6 | Starlette | 1504.83 req/s | 29.66 ms | 1.76 ms | 87.57 ms | 100.0% |
| 7 | Quart | 1467.66 req/s | 29.89 ms | 1.95 ms | 109.03 ms | 100.0% |
| 8 | Django | 1045.83 req/s | 48.03 ms | 44.99 ms | 74.23 ms | 100.0% |
| 9 | Aquilia | 744.16 req/s | 67.57 ms | 66.46 ms | 74.40 ms | 100.0% |

### Scenario: `fortunes`
GET `/fortunes` fetching fortunes from database, adding a custom fortune, sorting, and rendering to HTML via Jinja2.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Aquilia | 4412.41 req/s | 11.33 ms | 11.18 ms | 11.99 ms | 100.0% |
| 2 | Falcon | 2903.08 req/s | 17.23 ms | 17.00 ms | 21.77 ms | 100.0% |
| 3 | Starlette | 2776.35 req/s | 18.03 ms | 17.69 ms | 23.25 ms | 100.0% |
| 4 | Litestar | 2724.66 req/s | 18.37 ms | 17.91 ms | 23.24 ms | 100.0% |
| 5 | Sanic | 2704.79 req/s | 18.50 ms | 18.18 ms | 23.35 ms | 100.0% |
| 6 | FastAPI | 2683.79 req/s | 18.66 ms | 18.18 ms | 24.01 ms | 100.0% |
| 7 | Flask | 2514.25 req/s | 19.84 ms | 16.97 ms | 45.73 ms | 100.0% |
| 8 | Quart | 2512.57 req/s | 19.92 ms | 19.61 ms | 24.31 ms | 100.0% |
| 9 | Django | 1184.75 req/s | 42.33 ms | 41.03 ms | 60.73 ms | 100.0% |

### Scenario: `cached`
GET `/cached` retrieving 5 random items from memory cache with fallback to DB.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 46509.19 req/s | 1.07 ms | 1.07 ms | 1.13 ms | 100.0% |
| 2 | Starlette | 37829.39 req/s | 1.32 ms | 1.28 ms | 1.41 ms | 100.0% |
| 3 | Litestar | 33149.11 req/s | 1.51 ms | 1.49 ms | 1.56 ms | 100.0% |
| 4 | Sanic | 26776.58 req/s | 1.87 ms | 1.58 ms | 2.25 ms | 100.0% |
| 5 | Aquilia | 26440.91 req/s | 1.89 ms | 1.87 ms | 1.95 ms | 100.0% |
| 6 | FastAPI | 17081.49 req/s | 2.93 ms | 2.90 ms | 2.99 ms | 100.0% |
| 7 | Quart | 13902.53 req/s | 3.59 ms | 3.28 ms | 3.55 ms | 100.0% |
| 8 | Django | 3304.33 req/s | 15.14 ms | 14.09 ms | 29.95 ms | 100.0% |
| 9 | Flask | 2301.82 req/s | 21.68 ms | 12.80 ms | 58.94 ms | 100.0% |

### Scenario: `validation`
POST `/validation` parsing and validating a nested payload (Contract vs Pydantic vs Dataclasses).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Litestar | 17421.97 req/s | 2.87 ms | 2.86 ms | 2.95 ms | 100.0% |
| 2 | FastAPI | 13382.48 req/s | 3.73 ms | 3.56 ms | 4.04 ms | 100.0% |
| 3 | Django | 2146.27 req/s | 23.29 ms | 19.91 ms | 43.58 ms | 100.0% |
| 4 | Starlette | 2020.49 req/s | 49.10 ms | 48.88 ms | 79.86 ms | 50.1% |
| 5 | Aquilia | 1809.47 req/s | 27.70 ms | 27.09 ms | 31.70 ms | 100.0% |
| 6 | Falcon | 1611.76 req/s | 31.07 ms | 32.91 ms | 39.76 ms | 100.0% |
| 7 | Sanic | 1164.17 req/s | 43.17 ms | 44.52 ms | 50.41 ms | 100.0% |
| 8 | Quart | 497.30 req/s | 101.14 ms | 96.60 ms | 123.29 ms | 100.0% |
| 9 | Flask | 424.54 req/s | 118.44 ms | 149.51 ms | 194.50 ms | 100.0% |

### Scenario: `route_static`
GET `/route/static` matched against a large route table containing 500 placeholder routes. (Measures routing lookup performance).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 58804.75 req/s | 0.85 ms | 0.85 ms | 0.88 ms | 100.0% |
| 2 | Starlette | 48606.08 req/s | 1.03 ms | 1.02 ms | 1.08 ms | 100.0% |
| 3 | Litestar | 41518.43 req/s | 1.20 ms | 1.20 ms | 1.27 ms | 100.0% |
| 4 | Aquilia | 33912.98 req/s | 1.47 ms | 1.46 ms | 1.54 ms | 100.0% |
| 5 | Sanic | 33692.73 req/s | 1.48 ms | 1.24 ms | 1.94 ms | 100.0% |
| 6 | Quart | 15217.96 req/s | 3.28 ms | 2.91 ms | 3.41 ms | 100.0% |
| 7 | FastAPI | 4340.79 req/s | 11.52 ms | 11.56 ms | 11.73 ms | 100.0% |
| 8 | Django | 3472.20 req/s | 14.41 ms | 13.39 ms | 28.96 ms | 100.0% |
| 9 | Flask | 1982.45 req/s | 25.26 ms | 12.67 ms | 64.55 ms | 100.0% |

### Scenario: `route_params`
GET `/route/params/<user_id>/orders/<order_id>` parsing path variables.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 55860.34 req/s | 0.89 ms | 0.89 ms | 0.94 ms | 100.0% |
| 2 | Starlette | 45567.83 req/s | 1.10 ms | 1.07 ms | 1.14 ms | 100.0% |
| 3 | Litestar | 37390.48 req/s | 1.34 ms | 1.32 ms | 1.42 ms | 100.0% |
| 4 | Sanic | 33273.22 req/s | 1.50 ms | 1.26 ms | 1.97 ms | 100.0% |
| 5 | Aquilia | 33181.78 req/s | 1.51 ms | 1.49 ms | 1.57 ms | 100.0% |
| 6 | Quart | 14138.74 req/s | 3.53 ms | 3.09 ms | 4.04 ms | 100.0% |
| 7 | FastAPI | 4073.30 req/s | 12.28 ms | 12.15 ms | 12.49 ms | 100.0% |
| 8 | Django | 3440.44 req/s | 14.54 ms | 13.49 ms | 29.02 ms | 100.0% |
| 9 | Flask | 2078.88 req/s | 24.11 ms | 12.50 ms | 67.01 ms | 100.0% |

### Scenario: `di`
GET `/di` resolving a nested dependency injection hierarchy (Leaf -> Mid -> Top).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 58537.79 req/s | 0.85 ms | 0.85 ms | 0.89 ms | 100.0% |
| 2 | Starlette | 47047.60 req/s | 1.06 ms | 1.05 ms | 1.11 ms | 100.0% |
| 3 | Litestar | 41501.07 req/s | 1.20 ms | 1.20 ms | 1.27 ms | 100.0% |
| 4 | Sanic | 33570.20 req/s | 1.49 ms | 1.24 ms | 1.94 ms | 100.0% |
| 5 | Aquilia | 33464.61 req/s | 1.49 ms | 1.48 ms | 1.55 ms | 100.0% |
| 6 | Quart | 15596.84 req/s | 3.20 ms | 2.90 ms | 3.16 ms | 100.0% |
| 7 | Django | 3467.14 req/s | 14.38 ms | 13.36 ms | 29.08 ms | 100.0% |
| 8 | FastAPI | 2900.58 req/s | 17.26 ms | 16.43 ms | 22.47 ms | 100.0% |
| 9 | Flask | 2231.32 req/s | 22.46 ms | 12.37 ms | 61.44 ms | 100.0% |

### Scenario: `multipart`
POST `/body/multipart` uploading a 10KB text file. (Measures multipart parsing).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Sanic | 22989.40 req/s | 2.17 ms | 1.87 ms | 2.67 ms | 100.0% |
| 2 | Litestar | 21874.83 req/s | 2.28 ms | 2.27 ms | 2.38 ms | 100.0% |
| 3 | Falcon | 20781.56 req/s | 2.40 ms | 2.10 ms | 3.12 ms | 100.0% |
| 4 | Starlette | 15822.70 req/s | 3.16 ms | 3.14 ms | 3.23 ms | 100.0% |
| 5 | Aquilia | 9723.43 req/s | 5.14 ms | 5.08 ms | 5.25 ms | 100.0% |
| 6 | Quart | 7234.96 req/s | 6.91 ms | 6.48 ms | 7.72 ms | 100.0% |
| 7 | FastAPI | 3403.24 req/s | 14.72 ms | 14.51 ms | 15.43 ms | 100.0% |
| 8 | Django | 2791.85 req/s | 17.92 ms | 16.70 ms | 33.51 ms | 100.0% |
| 9 | Flask | 2450.75 req/s | 20.31 ms | 16.48 ms | 56.72 ms | 100.0% |

### Scenario: `stream`
GET `/response/stream` sending a 32KB chunked-encoded stream.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 9360.80 req/s | 5.34 ms | 5.25 ms | 5.62 ms | 100.0% |
| 2 | Aquilia | 7532.32 req/s | 6.64 ms | 6.57 ms | 6.86 ms | 100.0% |
| 3 | Litestar | 6816.97 req/s | 7.33 ms | 7.22 ms | 7.97 ms | 100.0% |
| 4 | Starlette | 6669.65 req/s | 7.50 ms | 7.43 ms | 7.73 ms | 100.0% |
| 5 | Quart | 6317.47 req/s | 7.91 ms | 7.76 ms | 8.20 ms | 100.0% |
| 6 | FastAPI | 2331.70 req/s | 21.49 ms | 20.03 ms | 32.02 ms | 100.0% |
| 7 | Sanic | 2090.76 req/s | 23.94 ms | 25.04 ms | 31.54 ms | 100.0% |
| 8 | Django | 1125.63 req/s | 44.58 ms | 41.90 ms | 67.16 ms | 100.0% |
| 9 | Flask | 30.97 req/s | 1804.19 ms | 2349.41 ms | 2378.43 ms | 100.0% |

### Scenario: `middleware_0`
GET `/plaintext` with 0 custom middleware layers.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 67318.93 req/s | 0.74 ms | 0.74 ms | 0.89 ms | 100.0% |
| 2 | Starlette | 57274.31 req/s | 0.87 ms | 0.86 ms | 0.94 ms | 100.0% |
| 3 | Litestar | 41843.02 req/s | 1.19 ms | 1.18 ms | 1.32 ms | 100.0% |
| 4 | Aquilia | 33376.04 req/s | 1.50 ms | 1.48 ms | 1.56 ms | 100.0% |
| 5 | FastAPI | 32624.44 req/s | 1.53 ms | 1.51 ms | 1.63 ms | 100.0% |
| 6 | Sanic | 32111.39 req/s | 1.56 ms | 1.22 ms | 1.94 ms | 100.0% |
| 7 | Quart | 16429.84 req/s | 3.04 ms | 2.74 ms | 3.01 ms | 100.0% |
| 8 | Django | 3564.10 req/s | 14.04 ms | 13.13 ms | 27.99 ms | 100.0% |
| 9 | Flask | 1017.90 req/s | 49.45 ms | 13.84 ms | 88.74 ms | 100.0% |

### Scenario: `middleware_5`
GET `/plaintext` with 5 stacked custom middleware layers.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 66512.27 req/s | 0.75 ms | 0.76 ms | 0.87 ms | 100.0% |
| 2 | Starlette | 57183.03 req/s | 0.87 ms | 0.86 ms | 0.93 ms | 100.0% |
| 3 | Litestar | 39324.64 req/s | 1.27 ms | 1.24 ms | 1.34 ms | 100.0% |
| 4 | Aquilia | 35099.88 req/s | 1.42 ms | 1.41 ms | 1.48 ms | 100.0% |
| 5 | Sanic | 32051.25 req/s | 1.56 ms | 1.27 ms | 2.04 ms | 100.0% |
| 6 | Quart | 15806.18 req/s | 3.16 ms | 2.86 ms | 3.11 ms | 100.0% |
| 7 | FastAPI | 3297.93 req/s | 15.17 ms | 13.94 ms | 32.19 ms | 100.0% |
| 8 | Django | 2763.72 req/s | 18.11 ms | 16.04 ms | 31.70 ms | 100.0% |
| 9 | Flask | 1701.02 req/s | 29.42 ms | 12.88 ms | 85.27 ms | 100.0% |

### Scenario: `middleware_10`
GET `/plaintext` with 10 stacked custom middleware layers.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 65030.01 req/s | 0.77 ms | 0.77 ms | 0.83 ms | 100.0% |
| 2 | Starlette | 54198.05 req/s | 0.92 ms | 0.90 ms | 0.97 ms | 100.0% |
| 3 | Litestar | 39480.09 req/s | 1.26 ms | 1.26 ms | 1.33 ms | 100.0% |
| 4 | Aquilia | 35147.65 req/s | 1.42 ms | 1.41 ms | 1.49 ms | 100.0% |
| 5 | Sanic | 31155.42 req/s | 1.60 ms | 1.33 ms | 2.06 ms | 100.0% |
| 6 | Quart | 15176.33 req/s | 3.29 ms | 3.01 ms | 3.25 ms | 100.0% |
| 7 | Django | 2928.79 req/s | 17.09 ms | 16.01 ms | 31.36 ms | 100.0% |
| 8 | FastAPI | 1703.63 req/s | 29.37 ms | 25.36 ms | 49.22 ms | 100.0% |
| 9 | Flask | 1555.99 req/s | 31.96 ms | 13.99 ms | 98.13 ms | 100.0% |

## 3. Key Performance Insights
### Middleware Scaling Cost
This table summarizes how throughput scales as middleware layers are stacked (0 -> 5 -> 10 layers).

| Framework | 0 Layers QPS | 5 Layers QPS | 10 Layers QPS | Overhead (10 vs 0) |
| :--- | :--- | :--- | :--- | :--- |
| Aquilia | 33376.04 | 35099.88 | 35147.65 | -5.3% decrease |
| FastAPI | 32624.44 | 3297.93 | 1703.63 | 94.8% decrease |
| Starlette | 57274.31 | 57183.03 | 54198.05 | 5.4% decrease |
| Litestar | 41843.02 | 39324.64 | 39480.09 | 5.6% decrease |
| Falcon | 67318.93 | 66512.27 | 65030.01 | 3.4% decrease |
| Sanic | 32111.39 | 32051.25 | 31155.42 | 3.0% decrease |
| Quart | 16429.84 | 15806.18 | 15176.33 | 7.6% decrease |
| Flask | 1017.90 | 1701.02 | 1555.99 | -52.9% decrease |
| Django | 3564.10 | 2763.72 | 2928.79 | 17.8% decrease |

