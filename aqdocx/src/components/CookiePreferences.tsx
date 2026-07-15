import { useState, useEffect } from 'react'
import { useTheme } from '../context/ThemeContext'
import { Shield, Settings, Check, X } from 'lucide-react'

export function CookiePreferences() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const [isOpen, setIsOpen] = useState(false)
  const [showDetails, setShowDetails] = useState(false)
  const [preferences, setPreferences] = useState({
    essential: true,
    analytics: true,
    marketing: false,
  })

  useEffect(() => {
    const consent = localStorage.getItem('aquilia_cookie_consent')
    if (!consent) {
      // Small delay for visual entry
      const timer = setTimeout(() => setIsOpen(true), 1500)
      return () => clearTimeout(timer)
    }
  }, [])

  const handleAcceptAll = () => {
    const consentObj = { essential: true, analytics: true, marketing: true }
    localStorage.setItem('aquilia_cookie_consent', JSON.stringify(consentObj))
    setIsOpen(false)
  }

  const handleSave = () => {
    localStorage.setItem('aquilia_cookie_consent', JSON.stringify(preferences))
    setIsOpen(false)
  }

  if (!isOpen) return null

  return (
    <div className="fixed bottom-6 right-6 z-50 max-w-md w-full p-6 backdrop-blur-xl bg-white/70 dark:bg-zinc-950/70 border border-gray-200 dark:border-white/5 shadow-2xl rounded-2xl animate-fade-in-up transition-all duration-300 print:hidden">
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex gap-3">
            <Shield className="w-5 h-5 text-aquilia-500 shrink-0 mt-1" />
            <div>
              <h4 className={`text-base font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Cookie Settings</h4>
              <p className={`text-xs mt-1 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                We use cookies to optimize your documentation reading experience.
              </p>
            </div>
          </div>
          <button 
            onClick={() => setIsOpen(false)}
            className={`p-1.5 rounded-lg transition ${isDark ? 'text-gray-500 hover:text-white hover:bg-white/5' : 'text-gray-400 hover:text-gray-900 hover:bg-gray-100'}`}
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Details Toggle Panel */}
        {showDetails ? (
          <div className="space-y-3 pt-2">
            {/* Essential */}
            <div className="flex justify-between items-start gap-4">
              <div className="space-y-0.5">
                <span className={`text-xs font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Essential Cookies</span>
                <p className={`text-[10px] ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>Required for secure sessions and theme persistence.</p>
              </div>
              <div className="flex items-center">
                <span className="text-[10px] text-aquilia-500 bg-aquilia-500/10 px-2 py-0.5 rounded-md font-semibold">Always Active</span>
              </div>
            </div>

            {/* Analytics */}
            <div className="flex justify-between items-start gap-4 pt-2 border-t border-gray-100 dark:border-white/5">
              <div className="space-y-0.5">
                <span className={`text-xs font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Analytics</span>
                <p className={`text-[10px] ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>Used to analyze user traffic and documentation reading patterns.</p>
              </div>
              <button
                onClick={() => setPreferences({ ...preferences, analytics: !preferences.analytics })}
                className={`w-8 h-4 rounded-full transition-colors relative ${preferences.analytics ? 'bg-aquilia-500' : 'bg-gray-300 dark:bg-zinc-700'}`}
              >
                <div className={`w-3.5 h-3.5 rounded-full bg-white absolute top-0.25 transition-transform ${preferences.analytics ? 'translate-x-4' : 'translate-x-0.5'}`} />
              </button>
            </div>

            {/* Marketing */}
            <div className="flex justify-between items-start gap-4 pt-2 border-t border-gray-100 dark:border-white/5">
              <div className="space-y-0.5">
                <span className={`text-xs font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Marketing</span>
                <p className={`text-[10px] ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>Used for tailoring framework updates and community announcement newsletters.</p>
              </div>
              <button
                onClick={() => setPreferences({ ...preferences, marketing: !preferences.marketing })}
                className={`w-8 h-4 rounded-full transition-colors relative ${preferences.marketing ? 'bg-aquilia-500' : 'bg-gray-300 dark:bg-zinc-700'}`}
              >
                <div className={`w-3.5 h-3.5 rounded-full bg-white absolute top-0.25 transition-transform ${preferences.marketing ? 'translate-x-4' : 'translate-x-0.5'}`} />
              </button>
            </div>
          </div>
        ) : null}

        {/* Action Buttons */}
        <div className="flex items-center gap-2 pt-2">
          <button
            onClick={() => setShowDetails(!showDetails)}
            className={`flex items-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-xl border transition ${
              isDark 
                ? 'border-white/10 hover:border-white/20 text-gray-300 hover:text-white bg-white/5' 
                : 'border-gray-200 hover:border-gray-300 text-gray-700 hover:text-gray-900 bg-white'
            }`}
          >
            <Settings className="w-3.5 h-3.5" />
            Customize
          </button>
          
          {showDetails ? (
            <button
              onClick={handleSave}
              className="flex-1 py-2 text-xs font-semibold text-white bg-aquilia-500 hover:bg-aquilia-600 rounded-xl transition flex items-center justify-center gap-1.5"
            >
              <Check className="w-3.5 h-3.5" />
              Save Preferences
            </button>
          ) : (
            <button
              onClick={handleAcceptAll}
              className="flex-1 py-2 text-xs font-semibold text-white bg-aquilia-500 hover:bg-aquilia-600 rounded-xl transition"
            >
              Accept All
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
