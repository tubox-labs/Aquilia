import { Navbar } from '../components/Navbar'
import { Footer } from '../components/Footer'
import { useTheme } from '../context/ThemeContext'
import { Shield } from 'lucide-react'

export function PrivacyPage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className={`min-h-screen flex flex-col ${isDark ? 'bg-black text-gray-100' : 'bg-gray-50 text-gray-900'}`}>
      <Navbar />

      <main className="flex-grow max-w-4xl mx-auto px-6 py-16 w-full space-y-12">
        {/* Header */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium">
            <Shield className="w-4 h-4" />
            Legal / Compliance
          </div>
          <h1 className="text-4xl font-bold tracking-tighter">
            <span className="gradient-text font-mono relative group inline-block">
              Privacy Policy
              <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
            </span>
          </h1>
          <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>Last updated: July 06, 2026</p>
        </div>

        {/* Content sections */}
        <div className={`space-y-8 text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <section className="space-y-3">
            <h2 className={`text-lg font-bold font-mono ${isDark ? 'text-white' : 'text-gray-900'}`}>1. Overview & Scope</h2>
            <p>
              Aquilia Framework is committed to protecting the privacy of developers visiting our documentation site. This Privacy Policy details the types of data we process, our purposes for doing so, and the controls available to you.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className={`text-lg font-bold font-mono ${isDark ? 'text-white' : 'text-gray-900'}`}>2. Cookie Preferences & Granular Consent</h2>
            <p>
              We employ a cookie preference panel enabling you to toggle non-essential cookies. Below is an overview of cookie categories used on this site:
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>
                <strong>Essential Cookies:</strong> Used exclusively to preserve critical preferences, such as your theme state (dark/light mode) and whether you have acknowledged our compliance statements. These cannot be disabled as the site cannot function properly without them.
              </li>
              <li>
                <strong>Analytics Cookies:</strong> Help us measure documentation usage (e.g., page views, scroll depth, and search query trends). You can toggle these cookies on or off through the Customize popup.
              </li>
              <li>
                <strong>Marketing / Notification Cookies:</strong> Used optionally to tailor announcements, framework update rollouts, and community newsletters.
              </li>
            </ul>
          </section>

          <section className="space-y-3">
            <h2 className={`text-lg font-bold font-mono ${isDark ? 'text-white' : 'text-gray-900'}`}>3. Server Logs & Hosting Environments</h2>
            <p>
              This documentation is served statically. The hosting infrastructure provider (such as GitHub Pages or Vercel) may log standard network requests, including IP addresses, browser user-agents, and request timestamps. These logs are processed by the hosting provider for security purposes, network routing, and DDoS mitigation under their respective privacy policies. We do not store or import these raw connection logs.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className={`text-lg font-bold font-mono ${isDark ? 'text-white' : 'text-gray-900'}`}>4. Developer Controls & Rights</h2>
            <p>
              As a visitor, you have full control over your browser data. You can clear your cookies, disable local storage, or modify your cookie consent choices at any time. Under regional frameworks like GDPR or CCPA, you have the right to visit our site without being tracked, which is why all analytics and marketing cookies remain disabled by default until you explicitly opt-in.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className={`text-lg font-bold font-mono ${isDark ? 'text-white' : 'text-gray-900'}`}>5. Contact & Feedback</h2>
            <p>
              If you have any questions or concerns regarding our privacy controls, please contact our maintainers or open a thread in the community discussions on GitHub.
            </p>
          </section>
        </div>
      </main>

      <Footer />
    </div>
  )
}
