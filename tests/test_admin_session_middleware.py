"""Admin session wiring -- the silent login redirect loop.

An application with **sessions enabled** and **framework auth disabled**
(the common shape for apps that manage their own Bearer tokens) never ran
``SessionMiddleware`` and never registered the ``SessionEngine`` in DI:
both were nested inside ``if use_auth:``. The admin dashboard then
authenticated its login correctly, issued no session cookie, and bounced
between ``/admin/login`` and ``/admin/`` forever -- silent, because each
hop is a legitimate 302.

Session middleware and the engine's DI registration are now gated on the
session engine existing, not on auth being enabled. ``AquilAuthMiddleware``
still owns session handling whenever auth initializes, so the session-only
middleware is skipped in that case.
"""

from __future__ import annotations

import re

import pytest

from aquilia.manifest import AppManifest
from aquilia.testing import TestClient, TestServer

SUPERUSER = {"AQUILIA_ADMIN_USER": "root", "AQUILIA_ADMIN_PASSWORD": "S3cret-Pass!"}


def make_server(*, sessions: bool, auth: bool, admin: bool = True) -> TestServer:
    # TestServer's enable_* flags only stop the subsystem being force-DISABLED;
    # the integration entries below are what actually turn things on.
    integrations: dict = {}
    if admin:
        integrations["admin"] = {"enabled": True}
    if sessions:
        integrations["sessions"] = {"enabled": True}
    if auth:
        integrations["auth"] = {"enabled": True}
    return TestServer(
        manifests=[AppManifest(name="sessapp", version="0.0.1")],
        enable_sessions=sessions,
        enable_auth=auth,
        config_overrides={"integrations": integrations},
    )


def middleware_names(server: TestServer) -> list[str | None]:
    return [getattr(descriptor, "name", None) for descriptor in server.middleware_stack.middlewares]


async def drive_login(client: TestClient) -> tuple[int, str | None]:
    """GET the login page, POST credentials; return (status, location)."""
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


@pytest.mark.asyncio
async def test_sessions_without_auth_mount_session_middleware(monkeypatch):
    for key, value in SUPERUSER.items():
        monkeypatch.setenv(key, value)

    server = make_server(sessions=True, auth=False)
    await server.start()
    try:
        names = middleware_names(server)
        assert "session" in names
        assert server.server._session_engine is not None

        client = TestClient(server, follow_redirects=False)
        status, location = await drive_login(client)

        assert status == 302 and location == "/admin/"
        # The TestClient auto-stores response cookies; a session cookie
        # landing here is exactly what the browser would have received.
        assert "aquilia_session" in client.cookies, "login must issue a session cookie"

        # With the (auto-stored) session cookie the dashboard renders.
        dashboard = await client.get("/admin/")
        assert dashboard.status_code == 200
    finally:
        await server.stop()


@pytest.mark.asyncio
async def test_dashboard_still_guarded_without_cookie(monkeypatch):
    """The fix must not weaken the auth guard: no cookie → redirect to login."""
    for key, value in SUPERUSER.items():
        monkeypatch.setenv(key, value)

    server = make_server(sessions=True, auth=False)
    await server.start()
    try:
        client = TestClient(server, follow_redirects=False)
        response = await client.get("/admin/")
        assert response.status_code == 302
        assert response.headers.get("location") == "/admin/login"
    finally:
        await server.stop()


@pytest.mark.asyncio
async def test_session_engine_registered_in_di(monkeypatch):
    for key, value in SUPERUSER.items():
        monkeypatch.setenv(key, value)

    server = make_server(sessions=True, auth=False)
    await server.start()
    try:
        from aquilia.sessions import SessionEngine

        containers = server.server.runtime.di_containers
        assert containers, "no DI containers were created"
        for container in containers.values():
            engine = await container.resolve_async(SessionEngine)
            assert engine is server.server._session_engine
    finally:
        await server.stop()


@pytest.mark.asyncio
async def test_no_session_middleware_when_sessions_disabled():
    server = make_server(sessions=False, auth=False)
    await server.start()
    try:
        names = middleware_names(server)
        assert "session" not in names
        assert "auth" not in names
    finally:
        await server.stop()


@pytest.mark.asyncio
async def test_auth_enabled_mounts_auth_middleware_not_session(monkeypatch):
    """The auth path keeps its shape: AquilAuthMiddleware, no duplicate session mw."""
    for key, value in SUPERUSER.items():
        monkeypatch.setenv(key, value)

    server = make_server(sessions=True, auth=True)
    await server.start()
    try:
        names = middleware_names(server)
        assert "auth" in names
        # AquilAuthMiddleware owns sessions here; the session-only
        # middleware must not double-run.
        assert "session" not in names
    finally:
        await server.stop()


@pytest.mark.asyncio
async def test_admin_di_providers_register_and_resolve():
    """The 1.4.0 'ValueProvider missing token' regression (fixed in fdfa7aec).

    All admin security and subsystem providers must register into a real
    container and resolve back to their values -- the failure mode in
    1.4.0 was silent apart from a boot warning.
    """
    from aquilia.admin.audit import AdminAuditLog
    from aquilia.admin.di_providers import register_admin_providers
    from aquilia.admin.security import (
        AdminCSRFProtection,
        AdminRateLimiter,
        AdminSecurityHeaders,
        AdminSecurityPolicy,
        PasswordValidator,
        SecurityEventTracker,
        register_security_providers,
    )
    from aquilia.di import Container

    container = Container()
    register_security_providers(container)
    register_admin_providers(container)

    for token in (
        AdminSecurityPolicy,
        AdminCSRFProtection,
        AdminRateLimiter,
        AdminSecurityHeaders,
        PasswordValidator,
        SecurityEventTracker,
        AdminAuditLog,
    ):
        assert await container.resolve_async(token) is not None, token
