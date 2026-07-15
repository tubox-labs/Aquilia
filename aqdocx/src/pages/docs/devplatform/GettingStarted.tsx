import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { motion } from 'framer-motion'

export function ADPGettingStartedPage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl">
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.25 }}>
        <h1 className={`text-4xl font-extrabold tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Getting Started
        </h1>
        <p className={`text-lg leading-relaxed mb-6 ${isDark ? 'text-zinc-300' : 'text-zinc-700'}`}>
          The Aquilia Development Platform is set up by default in every new workspace. You don't need any complex files or 
          boilerplate setups — running your dev server is a single command.
        </p>
      </motion.div>

      <section className="mt-10">
        <h2 className={`text-2xl font-bold mb-4 pb-2 border-b ${isDark ? 'border-zinc-800/60 text-white' : 'border-gray-100 text-gray-900'}`}>
          Prerequisites
        </h2>
        <p className={`text-sm leading-relaxed mb-4 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          Before starting, verify that your local environment has the required packages:
        </p>
        <ul className={`text-sm space-y-2 pl-4 list-disc ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          <li>Python 3.10+ installed on your system.</li>
          <li>Aquilia Framework installed: <code className="font-mono text-xs px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400">pip install aquilia</code></li>
          <li>A workspace generated using: <code className="font-mono text-xs px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400">aq init myapp</code></li>
          <li>Optional: <code className="font-mono text-xs px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400">pip install watchfiles</code> for filesystem hot-reloads.</li>
        </ul>
      </section>

      <section className="mt-12">
        <h2 className={`text-2xl font-bold mb-4 pb-2 border-b ${isDark ? 'border-zinc-800/60 text-white' : 'border-gray-100 text-gray-900'}`}>
          Starting the Server
        </h2>
        <p className={`text-sm mb-4 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          Navigate into your project folder and run the dev server:
        </p>
        <CodeBlock 
          language="bash" 
          highlightLines={[2]}
          code={`cd myapp
aq dev`} 
        />
        <p className={`text-sm mt-6 mb-4 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          Once started, the server begins:
        </p>
        <div className="space-y-4">
          <div className="flex items-start gap-3">
            <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${isDark ? 'bg-zinc-800 text-zinc-400' : 'bg-zinc-100 text-zinc-600'}`}>1</span>
            <p className={`text-sm ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
              <strong>Config Validation:</strong> Resolves keys from your <code className="font-mono text-xs">workspace.py</code> or environment variables using <DocTerm id="devplatform.config">AquiliaDevelopmentConfig</DocTerm>.
            </p>
          </div>
          <div className="flex items-start gap-3">
            <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${isDark ? 'bg-zinc-800 text-zinc-400' : 'bg-zinc-100 text-zinc-600'}`}>2</span>
            <p className={`text-sm ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
              <strong>Console Bootstrap:</strong> Launches the interactive UI showing keyboard control commands via <DocTerm id="devplatform.ui">ADPTerminalUI</DocTerm>.
            </p>
          </div>
          <div className="flex items-start gap-3">
            <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${isDark ? 'bg-zinc-800 text-zinc-400' : 'bg-zinc-100 text-zinc-600'}`}>3</span>
            <p className={`text-sm ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
              <strong>TCP Binding:</strong> Opens a native HTTP/1.1 endpoint (default is <code className="font-mono text-xs">http://127.0.0.1:8000</code>) backed by <DocTerm id="devplatform.server">AquiliaDevelopmentServer</DocTerm>.
            </p>
          </div>
        </div>
      </section>

      <section className="mt-12">
        <h2 className={`text-2xl font-bold mb-4 pb-2 border-b ${isDark ? 'border-zinc-800/60 text-white' : 'border-gray-100 text-gray-900'}`}>
          Common CLI Overrides
        </h2>
        <p className={`text-sm mb-4 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          Use flags to adjust server configuration fields instantly without touching files:
        </p>
        <CodeBlock 
          language="bash" 
          highlightLines={[2, 5, 8]}
          code={`# Bind to custom network interfaces or ports
aq dev --host 0.0.0.0 --port 9000

# Disable filesystem watcher tasks (faster initialization)
aq dev --no-reload

# Wrap the HTTP loop with Uvicorn instead of native H11 connection logic
aq dev --http auto

# Bind directly to a Unix Domain Socket instead of host/port
aq dev --uds /tmp/myapp.sock`} 
        />
      </section>

      <section className="mt-12">
        <h2 className={`text-2xl font-bold mb-4 pb-2 border-b ${isDark ? 'border-zinc-800/60 text-white' : 'border-gray-100 text-gray-900'}`}>
          Shutdown Sequence
        </h2>
        <p className={`text-sm mb-4 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          To stop the server cleanly, press <kbd className="px-1.5 py-0.5 text-xs font-mono rounded border">Q</kbd> in your TTY shell, 
          or hit <kbd className="px-1.5 py-0.5 text-xs font-mono rounded border">Ctrl + C</kbd>. This schedules a graceful shutdown sequence:
        </p>
        <ul className={`text-sm space-y-2 pl-4 list-decimal ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          <li>Stops accepting incoming TCP connections on the socket.</li>
          <li>Drains active client requests (waiting up to the timeout interval).</li>
          <li>Cancels running lifespan tasks cleanly.</li>
          <li>Teardown hooks are executed across all registered plugins to clean up resource file descriptors.</li>
        </ul>
      </section>

      <section className="mt-16">
        <NextSteps items={[
          { text: 'Architecture', link: '/docs/devplatform/architecture' },
          { text: 'Configuration', link: '/docs/devplatform/configuration' },
        ]} />
      </section>
    </div>
  )
}
