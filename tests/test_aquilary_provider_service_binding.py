"""Regression tests for provider-style service bindings in RuntimeRegistry."""

from types import SimpleNamespace

import pytest

from aquilia.aquilary.core import AppContext, RuntimeRegistry
from aquilia.http.client import AsyncHTTPClient
from aquilia.http.integration import HTTPClientProvider
from aquilia.manifest import ServiceConfig


class ProvidedService:
    """Simple service returned by a provider-style class."""


class AliasToken:
    """Alias token for provider output binding."""


class AnnotatedProvider:
    """Provider class exposing a typed provide() method."""

    def provide(self) -> ProvidedService:
        return ProvidedService()


def _build_runtime(services):
    ctx = AppContext(
        name="auth",
        version="1.0.0",
        manifest=SimpleNamespace(__module__="modules.auth.manifest"),
        config_namespace={},
        services=services,
    )
    return RuntimeRegistry.from_metadata(SimpleNamespace(app_contexts=[ctx]), config=SimpleNamespace())


@pytest.mark.asyncio
async def test_runtime_registers_callable_provider_output_token():
    runtime = _build_runtime(["aquilia.http.integration.HTTPClientProvider"])

    runtime._register_services()
    container = runtime.di_containers["auth"]

    assert container.is_registered(HTTPClientProvider)
    assert container.is_registered(AsyncHTTPClient)

    client = await container.resolve_async(AsyncHTTPClient)
    assert isinstance(client, AsyncHTTPClient)

    # The provider instance owns HTTP client shutdown in this binding mode.
    await container.shutdown()


@pytest.mark.asyncio
async def test_runtime_alias_binds_to_provider_output_token():
    runtime = _build_runtime(
        [
            ServiceConfig(
                class_path=f"{__name__}:AnnotatedProvider",
                aliases=[f"{__name__}:AliasToken"],
            )
        ]
    )

    runtime._register_services()
    container = runtime.di_containers["auth"]

    resolved = await container.resolve_async(ProvidedService)
    aliased = await container.resolve_async(AliasToken)

    assert isinstance(resolved, ProvidedService)
    assert isinstance(aliased, ProvidedService)
