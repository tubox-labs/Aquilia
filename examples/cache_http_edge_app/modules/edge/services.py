from __future__ import annotations

from typing import Any

from aquilia.cache import CacheConfig, CacheService
from aquilia.cache.backends.memory import MemoryBackend
from aquilia.http import AsyncHTTPClient
from aquilia.http._transport import MockTransport


class EdgeGatewayService:
    def __init__(self, cache: CacheService | None = None, transport: MockTransport | None = None) -> None:
        self.cache = cache or CacheService(
            MemoryBackend(max_size=256, eviction_policy="lru"),
            CacheConfig(default_ttl=60, namespace="edge", key_prefix="edge:"),
        )
        self.transport = transport or MockTransport()
        self.origin_hits = 0
        self._started = False

    async def startup(self) -> None:
        if not self._started:
            await self.cache.initialize()
            self._started = True

    async def shutdown(self) -> None:
        if self._started:
            await self.cache.shutdown()
            self._started = False

    async def configure_origin(self, sku: str, payload: dict[str, Any]) -> None:
        self.transport.add_json_response("GET", f"https://inventory.example.test/products/{sku}", payload)

    async def product_snapshot(self, sku: str) -> dict[str, Any]:
        await self.startup()

        async def load() -> dict[str, Any]:
            self.origin_hits += 1
            async with AsyncHTTPClient(transport=self.transport) as client:
                response = await client.get(f"https://inventory.example.test/products/{sku}")
                return await response.json()

        return await self.cache.get_or_set(f"product:{sku}", load, ttl=120, tags=("products",))

    async def purge_product(self, sku: str) -> bool:
        await self.startup()
        return await self.cache.delete(f"product:{sku}")
