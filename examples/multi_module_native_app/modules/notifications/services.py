from aquilia.tasks import TaskManager

from .tasks import send_order_receipt


class NotificationService:
    def __init__(self, manager: TaskManager | None = None):
        self.manager = manager or TaskManager(num_workers=2, default_queue="mail")

    async def ensure_started(self):
        if not self.manager.is_running:
            await self.manager.start()

    async def send_receipt(self, email: str, order_id: str) -> str:
        await self.ensure_started()
        return await send_order_receipt.delay(email=email, order_id=order_id)
