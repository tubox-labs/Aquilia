import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { NextSteps } from '../../../components/NextSteps'
import { Search } from 'lucide-react'

export function CLIInspectionCommands() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const sectionClass = "mb-16 scroll-mt-24"
  const h2Class = `text-2xl font-bold mb-6 flex items-center gap-3 ${isDark ? 'text-white' : 'text-gray-900'}`
  const h3Class = `text-lg font-semibold mt-8 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`
  const pClass = `mb-4 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`

  return (
    <div className="max-w-4xl mx-auto pb-20">
      {/* Header */}
      <div className="mb-12 border-b border-gray-200 dark:border-white/10 pb-8">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Search className="w-4 h-4" />
          CLI / Inspection
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Inspection &amp; Discovery
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500 font-mono font-bold">aq inspect</code> and <code className="text-aquilia-500 font-mono font-bold">aq discover</code> command suites inspect routing, DI dependencies, configuration values, and module loading without spinning up a live server.
        </p>
      </div>

      {/* aq inspect routes */}
      <section id="inspect-routes" className={sectionClass}>
        <h2 className={h2Class}>aq inspect routes</h2>
        <p className={pClass}>
          Displays all routes registered in the application, showing HTTP verbs, URL templates, and target controller methods.
        </p>
        <CodeBlock language="bash" filename="Terminal">aq inspect routes</CodeBlock>
      </section>

      {/* aq inspect di */}
      <section id="inspect-di" className={sectionClass}>
        <h2 className={h2Class}>aq inspect di</h2>
        <p className={pClass}>
          Prints the compiled Dependency Injection (DI) registry tree, showcasing registered classes, factory tokens, scopes, and active provider locations.
        </p>
        <CodeBlock language="bash" filename="Terminal">aq inspect di</CodeBlock>
      </section>

      {/* aq inspect modules */}
      <section id="inspect-modules" className={sectionClass}>
        <h2 className={h2Class}>aq inspect modules</h2>
        <p className={pClass}>
          Lists loaded modules alongside active dependencies, import permissions, exports, and manifest configurations.
        </p>
        <CodeBlock language="bash" filename="Terminal">aq inspect modules</CodeBlock>
      </section>

      {/* aq inspect faults */}
      <section id="inspect-faults" className={sectionClass}>
        <h2 className={h2Class}>aq inspect faults</h2>
        <p className={pClass}>
          Dumps all declared fault categories and domains, detailing security overrides and default HTTP status codes.
        </p>
        <CodeBlock language="bash" filename="Terminal">aq inspect faults</CodeBlock>
      </section>

      {/* aq inspect config */}
      <section id="inspect-config" className={sectionClass}>
        <h2 className={h2Class}>aq inspect config</h2>
        <p className={pClass}>
          Renders the fully resolved application configuration, merging values from <code className="text-aquilia-500 font-mono">workspace.py</code>, active environment variables, and dot-env files.
        </p>
        <CodeBlock language="bash" filename="Terminal">aq inspect config</CodeBlock>
      </section>

      {/* aq discover */}
      <section id="discover" className={sectionClass}>
        <h2 className={h2Class}>aq discover</h2>
        <p className={pClass}>
          Scans the workspace modules directory for new controllers, models, or tasks that are not yet registered in manifests.
        </p>
        <CodeBlock language="bash" filename="Terminal">{`# List all untracked modules and handlers
aq discover

# Sync discovered components into active manifests automatically
aq discover --sync

# Sync dry-run to preview changes
aq discover --sync --dry-run`}</CodeBlock>

        <h3 className={h3Class}>Options</h3>
        <div className="overflow-x-auto py-2 mb-6">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-white/10 text-gray-500 dark:text-gray-400 text-left">
                <th className="px-4 py-3 font-semibold">Option</th>
                <th className="px-4 py-3 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5 text-gray-300' : 'divide-gray-150 text-gray-700'}`}>
              {[
                ['--path', 'Custom directories scan path.'],
                ['--sync', 'Auto-write discovered components directly into manifest.py.'],
                ['--dry-run', 'Preview changes without modifying manifest files.'],
                ['--json', 'Outputs discovered items as a structured JSON object.']
              ].map(([opt, desc], i) => (
                <tr key={i} className="hover:bg-aquilia-500/5 transition-colors">
                  <td className="px-4 py-2 font-mono text-xs text-aquilia-500 font-semibold">{opt}</td>
                  <td className="px-4 py-2 text-xs">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* aq analytics */}
      <section id="analytics" className={sectionClass}>
        <h2 className={h2Class}>aq analytics</h2>
        <p className={pClass}>
          Provides static discovery analysis metrics, listing circular dependencies, registration bottlenecks, and manifest health scores.
        </p>
        <CodeBlock language="bash" filename="Terminal">aq analytics</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}