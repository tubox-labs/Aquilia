import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { motion } from 'framer-motion'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

interface ConfigRowProps {
  field: string
  type: string
  default_: string
  envVar: string
  desc: string
  isDark: boolean
}

function ConfigRow({ field, type, default_, envVar, desc, isDark }: ConfigRowProps) {
  return (
    <tr className="border-b border-zinc-100 dark:border-zinc-800/40 last:border-b-0 hover:bg-zinc-50/50 dark:hover:bg-zinc-800/10 transition-colors">
      <td className="py-3.5 pr-4 align-top">
        <code className={`text-xs font-mono font-bold ${isDark ? 'text-aquilia-300' : 'text-aquilia-600'}`}>{field}</code>
      </td>
      <td className={`py-3.5 pr-4 align-top text-xs font-mono ${isDark ? 'text-zinc-500' : 'text-zinc-500'}`}>{type}</td>
      <td className={`py-3.5 pr-4 align-top text-xs font-mono ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>{default_}</td>
      <td className={`py-3.5 pr-4 align-top text-xs font-mono ${isDark ? 'text-zinc-400' : 'text-zinc-500'}`}>{envVar}</td>
      <td className={`py-3.5 text-xs leading-relaxed ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>{desc}</td>
    </tr>
  )
}

export function ADPConfigurationPage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const rows: ConfigRowProps[] = [
    { field: 'host', type: 'str', default_: '"127.0.0.1"', envVar: 'AQ_DEV_HOST', desc: 'Bind host address for the TCP socket listener.', isDark },
    { field: 'port', type: 'int', default_: '8000', envVar: 'AQ_DEV_PORT', desc: 'Bind port number. Must be in the range 1-65535.', isDark },
    { field: 'uds', type: 'str|None', default_: 'None', envVar: 'AQ_DEV_UDS', desc: 'Path to a Unix Domain Socket. Takes precedence over host:port.', isDark },
    { field: 'fd', type: 'int|None', default_: 'None', envVar: 'AQ_DEV_FD', desc: 'Inherited socket file descriptor index for process supervisor controls.', isDark },
    { field: 'http', type: 'str', default_: '"h11"', envVar: 'AQ_DEV_HTTP', desc: 'Transport parser selection: "h11" (ADP native transport) or "auto" (Uvicorn).', isDark },
    { field: 'ws', type: 'str', default_: '"auto"', envVar: 'AQ_DEV_WS', desc: 'WebSocket protocol mode: "auto" (enables WS upgraded loops) or "none".', isDark },
    { field: 'reload', type: 'bool', default_: 'True', envVar: 'AQ_DEV_RELOAD', desc: 'Enables hot-reload watching on the workspace filesystem.', isDark },
    { field: 'reload_dirs', type: 'list[Path]', default_: '[cwd]', envVar: '—', desc: 'Paths to watch. Defaults to the current working directory.', isDark },
    { field: 'reload_excludes', type: 'list[str]', default_: '[]', envVar: '—', desc: 'Glob patterns indicating files/directories to bypass during reload monitoring.', isDark },
    { field: 'log_level', type: 'str', default_: '"INFO"', envVar: 'AQ_DEV_LOG_LEVEL', desc: 'ADP logger outputs level: DEBUG, INFO, WARNING, or ERROR.', isDark },
    { field: 'inspector_enabled', type: 'bool', default_: 'True', envVar: 'AQ_DEV_INSPECTOR_ENABLED', desc: 'Enables telemetry collection, request history recording, and diagnostics.', isDark },
    { field: 'max_request_history', type: 'int', default_: '500', envVar: 'AQ_DEV_MAX_REQUEST_HISTORY', desc: 'Length of the circular history queue storing RequestRecord logs.', isDark },
    { field: 'profiler_enabled', type: 'bool', default_: 'False', envVar: 'AQ_DEV_PROFILER_ENABLED', desc: 'Enables cProfile execution tracking for incoming requests (adds significant overhead).', isDark },
    { field: 'sql_explain_threshold_ms', type: 'float', default_: '50.0', envVar: 'AQ_DEV_SQL_EXPLAIN_THRESHOLD_MS', desc: 'Executes EXPLAIN plans on database queries taking longer than this duration.', isDark },
    { field: 'n_plus_one_detection', type: 'bool', default_: 'True', envVar: 'AQ_DEV_N_PLUS_ONE_DETECTION', desc: 'Checks request cycles for duplicate database reads matching N+1 patterns.', isDark },
    { field: 'memory_snapshot_interval_s', type: 'float', default_: '30.0', envVar: 'AQ_DEV_MEMORY_SNAPSHOT_INTERVAL_S', desc: 'Frequence of tracemalloc snapshot saves. Set to 0 to disable memory tracing.', isDark },
    { field: 'timeout_graceful_shutdown', type: 'float', default_: '5.0', envVar: 'AQ_DEV_TIMEOUT_GRACEFUL_SHUTDOWN', desc: 'Grace period (in seconds) allowed for active connections to finish before termination.', isDark },
  ]

  return (
    <div className="max-w-4xl">
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.25 }}>
        <h1 className={`text-4xl font-extrabold tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Configuration
        </h1>
        <p className={`text-lg leading-relaxed mb-6 ${isDark ? 'text-zinc-300' : 'text-zinc-700'}`}>
          ADP parameters can be specified via environment variables, <code className="font-mono text-sm">workspace.py</code> configs, 
          or CLI flags. Setting options dynamically enables developers to tailor diagnostic thresholds and reload scopes.
        </p>
      </motion.div>

      <section className="mt-10">
        <h2 className={`text-2xl font-bold mb-4 pb-2 border-b ${isDark ? 'border-zinc-800/60 text-white' : 'border-gray-100 text-gray-900'}`}>
          Resolution Precedence
        </h2>
        <p className={`text-sm mb-4 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          Config parameters are merged from lowest to highest priority:
        </p>
        <div className={`flex flex-wrap items-center gap-2 text-xs font-semibold px-4 py-3.5 rounded-xl border mb-6 ${isDark ? 'border-zinc-800 bg-zinc-900/20 text-zinc-300' : 'border-zinc-200 bg-zinc-50 text-zinc-700'}`}>
          <span>Defaults</span>
          <span className="opacity-50">→</span>
          <span>workspace.py</span>
          <span className="opacity-50">→</span>
          <span>AQ_DEV_* Env Vars</span>
          <span className="opacity-50">→</span>
          <span>CLI Arguments</span>
        </div>

        <p className={`text-sm mb-4 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          Configure your development options under the server class in <code className="font-mono text-sm">workspace.py</code>:
        </p>
        <CodeBlock 
          language="python" 
          highlightLines={[3, 4, 7, 8]}
          code={`# workspace.py
class MyServer(AquilaConfig.Server):
    adp_inspector = True
    adp_max_request_history = 1000
    adp_profiler = False
    adp_sql_explain_threshold_ms = 25.0
    adp_n_plus_one_detection = True
    adp_memory_snapshot_interval_s = 60.0
    adp_http = "h11"
    adp_ws = "auto"
    use_adp = True`} 
        />
      </section>

      <section className="mt-12">
        <h2 className={`text-2xl font-bold mb-6 pb-2 border-b ${isDark ? 'border-zinc-800/60 text-white' : 'border-gray-100 text-gray-900'}`}>
          <DocTerm id="devplatform.config">AquiliaDevelopmentConfig</DocTerm> Fields
        </h2>
        <div className="overflow-x-auto">
          <table className={`w-full text-left text-sm ${isDark ? 'text-zinc-300' : 'text-zinc-700'}`}>
            <thead>
              <tr className={`border-b text-xs uppercase tracking-wider ${isDark ? 'border-zinc-800 text-zinc-500' : 'border-zinc-200 text-zinc-400'}`}>
                <th className="pb-3 font-bold pr-4">Field</th>
                <th className="pb-3 font-bold pr-4">Type</th>
                <th className="pb-3 font-bold pr-4">Default</th>
                <th className="pb-3 font-bold pr-4">Env Override</th>
                <th className="pb-3 font-bold">Description</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(r => <ConfigRow key={r.field} {...r} />)}
            </tbody>
          </table>
        </div>
      </section>

      <section className="mt-12">
        <h2 className={`text-2xl font-bold mb-4 pb-2 border-b ${isDark ? 'border-zinc-800/60 text-white' : 'border-gray-100 text-gray-900'}`}>
          Environment File Overrides
        </h2>
        <p className={`text-sm mb-4 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          To configure the dev platform locally, append any <code className="font-mono text-sm">AQ_DEV_*</code> key to your 
          workspace's <code className="font-mono text-sm">.env</code> file:
        </p>
        <CodeBlock 
          language="bash" 
          highlightLines={[2, 3, 7, 8]}
          code={`# .env
AQ_DEV_HOST=0.0.0.0
AQ_DEV_PORT=8000
AQ_DEV_RELOAD=true
AQ_DEV_LOG_LEVEL=DEBUG
AQ_DEV_INSPECTOR_ENABLED=true
AQ_DEV_SQL_EXPLAIN_THRESHOLD_MS=25.0
AQ_DEV_N_PLUS_ONE_DETECTION=true`} 
        />
      </section>

      <section className="mt-16">
        <NextSteps items={[
          { text: 'Terminal UI', link: '/docs/devplatform/terminal-ui' },
          { text: 'Hot Reload', link: '/docs/devplatform/hot-reload' },
          { text: 'Diagnostics', link: '/docs/devplatform/diagnostics' },
        ]} />
      </section>
    </div>
  )
}
