import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { ArrowLeft, Cpu } from 'lucide-react'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'

export function DIDiagnostics() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      {/* Title Header */}
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Cpu className="w-4 h-4" />
          Dependency Injection / Diagnostics
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          DI Diagnostics &amp; Observability
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          The diagnostics module under <code className="text-aquilia-500">aquilia/di/diagnostics.py</code> exposes runtime events, resolution timing metrics, and validation tracers.
        </p>
      </div>

      {/* DIEventType */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>DIEventType</h2>
        <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="py-4 px-6 text-left font-semibold text-aquilia-500">Event</th>
                <th className="py-4 px-6 text-left font-semibold">Emitted When</th>
                <th className="py-4 px-6 text-left font-semibold">Metadata</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['REGISTRATION', 'container.register() is called', 'token, tag, provider_name'],
                ['RESOLUTION_START', 'resolve_async() begins for a token', 'token, tag'],
                ['RESOLUTION_SUCCESS', 'resolve_async() completes successfully', 'token, tag, duration'],
                ['RESOLUTION_FAILURE', 'resolve_async() raises an error', 'token, tag, duration, error'],
                ['LIFECYCLE_STARTUP', 'Container startup begins', 'app_name (via metadata)'],
                ['LIFECYCLE_SHUTDOWN', 'Container shutdown begins', 'app_name (via metadata)'],
                ['PROVIDER_INSTANTIATION', 'A provider creates a new instance', 'token, provider_name, duration'],
              ].map(([event, when, meta], i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                  <td className="py-3.5 px-6 font-mono text-aquilia-500 text-xs">{event}</td>
                  <td className={`py-3.5 px-6 text-xs ${subtleText}`}>{when}</td>
                  <td className="py-3.5 px-6 font-mono text-xs text-yellow-500">{meta}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* ConsoleDiagnosticListener */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>ConsoleDiagnosticListener</h2>
        <p className={`mb-4 ${subtleText}`}>
          A built-in diagnostic listener that formats DI events to log targets. Perfect for local dev debugging:
        </p>
        <CodeBlock language="python" filename="diag_listener.py">{`from aquilia.di import DIDiagnostics, ConsoleDiagnosticListener

# Register the console diagnostic event listener
listener = ConsoleDiagnosticListener()
container._diagnostics.register_listener(listener)

# Resolutions will now dump trace profiles into standard error:
# [DI] RESOLUTION_START: token=myapp.services.UserService tag=None
# [DI] PROVIDER_INSTANTIATION: token=myapp.services.UserService duration=0.0012s
# [DI] RESOLUTION_SUCCESS: token=myapp.services.UserService duration=0.0014s`}</CodeBlock>
      </section>

      {/* CLI Commands */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>CLI Commands</h2>
        <p className={`mb-6 ${subtleText}`}>
          Manage and check your dependency injection setup using the <code className="text-aquilia-500">aq</code> command line interface:
        </p>

        {/* di-check */}
        <div className="mb-10 border-l-2 border-white/5 pl-6">
          <h3 className={`text-lg font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}><code className="text-aquilia-500 text-lg">aq di-check</code></h3>
          <p className={`mb-3 text-sm ${subtleText}`}>
            Verifies cyclic loops, scope matching, app isolation, and missing providers.
          </p>
          <CodeBlock language="bash">{`aq di-check --settings settings.py`}</CodeBlock>
        </div>

        {/* di-tree */}
        <div className="mb-10 border-l-2 border-white/5 pl-6">
          <h3 className={`text-lg font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}><code className="text-aquilia-500 text-lg">aq di-tree</code></h3>
          <p className={`mb-3 text-sm ${subtleText}`}>
            Prints a clean text tree representing the entire DI hierarchy.
          </p>
          <CodeBlock language="bash">{`aq di-tree --settings settings.py --root UserService`}</CodeBlock>
        </div>

        {/* di-graph */}
        <div className="mb-10 border-l-2 border-white/5 pl-6">
          <h3 className={`text-lg font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}><code className="text-aquilia-500 text-lg">aq di-graph</code></h3>
          <p className={`mb-3 text-sm ${subtleText}`}>
            Generates a Graphviz DOT visualization.
          </p>
          <CodeBlock language="bash">{`aq di-graph --settings settings.py --out graph.dot`}</CodeBlock>
        </div>

        {/* di-profile */}
        <div className="mb-10 border-l-2 border-white/5 pl-6">
          <h3 className={`text-lg font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}><code className="text-aquilia-500 text-lg">aq di-profile</code></h3>
          <p className={`mb-3 text-sm ${subtleText}`}>
            Benchmarks DI cold start and warm O(1) resolution latency profiles.
          </p>
          <CodeBlock language="bash">{`aq di-profile --settings settings.py --bench resolve`}</CodeBlock>
        </div>
      </section>

      {/* Navigation */}
      <div className={`mt-16 pt-8 border-t flex justify-between ${isDark ? 'border-white/5' : 'border-gray-200'}`}>
        <Link to="/docs/di/lifecycle" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition font-medium">
          <ArrowLeft className="w-4 h-4" /> Lifecycle
        </Link>
        <span />
      </div>

      <NextSteps />
    </div>
  )
}