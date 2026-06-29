import asyncio

import pytest

from aquilia import GET, Controller, RequestCtx, Response
from aquilia.manifest import AppManifest
from aquilia.testing import TestClient, TestServer


class SimpleController(Controller):
    @GET("/request-id")
    async def get_request_id(self, ctx: RequestCtx):
        return Response.json({"ctx_request_id": ctx.request_id})


def make_manifest():
    return AppManifest(
        name="test_app",
        version="0.0.1",
        controllers=["tests.test_request_id_stability:SimpleController"],
    )


@pytest.mark.asyncio
async def test_request_id_stable_without_header():
    manifest = make_manifest()
    async with TestServer(manifests=[manifest]) as server:
        client = TestClient(server)
        response = await client.get("/test_app/request-id")
        assert response.status_code == 200
        data = response.json()
        ctx_request_id = data["ctx_request_id"]
        response_header_request_id = response.headers.get("x-request-id")
        assert ctx_request_id is not None
        assert response_header_request_id is not None
        assert ctx_request_id == response_header_request_id


@pytest.mark.asyncio
async def test_request_id_header_still_wins():
    manifest = make_manifest()
    async with TestServer(manifests=[manifest]) as server:
        client = TestClient(server)
        response = await client.get("/test_app/request-id", headers={"x-request-id": "custom-id-123"})
        assert response.status_code == 200
        data = response.json()
        assert data["ctx_request_id"] == "custom-id-123"
        assert response.headers.get("x-request-id") == "custom-id-123"


@pytest.mark.asyncio
async def test_request_id_unique_per_request():
    manifest = make_manifest()
    async with TestServer(manifests=[manifest]) as server:
        client = TestClient(server)

        async def make_req():
            resp = await client.get("/test_app/request-id")
            return resp.headers.get("x-request-id")

        tasks = [make_req() for _ in range(200)]
        ids = await asyncio.gather(*tasks)
        assert len(ids) == 200
        assert len(set(ids)) == 200
