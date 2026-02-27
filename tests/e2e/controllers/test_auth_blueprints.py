import pytest
import uuid


pytestmark = pytest.mark.asyncio


def _unique_email(tag: str = "") -> str:
    return f"auth-bp-{tag}-{uuid.uuid4().hex[:8]}@test.com"


async def test_auth_workflow_with_blueprints(client):
    """
    Test the full registration and login flow using the new Blueprints.
    Targets endpoints:
    - POST /auth/register
    - POST /auth/login
    """
    email = _unique_email("full")
    password = "Str0ngP@ssword123!"
    
    # 1. Register with 'full_name' (E2E compatibility mode)
    reg_payload = {
        "email": email,
        "password": password,
        "full_name": "Blueprint Tester"
    }
    
    resp = await client.post("/auth/register", json=reg_payload)
    assert resp.status_code == 201, f"Registration failed: {resp.text}"
    
    user_data = resp.json()
    assert "name" in user_data
    assert user_data["name"]["first_name"] == "Blueprint"
    assert user_data["name"]["last_name"] == "Tester"
    
    # 2. Login
    login_payload = {
        "email": email,
        "password": password
    }
    
    resp = await client.post("/auth/login", json=login_payload)
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    
    tokens = resp.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "Bearer"


async def test_auth_registration_with_nested_blueprint(client):
    """
    Test registration using the nested 'name' Blueprint structure.
    """
    email = _unique_email("nested")
    reg_payload = {
        "email": email,
        "password": "Password123!",
        "username": "nested_user",
        "name": {
            "first_name": "Nested",
            "last_name": "Expert"
        }
    }
    
    resp = await client.post("/auth/register", json=reg_payload)
    assert resp.status_code == 201
    
    user_data = resp.json()
    assert user_data["name"]["first_name"] == "Nested"
    assert user_data["name"]["last_name"] == "Expert"


async def test_auth_list_simple_route(client):
    """
    Test the simple GET /auth/<name> route.
    """
    resp = await client.get("/auth/tester")
    assert resp.status_code == 200
    assert resp.json() == {"name": "tester"}
