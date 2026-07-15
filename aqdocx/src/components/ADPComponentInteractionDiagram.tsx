export function ADPComponentInteractionDiagram({ isDark, className = "max-w-4xl" }: { isDark: boolean; className?: string }) {
  const accentColor = '#3b82f6' // Blue
  const successColor = '#10b981' // Emerald
  const warningColor = '#f59e0b' // Amber
  const textColor = isDark ? '#f4f4f5' : '#18181b'
  const mutedColor = isDark ? '#a1a1aa' : '#71717a'
  const gridColor = isDark ? 'rgba(255, 255, 255, 0.03)' : 'rgba(0, 0, 0, 0.02)'


  return (
    <div className="w-full overflow-hidden py-8 flex justify-center bg-transparent">
      <svg viewBox="0 0 900 650" className={`w-full h-auto ${className}`}>
        <style>{`
          @media print {
            text {
              fill: #111111 !important;
            }
            rect {
              fill: #ffffff !important;
              stroke: #111111 !important;
              filter: none !important;
            }
            path {
              stroke: #333333 !important;
              filter: none !important;
            }
            circle {
              fill: #eeeeee !important;
              stroke: #333333 !important;
            }
            line {
              stroke: #dddddd !important;
            }
          }
        `}</style>
        <defs>
          <filter id="diagram-glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="5" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>

          <linearGradient id="blueG" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.12" />
            <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.02" />
          </linearGradient>
          <linearGradient id="emeraldG" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#10b981" stopOpacity="0.12" />
            <stop offset="100%" stopColor="#10b981" stopOpacity="0.02" />
          </linearGradient>
          <linearGradient id="amberG" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.12" />
            <stop offset="100%" stopColor="#f59e0b" stopOpacity="0.02" />
          </linearGradient>

          <marker id="adp-arrow-marker" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill={isDark ? "#71717a" : "#a1a1aa"} />
          </marker>
        </defs>

        <g stroke={gridColor} strokeWidth="1">
          {Array.from({ length: 9 }).map((_, i) => (
            <line key={`v-${i}`} x1={i * 100} y1="0" x2={i * 100} y2="650" />
          ))}
          {Array.from({ length: 7 }).map((_, i) => (
            <line key={`h-${i}`} x1="0" y1={i * 100} x2="900" y2={i * 100} />
          ))}
        </g>

        {/* ─── CONNECTORS ─── */}
        <g fill="none" strokeWidth="1.5" stroke={isDark ? "#3f3f46" : "#d4d4d8"} markerEnd="url(#adp-arrow-marker)">
          {/* Client -> Protocol */}
          <path d="M 175 125 C 175 160, 175 160, 220 185" />
          {/* Protocol -> App */}
          <path d="M 315 210 C 370 210, 390 210, 440 210" />
          
          {/* App -> SQL, DI, Prof */}
          <path d="M 570 210 C 620 210, 600 290, 310 320" /> {/* App -> SQL */}
          <path d="M 570 210 C 650 210, 650 290, 520 320" /> {/* App -> DI */}
          <path d="M 570 210 C 680 210, 680 290, 715 320" /> {/* App -> Prof */}

          {/* Diagnostics -> Inspector */}
          <path d="M 270 375 C 270 430, 420 440, 440 480" />
          <path d="M 490 375 C 490 430, 490 440, 490 470" />
          <path d="M 710 375 C 710 430, 560 440, 540 480" />

          {/* Protocol -> Inspector */}
          <path d="M 230 235 C 230 330, 300 460, 430 500" strokeDasharray="3,3" />

          {/* Watcher -> Reload -> Preserve -> App */}
          <path d="M 780 125 C 780 150, 640 150, 600 150" />
          <path d="M 470 150 C 440 150, 440 180, 480 190" />
          <path d="M 570 190 C 590 190, 590 170, 570 160" />

          {/* Runtime/State -> Inspector */}
          <path d="M 285 530 C 340 530, 380 530, 420 520" />
          <path d="M 695 530 C 640 530, 600 530, 560 520" />
        </g>

        {/* ─── NODES ─── */}

        {/* Input Trigger Block */}
        <g transform="translate(90, 50)">
          <rect x="0" y="0" width="170" height="75" rx="16" fill="url(#blueG)" stroke={accentColor} strokeWidth="1" />
          <text x="85" y="30" textAnchor="middle" fill={textColor} fontSize="12" fontWeight="bold" className="font-mono">Client Socket</text>
          <text x="85" y="48" textAnchor="middle" fill={mutedColor} fontSize="9">ASGI HTTP/WS Streams</text>
        </g>

        {/* Watcher File System */}
        <g transform="translate(685, 50)">
          <rect x="0" y="0" width="190" height="75" rx="16" fill="url(#amberG)" stroke={warningColor} strokeWidth="1" />
          <text x="95" y="30" textAnchor="middle" fill={textColor} fontSize="12" fontWeight="bold" className="font-mono">watcher.py</text>
          <text x="95" y="48" textAnchor="middle" fill={mutedColor} fontSize="9">Debounced FS File Saves</text>
        </g>

        {/* Protocol Module */}
        <g transform="translate(140, 175)">
          <rect x="0" y="0" width="175" height="70" rx="16" fill="url(#blueG)" stroke={accentColor} strokeWidth="1.5" />
          <text x="87.5" y="30" textAnchor="middle" fill={textColor} fontSize="12" fontWeight="bold" className="font-mono">protocol.py</text>
          <text x="87.5" y="46" textAnchor="middle" fill={mutedColor} fontSize="9">ADPProtocolHandler</text>
        </g>

        {/* Reload Module */}
        <g transform="translate(470, 115)">
          <rect x="0" y="0" width="190" height="60" rx="16" fill="url(#amberG)" stroke={warningColor} strokeWidth="1.5" />
          <text x="95" y="28" textAnchor="middle" fill={textColor} fontSize="11" fontWeight="bold" className="font-mono">reload/executor.py</text>
          <text x="95" y="44" textAnchor="middle" fill={mutedColor} fontSize="9">Topological Module Reload</text>
        </g>

        {/* Aquilia Core App Container */}
        <g transform="translate(440, 185)">
          <rect x="0" y="0" width="220" height="75" rx="20" fill={isDark ? "rgba(16, 185, 129, 0.05)" : "rgba(16, 185, 129, 0.01)"} stroke={successColor} strokeWidth="2.5" filter="url(#diagram-glow)" />
          <text x="110" y="32" textAnchor="middle" fill={textColor} fontSize="13" fontWeight="black" className="font-mono">Aquilia Application</text>
          <text x="110" y="50" textAnchor="middle" fill={successColor} fontSize="10" fontWeight="bold">ASGILifespan / Controllers</text>
        </g>

        {/* Diagnostic Stack */}
        <g transform="translate(170, 315)">
          <rect x="0" y="0" width="180" height="60" rx="14" fill="url(#emeraldG)" stroke={successColor} strokeWidth="1" />
          <text x="90" y="28" textAnchor="middle" fill={textColor} fontSize="11" fontWeight="bold" className="font-mono">diagnostics/sql.py</text>
          <text x="90" y="42" textAnchor="middle" fill={mutedColor} fontSize="8.5">N+1 Queries Accumulator</text>
        </g>

        <g transform="translate(400, 315)">
          <rect x="0" y="0" width="180" height="60" rx="14" fill="url(#emeraldG)" stroke={successColor} strokeWidth="1" />
          <text x="90" y="28" textAnchor="middle" fill={textColor} fontSize="11" fontWeight="bold" className="font-mono">di_listener.py</text>
          <text x="90" y="42" textAnchor="middle" fill={mutedColor} fontSize="8.5">DI Resolver Events</text>
        </g>

        <g transform="translate(620, 315)">
          <rect x="0" y="0" width="180" height="60" rx="14" fill="url(#emeraldG)" stroke={successColor} strokeWidth="1" />
          <text x="90" y="28" textAnchor="middle" fill={textColor} fontSize="11" fontWeight="bold" className="font-mono">profiler/engine.py</text>
          <text x="90" y="42" textAnchor="middle" fill={mutedColor} fontSize="8.5">cProfile Execution Timer</text>
        </g>

        {/* Data Singleton Providers */}
        <g transform="translate(125, 495)">
          <rect x="0" y="0" width="160" height="65" rx="14" fill="url(#blueG)" stroke={accentColor} strokeWidth="1" />
          <text x="80" y="28" textAnchor="middle" fill={textColor} fontSize="11" fontWeight="bold" className="font-mono">runtime.py</text>
          <text x="80" y="44" textAnchor="middle" fill={mutedColor} fontSize="8.5">RuntimeStateStore</text>
        </g>

        <g transform="translate(695, 495)">
          <rect x="0" y="0" width="160" height="65" rx="14" fill="url(#blueG)" stroke={accentColor} strokeWidth="1" />
          <text x="80" y="28" textAnchor="middle" fill={textColor} fontSize="11" fontWeight="bold" className="font-mono">state.py</text>
          <text x="80" y="44" textAnchor="middle" fill={mutedColor} fontSize="8.5">RequestRecord Telemetry</text>
        </g>

        {/* Target Inspector Panel */}
        <g transform="translate(390, 480)">
          <rect x="0" y="0" width="200" height="85" rx="20" fill="url(#blueG)" stroke={accentColor} strokeWidth="2.5" filter="url(#diagram-glow)" />
          <text x="100" y="35" textAnchor="middle" fill={textColor} fontSize="13" fontWeight="black" className="font-mono">aquilia/inspector</text>
          <text x="100" y="52" textAnchor="middle" fill={accentColor} fontSize="9.5" fontWeight="bold">Central Dashboard Lane</text>
          <text x="100" y="66" textAnchor="middle" fill={mutedColor} fontSize="8.5">Traces, SQLs & Exception Graphs</text>
        </g>
      </svg>
    </div>
  )
}
