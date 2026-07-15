import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { motion } from 'framer-motion'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { NextSteps } from '../../../components/NextSteps'

export function ADPFaultsPage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const faults = [
    { name: 'DevPlatformFault', desc: 'The base exception for the dev platform domain. Extends Aquilia\'s standard Fault class.' },
    { name: 'StartupFault', desc: 'Raised during startup issues, such as socket binding errors (EADDRINUSE) or lifespan timeouts.' },
    { name: 'ReloadFault', desc: 'Raised when the hot-reload scheduler or AST analyzer encounters an unrecoverable exception.' },
    { name: 'InspectorFault', desc: 'Raised by diagnostics when failing to communicate metadata or telemetry queries to the host.' },
    { name: 'WorkerFault', desc: 'Raised when background threads, periodic diagnostics, or plugin hook callbacks raise errors.' },
    { name: 'ConfigurationFault', desc: 'Raised when configuration values fail schema type or boundary validation constraints.' },
  ]

  return (
    <div className="max-w-4xl">
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.25 }}>
        <h1 className={`text-4xl font-extrabold tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Faults
        </h1>
        <p className={`text-lg leading-relaxed mb-6 ${isDark ? 'text-zinc-300' : 'text-zinc-700'}`}>
          ADP errors utilize Aquilia\'s standard fault reporting structure rather than throwing raw tracebacks. 
          Exceptions are typed subclasses of <DocTerm id="devplatform.fault.base">DevPlatformFault</DocTerm>, ensuring clean, 
          actionable error reporting.
        </p>
      </motion.div>

      <section className="mt-10">
        <h2 className={`text-2xl font-bold mb-4 pb-2 border-b ${isDark ? 'border-zinc-800/60 text-white' : 'border-gray-100 text-gray-900'}`}>
          Fault Hierarchy
        </h2>
        <p className={`text-sm mb-4 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          ADP exception inheritance maps directly to the central fault engine structure:
        </p>
        <CodeBlock 
          language="python" 
          highlightLines={[2, 3, 4, 5, 6]}
          code={`# aquilia/devplatform/faults.py
DevPlatformFault
├── StartupFault          # Fatal server boot failures
├── ReloadFault           # Recoverable module compile errors
├── InspectorFault        # Telemetry/diagnostic socket exceptions
├── WorkerFault           # Plugin hooks unhandled errors
└── ConfigurationFault    # Invalid environment properties`} 
        />
      </section>

      <section className="mt-12">
        <h2 className={`text-2xl font-bold mb-4 pb-2 border-b ${isDark ? 'border-zinc-800/60 text-white' : 'border-gray-100 text-gray-900'}`}>
          Fault Reference
        </h2>
        <div className="divide-y divide-zinc-100 dark:divide-zinc-800/40">
          {faults.map(({ name, desc }) => (
            <div key={name} className="py-4">
              <code className={`text-sm font-mono font-bold ${isDark ? 'text-aquilia-300' : 'text-aquilia-600'}`}>{name}</code>
              <p className={`text-sm mt-1.5 leading-relaxed ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>{desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mt-12">
        <h2 className={`text-2xl font-bold mb-4 pb-2 border-b ${isDark ? 'border-zinc-800/60 text-white' : 'border-gray-100 text-gray-900'}`}>
          Reporting Faults
        </h2>
        <p className={`text-sm mb-4 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          Plugins and servers raise and log platform exceptions using the <DocTerm id="devplatform.report_fault">report_fault</DocTerm> helper:
        </p>
        <CodeBlock 
          language="python" 
          highlightLines={[6, 7, 8]}
          code={`from aquilia.devplatform.faults import ReloadFault, report_fault

try:
    reload_changed_modules(paths)
except Exception as exc:
    report_fault(
        ReloadFault("Compilation failed", metadata={"module": name}),
        app=current_app
    )`} 
        />
      </section>

      <section className="mt-12">
        <h2 className={`text-2xl font-bold mb-4 pb-2 border-b ${isDark ? 'border-zinc-800/60 text-white' : 'border-gray-100 text-gray-900'}`}>
          Startup Faults and Port Bind Failures
        </h2>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          If the target network port is occupied by another process, ADP intercepts the operating system's 
          <code className="text-sm font-mono">EADDRINUSE</code> error. Instead of outputting a verbose socket traceback, 
          it throws a <DocTerm id="devplatform.fault.startup">StartupFault</DocTerm> with suggestions (e.g. running 
          <code className="text-sm font-mono">lsof -i :8000</code> or changing the port flag) and shuts down 
          with exit code 1.
        </p>
      </section>

      <section className="mt-16">
        <NextSteps items={[
          { text: 'Overview', link: '/docs/devplatform/overview' },
          { text: 'Architecture', link: '/docs/devplatform/architecture' },
        ]} />
      </section>
    </div>
  )
}
