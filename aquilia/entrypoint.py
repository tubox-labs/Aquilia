"""
Aquilia ASGI Entrypoint — Zero-Config Production Application Factory.

This module provides a universal ASGI entrypoint that eliminates the need
for pre-generating ``runtime/app.py`` during Docker builds.  Instead of
the fragile pattern:

    RUN python -c "from aquilia.cli.commands.run import _create_workspace_app; ..."

Containers simply use:

    CMD ["uvicorn", "aquilia.entrypoint:app", "--host", "0.0.0.0"]

Architecture
------------
Delegates entirely to :class:`~aquilia.runtime.AquiliaRuntime`, which
manages the full lifecycle:

1. Resolve workspace root from ``AQUILIA_WORKSPACE`` env var or ``/app``
2. Load ``workspace.py`` via ``ConfigLoader``
3. Discover module manifests from ``modules/*/manifest.py``
4. Construct ``AquiliaServer`` with full manifest list
5. Export ``app`` (ASGI callable) and ``server`` (AquiliaServer instance)

Environment Variables
---------------------
``AQUILIA_WORKSPACE``
    Path to the workspace root directory (default: ``/app``).

``AQUILIA_ENV``
    Runtime mode: ``dev``, ``test``, or ``prod`` (default: ``prod``).

``AQ_SERVER_WORKERS``
    Number of uvicorn workers (handled by uvicorn, not this module).

``AQ_SERVER_PORT``
    Listening port (handled by uvicorn, not this module).

Security
--------
- No ``eval()`` or ``exec()`` — all imports are explicit.
- Module discovery uses ``importlib`` with validated paths.
- Environment variables are sanitised before use.
- Logging never exposes secrets or credentials.

Usage
-----
Docker (recommended)::

    CMD ["uvicorn", "aquilia.entrypoint:app", \\
         "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

Gunicorn::

    CMD ["gunicorn", "aquilia.entrypoint:app", \\
         "-k", "uvicorn.workers.UvicornWorker", "-w", "4"]

Hypercorn::

    CMD ["hypercorn", "aquilia.entrypoint:app", "--bind", "0.0.0.0:8000"]

Direct (testing)::

    python -c "import aquilia.entrypoint; print(aquilia.entrypoint.app)"
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

__all__ = ["app", "server", "create_app"]

_logger = logging.getLogger("aquilia.entrypoint")


def _sanitise_env(key: str, default: str, *, allowed: set | None = None) -> str:
    """Read and sanitise an environment variable.

    - Strips whitespace
    - Rejects values with null bytes (injection guard)
    - Optionally validates against an allowlist
    """
    value = os.environ.get(key, default).strip()
    if "\x00" in value:
        _logger.warning("Null byte in env var %s — using default", key)
        return default
    if allowed and value not in allowed:
        _logger.warning("Invalid value for %s: %r — using default %r", key, value, default)
        return default
    return value


def create_app(
    workspace_root: Path | None = None,
    mode: str | None = None,
) -> Any:
    """Create the ASGI application from workspace configuration.

    Delegates to :class:`~aquilia.runtime.AquiliaRuntime` for the full
    bootstrap lifecycle.  This function is the public-facing factory
    and is invoked automatically at module import time.

    Dotenv Integration
    ------------------
    Dotenv loading is handled automatically by ``AquiliaRuntime`` via
    ``ConfigLoader``.  You do NOT need to call ``load_dotenv()`` manually.

    Args:
        workspace_root: Path to workspace directory (default: from env).
        mode: Runtime mode — ``dev``, ``test``, or ``prod`` (default: from env).

    Returns:
        The :class:`~aquilia.server.AquiliaServer` instance.

    Raises:
        FileNotFoundError: If ``workspace.py`` is not found.
        ImportError: If a module manifest cannot be imported.
    """
    from .runtime import AquiliaRuntime

    # Resolve workspace root with the entrypoint's default of /app
    if workspace_root is None:
        ws_path = _sanitise_env("AQUILIA_WORKSPACE", "/app")
        workspace_root = Path(ws_path).resolve()

    if mode is None:
        mode = _sanitise_env(
            "AQUILIA_ENV",
            "prod",
            allowed={"dev", "test", "prod", "production"},
        )
        if mode == "production":
            mode = "prod"

    runtime = AquiliaRuntime.from_workspace(
        workspace_root=workspace_root,
        mode=mode,
    )

    return runtime.server


# ── Module-level application factory ─────────────────────────────────────
# Import this module and the ASGI app is ready.
# Guarded so import errors produce clear messages.

_server_instance: Any | None = None

try:
    _server_instance = create_app()
    server = _server_instance
    app = _server_instance.app
except FileNotFoundError as _e:
    _logger.error("Aquilia entrypoint: %s", _e)

    # Provide a stub that returns 503 so the container doesn't crash silently
    async def app(scope, receive, send):  # type: ignore[misc]
        if scope["type"] == "http":
            await send(
                {
                    "type": "http.response.start",
                    "status": 503,
                    "headers": [[b"content-type", b"application/json"]],
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": b'{"error":"workspace.py not found","hint":"Set AQUILIA_WORKSPACE"}',
                }
            )
        elif scope["type"] == "lifespan":
            await receive()
            await send({"type": "lifespan.startup.complete"})
            await receive()
            await send({"type": "lifespan.shutdown.complete"})

    server = None  # type: ignore[assignment]
except Exception as _e:
    _logger.error("Aquilia entrypoint failed: %s", _e, exc_info=True)

    async def app(scope, receive, send):  # type: ignore[misc]
        if scope["type"] == "http":
            await send(
                {
                    "type": "http.response.start",
                    "status": 500,
                    "headers": [[b"content-type", b"application/json"]],
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": b'{"error":"Application startup failed","hint":"Check logs"}',
                }
            )
        elif scope["type"] == "lifespan":
            await receive()
            await send({"type": "lifespan.startup.complete"})
            await receive()
            await send({"type": "lifespan.shutdown.complete"})

    server = None  # type: ignore[assignment]
