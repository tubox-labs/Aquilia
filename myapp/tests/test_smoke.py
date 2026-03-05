"""
Smoke tests for myapp workspace.

Demonstrates both testing styles available in aquilia.testing:
- SimpleTestCase  -- pure unit tests, no server overhead
- AquiliaTestCase -- full async test case with live TestServer
- pytest fixtures -- functional style via aquilia_fixtures()
"""

import aquilia
from aquilia.testing import (
    AquiliaTestCase,
    SimpleTestCase,
    TestClient,
)


# ── Unit-style tests (no server) ──────────────────────────────────

class TestWorkspace(SimpleTestCase):
    """Verify the workspace boots without errors."""

    def test_aquilia_importable(self):
        """Aquilia framework must be importable."""
        self.assertIsNotNone(aquilia.__version__)

    def test_aquilia_version_is_string(self):
        self.assertIsInstance(aquilia.__version__, str)


# ── Integration-style tests (full server lifecycle) ───────────────

class TestSmoke(AquiliaTestCase):
    """
    End-to-end smoke tests against a live TestServer.

    ``self.client`` is a :class:`TestClient` pre-wired to the server.
    Add your manifests via ``manifests = [my_manifest]``.
    """

    settings = {"debug": True}

    async def test_health_endpoint(self):
        """Built-in /health endpoint must return 200."""
        resp = await self.client.get("/health")
        self.assert_status(resp, 200)

    async def test_response_is_json(self):
        """Health response should be valid JSON."""
        resp = await self.client.get("/health")
        self.assert_json(resp)


# ── Pytest-fixture style tests ────────────────────────────────────

async def test_health_with_fixture(test_client):
    """
    Same smoke test using the ``test_client`` pytest fixture.

    Registered automatically by ``aquilia_fixtures()`` in conftest.py.
    """
    resp = await test_client.get("/health")
    assert resp.status_code == 200


async def test_fault_engine_captures(test_server, fault_engine):
    """MockFaultEngine records faults for assertion in tests."""
    fault_engine.raise_on_next("not_found", message="Resource missing")
    assert fault_engine.has_pending()


async def test_settings_override(test_client, settings_override):
    """settings_override context manager lets you flip config mid-test."""
    with settings_override(debug=False):
        resp = await test_client.get("/health")
        assert resp.status_code == 200
