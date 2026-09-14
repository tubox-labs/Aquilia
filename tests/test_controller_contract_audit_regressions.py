"""
Controller/contract regressions from the AniWave migration audit (2026-09-14).

F-10 -- a bare facet class in ``Annotated[str, EmailFacet, ...]`` matched
        nothing in metadata resolution, silently disabling the constraint:
        garbage data was accepted with no warning.
F-16 -- ``SealFault`` stored its errors under ``field_errors`` while the
        constructor keyword is ``errors``, and per-field messages leaked the
        internal ``[BP1xx]`` fault-code prefix into API responses.
F-06  -- the route decorator's ``status_code=`` parameter existed on every
        verb but was never applied: a handler returning a dict always got
        200 even when the route declared 201.
"""

from __future__ import annotations

import re
from typing import Annotated

import pytest

from aquilia import GET, POST, Controller, RequestCtx, Response
from aquilia.contracts import Contract, Field
from aquilia.contracts.exceptions import ContractFault, SealFault, fault_message
from aquilia.contracts.facets import EmailFacet
from aquilia.manifest import AppManifest
from aquilia.testing import TestClient, TestServer


class StatusController(Controller):
    @POST("/created", status_code=201)
    async def create_thing(self, ctx: RequestCtx):
        return {"id": 1}

    @POST("/accepted", status_code=202)
    async def accepted(self, ctx: RequestCtx):
        return "queued"

    @POST("/no-content", status_code=204)
    async def no_content(self, ctx: RequestCtx):
        return None

    @POST("/explicit-response")
    async def explicit(self, ctx: RequestCtx):
        return Response.json({"id": 1}, status=207)

    @GET("/default")
    async def default_status(self, ctx: RequestCtx):
        return {"ok": True}


class RegisterContract(Contract):
    email: Annotated[str, EmailFacet, Field(max_length=254)]


class ContractController(Controller):
    @POST("/register", request_contract=RegisterContract)
    async def register(self, ctx: RequestCtx, contract: RegisterContract):
        return {"email": contract.validated_data["email"]}


def make_manifest(controller, name="audit_app"):
    return AppManifest(
        name=name,
        version="0.0.1",
        controllers=[f"{controller.__module__}:{controller.__name__}"],
    )


@pytest.mark.asyncio
async def test_declared_status_applies_to_dict_returns():
    async with TestServer(manifests=[make_manifest(StatusController)]) as server:
        client = TestClient(server)
        response = await client.post("/audit_app/created")
        assert response.status_code == 201
        assert response.json() == {"id": 1}


@pytest.mark.asyncio
async def test_declared_status_applies_to_str_returns():
    async with TestServer(manifests=[make_manifest(StatusController)]) as server:
        client = TestClient(server)
        response = await client.post("/audit_app/accepted")
        assert response.status_code == 202


@pytest.mark.asyncio
async def test_declared_status_applies_to_none_returns():
    async with TestServer(manifests=[make_manifest(StatusController)]) as server:
        client = TestClient(server)
        response = await client.post("/audit_app/no-content")
        assert response.status_code == 204


@pytest.mark.asyncio
async def test_explicit_response_status_is_not_overridden():
    async with TestServer(manifests=[make_manifest(StatusController)]) as server:
        client = TestClient(server)
        response = await client.post("/audit_app/explicit-response")
        assert response.status_code == 207


@pytest.mark.asyncio
async def test_default_status_unchanged():
    async with TestServer(manifests=[make_manifest(StatusController)]) as server:
        client = TestClient(server)
        response = await client.get("/audit_app/default")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_bare_facet_class_validates_requests():
    """F-10: the natural spelling must not silently disable validation."""
    async with TestServer(manifests=[make_manifest(ContractController, "contract_app")]) as server:
        client = TestClient(server)

        rejected = await client.post("/contract_app/register", json={"email": "not-an-email"})
        assert rejected.status_code == 400

        accepted = await client.post("/contract_app/register", json={"email": "a@b.com"})
        assert accepted.status_code == 200
        assert accepted.json() == {"email": "a@b.com"}


# ── F-16: stable fault surface ──────────────────────────────────────────────


def test_contract_fault_errors_alias():
    fault = ContractFault("boom", errors={"email": ["Invalid email address"]})

    assert fault.errors == {"email": ["Invalid email address"]}
    assert fault.errors is fault.field_errors


def test_seal_fault_errors_alias_and_clean_messages():
    contract = RegisterContract(data={"email": "not-an-email"})
    try:
        contract.is_sealed(raise_fault=True)
        raise AssertionError("expected SealFault")
    except SealFault as fault:
        assert fault.errors == fault.field_errors
        # The internal [BP1xx] code prefix must not leak into field
        # messages -- it is server-side diagnostics, not client content.
        assert not re.search(r"\[BP\d+\]", str(fault.field_errors))
        assert not re.search(r"\[BP\d+\]", str(fault.errors))


def test_fault_message_strips_code_prefix():
    try:
        raise ContractFault("something failed")
    except ContractFault as fault:
        assert fault_message(fault) == "something failed"
        assert str(fault).startswith("[BP000]")

    assert fault_message(ValueError("plain")) == "plain"


# ── F-17: TestClient inline query URLs ──────────────────────────────────────


class QueryController(Controller):
    @GET("/search")
    async def search(self, ctx: RequestCtx):
        q = ctx.query_params.get("q", "")
        tags = ctx.query_params.getlist("tag") if hasattr(ctx.query_params, "getlist") else []
        return {"q": q, "tags": tags}

    @GET("/moved")
    async def moved(self, ctx: RequestCtx):
        return Response("", status=302, headers={"location": "/query_app/search?q=redirected"})


@pytest.mark.asyncio
async def test_inline_query_url_is_split():
    manifest = AppManifest(
        name="query_app",
        version="0.0.1",
        controllers=["tests.test_controller_contract_audit_regressions:QueryController"],
    )
    async with TestServer(manifests=[manifest]) as server:
        client = TestClient(server)

        response = await client.get("/query_app/search?q=hello")
        assert response.status_code == 200, response.text
        assert response.json()["q"] == "hello"


@pytest.mark.asyncio
async def test_multiple_query_params_inline():
    manifest = AppManifest(
        name="query_app",
        version="0.0.1",
        controllers=["tests.test_controller_contract_audit_regressions:QueryController"],
    )
    async with TestServer(manifests=[manifest]) as server:
        client = TestClient(server)

        response = await client.get("/query_app/search?q=a&tag=x&tag=y")
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["q"] == "a"


@pytest.mark.asyncio
async def test_explicit_query_string_still_works():
    manifest = AppManifest(
        name="query_app",
        version="0.0.1",
        controllers=["tests.test_controller_contract_audit_regressions:QueryController"],
    )
    async with TestServer(manifests=[manifest]) as server:
        client = TestClient(server)

        response = await client.get("/query_app/search", query_string="q=explicit")
        assert response.status_code == 200, response.text
        assert response.json()["q"] == "explicit"


@pytest.mark.asyncio
async def test_redirect_location_with_query_is_followed():
    manifest = AppManifest(
        name="query_app",
        version="0.0.1",
        controllers=["tests.test_controller_contract_audit_regressions:QueryController"],
    )
    async with TestServer(manifests=[manifest]) as server:
        client = TestClient(server)

        response = await client.get("/query_app/moved", follow_redirects=True)
        assert response.status_code == 200, response.text
        assert response.json()["q"] == "redirected"
