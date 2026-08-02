import { motion } from 'framer-motion'

export function ADPRequestFlowDiagram({ isDark, className = "max-w-4xl" }: { isDark: boolean; className?: string }) {
  const stages = [

    { name: 'Bytes Ingress', type: 'TCP Connection', desc: 'StreamReader reads client chunks off the active socket transport.' },
    { name: 'H11Connection.run()', type: 'HTTP Protocol Parser', desc: 'h11 parses HTTP/1.1 structures, boundary marks, and chunk headers.' },
    { name: 'WS Upgrade Inspection', type: 'Protocol Handover', desc: 'Inspects upgrade headers to handoff connection to WebSocketConnection.' },
    { name: 'ADPProtocolHandler.__call__', type: 'ASGI Boundary', desc: 'Invoked by ASGI server context with raw scope parameters.' },
    { name: 'Trace Generation', type: 'TraceSpan Setup', desc: 'Constructs TraceSpan instance, generating request trace ID.' },
    { name: 'app(scope, recv, send)', type: 'App Execution', desc: 'Delegates request execution to Aquilia router middleware stack.' },
    { name: 'Metrics Commit', type: 'RequestRecord Build', desc: 'Compiles response code, diagnostics data, and database timings.' },
    { name: 'State Registry', type: 'State Store Log', desc: 'Commits RequestRecord to RuntimeStateStore, executing developer plugins.' },
  ]

  return (
    <div className={`w-full py-6 flex flex-col items-center bg-transparent ${className}`}>
      <div className="relative border-l-2 border-zinc-200 dark:border-zinc-800/80 ml-6 pl-8 space-y-6 w-full">
        {stages.map((stage, idx) => (
          <motion.div 
            key={idx} 
            className="relative group flex flex-col md:flex-row md:items-center justify-between p-4 rounded-xl border border-transparent hover:border-zinc-100 hover:dark:border-zinc-800/40 hover:bg-zinc-50/50 hover:dark:bg-zinc-900/10 transition-all duration-200"
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: idx * 0.05, duration: 0.2 }}
          >
            {/* Step indicator circle */}
            <div className={`absolute -left-12 top-4 w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold font-mono transition-transform duration-200 group-hover:scale-110 ${
              isDark ? 'bg-blue-500/10 text-blue-400 border border-blue-500/30' : 'bg-blue-50 text-blue-600 border border-blue-200'
            }`}>
              {idx + 1}
            </div>

            <div className="flex-1">
              <div className="flex items-baseline gap-3 flex-wrap">
                <span className={`font-mono font-bold text-sm ${isDark ? 'text-zinc-100' : 'text-zinc-900'}`}>{stage.name}</span>
                <span className={`text-[10px] uppercase tracking-wider font-semibold font-mono ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`}>{stage.type}</span>
              </div>
              <p className={`text-xs mt-1 leading-relaxed ${isDark ? 'text-zinc-400' : 'text-zinc-500'}`}>{stage.desc}</p>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
