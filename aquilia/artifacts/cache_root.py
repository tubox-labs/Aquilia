"""
Cache root resolution — single source of truth for artifact storage paths.

All framework-generated artifacts live under a single configurable root:

    <project_root>/
    └── .aquilia/
        └── artifacts/
            ├── discovery_cache.json          (auto-discovery engine cache)
            ├── schema_snapshot.json          (ORM schema snapshot for migrations)
            ├── templates.bytecode.json       (compiled Jinja2 bytecode, HMAC-signed)
            ├── templates.json                (template manifest / inventory)
            ├── ws.json                       (WebSocket controller metadata)
            ├── mcp_knowledge_index.json      (MCP context knowledge index)
            ├── di_manifest.json              (DI provider graph for LSP/IDE)
            └── route_index.json              (compiled route index)

Every artifact producer resolves its path by calling ``resolve_artifact_root()``
rather than hard-coding an ``artifacts/`` directory.  This guarantees all
framework artifacts are co-located, gitignore-able as a group, and
consistently discoverable by ``aq artifacts status / verify / clean``.

The frozen registry manifest is deliberately excluded — it lives wherever the
operator points ``aq aquilary freeze``, because it is meant to be committed
to VCS at the team's chosen location.

Configuration override::

    # pyproject.toml or aquilia.toml
    [aquilia.artifacts]
    root = "/var/lib/myapp/artifacts"

Or via environment variable::

    AQUILIA_ARTIFACT_ROOT=/var/lib/myapp/artifacts
"""

from __future__ import annotations

import os
from pathlib import Path


def resolve_artifact_root(
    *,
    config_root: str | Path | None = None,
    project_root: str | Path | None = None,
    env_var: str = "AQUILIA_ARTIFACT_ROOT",
) -> Path:
    """
    Resolve the canonical artifact root path.

    Priority:
    1. ``config_root`` parameter (from pyconfig / Integration config)
    2. ``AQUILIA_ARTIFACT_ROOT`` environment variable
    3. ``<project_root>/.aquilia/artifacts``
    4. ``<cwd>/.aquilia/artifacts``

    Parameters
    ----------
    config_root
        Explicit root from framework configuration.
    project_root
        Root of the Aquilia project (used for the default path).
    env_var
        Environment variable name to check.

    Returns
    -------
    Path
        Resolved, absolute artifact root path.
    """
    # 1. Explicit config
    if config_root:
        return Path(config_root).resolve()

    # 2. Environment variable
    env_root = os.environ.get(env_var)
    if env_root:
        return Path(env_root).resolve()

    # 3. Project root
    base = Path(project_root).resolve() if project_root else Path.cwd()
    return base / ".aquilia" / "artifacts"


def ensure_artifact_root(root: Path) -> Path:
    """Create the artifact root directory if it doesn't exist."""
    root.mkdir(parents=True, exist_ok=True)
    return root


def legacy_discovery_cache_path(modules_dir: Path) -> Path:
    """
    Return the legacy discovery cache path used before the artifact store.

    This is the path that ``DiscoveryCache`` in ``aquilia/discovery/engine.py``
    used to write to: ``<modules_dir>/../.aquilia/discovery_cache.json``.
    Used during migration to detect and delete old cache files.
    """
    return modules_dir.parent / ".aquilia" / "discovery_cache.json"
