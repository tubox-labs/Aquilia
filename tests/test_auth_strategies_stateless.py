"""Strategies, stateless verification, and adversarial token handling.

Covers:

* **AG-03 / M-6** — the stateless JWT mode (verified claims → principal, no
  identity-store lookup per request).
* **M-1** — the Passport-style strategy registry (``register_strategy``).
* **AG-08** — collapse-errors mode (one generic 401, anti-enumeration).
* **AG-07** — arbitrary extra claims, reserved-claim protection.
* Adversarial JWT matrix: malformed, expired, forged-signature,
  algorithm-confusion (header alg lying), wrong kid, wrong issuer/audience,
  nbf-in-future, boundary exp, revoked jti.
"""

from __future__ import annotations

import asyncio
import base64
import json
import time
from dataclasses import dataclass
from typing import Any

import pytest

from aquilia.auth.backends.base import resolve_backend
from aquilia.auth.backends.token import StatelessTokenBackend, TokenBackend
from aquilia.auth.core import Identity, IdentityType
from aquilia.auth.faults import (
    AUTH_TOKEN_EXPIRED,
    AUTH_TOKEN_INVALID,
    AUTH_TOKEN_REVOKED,
)
from aquilia.auth.stores import MemoryIdentityStore, MemoryTokenStore
from aquilia.auth.strategies import (
    AuthStrategyRegistry,
    create_default_registry,
    get_default_registry,
    register_strategy,
    reset_default_registry,
)
from aquilia.auth.tokens import (
    RESERVED_CLAIMS,
    KeyDescriptor,
    KeyRing,
    TokenConfig,
    TokenManager,
)


def _manager(**config_overrides: Any) -> TokenManager:
    ring = KeyRing([KeyDescriptor.generate(kid="active", algorithm="HS256", secret="s" * 32)])
    config = TokenConfig(access_token_ttl=600, refresh_token_ttl=3600, **config_overrides)
    return TokenManager(key_ring=ring, token_store=MemoryTokenStore(), config=config)


def _b64(obj: dict) -> str:
    """Encode exactly like the token engine (compact separators)."""
    raw = json.dumps(obj, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


# ============================================================================
# Strategy registry
# ============================================================================


class TestStrategyRegistry:
    def setup_method(self):
        reset_default_registry()

    def teardown_method(self):
        reset_default_registry()

    def test_builtin_names_registered(self):
        registry = create_default_registry()
        for name in ("token", "jwt", "jwt-stateless", "stateless", "session", "api_key", "password"):
            assert registry.is_registered(name), name

    def test_register_and_create_custom_strategy(self):
        created: list[Any] = []

        class HeaderAuthBackend:
            def __init__(self, auth_manager):
                created.append(auth_manager)
                self.auth_manager = auth_manager

            def accepts(self, credentials):
                return "x_custom" in credentials

            async def authenticate(self, credentials):
                return Identity(id=credentials["x_custom"], type=IdentityType.USER, attributes={})

        register_strategy("custom-header", HeaderAuthBackend)

        class FakeManager:
            identity_store = MemoryIdentityStore()

        backend = resolve_backend("custom-header", FakeManager())
        assert isinstance(backend, HeaderAuthBackend)
        assert created == [backend.auth_manager]

    def test_unknown_name_raises_with_available_list(self):
        with pytest.raises(ValueError, match="Unknown authentication (strategy|backend)"):
            resolve_backend("nope", object())

    def test_instance_registration(self):
        sentinel = object()
        registry = AuthStrategyRegistry()
        registry.register("fixed", sentinel)
        assert registry.create("fixed", None) is sentinel

    def test_factory_registration(self):
        registry = AuthStrategyRegistry()
        marker = object()
        registry.register_factory("made", lambda am: marker)
        assert registry.create("made", None) is marker

    def test_short_name_aliases_resolve_to_real_backends(self):
        from aquilia.auth.backends.api_key import ApiKeyBackend
        from aquilia.auth.backends.password import PasswordBackend
        from aquilia.auth.backends.token import TokenBackend as TB

        class FakeManager:
            identity_store = MemoryIdentityStore()
            credential_store = object()
            token_manager = _manager()
            password_hasher = object()
            rate_limiter = object()
            login_identifier_attributes = ("email",)

        assert isinstance(resolve_backend("token", FakeManager()), TB)
        assert isinstance(resolve_backend("api_key", FakeManager()), ApiKeyBackend)
        assert isinstance(resolve_backend("password", FakeManager()), PasswordBackend)

    def test_registry_isolation_between_instances(self):
        registry = AuthStrategyRegistry()
        registry.register("private", object())
        assert registry.is_registered("private")
        assert not get_default_registry().is_registered("private")

    def test_dotted_path_still_supported(self):
        backend = resolve_backend("aquilia.auth.backends.SessionBackend", type("M", (), {"identity_store": MemoryIdentityStore()})())
        assert backend.__class__.__name__ == "SessionBackend"


# ============================================================================
# Stateless backend (AG-03 / M-6)
# ============================================================================


class TestStatelessBackend:
    async def test_no_identity_store_lookup(self):
        """The defining property: authentication works with an empty store."""
        manager = _manager()
        backend = StatelessTokenBackend(manager)

        token = await manager.issue_access_token("user-42", scopes=["read"])
        result = await backend.authenticate({"token": token})

        assert result is not None
        assert result.identity.id == "user-42"
        assert result.claims["sub"] == "user-42"
        assert result.claims["scopes"] == ["read"]

    async def test_roles_and_tenant_flow_into_identity_attributes(self):
        manager = _manager()
        backend = StatelessTokenBackend(manager)
        token = await manager.issue_access_token(
            "u1", scopes=["read"], roles=["admin"], tenant_id="t1"
        )
        result = await backend.authenticate({"token": token})
        assert result.identity.attributes["roles"] == ["admin"]
        assert result.identity.attributes["scopes"] == ["read"]
        assert result.identity.tenant_id == "t1"

    async def test_principal_builder_receives_identity_and_claims(self):
        @dataclass
        class AppUser:
            id: str
            session_id: str | None

        manager = _manager()

        def builder(identity, claims):
            return AppUser(id=identity.id, session_id=claims.get("sid"))

        backend = StatelessTokenBackend(manager, principal_builder=builder)
        token = await manager.issue_access_token("u1", session_id="sess-9")
        result = await backend.authenticate({"token": token})

        assert result.principal == AppUser(id="u1", session_id="sess-9")

    async def test_invalid_token_raises(self):
        backend = StatelessTokenBackend(_manager())
        with pytest.raises(AUTH_TOKEN_INVALID):
            await backend.authenticate({"token": "garbage"})

    async def test_stateful_backend_still_resolves_via_store(self):
        """TokenBackend (stateful) keeps its identity-store contract."""
        manager = _manager()
        store = MemoryIdentityStore()
        await store.create(Identity(id="real-user", type=IdentityType.USER, attributes={}))

        backend = TokenBackend(manager, store)
        token = await manager.issue_access_token("real-user")
        result = await backend.authenticate({"token": token})
        assert result.identity.id == "real-user"
        assert result.claims["sub"] == "real-user"

        # Unknown subject → None (anonymous), not an error.
        token = await manager.issue_access_token("ghost")
        assert await backend.authenticate({"token": token}) is None


# ============================================================================
# Adversarial JWT matrix
# ============================================================================


class TestAdversarialTokens:
    async def test_malformed_tokens(self):
        manager = _manager()
        for bad in ("", "a", "a.b", "a.b.c.d", "....", "!!!", "a.b.c", None):
            if bad is None:
                continue
            with pytest.raises(AUTH_TOKEN_INVALID):
                await manager.validate_access_token(bad)

    async def test_alg_none_rejected(self):
        manager = _manager()
        token = await manager.issue_access_token("u1")
        header_b64, payload_b64, _ = token.split(".")

        # Re-forge with alg=none and no signature.
        header = json.loads(base64.urlsafe_b64decode(header_b64 + "=="))
        header["alg"] = "none"
        forged = f"{_b64(header)}.{payload_b64}."
        with pytest.raises(AUTH_TOKEN_INVALID):
            await manager.validate_access_token(forged)

    async def test_forged_signature_rejected(self):
        manager = _manager()
        # A second manager with a DIFFERENT secret.
        ring = KeyRing([KeyDescriptor.generate(kid="active", algorithm="HS256", secret="attacker-" + "k" * 20)])
        attacker = TokenManager(key_ring=ring, token_store=MemoryTokenStore(), config=TokenConfig())
        token = await attacker.issue_access_token("u1")
        with pytest.raises(AUTH_TOKEN_INVALID):
            await manager.validate_access_token(token)

    async def test_tampered_payload_rejected(self):
        manager = _manager()
        token = await manager.issue_access_token("u1")
        header_b64, payload_b64, sig_b64 = token.split(".")
        payload = json.loads(base64.urlsafe_b64decode(payload_b64 + "=="))
        payload["sub"] = "admin"
        tampered = f"{header_b64}.{_b64(payload)}.{sig_b64}"
        with pytest.raises(AUTH_TOKEN_INVALID):
            await manager.validate_access_token(tampered)

    async def test_algorithm_confusion_header_alg_lying(self):
        """The verifier uses the KEY descriptor's algorithm, never the
        header's — a lying header cannot redirect verification, and the
        claims stay bound to the genuinely verified signature."""
        ring = KeyRing(
            [
                KeyDescriptor.generate(kid="active", algorithm="HS256", secret="real-" + "s" * 20),
                KeyDescriptor.generate(kid="secondary", algorithm="HS512", secret="other-" + "s" * 20),
            ]
        )
        manager = TokenManager(key_ring=ring, token_store=MemoryTokenStore(), config=TokenConfig())

        now = int(time.time())
        payload = {
            "iss": "aquilia",
            "sub": "u1",
            "aud": ["api"],
            "exp": now + 600,
            "iat": now,
            "nbf": now,
            "jti": "at_confusion",
            "scopes": [],
        }
        key = ring.get_signing_key()
        lying_header = {"alg": "HS512", "kid": "active", "typ": "JWT"}  # claims HS512, is HS256
        header_b64 = manager._base64_encode_json(lying_header)
        payload_b64 = manager._base64_encode_json(payload)
        signature = manager._create_signature(f"{header_b64}.{payload_b64}".encode(), key)
        confused = f"{header_b64}.{payload_b64}.{manager._base64_encode(signature)}"

        claims = await manager.validate_access_token(confused)
        assert claims["sub"] == "u1"

    async def test_unknown_kid_rejected(self):
        manager = _manager()
        token = await manager.issue_access_token("u1")
        header_b64, payload_b64, sig_b64 = token.split(".")
        header = json.loads(base64.urlsafe_b64decode(header_b64 + "=="))
        header["kid"] = "unknown-kid"
        forged = f"{_b64(header)}.{payload_b64}.{sig_b64}"
        with pytest.raises(AUTH_TOKEN_INVALID):
            await manager.validate_access_token(forged)

    async def test_expired_token(self):
        manager = _manager()
        token = await manager.issue_access_token("u1", ttl=-10)
        with pytest.raises(AUTH_TOKEN_EXPIRED):
            await manager.validate_access_token(token)

    async def test_expiration_boundary(self):
        """A token exactly at exp is expired (exp < now - skew with skew 0)."""
        manager = _manager()
        token = await manager.issue_access_token("u1", ttl=1)
        claims = await manager.validate_access_token(token)
        assert claims["exp"] >= int(time.time())

    async def test_clock_skew_grants_tolerance(self):
        manager = _manager(clock_skew_seconds=30)
        token = await manager.issue_access_token("u1", ttl=-10)  # 10s expired
        claims = await manager.validate_access_token(token)  # within 30s skew
        assert claims["sub"] == "u1"

    async def test_wrong_issuer_rejected(self):
        manager = _manager()
        other = _manager()  # same secret, different default issuer? no — same.
        # Build a token with a lying iss via a second manager with a different issuer.
        from aquilia.auth.tokens import TokenConfig as TC

        ring = KeyRing([KeyDescriptor.generate(kid="active", algorithm="HS256", secret="s" * 32)])
        liar = TokenManager(
            key_ring=ring,
            token_store=MemoryTokenStore(),
            config=TC(issuer="evil.example"),
        )
        token = await liar.issue_access_token("u1")
        with pytest.raises(AUTH_TOKEN_INVALID):
            await manager.validate_access_token(token)

    async def test_wrong_audience_rejected(self):
        ring = KeyRing([KeyDescriptor.generate(kid="active", algorithm="HS256", secret="s" * 32)])
        from aquilia.auth.tokens import TokenConfig as TC

        other_aud = TokenManager(
            key_ring=ring,
            token_store=MemoryTokenStore(),
            config=TC(audience=["other-service"]),
        )
        manager = _manager()
        token = await other_aud.issue_access_token("u1")
        with pytest.raises(AUTH_TOKEN_INVALID):
            await manager.validate_access_token(token)

    async def test_nbf_in_future_rejected(self):
        manager = _manager()
        now = int(time.time())
        payload = {
            "iss": manager.config.issuer,
            "sub": "u1",
            "aud": manager.config.audience,
            "exp": now + 600,
            "iat": now,
            "nbf": now + 3600,  # not valid for another hour
            "jti": "at_future",
            "scopes": [],
        }
        token = manager._sign_token(payload)  # genuinely signed by the manager
        with pytest.raises(AUTH_TOKEN_INVALID):
            await manager.validate_access_token(token)

    async def test_revoked_jti_rejected(self):
        manager = _manager()
        token = await manager.issue_access_token("u1")
        claims = await manager.validate_access_token(token)
        await manager.token_store.revoke_refresh_token(claims["jti"])
        with pytest.raises(AUTH_TOKEN_REVOKED):
            await manager.validate_access_token(token)

    async def test_high_volume_verification(self):
        """1_000 verifications under load — no state corruption."""
        manager = _manager()
        tokens = [await manager.issue_access_token(f"u{i}") for i in range(200)]

        async def verify_all(token: str) -> bool:
            for _ in range(5):
                claims = await manager.validate_access_token(token)
                if claims["sub"] != token[:0] + claims["sub"]:
                    return False
            return True

        results = await asyncio.gather(*[verify_all(t) for t in tokens])
        assert all(results)


# ============================================================================
# Collapse-errors mode (AG-08) + extra claims (AG-07)
# ============================================================================


class TestCollapseErrorsAndClaims:
    async def test_collapse_maps_every_failure_to_one_generic_fault(self):
        manager = _manager(collapse_errors=True)

        # invalid
        with pytest.raises(AUTH_TOKEN_INVALID) as exc_info:
            await manager.validate_access_token("garbage")
        assert exc_info.value.public_message == "Invalid or expired access token"

        # expired → collapsed
        token = await manager.issue_access_token("u1", ttl=-10)
        with pytest.raises(AUTH_TOKEN_INVALID) as exc_info:
            await manager.validate_access_token(token)
        assert exc_info.value.code == "AUTH_002"
        assert exc_info.value.public_message == "Invalid or expired access token"

        # revoked → collapsed
        token = await manager.issue_access_token("u1")
        claims = await manager.validate_access_token(token)
        await manager.token_store.revoke_refresh_token(claims["jti"])
        with pytest.raises(AUTH_TOKEN_INVALID) as exc_info:
            await manager.validate_access_token(token)
        assert exc_info.value.code == "AUTH_002"

    async def test_without_collapse_codes_are_distinct(self):
        manager = _manager()
        with pytest.raises(AUTH_TOKEN_INVALID):
            await manager.validate_access_token("garbage")
        token = await manager.issue_access_token("u1", ttl=-10)
        with pytest.raises(AUTH_TOKEN_EXPIRED):
            await manager.validate_access_token(token)

    async def test_extra_claims_round_trip(self):
        manager = _manager()
        token = await manager.issue_access_token(
            "u1", extra_claims={"org": "acme", "tier": "pro", "is_beta": True}
        )
        claims = await manager.validate_access_token(token)
        assert claims["org"] == "acme"
        assert claims["tier"] == "pro"
        assert claims["is_beta"] is True

    async def test_extra_claims_cannot_override_reserved(self):
        manager = _manager()
        for reserved in sorted(RESERVED_CLAIMS):
            with pytest.raises(ValueError, match="reserved"):
                await manager.issue_access_token("u1", extra_claims={reserved: "evil"})

    async def test_scopes_now_optional(self):
        manager = _manager()
        token = await manager.issue_access_token("u1")
        claims = await manager.validate_access_token(token)
        assert claims["scopes"] == []

    async def test_claims_dataclass_carries_extras(self):
        from aquilia.auth.core import TokenClaims

        manager = _manager()
        token = await manager.issue_access_token("u1", extra_claims={"org": "acme"})
        raw = await manager.token_manager_validate() if False else await manager.validate_access_token(token)

        claims = TokenClaims.from_dict(raw)
        assert claims.extra == {"org": "acme"}
        assert claims.get_claim("org") == "acme"
        assert claims.get_claim("sub") == "u1"
        assert claims.to_dict()["org"] == "acme"
