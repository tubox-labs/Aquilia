"""
Rest module services (business logic).
Uses pure Aquilia ORM (Rest.objects) and Contract imprint operations.
"""

from typing import Any

from aquilia.contracts import Contract
from aquilia.di import service
from aquilia.faults import ModelNotFoundFault

from .contracts import CreateArticleContract
from .faults import RestNotFoundFault
from .models import Rest


@service(scope="app")
class RestService:
    """
    Service for rest module business logic using native Aquilia ORM operations.
    """

    async def get_all(self) -> list[Rest]:
        """Get all items from database using ORM."""
        return await Rest.objects.all()

    async def get_by_id(self, item_id: str) -> Rest:
        """Get item by ID from database or raise fault."""
        try:
            return await Rest.objects.get(id=item_id)
        except ModelNotFoundFault:
            raise RestNotFoundFault(item_id=item_id)

    async def create(self, data: CreateArticleContract) -> Rest:
        """Create new item in database using contract imprint or ORM create."""
        return await data.imprint()

    async def update(self, item_id: str, data: Any) -> Rest:
        """Update existing item in database."""
        existing = await self.get_by_id(item_id)

        if isinstance(data, Contract):
            return await data.imprint(instance=existing)

        if isinstance(data, dict):
            for k, v in data.items():
                if v is not None and hasattr(existing, k):
                    setattr(existing, k, v)
            await existing.save()
            return existing

        return existing

    async def delete(self, item_id: str) -> bool:
        """Delete item from database."""
        item = await self.get_by_id(item_id)
        await item.delete_instance()
        return True

    async def list_articles(
        self,
        page: int = 1,
        limit: int = 10,
        search: str | None = None,
        category: str | None = None,
        status: str | None = None,
        ordering: str = "-created_at",
    ) -> tuple[list[Rest], int]:
        """List items matching query filters and pagination from database."""
        qs = Rest.objects.all()

        if category:
            qs = qs.filter(category=category)
        if status:
            qs = qs.filter(status=status)

        try:
            total = await qs.count()
        except Exception:
            total = 0

        try:
            items = await qs.order(ordering).offset((page - 1) * limit).limit(limit).all()
        except Exception:
            items = []

        return items, total
