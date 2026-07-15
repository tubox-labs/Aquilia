import { Link } from 'react-router-dom'
import { useTheme } from '../context/ThemeContext'
import { Github, MessageSquare } from 'lucide-react'
import { CONSTANTS } from '../data/constants'

export function Footer() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <footer className={`border-t backdrop-blur-sm mt-auto ${isDark ? 'border-white/5 bg-zinc-950/20' : 'border-gray-100 bg-white/20'}`}>
      <div className="max-w-[90rem] mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row justify-between items-center gap-6">
          {/* Brand */}
          <div className="flex items-center gap-2">
            <img src="/logo.png" alt="Aquilia" className="w-5 h-5 object-contain opacity-80" />
            <span className={`text-xs font-bold tracking-wider ${isDark ? 'text-white' : 'text-gray-900'}`}>AQUILIA</span>
          </div>

          {/* Links */}
          <div className="flex flex-wrap items-center justify-center gap-x-8 gap-y-2 text-xs">
            <Link to="/help" className={`${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'} transition-colors`}>Help</Link>
            <Link to="/community" className={`${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'} transition-colors`}>Community</Link>
            <Link to="/privacy" className={`${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'} transition-colors`}>Privacy</Link>
            <Link to="/terms" className={`${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'} transition-colors`}>Terms & Conditions</Link>
          </div>

          {/* Social Icons */}
          <div className="flex items-center gap-4">
            <a 
              href={CONSTANTS.GITHUB_REPO_URL} 
              target="_blank" 
              rel="noopener" 
              className={`transition-colors ${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`}
              title="GitHub Repository"
            >
              <Github className="w-4 h-4" />
            </a>
            <a 
              href={CONSTANTS.GITHUB_DISCUSSIONS_URL} 
              target="_blank" 
              rel="noopener" 
              className={`transition-colors ${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`}
              title="Discussions"
            >
              <MessageSquare className="w-4 h-4" />
            </a>
          </div>
        </div>
        <div className="mt-6 pt-4 border-t border-gray-100 dark:border-white/5 flex flex-col sm:flex-row justify-between items-center gap-2">
          <div className={`text-[10px] ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
            © 2026 Aquilia Framework. Built for performance and safety.
          </div>
          <div className={`text-[10px] ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
            Licensed under MIT.
          </div>
        </div>
      </div>
    </footer>
  )
}
