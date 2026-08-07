# Aquilia Professional Web Framework Benchmarks

This document presents the objective, reproducible, and statistically valid benchmarks comparing the performance characteristics of Aquilia against major Python web frameworks.

## Benchmark Parameters
- **Load Testing Utility**: `oha` (Rust-based HTTP/1.1 load generator)
- **Concurrency Level**: `50` simultaneous connections
- **Duration**: `5s` per endpoint run
- **Server Environment**: Python 3.11.15 (CPython) — Darwin arm64 — Uvicorn, single worker — JSON backend: `aquilia._json` — `_core` present — `_dataengine` present — `_json` present
- **Database Engine**: SQLite 3 (Standard 10,000-row TechEmpower Schema)
- **Success Rate**: fraction of responses with a 2xx/3xx status. Endpoints failing a single-request preflight are reported as 0 and excluded from ranking.

> **Provenance note.** All scenarios below except `validation` were measured
> *before* the native validation engine was connected. `_native_plan.py`
> compiled a `FieldPlan` per contract but nothing invoked it, so contract
> validation ran the pure-Python field loop while this header printed
> `` `_dataengine` present ``. The engine is now wired into `Sigil.validate`.
>
> The `validation` row is from a re-run after that fix. Scenarios touching
> contracts or ORM hydration should be treated as provisional until the full
> suite is re-run in one pass.

## 1. Cold Startup & Importing Overhead
Measures the pure framework importing and initialization time. Fast cold start times are critical for Serverless deployments and developer container boot-ups.

| Rank | Framework | Mean Startup (ms) | StdDev (ms) | Min (ms) | Max (ms) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Starlette | 180.89ms | ±1.97ms | 178.39ms | 183.31ms |
| 2 | Django | 219.64ms | ±3.35ms | 214.81ms | 224.70ms |
| 3 | Flask | 220.69ms | ±2.94ms | 216.06ms | 223.33ms |
| 4 | Aquilia | 233.85ms | ±3.23ms | 229.82ms | 238.71ms |
| 5 | Falcon | 234.04ms | ±2.76ms | 230.82ms | 237.86ms |
| 6 | Quart | 249.02ms | ±3.37ms | 245.55ms | 254.47ms |
| 7 | Sanic | 255.12ms | ±3.60ms | 250.57ms | 261.56ms |
| 8 | FastAPI | 302.26ms | ±3.65ms | 297.63ms | 307.13ms |
| 9 | Litestar | 382.68ms | ±3.17ms | 377.38ms | 386.57ms |

## 2. HTTP Throughput and Latency Results
The tables below highlight framework performance metrics across various workload scenarios.

### Scenario: `plaintext`
GET `/plaintext` returning 'Hello, World!' (Measures raw HTTP parsing and serialization throughput).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 69826.11 req/s | 0.71 ms | 0.78 ms | 0.88 ms | 100.0% |
| 2 | Starlette | 58748.74 req/s | 0.85 ms | 0.85 ms | 0.88 ms | 100.0% |
| 3 | Litestar | 43211.64 req/s | 1.16 ms | 1.15 ms | 1.22 ms | 100.0% |
| 4 | Aquilia | 34222.54 req/s | 1.46 ms | 1.44 ms | 1.53 ms | 100.0% |
| 5 | Sanic | 34217.59 req/s | 1.46 ms | 1.23 ms | 1.90 ms | 100.0% |
| 6 | FastAPI | 32914.32 req/s | 1.52 ms | 1.51 ms | 1.58 ms | 100.0% |
| 7 | Quart | 16548.93 req/s | 3.02 ms | 2.74 ms | 2.93 ms | 100.0% |
| 8 | Django | 3845.35 req/s | 13.02 ms | 11.55 ms | 27.07 ms | 100.0% |
| 9 | Flask | 2466.27 req/s | 20.28 ms | 25.83 ms | 47.23 ms | 56.2% |

### Scenario: `json`
GET `/json` returning a small JSON dictionary. (Measures JSON encoding overhead).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 59832.81 req/s | 0.83 ms | 0.83 ms | 0.87 ms | 100.0% |
| 2 | Starlette | 53942.80 req/s | 0.93 ms | 0.92 ms | 0.97 ms | 100.0% |
| 3 | Litestar | 41811.27 req/s | 1.19 ms | 1.18 ms | 1.25 ms | 100.0% |
| 4 | Aquilia | 34504.55 req/s | 1.45 ms | 1.44 ms | 1.52 ms | 100.0% |
| 5 | Sanic | 33390.11 req/s | 1.50 ms | 1.26 ms | 1.95 ms | 100.0% |
| 6 | FastAPI | 29234.40 req/s | 1.71 ms | 1.70 ms | 1.78 ms | 100.0% |
| 7 | Quart | 15602.76 req/s | 3.20 ms | 2.92 ms | 3.17 ms | 100.0% |
| 8 | Django | 3676.89 req/s | 13.60 ms | 12.69 ms | 27.67 ms | 100.0% |
| 9 | Flask | 3570.60 req/s | 14.00 ms | 18.35 ms | 25.09 ms | 67.0% |

### Scenario: `json_large`
GET `/json/large` returning a nested 100KB JSON payload. (Measures large serialization performance).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Litestar | 6692.46 req/s | 7.47 ms | 7.29 ms | 7.49 ms | 100.0% |
| 2 | Aquilia | 4542.18 req/s | 11.01 ms | 10.67 ms | 11.36 ms | 100.0% |
| 3 | Sanic | 2322.10 req/s | 21.56 ms | 20.83 ms | 22.08 ms | 100.0% |
| 4 | Starlette | 1332.03 req/s | 37.65 ms | 36.84 ms | 37.17 ms | 100.0% |
| 5 | Falcon | 1304.08 req/s | 38.46 ms | 37.74 ms | 38.20 ms | 100.0% |
| 6 | Quart | 1150.36 req/s | 43.61 ms | 43.33 ms | 43.82 ms | 100.0% |
| 7 | Flask | 984.31 req/s | 51.00 ms | 50.73 ms | 66.07 ms | 94.7% |
| 8 | Django | 981.80 req/s | 51.15 ms | 50.31 ms | 65.54 ms | 100.0% |
| 9 | FastAPI | 171.94 req/s | 240.40 ms | 183.05 ms | 327.80 ms | 100.0% |

### Scenario: `db_single`
GET `/db` executing 1 SQL query. (Measures single database retrieval latency).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Aquilia | 17286.29 req/s | 2.89 ms | 2.70 ms | 4.08 ms | 100.0% |
| 2 | Falcon | 6696.93 req/s | 7.46 ms | 7.38 ms | 8.70 ms | 100.0% |
| 3 | Starlette | 6164.71 req/s | 8.11 ms | 7.96 ms | 9.44 ms | 100.0% |
| 4 | Litestar | 6082.51 req/s | 8.22 ms | 8.08 ms | 9.47 ms | 100.0% |
| 5 | Sanic | 5720.67 req/s | 8.74 ms | 8.44 ms | 10.24 ms | 100.0% |
| 6 | FastAPI | 5411.45 req/s | 9.24 ms | 8.92 ms | 10.81 ms | 100.0% |
| 7 | Quart | 4827.30 req/s | 10.36 ms | 10.01 ms | 11.86 ms | 100.0% |
| 8 | Flask | 3116.04 req/s | 16.06 ms | 19.51 ms | 25.56 ms | 75.2% |
| 9 | Django | 1301.00 req/s | 38.55 ms | 31.35 ms | 54.38 ms | 100.0% |

### Scenario: `db_queries`
GET `/queries` executing 5 random SQL queries sequentially.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Aquilia | 7114.24 req/s | 7.02 ms | 5.60 ms | 14.96 ms | 100.0% |
| 2 | Falcon | 2936.94 req/s | 17.04 ms | 16.88 ms | 19.66 ms | 100.0% |
| 3 | Flask | 2860.97 req/s | 17.48 ms | 20.95 ms | 26.92 ms | 77.8% |
| 4 | Starlette | 2681.46 req/s | 18.66 ms | 18.55 ms | 21.26 ms | 100.0% |
| 5 | Litestar | 2669.13 req/s | 18.75 ms | 18.62 ms | 21.30 ms | 100.0% |
| 6 | Sanic | 2548.61 req/s | 19.64 ms | 19.30 ms | 22.37 ms | 100.0% |
| 7 | FastAPI | 2492.94 req/s | 20.08 ms | 19.85 ms | 23.03 ms | 100.0% |
| 8 | Quart | 2367.91 req/s | 21.14 ms | 20.94 ms | 23.95 ms | 100.0% |
| 9 | Django | 914.72 req/s | 54.93 ms | 52.29 ms | 72.32 ms | 100.0% |

### Scenario: `db_updates`
GET `/updates` executing 5 select-update SQL statements under a database transaction.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Flask | 4033.35 req/s | 33.79 ms | 21.77 ms | 47.93 ms | 86.9% |
| 2 | Aquilia | 1909.41 req/s | 26.23 ms | 25.91 ms | 28.00 ms | 100.0% |
| 3 | Falcon | 1593.90 req/s | 27.94 ms | 0.68 ms | 82.68 ms | 100.0% |
| 4 | Starlette | 1580.52 req/s | 26.85 ms | 0.70 ms | 87.53 ms | 100.0% |
| 5 | Litestar | 1569.40 req/s | 27.62 ms | 0.71 ms | 84.21 ms | 100.0% |
| 6 | Sanic | 1558.42 req/s | 27.84 ms | 0.73 ms | 83.05 ms | 100.0% |
| 7 | FastAPI | 1530.39 req/s | 28.02 ms | 1.83 ms | 83.44 ms | 100.0% |
| 8 | Quart | 1513.96 req/s | 29.36 ms | 1.93 ms | 87.34 ms | 100.0% |
| 9 | Django | 965.49 req/s | 52.07 ms | 47.54 ms | 85.92 ms | 17.2% |

### Scenario: `fortunes`
GET `/fortunes` fetching fortunes from database, adding a custom fortune, sorting, and rendering to HTML via Jinja2.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Aquilia | 5211.78 req/s | 9.60 ms | 9.48 ms | 10.49 ms | 100.0% |
| 2 | Flask | 3387.23 req/s | 19.55 ms | 20.55 ms | 28.37 ms | 79.4% |
| 3 | Starlette | 2994.96 req/s | 16.70 ms | 16.34 ms | 21.88 ms | 100.0% |
| 4 | Litestar | 2967.35 req/s | 16.86 ms | 16.39 ms | 21.30 ms | 100.0% |
| 5 | Falcon | 2952.53 req/s | 16.94 ms | 16.79 ms | 21.75 ms | 100.0% |
| 6 | Sanic | 2707.83 req/s | 18.48 ms | 18.10 ms | 23.33 ms | 100.0% |
| 7 | FastAPI | 2614.33 req/s | 19.14 ms | 18.60 ms | 24.81 ms | 100.0% |
| 8 | Quart | 2511.69 req/s | 19.93 ms | 19.58 ms | 24.37 ms | 100.0% |
| 9 | Django | 1139.93 req/s | 44.02 ms | 41.04 ms | 65.51 ms | 100.0% |

### Scenario: `cached`
GET `/cached` retrieving 5 random items from memory cache with fallback to DB.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 46513.75 req/s | 1.07 ms | 1.07 ms | 1.14 ms | 100.0% |
| 2 | Starlette | 38696.61 req/s | 1.29 ms | 1.29 ms | 1.36 ms | 100.0% |
| 3 | Litestar | 33763.64 req/s | 1.48 ms | 1.47 ms | 1.55 ms | 100.0% |
| 4 | Aquilia | 27464.67 req/s | 1.82 ms | 1.80 ms | 1.89 ms | 100.0% |
| 5 | Sanic | 26119.13 req/s | 1.91 ms | 1.62 ms | 2.29 ms | 100.0% |
| 6 | FastAPI | 16886.47 req/s | 2.96 ms | 2.95 ms | 3.03 ms | 100.0% |
| 7 | Quart | 13831.71 req/s | 3.61 ms | 3.33 ms | 3.59 ms | 100.0% |
| 8 | Flask | 3460.46 req/s | 14.46 ms | 15.23 ms | 29.74 ms | 73.7% |
| 9 | Django | 3256.33 req/s | 15.37 ms | 14.07 ms | 30.51 ms | 100.0% |

### Scenario: `validation`
POST `/validation` parsing and validating a nested payload (Contract vs Pydantic vs Dataclasses).

**Re-measured after the native `FieldPlan` was wired into `Sigil.validate`.**
Aquilia moved from 16066.99 req/s to 18355.03 req/s (+14.2%) on the same
payload. In isolation the same validation is 2.3x faster
(`benchmarks/engine/microbench_contracts.py`); the HTTP delta is smaller
because transport and the rest of the pipeline dominate the request.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 44412.97 req/s | 1.12 ms | 1.12 ms | 1.19 ms | 100.0% |
| 2 | Starlette | 39355.20 req/s | 1.27 ms | 1.27 ms | 1.34 ms | 100.0% |
| 3 | Litestar | 27787.86 req/s | 1.80 ms | 1.79 ms | 1.87 ms | 100.0% |
| 4 | Sanic | 26805.72 req/s | 1.86 ms | 1.56 ms | 2.33 ms | 100.0% |
| 5 | FastAPI | 19790.29 req/s | 2.53 ms | 2.51 ms | 2.61 ms | 100.0% |
| 6 | Aquilia | 18355.03 req/s | 2.72 ms | 2.71 ms | 2.81 ms | 100.0% |
| 7 | Quart | 13634.06 req/s | 3.67 ms | 3.47 ms | 3.69 ms | 100.0% |
| 8 | Flask | 4859.29 req/s | 10.29 ms | 12.31 ms | 15.08 ms | 78.8% |
| 9 | Django | 3535.22 req/s | 14.16 ms | 13.17 ms | 28.08 ms | 100.0% |

### Scenario: `route_static`
GET `/route/static` matched against a large route table containing 500 placeholder routes. (Measures routing lookup performance).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 58420.40 req/s | 0.85 ms | 0.85 ms | 0.89 ms | 100.0% |
| 2 | Starlette | 48647.25 req/s | 1.03 ms | 1.02 ms | 1.08 ms | 100.0% |
| 3 | Litestar | 41414.38 req/s | 1.21 ms | 1.20 ms | 1.27 ms | 100.0% |
| 4 | Sanic | 33243.41 req/s | 1.50 ms | 1.27 ms | 1.96 ms | 100.0% |
| 5 | Aquilia | 33051.47 req/s | 1.51 ms | 1.49 ms | 1.58 ms | 100.0% |
| 6 | Quart | 15071.25 req/s | 3.32 ms | 2.99 ms | 3.22 ms | 100.0% |
| 7 | FastAPI | 4150.91 req/s | 12.05 ms | 12.07 ms | 12.33 ms | 100.0% |
| 8 | Django | 3515.68 req/s | 14.23 ms | 12.40 ms | 30.07 ms | 100.0% |
| 9 | Flask | 3294.69 req/s | 16.42 ms | 13.00 ms | 38.45 ms | 76.4% |

### Scenario: `route_params`
GET `/route/params/<user_id>/orders/<order_id>` parsing path variables.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 55976.45 req/s | 0.89 ms | 0.89 ms | 0.93 ms | 100.0% |
| 2 | Starlette | 46075.94 req/s | 1.08 ms | 1.08 ms | 1.14 ms | 100.0% |
| 3 | Litestar | 38020.38 req/s | 1.31 ms | 1.31 ms | 1.38 ms | 100.0% |
| 4 | Sanic | 32858.81 req/s | 1.52 ms | 1.28 ms | 1.99 ms | 100.0% |
| 5 | Aquilia | 32294.09 req/s | 1.55 ms | 1.50 ms | 1.65 ms | 100.0% |
| 6 | Quart | 14608.92 req/s | 3.42 ms | 3.11 ms | 3.37 ms | 100.0% |
| 7 | FastAPI | 3912.66 req/s | 12.78 ms | 12.73 ms | 13.03 ms | 100.0% |
| 8 | Django | 3457.33 req/s | 14.47 ms | 13.38 ms | 29.34 ms | 100.0% |
| 9 | Flask | 2934.39 req/s | 17.05 ms | 12.86 ms | 41.04 ms | 77.5% |

### Scenario: `di`
GET `/di` resolving a nested dependency injection hierarchy (Leaf -> Mid -> Top).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 59447.46 req/s | 0.84 ms | 0.84 ms | 0.91 ms | 100.0% |
| 2 | Starlette | 47252.89 req/s | 1.06 ms | 1.06 ms | 1.11 ms | 100.0% |
| 3 | Litestar | 41657.75 req/s | 1.20 ms | 1.20 ms | 1.26 ms | 100.0% |
| 4 | Sanic | 33355.85 req/s | 1.50 ms | 1.26 ms | 1.96 ms | 100.0% |
| 5 | Aquilia | 33319.24 req/s | 1.50 ms | 1.49 ms | 1.57 ms | 100.0% |
| 6 | Quart | 15595.98 req/s | 3.20 ms | 2.90 ms | 3.13 ms | 100.0% |
| 7 | Flask | 4327.68 req/s | 27.55 ms | 11.63 ms | 46.29 ms | 88.4% |
| 8 | Django | 3464.35 req/s | 14.40 ms | 13.34 ms | 29.10 ms | 100.0% |
| 9 | FastAPI | 3001.07 req/s | 16.68 ms | 16.09 ms | 20.26 ms | 100.0% |

### Scenario: `multipart`
POST `/body/multipart` uploading a 10KB text file. (Measures multipart parsing).

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Sanic | 22578.27 req/s | 2.21 ms | 1.91 ms | 2.71 ms | 100.0% |
| 2 | Falcon | 21879.46 req/s | 2.28 ms | 2.09 ms | 2.85 ms | 100.0% |
| 3 | Starlette | 15967.05 req/s | 3.13 ms | 3.12 ms | 3.21 ms | 100.0% |
| 4 | Aquilia | 9773.39 req/s | 5.11 ms | 5.06 ms | 5.21 ms | 100.0% |
| 5 | Quart | 7076.38 req/s | 7.06 ms | 6.78 ms | 7.08 ms | 100.0% |
| 6 | Flask | 3589.39 req/s | 20.15 ms | 16.74 ms | 35.53 ms | 84.2% |
| 7 | FastAPI | 3334.59 req/s | 15.01 ms | 15.06 ms | 15.32 ms | 100.0% |
| 8 | Django | 2810.25 req/s | 17.81 ms | 16.59 ms | 33.74 ms | 100.0% |
| 9 | Litestar | 0.00 req/s | 0.00 ms | 0.00 ms | 0.00 ms | 0.0% |

### Scenario: `stream`
GET `/response/stream` sending a 32KB chunked-encoded stream.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 9145.23 req/s | 5.46 ms | 5.44 ms | 5.66 ms | 100.0% |
| 2 | Aquilia | 7372.21 req/s | 6.78 ms | 6.72 ms | 6.98 ms | 100.0% |
| 3 | Litestar | 6828.87 req/s | 7.32 ms | 7.30 ms | 7.59 ms | 100.0% |
| 4 | Starlette | 6561.87 req/s | 7.62 ms | 7.52 ms | 8.13 ms | 100.0% |
| 5 | Quart | 6314.60 req/s | 7.92 ms | 7.85 ms | 8.20 ms | 100.0% |
| 6 | FastAPI | 2372.30 req/s | 21.12 ms | 20.14 ms | 31.82 ms | 100.0% |
| 7 | Django | 1129.63 req/s | 44.43 ms | 41.76 ms | 67.06 ms | 100.0% |
| 8 | Flask | 30.97 req/s | 1814.49 ms | 2359.30 ms | 2369.55 ms | 100.0% |
| 9 | Sanic | 0.00 req/s | 0.00 ms | 0.00 ms | 0.00 ms | 0.0% |

### Scenario: `middleware_0`
GET `/plaintext` with 0 custom middleware layers.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 68345.54 req/s | 0.73 ms | 0.77 ms | 0.89 ms | 100.0% |
| 2 | Starlette | 58684.59 req/s | 0.85 ms | 0.86 ms | 0.96 ms | 100.0% |
| 3 | Litestar | 42230.84 req/s | 1.18 ms | 1.18 ms | 1.26 ms | 100.0% |
| 4 | Aquilia | 34167.48 req/s | 1.46 ms | 1.46 ms | 1.53 ms | 100.0% |
| 5 | Sanic | 33957.11 req/s | 1.47 ms | 1.22 ms | 1.91 ms | 100.0% |
| 6 | FastAPI | 32220.25 req/s | 1.55 ms | 1.54 ms | 1.61 ms | 100.0% |
| 7 | Quart | 16889.08 req/s | 2.96 ms | 2.71 ms | 2.90 ms | 100.0% |
| 8 | Django | 3577.43 req/s | 13.98 ms | 12.99 ms | 28.71 ms | 100.0% |
| 9 | Flask | 2426.33 req/s | 20.63 ms | 12.49 ms | 55.73 ms | 76.3% |

### Scenario: `middleware_5`
GET `/plaintext` with 5 stacked custom middleware layers.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 66356.85 req/s | 0.75 ms | 0.77 ms | 0.89 ms | 100.0% |
| 2 | Starlette | 56571.81 req/s | 0.88 ms | 0.88 ms | 0.92 ms | 100.0% |
| 3 | Litestar | 40303.78 req/s | 1.24 ms | 1.24 ms | 1.30 ms | 100.0% |
| 4 | Aquilia | 34712.45 req/s | 1.44 ms | 1.43 ms | 1.51 ms | 100.0% |
| 5 | Sanic | 32230.55 req/s | 1.55 ms | 1.31 ms | 2.03 ms | 100.0% |
| 6 | Quart | 15613.39 req/s | 3.20 ms | 2.91 ms | 3.11 ms | 100.0% |
| 7 | FastAPI | 3357.74 req/s | 14.90 ms | 13.88 ms | 17.11 ms | 100.0% |
| 8 | Django | 3015.12 req/s | 16.60 ms | 15.79 ms | 30.89 ms | 100.0% |
| 9 | Flask | 2668.76 req/s | 18.72 ms | 11.92 ms | 50.58 ms | 79.9% |

### Scenario: `middleware_10`
GET `/plaintext` with 10 stacked custom middleware layers.

| Rank | Framework | Throughput (QPS) | Latency Average | P50 Latency | P95 Latency | Success Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Falcon | 64967.75 req/s | 0.77 ms | 0.79 ms | 0.88 ms | 100.0% |
| 2 | Starlette | 54565.71 req/s | 0.92 ms | 0.91 ms | 0.95 ms | 100.0% |
| 3 | Litestar | 39240.04 req/s | 1.27 ms | 1.27 ms | 1.34 ms | 100.0% |
| 4 | Aquilia | 34657.40 req/s | 1.44 ms | 1.44 ms | 1.51 ms | 100.0% |
| 5 | Sanic | 31004.37 req/s | 1.61 ms | 1.37 ms | 2.09 ms | 100.0% |
| 6 | Quart | 14768.65 req/s | 3.38 ms | 3.06 ms | 3.25 ms | 100.0% |
| 7 | Django | 3000.93 req/s | 16.68 ms | 15.89 ms | 21.50 ms | 100.0% |
| 8 | Flask | 2192.67 req/s | 22.67 ms | 12.42 ms | 64.74 ms | 76.8% |
| 9 | FastAPI | 1774.05 req/s | 28.24 ms | 25.24 ms | 46.42 ms | 100.0% |

## 3. Key Performance Insights
### Middleware Scaling Cost
This table summarizes how throughput scales as middleware layers are stacked (0 -> 5 -> 10 layers).

| Framework | 0 Layers QPS | 5 Layers QPS | 10 Layers QPS | Overhead (10 vs 0) |
| :--- | :--- | :--- | :--- | :--- |
| Aquilia | 34167.48 | 34712.45 | 34657.40 | -1.4% decrease |
| FastAPI | 32220.25 | 3357.74 | 1774.05 | 94.5% decrease |
| Starlette | 58684.59 | 56571.81 | 54565.71 | 7.0% decrease |
| Litestar | 42230.84 | 40303.78 | 39240.04 | 7.1% decrease |
| Falcon | 68345.54 | 66356.85 | 64967.75 | 4.9% decrease |
| Sanic | 33957.11 | 32230.55 | 31004.37 | 8.7% decrease |
| Quart | 16889.08 | 15613.39 | 14768.65 | 12.6% decrease |
| Flask | 2426.33 | 2668.76 | 2192.67 | 9.6% decrease |
| Django | 3577.43 | 3015.12 | 3000.93 | 16.1% decrease |
