import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { FlaskConical, Cpu, Layers } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function TestingMocks() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const sectionClass = "mb-16 scroll-mt-24"
  const h2Class = `text-2xl font-bold mb-6 flex items-center gap-3 ${isDark ? 'text-white' : 'text-gray-900'}`
  const h3Class = `text-lg font-semibold mt-8 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`
  const pClass = `mb-4 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`
  const listClass = "space-y-4 pl-5 list-disc"
  const itemClass = `text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`

  return (
    <div className="max-w-4xl mx-auto pb-20">
      {/* Header */}
      <div className="mb-12 border-b border-gray-200 dark:border-white/10 pb-8">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <FlaskConical className="w-4 h-4" />
          Testing / Mocks & Mixins
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Mocks & Test Mixins
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia provides specialized mock objects, context overrides, and testing mixins. Swap dependencies, assert on background flows, and inspect side-effects cleanly from your tests.
        </p>
      </div>

      {/* MockFaultEngine */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Cpu className="w-5 h-5 text-aquilia-400" />
          MockFaultEngine
        </h2>
        <p className={pClass}>
          <DocTerm id="testing.mock_fault_engine">MockFaultEngine</DocTerm> replaces the framework default FaultEngine during test phases, capturing all raised faults into an internal list instead of dispatching them to production handlers.
        </p>

        <CodeBlock language="python" filename="test_faults.py" highlightLines={[5, 9, 13, 14, 15]}>{`from aquilia.testing import MockFaultEngine
from aquilia.faults import Fault

# Setup engine
engine = MockFaultEngine()

# Simulate code emitting a fault
my_fault = Fault(code="DATABASE_TIMEOUT", message="DB took too long")
engine.emit(my_fault, app_name="billing")

# Check captured faults
assert engine.has_fault("DATABASE_TIMEOUT")
assert engine.fault_count == 1
assert engine.last_fault_code == "DATABASE_TIMEOUT"

# Reset history between assertions
engine.reset()
assert engine.fault_count == 0`}</CodeBlock>

        <h3 className={h3Class}>Testing Assertions</h3>
        <p className={pClass}>
          If you subclass <DocTerm id="testing.aquilia_test_case">AquiliaTestCase</DocTerm>, you gain access to the following fault assertion methods:
        </p>
        <ul className={listClass}>
          <li className={itemClass}>
            <strong>self.assert_fault_raised(engine, code=None, domain=None):</strong> Asserts that at least one fault matching the code or domain was captured.
          </li>
          <li className={itemClass}>
            <strong>self.assert_no_faults(engine):</strong> Asserts that no faults were captured.
          </li>
          <li className={itemClass}>
            <strong>self.assert_fault_count(engine, expected):</strong> Asserts that exactly the expected number of faults were captured.
          </li>
        </ul>
      </section>

      {/* MockEffectRegistry */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Cpu className="w-5 h-5 text-aquilia-400" />
          MockEffectRegistry & MockFlowContext
        </h2>
        <p className={pClass}>
          The effect system isolates side effects like databases, cache backends, and task queues. With <DocTerm id="testing.mock_effect_registry">MockEffectRegistry</DocTerm> and <code className="text-aquilia-500">MockFlowContext</code>, you can stub these operations and inject mock values into your pipeline handlers:
        </p>

        <CodeBlock language="python" filename="test_effects.py" highlightLines={[4, 11, 20, 21, 22]}>{`from aquilia.testing import MockEffectRegistry, MockFlowContext

# Create registry and register mock effects
registry = MockEffectRegistry()
mock_db = registry.register_mock("DBTx", return_value="fake_connection")

# Acquire effect resources
provider = registry.get_provider("DBTx")
conn = await provider.acquire(mode="write")
assert conn == "fake_connection"
assert provider.acquire_count == 1

# Setup sequential returns (for multiple calls)
mock_cache = registry.register_mock("Cache", return_sequence=["val1", "val2"])
provider_cache = registry.get_provider("Cache")
assert await provider_cache.acquire() == "val1"
assert await provider_cache.acquire() == "val2"
assert await provider_cache.acquire() == "val2"  # Repeats last item

# Inject into MockFlowContext for pipeline node testing
ctx = MockFlowContext.from_registry(registry)
db_resource = ctx.get_effect("DBTx")
assert db_resource == "fake_connection"`}</CodeBlock>
      </section>

      {/* Dependency Injection (DI) Testing */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Layers className="w-5 h-5 text-aquilia-400" />
          Dependency Injection Overrides
        </h2>
        <p className={pClass}>
          Aquilia's DI system includes testing helpers to override services and monitor calls within the container:
        </p>
        <ul className={listClass}>
          <li className={itemClass}>
            <strong>mock_provider(token, value):</strong> Creates a mock provider that resolves to a fixed stub object.
          </li>
          <li className={itemClass}>
            <strong>override_provider(container, token, mock_value):</strong> Async context manager that temporarily swaps a token provider in the container, restoring the original on exit.
          </li>
          <li className={itemClass}>
            <strong>spy_provider(container, token):</strong> Async context manager that wraps a real provider. It monitors and logs instantiation counts and values, but still delegates calls to the real service.
          </li>
        </ul>

        <CodeBlock language="python" filename="test_di_mocking.py" highlightLines={[7, 13, 17]}>{`from aquilia.testing import override_provider, spy_provider

class TestServiceDI(AquiliaTestCase):
    async def test_repository_override(self):
        # Override the real database repo with a mock repo
        fake_repo = MockUserRepository()
        async with override_provider(self.di_container, UserRepository, fake_repo):
            resolved = await self.di_container.resolve_async(UserRepository)
            assert resolved is fake_repo

    async def test_email_spy(self):
        # Spy on the real email service
        async with spy_provider(self.di_container, EmailService) as spy:
            # Trigger logic that invokes EmailService
            await self.client.post("/api/register", json={"email": "alice@test.com"})
            
            # Assert details on spy
            assert spy.resolve_count == 1
            assert len(spy.resolved_values) == 1`}</CodeBlock>
      </section>

      {/* Testing Mixins */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Layers className="w-5 h-5 text-aquilia-400" />
          Subsystem Mixins
        </h2>
        <p className={pClass}>
          Aquilia includes three mixins to easily interact with and assert on cache, authentication, and mail payloads:
        </p>

        <h3 className={h3Class}>1. CacheTestMixin</h3>
        <p className={pClass}>
          Integrates cache assertions. Automatically hooks into <code className="text-aquilia-500">self.cache_service</code>:
        </p>
        <ul className={listClass}>
          <li className={itemClass}><strong>self.populate_cache(data, ttl=None):</strong> Populate keys into the cache.</li>
          <li className={itemClass}><strong>self.assert_cached(key):</strong> Assert key is present.</li>
          <li className={itemClass}><strong>self.assert_not_cached(key):</strong> Assert key is missing.</li>
          <li className={itemClass}><strong>self.assert_cache_value(key, expected):</strong> Assert key value matches expected.</li>
          <li className={itemClass}><strong>self.assert_cache_count(expected, pattern="*"):</strong> Assert number of matching keys.</li>
          <li className={itemClass}><strong>self.flush_cache():</strong> Flush all keys.</li>
        </ul>

        <h3 className={h3Class}>2. AuthTestMixin</h3>
        <p className={pClass}>
          Enables quick authentication mocking, letting you bypass credential verification:
        </p>
        <ul className={listClass}>
          <li className={itemClass}>
            <strong>self.force_login(identity):</strong> Injects an identity into the TestClient session headers, making subsequent requests appear authenticated.
          </li>
          <li className={itemClass}>
            <strong>self.authenticate_as(identity):</strong> thorough than <code className="text-aquilia-500">force_login</code>, registers the identity directly into the server's identity store.
          </li>
          <li className={itemClass}>
            <strong>self.login_as_admin(id=None, **kw):</strong> Helper that builds an admin identity and authenticates it.
          </li>
          <li className={itemClass}>
            <strong>self.login_as_user(id=None, **kw):</strong> Helper that builds a regular user identity and authenticates it.
          </li>
        </ul>
        <CodeBlock language="python" filename="test_auth_mixin.py" highlightLines={[8, 11]}>{`from aquilia.testing import AquiliaTestCase, AuthTestMixin

class TestBilling(AuthTestMixin, AquiliaTestCase):
    enable_auth = True

    async def test_access_billing(self):
        # Build and authenticate user identity
        self.login_as_admin(id="user-123", email="admin@test.com")
        
        # Injected identity header is sent automatically
        resp = await self.client.get("/api/billing")
        self.assert_status(resp, 200)`}</CodeBlock>

        <h3 className={h3Class}>3. MailTestMixin</h3>
        <p className={pClass}>
          Captures outgoing emails sent via the mail subsystem, placing them in an outbox array instead of triggering SMTP:
        </p>
        <ul className={listClass}>
          <li className={itemClass}><strong>self.mail_outbox:</strong> Read-only list containing all sent <code className="text-aquilia-500">CapturedMail</code> objects.</li>
          <li className={itemClass}><strong>self.latest_mail:</strong> Returns the most recently sent <code className="text-aquilia-500">CapturedMail</code> object.</li>
          <li className={itemClass}><strong>self.assert_mail_count(outbox, expected):</strong> Asserts exact number of sent messages.</li>
          <li className={itemClass}><strong>self.assert_mail_to(outbox, address):</strong> Asserts email was sent to address.</li>
        </ul>
      </section>

      <NextSteps />
    </div>
  )
}