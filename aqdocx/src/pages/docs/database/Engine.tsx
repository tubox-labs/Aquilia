import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview'
import { Link } from 'react-router-dom'
import { Database, ArrowLeft, ArrowRight } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function DatabaseEngine() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const t = (d: string, l: string) => isDark ? d : l

  return (
    <div className="max-w-4xl mx-auto">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm mb-6">
        <Link to="/docs" className={t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}>Docs</Link>
        <span className={t('text-gray-500','text-gray-400')}>/</span>
        <Link to="/docs/database" className={t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}>Database</Link>
        <span className={t('text-gray-500','text-gray-400')}>/</span>
        <span className={t('text-gray-300','text-gray-600')}>AquiliaDatabase</span>
      </div>

      {/* Header */}
      <div className="mb-10">
        <h1 className={`text-4xl font-bold tracking-tighter mb-4 ${t('text-white','text-gray-900')}`}>
          <span className="gradient-text font-mono">AquiliaDatabase</span>
        </h1>
        <p className={`text-xl leading-relaxed ${t('text-gray-300','text-gray-600')}`}>
          The central async database engine — connection lifecycle, raw query API, transactions, savepoints, and introspection. Registered as a DI <code>@service(scope="app")</code>.
        </p>
      </div>

      {/* Class signature callout */}
      <div className={`rounded-xl p-5 mb-10 border ${t('bg-gray-900 border-gray-700','bg-gray-50 border-gray-200')}`}>
        <div className="flex items-start gap-3">
          <Database className={`w-5 h-5 mt-0.5 shrink-0 ${t('text-aquilia-400','text-blue-600')}`} />
          <div className="min-w-0 flex-1">
            <div className={`font-mono text-sm font-semibold mb-1 ${t('text-white','text-gray-900')}`}>
              <DocTerm id="db.aquilia_database">AquiliaDatabase</DocTerm>
            </div>
            <p className={`text-xs ${t('text-gray-400','text-gray-500')}`}>
              Source: <code>aquilia/db/engine.py:89</code> · DI scope: <code>app</code>
            </p>
          </div>
        </div>
      </div>

      {/* Constructor */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Constructor</h2>
        <CodeBlock language="python">{`class AquiliaDatabase:
    def __init__(
        self,
        url: str | None = None,
        *,
        config: DatabaseConfig | None = None,
        connect_retries: int = 3,
        connect_retry_delay: float = 0.5,
        **options,
    ): ...`}</CodeBlock>

        <div className={`mt-4 rounded-xl border overflow-hidden ${t('border-gray-700','border-gray-200')}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={t('bg-gray-800','bg-gray-50')}>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Param</th>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Type</th>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${t('divide-gray-700','divide-gray-200')}`}>
              {[
                ['url', 'str | None', 'Database URL. Supported schemes: sqlite:///, postgresql://, mysql://, oracle://'],
                ['config', 'DatabaseConfig | None', 'Typed config (SqliteConfig, PostgresConfig, MysqlConfig, OracleConfig). Takes precedence over url.'],
                ['connect_retries', 'int', 'Number of connection attempts before raising DatabaseConnectionFault. Default: 3.'],
                ['connect_retry_delay', 'float', 'Seconds between retry attempts. Default: 0.5.'],
              ].map(([p,type,desc]) => (
                <tr key={p}>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-aquilia-400','text-aquilia-600')}`}>{p}</td>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-gray-400','text-gray-500')}`}>{type}</td>
                  <td className={`px-4 py-3 text-xs ${t('text-gray-300','text-gray-600')}`}>{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <CodeBlock language="python">{`from aquilia.db import AquiliaDatabase
from aquilia.db.configs import PostgresConfig, SqliteConfig

# URL string
db = AquiliaDatabase("sqlite:///app.db")
db = AquiliaDatabase("postgresql://admin:s3cr3t@localhost/mydb")

# Typed config (recommended — IDE autocompletion)
db = AquiliaDatabase(config=PostgresConfig(
    host="localhost", database="mydb", user="admin", password="s3cr3t",
    pool_size=20, sslmode="require",
))

# Custom retry
db = AquiliaDatabase("postgresql://...", connect_retries=5, connect_retry_delay=1.0)`}</CodeBlock>
      </section>

      {/* Connection management */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Connection Management</h2>
        <div className={`rounded-xl border overflow-hidden mb-4 ${t('border-gray-700','border-gray-200')}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={t('bg-gray-800','bg-gray-50')}>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Method</th>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${t('divide-gray-700','divide-gray-200')}`}>
              {[
                ['connect()', 'Open the database connection with retry logic.'],
                ['disconnect()', 'Close the connection cleanly.'],
                ['ensure_connected()', 'Reconnect if the connection was dropped.'],
                ['on_startup()', 'Lifecycle hook — called by LifecycleCoordinator at app start.'],
                ['on_shutdown()', 'Lifecycle hook — called at app shutdown.'],
              ].map(([m,d]) => (
                <tr key={m}>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-aquilia-400','text-aquilia-600')}`}>{m}</td>
                  <td className={`px-4 py-3 text-xs ${t('text-gray-300','text-gray-600')}`}>{d}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Query methods */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Query Methods</h2>
        <div className={`rounded-xl border overflow-hidden mb-6 ${t('border-gray-700','border-gray-200')}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={t('bg-gray-800','bg-gray-50')}>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Method</th>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Returns</th>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${t('divide-gray-700','divide-gray-200')}`}>
              {[
                ['execute(sql, params)', 'cursor', 'Run INSERT/UPDATE/DELETE. Returns cursor with lastrowid, rowcount.'],
                ['execute_many(sql, params_list)', 'None', 'Run same SQL with multiple parameter sets (bulk ops).'],
                ['fetch_all(sql, params)', 'list[dict]', 'Run SELECT, return all rows as list of dicts.'],
                ['fetch_one(sql, params)', 'dict | None', 'Run SELECT, return first row as dict or None.'],
                ['fetch_val(sql, params)', 'Any', 'Run SELECT, return scalar from row[0][col[0]].'],
              ].map(([m,r,d]) => (
                <tr key={m}>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-aquilia-400','text-aquilia-600')}`}>
                    <DocTerm id={
                      m.startsWith('execute_many') ? 'db.execute_many' :
                      m.startsWith('execute') ? 'db.execute' :
                      m.startsWith('fetch_all') ? 'db.fetch_all' :
                      m.startsWith('fetch_one') ? 'db.fetch_one' : 'db.fetch_val'
                    }>{m}</DocTerm>
                  </td>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-gray-400','text-gray-500')}`}>{r}</td>
                  <td className={`px-4 py-3 text-xs ${t('text-gray-300','text-gray-600')}`}>{d}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <CodeBlock language="python">{`# All methods use ? placeholders — adapter normalises per backend
rows  = await db.fetch_all("SELECT * FROM users WHERE active = ?", [True])
row   = await db.fetch_one("SELECT * FROM users WHERE id = ?", [42])
count = await db.fetch_val("SELECT COUNT(*) FROM orders WHERE status = ?", ["paid"])

res   = await db.execute("UPDATE users SET active = ? WHERE id = ?", [False, 99])
print(res.rowcount)   # rows affected

await db.execute_many(
    "INSERT INTO tags (name) VALUES (?)",
    [["python"], ["async"], ["orm"]],
)`}</CodeBlock>
      </section>

      {/* Transactions */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Transactions</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Use the <DocTerm id="db.transaction">transaction()</DocTerm> context manager for automatic commit / rollback. For manual control call <code>begin()</code>, <code>commit()</code>, <code>rollback()</code> directly.
        </p>
        <CodeBlock language="python">{`# Context manager (recommended)
async with db.transaction():
    await db.execute("INSERT INTO orders ...")
    await db.execute("UPDATE inventory ...")
    # Commits if no exception, rolls back otherwise

# Manual
await db.begin(isolation="REPEATABLE READ")
try:
    await db.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", [100, 1])
    await db.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", [100, 2])
    await db.commit()
except Exception:
    await db.rollback()
    raise`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-8 mb-3 ${t('text-white','text-gray-900')}`}>Savepoints</h3>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Nested checkpoints inside a transaction. Name must match <code>[a-zA-Z_][a-zA-Z0-9_]*</code>.
        </p>
        <CodeBlock language="python">{`await db.begin()

await db.savepoint("before_risky_op")
try:
    await db.execute("DELETE FROM temporary_data WHERE expired = ?", [True])
    await db.release_savepoint("before_risky_op")    # commit savepoint
except Exception:
    await db.rollback_to_savepoint("before_risky_op") # undo only this block

await db.commit()`}</CodeBlock>

        <div className={`mt-4 p-4 rounded-lg border flex gap-2 ${t('bg-amber-500/10 border-amber-500/20','bg-amber-50 border-amber-200')}`}>
          <span className={`text-xs mt-0.5 ${t('text-amber-300','text-amber-700')}`}>⚠️</span>
          <p className={`text-xs ${t('text-amber-200','text-amber-700')}`}>
            <strong>Prefer <DocTerm id="orm.atomic">atomic()</DocTerm> from the ORM layer</strong> when working with Model.save() — it integrates with signals and on_commit hooks. Use <code>db.transaction()</code> for raw SQL blocks only.
          </p>
        </div>
      </section>

      {/* Introspection */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Schema Introspection</h2>
        <div className={`rounded-xl border overflow-hidden mb-4 ${t('border-gray-700','border-gray-200')}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={t('bg-gray-800','bg-gray-50')}>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Method</th>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Returns</th>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${t('divide-gray-700','divide-gray-200')}`}>
              {[
                ['table_exists(name)', 'bool', 'Check if table exists.'],
                ['get_tables()', 'list[str]', 'List all table names in the database.'],
                ['get_columns(table)', 'list[ColumnInfo]', 'Column metadata: name, type, nullable, default, primary_key.'],
              ].map(([m,r,d]) => (
                <tr key={m}>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-aquilia-400','text-aquilia-600')}`}>{m}</td>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-gray-400','text-gray-500')}`}>{r}</td>
                  <td className={`px-4 py-3 text-xs ${t('text-gray-300','text-gray-600')}`}>{d}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <CodeBlock language="python">{`tables = await db.get_tables()
# ["users", "posts", "tags", "migrations"]

exists = await db.table_exists("sessions")

cols = await db.get_columns("users")
for col in cols:
    print(f"{col.name}: {col.type} {'NOT NULL' if not col.nullable else ''}")`}</CodeBlock>
      </section>

      {/* Module-level functions */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Module-Level Functions</h2>
        <CodeBlock language="python">{`from aquilia.db import configure_database, get_database, set_database, get_all_databases

# Configure (called automatically by Integration.database())
db = configure_database(url="sqlite:///app.db")
db = configure_database(config=PostgresConfig(...), alias="primary")

# Retrieve
db = get_database()             # default
db = get_database("primary")    # named alias

# Replace an existing instance
set_database(my_db, alias="default")

# All configured databases
all_dbs = get_all_databases()   # {"default": AquiliaDatabase, ...}`}</CodeBlock>
      </section>

      {/* Faults */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Faults</h2>
        <div className={`rounded-xl border overflow-hidden ${t('border-gray-700','border-gray-200')}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={t('bg-gray-800','bg-gray-50')}>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Fault</th>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>When raised</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${t('divide-gray-700','divide-gray-200')}`}>
              {[
                ['DatabaseConnectionFault', 'Connection fails after all retries, or disconnect fails.'],
                ['QueryFault', 'execute/fetch fails due to SQL error or driver exception.'],
                ['SchemaFault', 'DDL (CREATE TABLE, ALTER TABLE) operation fails.'],
              ].map(([f,d]) => (
                <tr key={f}>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-rose-400','text-rose-600')}`}>{f}</td>
                  <td className={`px-4 py-3 text-xs ${t('text-gray-300','text-gray-600')}`}>{d}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <CodeBlock language="python">{`from aquilia.models import DatabaseConnectionFault, QueryFault

try:
    rows = await db.fetch_all("SELECT * FROM users")
except QueryFault as e:
    print(e.reason, e.metadata)
except DatabaseConnectionFault as e:
    print("Connection lost:", e.reason)`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex justify-between items-center pt-8 mt-8 border-t ${t('border-gray-700','border-gray-200')}`}>
        <Link to="/docs/database" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          <ArrowLeft className="w-4 h-4" /> Overview
        </Link>
        <Link to="/docs/database/configs" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          Config Classes <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
      <NextSteps />
    </div>
  )
}