from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def auth_stack():
    from aquilia.auth.core import Identity, IdentityType, PasswordCredential
    from aquilia.auth.hashing import PasswordHasher
    from aquilia.auth.manager import AuthManager
    from aquilia.auth.stores import MemoryCredentialStore, MemoryIdentityStore, MemoryTokenStore
    from aquilia.auth.tokens import KeyDescriptor, KeyRing, TokenManager

    identity_store = MemoryIdentityStore()
    credential_store = MemoryCredentialStore()
    token_store = MemoryTokenStore()

    key = KeyDescriptor.generate(kid="test-key", algorithm="HS256", secret="unit-test-secret")
    token_manager = TokenManager(key_ring=KeyRing(keys=[key]), token_store=token_store)

    manager = AuthManager(
        identity_store=identity_store,
        credential_store=credential_store,
        token_manager=token_manager,
        password_hasher=PasswordHasher(),
    )

    identity = Identity(
        id="user-1",
        type=IdentityType.USER,
        attributes={"email": "dev@example.com", "roles": ["member"]},
    )

    return {
        "manager": manager,
        "identity_store": identity_store,
        "credential_store": credential_store,
        "token_store": token_store,
        "identity": identity,
        "credential_factory": PasswordCredential,
    }


async def _seed_password(auth_stack, plain_password: str = "secret-pass"):
    manager = auth_stack["manager"]
    identity_store = auth_stack["identity_store"]
    credential_store = auth_stack["credential_store"]
    identity = auth_stack["identity"]
    credential_factory = auth_stack["credential_factory"]

    await identity_store.create(identity)
    await credential_store.save_password(
        credential_factory(identity_id=identity.id, password_hash=manager.password_hasher.hash(plain_password))
    )


@pytest.mark.asyncio
async def test_auth_manager_uses_runtime_session_id_and_binds_identity(auth_stack):
    from aquilia.auth.integration.runtime_context import (
        AuthRuntimeContext,
        reset_auth_runtime_context,
        set_auth_runtime_context,
    )
    from aquilia.sessions import Session, SessionID

    await _seed_password(auth_stack)

    session = Session(id=SessionID())
    token = set_auth_runtime_context(AuthRuntimeContext(request=MagicMock(), session=session))

    try:
        result = await auth_stack["manager"].authenticate_password(
            username="dev@example.com",
            password="secret-pass",
        )
    finally:
        reset_auth_runtime_context(token)

    assert result.session_id == str(session.id)
    assert session.is_authenticated is True
    assert session.data["identity_id"] == "user-1"

    claims = await auth_stack["manager"].verify_token(result.access_token)
    assert claims.sid == str(session.id)


@pytest.mark.asyncio
async def test_explicit_session_id_overrides_runtime_session_binding(auth_stack):
    from aquilia.auth.integration.runtime_context import (
        AuthRuntimeContext,
        reset_auth_runtime_context,
        set_auth_runtime_context,
    )
    from aquilia.sessions import Session, SessionID

    await _seed_password(auth_stack)

    session = Session(id=SessionID())
    explicit_sid = "sess_explicit_external"

    token = set_auth_runtime_context(AuthRuntimeContext(request=MagicMock(), session=session))
    try:
        result = await auth_stack["manager"].authenticate_password(
            username="dev@example.com",
            password="secret-pass",
            session_id=explicit_sid,
        )
    finally:
        reset_auth_runtime_context(token)

    assert result.session_id == explicit_sid
    assert session.is_authenticated is False
    assert "identity_id" not in session.data


@pytest.mark.asyncio
async def test_auth_manager_outside_request_generates_session_id(auth_stack):
    await _seed_password(auth_stack)

    result = await auth_stack["manager"].authenticate_password(
        username="dev@example.com",
        password="secret-pass",
    )

    assert result.session_id is not None
    assert result.session_id.startswith("sess_")


@pytest.mark.asyncio
async def test_logout_uses_runtime_session_id_when_missing(auth_stack):
    from aquilia.auth.integration.runtime_context import (
        AuthRuntimeContext,
        reset_auth_runtime_context,
        set_auth_runtime_context,
    )
    from aquilia.sessions import Session, SessionID

    await _seed_password(auth_stack)

    session = Session(id=SessionID())

    token = set_auth_runtime_context(AuthRuntimeContext(request=MagicMock(), session=session))
    try:
        result = await auth_stack["manager"].authenticate_password(
            username="dev@example.com",
            password="secret-pass",
        )
        await auth_stack["manager"].logout()
    finally:
        reset_auth_runtime_context(token)

    assert result.refresh_token is not None
    assert await auth_stack["token_store"].is_token_revoked(result.refresh_token) is True
    assert session.is_authenticated is False


@pytest.mark.asyncio
async def test_auth_middleware_sets_and_resets_runtime_context():
    from aquilia.auth.integration.middleware import AquilAuthMiddleware
    from aquilia.auth.integration.runtime_context import get_auth_runtime_context

    session = MagicMock()
    session.is_authenticated = False

    session_engine = MagicMock()
    session_engine.resolve = AsyncMock(return_value=session)
    session_engine.commit = AsyncMock(return_value=None)

    auth_manager = MagicMock()
    auth_manager.get_identity_from_token = AsyncMock(return_value=None)

    middleware = AquilAuthMiddleware(session_engine=session_engine, auth_manager=auth_manager)

    request = MagicMock()
    request.state = {}
    request.header = lambda _name: None

    ctx = MagicMock()
    ctx.container = None
    ctx.session = None
    ctx.identity = None

    async def next_handler(_request, _ctx):
        runtime = get_auth_runtime_context()
        assert runtime is not None
        assert runtime.session is session
        return MagicMock()

    response = await middleware(request, ctx, next_handler)

    assert response is not None
    assert get_auth_runtime_context() is None
    session_engine.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_auth_manager_auto_provisions_identity_and_credential_stores():
    from aquilia.auth.manager import AuthManager
    from aquilia.auth.stores import MemoryTokenStore
    from aquilia.auth.tokens import KeyDescriptor, KeyRing, TokenManager

    key = KeyDescriptor.generate(kid="test-key", algorithm="HS256", secret="unit-test-secret")
    token_manager = TokenManager(key_ring=KeyRing(keys=[key]), token_store=MemoryTokenStore())

    manager = AuthManager(token_manager=token_manager)

    assert manager.identity_store is not None
    assert manager.credential_store is not None


@pytest.mark.asyncio
async def test_auth_middleware_populates_request_and_ctx_auth_data():
    from aquilia.auth.integration.middleware import AquilAuthMiddleware

    session = MagicMock()
    session.is_authenticated = False

    session_engine = MagicMock()
    session_engine.resolve = AsyncMock(return_value=session)
    session_engine.commit = AsyncMock(return_value=None)

    auth_manager = MagicMock()
    auth_manager.get_identity_from_token = AsyncMock(return_value=None)

    middleware = AquilAuthMiddleware(session_engine=session_engine, auth_manager=auth_manager)

    request = MagicMock()
    request.state = {}
    request.header = lambda _name: None

    ctx = MagicMock()
    ctx.container = None
    ctx.session = None
    ctx.identity = None
    ctx.auth = None

    async def next_handler(_request, _ctx):
        assert _request.state["session"] is session
        assert "auth" in _request.state
        assert _ctx.session is session
        assert _ctx.auth is _request.state["auth"]
        return MagicMock()

    response = await middleware(request, ctx, next_handler)

    assert response is not None
    assert request.state["session"] is session
    assert "auth" in request.state
