"""
Aquilia Testing - Pytest Fixtures.

Provides ready-to-use pytest fixtures for common Aquilia testing
patterns.  Import ``aquilia_fixtures`` in your ``conftest.py`` to
register all fixtures at once, or import individual fixtures.

Usage in conftest.py::

    from aquilia.testing.fixtures import aquilia_fixtures
    aquilia_fixtures()  # registers all fixtures

Or use the plugin entry point (automatic via pip install).
"""

try:
    import pytest

    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False

    class _DummyPytest:
        @staticmethod
        def fixture(*args, **kwargs):
            def decorator(func):
                return func

            if len(args) == 1 and callable(args[0]):
                return args[0]
            return decorator

    pytest = _DummyPytest()

from aquilia.config import ConfigLoader
from aquilia.testing.auth import TestIdentityFactory
from aquilia.testing.cache import MockCacheBackend
from aquilia.testing.client import TestClient, WebSocketTestClient
from aquilia.testing.config import TestConfig, override_settings, set_active_config
from aquilia.testing.di import TestContainer
from aquilia.testing.effects import MockEffectRegistry
from aquilia.testing.faults import MockFaultEngine
from aquilia.testing.mail import clear_outbox, get_outbox
from aquilia.testing.server import TestServer
from aquilia.testing.utils import make_test_request, make_test_scope


def aquilia_fixtures():
    """
    Register Aquilia pytest fixtures.

    Call this function in your ``conftest.py`` to make all fixtures
    available::

        # conftest.py
        from aquilia.testing.fixtures import aquilia_fixtures
        aquilia_fixtures()

    This is a no-op -- the fixtures are registered by the module being
    imported.  The function exists as a documentation anchor and to
    ensure the module's side-effects run.
    """
    if not HAS_PYTEST:
        raise ImportError(
            "pytest is required to use aquilia pytest fixtures. "
            "Install it with: pip install pytest (or pip install aquilia[test])"
        )
    pass  # Side-effect of import registers the fixtures below


# -----------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------


@pytest.fixture
def test_config():
    """A blank :class:`TestConfig` for unit tests."""

    loader = ConfigLoader()
    loader.config_data = {"debug": True, "runtime": {"mode": "test"}}
    cfg = TestConfig(loader)
    set_active_config(cfg)
    yield cfg


@pytest.fixture
def fault_engine():
    """A :class:`MockFaultEngine` for capturing faults."""
    engine = MockFaultEngine()
    yield engine
    engine.reset()


@pytest.fixture
def effect_registry():
    """A :class:`MockEffectRegistry` for stubbing effects."""
    registry = MockEffectRegistry()
    yield registry
    registry.reset_all()


@pytest.fixture
def cache_backend():
    """A :class:`MockCacheBackend` (in-memory, zero-config)."""
    backend = MockCacheBackend()
    yield backend
    backend.reset()


@pytest.fixture
def di_container():
    """A :class:`TestContainer` with relaxed validation."""
    container = TestContainer()
    yield container
    container.reset()


@pytest.fixture
def identity_factory():
    """A :class:`TestIdentityFactory` for creating test identities."""
    return TestIdentityFactory()


@pytest.fixture
def mail_outbox():
    """
    Clear the mail outbox before the test and return it.

    Use ``assert len(mail_outbox) == 1`` to verify mail was sent.
    """
    clear_outbox()
    yield get_outbox()
    clear_outbox()


@pytest.fixture
def test_request():
    """
    Factory fixture -- call with kwargs to create test requests.

    Usage::

        def test_something(test_request):
            req = test_request(method="POST", path="/api", json={"a": 1})
    """
    return make_test_request


@pytest.fixture
def test_scope():
    """
    Factory fixture -- call with kwargs to create ASGI scopes.

    Usage::

        def test_scope_stuff(test_scope):
            scope = test_scope(method="GET", path="/health")
    """
    return make_test_scope


# -----------------------------------------------------------------------
# Async fixtures (require pytest-asyncio)
# -----------------------------------------------------------------------


@pytest.fixture
async def test_server():
    """
    Async fixture providing a booted :class:`TestServer`.

    Shuts down automatically after the test.

    Usage::

        async def test_api(test_server):
            client = TestClient(test_server)
            resp = await client.get("/")
            assert resp.status_code == 200
    """
    server = TestServer()
    await server.start()
    yield server
    await server.stop()


@pytest.fixture
async def test_client(test_server):
    """
    Async fixture providing a :class:`TestClient` wired to a :class:`TestServer`.

    Usage::

        async def test_index(test_client):
            resp = await test_client.get("/")
    """
    return TestClient(test_server)


@pytest.fixture
async def ws_client(test_server):
    """
    Async fixture providing a :class:`WebSocketTestClient` wired to a :class:`TestServer`.

    Usage::

        async def test_websocket(ws_client):
            await ws_client.connect("/ws")
            await ws_client.send_text("hello")
            msg = await ws_client.receive_text()
            await ws_client.close()
    """
    client = WebSocketTestClient(test_server)
    yield client
    if client.is_connected:
        await client.close()


@pytest.fixture
def settings_override():
    """
    Fixture factory for overriding settings.

    Usage::

        def test_debug(settings_override):
            with settings_override(DEBUG=True):
                # config is overridden
                pass
    """
    return override_settings


# ── Session-scoped app boot (pooled resources on one loop) ──────────────
#
# An application holding pooled async resources (asyncpg pools, redis
# clients) binds them to the event loop where startup ran. A
# function-scoped app fixture therefore breaks on the second test with
# ``got Future ... attached to a different loop`` -- an error that says
# nothing about its actual cause. The supported "boot once, test many"
# pattern is the pair of fixtures below plus session-scoped loops:
#
#     # pyproject.toml
#     [tool.pytest.ini_options]
#     asyncio_default_fixture_loop_scope = "session"
#     asyncio_default_test_loop_scope = "session"
#
#     # conftest.py
#     import pytest_asyncio
#     from aquilia.testing.fixtures import aquilia_fixtures
#
#     aquilia_fixtures()
#
#     @pytest_asyncio.fixture(scope="session", loop_scope="session")
#     async def app_server(session_test_server):
#         from myapp.manifests import MY_MANIFEST
#         return await session_test_server(MY_MANIFEST)
#
#     # tests then request `app_server` and build clients from it.

try:
    import pytest_asyncio  # noqa: F401

    _HAS_PYTEST_ASYNCIO = True
except ImportError:  # pragma: no cover -- pytest-asyncio is a test extra
    _HAS_PYTEST_ASYNCIO = False

if _HAS_PYTEST_ASYNCIO:

    @pytest_asyncio.fixture(scope="session", loop_scope="session")
    async def session_test_server():
        """Boot ONE :class:`TestServer` for the whole test session.

        Returns an async factory: the first caller's manifests and keyword
        arguments configure the server; every later call returns the same
        running instance. The server is started on the session's event
        loop (see ``loop_scope`` above) and stopped when the session ends,
        so pooled resources bound at startup stay valid for every test.
        """
        state: dict = {"server": None}

        async def _boot(*manifests, **kwargs):
            if state["server"] is None:
                server = TestServer(manifests=list(manifests), **kwargs)
                await server.start()
                state["server"] = server
            return state["server"]

        yield _boot

        if state["server"] is not None:
            await state["server"].stop()
