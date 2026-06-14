# aq serve

Start the Aquilia production server. Uses **uvicorn** by default with optional **gunicorn** process management for production deployments.

## Usage

```bash
aq serve [OPTIONS]
```

## Options

| Option               | Description                                                          | Default                    |
| -------------------- | -------------------------------------------------------------------- | -------------------------- |
| `--workers`          | Number of worker processes                                           | From config, or `1`       |
| `--bind`             | Bind address in `host:port` format                                   | From config, or `0.0.0.0:8000` |
| `--use-gunicorn`     | Use gunicorn with UvicornWorker (recommended for production)         | `False`                    |
| `--timeout`          | Worker timeout in seconds (gunicorn only)                            | `120`                      |
| `--graceful-timeout` | Graceful shutdown timeout in seconds (gunicorn only)                 | `30`                       |

## Resolution Order

Host, port, and worker count are resolved in this order:

1. Explicit CLI flags (`--bind`, `--workers`)
2. `AquilaConfig.Server` values from `workspace.py`
3. Hardcoded defaults

## Backends

### Default: uvicorn

```bash
aq serve
aq serve --workers=4
```

Uses uvicorn's direct process management. Suitable for smaller deployments.

### Production: gunicorn + UvicornWorker

```bash
aq serve --use-gunicorn --workers=4
aq serve --use-gunicorn --workers=8 --timeout=180 --graceful-timeout=60
```

Provides robust process management with:

- Pre-fork worker model
- Graceful worker restarts
- Configurable timeouts
- `--proxy-protocol` support
- Access and error logging

!!! tip "Production Recommendation"
    Use `--use-gunicorn` for production deployments. It provides better process management, automatic worker recycling, and graceful shutdown handling.

## Requirements

- **uvicorn**: `pip install uvicorn` or `pip install 'aquilia[server]'`
- **gunicorn**: `pip install gunicorn` or `pip install 'aquilia[server]'` (for `--use-gunicorn`)

## Environment Variables

| Variable            | Effect                               |
| ------------------- | ------------------------------------ |
| `AQUILIA_ENV`       | Always set to `prod`                  |
| `AQUILIA_WORKSPACE` | Set to workspace root path           |

## Examples

```bash
# Default production server
aq serve

# 4 worker processes
aq serve --workers=4

# Production with gunicorn
aq serve --use-gunicorn --workers=4

# Custom bind address
aq serve --bind=0.0.0.0:8080

# Gunicorn with custom timeouts
aq serve --use-gunicorn --workers=8 --timeout=180 --graceful-timeout=60
```

## Exit Behavior

- **`Ctrl+C`**: Graceful shutdown with confirmation message
- **Errors**: Exits with code 1 and error message
- **`--debug`**: Prints full traceback on errors

## See Also

- [`aq run`](run.md) — Development server with hot-reload
- [`aq deploy`](deploy.md) — Generate deployment files