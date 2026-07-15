import { motion } from 'framer-motion'

export function ADPArchitectureDiagram({ isDark, className = "max-w-4xl" }: { isDark: boolean; className?: string }) {
  const accentColor = '#3b82f6' // Blue accent for ADP
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
          {/* Subtle Glow Filter */}
          <filter id="adp-glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="6" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>

          {/* Gradients */}
          <linearGradient id="blueGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.15" />
            <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0.03" />
          </linearGradient>
          <linearGradient id="greenGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#10b981" stopOpacity="0.15" />
            <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.03" />
          </linearGradient>
          <linearGradient id="amberGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.15" />
            <stop offset="100%" stopColor="#ef4444" stopOpacity="0.03" />
          </linearGradient>

          {/* Arrow markers */}
          <marker id="adp-arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
            <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill={isDark ? "#52525b" : "#a1a1aa"} />
          </marker>
        </defs>

        {/* Faint Background Grid Pattern */}
        <g stroke={gridColor} strokeWidth="1">
          {Array.from({ length: 10 }).map((_, i) => (
            <line key={`v-${i}`} x1={i * 100} y1="0" x2={i * 100} y2="650" />
          ))}
          {Array.from({ length: 7 }).map((_, i) => (
            <line key={`h-${i}`} x1="0" y1={i * 100} x2="900" y2={i * 100} />
          ))}
        </g>

        {/* ─── CONNECTION FLOW PATHS (Curved Beziers) ─── */}
        <g fill="none" strokeWidth="1.5" stroke={isDark ? "#27272a" : "#e4e4e7"} markerEnd="url(#adp-arrow)">
          {/* Socket -> H11 Transport */}
          <path d="M 120 180 C 180 180, 200 180, 240 180" />
          {/* Keyboard -> Terminal UI */}
          <path d="M 120 480 C 180 480, 200 480, 240 480" />
          {/* H11 Transport -> Protocol Handler */}
          <path d="M 370 180 C 400 180, 420 220, 450 250" />
          {/* Terminal UI -> Config / Server control */}
          <path d="M 370 480 C 400 480, 420 440, 450 410" />
          {/* Protocol Handler -> Lifespan Manager */}
          <path d="M 570 280 V 340" />
          {/* Lifespan Manager -> Aquilia Application */}
          <path d="M 570 400 V 460" />
          {/* Hot Reload -> Aquilia Application */}
          <path d="M 720 180 C 650 180, 600 300, 580 440" strokeDasharray="4,4" />
          {/* Protocol Handler -> State Store */}
          <path d="M 570 260 C 650 260, 700 280, 720 300" />
          {/* Diagnostics -> State Store */}
          <path d="M 720 480 C 680 480, 680 340, 720 340" />
        </g>

        {/* Dynamic moving pulses */}
        <motion.circle r="3.5" fill={accentColor} filter="url(#adp-glow)"
          animate={{
            cx: [240, 450],
            cy: [180, 250],
          }}
          transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
        />
        <motion.circle r="3.5" fill={successColor} filter="url(#adp-glow)"
          animate={{
            cx: [570, 570],
            cy: [400, 460],
          }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
        />

        {/* ─── NODE GROUPS (Using clean rounded outlines and soft glows) ─── */}

        {/* Left Column: Entry Interfaces */}
        <g transform="translate(10, 130)">
          {/* TCP / UDS Socket Node */}
          <rect x="0" y="0" width="130" height="90" rx="20" fill="url(#blueGrad)" stroke={accentColor} strokeWidth="1" />
          <text x="65" y="32" textAnchor="middle" fill={textColor} fontSize="12" fontWeight="bold" className="font-mono">NETWORK</text>
          <text x="65" y="50" textAnchor="middle" fill={accentColor} fontSize="10" fontWeight="bold">TCP / UDS Socket</text>
          <text x="65" y="65" textAnchor="middle" fill={mutedColor} fontSize="9">h11 Acceptor</text>
        </g>

        <g transform="translate(10, 430)">
          {/* Keyboard Daemon Node */}
          <rect x="0" y="0" width="130" height="90" rx="20" fill="url(#amberGrad)" stroke={warningColor} strokeWidth="1" />
          <text x="65" y="32" textAnchor="middle" fill={textColor} fontSize="12" fontWeight="bold" className="font-mono">TTY CONSOLE</text>
          <text x="65" y="50" textAnchor="middle" fill={warningColor} fontSize="10" fontWeight="bold">Keyboard Thread</text>
          <text x="65" y="65" textAnchor="middle" fill={mutedColor} fontSize="9">termios / cbreak</text>
        </g>

        {/* Middle Column: Transport & Protocol Bridge */}
        <g transform="translate(220, 135)">
          {/* H11 Transport Layer */}
          <rect x="0" y="0" width="170" height="90" rx="20" fill="url(#blueGrad)" stroke={accentColor} strokeWidth="1.5" />
          <text x="85" y="32" textAnchor="middle" fill={textColor} fontSize="12" fontWeight="bold" className="font-mono">H11Connection</text>
          <text x="85" y="50" textAnchor="middle" fill={mutedColor} fontSize="9.5">HTTP/1.1 Parser</text>
          <text x="85" y="66" textAnchor="middle" fill={accentColor} fontSize="9" fontWeight="medium">Keep-Alive & Chunked</text>
        </g>

        <g transform="translate(220, 435)">
          {/* Terminal Keyboard UI */}
          <rect x="0" y="0" width="170" height="90" rx="20" fill="url(#amberGrad)" stroke={warningColor} strokeWidth="1.5" />
          <text x="85" y="32" textAnchor="middle" fill={textColor} fontSize="12" fontWeight="bold" className="font-mono">ADPTerminalUI</text>
          <text x="85" y="50" textAnchor="middle" fill={mutedColor} fontSize="9.5">Interactive CLI Banner</text>
          <text x="85" y="66" textAnchor="middle" fill={warningColor} fontSize="9" fontWeight="medium">Keys: R / C / P / M / Q</text>
        </g>

        {/* Center Kernel Stack */}
        <g transform="translate(450, 230)">
          {/* Protocol Dispatch Handler */}
          <rect x="0" y="0" width="240" height="70" rx="16" fill="url(#blueGrad)" stroke={accentColor} strokeWidth="2" filter="url(#adp-glow)" />
          <text x="120" y="28" textAnchor="middle" fill={textColor} fontSize="12" fontWeight="extrabold" className="font-mono">ADPProtocolHandler</text>
          <text x="120" y="46" textAnchor="middle" fill={mutedColor} fontSize="9.5">ASGI Dispatcher (lifespan/http/ws)</text>
          <text x="120" y="58" textAnchor="middle" fill={accentColor} fontSize="8.5" fontWeight="bold">Generates trace_id & measures duration</text>
        </g>

        <g transform="translate(450, 320)">
          {/* Lifespan Orchestrator */}
          <rect x="0" y="0" width="240" height="80" rx="16" fill="url(#greenGrad)" stroke={successColor} strokeWidth="1.5" />
          <text x="120" y="32" textAnchor="middle" fill={textColor} fontSize="12" fontWeight="bold" className="font-mono">ASGILifespanManager</text>
          <text x="120" y="50" textAnchor="middle" fill={mutedColor} fontSize="9.5">Intercepts lifespan.startup / shutdown</text>
          <text x="120" y="64" textAnchor="middle" fill={successColor} fontSize="8.5" fontWeight="bold">Triggers _adp_startup() telemetry</text>
        </g>

        <g transform="translate(450, 460)">
          {/* Aquilia Server Application */}
          <rect x="0" y="0" width="240" height="90" rx="24" fill={isDark ? "rgba(16, 185, 129, 0.05)" : "rgba(16, 185, 129, 0.01)"} stroke={successColor} strokeWidth="2.5" />
          <text x="120" y="35" textAnchor="middle" fill={textColor} fontSize="13" fontWeight="black" className="font-mono">Aquilia App</text>
          <text x="120" y="55" textAnchor="middle" fill={mutedColor} fontSize="9.5">Your Workspace Application</text>
          <text x="120" y="70" textAnchor="middle" fill={successColor} fontSize="9" fontWeight="bold">Controllers & DI Containers</text>
        </g>

        {/* Right Column: Observers, reloaders & stats */}
        <g transform="translate(710, 135)">
          {/* Workspace Watcher */}
          <rect x="0" y="0" width="180" height="90" rx="20" fill="url(#blueGrad)" stroke={accentColor} strokeWidth="1" strokeDasharray="4,2" />
          <text x="90" y="30" textAnchor="middle" fill={textColor} fontSize="11.5" fontWeight="bold" className="font-mono">WorkspaceWatcher</text>
          <text x="90" y="48" textAnchor="middle" fill={accentColor} fontSize="9.5" fontWeight="bold">Hot Reload Watcher</text>
          <text x="90" y="64" textAnchor="middle" fill={mutedColor} fontSize="9">AST Dependency Graph</text>
          <text x="90" y="76" textAnchor="middle" fill={mutedColor} fontSize="8">Topological Module Reload</text>
        </g>

        <g transform="translate(710, 275)">
          {/* State Store Singleton */}
          <rect x="0" y="0" width="180" height="95" rx="20" fill="url(#blueGrad)" stroke={accentColor} strokeWidth="2" filter="url(#adp-glow)" />
          <text x="90" y="30" textAnchor="middle" fill={textColor} fontSize="12" fontWeight="black" className="font-mono">RuntimeStateStore</text>
          <text x="90" y="48" textAnchor="middle" fill={accentColor} fontSize="10" fontWeight="bold">Thread-Safe Singleton</text>
          <text x="90" y="64" textAnchor="middle" fill={mutedColor} fontSize="9">Circular history (deque)</text>
          <text x="90" y="76" textAnchor="middle" fill={mutedColor} fontSize="8.5">Metrics snapshot, RPS & EMA</text>
        </g>

        <g transform="translate(710, 415)">
          {/* Observers & Diagnostics */}
          <rect x="0" y="0" width="180" height="135" rx="20" fill="url(#greenGrad)" stroke={successColor} strokeWidth="1" />
          <text x="90" y="28" textAnchor="middle" fill={textColor} fontSize="11" fontWeight="bold" className="font-mono">DIAGNOSTICS</text>
          <path d="M 20 40 H 160" stroke={gridColor} strokeWidth="1" />
          
          <text x="15" y="58" fill={textColor} fontSize="9.5" fontWeight="bold">1. SQL Query Analyzer</text>
          <text x="15" y="70" fill={mutedColor} fontSize="8.5">   N+1 queries & explain plan</text>
          
          <text x="15" y="90" fill={textColor} fontSize="9.5" fontWeight="bold">2. Memory Tracker</text>
          <text x="15" y="102" fill={mutedColor} fontSize="8.5">   tracemalloc snapshots</text>
          
          <text x="15" y="122" fill={textColor} fontSize="9.5" fontWeight="bold">3. Event-Loop Monitor</text>
        </g>
      </svg>
    </div>
  )
}
