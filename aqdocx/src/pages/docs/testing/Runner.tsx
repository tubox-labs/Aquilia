import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Play, Compass, ShieldAlert, Cpu } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function TestingRunner() {
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
          <Play className="w-4 h-4" />
          Testing / Test Runner
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            aq test — Test Runner
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500 font-mono font-bold">aq test</code> CLI command is Aquilia's built-in test runner. It wraps pytest, automatically sets test environments, discovers workspace-wide test structures, and executes specs with optimized asyncio profiles.
        </p>
      </div>

      {/* Overview & Architecture */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Cpu className="w-5 h-5 text-aquilia-400" />
          Runner Architecture &amp; Lifecycle
        </h2>
        <p className={pClass}>
          Executing tests in a manifest-driven architecture requires configuring global configurations and mock files before loading modules. The test runner streamlines this by wrapping the standard pytest execution pipeline:
        </p>

        <div className="space-y-6 mt-8">
          {[
            {
              title: 'Environment Locking',
              desc: 'Before invoking pytest, the runner locks os.environ["AQUILIA_ENV"] = "test". This redirects database adapters to in-memory/test paths and ensures credentials point to test configurations.'
            },
            {
              title: 'Auto-discovery Pipeline',
              desc: 'Scans the directory structure for test folders statically, identifying top-level tests/ directories, modules/*/tests/ paths, and standalone modules/*/test_*.py files, running them together seamlessly.'
            },
            {
              title: 'pytest-asyncio Auto Mode',
              desc: 'Appends -o asyncio_mode=auto to pytest CLI arguments. This enables you to mark test methods as async def without manually appending @pytest.mark.asyncio decorators on every method.'
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

      {/* CLI Command Options */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Compass className="w-5 h-5 text-aquilia-400" />
          Test CLI Command Options
        </h2>
        <p className={pClass}>
          Below are the Click arguments and flags supported by the <code className="text-aquilia-500 font-mono font-bold">aq test</code> command:
        </p>

        <div className="overflow-x-auto py-2 mb-6">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-white/10 text-gray-500 dark:text-gray-400 text-left">
                <th className="px-4 py-3 font-semibold">Option / Argument</th>
                <th className="px-4 py-3 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5 text-gray-300' : 'divide-gray-150 text-gray-700'}`}>
              {[
                ['PATHS (positional)', 'Specify specific test files or directory paths. If omitted, the runner executes auto-discovery.'],
                ['-k, --pattern', 'Only run tests with names matching the expression pattern (equivalent to pytest -k).'],
                ['-m, --markers', 'Only run tests matching specific custom pytest markers (equivalent to pytest -m).'],
                ['--coverage', 'Enables code coverage metrics, printing a terminal summary upon test suite completion.'],
                ['--coverage-html', 'Generates an interactive HTML coverage report inside htmlcov/ directory.'],
                ['-x, --failfast', 'Stop the test execution pipeline on the first failing assertion.'],
                ['-v, --verbose', 'Passes verbosity parameters to pytest (equivalent to pytest -v).']
              ].map(([opt, desc], i) => (
                <tr key={i} className="hover:bg-aquilia-500/5 transition-colors">
                  <td className="px-4 py-2 font-mono text-xs text-aquilia-500 font-semibold">{opt}</td>
                  <td className="px-4 py-2 text-xs">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <CodeBlock
          code={`# Run the entire discovered test suite
aq test

# Run tests in a specific module only
aq test modules/billing/tests/

# Filter execution to test names matching "login"
aq test -k "login"

# Run tests with coverage collection and HTML report output
aq test --coverage --coverage-html

# Stop immediately on the first assertion failure
aq test -x`}
          language="bash"
          filename="Terminal"
          highlightLines={[2, 5, 8, 11, 14]}
        />
      </section>

      {/* Writing Pytest Tests */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <ShieldAlert className="w-5 h-5 text-aquilia-400" />
          Writing Pytest-native Tests
        </h2>
        <p className={pClass}>
          While unittest is supported natively via <DocTerm id="testing.aquilia_test_case">AquiliaTestCase</DocTerm>, you can write native pytest functions and utilize fixtures:
        </p>

        <CodeBlock
          code={`import pytest
from aquilia.testing import TestClient
from myapp.manifests import api_manifest

@pytest.fixture
def test_app():
    # Setup your workspace application test environment
    from aquilia.server import AquiliaServer
    return AquiliaServer(manifests=[api_manifest])

@pytest.mark.asyncio
async def test_api_endpoint(test_app):
    async with TestClient(test_app) as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"`}
          language="python"
          filename="test_pytest.py"
          highlightLines={[5, 11, 12, 13, 14]}
        />
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/testing/mocks" className={`flex items-center gap-2 text-sm ${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`}>
          <ArrowLeft className="w-4 h-4" /> Mocks &amp; Fixtures
        </Link>
        <Link to="/docs/cli" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400">
          CLI Overview <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
