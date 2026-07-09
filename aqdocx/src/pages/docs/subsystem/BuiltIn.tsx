import { useTheme } from '../../../context/ThemeContext'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Workflow, Database, RefreshCw, Send, Globe, HardDrive } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function EffectsBuiltIn() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const capabilities = [
    {
      title: "Database Transactions",
      description: "Lease connections from the core application pool. Enforces transactional safety with automatic commits and rollbacks based on request outcomes.",
      token: "DBTx",
      provider: "DBTxProvider",
      link: "/docs/subsystem/dbtx",
      icon: Database,
      accent: "from-emerald-500/20 to-teal-500/20"
    },
    {
      title: "Key-Value Caching",
      description: "Partition caching operations by namespace to prevent key overlap. Connects directly to Redis or Memcached, with dict fallbacks.",
      token: "CacheEffect",
      provider: "CacheProvider",
      link: "/docs/subsystem/cache",
      icon: RefreshCw,
      accent: "from-green-500/20 to-emerald-500/20"
    },
    {
      title: "Queue & Task Workers",
      description: "Publish events to brokers like RabbitMQ/Redis Streams or bridge with task workers to enqueue asynchronous background jobs.",
      token: "QueueEffect",
      provider: "QueueProvider / TaskQueueProvider",
      link: "/docs/subsystem/queue",
      icon: Send,
      accent: "from-blue-500/20 to-indigo-500/20"
    },
    {
      title: "Outbound HTTP Clients",
      description: "Acquire pooled outbound HTTP client sessions with base URLs, headers, and request timeouts managed at the framework level.",
      token: "HTTPEffect",
      provider: "HTTPProvider",
      link: "/docs/subsystem/http",
      icon: Globe,
      accent: "from-sky-500/20 to-blue-500/20"
    },
    {
      title: "Unified Object Storage",
      description: "Abstract cloud object buckets and local filesystem paths behind a standard read/write interface for uploads and media assets.",
      token: "StorageEffect",
      provider: "StorageProvider",
      link: "/docs/subsystem/storage",
      icon: HardDrive,
      accent: "from-violet-500/20 to-purple-500/20"
    }
  ]

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <Workflow className="w-4 h-4" />
          <span>EFFECTS / BUILT-IN</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Built-in Capabilities
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia packages five core capabilities natively, covering database transactions, memory caches, messaging brokers, background task executors, HTTP clients, and unified blob storage.
        </p>
      </div>

      {/* Catalog Grid */}
      <section className="mb-16">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {capabilities.map((cap, i) => {
            const Icon = cap.icon
            return (
              <div 
                key={i} 
                className={`relative group p-6 rounded-2xl border transition-all duration-300 ${
                  isDark 
                    ? "bg-white/[0.01] border-white/5 hover:border-white/15 hover:bg-white/[0.03]" 
                    : "bg-gray-50/50 border-gray-200/60 hover:border-gray-300 hover:bg-gray-50"
                }`}
              >
                {/* Visual Accent Glow (Premium styling, no box layout) */}
                <div className={`absolute inset-0 bg-gradient-to-br ${cap.accent} opacity-0 group-hover:opacity-100 rounded-2xl blur-xl transition-opacity duration-500 -z-10`} />

                <div className="flex items-start gap-4 mb-4">
                  <div className={`p-2.5 rounded-xl ${isDark ? "bg-white/5 text-aquilia-400" : "bg-gray-100 text-aquilia-600"}`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className={`text-md font-semibold ${isDark ? "text-white" : "text-gray-900"}`}>{cap.title}</h3>
                    <div className="flex flex-wrap gap-2 mt-1">
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-aquilia-500/10 text-aquilia-400">{cap.token}</span>
                      <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${isDark ? "bg-white/5 text-gray-400" : "bg-gray-100 text-gray-500"}`}>{cap.provider}</span>
                    </div>
                  </div>
                </div>

                <p className={`text-sm leading-relaxed mb-6 font-light ${isDark ? "text-gray-400" : "text-gray-600"}`}>
                  {cap.description}
                </p>

                <Link 
                  to={cap.link} 
                  className="inline-flex items-center gap-1.5 text-xs font-mono font-bold text-aquilia-500 hover:text-aquilia-400 transition-colors"
                >
                  EXPLORE API <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            )
          })}
        </div>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/subsystem/overview" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Overview
        </Link>
        <span />
      </div>

      <NextSteps />
    </div>
  )
}
