from __future__ import annotations

import hashlib
from typing import Any

from aquilia.storage import MemoryConfig, MemoryStorage, StorageRegistry


class FileHubService:
    def __init__(self, registry: StorageRegistry | None = None) -> None:
        self.registry = registry or StorageRegistry.from_config(
            [
                {"alias": "documents", "backend": "memory", "max_size": 1024 * 1024, "default": True},
                {"alias": "quarantine", "backend": "memory", "max_size": 256 * 1024},
            ]
        )

    async def startup(self) -> None:
        await self.registry.initialize_all()

    async def shutdown(self) -> None:
        await self.registry.shutdown_all()

    async def upload_document(self, name: str, content: bytes, *, tenant: str, quarantine: bool = False) -> dict[str, Any]:
        backend = self.registry["quarantine" if quarantine else "documents"]
        stored_name = await backend.save(
            f"{tenant}/{name}",
            content,
            content_type=backend.guess_content_type(name),
            metadata={"tenant": tenant, "sha256": hashlib.sha256(content).hexdigest()},
            overwrite=False,
        )
        meta = await backend.stat(stored_name)
        return {"name": stored_name, "size": meta.size, "content_type": meta.content_type, "metadata": meta.metadata}

    async def download(self, name: str, alias: str = "documents") -> bytes:
        stored = await self.registry[alias].open(name)
        try:
            return await stored.read()
        finally:
            await stored.close()

    async def inventory(self, alias: str = "documents") -> dict[str, Any]:
        dirs, files = await self.registry[alias].listdir()
        health = await self.registry.health_check()
        return {"alias": alias, "dirs": dirs, "files": files, "health": health}


def build_ephemeral_backend(max_size: int = 1024) -> MemoryStorage:
    return MemoryStorage(MemoryConfig(max_size=max_size))
