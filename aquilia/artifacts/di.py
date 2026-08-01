"""
Dependency injection integration for ArtifactStore.

Registers ArtifactStore as a singleton DI service so it can be
injected into framework services that need artifact persistence.

Usage in a manifest:

    from aquilia.artifacts.di import ArtifactStoreProvider

    class AppManifest:
        services = [ArtifactStoreProvider]

Or direct factory:

    from aquilia.artifacts.di import provide_artifact_store
    store = provide_artifact_store(config)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from aquilia.artifacts.cache_root import resolve_artifact_root
from aquilia.artifacts.store import ArtifactStore


def provide_artifact_store(
    config: Any = None,
    *,
    root: str | Path | None = None,
) -> ArtifactStore:
    """
    Factory function for ArtifactStore.

    Resolves artifact root from:
    1. Explicit root parameter
    2. config.artifacts.root (if config has artifacts section)
    3. AQUILIA_ARTIFACT_ROOT env var
    4. <cwd>/.aquilia/artifacts
    """
    config_root = None
    if config is not None:
        # Try common config shapes
        if hasattr(config, "artifacts"):
            artifacts_cfg = config.artifacts
            if hasattr(artifacts_cfg, "root"):
                config_root = artifacts_cfg.root
            elif isinstance(artifacts_cfg, dict):
                config_root = artifacts_cfg.get("root")
        elif isinstance(config, dict):
            config_root = config.get("artifacts", {}).get("root")

    effective_root = root or config_root
    artifact_root = resolve_artifact_root(config_root=effective_root)
    return ArtifactStore.for_root(artifact_root)


class ArtifactStoreProvider:
    """
    DI provider descriptor for ArtifactStore.

    Add to your manifest's services list to make ArtifactStore
    available for injection throughout the framework.

    Example::

        class AppManifest:
            services = [ArtifactStoreProvider]

    Then inject::

        class MyService:
            def __init__(self, store: ArtifactStore):
                self.store = store
    """

    # DI provider metadata
    class_path = "aquilia.artifacts.di.provide_artifact_store"
    scope = "app"
    aliases = ["ArtifactStore", "artifact_store"]
    config = {}

    @classmethod
    def to_dict(cls) -> dict:
        return {
            "class_path": cls.class_path,
            "scope": cls.scope,
            "aliases": cls.aliases,
            "config": cls.config,
        }
