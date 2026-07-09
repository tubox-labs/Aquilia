import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, FlaskConical, Settings, Plug, Layers } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function TestingOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const sectionClass = "mb-16 scroll-mt-24"
  const h2Class = `text-2xl font-bold mb-6 flex items-center gap-3 ${isDark ? 'text-white' : 'text-gray-900'}`
  const pClass = `mb-4 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`

  return (
    <div className="max-w-4xl mx-auto pb-20">
      {/* Header */}
      <div className="mb-12 border-b border-gray-200 dark:border-white/10 pb-8">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <FlaskConical className="w-4 h-4" />
          Tooling / Testing
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Testing Framework
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia provides a batteries-included testing framework designed to test async controllers, background jobs, DB integrations, and WebSocket endpoints. It features automated server lifecycle hooks, DI mocking containers, mock storage, and custom assertions.
        </p>
      </div>

      {/* Philosophy */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Settings className="w-5 h-5 text-aquilia-400" />
          Testing Architecture
        </h2>
        <p className={pClass}>
          Testing in Aquilia avoids slow network calls and side effects by leveraging in-process ASGI loops. It connects your tests directly to the dependency container, permitting run-time provider swapping:
        </p>
        <div className="space-y-6 mt-8">
          {[
            {
              title: 'In-Process ASGI Pipeline',
              desc: 'Testing does not run TCP socket loops. The TestClient formats ASGI scope dictionary and triggers the server application directly, providing high-fidelity responses in milliseconds.'
            },
            {
              title: 'Tethered Dependency Injection',
              desc: 'Test case classes share container instances, allowing you to substitute mock repositories, email providers, or cache backends directly through context managers.'
            },
            {
              title: 'Isolated Transactions',
              desc: 'For database integration tests, Aquilia wraps each test in a database transaction block and automatically rolls it back on teardown, avoiding database leakage.'
            }
          ].map((item, i) => (
            <div key={i} className="flex items-start gap-4">
              <div className="w-1.5 h-1.5 rounded-full bg-aquilia-500 mt-2 flex-shrink-0" />
              <div>
                <h3 className={`font-bold text-sm mb-1 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>{item.title}</h3>
                <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Quick Start example */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Layers className="w-5 h-5 text-aquilia-400" />
          Writing Your First Test
        </h2>
        <p className={pClass}>
          Subclass <DocTerm id="testing.aquilia_test_case">AquiliaTestCase</DocTerm> to write an integration test. The server automatically starts up before the test runs and self-terminates on completion:
        </p>
        <CodeBlock language="python" filename="test_api.py" highlightLines={[6, 11, 16, 22]}>{`from aquilia.testing import AquiliaTestCase
from myapp.manifests import users_manifest

class TestUserAPI(AquiliaTestCase):
    # Specify the manifests to load into the test server
    manifests = [users_manifest]
    
    # Overwrite configuration fields
    settings = {
        "debug": True,
        "database": {"url": "sqlite:///:memory:"}
    }

    async def test_create_user(self):
        # Trigger an HTTP post
        response = await self.client.post("/api/users", json={
            "username": "testguy",
            "email": "test@example.com"
        })
        
        # Use built-in assertions
        self.assert_status(response, 201)
        self.assert_json_path(response, "username", "testguy")`}</CodeBlock>
      </section>

      {/* Directory Sections */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Plug className="w-5 h-5 text-aquilia-400" />
          Framework Reference
        </h2>
        <div className="divide-y divide-gray-150 dark:divide-white/5">
          {[
            {
              to: '/docs/testing/client',
              title: 'TestClient & WebSockets',
              desc: 'Details on GET, POST, PUT, DELETE requests, multipart file uploads, cookie jar tracking, and WebSocketTestClient assertions.'
            },
            {
              to: '/docs/testing/cases',
              title: 'Test Case Classes',
              desc: 'Learn about SimpleTestCase, AquiliaTestCase, TransactionTestCase, and LiveServerTestCase with their setup toggles and DI container hooks.'
            },
            {
              to: '/docs/testing/mocks',
              title: 'Mocks, Spies & Mixins',
              desc: 'Stub out dependencies with override_provider() and spy_provider(), intercept exceptions with MockFaultEngine, and assert on cache, auth, and mail mixins.'
            },
            {
              to: '/docs/testing/runner',
              title: 'Test Runner (aq test)',
              desc: 'Detailed options, auto-discovery targets, code coverage metrics, and parallel worker configurations.'
            }
          ].map((sec, i) => (
            <Link key={i} to={sec.to} className="group block py-5 first:pt-0 last:pb-0 transition-colors">
              <div className="flex items-center gap-2 mb-1">
                <span className={`font-mono font-bold text-lg group-hover:text-aquilia-500 transition-colors ${isDark ? 'text-gray-100' : 'text-gray-900'}`}>{sec.title}</span>
                <span className="text-gray-400 group-hover:translate-x-1 transition-transform duration-200">→</span>
              </div>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>{sec.desc}</p>
            </Link>
          ))}
        </div>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/cli" className={`flex items-center gap-2 text-sm ${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`}>
          <ArrowLeft className="w-4 h-4" /> CLI
        </Link>
        <Link to="/docs/controllers/openapi" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400">
          OpenAPI <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}