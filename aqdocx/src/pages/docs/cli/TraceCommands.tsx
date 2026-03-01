import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Terminal, Eye } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function CLITraceCommands() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const sectionClass = 'mb-16 scroll-mt-24'
  const h2Class = `text-2xl font-bold mb-6 flex items-center gap-3 ${isDark ? 'text-white' : 'text-gray-900'}`
  const h3Class = `text-lg font-semibold mt-8 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`
  const pClass = `mb-4 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`
  const codeClass = 'text-xs font-mono bg-black/5 dark:bg-white/10 px-1.5 py-0.5 rounded text-aquilia-600 dark:text-aquilia-400'
  const noteClass = `p-4 rounded-xl border-l-4 ${isDark ? 'bg-yellow-500/5 border-yellow-500/50 text-gray-300' : 'bg-yellow-50 border-yellow-500 text-gray-700'}`

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
          <Eye className="w-4 h-4" />
          CLI / Trace Commands
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Trace Commands
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className={codeClass}>aq trace</code> command group manages the <code className={codeClass}>.aquilia/</code> trace directory — a runtime-generated diagnostic snapshot that captures manifest state, routes, DI graph, schema, configuration, and lifecycle journal events.
        </p>
      </div>

      {/* Overview */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Eye className="w-6 h-6 text-aquilia-500" />
          Sub-Commands
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {[
            { cmd: 'aq trace status', desc: 'Show .aquilia/ directory status — lock state, file list, health, boot info' },
            { cmd: 'aq trace inspect', desc: 'Inspect a specific trace section (manifest, routes, di, schema, config, diagnostics)' },
            { cmd: 'aq trace journal', desc: 'View lifecycle journal events — boot, shutdown, errors, phases' },
            { cmd: 'aq trace clean', desc: 'Delete all trace files from .aquilia/' },
            { cmd: 'aq trace diff', desc: 'Diff current trace against another trace directory' },
          ].map((item, i) => (
            <div key={i} className={boxClass}>
              <code className={`font-bold text-sm ${isDark ? 'text-aquilia-400' : 'text-aquilia-600'}`}>{item.cmd}</code>
              <p className={`text-xs mt-1 ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* trace status */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Terminal className="w-6 h-6 text-aquilia-500" />
          aq trace status
        </h2>
        <p className={pClass}>
          Show a comprehensive status summary of the <code className={codeClass}>.aquilia/</code> trace directory, including lock state, mode, app count, fingerprint, route/provider/model counts, boot timing, uptime, health, and active subsystems.
        </p>
        <Table>
          <Row opt="--dir, -d" desc="Workspace root directory" def="." />
          <Row opt="--json-output, -j" desc="Output as JSON" def="false" />
        </Table>
        <CodeBlock language="bash" filename="Terminal">{`# Show trace status
aq trace status

# JSON output
aq trace status --json`}</CodeBlock>

        <CodeBlock language="text" filename="Example Output">{`── .aquilia/ Trace Status ──────────────────
  Root             .aquilia/
  Locked           No
  Files            manifest.json, routes.json, di_graph.json, schema.json
  Mode             DEV
  Apps             3
  Fingerprint      a1b2c3d4e5f6...
  Routes           12
  Providers        8
  Models           5
  Events           42
  Last boot        2025-01-15 10:30:22 (145ms)
  Last stop        2025-01-15 11:45:33 (uptime 4511.2s)
  Health           ✓ Healthy
  Subsystems       cache, sessions, auth, mail`}</CodeBlock>
      </section>

      {/* trace inspect */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Terminal className="w-6 h-6 text-aquilia-500" />
          aq trace inspect
        </h2>
        <p className={pClass}>
          Inspect a specific section of the trace data. Outputs the raw JSON content for the selected section.
        </p>
        <Table>
          <Row opt="SECTION" desc="Section to inspect: manifest, routes, di, schema, config, diagnostics" def="-" />
          <Row opt="--dir, -d" desc="Workspace root directory" def="." />
        </Table>
        <CodeBlock language="bash" filename="Terminal">{`# Inspect manifest trace
aq trace inspect manifest

# Inspect route table
aq trace inspect routes

# Inspect DI graph
aq trace inspect di

# Inspect database schema
aq trace inspect schema

# Inspect resolved config
aq trace inspect config

# Inspect diagnostics
aq trace inspect diagnostics`}</CodeBlock>
        <h3 className={h3Class}>Available Sections</h3>
        <ul className={`list-disc pl-6 mb-4 space-y-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <li><strong>manifest</strong> — compiled manifest data: mode, app list, fingerprint</li>
          <li><strong>routes</strong> — full route table with methods, paths, handlers, middleware</li>
          <li><strong>di</strong> — dependency injection graph: providers, scopes, dependencies</li>
          <li><strong>schema</strong> — database schema snapshot: tables, columns, types</li>
          <li><strong>config</strong> — resolved configuration snapshot from all sources</li>
          <li><strong>diagnostics</strong> — subsystem health data (cache, sessions, auth, etc.)</li>
        </ul>
      </section>

      {/* trace journal */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Terminal className="w-6 h-6 text-aquilia-500" />
          aq trace journal
        </h2>
        <p className={pClass}>
          View lifecycle journal events recorded during server boot, shutdown, and operation. Events include timestamps, duration, and contextual metadata.
        </p>
        <Table>
          <Row opt="--dir, -d" desc="Workspace root directory" def="." />
          <Row opt="--tail, -n" desc="Show last N events" def="20" />
          <Row opt="--event, -e" desc="Filter by event type (boot, shutdown, error, warning, phase)" def="all" />
          <Row opt="--json-output, -j" desc="Output as JSON" def="false" />
        </Table>
        <CodeBlock language="bash" filename="Terminal">{`# Show last 20 journal events
aq trace journal

# Show last 5 events
aq trace journal --tail 5

# Filter by event type
aq trace journal --event boot
aq trace journal --event error

# JSON output
aq trace journal --event error --json`}</CodeBlock>

        <h3 className={h3Class}>Event Types</h3>
        <ul className={`list-disc pl-6 mb-4 space-y-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <li><span className="text-green-500 font-mono">boot</span> — server startup with app count, route count, mode, duration</li>
          <li><span className="text-yellow-500 font-mono">shutdown</span> — server shutdown with uptime</li>
          <li><span className="text-red-500 font-mono">error</span> — runtime errors with message</li>
          <li><span className="text-purple-500 font-mono">warning</span> — warnings during operation</li>
          <li><span className="text-blue-500 font-mono">phase</span> — lifecycle phase transitions (manifest loading, DI wiring, etc.)</li>
          <li><span className="font-mono">custom</span> — user-defined journal entries</li>
        </ul>
      </section>

      {/* trace clean */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Terminal className="w-6 h-6 text-aquilia-500" />
          aq trace clean
        </h2>
        <p className={pClass}>
          Delete all trace files from the <code className={codeClass}>.aquilia/</code> directory. By default, asks for confirmation and refuses if the server is currently running (trace is locked).
        </p>
        <Table>
          <Row opt="--dir, -d" desc="Workspace root directory" def="." />
          <Row opt="--force, -f" desc="Skip confirmation and allow cleaning locked traces" def="false" />
        </Table>
        <CodeBlock language="bash" filename="Terminal">{`# Clean trace (with confirmation)
aq trace clean

# Force clean (skip confirmation, ignore lock)
aq trace clean --force`}</CodeBlock>
        <div className={noteClass}>
          <strong>Caution:</strong> Cleaning the trace directory while the server is running may cause diagnostic data loss. Use <code className={codeClass}>--force</code> only when you're sure the server is not running.
        </div>
      </section>

      {/* trace diff */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Terminal className="w-6 h-6 text-aquilia-500" />
          aq trace diff
        </h2>
        <p className={pClass}>
          Compare the current trace against another trace file to see what changed between two server runs — added routes, removed routes, and modified routes.
        </p>
        <Table>
          <Row opt="OTHER" desc="Path to the other trace file (positional argument)" def="-" />
          <Row opt="--dir, -d" desc="Workspace root directory" def="." />
          <Row opt="--section, -s" desc="Section to diff (currently supports 'routes')" def="routes" />
        </Table>
        <CodeBlock language="bash" filename="Terminal">{`# Diff routes against a previous trace
aq trace diff /path/to/old/.aquilia/routes.json`}</CodeBlock>
      </section>

      {/* .aquilia/ Directory Structure */}
      <section className={sectionClass}>
        <h2 className={h2Class}>The .aquilia/ Directory</h2>
        <p className={pClass}>
          The <code className={codeClass}>.aquilia/</code> directory is automatically generated by the server on boot and contains:
        </p>
        <CodeBlock language="text" filename="Directory Structure">{`.aquilia/
├── manifest.json      # Compiled manifest snapshot
├── routes.json        # Full route table
├── di_graph.json      # Dependency injection graph
├── schema.json        # Database schema snapshot
├── config.json        # Resolved configuration
├── diagnostics.json   # Subsystem health data
├── journal.jsonl      # Lifecycle event journal (append-only)
└── .lock              # Server lock file (present while running)`}</CodeBlock>
        <p className={pClass}>
          This directory should typically be added to <code className={codeClass}>.gitignore</code> as it contains runtime-specific data.
        </p>
      </section>

      <NextSteps
        items={[
          { text: 'Trace & Debug Docs', link: '/docs/trace' },
          { text: 'Inspection Commands', link: '/docs/cli/inspection' },
          { text: 'Artifact Commands', link: '/docs/cli/artifacts' },
          { text: 'Core Commands', link: '/docs/cli/core' },
        ]}
      />
    </div>
  )
}
