import { Navbar } from '../components/Navbar'
import { Footer } from '../components/Footer'
import { useTheme } from '../context/ThemeContext'
import { FileText, AlertTriangle } from 'lucide-react'
import { SEO } from '../components/SEO'

export function TermsPage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const schema = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "WebPage",
        "@id": "https://tubox.cloud/terms#webpage",
        "name": "Terms of Service — Aquilia",
        "description": "Read the terms of service and acceptable use conditions for the Aquilia documentation site and services.",
        "url": "https://tubox.cloud/terms"
      },
      {
        "@type": "BreadcrumbList",
        "@id": "https://tubox.cloud/terms#breadcrumbs",
        "itemListElement": [
          { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://tubox.cloud/" },
          { "@type": "ListItem", "position": 2, "name": "Terms of Service", "item": "https://tubox.cloud/terms" }
        ]
      }
    ]
  }

  return (
    <div className={`min-h-screen flex flex-col ${isDark ? 'bg-black text-gray-100' : 'bg-gray-50 text-gray-900'}`}>
      <SEO
        title="Terms of Service — Aquilia"
        description="Read the terms of service for using Aquilia websites, documentation, and tools."
        keywords="terms of service, legal, acceptable use, Aquilia framework"
        schema={schema}
      />
      <Navbar />

      <main className="flex-grow max-w-4xl mx-auto px-6 py-16 w-full space-y-12">
        {/* Header */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium">
            <FileText className="w-4 h-4" />
            Legal / Terms of Use
          </div>
          <h1 className="text-4xl font-bold tracking-tighter">
            <span className="gradient-text font-mono relative group inline-block">
              Terms & Conditions
              <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
            </span>
          </h1>
          <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>Last updated: July 06, 2026</p>
        </div>

        {/* Warning Banner */}
        <div className="p-4 border-l-4 border-amber-500 bg-amber-500/5 rounded-r-xl space-y-2">
          <h4 className="font-bold text-sm text-amber-500 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" />
            WARNING: Template Content
          </h4>
          <p className={`text-xs leading-relaxed ${isDark ? 'text-amber-200/80' : 'text-amber-800'}`}>
            This page is a starting-point template, not legal advice. Have qualified legal counsel review and adapt it before relying on it for a production site.
          </p>
        </div>

        {/* Content sections */}
        <div className={`space-y-8 text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <p className={`text-xs italic ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
            Conditions for using the Aquilia documentation site. Template content — review with qualified legal counsel before production use.
          </p>

          <section className="space-y-3">
            <h2 className={`text-lg font-bold font-mono ${isDark ? 'text-white' : 'text-gray-900'}`}>1. Acceptable Use</h2>
            <p>
              The Aquilia documentation is provided for reference and educational purposes. You agree not to misuse the site, attempt to disrupt it, or use it in violation of applicable law.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className={`text-lg font-bold font-mono ${isDark ? 'text-white' : 'text-gray-900'}`}>2. Intellectual Property</h2>
            <p>
              The Aquilia framework is published under the license stated in its repository. The documentation content on this site is provided to support that framework; trademarks, logos, and brand elements remain the property of their respective owners.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className={`text-lg font-bold font-mono ${isDark ? 'text-white' : 'text-gray-900'}`}>3. Warranty Disclaimer</h2>
            <p>
              The documentation is provided "as is", without warranty of any kind, express or implied, including warranties of merchantability, fitness for a particular purpose, and non-infringement.
            </p>
          </section>

          <section className="space-y-3">
            <h2 className={`text-lg font-bold font-mono ${isDark ? 'text-white' : 'text-gray-900'}`}>4. Limitation of Liability</h2>
            <p>
              To the maximum extent permitted by law, in no event will the project, its maintainers, or its contributors be liable for any indirect, incidental, special, consequential or punitive damages arising out of or related to use of this site.
            </p>
          </section>
        </div>
      </main>

      <Footer />
    </div>
  )
}
