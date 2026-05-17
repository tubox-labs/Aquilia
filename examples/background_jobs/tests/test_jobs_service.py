import pytest

from examples.background_jobs.modules.jobs.services import JobsService


@pytest.mark.asyncio
async def test_enqueue_welcome_job():
    service = JobsService()
    try:
        job_id = await service.send_welcome("test@example.com", "Test")
        assert job_id
        status = await service.job_status(job_id)
        assert status is not None
    finally:
        await service.manager.stop()
