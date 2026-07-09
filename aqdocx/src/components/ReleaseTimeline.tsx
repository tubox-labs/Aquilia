import { useRef, useEffect, useState } from 'react'
import { motion, useInView } from 'framer-motion'
import { GitBranch, CircleDot, Activity, Check } from 'lucide-react'

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
    version: '1.0.0',
    codename: 'Genesis',
    date: 'Feb 22, 2026',
    status: 'released',
    type: 'major',
    highlights: ['First Stable', 'Async ASGI Core', 'Scoped DI'],
  },
  {
    version: '1.0.1',
    codename: 'Genesis P1',
    date: 'Mar 08, 2026',
    status: 'released',
    type: 'patch',
    highlights: ['Framework Security', 'Argon2 hashing', 'Path checks'],
  },
  {
    version: '1.0.2',
    codename: 'Genesis P2',
    date: 'Apr 02, 2026',
    status: 'released',
    type: 'patch',
    highlights: ['SQLite pools', 'Cookie sessions', 'TX commits'],
  },
  {
    version: '1.0.3',
    codename: 'Genesis P3',
    date: 'Apr 19, 2026',
    status: 'released',
    type: 'patch',
    highlights: ['Route cache compile', 'OpenAPI schemas'],
  },
  {
    version: '1.0.4',
    codename: 'Genesis P4',
    date: 'May 17, 2026',
    status: 'released',
    type: 'patch',
    highlights: ['Removed workspace compile', 'Native execution'],
  },
  {
    version: '1.0.5',
    codename: 'Jolly Roger',
    date: 'Jun 04, 2026',
    status: 'released',
    type: 'patch',
    highlights: ['Aquilia MCP Server', 'Surp serialization'],
  },
  {
    version: '1.1.0',
    codename: 'Black Pearl',
    date: 'Jun 08, 2026',
    status: 'released',
    type: 'minor',
    highlights: ['SSE Streaming', 'OpenTelemetry', 'Body validation'],
    branch: 'beta',
  },
  {
    version: '1.1.1',
    codename: 'Sea Serpent',
    date: 'Jun 09, 2026',
    status: 'released',
    type: 'patch',
    highlights: ['Decoupled builders', 'Thread-safe dotenv'],
  },
  {
    version: '1.1.2',
    codename: 'Crimson Gale',
    date: 'Jun 12, 2026',
    status: 'released',
    type: 'patch',
    highlights: ['Middleware scopes', 'Env mapping overrides'],
  },
  {
    version: '1.2.0',
    codename: 'Kraken\'s Wake',
    date: 'Jun 28, 2026',
    status: 'released',
    type: 'minor',
    highlights: ['Request Inspector', 'DB CLI rollbacks', 'API versioning'],
    branch: 'rc',
  },
  {
    version: '1.2.1',
    codename: 'Kraken\'s Wake',
    date: 'Jul 01, 2026',
    status: 'released',
    type: 'patch',
    highlights: ['Startup decoupling', 'Lazy Jinja2 loader', 'Windows locks'],
  },
  {
    version: '1.2.2',
    codename: 'Kraken\'s Wake',
    date: 'Jul 01, 2026',
    status: 'current',
    type: 'patch',
    highlights: ['Database integrate', 'ORM schema indices', 'CLI sync engine'],
  },
]

interface Props {
  isDark: boolean
}

export function ReleaseTimeline({ isDark }: Props) {
  const graphRef = useRef<HTMLDivElement>(null)
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const isInView = useInView(graphRef, { once: true, amount: 0.2 })
  const [nodes, setNodes] = useState<RoadmapNode[]>(roadmap)

  useEffect(() => {
    fetch('https://api.github.com/repos/tubox-labs/Aquilia/tags')
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch tags')
        return res.json()
      })
      .then(data => {
        if (Array.isArray(data) && data.length > 0) {
          const tags = [...data].reverse()
          
          let latestStable = '1.2.2'
          for (let k = tags.length - 1; k >= 0; k--) {
            const v = tags[k].name.replace(/^v/, '')
            if (!/[ab]|rc|dev|pre/i.test(v)) {
              latestStable = v
              break
            }
          }

          const mapped = tags.map((tag: any, i) => {
            const version = tag.name.replace(/^v/, '')
            const staticMatch = roadmap.find(r => r.version === version)
            
            let defaultCodename = "Genesis"
            if (version.startsWith('1.3')) {
              defaultCodename = "Poseidon's Trident"
            } else if (version.startsWith('1.2')) {
              defaultCodename = "Kraken's Wake"
            } else if (version.startsWith('1.1')) {
              defaultCodename = "Black Pearl"
            } else if (version === '1.0.5') {
              defaultCodename = "Jolly Roger"
            }
            
            const isPre = /[ab]|rc|dev|pre/i.test(version)
            let branch = staticMatch?.branch
            if (isPre) {
              if (version.includes('a')) branch = 'alpha'
              else if (version.includes('b')) branch = 'beta'
              else if (version.includes('rc')) branch = 'rc'
            }

            let status: 'released' | 'current' | 'planned' | 'future' = 'released'
            if (version === latestStable) {
              status = 'current'
            } else if (isPre) {
              status = 'planned'
            } else {
              const latestStableIdx = tags.findIndex((t: any) => t.name.replace(/^v/, '') === latestStable)
              if (i > latestStableIdx) {
                status = 'planned'
              } else {
                status = 'released'
              }
            }

            return {
              version,
              codename: staticMatch?.codename || defaultCodename,
              date: staticMatch?.date || "Jul 2026",
              status,
              type: staticMatch?.type || (version.endsWith('.0') ? 'minor' as const : 'patch' as const),
              highlights: staticMatch?.highlights || (isPre ? ['Upcoming features & testing'] : ['GitHub tag release']),
              branch
            }
          })
          setNodes(mapped)
          
          // Auto-scroll to the end (latest version) after nodes state is set and DOM updates
          setTimeout(() => {
            if (scrollContainerRef.current) {
              scrollContainerRef.current.scrollLeft = scrollContainerRef.current.scrollWidth
            }
          }, 100)
        }
      })
      .catch(err => {
        console.error('Failed to fetch github tags for timeline:', err)
        // Fallback auto-scroll on failure
        if (scrollContainerRef.current) {
          scrollContainerRef.current.scrollLeft = scrollContainerRef.current.scrollWidth
        }
      })
  }, [])

  const nodeStatusStyles: Record<string, { dot: string; glow: string; label: string }> = {
    released: {
      dot: isDark
        ? 'bg-zinc-950 border-aquilia-500/60'
        : 'bg-white border-aquilia-400',
      glow: '',
      label: isDark ? 'text-gray-500' : 'text-gray-400',
    },
    current: {
      dot: isDark
        ? 'bg-zinc-950 border-aquilia-500'
        : 'bg-white border-aquilia-600',
      glow: 'shadow-[0_0_20px_rgba(34,197,94,0.5),0_0_40px_rgba(34,197,94,0.2)]',
      label: isDark ? 'text-aquilia-400' : 'text-aquilia-600',
    },
    planned: {
      dot: isDark
        ? 'bg-zinc-950 border-white/20 border-dashed'
        : 'bg-white border-gray-300 border-dashed',
      glow: '',
      label: isDark ? 'text-gray-600' : 'text-gray-400',
    },
    future: {
      dot: isDark
        ? 'bg-zinc-950 border-white/10 border-dashed'
        : 'bg-white border-gray-200 border-dashed',
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
  const currentIdx = nodes.findIndex(n => n.status === 'current')
  const progressPct = ((currentIdx + 0.5) / nodes.length) * 100

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
                From Genesis to Kraken's Wake and beyond
              </p>
            </div>
          </div>

          <div className="hidden sm:flex items-center gap-4">
            {[
              { color: isDark ? 'bg-aquilia-500/40' : 'bg-aquilia-300', label: 'Released' },
              { color: 'bg-aquilia-500', label: 'Current' },
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
      <div
        ref={scrollContainerRef}
        className="px-6 sm:px-8 py-8 overflow-x-auto scrollbar-thin scrollbar-thumb-aquilia-500/20 scrollbar-track-transparent scroll-smooth"
      >
        <div className="relative min-w-[2000px]">

          {/* Trunk line */}
          <div className="absolute top-[40px] left-0 right-0 h-[3px]">
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
            {nodes.map((node, i) => {
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
                  style={{ width: `${100 / nodes.length}%` }}
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
                  <div className="relative h-8 flex items-center justify-center">
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
                      } ${isMajor ? 'w-8 h-8' : 'w-5 h-5'} flex items-center justify-center`}
                    >
                      {isCurrent && (
                        <div className="absolute inset-1 rounded-full bg-aquilia-400 animate-pulse" />
                      )}
                      {isPast && (
                        <Check className={`${isMajor ? 'w-4 h-4' : 'w-3 h-3'} text-aquilia-500`} />
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
