export function ADPStartupSequenceSVG({ isDark, className = "max-w-4xl" }: { isDark: boolean; className?: string }) {
  const accentColor = '#3b82f6'
  const successColor = '#10b981'
  const textColor = isDark ? '#f4f4f5' : '#18181b'
  const mutedColor = isDark ? '#a1a1aa' : '#71717a'
  const gridColor = isDark ? 'rgba(255, 255, 255, 0.03)' : 'rgba(0, 0, 0, 0.02)'

  return (
    <div className="w-full overflow-hidden py-8 flex justify-center bg-transparent">
      <svg viewBox="0 0 950 620" className={`w-full h-auto ${className}`}>
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
          <filter id="adp-startup-glow-new" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>

          <linearGradient id="blueGrad-start" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.12" />
            <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.02" />
          </linearGradient>
          <linearGradient id="emeraldGrad-start" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#10b981" stopOpacity="0.12" />
            <stop offset="100%" stopColor="#10b981" stopOpacity="0.02" />
          </linearGradient>

          <marker id="start-arrow-new" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill={isDark ? "#71717a" : "#a1a1aa"} />
          </marker>
        </defs>

        {/* Grid backgrounds */}
        <g stroke={gridColor} strokeWidth="1">
          {Array.from({ length: 10 }).map((_, i) => (
            <line key={`v-${i}`} x1={i * 100} y1="0" x2={i * 100} y2="620" />
          ))}
          {Array.from({ length: 7 }).map((_, i) => (
            <line key={`h-${i}`} x1="0" y1={i * 100} x2="950" y2={i * 100} />
          ))}
        </g>

        {/* ─── FLOW CONNECTOR PATHS ─── */}
        <g fill="none" strokeWidth="1.5" stroke={isDark ? "#3f3f46" : "#d4d4d8"} markerEnd="url(#start-arrow-new)">
          {/* 1. CLI -> 2. Config */}
          <path d="M 230 95 H 370" />
          {/* 2. Config -> 3. UI Daemon */}
          <path d="M 580 95 C 640 95, 680 110, 715 140" />
          {/* 2. Config -> 4. Server start */}
          <path d="M 480 130 V 170" />

          {/* 4. Server start -> 5. Lifespan */}
          <path d="M 380 205 C 310 205, 270 210, 235 240" />
          {/* 5. Lifespan -> 6. Protocol */}
          <path d="M 140 295 V 360" />

          {/* 4. Server start -> 7. Telemetry */}
          <path d="M 580 205 C 650 205, 690 210, 725 240" />
          {/* 7. Telemetry -> 8. Watcher */}
          <path d="M 830 295 V 360" />

          {/* 6. Protocol -> 9. Bind */}
          <path d="M 240 395 C 290 395, 340 430, 370 470" />
          {/* 8. Watcher -> 9. Bind */}
          <path d="M 720 395 C 670 395, 620 430, 590 470" />
        </g>

        {/* ─── PROCESS BUBBLES ─── */}

        {/* 1. CLI Entry */}
        <g transform="translate(30, 60)">
          <rect x="0" y="0" width="200" height="70" rx="16" fill="url(#blueGrad-start)" stroke={accentColor} strokeWidth="1" />
          <circle cx="20" cy="20" r="10" fill={accentColor} fillOpacity="0.2" />
          <text x="20" y="23" textAnchor="middle" fill={textColor} fontSize="8" fontWeight="bold">1</text>
          <text x="40" y="24" fill={textColor} fontSize="11" fontWeight="bold" className="font-mono">aq dev / aq run</text>
          <text x="40" y="42" fill={mutedColor} fontSize="8.5">CLI environment parsing</text>
          <text x="40" y="52" fill={mutedColor} fontSize="8.5">resolves workspace settings</text>
        </g>

        {/* 2. Config resolver */}
        <g transform="translate(370, 60)">
          <rect x="0" y="0" width="210" height="70" rx="16" fill="url(#blueGrad-start)" stroke={accentColor} strokeWidth="1.5" />
          <circle cx="20" cy="20" r="10" fill={accentColor} fillOpacity="0.2" />
          <text x="20" y="23" textAnchor="middle" fill={textColor} fontSize="8" fontWeight="bold">2</text>
          <text x="40" y="24" fill={textColor} fontSize="11" fontWeight="bold" className="font-mono">_run_with_adp()</text>
          <text x="40" y="42" fill={mutedColor} fontSize="8.5">Constructs development config</text>
          <text x="40" y="52" fill={mutedColor} fontSize="8.5">validates keys & secrets</text>
        </g>

        {/* 3. Terminal UI Daemon (Y shifted to 140 to avoid overlap) */}
        <g transform="translate(710, 125)">
          <rect x="0" y="0" width="200" height="70" rx="16" fill="url(#blueGrad-start)" stroke={accentColor} strokeWidth="1" />
          <circle cx="20" cy="20" r="10" fill={accentColor} fillOpacity="0.2" />
          <text x="20" y="23" textAnchor="middle" fill={textColor} fontSize="8" fontWeight="bold">3</text>
          <text x="40" y="24" fill={textColor} fontSize="11" fontWeight="bold" className="font-mono">ADPTerminalUI.start()</text>
          <text x="40" y="42" fill={mutedColor} fontSize="8.5">Spawns adp-kb daemon thread</text>
          <text x="40" y="52" fill={mutedColor} fontSize="8.5">for hotkey intercepts</text>
        </g>

        {/* 4. Core Server Execution */}
        <g transform="translate(370, 170)">
          <rect x="0" y="0" width="210" height="70" rx="18" fill="url(#blueGrad-start)" stroke={accentColor} strokeWidth="2" filter="url(#adp-startup-glow-new)" />
          <circle cx="20" cy="20" r="10" fill={accentColor} fillOpacity="0.2" />
          <text x="20" y="23" textAnchor="middle" fill={textColor} fontSize="8" fontWeight="bold">4</text>
          <text x="40" y="24" fill={textColor} fontSize="11" fontWeight="black" className="font-mono">Server.start(app)</text>
          <text x="40" y="42" fill={accentColor} fontSize="8.5" fontWeight="bold">Initializes server run context</text>
          <text x="40" y="52" fill={mutedColor} fontSize="8.5">mounts socket acceptor loops</text>
        </g>

        {/* 5. Lifespan wrapping */}
        <g transform="translate(40, 225)">
          <rect x="0" y="0" width="200" height="70" rx="16" fill="url(#emeraldGrad-start)" stroke={successColor} strokeWidth="1.5" />
          <circle cx="20" cy="20" r="10" fill={successColor} fillOpacity="0.2" />
          <text x="20" y="23" textAnchor="middle" fill={textColor} fontSize="8" fontWeight="bold">5</text>
          <text x="40" y="24" fill={textColor} fontSize="11" fontWeight="bold" className="font-mono">ASGILifespanManager</text>
          <text x="40" y="42" fill={mutedColor} fontSize="8.5">Wraps app target to capture</text>
          <text x="40" y="52" fill={mutedColor} fontSize="8.5">asyncio lifespan signals</text>
        </g>

        {/* 6. Protocol boundary handler */}
        <g transform="translate(40, 360)">
          <rect x="0" y="0" width="200" height="70" rx="16" fill="url(#emeraldGrad-start)" stroke={successColor} strokeWidth="1.5" />
          <circle cx="20" cy="20" r="10" fill={successColor} fillOpacity="0.2" />
          <text x="20" y="23" textAnchor="middle" fill={textColor} fontSize="8" fontWeight="bold">6</text>
          <text x="40" y="24" fill={textColor} fontSize="11" fontWeight="bold" className="font-mono">ADPProtocolHandler</text>
          <text x="40" y="42" fill={mutedColor} fontSize="8.5">Dispatcher wraps WS upgrades</text>
          <text x="40" y="52" fill={mutedColor} fontSize="8.5">HTTP endpoints & exceptions</text>
        </g>

        {/* 7. Background telemetry (Y shifted to 225 to avoid overlap) */}
        <g transform="translate(720, 225)">
          <rect x="0" y="0" width="190" height="70" rx="16" fill="url(#emeraldGrad-start)" stroke={successColor} strokeWidth="1.5" />
          <circle cx="20" cy="20" r="10" fill={successColor} fillOpacity="0.2" />
          <text x="20" y="23" textAnchor="middle" fill={textColor} fontSize="8" fontWeight="bold">7</text>
          <text x="40" y="24" fill={textColor} fontSize="11" fontWeight="bold" className="font-mono">_start_telemetry()</text>
          <text x="40" y="42" fill={mutedColor} fontSize="8.5">Spawns diagnostic tasks</text>
          <text x="40" y="52" fill={mutedColor} fontSize="8.5">event loop & memory trackers</text>
        </g>

        {/* 8. Hot reload setup */}
        <g transform="translate(720, 360)">
          <rect x="0" y="0" width="190" height="70" rx="16" fill="url(#emeraldGrad-start)" stroke={successColor} strokeWidth="1.5" />
          <circle cx="20" cy="20" r="10" fill={successColor} fillOpacity="0.2" />
          <text x="20" y="23" textAnchor="middle" fill={textColor} fontSize="8" fontWeight="bold">8</text>
          <text x="40" y="24" fill={textColor} fontSize="11" fontWeight="bold" className="font-mono">_start_hot_reload()</text>
          <text x="40" y="42" fill={mutedColor} fontSize="8.5">Loads WorkspaceWatcher loop</text>
          <text x="40" y="52" fill={mutedColor} fontSize="8.5">monitors filesystem updates</text>
        </g>

        {/* 9. Socket binding */}
        <g transform="translate(375, 470)">
          <rect x="0" y="0" width="200" height="70" rx="18" fill="url(#blueGrad-start)" stroke={accentColor} strokeWidth="2" filter="url(#adp-startup-glow-new)" />
          <circle cx="20" cy="20" r="10" fill={accentColor} fillOpacity="0.2" />
          <text x="20" y="23" textAnchor="middle" fill={textColor} fontSize="8" fontWeight="bold">9</text>
          <text x="40" y="24" fill={textColor} fontSize="11" fontWeight="black" className="font-mono">asyncio.start_server</text>
          <text x="40" y="42" fill={accentColor} fontSize="8.5" fontWeight="bold">Binds network port interface</text>
          <text x="40" y="52" fill={mutedColor} fontSize="8.5">defaults to http://127.0.0.1:8000</text>
        </g>
      </svg>
    </div>
  )
}
