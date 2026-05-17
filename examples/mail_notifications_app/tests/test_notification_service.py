import pytest

from examples.mail_notifications_app.modules.notifications.services import NotificationService


@pytest.mark.asyncio
async def test_welcome_message_writes_file_provider_output(tmp_path):
    service = NotificationService(output_dir=tmp_path)
    result = await service.send_welcome("new@example.test", "New User")
    await service.shutdown()

    assert result["sent"] is True
    assert result["to"] == ["new@example.test"]
    assert (tmp_path / "index.jsonl").exists()
    assert list(tmp_path.glob("*.eml"))
