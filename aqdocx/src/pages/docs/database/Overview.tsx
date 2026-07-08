import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview'
import { Link } from 'react-router-dom'
import { Database, ArrowRight } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function DatabaseOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const t = (d: string, l: string) => isDark ? d : l

  return (
    <div className="max-w-4xl mx-auto">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm mb-6">
        <Link to="/docs" className={t('text-aquilia-400 hover:text-aquilia-300', 'text-aquilia-600 hover:text-aquilia-500')}>Docs</Link>
        <span className={t('text-gray-500', 'text-gray-400')}>/</span>
        <span className={t('text-gray-300', 'text-gray-600')}>Database Engine</span>
      </div>

      {/* Header */}
      <div className="mb-10">
        <h1 className={`text-4xl font-bold tracking-tighter mb-4 ${t('text-white', 'text-gray-900')}`}>
          <span className="gradient-text font-mono">Database Engine</span>
        </h1>
        <p className={`text-xl leading-relaxed ${t('text-gray-300', 'text-gray-600')}`}>
          Aquilia's database layer is a thin, async-first abstraction over multiple backends. One API — SQLite, PostgreSQL, MySQL, or Oracle. All operations use <code className={t('text-aquilia-400','text-aquilia-600')}>?</code> placeholders; the adapter normalises to the native param style.
        </p>
      </div>

      {/* Architecture callout */}
      <div className={`rounded-xl p-6 mb-10 border ${t('bg-aquilia-500/5 border-aquilia-500/20', 'bg-blue-50/60 border-blue-200/60')}`}>
        <div className="flex items-start gap-3">
          <Database className={`w-5 h-5 mt-0.5 shrink-0 ${t('text-aquilia-400', 'text-blue-600')}`} />
          <div>
            <h3 className={`font-semibold mb-2 ${t('text-aquilia-300', 'text-blue-700')}`}>How it works</h3>
            <p className={`text-sm leading-relaxed ${t('text-aquilia-200', 'text-blue-700')}`}>
              <DocTerm id="db.aquilia_database">AquiliaDatabase</DocTerm> is a DI-registered <code>@service(scope="app")</code>. On startup the{' '}
              <code>LifecycleCoordinator</code> calls <code>on_startup()</code>, which opens a connection (with retry logic). All queries go through backend adapters — <strong>SQLiteAdapter</strong>, <strong>PostgresAdapter</strong> (asyncpg), <strong>MySQLAdapter</strong> (aiomysql), <strong>OracleAdapter</strong> (python-oracledb). The engine records every query duration and emits spans to the active trace for the query inspector.
            </p>
          </div>
        </div>
      </div>

      {/* Quick start */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}>Quick Start</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300', 'text-gray-600')}`}>
          Configure the database in <code>workspace.py</code> via the Integration builder:
        </p>
        <CodeBlock language="python" filename="workspace.py">{`from aquilia.workspace import Workspace, Module
from aquilia.integrations import Integration
from aquilia.db.configs import PostgresConfig

workspace = (
    Workspace("my-api")
    .add_module(Module("users"))
    .integrate(Integration.database(
        config=PostgresConfig(
            host="localhost",
            database="mydb",
            user="admin",
            password="secret",
            pool_size=10,
        )
    ))
    .build()
)`}</CodeBlock>
        <p className={`mt-4 mb-4 text-sm ${t('text-gray-300', 'text-gray-600')}`}>
          Or use a URL string:
        </p>
        <CodeBlock language="python">{`Integration.database(url="postgresql://admin:secret@localhost/mydb")
Integration.database(url="sqlite:///app.db")
Integration.database(url="mysql://root:pass@localhost/mydb")`}</CodeBlock>
      </section>

      {/* Backends grid */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-6 ${t('text-white', 'text-gray-900')}`}>Supported Backends</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {[
            {
              name: 'SQLite',
              driver: 'aquilia.sqlite (native)',
              url: 'sqlite:///path/to/db.sqlite3',
              pkg: 'built-in',
              note: 'WAL mode, connection pooling, in-memory support',
              config: 'SqliteConfig',
              href: '/docs/database/sqlite',
            },
            {
              name: 'PostgreSQL',
              driver: 'asyncpg',
              url: 'postgresql://user:pass@host/db',
              pkg: 'pip install asyncpg',
              note: 'Full async, pool, SSL, JSON, arrays',
              config: 'PostgresConfig',
              href: '/docs/database/postgresql',
            },
            {
              name: 'MySQL / MariaDB',
              driver: 'aiomysql',
              url: 'mysql://user:pass@host/db',
              pkg: 'pip install aiomysql',
              note: 'utf8mb4, connection pool, charset config',
              config: 'MysqlConfig',
              href: '/docs/database/mysql',
            },
            {
              name: 'Oracle',
              driver: 'python-oracledb',
              url: 'oracle://user:pass@host:1521/SERVICE',
              pkg: 'pip install oracledb',
              note: 'Thin mode (no Client), SID or service name',
              config: 'OracleConfig',
              href: '#',
            },
          ].map(b => (
            <div key={b.name} className={`p-5 rounded-xl border ${t('bg-gray-900 border-gray-700/60', 'bg-white border-gray-200')}`}>
              <div className="flex items-center justify-between mb-3">
                <h3 className={`font-bold text-base ${t('text-white', 'text-gray-900')}`}>{b.name}</h3>
                <code className={`text-xs px-1.5 py-0.5 rounded ${t('bg-white/5 text-gray-400', 'bg-gray-100 text-gray-500')}`}>{b.pkg}</code>
              </div>
              <div className={`text-xs font-mono mb-2 ${t('text-aquilia-400', 'text-aquilia-600')}`}>{b.url}</div>
              <p className={`text-xs mb-3 ${t('text-gray-400', 'text-gray-500')}`}>{b.note}</p>
              <Link to={`/docs/database/configs`} className={`inline-flex items-center gap-1 text-xs font-medium ${t('text-aquilia-400 hover:text-aquilia-300', 'text-aquilia-600 hover:text-aquilia-500')}`}>
                <DocTerm id={b.config === 'SqliteConfig' ? 'db.sqlite_config' : b.config === 'PostgresConfig' ? 'db.postgres_config' : b.config === 'MysqlConfig' ? 'db.mysql_config' : 'db.oracle_config'}>
                  {b.config}
                </DocTerm>
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* Raw queries */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}>Raw Queries</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300', 'text-gray-600')}`}>
          Use the <DocTerm id="db.aquilia_database">AquiliaDatabase</DocTerm> instance directly for raw SQL. All methods accept <code>?</code> placeholders.
        </p>
        <CodeBlock language="python">{`from aquilia.db import get_database

db = get_database()

# SELECT all rows
rows = await db.fetch_all("SELECT * FROM users WHERE active = ?", [True])

# SELECT one row
row = await db.fetch_one("SELECT * FROM users WHERE id = ?", [42])

# SELECT scalar value
count = await db.fetch_val("SELECT COUNT(*) FROM users")

# INSERT / UPDATE / DELETE
result = await db.execute("INSERT INTO logs (message) VALUES (?)", ["app started"])
print(result.lastrowid)

# Bulk insert
await db.execute_many(
    "INSERT INTO tags (name) VALUES (?)",
    [["python"], ["async"], ["orm"]],
)`}</CodeBlock>
      </section>

      {/* DI injection */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}>DI Injection</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300', 'text-gray-600')}`}>
          <DocTerm id="db.aquilia_database">AquiliaDatabase</DocTerm> is registered as a DI service. Inject it into services or controllers with <code>@inject</code>:
        </p>
        <CodeBlock language="python">{`from aquilia.db import AquiliaDatabase
from aquilia.di import inject

class UserService:
    @inject
    def __init__(self, db: AquiliaDatabase):
        self.db = db

    async def get_active_users(self):
        return await self.db.fetch_all("SELECT * FROM users WHERE active = ?", [True])`}</CodeBlock>
      </section>

      {/* Properties */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}>Properties</h2>
        <div className={`rounded-xl border overflow-hidden ${t('border-gray-700', 'border-gray-200')}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={t('bg-gray-800', 'bg-gray-50')}>
                <th className={`px-4 py-3 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Property</th>
                <th className={`px-4 py-3 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Type</th>
                <th className={`px-4 py-3 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${t('divide-gray-700','divide-gray-200')}`}>
              {[
                ['is_connected', 'bool', 'True when the adapter has an open connection.'],
                ['url', 'str', 'The connection URL (with password redacted).'],
                ['driver', 'str', '"sqlite", "postgresql", "mysql", or "oracle".'],
                ['dialect', 'str', 'SQL dialect name from the adapter.'],
                ['in_transaction', 'bool', 'True when inside an explicit transaction.'],
                ['capabilities', 'AdapterCapabilities', 'Backend feature flags (JSON, arrays, returning, etc.).'],
                ['adapter', 'DatabaseAdapter', 'Direct access to the raw backend adapter.'],
              ].map(([prop, type, desc]) => (
                <tr key={prop}>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-aquilia-400','text-aquilia-600')}`}>{prop}</td>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-gray-400','text-gray-500')}`}>{type}</td>
                  <td className={`px-4 py-3 text-xs ${t('text-gray-300','text-gray-600')}`}>{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Multi-database */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}>Multi-Database</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300', 'text-gray-600')}`}>
          Use <DocTerm id="db.configure_database">configure_database()</DocTerm> with named aliases to manage multiple connections:
        </p>
        <CodeBlock language="python">{`from aquilia.db import configure_database, get_database
from aquilia.db.configs import PostgresConfig, SqliteConfig

# Primary (Postgres)
configure_database(config=PostgresConfig(host="pg-host", name="app"), alias="default")

# Read replica
configure_database(config=PostgresConfig(host="pg-replica", name="app"), alias="replica")

# Analytics sidecar
configure_database(config=SqliteConfig(path="analytics.db"), alias="analytics")

# Retrieve by alias
db      = get_database()           # "default"
replica = get_database("replica")
stats   = get_database("analytics")`}</CodeBlock>
      </section>

      {/* Next page navigation */}
      <div className={`flex justify-end items-center pt-8 mt-8 border-t ${t('border-gray-700','border-gray-200')}`}>
        <Link to="/docs/database/engine" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          Engine API <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
      <NextSteps />
    </div>
  )
}