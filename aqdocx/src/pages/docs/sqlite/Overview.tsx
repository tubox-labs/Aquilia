import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Database, Zap, Shield, Layers } from 'lucide-react'

export function SqliteOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const features = [
    { icon: Zap, title: 'Native Async Pool', desc: 'Multi-reader + single-writer architecture' },
    { icon: Shield, title: 'Zero Dependencies', desc: 'Uses stdlib sqlite3 only — no aiosqlite required' },
    { icon: Database, title: 'Dict-like Rows', desc: 'Access columns by name, index, or attribute' },
    { icon: Layers, title: 'Transactions & Savepoints', desc: 'Nested transactions with full rollback support' },
  ]

  return (
    <div className="max-w-4xl mx-auto">
      {/* Hero */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Database className="w-4 h-4" />
          SQLite Module
        </div>
        <h1 className={`text-5xl mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono">
            async SQLite
          </span>
        </h1>
        <p className={`text-xl leading-relaxed mb-6 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Zero-dependency native async SQLite module. Built on stdlib <code className="text-aquilia-500">sqlite3</code> with a production-grade connection pool — no aiosqlite needed.
        </p>
      </div>

      {/* Features Grid */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Features
        </h2>
        <div className="grid md:grid-cols-2 gap-6">
          {features.map((feature, i) => (
            <div
              key={i}
              className={`p-6 rounded-xl border ${
                isDark
                  ? 'bg-[#111] border-white/10 hover:border-aquilia-500/50'
                  : 'bg-white border-gray-200 hover:border-aquilia-500/50'
              } transition-colors`}
            >
              <feature.icon className="w-8 h-8 text-aquilia-500 mb-3" />
              <h3 className={`text-lg font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                {feature.title}
              </h3>
              <p className={isDark ? 'text-gray-400' : 'text-gray-600'}>
                {feature.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Quick Start */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Quick Start
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Create a connection pool and run queries.
        </p>

        <CodeBlock language="python">{`from aquilia.sqlite import create_pool

# Create a connection pool
pool = await create_pool(
    database="app.db",
    max_readers=10,          # Max concurrent readers
    timeout=30.0,            # Connection timeout
    journal_mode="WAL",      # Write-ahead logging
)

# Execute a query
async with pool.acquire() as conn:
    # Create table
    await conn.execute(\`\`\`
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE
        )
    \`\`\`)
    
    # Insert data
    await conn.execute(
        "INSERT INTO users (name, email) VALUES (?, ?)",
        ("Alice", "alice@example.com")
    )
    await conn.commit()
    
    # Query data
    rows = await conn.fetchall("SELECT * FROM users")
    for row in rows:
        print(f"{row.id}: {row.name} ({row.email})")`}</CodeBlock>
      </section>

      {/* Architecture */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Pool Architecture
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The pool maintains N readers + 1 writer, all dispatched via <code className="text-aquilia-500">ThreadPoolExecutor</code> to make stdlib sqlite3 async-safe.
        </p>

        <div className={`p-6 rounded-xl border ${isDark ? 'bg-[#111] border-white/10' : 'bg-white border-gray-200'}`}>
          <pre className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>{`┌─────────────────────────────────────┐
│      ConnectionPool                │
├─────────────────────────────────────┤
│ Reader Pool (10 connections)        │
│  ├─ reader_0 (read-only, thread 1)  │
│  ├─ reader_1 (read-only, thread 2)  │
│  └─ ...                             │
│                                     │
│ Writer (1 connection)               │
│  └─ writer (read-write, thread N)   │
│                                     │
│ ThreadPoolExecutor                  │
│  └─ Dispatches all sync ops         │
└─────────────────────────────────────┘`}</pre>
        </div>

        <div className={`mt-6 p-4 rounded-xl border ${isDark ? 'bg-blue-500/10 border-blue-500/20' : 'bg-blue-50 border-blue-200'}`}>
          <p className={`text-sm ${isDark ? 'text-blue-300' : 'text-blue-900'}`}>
            <strong>Why multiple readers?</strong> SQLite supports concurrent reads in WAL mode. The pool creates N reader connections to maximize read throughput.
          </p>
        </div>
      </section>

      {/* Row Object */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Row Object
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Rows are dict-like objects with three access patterns: by name, by index, or by attribute.
        </p>

        <CodeBlock language="python">{`row = await conn.fetchone("SELECT id, name, email FROM users WHERE id = 1")

# Access by attribute
print(row.name)        # "Alice"

# Access by key
print(row["email"])    # "alice@example.com"

# Access by index
print(row[0])          # 1

# Dict conversion
print(dict(row))       # {"id": 1, "name": "Alice", "email": "alice@example.com"}

# Iteration
for value in row:
    print(value)`}</CodeBlock>
      </section>

      {/* Transactions */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Transactions & Savepoints
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Full transaction support with nested savepoints.
        </p>

        <CodeBlock language="python">{`async with pool.acquire() as conn:
    # Start transaction
    async with conn.transaction():
        await conn.execute("INSERT INTO users (name, email) VALUES (?, ?)", ("Bob", "bob@example.com"))
        
        # Nested savepoint
        async with conn.savepoint("sp1"):
            await conn.execute("UPDATE users SET name = ? WHERE id = ?", ("Robert", 2))
            # Rollback this savepoint only
            raise Exception("Oops")
    
    # Transaction auto-commits if no exception
    # Transaction auto-rolls back on exception`}</CodeBlock>
      </section>

      {/* vs aiosqlite */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          vs. aiosqlite
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Why use <code className="text-aquilia-500">aquilia.sqlite</code> instead of <code className="text-aquilia-500">aiosqlite</code>?
        </p>

        <div className={`overflow-x-auto rounded-xl border ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={isDark ? 'bg-white/5' : 'bg-gray-50'}>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Feature</th>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>aquilia.sqlite</th>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>aiosqlite</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/10' : 'divide-gray-200'}`}>
              <tr>
                <td className={`px-4 py-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Connection Pool</td>
                <td className={`px-4 py-3 text-emerald-600 dark:text-emerald-400`}>✓ Built-in</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Manual</td>
              </tr>
              <tr>
                <td className={`px-4 py-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Dict-like Rows</td>
                <td className={`px-4 py-3 text-emerald-600 dark:text-emerald-400`}>✓ row.name, row["name"], row[0]</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>row[0] only</td>
              </tr>
              <tr>
                <td className={`px-4 py-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Nested Transactions</td>
                <td className={`px-4 py-3 text-emerald-600 dark:text-emerald-400`}>✓ Savepoints</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Manual</td>
              </tr>
              <tr>
                <td className={`px-4 py-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Statement Caching</td>
                <td className={`px-4 py-3 text-emerald-600 dark:text-emerald-400`}>✓ Automatic</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>None</td>
              </tr>
              <tr>
                <td className={`px-4 py-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Metrics</td>
                <td className={`px-4 py-3 text-emerald-600 dark:text-emerald-400`}>✓ Observable counters</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>None</td>
              </tr>
              <tr>
                <td className={`px-4 py-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Dependencies</td>
                <td className={`px-4 py-3 text-emerald-600 dark:text-emerald-400`}>✓ Zero (stdlib only)</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Requires aiosqlite</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Configuration */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Pool Configuration
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Configure the connection pool with sensible defaults.
        </p>

        <CodeBlock language="python">{`from aquilia.sqlite import create_pool, SqlitePoolConfig

pool = await create_pool(
    database="app.db",              # Database file path (or ":memory:")
    max_readers=10,                 # Max concurrent readers
    timeout=30.0,                   # Connection timeout (seconds)
    check_same_thread=False,        # Allow cross-thread usage
    
    # WAL mode for concurrent reads
    journal_mode="WAL",             # WAL, DELETE, TRUNCATE, PERSIST, MEMORY, OFF
    
    # Performance tuning
    synchronous="NORMAL",           # OFF, NORMAL, FULL, EXTRA
    cache_size=-64000,              # Negative = KB, positive = pages
    mmap_size=0,                    # Memory-mapped I/O size (0 = disabled)
    
    # Statement caching
    statement_cache_size=128,       # Max cached prepared statements
    
    # Busy timeout
    busy_timeout=5000,              # Milliseconds to wait on SQLITE_BUSY
)`}</CodeBlock>
      </section>

      {/* Next Steps */}
    </div>
  )
}
