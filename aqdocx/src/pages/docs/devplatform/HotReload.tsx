import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { motion } from 'framer-motion'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function ADPHotReloadPage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl">
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.25 }}>
        <h1 className={`text-4xl font-extrabold tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Hot Reload
        </h1>
        <p className={`text-lg leading-relaxed mb-6 ${isDark ? 'text-zinc-300' : 'text-zinc-700'}`}>
          ADP features an intelligent, framework-aware hot reload system. Instead of restarting the python process — 
          which discards database connection pools and warm caches — ADP parses dependency imports statically using AST, 
          reloading only the changed modules.
        </p>
      </motion.div>

      <section className="mt-10">
        <h2 className={`text-2xl font-bold mb-6 pb-2 border-b ${isDark ? 'border-zinc-800/60 text-white' : 'border-gray-100 text-gray-900'}`}>
          The Reload Lifecycle
        </h2>
        <div className="space-y-8">
          {[
            { step: '1', title: <DocTerm id="devplatform.watcher">WorkspaceWatcher</DocTerm>, pkg: 'reload.watcher', desc: 'Monitors the workspace root using watchfiles. Integrates a 50ms debounce window to bundle multiple quick saves. Uses an asyncio shutdown task to cleanly exit when the server stops.' },
            { step: '2', title: 'DependencyGraphAnalyzer', pkg: 'reload.analyzer', desc: 'Builds a directed graph of imports by parsing python files statically using ast.parse. When a file is modified, it computes the transitive closure of all downstream modules requiring updates.' },
            { step: '3', title: 'ModuleReloadExecutor', pkg: 'reload.executor', desc: 'Sorts affected modules topologically (using a depth-first search order) and invokes importlib.reload() sequentially. This guarantees parents reload after their dependencies, avoiding reference issues.' },
            { step: '4', title: 'StatePreservation', pkg: 'reload.state_preservation', desc: 'Pre-reload and post-reload callback hooks can be registered on custom singleton classes to capture state objects (like database pools or sockets) and restore them post-reload.' },
          ].map(({ step, title, pkg, desc }) => (
            <div key={step} className="flex gap-4 items-start py-2">
              <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${isDark ? 'bg-aquilia-500/10 text-aquilia-400' : 'bg-aquilia-50 text-aquilia-700'}`}>{step}</div>
              <div>
                <div className="flex items-baseline gap-2 mb-1.5 flex-wrap">
                  <span className={`font-bold text-base ${isDark ? 'text-zinc-100' : 'text-zinc-900'}`}>{title}</span>
                  <code className={`text-xs px-2 py-0.5 rounded font-mono ${isDark ? 'bg-zinc-800 text-zinc-400' : 'bg-zinc-100 text-zinc-500'}`}>{pkg}</code>
                </div>
                <p className={`text-sm leading-relaxed ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>{desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="mt-12">
        <h2 className={`text-2xl font-bold mb-4 pb-2 border-b ${isDark ? 'border-zinc-800/60 text-white' : 'border-gray-100 text-gray-900'}`}>
          Excludes & Glob Filters
        </h2>
        <p className={`text-sm mb-4 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          To prevent loop cycles or unnecessary disk checks, the watcher filters out temporary and virtual environment directories in <DocTerm id="devplatform.config">AquiliaDevelopmentConfig</DocTerm>:
        </p>
        <CodeBlock 
          language="python" 
          highlightLines={[3, 4, 7]}
          code={`# AquiliaDevelopmentConfig defaults
reload_excludes: list[str] = [
    "__pycache__",
    "*.pyc",
    ".git",
    ".venv",
    "node_modules",
]`} 
        />
      </section>

      <section className="mt-12">
        <h2 className={`text-2xl font-bold mb-4 pb-2 border-b ${isDark ? 'border-zinc-800/60 text-white' : 'border-gray-100 text-gray-900'}`}>
          Manual Control
        </h2>
        <p className={`text-sm mb-4 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          If you are working in an environment without file-write watchers (such as remote containers), you can trigger 
          an AST reload on demand by pressing <kbd className="px-1.5 py-0.5 text-xs font-mono rounded border">R</kbd> in your interactive terminal:
        </p>
        <CodeBlock 
          language="bash" 
          code={`# In your active dev console:
# Press: R

  ↻ Triggering manual reload...
INFO | aquilia.devplatform.reload.watcher — File change detected: [<manual>]`} 
        />
      </section>

      <section className="mt-16">
        <NextSteps items={[
          { text: 'Diagnostics', link: '/docs/devplatform/diagnostics' },
          { text: 'Configuration', link: '/docs/devplatform/configuration' },
        ]} />
      </section>
    </div>
  )
}
