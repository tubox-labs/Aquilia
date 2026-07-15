import { Navbar } from '../components/Navbar'
import { Footer } from '../components/Footer'
import { useTheme } from '../context/ThemeContext'
import { MessageSquare, AlertCircle, HelpCircle, ArrowRight } from 'lucide-react'
import { SEO } from '../components/SEO'


export function HelpPage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const schema = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "FAQPage",
        "@id": "https://tubox.cloud/help#faq",
        "mainEntity": [
          {
            "@type": "Question",
            "name": "What is ScopeViolationError?",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "This occurs when a SINGLETON scoped service attempts to inject a REQUEST or transient scoped dependency in its constructor. Ensure constructor injections match or use a factory method instead."
            }
          },
          {
            "@type": "Question",
            "name": "What is PatternSyntaxError?",
            "acceptedAnswer": {
              "@type": "Answer",
              "text": "Triggered if your URL parameter syntax is malformed. Ensure you use the updated curly brace format (e.g. {id:int}) and not the legacy chevron tags."
            }
          }
        ]
      },
      {
        "@type": "BreadcrumbList",
        "@id": "https://tubox.cloud/help#breadcrumbs",
        "itemListElement": [
          { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://tubox.cloud/" },
          { "@type": "ListItem", "position": 2, "name": "Help & Support", "item": "https://tubox.cloud/help" }
        ]
      }
    ]
  }

  return (
    <div className={`min-h-screen flex flex-col ${isDark ? 'bg-black text-gray-100' : 'bg-gray-50 text-gray-900'}`}>
      <SEO
        title="Help Center & Support — Aquilia"
        description="Find resources, FAQs, troubleshooting guides, and community channels to resolve issues with the Aquilia Python framework."
        keywords="Aquilia support, help center, ScopeViolationError, PatternSyntaxError, Python framework support"
        schema={schema}
      />
      <Navbar />

      <main className="flex-grow max-w-4xl mx-auto px-6 py-16 w-full space-y-16">
        {/* Header */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium">
            <HelpCircle className="w-4 h-4" />
            Support / Troubleshooting
          </div>
          <h1 className="text-4xl font-bold tracking-tighter">
            <span className="gradient-text font-mono relative group inline-block">
              Help Center
              <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
            </span>
          </h1>
          <p className={`text-base leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Encountered an issue or have questions about the Aquilia framework? Our developer resources are designed to get you unblocked quickly.
          </p>
        </div>

        {/* GitHub Support Actions */}
        <section className="space-y-6">
          <h2 className="text-xl font-bold font-mono">Official Support Channels</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Raise Issue */}
            <a 
              href="https://github.com/tubox-labs/Aquilia/issues" 
              target="_blank" 
              rel="noopener"
              className={`group block space-y-2 p-6 rounded-2xl border transition-all ${
                isDark 
                  ? 'border-white/5 bg-zinc-950/20 hover:border-aquilia-500/20 hover:bg-aquilia-500/[0.02]' 
                  : 'border-gray-200 bg-white hover:border-aquilia-500/20 hover:bg-aquilia-500/[0.01]'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="p-2.5 rounded-xl bg-red-500/10 text-red-500">
                  <AlertCircle className="w-5 h-5" />
                </div>
                <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-aquilia-500 transition-colors" />
              </div>
              <h3 className="font-bold text-sm pt-2">Report an Issue</h3>
              <p className={`text-xs leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                Found a bug or incorrect compiler behavior? Raise an issue on our GitHub repository with reproduction steps.
              </p>
            </a>

            {/* Discussions */}
            <a 
              href="https://github.com/tubox-labs/Aquilia/discussions" 
              target="_blank" 
              rel="noopener"
              className={`group block space-y-2 p-6 rounded-2xl border transition-all ${
                isDark 
                  ? 'border-white/5 bg-zinc-950/20 hover:border-aquilia-500/20 hover:bg-aquilia-500/[0.02]' 
                  : 'border-gray-200 bg-white hover:border-aquilia-500/20 hover:bg-aquilia-500/[0.01]'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="p-2.5 rounded-xl bg-aquilia-500/10 text-aquilia-500">
                  <MessageSquare className="w-5 h-5" />
                </div>
                <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-aquilia-500 transition-colors" />
              </div>
              <h3 className="font-bold text-sm pt-2">Join GitHub Discussions</h3>
              <p className={`text-xs leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                Have a question about DI scopes, session adapters, or custom URL routing? Start a thread or seek advice from the community.
              </p>
            </a>
          </div>
        </section>

        {/* Common Troubleshooting */}
        <section className="space-y-6">
          <h2 className="text-xl font-bold font-mono">Frequently Encountered Errors</h2>
          <div className="space-y-4">
            <div className="space-y-1">
              <h3 className="text-sm font-semibold">ScopeViolationError</h3>
              <p className={`text-xs leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                This occurs when a <code className="text-aquilia-500">SINGLETON</code> scoped service attempts to inject a <code className="text-aquilia-500">REQUEST</code> or transient scoped dependency in its constructor. Ensure constructor injections match or use a factory method instead.
              </p>
            </div>
            <div className="space-y-1">
              <h3 className="text-sm font-semibold">PatternSyntaxError</h3>
              <p className={`text-xs leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                Triggered if your URL parameter syntax is malformed. Ensure you use the updated curly brace format (e.g. <code className="text-aquilia-500">{"{id:int}"}</code>) and not the legacy chevron tags.
              </p>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  )
}
