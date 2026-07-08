import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Cpu } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function DIAdvanced() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      {/* Title Header */}
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Cpu className="w-4 h-4" />
          Dependency Injection / Advanced
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          Advanced DI &amp; Testing Overrides
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          Customize the resolution graph dynamically, swap providers at runtime during tests, and configure complex factory pipelines.
        </p>
      </div>

      {/* Advanced Decorators Reference */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Decorators Cheat Sheet</h2>
        <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl mb-6">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="py-4 px-6 text-left font-semibold text-aquilia-500">Decorator</th>
                <th className="py-4 px-6 text-left font-semibold">Scope</th>
                <th className="py-4 px-6 text-left font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {[
                { d: '@service', s: 'singleton', desc: 'Class-based provider, instantiated once and cached.' },
                { d: '@service(scope="request")', s: 'request', desc: 'Per-request instance, cleared on request teardown.' },
                { d: '@service(scope="transient")', s: 'transient', desc: 'New instance generated on every resolution call.' },
                { d: '@factory', s: 'configurable', desc: 'Decorator mapping functions as service providers.' },
                { d: '@provides(Token)', s: 'n/a', desc: 'Defines a custom provider function inside another service.' },
                { d: '@auto_inject', s: 'n/a', desc: 'Scan annotations and auto-resolve constructor arguments.' },
              ].map((row, i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                  <td className="py-3.5 px-6 font-mono text-aquilia-500 text-xs">{row.d}</td>
                  <td className="py-3.5 px-6 font-mono text-xs text-yellow-500">{row.s}</td>
                  <td className={`py-3.5 px-6 text-xs ${subtleText}`}>{row.desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Test Overrides */}
      <section className="mb-16 border-l-2 border-aquilia-500/30 pl-6">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>TestRegistry Overrides</h2>
        <p className={`mb-4 ${subtleText}`}>
          Swap components with mock implementations during unit or integration testing:
        </p>
        <CodeBlock language="python" filename="test_registry.py">{`from aquilia.di import TestRegistry, MockProvider

# Create a test registry delegating to production setup
test_reg = TestRegistry(base=production_registry)

# Override with custom value or MockProvider
test_reg.override(EmailService, MockProvider(
    send=AsyncMock(return_value=True)
))

# Override database connection pools with mock mocks
test_reg.override(DatabasePool, value=FakeDbPool())`}</CodeBlock>
      </section>

      {/* Pytest Fixtures */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Pytest Fixtures</h2>
        <p className={`mb-4 ${subtleText}`}>
          Use the built-in context overrides helper to automatically mock out components during test execution:
        </p>
        <CodeBlock language="python" filename="test_controller.py">{`import pytest
from aquilia.di.testing import override_container

@pytest.mark.asyncio
async def test_user_creation(client, app_container):
    # Override UserService inside the app DI container temporarily:
    mock_service = MagicMock()
    
    with override_container(app_container, {UserService: mock_service}):
        response = await client.post("/users", json={"name": "Alice"})
        assert response.status_code == 201
        mock_service.create.assert_called_once()`}</CodeBlock>
      </section>

      {/* Nav */}
      <div className="flex justify-between items-center mt-16 pt-8 border-t border-white/5">
        <Link to="/docs/di/scopes" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition">
          <ArrowLeft className="w-4 h-4" /> Scopes
        </Link>
        <Link to="/docs/models" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition">
          Models <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    
      <NextSteps />
    </div>
  )
}