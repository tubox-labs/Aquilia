"""
Aquilia Testing Framework.

Provides a comprehensive, batteries-included testing module tightly
integrated with every Aquilia subsystem: Server, Config, DI, Faults,
Effects, Cache, Sessions, Auth, Controllers, Middleware, CLI, Templates,
WebSockets, Models, and Lifecycle.

Usage:
    from aquilia.testing import AquiliaTestCase, TestClient, override_settings

    class TestMyAPI(AquiliaTestCase):
        settings = {"debug": True}

        async def test_index(self):
            response = await self.client.get("/")
            self.assert_status(response, 200)

Components:
    - TestClient:          HTTP client for controller testing
    - AquiliaTestCase:     Base test case with server lifecycle management
    - TransactionTestCase: Test case with DB transaction rollback
    - LiveServerTestCase:  Test case that starts a real ASGI server
    - override_settings:   Context manager for config overrides
    - TestServer:          Lightweight test server factory
    - MockFaultEngine:     Fault engine with capture/assertion helpers
    - MockEffectRegistry:  Effect registry with stubs
    - CacheTestMixin:      Cache testing utilities
    - AuthTestMixin:       Auth/identity testing helpers
    - MailTestMixin:       Captured outbox for mail assertions
    - WebSocketTestClient: WebSocket testing client
"""

from aquilia._version import __version__  # noqa: F401 — re-exported

from .assertions import AquiliaAssertions
from .auth import AuthTestMixin, IdentityBuilder, TestIdentityFactory
from .cache import CacheTestMixin, MockCacheBackend
from .cases import (
    AquiliaTestCase,
    LiveServerTestCase,
    SimpleTestCase,
    TransactionTestCase,
)
from .client import TestClient, WebSocketTestClient
from .config import TestConfig, override_settings
from .di import (
    TestContainer,
    factory_provider,
    mock_provider,
    override_provider,
    spy_provider,
)
from .effects import EffectCall, MockEffectProvider, MockEffectRegistry
from .faults import CapturedFault, MockFaultEngine
from .fixtures import aquilia_fixtures
from .mail import CapturedMail, MailTestMixin
from .server import TestServer, create_test_server
from .utils import (
    make_test_receive,
    make_test_request,
    make_test_response,
    make_test_scope,
    make_test_ws_scope,
    make_upload_file,
)

__all__ = [
    # Client
    "TestClient",
    "WebSocketTestClient",
    # Test cases
    "AquiliaTestCase",
    "TransactionTestCase",
    "LiveServerTestCase",
    "SimpleTestCase",
    # Server
    "TestServer",
    "create_test_server",
    # Config
    "override_settings",
    "TestConfig",
    # Faults
    "MockFaultEngine",
    "CapturedFault",
    # Effects
    "MockEffectRegistry",
    "MockEffectProvider",
    "EffectCall",
    # Cache
    "CacheTestMixin",
    "MockCacheBackend",
    # Auth
    "AuthTestMixin",
    "TestIdentityFactory",
    "IdentityBuilder",
    # Mail
    "MailTestMixin",
    "CapturedMail",
    # DI
    "TestContainer",
    "mock_provider",
    "override_provider",
    "factory_provider",
    "spy_provider",
    # Assertions
    "AquiliaAssertions",
    # Fixtures
    "aquilia_fixtures",
    # Utils
    "make_test_scope",
    "make_test_request",
    "make_test_receive",
    "make_test_response",
    "make_test_ws_scope",
    "make_upload_file",
]
