import { Link } from 'react-router-dom'
import { Navbar } from '../components/Navbar'
import { Sidebar } from '../components/Sidebar'
import { useTheme } from '../context/ThemeContext'
import {
  ArrowRight, Check, Github, ExternalLink, BookOpen, Package
} from 'lucide-react'
import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'

interface ChangelogSection {
  title: string
  type: 'added' | 'changed' | 'fixed' | 'deprecated' | 'security' | 'breaking' | 'removed'
  items: string[]
}

interface ChangelogEntry {
  version: string
  codename?: string
  date: string
  tag: 'major' | 'minor' | 'patch'
  summary: string
  sections: ChangelogSection[]
}

const changelogs: ChangelogEntry[] = [
  {
    version: '1.2.2',
    codename: 'Kraken\'s Wake',
    date: '2026-07-01',
    tag: 'patch',
    summary: 'Kraken\'s Wake release patch addressing database integration setup, expression serialization in admin tools, CLI discovery parser, and SQLite constraints.',
    sections: [
      {
        title: 'Fixed',
        type: 'fixed',
        items: [
          'Database Integration Configuration: Fixed Workspace.integrate() to correctly handle DatabaseIntegration protocol instances and set self._database_config.',
          'ORM Schema Expression Serialization: Added automatic string casting for expression constraints (like Lower or Upper) and expression-based index fields within the admin dashboard\'s model metadata collection (get_model_schema()).',
          'Auto-Discovery Integration in CLI: Replaced the legacy parser inside the server startup sequence with the unified next-generation AutoDiscoveryEngine to automatically sync manifests when running the development server.',
          'SQLite Alter Constraints: Modified migration translation to translate UniqueConstraint into unique indexes when applying migrations on SQLite databases.'
        ]
      }
    ]
  },
  {
    version: '1.2.1',
    codename: 'Kraken\'s Wake',
    date: '2026-07-01',
    tag: 'patch',
    summary: 'Kraken\'s Wake release patch decoupling Jinja2 and MarkupSafe, converting template imports to lazy getattr loading, resolving Windows SQLite file locking, and CSP nonces in toolbar.',
    sections: [
      {
        title: 'Fixed',
        type: 'fixed',
        items: [
          'Startup dependency decoupling: Decoupled jinja2 and markupsafe from core dependencies, moving them to the aquilia[template] extras bundle to keep core installation lightweight.',
          'Lazy Imports: Converted eager template imports to a module-level lazy __getattr__ import resolution mechanism, preventing startup crashes when jinja2 is not installed.',
          'Windows File Locking: Resolved a trace storage lock issue on Windows by explicitly closing all SQLite connections in SQLiteTraceStore.',
          'Toolbar Nonce Compatibility: Injected toolbar now parses JSON trace payload dynamically by finding the script tag end delimiter instead of matching the full signature, allowing parsing even when CSP nonces are present.'
        ]
      }
    ]
  },
  {
    version: '1.2.0',
    codename: 'Kraken\'s Wake',
    date: '2026-06-28',
    tag: 'minor',
    summary: 'Kraken\'s Wake release adding Database CLI rollback/seeding/checking, Click CLI styling, API versioning override in manifest, Request Inspector tool, and Sigil schema representation.',
    sections: [
      {
        title: 'Added',
        type: 'added',
        items: [
          'Database CLI Enhancements: Added history, rollback, check, diff, seed, reset, and flush subcommands.',
          'Click CLI Help Custom Colorization: formats option flags in bold green, help text in white, and headers in bold cyan.',
          'Manifest-Level API Versioning Override: Replaced legacy Module().versioning() with manifest AppManifest.versioning configuration supporting strategy, versions, default, sunset, etc.',
          'Request Inspector (aquilia.inspector): Full request execution tracing with spans, lanes, timeline visualization, and live SSE streaming to admin panel.',
          'Container self-registration in DI DI containers.',
          'Container.add_diagnostic_listener() public API.',
          'Explicit Cross-field validation (@ward) decorator.',
          'Intermediate Representation (Sigil) schema validator and migration engine.',
          'Transforms and Pipelines (>>) on facets.',
          'Bulk & Stream Validation: seal_many, seal_stream, seal_columnar.',
          'Test Generation Strategy support.',
          'Discriminated Unions (BlueprintUnion).',
          'Form & File Uploads via Blueprints (UploadFile and FormData).',
          'Unified Request Input Resolution & Parameter Casting.',
          'Click-based Aquilary CLI commands.'
        ]
      },
      {
        title: 'Removed',
        type: 'removed',
        items: [
          'Artifact System: Entirely removed the redundant aquilia.artifacts module, and compile/freeze commands.'
        ]
      },
      {
        title: 'Changed',
        type: 'changed',
        items: [
          'Database Introspection and Migration Rollback.',
          'Scaffolding Integration API migration.',
          'Boilerplate reduction and scaffolding cleanup.',
          'Zero Runtime Dependencies: Migrated blueprints to pure-Python.',
          'Deep Performance Optimizations: lazy wrapping, regex caches, ORM fast-path checks.'
        ]
      },
      {
        title: 'Fixed',
        type: 'fixed',
        items: [
          'Discovery system improvements dotted parent prefix loading.',
          'Windows compatibility fixes for signal.SIGKILL and mcp commands.',
          'RequestIdMiddleware stability across pool boundaries.',
          'Multiple Blueprint Parameter Support.',
          'String Annotation Evaluation (PEP 563).'
        ]
      }
    ]
  },
  {
    version: '1.1.2',
    codename: 'Crimson Gale',
    date: '2026-06-12',
    tag: 'patch',
    summary: 'Crimson Gale release patching nested middleware Entry NameErrors and dotenv load order overrides.',
    sections: [
      {
        title: 'Fixed',
        type: 'fixed',
        items: [
          'name \'Entry\' is not defined server crash: fixed nested middleware class namespace lookups.',
          'Generated workspace missing Integration import in generated workspace.py file templates.',
          '.env values never reflected in workspace config: fixed load order where .env.example overrode .env.',
          'AQ_ENV/AQUILIA_ENV inconsistency and resolved template files dotenv search paths.'
        ]
      }
    ]
  },
  {
    version: '1.1.1',
    codename: 'Sea Serpent',
    date: '2026-06-09',
    tag: 'patch',
    summary: 'Sea Serpent release decoupling Workspace configs, resolving thread-safe dotenv loading, and standardizing catalog format defaults.',
    sections: [
      {
        title: 'Changed',
        type: 'changed',
        items: [
          'Workspace module config builders decoupling.',
          'Replaced legacy static Integration API with typed class adapters.'
        ]
      },
      {
        title: 'Fixed',
        type: 'fixed',
        items: [
          'Thread safety Lock in pyconfig.py.',
          'I18n default values catalog format resolution defaults.'
        ]
      }
    ]
  },
  {
    version: '1.1.0',
    codename: 'Black Pearl',
    date: '2026-06-08',
    tag: 'minor',
    summary: 'Black Pearl release removing mlops and LSP servers, adding SSE stream manager, OpenTelemetry traces, and @validate_body.',
    sections: [
      {
        title: 'Added',
        type: 'added',
        items: [
          'aquilia.sse Server-Sent Events managers.',
          'aquilia.otel OpenTelemetry configs and middleware.',
          '@validate_body body annotation validators.'
        ]
      },
      {
        title: 'Removed',
        type: 'removed',
        items: [
          'Removed duplicate mlops package, AMDL DSL, and language server modules.'
        ]
      }
    ]
  },
  {
    version: '1.0.5',
    codename: 'Jolly Roger',
    date: '2026-06-04',
    tag: 'patch',
    summary: 'Jolly Roger release launching stdio MCP server support and Surp binary serialization.',
    sections: [
      {
        title: 'Added',
        type: 'added',
        items: [
          'Aquilia MCP server under aquilia.mcp.',
          'MCP tools for API discovery and prompt helpers.'
        ]
      },
      {
        title: 'Changed',
        type: 'changed',
        items: [
          'Upgraded serialization from Crous to Surp.'
        ]
      }
    ]
  },
  {
    version: '1.0.4',
    date: '2026-05-17',
    tag: 'patch',
    summary: 'Patches compiling workflows by removing build compile pipelines and enabling live Python workspace introspection.',
    sections: [
      {
        title: 'Removed',
        type: 'removed',
        items: [
          'Removed react-style aquilia/build package and aq build.',
          'Removed build-gating barriers.'
        ]
      },
      {
        title: 'Changed',
        type: 'changed',
        items: [
          'aq compile writes explicit artifacts.',
          'aq freeze snapshots cryptographic integrity signatures.'
        ]
      }
    ]
  },
  {
    version: '1.0.1',
    codename: 'Framework Audit',
    date: '2026-03-08',
    tag: 'patch',
    summary: 'Phase 1-15 comprehensive framework security audit and hardening.',
    sections: [
      {
        title: 'Added',
        type: 'added',
        items: [
          'Core ASGI server, DI registry, Auth stack, controller and session security hardening.',
          'HMAC SHA-256 validation for Jinja2 template cache files.',
          'Path traversal path checks rejecting null-bytes.',
          'Allowlist validation for background tasks.'
        ]
      }
    ]
  },
  {
    version: '1.0.0',
    codename: 'Genesis',
    date: 'February 22, 2026',
    tag: 'major',
    summary: 'Initial stable launch of Aquilia framework.',
    sections: [
      {
        title: 'Added',
        type: 'added',
        items: [
          'Manifest-First Architecture implementation.',
          'Scoped Dependency Injection targeting Singleton, App, and Request contexts.',
          'Async-Native ASGI server using Uvicorn.'
        ]
      }
    ]
  }
]

const tagColors: Record<string, string> = {
  major: 'text-aquilia-400 bg-aquilia-500/10 border border-aquilia-500/20',
  minor: 'text-blue-400 bg-blue-500/10 border border-blue-500/20',
  patch: 'text-amber-400 bg-amber-500/10 border border-amber-500/20',
}

const typeColors: Record<string, { text: string; bg: string; border: string }> = {
  added: { text: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20' },
  changed: { text: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/20' },
  fixed: { text: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/20' },
  security: { text: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20' },
  breaking: { text: 'text-purple-400', bg: 'bg-purple-500/10', border: 'border-purple-500/20' },
  removed: { text: 'text-zinc-400', bg: 'bg-zinc-500/10', border: 'border-zinc-500/20' }
}

export function Changelogs() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)

  useEffect(() => {
    document.title = "Changelogs — Aquilia"
  }, [])
  const [activeFilter, setActiveFilter] = useState<string | null>(null)
  const [expandedVersions, setExpandedVersions] = useState<Record<string, boolean>>({ '1.2.2': true })

  const toggleVersion = (version: string) => {
    setExpandedVersions(prev => ({ ...prev, [version]: !prev[version] }))
  }

  const filteredChangelogs = changelogs.map(entry => {
    if (!activeFilter) return entry
    const filteredSections = entry.sections.filter(s => s.type === activeFilter)
    return { ...entry, sections: filteredSections }
  }).filter(entry => entry.sections.length > 0 || !activeFilter)

  return (
    <div className="min-h-screen flex flex-col overflow-x-hidden">
      <Navbar onToggleSidebar={() => setIsSidebarOpen(true)} />
      <div className="lg:hidden">
        <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />
      </div>

      <main className="flex-grow pt-16 relative">
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
                <span className="gradient-text font-mono">Changelog</span>
              </h1>
              <p className={`text-base max-w-2xl ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                A comprehensive, sequential log of all additions, changes, and fixes across the Aquilia core framework and libraries.
              </p>
            </motion.div>
          </div>
        </section>

        {/* Filter Toolbar (Clean borderless pills) */}
        <section className="py-4 border-b border-white/[0.04]">
          <div className="max-w-[90rem] mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex flex-wrap items-center gap-2">
              <span className={`text-xs uppercase tracking-wider font-semibold mr-2 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                Filter logs:
              </span>
              <button
                onClick={() => setActiveFilter(null)}
                className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-all ${
                  !activeFilter
                    ? isDark ? 'bg-white/10 text-white' : 'bg-gray-150 text-gray-900'
                    : isDark ? 'text-gray-400 hover:text-white' : 'text-gray-600 hover:text-gray-955'
                }`}
              >
                All
              </button>
              {(['added', 'changed', 'fixed', 'breaking'] as const).map(type => (
                <button
                  key={type}
                  onClick={() => setActiveFilter(activeFilter === type ? null : type)}
                  className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-all capitalize ${
                    activeFilter === type
                      ? isDark ? 'bg-white/10 text-white' : 'bg-gray-150 text-gray-900'
                      : isDark ? 'text-gray-400 hover:text-white' : 'text-gray-600 hover:text-gray-955'
                  }`}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>
        </section>

        {/* Main Content */}
        <section className="pb-24 pt-12">
          <div className="max-w-[90rem] mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex flex-col xl:flex-row gap-16">

              {/* LEFT — Changelog timeline (No borders, completely clean layout) */}
              <div className="flex-1 min-w-0">
                <div className={`relative pl-8 sm:pl-12 border-l-2 ${isDark ? 'border-zinc-800' : 'border-zinc-200'} space-y-16 py-4`}>
                  {filteredChangelogs.map((entry, idx) => {
                    const isExpanded = expandedVersions[entry.version] ?? false

                    return (
                      <motion.div
                        key={entry.version}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: idx * 0.05, duration: 0.5 }}
                        className="relative"
                      >
                        {/* Node point */}
                        <div className={`absolute -left-[41px] sm:-left-[57px] top-2.5 w-4 h-4 rounded-full border-2 ${isDark ? 'bg-black border-zinc-800' : 'bg-white border-zinc-200'} flex items-center justify-center`}>
                          <div className={`w-1.5 h-1.5 rounded-full ${entry.tag === 'major' ? 'bg-aquilia-400' : entry.tag === 'minor' ? 'bg-blue-400' : 'bg-amber-400'}`} />
                        </div>

                        {/* Heading */}
                        <div className="mb-4">
                          <button
                            onClick={() => toggleVersion(entry.version)}
                            className="flex flex-col sm:flex-row sm:items-baseline gap-3 w-full text-left group"
                          >
                            <h2 className={`text-2xl font-extrabold font-mono tracking-tight transition-colors ${isDark ? 'text-white group-hover:text-aquilia-400' : 'text-gray-900 group-hover:text-aquilia-600'}`}>
                              v{entry.version} {entry.codename && <span className={`text-sm font-normal font-sans ml-2 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>— {entry.codename}</span>}
                            </h2>
                            <span className={`px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded-full ${tagColors[entry.tag] || 'bg-zinc-500'}`}>
                              {entry.tag}
                            </span>
                            <span className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'} ml-auto`}>
                              {entry.date}
                            </span>
                          </button>
                        </div>

                        <p className={`text-sm leading-relaxed mb-6 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                          {entry.summary}
                        </p>

                        {/* Version sections */}
                        {isExpanded && entry.sections.length > 0 && (
                          <div className="space-y-6 mt-6">
                            {entry.sections.map((section, sIdx) => {
                              const colors = typeColors[section.type] || { text: 'text-gray-400', bg: 'bg-zinc-800', border: 'border-zinc-700' }
                              return (
                                <div key={sIdx} className="space-y-2">
                                  <div className="flex items-center gap-2">
                                    <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md ${colors.bg} ${colors.text} border ${colors.border}`}>
                                      {section.type}
                                    </span>
                                    <h4 className={`text-xs font-bold uppercase tracking-wider ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                                      {section.title}
                                    </h4>
                                  </div>
                                  <ul className="space-y-2">
                                    {section.items.map((item, iIdx) => (
                                      <li key={iIdx} className="flex items-start gap-2 text-sm">
                                        <Check className={`w-3.5 h-3.5 mt-0.5 flex-shrink-0 ${colors.text}`} />
                                        <span className={isDark ? 'text-gray-300' : 'text-gray-700'}>
                                          {item}
                                        </span>
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )
                            })}
                          </div>
                        )}
                      </motion.div>
                    )
                  })}
                </div>
              </div>

              {/* RIGHT — Premium sidebar (Quick Links only) */}
              <div className="xl:w-80 2xl:w-96 flex-shrink-0">
                <div className="xl:sticky xl:top-24 space-y-12">
                  {/* Convention Note */}
                  <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2, duration: 0.5 }}
                    className="space-y-2"
                  >
                    <h4 className={`text-sm font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Keep a Changelog</h4>
                    <p className={`text-xs leading-relaxed ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                      Aquilia follows semantic versioning rules (`vMajor.Minor.Patch`) and tracks modifications according to Keep a Changelog guidelines.
                    </p>
                  </motion.div>

                  {/* Quick Links */}
                  <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3, duration: 0.5 }}
                    className="space-y-4"
                  >
                    <h3 className={`text-xs font-bold uppercase tracking-wider ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                      Quick Links
                    </h3>
                    <div className="space-y-3">
                      <Link
                        to="/releases"
                        className={`flex items-center gap-2 py-2 text-sm font-medium transition-colors ${isDark ? 'text-gray-300 hover:text-white' : 'text-gray-700 hover:text-gray-900'}`}
                      >
                        <Package className="w-4 h-4" />
                        <span className="flex-1">View Releases</span>
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
                        href="https://github.com/axiomchronicles/Aquilia"
                        target="_blank"
                        rel="noopener"
                        className={`flex items-center gap-2 py-2 text-sm font-medium transition-colors ${isDark ? 'text-gray-300 hover:text-white' : 'text-gray-700 hover:text-gray-900'}`}
                      >
                        <Github className="w-4 h-4" />
                        <span className="flex-1">GitHub Repository</span>
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
