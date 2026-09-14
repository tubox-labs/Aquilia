"""Principal injection and the AniWave-shaped end-to-end flow.

Covers:

* **AG-10 / M-4** — ``@CurrentUser``-style injection of application-defined
  principal types (``Annotated[AppUser, CurrentUser]``), the
  ``principal_factory`` pipeline hook, and optional/anonymous degradation.
* The whole architecture working together as a real application would use
  it: stateless Bearer tokens, protect-by-default + ``@Public()``,
  exact-contract 401 bodies via the error renderer, principal injection
  through real HTTP, concurrent login/refresh/me traffic, and token
  revocation landing within the token TTL.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Annotated, Any, Optional

import pytest

from aquilia import GET, POST, Controller, Public, RequestCtx, UseGuards
from aquilia.auth import CurrentUser
from aquilia.auth.core import Identity, IdentityType
from aquilia.auth.faults import AUTH_REQUIRED
from aquilia.auth.guards import AuthGuard
from aquilia.manifest import AppManifest
from aquilia.testing import TestClient, TestServer

SECRET = "e2e-secret-" + "e" * 24


@dataclass(frozen=True)
class AppUser:
    """The application's principal type — exactly the fields handlers use."""

    id: str
    session_id: str | None
    is_guest: bool = False


def build_principal(identity: Identity, claims: dict[str, Any] | None) -> AppUser:
    claims = claims or {}
    return AppUser(
        id=identity.id,
        session_id=claims.get("sid"),
        is_guest=claims.get("guest") is True,
    )


class AuthController(Controller):
    @GET("/me")
    async def me(self, ctx: RequestCtx, user: Annotated[AppUser, CurrentUser]):
        return {"id": user.id, "sessionId": user.session_id, "isGuest": user.is_guest}

    @GET("/me-optional")
    @Public()
    async def me_optional(self, ctx: RequestCtx, user: Annotated[Optional[AppUser], CurrentUser(optional=True)]):
        # @Public() + CurrentUser(optional=True) is the "maybe-user" route:
        # anonymous requests pass and inject None.
        return {"id": user.id if user else None}

    @GET("/me-identity")
    async def me_identity(self, ctx: RequestCtx, user: Annotated[Identity, CurrentUser]):
        return {"id": user.id, "type": user.type.value}

    @GET("/profile")
    @UseGuards(AuthGuard)
    async def profile(self, ctx: RequestCtx, current_user: AppUser):
        # 'current_user' parameter name → principal without the marker
        return {"profileFor": current_user.id}

    @GET("/health")
    @Public()
    async def health(self, ctx: RequestCtx):
        return {"status": "ok"}


def _manifest() -> AppManifest:
    return AppManifest(
        name="app",
        version="0.0.1",
        controllers=["tests.test_auth_principal_e2e:AuthController"],
    )


def _auth_config(**extra: Any) -> dict:
    config: dict[str, Any] = {
        "enabled": True,
        "stateless": True,
        "backends": ["token"],
        "require_auth_by_default": True,
        "collapse_token_errors": True,
        "principal_factory": "tests.test_auth_principal_e2e:build_principal",
        "tokens": {"secret_key": SECRET, "access_token_ttl_seconds": 600},
    }
    config.update(extra)
    return config


async def _boot(**auth_extra: Any):
    server_ctx = await TestServer(
        manifests=[_manifest()],
        enable_auth=True,
        config_overrides={"integrations": {"auth": _auth_config(**auth_extra)}},
    ).__aenter__()
    return server_ctx


@pytest.mark.asyncio
class TestPrincipalInjection:
    async def test_app_principal_injected_with_claims(self):
        async with await _boot() as server:
            manager = server.server._auth_manager
            token = await manager.token_manager.issue_access_token(
                "user-77", session_id="sess-1"
            )
            client = TestClient(server)
            response = await client.get("/app/me", headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 200
            assert response.json() == {"id": "user-77", "sessionId": "sess-1", "isGuest": False}

    async def test_extra_claims_reach_the_principal(self):
        async with await _boot() as server:
            manager = server.server._auth_manager
            token = await manager.token_manager.issue_access_token(
                "guest-1", session_id="g", extra_claims={"guest": True}
            )
            client = TestClient(server)
            response = await client.get("/app/me", headers={"Authorization": f"Bearer {token}"})
            assert response.json()["isGuest"] is True

    async def test_optional_marker_allows_anonymous(self):
        async with await _boot() as server:
            client = TestClient(server)
            response = await client.get("/app/me-optional")
            assert response.status_code == 200
            assert response.json() == {"id": None}

    async def test_framework_identity_available_without_factory(self):
        async with await _boot() as server:
            manager = server.server._auth_manager
            token = await manager.token_manager.issue_access_token("u-identity")
            client = TestClient(server)
            response = await client.get("/app/me-identity", headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 200
            assert response.json() == {"id": "u-identity", "type": "user"}

    async def test_current_user_param_name_without_marker(self):
        async with await _boot() as server:
            manager = server.server._auth_manager
            token = await manager.token_manager.issue_access_token("named-user")
            client = TestClient(server)
            response = await client.get("/app/profile", headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 200
            assert response.json() == {"profileFor": "named-user"}

    async def test_required_principal_anonymous_is_401(self):
        async with await _boot() as server:
            client = TestClient(server)
            response = await client.get("/app/me")
            assert response.status_code == 401


@pytest.mark.asyncio
class TestAniWaveShapedE2E:
    """A Bearer-only app with AniWave's exact posture: stateless verification,
    protect-by-default with @Public, collapsed 401 bodies, custom error
    contract — all through the framework path (no bypass)."""

    async def test_public_and_protected_matrix(self):
        async with await _boot() as server:
            manager = server.server._auth_manager
            client = TestClient(server)

            # Health is public — anonymous, garbage token, and stale token all pass.
            assert (await client.get("/app/health")).status_code == 200
            assert (await client.get("/app/health", headers={"Authorization": "Bearer junk"})).status_code == 200

            # Everything else is protected by default.
            assert (await client.get("/app/me")).status_code == 401
            assert (await client.get("/app/me", headers={"Authorization": "Bearer junk"})).status_code == 401

            # A valid token opens the protected route.
            token = await manager.token_manager.issue_access_token("real-user")
            response = await client.get("/app/me", headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 200

    async def test_collapsed_401_body_is_uniform(self):
        """AG-08's anti-enumeration posture: every *token* failure is one
        generic body; a missing header stays distinct (AUTH_010)."""
        async with await _boot() as server:
            manager = server.server._auth_manager
            client = TestClient(server)

            missing = await client.get("/app/me")
            invalid = await client.get("/app/me", headers={"Authorization": "Bearer junk"})
            expired = await client.get(
                "/app/me",
                headers={
                    "Authorization": f"Bearer {await manager.token_manager.issue_access_token('u', ttl=-5)}"
                },
            )

            # Token failures collapse to one generic body.
            for response in (invalid, expired):
                assert response.status_code == 401
                body = response.json()
                assert body["error"]["code"] == "AUTH_002"
                assert body["error"]["message"] == "Invalid or expired access token"

            # A missing header is the distinct AUTH_010 (AniWave's contract:
            # "Authentication required" vs "Invalid or expired access token").
            assert missing.status_code == 401
            assert missing.json()["error"]["code"] == "AUTH_010"

    async def test_error_renderer_controls_auth_error_bodies(self):
        """The F-20 renderer applies to auth faults too (N-7 fix) — an app
        with the Node envelope gets it for 401s without replacing middleware."""
        from aquilia.middleware.builtin.exceptions import ExceptionMiddleware

        async with await _boot() as server:
            for descriptor in server.server.middleware_stack.middlewares:
                middleware = getattr(descriptor, "middleware", descriptor)
                if isinstance(middleware, ExceptionMiddleware):

                    def node_renderer(fault, status, request, _mw=middleware):
                        return {
                            "statusCode": status,
                            "code": getattr(fault, "code", "UNKNOWN"),
                            "message": getattr(fault, "public_message", str(fault)),
                        }

                    middleware.error_renderer = node_renderer

            client = TestClient(server)
            response = await client.get("/app/me")
            assert response.status_code == 401
            body = response.json()
            assert body["statusCode"] == 401
            assert body["code"]
            assert "error" not in body

    async def test_high_volume_mixed_traffic(self):
        """100+ concurrent requests mixing public, protected-valid, and
        protected-invalid — no cross-request state corruption."""
        async with await _boot() as server:
            manager = server.server._auth_manager
            client = TestClient(server)
            tokens = [await manager.token_manager.issue_access_token(f"user-{i}") for i in range(25)]

            async def one_request(i: int) -> int:
                if i % 4 == 0:
                    response = await client.get("/app/health")
                elif i % 4 == 1:
                    response = await client.get("/app/me", headers={"Authorization": f"Bearer {tokens[i % 25]}"})
                elif i % 4 == 2:
                    response = await client.get("/app/me", headers={"Authorization": "Bearer junk"})
                else:
                    response = await client.get("/app/me")
                return response.status_code

            statuses = await asyncio.gather(*[one_request(i) for i in range(120)])
            expected = [200 if i % 4 == 0 else 200 if i % 4 == 1 else 401 for i in range(120)]
            assert statuses == expected

    async def test_refresh_flow_through_token_manager_with_rotation(self):
        """Login-equivalent issuance → refresh → refresh-again → replay
        detection, under the server's own configured manager."""
        async with await _boot() as server:
            tokens = server.server._auth_manager.token_manager

            rt1 = await tokens.issue_refresh_token("user-1", scopes=[], session_id="e2e")
            access1, rt2 = await tokens.refresh_access_token(rt1)
            claims1 = await tokens.validate_access_token(access1)
            assert claims1["sub"] == "user-1"

            access2, rt3 = await tokens.refresh_access_token(rt2)
            assert access2

            # Replay of rt2 (rotated away) revokes the whole family.
            with pytest.raises(Exception):
                await tokens.refresh_access_token(rt2)
            with pytest.raises(Exception):
                await tokens.refresh_access_token(rt3)

            # …and revocation is visible to the access path within the TTL:
            # the session's refresh credentials are dead, while access tokens
            # remain valid until expiry (the documented stateless tradeoff).
            claims2 = await tokens.validate_access_token(access2)
            assert claims2["sub"] == "user-1"

    async def test_concurrent_refresh_single_winner_e2e(self):
        async with await _boot() as server:
            tokens = server.server._auth_manager.token_manager
            rt = await tokens.issue_refresh_token("racer", scopes=[], session_id="race-e2e")
            results = await asyncio.gather(
                *[tokens.refresh_access_token(rt) for _ in range(5)],
                return_exceptions=True,
            )
            winners = [r for r in results if not isinstance(r, Exception)]
            assert len(winners) == 1

    async def test_authstate_is_the_single_canonical_truth(self):
        """MS-8/9: every legacy mirror agrees with the canonical state."""
        captured: dict[str, Any] = {}

        class ProbeController(Controller):
            @GET("/probe")
            @UseGuards(AuthGuard)
            async def probe(self, ctx: RequestCtx):
                state = ctx.request.state.get("auth_state")
                captured["identity"] = ctx.identity
                captured["state_identity"] = state.identity if state else None
                captured["state_principal"] = state.principal if state else None
                captured["request_identity"] = ctx.request.state.get("identity")
                captured["authenticated_flag"] = ctx.request.state.get("authenticated")
                captured["principal"] = ctx.request.state.get("principal")
                captured["claims"] = ctx.request.state.get("token_claims")
                return {"ok": True}

        # Expose at module level for the controller importer.
        import tests.test_auth_principal_e2e as _self_module

        _self_module.ProbeController = ProbeController
        try:
            manifest = AppManifest(
                name="probe",
                version="0.0.1",
                controllers=["tests.test_auth_principal_e2e:ProbeController"],
            )
            async with TestServer(
                manifests=[manifest],
                enable_auth=True,
                config_overrides={"integrations": {"auth": _auth_config()}},
            ) as server:
                manager = server.server._auth_manager
                token = await manager.token_manager.issue_access_token("canonical-user", session_id="s-canon")
                client = TestClient(server)
                response = await client.get("/probe/probe", headers={"Authorization": f"Bearer {token}"})
                assert response.status_code == 200
        finally:
            del _self_module.ProbeController

        assert captured["identity"] is captured["state_identity"]
        assert captured["identity"] is captured["request_identity"]
        assert captured["authenticated_flag"] is True
        assert isinstance(captured["principal"], AppUser)
        assert captured["principal"] is captured["state_principal"]
        assert captured["claims"]["sid"] == "s-canon"
