import { Link, useLocation } from 'react-router-dom'
import { useTheme } from '../context/ThemeContext'
import {
  Sun, Moon, Github, BookOpen, Menu, Tag, Activity, FileText
} from 'lucide-react'
import { useState, useEffect } from 'react'
import { UniversalSearch } from './UniversalSearch'



interface NavbarProps {
  onToggleSidebar?: () => void
}

export function Navbar({ onToggleSidebar }: NavbarProps) {
  const { theme, toggle } = useTheme()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const location = useLocation()
  const isDark = theme === 'dark'

  // Close on route change
  useEffect(() => { setMobileMenuOpen(false) }, [location.pathname])

  return (
    <nav className="fixed w-full z-40 glass border-b border-[var(--border-color)]/50 print:hidden">
      <div className="max-w-[90rem] mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Left: Hamburger + Logo */}
          <div className="flex items-center gap-4">
            {/* Hamburger for mobile */}
            {!location.pathname.startsWith('/docs') && (
              <button
                onClick={() => {
                  if (onToggleSidebar) {
                    onToggleSidebar()
                  } else {
                    setMobileMenuOpen(!mobileMenuOpen)
                  }
                }}
                className={`lg:hidden p-2 -ml-2 rounded-lg transition-colors ${isDark ? 'text-gray-400 hover:bg-white/10 hover:text-white' : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'}`}
              >
                <Menu className="w-5 h-5" />
              </button>
            )}

            {/* Logo */}
            <Link to="/" className="flex-shrink-0 flex items-center gap-3 group relative">
              <div className="relative">
                <img
                  src="/logo.png"
                  alt="Aquilia"
                  className="w-9 h-9 rounded-lg shadow-lg shadow-aquilia-500/20 transition-all duration-300 group-hover:scale-110 group-hover:shadow-aquilia-500/40"
                />
                <div className="absolute inset-0 rounded-lg bg-gradient-to-tr from-aquilia-500/0 via-aquilia-400/0 to-aquilia-300/0 group-hover:from-aquilia-500/20 group-hover:via-aquilia-400/10 group-hover:to-transparent transition-all duration-300" />
              </div>
              <span className="font-bold text-xl tracking-tighter gradient-text font-mono hidden sm:inline relative">
                Aquilia
                <span className="block text-[10px] uppercase tracking-widest text-gray-500 font-sans -mt-1 opacity-70">
                  Zero-Boilerplate Python Framework
                </span>
                <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
              </span>
            </Link>
          </div>

          {/* Center: links */}
          <div className="flex items-center gap-1">

            <Link
              to="/docs"
              className={`hidden md:flex items-center gap-1.5 px-3 py-2 text-sm font-medium transition-all duration-200 rounded-lg group/guide relative overflow-hidden ${location.pathname.startsWith('/docs')
                ? 'text-aquilia-400'
                : `${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`
                }`}
            >
              <BookOpen className="w-4 h-4 group-hover/guide:scale-110 transition-transform duration-200" />
              <span>Documentation</span>
              <div className={`absolute inset-0 -translate-x-full group-hover/guide:translate-x-full transition-transform duration-700 bg-gradient-to-r ${isDark ? 'from-transparent via-white/5 to-transparent' : 'from-transparent via-gray-200 to-transparent'}`} />
            </Link>

            <Link
              to="/benchmark"
              className={`hidden md:flex items-center gap-1.5 px-3 py-2 text-sm font-medium transition-all duration-200 rounded-lg group/bench relative overflow-hidden ${location.pathname === '/benchmark'
                ? 'text-aquilia-400'
                : `${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`
                }`}
            >
              <Activity className="w-4 h-4 group-hover/bench:scale-110 transition-transform duration-200" />
              <span>Benchmark</span>
              <div className={`absolute inset-0 -translate-x-full group-hover/bench:translate-x-full transition-transform duration-700 bg-gradient-to-r ${isDark ? 'from-transparent via-white/5 to-transparent' : 'from-transparent via-gray-200 to-transparent'}`} />
            </Link>

            <Link
              to="/changelogs"
              className={`hidden md:flex items-center gap-1.5 px-3 py-2 text-sm font-medium transition-all duration-200 rounded-lg group/cl relative overflow-hidden ${location.pathname === '/changelogs'
                ? 'text-aquilia-400'
                : `${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`
                }`}
            >
              <FileText className="w-4 h-4 group-hover/cl:scale-110 transition-transform duration-200" />
              <span>Changelogs</span>
              <div className={`absolute inset-0 -translate-x-full group-hover/cl:translate-x-full transition-transform duration-700 bg-gradient-to-r ${isDark ? 'from-transparent via-white/5 to-transparent' : 'from-transparent via-gray-200 to-transparent'}`} />
            </Link>

            <Link
              to="/releases"
              className={`hidden md:flex items-center gap-1.5 px-3 py-2 text-sm font-medium transition-all duration-200 rounded-lg group/rel relative overflow-hidden ${location.pathname === '/releases'
                ? 'text-aquilia-400'
                : `${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`
                }`}
            >
              <Tag className="w-4 h-4 group-hover/rel:scale-110 transition-transform duration-200" />
              <span>Releases</span>
              <div className={`absolute inset-0 -translate-x-full group-hover/rel:translate-x-full transition-transform duration-700 bg-gradient-to-r ${isDark ? 'from-transparent via-white/5 to-transparent' : 'from-transparent via-gray-200 to-transparent'}`} />
            </Link>
          </div>

          {/* Right actions */}
          <div className="flex items-center gap-2">
            <UniversalSearch />
            <button
              onClick={toggle}
              className={`p-2 rounded-lg transition-all duration-200 relative overflow-hidden group ${isDark ? 'hover:bg-white/10 text-gray-400 hover:text-white' : 'hover:bg-gray-200 text-gray-500 hover:text-gray-900'}`}
              title="Toggle theme"
            >
              {isDark ? (
                <Sun className="w-5 h-5 group-hover:rotate-180 transition-transform duration-500" />
              ) : (
                <Moon className="w-5 h-5 group-hover:-rotate-12 transition-transform duration-300" />
              )}
              <div className={`absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-700 bg-gradient-to-r ${isDark ? 'from-transparent via-white/5 to-transparent' : 'from-transparent via-gray-200 to-transparent'}`} />
            </button>
            <a
              href="https://github.com/axiomchronicles/Aquilia"
              target="_blank"
              rel="noopener"
              className={`p-2 rounded-lg transition-all duration-200 relative overflow-hidden group ${isDark ? 'hover:bg-white/10 text-gray-400 hover:text-white' : 'hover:bg-gray-200 text-gray-500 hover:text-gray-900'}`}
              title="View on GitHub"
            >
              <Github className="w-5 h-5 group-hover:scale-110 transition-transform duration-200" />
              <div className={`absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-700 bg-gradient-to-r ${isDark ? 'from-transparent via-white/5 to-transparent' : 'from-transparent via-gray-200 to-transparent'}`} />
            </a>
          </div>
        </div>
      </div>

      {/* Mobile menu — shown when hamburger clicked on standalone pages */}
      {mobileMenuOpen && !onToggleSidebar && (
        <div className={`lg:hidden border-t ${isDark ? 'bg-[#09090b]/98 border-white/10' : 'bg-white/98 border-gray-200'}`}>
          <div className="px-4 py-4 space-y-1">
            <Link
              to="/docs"
              className={`flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${isDark ? 'text-gray-300 hover:bg-white/5' : 'text-gray-600 hover:bg-gray-50'}`}
            >
              <BookOpen className="w-4 h-4" />
              Documentation
            </Link>
            <Link
              to="/changelogs"
              className={`flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                location.pathname === '/changelogs'
                  ? 'text-aquilia-500 bg-aquilia-500/10'
                  : isDark ? 'text-gray-300 hover:bg-white/5' : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <FileText className="w-4 h-4" />
              Changelogs
            </Link>
            <Link
              to="/benchmark"
              className={`flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                location.pathname === '/benchmark'
                  ? 'text-aquilia-500 bg-aquilia-500/10'
                  : isDark ? 'text-gray-300 hover:bg-white/5' : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <Activity className="w-4 h-4" />
              Benchmark
            </Link>
            <Link
              to="/releases"
              className={`flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                location.pathname === '/releases'
                  ? 'text-aquilia-500 bg-aquilia-500/10'
                  : isDark ? 'text-gray-300 hover:bg-white/5' : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <Tag className="w-4 h-4" />
              Releases
            </Link>
          </div>
        </div>
      )}
    </nav>
  )
}
