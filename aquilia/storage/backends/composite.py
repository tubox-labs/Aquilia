"""
Composite / Multi-Backend Storage.

Routes files to different backends based on glob-pattern rules.
Useful for sending images to S3, documents to local, logs to GCS, etc.

Usage::

    from aquilia.storage.backends.composite import CompositeStorage
    from aquilia.storage.configs import CompositeConfig

    storage = CompositeStorage(CompositeConfig(
        backends={
            "media": {"backend": "s3", "bucket": "cdn-media"},
            "docs":  {"backend": "local", "root": "/var/docs"},
        },
        rules={
            "*.jpg": "media",
            "*.png": "media",
            "*.pdf": "docs",
        },
        fallback="media",
    ))
"""

from __future__ import annotations

import contextlib
import fnmatch
from collections.abc import AsyncIterator
from typing import (
    BinaryIO,
)

from ..base import (
    BackendUnavailableError,
    StorageBackend,
    StorageFile,
    StorageMetadata,
)
from ..configs import CompositeConfig, config_from_dict
from ..registry import create_backend


class CompositeStorage(StorageBackend):
    """
    Composite storage that routes files to sub-backends by rules.

    Rules are glob patterns (e.g. ``*.jpg``) mapped to backend aliases.
    If no rule matches, the ``fallback`` backend is used.
    """

    __slots__ = ("_config", "_backends", "_rules", "_fallback")

    def __init__(self, config: CompositeConfig) -> None:
        self._config = config
        self._backends: dict[str, StorageBackend] = {}
        self._rules: list[tuple[str, str]] = []  # (glob, alias)
        self._fallback: str = config.fallback

    @property
    def backend_name(self) -> str:
        return "composite"

    # -- Lifecycle ---------------------------------------------------------

    async def initialize(self) -> None:
        # Instantiate sub-backends from config dicts
        for alias, raw in self._config.backends.items():
            if "alias" not in raw:
                raw = dict(raw, alias=alias)
            cfg = config_from_dict(raw)
            backend = create_backend(cfg)
            await backend.initialize()
            self._backends[alias] = backend

        # Parse rules
        self._rules = [(pattern, alias) for pattern, alias in self._config.rules.items()]

    async def shutdown(self) -> None:
        for backend in self._backends.values():
            with contextlib.suppress(Exception):
                await backend.shutdown()

    async def ping(self) -> bool:
        for backend in self._backends.values():
            if not await backend.ping():
                return False
        return True

    # -- Routing -----------------------------------------------------------

    def _resolve(self, name: str) -> StorageBackend:
        """Resolve which backend should handle a given filename."""
        basename = name.rsplit("/", 1)[-1] if "/" in name else name

        for pattern, alias in self._rules:
            if fnmatch.fnmatch(basename, pattern) and alias in self._backends:
                return self._backends[alias]

        # Fallback
        if self._fallback in self._backends:
            return self._backends[self._fallback]

        # Last resort: first registered backend
        if self._backends:
            return next(iter(self._backends.values()))

        raise BackendUnavailableError(
            "No backends configured in composite storage",
            backend="composite",
            path=name,
        )

    # -- Core operations (delegate) ----------------------------------------

    async def save(
        self,
        name: str,
        content: bytes | BinaryIO | AsyncIterator[bytes] | StorageFile,
        *,
        content_type: str | None = None,
        metadata: dict[str, str] | None = None,
        overwrite: bool = False,
    ) -> str:
        backend = self._resolve(name)
        return await backend.save(
            name,
            content,
            content_type=content_type,
            metadata=metadata,
            overwrite=overwrite,
        )

    async def open(self, name: str, mode: str = "rb") -> StorageFile:
        backend = self._resolve(name)
        return await backend.open(name, mode)

    async def delete(self, name: str) -> None:
        backend = self._resolve(name)
        await backend.delete(name)

    async def exists(self, name: str) -> bool:
        backend = self._resolve(name)
        return await backend.exists(name)

    async def stat(self, name: str) -> StorageMetadata:
        backend = self._resolve(name)
        return await backend.stat(name)

    async def listdir(self, path: str = "") -> tuple[list[str], list[str]]:
        # Aggregate from all backends
        all_dirs: set = set()
        all_files: set = set()
        for backend in self._backends.values():
            dirs, files = await backend.listdir(path)
            all_dirs.update(dirs)
            all_files.update(files)
        return sorted(all_dirs), sorted(all_files)

    async def size(self, name: str) -> int:
        backend = self._resolve(name)
        return await backend.size(name)

    async def url(self, name: str, expire: int | None = None) -> str:
        backend = self._resolve(name)
        return await backend.url(name, expire)
