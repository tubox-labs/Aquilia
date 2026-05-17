import pytest

from modules.chat.services import ChatPresenceService


@pytest.mark.asyncio
async def test_presence_join_leave():
    service = ChatPresenceService()
    await service.join("lobby", "c1")
    await service.join("lobby", "c2")
    assert (await service.snapshot())["lobby"] == ["c1", "c2"]
    await service.leave("lobby", "c1")
    assert (await service.snapshot())["lobby"] == ["c2"]
