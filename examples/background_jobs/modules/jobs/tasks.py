from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from aquilia.tasks import Priority, every, task


@task(queue="mail", priority=Priority.HIGH, max_retries=5, retry_delay=2.0, tags=["mail", "user"])
async def send_welcome_email(email: str, name: str) -> dict:
    await asyncio.sleep(0.01)
    return {"sent": True, "email": email, "name": name, "sent_at": datetime.now(timezone.utc).isoformat()}


@task(queue="reports", priority=Priority.NORMAL, timeout=120.0, tags=["reports"])
async def rebuild_daily_report(date: str) -> dict:
    await asyncio.sleep(0.01)
    return {"rebuilt": True, "date": date}


@task(queue="maintenance", schedule=every(minutes=30), tags=["maintenance"])
async def cleanup_old_jobs() -> dict:
    return {"cleaned": True, "checked_at": datetime.now(timezone.utc).isoformat()}
