import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useTheme } from '../context/ThemeContext'
import { ArrowLeft, Search, Terminal } from 'lucide-react'
import { SEO } from '../components/SEO'

export function NotFoundPage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className={`min-h-screen flex flex-col justify-center items-center px-6 relative overflow-hidden ${
      isDark ? 'bg-black text-gray-100' : 'bg-gray-50 text-gray-900'
    }`}>
      <SEO
        title="404 - Page Not Found — Aquilia"
        description="The requested URL was not found on this documentation server."
      />

      {/* Decorative dynamic ambient glows (No Boxy, just raw color fields) */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[500px] h-[500px] pointer-events-none -z-10">
        <div className={`absolute inset-0 rounded-full blur-[120px] opacity-20 bg-gradient-to-br from-aquilia-500 to-blue-500`} />
      </div>

      <main className="max-w-xl w-full text-center space-y-10 relative z-10">
        {/* Terminal Traceback (Developer Aesthetic) */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
          className="space-y-4"
        >
          <div className="flex justify-center">
            <div className={`p-4 rounded-full ${isDark ? 'bg-white/5 text-aquilia-400' : 'bg-aquilia-500/10 text-aquilia-600'}`}>
              <Terminal className="w-12 h-12" />
            </div>
          </div>
          <h1 className="text-8xl font-black font-mono tracking-tighter bg-gradient-to-b from-aquilia-400 to-aquilia-600 bg-clip-text text-transparent">
            404
          </h1>
          <p className="text-sm font-bold font-mono tracking-widest text-aquilia-500 uppercase">
            LookupError: Path Registry Failure
          </p>
        </motion.div>

        {/* Description */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.5 }}
          className="space-y-3"
        >
          <h2 className="text-2xl font-bold font-mono">Lost in the Namespace?</h2>
          <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            The route you requested could not be resolved in the <code className="text-aquilia-500 font-mono">AppManifest.registry</code>. It may have been deprecated, moved, or never declared.
          </p>
        </motion.div>

        {/* Dynamic Actions */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.5 }}
          className="flex flex-col sm:flex-row gap-4 justify-center items-center"
        >
          <Link
            to="/"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 bg-aquilia-500 text-black font-bold rounded-lg transition-all hover:bg-aquilia-400 hover:scale-105 shadow-[0_0_30px_rgba(34,197,94,0.2)] cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" />
            Return Home
          </Link>
          <Link
            to="/docs"
            className={`w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3 border rounded-lg font-semibold transition-all cursor-pointer ${
              isDark
                ? 'border-white/10 hover:bg-white/5 text-white'
                : 'border-gray-200 hover:bg-gray-100 text-gray-800'
            }`}
          >
            <Search className="w-4 h-4" />
            Search Docs
          </Link>
        </motion.div>
      </main>

      {/* Footer hint */}
      <div className={`absolute bottom-8 left-0 right-0 text-center text-xs ${isDark ? 'text-gray-600' : 'text-gray-400'}`}>
        Aquilia Router Compiler v1.2.2 • <a href="https://github.com/tubox-labs/Aquilia" target="_blank" rel="noopener" className="hover:text-aquilia-500 transition-colors">Submit Issue</a>
      </div>
    </div>
  )
}
