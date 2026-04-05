# Benchmark Suite: Aquilia vs FastAPI vs Flask

This benchmark package provides a reproducible cross-framework harness covering:

- JSON serialization throughput
- Dependency resolution path overhead
- Middleware stack overhead
- Route matching (simple, parameterized, and dense route tables)
- Request body parsing (JSON, form, multipart)
- Response generation (text, stream, file)
- Async concurrency behavior
- Startup and cold-start health readiness
- CPU and memory usage under load
- Handled and unhandled error paths
- Static file serving
- WebSocket echo latency/throughput (when framework stack supports it)

## Layout

- `benchmark/apps/aquilia_app`: Aquilia benchmark workspace app
- `benchmark/apps/fastapi_app.py`: FastAPI benchmark app
- `benchmark/apps/flask_app.py`: Flask benchmark app (served via Uvicorn ASGI adapter)
- `benchmark/run.py`: orchestrated benchmark runner + report generator
- `benchmark/results/`: timestamped benchmark outputs (`results.json` + `report.md`)

## Install Dependencies

```bash
pip install -r benchmark/requirements.txt
```

## Run

Standard run:

```bash
python benchmark/run.py
```

Quick smoke run:

```bash
python benchmark/run.py --quick
```

Custom parameters:

```bash
python benchmark/run.py --requests 3000 --concurrency 96 --warmup 200
```

Skip WebSocket scenarios:

```bash
python benchmark/run.py --skip-websocket
```

## Output

Each run creates a folder under `benchmark/results/<timestamp>/`:

- `results.json`: full raw metrics
- `report.md`: human-readable report

A symlink `benchmark/results/latest` always points at the most recent run.

## Notes on Fairness

- All servers run on localhost, single process, with identical host transport.
- Flask is run through ASGI adaptation for server parity with Uvicorn; this intentionally includes adapter overhead in Flask results.
- WebSocket is treated as unsupported for Flask in this suite unless you intentionally add a Flask websocket stack extension.
