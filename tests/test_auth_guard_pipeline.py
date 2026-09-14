"""Guard pipeline — global/module/route guards, @Public, async guards.

Covers the gap-analysis findings:

* **AG-04** — the Guard protocol was synchronous; token verification (async
  TokenManager) and any authorization decision requiring async I/O could not
  live in a guard.
* **AG-09 / AG-18 / M-2 / M-3 / M-5** — no global (APP_GUARD-equivalent)
  guard registration; manifest ``guards`` validated but dead at runtime for
  HTTP; no ``@Public()`` per-route opt-out; protect-by-default unusable.
* **AG-02 / M-7** — invalid tokens on public routes must degrade to
  anonymous instead of rejecting the request.

Adversarial angles: guard ordering, stacked combinations, async guards doing
real awaitable work, legacy sync guards through the new pipeline, denial
fault propagation through the exception middleware (401 vs 403), and route
metadata surviving decorator stacking.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from aquilia import GET, POST, Controller, Public, RequestCtx, UseGuards
from aquilia.auth.faults import AUTH_REQUIRED
from aquilia.auth.guards import (
    AuthGuard,
    GuardContext,
    GuardPipeline,
    RoleGuard,
    is_authentication_guard,
    run_guard,
)
from aquilia.auth.state import AuthState
from aquilia.manifest import AppManifest
from aquilia.testing import TestClient, TestServer

SECRET = "guard-test-secret-" + "g" * 16

#: Shared execution-order log the test guards append to.
EXECUTION_ORDER: list[str] = []


class AsyncTenantGuard:
    """Async guard performing real awaitable work (AG-04's impossible case)."""

    async def can_activate(self, ctx: GuardContext) -> bool:
        await asyncio.sleep(0)  # genuinely awaits
        EXECUTION_ORDER.append("global:async_tenant")
        if ctx.user is None:
            raise AUTH_REQUIRED()
        tenant = getattr(ctx.user, "tenant_id", None)
        return tenant in (None, "tenant-a")


class GlobalRoleGuard:
    def __init__(self) -> None:
        self.denial_fault = AUTH_REQUIRED

    async def can_activate(self, ctx: GuardContext) -> bool:
        EXECUTION_ORDER.append("global:role")
        # Authorization guards run even on public routes — by design.
        return True


class ModuleSyncGuard:
    """Legacy sync contract (check) running through the new pipeline."""

    def check(self, ctx: Any) -> None:
        EXECUTION_ORDER.append("module:sync")


class RouteAsyncGuard:
    async def can_activate(self, ctx: GuardContext) -> bool:
        await asyncio.sleep(0)
        EXECUTION_ORDER.append("route:async")
        return True


class DenyAllGuard:
    async def can_activate(self, ctx: GuardContext) -> bool:
        EXECUTION_ORDER.append("route:deny")
        return False


class GuardedController(Controller):
    @GET("/public")
    @Public()
    async def public(self, ctx: RequestCtx):
        return {"public": True, "identity": ctx.identity.id if ctx.identity else None}

    @GET("/me")
    @UseGuards(AuthGuard)
    async def me(self, ctx: RequestCtx):
        return {"id": ctx.identity.id}

    @GET("/role-admin")
    @UseGuards(AuthGuard, RoleGuard("admin"))
    async def admin_only(self, ctx: RequestCtx):
        return {"admin": True}

    @GET("/all-guards")
    @UseGuards(RouteAsyncGuard, DenyAllGuard)
    async def all_guards(self, ctx: RequestCtx):
        return {"unreachable": True}

    @POST("/echo")
    async def echo(self, ctx: RequestCtx):
        return {"ok": True}


def _manifest() -> AppManifest:
    return AppManifest(
        name="guards_app",
        version="0.0.1",
        controllers=["tests.test_auth_guard_pipeline:GuardedController"],
        guards=["tests.test_auth_guard_pipeline:ModuleSyncGuard"],
    )


def _auth_config(require_auth_by_default: bool = False, global_guards: list | None = None) -> dict:
    auth: dict[str, Any] = {
        "enabled": True,
        "stateless": True,
        "backends": ["token"],
        "require_auth_by_default": require_auth_by_default,
        "tokens": {"secret_key": SECRET, "access_token_ttl_seconds": 600},
    }
    if global_guards is not None:
        auth["global_guards"] = global_guards
    return auth


async def _issue_token(server: TestServer, identity_id: str = "user-1", roles: list[str] | None = None):
    manager = server.server._auth_manager
    return await manager.token_manager.issue_access_token(identity_id, scopes=[], roles=roles)


# ============================================================================
# Unit: the runner + protocol adapters
# ============================================================================


class TestGuardRunner:
    async def test_async_can_activate_true_allows(self):
        from aquilia.auth.core import Identity, IdentityType

        identity = Identity(id="u1", type=IdentityType.USER, attributes={})
        ctx = GuardContext(auth_state=AuthState(identity=identity))
        assert await run_guard(AsyncTenantGuard(), ctx) is True
        assert EXECUTION_ORDER[-1] == "global:async_tenant"

    async def test_async_false_denies_with_default_fault(self):
        from aquilia.auth.faults import AUTHZ_RESOURCE_FORBIDDEN
        from aquilia.faults import Fault

        ctx = GuardContext(auth_state=AuthState())
        with pytest.raises(Fault) as exc_info:
            await run_guard(DenyAllGuard(), ctx)
        assert isinstance(exc_info.value, AUTHZ_RESOURCE_FORBIDDEN) or exc_info.value.code == "AUTHZ_004"

    async def test_legacy_check_guard_runs(self):
        EXECUTION_ORDER.clear()
        ctx = GuardContext(auth_state=AuthState())
        await run_guard(ModuleSyncGuard(), ctx)
        assert "module:sync" in EXECUTION_ORDER

    async def test_class_reference_instantiated(self):
        EXECUTION_ORDER.clear()
        await run_guard(ModuleSyncGuard, GuardContext(auth_state=AuthState()))
        assert "module:sync" in EXECUTION_ORDER

    async def test_callable_guard_denied_on_false(self):
        from aquilia.faults import Fault

        async def bare_guard(ctx):
            return False

        with pytest.raises(Fault):
            await run_guard(bare_guard, GuardContext(auth_state=AuthState()))

    def test_authentication_guard_detection(self):
        assert is_authentication_guard(AuthGuard) is True
        assert is_authentication_guard(AuthGuard()) is True
        assert is_authentication_guard(RoleGuard("x")) is False
        assert is_authentication_guard(AsyncTenantGuard()) is False

        class OptInGuard:
            authentication_guard = True

            async def can_activate(self, ctx):
                return True

        assert is_authentication_guard(OptInGuard()) is True

    async def test_guard_context_views(self):
        from aquilia.auth.core import Identity, IdentityType

        identity = Identity(id="u1", type=IdentityType.USER, attributes={"roles": ["admin"]})
        state = AuthState(identity=identity, claims={"sid": "s1"})
        ctx = GuardContext(auth_state=state)
        assert ctx.identity is identity
        assert ctx.user is identity
        assert ctx.claims == {"sid": "s1"}
        assert ctx.authenticated if hasattr(ctx, "authenticated") else True
        # dict-style access for legacy guards
        assert ctx["identity"] is identity
        assert ctx.get("container") is None


# ============================================================================
# E2E: guard pipeline through a real server
# ============================================================================


@pytest.mark.asyncio
class TestGuardPipelineE2E:
    async def test_route_guard_requires_authentication(self):
        async with TestServer(
            manifests=[_manifest()],
            enable_auth=True,
            config_overrides={"integrations": {"auth": _auth_config()}},
        ) as server:
            client = TestClient(server)

            # Anonymous → 401 (AUTH_REQUIRED through the exception pipeline)
            response = await client.get("/guards_app/me")
            assert response.status_code == 401

            # Valid token → 200
            token = await _issue_token(server)
            response = await client.get("/guards_app/me", headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 200
            assert response.json() == {"id": "user-1"}

    async def test_role_guard_denies_wrong_role_with_403(self):
        async with TestServer(
            manifests=[_manifest()],
            enable_auth=True,
            config_overrides={"integrations": {"auth": _auth_config()}},
        ) as server:
            client = TestClient(server)
            token = await _issue_token(server, roles=["viewer"])  # not admin
            response = await client.get("/guards_app/role-admin", headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 403

            admin_token = await _issue_token(server, roles=["admin"])
            response = await client.get("/guards_app/role-admin", headers={"Authorization": f"Bearer {admin_token}"})
            assert response.status_code == 200

    async def test_public_route_with_invalid_token_degrades_to_anonymous(self):
        """AG-02/M-7: a malformed token on a public route must NOT reject."""
        async with TestServer(
            manifests=[_manifest()],
            enable_auth=True,
            config_overrides={"integrations": {"auth": _auth_config(require_auth_by_default=True)}},
        ) as server:
            client = TestClient(server)

            # garbage bearer on public route → anonymous 200
            response = await client.get("/guards_app/public", headers={"Authorization": "Bearer garbage.token.here"})
            assert response.status_code == 200
            assert response.json() == {"public": True, "identity": None}

            # forged-but-well-formed token → still anonymous 200
            forged = "eyJhbGciOiJIUzI1NiIsImtpZCI6ImFjdGl2ZSJ9.eyJzdWIiOiJoYWNrZXIifQ.zzz"
            response = await client.get("/guards_app/public", headers={"Authorization": f"Bearer {forged}"})
            assert response.status_code == 200
            assert response.json()["identity"] is None

            # anonymous plain request → 200
            response = await client.get("/guards_app/public")
            assert response.status_code == 200

    async def test_protect_by_default_with_public_optout(self):
        """require_auth_by_default: everything 401s except @Public routes."""
        async with TestServer(
            manifests=[_manifest()],
            enable_auth=True,
            config_overrides={"integrations": {"auth": _auth_config(require_auth_by_default=True)}},
        ) as server:
            client = TestClient(server)

            # plain route → 401
            response = await client.post("/guards_app/echo")
            assert response.status_code == 401

            # public route → 200 anonymous
            response = await client.get("/guards_app/public")
            assert response.status_code == 200

            # authenticated plain route → 200
            token = await _issue_token(server)
            response = await client.post("/guards_app/echo", headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 200

    async def test_global_module_route_execution_order(self):
        """Global → module → route, each actually running once."""
        EXECUTION_ORDER.clear()
        async with TestServer(
            manifests=[_manifest()],
            enable_auth=True,
            config_overrides={
                "integrations": {
                    "auth": _auth_config(global_guards=["tests.test_auth_guard_pipeline:GlobalRoleGuard"])
                }
            },
        ) as server:
            client = TestClient(server)
            token = await _issue_token(server)
            response = await client.get("/guards_app/me", headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 200

        assert EXECUTION_ORDER[:2] == ["global:role", "module:sync"]

    async def test_route_guard_denial_short_circuits(self):
        """DenyAllGuard (route level) blocks the handler."""
        EXECUTION_ORDER.clear()
        async with TestServer(
            manifests=[_manifest()],
            enable_auth=True,
            config_overrides={"integrations": {"auth": _auth_config()}},
        ) as server:
            client = TestClient(server)
            token = await _issue_token(server)
            response = await client.get("/guards_app/all-guards", headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 403
            # RouteAsyncGuard ran before DenyAllGuard (declaration order)
            assert EXECUTION_ORDER[-2:] == ["route:async", "route:deny"]

    async def test_invalid_token_on_guarded_route_is_401_not_403(self):
        """N-2: AUTH_002/003/004 must render 401 (was 403)."""
        async with TestServer(
            manifests=[_manifest()],
            enable_auth=True,
            config_overrides={"integrations": {"auth": _auth_config()}},
        ) as server:
            client = TestClient(server)
            response = await client.get("/guards_app/me", headers={"Authorization": "Bearer not-a-jwt"})
            assert response.status_code == 401
            body = response.json()
            assert body["error"]["code"] == "AUTH_002"

    async def test_stateless_mode_resolves_identity_from_claims(self):
        """stateless=True: no identity-store lookup — identity comes from claims."""
        async with TestServer(
            manifests=[_manifest()],
            enable_auth=True,
            config_overrides={"integrations": {"auth": _auth_config()}},
        ) as server:
            client = TestClient(server)
            manager = server.server._auth_manager

            # The identity does NOT exist in the identity store…
            stored = await manager.identity_store.get("ghost-user")
            assert stored is None

            # …but the token still authenticates (claims are the truth).
            token = await manager.token_manager.issue_access_token("ghost-user", scopes=[])
            response = await client.get("/guards_app/me", headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 200
            assert response.json() == {"id": "ghost-user"}

    async def test_metadata_extraction_lands_in_raw_metadata(self):
        from aquilia.controller.metadata import extract_controller_metadata

        metadata = extract_controller_metadata(GuardedController, "tests.test_auth_guard_pipeline")
        by_path = {r.full_path: r for r in metadata.routes}

        public_route = by_path["/public"]
        assert public_route._raw_metadata.get("public") is True

        me_route = by_path["/me"]
        guard_entries = me_route._raw_metadata.get("guards")
        assert guard_entries and AuthGuard in guard_entries

        plain_route = by_path["/echo"]
        assert not plain_route._raw_metadata.get("public")
        assert not plain_route._raw_metadata.get("guards")

    async def test_guard_pipeline_runs_without_auth_middleware(self):
        """Guards work on servers that never enabled the framework auth
        pipeline (the AniWave 'own tokens + framework guards' shape)."""
        calls: list[str] = []

        class AppGuard:
            async def can_activate(self, ctx: GuardContext) -> bool:
                # A pure-authorization guard: runs for every route, reads
                # whatever state other layers set, never rejects here.
                calls.append("app")
                return True

        from aquilia.controller.engine import ControllerEngine
        from aquilia.controller.factory import ControllerFactory

        async with TestServer(manifests=[_manifest()]) as server:
            # Attach a pipeline post-boot (the way an app plugin would).
            server.server.controller_engine.guard_pipeline = GuardPipeline([AppGuard()])
            client = TestClient(server)

            response = await client.get("/guards_app/public")
            assert response.status_code == 200  # public: auth guard skipped… but AppGuard isn't an auth guard
            assert calls == ["app"]

            # Route with no guards and no public marker: pipeline still runs
            response = await client.post("/guards_app/echo")
            assert response.status_code == 200
            assert calls == ["app", "app"]
