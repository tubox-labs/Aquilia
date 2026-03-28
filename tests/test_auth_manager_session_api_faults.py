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

    key = KeyDescriptor.generate(kid="fault-tests-key", algorithm="HS256", secret="unit-test-secret")
    token_manager = TokenManager(key_ring=KeyRing(keys=[key]), token_store=token_store)

    manager = AuthManager(
        identity_store=identity_store,
        credential_store=credential_store,
        token_manager=token_manager,
        password_hasher=PasswordHasher(),
    )

    identity = Identity(
        id="user-fault-tests",
        type=IdentityType.USER,
        attributes={"email": "fault@example.com", "username": "fault_user", "roles": ["member"]},
    )

    return {
        "manager": manager,
        "identity_store": identity_store,
        "credential_store": credential_store,
        "token_store": token_store,
        "identity": identity,
        "credential_factory": PasswordCredential,
    }


async def _seed_password(auth_stack, plain_password: str = "test-secret"):
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
async def test_sign_in_rejects_empty_explicit_session(auth_stack):
    from aquilia.faults.domains import ConfigInvalidFault

    await _seed_password(auth_stack)

    with pytest.raises(ConfigInvalidFault):
        await auth_stack["manager"].sign_in(
            username="fault@example.com",
            password="test-secret",
            session="",
        )


@pytest.mark.asyncio
async def test_sign_out_identity_scope_requires_identity(auth_stack):
    from aquilia.auth.faults import AUTH_REQUIRED

    with pytest.raises(AUTH_REQUIRED):
        await auth_stack["manager"].sign_out(scope="identity")


@pytest.mark.asyncio
async def test_sign_out_session_scope_requires_session(auth_stack):
    from aquilia.auth.faults import AUTH_SESSION_REQUIRED

    with pytest.raises(AUTH_SESSION_REQUIRED):
        await auth_stack["manager"].sign_out(scope="session")


@pytest.mark.asyncio
async def test_sign_out_all_scope_uses_runtime_identity_and_session(auth_stack):
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

    runtime_token = set_auth_runtime_context(AuthRuntimeContext(request=MagicMock(), session=session))
    try:
        summary = await auth_stack["manager"].sign_out(scope="all")
    finally:
        reset_auth_runtime_context(runtime_token)

    assert summary["revoked_identity"] is True
    assert summary["revoked_session"] is True
    assert summary["identity_id"] == auth_stack["identity"].id
    assert summary["session_id"] == str(session.id)
