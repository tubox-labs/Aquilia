import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { motion } from 'framer-motion'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function ADPDiagnosticsPage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl">
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.25 }}>
        <h1 className={`text-4xl font-extrabold tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Diagnostics
        </h1>
        <p className={`text-lg leading-relaxed mb-6 ${isDark ? 'text-zinc-300' : 'text-zinc-700'}`}>
          ADP ships with observer-based telemetry trackers. Because these run on background threads or hook into core event cycles, 
          they introduce zero overhead during standard execution.
        </p>
      </motion.div>

      <section className="mt-10">
        <h2 className={`text-2xl font-bold mb-4 pb-2 border-b ${isDark ? 'border-zinc-800/60 text-white' : 'border-gray-100 text-gray-900'}`}>
          1. SQL Query Analyzer
        </h2>
        <p className={`text-sm leading-relaxed mb-6 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          Implemented in <code className="font-mono text-xs">aquilia/devplatform/diagnostics/sql.py</code>, the SQL diagnostic subsystem registers 
          two key observers to trace transactions:
        </p>

        <div className="space-y-6">
          <div className="py-2">
            <h4 className={`font-bold text-base mb-1 ${isDark ? 'text-zinc-100' : 'text-zinc-900'}`}>RequestSQLAccumulator</h4>
            <p className={`text-sm leading-relaxed ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
              Traces executed SQL lines during the request lifespan by listening to database connection spans. 
              Rather than directly importing or interfering with the Database layer, it captures details 
              exclusively via trace span emissions.
            </p>
          </div>
          <div className="py-2">
            <h4 className={`font-bold text-base mb-1 ${isDark ? 'text-zinc-100' : 'text-zinc-900'}`}>SQLQueryAnalyzer</h4>
            <p className={`text-sm leading-relaxed ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
              Analyzes database calls at the end of each request. Highlights slow queries taking longer than the threshold, 
              flags duplicate lines, and identifies N+1 query loops (e.g. repeated select transactions querying the same 
              table with differing primary keys).
            </p>
          </div>
        </div>

        <p className={`text-sm mt-6 mb-4 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          Define diagnostic thresholds in your server settings:
        </p>
        <CodeBlock 
          language="python" 
          highlightLines={[3, 4]}
          code={`# workspace.py
class MyServer(AquilaConfig.Server):
    adp_sql_explain_threshold_ms = 25.0  # Runs EXPLAIN on slow queries
    adp_n_plus_one_detection = True       # Logs warnings on N+1 reads`} 
        />
      </section>

      <section className="mt-12">
        <h2 className={`text-2xl font-bold mb-4 pb-2 border-b ${isDark ? 'border-zinc-800/60 text-white' : 'border-gray-100 text-gray-900'}`}>
          2. Memory Snapshot Tracker
        </h2>
        <p className={`text-sm leading-relaxed mb-4 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          The memory system utilizes Python's <code className="font-mono text-xs">tracemalloc</code> library. 
          When enabled, a background thread records diagnostic allocations at periodic intervals. 
          You can inspect snapshots on demand using terminal keys or access them programmatically:
        </p>
        <CodeBlock 
          language="python" 
          highlightLines={[3]}
          code={`# workspace.py
class MyServer(AquilaConfig.Server):
    adp_memory_snapshot_interval_s = 30.0  # Snapshots memory every 30 seconds`} 
        />
        <p className={`text-sm mt-4 leading-relaxed ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          Press <kbd className="px-1.5 py-0.5 text-xs font-mono rounded border">M</kbd> in your active terminal session to trigger an immediate snapshot 
          and output the top line allocators.
        </p>
      </section>

      <section className="mt-12">
        <h2 className={`text-2xl font-bold mb-4 pb-2 border-b ${isDark ? 'border-zinc-800/60 text-white' : 'border-gray-100 text-gray-900'}`}>
          3. Event-Loop Monitor
        </h2>
        <p className={`text-sm leading-relaxed mb-4 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          ADP registers a callback timer on the active asyncio event loop. If any execution thread blocks the loop's 
          callback execution beyond the warning limit (default: 10ms), ADP fires a warning:
        </p>
        <CodeBlock 
          language="bash" 
          code={`WARNING | aquilia.devplatform.diagnostics — Slow event-loop callback: 
    myapp.controllers.users:fetch_list took 84.1ms (threshold: 10ms)`} 
        />
        <p className={`text-sm mt-4 leading-relaxed ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          This is crucial for async development, highlighting instances where synchronous operations (like third-party requests 
          or long files reads) block connection handling.
        </p>
      </section>

      <section className="mt-12">
        <h2 className={`text-2xl font-bold mb-4 pb-2 border-b ${isDark ? 'border-zinc-800/60 text-white' : 'border-gray-100 text-gray-900'}`}>
          The Metrics Database: <DocTerm id="devplatform.runtime_state_store">RuntimeStateStore</DocTerm>
        </h2>
        <p className={`text-sm mb-4 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          Telemetry metrics are committed to a circular queue inside the state store. 
          Query the singleton to pull transactional analytics:
        </p>
        <CodeBlock 
          language="python" 
          highlightLines={[3, 6, 12]}
          code={`from aquilia.devplatform.core.runtime import RuntimeStateStore

store = RuntimeStateStore.get_instance()

# Fetch active metrics
snap = store.snapshot()
print(f"RPS (1s): {snap.rps_1s}")
print(f"EMA Latency: {snap.avg_latency_ms}ms")

# Read request records history
records = store.get_recent_requests(limit=50)
for rec in records:
    print(rec.trace_id, rec.path, rec.duration_ms)`} 
        />
      </section>

      <section className="mt-16">
        <NextSteps items={[
          { text: 'Plugins', link: '/docs/devplatform/plugins' },
          { text: 'Faults', link: '/docs/devplatform/faults' },
        ]} />
      </section>
    </div>
  )
}
