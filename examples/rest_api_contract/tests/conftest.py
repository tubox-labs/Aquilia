"""
Shared test configuration for rest_api_contract.

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
pytest_plugins = ["aquilia.testing.fixtures"]


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
