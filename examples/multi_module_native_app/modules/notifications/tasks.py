from datetime import datetime, timezone

from aquilia.tasks import Priority, task


@task(queue="mail", priority=Priority.HIGH, max_retries=5, tags=["mail", "orders"])
async def send_order_receipt(email: str, order_id: str) -> dict:
    return {"email": email, "order_id": order_id, "sent_at": datetime.now(timezone.utc).isoformat()}
