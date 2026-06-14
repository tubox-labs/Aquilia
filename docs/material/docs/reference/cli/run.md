# aq run

Start the Aquilia development server with hot-reload. Auto-discovers controllers and services, validates workspace configuration, and launches uvicorn with Aquilia-aware defaults.

## Usage

```bash
aq run [OPTIONS]
```

## Options

| Option           | Description                                                          | Default                          |
| ---------------- | -------------------------------------------------------------------- | -------------------------------- |
| `--mode`         | Runtime mode: `dev` or `test`                                       | `dev`                            |
| `--port`         | Server port                                                          | From config, or `8000`           |
| `--host`         | Server host                                                          | From config, or `127.0.0.1`      |
| `--reload` / `--no-reload` | Enable/disable hot-reload                                  | From config, or `True`           |
| `--skip-checks`  | Skip admin pre-flight dependency checks                             | `False`                          |

## Resolution Order

Host, port, and reload settings are resolved in this order:

1. Explicit CLI flags (`--host`, `--port`, `--reload`/`--no-reload`)
2. `AquilaConfig.Server` values from `workspace.py`
3. Hardcoded fallback defaults

## Startup Sequence

When you run `aq run`, the following happens in order:

1. **Environment setup** — Sets `AQUILIA_ENV` and `AQUILIA_WORKSPACE`
2. **Admin pre-flight checks** — Warns if admin integration is enabled but sessions are not configured
3. **Auto-discovery** — Scans all modules for controllers, services, models, guards, pipes, and interceptors
4. **Manifest sync** — Updates `manifest.py` files with discovered components
5. **Workspace validation** — Validates that all registered modules exist and all import paths resolve
6. **Route discovery** — Prints a route table showing all discovered endpoints
7. **App generation** — Generates `runtime/app.py` ASGI entrypoint
8. **Server start** — Launches uvicorn with hot-reload

### Auto-Discovery

`aq run` automatically discovers and updates manifests with:

- **Controllers** — classes ending in `Controller`, `Handler`, `View`
- **Services** — classes ending in `Service` or with `__di_scope__`
- **Socket controllers** — WebSocket namespace controllers
- **Models** — `Model` subclasses (via AST engine)
- **Guards** — guard classes (via AST engine)
- **Pipes** — pipe classes (via AST engine)
- **Interceptors** — interceptor classes (via AST engine)

### Route Display

After discovery, `aq run` prints a route summary:

```
  Discovered Routes & Modules
======================================================================
  Module               Route Prefix              Controllers  Services
  ──────────────────── ───────────────────────── ──────────── ──────────
  users                /users                    3            2
  products             /products                 2            1

  Controller Details:
  users:
    • UsersController
    • UserAuthController
  products:
    • ProductsController

  WebSocket Controllers:
  chat:
    -> ChatController -> /ws/chat

======================================================================
  Summary:
  Total Modules: 2
  With Services: 2 (3 total)
  With Controllers: 2 (5 total)
  All modules validated!
```

### Route Discovery Report

A `ROUTES.md` file is also generated in the workspace root with a markdown-formatted discovery report.

## Admin Pre-Flight Checks

When admin integration is detected in `workspace.py`, `aq run` checks that sessions are configured. Without sessions, admin login will not work.

```
  ! Admin integration detected but sessions are NOT configured.
    Admin login will NOT work without session support.
    Run 'aq admin setup' to auto-configure everything.
    Or:  'aq admin check' for full diagnostics.
    Use --skip-checks to suppress this warning.
```

Use `--skip-checks` to bypass this check.

## Environment Variables

| Variable            | Effect                                         |
| ------------------- | ---------------------------------------------- |
| `AQUILIA_ENV`       | Set to `dev` or `test` based on `--mode`       |
| `AQUILIA_WORKSPACE` | Set to workspace root path                     |

## Uvicorn Configuration

`aq run` forwards all `AquilaConfig.Server` fields to uvicorn. Supported parameters include:

`host`, `port`, `reload`, `reload_dirs`, `reload_delay`, `reload_includes`, `reload_excludes`, `workers`, `log_level`, `access_log`, `use_colors`, `proxy_headers`, `server_header`, `date_header`, `forwarded_allow_ips`, `root_path`, `limit_concurrency`, `limit_max_requests`, `backlog`, `timeout_keep_alive`, `ssl_keyfile`, `ssl_certfile`, and more.

Dev-mode defaults:

- `reload_dirs`: workspace root (when reload is enabled)
- `use_colors`: `True`
- `log_level`: `info` (or `debug` in verbose mode)

## Examples

```bash
# Start development server
aq run

# Custom port
aq run --port=3000

# Test mode without hot-reload
aq run --mode=test --no-reload

# Skip admin checks
aq run --skip-checks

# Verbose startup
aq run -v
```

## Exit Behavior

- **`Ctrl+C`**: Graceful shutdown with confirmation
- **Errors**: Exits with code 1

## Requirements

- **uvicorn**: `pip install uvicorn` or `pip install 'aquilia[server]'`

## See Also

- [`aq serve`](serve.md) — Start the production server
- [`aq admin check`](admin.md) — Admin pre-flight diagnostics