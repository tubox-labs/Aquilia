"""Cross-module DI links via `imports` -- F-11 of the AniWave audit.

The audit found that replacing manifest ``depends_on`` with ``imports``
(per the deprecation warning's own recommendation) broke cross-module
injection: only ``depends_on`` created container dependency links, so
``PROVIDER_NOT_FOUND`` came back at runtime. ``imports`` must be a full
functional replacement.
"""

from __future__ import annotations

from typing import Annotated

import pytest

from aquilia import GET, Controller, RequestCtx
from aquilia.di import Inject
from aquilia.manifest import AppManifest
from aquilia.testing import TestClient, TestServer


class ProviderService:
    def name(self) -> str:
        return "providers"


class CatalogService:
    def __init__(self, provider: Annotated[ProviderService, Inject()]):
        self._provider = provider

    def provider_name(self) -> str:
        return self._provider.name()


class CatalogController(Controller):
    @GET("/provider-name")
    async def provider_name(self, ctx: RequestCtx):
        service = await ctx.container.resolve_async(CatalogService)
        return {"provider": service.provider_name()}


def _manifests():
    import sys

    module = sys.modules[__name__]
    return [
        AppManifest(
            name="prov",
            version="0.0.1",
            services=[f"{module.__name__}:ProviderService"],
            # The v2 spelling only -- no depends_on anywhere.
            imports=[],
        ),
        AppManifest(
            name="shop",
            version="0.0.1",
            controllers=[f"{module.__name__}:CatalogController"],
            services=[f"{module.__name__}:CatalogService"],
            # The audit's exact replacement: imports instead of depends_on.
            imports=["prov"],
        ),
    ]


@pytest.mark.asyncio
async def test_imports_creates_dependency_links():
    async with TestServer(manifests=_manifests()) as server:
        client = TestClient(server)
        response = await client.get("/shop/provider-name")

    assert response.status_code == 200, response.text
    assert response.json() == {"provider": "providers"}


@pytest.mark.asyncio
async def test_depends_on_still_creates_dependency_links():
    import sys

    module = sys.modules[__name__]
    manifests = [
        AppManifest(
            name="prov",
            version="0.0.1",
            services=[f"{module.__name__}:ProviderService"],
        ),
        AppManifest(
            name="shop",
            version="0.0.1",
            controllers=[f"{module.__name__}:CatalogController"],
            services=[f"{module.__name__}:CatalogService"],
            depends_on=["prov"],
        ),
    ]
    async with TestServer(manifests=manifests) as server:
        client = TestClient(server)
        response = await client.get("/shop/provider-name")

    assert response.status_code == 200, response.text
    assert response.json() == {"provider": "providers"}


def test_depends_on_and_imports_are_synced():
    """Whichever spelling is used, both fields agree after construction."""
    forward = AppManifest(name="a", version="0", depends_on=["b"])
    backward = AppManifest(name="c", version="0", imports=["b"])

    assert forward.imports == ["b"]
    assert backward.depends_on == ["b"]
