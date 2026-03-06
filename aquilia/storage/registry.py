"""
Storage Registry -- Named backend registry with Django-style aliases.

Centralises all storage backends.  Access by name like Django's ``storages``:

    registry["default"]   → the default StorageBackend
    registry["avatars"]   → a custom alias
    registry.default      → shortcut for "default"

The registry is populated by the ``StorageSubsystem`` at boot time from
``Workspace`` config, and published into the DI container so that
controllers and effects can consume it.
"""

from __future__ import annotations

import importlib
from typing import Any, Dict, Iterator, Optional, Type

from .base import BackendUnavailableError, StorageBackend
from .configs import (
    AzureBlobConfig,
    CompositeConfig,
    GCSConfig,
    LocalConfig,
    MemoryConfig,
    S3Config,
    SFTPConfig,
    StorageConfig,
    config_from_dict,
)


# ═══════════════════════════════════════════════════════════════════════════
# Backend factory map (shorthand → dotted import path)
# ═══════════════════════════════════════════════════════════════════════════

_BUILTIN_BACKENDS: Dict[str, str] = {
    "local":     "aquilia.storage.backends.local.LocalStorage",
    "memory":    "aquilia.storage.backends.memory.MemoryStorage",
    "s3":        "aquilia.storage.backends.s3.S3Storage",
    "gcs":       "aquilia.storage.backends.gcs.GCSStorage",
    "azure":     "aquilia.storage.backends.azure.AzureBlobStorage",
    "sftp":      "aquilia.storage.backends.sftp.SFTPStorage",
    "composite": "aquilia.storage.backends.composite.CompositeStorage",
}


def _import_backend(dotted: str) -> Type[StorageBackend]:
    """Import a StorageBackend class from a dotted path."""
    module_path, _, cls_name = dotted.rpartition(".")
    mod = importlib.import_module(module_path)
    cls = getattr(mod, cls_name, None)
    if cls is None:
        raise ImportError(f"Cannot find class {cls_name!r} in {module_path!r}")
    return cls


def create_backend(config: StorageConfig) -> StorageBackend:
    """
    Instantiate a ``StorageBackend`` from a ``StorageConfig``.

    1. Resolves the backend shorthand ('s3') or dotted import path.
    2. Imports the class.
    3. Instantiates it with the config.
    """
    backend_key = config.backend

    # Resolve shorthand → dotted path
    if backend_key in _BUILTIN_BACKENDS:
        dotted = _BUILTIN_BACKENDS[backend_key]
    elif "." in backend_key:
        dotted = backend_key
    else:
        raise BackendUnavailableError(
            f"Unknown storage backend: {backend_key!r}. "
            f"Available: {', '.join(_BUILTIN_BACKENDS)}",
            backend=backend_key,
        )

    cls = _import_backend(dotted)
    return cls(config)


# ═══════════════════════════════════════════════════════════════════════════
# StorageRegistry
# ═══════════════════════════════════════════════════════════════════════════

class StorageRegistry:
    """
    Named registry of storage backends.

    Dict-like access with a ``default`` shortcut property.

    Usage::

        registry = StorageRegistry()
        registry.register("media", LocalStorage(LocalConfig(root="/media")))
        registry.set_default("media")

        await registry["media"].save("avatar.png", data)
        await registry.default.save("report.pdf", data)
    """

    __slots__ = ("_backends", "_default_alias")

    def __init__(self) -> None:
        self._backends: Dict[str, StorageBackend] = {}
        self._default_alias: str = "default"

    # -- Registration ------------------------------------------------------

    def register(self, alias: str, backend: StorageBackend) -> None:
        """Register a backend under an alias."""
        self._backends[alias] = backend

    def unregister(self, alias: str) -> Optional[StorageBackend]:
        """Remove and return a backend by alias."""
        return self._backends.pop(alias, None)

    def set_default(self, alias: str) -> None:
        """Set which alias is the default backend."""
        if alias not in self._backends:
            raise KeyError(f"No backend registered under alias {alias!r}")
        self._default_alias = alias

    # -- Access ------------------------------------------------------------

    @property
    def default(self) -> StorageBackend:
        """Return the default backend."""
        try:
            return self._backends[self._default_alias]
        except KeyError:
            raise BackendUnavailableError(
                f"No default storage backend (alias={self._default_alias!r}). "
                "Register one via Workspace.storage() config.",
                backend=self._default_alias,
            )

    def get(self, alias: str) -> Optional[StorageBackend]:
        """Return a backend by alias, or None."""
        return self._backends.get(alias)

    def __getitem__(self, alias: str) -> StorageBackend:
        try:
            return self._backends[alias]
        except KeyError:
            raise BackendUnavailableError(
                f"Storage backend {alias!r} not registered. "
                f"Available: {', '.join(self._backends) or '(none)'}",
                backend=alias,
            )

    def __contains__(self, alias: str) -> bool:
        return alias in self._backends

    def __len__(self) -> int:
        return len(self._backends)

    def __iter__(self) -> Iterator[str]:
        return iter(self._backends)

    def aliases(self) -> list[str]:
        """Return all registered aliases."""
        return list(self._backends.keys())

    def items(self) -> list[tuple[str, StorageBackend]]:
        return list(self._backends.items())

    # -- Lifecycle ---------------------------------------------------------

    async def initialize_all(self) -> None:
        """Initialize every registered backend."""
        for alias, backend in self._backends.items():
            await backend.initialize()

    async def shutdown_all(self) -> None:
        """Shutdown every registered backend."""
        for alias, backend in self._backends.items():
            try:
                await backend.shutdown()
            except Exception:
                pass  # Best-effort cleanup

    async def health_check(self) -> Dict[str, bool]:
        """Ping every backend and return alias → healthy map."""
        results: Dict[str, bool] = {}
        for alias, backend in self._backends.items():
            try:
                results[alias] = await backend.ping()
            except Exception:
                results[alias] = False
        return results

    # -- Factory from config -----------------------------------------------

    @classmethod
    def from_config(cls, configs: list[Dict[str, Any]]) -> "StorageRegistry":
        """
        Build a registry from a list of config dicts.

        Each dict must have a ``backend`` key and optionally an ``alias``.

        Example::

            StorageRegistry.from_config([
                {"alias": "default", "backend": "local", "root": "./uploads"},
                {"alias": "cdn", "backend": "s3", "bucket": "assets"},
            ])
        """
        registry = cls()
        default_set = False

        for raw in configs:
            cfg = config_from_dict(raw)
            backend = create_backend(cfg)
            alias = cfg.alias or "default"
            registry.register(alias, backend)

            if cfg.default or (alias == "default" and not default_set):
                registry._default_alias = alias
                default_set = True

        return registry

    def __repr__(self) -> str:
        aliases = ", ".join(self._backends)
        return f"<StorageRegistry backends=[{aliases}] default={self._default_alias!r}>"
