import { motion } from 'framer-motion'

export function ADPIntegrationPointsDiagram({ isDark, className = "max-w-4xl" }: { isDark: boolean; className?: string }) {
  const accentColor = '#3b82f6'
  const successColor = '#10b981'
  const textColor = isDark ? '#f4f4f5' : '#18181b'
  const mutedColor = isDark ? '#a1a1aa' : '#71717a'
  const gridColor = isDark ? 'rgba(255, 255, 255, 0.03)' : 'rgba(0, 0, 0, 0.02)'


  return (
    <div className="w-full overflow-hidden py-8 flex justify-center bg-transparent">
      <svg viewBox="0 0 950 380" className={`w-full h-auto ${className}`}>
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
          <filter id="points-glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>

          <linearGradient id="purpleGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.12" />
            <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0.02" />
          </linearGradient>
          <linearGradient id="blueGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.12" />
            <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.02" />
          </linearGradient>
          <linearGradient id="emeraldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#10b981" stopOpacity="0.12" />
            <stop offset="100%" stopColor="#10b981" stopOpacity="0.02" />
          </linearGradient>

          <marker id="pts-arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill={isDark ? "#71717a" : "#a1a1aa"} />
          </marker>
        </defs>

        <g stroke={gridColor} strokeWidth="1">
          {Array.from({ length: 10 }).map((_, i) => (
            <line key={`v-${i}`} x1={i * 100} y1="0" x2={i * 100} y2="380" />
          ))}
          {Array.from({ length: 4 }).map((_, i) => (
            <line key={`h-${i}`} x1="0" y1={i * 100} x2="950" y2={i * 100} />
          ))}
        </g>

        {/* ─── CONNECTORS ─── */}
        <g fill="none" strokeWidth="1.5" stroke={isDark ? "#3f3f46" : "#d4d4d8"} markerEnd="url(#pts-arrow)">
          {/* Subsystem -> FaultEngine */}
          <path d="M 230 190 C 280 140, 310 90, 390 90" />
          {/* Subsystem -> Config */}
          <path d="M 230 190 H 390" />
          {/* Subsystem -> Trace spans */}
          <path d="M 230 190 C 280 240, 310 290, 390 290" />

          {/* FaultEngine -> Inspector */}
          <path d="M 580 90 C 650 90, 710 140, 750 160" />
          {/* Trace spans -> Inspector */}
          <path d="M 585 290 C 650 290, 710 240, 750 220" />
        </g>

        {/* Dynamic moving pulses */}
        <motion.circle r="3" fill="#3b82f6" filter="url(#points-glow)"
          animate={{ cx: [230, 390], cy: [190, 190] }}
          transition={{ duration: 2.5, repeat: Infinity, ease: "linear" }}
        />

        {/* ─── NODES ─── */}

        {/* ADP Subsystem Node */}
        <g transform="translate(30, 145)">
          <rect x="0" y="0" width="200" height="90" rx="20" fill="url(#purpleGrad)" stroke="#8b5cf6" strokeWidth="2" filter="url(#points-glow)" />
          <text x="100" y="38" textAnchor="middle" fill={textColor} fontSize="12" fontWeight="black" className="font-mono">devplatform</text>
          <text x="100" y="55" textAnchor="middle" fill="#8b5cf6" fontSize="10.5" fontWeight="bold">ADP Subsystem</text>
          <text x="100" y="68" textAnchor="middle" fill={mutedColor} fontSize="8.5">Telemetry & reload daemon</text>
        </g>

        {/* Fault Engine Node */}
        <g transform="translate(390, 50)">
          <rect x="0" y="0" width="195" height="75" rx="16" fill="url(#blueGrad)" stroke={accentColor} strokeWidth="1" />
          <text x="97.5" y="30" textAnchor="middle" fill={textColor} fontSize="11" fontWeight="bold" className="font-mono">FaultEngine.process()</text>
          <text x="97.5" y="46" textAnchor="middle" fill={accentColor} fontSize="9" fontWeight="bold">report_fault(fault, app)</text>
          <text x="97.5" y="58" textAnchor="middle" fill={mutedColor} fontSize="8.5">Exception Lane Routing</text>
        </g>

        {/* Config Node */}
        <g transform="translate(390, 150)">
          <rect x="0" y="0" width="195" height="75" rx="16" fill="url(#blueGrad)" stroke={accentColor} strokeWidth="1.5" />
          <text x="97.5" y="30" textAnchor="middle" fill={textColor} fontSize="11" fontWeight="bold" className="font-mono">AquiliaDevelopmentConfig</text>
          <text x="97.5" y="46" textAnchor="middle" fill={mutedColor} fontSize="9">Env resolution + validation</text>
          <text x="97.5" y="58" textAnchor="middle" fill={accentColor} fontSize="8.5" fontWeight="bold">to_dict() single truth</text>
        </g>

        {/* Trace spans Node */}
        <g transform="translate(390, 250)">
          <rect x="0" y="0" width="195" height="75" rx="16" fill="url(#blueGrad)" stroke={accentColor} strokeWidth="1" />
          <text x="97.5" y="30" textAnchor="middle" fill={textColor} fontSize="11" fontWeight="bold" className="font-mono">current_trace</text>
          <text x="97.5" y="46" textAnchor="middle" fill={mutedColor} fontSize="9">Lane.DATABASE / DEVPLATFORM</text>
          <text x="97.5" y="58" textAnchor="middle" fill={accentColor} fontSize="8.5" fontWeight="bold">Request spans instrumentation</text>
        </g>

        {/* Inspector Target Node */}
        <g transform="translate(720, 140)">
          <rect x="0" y="0" width="200" height="90" rx="20" fill="url(#emeraldGrad)" stroke={successColor} strokeWidth="2.5" filter="url(#points-glow)" />
          <text x="100" y="35" textAnchor="middle" fill={textColor} fontSize="12" fontWeight="black" className="font-mono">Inspector</text>
          <text x="100" y="52" textAnchor="middle" fill={successColor} fontSize="10" fontWeight="bold">Lane.EXCEPTION Dashboard</text>
          <text x="100" y="68" textAnchor="middle" fill={mutedColor} fontSize="8.5">Dynamic charts & profiles</text>
        </g>
      </svg>
    </div>
  )
}
