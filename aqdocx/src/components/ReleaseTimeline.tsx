import { useRef } from 'react'
import { motion, useInView } from 'framer-motion'
import { GitBranch, CircleDot, Activity } from 'lucide-react'

export interface RoadmapNode {
  version: string
  codename: string
  date: string
  status: 'released' | 'current' | 'planned' | 'future'
  type: 'major' | 'minor' | 'patch'
  highlights: string[]
  branch?: string
}

export const roadmap: RoadmapNode[] = [
  {
    version: '0.1.0',
    codename: 'Spark',
    date: 'Jun 2025',
    status: 'released',
    type: 'minor',
    highlights: ['Core ASGI runtime', 'Basic routing'],
    branch: 'alpha',
  },
  {
    version: '0.5.0',
    codename: 'Foundation',
    date: 'Sep 2025',
    status: 'released',
    type: 'minor',
    highlights: ['Controller system', 'DI container', 'ORM draft'],
    branch: 'beta',
  },
  {
    version: '0.9.0',
    codename: 'Horizon',
    date: 'Dec 2025',
    status: 'released',
    type: 'minor',
    highlights: ['Auth stack', 'Blueprints', 'CLI tooling'],
    branch: 'rc',
  },
  {
    version: '1.0.0',
    codename: 'Genesis',
    date: 'Feb 2026',
    status: 'current',
    type: 'major',
    highlights: ['Production-ready', 'Full framework', '250+ APIs'],
  },
  {
    version: '1.1.0',
    codename: 'Pulse',
    date: 'Q2 2026',
    status: 'planned',
    type: 'minor',
    highlights: ['GraphQL support', 'Admin dashboard', 'Task queues'],
  },
  {
    version: '1.2.0',
    codename: 'Nexus',
    date: 'Q3 2026',
    status: 'planned',
    type: 'minor',
    highlights: ['gRPC transport', 'OpenTelemetry', 'Plugin marketplace'],
  },
  {
    version: '2.0.0',
    codename: 'Nova',
    date: '2027',
    status: 'future',
    type: 'major',
    highlights: ['Multi-runtime', 'Native compilation', 'Edge deployments'],
  },
]

interface Props {
  isDark: boolean
}

export function ReleaseTimeline({ isDark }: Props) {
  const graphRef = useRef<HTMLDivElement>(null)
  const isInView = useInView(graphRef, { once: true, amount: 0.2 })

  const nodeStatusStyles: Record<string, { dot: string; glow: string; label: string }> = {
    released: {
      dot: isDark
        ? 'bg-aquilia-500/40 border-aquilia-500/60'
        : 'bg-aquilia-200 border-aquilia-400',
      glow: '',
      label: isDark ? 'text-gray-500' : 'text-gray-400',
    },
    current: {
      dot: 'bg-aquilia-500 border-aquilia-400',
      glow: 'shadow-[0_0_20px_rgba(34,197,94,0.5),0_0_40px_rgba(34,197,94,0.2)]',
      label: isDark ? 'text-aquilia-400' : 'text-aquilia-600',
    },
    planned: {
      dot: isDark
        ? 'bg-white/10 border-white/20 border-dashed'
        : 'bg-gray-100 border-gray-300 border-dashed',
      glow: '',
      label: isDark ? 'text-gray-600' : 'text-gray-400',
    },
    future: {
      dot: isDark
        ? 'bg-white/5 border-white/10 border-dashed'
        : 'bg-gray-50 border-gray-200 border-dashed',
      glow: '',
      label: isDark ? 'text-gray-700' : 'text-gray-300',
    },
  }

  const branchColors: Record<string, string> = {
    alpha: isDark
      ? 'text-purple-400 bg-purple-500/10 border-purple-500/20'
      : 'text-purple-600 bg-purple-50 border-purple-200',
    beta: isDark
      ? 'text-blue-400 bg-blue-500/10 border-blue-500/20'
      : 'text-blue-600 bg-blue-50 border-blue-200',
    rc: isDark
      ? 'text-amber-400 bg-amber-500/10 border-amber-500/20'
      : 'text-amber-600 bg-amber-50 border-amber-200',
  }

  // index of the "current" node (inclusive)
  const currentIdx = roadmap.findIndex(n => n.status === 'current')
  const progressPct = ((currentIdx + 0.5) / roadmap.length) * 100

  return (
    <motion.div
      ref={graphRef}
      initial={{ opacity: 0, y: 30 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.7, ease: 'easeOut' }}
      className="overflow-hidden"
    >
      {/* Header */}
      <div className="py-5">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-aquilia-500/10 flex items-center justify-center">
              <GitBranch className="w-5 h-5 text-aquilia-500" />
            </div>
            <div>
              <h3 className={`text-lg font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                Release Timeline
              </h3>
              <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                From first spark to production and beyond
              </p>
            </div>
          </div>

          <div className="hidden sm:flex items-center gap-4">
            {[
              { color: isDark ? 'bg-aquilia-500/40' : 'bg-aquilia-300', label: 'Released' },
              { color: 'bg-aquilia-500', label: 'Current' },
              { color: isDark ? 'bg-white/10' : 'bg-gray-200', label: 'Planned' },
            ].map(l => (
              <div key={l.label} className="flex items-center gap-1.5">
                <div className={`w-2.5 h-2.5 rounded-full ${l.color}`} />
                <span
                  className={`text-[10px] uppercase tracking-wider font-medium ${
                    isDark ? 'text-gray-500' : 'text-gray-400'
                  }`}
                >
                  {l.label}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Graph body */}
      <div className="px-6 sm:px-8 py-8 overflow-x-auto">
        <div className="relative min-w-[680px]">

          {/* Trunk line */}
          <div className="absolute top-[52px] left-0 right-0 h-[3px]">
            <div
              className={`absolute inset-0 rounded-full ${
                isDark ? 'bg-white/5' : 'bg-gray-100'
              }`}
            />
            <motion.div
              initial={{ width: 0 }}
              animate={isInView ? { width: `${progressPct}%` } : {}}
              transition={{ duration: 1.5, delay: 0.3, ease: 'easeOut' }}
              className="absolute inset-y-0 left-0 rounded-full"
              style={{
                background: isDark
                  ? 'linear-gradient(90deg, rgba(34,197,94,0.15), rgba(34,197,94,0.6))'
                  : 'linear-gradient(90deg, rgba(34,197,94,0.2), rgba(34,197,94,0.7))',
              }}
            />
          </div>

          {/* Nodes */}
          <div className="relative flex justify-between">
            {roadmap.map((node, i) => {
              const styles = nodeStatusStyles[node.status]
              const isCurrent = node.status === 'current'
              const isPast = node.status === 'released'
              const isMajor = node.type === 'major'

              return (
                <motion.div
                  key={node.version}
                  initial={{ opacity: 0, y: 20 }}
                  animate={isInView ? { opacity: 1, y: 0 } : {}}
                  transition={{ delay: 0.2 + i * 0.12, duration: 0.5 }}
                  className="flex flex-col items-center relative"
                  style={{ width: `${100 / roadmap.length}%` }}
                >
                  {/* Branch pill */}
                  <div className="h-5 flex items-center justify-center mb-1">
                    {node.branch && (
                      <span
                        className={`px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider rounded-full border ${
                          branchColors[node.branch]
                        }`}
                      >
                        {node.branch}
                      </span>
                    )}
                  </div>

                  {/* Dot */}
                  <div className="relative flex items-center justify-center">
                    {isCurrent && (
                      <motion.div
                        animate={{ scale: [1, 1.8, 1], opacity: [0.5, 0, 0.5] }}
                        transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
                        className="absolute w-10 h-10 rounded-full bg-aquilia-500/20"
                      />
                    )}
                    <div
                      className={`relative z-10 rounded-full border-2 transition-all ${styles.dot} ${
                        styles.glow
                      } ${isMajor ? 'w-8 h-8' : 'w-5 h-5'}`}
                    >
                      {isCurrent && (
                        <div className="absolute inset-1 rounded-full bg-aquilia-400 animate-pulse" />
                      )}
                    </div>
                  </div>

                  {/* Labels */}
                  <div className={`mt-3 text-center ${isCurrent ? 'scale-105' : ''}`}>
                    <div
                      className={`font-bold font-mono ${
                        isCurrent
                          ? isDark
                            ? 'text-aquilia-400'
                            : 'text-aquilia-600'
                          : styles.label
                      } ${isMajor ? 'text-base' : 'text-sm'}`}
                    >
                      v{node.version}
                    </div>
                    <div
                      className={`text-[10px] italic mt-0.5 ${
                        isCurrent
                          ? isDark
                            ? 'text-aquilia-400/60'
                            : 'text-aquilia-600/60'
                          : isDark
                          ? 'text-gray-600'
                          : 'text-gray-400'
                      }`}
                    >
                      {node.codename}
                    </div>
                    <div
                      className={`text-[10px] mt-0.5 ${
                        isDark ? 'text-gray-700' : 'text-gray-300'
                      }`}
                    >
                      {node.date}
                    </div>
                  </div>

                  {/* Bullet highlights */}
                  <div className="mt-3 w-full max-w-[120px]">
                    {node.highlights.map((h, j) => (
                      <div
                        key={j}
                        className={`flex items-start gap-1 mt-0.5 ${
                          isPast || isCurrent ? '' : 'opacity-50'
                        }`}
                      >
                        <CircleDot
                          className={`w-2.5 h-2.5 mt-[3px] flex-shrink-0 ${
                            isCurrent
                              ? 'text-aquilia-500'
                              : isPast
                              ? isDark
                                ? 'text-aquilia-500/50'
                                : 'text-aquilia-400'
                              : isDark
                              ? 'text-gray-700'
                              : 'text-gray-300'
                          }`}
                        />
                        <span
                          className={`text-[10px] leading-tight ${
                            isCurrent
                              ? isDark
                                ? 'text-gray-300'
                                : 'text-gray-700'
                              : isDark
                              ? 'text-gray-600'
                              : 'text-gray-400'
                          }`}
                        >
                          {h}
                        </span>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Footer note */}
      <div className="py-4 flex items-center gap-2">
        <Activity className="w-3 h-3" />
        <span className={`text-[10px] uppercase tracking-wider font-medium ${
          isDark ? 'text-gray-600' : 'text-gray-400'
        }`}>
          Roadmap is indicative — release dates may shift based on community feedback
        </span>
      </div>
    </motion.div>
  )
}
