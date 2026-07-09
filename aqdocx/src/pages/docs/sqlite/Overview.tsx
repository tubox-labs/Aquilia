import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { NextSteps } from '../../../components/NextSteps'
import { Database, Zap, Shield, Layers, Cpu, ShieldAlert, Info } from 'lucide-react'

export function SqliteOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'

  const features = [
    {
      icon: <Zap className="w-5 h-5 text-aquilia-400" />,
      title: 'Native Async Pool',
      desc: 'Multi-reader and single-writer concurrency model built purely on Python\'s standard library.',
    },
    {
      icon: <Shield className="w-5 h-5 text-blue-400" />,
      title: 'Zero Dependencies',
      desc: 'Does not require aiosqlite or any third-party C extensions. Relies on standard sqlite3.',
    },
    {
      icon: <Database className="w-5 h-5 text-emerald-400" />,
      title: 'Dict-like Rows',
      desc: 'Returned rows allow access by column names, integer indices, or attributes (row.name).',
    },
    {
      icon: <Layers className="w-5 h-5 text-purple-400" />,
      title: 'Nested Transactions',
      desc: 'Full transaction and savepoint contexts with automatic rollbacks on exception faults.',
    },
  ]

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      {/* Title Header */}
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Database className="w-4 h-4 animate-pulse" />
          SQLite Module / Overview
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          async SQLite Module
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          Aquilia provides a zero-dependency, native async SQLite connection pool wrapper that makes standard library <code className="text-aquilia-500">sqlite3</code> async-safe by offloading blocking operations to a dedicated thread pool.
        </p>
      </div>

      {/* Quick Start */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Cpu className="w-5 h-5 text-aquilia-500" />
          Quick Start
        </h2>

        <div className="space-y-4">
          <p className={`text-sm ${subtleText}`}>
            Instantiate the connection pool using <DocTerm id="sqlite.create_pool">create_pool()</DocTerm> and a <DocTerm id="sqlite.SqlitePoolConfig">SqlitePoolConfig</DocTerm> or a DB URL string.
          </p>
          <CodeBlock language="python" highlightLines={[4, 13, 16, 19, 24]}>{`from aquilia.sqlite import create_pool, SqlitePoolConfig

# Option A: Simple connection URL (uses WAL mode and default pool settings)
pool = await create_pool("sqlite:///app.db")

# Option B: Advanced configuration via SqlitePoolConfig
config = SqlitePoolConfig(
    path="app.db",
    pool_size=10,             # Number of concurrent reader connections
    journal_mode="WAL",       # Write-Ahead Logging
    synchronous="NORMAL",     # Optimal WAL speed/durability trade-off
)
pool = await create_pool(config)

# Quick execution (uses connection pool direct helpers)
await pool.execute(
    "CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY, name TEXT)"
)
await pool.execute(
    "INSERT INTO items (name) VALUES (?)", ["Product A"]
)

# Fetching rows (returns dict-like Row objects)
rows = await pool.fetch_all("SELECT * FROM items")
for row in rows:
    print(f"ID: {row.id} | Name: {row['name']}")`}</CodeBlock>
        </div>
      </section>

      {/* Workspace Configuration Styles */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Workspace Configuration Styles
        </h2>
        <p className={`mb-6 ${subtleText}`}>
          Aquilia support both the legacy static builder integration style and the modern typed-dataclass style inside <code className="text-aquilia-500">workspace.py</code>:
        </p>

        {/* Modern Style */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-3">
            <Info className="w-5 h-5 text-emerald-400" />
            <h3 className="text-lg font-semibold">Modern Style: DatabaseIntegration Dataclass (Recommended)</h3>
          </div>
          <p className={`text-sm mb-4 ${subtleText}`}>
            Directly integrate the typed <code className="text-aquilia-500">DatabaseIntegration</code> configuration:
          </p>
          <CodeBlock language="python" highlightLines={[7, 8, 9, 10, 11, 12]}>{`# workspace.py
from aquilia import Workspace
from aquilia.integrations import DatabaseIntegration

workspace = (
    Workspace("myapp")
    .integrate(DatabaseIntegration(
        url="sqlite:///app.db",
        pool_size=8,
        journal_mode="WAL",
        synchronous="NORMAL"
    ))
)`}</CodeBlock>
        </div>

        {/* Legacy Style */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-3">
            <ShieldAlert className="w-5 h-5 text-amber-500" />
            <h3 className="text-lg font-semibold text-amber-500">Legacy Style: Static Database Builder</h3>
          </div>
          <p className={`text-sm mb-4 ${subtleText}`}>
            The legacy static <code className="text-aquilia-500">Integration.database()</code> or <code className="text-aquilia-500">.database()</code> method:
          </p>
          <CodeBlock language="python" highlightLines={[7]}>{`# workspace.py (Legacy)
from aquilia import Workspace
from aquilia.integrations import Integration

workspace = (
    Workspace("myapp")
    .database(url="sqlite:///app.db")
)`}</CodeBlock>
          <div className="group relative overflow-hidden rounded-xl bg-amber-500/5 border border-amber-500/10 p-4 mt-3">
            <p className="text-xs leading-relaxed text-amber-400">
              <strong>Warning:</strong> The legacy static helper <code className="text-aquilia-500">.database()</code> is deprecated and will be removed in a future release. Migrate to direct constructor calls using <code className="text-aquilia-500">DatabaseIntegration</code>.
            </p>
          </div>
        </div>
      </section>

      {/* Key Pillars */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Subsystem Features
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {features.map((feature, i) => (
            <div key={i} className="group relative overflow-hidden rounded-2xl bg-white/5 border border-white/5 hover:border-aquilia-500/20 p-6 backdrop-blur-sm transition-all duration-300 hover:translate-y-[-2px] hover:shadow-lg shadow-black/40">
              <div className="absolute top-0 bottom-0 left-0 w-1 bg-gradient-to-b from-aquilia-500 to-transparent opacity-50 group-hover:opacity-100 transition-opacity duration-300" />
              <div className="flex items-center gap-3 mb-3">
                <div className="text-aquilia-500">{feature.icon}</div>
                <h3 className={`font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>{feature.title}</h3>
              </div>
              <p className={`text-sm leading-relaxed ${subtleText}`}>{feature.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pool Concurrency Architecture */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Pool Concurrency Architecture
        </h2>
        <p className={`mb-6 ${subtleText}`}>
          Aquilia's connection pool maintains <code className="text-aquilia-500">N</code> reader connections plus exactly <code className="text-aquilia-500">1</code> writer connection. This matches SQLite's single-writer limitation while allowing concurrent reads in Write-Ahead Log (WAL) mode.
        </p>

        {/* Floating borderless SVG Pool Concurrency Architecture Flowchart */}
        <div className="w-full mx-auto py-4 flex justify-center overflow-visible">
          <svg viewBox="0 0 660 220" className="w-full h-auto overflow-visible">
            <defs>
              <linearGradient id="grad-sqlite-pool" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#10b981" stopOpacity="0.2" />
                <stop offset="100%" stopColor="#047857" stopOpacity="0.0" />
              </linearGradient>
              <linearGradient id="grad-sqlite-reader" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.2" />
                <stop offset="100%" stopColor="#1d4ed8" stopOpacity="0.0" />
              </linearGradient>
              <linearGradient id="grad-sqlite-writer" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#ef4444" stopOpacity="0.2" />
                <stop offset="100%" stopColor="#b91c1c" stopOpacity="0.0" />
              </linearGradient>
              <marker id="db-arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 1 L 10 5 L 0 9 z" fill="#10b981" />
              </marker>
              <filter id="glow-sqlite" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>

            {/* ConnectionPool Node */}
            <g transform="translate(230, 10)">
              <rect x="0" y="0" width="200" height="65" rx="14" fill="url(#grad-sqlite-pool)" stroke="#10b981" strokeWidth="1.5" filter="url(#glow-sqlite)" />
              <text x="100" y="27" textAnchor="middle" fill="#34d399" fontSize="12" fontWeight="700" letterSpacing="0.05em">CONNECTIONPOOL</text>
              <text x="100" y="47" textAnchor="middle" fill={isDark ? '#e5e5e5' : '#374151'} fontSize="9.5" fontFamily="monospace">WAL Concurrency Mode</text>
            </g>

            {/* Reader Pool Box */}
            <g transform="translate(40, 115)">
              <rect x="0" y="0" width="220" height="90" rx="14" fill="url(#grad-sqlite-reader)" stroke="#3b82f6" strokeWidth="1.5" filter="url(#glow-sqlite)" />
              <text x="110" y="25" textAnchor="middle" fill="#93c5fd" fontSize="11" fontWeight="700" letterSpacing="0.03em">READER POOL</text>
              <text x="110" y="45" textAnchor="middle" fill={isDark ? '#e5e5e5' : '#374151'} fontSize="9.5" fontFamily="monospace">N read-only connections</text>
              <text x="110" y="60" textAnchor="middle" fill="#60a5fa" fontSize="8.5">Semaphore protected</text>
              <text x="110" y="75" textAnchor="middle" fill="#93c5fd" fontSize="8" fontFamily="monospace">reader_0, reader_1, ... reader_N</text>
            </g>

            {/* Serialized Writer Box */}
            <g transform="translate(400, 115)">
              <rect x="0" y="0" width="220" height="90" rx="14" fill="url(#grad-sqlite-writer)" stroke="#ef4444" strokeWidth="1.5" filter="url(#glow-sqlite)" />
              <text x="110" y="25" textAnchor="middle" fill="#f87171" fontSize="11" fontWeight="700" letterSpacing="0.03em">SERIALIZED WRITER</text>
              <text x="110" y="45" textAnchor="middle" fill={isDark ? '#e5e5e5' : '#374151'} fontSize="9.5" fontFamily="monospace">1 read-write connection</text>
              <text x="110" y="60" textAnchor="middle" fill="#f87171" fontSize="8.5">asyncio.Lock protected</text>
              <text x="110" y="75" textAnchor="middle" fill="#fca5a5" fontSize="8" fontFamily="monospace">writer_connection (exclusive write)</text>
            </g>

            {/* Connection Lines */}
            <path d="M 330 75 L 330 95 L 150 95 L 150 115" fill="none" stroke="#10b981" strokeWidth="1.2" strokeDasharray="3 2" markerEnd="url(#db-arrow)" />
            <path d="M 330 75 L 330 95 L 510 95 L 510 115" fill="none" stroke="#10b981" strokeWidth="1.2" strokeDasharray="3 2" markerEnd="url(#db-arrow)" />
          </svg>
        </div>
      </section>

      <NextSteps />
    </div>
  )
}
