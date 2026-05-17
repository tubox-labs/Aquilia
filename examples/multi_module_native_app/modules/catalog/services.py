from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from aquilia.faults import ConflictFault, NotFoundFault


@dataclass(slots=True)
class Product:
    sku: str
    name: str
    price_cents: int
    active: bool = True
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CatalogService:
    def __init__(self):
        self._products: dict[str, Product] = {
            "AQ-STARTER": Product(
                sku="AQ-STARTER",
                name="Aquilia Starter Kit",
                price_cents=4900,
                tags=["starter", "framework"],
            ),
            "AQ-PRO": Product(
                sku="AQ-PRO",
                name="Aquilia Production Pack",
                price_cents=12900,
                tags=["production", "observability"],
            ),
        }

    async def list_products(
        self,
        *,
        q: str | None = None,
        active: bool | None = True,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        items = list(self._products.values())
        if active is not None:
            items = [item for item in items if item.active is active]
        if q:
            needle = q.lower()
            items = [
                item for item in items
                if needle in item.name.lower() or needle in item.sku.lower() or needle in " ".join(item.tags).lower()
            ]
        total = len(items)
        page = items[offset: offset + limit]
        return {"items": [item.to_dict() for item in page], "total": total, "limit": limit, "offset": offset}

    async def get_product(self, sku: str) -> dict[str, Any]:
        product = self._products.get(sku.upper())
        if product is None:
            raise NotFoundFault(detail=f"Product {sku!r} was not found")
        return product.to_dict()

    async def create_product(self, data: dict[str, Any]) -> dict[str, Any]:
        sku = data["sku"].upper()
        if sku in self._products:
            raise ConflictFault(detail=f"Product {sku!r} already exists")
        product = Product(**data)
        self._products[sku] = product
        return product.to_dict()

    async def update_product(self, sku: str, changes: dict[str, Any]) -> dict[str, Any]:
        product = self._products.get(sku.upper())
        if product is None:
            raise NotFoundFault(detail=f"Product {sku!r} was not found")
        for key, value in changes.items():
            if value is not None and hasattr(product, key):
                setattr(product, key, value)
        product.updated_at = datetime.now(timezone.utc).isoformat()
        return product.to_dict()

    async def deactivate_product(self, sku: str) -> dict[str, Any]:
        return await self.update_product(sku, {"active": False})
