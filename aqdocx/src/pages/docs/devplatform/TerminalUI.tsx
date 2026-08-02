import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { motion } from 'framer-motion'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

function KeyRow({ k, desc, isDark }: { k: string; desc: string; isDark: boolean }) {
  return (
    <div className="flex items-center gap-4 py-3 border-b border-zinc-100 dark:border-zinc-800/40 last:border-b-0">
      <kbd className={`px-2 py-1 text-xs font-bold rounded font-mono shrink-0 select-none ${isDark ? 'bg-aquilia-500/10 text-aquilia-400 border border-aquilia-500/10' : 'bg-aquilia-50 text-aquilia-700 border border-aquilia-100'}`}>{k}</kbd>
      <span className={`text-sm ${isDark ? 'text-zinc-300' : 'text-zinc-600'}`}>{desc}</span>
    </div>
  )
}

export function ADPTerminalUIPage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl">
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.25 }}>
        <h1 className={`text-4xl font-extrabold tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Terminal UI
        </h1>
        <p className={`text-lg leading-relaxed mb-4 ${isDark ? 'text-zinc-300' : 'text-zinc-700'}`}>
          ADP ships with an interactive keyboard-driven terminal layout. When running <code className="font-mono text-sm">aq dev</code>, 
          a daemon listener thread captures keystrokes, enabling you to inspect diagnostics or trigger reloads directly in the shell.
        </p>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          Implemented in <code className="font-mono text-xs">aquilia/devplatform/ui.py</code>. By utilizing 
          Python's standard <code className="font-mono text-xs">termios</code> and <code className="font-mono text-xs">tty</code> modules, 
          ADP enables cbreak console reads without external curses dependencies.
        </p>
      </motion.div>

      <section className="mt-10">
        <h2 className={`text-2xl font-bold mb-4 pb-2 border-b ${isDark ? 'border-zinc-800/60 text-white' : 'border-gray-100 text-gray-900'}`}>
          Active Console Hotkeys
        </h2>
        <p className={`text-sm mb-4 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          The keyboard daemon captures keystrokes without blocking request cycles. The following hotkeys are active when connected to a TTY:
        </p>
        <div className="divide-y divide-zinc-100 dark:divide-zinc-800/40">
          <KeyRow k="R" desc="Triggers hot-reload instantly, running static AST analyses on modified modules." isDark={isDark} />
          <KeyRow k="C" desc="Clears the terminal scrollback and prints the startup banner layout." isDark={isDark} />
          <KeyRow k="P" desc="Fetches performance snapshots from the RuntimeStateStore, outputting live requests, active WebSockets, and latency metrics." isDark={isDark} />
          <KeyRow k="M" desc="Takes a tracemalloc memory snapshot and lists the top 8 line allocators." isDark={isDark} />
          <KeyRow k="D" desc="Runs a routing schema discovery analysis, rendering a table of all registered path handlers." isDark={isDark} />
          <KeyRow k="L" desc="Toggles console logs logging levels outputs between verbose and normal layouts." isDark={isDark} />
          <KeyRow k="H" desc="Renders the full documentation shortcut reference in the console." isDark={isDark} />
          <KeyRow k="Q" desc="Triggers a graceful shutdown sequence, closing ports and finishing active requests." isDark={isDark} />
        </div>
      </section>

      <section className="mt-12">
        <h2 className={`text-2xl font-bold mb-4 pb-2 border-b ${isDark ? 'border-zinc-800/60 text-white' : 'border-gray-100 text-gray-900'}`}>
          Performance Analytics Panel (P)
        </h2>
        <p className={`text-sm mb-4 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          Pressing <kbd className="px-1.5 py-0.5 text-xs font-mono rounded border">P</kbd> queries the global metrics store:
        </p>
        <CodeBlock language="bash" code={`  ◆ Performance Metrics
  Uptime          120.4s
  Requests        8493
  Errors          1
  Active Conns    5
  RPS (1s)        24.5
  Avg Latency     3.12ms
  WebSockets      2`} />
      </section>

      <section className="mt-12">
        <h2 className={`text-2xl font-bold mb-4 pb-2 border-b ${isDark ? 'border-zinc-800/60 text-white' : 'border-gray-100 text-gray-900'}`}>
          Programmatic Interface
        </h2>
        <p className={`text-sm mb-4 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          The <DocTerm id="devplatform.ui">ADPTerminalUI</DocTerm> interface can be mounted manually on custom development server runners and linked to the <DocTerm id="devplatform.runtime_state_store">RuntimeStateStore</DocTerm>:
        </p>
        <CodeBlock 
          language="python" 
          highlightLines={[7, 13, 14, 17]}
          code={`from aquilia.devplatform.ui import ADPTerminalUI
from aquilia.devplatform.config import AquiliaDevelopmentConfig

config = AquiliaDevelopmentConfig()
runtime = server.get_runtime()

ui = ADPTerminalUI(
    config=config,
    runtime=runtime,
    mode="dev",
    on_reload=lambda: execute_reload(),
    on_quit=lambda: shutdown_server(),
)

ui.render_header()
ui.start()  # Launches background daemon thread
try:
    await dev_server.start(app)
finally:
    ui.stop()  # Cleanly shuts down keyboard listener`} 
        />
      </section>

      <section className="mt-12">
        <h2 className={`text-2xl font-bold mb-4 pb-2 border-b ${isDark ? 'border-zinc-800/60 text-white' : 'border-gray-100 text-gray-900'}`}>
          Interactive Terminals and TTY checks
        </h2>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          To ensure compatibility with CI pipelines, process managers (e.g. systemd), and containerized runs, 
          the <DocTerm id="devplatform.ui">ADPTerminalUI</DocTerm> verifies standard input state. If <code className="font-mono text-xs">sys.stdin.isatty()</code> returns 
          <code className="font-mono text-xs">False</code>, the daemon listener skips terminal controls. 
          Additionally, if <code className="font-mono text-xs">sys.stdout.isatty()</code> is false, 
          standard ANSI color escape sequences are bypassed to avoid logging raw escape strings.
        </p>
      </section>

      <section className="mt-16">
        <NextSteps items={[
          { text: 'Hot Reload', link: '/docs/devplatform/hot-reload' },
          { text: 'Diagnostics', link: '/docs/devplatform/diagnostics' },
        ]} />
      </section>
    </div>
  )
}
