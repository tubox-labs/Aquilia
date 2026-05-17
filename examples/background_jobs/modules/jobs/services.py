from __future__ import annotations

from aquilia.tasks import TaskManager

from .tasks import rebuild_daily_report, send_welcome_email


class JobsService:
    def __init__(self, manager: TaskManager | None = None):
        self.manager = manager or TaskManager(num_workers=2, default_queue="default", scheduler_tick=10.0)

    async def ensure_started(self):
        if not self.manager.is_running:
            await self.manager.start()

    async def send_welcome(self, email: str, name: str) -> str:
        await self.ensure_started()
        return await send_welcome_email.delay(email=email, name=name)

    async def rebuild_report(self, date: str) -> str:
        await self.ensure_started()
        return await self.manager.enqueue(rebuild_daily_report, date=date, queue="reports")

    async def job_status(self, job_id: str):
        await self.ensure_started()
        job = await self.manager.get_job(job_id)
        return job.to_dict() if job else None

    async def stats(self):
        await self.ensure_started()
        return await self.manager.get_stats()
