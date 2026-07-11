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
| 1 | Aquilia | 214.80ms | ±4.04ms | 209.23ms | 223.36ms |
| 2 | Starlette | 263.22ms | ±7.02ms | 255.45ms | 274.71ms |
| 3 | Django | 293.02ms | ±3.86ms | 287.80ms | 297.84ms |
| 4 | Flask | 305.74ms | ±4.60ms | 301.07ms | 313.93ms |
| 5 | Falcon | 318.41ms | ±4.91ms | 311.84ms | 325.64ms |
| 6 | Sanic | 320.30ms | ±3.65ms | 314.07ms | 324.77ms |
| 7 | Quart | 337.95ms | ±2.72ms | 333.69ms | 341.88ms |
| 8 | FastAPI | 388.68ms | ±12.92ms | 374.65ms | 411.98ms |
| 9 | Litestar | 467.42ms | ±6.27ms | 460.77ms | 478.79ms |

## 2. HTTP Throughput and Latency Results
The tables below highlight framework performance metrics across various workload scenarios.

### Scenario: `plaintext`
GET `/plaintext` returning 'Hello, World!' (Measures raw HTTP parsing and serialization throughput).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 69743.11 req/s | 0.72 ms | 0.74 ms | 0.85 ms | 100.0% |
| 2 | Starlette | 63107.09 req/s | 0.79 ms | 0.79 ms | 0.83 ms | 100.0% |
| 3 | Litestar | 44539.10 req/s | 1.12 ms | 1.11 ms | 1.18 ms | 100.0% |
| 4 | FastAPI | 37482.28 req/s | 1.33 ms | 1.31 ms | 1.41 ms | 100.0% |
| 5 | Sanic | 36565.50 req/s | 1.37 ms | 1.25 ms | 2.50 ms | 100.0% |
| 6 | Quart | 19066.70 req/s | 2.62 ms | 2.55 ms | 2.74 ms | 100.0% |
| 7 | Aquilia | 17497.59 req/s | 2.85 ms | 2.84 ms | 2.95 ms | 100.0% |
| 8 | Django | 5075.29 req/s | 9.86 ms | 8.97 ms | 12.70 ms | 100.0% |
| 9 | Flask | 2783.42 req/s | 17.92 ms | 12.04 ms | 46.56 ms | 100.0% |

### Scenario: `json`
GET `/json` returning a small JSON dictionary. (Measures JSON encoding overhead).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 61114.76 req/s | 0.82 ms | 0.81 ms | 0.85 ms | 100.0% |
| 2 | Starlette | 56970.00 req/s | 0.88 ms | 0.86 ms | 0.93 ms | 100.0% |
| 3 | Litestar | 44110.16 req/s | 1.13 ms | 1.13 ms | 1.20 ms | 100.0% |
| 4 | Sanic | 35164.54 req/s | 1.42 ms | 1.28 ms | 2.64 ms | 100.0% |
| 5 | FastAPI | 33534.71 req/s | 1.49 ms | 1.48 ms | 1.56 ms | 100.0% |
| 6 | Quart | 17825.55 req/s | 2.80 ms | 2.73 ms | 2.97 ms | 100.0% |
| 7 | Aquilia | 16306.89 req/s | 3.07 ms | 3.05 ms | 3.17 ms | 100.0% |
| 8 | Django | 4703.42 req/s | 10.64 ms | 9.79 ms | 13.31 ms | 100.0% |
| 9 | Flask | 2052.53 req/s | 24.28 ms | 14.15 ms | 67.64 ms | 100.0% |

### Scenario: `json_large`
GET `/json/large` returning a nested 100KB JSON payload. (Measures large serialization performance).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Litestar | 6882.67 req/s | 7.27 ms | 7.12 ms | 7.32 ms | 100.0% |
| 2 | Sanic | 2161.98 req/s | 23.17 ms | 22.44 ms | 24.74 ms | 100.0% |
| 3 | Starlette | 1632.10 req/s | 30.71 ms | 29.72 ms | 31.16 ms | 100.0% |
| 4 | Falcon | 1574.40 req/s | 31.85 ms | 30.77 ms | 32.81 ms | 100.0% |
| 5 | Django | 1246.44 req/s | 40.26 ms | 39.13 ms | 44.06 ms | 100.0% |
| 6 | Quart | 1238.26 req/s | 40.53 ms | 40.28 ms | 41.48 ms | 100.0% |
| 7 | Flask | 802.75 req/s | 62.56 ms | 68.36 ms | 76.21 ms | 100.0% |
| 8 | FastAPI | 203.30 req/s | 222.22 ms | 159.37 ms | 286.07 ms | 100.0% |
| 9 | Aquilia | 199.84 req/s | 226.12 ms | 169.81 ms | 297.99 ms | 100.0% |

### Scenario: `db_single`
GET `/db` executing 1 SQL query. (Measures single database retrieval latency).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 6299.94 req/s | 7.94 ms | 7.87 ms | 9.40 ms | 100.0% |
| 2 | Litestar | 5897.86 req/s | 8.48 ms | 8.39 ms | 10.05 ms | 100.0% |
| 3 | Starlette | 5755.15 req/s | 8.69 ms | 8.16 ms | 12.88 ms | 100.0% |
| 4 | Sanic | 5569.08 req/s | 8.98 ms | 8.72 ms | 11.13 ms | 100.0% |
| 5 | FastAPI | 5342.89 req/s | 9.36 ms | 8.94 ms | 10.92 ms | 100.0% |
| 6 | Quart | 4742.33 req/s | 10.55 ms | 10.39 ms | 12.38 ms | 100.0% |
| 7 | Aquilia | 4313.25 req/s | 11.60 ms | 11.13 ms | 12.31 ms | 100.0% |
| 8 | Django | 3662.96 req/s | 13.66 ms | 12.70 ms | 18.00 ms | 100.0% |
| 9 | Flask | 1982.46 req/s | 25.32 ms | 20.33 ms | 57.64 ms | 99.9% |

### Scenario: `db_queries`
GET `/queries` executing 5 random SQL queries sequentially.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 2608.32 req/s | 19.20 ms | 19.10 ms | 22.22 ms | 100.0% |
| 2 | Django | 2604.14 req/s | 19.22 ms | 18.44 ms | 28.30 ms | 100.0% |
| 3 | Starlette | 2562.81 req/s | 19.54 ms | 19.36 ms | 23.00 ms | 100.0% |
| 4 | Litestar | 2485.11 req/s | 20.15 ms | 20.00 ms | 23.44 ms | 100.0% |
| 5 | Sanic | 2409.38 req/s | 20.78 ms | 20.55 ms | 24.35 ms | 100.0% |
| 6 | FastAPI | 2331.34 req/s | 21.48 ms | 21.35 ms | 25.03 ms | 100.0% |
| 7 | Quart | 2236.79 req/s | 22.39 ms | 22.26 ms | 26.10 ms | 100.0% |
| 8 | Flask | 2091.75 req/s | 24.84 ms | 22.61 ms | 54.11 ms | 96.1% |
| 9 | Aquilia | 1299.00 req/s | 38.61 ms | 38.44 ms | 41.37 ms | 100.0% |

### Scenario: `db_updates`
GET `/updates` executing 5 select-update SQL statements under a database transaction.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Django | 3070.54 req/s | 16.31 ms | 12.03 ms | 44.30 ms | 98.7% |
| 2 | Starlette | 1596.12 req/s | 27.81 ms | 0.69 ms | 87.30 ms | 100.0% |
| 3 | Falcon | 1595.57 req/s | 28.62 ms | 0.68 ms | 107.66 ms | 100.0% |
| 4 | Litestar | 1572.98 req/s | 28.10 ms | 0.71 ms | 86.91 ms | 100.0% |
| 5 | Sanic | 1547.07 req/s | 28.86 ms | 0.70 ms | 85.17 ms | 100.0% |
| 6 | FastAPI | 1536.64 req/s | 29.35 ms | 1.80 ms | 89.44 ms | 100.0% |
| 7 | Quart | 1528.32 req/s | 28.55 ms | 1.84 ms | 84.38 ms | 100.0% |
| 8 | Flask | 1404.68 req/s | 35.72 ms | 22.47 ms | 61.26 ms | 100.0% |
| 9 | Aquilia | 683.92 req/s | 73.63 ms | 71.30 ms | 86.90 ms | 100.0% |

### Scenario: `fortunes`
GET `/fortunes` fetching fortunes from database, adding a custom fortune, sorting, and rendering to HTML via Jinja2.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Aquilia | 3505.83 req/s | 14.28 ms | 14.17 ms | 15.22 ms | 100.0% |
| 2 | Falcon | 2831.65 req/s | 17.68 ms | 17.63 ms | 22.46 ms | 100.0% |
| 3 | Litestar | 2755.79 req/s | 18.16 ms | 18.07 ms | 22.90 ms | 100.0% |
| 4 | Starlette | 2753.78 req/s | 18.18 ms | 18.12 ms | 22.84 ms | 100.0% |
| 5 | Django | 2660.79 req/s | 18.89 ms | 18.22 ms | 27.79 ms | 99.5% |
| 6 | FastAPI | 2655.61 req/s | 18.86 ms | 18.68 ms | 23.88 ms | 100.0% |
| 7 | Sanic | 2613.46 req/s | 19.16 ms | 19.00 ms | 24.03 ms | 100.0% |
| 8 | Quart | 2440.56 req/s | 20.52 ms | 20.37 ms | 25.60 ms | 100.0% |
| 9 | Flask | 2016.25 req/s | 24.75 ms | 21.05 ms | 52.18 ms | 99.7% |

### Scenario: `cached`
GET `/cached` retrieving 5 random items from memory cache with fallback to DB.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 48437.25 req/s | 1.03 ms | 1.03 ms | 1.08 ms | 100.0% |
| 2 | Starlette | 42660.58 req/s | 1.17 ms | 1.17 ms | 1.23 ms | 100.0% |
| 3 | Litestar | 35858.34 req/s | 1.39 ms | 1.39 ms | 1.46 ms | 100.0% |
| 4 | Sanic | 27816.67 req/s | 1.80 ms | 1.59 ms | 3.15 ms | 100.0% |
| 5 | FastAPI | 18997.56 req/s | 2.63 ms | 2.62 ms | 2.71 ms | 100.0% |
| 6 | Quart | 15000.34 req/s | 3.33 ms | 3.18 ms | 3.79 ms | 100.0% |
| 7 | Aquilia | 13149.87 req/s | 3.80 ms | 3.80 ms | 3.91 ms | 100.0% |
| 8 | Django | 4743.38 req/s | 10.54 ms | 9.82 ms | 12.41 ms | 100.0% |
| 9 | Flask | 1927.41 req/s | 25.99 ms | 12.59 ms | 80.18 ms | 100.0% |

### Scenario: `validation`
POST `/validation` parsing and validating a nested payload (Contract vs Pydantic vs Dataclasses).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Litestar | 19771.01 req/s | 2.53 ms | 2.52 ms | 2.60 ms | 100.0% |
| 2 | FastAPI | 14885.50 req/s | 3.36 ms | 3.26 ms | 3.53 ms | 100.0% |
| 3 | Django | 2860.35 req/s | 17.51 ms | 15.35 ms | 18.51 ms | 100.0% |
| 4 | Starlette | 1801.34 req/s | 49.88 ms | 46.27 ms | 80.70 ms | 55.5% |
| 5 | Falcon | 1514.63 req/s | 33.02 ms | 33.77 ms | 40.73 ms | 100.0% |
| 6 | Aquilia | 1094.83 req/s | 45.76 ms | 44.66 ms | 55.67 ms | 100.0% |
| 7 | Sanic | 1011.13 req/s | 49.55 ms | 51.59 ms | 58.41 ms | 100.0% |
| 8 | Quart | 496.47 req/s | 101.05 ms | 95.75 ms | 119.94 ms | 100.0% |
| 9 | Flask | 413.94 req/s | 121.87 ms | 154.24 ms | 198.31 ms | 100.0% |

### Scenario: `route_static`
GET `/route/static` matched against a large route table containing 500 placeholder routes. (Measures routing lookup performance).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 59663.43 req/s | 0.84 ms | 0.83 ms | 0.90 ms | 100.0% |
| 2 | Starlette | 52471.41 req/s | 0.95 ms | 0.95 ms | 1.01 ms | 100.0% |
| 3 | Litestar | 43680.47 req/s | 1.14 ms | 1.14 ms | 1.21 ms | 100.0% |
| 4 | Sanic | 35567.65 req/s | 1.40 ms | 1.28 ms | 2.61 ms | 100.0% |
| 5 | Quart | 17381.69 req/s | 2.88 ms | 2.76 ms | 3.10 ms | 100.0% |
| 6 | Aquilia | 16161.87 req/s | 3.09 ms | 3.08 ms | 3.20 ms | 100.0% |
| 7 | FastAPI | 5906.49 req/s | 8.47 ms | 8.29 ms | 9.57 ms | 100.0% |
| 8 | Django | 5056.10 req/s | 9.90 ms | 9.23 ms | 11.63 ms | 100.0% |
| 9 | Flask | 1572.61 req/s | 31.53 ms | 14.74 ms | 98.20 ms | 100.0% |

### Scenario: `route_params`
GET `/route/params/<user_id>/orders/<order_id>` parsing path variables.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 57930.78 req/s | 0.86 ms | 0.86 ms | 0.95 ms | 100.0% |
| 2 | Starlette | 50085.72 req/s | 1.00 ms | 1.00 ms | 1.05 ms | 100.0% |
| 3 | Litestar | 39745.31 req/s | 1.26 ms | 1.26 ms | 1.31 ms | 100.0% |
| 4 | Sanic | 35627.78 req/s | 1.40 ms | 1.29 ms | 2.63 ms | 100.0% |
| 5 | Quart | 16601.09 req/s | 3.01 ms | 2.93 ms | 3.16 ms | 100.0% |
| 6 | Aquilia | 13965.99 req/s | 3.58 ms | 3.57 ms | 3.68 ms | 100.0% |
| 7 | FastAPI | 5472.14 req/s | 9.14 ms | 9.14 ms | 9.52 ms | 100.0% |
| 8 | Django | 4960.14 req/s | 10.09 ms | 9.32 ms | 11.92 ms | 100.0% |
| 9 | Flask | 1612.46 req/s | 31.15 ms | 15.17 ms | 81.67 ms | 100.0% |

### Scenario: `di`
GET `/di` resolving a nested dependency injection hierarchy (Leaf -> Mid -> Top).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 59576.14 req/s | 0.84 ms | 0.82 ms | 0.93 ms | 100.0% |
| 2 | Starlette | 51758.65 req/s | 0.97 ms | 0.96 ms | 1.02 ms | 100.0% |
| 3 | Litestar | 43362.84 req/s | 1.15 ms | 1.15 ms | 1.21 ms | 100.0% |
| 4 | Sanic | 35424.51 req/s | 1.41 ms | 1.27 ms | 2.61 ms | 100.0% |
| 5 | Quart | 18000.60 req/s | 2.78 ms | 2.71 ms | 2.92 ms | 100.0% |
| 6 | Aquilia | 16089.85 req/s | 3.11 ms | 3.10 ms | 3.20 ms | 100.0% |
| 7 | Django | 5043.16 req/s | 9.91 ms | 9.23 ms | 11.68 ms | 100.0% |
| 8 | FastAPI | 4228.99 req/s | 11.83 ms | 11.47 ms | 14.34 ms | 100.0% |
| 9 | Flask | 1648.90 req/s | 30.20 ms | 12.47 ms | 93.73 ms | 100.0% |

### Scenario: `multipart`
POST `/body/multipart` uploading a 10KB text file. (Measures multipart parsing).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Sanic | 23806.74 req/s | 2.10 ms | 1.89 ms | 3.68 ms | 100.0% |
| 2 | Litestar | 23375.12 req/s | 2.14 ms | 2.13 ms | 2.21 ms | 100.0% |
| 3 | Falcon | 22660.60 req/s | 2.21 ms | 2.06 ms | 2.54 ms | 100.0% |
| 4 | Starlette | 16928.86 req/s | 2.95 ms | 2.89 ms | 3.36 ms | 100.0% |
| 5 | Aquilia | 7370.57 req/s | 6.78 ms | 6.70 ms | 7.14 ms | 100.0% |
| 6 | Quart | 7003.39 req/s | 7.14 ms | 6.89 ms | 7.96 ms | 100.0% |
| 7 | FastAPI | 4564.01 req/s | 10.97 ms | 11.00 ms | 11.30 ms | 100.0% |
| 8 | Django | 3484.19 req/s | 14.34 ms | 12.80 ms | 20.57 ms | 100.0% |
| 9 | Flask | 1923.84 req/s | 25.90 ms | 16.48 ms | 69.44 ms | 100.0% |

### Scenario: `stream`
GET `/response/stream` sending a 32KB chunked-encoded stream.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 8980.16 req/s | 5.57 ms | 5.46 ms | 6.18 ms | 100.0% |
| 2 | Litestar | 6521.06 req/s | 7.67 ms | 7.53 ms | 8.03 ms | 100.0% |
| 3 | Starlette | 6453.93 req/s | 7.75 ms | 7.71 ms | 8.01 ms | 100.0% |
| 4 | Quart | 6214.42 req/s | 8.05 ms | 7.79 ms | 9.19 ms | 100.0% |
| 5 | Aquilia | 6071.55 req/s | 8.24 ms | 8.12 ms | 8.89 ms | 100.0% |
| 6 | FastAPI | 3142.24 req/s | 15.95 ms | 15.69 ms | 17.20 ms | 100.0% |
| 7 | Sanic | 1712.01 req/s | 29.20 ms | 29.88 ms | 41.01 ms | 100.0% |
| 8 | Django | 1164.88 req/s | 43.06 ms | 41.57 ms | 48.95 ms | 100.0% |
| 9 | Flask | 31.38 req/s | 1789.50 ms | 2321.11 ms | 2347.51 ms | 100.0% |

### Scenario: `middleware_0`
GET `/plaintext` with 0 custom middleware layers.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 63325.45 req/s | 0.79 ms | 0.79 ms | 1.03 ms | 100.0% |
| 2 | Starlette | 62708.01 req/s | 0.80 ms | 0.81 ms | 0.87 ms | 100.0% |
| 3 | Litestar | 44205.20 req/s | 1.13 ms | 1.13 ms | 1.20 ms | 100.0% |
| 4 | FastAPI | 37624.74 req/s | 1.33 ms | 1.32 ms | 1.39 ms | 100.0% |
| 5 | Sanic | 36384.09 req/s | 1.37 ms | 1.25 ms | 2.52 ms | 100.0% |
| 6 | Quart | 18744.15 req/s | 2.67 ms | 2.60 ms | 2.78 ms | 100.0% |
| 7 | Aquilia | 17265.57 req/s | 2.89 ms | 2.89 ms | 2.98 ms | 100.0% |
| 8 | Django | 4986.57 req/s | 10.03 ms | 9.18 ms | 12.46 ms | 100.0% |
| 9 | Flask | 845.72 req/s | 59.11 ms | 18.08 ms | 105.52 ms | 100.0% |

### Scenario: `middleware_5`
GET `/plaintext` with 5 stacked custom middleware layers.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 67216.60 req/s | 0.74 ms | 0.76 ms | 0.86 ms | 100.0% |
| 2 | Starlette | 61244.99 req/s | 0.82 ms | 0.82 ms | 0.88 ms | 100.0% |
| 3 | Litestar | 41754.93 req/s | 1.20 ms | 1.17 ms | 1.29 ms | 100.0% |
| 4 | Sanic | 34511.36 req/s | 1.45 ms | 1.32 ms | 2.65 ms | 100.0% |
| 5 | Aquilia | 17606.46 req/s | 2.84 ms | 2.83 ms | 2.93 ms | 100.0% |
| 6 | Quart | 17373.80 req/s | 2.88 ms | 2.78 ms | 2.94 ms | 100.0% |
| 7 | Django | 4051.49 req/s | 12.35 ms | 11.61 ms | 14.64 ms | 100.0% |
| 8 | FastAPI | 3524.41 req/s | 14.20 ms | 13.67 ms | 15.77 ms | 100.0% |
| 9 | Flask | 1362.76 req/s | 36.81 ms | 13.88 ms | 107.86 ms | 100.0% |

### Scenario: `middleware_10`
GET `/plaintext` with 10 stacked custom middleware layers.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 66374.53 req/s | 0.75 ms | 0.76 ms | 0.85 ms | 100.0% |
| 2 | Starlette | 59764.68 req/s | 0.84 ms | 0.83 ms | 0.87 ms | 100.0% |
| 3 | Litestar | 42768.72 req/s | 1.17 ms | 1.16 ms | 1.24 ms | 100.0% |
| 4 | Sanic | 33327.13 req/s | 1.50 ms | 1.35 ms | 2.69 ms | 100.0% |
| 5 | Aquilia | 17465.96 req/s | 2.86 ms | 2.85 ms | 2.95 ms | 100.0% |
| 6 | Quart | 16929.40 req/s | 2.95 ms | 2.85 ms | 3.16 ms | 100.0% |
| 7 | Django | 4023.28 req/s | 12.43 ms | 11.66 ms | 14.65 ms | 100.0% |
| 8 | FastAPI | 1934.75 req/s | 25.90 ms | 24.43 ms | 28.60 ms | 100.0% |
| 9 | Flask | 1442.93 req/s | 34.71 ms | 13.60 ms | 102.98 ms | 100.0% |

## 3. Key Performance Insights
### Middleware Scaling Cost
This table summarizes how throughput scales as middleware layers are stacked (0 -> 5 -> 10 layers).

| Framework | 0 Layers QPS | 5 Layers QPS | 10 Layers QPS | Overhead (10 vs 0) |
| :--- | :--- | :--- | :--- | :--- |
| Aquilia | 17265.57 | 17606.46 | 17465.96 | -1.2% decrease |
| FastAPI | 37624.74 | 3524.41 | 1934.75 | 94.9% decrease |
| Starlette | 62708.01 | 61244.99 | 59764.68 | 4.7% decrease |
| Litestar | 44205.20 | 41754.93 | 42768.72 | 3.2% decrease |
| Falcon | 63325.45 | 67216.60 | 66374.53 | -4.8% decrease |
| Sanic | 36384.09 | 34511.36 | 33327.13 | 8.4% decrease |
| Quart | 18744.15 | 17373.80 | 16929.40 | 9.7% decrease |
| Flask | 845.72 | 1362.76 | 1442.93 | -70.6% decrease |
| Django | 4986.57 | 4051.49 | 4023.28 | 19.3% decrease |

