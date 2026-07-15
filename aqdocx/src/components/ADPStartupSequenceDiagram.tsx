import { motion } from 'framer-motion'

export function ADPStartupSequenceDiagram({ isDark, className = "max-w-4xl" }: { isDark: boolean; className?: string }) {
  const steps = [

    { name: 'aq dev / aq run', type: 'CLI Entry', desc: 'CLI entry point parses terminal arguments and resolves workspace.py settings.' },
    { name: '_run_with_adp()', type: 'Config Instantiation', desc: 'Constructs the AquiliaDevelopmentConfig instance resolving Env and Secret keys.' },
    { name: 'ADPTerminalUI.start()', type: 'Keyboard UI Daemon', desc: 'Spawns the background input listener thread (adp-kb) for single-key command interceptors.' },
    { name: 'AquiliaDevelopmentServer.start()', type: 'Core Server Setup', desc: 'Main ASGI server runner begins binding socket acceptors and handlers.' },
    { name: '  ASGILifespanManager(app)', type: 'ASGI Lifespan wrapper', desc: 'Wraps application instance to capture asyncio startup/shutdown hooks.' },
    { name: '  ADPProtocolHandler(wrapped)', type: 'ASGI Dispatcher', desc: 'ASGI router wraps request contexts, WebSocket upgrades, and exceptions.' },
    { name: '  _start_telemetry()', type: 'Metrics loop', desc: 'Spawns memory diagnostics and CPU loop timers; registers state store.' },
    { name: '  _start_hot_reload()', type: 'Watcher setup', desc: 'Spawns WorkspaceWatcher file monitor loop (if watchfiles library is available).' },
    { name: '  asyncio.start_server()', type: 'TCP socket bind', desc: 'Binds socket listener to host:port, UDS paths, or inherited systemd file descriptors.' },
  ]

  return (
    <div className={`w-full py-6 flex flex-col items-center bg-transparent ${className}`}>
      <div className="relative border-l-2 border-zinc-200 dark:border-zinc-800/80 ml-6 pl-8 space-y-6 w-full">
        {steps.map((step, idx) => {
          const isIndent = step.name.startsWith('  ')
          const cleanName = step.name.trim()
          return (
            <motion.div 
              key={idx} 
              className={`relative group flex flex-col md:flex-row md:items-center justify-between p-4 rounded-xl border border-transparent hover:border-zinc-100 hover:dark:border-zinc-800/40 hover:bg-zinc-50/50 hover:dark:bg-zinc-900/10 transition-all duration-200 ${isIndent ? 'ml-6' : ''}`}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: idx * 0.05, duration: 0.2 }}
            >
              {/* Step indicator circle */}
              <div className={`absolute -left-12 top-4 w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold font-mono transition-transform duration-200 group-hover:scale-110 ${
                idx < 4 
                  ? (isDark ? 'bg-blue-500/10 text-blue-400 border border-blue-500/30' : 'bg-blue-50 text-blue-600 border border-blue-200')
                  : (isDark ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' : 'bg-emerald-50 text-emerald-600 border border-emerald-200')
              }`}>
                {idx + 1}
              </div>

              <div className="flex-1">
                <div className="flex items-baseline gap-3 flex-wrap">
                  <span className={`font-mono font-bold text-sm ${isDark ? 'text-zinc-100' : 'text-zinc-900'}`}>{cleanName}</span>
                  <span className={`text-[10px] uppercase tracking-wider font-semibold font-mono ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`}>{step.type}</span>
                </div>
                <p className={`text-xs mt-1 leading-relaxed ${isDark ? 'text-zinc-400' : 'text-zinc-500'}`}>{step.desc}</p>
              </div>
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}
