from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from aquilia.sessions import SessionScope


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
        scopes=SessionScope.USER,
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
async def test_sign_in_auto_provisions_identity_and_password_from_seed(auth_stack):
    from aquilia.auth.core import Identity, IdentityStatus, IdentityType

    seeded_identity = Identity(
        id="seed-user-1",
        type=IdentityType.USER,
        attributes={"email": "seed@example.com", "username": "seed_user", "roles": ["member"]},
        status=IdentityStatus.ACTIVE,
    )

    result = await auth_stack["manager"].sign_in(
        username="seed@example.com",
        password="seed-password",
        identity=seeded_identity,
    )

    assert result.identity.id == "seed-user-1"
    assert result.refresh_token is not None


@pytest.mark.asyncio
async def test_sign_in_identity_seed_backfills_missing_password_hash(auth_stack):
    from aquilia.auth.core import Identity, IdentityStatus, IdentityType

    seeded_identity = Identity(
        id="seed-user-2",
        type=IdentityType.USER,
        attributes={"email": "seed2@example.com", "username": "seed_user_2", "roles": ["member"]},
        status=IdentityStatus.ACTIVE,
    )

    await auth_stack["identity_store"].create(seeded_identity)

    result = await auth_stack["manager"].sign_in(
        username="seed2@example.com",
        password="seed2-password",
        identity=seeded_identity,
    )

    assert result.identity.id == "seed-user-2"
    password_cred = await auth_stack["credential_store"].get_password("seed-user-2")
    assert password_cred is not None


@pytest.mark.asyncio
async def test_sign_in_bootstraps_from_username_password_without_seed(auth_stack, monkeypatch):
    monkeypatch.setenv("AQUILIA_ENV", "dev")

    result = await auth_stack["manager"].sign_in(
        username="implicit@example.com",
        password="implicit-pass",
    )

    assert result.identity is not None
    assert result.identity.id.startswith("usr_")


@pytest.mark.asyncio
async def test_sign_in_bootstrap_enforces_password_after_first_sign_in(auth_stack, monkeypatch):
    from aquilia.auth.faults import AUTH_INVALID_CREDENTIALS

    monkeypatch.setenv("AQUILIA_ENV", "dev")

    await auth_stack["manager"].sign_in(
        username="sticky@example.com",
        password="first-pass",
    )

    with pytest.raises(AUTH_INVALID_CREDENTIALS):
        await auth_stack["manager"].sign_in(
            username="sticky@example.com",
            password="wrong-pass",
        )


@pytest.mark.asyncio
async def test_sign_in_normalizes_email_identifier(auth_stack):
    await _seed_password(auth_stack)

    result = await auth_stack["manager"].sign_in(
        username="  SESSION@EXAMPLE.COM  ",
        password="top-secret",
    )

    assert result.identity.id == auth_stack["identity"].id


@pytest.mark.asyncio
async def test_sign_in_in_prod_disables_implicit_username_bootstrap(auth_stack, monkeypatch):
    from aquilia.auth.faults import AUTH_INVALID_CREDENTIALS

    monkeypatch.setenv("AQUILIA_ENV", "prod")

    with pytest.raises(AUTH_INVALID_CREDENTIALS):
        await auth_stack["manager"].sign_in(
            username="prod-bootstrap@example.com",
            password="prod-pass",
        )


@pytest.mark.asyncio
async def test_sign_in_same_identity_in_runtime_session_raises_conflict(auth_stack):
    from aquilia.auth.integration.aquila_sessions import bind_identity
    from aquilia.auth.integration.runtime_context import (
        AuthRuntimeContext,
        reset_auth_runtime_context,
        set_auth_runtime_context,
    )
    from aquilia.faults.domains import ConflictFault
    from aquilia.sessions import Session, SessionID

    await _seed_password(auth_stack)

    session = Session(id=SessionID())
    bind_identity(session, auth_stack["identity"])

    runtime_token = set_auth_runtime_context(AuthRuntimeContext(request=MagicMock(), session=session))
    try:
        with pytest.raises(ConflictFault):
            await auth_stack["manager"].sign_in(
                username="session@example.com",
                password="top-secret",
            )
    finally:
        reset_auth_runtime_context(runtime_token)


@pytest.mark.asyncio
async def test_sign_in_supports_identity_without_email_via_login_identifier(auth_stack):
    from aquilia.auth.core import Identity, IdentityType, PasswordCredential

    identity = Identity(
        id="user-login-only",
        type=IdentityType.USER,
        attributes={"login": "alpha-login", "roles": ["member"]},
    )

    await auth_stack["identity_store"].create(identity)
    await auth_stack["credential_store"].save_password(
        PasswordCredential(
            identity_id=identity.id,
            password_hash=auth_stack["manager"].password_hasher.hash("alpha-pass"),
        )
    )

    result = await auth_stack["manager"].sign_in(
        username="alpha-login",
        password="alpha-pass",
    )

    assert result.identity.id == "user-login-only"


@pytest.mark.asyncio
async def test_sign_in_same_runtime_identity_conflict_without_email_attribute(auth_stack):
    from aquilia.auth.core import Identity, IdentityType
    from aquilia.auth.integration.aquila_sessions import bind_identity
    from aquilia.auth.integration.runtime_context import (
        AuthRuntimeContext,
        reset_auth_runtime_context,
        set_auth_runtime_context,
    )
    from aquilia.faults.domains import ConflictFault
    from aquilia.sessions import Session, SessionID

    identity = Identity(
        id="user-login-only-ctx",
        type=IdentityType.USER,
        attributes={"login": "ctx-login", "roles": ["member"]},
    )

    session = Session(id=SessionID())
    bind_identity(session, identity)

    runtime_token = set_auth_runtime_context(
        AuthRuntimeContext(request=MagicMock(), session=session, identity=identity)
    )
    try:
        with pytest.raises(ConflictFault):
            await auth_stack["manager"].sign_in(
                username="ctx-login",
                password="irrelevant-pass",
                identity=identity,
            )
    finally:
        reset_auth_runtime_context(runtime_token)


@pytest.mark.asyncio
async def test_sign_in_raises_429_for_new_identity_when_runtime_session_authenticated(auth_stack, monkeypatch):
    from aquilia.auth.integration.aquila_sessions import bind_identity
    from aquilia.auth.integration.runtime_context import (
        AuthRuntimeContext,
        reset_auth_runtime_context,
        set_auth_runtime_context,
    )
    from aquilia.faults.domains import TooManyRequestsFault
    from aquilia.sessions import Session, SessionID

    monkeypatch.setenv("AQUILIA_ENV", "dev")

    await _seed_password(auth_stack)

    session = Session(id=SessionID())
    bind_identity(session, auth_stack["identity"])

    runtime_token = set_auth_runtime_context(AuthRuntimeContext(request=MagicMock(), session=session))
    try:
        with pytest.raises(TooManyRequestsFault):
            await auth_stack["manager"].sign_in(
                username="brand-new-user@example.com",
                password="new-pass",
            )
    finally:
        reset_auth_runtime_context(runtime_token)


@pytest.mark.asyncio
async def test_sign_in_raises_429_for_identity_seed_switch_when_runtime_session_authenticated(auth_stack):
    from aquilia.auth.core import Identity, IdentityStatus, IdentityType
    from aquilia.auth.integration.aquila_sessions import bind_identity
    from aquilia.auth.integration.runtime_context import (
        AuthRuntimeContext,
        reset_auth_runtime_context,
        set_auth_runtime_context,
    )
    from aquilia.faults.domains import TooManyRequestsFault
    from aquilia.sessions import Session, SessionID

    await _seed_password(auth_stack)

    session = Session(id=SessionID())
    bind_identity(session, auth_stack["identity"])

    runtime_token = set_auth_runtime_context(AuthRuntimeContext(request=MagicMock(), session=session))
    try:
        with pytest.raises(TooManyRequestsFault):
            await auth_stack["manager"].sign_in(
                username="seed-switch@example.com",
                password="seed-switch-pass",
                identity=Identity(
                    id="other-user-id",
                    type=IdentityType.USER,
                    attributes={"email": "seed-switch@example.com"},
                    status=IdentityStatus.ACTIVE,
                ),
            )
    finally:
        reset_auth_runtime_context(runtime_token)


@pytest.mark.asyncio
async def test_sign_out_scope_identity_revokes_identity_tokens(auth_stack):
    await _seed_password(auth_stack)

    result = await auth_stack["manager"].authenticate_password(
        username="session@example.com",
        password="top-secret",
        scopes=SessionScope.USER,
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
async def test_sign_out_resolves_identity_and_session_from_access_token(auth_stack):
    await _seed_password(auth_stack)

    result = await auth_stack["manager"].authenticate_password(
        username="session@example.com",
        password="top-secret",
    )

    summary = await auth_stack["manager"].sign_out(
        scope="all",
        access_token=result.access_token,
    )

    assert summary["identity_id"] == auth_stack["identity"].id
    assert summary["session_id"] == result.session_id
    assert summary["revoked_access"] is True


@pytest.mark.asyncio
async def test_sign_out_clears_runtime_request_and_session_auth_state(auth_stack):
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

    request = MagicMock()
    request.state = {
        "identity": auth_stack["identity"],
        "authenticated": True,
        "auth": object(),
    }

    result = await auth_stack["manager"].authenticate_password(
        username="session@example.com",
        password="top-secret",
    )

    runtime_token = set_auth_runtime_context(AuthRuntimeContext(request=request, session=session))
    try:
        summary = await auth_stack["manager"].sign_out(
            scope="all",
            refresh_token=result.refresh_token,
        )
    finally:
        reset_auth_runtime_context(runtime_token)

    assert summary["runtime_context_cleared"] is True
    assert summary["request_state_cleared"] is True
    assert summary["session_state_cleared"] is True
    assert summary["revoked_refresh"] is True
    assert request.state.get("identity") is None
    assert request.state.get("authenticated") is False
    assert session.is_authenticated is False
    assert "identity_id" not in session.data


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
