import { useTheme } from '../../../context/ThemeContext'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Terminal } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function CLIOverview() {
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
          <Terminal className="w-4 h-4" />
          Tooling / CLI
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            CLI — The <code className="text-aquilia-500 font-mono font-bold">aq</code> Command
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilate (<code className="text-aquilia-500 font-mono font-bold">aq</code>) is Aquilia's native command-line tool. It manages the entire application lifecycle—from workspace bootstrap and module generation to static validation, artifact compilation, database migration, and Docker/Kubernetes deployment configurations.
        </p>
      </div>

      {/* Philosophy */}
      <section className={sectionClass}>
        <h2 className={h2Class}>Philosophy</h2>
        <div className="space-y-6 mt-8">
          {[
            {
              title: 'Manifest-first',
              desc: 'Instead of scattering configurations across multiple files, the CLI uses workspace.py and module manifest.py files as the single source of truth.'
            },
            {
              title: 'Composition over centralization',
              desc: 'Modules are designed as self-contained, isolated units with declared imports and exports, promoting clean architectural separation.'
            },
            {
              title: 'Artifacts over runtime magic',
              desc: 'By compiling manifests into static .surp files, the CLI catches errors and conflicts before application boot, eliminating runtime dependency surprises.'
            },
            {
              title: 'CLI as primary UX',
              desc: 'Provides developers with standard CLI commands to inspect Dependency Injection graphs, trace routes, and configure environments without launching servers.'
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

      {/* Root Options */}
      <section className={sectionClass}>
        <h2 className={h2Class}>Global CLI Options</h2>
        <p className={pClass}>
          These flags can be specified on the root <code className="text-aquilia-500 font-mono font-bold">aq</code> command to control logging and output formatting:
        </p>
        <div className="overflow-x-auto py-2 mb-6">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-white/10 text-gray-500 dark:text-gray-400 text-left">
                <th className="px-4 py-3 font-semibold">Flag</th>
                <th className="px-4 py-3 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5 text-gray-300' : 'divide-gray-150 text-gray-700'}`}>
              {[
                ['--version', 'Displays the Aquilia framework version and current release name, then exits.'],
                ['--verbose, -v', 'Enables verbose output. Displays detailed logs, debug traces, and complete execution times.'],
                ['--quiet, -q', 'Minimal output. Suppresses CLI banners, ascii borders, and decorative elements.'],
                ['--debug', 'Enables debug mode, causing unhandled exceptions to crash with complete Python stack traces.'],
                ['--no-color', 'Disables colored terminal styles, rendering logs in standard raw text.']
              ].map(([flag, desc], i) => (
                <tr key={i} className="hover:bg-aquilia-500/5 transition-colors">
                  <td className="px-4 py-2 font-mono text-xs text-aquilia-500 font-semibold">{flag}</td>
                  <td className="px-4 py-2 text-xs">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Sections Grid */}
      <section className={sectionClass}>
        <h2 className={h2Class}>Documentation Sections</h2>
        <div className="divide-y divide-gray-150 dark:divide-white/5">
          {[
            {
              to: '/docs/cli/core',
              title: 'Core Commands',
              desc: 'Lifecycle management: init workspace, add module, validate manifests, compile artifacts, run dev server, serve production, and freeze snapshots.'
            },
            {
              to: '/docs/cli/database',
              title: 'Database & Migrations',
              desc: 'Create and run database migrations, inspect table schemas, dump DDL files, and run the async DB shell REPL.'
            },
            {
              to: '/docs/cli/inspection',
              title: 'Inspection & Discovery',
              desc: 'List compiled routes, inspect Dependency Injection graphs, discover untracked modules, and view fault domain scopes.'
            },
            {
              to: '/docs/cli/generators',
              title: 'Scaffolding & Scaffolding Generators',
              desc: 'Generate new controllers, models, and module templates automatically using pre-coded structures.'
            },
            {
              to: '/docs/cli/websockets',
              title: 'WebSocket Administration',
              desc: 'Inspect websocket controllers, broadcast realtime events, generate TypeScript client SDKs, and kick connection IDs.'
            },
            {
              to: '/docs/cli/deploy',
              title: 'Infrastructure & Deployment',
              desc: 'Generate optimized Dockerfiles, docker-compose configuration, Kubernetes manifests, reverse proxies, and Grafana monitoring stacks.'
            },
            {
              to: '/docs/cli/artifacts',
              title: 'Artifact Management',
              desc: 'Create, sign, inspect, and verify binary .surp bundle packages for production deployments.'
            },
            {
              to: '/docs/cli/subsystems',
              title: 'Subsystem Checks',
              desc: 'Verify cache, mail, and i18n configurations, test client adapters, and run translations extraction.'
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
        <Link to="/docs/admin-panel" className={`flex items-center gap-2 text-sm ${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`}>
          <ArrowLeft className="w-4 h-4" /> Admin Setup
        </Link>
        <Link to="/docs/cli/core" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400">
          Core Commands <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}