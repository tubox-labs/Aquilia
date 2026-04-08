import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { GitBranch } from 'lucide-react'

export function SqliteTransactions() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <GitBranch className="w-4 h-4" />
          SQLite › Transactions
        </div>
        <h1 className={`text-4xl mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono">
            Transactions & Savepoints
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Master atomic operations with transactions and nested savepoints.
        </p>
      </div>

      {/* Basic Transactions */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Basic Transactions
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Use <code className="text-aquilia-500">transaction()</code> to ensure atomic operations.
        </p>

        <CodeBlock language="python">{`from aquilia.sqlite import create_pool

pool = await create_pool("app.db")

async with pool.acquire() as conn:
    async with conn.transaction():
        # All operations are atomic
        await conn.execute(
            "INSERT INTO users (name, email) VALUES (?, ?)",
            ("Alice", "alice@example.com")
        )
        await conn.execute(
            "INSERT INTO posts (user_id, title) VALUES (?, ?)",
            (1, "My First Post")
        )
        # Auto-commits on success
        # Auto-rolls back on exception`}</CodeBlock>

        <div className={`mt-6 p-4 rounded-xl border ${isDark ? 'bg-blue-500/10 border-blue-500/20' : 'bg-blue-50 border-blue-200'}`}>
          <p className={`text-sm ${isDark ? 'text-blue-300' : 'text-blue-900'}`}>
            <strong>Automatic commit/rollback:</strong> The transaction commits when the context exits successfully, and rolls back on any exception.
          </p>
        </div>
      </section>

      {/* Manual Control */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Manual Commit/Rollback
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Explicit control over when to commit or rollback.
        </p>

        <CodeBlock language="python">{`async with pool.acquire() as conn:
    # Start implicit transaction
    await conn.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))
    
    # Explicitly commit
    await conn.commit()
    
    # Another transaction
    await conn.execute("INSERT INTO users (name) VALUES (?)", ("Bob",))
    
    # Explicitly rollback
    await conn.rollback()`}</CodeBlock>
      </section>

      {/* Savepoints */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Savepoints (Nested Transactions)
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Create nested savepoints to rollback partial work.
        </p>

        <CodeBlock language="python">{`async with pool.acquire() as conn:
    async with conn.transaction():
        # Insert user (will commit)
        await conn.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))
        
        # Nested savepoint
        try:
            async with conn.savepoint("sp1"):
                await conn.execute("INSERT INTO users (name) VALUES (?)", ("Bob",))
                raise Exception("Oops, rollback Bob")
        except Exception:
            pass  # Bob is rolled back, Alice remains
        
        # Another savepoint
        async with conn.savepoint("sp2"):
            await conn.execute("INSERT INTO users (name) VALUES (?)", ("Charlie",))
        
    # Transaction commits: Alice and Charlie saved, Bob rolled back`}</CodeBlock>
      </section>

      {/* Nested Example */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Deep Nesting
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Savepoints can be nested arbitrarily deep.
        </p>

        <CodeBlock language="python">{`async with conn.transaction():
    await conn.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))
    
    async with conn.savepoint("level1"):
        await conn.execute("INSERT INTO users (name) VALUES (?)", ("Bob",))
        
        async with conn.savepoint("level2"):
            await conn.execute("INSERT INTO users (name) VALUES (?)", ("Charlie",))
            
            async with conn.savepoint("level3"):
                await conn.execute("INSERT INTO users (name) VALUES (?)", ("David",))
                raise Exception("Rollback David only")
            
            # Charlie is safe
        # Bob is safe
    # Alice is safe`}</CodeBlock>
      </section>

      {/* Error Handling */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Error Handling
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Handle constraint violations and rollback gracefully.
        </p>

        <CodeBlock language="python">{`from aquilia.sqlite import SqliteIntegrityError

async with pool.acquire() as conn:
    async with conn.transaction():
        await conn.execute("INSERT INTO users (id, name) VALUES (?, ?)", (1, "Alice"))
        
        try:
            # This will fail (duplicate id)
            await conn.execute("INSERT INTO users (id, name) VALUES (?, ?)", (1, "Bob"))
        except SqliteIntegrityError:
            # Handle constraint violation
            print("User ID already exists")
            # Transaction still active, can continue
            await conn.execute("INSERT INTO users (id, name) VALUES (?, ?)", (2, "Bob"))
        
        # Transaction commits both Alice and Bob (id=2)`}</CodeBlock>
      </section>

      {/* Isolation Levels */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Isolation Levels
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          SQLite supports three isolation levels.
        </p>

        <div className={`overflow-x-auto rounded-xl border ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={isDark ? 'bg-white/5' : 'bg-gray-50'}>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Level</th>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/10' : 'divide-gray-200'}`}>
              <tr>
                <td className={`px-4 py-3 font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>DEFERRED</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Lock acquired on first write (default)</td>
              </tr>
              <tr>
                <td className={`px-4 py-3 font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>IMMEDIATE</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Lock acquired immediately</td>
              </tr>
              <tr>
                <td className={`px-4 py-3 font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>EXCLUSIVE</td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Exclusive lock, no other connections allowed</td>
              </tr>
            </tbody>
          </table>
        </div>

        <CodeBlock language="python">{`# Default: DEFERRED
async with conn.transaction():
    pass

# Start with IMMEDIATE lock
async with conn.transaction(mode="IMMEDIATE"):
    pass

# Exclusive lock
async with conn.transaction(mode="EXCLUSIVE"):
    pass`}</CodeBlock>
      </section>

      {/* Read-Only Transactions */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Read-Only Transactions
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Optimize reads by using read-only connections.
        </p>

        <CodeBlock language="python">{`# Pool automatically routes reads to reader connections
rows = await pool.fetchall("SELECT * FROM users")

# Or explicitly use a reader
async with pool.acquire(write=False) as conn:
    rows = await conn.fetchall("SELECT * FROM users")`}</CodeBlock>
      </section>

      {/* Common Pitfalls */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Common Pitfalls
        </h2>

        <div className="space-y-6">
          <div className={`p-4 rounded-xl border ${isDark ? 'bg-amber-500/10 border-amber-500/20' : 'bg-amber-50 border-amber-200'}`}>
            <h4 className="font-semibold text-amber-600 dark:text-amber-400 mb-2">1. Forgetting to commit</h4>
            <CodeBlock language="python">{`# BAD: Changes are lost
async with pool.acquire() as conn:
    await conn.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))
    # Missing: await conn.commit()

# GOOD: Use transaction context
async with pool.acquire() as conn:
    async with conn.transaction():
        await conn.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))
        # Auto-commits`}</CodeBlock>
          </div>

          <div className={`p-4 rounded-xl border ${isDark ? 'bg-amber-500/10 border-amber-500/20' : 'bg-amber-50 border-amber-200'}`}>
            <h4 className="font-semibold text-amber-600 dark:text-amber-400 mb-2">2. Long-running transactions</h4>
            <CodeBlock language="python">{`# BAD: Locks database for entire request
async with conn.transaction():
    user = await conn.fetchone("SELECT * FROM users WHERE id = ?", (1,))
    await external_api_call(user)  # DON'T DO THIS
    await conn.execute("UPDATE users SET last_seen = ? WHERE id = ?", (now, 1))

# GOOD: Keep transactions short
user = await conn.fetchone("SELECT * FROM users WHERE id = ?", (1,))
await external_api_call(user)
async with conn.transaction():
    await conn.execute("UPDATE users SET last_seen = ? WHERE id = ?", (now, 1))`}</CodeBlock>
          </div>

          <div className={`p-4 rounded-xl border ${isDark ? 'bg-amber-500/10 border-amber-500/20' : 'bg-amber-50 border-amber-200'}`}>
            <h4 className="font-semibold text-amber-600 dark:text-amber-400 mb-2">3. Nesting transactions (use savepoints)</h4>
            <CodeBlock language="python">{`# BAD: Cannot nest transactions
async with conn.transaction():
    async with conn.transaction():  # ERROR!
        pass

# GOOD: Use savepoints
async with conn.transaction():
    async with conn.savepoint("sp1"):
        pass`}</CodeBlock>
          </div>
        </div>
      </section>
    </div>
  )
}
