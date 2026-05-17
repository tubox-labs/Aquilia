from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from aquilia.faults import NotFoundFault


@dataclass(slots=True)
class OrderRecord:
    id: str
    customer_email: str
    lines: list[dict[str, Any]]
    status: str = "accepted"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self):
        return asdict(self)


class OrdersService:
    def __init__(self):
        self._orders: dict[str, OrderRecord] = {}
        self._sequence = 0

    async def create_order(self, data: dict[str, Any]):
        self._sequence += 1
        order_id = f"ord_{self._sequence:06d}"
        order = OrderRecord(id=order_id, customer_email=data["customer_email"], lines=data["lines"])
        self._orders[order_id] = order
        return order.to_dict()

    async def get_order(self, order_id: str):
        order = self._orders.get(order_id)
        if order is None:
            raise NotFoundFault(detail="Order was not found")
        return order.to_dict()

    async def list_orders(self):
        return [order.to_dict() for order in self._orders.values()]
