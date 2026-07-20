import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useTheme } from '../context/ThemeContext'
import { Navbar } from '../components/Navbar'
import { Footer } from '../components/Footer'
import { TableOfContents } from '../components/TableOfContents'
import { SEO } from '../components/SEO'
import { MarkdownBridge } from '../components/MarkdownBridge'
import {
  Tag,
  ChevronRight,
  Github,
  BookOpen,
  Terminal,
  Copy,
  Check,
  ChevronDown,
  Info,
  Clock,
  ArrowLeft,
  X,
  ExternalLink
} from 'lucide-react'

// Known static releases list to populate version dropdown and fallbacks
interface ReleaseAsset {
  name: string
  size: string
  type: string
}

interface StaticRelease {
  version: string
  codename: string
  date: string
  tag: 'latest' | 'stable' | 'pre-release'
  python: string[]
  license: string
  summary: string
  assets: ReleaseAsset[]
  installCmd: string
  commitCount: string
  contributors: number
}

const staticReleases: StaticRelease[] = [
  {
    version: '1.3.2',
    codename: 'Deep Current',
    date: 'Jul 20, 2026',
    tag: 'latest',
    python: ['3.10', '3.11', '3.12', '3.13'],
    license: 'MIT',
    summary: 'Dependency-injection rewrite: unified resolution engine, typed DISettings, provider interceptors, DI plugins, conditional providers, hardened pooling and cross-app resolution.',
    assets: [
      { name: 'aquilia-1.3.2.tar.gz', size: '2.5 MB', type: 'Source' },
      { name: 'aquilia-1.3.2-py3-none-any.whl', size: '2.0 MB', type: 'Wheel' }
    ],
    installCmd: 'pip install aquilia==1.3.2',
    commitCount: '32',
    contributors: 2
  },
  {
    version: '1.3.1',
    codename: 'Backend Refactoring',
    date: 'Jul 15, 2026',
    tag: 'stable',
    python: ['3.10', '3.11', '3.12', '3.13'],
    license: 'MIT',
    summary: 'Pluggable Authentication Backends, Unified Permission Engine, Session Hardening, clock-skew JWT validation.',
    assets: [
      { name: 'aquilia-1.3.1.tar.gz', size: '2.5 MB', type: 'Source' },
      { name: 'aquilia-1.3.1-py3-none-any.whl', size: '2.0 MB', type: 'Wheel' }
    ],
    installCmd: 'pip install aquilia==1.3.1',
    commitCount: '48',
    contributors: 2
  },
  {
    version: '1.2.2',
    codename: 'Kraken\'s Wake',
    date: 'Jul 01, 2026',
    tag: 'stable',
    python: ['3.10', '3.11', '3.12', '3.13'],
    license: 'MIT',
    summary: 'Database integrate configuration, ORM schema expressions, CLI auto-discovery sync.',
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
    assets: [
      { name: 'aquilia-1.0.1.tar.gz', size: '2.1 MB', type: 'Source' },
      { name: 'aquilia-1.0.1-py3-none-any.whl', size: '1.8 MB', type: 'Wheel' }
    ],
    installCmd: 'pip install aquilia==1.0.1',
    commitCount: '47',
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
    assets: [
      { name: 'aquilia-1.0.0.tar.gz', size: '2.1 MB', type: 'Source' },
      { name: 'aquilia-1.0.0-py3-none-any.whl', size: '1.8 MB', type: 'Wheel' }
    ],
    installCmd: 'pip install aquilia==1.0.0',
    commitCount: '500+',
    contributors: 1
  }
]

const PAGE_LABEL_MAP: Record<string, string> = {
  'README.md': 'Overview',
  'backends.md': 'Pluggable Auth Backends',
  'guards.md': 'Authorization & Guards',
  'sessions.md': 'Session Hardening',
  'migration.md': 'Migration Guide',
  'di-settings.md': 'DI Settings & Configuration',
  'engine.md': 'Unified Resolution Engine',
  'extensibility.md': 'Interceptors, Plugins & Conditionals'
}

function getFileLabel(filename: string): string {
  if (PAGE_LABEL_MAP[filename]) return PAGE_LABEL_MAP[filename]
  return filename
    .replace(/\.md$/, '')
    .replace(/[-_]+/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase())
}

function supportsFolderNotes(versionStr: string): boolean {
  const clean = versionStr.replace(/^v/, '').split(/[a-zA-Z-]/)[0]
  const parts = clean.split('.').map(Number)
  if (parts.length >= 3 && !isNaN(parts[0]) && !isNaN(parts[1]) && !isNaN(parts[2])) {
    const [major, minor, patch] = parts
    if (major > 1) return true
    if (major === 1 && minor > 3) return true
    if (major === 1 && minor === 3 && patch >= 1) return true
  }
  return false
}

export function ReleaseDetail() {
  const { version = '1.3.1', page = 'README.md' } = useParams<{ version: string; page: string }>()
  const navigate = useNavigate()
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const [files, setFiles] = useState<{ name: string; label: string }[]>([])
  const [content, setContent] = useState<string>('')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // Versions lists & selector dropdown
  const [versions, setVersions] = useState<string[]>(staticReleases.map(r => r.version))
  const [isVersionDropdownOpen, setIsVersionDropdownOpen] = useState(false)
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [copiedCmd, setCopiedCmd] = useState<string | null>(null)

  // References
  const dropdownRef = useRef<HTMLDivElement>(null)
  const contentRef = useRef<HTMLDivElement>(null)

  // Close dropdown on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsVersionDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Fetch release versions/tags from GitHub to get full list, fallback to static
  useEffect(() => {
    fetch('https://api.github.com/repos/tubox-labs/Aquilia/tags')
      .then(res => {
        if (!res.ok) throw new Error('API failure')
        return res.json()
      })
      .then(data => {
        if (Array.isArray(data)) {
          const fetched = data.map((tag: any) => tag.name.replace(/^v/, ''))
          // Merge unique
          const combined = Array.from(new Set([...fetched, ...staticReleases.map(r => r.version)]))
          setVersions(combined)
        }
      })
      .catch(err => {
        console.warn('Failed to fetch github tags, using static list:', err)
      })
  }, [])

  // Fetch release notes page content
  useEffect(() => {
    setIsLoading(true)
    setError(null)
    
    const cleanVersion = version.replace(/^v/, '')

    if (!supportsFolderNotes(cleanVersion)) {
      setError('NO_RELEASE_NOTES')
      setIsLoading(false)
      return
    }

    // Dynamic Fetch from GitHub Contents API
    fetch(`https://api.github.com/repos/tubox-labs/Aquilia/contents/releases/${cleanVersion}`)
      .then(res => {
        if (res.status === 404) {
          throw new Error('NO_RELEASE_NOTES')
        }
        if (!res.ok) throw new Error('API_ERROR')
        return res.json()
      })
      .then(async (data) => {
        if (Array.isArray(data)) {
          const mdFiles = data.filter((f: any) => f.name.endsWith('.md'))
          if (mdFiles.length === 0) {
            throw new Error('NO_RELEASE_NOTES')
          }

          const fileList = mdFiles.map((f: any) => {
            return { name: f.name, label: getFileLabel(f.name) }
          })

          fileList.sort((a: any, b: any) => {
            if (a.name === 'README.md') return -1
            if (b.name === 'README.md') return 1
            return a.label.localeCompare(b.label)
          })

          setFiles(fileList)

          const fileData = mdFiles.find((f: any) => f.name === page)
          if (fileData) {
            const rawRes = await fetch(fileData.download_url)
            if (!rawRes.ok) throw new Error('RAW_FETCH_ERROR')
            const text = await rawRes.text()
            setContent(text)
          } else {
            setError('FILE_NOT_FOUND')
          }
        }
        setIsLoading(false)
      })
      .catch(err => {
        if (err.message === 'NO_RELEASE_NOTES') {
          setError('NO_RELEASE_NOTES')
        } else {
          console.error(err)
          setError('FETCH_ERROR')
        }
        setIsLoading(false)
      })
  }, [version, page])

  const copyText = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopiedCmd(text)
    setTimeout(() => setCopiedCmd(null), 2000)
  }

  // Get active file name to render breadcrumbs and page details
  const activeFile = files.find(f => f.name === page)
  const pageTitle = activeFile ? activeFile.label : 'Release Notes'
  const activeReleaseInfo = staticReleases.find(r => r.version === version)

  const metaTitle = `v${version} ${pageTitle} — Aquilia Releases`
  const metaDescription = `Release notes and update details for version ${version} of Aquilia framework.`

  // Fallback view for versions without folder release notes (e.g. 1.2.2 or older)
  const renderFallbackNotes = () => {
    if (!activeReleaseInfo) {
      return (
        <div className="py-12 text-center max-w-xl mx-auto space-y-6 flex flex-col items-center justify-center min-h-[55vh] w-full">
          <div className="inline-flex p-3.5 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-500 mb-2">
            <Info className="w-6 h-6" />
          </div>
          <div className="space-y-2">
            <h2 className={`text-3xl font-extrabold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
              v{version} Release Notes
            </h2>
            <p className={`text-sm leading-relaxed max-w-md mx-auto ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Detailed documentation pages are not available for this version. Folder-based modular release documentation was introduced in version 1.3.1.
            </p>
          </div>
          <div className="pt-2 flex flex-col sm:flex-row justify-center gap-4 w-full max-w-md">
            <a
              href={`https://github.com/tubox-labs/Aquilia/releases/tag/v${version}`}
              target="_blank"
              rel="noopener noreferrer"
              className={`flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold border transition-all cursor-pointer ${
                isDark
                  ? 'border-white/10 hover:border-aquilia-400/50 hover:bg-white/5 text-white'
                  : 'border-gray-200 hover:border-aquilia-600/30 hover:bg-gray-50 text-gray-800'
              }`}
            >
              <Github className="w-4 h-4 text-gray-500" />
              View GitHub Release
              <ExternalLink className="w-3 h-3 opacity-60" />
            </a>
            <Link
              to="/releases"
              className={`flex items-center justify-center gap-1.5 px-5 py-2.5 rounded-xl text-xs font-bold transition-all ${
                isDark ? 'bg-white/5 hover:bg-white/10 text-gray-300' : 'bg-gray-100 hover:bg-gray-200 text-gray-800'
              }`}
            >
              <ArrowLeft className="w-3.5 h-3.5 opacity-80" />
              Timeline Overview
            </Link>
          </div>
        </div>
      )
    }

    return (
      <div className="space-y-12 max-w-3xl">
        <div className="space-y-4 border-b border-white/[0.04] pb-8">
          <div className="flex items-center gap-3">
            <h1 className={`text-4.5xl font-extrabold font-mono tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
              v{activeReleaseInfo.version}
            </h1>
            <span className={`px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20`}>
              {activeReleaseInfo.tag}
            </span>
          </div>
          <p className={`text-lg italic font-mono ${isDark ? 'text-aquilia-400/90' : 'text-aquilia-600/90'}`}>
            "{activeReleaseInfo.codename}"
          </p>
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <Clock className="w-3.5 h-3.5" />
            <span>Published on {activeReleaseInfo.date}</span>
            <span>•</span>
            <span>MIT License</span>
          </div>
        </div>

        <div className="space-y-6">
          <h3 className={`text-xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Summary</h3>
          <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            {activeReleaseInfo.summary}
          </p>
        </div>

        {/* Installation */}
        <div className="space-y-3">
          <h3 className={`text-xs font-bold uppercase tracking-wider ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
            Quick Install
          </h3>
          <div className={`flex items-center justify-between p-4 rounded-xl border font-mono text-sm font-semibold transition-all ${
            isDark ? 'bg-zinc-950/40 border-white/5 text-aquilia-400' : 'bg-gray-50 border-gray-200 text-aquilia-600'
          }`}>
            <div className="flex items-center gap-3">
              <Terminal className="w-4 h-4 text-aquilia-500/80" />
              <span>{activeReleaseInfo.installCmd}</span>
            </div>
            <button
              onClick={() => copyText(activeReleaseInfo.installCmd)}
              className={`p-1.5 rounded-lg transition-all ${isDark ? 'hover:bg-white/5 text-gray-500 hover:text-white' : 'hover:bg-gray-100 text-gray-400 hover:text-gray-700'}`}
            >
              {copiedCmd === activeReleaseInfo.installCmd ? <Check className="w-4 h-4 text-aquilia-500" /> : <Copy className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* Assets */}
        {activeReleaseInfo.assets && activeReleaseInfo.assets.length > 0 && (
          <div className="space-y-3">
            <h3 className={`text-xs font-bold uppercase tracking-wider ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
              Assets &amp; Downloads
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {activeReleaseInfo.assets.map((asset, i) => (
                <div
                  key={i}
                  className={`flex items-center justify-between p-3.5 rounded-xl border text-xs ${
                    isDark ? 'bg-[#0b0b0b] border-white/5 text-gray-300' : 'bg-white border-gray-200 text-gray-700'
                  }`}
                >
                  <span className="font-mono">{asset.name}</span>
                  <span className={`text-[10px] ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                    {asset.type} • {asset.size}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className={`p-5 rounded-r-xl border-l-4 border-blue-500 flex gap-4 ${
          isDark ? 'bg-blue-500/5' : 'bg-blue-50'
        }`}>
          <Info className="w-5 h-5 text-blue-500 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <span className="font-bold text-xs uppercase text-blue-500 tracking-wider block">Note</span>
            <p className={`text-xs leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Separate multi-page documentation release notes are compiled starting with <Link to="/releases/1.3.1" className="text-aquilia-500 hover:underline">v1.3.1</Link>. You can inspect this release by switching using the dropdown in the sidebar.
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="h-screen overflow-hidden flex flex-col print:h-auto print:overflow-visible print:block">
      <SEO
        title={metaTitle}
        description={metaDescription}
        keywords={`Aquilia, release notes, v${version}, Python framework, changelog`}
      />
      
      {/* Ambient background */}
      <div className="fixed inset-0 -z-10 pointer-events-none print:hidden">
        <div className={isDark ? 'absolute inset-0 bg-black' : 'absolute inset-0 bg-[#fafafa]'} />
        <div className={`absolute inset-0 ${isDark ? 'bg-gradient-to-br from-aquilia-500/5 via-transparent to-blue-500/5' : ''}`} />
        <div className={`absolute top-0 left-1/4 w-96 h-96 ${isDark ? 'bg-aquilia-500/10' : 'bg-aquilia-500/5'} rounded-full blur-3xl`} />
        <div className={`absolute bottom-0 right-1/4 w-96 h-96 ${isDark ? 'bg-blue-500/10' : 'bg-blue-500/5'} rounded-full blur-3xl`} />
      </div>

      {/* Navbar */}
      <Navbar onToggleSidebar={() => setIsSidebarOpen(true)} />

      {/* Main Content Area */}
      <div className="flex flex-1 overflow-hidden pt-[var(--navbar-height,64px)] print:block print:overflow-visible print:pt-0">
        
        {/* LEFT SIDEBAR */}
        <div className={`
          fixed lg:static inset-y-0 left-0 z-50 w-64 lg:h-full print:hidden
          transform transition-transform duration-300 ease-in-out
          ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
          flex-shrink-0 border-r 
          ${isDark ? 'border-white/10 bg-[#09090b]' : 'border-gray-200 bg-white'} 
          lg:bg-transparent lg:backdrop-blur-xl flex flex-col
        `}>
          
          {/* Sidebar scroll container */}
          <div className="flex-1 overflow-y-auto px-5 py-6 space-y-6">
            
            {/* Mobile Header */}
            <div className="lg:hidden flex items-center justify-between">
              <span className={`font-bold text-sm ${isDark ? 'text-white' : 'text-gray-900'}`}>Releases Navigation</span>
              <button
                onClick={() => setIsSidebarOpen(false)}
                className={`p-2 rounded-lg ${isDark ? 'hover:bg-white/10 text-gray-400' : 'hover:bg-gray-100 text-gray-600'}`}
              >
                <X className="w-4.5 h-4.5" />
              </button>
            </div>

            {/* Version Switcher */}
            <div className="space-y-2">
              <label className={`text-[10px] font-bold uppercase tracking-wider ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                Release Version
              </label>
              <div className="relative" ref={dropdownRef}>
                <button
                  onClick={() => setIsVersionDropdownOpen(!isVersionDropdownOpen)}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-xl border text-sm font-semibold transition-all ${
                    isDark
                      ? 'bg-zinc-950/40 border-white/10 hover:border-white/20 text-white'
                      : 'bg-gray-50 border-gray-200 hover:border-gray-300 text-gray-900'
                  }`}
                >
                  <span className="flex items-center gap-2">
                    <Tag className="w-4 h-4 text-aquilia-500" />
                    v{version}
                  </span>
                  <ChevronDown className="w-4 h-4 opacity-60" />
                </button>
                
                {isVersionDropdownOpen && (
                  <div className={`absolute left-0 right-0 mt-2 max-h-60 overflow-y-auto rounded-xl p-1.5 shadow-xl border z-20 backdrop-blur-xl ${
                    isDark 
                      ? 'bg-zinc-950/95 border-white/10 text-gray-200' 
                      : 'bg-white/95 border-gray-200 text-gray-800'
                  }`}>
                    {versions.map(v => (
                      <button
                        key={v}
                        onClick={() => {
                          setIsVersionDropdownOpen(false)
                          navigate(`/releases/${v}`)
                        }}
                        className={`w-full text-left px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                          v === version
                            ? 'bg-aquilia-500/10 text-aquilia-400'
                            : isDark ? 'hover:bg-white/5 hover:text-white' : 'hover:bg-gray-100 hover:text-gray-900'
                        }`}
                      >
                        v{v} {v === '1.3.1' ? '(Static Notes)' : ''}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Sidebar Documents list (if release notes exist) */}
            {files.length > 0 && (
              <div className="space-y-3 pt-4 border-t border-white/[0.04]">
                <h4 className={`text-[10px] font-bold uppercase tracking-wider flex items-center gap-2 ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                  <BookOpen className="w-3.5 h-3.5" />
                  Documentation Pages
                </h4>
                <ul className="space-y-1">
                  {files.map(file => {
                    const active = page === file.name
                    return (
                      <li key={file.name}>
                        <Link
                          to={file.name === 'README.md' ? `/releases/${version}` : `/releases/${version}/${file.name}`}
                          className={`block py-2 px-3 rounded-lg text-xs font-medium transition-all ${
                            active
                              ? isDark ? 'bg-aquilia-500/10 text-aquilia-400 font-semibold' : 'bg-aquilia-50 text-aquilia-600 font-semibold'
                              : isDark ? 'text-gray-400 hover:text-white hover:bg-white/5' : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                          }`}
                        >
                          {file.label}
                        </Link>
                      </li>
                    )
                  })}
                </ul>
              </div>
            )}
          </div>
        </div>

        {/* Scroll Container for center content + right TOC */}
        <div
          className="flex-1 min-w-0 overflow-y-auto print:overflow-visible print:block"
          data-scroll-container=""
          ref={contentRef}
        >
          <div className="flex max-w-[80rem] mx-auto print:block print:w-full print:max-w-none">
            
            {/* Main content pane */}
            <main className="flex-1 min-w-0 px-4 sm:px-6 lg:px-10 py-12 print:px-0 print:py-0 print:m-0 print:w-full print:max-w-none print:block">
              
              {/* Breadcrumbs */}
              <div className="flex items-center gap-2 text-xs font-mono text-gray-500 mb-6 print:hidden">
                <Link to="/releases" className="hover:text-aquilia-500 transition-colors">Releases</Link>
                <ChevronRight className="w-3 h-3" />
                <Link to={`/releases/${version}`} className="hover:text-aquilia-500 transition-colors">v{version}</Link>
                {page !== 'README.md' && (
                  <>
                    <ChevronRight className="w-3 h-3" />
                    <span className="text-gray-400 truncate max-w-[150px]">{pageTitle}</span>
                  </>
                )}
              </div>

              {/* Page Contents */}
              <div className="max-w-3xl w-full mx-auto">
                {isLoading ? (
                  <div className="py-24 flex flex-col items-center justify-center min-h-[50vh] gap-4 w-full mx-auto">
                    <div className="w-10 h-10 rounded-full border-2 border-aquilia-500/10 border-t-aquilia-500 animate-spin" />
                    <span className={`text-xs font-mono tracking-widest ${isDark ? 'text-zinc-500' : 'text-zinc-400'} uppercase animate-pulse`}>
                      Loading Release Notes...
                    </span>
                  </div>
                ) : error === 'NO_RELEASE_NOTES' ? (
                  renderFallbackNotes()
                ) : error ? (
                  <div className="py-12 text-center max-w-xl mx-auto space-y-6 flex flex-col items-center justify-center min-h-[55vh] w-full">
                    <div className="inline-flex p-3.5 rounded-full bg-red-500/10 border border-red-500/20 text-red-500 mb-2">
                      <Info className="w-6 h-6" />
                    </div>
                    <div className="space-y-2">
                      <h2 className={`text-3xl font-extrabold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
                        Content Not Found
                      </h2>
                      <p className={`text-sm leading-relaxed max-w-md mx-auto ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                        {error === 'FILE_NOT_FOUND' 
                          ? 'The requested release notes page could not be found.' 
                          : 'An error occurred while loading release documentation.'}
                      </p>
                    </div>
                    <div className="pt-2 flex justify-center gap-4">
                      <Link
                        to={`/releases/${version}`}
                        className={`flex items-center justify-center gap-1.5 px-5 py-2.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                          isDark ? 'bg-white/5 hover:bg-white/10 text-gray-300' : 'bg-gray-100 hover:bg-gray-200 text-gray-800'
                        }`}
                      >
                        <ArrowLeft className="w-3.5 h-3.5" />
                        Back to Overview
                      </Link>
                    </div>
                  </div>
                ) : (
                  <MarkdownBridge content={content} version={version} currentPage={page} />
                )}
              </div>

              {/* Footer */}
              <div className="mt-16 print:hidden">
                <Footer />
              </div>
            </main>

            {/* RIGHT TABLE OF CONTENTS */}
            {!isLoading && !error && (
              <aside className="hidden xl:block w-56 shrink-0 py-12 px-2 print:hidden">
                <div className="sticky top-0">
                  <TableOfContents />
                </div>
              </aside>
            )}

          </div>
        </div>

      </div>
    </div>
  )
}
