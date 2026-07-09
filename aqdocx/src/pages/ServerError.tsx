import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useTheme } from '../context/ThemeContext'
import { RefreshCw, AlertOctagon, Github } from 'lucide-react'
import { useVersion } from '../hooks/useVersion'
import { SEO } from '../components/SEO'

export function ServerErrorPage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const version = useVersion()

  const reloadPage = () => {
    window.location.reload()
  }

  return (
    <div className={`min-h-screen flex flex-col justify-center items-center px-6 relative overflow-hidden ${
      isDark ? 'bg-black text-gray-100' : 'bg-gray-50 text-gray-900'
    }`}>
      <SEO
        title="500 - Internal Server Error — Aquilia"
        description="A runtime framework exception occurred on the documentation server."
      />

      {/* Crimson Ambient Glows */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[500px] h-[500px] pointer-events-none -z-10">
        <div className={`absolute inset-0 rounded-full blur-[120px] opacity-15 bg-gradient-to-br from-red-600 to-amber-500`} />
      </div>

      <main className="max-w-2xl w-full text-center space-y-10 relative z-10">
        {/* Header Indicator */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="space-y-4"
        >
          <div className="flex justify-center">
            <div className="p-4 rounded-full bg-red-500/10 text-red-500 animate-pulse">
              <AlertOctagon className="w-12 h-12" />
            </div>
          </div>
          <h1 className="text-8xl font-black font-mono tracking-tighter bg-gradient-to-b from-red-400 to-red-600 bg-clip-text text-transparent">
            500
          </h1>
          <p className="text-sm font-bold font-mono tracking-widest text-red-500 uppercase">
            InternalServerError: LifespanHookFailure
          </p>
        </motion.div>

        {/* Traceback Simulator (Premium Terminal Mock) */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.5 }}
          className="text-left font-mono text-xs p-5 rounded-2xl border border-red-500/20 bg-red-950/5 select-none"
        >
          <p className="text-red-400 font-bold">// Traceback (most recent render call):</p>
          <p className="text-gray-500 pl-4">File "aquilia/runtime/lifecycle.py", line 42, in bootstrap</p>
          <p className="text-gray-300 pl-8">await self.container.resolve_lifespan()</p>
          <p className="text-gray-500 pl-4">File "aquilia/di/container.py", line 128, in resolve_lifespan</p>
          <p className="text-red-500 font-semibold pl-4">ScopeViolationError: Singleton scoped engine resolved transient db_session context</p>
        </motion.div>

        {/* Description */}
        <div className="space-y-3 max-w-lg mx-auto">
          <h2 className="text-2xl font-bold font-mono">Something went sideways.</h2>
          <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            A severe container resolution exception was encountered during runtime evaluation. The workspace components failed to mount.
          </p>
        </div>

        {/* Dynamic Actions */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.5 }}
          className="flex flex-col sm:flex-row gap-4 justify-center items-center"
        >
          <button
            onClick={reloadPage}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 bg-red-600 text-white font-bold rounded-lg transition-all hover:bg-red-500 hover:scale-105 shadow-[0_0_30px_rgba(239,68,68,0.2)] cursor-pointer"
          >
            <RefreshCw className="w-4 h-4" />
            Reload Workspace
          </button>
          <a
            href="https://github.com/tubox-labs/Aquilia/issues"
            target="_blank"
            rel="noopener"
            className={`w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 border rounded-lg font-semibold transition-all cursor-pointer ${
              isDark
                ? 'border-white/10 hover:bg-white/5 text-white'
                : 'border-gray-200 hover:bg-gray-100 text-gray-800'
            }`}
          >
            <Github className="w-4 h-4" />
            Report Runtime Issue
          </a>
        </motion.div>
      </main>

      {/* Footer hint */}
      <div className={`absolute bottom-8 left-0 right-0 text-center text-xs ${isDark ? 'text-gray-600' : 'text-gray-400'}`}>
        Aquilia Framework CLI v{version} • <Link to="/help" className="hover:text-red-400 transition-colors">Troubleshooting Guide</Link>
      </div>
    </div>
  )
}
