import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Terminal, Stethoscope, Mail, Database as CacheIcon, TestTube, Search, BarChart, ArrowRight } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function CLISubsystemCommands() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const sectionClass = 'mb-16 scroll-mt-24'
  const h2Class = `text-2xl font-bold mb-6 flex items-center gap-3 ${isDark ? 'text-white' : 'text-gray-900'}`
  const h3Class = `text-lg font-semibold mt-8 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`
  const pClass = `mb-4 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`
  const codeClass = 'text-xs font-mono bg-black/5 dark:bg-white/10 px-1.5 py-0.5 rounded text-aquilia-600 dark:text-aquilia-400'
  const noteClass = `p-4 rounded-xl border-l-4 ${isDark ? 'bg-blue-500/5 border-blue-500/50 text-gray-300' : 'bg-blue-50 border-blue-500 text-gray-700'}`

  const Table = ({ children }: { children: React.ReactNode }) => (
    <div className={`overflow-hidden border rounded-lg mb-6 ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
      <table className="w-full text-sm text-left">
        <thead className={`text-xs uppercase ${isDark ? 'bg-white/5 text-gray-400' : 'bg-gray-50 text-gray-500'}`}>
          <tr>
            <th className="px-4 py-3 font-medium">Option</th>
            <th className="px-4 py-3 font-medium">Description</th>
            <th className="px-4 py-3 font-medium w-32">Default</th>
          </tr>
        </thead>
        <tbody className={`divide-y ${isDark ? 'divide-white/10' : 'divide-gray-200'}`}>
          {children}
        </tbody>
      </table>
    </div>
  )

  const Row = ({ opt, desc, def: defaultVal }: { opt: string; desc: string; def?: string }) => (
    <tr className={isDark ? 'hover:bg-white/5' : 'hover:bg-gray-50'}>
      <td className="px-4 py-3 font-mono text-aquilia-500">{opt}</td>
      <td className={`px-4 py-3 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>{desc}</td>
      <td className={`px-4 py-3 font-mono text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>{defaultVal || '-'}</td>
    </tr>
  )

  return (
    <div className="max-w-4xl mx-auto pb-20">
      {/* Header */}
      <div className="mb-12 border-b border-gray-200 dark:border-white/10 pb-8">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Stethoscope className="w-4 h-4" />
          CLI / Subsystem Commands
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Subsystem Commands
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia CLI provides dedicated command groups for diagnosing, inspecting, and managing individual subsystems — Doctor, Cache, Mail, Test, Discovery, and Analytics.
        </p>
      </div>

      {/* ═══════════════ DOCTOR ═══════════════ */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Stethoscope className="w-6 h-6 text-green-500" />
          aq doctor
        </h2>
        <p className={pClass}>
          Performs comprehensive health checks across every layer of the Manifest-First Architecture:
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-6">
          {[
            { phase: 'Phase 1 — Environment', desc: 'Python version, Aquilia installation, key dependencies' },
            { phase: 'Phase 2 — Workspace', desc: 'File presence, directory structure, config files' },
            { phase: 'Phase 3 — Manifests', desc: 'Load/validate each AppManifest, field completeness' },
            { phase: 'Phase 4 — Pipeline', desc: 'Aquilary validation, dependency graph, fingerprint' },
            { phase: 'Phase 5 — Integrations', desc: 'DB connectivity, cache, sessions, mail, auth, templates' },
            { phase: 'Phase 6 — Deployment', desc: 'Docker files, compose, Kubernetes manifests' },
          ].map((item, i) => (
            <div key={i} className={`flex items-start gap-2 p-3 rounded-lg ${isDark ? 'bg-white/5' : 'bg-gray-50'}`}>
              <ArrowRight className="w-3 h-3 text-green-500 mt-1 flex-shrink-0" />
              <div>
                <span className={`font-semibold text-sm ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>{item.phase}</span>
                <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
        <CodeBlock language="bash" filename="Terminal">{`# Run full diagnostics
aq doctor

# Verbose diagnostics
aq doctor -v`}</CodeBlock>
        <h3 className={h3Class}>Checked Dependencies</h3>
        <p className={pClass}>Doctor validates both required and optional dependencies:</p>
        <ul className={`list-disc pl-6 mb-4 space-y-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <li><strong>Required:</strong> Python ≥ 3.10, Aquilia (manifest, aquilary, config, server, di, faults, controller, effects, blueprints)</li>
          <li><strong>Runtime:</strong> uvicorn (dev server)</li>
          <li><strong>Optional:</strong> orjson, pyyaml, click, watchfiles</li>
        </ul>
      </section>

      {/* ═══════════════ CACHE ═══════════════ */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <CacheIcon className="w-6 h-6 text-blue-500" />
          aq cache
        </h2>
        <p className={pClass}>
          AquilaCache CLI — check, inspect, clear, and view cache statistics without starting the server.
        </p>

        {/* cache check */}
        <h3 className={h3Class}>aq cache check</h3>
        <p className={pClass}>
          Validates cache configuration and tests backend connectivity. For Redis backends, performs a PING test and reports memory usage.
        </p>
        <CodeBlock language="bash" filename="Terminal">{`aq cache check`}</CodeBlock>
        <p className={pClass}>Reports: enabled status, backend type, default TTL, max size, eviction policy, serializer, key prefix, Redis connection health, composite L1/L2 config, and middleware settings.</p>

        {/* cache inspect */}
        <h3 className={h3Class}>aq cache inspect</h3>
        <p className={pClass}>
          Display the current cache configuration as JSON. Loads from <code className={codeClass}>workspace.py</code> or config files.
        </p>
        <CodeBlock language="bash" filename="Terminal">{`aq cache inspect`}</CodeBlock>

        {/* cache stats */}
        <h3 className={h3Class}>aq cache stats</h3>
        <p className={pClass}>
          Display cache statistics from the trace diagnostics file. Requires a running server that has generated <code className={codeClass}>.aquilia/diagnostics.json</code>.
        </p>
        <CodeBlock language="bash" filename="Terminal">{`aq cache stats`}</CodeBlock>

        {/* cache clear */}
        <h3 className={h3Class}>aq cache clear</h3>
        <p className={pClass}>
          Clear all cache entries or only a specific namespace. Creates a temporary CacheService from config to perform the clear operation.
        </p>
        <Table>
          <Row opt="--namespace, -n" desc="Clear only entries in this namespace" def="all" />
        </Table>
        <CodeBlock language="bash" filename="Terminal">{`# Clear all cache entries
aq cache clear

# Clear specific namespace
aq cache clear --namespace http`}</CodeBlock>
      </section>

      {/* ═══════════════ MAIL ═══════════════ */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Mail className="w-6 h-6 text-orange-500" />
          aq mail
        </h2>
        <p className={pClass}>
          AquilaMail CLI — test, inspect, and validate mail configuration without starting the server.
        </p>

        {/* mail check */}
        <h3 className={h3Class}>aq mail check</h3>
        <p className={pClass}>
          Validate mail configuration and report issues. Checks enabled status, default sender, subject prefix, providers, console backend, security settings (DKIM, TLS, PII redaction), and common misconfigurations.
        </p>
        <CodeBlock language="bash" filename="Terminal">{`aq mail check`}</CodeBlock>

        {/* mail send-test */}
        <h3 className={h3Class}>aq mail send-test</h3>
        <p className={pClass}>
          Send a test email to verify provider configuration. Creates a temporary MailService and sends through the configured provider chain.
        </p>
        <Table>
          <Row opt="TO" desc="Recipient email address (positional argument)" def="-" />
          <Row opt="--subject" desc="Email subject line" def="Aquilia Mail Test" />
          <Row opt="--body" desc="Email body text" def="auto-generated" />
        </Table>
        <CodeBlock language="bash" filename="Terminal">{`# Send test email
aq mail send-test user@example.com

# With custom subject
aq mail send-test user@example.com --subject="Hello from Aquilia"`}</CodeBlock>

        {/* mail inspect */}
        <h3 className={h3Class}>aq mail inspect</h3>
        <p className={pClass}>
          Display the current mail configuration as JSON. Useful for debugging provider setup.
        </p>
        <CodeBlock language="bash" filename="Terminal">{`aq mail inspect`}</CodeBlock>
      </section>

      {/* ═══════════════ TEST ═══════════════ */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <TestTube className="w-6 h-6 text-purple-500" />
          aq test
        </h2>
        <p className={pClass}>
          Run the test suite with Aquilia-aware defaults. Automatically sets <code className={codeClass}>AQUILIA_ENV=test</code>, discovers test directories, and configures pytest-asyncio auto mode.
        </p>
        <Table>
          <Row opt="PATHS" desc="Specific test file/directory paths (positional, multiple)" def="auto-discover" />
          <Row opt="-k, --pattern" desc="Only run tests matching this name pattern" def="-" />
          <Row opt="-m, --markers" desc="Only run tests matching these markers" def="-" />
          <Row opt="--coverage" desc="Collect code coverage data" def="false" />
          <Row opt="--coverage-html" desc="Generate HTML coverage report" def="false" />
          <Row opt="--failfast, -x" desc="Stop on first failure" def="false" />
        </Table>
        <CodeBlock language="bash" filename="Terminal">{`# Run all tests
aq test

# Run specific test file
aq test tests/test_users.py

# Pattern matching
aq test -k "test_login"

# With coverage
aq test --coverage

# HTML coverage report
aq test --coverage-html

# Stop on first failure with verbose output
aq test --failfast -v`}</CodeBlock>
        <h3 className={h3Class}>Auto-Discovery</h3>
        <p className={pClass}>
          When no paths are specified, <code className={codeClass}>aq test</code> auto-discovers tests in:
        </p>
        <ul className={`list-disc pl-6 mb-4 space-y-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <li><code className={codeClass}>tests/</code> — top-level test directory</li>
          <li><code className={codeClass}>modules/*/tests/</code> — per-module test directories</li>
          <li><code className={codeClass}>modules/*/test_*.py</code> — standalone module test files</li>
        </ul>
      </section>

      {/* ═══════════════ DISCOVER ═══════════════ */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Search className="w-6 h-6 text-cyan-500" />
          aq discover
        </h2>
        <p className={pClass}>
          Inspect auto-discovered modules and components using the AST-based <code className={codeClass}>AutoDiscoveryEngine</code>. Shows module metadata, dependencies, controllers, services, middleware, guards, pipes, and interceptors. Optionally syncs discovered components into manifest.py files.
        </p>
        <Table>
          <Row opt="--path" desc="Workspace path to scan" def="cwd" />
          <Row opt="--sync" desc="Auto-sync discovered components into manifest.py files" def="false" />
          <Row opt="--dry-run" desc="Preview sync changes without writing (use with --sync)" def="false" />
        </Table>
        <CodeBlock language="bash" filename="Terminal">{`# Inspect discovered modules
aq discover

# Verbose output with detailed module info
aq discover -v

# Auto-sync manifests
aq discover --sync

# Preview sync changes
aq discover --sync --dry-run`}</CodeBlock>
        <h3 className={h3Class}>Discovery Pipeline</h3>
        <p className={pClass}>
          The discovery system uses a two-stage pipeline:
        </p>
        <ul className={`list-disc pl-6 mb-4 space-y-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <li><strong>AST-based AutoDiscoveryEngine</strong> — primary scanner for all component kinds (controllers, services, models, guards, pipes, interceptors) using Python AST parsing</li>
          <li><strong>EnhancedDiscovery</strong> — fallback scanner for controllers, services, and sockets using runtime introspection</li>
        </ul>
        <p className={pClass}>
          The <code className={codeClass}>--sync</code> flag compares discovered components with manifest declarations and automatically updates manifest.py to include any new, undeclared components.
        </p>
      </section>

      {/* ═══════════════ ANALYTICS ═══════════════ */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <BarChart className="w-6 h-6 text-yellow-500" />
          aq analytics
        </h2>
        <p className={pClass}>
          Run deep discovery analytics and generate a comprehensive health report with metrics, dependency analysis, complexity scoring, and optimization recommendations.
        </p>
        <Table>
          <Row opt="--path" desc="Workspace path to analyze" def="cwd" />
        </Table>
        <CodeBlock language="bash" filename="Terminal">{`# Run analytics
aq analytics

# Analyze custom workspace path
aq analytics --path /path/to/workspace`}</CodeBlock>
        <h3 className={h3Class}>Report Sections</h3>
        <ul className={`list-disc pl-6 mb-4 space-y-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <li><strong>Summary</strong> — total modules, with services/controllers/middleware/dependencies/tags</li>
          <li><strong>Health Metrics</strong> — health score (0–100), validation errors, warnings</li>
          <li><strong>Dependencies</strong> — max depth, cyclic detection, load order</li>
          <li><strong>Per-Module</strong> — version, maturity (alpha/beta/stable/production), complexity, components</li>
          <li><strong>Recommendations</strong> — actionable suggestions for improving module quality</li>
        </ul>
      </section>

      {/* ═══════════════ MIGRATE (LEGACY) ═══════════════ */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Terminal className="w-6 h-6 text-red-500" />
          aq migrate legacy
        </h2>
        <p className={pClass}>
          Migrate from a Django-style project layout to the Aquilia workspace structure. Scans for directories with <code className={codeClass}>views.py</code> or <code className={codeClass}>urls.py</code> and converts them to Aquilia modules.
        </p>
        <Table>
          <Row opt="--dry-run" desc="Preview migration changes without writing files" def="false" />
        </Table>
        <CodeBlock language="bash" filename="Terminal">{`# Preview migration
aq migrate legacy --dry-run

# Execute migration
aq migrate legacy`}</CodeBlock>
        <h3 className={h3Class}>What Gets Generated</h3>
        <ul className={`list-disc pl-6 mb-4 space-y-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <li><code className={codeClass}>modules/&lt;app&gt;/manifest.py</code> — AppManifest with module metadata</li>
          <li><code className={codeClass}>modules/&lt;app&gt;/__init__.py</code> — module package init</li>
          <li><code className={codeClass}>modules/&lt;app&gt;/controllers.py</code> — from views.py stub</li>
          <li><code className={codeClass}>modules/&lt;app&gt;/services.py</code> — from models.py stub</li>
          <li><code className={codeClass}>modules/&lt;app&gt;/faults.py</code> — fault definitions</li>
          <li><code className={codeClass}>workspace.py</code> — workspace config with all discovered modules</li>
        </ul>
      </section>

      <NextSteps
        items={[
          { text: 'Core Commands', link: '/docs/cli/core' },
          { text: 'Database Commands', link: '/docs/cli/database' },
          { text: 'Inspection Commands', link: '/docs/cli/inspection' },
          { text: 'Cache Docs', link: '/docs/cache' },
          { text: 'Mail Docs', link: '/docs/mail' },
        ]}
      />
    </div>
  )
}
