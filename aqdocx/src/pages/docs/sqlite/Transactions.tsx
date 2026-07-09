import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { NextSteps } from '../../../components/NextSteps'
import { GitBranch, AlertTriangle } from 'lucide-react'

export function SqliteTransactions() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      {/* Title Header */}
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <GitBranch className="w-4 h-4 animate-pulse" />
          SQLite / Transactions & Savepoints
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          Transactions & Savepoints
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          Execute atomic block queries with automatic transaction rollbacks and nested savepoints.
        </p>
      </div>

      {/* Basic Transactions */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Basic Transactions
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Use the <code className="text-aquilia-500">transaction()</code> context manager of a connection to run multiple queries atomically. By default, transactions run in <code className="text-aquilia-500">DEFERRED</code> mode.
        </p>

        <CodeBlock language="python">{`async with pool.acquire(readonly=False) as conn:
    async with conn.transaction():
        # Both inserts succeed together, or both are rolled back on error
        await conn.execute(
            "INSERT INTO users (name, email) VALUES (?, ?)", ["Alice", "alice@example.com"]
        )
        await conn.execute(
            "INSERT INTO settings (user_name, theme) VALUES (?, ?)", ["Alice", "dark"]
        )`}</CodeBlock>

        <div className="group relative overflow-hidden rounded-2xl bg-white/5 border border-white/5 p-6 backdrop-blur-sm shadow-xl mt-6">
          <div className="absolute top-0 bottom-0 left-0 w-1 bg-gradient-to-b from-aquilia-500 to-transparent opacity-50" />
          <p className="text-sm leading-relaxed">
            <strong>Auto-Commit / Auto-Rollback:</strong> The transaction is committed automatically when exiting the context block without exceptions. If an unhandled exception occurs inside the block, the transaction is rolled back immediately.
          </p>
        </div>
      </section>

      {/* Savepoints */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Savepoints (Nested Transactions)
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          SQLite does not support nested transactions natively. However, Aquilia provides <code className="text-aquilia-500">savepoint_ctx()</code> to implement nested transaction boundaries that rollback partial work without rolling back the entire parent transaction.
        </p>

        <CodeBlock language="python">{`async with pool.acquire(readonly=False) as conn:
    async with conn.transaction() as parent_txn:
        # Parent insertion
        await conn.execute("INSERT INTO logs (message) VALUES (?)", ["Initial Log"])
        
        try:
            # Nested savepoint context
            async with conn.savepoint_ctx("sp1"):
                await conn.execute("INSERT INTO users (name) VALUES (?)", ["Bob"])
                raise ValueError("Rollback Bob insertion")
        except ValueError:
            # Bob insertion is rolled back, parent logs are preserved
            pass
            
        await conn.execute("INSERT INTO logs (message) VALUES (?)", ["Execution Finished"])`}</CodeBlock>
      </section>

      {/* Transaction Modes */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Transaction Locking Modes
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Control when lock acquisitions are obtained on the database file. Configure via the <code className="text-aquilia-500">mode</code> argument on <code className="text-aquilia-500">transaction()</code>.
        </p>

        <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl mb-6">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="text-left py-4 px-6 font-semibold text-aquilia-500">Lock Mode</th>
                <th className="text-left py-4 px-6 font-semibold">Lock Acquisition</th>
                <th className="text-left py-4 px-6 font-semibold">Typical Use Case</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['DEFERRED', 'No lock is acquired until the first read/write operation is executed (Default).', 'Standard read/write flows.'],
                ['IMMEDIATE', 'Acquires a reserved lock on the database immediately, preventing other writers.', 'Avoids deadlock risks when writing is guaranteed.'],
                ['EXCLUSIVE', 'Acquires an exclusive lock immediately, preventing all other connections (readers and writers).', 'Bulk data operations and migrations.'],
              ].map(([mode, lock, desc], i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                  <td className="py-3.5 px-6 font-mono text-xs text-aquilia-400">{mode}</td>
                  <td className={`py-3.5 px-6 text-xs ${subtleText}`}>{lock}</td>
                  <td className="py-3.5 px-6 text-xs">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Reader Routing */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Read-Only Connections
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Maximize WAL concurrency by explicitly acquiring read-only connections. The pool routes read queries to the parallel reader pool when <code className="text-aquilia-500">readonly=True</code> is passed.
        </p>
        <CodeBlock language="python">{`# Acquire a read-only reader connection (does not block the writer connection)
async with pool.acquire(readonly=True) as conn:
    rows = await conn.fetch_all("SELECT * FROM users WHERE active = 1")`}</CodeBlock>
      </section>

      {/* Pitfalls */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <AlertTriangle className="w-5 h-5 text-amber-500" />
          Common Pitfalls
        </h2>
        <div className="space-y-6">
          <div className="group relative overflow-hidden rounded-2xl bg-white/5 border border-white/5 p-5 transition-all duration-300">
            <div className="absolute top-0 bottom-0 left-0 w-1 bg-white/5 group-hover:bg-aquilia-500 transition-colors duration-300" />
            <h4 className="font-semibold mb-2">1. Nested Transaction Calls</h4>
            <p className={`text-xs mb-3 ${subtleText}`}>
              Calling nested <code className="text-aquilia-500">conn.transaction()</code> blocks within each other raises an error. Always use savepoint contexts for nesting.
            </p>
            <CodeBlock language="python">{`# BAD - Will raise error
async with conn.transaction():
    async with conn.transaction():  # Raises TransactionFault
        pass

# GOOD - Use savepoint contexts
async with conn.transaction():
    async with conn.savepoint_ctx("sp_checkpoint"):
        pass`}</CodeBlock>
          </div>

          <div className="group relative overflow-hidden rounded-2xl bg-white/5 border border-white/5 p-5 transition-all duration-300">
            <div className="absolute top-0 bottom-0 left-0 w-1 bg-white/5 group-hover:bg-aquilia-500 transition-colors duration-300" />
            <h4 className="font-semibold mb-2">2. Network I/O Inside Transactions</h4>
            <p className={`text-xs mb-3 ${subtleText}`}>
              Since SQLite serialization restricts concurrent writes, holding a transaction open while executing slow HTTP requests blocks other writers.
            </p>
            <CodeBlock language="python">{`# BAD - Blocks the single database writer connection
async with conn.transaction():
    await conn.execute("UPDATE users SET processing = 1 WHERE id = ?", [user_id])
    await call_third_party_api()  # Network call blocks connection pool
    await conn.execute("UPDATE users SET processed = 1 WHERE id = ?", [user_id])

# GOOD - Keep transaction blocks brief
await conn.execute("UPDATE users SET processing = 1 WHERE id = ?", [user_id])
await call_third_party_api()
async with conn.transaction():
    await conn.execute("UPDATE users SET processed = 1 WHERE id = ?", [user_id])`}</CodeBlock>
          </div>
        </div>
      </section>

      <NextSteps />
    </div>
  )
}
