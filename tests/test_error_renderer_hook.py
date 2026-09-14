"""Pluggable error renderer -- F-20 of the AniWave migration audit.

The exception middleware hard-coded its ``{"error": {...}}`` envelope, so
an application with an existing error contract (the audit's client expected
``{statusCode, code, message, details?, requestId}``) had to replace the
entire middleware -- inheriting its responsibilities (request-id header,
final-status access logging) by hand. ``ExceptionMiddleware(error_renderer=...)``
customizes only the body; the middleware keeps status, headers, and the
fallback when the renderer itself fails.
"""

from __future__ import annotations

import pytest

from aquilia import GET, Controller, RequestCtx
from aquilia.faults.domains import HTTPFault
from aquilia.manifest import AppManifest
from aquilia.middleware.builtin.exceptions import ExceptionMiddleware
from aquilia.testing import TestClient, TestServer


class BoomController(Controller):
    @GET("/boom")
    async def boom(self, ctx: RequestCtx):
        raise HTTPFault(status=418, code="TEAPOT", message="short and stout")

    @GET("/fine")
    async def fine(self, ctx: RequestCtx):
        return {"ok": True}


def custom_renderer(fault, status, request):
    return {
        "statusCode": status,
        "code": getattr(fault, "code", "UNKNOWN"),
        "message": str(getattr(fault, "message", fault)),
        "requestId": getattr(request.state, "get", lambda k, default=None: default)("request_id"),
    }


def _manifest():
    return AppManifest(
        name="renderer_app",
        version="0.0.1",
        controllers=["tests.test_error_renderer_hook:BoomController"],
    )


def test_middleware_uses_renderer_body():
    middleware = ExceptionMiddleware(error_renderer=custom_renderer)
    assert middleware.error_renderer is custom_renderer


@pytest.mark.asyncio
async def test_default_envelope_unchanged_without_renderer():
    async with TestServer(manifests=[_manifest()]) as server:
        client = TestClient(server)
        response = await client.get("/renderer_app/boom")

    assert response.status_code == 418
    body = response.json()
    assert body["error"]["code"] == "TEAPOT"


@pytest.mark.asyncio
async def test_renderer_body_replaces_envelope_but_not_status():
    """Wire the renderer by patching the booted server's middleware."""
    async with TestServer(manifests=[_manifest()]) as server:
        # Replace the renderer on the live exception middleware -- the same
        # object the FaultHandlingIntegration path would have constructed
        # it with.
        for descriptor in server.server.middleware_stack.middlewares:
            middleware = getattr(descriptor, "middleware", descriptor)
            if isinstance(middleware, ExceptionMiddleware):
                middleware.error_renderer = custom_renderer

        client = TestClient(server)
        response = await client.get("/renderer_app/boom")

    assert response.status_code == 418
    body = response.json()
    assert body["statusCode"] == 418
    assert body["code"] == "TEAPOT"
    assert body["message"] == "short and stout"
    assert "error" not in body


@pytest.mark.asyncio
async def test_renderer_failure_falls_back_to_default():
    def broken_renderer(fault, status, request):
        raise RuntimeError("renderer bug")

    async with TestServer(manifests=[_manifest()]) as server:
        for descriptor in server.server.middleware_stack.middlewares:
            middleware = getattr(descriptor, "middleware", descriptor)
            if isinstance(middleware, ExceptionMiddleware):
                middleware.error_renderer = broken_renderer

        client = TestClient(server)
        response = await client.get("/renderer_app/boom")

    assert response.status_code == 418
    assert response.json()["error"]["code"] == "TEAPOT"


@pytest.mark.asyncio
async def test_renderer_none_falls_back_to_default():
    async with TestServer(manifests=[_manifest()]) as server:
        for descriptor in server.server.middleware_stack.middlewares:
            middleware = getattr(descriptor, "middleware", descriptor)
            if isinstance(middleware, ExceptionMiddleware):
                middleware.error_renderer = lambda fault, status, request: None

        client = TestClient(server)
        response = await client.get("/renderer_app/boom")

    assert response.status_code == 418
    assert response.json()["error"]["code"] == "TEAPOT"
