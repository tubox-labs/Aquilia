import pytest

from examples.auth_app.modules.accounts.services import AccountsService


@pytest.mark.asyncio
async def test_register_then_login():
    service = AccountsService()
    await service.register({"email": "ada@example.com", "password": "password123", "name": "Ada"})
    result = await service.login({"email": "ada@example.com", "password": "password123"})
    assert result["access_token"]
    assert result["refresh_token"]
    assert result["identity"]["attributes"]["email"] == "ada@example.com"
