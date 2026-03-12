"""
Content-addressable blob store.

Stores binary blobs indexed by their SHA-256 digest.
Used both by the local modelpack builder and the registry backend.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger("aquilia.mlops.pack.content_store")


class ContentStore:
    """
    Local filesystem content-addressable blob store.

    Blobs are stored at ``<root>/<algo>/<hex[:2]>/<hex>``.

    Usage::

        store = ContentStore("./blobs")
        await store.store("sha256:abc...", data)
        data = await store.retrieve("sha256:abc...")
    """

    def __init__(self, root: str = ".aquilia-store"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _blob_path(self, digest: str) -> Path:
        """Compute the storage path for a digest."""
        algo, hex_hash = digest.split(":", 1)
        return self.root / algo / hex_hash[:2] / hex_hash

    async def store(self, digest: str, data: bytes) -> str:
        """
        Store blob by digest. Idempotent -- skips if already exists.

        Returns:
            The storage path as a string.
        """
        path = self._blob_path(digest)
        if path.exists():
            return str(path)

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return str(path)

    async def retrieve(self, digest: str) -> bytes:
        """Retrieve blob by digest."""
        path = self._blob_path(digest)
        if not path.exists():
            raise FileNotFoundError(f"Blob not found: {digest}")
        return path.read_bytes()

    async def exists(self, digest: str) -> bool:
        """Check if blob exists."""
        return self._blob_path(digest).exists()

    async def delete(self, digest: str) -> None:
        """Delete blob by digest."""
        path = self._blob_path(digest)
        if path.exists():
            path.unlink()

    async def list_digests(self) -> list[str]:
        """List all stored blob digests."""
        digests: list[str] = []
        for algo_dir in self.root.iterdir():
            if not algo_dir.is_dir():
                continue
            algo = algo_dir.name
            for prefix_dir in algo_dir.iterdir():
                if not prefix_dir.is_dir():
                    continue
                for blob_file in prefix_dir.iterdir():
                    if blob_file.is_file():
                        digests.append(f"{algo}:{blob_file.name}")
        return digests

    async def gc(self, referenced_digests: set[str]) -> int:
        """
        Garbage-collect unreferenced blobs.

        Args:
            referenced_digests: Set of digests that should be kept.

        Returns:
            Number of blobs deleted.
        """
        all_digests = await self.list_digests()
        deleted = 0
        for digest in all_digests:
            if digest not in referenced_digests:
                await self.delete(digest)
                deleted += 1
        return deleted

    @property
    def size_bytes(self) -> int:
        """Total size of all stored blobs in bytes."""
        total = 0
        for root, _dirs, files in os.walk(self.root):
            for f in files:
                total += os.path.getsize(os.path.join(root, f))
        return total
