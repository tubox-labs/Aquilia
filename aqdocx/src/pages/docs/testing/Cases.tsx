import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { NextSteps } from '../../../components/NextSteps'
import { FlaskConical, Cpu, Layers } from 'lucide-react'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function TestingCases() {
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
          Testing / Test Cases
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Test Case Classes
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia features a set of test case subclasses tailored for various degrees of infrastructure dependency. These base classes automate uvicorn starting/stopping, manage database transaction rollbacks, and expose testing properties.
        </p>
      </div>

      {/* Class Hierarchy */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Layers className="w-5 h-5 text-aquilia-400" />
          Test Case Hierarchy
        </h2>
        <p className={pClass}>
          Choose the appropriate test class depending on your test scope to maximize execution speed and correctness:
        </p>
        <div className="space-y-8 mt-6">
          {[
            {
              name: 'SimpleTestCase',
              termId: 'testing.simple_test_case',
              setup: 'No environment setup',
              desc: 'Pure unit testing class. Inherits from unittest.TestCase and mixes in AquiliaAssertions. No server startup, DI container resolution, or database transactions. Perfect for utilities, helper methods, or algorithmic testing.'
            },
            {
              name: 'AquiliaTestCase',
              termId: 'testing.aquilia_test_case',
              setup: 'In-process server + DI container',
              desc: 'Standard integration testing class. Automatically provisions a TestServer instance using your modules/configs before each test, launching the ASGI app and binding a TestClient. Ideal for controller routing, middlewares, and business flow assertions.'
            },
            {
              name: 'TransactionTestCase',
              termId: 'testing.transaction_test_case',
              setup: 'In-process server + DB transaction rollback',
              desc: 'Extends AquiliaTestCase to automatically wrap each test method in an active database transaction block. On teardown, the transaction is rolled back, preventing records from persisting or contaminating neighboring tests.'
            },
            {
              name: 'LiveServerTestCase',
              termId: 'testing.live_server_test_case',
              setup: 'Real HTTP socket loops',
              desc: 'Launches a real ASGI server in a background thread or event loop task on a random localhost port (accessible via self.live_server_url). Use for genuine TCP sockets (e.g. testing with external HTTP clients or browser frameworks like Playwright).'
            }
          ].map((tc, i) => (
            <div key={i} className="flex items-start gap-4">
              <div className="w-1.5 h-1.5 rounded-full bg-aquilia-500 mt-2 flex-shrink-0" />
              <div>
                <div className="flex items-center gap-3 mb-1 flex-wrap">
                  <h3 className="font-mono font-bold text-base"><DocTerm id={tc.termId}>{tc.name}</DocTerm></h3>
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-aquilia-500/10 text-aquilia-400 border border-aquilia-500/20">{tc.setup}</span>
                </div>
                <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{tc.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Class Configuration Attributes */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Cpu className="w-5 h-5 text-aquilia-400" />
          Lifecycle & Configurations
        </h2>
        <p className={pClass}>
          For <DocTerm id="testing.aquilia_test_case">AquiliaTestCase</DocTerm> and its subclasses, you configure dependencies and subsystem integrations using class-level attributes:
        </p>

        <div className="overflow-x-auto py-2 mb-6">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-white/10 text-gray-500 dark:text-gray-400 text-left">
                <th className="px-4 py-3 font-semibold">Attribute</th>
                <th className="px-4 py-3 font-semibold">Type</th>
                <th className="px-4 py-3 font-semibold">Purpose</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5 text-gray-300' : 'divide-gray-150 text-gray-700'}`}>
              {[
                ['manifests', 'list[AppManifest]', 'List of app manifests to load. Determines route bindings and dependency injections.'],
                ['settings', 'dict[str, Any]', 'Configuration dictionary overrides injected during container startup.'],
                ['enable_cache', 'bool (False)', 'Boot the Cache subsystem for this test case.'],
                ['enable_sessions', 'bool (False)', 'Enable transport and storage layers for typed session objects.'],
                ['enable_auth', 'bool (False)', 'Setup credentials, guards, clearance maps, and authentication policies.'],
                ['enable_mail', 'bool (False)', 'Intercept sent mail envelopes in a mock outbox collection.'],
                ['enable_templates', 'bool (False)', 'Setup Jinja environment loader paths for HTML output rendering.']
              ].map(([attr, type, purpose], i) => (
                <tr key={i} className="hover:bg-aquilia-500/5 transition-colors">
                  <td className="px-4 py-2 font-mono text-xs text-aquilia-500 font-semibold">{attr}</td>
                  <td className="px-4 py-2 font-mono text-xs text-gray-500 dark:text-gray-400">{type}</td>
                  <td className="px-4 py-2 text-xs">{purpose}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <CodeBlock language="python" filename="test_complex_setup.py" highlightLines={[5, 6, 7, 8, 9, 10, 11]}>{`from aquilia.testing import AquiliaTestCase
from myapp.manifests import api_manifest

class TestBillingFlows(AquiliaTestCase):
    manifests = [api_manifest]
    enable_cache = True
    enable_auth = True
    settings = {
        "billing": {"gateway": "mock-stripe"},
        "cache": {"backend": "memory"}
    }

    async def test_checkout(self):
        # Cache and Auth systems are automatically active here
        ...`}</CodeBlock>
      </section>

      {/* Properties & Helpers */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Layers className="w-5 h-5 text-aquilia-400" />
          Test Properties & Helpers
        </h2>
        <p className={pClass}>
          When running <DocTerm id="testing.aquilia_test_case">AquiliaTestCase</DocTerm>, several properties and helper methods are exposed on the class instance:
        </p>

        <h3 className={h3Class}>Instance Properties</h3>
        <ul className={listClass}>
          <li className={itemClass}>
            <strong>di_container:</strong> Direct access to the active <DocTerm id="di.container">Container</DocTerm> instance of the test server, letting you manually resolve or check dependencies.
          </li>
          <li className={itemClass}>
            <strong>fault_engine:</strong> Reference to the running <DocTerm id="faults.engine">FaultEngine</DocTerm> (or MockFaultEngine).
          </li>
          <li className={itemClass}>
            <strong>config:</strong> The active config loader reference.
          </li>
          <li className={itemClass}>
            <strong>controller_router:</strong> The route table resolver, containing all registered HTTP paths.
          </li>
          <li className={itemClass}>
            <strong>cache_service:</strong> Exposes the running cache manager if <code className="text-aquilia-500">enable_cache=True</code>.
          </li>
        </ul>

        <h3 className={h3Class}>Utility Methods</h3>
        <ul className={listClass}>
          <li className={itemClass}>
            <strong>get_url(route_name, **params):</strong> Resolves a named controller route pattern back into an absolute URI path (e.g. <code className="text-aquilia-500">self.get_url("get_user", id="123")</code> yields <code className="text-aquilia-500">"/users/123"</code>).
          </li>
          <li className={itemClass}>
            <strong>login(username, password):</strong> Convenience helper that issues a POST to <code className="text-aquilia-500">/auth/login</code> containing credentials, returning the HTTP response.
          </li>
        </ul>
      </section>

      <NextSteps />
    </div>
  )
}