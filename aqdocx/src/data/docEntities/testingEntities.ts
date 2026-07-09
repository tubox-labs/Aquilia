import { registerDocEntities } from '../../lib/docPreview/registry'

registerDocEntities([
  {
    id: 'testing.test_client',
    type: 'class',
    title: 'TestClient',
    description: 'In-process ASGI HTTP client for issuing mock requests to controllers. Does not open socket connections, supports session cookies, authorization headers, and files/multipart payloads.',
    signature: 'class TestClient:\n    def __init__(self, server_or_app: Any, *, base_url: str = "http://testserver", raise_server_exceptions: bool = True, follow_redirects: bool = False)',
    language: 'python',
    example: {
      code: `async with TestClient(app) as client:
    resp = await client.get("/api/users")
    assert resp.status_code == 200`,
      language: 'python'
    },
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/testing/client'
  },
  {
    id: 'testing.websocket_client',
    type: 'class',
    title: 'WebSocketTestClient',
    description: 'In-process WebSocket testing client. Simulates client connection handshake, send/receive text, JSON events, and binary data against @Socket controllers.',
    signature: 'class WebSocketTestClient:\n    def __init__(self, server_or_app: Any)',
    language: 'python',
    example: {
      code: `async with WebSocketTestClient(app) as ws:
    await ws.connect("/ws/chat")
    await ws.send_json({"event": "join", "room": "general"})
    event = await ws.receive_json()`,
      language: 'python'
    },
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/testing/client'
  },
  {
    id: 'testing.simple_test_case',
    type: 'class',
    title: 'SimpleTestCase',
    description: 'Lightweight unit test case subclass. Inherits from unittest.TestCase and provides AquiliaAssertions. Does not run dependency injection or server lifecycles.',
    signature: 'class SimpleTestCase(unittest.TestCase, AquiliaAssertions)',
    language: 'python',
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/testing/cases'
  },
  {
    id: 'testing.aquilia_test_case',
    type: 'class',
    title: 'AquiliaTestCase',
    description: 'Central async test case class. Automatically boots a TestServer before each test, tears it down after, and initializes self.client (TestClient). Gives access to self.di_container.',
    signature: 'class AquiliaTestCase(unittest.IsolatedAsyncioTestCase, AquiliaAssertions):\n    manifests: list[AppManifest] = []\n    settings: dict[str, Any] = {}',
    language: 'python',
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/testing/cases'
  },
  {
    id: 'testing.transaction_test_case',
    type: 'class',
    title: 'TransactionTestCase',
    description: 'Extends AquiliaTestCase to automatically wrap each test execution in a database transaction, rolling it back on teardown to ensure DB clean isolation.',
    signature: 'class TransactionTestCase(AquiliaTestCase)',
    language: 'python',
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/testing/cases'
  },
  {
    id: 'testing.live_server_test_case',
    type: 'class',
    title: 'LiveServerTestCase',
    description: 'Starts a genuine TCP Uvicorn server in a background task on a random port. Allows testing with standard HTTP clients (e.g. httpx, requests) and browser automation.',
    signature: 'class LiveServerTestCase(AquiliaTestCase):\n    host: str = "127.0.0.1"\n    port: int = 0',
    language: 'python',
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/testing/cases'
  },
  {
    id: 'testing.override_settings',
    type: 'decorator',
    title: '@override_settings',
    description: 'Decorator or context manager that overrides specific configuration settings for the duration of a test function or context block.',
    signature: 'def override_settings(**settings: Any)',
    language: 'python',
    example: {
      code: `@override_settings(debug=True, cache={"backend": "null"})
async def test_debug_endpoint(self):
    resp = await self.client.get("/debug")`,
      language: 'python'
    },
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/testing/cases'
  },
  {
    id: 'testing.mock_fault_engine',
    type: 'class',
    title: 'MockFaultEngine',
    description: 'Mock implementation of FaultEngine. Captures all emitted faults in self.captured list, allowing assertions without dispatching them to external handlers.',
    signature: 'class MockFaultEngine:\n    def __init__(self)',
    language: 'python',
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/testing/mocks'
  },
  {
    id: 'testing.mock_effect_registry',
    type: 'class',
    title: 'MockEffectRegistry',
    description: 'Test-friendly EffectRegistry. Automatically creates MockEffectProviders for any unregistered effect tokens, easing effect-stubbing inside FlowContexts.',
    signature: 'class MockEffectRegistry(EffectRegistry):\n    def __init__(self)',
    language: 'python',
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/testing/mocks'
  },
  {
    id: 'testing.mock_provider',
    type: 'function',
    title: 'mock_provider',
    description: 'Creates a mock DI provider that returns a fixed value. Used to override dependencies in the container during testing.',
    signature: 'def mock_provider(token: type[T] | str, value: T, scope: str = "singleton") -> _MockProvider',
    language: 'python',
    example: {
      code: `fake_repo = FakeUserRepository()
provider = mock_provider(UserRepository, fake_repo)
container.register(provider)`,
      language: 'python'
    },
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/testing/mocks'
  },
  {
    id: 'testing.spy_provider',
    type: 'function',
    title: 'spy_provider',
    description: 'Wraps an existing provider to record its resolves and instantiation counts, while still invoking the original factory/class logic.',
    signature: 'def spy_provider(container: Container, token: type[T] | str, *, tag: str | None = None)',
    language: 'python',
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/testing/mocks'
  },
  {
    id: 'testing.override_provider',
    type: 'function',
    title: 'override_provider',
    description: 'Async context manager to temporarily override a DI token provider in a container, restoring the original provider upon exit.',
    signature: 'async def override_provider(container: Container, token: type[T] | str, mock_value: T, *, tag: str | None = None)',
    language: 'python',
    example: {
      code: `async with override_provider(container, UserRepo, FakeRepo()):
    user_repo = await container.resolve_async(UserRepo)
    assert isinstance(user_repo, FakeRepo)`,
      language: 'python'
    },
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/testing/mocks'
  }
])
