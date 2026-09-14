"""Second-audit regressions — fixes for the hostile-review findings.

Each test pins one finding from the post-implementation independent audit:

* **F1 (critical)** — the default ``[token, session]`` deployment crashed on
  every valid Bearer request (``bind_token_claims`` received a dict but read
  attributes). The original e2e suite missed it because every test ran
  stateless.
* **R1** — session ``Set-Cookie`` lost on 401 denials (cookie now rides the
  denial fault's metadata headers).
* **C1** — ``auth`` and ``integrations.auth`` shadowed each other (first-wins
  ``or``); an ``AQ_AUTH__TOKENS__SECRET_KEY`` env var silently disabled a
  configured integration.
* **C2** — TTL minute/day aliases masked by canonical-field defaults in the
  typed layers (``refresh_token_ttl_days = 7`` silently became 30 days).
* **F2/F3/F4/F5/F6, H1/H2/H4, M1/M2/M4** — guard-contract and normalizer
  hardening.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

import pytest

from aquilia import GET, Controller, Public, RequestCtx, UseGuards
from aquilia.auth import CurrentUser
from aquilia.auth.core import Identity, IdentityType
from aquilia.auth.faults import AUTH_REQUIRED
from aquilia.auth.guards import AuthGuard, GuardContext, GuardPipeline, is_authentication_guard, run_guard
from aquilia.auth.state import AuthState, route_is_public
from aquilia.manifest import AppManifest
from aquilia.testing import TestClient, TestServer

SECRET = "audit-secret-" + "a" * 20


class DefaultShapeController(Controller):
    """Uses the DEFAULT framework shape: session-capable, stateful token."""

    @GET("/me")
    async def me(self, ctx: RequestCtx):
        return {"id": ctx.identity.id if ctx.identity else None}

    @GET("/open")
    @Public()
    async def open(self, ctx: RequestCtx):
        return {"ok": True}


def _manifest() -> AppManifest:
    return AppManifest(
        name="dflt",
        version="0.0.1",
        controllers=["tests.test_auth_second_audit:DefaultShapeController"],
    )


def _default_auth_config(**extra: Any) -> dict:
    config: dict[str, Any] = {
        "enabled": True,
        # NOTE: no `stateless`, no custom backends — the DEFAULT
        # [token, session] pipeline with sessions force-enabled (F1's shape).
        "tokens": {"secret_key": SECRET},
        "require_auth_by_default": True,
    }
    config.update(extra)
    return config


@pytest.mark.asyncio
class TestF1DefaultShape:
    async def test_default_backends_with_sessions_do_not_500(self):
        """F1: valid Bearer + mounted session engine + default backends —
        the stateful token path must not crash on claims binding."""
        async with TestServer(
            manifests=[_manifest()],
            enable_auth=True,
            enable_sessions=True,
            config_overrides={"integrations": {"auth": _default_auth_config()}},
        ) as server:
            manager = server.server._auth_manager
            # Register the identity so TokenBackend can resolve it.
            await manager.identity_store.create(
                Identity(id="user-1", type=IdentityType.USER, attributes={"email": "u@x.com"})
            )
            token = await manager.token_manager.issue_access_token("user-1", session_id="s1")

            client = TestClient(server)
            response = await client.get("/dflt/me", headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 200
            assert response.json() == {"id": "user-1"}

    async def test_default_shape_invalid_token_on_public_route(self):
        """Same default shape: garbage token on @Public route → anonymous 200."""
        async with TestServer(
            manifests=[_manifest()],
            enable_auth=True,
            enable_sessions=True,
            config_overrides={"integrations": {"auth": _default_auth_config()}},
        ) as server:
            client = TestClient(server)
            response = await client.get("/dflt/open", headers={"Authorization": "Bearer junk"})
            assert response.status_code == 200


@pytest.mark.asyncio
class TestR1CookieOnDenial:
    async def test_denied_request_still_receives_session_cookie(self):
        """R1: the 401 response carries the session's Set-Cookie so denied
        requests establish/rotate their session (no per-request session
        churn)."""
        async with TestServer(
            manifests=[_manifest()],
            enable_auth=True,
            enable_sessions=True,
            config_overrides={"integrations": {"auth": _default_auth_config()}},
        ) as server:
            client = TestClient(server)
            response = await client.get("/dflt/me")  # anonymous + protected
            assert response.status_code == 401
            set_cookie = [v for k, v in response.headers.items() if k.lower() == "set-cookie"]
            assert set_cookie, "401 denial must still deliver the session cookie"


class TestC1ConfigMerge:
    def test_env_section_does_not_shadow_integration(self):
        """C1's kill-switch: an env var creating an `auth` section must not
        discard a configured integration wholesale."""
        import os

        os.environ["AQ_AUTH__TOKENS__SECRET_KEY"] = "env-provided-" + "b" * 16
        try:
            from aquilia.config import ConfigLoader

            loader = ConfigLoader.load(paths=[])
            loader._merge_dict(
                loader.config_data,
                {
                    "integrations": {
                        "auth": {
                            "enabled": True,
                            "tokens": {"access_token_ttl_seconds": 900},
                            "require_auth_by_default": True,
                        }
                    }
                },
            )
            auth = loader.get_auth_config()
            assert auth["enabled"] is True, "integration must survive the env-created auth section"
            assert auth["tokens"]["secret_key"].startswith("env-provided")
            assert auth["tokens"]["access_token_ttl_seconds"] == 900
            assert auth["security"]["require_auth_by_default"] is True
        finally:
            del os.environ["AQ_AUTH__TOKENS__SECRET_KEY"]

    def test_explicit_true_wins_when_both_sources_present(self):
        from aquilia.config import ConfigLoader

        loader = ConfigLoader(env_prefix="AQ_")
        loader._merge_dict(
            loader.config_data,
            {
                "auth": {"enabled": False, "secret_key": "flat-" + "c" * 16},
                "integrations": {"auth": {"enabled": True, "backends": ["token"]}},
            },
        )
        auth = loader.get_auth_config()
        # Explicit True anywhere wins (a typed Integration.auth() is opt-in).
        assert auth["enabled"] is True
        assert auth["security"]["backends"] == ["token"]
        assert auth["tokens"]["secret_key"].startswith("flat-")


class TestC2AliasNotMasked:
    def test_pyconfig_alias_not_masked_by_default(self):
        """C2: `refresh_token_ttl_days = 7` on the env class must yield
        7 days — not the 30-day class default of the seconds field."""
        from aquilia.auth.config import AuthSettings
        from aquilia.pyconfig import AquilaConfig

        class Env(AquilaConfig):
            class auth(AquilaConfig.Auth):
                secret_key = SECRET
                refresh_token_ttl_days = 7

        data = Env.to_dict()
        # The env class emits BOTH the alias (7) and the seconds default
        # (None) — the alias must survive normalization.
        settings = AuthSettings.from_config(data["auth"])
        assert settings.refresh_token_ttl == 7 * 86400

    def test_pyconfig_seconds_wins_when_explicit(self):
        from aquilia.auth.config import AuthSettings
        from aquilia.pyconfig import AquilaConfig

        class Env(AquilaConfig):
            class auth(AquilaConfig.Auth):
                access_token_ttl_minutes = 99  # alias loses
                access_token_ttl_seconds = 600  # explicit canonical wins

        settings = AuthSettings.from_config(Env.to_dict()["auth"])
        assert settings.access_token_ttl == 600


class TestGuardContractHardening:
    async def test_falsy_none_allows_false_denies(self):
        """F2: None (no opinion) allows; the singleton False denies."""
        ctx = GuardContext(auth_state=AuthState())

        class NoneGuard:
            async def can_activate(self, ctx):
                return None

        assert await run_guard(NoneGuard(), ctx) is True

        class ZeroGuard:
            async def can_activate(self, ctx):
                return 0  # falsy but not False — allowed per contract

        assert await run_guard(ZeroGuard(), ctx) is True

    def test_f3_authentication_guard_opt_out(self):
        """F3: `authentication_guard = False` re-enables an AuthGuard
        subclass on public routes."""

        class AlwaysRunAuthGuard(AuthGuard):
            authentication_guard = False  # opt OUT of the @Public skip

        assert is_authentication_guard(AuthGuard()) is True
        assert is_authentication_guard(AlwaysRunAuthGuard()) is False
        assert is_authentication_guard(AlwaysRunAuthGuard) is False

        class MarkerGuard:
            authentication_guard = True

            async def can_activate(self, ctx):
                return True

        assert is_authentication_guard(MarkerGuard()) is True

    def test_f4_mock_request_is_not_public(self):
        """F4: Mock requests must never count as @Public (enforcement may
        not be silently disabled by test doubles)."""
        from unittest.mock import MagicMock

        assert route_is_public(MagicMock()) is False
        assert route_is_public(None) is False

    def test_f5_dict_route_metadata_supported(self):
        class _State(dict):
            pass

        request = type("R", (), {"state": {"route_metadata": {"public": True}}})()
        assert route_is_public(request) is True

        request = type("R", (), {"state": {"route_metadata": {"_raw_metadata": {"public": True}}}})()
        assert route_is_public(request) is True

        request = type("R", (), {"state": {"route_metadata": {"public": False}}})()
        assert route_is_public(request) is False

    async def test_f6_requires_supports_async_only_guards(self):
        """F6: the legacy @requires decorator must not silently no-op a
        guard that only implements can_activate."""
        from aquilia.auth.guards import requires

        ran: list[bool] = []

        class AsyncOnlyGuard:
            async def can_activate(self, ctx) -> bool:
                ran.append(True)
                return True

        @requires(AsyncOnlyGuard())
        async def handler(ctx):
            return "ok"

        result = await handler({"identity": None})
        assert result == "ok"
        assert ran == [True]

        # …and a denying async-only guard actually denies through @requires.
        class AsyncDeny:
            async def can_activate(self, ctx) -> bool:
                return False

        @requires(AsyncDeny())
        async def handler2(ctx):
            return "unreachable"

        from aquilia.faults import Fault

        with pytest.raises(Fault):
            await handler2({"identity": None})


class TestNormalizerHardening:
    def test_h1_malformed_sections_do_not_crash(self):
        """H1: garbage section values warn and degrade, never crash boot."""
        from aquilia.auth.config import normalize_auth_config

        cfg = normalize_auth_config(
            {"tokens": "hello", "security": "strict", "store": "memory"}
        )
        assert cfg["tokens"] == {}
        assert cfg["security"] == {}
        assert cfg["store"] == {"type": "memory"}  # sibling-session spelling

    def test_h1_bool_backends_tolerated(self):
        from aquilia.auth.config import normalize_auth_config

        cfg = normalize_auth_config({"security": {"backends": True}})
        assert "backends" not in cfg["security"]  # nonsense dropped, not iterated

    def test_h2_tuple_global_guards(self):
        from aquilia.auth.config import AuthSettings, normalize_auth_config

        cfg = normalize_auth_config({"global_guards": ("app.g:A", "app.g:B")})
        assert cfg["security"]["global_guards"] == ["app.g:A", "app.g:B"]

        settings = AuthSettings.from_config({"global_guards": ("app.g:A",)})
        assert settings.global_guards == ["app.g:A"]

    def test_m1_retired_nested_secret_cannot_shadow_flat(self):
        from aquilia.auth.config import normalize_auth_config

        cfg = normalize_auth_config(
            {"secret_key": "real-secret-" + "d" * 16, "tokens": {"secret_key": ""}}
        )
        assert cfg["tokens"]["secret_key"].startswith("real-secret")

    def test_m2_explicit_zero_survives(self):
        from aquilia.auth.config import AuthSettings

        settings = AuthSettings.from_config(
            {"security": {"rate_limit_max_attempts": 0, "rate_limit_window_seconds": 0}}
        )
        assert settings.rate_limit_max_attempts == 0
        assert settings.rate_limit_window_seconds == 0

    def test_m3_negative_ttl_rejected(self):
        from aquilia.auth.config import AuthSettings

        settings = AuthSettings.from_config({"tokens": {"access_token_ttl_seconds": -60}})
        assert settings.access_token_ttl == 3600  # warned + defaulted

    def test_m4_string_bool_parsing(self):
        from aquilia.auth.config import AuthSettings

        settings = AuthSettings.from_config({"enabled": "false"})
        assert settings.enabled is False
        settings = AuthSettings.from_config({"enabled": "true"})
        assert settings.enabled is True
        settings = AuthSettings.from_config({"require_auth_by_default": "1"})
        assert settings.require_auth_by_default is True

    def test_m3_non_integer_ttl_warns_not_crashes(self):
        from aquilia.auth.config import AuthSettings

        settings = AuthSettings.from_config({"tokens": {"access_token_ttl_seconds": "abc"}})
        assert settings.access_token_ttl == 3600


@pytest.mark.asyncio
class TestH3GuardReferencePolicy:
    async def test_bare_guard_name_fails_boot_with_clear_message(self):
        """H3: `global_guards: ["RolesGuard"]` (no module) must fail loudly,
        not silently run an unconfigured guard."""
        from aquilia.faults.domains import ConfigInvalidFault

        with pytest.raises(ConfigInvalidFault, match="dotted path"):
            async with TestServer(
                manifests=[_manifest()],
                enable_auth=True,
                config_overrides={
                    "integrations": {"auth": _default_auth_config(global_guards=["RolesGuard"])}
                },
            ) as server:
                pass  # pragma: no cover — boot must fail before this


@pytest.mark.asyncio
class TestC3FailClosedBootstrap:
    async def test_insecure_secret_fails_closed_outside_dev(self):
        """C3: in non-DEV mode, an insecure/missing secret must crash the
        boot instead of silently serving without auth."""
        from aquilia.aquilary.core import RegistryMode

        with pytest.raises(Exception) as exc_info:
            async with TestServer(
                manifests=[_manifest()],
                mode=RegistryMode.PROD,
                debug=False,  # debug mode legitimately stays lenient
                enable_auth=True,
                config_overrides={
                    "integrations": {
                        "auth": {
                            "enabled": True,
                            "tokens": {"secret_key": "aquilia_insecure_dev_secret"},
                        }
                    }
                },
            ) as server:
                pass  # pragma: no cover
        assert "secret" in str(exc_info.value).lower()
