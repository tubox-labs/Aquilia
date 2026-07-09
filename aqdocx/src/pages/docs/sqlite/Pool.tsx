import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { NextSteps } from '../../../components/NextSteps'
import { Settings, ShieldAlert, BarChart2 } from 'lucide-react'

export function SqlitePool() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      {/* Title Header */}
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Settings className="w-4 h-4 animate-pulse" />
          SQLite / Pool Configuration
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          Pool Configuration
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          Fine-tune the SQLite connection pool settings, sizing limits, PRAGMA parameters, and statement caches for production workloads.
        </p>
      </div>

      {/* Configuration Dataclass */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Settings className="w-5 h-5 text-aquilia-500" />
          Configuring via SqlitePoolConfig
        </h2>
        <p className={`mb-6 ${subtleText}`}>
          All connection pool settings are configured via the <DocTerm id="sqlite.SqlitePoolConfig">SqlitePoolConfig</DocTerm> dataclass, which is passed to <DocTerm id="sqlite.create_pool">create_pool()</DocTerm>.
        </p>

        <CodeBlock language="python">{`from aquilia.sqlite import create_pool, SqlitePoolConfig

config = SqlitePoolConfig(
    path="app.db",
    
    # Pool sizing & timeouts
    pool_size=10,                 # Number of concurrent reader connections
    pool_min_size=4,              # Pre-opened reader connections
    pool_timeout=30.0,            # Wait limit to acquire connection (seconds)
    pool_max_idle_time=300.0,     # Eviction time for idle connections (seconds)
    
    # Cache settings
    cache_size=-16000,            # Negative = KiB (16MB memory cache)
    statement_cache_size=256,     # Max cached prepared statements per connection
)

pool = await create_pool(config)`}</CodeBlock>
      </section>

      {/* Journal Modes */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          SQLite Journal Modes
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Controls how SQLite handles transaction logs on disk. WAL mode is highly recommended as it enables multi-reader concurrency.
        </p>

        <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl mb-6">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="text-left py-4 px-6 font-semibold text-aquilia-500">Journal Mode</th>
                <th className="text-left py-4 px-6 font-semibold">Description</th>
                <th className="text-left py-4 px-6 font-semibold">Concurrency Level</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['WAL', 'Write-Ahead Logging. Writes are saved to a separate -wal file.', 'Multi-reader concurrent with single-writer (Recommended)'],
                ['DELETE', 'Rollback journal is deleted at the end of each transaction.', 'Sequential reads and writes (locks entire DB)'],
                ['MEMORY', 'Rollback journal is stored in RAM only.', 'Faster, but risks database corruption if process crashes'],
                ['OFF', 'No rollback journal is kept.', 'Fastest, but no rollback or recovery capability (Dangerous)'],
              ].map(([mode, desc, conc], i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                  <td className="py-3.5 px-6 font-mono text-xs text-aquilia-400">{mode}</td>
                  <td className={`py-3.5 px-6 text-xs ${subtleText}`}>{desc}</td>
                  <td className="py-3.5 px-6 font-mono text-xs">{conc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Synchronous Modes */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Synchronous Disk Flushing
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Determines how aggressively SQLite forces disk syncs (<code className="text-aquilia-500">fsync</code>). When using WAL mode, <code className="text-aquilia-500">NORMAL</code> is recommended.
        </p>

        <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl mb-6">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="text-left py-4 px-6 font-semibold text-aquilia-500">Sync Mode</th>
                <th className="text-left py-4 px-6 font-semibold">Disk Flushing</th>
                <th className="text-left py-4 px-6 font-semibold">Safety Level</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['FULL', 'Flushes log files and database directories at every checkpoint.', 'Maximum safety (survives sudden host power cuts)'],
                ['NORMAL', 'Flushes at key transaction boundaries. Safe in WAL mode.', 'Very good safety (recommended for performance + integrity)'],
                ['OFF', 'Does not flush to disk (delegates to OS cache).', 'No safety guarantees (database easily corrupts on host failure)'],
              ].map(([mode, flush, safety], i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                  <td className="py-3.5 px-6 font-mono text-xs text-aquilia-400">{mode}</td>
                  <td className={`py-3.5 px-6 text-xs ${subtleText}`}>{flush}</td>
                  <td className="py-3.5 px-6 font-mono text-xs">{safety}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Performance Optimization */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Performance Optimization Settings
        </h2>
        <div className="space-y-6">
          <div>
            <h3 className="font-semibold mb-2">Memory-Mapped I/O (<code className="text-aquilia-500">mmap_size</code>)</h3>
            <p className={`text-sm mb-3 ${subtleText}`}>
              Memory-mapping maps database pages directly into host process RAM, bypassing system call read paths. Highly recommended for read-heavy databases.
            </p>
            <CodeBlock language="python">{`# Enable 256MB memory mapping
config = SqlitePoolConfig(mmap_size=268435456)`}</CodeBlock>
            <div className="group relative overflow-hidden rounded-xl bg-amber-500/5 border border-amber-500/20 p-4 mt-3">
              <div className="flex gap-2">
                <ShieldAlert className="w-5 h-5 text-amber-500 shrink-0" />
                <p className={`text-xs leading-relaxed ${subtleText}`}>
                  <strong>Warning:</strong> Set <code className="text-aquilia-500">mmap_size=0</code> for databases that are extremely write-heavy to prevent memory thrashing.
                </p>
              </div>
            </div>
          </div>

          <div>
            <h3 className="font-semibold mb-2">Statement Cache (<code className="text-aquilia-500">statement_cache_size</code>)</h3>
            <p className={`text-sm mb-3 ${subtleText}`}>
              Caches prepared SQL queries to eliminate SQL parsing overhead on subsequent executions.
            </p>
            <CodeBlock language="python">{`# Cache 256 prepared statements per connection
config = SqlitePoolConfig(statement_cache_size=256)`}</CodeBlock>
          </div>
        </div>
      </section>

      {/* Uptime & Connection Metrics */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <BarChart2 className="w-5 h-5 text-aquilia-500" />
          Uptime & Performance Metrics
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Inspect connection pool allocations and statements caching hits:
        </p>

        <CodeBlock language="python">{`# Inspect active connection counters
print(f"Total Queries: {pool.metrics.total_queries}")
print(f"Active Reader Connections: {pool.metrics.active_readers}")
print(f"Average Query Duration: {pool.metrics.avg_query_time_ms}ms")

# Inspect statement cache efficiency stats
print(f"Prepared Cache Hits: {pool.cache_stats.hits}")
print(f"Prepared Cache Misses: {pool.cache_stats.misses}")
print(f"Hit Rate Percent: {pool.cache_stats.hit_rate_pct}%")`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
