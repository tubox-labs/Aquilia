from __future__ import annotations

import tempfile
from pathlib import Path

from aquilia.cache import CacheConfig, CacheService, MemoryBackend
from aquilia.filesystem import AsyncPath, file_exists, read_file, write_file
from aquilia.storage import MemoryConfig, MemoryStorage


async def run() -> dict:
    cache = CacheService(MemoryBackend(max_size=32), CacheConfig(default_ttl=60, namespace="catalog"))
    await cache.initialize()
    await cache.set("product:AQ", {"sku": "AQ", "stock": 7}, tags=("products",))
    cached_product = await cache.get("product:AQ")
    stats = await cache.stats()

    storage = MemoryStorage(MemoryConfig())
    await storage.initialize()
    saved_name = await storage.save("receipts/ord-1.txt", b"paid", content_type="text/plain", overwrite=True)
    stored_file = await storage.open(saved_name)
    stored_bytes = await stored_file.read()

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        path = root / "reports" / "daily.txt"
        await AsyncPath(path.parent).mkdir(parents=True, exist_ok=True)
        await write_file(path, "orders=3\n", atomic=True)
        exists = await file_exists(path)
        text = await read_file(path, encoding="utf-8")

    await storage.shutdown()
    await cache.shutdown()
    return {
        "cache_hit": cached_product["stock"] == 7,
        "cache_backend": stats.backend,
        "storage_url": await storage.url(saved_name),
        "storage_bytes": stored_bytes.decode("utf-8"),
        "filesystem_exists": exists,
        "filesystem_text": text.strip(),
    }
