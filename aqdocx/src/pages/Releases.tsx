import { Link } from 'react-router-dom'
import { Navbar } from '../components/Navbar'
import { Sidebar } from '../components/Sidebar'
import { useTheme } from '../context/ThemeContext'
import {
  Package, Tag, Download, Github, Calendar, Star, GitCommit,
  Check, ChevronRight, ArrowRight, ExternalLink, FileText,
  Terminal, Copy, Cpu, Shield, Globe, Zap, Database,
  Users, Layers, BookOpen, HardDrive, Hash, Sparkles,
  Box, Rocket
} from 'lucide-react'
import { useState } from 'react'
import { motion } from 'framer-motion'
import { ReleaseTimeline } from '../components/ReleaseTimeline'

interface ReleaseAsset {
  name: string
  size: string
  type: string
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

const releases: ReleaseEntry[] = [
  {
    version: '1.0.0',
    codename: 'Genesis',
    date: 'February 28, 2026',
    tag: 'latest',
    python: ['3.10', '3.11', '3.12'],
    license: 'MIT',
    summary: 'The first production-ready release of Aquilia — a modern, async-native Python web framework featuring manifest-first architecture, a complete ORM, dependency injection, pluggable authentication, MLOps integration, and a full developer toolchain.',
    highlights: [
      'Async-native ASGI server with lifecycle hooks and graceful shutdown',
      'Manifest-first bootstrap → compile → serve architecture',
      'Class-based controllers with full HTTP method decorators',
      'Pure-Python async ORM with 30+ field types and migrations',
      'Hierarchical dependency injection with 6 lifetime scopes',
      'Blueprint system for model-to-world serialization contracts',
      'JWT authentication with RBAC, ABAC, OAuth2, and MFA support',
      'Multi-backend cache with LRU/LFU/TTL/FIFO eviction',
      'WebSocket support with namespace routing and guards',
      'Integrated MLOps toolkit for model training and deployment',
      'Comprehensive CLI with 40+ commands for development workflow',
      'Full test framework with async HTTP client and pytest integration',
      'Trace & artifact system for build introspection and supply-chain tracking',
    ],
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
  latest: { bg: 'bg-aquilia-500', text: 'text-black' },
  stable: { bg: 'bg-blue-500', text: 'text-white' },
  'pre-release': { bg: 'bg-amber-500', text: 'text-black' },
}

// ----- Release Graph Component — see src/components/ReleaseTimeline.tsx -----


// ----- Upgrade Path Component -----
function UpgradePath({ isDark }: { isDark: boolean }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5 }}
      className="overflow-hidden"
    >
      <div className="px-6 sm:px-8 py-5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-aquilia-500/10 flex items-center justify-center">
            <Rocket className="w-5 h-5 text-aquilia-500" />
          </div>
          <div>
            <h3 className={`text-lg font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Upgrade Guide</h3>
            <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>Steps to get started or upgrade to v1.0.0</p>
          </div>
        </div>
      </div>

      <div className="px-6 sm:px-8 py-6 space-y-5">
        {[
          {
            step: '01',
            title: 'Install or upgrade Aquilia',
            description: 'Install the latest stable release from PyPI.',
            command: 'pip install aquilia==1.0.0',
            note: 'For MLOps features, add the extras:',
            extras: ['pip install aquilia[mlops]', 'pip install aquilia[dev]'],
          },
          {
            step: '02',
            title: 'Initialize your project',
            description: 'Scaffold a new project with the CLI.',
            command: 'aq init myproject',
            note: 'This creates the manifest, config, and directory structure.',
          },
          {
            step: '03',
            title: 'Start the development server',
            description: 'Launch with hot-reload enabled.',
            command: 'aq serve --reload',
            note: 'Your app will be running at localhost:8000.',
          },
          {
            step: '04',
            title: 'Explore the routes',
            description: 'Inspect all compiled routes and controllers.',
            command: 'aq show routes',
            note: 'Use aq check to verify your manifest and DI graph.',
          },
        ].map((item, i) => (
          <motion.div
            key={item.step}
            initial={{ opacity: 0, x: -15 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ delay: i * 0.1, duration: 0.4 }}
            className="flex gap-4"
          >
            {/* Step number */}
            <div className="flex flex-col items-center flex-shrink-0">
              <div className={`w-9 h-9 rounded-xl flex items-center justify-center text-xs font-bold font-mono ${isDark ? 'bg-aquilia-500/10 text-aquilia-400 border border-aquilia-500/20' : 'bg-aquilia-50 text-aquilia-600 border border-aquilia-200'}`}>
                {item.step}
              </div>
              {i < 3 && (
                <div className={`w-px flex-1 mt-2 ${isDark ? 'bg-white/10' : 'bg-gray-200'}`} />
              )}
            </div>

            {/* Content */}
            <div className="flex-1 pb-5">
              <h4 className={`text-sm font-bold mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>{item.title}</h4>
              <p className={`text-xs mb-2.5 ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>{item.description}</p>

              {/* Plain text command — aquilia green */}
              <div className={`flex items-center gap-2 py-2 px-3 rounded-xl ${isDark ? 'bg-aquilia-500/5 border border-aquilia-500/10' : 'bg-aquilia-50/50 border border-aquilia-100'}`}>
                <ChevronRight className={`w-3 h-3 flex-shrink-0 ${isDark ? 'text-aquilia-500/50' : 'text-aquilia-400'}`} />
                <span className={`text-sm font-mono font-semibold ${isDark ? 'text-aquilia-400' : 'text-aquilia-600'}`}>{item.command}</span>
              </div>

              {item.extras && (
                <div className="mt-2 space-y-1.5">
                  {item.extras.map((ext, j) => (
                    <div key={j} className={`flex items-center gap-2 py-1.5 px-3 rounded-lg ${isDark ? 'bg-white/[0.02]' : 'bg-gray-50'}`}>
                      <ChevronRight className={`w-2.5 h-2.5 flex-shrink-0 ${isDark ? 'text-gray-600' : 'text-gray-300'}`} />
                      <span className={`text-xs font-mono ${isDark ? 'text-aquilia-400/70' : 'text-aquilia-600/70'}`}>{ext}</span>
                    </div>
                  ))}
                </div>
              )}

              {item.note && !item.extras && (
                <p className={`text-[10px] mt-1.5 ${isDark ? 'text-gray-600' : 'text-gray-400'}`}>{item.note}</p>
              )}
              {item.note && item.extras && (
                <p className={`text-[10px] mt-1 ${isDark ? 'text-gray-600' : 'text-gray-400'}`}>{item.note}</p>
              )}
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  )
}

export function Releases() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [copiedCmd, setCopiedCmd] = useState<string | null>(null)

  const copyText = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopiedCmd(text)
    setTimeout(() => setCopiedCmd(null), 2000)
  }

  return (
    <div className="min-h-screen flex flex-col overflow-x-hidden">
      <Navbar onToggleSidebar={() => setIsSidebarOpen(true)} />
      <div className="lg:hidden">
        <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />
      </div>

      <main className="flex-grow pt-16 relative">
        {/* Background */}
        <div className={`fixed inset-0 z-[-1] opacity-20 ${isDark ? '' : 'opacity-5'}`} style={{ backgroundImage: 'linear-gradient(#27272a 1px, transparent 1px), linear-gradient(90deg, #27272a 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
        <div className="fixed inset-0 z-[-1] bg-gradient-to-b from-transparent via-[var(--bg-primary)]/80 to-[var(--bg-primary)]" />

        {/* Hero */}
        <section className={`relative pt-12 pb-10 overflow-hidden ${isDark ? 'bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-aquilia-900/20 via-black to-black' : ''}`}>
          <div className={`absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)]`} />
          <div className="max-w-[90rem] mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <div className={`inline-flex items-center gap-2 mb-4 px-4 py-1.5 rounded-full border text-sm font-medium ${isDark ? 'border-aquilia-500/30 bg-aquilia-500/10 text-aquilia-400' : 'border-aquilia-600/30 bg-aquilia-500/10 text-aquilia-600'}`}>
                <Package className="w-4 h-4" />
                Releases
              </div>
              <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight mb-3">
                <span className="gradient-text font-mono">Release History</span>
              </h1>
              <p className={`text-lg max-w-2xl ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                Official releases with downloads, installation instructions, and upgrade guides.
              </p>
            </motion.div>
          </div>
        </section>

        {/* Release Timeline Graph — full-width */}
        <section className="pt-4 pb-8">
          <div className="max-w-[90rem] mx-auto px-4 sm:px-6 lg:px-8">
            <ReleaseTimeline isDark={isDark} />
          </div>
        </section>

        {/* Main Content — two-column */}
        <section className="pb-24">
          <div className="max-w-[90rem] mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex flex-col xl:flex-row gap-8">

              {/* LEFT — Release cards + Upgrade guide */}
              <div className="flex-1 min-w-0 space-y-8">
                {releases.map((release, idx) => (
                  <motion.div
                    key={release.version}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.1, duration: 0.5 }}
                    className="overflow-hidden"
                  >
                    {/* Release Header */}
                    <div className="p-6 sm:p-8">
                      <div className="flex flex-col sm:flex-row sm:items-center gap-4 mb-4">
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 rounded-xl bg-aquilia-500/10 flex items-center justify-center">
                            <Package className="w-6 h-6 text-aquilia-500" />
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <h2 className={`text-2xl font-bold font-mono ${isDark ? 'text-white' : 'text-gray-900'}`}>
                                v{release.version}
                              </h2>
                              <span className={`px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded-full ${tagColors[release.tag].bg} ${tagColors[release.tag].text}`}>
                                {release.tag}
                              </span>
                            </div>
                            <div className="flex items-center gap-2 mt-0.5">
                              <span className={`text-sm italic ${isDark ? 'text-aquilia-400/70' : 'text-aquilia-600/70'}`}>"{release.codename}"</span>
                              <span className={`text-xs ${isDark ? 'text-gray-600' : 'text-gray-400'}`}>•</span>
                              <span className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>{release.date}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                      <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                        {release.summary}
                      </p>
                    </div>

                    {/* Highlights */}
                    <div className="p-6 sm:p-8">
                      <h3 className={`text-sm font-bold uppercase tracking-wider mb-4 flex items-center gap-2 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                        <Star className="w-3.5 h-3.5 text-aquilia-500" />
                        Release Highlights
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        {release.highlights.map((hl, i) => (
                          <motion.div
                            key={i}
                            initial={{ opacity: 0, x: -10 }}
                            whileInView={{ opacity: 1, x: 0 }}
                            viewport={{ once: true }}
                            transition={{ delay: i * 0.03, duration: 0.3 }}
                            className="flex items-start gap-2"
                          >
                            <Check className="w-3.5 h-3.5 mt-0.5 text-aquilia-500 flex-shrink-0" />
                            <span className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>{hl}</span>
                          </motion.div>
                        ))}
                      </div>
                    </div>

                    {/* Installation — plain text, no code boxes */}
                    <div className="p-6 sm:p-8">
                      <h3 className={`text-sm font-bold uppercase tracking-wider mb-4 flex items-center gap-2 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                        <Terminal className="w-3.5 h-3.5 text-aquilia-500" />
                        Installation
                      </h3>

                      <div className="space-y-3">
                        {/* Primary install */}
                        <div className="flex items-center gap-3 group">
                          <div className={`flex items-center gap-2 flex-1 min-w-0`}>
                            <ArrowRight className={`w-3 h-3 flex-shrink-0 ${isDark ? 'text-aquilia-500/50' : 'text-aquilia-400'}`} />
                            <span className={`font-mono text-sm font-semibold ${isDark ? 'text-aquilia-400' : 'text-aquilia-600'}`}>
                              {release.installCmd}
                            </span>
                          </div>
                          <button
                            onClick={() => copyText(release.installCmd)}
                            className={`p-1.5 rounded-lg transition-all opacity-0 group-hover:opacity-100 ${isDark ? 'hover:bg-white/5 text-gray-500 hover:text-white' : 'hover:bg-gray-100 text-gray-400 hover:text-gray-700'}`}
                            title="Copy"
                          >
                            {copiedCmd === release.installCmd ? <Check className="w-3.5 h-3.5 text-aquilia-500" /> : <Copy className="w-3.5 h-3.5" />}
                          </button>
                        </div>

                        {/* Extras */}
                        <div className={`pl-5 space-y-2 border-l-2 ${isDark ? 'border-aquilia-500/10' : 'border-aquilia-100'}`}>
                          <p className={`text-[10px] uppercase tracking-wider font-medium ${isDark ? 'text-gray-600' : 'text-gray-400'}`}>Optional extras</p>
                          {[
                            { cmd: 'pip install aquilia[mlops]', label: 'MLOps toolkit' },
                            { cmd: 'pip install aquilia[dev]', label: 'Dev tools' },
                          ].map(extra => (
                            <div key={extra.cmd} className="flex items-center gap-3 group">
                              <div className="flex items-center gap-2 flex-1 min-w-0">
                                <ChevronRight className={`w-2.5 h-2.5 flex-shrink-0 ${isDark ? 'text-gray-700' : 'text-gray-300'}`} />
                                <span className={`font-mono text-xs ${isDark ? 'text-aquilia-400/70' : 'text-aquilia-600/70'}`}>
                                  {extra.cmd}
                                </span>
                                <span className={`text-[10px] ${isDark ? 'text-gray-700' : 'text-gray-300'}`}>— {extra.label}</span>
                              </div>
                              <button
                                onClick={() => copyText(extra.cmd)}
                                className={`p-1 rounded-lg transition-all opacity-0 group-hover:opacity-100 ${isDark ? 'hover:bg-white/5 text-gray-600' : 'hover:bg-gray-100 text-gray-400'}`}
                              >
                                {copiedCmd === extra.cmd ? <Check className="w-3 h-3 text-aquilia-500" /> : <Copy className="w-3 h-3" />}
                              </button>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>

                    {/* Assets */}
                    <div className="p-6 sm:p-8">
                      <h3 className={`text-sm font-bold uppercase tracking-wider mb-4 flex items-center gap-2 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                        <Download className="w-3.5 h-3.5 text-aquilia-500" />
                        Assets
                      </h3>
                      <div className="space-y-2">
                        {release.assets.map((asset, i) => (
                          <div
                            key={i}
                            className={`flex items-center justify-between p-3 rounded-xl border transition-colors ${isDark
                              ? 'bg-white/[0.02] border-white/5 hover:border-aquilia-500/20'
                              : 'bg-gray-50 border-gray-100 hover:border-aquilia-200'
                              }`}
                          >
                            <div className="flex items-center gap-3">
                              <HardDrive className={`w-4 h-4 ${isDark ? 'text-gray-500' : 'text-gray-400'}`} />
                              <div>
                                <div className={`text-sm font-mono font-medium ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>{asset.name}</div>
                                <div className={`text-xs ${isDark ? 'text-gray-600' : 'text-gray-400'}`}>{asset.type} • {asset.size}</div>
                              </div>
                            </div>
                            <Download className={`w-4 h-4 ${isDark ? 'text-gray-600 hover:text-aquilia-400' : 'text-gray-400 hover:text-aquilia-600'} transition-colors cursor-pointer`} />
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Checksums */}
                    <div className="p-6 sm:p-8">
                      <h3 className={`text-sm font-bold uppercase tracking-wider mb-4 flex items-center gap-2 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                        <Shield className="w-3.5 h-3.5 text-aquilia-500" />
                        Integrity
                      </h3>
                      <div className="space-y-2">
                        {[
                          { algo: 'SHA-256', file: 'aquilia-1.0.0.tar.gz', hash: 'a3f8c1d7e9b4...2f6a0e1c' },
                          { algo: 'SHA-256', file: 'aquilia-1.0.0-py3-none-any.whl', hash: 'b7e2d9f4a1c6...8d3b5e7f' },
                        ].map((ck, i) => (
                          <div key={i} className="flex items-center gap-3 group">
                            <span className={`text-[10px] uppercase tracking-wider font-bold w-14 ${isDark ? 'text-gray-600' : 'text-gray-400'}`}>{ck.algo}</span>
                            <span className={`font-mono text-xs truncate flex-1 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>{ck.hash}</span>
                            <span className={`text-[10px] truncate max-w-[140px] ${isDark ? 'text-gray-700' : 'text-gray-300'}`}>{ck.file}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Metadata bar */}
                    <div className={`px-6 sm:px-8 py-4 flex flex-wrap gap-x-6 gap-y-2 text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                      <span className="flex items-center gap-1.5">
                        <GitCommit className="w-3 h-3" /> {release.commitCount} commits
                      </span>
                      <span className="flex items-center gap-1.5">
                        <Users className="w-3 h-3" /> {release.contributors} contributor{release.contributors > 1 ? 's' : ''}
                      </span>
                      <span className="flex items-center gap-1.5">
                        <Tag className="w-3 h-3" /> {release.license} License
                      </span>
                      <span className="flex items-center gap-1.5">
                        <Calendar className="w-3 h-3" /> {release.date}
                      </span>
                    </div>
                  </motion.div>
                ))}

                {/* Upgrade Guide */}
                <UpgradePath isDark={isDark} />
              </div>

              {/* RIGHT — Sticky sidebar */}
              <div className="xl:w-80 2xl:w-96 flex-shrink-0">
                <div className="xl:sticky xl:top-24 space-y-5">

                  {/* Quick Install — plain text */}
                  <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.2, duration: 0.5 }}
                    className={`rounded-2xl border p-5 ${isDark ? 'bg-aquilia-500/5 border-aquilia-500/10' : 'bg-aquilia-50 border-aquilia-100'}`}
                  >
                    <h3 className={`text-xs font-bold uppercase tracking-wider mb-4 flex items-center gap-2 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                      <Zap className="w-3.5 h-3.5 text-aquilia-500" />
                      Quick Install
                    </h3>
                    <button
                      onClick={() => copyText('pip install aquilia')}
                      className={`w-full flex items-center gap-2 py-3 px-4 rounded-xl transition-all group ${isDark ? 'hover:bg-aquilia-500/10' : 'hover:bg-aquilia-100'}`}
                    >
                      <ArrowRight className={`w-3 h-3 flex-shrink-0 ${isDark ? 'text-aquilia-500/50' : 'text-aquilia-400'}`} />
                      <span className={`flex-1 text-left font-mono text-sm font-semibold ${isDark ? 'text-aquilia-400' : 'text-aquilia-600'}`}>
                        pip install aquilia
                      </span>
                      <span className={`${isDark ? 'text-gray-600 group-hover:text-aquilia-400' : 'text-gray-400 group-hover:text-aquilia-600'} transition-colors`}>
                        {copiedCmd === 'pip install aquilia' ? <Check className="w-3.5 h-3.5 text-aquilia-500" /> : <Copy className="w-3.5 h-3.5" />}
                      </span>
                    </button>
                    <p className={`text-[10px] mt-2 uppercase tracking-wider text-center ${isDark ? 'text-gray-600' : 'text-gray-400'}`}>
                      Click to copy • Latest v1.0.0
                    </p>
                  </motion.div>

                  {/* Python Compatibility */}
                  <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.3, duration: 0.5 }}
                    className={`rounded-2xl border p-5 ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200 shadow-sm'}`}
                  >
                    <h3 className={`text-xs font-bold uppercase tracking-wider mb-4 flex items-center gap-2 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                      <Cpu className="w-3.5 h-3.5 text-aquilia-500" />
                      Compatibility
                    </h3>
                    <div className="space-y-3">
                      <div>
                        <span className={`text-[10px] uppercase tracking-wider font-medium ${isDark ? 'text-gray-600' : 'text-gray-400'}`}>Python Versions</span>
                        <div className="flex gap-2 mt-1.5">
                          {releases[0].python.map(v => (
                            <span key={v} className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold ${isDark ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' : 'bg-blue-50 text-blue-700 border border-blue-200'}`}>
                              {v}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div>
                        <span className={`text-[10px] uppercase tracking-wider font-medium ${isDark ? 'text-gray-600' : 'text-gray-400'}`}>Platform</span>
                        <div className="flex gap-2 mt-1.5">
                          {['Linux', 'macOS', 'Windows'].map(p => (
                            <span key={p} className={`px-2.5 py-1 rounded-lg text-xs font-medium ${isDark ? 'bg-white/[0.03] border border-white/5 text-gray-400' : 'bg-gray-50 border border-gray-100 text-gray-600'}`}>
                              {p}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div>
                        <span className={`text-[10px] uppercase tracking-wider font-medium ${isDark ? 'text-gray-600' : 'text-gray-400'}`}>Type</span>
                        <div className="flex gap-2 mt-1.5">
                          <span className={`px-2.5 py-1 rounded-lg text-xs font-medium ${isDark ? 'bg-white/[0.03] border border-white/5 text-gray-400' : 'bg-gray-50 border border-gray-100 text-gray-600'}`}>
                            Pure Python
                          </span>
                          <span className={`px-2.5 py-1 rounded-lg text-xs font-medium ${isDark ? 'bg-white/[0.03] border border-white/5 text-gray-400' : 'bg-gray-50 border border-gray-100 text-gray-600'}`}>
                            py3-none-any
                          </span>
                        </div>
                      </div>
                    </div>
                  </motion.div>

                  {/* Framework Stats */}
                  <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.4, duration: 0.5 }}
                    className={`rounded-2xl border p-5 ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200 shadow-sm'}`}
                  >
                    <h3 className={`text-xs font-bold uppercase tracking-wider mb-4 flex items-center gap-2 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                      <Sparkles className="w-3.5 h-3.5 text-aquilia-500" />
                      What's Inside
                    </h3>
                    <div className="space-y-2">
                      {[
                        { icon: <Layers className="w-3.5 h-3.5" />, label: 'Modules', value: '20+' },
                        { icon: <Box className="w-3.5 h-3.5" />, label: 'Public APIs', value: '250+' },
                        { icon: <Database className="w-3.5 h-3.5" />, label: 'Field Types', value: '30+' },
                        { icon: <Shield className="w-3.5 h-3.5" />, label: 'Middleware', value: '10+' },
                        { icon: <Terminal className="w-3.5 h-3.5" />, label: 'CLI Commands', value: '40+' },
                        { icon: <Globe className="w-3.5 h-3.5" />, label: 'Facet Types', value: '20+' },
                      ].map(item => (
                        <div
                          key={item.label}
                          className={`flex items-center justify-between px-3 py-2 rounded-xl ${isDark ? 'bg-white/[0.02] hover:bg-white/[0.04]' : 'bg-gray-50 hover:bg-gray-100'} transition-colors`}
                        >
                          <span className={`flex items-center gap-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                            <span className="text-aquilia-500">{item.icon}</span>
                            {item.label}
                          </span>
                          <span className={`text-sm font-bold font-mono ${isDark ? 'text-aquilia-400' : 'text-aquilia-600'}`}>{item.value}</span>
                        </div>
                      ))}
                    </div>
                  </motion.div>

                  {/* Key Dependencies */}
                  <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.5, duration: 0.5 }}
                    className={`rounded-2xl border p-5 ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200 shadow-sm'}`}
                  >
                    <h3 className={`text-xs font-bold uppercase tracking-wider mb-4 flex items-center gap-2 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                      <Hash className="w-3.5 h-3.5 text-aquilia-500" />
                      Key Dependencies
                    </h3>
                    <div className="space-y-1.5">
                      {[
                        { name: 'uvicorn', desc: 'ASGI server' },
                        { name: 'jinja2', desc: 'Template engine' },
                        { name: 'click', desc: 'CLI framework' },
                        { name: 'pyyaml', desc: 'Config parsing' },
                        { name: 'aiosqlite', desc: 'Async SQLite' },
                        { name: 'argon2-cffi', desc: 'Password hashing' },
                        { name: 'pyjwt', desc: 'JWT tokens' },
                      ].map(dep => (
                        <div
                          key={dep.name}
                          className={`flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs transition-colors ${isDark ? 'text-gray-400 hover:bg-white/5' : 'text-gray-500 hover:bg-gray-50'}`}
                        >
                          <span className={`font-mono font-medium ${isDark ? 'text-aquilia-400/70' : 'text-aquilia-600/80'}`}>{dep.name}</span>
                          <span>{dep.desc}</span>
                        </div>
                      ))}
                    </div>
                  </motion.div>

                  {/* Quick Links */}
                  <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.6, duration: 0.5 }}
                    className="space-y-2"
                  >
                    <h3 className={`text-xs font-bold uppercase tracking-wider mb-4 flex items-center gap-2 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                      <ChevronRight className="w-3.5 h-3.5 text-aquilia-500" />
                      Quick Links
                    </h3>
                      <Link
                        to="/changelogs"
                        className={`flex items-center gap-2 px-3 py-2.5 rounded-xl text-sm font-medium transition-all group ${isDark ? 'bg-aquilia-500/5 border border-aquilia-500/10 text-aquilia-400 hover:bg-aquilia-500/10' : 'bg-aquilia-50 border border-aquilia-100 text-aquilia-700 hover:bg-aquilia-100'}`}
                      >
                        <FileText className="w-4 h-4" />
                        <span className="flex-1">Full Changelog</span>
                        <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                      </Link>
                      <Link
                        to="/docs"
                        className={`flex items-center gap-2 px-3 py-2.5 rounded-xl text-sm font-medium transition-all group ${isDark ? 'bg-white/[0.03] border border-white/5 text-gray-300 hover:bg-white/[0.06]' : 'bg-gray-50 border border-gray-100 text-gray-700 hover:bg-gray-100'}`}
                      >
                        <BookOpen className="w-4 h-4" />
                        <span className="flex-1">Documentation</span>
                        <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                      </Link>
                      <a
                        href="https://pypi.org/project/aquilia/"
                        target="_blank"
                        rel="noopener"
                        className={`flex items-center gap-2 px-3 py-2.5 rounded-xl text-sm font-medium transition-all group ${isDark ? 'bg-white/[0.03] border border-white/5 text-gray-300 hover:bg-white/[0.06]' : 'bg-gray-50 border border-gray-100 text-gray-700 hover:bg-gray-100'}`}
                      >
                        <Package className="w-4 h-4" />
                        <span className="flex-1">PyPI Package</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                      <a
                        href="https://github.com/axiomchronicles/Aquilia"
                        target="_blank"
                        rel="noopener"
                        className={`flex items-center gap-2 px-3 py-2.5 rounded-xl text-sm font-medium transition-all group ${isDark ? 'bg-white/[0.03] border border-white/5 text-gray-300 hover:bg-white/[0.06]' : 'bg-gray-50 border border-gray-100 text-gray-700 hover:bg-gray-100'}`}
                      >
                        <Github className="w-4 h-4" />
                        <span className="flex-1">GitHub Repository</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    </motion.div>

                  {/* License Badge */}
                  <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.7, duration: 0.5 }}
                    className="space-y-2"
                  >
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-lg bg-aquilia-500/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                        <Shield className="w-4 h-4 text-aquilia-500" />
                      </div>
                      <div>
                        <h4 className={`text-sm font-bold mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>MIT License</h4>
                        <p className={`text-xs leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                          Aquilia is free and open-source software, distributed under the MIT License. Use it in personal and commercial projects.
                        </p>
                      </div>
                    </div>
                  </motion.div>

                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className={`border-t backdrop-blur-sm mt-auto ${isDark ? 'border-[var(--border-color)] bg-[var(--bg-card)]/50' : 'border-gray-200 bg-white/50'}`}>
        <div className="max-w-[90rem] mx-auto py-12 px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-8">
            <div className="flex items-center gap-2">
              <img src="/logo.png" alt="Aquilia" className="w-6 h-6 object-contain opacity-80" />
              <span className={`text-sm font-bold tracking-tighter ${isDark ? 'text-white' : 'text-gray-900'}`}>AQUILIA</span>
            </div>
            <div className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
              © 2026 Aquilia Framework. Built for the modern web.
            </div>
            <div className="flex space-x-6">
              <a href="https://github.com/axiomchronicles/Aquilia" target="_blank" rel="noopener" className={`transition-colors ${isDark ? 'text-gray-400 hover:text-aquilia-400' : 'text-gray-400 hover:text-aquilia-600'}`}>
                <Github className="w-5 h-5" />
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
