"""
Shared test configuration for myapp.

Registers all Aquilia testing fixtures (TestServer, TestClient,
MockFaultEngine, MockEffectRegistry, etc.) and provides
workspace-level overrides.

Run tests with:
    aq test
Or directly:
    pytest tests/ -v
"""

import pytest

# Register all built-in Aquilia fixtures:
#   test_server, test_client, ws_client, fault_engine,
#   effect_registry, di_container, identity_factory,
#   mail_outbox, test_request, test_scope, settings_override
from aquilia.testing.fixtures import aquilia_fixtures
aquilia_fixtures()


# ── Workspace-level overrides ─────────────────────────────────────

@pytest.fixture
def app_settings():
    """
    Base settings applied to every test server in this workspace.
    Override per-test via the ``settings_override`` fixture or
    by setting ``settings = {...}`` on an :class:`AquiliaTestCase`.
    """
    return {
        "debug": True,
        "runtime": {"mode": "test"},
    }
