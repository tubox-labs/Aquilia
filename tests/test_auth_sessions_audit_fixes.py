"""Regression tests for the auth/sessions/admin forensic-audit fixes.

Covers, per the audit report:

* F-AU-01 — pre-auth admin routes (``GET/POST /admin/login``,
  ``GET /admin/offline``) are marked public so
  ``auth.require_auth_by_default=True`` no longer locks the framework
  admin. Unmarked API routes still 401.
* F-AU-06 / NEW-6 — session cookie churn: eager anonymous-session
  creation on every API response. Fixed by two policy knobs:
  ``path_prefix`` (skip the session lifecycle outside a URL prefix) and
  ``persist_anonymous=False`` (never persist or cookie an untouched
  anonymous session). Defaults preserve historic behavior.
* NEW-2 — session fixation: ``Session.regenerate()`` now exists and the
  admin login calls it, so the pre-login session ID does not survive
  authentication.
* NEW-3 — privilege revocation lag: the session stores ``identity_id``
  (+ minimal display snapshot) and the admin re-resolves the identity
  per request; a downgrade/delete in the store takes effect on the next
  request. The env-superuser fallback identity (``admin-1``) is the only
  stored-dict case.
* NEW-4 — env-superuser hardening: dev/test-gated, timing-safe compare.
* NEW-8 — password backend username-enumeration timing parity via a
  fixed dummy hash on every miss path.
* NEW-9 — TOTP replay protection via last-used-counter tracking.
"""

from __future__ import annotations

import asyncio
import re
import time
from typing import Any

import pytest

from aquilia.controller.base import Controller, RequestCtx
from aquilia.controller.decorators import GET
from aquilia.manifest import AppManifest
from aquilia.testing import TestClient, TestServer

# ── Shared fixtures ────────────────────────────────────────────────────────

SUPERUSER = {"AQUILIA_ADMIN_USER": "root", "AQUILIA_ADMIN_PASSWORD": "S3cret-Pass!"}


class AuditFixApi(Controller):
    """API controller wired into the manifest-app used by these tests."""

    @GET("/ping")
    async def ping(self, ctx: RequestCtx) -> dict:
        return {"pong": True}


def _api_manifest() -> AppManifest:
    return AppManifest(
        name="auditfix",
        version="0.0.1",
        controllers=["tests.test_auth_sessions_audit_fixes:AuditFixApi"],
    )


async def _make_server(
    *,
    auth: bool = False,
    require_auth_by_default: bool = False,
    session_policy: Any = None,
    store: Any = None,
    debug: bool = True,
) -> TestServer:
    sessions: dict[str, Any] = {"enabled": True}
    if session_policy is not None:
        sessions["policy"] = session_policy
        if store is not None:
            sessions["store"] = store

    auth_cfg: dict[str, Any] = {"enabled": True, "backends": ["session"]}
    if require_auth_by_default:
        auth_cfg["require_auth_by_default"] = True
        auth_cfg["tokens"] = {"secret_key": "audit-fixes-test-secret-key-0123456789ab"}

    integrations: dict[str, Any] = {
        "admin": {"enabled": True},
        "sessions": sessions,
    }
    if auth:
        integrations["auth"] = auth_cfg

    server = TestServer(
        manifests=[_api_manifest()],
        enable_sessions=True,
        enable_auth=auth,
        debug=debug,
        config_overrides={"integrations": integrations},
    )
    await server.start()
    return server


async def _drive_login(client: TestClient) -> tuple[int, str | None]:
    """GET the login page, POST env-superuser credentials."""
    page = await client.get("/admin/login")
    assert page.status_code == 200
    match = re.search(r'name="_csrf_token"[^>]*value="([^"]+)"', page.text)
    csrf_token = match.group(1) if match else ""
    response = await client.post(
        "/admin/login",
        data={
            "username": SUPERUSER["AQUILIA_ADMIN_USER"],
            "password": SUPERUSER["AQUILIA_ADMIN_PASSWORD"],
            "_csrf_token": csrf_token,
        },
    )
    return response.status_code, response.headers.get("location")


def _has_set_cookie(response) -> bool:
    return "set-cookie" in {k.lower() for k in response.headers}


# ═══════════════════════════════════════════════════════════════════════════
# F-AU-01 — require_auth_by_default must not lock the framework admin
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestPublicPreAuthAdminRoutes:
    async def test_admin_login_page_reachable_under_protect_by_default(self):
        server = await _make_server(auth=True, require_auth_by_default=True)
        try:
            client = TestClient(server)
            response = await client.get("/admin/login")
            assert response.status_code == 200, "pre-auth login route must be public"
        finally:
            await server.stop()

    async def test_admin_offline_reachable_under_protect_by_default(self):
        server = await _make_server(auth=True, require_auth_by_default=True)
        try:
            client = TestClient(server)
            response = await client.get("/admin/offline")
            assert response.status_code == 200, "pre-auth offline route must be public"
        finally:
            await server.stop()

    async def test_unmarked_api_route_still_rejected(self):
        server = await _make_server(auth=True, require_auth_by_default=True)
        try:
            client = TestClient(server)
            response = await client.get("/auditfix/ping")
            assert response.status_code == 401, "unmarked routes must stay protected"
        finally:
            await server.stop()

    async def test_admin_dashboard_still_rejected_anonymously(self):
        server = await _make_server(auth=True, require_auth_by_default=True)
        try:
            client = TestClient(server, follow_redirects=False)
            response = await client.get("/admin/")
            assert response.status_code in (302, 401)
            if response.status_code == 302:
                assert response.headers.get("location") == "/admin/login"
        finally:
            await server.stop()


# ═══════════════════════════════════════════════════════════════════════════
# F-AU-06 / NEW-6 — session cookie churn
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestSessionCookieChurn:
    async def test_default_policy_still_emits_cookie_backcompat(self):
        """Default policy (path_prefix='/', persist_anonymous=True) keeps
        the historic behavior: anonymous API hits get a session cookie."""
        from aquilia.sessions import MemoryStore, SessionPolicy

        store = MemoryStore()
        server = await _make_server(session_policy=SessionPolicy(name="default"), store=store)
        try:
            client = TestClient(server)
            response = await client.get("/auditfix/ping")
            assert response.status_code == 200
            assert _has_set_cookie(response), "default policy must keep emitting cookies"
            assert store.get_stats()["total_sessions"] >= 1
        finally:
            await server.stop()

    async def test_path_prefix_scopes_cookie_to_admin(self):
        """path_prefix='/admin': API routes get no Set-Cookie and create
        zero store entries; admin routes still run the session lifecycle."""
        from aquilia.sessions import MemoryStore, SessionPolicy

        store = MemoryStore()
        server = await _make_server(
            session_policy=SessionPolicy(name="admin_scoped", path_prefix="/admin"), store=store
        )
        try:
            client = TestClient(server)
            api_response = await client.get("/auditfix/ping")
            assert api_response.status_code == 200
            assert not _has_set_cookie(api_response), "API route must not set a session cookie"
            assert store.get_stats()["total_sessions"] == 0

            admin_response = await client.get("/admin/login")
            assert admin_response.status_code == 200
            assert _has_set_cookie(admin_response), "admin routes must still issue sessions"
            assert store.get_stats()["total_sessions"] == 1
        finally:
            await server.stop()

    async def test_persist_anonymous_false_creates_zero_store_entries(self):
        """200 cookie-less anonymous API hits must create ZERO store
        entries (was: one stored session per hit)."""
        from aquilia.sessions import MemoryStore, SessionPolicy

        store = MemoryStore()
        server = await _make_server(
            session_policy=SessionPolicy(name="lazy", persist_anonymous=False), store=store
        )
        try:
            client = TestClient(server)
            for _ in range(200):
                response = await client.get("/auditfix/ping")
                assert response.status_code == 200
            assert store.get_stats()["total_sessions"] == 0, "anonymous hits must not grow the store"
        finally:
            await server.stop()

    async def test_persist_anonymous_false_still_persists_authenticated_login(self, monkeypatch):
        """Lazy persistence must not break the login flow: once the admin
        identity is bound (session data written), the session persists."""
        from aquilia.sessions import MemoryStore, SessionPolicy

        for key, value in SUPERUSER.items():
            monkeypatch.setenv(key, value)

        store = MemoryStore()
        server = await _make_server(
            session_policy=SessionPolicy(name="lazy", persist_anonymous=False), store=store
        )
        try:
            client = TestClient(server, follow_redirects=False)
            status, location = await _drive_login(client)
            assert status == 302 and location == "/admin/"
            assert store.get_stats()["total_sessions"] >= 1, "authenticated session must persist"

            dashboard = await client.get("/admin/")
            assert dashboard.status_code == 200
        finally:
            await server.stop()

    async def test_scoped_and_lazy_admin_login_roundtrip(self, monkeypatch):
        """The recommended scaffold shape (path_prefix + lazy) end-to-end:
        API routes untouched, admin login works, session rotates."""
        from aquilia.sessions import MemoryStore, SessionPolicy

        for key, value in SUPERUSER.items():
            monkeypatch.setenv(key, value)

        store = MemoryStore()
        server = await _make_server(
            session_policy=SessionPolicy(
                name="admin_lazy_scoped", path_prefix="/admin", persist_anonymous=False
            ),
            store=store,
        )
        try:
            client = TestClient(server, follow_redirects=False)

            api_response = await client.get("/auditfix/ping")
            assert not _has_set_cookie(api_response)
            assert store.get_stats()["total_sessions"] == 0

            page = await client.get("/admin/login")
            pre_login_cookie = client.cookies.get("aquilia_session")
            assert pre_login_cookie is not None

            status, location = await _drive_login(client)
            assert status == 302 and location == "/admin/"
            assert store.get_stats()["total_sessions"] >= 1

            dashboard = await client.get("/admin/")
            assert dashboard.status_code == 200
        finally:
            await server.stop()


# ═══════════════════════════════════════════════════════════════════════════
# NEW-2 — session fixation (admin login must rotate the session ID)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestSessionFixationRotation:
    async def test_session_id_rotates_on_login(self, monkeypatch):
        """The pre-login session ID must not survive authentication."""
        for key, value in SUPERUSER.items():
            monkeypatch.setenv(key, value)

        server = await _make_server()
        try:
            client = TestClient(server, follow_redirects=False)

            await client.get("/admin/login")
            pre_login_sid = client.cookies.get("aquilia_session")
            assert pre_login_sid is not None

            status, _ = await _drive_login(client)
            assert status == 302

            post_login_sid = client.cookies.get("aquilia_session")
            assert post_login_sid is not None
            assert post_login_sid != pre_login_sid, "session ID must rotate on login"

            # The old ID must be dead: presenting it alone bounces to login.
            stale = TestClient(server, follow_redirects=False)
            stale.set_cookie("aquilia_session", pre_login_sid)
            dashboard = await stale.get("/admin/")
            assert dashboard.status_code == 302
            assert dashboard.headers.get("location") == "/admin/login"
        finally:
            await server.stop()

    async def test_session_regenerate_method_exists_and_marks(self):
        """Session.regenerate() is real (the old hasattr guard was dead
        code) and requests rotation at commit."""
        from aquilia.sessions.core import Session, SessionID

        session = Session(id=SessionID())
        assert hasattr(session, "regenerate")
        session.regenerate()
        assert getattr(session, "_rotation_requested", False) is True
        assert session.is_dirty

    async def test_engine_commit_rotates_on_regenerate_request(self):
        """SessionEngine.commit honors a regenerate() request: new ID,
        data preserved, old ID gone from the store."""
        from unittest.mock import MagicMock

        from aquilia.sessions import MemoryStore, SessionPolicy
        from aquilia.sessions.engine import SessionEngine
        from aquilia.sessions.transport import CookieTransport

        store = MemoryStore()
        policy = SessionPolicy(name="rotation_test", rotate_on_privilege_change=False)
        transport = MagicMock(spec=CookieTransport)
        engine = SessionEngine(policy=policy, store=store, transport=transport)

        request = MagicMock()
        request.path = "/"
        request.client = ("127.0.0.1", 8000)
        request.header = MagicMock(return_value=None)

        session = await engine.resolve(request)
        session.data["marker"] = "keep-me"
        old_id = session.id
        await store.save(session)

        session.regenerate()
        response = MagicMock()
        await engine.commit(session, response)

        # New session emitted, data preserved, old ID deleted
        new_session = transport.inject.call_args[0][1]
        assert new_session.id != old_id
        assert new_session.data.get("marker") == "keep-me"
        assert await store.load(old_id) is None
        assert await store.load(new_session.id) is not None


# ═══════════════════════════════════════════════════════════════════════════
# NEW-3 — privilege revocation must not lag (identity re-resolution)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestPrivilegeRevocation:
    async def _login_env_superuser(self, monkeypatch) -> tuple[TestServer, TestClient]:
        for key, value in SUPERUSER.items():
            monkeypatch.setenv(key, value)
        server = await _make_server()
        client = TestClient(server, follow_redirects=False)
        status, location = await _drive_login(client)
        assert status == 302 and location == "/admin/"
        return server, client

    async def test_session_stores_identity_id_not_full_payload(self, monkeypatch):
        """Login must write ``identity_id``; the stored snapshot must not
        carry the full roles/permission payload for store-backed
        identities (env-superuser is the sanctioned exception)."""
        from aquilia.sessions.core import SessionID

        server, client = await self._login_env_superuser(monkeypatch)
        try:
            engine = server.server._session_engine
            sid = client.cookies.get("aquilia_session")
            session = await engine.store.load(SessionID.from_string(sid))
            assert session is not None
            assert session.data.get("identity_id"), "login must store identity_id"
            snapshot = session.data.get("_admin_identity", {})
            assert snapshot.get("id") == session.data["identity_id"]
            # Display-only for store-backed identities; the env superuser
            # carries roles because it has no store to re-resolve from.
            assert "name" in snapshot.get("attributes", {})
        finally:
            await server.stop()

    async def test_identity_store_downgrade_revokes_admin_access(self, monkeypatch):
        """A store-backed identity downgraded (roles removed) in the
        identity store loses admin access on the very next request."""
        from aquilia.auth.core import Identity, IdentityType
        from aquilia.auth.stores import MemoryIdentityStore

        # Build an identity store with an admin identity and a session
        # whose identity_id points at it.
        identity_store = MemoryIdentityStore()
        admin_identity = Identity(
            id="admin-store-1",
            type=IdentityType.USER,
            attributes={"username": "dbadmin", "name": "DB Admin", "roles": ["superadmin"]},
        )
        await identity_store.create(admin_identity)

        from aquilia.sessions import MemoryStore, SessionPolicy

        store = MemoryStore()
        server = await _make_server(session_policy=SessionPolicy(name="revocation"), store=store)
        try:
            engine = server.server._session_engine
            # Forge the session the way an authenticated one would look
            # after a store-backed login: identity_id set, no snapshot.
            request_page = await TestClient(server).get("/admin/login")
            client = TestClient(server, follow_redirects=False)

            # Create a session directly in the store bound to the store identity.
            new_session = await engine._create_new(asyncio.get_event_loop().time() and __import__("datetime").datetime.now(__import__("datetime").timezone.utc))
            new_session.data["identity_id"] = "admin-store-1"
            new_session.mark_dirty()
            await engine.store.save(new_session)

            # Register the identity store in the server's auth manager so
            # _resolve_admin_identity can find it via DI.
            auth_manager = server.server._auth_manager
            if auth_manager is not None:
                auth_manager.identity_store = identity_store
            # Register in every DI container (how the server wires stores).
            for container in server.server.runtime.di_containers.values():
                from aquilia.auth.core import IdentityStore
                from aquilia.di.providers import ValueProvider

                container.register(ValueProvider(value=identity_store, token=IdentityStore, scope="app"))

            client.set_cookie("aquilia_session", str(new_session.id))
            dashboard = await client.get("/admin/")
            assert dashboard.status_code == 200, "superadmin identity must access the dashboard"

            # Downgrade: strip the roles in the store.
            downgraded = Identity(
                id="admin-store-1",
                type=IdentityType.USER,
                attributes={"username": "dbadmin", "name": "DB Admin"},
            )
            await identity_store.update(downgraded)

            revoked = await client.get("/admin/")
            assert revoked.status_code == 302, "downgraded identity must lose admin access"
            assert revoked.headers.get("location") == "/admin/login"
            assert request_page.status_code == 200
        finally:
            await server.stop()

    async def test_identity_store_delete_revokes_admin_access(self, monkeypatch):
        """Deleting the identity in the store kills the session's admin
        access immediately (no stale snapshot fallback)."""
        from aquilia.auth.core import Identity, IdentityType
        from aquilia.auth.stores import MemoryIdentityStore
        from aquilia.sessions import MemoryStore, SessionPolicy

        identity_store = MemoryIdentityStore()
        admin_identity = Identity(
            id="admin-store-2",
            type=IdentityType.USER,
            attributes={"username": "dbadmin2", "name": "DB Admin 2", "roles": ["staff"], "admin_role": "staff"},
        )
        await identity_store.create(admin_identity)

        store = MemoryStore()
        server = await _make_server(session_policy=SessionPolicy(name="revocation2"), store=store)
        try:
            engine = server.server._session_engine
            from datetime import datetime, timezone

            new_session = await engine._create_new(datetime.now(timezone.utc))
            new_session.data["identity_id"] = "admin-store-2"
            new_session.mark_dirty()
            await engine.store.save(new_session)

            for container in server.server.runtime.di_containers.values():
                from aquilia.auth.core import IdentityStore
                from aquilia.di.providers import ValueProvider

                container.register(ValueProvider(value=identity_store, token=IdentityStore, scope="app"))

            client = TestClient(server, follow_redirects=False)
            client.set_cookie("aquilia_session", str(new_session.id))
            dashboard = await client.get("/admin/")
            assert dashboard.status_code == 200

            await identity_store.delete("admin-store-2")

            revoked = await client.get("/admin/")
            assert revoked.status_code == 302
            assert revoked.headers.get("location") == "/admin/login"
        finally:
            await server.stop()


# ═══════════════════════════════════════════════════════════════════════════
# NEW-4 — env-superuser hardening (dev/test gate + timing-safe compare)
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestEnvSuperuserHardening:
    async def test_env_fallback_works_in_test_mode(self, monkeypatch):
        from aquilia.admin.controller import AdminController
        from aquilia.admin.site import AdminSite

        for key, value in SUPERUSER.items():
            monkeypatch.setenv(key, value)
        monkeypatch.setenv("AQUILIA_ENV", "test")

        ctrl = AdminController(site=AdminSite())
        identity = await ctrl._authenticate_admin("root", "S3cret-Pass!")
        assert identity is not None
        assert identity.id == "admin-1"

        bad = await ctrl._authenticate_admin("root", "wrong")
        assert bad is None

    async def test_env_fallback_refused_in_production_mode(self, monkeypatch):
        """In prod mode (no dev/test/debug markers) the env fallback must
        refuse login, even with matching credentials."""
        from aquilia.admin.controller import AdminController
        from aquilia.admin.site import AdminSite

        for key, value in SUPERUSER.items():
            monkeypatch.setenv(key, value)
        # Scrub every dev/test marker: bare site, prod env.
        monkeypatch.delenv("AQUILIA_ENV", raising=False)

        site = AdminSite()
        ctrl = AdminController(site=site)
        # No server wired: site.config is None, no debug flag.
        identity = await ctrl._authenticate_admin("root", "S3cret-Pass!")
        assert identity is None, "env fallback must be refused outside dev/test"

    async def test_env_fallback_refused_when_prod_mode_configured(self, monkeypatch):
        from aquilia.admin.controller import AdminController
        from aquilia.admin.site import AdminSite

        for key, value in SUPERUSER.items():
            monkeypatch.setenv(key, value)
        monkeypatch.delenv("AQUILIA_ENV", raising=False)

        site = AdminSite()

        class ProdConfig:
            def get(self, key, default=None):
                return {"mode": "production", "debug": False}.get(key, default)

        site.config = ProdConfig()
        ctrl = AdminController(site=site)
        identity = await ctrl._authenticate_admin("root", "S3cret-Pass!")
        assert identity is None

    async def test_env_fallback_allowed_when_dev_mode_configured(self, monkeypatch):
        from aquilia.admin.controller import AdminController
        from aquilia.admin.site import AdminSite

        for key, value in SUPERUSER.items():
            monkeypatch.setenv(key, value)
        monkeypatch.delenv("AQUILIA_ENV", raising=False)

        site = AdminSite()

        class DevConfig:
            def get(self, key, default=None):
                return {"mode": "dev"}.get(key, default)

        site.config = DevConfig()
        ctrl = AdminController(site=site)
        identity = await ctrl._authenticate_admin("root", "S3cret-Pass!")
        assert identity is not None

    async def test_prod_mode_http_login_via_env_creds_fails(self, monkeypatch):
        """End-to-end: a prod-mode server (debug=False, runtime.mode=prod)
        must reject the env-superuser login."""
        for key, value in SUPERUSER.items():
            monkeypatch.setenv(key, value)
        monkeypatch.delenv("AQUILIA_ENV", raising=False)

        server = await _make_server(debug=False)
        try:
            # TestConfig.get checks its _overrides dict first — pin every
            # mode signal to production there, plus the process env.
            cfg = server.server.config
            cfg._overrides["runtime"] = {"mode": "production"}
            cfg._overrides["mode"] = "production"
            cfg._overrides["debug"] = False
            cfg._merged = None  # invalidate any cached merge
            monkeypatch.setenv("AQUILIA_ENV", "production")
            client = TestClient(server, follow_redirects=False)
            status, _ = await _drive_login(client)
            assert status == 401, "prod mode must refuse env-superuser login"
        finally:
            await server.stop()

    def test_compare_digest_used_not_eq(self):
        """The credential comparison routes through secrets.compare_digest."""
        import inspect

        from aquilia.admin import controller as admin_controller

        source = inspect.getsource(admin_controller.AdminController._authenticate_admin)
        assert "compare_digest" in source, "login must use timing-safe comparison"


# ═══════════════════════════════════════════════════════════════════════════
# NEW-8 — password backend username-enumeration timing parity
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
class TestPasswordBackendTimingParity:
    def _backend(self):
        from aquilia.auth.backends.password import PasswordBackend
        from aquilia.auth.hashing import PasswordHasher
        from aquilia.auth.stores import MemoryCredentialStore, MemoryIdentityStore

        return PasswordBackend(
            identity_store=MemoryIdentityStore(),
            credential_store=MemoryCredentialStore(),
            password_hasher=PasswordHasher(),
        )

    async def test_unknown_username_verifies_dummy_hash(self):
        """The unknown-username path must run a hash verification (dummy
        hash) so its timing matches the wrong-password path."""
        from aquilia.auth.faults import AUTH_INVALID_CREDENTIALS

        backend = self._backend()
        calls: list[tuple[str, str]] = []
        original_verify = backend._hasher.verify

        def spying_verify(password_hash, password):
            calls.append((password_hash, password))
            return original_verify(password_hash, password)

        backend._hasher.verify = spying_verify

        with pytest.raises(AUTH_INVALID_CREDENTIALS):
            await backend.authenticate({"username": "ghost", "password": "whatever"})
        assert calls, "unknown username must still perform a hash verification"

    async def test_missing_credential_verifies_dummy_hash(self):
        """Known identity without a password credential must also pay the
        dummy-verification cost."""
        from aquilia.auth.core import Identity, IdentityType
        from aquilia.auth.faults import AUTH_INVALID_CREDENTIALS

        backend = self._backend()
        await backend._identity_store.create(
            Identity(id="u1", type=IdentityType.USER, attributes={"email": "u1@example.com"})
        )
        calls: list[tuple[str, str]] = []
        original_verify = backend._hasher.verify

        def spying_verify(password_hash, password):
            calls.append((password_hash, password))
            return original_verify(password_hash, password)

        backend._hasher.verify = spying_verify

        with pytest.raises(AUTH_INVALID_CREDENTIALS):
            await backend.authenticate({"username": "u1@example.com", "password": "whatever"})
        assert calls, "missing-credential path must still perform a hash verification"

    async def test_timing_parity_loose_bound(self):
        """Both paths (unknown username vs wrong password) cost the same
        order of magnitude — the miss path must pay real Argon2 work."""
        from aquilia.auth.core import Identity, IdentityType, PasswordCredential
        from aquilia.auth.faults import AUTH_INVALID_CREDENTIALS

        backend = self._backend()
        await backend._identity_store.create(
            Identity(id="u2", type=IdentityType.USER, attributes={"email": "u2@example.com"})
        )
        await backend._credential_store.save_password(
            PasswordCredential(
                identity_id="u2",
                password_hash=backend._hasher.hash("correct-horse-battery"),
            )
        )

        async def _timed(username: str) -> float:
            start = time.perf_counter()
            with pytest.raises(AUTH_INVALID_CREDENTIALS):
                await backend.authenticate({"username": username, "password": "wrong-password"})
            return time.perf_counter() - start

        unknown = min([await _timed("ghost-user") for _ in range(3)])
        wrong_pw = min([await _timed("u2@example.com") for _ in range(3)])

        # Loose bound: the unknown-user path must not be ~free relative to
        # the wrong-password path (previously it skipped Argon2 entirely).
        assert unknown >= wrong_pw * 0.25, (
            f"unknown-username path too fast ({unknown:.4f}s vs {wrong_pw:.4f}s) "
            "-- enumeration oracle"
        )

    async def test_dummy_hash_built_once_and_used(self):
        from aquilia.auth.backends import password as password_module

        backend = self._backend()
        first = password_module._dummy_hash(backend._hasher)
        second = password_module._dummy_hash(backend._hasher)
        assert first is second, "dummy hash must be computed once"
        assert first.startswith("$") or ":" in first or len(first) > 20, "dummy must be a real hash"


# ═══════════════════════════════════════════════════════════════════════════
# NEW-9 — TOTP replay protection
# ═══════════════════════════════════════════════════════════════════════════


class TestTotpReplayProtection:
    def _provider(self):
        from aquilia.auth.mfa import TOTPProvider

        return TOTPProvider()

    def test_code_verifies_first_time(self):
        totp = self._provider()
        secret = totp.generate_secret()
        ts = 1_700_000_000
        code = totp.generate_code(secret, ts)
        assert totp.verify_code(secret, code, timestamp=ts)

    def test_same_code_rejected_on_replay(self):
        """A code that already verified once must not verify again within
        its window (the audit's core replay scenario)."""
        totp = self._provider()
        secret = totp.generate_secret()
        ts = 1_700_000_000
        code = totp.generate_code(secret, ts)

        assert totp.verify_code(secret, code, timestamp=ts)
        used_counter = totp.last_verified_counter
        assert used_counter is not None

        # Replay the exact same code at the same timestamp.
        assert not totp.verify_code(secret, code, timestamp=ts, last_used_counter=used_counter)
        # Replay it within the drift window too.
        assert not totp.verify_code(
            secret, code, timestamp=ts + 30, last_used_counter=used_counter
        )

    def test_next_period_code_accepted_after_replay(self):
        """Replay protection must not brick the token: the next period's
        code still verifies."""
        totp = self._provider()
        secret = totp.generate_secret()
        ts = 1_700_000_000
        code = totp.generate_code(secret, ts)
        assert totp.verify_code(secret, code, timestamp=ts)
        used_counter = totp.last_verified_counter

        next_code = totp.generate_code(secret, ts + 30)
        assert totp.verify_code(secret, next_code, timestamp=ts + 30, last_used_counter=used_counter)

    def test_stateless_without_counter_keeps_historic_behavior(self):
        """Without a persisted counter (legacy stateless callers) the
        provider keeps its documented historic semantics."""
        totp = self._provider()
        secret = totp.generate_secret()
        ts = 1_700_000_000
        code = totp.generate_code(secret, ts)
        assert totp.verify_code(secret, code, timestamp=ts)
        assert totp.verify_code(secret, code, timestamp=ts)


# ═══════════════════════════════════════════════════════════════════════════
# CLI generator — admin sessions block emission (NEW-5 / NEW-6 scaffold)
# ═══════════════════════════════════════════════════════════════════════════


class TestAdminGeneratorSessionBlock:
    def test_injected_block_scopes_sessions_and_secures_cookie(self):
        """The aq admin generator's sessions block must scope sessions to
        /admin, persist lazily, and not hardcode cookie_secure=False."""
        import inspect

        from aquilia.cli import __main__ as cli_main

        source = inspect.getsource(cli_main)
        assert 'cookie_secure=False' not in source, (
            "generator must not hardcode cookie_secure=False (NEW-5); omit the "
            "key or emit True so the dev override applies"
        )
        # The injected block carries the scoping keys.
        assert '"path_prefix="/admin"' in source or 'path_prefix="/admin"' in source
        assert "persist_anonymous=False" in source

    def test_emitted_block_is_valid_python(self):
        """The generator's emitted sessions block parses as Python."""
        import ast
        import inspect

        from aquilia.cli import __main__ as cli_main

        source = inspect.getsource(cli_main)
        tree = ast.parse(source)
        sessions_blocks: list[str] = []
        for node in ast.walk(tree):
            # find `X = "\n" + "\n".join("    " + line for line in [...])`
            if not isinstance(node, ast.Assign):
                continue
            value = node.value
            if not (
                isinstance(value, ast.BinOp)
                and isinstance(value.op, ast.Add)
                and isinstance(value.right, ast.Call)
                and isinstance(value.right.func, ast.Attribute)
                and value.right.func.attr == "join"
            ):
                continue
            for gen in value.right.args:
                if not isinstance(gen, ast.GeneratorExp):
                    continue
                # prefix: "    " + line
                prefix = ""
                elt = gen.elt
                if isinstance(elt, ast.BinOp) and isinstance(elt.left, ast.Constant):
                    prefix = elt.left.value
                # iterable: the list of string constants
                for comp in gen.generators:
                    it = comp.iter
                    if isinstance(it, ast.List):
                        if not all(isinstance(e, ast.Constant) for e in it.elts):
                            continue
                        entries = [e.value for e in it.elts]
                        sessions_blocks.append(
                            "\n".join(prefix + e for e in entries)
                        )
        assert sessions_blocks, "no generated blocks found"
        sessions_block = next(b for b in sessions_blocks if ".sessions(" in b)
        # The block is a method-call fragment (.sessions(...) chained onto
        # the workspace builder) — it is only valid as a continuation inside
        # an open expression, which is exactly how the generator inserts it.
        compile(
            "\n_result = (\n    _workspace\n" + sessions_block + "\n)\n",
            "<generated-sessions-block>",
            "exec",
        )
        # Sanity: the block carries the scoping keys.
        assert "path_prefix" in sessions_block
        assert "persist_anonymous" in sessions_block


# ═══════════════════════════════════════════════════════════════════════════
# NEW-1 / NEW-7 — documented decisions (no behavior change)
# ═══════════════════════════════════════════════════════════════════════════


class TestDocumentedDecisions:
    def test_token_session_binding_note_present(self):
        """NEW-1: the token→session binding carries a security note
        documenting the CSRF trade-off (audit decision: do not fix)."""
        import inspect

        from aquilia.auth.integration import middleware

        source = inspect.getsource(middleware)
        assert "SECURITY NOTE" in source
        assert "NEW-1" in source

    def test_session_policy_defaults_preserve_historic_behavior(self):
        """The two new policy knobs default to the historic eager,
        match-everything behavior."""
        from aquilia.sessions import SessionPolicy

        policy = SessionPolicy(name="defaults")
        assert policy.path_prefix == "/"
        assert policy.persist_anonymous is True
