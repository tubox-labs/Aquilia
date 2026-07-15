import { Link } from 'react-router-dom'
import { Navbar } from '../components/Navbar'
import { Footer } from '../components/Footer'
import { Sidebar } from '../components/Sidebar'
import { useTheme } from '../context/ThemeContext'
import {
  Check, Copy, ArrowRight, ExternalLink, BookOpen, FileText, Github, Terminal, Download
} from 'lucide-react'
import { useState, useEffect } from 'react'
import { useVersion } from '../hooks/useVersion'
import { motion } from 'framer-motion'
import { ReleaseTimeline } from '../components/ReleaseTimeline'
import { SEO } from '../components/SEO'

interface ReleaseAsset {
  name: string
  size: string
  type: string
  downloadUrl?: string
}

interface ReleaseEntry {
  version: string
  codename: string
  date: string
  tag: 'latest' | 'stable' | 'pre-release'
  python: string[]
  license: string
  summary: string
  highlights: string[]
  assets: ReleaseAsset[]
  installCmd: string
  commitCount: string
  contributors: number
}

const staticReleases: ReleaseEntry[] = [
  {
    version: '1.2.2',
    codename: 'Kraken\'s Wake',
    date: 'Jul 01, 2026',
    tag: 'latest',
    python: ['3.10', '3.11', '3.12', '3.13'],
    license: 'MIT',
    summary: 'Database integrate configuration, ORM schema expressions, CLI auto-discovery sync.',
    highlights: [],
    assets: [
      { name: 'aquilia-1.2.2.tar.gz', size: '2.4 MB', type: 'Source' },
      { name: 'aquilia-1.2.2-py3-none-any.whl', size: '1.9 MB', type: 'Wheel' }
    ],
    installCmd: 'pip install aquilia==1.2.2',
    commitCount: '15',
    contributors: 1
  },
  {
    version: '1.2.1',
    codename: 'Kraken\'s Wake',
    date: 'Jul 01, 2026',
    tag: 'stable',
    python: ['3.10', '3.11', '3.12', '3.13'],
    license: 'MIT',
    summary: 'Startup decoupling, lazy jinja2 imports, Windows file locking.',
    highlights: [],
    assets: [
      { name: 'aquilia-1.2.1.tar.gz', size: '2.4 MB', type: 'Source' },
      { name: 'aquilia-1.2.1-py3-none-any.whl', size: '1.9 MB', type: 'Wheel' }
    ],
    installCmd: 'pip install aquilia==1.2.1',
    commitCount: '8',
    contributors: 1
  },
  {
    version: '1.2.0',
    codename: 'Kraken\'s Wake',
    date: 'Jun 28, 2026',
    tag: 'stable',
    python: ['3.10', '3.11', '3.12', '3.13'],
    license: 'MIT',
    summary: 'API versioning override, Request Inspector, database rollbacks/seed/flush, cProfile.',
    highlights: [],
    assets: [
      { name: 'aquilia-1.2.0.tar.gz', size: '2.4 MB', type: 'Source' },
      { name: 'aquilia-1.2.0-py3-none-any.whl', size: '1.9 MB', type: 'Wheel' }
    ],
    installCmd: 'pip install aquilia==1.2.0',
    commitCount: '120',
    contributors: 2
  },
  {
    version: '1.1.2',
    codename: 'Crimson Gale',
    date: 'Jun 12, 2026',
    tag: 'stable',
    python: ['3.10', '3.11', '3.12', '3.13'],
    license: 'MIT',
    summary: 'Middleware name scoping, dot-env overrides, workspace configuration.',
    highlights: [],
    assets: [
      { name: 'aquilia-1.1.2.tar.gz', size: '2.3 MB', type: 'Source' },
      { name: 'aquilia-1.1.2-py3-none-any.whl', size: '1.8 MB', type: 'Wheel' }
    ],
    installCmd: 'pip install aquilia==1.1.2',
    commitCount: '14',
    contributors: 1
  },
  {
    version: '1.1.1',
    codename: 'Sea Serpent',
    date: 'Jun 09, 2026',
    tag: 'stable',
    python: ['3.10', '3.11', '3.12', '3.13'],
    license: 'MIT',
    summary: 'Deleted config_builders, unified Workspace module, thread-safe dotenv.',
    highlights: [],
    assets: [
      { name: 'aquilia-1.1.1.tar.gz', size: '2.3 MB', type: 'Source' },
      { name: 'aquilia-1.1.1-py3-none-any.whl', size: '1.8 MB', type: 'Wheel' }
    ],
    installCmd: 'pip install aquilia==1.1.1',
    commitCount: '9',
    contributors: 1
  },
  {
    version: '1.1.0',
    codename: 'Black Pearl',
    date: 'Jun 08, 2026',
    tag: 'stable',
    python: ['3.10', '3.11', '3.12', '3.13'],
    license: 'MIT',
    summary: 'SSE, OpenTelemetry, @validate_body, SqlitePoolConfig.',
    highlights: [],
    assets: [
      { name: 'aquilia-1.1.0.tar.gz', size: '2.3 MB', type: 'Source' },
      { name: 'aquilia-1.1.0-py3-none-any.whl', size: '1.8 MB', type: 'Wheel' }
    ],
    installCmd: 'pip install aquilia==1.1.0',
    commitCount: '185',
    contributors: 2
  },
  {
    version: '1.0.5',
    codename: 'Jolly Roger',
    date: 'Jun 04, 2026',
    tag: 'stable',
    python: ['3.10', '3.11', '3.12'],
    license: 'MIT',
    summary: 'Aquilia MCP server, Surp binary serialization.',
    highlights: [],
    assets: [
      { name: 'aquilia-1.0.5.tar.gz', size: '2.1 MB', type: 'Source' },
      { name: 'aquilia-1.0.5-py3-none-any.whl', size: '1.8 MB', type: 'Wheel' }
    ],
    installCmd: 'pip install aquilia==1.0.5',
    commitCount: '18',
    contributors: 1
  },
  {
    version: '1.0.4',
    codename: 'Genesis P4',
    date: 'May 17, 2026',
    tag: 'stable',
    python: ['3.10', '3.11', '3.12', '3.13'],
    license: 'MIT',
    summary: 'Removed workspace compile gates, native python runtime.',
    highlights: [],
    assets: [
      { name: 'aquilia-1.0.4.tar.gz', size: '2.1 MB', type: 'Source' },
      { name: 'aquilia-1.0.4-py3-none-any.whl', size: '1.8 MB', type: 'Wheel' }
    ],
    installCmd: 'pip install aquilia==1.0.4',
    commitCount: '25',
    contributors: 1
  },
  {
    version: '1.0.3',
    codename: 'Genesis P3',
    date: 'Apr 19, 2026',
    tag: 'stable',
    python: ['3.10', '3.11', '3.12'],
    license: 'MIT',
    summary: 'Route cache compilation, OpenAPI schema molds.',
    highlights: [],
    assets: [
      { name: 'aquilia-1.0.3.tar.gz', size: '2.1 MB', type: 'Source' },
      { name: 'aquilia-1.0.3-py3-none-any.whl', size: '1.8 MB', type: 'Wheel' }
    ],
    installCmd: 'pip install aquilia==1.0.3',
    commitCount: '14',
    contributors: 1
  },
  {
    version: '1.0.2',
    codename: 'Genesis P2',
    date: 'Apr 02, 2026',
    tag: 'stable',
    python: ['3.10', '3.11', '3.12'],
    license: 'MIT',
    summary: 'SQLite connector pools, transaction commits, cookie session transport.',
    highlights: [],
    assets: [
      { name: 'aquilia-1.0.2.tar.gz', size: '2.1 MB', type: 'Source' },
      { name: 'aquilia-1.0.2-py3-none-any.whl', size: '1.8 MB', type: 'Wheel' }
    ],
    installCmd: 'pip install aquilia==1.0.2',
    commitCount: '32',
    contributors: 1
  },
  {
    version: '1.0.1',
    codename: 'Framework Audit',
    date: 'Mar 08, 2026',
    tag: 'stable',
    python: ['3.10', '3.11', '3.12'],
    license: 'MIT',
    summary: 'Security audit phases 1-15, Argon2, path normalization, JSON bytecode.',
    highlights: [],
    assets: [
      { name: 'aquilia-1.0.1.tar.gz', size: '2.1 MB', type: 'Source' },
      { name: 'aquilia-1.0.1-py3-none-any.whl', size: '1.8 MB', type: 'Wheel' }
    ],
    installCmd: 'pip install aquilia==1.0.1',
    commitCount: '47',
    contributors: 1
  },
  {
    version: '1.0.1a4',
    codename: 'Genesis Alpha 4',
    date: 'Mar 13, 2026',
    tag: 'pre-release',
    python: ['3.10', '3.11', '3.12'],
    license: 'MIT',
    summary: 'Pre-release testing draft containing Windows smoke tests and OIDC Trusted Publisher pipelines.',
    highlights: [],
    assets: [
      { name: 'aquilia-1.0.1a4.tar.gz', size: '1.8 MB', type: 'Source' }
    ],
    installCmd: 'pip install aquilia==1.0.1a4',
    commitCount: '19',
    contributors: 1
  },
  {
    version: '1.0.1a3',
    codename: 'Genesis Alpha 3',
    date: 'Mar 12, 2026',
    tag: 'pre-release',
    python: ['3.10', '3.11', '3.12'],
    license: 'MIT',
    summary: 'Early pre-release containing basic testing pattern frameworks.',
    highlights: [],
    assets: [],
    installCmd: 'pip install aquilia==1.0.1a3',
    commitCount: '4',
    contributors: 1
  },
  {
    version: '1.0.0',
    codename: 'Genesis',
    date: 'Feb 22, 2026',
    tag: 'stable',
    python: ['3.10', '3.11', '3.12'],
    license: 'MIT',
    summary: 'Initial stable release, ASGI, DI container, manifest architecture.',
    highlights: [],
    assets: [
      { name: 'aquilia-1.0.0.tar.gz', size: '2.1 MB', type: 'Source' },
      { name: 'aquilia-1.0.0-py3-none-any.whl', size: '1.8 MB', type: 'Wheel' },
    ],
    installCmd: 'pip install aquilia==1.0.0',
    commitCount: '500+',
    contributors: 1,
  },
]

const tagColors: Record<string, { bg: string; text: string }> = {
  latest: { bg: 'bg-aquilia-500/10 text-aquilia-400 border border-aquilia-500/20', text: 'text-aquilia-400' },
  stable: { bg: 'bg-blue-500/10 text-blue-400 border border-blue-500/20', text: 'text-blue-400' },
  'pre-release': { bg: 'bg-amber-500/10 text-amber-400 border border-amber-500/20', text: 'text-amber-400' },
}

function UpgradePath({ isDark, version }: { isDark: boolean; version: string }) {
  return (
    <div className="mt-16 pt-16 border-t border-white/[0.04]">
      <div className="mb-8">
        <h3 className={`text-xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Upgrade Guide</h3>
        <p className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>Steps to get started or upgrade to v{version}</p>
      </div>

      <div className="space-y-8">
        {[
          {
            step: '01',
            title: 'Install or upgrade Aquilia',
            description: 'Install the latest stable release from PyPI.',
            command: `pip install aquilia==${version}`,
            note: 'For MLOps features, add the extras:',
            extras: ['pip install aquilia[mlops]', 'pip install aquilia[dev]'],
          },
          {
            step: '02',
            title: 'Initialize your project',
            description: 'Scaffold a new project with the CLI.',
            command: 'aq init workspace myproject',
            note: 'This creates the manifest, config, and directory structure.',
          },
          {
            step: '03',
            title: 'Start the development server',
            description: 'Launch the server with live reload.',
            command: 'aq run',
            note: 'Your app will be running with live reloading and CSP options.',
          },
          {
            step: '04',
            title: 'Discover workspace components',
            description: 'Validate and sync routes and modules.',
            command: 'aq discover',
            note: 'Use aq discover to sync manifests and auto-discover routes.',
          },
        ].map(item => (
          <div key={item.step} className="flex gap-6">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold font-mono ${isDark ? 'bg-white/5 text-gray-400 border border-white/10' : 'bg-gray-100 text-gray-600 border border-gray-200'} flex-shrink-0`}>
              {item.step}
            </div>
            <div className="flex-1">
              <h4 className={`text-sm font-bold mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>{item.title}</h4>
              <p className={`text-xs mb-3 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>{item.description}</p>
              
              <div className="flex items-center gap-2 text-sm font-semibold font-mono text-aquilia-400 mb-2">
                <Terminal className="w-4 h-4 text-aquilia-500/80" />
                <span>{item.command}</span>
              </div>

              {item.extras && (
                <div className="mt-2 space-y-1">
                  {item.extras.map((ext, j) => (
                    <div key={j} className="flex items-center gap-2 font-mono text-xs text-gray-500">
                      <Terminal className="w-3.5 h-3.5 opacity-60" />
                      <span>{ext}</span>
                    </div>
                  ))}
                </div>
              )}

              {item.note && (
                <p className={`text-[10px] mt-1 ${isDark ? 'text-gray-600' : 'text-gray-400'}`}>{item.note}</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export function Releases({ printMode = false }: { printMode?: boolean }) {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const latestStableVersion = useVersion()
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [copiedCmd, setCopiedCmd] = useState<string | null>(null)
  const [gitReleases, setGitReleases] = useState<ReleaseEntry[]>(printMode ? staticReleases : [])
  const [isLoading, setIsLoading] = useState(!printMode)

  const copyText = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopiedCmd(text)
    setTimeout(() => setCopiedCmd(null), 2000)
  }

  const schema = {
    "@context": "https://schema.org",
    "@graph": [
      {
        "@type": "CollectionPage",
        "@id": "https://aquilia.tubox.cloud/releases#webpage",
        "name": "Releases & Version History — Aquilia",
        "description": "Stay up to date with the latest releases, features, bug fixes, and upgrades of the Aquilia Python framework.",
        "url": "https://aquilia.tubox.cloud/releases"
      },
      {
        "@type": "BreadcrumbList",
        "@id": "https://aquilia.tubox.cloud/releases#breadcrumbs",
        "itemListElement": [
          { "@type": "ListItem", "position": 1, "name": "Home", "item": "https://aquilia.tubox.cloud/" },
          { "@type": "ListItem", "position": 2, "name": "Releases", "item": "https://aquilia.tubox.cloud/releases" }
        ]
      }
    ]
  }

  useEffect(() => {
    if (printMode) return

    fetch('https://api.github.com/repos/tubox-labs/Aquilia/tags')
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch')
        return res.json()
      })
      .then(data => {
        if (!Array.isArray(data) || data.length === 0) {
          throw new Error('Invalid tags data')
        }
        
        let latestStable = '1.2.2'
        for (let k = 0; k < data.length; k++) {
          const v = data[k].name.replace(/^v/, '')
          if (!/[ab]|rc|dev|pre/i.test(v)) {
            latestStable = v
            break
          }
        }

        const enriched = data.map((tag: any) => {
          const version = tag.name.replace(/^v/, '')
          const staticMatch = staticReleases.find(r => r.version === version)
          return {
            version,
            codename: staticMatch?.codename || 'Release',
            date: staticMatch?.date || 'Jul 1, 2026',
            tag: version === latestStable ? 'latest' as const : /[ab]|rc|dev|pre/i.test(version) ? 'pre-release' as const : 'stable' as const,
            python: ['3.10', '3.11', '3.12', '3.13'],
            license: 'MIT',
            summary: staticMatch?.summary || 'Official release details on GitHub.',
            highlights: [],
            assets: staticMatch?.assets || [
              { name: `aquilia-${version}.tar.gz`, size: 'TBD', type: 'Source' },
              { name: `aquilia-${version}-py3-none-any.whl`, size: 'TBD', type: 'Wheel' }
            ],
            installCmd: `pip install aquilia==${version}`,
            commitCount: staticMatch?.commitCount || 'TBD',
            contributors: 1
          }
        }) as ReleaseEntry[]
        
        setGitReleases(enriched)
        setIsLoading(false)
      })
      .catch(err => {
        console.error('Github API failed, falling back to static releases:', err)
        setGitReleases(staticReleases)
        setIsLoading(false)
      })
  }, [printMode])

  if (printMode) {
    return (
      <div className="space-y-16">
        <div className={`relative pl-8 sm:pl-12 border-l-2 ${isDark ? 'border-zinc-800' : 'border-zinc-200'} space-y-16 py-4`}>
          {gitReleases.map((release) => (
            <div key={release.version} className="relative">
              {/* Timeline node point */}
              <div className={`absolute -left-[41px] sm:-left-[57px] top-2.5 w-4 h-4 rounded-full border-2 ${isDark ? 'bg-black border-zinc-800' : 'bg-white border-zinc-200'} flex items-center justify-center`}>
                <div className={`w-1.5 h-1.5 rounded-full bg-blue-400`} />
              </div>

              {/* Release Header */}
              <div className="mb-6">
                <div className="flex flex-col sm:flex-row sm:items-baseline gap-3 mb-2">
                  <h2 className={`text-3xl font-extrabold font-mono tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
                    v{release.version}
                  </h2>
                  <span className={`px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded-full ${tagColors[release.tag]?.bg || 'bg-blue-500/10 text-blue-400'} ${tagColors[release.tag]?.text || 'text-white'}`}>
                    {release.tag}
                  </span>
                  <span className={`text-sm italic ${isDark ? 'text-aquilia-400/80' : 'text-aquilia-600/80'}`}>
                    "{release.codename}"
                  </span>
                  <span className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'} ml-auto`}>
                    {release.date}
                  </span>
                </div>
              </div>

              <p className={`text-sm leading-relaxed mb-6 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                {release.summary}
              </p>

              {/* Installation */}
              <div className="mb-6">
                <h3 className={`text-xs font-bold uppercase tracking-wider mb-3 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                  Quick Install
                </h3>
                <div className="flex items-center gap-3">
                  <span className={`font-mono text-sm font-semibold ${isDark ? 'text-aquilia-400' : 'text-aquilia-600'}`}>
                    {release.installCmd}
                  </span>
                </div>
              </div>

              {/* Assets */}
              {release.assets && release.assets.length > 0 && (
                <div className="mb-6">
                  <h3 className={`text-xs font-bold uppercase tracking-wider mb-3 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                    Downloads
                  </h3>
                  <div className="space-y-2">
                    {release.assets.map((asset, i) => (
                      <div
                        key={i}
                        className={`flex items-center justify-between py-2 px-3 rounded-lg text-xs ${
                          isDark ? 'text-gray-300' : 'text-gray-700'
                        }`}
                      >
                        <span className="font-mono flex items-center gap-2">
                          • {asset.name}
                        </span>
                        <span className={`text-[10px] ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                          {asset.type} • {asset.size}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Metadata summary */}
              <div className={`pt-4 border-t border-dashed border-white/[0.04] text-[11px] ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                <span>Distributed under MIT License • </span>
                <span>Published {release.date}</span>
              </div>
            </div>
          ))}
        </div>
        <UpgradePath isDark={isDark} version={latestStableVersion} />
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col overflow-x-hidden">
      <SEO
        title="Releases & Version History — Aquilia"
        description="Stay up to date with the latest releases, features, performance improvements, bug fixes, and upgrade notes of the Aquilia Python framework."
        keywords="Aquilia releases, Python web framework releases, async Python version history, Aquilia framework changelogs"
        schema={schema}
      />
      <Navbar onToggleSidebar={() => setIsSidebarOpen(true)} />
      <div className="lg:hidden">
        <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />
      </div>

      <main className="flex-grow pt-[var(--navbar-height,64px)] relative">
        {/* Background gradient only */}
        <div className="fixed inset-0 z-[-1] bg-gradient-to-b from-transparent via-[var(--bg-primary)]/80 to-[var(--bg-primary)]" />

        {/* Hero */}
        <section className={`relative pt-16 pb-12 overflow-hidden ${isDark ? 'bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-aquilia-900/20 via-black to-black' : ''}`}>
          <div className="max-w-[90rem] mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight mb-3">
                <span className="gradient-text font-mono">Releases</span>
              </h1>
              <p className={`text-base max-w-2xl ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                Official release history with downloads, installation instructions, and upgrade guides fetched directly from GitHub.
              </p>
            </motion.div>
          </div>
        </section>

        {/* Release Timeline — full-width */}
        <section className="pt-4 pb-8">
          <div className="max-w-[90rem] mx-auto px-4 sm:px-6 lg:px-8">
            <ReleaseTimeline isDark={isDark} />
          </div>
        </section>

        {/* Main Content — two-column */}
        <section className="pb-24">
          <div className="max-w-[90rem] mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex flex-col xl:flex-row gap-16">

              {/* LEFT — Release list as a vertical timeline */}
              <div className="flex-1 min-w-0">
                {isLoading ? (
                  <div className={`text-sm py-12 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                    Fetching latest releases from GitHub...
                  </div>
                ) : (
                  <div className={`relative pl-8 sm:pl-12 border-l-2 ${isDark ? 'border-zinc-800' : 'border-zinc-200'} space-y-16 py-4`}>
                    {gitReleases.map((release, idx) => (
                      <motion.div
                        key={release.version}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: idx * 0.1, duration: 0.5 }}
                        className="relative"
                      >
                        {/* Timeline node point */}
                        <div className={`absolute -left-[41px] sm:-left-[57px] top-2.5 w-4 h-4 rounded-full border-2 ${isDark ? 'bg-black border-zinc-800' : 'bg-white border-zinc-200'} flex items-center justify-center`}>
                          <div className={`w-1.5 h-1.5 rounded-full ${release.tag === 'latest' ? 'bg-aquilia-400' : release.tag === 'stable' ? 'bg-blue-400' : 'bg-amber-400'}`} />
                        </div>

                        {/* Release Header */}
                        <div className="mb-6">
                          <div className="flex flex-col sm:flex-row sm:items-baseline gap-3 mb-2">
                            <Link to={`/releases/${release.version}`}>
                              <h2 className={`text-3xl font-extrabold font-mono tracking-tight ${isDark ? 'text-white hover:text-aquilia-400' : 'text-gray-900 hover:text-aquilia-600'} transition-colors`}>
                                v{release.version}
                              </h2>
                            </Link>
                            <span className={`px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded-full ${tagColors[release.tag]?.bg || 'bg-blue-500/10 text-blue-400'} ${tagColors[release.tag]?.text || 'text-white'}`}>
                              {release.tag}
                            </span>
                            <span className={`text-sm italic ${isDark ? 'text-aquilia-400/80' : 'text-aquilia-600/80'}`}>
                              "{release.codename}"
                            </span>
                            <span className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'} ml-auto`}>
                              {release.date}
                            </span>
                          </div>
                        </div>

                        <p className={`text-sm leading-relaxed mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                          {release.summary}
                        </p>

                        <div className="mb-6">
                          <Link
                            to={`/releases/${release.version}`}
                            className={`inline-flex items-center gap-1 text-xs font-semibold ${
                              isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-500'
                            } transition-colors group/view`}
                          >
                            <span>Read Release Notes</span>
                            <ArrowRight className="w-3.5 h-3.5 group-hover/view:translate-x-0.5 transition-transform" />
                          </Link>
                        </div>

                        {/* Installation */}
                        <div className="mb-6">
                          <h3 className={`text-xs font-bold uppercase tracking-wider mb-3 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                            Quick Install
                          </h3>
                          <div className="flex items-center gap-3 group">
                            <Terminal className="w-4 h-4 text-aquilia-500/80" />
                            <span className={`font-mono text-sm font-semibold ${isDark ? 'text-aquilia-400' : 'text-aquilia-600'}`}>
                              {release.installCmd}
                            </span>
                            <button
                              onClick={() => copyText(release.installCmd)}
                              className={`p-1.5 rounded-lg transition-all ${isDark ? 'hover:bg-white/5 text-gray-500 hover:text-white' : 'hover:bg-gray-100 text-gray-400 hover:text-gray-700'}`}
                              title="Copy command"
                            >
                              {copiedCmd === release.installCmd ? <Check className="w-3.5 h-3.5 text-aquilia-500" /> : <Copy className="w-3.5 h-3.5" />}
                            </button>
                          </div>
                        </div>

                        {/* Assets */}
                        {release.assets && release.assets.length > 0 && (
                          <div className="mb-6">
                            <h3 className={`text-xs font-bold uppercase tracking-wider mb-3 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                              Downloads
                            </h3>
                            <div className="space-y-2">
                              {release.assets.map((asset, i) => (
                                <a
                                  key={i}
                                  href={asset.downloadUrl || '#'}
                                  target="_blank"
                                  rel="noopener"
                                  className={`flex items-center justify-between py-2 px-3 rounded-lg text-xs transition-colors ${
                                    isDark ? 'hover:bg-white/[0.02] text-gray-300' : 'hover:bg-gray-50 text-gray-700'
                                  }`}
                                >
                                  <span className="font-mono flex items-center gap-2">
                                    <Download className="w-3.5 h-3.5 text-gray-500/80" />
                                    {asset.name}
                                  </span>
                                  <span className={`text-[10px] ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                                    {asset.type} • {asset.size}
                                  </span>
                                </a>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Metadata summary (Clean inline text) */}
                        <div className={`pt-4 border-t border-dashed border-white/[0.04] text-[11px] ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                          <span>Distributed under MIT License • </span>
                          <span>Published {release.date}</span>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                )}

                {/* Upgrade Guide */}
                <UpgradePath isDark={isDark} version={latestStableVersion} />
              </div>

              {/* RIGHT — Premium sidebar (Quick Links only) */}
              <div className="xl:w-80 2xl:w-96 flex-shrink-0">
                <div className="xl:sticky xl:top-24">
                  {/* Quick Links */}
                  <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2, duration: 0.5 }}
                    className="space-y-4"
                  >
                    <h3 className={`text-xs font-bold uppercase tracking-wider ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                      Quick Links
                    </h3>
                    <div className="space-y-3">
                      <Link
                        to="/changelogs"
                        className={`flex items-center gap-2 py-2 text-sm font-medium transition-colors ${isDark ? 'text-gray-300 hover:text-white' : 'text-gray-700 hover:text-gray-900'}`}
                      >
                        <FileText className="w-4 h-4" />
                        <span className="flex-1">Full Changelog</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                      <Link
                        to="/docs"
                        className={`flex items-center gap-2 py-2 text-sm font-medium transition-colors ${isDark ? 'text-gray-300 hover:text-white' : 'text-gray-700 hover:text-gray-900'}`}
                      >
                        <BookOpen className="w-4 h-4" />
                        <span className="flex-1">Documentation</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                      <a
                        href="https://pypi.org/project/aquilia/"
                        target="_blank"
                        rel="noopener"
                        className={`flex items-center gap-2 py-2 text-sm font-medium transition-colors ${isDark ? 'text-gray-300 hover:text-white' : 'text-gray-700 hover:text-gray-900'}`}
                      >
                        <Github className="w-4 h-4" />
                        <span className="flex-1">PyPI Package</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>
                  </motion.div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <Footer />
    </div>
  )
}
