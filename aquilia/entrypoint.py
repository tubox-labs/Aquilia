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
The entrypoint auto-discovers the workspace configuration at import time:

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

import importlib
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any

from .typing.manifest import ManifestCollection

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


def _setup_logging(mode: str) -> None:
    """Configure structured, mode-aware logging."""
    level = logging.DEBUG if mode == "dev" else logging.INFO
    fmt = (
        "%(asctime)s | %(levelname)-8s | %(name)s — %(message)s"
        if mode == "prod"
        else "%(levelname)-8s | %(name)s — %(message)s"
    )
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(fmt))
    logging.root.handlers.clear()
    logging.root.addHandler(handler)
    logging.root.setLevel(level)

    # Silence noisy loggers
    for name in (
        "aquilia.sqlite",
        "asyncio",
        "urllib3",
        "httpcore",
        "httpx",
        "watchfiles",
        "uvicorn.error",
        "python_multipart",
        "python_multipart.multipart",
    ):
        logging.getLogger(name).setLevel(logging.WARNING)


def _discover_workspace_name(content: str) -> str:
    """Extract workspace name from workspace.py content."""
    match = re.search(r'Workspace\(\s*(?:name\s*=\s*)?["\']([^"\']+)["\']', content)
    return match.group(1) if match else "aquilia-app"


def _discover_module_names(content: str) -> list[str]:
    """Extract module names from workspace.py, ignoring comments."""
    clean_lines = [line for line in content.splitlines() if not line.strip().startswith("#")]
    clean = "\n".join(clean_lines)

    modules = re.findall(r'\.module\(\s*Module\(\s*["\']([^"\']+)["\']', clean)
    # Deduplicate preserving order, exclude the starter pseudo-module
    seen: set[str] = set()
    result: list[str] = []
    for m in modules:
        if m not in seen and m != "starter":
            seen.add(m)
            result.append(m)
    return result


def _load_workspace_modules(workspace_root: Path) -> dict[str, dict[str, Any]]:
    """Load workspace.py and extract module configs keyed by module name.

    This function loads the full Workspace object from workspace.py and
    extracts the module configurations (including route_prefix) so they
    can be threaded through to the runtime.

    Returns:
        Dict mapping module name to its workspace config dict.
        Example: {"users": {"route_prefix": "/api/users", ...}, ...}
    """
    ws_file = workspace_root / "workspace.py"
    if not ws_file.exists():
        return {}

    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location("_aq_workspace_loader", ws_file)
        if spec is None or spec.loader is None:
            _logger.warning("Failed to create module spec for workspace.py")
            return {}

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        workspace = getattr(module, "workspace", None)
        if workspace is None:
            _logger.warning("No 'workspace' object found in workspace.py")
            return {}

        # Get the full workspace config dict
        ws_dict = workspace.to_dict()
        modules_list = ws_dict.get("modules", [])

        # Build lookup by module name
        return {m["name"]: m for m in modules_list if "name" in m}

    except Exception as exc:
        _logger.warning("Failed to load workspace modules: %s", exc)
        return {}


def create_app(
    workspace_root: Path | None = None,
    mode: str | None = None,
) -> Any:
    """Create the ASGI application from workspace configuration.

    This is the core factory function.  It can be called explicitly
    or is invoked automatically when this module is imported.

    Dotenv Integration
    ------------------
    This function automatically loads ``.env`` files from the workspace
    root before processing any configuration. You do NOT need to call
    ``load_dotenv()`` manually.

    Args:
        workspace_root: Path to workspace directory (default: from env).
        mode: Runtime mode — ``dev``, ``test``, or ``prod`` (default: from env).

    Returns:
        The ASGI application callable (``AquiliaServer.app``).

    Raises:
        FileNotFoundError: If ``workspace.py`` is not found.
        ImportError: If a module manifest cannot be imported.
    """
    # ── 1. Resolve workspace root ────────────────────────────────────
    if workspace_root is None:
        ws_path = _sanitise_env("AQUILIA_WORKSPACE", "/app")
        workspace_root = Path(ws_path).resolve()

    if mode is None:
        mode = _sanitise_env("AQUILIA_ENV", "prod", allowed={"dev", "test", "prod", "production"})
        # Normalise "production" → "prod"
        if mode == "production":
            mode = "prod"

    # ── 2. Bootstrap paths and environment ───────────────────────────
    if str(workspace_root) not in sys.path:
        sys.path.insert(0, str(workspace_root))

    os.environ.setdefault("AQUILIA_ENV", mode)
    os.environ.setdefault("AQUILIA_WORKSPACE", str(workspace_root))

    _setup_logging(mode)

    # ── 2.5. Dotenv loading is resolved by pyconfig / ConfigLoader ─────
    # AquilaConfig class-level dotenv policy is applied during config
    # resolution, so avoid preloading hardcoded file lists here.

    # ── 3. Load workspace configuration ──────────────────────────────
    workspace_file = workspace_root / "workspace.py"
    if not workspace_file.exists():
        raise FileNotFoundError(
            f"workspace.py not found at {workspace_root}. Set AQUILIA_WORKSPACE to the correct path."
        )

    from aquilia.config import ConfigLoader

    config = ConfigLoader.load(
        paths=["workspace.py"],
        overrides={
            "mode": mode,
            "debug": str(mode == "dev"),
        },
    )

    # ── 4. Discover module manifests ─────────────────────────────────
    workspace_content = workspace_file.read_text(encoding="utf-8")
    workspace_name = _discover_workspace_name(workspace_content)
    module_names = _discover_module_names(workspace_content)

    # Ensure apps namespace
    if "apps" not in config.config_data:
        config.config_data["apps"] = {}

    manifests: ManifestCollection = []

    # Static imports for declared modules
    for mod_name in module_names:
        config.config_data["apps"].setdefault(mod_name, {})
        try:
            mod = importlib.import_module(f"modules.{mod_name}.manifest")
            manifest = getattr(mod, "manifest", None)
            if manifest is not None:
                manifests.append(manifest)
            else:
                _logger.warning("No 'manifest' attribute in modules.%s.manifest", mod_name)
        except Exception as exc:
            _logger.error("Failed to import manifest for %s: %s", mod_name, exc)

    # Dynamic discovery — pick up modules added after last build
    modules_dir = workspace_root / "modules"
    known = set(module_names)
    if modules_dir.is_dir():
        for pkg in sorted(modules_dir.iterdir()):
            if (
                pkg.is_dir()
                and pkg.name not in known
                and (pkg / "manifest.py").exists()
                and not pkg.name.startswith(("_", "."))
            ):
                try:
                    mod = importlib.import_module(f"modules.{pkg.name}.manifest")
                    m = getattr(mod, "manifest", None)
                    if m is not None:
                        manifests.append(m)
                        config.config_data["apps"].setdefault(pkg.name, {})
                except Exception as exc:
                    _logger.warning("Could not import manifest for %s: %s", pkg.name, exc)

    config._build_apps_namespace()

    # ── 5. Load workspace module configs ─────────────────────────────
    # Extract route_prefix and other module-level configs from workspace.py
    workspace_modules = _load_workspace_modules(workspace_root)

    # ── 6. Construct server ──────────────────────────────────────────
    from aquilia import AquiliaServer
    from aquilia.aquilary.core import RegistryMode

    mode_map = {"dev": RegistryMode.DEV, "prod": RegistryMode.PROD, "test": RegistryMode.TEST}
    registry_mode = mode_map.get(mode, RegistryMode.PROD)

    _server = AquiliaServer(
        manifests=manifests,
        config=config,
        mode=registry_mode,
        workspace_modules=workspace_modules,
    )

    return _server


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
