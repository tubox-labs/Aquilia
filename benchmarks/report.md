# Aquilia Professional Web Framework Benchmarks

This document presents the objective, reproducible, and statistically valid benchmarks comparing the performance characteristics of Aquilia against major Python web frameworks.

## Benchmark Parameters
- **Load Testing Utility**: `oha` (Rust-based HTTP/1.1 load generator)
- **Concurrency Level**: `50` simultaneous connections
- **Duration**: `3s` per endpoint run
- **Server Environment**: Python 3.13 served via Uvicorn (Single worker thread)
- **Database Engine**: SQLite 3 (Standard 10,000-row TechEmpower Schema)

## 1. Cold Startup & Importing Overhead
Measures the pure framework importing and initialization time. Fast cold start times are critical for Serverless deployments and developer container boot-ups.

| Rank | Framework | Mean Startup (ms) | StdDev (ms) | Min (ms) | Max (ms) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Aquilia | 210.43ms | ±2.56ms | 206.95ms | 214.34ms |
| 2 | Starlette | 256.60ms | ±2.56ms | 253.27ms | 260.16ms |
| 3 | Django | 295.63ms | ±4.18ms | 289.40ms | 304.40ms |
| 4 | Flask | 305.31ms | ±3.99ms | 300.52ms | 312.09ms |
| 5 | Falcon | 314.40ms | ±2.57ms | 309.76ms | 316.88ms |
| 6 | Sanic | 324.97ms | ±9.95ms | 313.88ms | 347.39ms |
| 7 | Quart | 351.63ms | ±16.03ms | 330.74ms | 378.86ms |
| 8 | FastAPI | 377.06ms | ±3.04ms | 373.01ms | 381.40ms |
| 9 | Litestar | 462.32ms | ±5.08ms | 457.56ms | 474.76ms |

## 2. HTTP Throughput and Latency Results
The tables below highlight framework performance metrics across various workload scenarios.

### Scenario: `plaintext`
GET `/plaintext` returning 'Hello, World!' (Measures raw HTTP parsing and serialization throughput).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 69376.99 req/s | 0.72 ms | 0.73 ms | 0.81 ms | 100.0% |
| 2 | Starlette | 63554.67 req/s | 0.79 ms | 0.79 ms | 0.83 ms | 100.0% |
| 3 | Litestar | 44334.69 req/s | 1.13 ms | 1.13 ms | 1.18 ms | 100.0% |
| 4 | Sanic | 37579.63 req/s | 1.33 ms | 1.23 ms | 2.43 ms | 100.0% |
| 5 | FastAPI | 37537.30 req/s | 1.33 ms | 1.33 ms | 1.40 ms | 100.0% |
| 6 | Quart | 18994.95 req/s | 2.63 ms | 2.56 ms | 2.81 ms | 100.0% |
| 7 | Aquilia | 15578.50 req/s | 3.21 ms | 3.17 ms | 3.40 ms | 100.0% |
| 8 | Django | 5294.15 req/s | 9.45 ms | 8.90 ms | 11.39 ms | 100.0% |
| 9 | Flask | 3250.86 req/s | 15.33 ms | 12.63 ms | 35.54 ms | 100.0% |

### Scenario: `json`
GET `/json` returning a small JSON dictionary. (Measures JSON encoding overhead).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 61167.71 req/s | 0.82 ms | 0.81 ms | 0.85 ms | 100.0% |
| 2 | Starlette | 58605.90 req/s | 0.85 ms | 0.85 ms | 0.89 ms | 100.0% |
| 3 | Litestar | 44422.99 req/s | 1.12 ms | 1.12 ms | 1.18 ms | 100.0% |
| 4 | Sanic | 37007.77 req/s | 1.35 ms | 1.25 ms | 2.52 ms | 100.0% |
| 5 | FastAPI | 33333.05 req/s | 1.50 ms | 1.50 ms | 1.56 ms | 100.0% |
| 6 | Quart | 17847.74 req/s | 2.80 ms | 2.73 ms | 2.98 ms | 100.0% |
| 7 | Aquilia | 13837.77 req/s | 3.61 ms | 3.45 ms | 3.81 ms | 100.0% |
| 8 | Django | 5248.28 req/s | 9.54 ms | 8.97 ms | 11.42 ms | 100.0% |
| 9 | Flask | 2970.38 req/s | 16.83 ms | 12.64 ms | 40.15 ms | 100.0% |

### Scenario: `json_large`
GET `/json/large` returning a nested 100KB JSON payload. (Measures large serialization performance).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Litestar | 6920.33 req/s | 7.23 ms | 7.08 ms | 7.28 ms | 100.0% |
| 2 | Sanic | 2195.75 req/s | 22.85 ms | 22.16 ms | 24.43 ms | 100.0% |
| 3 | Starlette | 1637.82 req/s | 30.66 ms | 29.79 ms | 30.85 ms | 100.0% |
| 4 | Falcon | 1583.20 req/s | 31.72 ms | 30.98 ms | 32.59 ms | 100.0% |
| 5 | Django | 1288.31 req/s | 39.03 ms | 38.10 ms | 41.15 ms | 100.0% |
| 6 | Quart | 1254.90 req/s | 40.09 ms | 40.22 ms | 40.86 ms | 100.0% |
| 7 | Flask | 1046.70 req/s | 48.12 ms | 47.46 ms | 55.78 ms | 100.0% |
| 8 | Aquilia | 244.36 req/s | 157.91 ms | 115.88 ms | 244.99 ms | 100.0% |
| 9 | FastAPI | 208.40 req/s | 171.93 ms | 124.01 ms | 284.68 ms | 100.0% |

### Scenario: `db_single`
GET `/db` executing 1 SQL query. (Measures single database retrieval latency).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 6371.45 req/s | 7.85 ms | 7.76 ms | 9.29 ms | 100.0% |
| 2 | Starlette | 6151.74 req/s | 8.14 ms | 8.06 ms | 9.60 ms | 100.0% |
| 3 | Litestar | 5906.24 req/s | 8.47 ms | 8.39 ms | 10.01 ms | 100.0% |
| 4 | Sanic | 5571.97 req/s | 8.98 ms | 8.75 ms | 11.12 ms | 100.0% |
| 5 | FastAPI | 5163.48 req/s | 9.70 ms | 9.07 ms | 10.83 ms | 100.0% |
| 6 | Quart | 4739.22 req/s | 10.57 ms | 10.38 ms | 12.31 ms | 100.0% |
| 7 | Aquilia | 4100.75 req/s | 12.21 ms | 11.41 ms | 13.81 ms | 100.0% |
| 8 | Django | 3749.84 req/s | 13.34 ms | 12.50 ms | 16.55 ms | 100.0% |
| 9 | Flask | 2528.81 req/s | 19.80 ms | 17.13 ms | 36.43 ms | 100.0% |

### Scenario: `db_queries`
GET `/queries` executing 5 random SQL queries sequentially.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Flask | 49026.80 req/s | 0.00 ms | 0.00 ms | 0.00 ms | 0.0% |
| 2 | Falcon | 2681.81 req/s | 18.69 ms | 18.59 ms | 21.62 ms | 100.0% |
| 3 | Django | 2615.10 req/s | 19.18 ms | 18.40 ms | 28.37 ms | 100.0% |
| 4 | Starlette | 2513.67 req/s | 19.95 ms | 19.85 ms | 22.96 ms | 100.0% |
| 5 | Litestar | 2482.48 req/s | 20.20 ms | 20.10 ms | 23.17 ms | 100.0% |
| 6 | Sanic | 2411.35 req/s | 20.80 ms | 20.49 ms | 24.26 ms | 100.0% |
| 7 | FastAPI | 2300.97 req/s | 21.78 ms | 21.65 ms | 25.03 ms | 100.0% |
| 8 | Quart | 2207.61 req/s | 22.71 ms | 22.62 ms | 26.48 ms | 100.0% |
| 9 | Aquilia | 1298.79 req/s | 38.72 ms | 38.06 ms | 41.36 ms | 100.0% |

### Scenario: `db_updates`
GET `/updates` executing 5 select-update SQL statements under a database transaction.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Flask | 237880.72 req/s | 0.00 ms | 0.00 ms | 0.00 ms | 0.0% |
| 2 | Django | 3107.09 req/s | 16.44 ms | 14.04 ms | 31.20 ms | 97.4% |
| 3 | Falcon | 1614.38 req/s | 24.62 ms | 0.67 ms | 87.74 ms | 100.0% |
| 4 | Starlette | 1596.66 req/s | 24.82 ms | 0.69 ms | 61.48 ms | 100.0% |
| 5 | Litestar | 1595.54 req/s | 24.74 ms | 0.70 ms | 85.68 ms | 100.0% |
| 6 | Sanic | 1566.82 req/s | 26.76 ms | 0.70 ms | 86.00 ms | 100.0% |
| 7 | FastAPI | 1562.48 req/s | 25.94 ms | 1.79 ms | 85.55 ms | 100.0% |
| 8 | Quart | 1552.26 req/s | 25.35 ms | 1.85 ms | 86.29 ms | 100.0% |
| 9 | Aquilia | 742.86 req/s | 68.00 ms | 68.23 ms | 71.02 ms | 100.0% |

### Scenario: `fortunes`
GET `/fortunes` fetching fortunes from database, adding a custom fortune, sorting, and rendering to HTML via Jinja2.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Flask | 48577.36 req/s | 0.00 ms | 0.00 ms | 0.00 ms | 0.0% |
| 2 | Aquilia | 3373.94 req/s | 14.85 ms | 14.54 ms | 16.92 ms | 100.0% |
| 3 | Falcon | 2894.68 req/s | 17.32 ms | 17.22 ms | 22.03 ms | 100.0% |
| 4 | Django | 2762.79 req/s | 19.16 ms | 18.72 ms | 29.33 ms | 91.6% |
| 5 | Starlette | 2736.85 req/s | 18.29 ms | 18.15 ms | 23.21 ms | 100.0% |
| 6 | Litestar | 2684.35 req/s | 18.67 ms | 18.67 ms | 23.55 ms | 100.0% |
| 7 | Sanic | 2612.72 req/s | 19.16 ms | 19.06 ms | 24.32 ms | 100.0% |
| 8 | FastAPI | 2581.95 req/s | 19.39 ms | 19.30 ms | 24.44 ms | 100.0% |
| 9 | Quart | 2378.07 req/s | 21.09 ms | 20.89 ms | 26.13 ms | 100.0% |

### Scenario: `cached`
GET `/cached` retrieving 5 random items from memory cache with fallback to DB.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 48661.86 req/s | 1.03 ms | 1.02 ms | 1.09 ms | 100.0% |
| 2 | Flask | 48430.89 req/s | 0.00 ms | 0.00 ms | 0.00 ms | 0.0% |
| 3 | Starlette | 42734.74 req/s | 1.17 ms | 1.17 ms | 1.24 ms | 100.0% |
| 4 | Litestar | 35947.22 req/s | 1.39 ms | 1.39 ms | 1.45 ms | 100.0% |
| 5 | Sanic | 28713.63 req/s | 1.74 ms | 1.56 ms | 3.04 ms | 100.0% |
| 6 | FastAPI | 18849.96 req/s | 2.65 ms | 2.65 ms | 2.73 ms | 100.0% |
| 7 | Quart | 15677.43 req/s | 3.19 ms | 3.13 ms | 3.35 ms | 100.0% |
| 8 | Aquilia | 12155.80 req/s | 4.11 ms | 4.07 ms | 4.29 ms | 100.0% |
| 9 | Django | 5204.95 req/s | 9.62 ms | 8.86 ms | 10.44 ms | 100.0% |

### Scenario: `validation`
POST `/validation` parsing and validating a nested payload (Blueprint vs Pydantic vs Dataclasses).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Flask | 51459.27 req/s | 0.00 ms | 0.00 ms | 0.00 ms | 0.0% |
| 2 | Litestar | 20009.95 req/s | 2.50 ms | 2.49 ms | 2.57 ms | 100.0% |
| 3 | FastAPI | 14740.25 req/s | 3.39 ms | 3.30 ms | 3.57 ms | 100.0% |
| 4 | Django | 3136.50 req/s | 15.97 ms | 14.84 ms | 17.84 ms | 100.0% |
| 5 | Starlette | 2347.77 req/s | 38.39 ms | 33.65 ms | 60.05 ms | 55.2% |
| 6 | Falcon | 2007.09 req/s | 24.96 ms | 25.62 ms | 31.58 ms | 100.0% |
| 7 | Sanic | 1455.77 req/s | 34.53 ms | 34.43 ms | 40.57 ms | 100.0% |
| 8 | Aquilia | 1157.78 req/s | 43.57 ms | 42.68 ms | 50.31 ms | 100.0% |
| 9 | Quart | 630.73 req/s | 79.72 ms | 75.21 ms | 96.20 ms | 100.0% |

### Scenario: `route_static`
GET `/route/static` matched against a large route table containing 500 placeholder routes. (Measures routing lookup performance).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Flask | 177819.65 req/s | 0.00 ms | 0.00 ms | 0.00 ms | 0.0% |
| 2 | Falcon | 60488.44 req/s | 0.83 ms | 0.82 ms | 0.86 ms | 100.0% |
| 3 | Starlette | 52712.63 req/s | 0.95 ms | 0.94 ms | 1.00 ms | 100.0% |
| 4 | Litestar | 43666.56 req/s | 1.14 ms | 1.14 ms | 1.21 ms | 100.0% |
| 5 | Sanic | 36473.00 req/s | 1.37 ms | 1.26 ms | 2.54 ms | 100.0% |
| 6 | Quart | 17726.25 req/s | 2.82 ms | 2.74 ms | 2.98 ms | 100.0% |
| 7 | Aquilia | 14316.53 req/s | 3.49 ms | 3.48 ms | 3.68 ms | 100.0% |
| 8 | FastAPI | 5786.30 req/s | 8.64 ms | 8.60 ms | 8.86 ms | 100.0% |
| 9 | Django | 5045.33 req/s | 9.92 ms | 9.15 ms | 11.63 ms | 100.0% |

### Scenario: `route_params`
GET `/route/params/<user_id>/orders/<order_id>` parsing path variables.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 58169.49 req/s | 0.86 ms | 0.86 ms | 0.89 ms | 100.0% |
| 2 | Starlette | 50415.94 req/s | 0.99 ms | 0.99 ms | 1.06 ms | 100.0% |
| 3 | Flask | 49702.45 req/s | 0.00 ms | 0.00 ms | 0.00 ms | 0.0% |
| 4 | Litestar | 39961.70 req/s | 1.25 ms | 1.25 ms | 1.31 ms | 100.0% |
| 5 | Sanic | 36190.44 req/s | 1.38 ms | 1.27 ms | 2.57 ms | 100.0% |
| 6 | Quart | 16770.15 req/s | 2.98 ms | 2.92 ms | 3.18 ms | 100.0% |
| 7 | Aquilia | 12532.60 req/s | 3.99 ms | 3.95 ms | 4.16 ms | 100.0% |
| 8 | FastAPI | 5344.94 req/s | 9.37 ms | 9.42 ms | 9.55 ms | 100.0% |
| 9 | Django | 5016.34 req/s | 9.98 ms | 9.25 ms | 11.76 ms | 100.0% |

### Scenario: `di`
GET `/di` resolving a nested dependency injection hierarchy (Leaf -> Mid -> Top).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Flask | 201065.58 req/s | 0.00 ms | 0.00 ms | 0.00 ms | 0.0% |
| 2 | Falcon | 60738.62 req/s | 0.82 ms | 0.82 ms | 0.85 ms | 100.0% |
| 3 | Starlette | 52523.32 req/s | 0.95 ms | 0.95 ms | 1.01 ms | 100.0% |
| 4 | Litestar | 43505.89 req/s | 1.15 ms | 1.15 ms | 1.21 ms | 100.0% |
| 5 | Sanic | 36702.01 req/s | 1.36 ms | 1.25 ms | 2.53 ms | 100.0% |
| 6 | Quart | 17780.16 req/s | 2.81 ms | 2.75 ms | 2.94 ms | 100.0% |
| 7 | Aquilia | 14338.07 req/s | 3.49 ms | 3.47 ms | 3.68 ms | 100.0% |
| 8 | Django | 5109.20 req/s | 9.80 ms | 9.16 ms | 11.55 ms | 100.0% |
| 9 | FastAPI | 4171.84 req/s | 12.01 ms | 11.84 ms | 14.19 ms | 100.0% |

### Scenario: `multipart`
POST `/body/multipart` uploading a 10KB text file. (Measures multipart parsing).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Flask | 147031.95 req/s | 0.00 ms | 0.00 ms | 0.00 ms | 0.0% |
| 2 | Sanic | 24450.32 req/s | 2.04 ms | 1.85 ms | 3.54 ms | 100.0% |
| 3 | Litestar | 23938.29 req/s | 2.09 ms | 2.08 ms | 2.16 ms | 100.0% |
| 4 | Falcon | 22706.24 req/s | 2.20 ms | 2.05 ms | 2.56 ms | 100.0% |
| 5 | Starlette | 17617.86 req/s | 2.84 ms | 2.84 ms | 2.91 ms | 100.0% |
| 6 | Quart | 7343.67 req/s | 6.81 ms | 6.75 ms | 7.04 ms | 100.0% |
| 7 | Aquilia | 6941.94 req/s | 7.20 ms | 7.15 ms | 7.34 ms | 100.0% |
| 8 | FastAPI | 4444.33 req/s | 11.26 ms | 11.29 ms | 11.54 ms | 100.0% |
| 9 | Django | 3857.13 req/s | 12.98 ms | 12.14 ms | 14.84 ms | 100.0% |

### Scenario: `stream`
GET `/response/stream` sending a 32KB chunked-encoded stream.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Flask | 204921.02 req/s | 0.00 ms | 0.00 ms | 0.00 ms | 0.0% |
| 2 | Falcon | 9337.00 req/s | 5.36 ms | 5.33 ms | 5.54 ms | 100.0% |
| 3 | Litestar | 6706.41 req/s | 7.46 ms | 7.42 ms | 7.68 ms | 100.0% |
| 4 | Starlette | 6454.99 req/s | 7.75 ms | 7.67 ms | 8.29 ms | 100.0% |
| 5 | Quart | 6401.41 req/s | 7.81 ms | 7.71 ms | 8.15 ms | 100.0% |
| 6 | Aquilia | 5622.66 req/s | 8.89 ms | 8.60 ms | 10.42 ms | 100.0% |
| 7 | FastAPI | 3019.17 req/s | 16.62 ms | 16.18 ms | 18.04 ms | 100.0% |
| 8 | Sanic | 2683.83 req/s | 18.67 ms | 19.12 ms | 25.23 ms | 100.0% |
| 9 | Django | 1180.94 req/s | 42.70 ms | 41.34 ms | 46.60 ms | 100.0% |

### Scenario: `middleware_0`
GET `/plaintext` with 0 custom middleware layers.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 69382.41 req/s | 0.72 ms | 0.75 ms | 0.85 ms | 100.0% |
| 2 | Starlette | 62681.62 req/s | 0.80 ms | 0.80 ms | 0.85 ms | 100.0% |
| 3 | Flask | 51770.88 req/s | 0.00 ms | 0.00 ms | 0.00 ms | 0.0% |
| 4 | Litestar | 43913.08 req/s | 1.14 ms | 1.14 ms | 1.19 ms | 100.0% |
| 5 | Sanic | 37476.01 req/s | 1.33 ms | 1.23 ms | 2.45 ms | 100.0% |
| 6 | FastAPI | 37023.11 req/s | 1.35 ms | 1.35 ms | 1.42 ms | 100.0% |
| 7 | Quart | 19003.70 req/s | 2.63 ms | 2.58 ms | 2.82 ms | 100.0% |
| 8 | Aquilia | 15343.75 req/s | 3.26 ms | 3.26 ms | 3.44 ms | 100.0% |
| 9 | Django | 5243.17 req/s | 9.55 ms | 8.94 ms | 11.42 ms | 100.0% |

### Scenario: `middleware_5`
GET `/plaintext` with 5 stacked custom middleware layers.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 67012.84 req/s | 0.75 ms | 0.76 ms | 0.85 ms | 100.0% |
| 2 | Starlette | 60990.66 req/s | 0.82 ms | 0.82 ms | 0.85 ms | 100.0% |
| 3 | Litestar | 42629.66 req/s | 1.17 ms | 1.17 ms | 1.23 ms | 100.0% |
| 4 | Sanic | 35659.52 req/s | 1.40 ms | 1.29 ms | 2.56 ms | 100.0% |
| 5 | Quart | 17752.14 req/s | 2.82 ms | 2.72 ms | 2.95 ms | 100.0% |
| 6 | Aquilia | 15606.95 req/s | 3.20 ms | 3.19 ms | 3.38 ms | 100.0% |
| 7 | Django | 4086.38 req/s | 12.25 ms | 11.61 ms | 14.21 ms | 100.0% |
| 8 | FastAPI | 3547.44 req/s | 14.12 ms | 13.69 ms | 15.54 ms | 100.0% |
| 9 | Flask | 2543.77 req/s | 19.57 ms | 12.18 ms | 55.99 ms | 100.0% |

### Scenario: `middleware_10`
GET `/plaintext` with 10 stacked custom middleware layers.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 65654.08 req/s | 0.76 ms | 0.76 ms | 0.82 ms | 100.0% |
| 2 | Starlette | 59589.76 req/s | 0.84 ms | 0.84 ms | 0.87 ms | 100.0% |
| 3 | Litestar | 42055.47 req/s | 1.19 ms | 1.19 ms | 1.25 ms | 100.0% |
| 4 | Sanic | 34192.03 req/s | 1.46 ms | 1.35 ms | 2.65 ms | 100.0% |
| 5 | Quart | 17339.65 req/s | 2.88 ms | 2.82 ms | 3.01 ms | 100.0% |
| 6 | Aquilia | 15557.52 req/s | 3.21 ms | 3.20 ms | 3.39 ms | 100.0% |
| 7 | Django | 4080.78 req/s | 12.27 ms | 11.62 ms | 14.27 ms | 100.0% |
| 8 | Flask | 2563.17 req/s | 19.51 ms | 12.04 ms | 51.75 ms | 100.0% |
| 9 | FastAPI | 1934.56 req/s | 25.97 ms | 24.54 ms | 27.23 ms | 100.0% |

## 3. Key Performance Insights
### Middleware Scaling Cost
This table summarizes how throughput scales as middleware layers are stacked (0 -> 5 -> 10 layers).

| Framework | 0 Layers QPS | 5 Layers QPS | 10 Layers QPS | Overhead (10 vs 0) |
| :--- | :--- | :--- | :--- | :--- |
| Aquilia | 15343.75 | 15606.95 | 15557.52 | -1.4% decrease |
| FastAPI | 37023.11 | 3547.44 | 1934.56 | 94.8% decrease |
| Starlette | 62681.62 | 60990.66 | 59589.76 | 4.9% decrease |
| Litestar | 43913.08 | 42629.66 | 42055.47 | 4.2% decrease |
| Falcon | 69382.41 | 67012.84 | 65654.08 | 5.4% decrease |
| Sanic | 37476.01 | 35659.52 | 34192.03 | 8.8% decrease |
| Quart | 19003.70 | 17752.14 | 17339.65 | 8.8% decrease |
| Flask | 51770.88 | 2543.77 | 2563.17 | 95.0% decrease |
| Django | 5243.17 | 4086.38 | 4080.78 | 22.2% decrease |

