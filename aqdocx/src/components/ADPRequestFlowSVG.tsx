export function ADPRequestFlowSVG({ isDark, className = "max-w-4xl" }: { isDark: boolean; className?: string }) {
  const accentColor = '#3b82f6'
  const successColor = '#10b981'
  const textColor = isDark ? '#f4f4f5' : '#18181b'
  const mutedColor = isDark ? '#a1a1aa' : '#71717a'
  const gridColor = isDark ? 'rgba(255, 255, 255, 0.03)' : 'rgba(0, 0, 0, 0.02)'

  return (
    <div className="w-full overflow-hidden py-8 flex justify-center bg-transparent">
      <svg viewBox="0 0 950 520" className={`w-full h-auto ${className}`}>
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
          <filter id="adp-request-glow-new" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>

          <linearGradient id="blueGrad-req" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.12" />
            <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.02" />
          </linearGradient>
          <linearGradient id="emeraldGrad-req" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#10b981" stopOpacity="0.12" />
            <stop offset="100%" stopColor="#10b981" stopOpacity="0.02" />
          </linearGradient>

          <marker id="req-arrow-new" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill={isDark ? "#71717a" : "#a1a1aa"} />
          </marker>
        </defs>

        {/* Grid backgrounds */}
        <g stroke={gridColor} strokeWidth="1">
          {Array.from({ length: 10 }).map((_, i) => (
            <line key={`v-${i}`} x1={i * 100} y1="0" x2={i * 100} y2="520" />
          ))}
          {Array.from({ length: 6 }).map((_, i) => (
            <line key={`h-${i}`} x1="0" y1={i * 100} x2="950" y2={i * 100} />
          ))}
        </g>

        {/* ─── FLOW CONNECTOR PATHS (S-Shape Grid) ─── */}
        <g fill="none" strokeWidth="1.5" stroke={isDark ? "#3f3f46" : "#d4d4d8"} markerEnd="url(#req-arrow-new)">
          {/* Lane 1: Left to Right */}
          <path d="M 230 95 H 370" /> {/* 1 -> 2 */}
          <path d="M 580 95 H 700" /> {/* 2 -> 3 */}

          {/* Lane 1 to Lane 2: Down on Right side */}
          <path d="M 800 130 V 220" /> {/* 3 -> 4 */}

          {/* Lane 2: Right to Left */}
          <path d="M 700 255 H 580" /> {/* 4 -> 5 */}
          <path d="M 370 255 H 240" /> {/* 5 -> 6 */}

          {/* Lane 2 to Lane 3: Down on Left side */}
          <path d="M 140 290 V 380" /> {/* 6 -> 7 */}

          {/* Lane 3: Left to Right */}
          <path d="M 240 415 H 370" /> {/* 7 -> 8 */}
          <path d="M 580 415 H 700" /> {/* 8 -> 9 */}
        </g>

        {/* ─── SWIMLANES ─── */}

        {/* --- LANE 1: Network Ingress (Y=60) --- */}
        {/* 1. Bytes Ingress */}
        <g transform="translate(30, 60)">
          <rect x="0" y="0" width="200" height="70" rx="16" fill="url(#blueGrad-req)" stroke={accentColor} strokeWidth="1" />
          <circle cx="20" cy="20" r="10" fill={accentColor} fillOpacity="0.2" />
          <text x="20" y="23" textAnchor="middle" fill={textColor} fontSize="8" fontWeight="bold">1</text>
          <text x="40" y="24" fill={textColor} fontSize="11" fontWeight="bold" className="font-mono">Bytes Ingress</text>
          <text x="40" y="42" fill={mutedColor} fontSize="8.5">StreamReader socket reads</text>
          <text x="40" y="52" fill={mutedColor} fontSize="8.5">chunks incoming TCP stream</text>
        </g>

        {/* 2. H11 Parser */}
        <g transform="translate(370, 60)">
          <rect x="0" y="0" width="210" height="70" rx="16" fill="url(#blueGrad-req)" stroke={accentColor} strokeWidth="1" />
          <circle cx="20" cy="20" r="10" fill={accentColor} fillOpacity="0.2" />
          <text x="20" y="23" textAnchor="middle" fill={textColor} fontSize="8" fontWeight="bold">2</text>
          <text x="40" y="24" fill={textColor} fontSize="11" fontWeight="bold" className="font-mono">H11Connection.run()</text>
          <text x="40" y="42" fill={mutedColor} fontSize="8.5">h11 engine parses protocol</text>
          <text x="40" y="52" fill={mutedColor} fontSize="8.5">keeps HTTP keep-alives open</text>
        </g>

        {/* 3. WS Upgrade check */}
        <g transform="translate(700, 60)">
          <rect x="0" y="0" width="200" height="70" rx="16" fill="url(#blueGrad-req)" stroke={accentColor} strokeWidth="1.5" />
          <circle cx="20" cy="20" r="10" fill={accentColor} fillOpacity="0.2" />
          <text x="20" y="23" textAnchor="middle" fill={textColor} fontSize="8" fontWeight="bold">3</text>
          <text x="40" y="24" fill={textColor} fontSize="11" fontWeight="bold" className="font-mono">WS Upgrade Check</text>
          <text x="40" y="42" fill={mutedColor} fontSize="8.5">Handoff socket control to</text>
          <text x="40" y="52" fill={mutedColor} fontSize="8.5">WebSocketConnection wrapper</text>
        </g>

        {/* --- LANE 2: ASGI Context (Y=220) --- */}
        {/* 4. Protocol handler dispatcher */}
        <g transform="translate(700, 220)">
          <rect x="0" y="0" width="200" height="70" rx="16" fill="url(#blueGrad-req)" stroke={accentColor} strokeWidth="1.5" />
          <circle cx="20" cy="20" r="10" fill={accentColor} fillOpacity="0.2" />
          <text x="20" y="23" textAnchor="middle" fill={textColor} fontSize="8" fontWeight="bold">4</text>
          <text x="40" y="24" fill={textColor} fontSize="11" fontWeight="black" className="font-mono">ProtocolHandler</text>
          <text x="40" y="42" fill={accentColor} fontSize="8.5" fontWeight="bold">ASGI entrypoint __call__</text>
          <text x="40" y="52" fill={mutedColor} fontSize="8.5">resolves route path parameters</text>
        </g>

        {/* 5. Trace span generation */}
        <g transform="translate(370, 220)">
          <rect x="0" y="0" width="210" height="70" rx="16" fill="url(#emeraldGrad-req)" stroke={successColor} strokeWidth="1.5" />
          <circle cx="20" cy="20" r="10" fill={successColor} fillOpacity="0.2" />
          <text x="20" y="23" textAnchor="middle" fill={textColor} fontSize="8" fontWeight="bold">5</text>
          <text x="40" y="24" fill={textColor} fontSize="11" fontWeight="bold" className="font-mono">Trace Generation</text>
          <text x="40" y="42" fill={mutedColor} fontSize="8.5">Creates TraceSpan instance</text>
          <text x="40" y="52" fill={mutedColor} fontSize="8.5">binds thread contexts</text>
        </g>

        {/* 6. Execution router stack */}
        <g transform="translate(40, 220)">
          <rect x="0" y="0" width="200" height="70" rx="16" fill="url(#emeraldGrad-req)" stroke={successColor} strokeWidth="1.5" />
          <circle cx="20" cy="20" r="10" fill={successColor} fillOpacity="0.2" />
          <text x="20" y="23" textAnchor="middle" fill={textColor} fontSize="8" fontWeight="bold">6</text>
          <text x="40" y="24" fill={textColor} fontSize="11" fontWeight="bold" className="font-mono">App Execution</text>
          <text x="40" y="42" fill={mutedColor} fontSize="8.5">Runs application middleware</text>
          <text x="40" y="52" fill={mutedColor} fontSize="8.5">resolves route controller</text>
        </g>

        {/* --- LANE 3: Telemetry Commit (Y=380) --- */}
        {/* 7. Logging & Timing stats */}
        <g transform="translate(40, 380)">
          <rect x="0" y="0" width="200" height="70" rx="16" fill="url(#emeraldGrad-req)" stroke={successColor} strokeWidth="1.5" />
          <circle cx="20" cy="20" r="10" fill={successColor} fillOpacity="0.2" />
          <text x="20" y="23" textAnchor="middle" fill={textColor} fontSize="8" fontWeight="bold">7</text>
          <text x="40" y="24" fill={textColor} fontSize="11" fontWeight="bold" className="font-mono">Metrics Capture</text>
          <text x="40" y="42" fill={mutedColor} fontSize="8.5">Gathers monotonic timestamps</text>
          <text x="40" y="52" fill={mutedColor} fontSize="8.5">logs trace response durations</text>
        </g>

        {/* 8. Metrics compiling */}
        <g transform="translate(370, 380)">
          <rect x="0" y="0" width="210" height="70" rx="16" fill="url(#emeraldGrad-req)" stroke={successColor} strokeWidth="1.5" />
          <circle cx="20" cy="20" r="10" fill={successColor} fillOpacity="0.2" />
          <text x="20" y="23" textAnchor="middle" fill={textColor} fontSize="8" fontWeight="bold">8</text>
          <text x="40" y="24" fill={textColor} fontSize="11" fontWeight="bold" className="font-mono">Metrics Commit</text>
          <text x="40" y="42" fill={mutedColor} fontSize="8.5">Builds request record JSON</text>
          <text x="40" y="52" fill={mutedColor} fontSize="8.5">captures SQL & timings</text>
        </g>

        {/* 9. State store commit */}
        <g transform="translate(700, 380)">
          <rect x="0" y="0" width="200" height="70" rx="18" fill="url(#blueGrad-req)" stroke={accentColor} strokeWidth="2" filter="url(#adp-request-glow-new)" />
          <circle cx="20" cy="20" r="10" fill={accentColor} fillOpacity="0.2" />
          <text x="20" y="23" textAnchor="middle" fill={textColor} fontSize="8" fontWeight="bold">9</text>
          <text x="40" y="24" fill={textColor} fontSize="11" fontWeight="black" className="font-mono">State Registry</text>
          <text x="40" y="42" fill={accentColor} fontSize="8.5" fontWeight="bold">Commits to RuntimeStateStore</text>
          <text x="40" y="52" fill={mutedColor} fontSize="8.5">triggers dev platform plugins</text>
        </g>
      </svg>
    </div>
  )
}
