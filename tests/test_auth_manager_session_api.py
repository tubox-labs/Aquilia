from __future__ import annotations

from unittest.mock import MagicMock

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

    key = KeyDescriptor.generate(kid="session-api-key", algorithm="HS256", secret="unit-test-secret")
    token_manager = TokenManager(key_ring=KeyRing(keys=[key]), token_store=token_store)

    manager = AuthManager(
        identity_store=identity_store,
        credential_store=credential_store,
        token_manager=token_manager,
        password_hasher=PasswordHasher(),
    )

    identity = Identity(
        id="user-session-api",
        type=IdentityType.USER,
        attributes={"email": "session@example.com", "username": "session_user", "roles": ["member"]},
    )

    return {
        "manager": manager,
        "identity_store": identity_store,
        "credential_store": credential_store,
        "token_store": token_store,
        "identity": identity,
        "credential_factory": PasswordCredential,
    }


async def _seed_password(auth_stack, plain_password: str = "top-secret"):
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
async def test_sign_in_with_new_session_forces_new_sid(auth_stack):
    await _seed_password(auth_stack)

    result = await auth_stack["manager"].sign_in(
        username="session@example.com",
        password="top-secret",
        session="new",
    )

    assert result.session_id is not None
    assert result.session_id.startswith("sess_")


@pytest.mark.asyncio
async def test_sign_in_with_explicit_session(auth_stack):
    await _seed_password(auth_stack)

    explicit_sid = "sess_explicit_aquilia_sid"
    result = await auth_stack["manager"].sign_in(
        username="session@example.com",
        password="top-secret",
        session=explicit_sid,
    )

    assert result.session_id == explicit_sid


@pytest.mark.asyncio
async def test_sign_out_scope_identity_revokes_identity_tokens(auth_stack):
    await _seed_password(auth_stack)

    result = await auth_stack["manager"].authenticate_password(
        username="session@example.com",
        password="top-secret",
    )

    summary = await auth_stack["manager"].sign_out(
        scope="identity",
        identity_id=auth_stack["identity"].id,
    )

    assert result.refresh_token is not None
    assert await auth_stack["token_store"].is_token_revoked(result.refresh_token) is True
    assert summary["revoked_identity"] is True


@pytest.mark.asyncio
async def test_sign_out_scope_session_uses_runtime_session(auth_stack):
    from aquilia.auth.integration.aquila_sessions import bind_identity
    from aquilia.auth.integration.runtime_context import (
        AuthRuntimeContext,
        reset_auth_runtime_context,
        set_auth_runtime_context,
    )
    from aquilia.sessions import Session, SessionID

    await _seed_password(auth_stack)

    session = Session(id=SessionID())
    bind_identity(session, auth_stack["identity"])

    token = set_auth_runtime_context(AuthRuntimeContext(request=MagicMock(), session=session))
    try:
        summary = await auth_stack["manager"].sign_out(scope="session")
    finally:
        reset_auth_runtime_context(token)

    assert summary["session_id"] == str(session.id)
    assert summary["revoked_session"] is True
    assert session.is_authenticated is False


@pytest.mark.asyncio
async def test_resume_identity_from_runtime_session(auth_stack):
    from aquilia.auth.integration.aquila_sessions import bind_identity
    from aquilia.auth.integration.runtime_context import (
        AuthRuntimeContext,
        reset_auth_runtime_context,
        set_auth_runtime_context,
    )
    from aquilia.sessions import Session, SessionID

    await _seed_password(auth_stack)

    session = Session(id=SessionID())
    bind_identity(session, auth_stack["identity"])

    token = set_auth_runtime_context(AuthRuntimeContext(request=MagicMock(), session=session))
    try:
        identity = await auth_stack["manager"].resume_identity()
    finally:
        reset_auth_runtime_context(token)

    assert identity is not None
    assert identity.id == auth_stack["identity"].id
