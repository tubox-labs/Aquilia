import pytest

from modules.projects.services import ProjectsService


@pytest.mark.asyncio
async def test_project_lifecycle():
    service = ProjectsService()
    created = await service.create_project(
        {"key": "api", "name": "API", "owner_email": "owner@example.com", "status": "active"}
    )
    assert created["key"] == "api"

    archived = await service.archive_project("api")
    assert archived["archived"] is True

    restored = await service.restore_project("api")
    assert restored["archived"] is False
