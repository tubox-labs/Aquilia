import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Settings } from 'lucide-react'

export function SqlitePool() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Settings className="w-4 h-4" />
          SQLite › Pool Configuration
        </div>
        <h1 className={`text-4xl mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono">
            Pool Configuration
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Fine-tune connection pool settings for optimal performance.
        </p>
      </div>

      {/* Basic Configuration */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Basic Configuration
        </h2>

        <CodeBlock language="python">{`from aquilia.sqlite import create_pool

pool = await create_pool(
    database="app.db",               # Database file path or ":memory:"
    max_readers=10,                  # Max concurrent readers
    timeout=30.0,                    # Connection acquire timeout (seconds)
    check_same_thread=False,         # Allow cross-thread usage
)`}</CodeBlock>
      </section>

      {/* Journal Modes */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Journal Modes
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Controls how SQLite manages transaction logs.
        </p>

        <div className={`overflow-x-auto rounded-xl border ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={isDark ? 'bg-white/5' : 'bg-gray-50'}>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Mode</th>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Description</th>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Best For</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/10' : 'divide-gray-200'}`}>
              <tr>
                <td className={`px-4 py-3 font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>WAL</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Write-ahead logging (recommended)</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Concurrent reads + writes</td>
              </tr>
              <tr>
                <td className={`px-4 py-3 font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>DELETE</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Classic rollback journal (default)</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Simple deployments</td>
              </tr>
              <tr>
                <td className={`px-4 py-3 font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>MEMORY</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>In-memory journal</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Temporary databases</td>
              </tr>
              <tr>
                <td className={`px-4 py-3 font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>OFF</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>No journal (dangerous)</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Bulk imports only</td>
              </tr>
            </tbody>
          </table>
        </div>

        <CodeBlock language="python">{`# Recommended: WAL mode for concurrent reads
pool = await create_pool(
    database="app.db",
    journal_mode="WAL",
)`}</CodeBlock>
      </section>

      {/* Synchronous Modes */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Synchronous Modes
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Controls how aggressively SQLite syncs to disk.
        </p>

        <div className={`overflow-x-auto rounded-xl border ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={isDark ? 'bg-white/5' : 'bg-gray-50'}>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Mode</th>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Speed</th>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Safety</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/10' : 'divide-gray-200'}`}>
              <tr>
                <td className={`px-4 py-3 font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>FULL</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Slowest</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Maximum (survives power loss)</td>
              </tr>
              <tr>
                <td className={`px-4 py-3 font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>NORMAL</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Balanced</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Good (recommended)</td>
              </tr>
              <tr>
                <td className={`px-4 py-3 font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>OFF</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Fastest</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>None (corruption risk)</td>
              </tr>
            </tbody>
          </table>
        </div>

        <CodeBlock language="python">{`# Recommended: NORMAL for most apps
pool = await create_pool(
    database="app.db",
    synchronous="NORMAL",
)`}</CodeBlock>
      </section>

      {/* Cache Configuration */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Cache Configuration
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Control SQLite page cache size.
        </p>

        <CodeBlock language="python">{`pool = await create_pool(
    database="app.db",
    cache_size=-64000,               # Negative = KB, positive = pages
                                     # -64000 = 64MB cache
    statement_cache_size=128,        # Prepared statement cache
)`}</CodeBlock>

        <div className={`mt-6 p-4 rounded-xl border ${isDark ? 'bg-blue-500/10 border-blue-500/20' : 'bg-blue-50 border-blue-200'}`}>
          <p className={`text-sm ${isDark ? 'text-blue-300' : 'text-blue-900'}`}>
            <strong>Tip:</strong> Use negative values for cache_size to specify size in KB. Larger caches improve performance for repeated queries.
          </p>
        </div>
      </section>

      {/* Memory-Mapped I/O */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Memory-Mapped I/O
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Enable memory-mapped I/O for read-heavy workloads.
        </p>

        <CodeBlock language="python">{`pool = await create_pool(
    database="app.db",
    mmap_size=268435456,             # 256MB memory-mapped (0 = disabled)
)`}</CodeBlock>

        <div className={`mt-6 p-4 rounded-xl border ${isDark ? 'bg-amber-500/10 border-amber-500/20' : 'bg-amber-50 border-amber-200'}`}>
          <p className={`text-sm ${isDark ? 'text-amber-300' : 'text-amber-900'}`}>
            <strong>Warning:</strong> mmap_size should be 0 for write-heavy workloads. Use only for read-heavy databases.
          </p>
        </div>
      </section>

      {/* Complete Example */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Production Configuration
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Recommended settings for production.
        </p>

        <CodeBlock language="python">{`from aquilia.sqlite import create_pool

# High-traffic web app
pool = await create_pool(
    database="app.db",
    
    # Pool settings
    max_readers=20,                  # Scale with CPU cores
    timeout=30.0,                    # Connection timeout
    
    # Journal settings (WAL for concurrent reads)
    journal_mode="WAL",
    synchronous="NORMAL",            # Balance speed + safety
    
    # Performance
    cache_size=-128000,              # 128MB cache
    mmap_size=0,                     # Disabled (write-heavy)
    statement_cache_size=256,        # Large statement cache
    
    # Lock handling
    busy_timeout=10000,              # 10 seconds on SQLITE_BUSY
)`}</CodeBlock>
      </section>

      {/* Metrics */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Pool Metrics
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Monitor pool health and performance.
        </p>

        <CodeBlock language="python">{`# Get pool metrics
metrics = pool.metrics

print(f"Total queries: {metrics.total_queries}")
print(f"Active connections: {metrics.active_connections}")
print(f"Pool exhausted count: {metrics.pool_exhausted_count}")
print(f"Avg query time: {metrics.avg_query_time_ms:.2f}ms")

# Statement cache stats
cache_stats = pool.cache_stats
print(f"Cache hits: {cache_stats.hits}")
print(f"Cache misses: {cache_stats.misses}")
print(f"Hit rate: {cache_stats.hit_rate:.1%}")`}</CodeBlock>
      </section>
    </div>
  )
}
