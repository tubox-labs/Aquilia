"""Production server command.

Starts the production server from the native workspace app loader.
Multi-worker support is enabled by default for production workloads.

Supports two backends:
- **gunicorn** (recommended) -- multi-worker process manager with
  UvicornWorker class for ASGI.  Best for production deploys.
- **uvicorn** (fallback) -- single-process or multi-worker via
  uvicorn's built-in forking.

The production pipeline resolves runtime settings, creates the workspace
app module, and hands it to uvicorn or gunicorn.
"""

import os
import sys
from pathlib import Path

from ..utils.workspace import get_workspace_file


def serve_production(
    workers: int | None = None,
    bind: str | None = None,
    verbose: bool = False,
    use_gunicorn: bool = False,
    timeout: int = 120,
    graceful_timeout: int = 30,
) -> None:
    """
    Start production server.

    Resolution order for host / port / workers:
    1. Explicit CLI flags (``--bind``, ``--workers``)
    2. AquilaConfig values from ``workspace.py``
    3. Hardcoded production defaults

    Args:
        workers: Number of workers (None = from workspace config or 1)
        bind: Bind address host:port (None = from workspace config or 0.0.0.0:8000)
        verbose: Enable verbose output
        use_gunicorn: Use gunicorn with UvicornWorker (recommended for production)
        timeout: Worker timeout in seconds (gunicorn only)
        graceful_timeout: Graceful shutdown timeout (gunicorn only)
    """
    workspace_root = Path.cwd()
    ws_file = get_workspace_file(workspace_root)

    if not ws_file:
        from aquilia.faults.domains import ConfigMissingFault

        raise ConfigMissingFault(key="workspace.py")

    # ── Resolve runtime settings from AquilaConfig ───────────────────
    from .run import _load_workspace_runtime_config

    rt = _load_workspace_runtime_config(workspace_root)

    if bind is not None:
        # Explicit --bind flag: parse host:port
        if ":" in bind:
            host, port_str = bind.rsplit(":", 1)
            port = int(port_str)
        else:
            host = bind
            port = rt.get("port", 8000)
    else:
        # No explicit bind — read from config
        host = rt.get("host", "0.0.0.0")
        port = rt.get("port", 8000)

    from .run import _find_available_port

    port = _find_available_port(host, port)

    workers = workers if workers is not None else rt.get("workers", 1)

    # Add workspace to path
    if str(workspace_root) not in sys.path:
        sys.path.insert(0, str(workspace_root))

    # Set env variables for production mode
    os.environ["AQUILIA_ENV"] = "prod"
    os.environ["AQUILIA_WORKSPACE"] = str(workspace_root)

    # Use the same app loader as `aq run` (runtime/app.py)
    from .run import _create_workspace_app

    app_module = _create_workspace_app(workspace_root, mode="prod", verbose=verbose)

    backend = "gunicorn" if use_gunicorn else "uvicorn"

    if verbose:
        print("  Starting Aquilia production server")
        print(f"  Backend: {backend}")
        print(f"  Bind:    {host}:{port}")
        print(f"  Workers: {workers}")
        print(f"  App:     {app_module}")
        print()

    if use_gunicorn:
        _serve_with_gunicorn(
            app_module=app_module,
            bind=f"{host}:{port}",
            workers=workers,
            timeout=timeout,
            graceful_timeout=graceful_timeout,
            verbose=verbose,
        )
    else:
        _serve_with_uvicorn(
            app_module=app_module,
            host=host,
            port=port,
            workers=workers,
            verbose=verbose,
            runtime_config=rt,
        )


def _serve_with_gunicorn(
    app_module: str,
    bind: str,
    workers: int,
    timeout: int,
    graceful_timeout: int,
    verbose: bool,
) -> None:
    """Start production server using gunicorn with UvicornWorker."""
    try:
        from gunicorn.app.wsgiapp import WSGIApplication
    except ImportError:
        raise ImportError(
            "gunicorn is required for --use-gunicorn mode.\n"
            "Install it with: pip install gunicorn\n"
            "Or with extras: pip install 'aquilia[server]'"
        )

    class AquiliaGunicornApp(WSGIApplication):
        """Custom gunicorn application for Aquilia ASGI servers."""

        def init(self, parser, opts, args):
            return {
                "bind": bind,
                "workers": workers,
                "worker_class": "uvicorn.workers.UvicornWorker",
                "timeout": timeout,
                "graceful_timeout": graceful_timeout,
                "accesslog": "-" if verbose else None,
                "errorlog": "-",
                "loglevel": "info" if verbose else "warning",
                "preload_app": False,
                "proxy_protocol": True,
                "forwarded_allow_ips": "*",
            }

        def load(self):
            # gunicorn loads the app string itself via UvicornWorker
            return None

    # gunicorn expects the app module on sys.argv
    sys.argv = ["gunicorn", app_module]
    AquiliaGunicornApp("%(prog)s [OPTIONS]").run()


def _serve_with_uvicorn(
    app_module: str,
    host: str,
    port: int,
    workers: int,
    verbose: bool,
    runtime_config: dict | None = None,
) -> None:
    """Start production server using uvicorn directly.

    All ``AquilaConfig.Server`` fields are forwarded to uvicorn so that
    settings like ``timeout_keep_alive``, ``limit_max_requests``,
    ``proxy_headers``, SSL certs, etc. take effect automatically.
    """
    try:
        import uvicorn
    except ImportError:
        raise ImportError(
            "uvicorn is required to run the production server.\n"
            "Install it with: pip install uvicorn\n"
            "Or with extras: pip install 'aquilia[server]'"
        )

    from .run import _build_uvicorn_kwargs

    uv_kwargs = _build_uvicorn_kwargs(
        runtime_config or {},
        overrides={
            "host": host,
            "port": port,
            "workers": workers,
        },
    )
    # Production-mode defaults
    uv_kwargs["reload"] = False
    uv_kwargs.setdefault("log_level", "info" if verbose else "warning")
    uv_kwargs.setdefault("access_log", False)

    uvicorn.run(app=app_module, **uv_kwargs)
