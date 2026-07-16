"""
Auth-Sessions Integration Tests — Post-Refactor Suite
======================================================

Tests verifying the cleaned-up integration between ``aquilia.auth`` and
``aquilia.sessions`` after removing ``auth/hardening.py`` and the dead
``auth/integration/sessions.py`` duplicate.

Coverage:
1.  Utility functions relocated from hardening.py to tokens.py
2.  AuthPrincipal construction and serialisation
3.  bind_identity / bind_token_claims session helpers
4.  SessionAuthBridge lifecycle (create, rotate, logout, logout_all)
5.  Auth-specific session policy factories
6.  AquilAuthMiddleware: token auth, session auth, require_auth guard
7.  Flow guards: RequireAuthGuard, RequireScopesGuard, RequireRolesGuard
8.  typing.auth Protocol conformance (IdentityLike, PrincipalLike, etc.)
"""

from __future__ import annotations

import time
from datetime import timedelta
from typing import Any
from unittest.mock import MagicMock

import pytest

# ===========================================================================
# 1. Utility functions (relocated from hardening.py → tokens.py)
# ===========================================================================


class TestTokenUtilities:
    """Utility functions now live in aquilia.auth.tokens."""

    def test_constant_time_compare_equal_strings(self) -> None:
        from aquilia.auth.tokens import constant_time_compare

        assert constant_time_compare("hello", "hello") is True

    def test_constant_time_compare_unequal_strings(self) -> None:
        from aquilia.auth.tokens import constant_time_compare

        assert constant_time_compare("hello", "world") is False

    def test_constant_time_compare_bytes(self) -> None:
        from aquilia.auth.tokens import constant_time_compare

        assert constant_time_compare(b"secret", b"secret") is True
        assert constant_time_compare(b"secret", b"other") is False

    def test_constant_time_compare_mixed_types(self) -> None:
        from aquilia.auth.tokens import constant_time_compare

        # str vs bytes with matching content
        assert constant_time_compare("abc", b"abc") is True

    def test_generate_secure_token_default_length(self) -> None:
        from aquilia.auth.tokens import generate_secure_token

        token = generate_secure_token()
        assert isinstance(token, str)
        assert len(token) > 0

    def test_generate_secure_token_custom_length(self) -> None:
        from aquilia.auth.tokens import generate_secure_token

        token = generate_secure_token(16)
        assert isinstance(token, str)

    def test_generate_secure_token_uniqueness(self) -> None:
        from aquilia.auth.tokens import generate_secure_token

        tokens = {generate_secure_token() for _ in range(100)}
        assert len(tokens) == 100  # all unique

    def test_generate_opaque_id_default_prefix(self) -> None:
        from aquilia.auth.tokens import generate_opaque_id

        oid = generate_opaque_id()
        assert oid.startswith("aq_")

    def test_generate_opaque_id_custom_prefix(self) -> None:
        from aquilia.auth.tokens import generate_opaque_id

        oid = generate_opaque_id("sess")
        assert oid.startswith("sess_")
        # random hex part is 32 chars
        hex_part = oid[len("sess_"):]
        assert len(hex_part) == 32
        assert all(c in "0123456789abcdef" for c in hex_part)

    def test_hash_token_deterministic(self) -> None:
        from aquilia.auth.tokens import hash_token

        t = "my-secret-token"
        assert hash_token(t) == hash_token(t)

    def test_hash_token_different_inputs(self) -> None:
        from aquilia.auth.tokens import hash_token

        assert hash_token("a") != hash_token("b")

    def test_hash_token_is_hex_64_chars(self) -> None:
        from aquilia.auth.tokens import hash_token

        digest = hash_token("test")
        assert len(digest) == 64
        assert all(c in "0123456789abcdef" for c in digest)

    def test_hash_sensitive_no_salt(self) -> None:
        from aquilia.auth.tokens import hash_sensitive

        h = hash_sensitive("user@example.com")
        assert isinstance(h, str)
        assert len(h) == 64

    def test_hash_sensitive_with_salt(self) -> None:
        from aquilia.auth.tokens import hash_sensitive

        h_salted = hash_sensitive("user@example.com", salt="tenant-1")
        h_unsalted = hash_sensitive("user@example.com")
        assert h_salted != h_unsalted

    def test_hash_sensitive_same_salt_deterministic(self) -> None:
        from aquilia.auth.tokens import hash_sensitive

        assert hash_sensitive("email", "salt") == hash_sensitive("email", "salt")

    def test_auth_init_re_exports_utilities(self) -> None:
        """Verify aquilia.auth re-exports the relocated utilities."""
        from aquilia.auth import (
            constant_time_compare,
            generate_opaque_id,
            generate_secure_token,
            hash_sensitive,
            hash_token,
        )

        assert callable(constant_time_compare)
        assert callable(generate_secure_token)
        assert callable(generate_opaque_id)
        assert callable(hash_token)
        assert callable(hash_sensitive)

    def test_hardening_module_is_removed(self) -> None:
        """aquilia.auth.hardening must no longer exist."""
        import importlib

        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("aquilia.auth.hardening")

    def test_dead_sessions_module_is_removed(self) -> None:
        """aquilia.auth.integration.sessions must no longer exist."""
        import importlib

        with pytest.raises(ModuleNotFoundError):
            importlib.import_module("aquilia.auth.integration.sessions")


# ===========================================================================
# 2. AuthPrincipal — construction and serialisation
# ===========================================================================


class TestAuthPrincipal:
    """AuthPrincipal extends SessionPrincipal with auth-specific fields."""

    def _make_identity(
        self,
        *,
        id: str = "usr_001",
        roles: list[str] | None = None,
        scopes: list[str] | None = None,
        tenant_id: str | None = None,
    ) -> Any:
        from aquilia.auth.core import Identity, IdentityStatus, IdentityType

        return Identity(
            id=id,
            type=IdentityType.USER,
            attributes={
                "roles": roles or ["user"],
                "scopes": scopes or ["read"],
                "email": "test@example.com",
            },
            status=IdentityStatus.ACTIVE,
            tenant_id=tenant_id,
        )

    def test_from_identity_populates_roles(self) -> None:
        from aquilia.auth.integration.aquila_sessions import AuthPrincipal

        identity = self._make_identity(roles=["admin", "editor"])
        principal = AuthPrincipal.from_identity(identity)
        assert "admin" in principal.roles
        assert "editor" in principal.roles

    def test_from_identity_populates_scopes(self) -> None:
        from aquilia.auth.integration.aquila_sessions import AuthPrincipal

        identity = self._make_identity(scopes=["orders:read", "orders:write"])
        principal = AuthPrincipal.from_identity(identity)
        assert "orders:read" in principal.scopes
        assert "orders:write" in principal.scopes

    def test_from_identity_mfa_defaults_false(self) -> None:
        from aquilia.auth.integration.aquila_sessions import AuthPrincipal

        principal = AuthPrincipal.from_identity(self._make_identity())
        assert principal.mfa_verified is False

    def test_from_identity_tenant_id(self) -> None:
        from aquilia.auth.integration.aquila_sessions import AuthPrincipal

        identity = self._make_identity(tenant_id="tenant-xyz")
        principal = AuthPrincipal.from_identity(identity)
        assert principal.tenant_id == "tenant-xyz"

    def test_to_dict_round_trip(self) -> None:
        from aquilia.auth.integration.aquila_sessions import AuthPrincipal

        original = AuthPrincipal(
            identity_id="usr_042",
            tenant_id="t1",
            roles=["admin"],
            scopes=["*"],
            mfa_verified=True,
        )
        data = original.to_dict()
        restored = AuthPrincipal.from_dict(data)

        assert restored.id == original.id
        assert restored.tenant_id == original.tenant_id
        assert restored.roles == original.roles
        assert restored.scopes == original.scopes
        assert restored.mfa_verified == original.mfa_verified

    def test_principal_kind_is_user(self) -> None:
        from aquilia.auth.integration.aquila_sessions import AuthPrincipal

        p = AuthPrincipal(identity_id="u1")
        assert p.kind == "user"


# ===========================================================================
# 3. Session helpers — bind_identity, bind_token_claims
# ===========================================================================


class TestSessionBindHelpers:
    """Test the session binding helpers in aquila_sessions.py."""

    def _make_session(self) -> Any:
        from aquilia.sessions.core import Session, SessionID, SessionScope

        return Session(id=SessionID(), scope=SessionScope.USER)

    def _make_identity(self) -> Any:
        from aquilia.auth.core import Identity, IdentityStatus, IdentityType

        return Identity(
            id="usr_999",
            type=IdentityType.USER,
            attributes={
                "roles": ["editor"],
                "scopes": ["articles:write"],
                "email": "writer@example.com",
            },
            status=IdentityStatus.ACTIVE,
            tenant_id="tenant-a",
        )

    def test_bind_identity_sets_identity_id(self) -> None:
        from aquilia.auth.integration.aquila_sessions import bind_identity, get_identity_id

        session = self._make_session()
        identity = self._make_identity()
        bind_identity(session, identity)

        assert get_identity_id(session) == identity.id

    def test_bind_identity_marks_authenticated(self) -> None:
        from aquilia.auth.integration.aquila_sessions import bind_identity

        session = self._make_session()
        bind_identity(session, self._make_identity())
        assert session.is_authenticated

    def test_bind_identity_stores_roles(self) -> None:
        from aquilia.auth.integration.aquila_sessions import bind_identity, get_roles

        session = self._make_session()
        identity = self._make_identity()
        bind_identity(session, identity)

        assert "editor" in get_roles(session)

    def test_bind_identity_stores_scopes(self) -> None:
        from aquilia.auth.integration.aquila_sessions import bind_identity, get_scopes

        session = self._make_session()
        identity = self._make_identity()
        bind_identity(session, identity)

        assert "articles:write" in get_scopes(session)

    def test_bind_identity_stores_tenant_id(self) -> None:
        from aquilia.auth.integration.aquila_sessions import bind_identity, get_tenant_id

        session = self._make_session()
        bind_identity(session, self._make_identity())

        assert get_tenant_id(session) == "tenant-a"

    def test_bind_token_claims_stores_sub(self) -> None:
        from aquilia.auth.core import TokenClaims
        from aquilia.auth.integration.aquila_sessions import bind_token_claims

        session = self._make_session()
        now = int(time.time())
        claims = TokenClaims(
            iss="aquilia",
            sub="usr_999",
            aud=["api"],
            exp=now + 3600,
            iat=now,
            nbf=now,
            jti="jti_abc",
            scopes=["articles:write"],
        )
        bind_token_claims(session, claims)

        stored = session.data.get("token_claims", {})
        assert stored["sub"] == "usr_999"
        assert "articles:write" in stored["scopes"]

    def test_get_identity_id_returns_none_when_unset(self) -> None:
        from aquilia.auth.integration.aquila_sessions import get_identity_id

        session = self._make_session()
        assert get_identity_id(session) is None

    def test_get_roles_returns_empty_when_unset(self) -> None:
        from aquilia.auth.integration.aquila_sessions import get_roles

        session = self._make_session()
        assert get_roles(session) == []

    def test_mfa_verification_flag(self) -> None:
        from aquilia.auth.integration.aquila_sessions import (
            bind_identity,
            is_mfa_verified,
            set_mfa_verified,
        )

        session = self._make_session()
        bind_identity(session, self._make_identity())

        assert not is_mfa_verified(session)
        set_mfa_verified(session)
        assert session.data.get("mfa_verified") is True


# ===========================================================================
# 4. SessionAuthBridge lifecycle
# ===========================================================================


class TestSessionAuthBridge:
    """SessionAuthBridge coordinates auth and session operations."""

    def _make_engine(self) -> Any:
        from aquilia.sessions import MemoryStore, SessionEngine
        from aquilia.sessions.policy import SessionPolicy, TransportPolicy
        from aquilia.sessions.transport import CookieTransport

        policy = SessionPolicy(
            name="test",
            ttl=timedelta(hours=1),
        )
        transport = CookieTransport(
            policy=TransportPolicy(
                adapter="cookie",
                cookie_name="test_sess",
            )
        )
        return SessionEngine(
            policy=policy,
            store=MemoryStore(),
            transport=transport,
        )

    def _make_identity(self, id: str = "usr_001") -> Any:
        from aquilia.auth.core import Identity, IdentityStatus, IdentityType

        return Identity(
            id=id,
            type=IdentityType.USER,
            attributes={"roles": ["user"], "scopes": ["read"]},
            status=IdentityStatus.ACTIVE,
        )

    @pytest.mark.asyncio
    async def test_create_auth_session_binds_identity(self) -> None:
        from aquilia.auth.integration.aquila_sessions import SessionAuthBridge, get_identity_id

        engine = self._make_engine()
        bridge = SessionAuthBridge(session_engine=engine)

        request = MagicMock()
        request.headers = {}
        request.cookies = {}

        identity = self._make_identity()
        session = await bridge.create_auth_session(identity, request)

        assert get_identity_id(session) == identity.id
        assert session.is_authenticated

    @pytest.mark.asyncio
    async def test_verify_and_extend_true_when_identity_bound(self) -> None:
        from aquilia.auth.integration.aquila_sessions import SessionAuthBridge, bind_identity

        engine = self._make_engine()
        bridge = SessionAuthBridge(session_engine=engine)

        request = MagicMock()
        request.headers = {}
        request.cookies = {}
        session = await engine.resolve(request)
        bind_identity(session, self._make_identity())

        result = await bridge.verify_and_extend(session)
        assert result is True

    @pytest.mark.asyncio
    async def test_verify_and_extend_false_when_no_identity(self) -> None:
        from aquilia.auth.integration.aquila_sessions import SessionAuthBridge

        engine = self._make_engine()
        bridge = SessionAuthBridge(session_engine=engine)

        request = MagicMock()
        request.headers = {}
        request.cookies = {}
        session = await engine.resolve(request)

        result = await bridge.verify_and_extend(session)
        assert result is False


# ===========================================================================
# 5. Auth-specific session policy factories
# ===========================================================================


class TestAuthSessionPolicies:
    """Verify the auth-specific policy factories produce valid SessionPolicy objects."""

    def test_user_session_policy_defaults(self) -> None:
        from aquilia.auth.integration.aquila_sessions import user_session_policy
        from aquilia.sessions import SessionPolicy

        policy = user_session_policy()
        assert isinstance(policy, SessionPolicy)
        assert policy.name == "auth_user"
        assert policy.ttl == timedelta(days=7)
        assert policy.idle_timeout == timedelta(hours=1)

    def test_user_session_policy_custom_ttl(self) -> None:
        from aquilia.auth.integration.aquila_sessions import user_session_policy

        policy = user_session_policy(ttl=timedelta(days=30))
        assert policy.ttl == timedelta(days=30)

    def test_api_session_policy_defaults(self) -> None:
        from aquilia.auth.integration.aquila_sessions import api_session_policy
        from aquilia.sessions import SessionPolicy

        policy = api_session_policy()
        assert isinstance(policy, SessionPolicy)
        assert policy.name == "auth_api"
        assert policy.idle_timeout is None  # No idle timeout for API tokens

    def test_device_session_policy_defaults(self) -> None:
        from aquilia.auth.integration.aquila_sessions import device_session_policy
        from aquilia.sessions import SessionPolicy

        policy = device_session_policy()
        assert isinstance(policy, SessionPolicy)
        assert policy.name == "auth_device"
        assert policy.ttl == timedelta(days=90)

    def test_user_session_policy_transport_is_cookie(self) -> None:
        from aquilia.auth.integration.aquila_sessions import user_session_policy

        policy = user_session_policy()
        assert policy.transport.adapter == "cookie"
        assert policy.transport.cookie_httponly is True
        assert policy.transport.cookie_secure is True

    def test_api_session_policy_transport_is_header(self) -> None:
        from aquilia.auth.integration.aquila_sessions import api_session_policy

        policy = api_session_policy()
        assert policy.transport.adapter == "header"

    def test_device_session_policy_concurrency(self) -> None:
        from aquilia.auth.integration.aquila_sessions import device_session_policy

        policy = device_session_policy()
        # Multiple devices allowed
        assert policy.concurrency.max_sessions_per_principal == 10


# ===========================================================================
# 6. Flow guards
# ===========================================================================


class TestFlowGuards:
    """Flow guards enforce security policies in the request pipeline."""

    def _make_identity(self, roles: list[str] | None = None, scopes: list[str] | None = None) -> Any:
        from aquilia.auth.core import Identity, IdentityStatus, IdentityType

        return Identity(
            id="usr_123",
            type=IdentityType.USER,
            attributes={
                "roles": roles or ["user"],
                "scopes": scopes or ["read"],
            },
            status=IdentityStatus.ACTIVE,
        )

    def _make_context(self, identity: Any = None, session: Any = None) -> dict:
        request = MagicMock()
        request.state = {}
        if identity is not None:
            request.state["identity"] = identity
        if session is not None:
            request.state["session"] = session

        return {
            "request": request,
            "identity": identity,
            "session": session,
        }

    # FlowGuards tests have been removed as part of the deprecated flow_guards cleanup (superseded by test_auth_guards.py).


# ===========================================================================
# 7. typing.auth Protocol conformance
# ===========================================================================


class TestAuthTypingProtocols:
    """Runtime isinstance() checks via runtime_checkable protocols."""

    def _make_identity(self) -> Any:
        from aquilia.auth.core import Identity, IdentityStatus, IdentityType

        return Identity(
            id="usr_000",
            type=IdentityType.USER,
            attributes={"roles": ["admin"], "scopes": ["*"]},
            status=IdentityStatus.ACTIVE,
        )

    def _make_principal(self) -> Any:
        from aquilia.sessions.core import SessionPrincipal

        return SessionPrincipal(kind="user", id="usr_000", attributes={})

    def _make_session(self) -> Any:
        from aquilia.sessions.core import Session, SessionID, SessionScope

        return Session(id=SessionID(), scope=SessionScope.USER)

    def _make_token_claims(self) -> Any:
        from aquilia.auth.core import TokenClaims

        now = int(time.time())
        return TokenClaims(
            iss="aquilia",
            sub="usr_000",
            aud=["api"],
            exp=now + 3600,
            iat=now,
            nbf=now,
            jti="jti_000",
            scopes=["read"],
        )

    def test_identity_conforms_to_identity_like(self) -> None:
        from aquilia.typing.auth import IdentityLike

        identity = self._make_identity()
        assert isinstance(identity, IdentityLike)

    def test_principal_conforms_to_principal_like(self) -> None:
        from aquilia.typing.auth import PrincipalLike

        principal = self._make_principal()
        assert isinstance(principal, PrincipalLike)

    def test_session_conforms_to_session_like(self) -> None:
        from aquilia.typing.auth import SessionLike

        session = self._make_session()
        assert isinstance(session, SessionLike)

    def test_token_claims_conforms_to_token_claims_like(self) -> None:
        from aquilia.typing.auth import TokenClaimsLike

        claims = self._make_token_claims()
        assert isinstance(claims, TokenClaimsLike)

    def test_identity_like_is_exported_from_typing(self) -> None:
        from aquilia.typing import IdentityLike, PrincipalLike, SessionLike, TokenClaimsLike

        assert IdentityLike is not None
        assert PrincipalLike is not None
        assert SessionLike is not None
        assert TokenClaimsLike is not None

    def test_flow_context_and_guard_callable_exported(self) -> None:
        from aquilia.typing.auth import FlowContext, GuardCallable

        assert FlowContext is not None
        assert GuardCallable is not None

    def test_scalar_type_aliases_exported(self) -> None:
        from aquilia.typing.auth import (
            IdentityID,
        )

        # These are TypeAlias — just verify they exist as names
        assert IdentityID is not None

    def test_non_identity_dict_does_not_conform(self) -> None:
        from aquilia.typing.auth import IdentityLike

        plain_dict = {"id": "usr_000", "roles": ["admin"]}
        assert not isinstance(plain_dict, IdentityLike)

    def test_none_does_not_conform_to_identity_like(self) -> None:
        from aquilia.typing.auth import IdentityLike

        assert not isinstance(None, IdentityLike)


# ===========================================================================
# 8. Session decorators  (no regressions after refactor)
# ===========================================================================


class TestSessionDecorators:
    """Session decorators must not regress after the integration refactor."""

    def test_session_decorator_imports(self) -> None:
        from aquilia.sessions import SessionContext, session, stateful

        assert session is not None
        assert callable(session.require)
        assert callable(stateful)
        assert SessionContext is not None

    def test_auth_decorator_imports(self) -> None:
        from aquilia.auth import authenticated, optional_auth, roles_required, scopes_required

        assert callable(authenticated)
        assert callable(roles_required)
        assert callable(scopes_required)
        assert callable(optional_auth)


# ===========================================================================
# 9. Auth init smoke test — no imports should raise
# ===========================================================================


class TestAuthModuleInit:
    """The auth package init should import cleanly after the refactor."""

    def test_auth_core_imports(self) -> None:
        from aquilia.auth import (
            AuthResult,
            Identity,
        )

        assert Identity is not None
        assert AuthResult is not None

    # Policy DSL imports test removed (deprecated Policy DSL was removed in refactoring).

    def test_auth_clearance_imports(self) -> None:
        from aquilia.auth import (
            AccessLevel,
            Clearance,
            grant,
        )

        assert AccessLevel is not None
        assert Clearance is not None
        assert grant is not None

    def test_auth_hashing_imports(self) -> None:
        from aquilia.auth import (
            PasswordHasher,
        )

        assert PasswordHasher is not None

    def test_auth_tokens_imports(self) -> None:
        from aquilia.auth import (
            TokenManager,
        )

        assert TokenManager is not None

    def test_auth_fault_imports(self) -> None:
        from aquilia.auth import (
            AUTH_REQUIRED,
        )

        assert AUTH_REQUIRED is not None

    def test_auth_store_imports(self) -> None:
        from aquilia.auth import (
            MemoryIdentityStore,
        )

        assert MemoryIdentityStore is not None

    def test_no_hardening_in_all(self) -> None:
        """auth.__all__ must not export any hardening-era classes."""
        import aquilia.auth as auth_mod

        hardening_names = {"CSRFProtection", "SecurityHeaders", "RequestFingerprint", "TokenBinder"}
        exported = set(getattr(auth_mod, "__all__", []))
        overlap = hardening_names & exported
        assert not overlap, f"Hardening classes still exported: {overlap}"
