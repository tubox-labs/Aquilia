import { Navbar } from '../components/Navbar'
import { Footer } from '../components/Footer'
import { useTheme } from '../context/ThemeContext'
import { Github, Users, MessageSquare, ArrowRight } from 'lucide-react'
import { SEO } from '../components/SEO'

export function CommunityPage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const schema = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "WebPage",
        "@id": "https://tubox.cloud/community#webpage",
        "name": "Developer Community & Ecosystem — Aquilia",
        "description": "Join the Aquilia framework community. Connect on GitHub, Discord, and Slack, and contribute to the async Python ecosystem.",
        "url": "https://tubox.cloud/community"
      },
      {
        "@type": "BreadcrumbList",
        "@id": "https://tubox.cloud/community#breadcrumbs",
        "itemListElement": [
          { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://tubox.cloud/" },
          { "@type": "ListItem", "position": 2, "name": "Community", "item": "https://tubox.cloud/community" }
        ]
      }
    ]
  }

  return (
    <div className={`min-h-screen flex flex-col ${isDark ? 'bg-black text-gray-100' : 'bg-gray-50 text-gray-900'}`}>
      <SEO
        title="Developer Community & Ecosystem — Aquilia"
        description="Join the Aquilia framework community. Connect on GitHub, Discussions, and contribute to the async Python ecosystem."
        keywords="Aquilia community, Python open source community, async Python framework community, contribute to Aquilia"
        schema={schema}
      />
      <Navbar />

      <main className="flex-grow max-w-4xl mx-auto px-6 py-16 w-full space-y-16">
        {/* Header */}
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium">
            <Users className="w-4 h-4" />
            Connect / Build
          </div>
          <h1 className="text-4xl font-bold tracking-tighter">
            <span className="gradient-text font-mono relative group inline-block">
              Community Space
              <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
            </span>
          </h1>
          <p className={`text-base leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Join our growing community of developers building production-grade asynchronous web applications, database pipelines, and APIs with Aquilia.
          </p>
        </div>

        {/* Channels Grid */}
        <section className="space-y-6">
          <h2 className="text-xl font-bold font-mono">Community Hubs</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Github discussions */}
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
              <h3 className="font-bold text-sm pt-2">GitHub Discussions</h3>
              <p className={`text-xs leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                Share projects, request comments, post RFCs, and collaborate with other developers.
              </p>
            </a>

            {/* Contributor Space */}
            <a 
              href="https://github.com/tubox-labs/Aquilia" 
              target="_blank" 
              rel="noopener"
              className={`group block space-y-2 p-6 rounded-2xl border transition-all ${
                isDark 
                  ? 'border-white/5 bg-zinc-950/20 hover:border-aquilia-500/20 hover:bg-aquilia-500/[0.02]' 
                  : 'border-gray-200 bg-white hover:border-aquilia-500/20 hover:bg-aquilia-500/[0.01]'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="p-2.5 rounded-xl bg-purple-500/10 text-purple-500">
                  <Github className="w-5 h-5" />
                </div>
                <ArrowRight className="w-4 h-4 text-gray-400 group-hover:text-aquilia-500 transition-colors" />
              </div>
              <h3 className="font-bold text-sm pt-2">Open Source Repository</h3>
              <p className={`text-xs leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                Explore the Python framework implementation, clone the repository, run test pipelines, or submit Pull Requests.
              </p>
            </a>
          </div>
        </section>

        {/* Contributing */}
        <section className="space-y-4">
          <h2 className="text-xl font-bold font-mono">How to Contribute</h2>
          <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            We welcome code contributions, performance optimizations, custom middlewares, and documentation updates. Read our contribution guide on GitHub to set up your environment, write tests using <code className="text-aquilia-500">pytest</code>, and follow the pre-commit checks.
          </p>
        </section>
      </main>

      <Footer />
    </div>
  )
}
