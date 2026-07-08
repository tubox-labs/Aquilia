import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function DatabaseConfigs() {
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
        <span className={t('text-gray-300','text-gray-600')}>Config Classes</span>
      </div>

      {/* Header */}
      <div className="mb-10">
        <h1 className={`text-4xl font-bold tracking-tighter mb-4 ${t('text-white','text-gray-900')}`}>
          <span className="gradient-text">Config Classes</span>
        </h1>
        <p className={`text-xl leading-relaxed ${t('text-gray-300','text-gray-600')}`}>
          Typed, IDE-friendly configuration dataclasses for each backend. No URL string typos — just Python with autocompletion.
        </p>
      </div>

      {/* DatabaseConfig base */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>DatabaseConfig (base)</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          All backend configs inherit from <code>DatabaseConfig</code>. Common pool, retry, and behavior settings.
        </p>
        <div className={`rounded-xl border overflow-hidden ${t('border-gray-700','border-gray-200')}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={t('bg-gray-800','bg-gray-50')}>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Field</th>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Default</th>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${t('divide-gray-700','divide-gray-200')}`}>
              {[
                ['pool_size', '5', 'Target connection pool size.'],
                ['pool_min_size', '2', 'Minimum connections to keep alive.'],
                ['pool_max_size', '10', 'Maximum open connections.'],
                ['echo', 'False', 'Log every SQL statement to logger.'],
                ['auto_connect', 'True', 'Connect automatically on first use.'],
                ['auto_create', 'True', 'Auto-create database file if missing (SQLite).'],
                ['auto_migrate', 'False', 'Apply pending migrations on startup.'],
                ['migrations_dir', '"migrations"', 'Relative path to migrations folder.'],
                ['connect_retries', '3', 'Attempts before raising DatabaseConnectionFault.'],
                ['connect_retry_delay', '0.5', 'Seconds between retry attempts.'],
                ['conn_max_age', '0', 'Max connection lifetime in seconds (0 = persistent).'],
                ['conn_health_checks', 'False', 'Ping connection before each use.'],
              ].map(([f,d,desc]) => (
                <tr key={f}>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-aquilia-400','text-aquilia-600')}`}>{f}</td>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-gray-400','text-gray-500')}`}>{d}</td>
                  <td className={`px-4 py-3 text-xs ${t('text-gray-300','text-gray-600')}`}>{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* SqliteConfig */}
      <section className="mb-12">
        <div className="flex items-center gap-3 mb-4">
          <h2 className={`text-2xl font-bold ${t('text-white','text-gray-900')}`}>
            <DocTerm id="db.sqlite_config">SqliteConfig</DocTerm>
          </h2>
          <code className={`text-xs px-2 py-0.5 rounded ${t('bg-white/5 text-gray-400','bg-gray-100 text-gray-500')}`}>built-in</code>
        </div>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          SQLite via Aquilia's native async SQLite driver. No extra packages required. WAL mode enabled by default for concurrent reads.
        </p>
        <CodeBlock language="python">{`from aquilia.db.configs import SqliteConfig

# File-based
cfg = SqliteConfig(path="data/app.db")

# In-memory (great for tests)
cfg = SqliteConfig(path=":memory:")

# Production settings
cfg = SqliteConfig(
    path="data/prod.db",
    journal_mode="WAL",        # WAL | DELETE | TRUNCATE | PERSIST | MEMORY | OFF
    foreign_keys=True,         # PRAGMA foreign_keys = ON
    busy_timeout=5000,         # PRAGMA busy_timeout = 5000 (ms)
    auto_migrate=True,
    conn_health_checks=True,
)

# From URL
cfg = SqliteConfig.from_url("sqlite:///data/app.db")`}</CodeBlock>

        <div className={`mt-4 rounded-xl border overflow-hidden ${t('border-gray-700','border-gray-200')}`}>
          <table className="w-full text-sm">
            <thead><tr className={t('bg-gray-800','bg-gray-50')}>
              <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Field</th>
              <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Default</th>
              <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Description</th>
            </tr></thead>
            <tbody className={`divide-y ${t('divide-gray-700','divide-gray-200')}`}>
              {[
                ['path', '"db.sqlite3"', 'File path or ":memory:".'],
                ['journal_mode', '"WAL"', 'SQLite journal mode. WAL recommended for production.'],
                ['foreign_keys', 'True', 'PRAGMA foreign_keys enforcement.'],
                ['busy_timeout', '5000', 'PRAGMA busy_timeout in milliseconds.'],
              ].map(([f,d,desc]) => (
                <tr key={f}>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-aquilia-400','text-aquilia-600')}`}>{f}</td>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-gray-400','text-gray-500')}`}>{d}</td>
                  <td className={`px-4 py-3 text-xs ${t('text-gray-300','text-gray-600')}`}>{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* PostgresConfig */}
      <section className="mb-12">
        <div className="flex items-center gap-3 mb-4">
          <h2 className={`text-2xl font-bold ${t('text-white','text-gray-900')}`}>
            <DocTerm id="db.postgres_config">PostgresConfig</DocTerm>
          </h2>
          <code className={`text-xs px-2 py-0.5 rounded ${t('bg-white/5 text-gray-400','bg-gray-100 text-gray-500')}`}>pip install asyncpg</code>
        </div>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          PostgreSQL via <code>asyncpg</code>. Supports SSL, connection pool min/max, and schema selection. Both <code>name</code> and <code>database</code> are accepted as the database name.
        </p>
        <CodeBlock language="python">{`from aquilia.db.configs import PostgresConfig

# Minimal
cfg = PostgresConfig(
    host="localhost",
    database="mydb",   # or: name="mydb"
    user="admin",
    password="secret",
)

# Production with SSL + pooling
cfg = PostgresConfig(
    host="db.example.com",
    port=5432,
    database="prod_db",
    user="app_user",
    password="s3cr3t",
    sslmode="require",          # disable | allow | prefer | require | verify-full
    schema="public",
    pool_size=20,
    pool_min_size=5,
    pool_max_size=50,
    conn_health_checks=True,
    conn_max_age=600,
)

# From URL
cfg = PostgresConfig.from_url("postgresql://admin:secret@localhost:5432/mydb", pool_size=10)`}</CodeBlock>

        <div className={`mt-4 rounded-xl border overflow-hidden ${t('border-gray-700','border-gray-200')}`}>
          <table className="w-full text-sm">
            <thead><tr className={t('bg-gray-800','bg-gray-50')}>
              <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Field</th>
              <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Default</th>
              <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Description</th>
            </tr></thead>
            <tbody className={`divide-y ${t('divide-gray-700','divide-gray-200')}`}>
              {[
                ['host', '"localhost"', 'Database server hostname.'],
                ['port', '5432', 'Server port.'],
                ['name / database', '""', 'Database name (both aliases work; database resolves to name).'],
                ['user', '""', 'Database user.'],
                ['password', '""', 'Database password.'],
                ['schema', '"public"', 'Default schema.'],
                ['sslmode', '"prefer"', 'SSL mode: disable, allow, prefer, require, verify-ca, verify-full.'],
              ].map(([f,d,desc]) => (
                <tr key={f}>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-aquilia-400','text-aquilia-600')}`}>{f}</td>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-gray-400','text-gray-500')}`}>{d}</td>
                  <td className={`px-4 py-3 text-xs ${t('text-gray-300','text-gray-600')}`}>{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* MysqlConfig */}
      <section className="mb-12">
        <div className="flex items-center gap-3 mb-4">
          <h2 className={`text-2xl font-bold ${t('text-white','text-gray-900')}`}>
            <DocTerm id="db.mysql_config">MysqlConfig</DocTerm>
          </h2>
          <code className={`text-xs px-2 py-0.5 rounded ${t('bg-white/5 text-gray-400','bg-gray-100 text-gray-500')}`}>pip install aiomysql</code>
        </div>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          MySQL and MariaDB via <code>aiomysql</code>. Defaults to <code>utf8mb4</code> charset with <code>utf8mb4_unicode_ci</code> collation.
        </p>
        <CodeBlock language="python">{`from aquilia.db.configs import MysqlConfig

cfg = MysqlConfig(
    host="mysql.example.com",
    database="prod_db",    # or: name="prod_db"
    user="app_user",
    password="s3cr3t",
    charset="utf8mb4",
    collation="utf8mb4_unicode_ci",
    pool_size=15,
)

cfg = MysqlConfig.from_url("mysql://root:pass@localhost:3306/mydb")`}</CodeBlock>

        <div className={`mt-4 rounded-xl border overflow-hidden ${t('border-gray-700','border-gray-200')}`}>
          <table className="w-full text-sm">
            <thead><tr className={t('bg-gray-800','bg-gray-50')}>
              <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Field</th>
              <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Default</th>
              <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Description</th>
            </tr></thead>
            <tbody className={`divide-y ${t('divide-gray-700','divide-gray-200')}`}>
              {[
                ['host', '"localhost"', 'Database server hostname.'],
                ['port', '3306', 'Server port.'],
                ['name / database', '""', 'Database name.'],
                ['user', '""', 'Database user.'],
                ['password', '""', 'Database password.'],
                ['charset', '"utf8mb4"', 'Character set.'],
                ['collation', '"utf8mb4_unicode_ci"', 'Collation setting.'],
              ].map(([f,d,desc]) => (
                <tr key={f}>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-aquilia-400','text-aquilia-600')}`}>{f}</td>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-gray-400','text-gray-500')}`}>{d}</td>
                  <td className={`px-4 py-3 text-xs ${t('text-gray-300','text-gray-600')}`}>{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* OracleConfig */}
      <section className="mb-12">
        <div className="flex items-center gap-3 mb-4">
          <h2 className={`text-2xl font-bold ${t('text-white','text-gray-900')}`}>
            <DocTerm id="db.oracle_config">OracleConfig</DocTerm>
          </h2>
          <code className={`text-xs px-2 py-0.5 rounded ${t('bg-white/5 text-gray-400','bg-gray-100 text-gray-500')}`}>pip install oracledb</code>
        </div>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Oracle via <code>python-oracledb</code>. Thin mode by default — no Oracle Client installation required. Use <code>service_name</code> or <code>sid</code>.
        </p>
        <CodeBlock language="python">{`from aquilia.db.configs import OracleConfig

# Service name (recommended)
cfg = OracleConfig(
    host="oracle.example.com",
    database="PROD_SERVICE",   # alias for service_name
    user="app_user",
    password="tiger",
    pool_size=20,
)

# SID-based
cfg = OracleConfig(
    host="oracle.example.com",
    sid="ORCL",
    user="scott",
    password="tiger",
)

# Thick mode (requires Oracle Client)
cfg = OracleConfig(
    host="oracle.example.com",
    database="PROD",
    user="scott",
    password="tiger",
    thick_mode=True,
    encoding="UTF-8",
)

cfg = OracleConfig.from_url("oracle://scott:tiger@oracle.example.com:1521/PROD")`}</CodeBlock>
      </section>

      {/* Using in Integration */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Using with Integration</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Pass any config class to <code>Integration.database(config=...)</code> in your workspace:
        </p>
        <CodeBlock language="python">{`from aquilia.workspace import Workspace, Module
from aquilia.integrations import Integration
from aquilia.db.configs import PostgresConfig, SqliteConfig

workspace = (
    Workspace("my-api")
    .add_module(Module("users"))
    .integrate(Integration.database(
        config=PostgresConfig(
            host="db.example.com",
            database="prod_db",
            user="admin",
            password="secret",
            pool_size=20,
            sslmode="require",
        )
    ))
    .build()
)

# Test workspace with in-memory SQLite
test_workspace = (
    Workspace("my-api-test")
    .add_module(Module("users"))
    .integrate(Integration.database(
        config=SqliteConfig(path=":memory:", auto_migrate=True)
    ))
    .build()
)`}</CodeBlock>
      </section>

      {/* from_url classmethod */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>from_url() Classmethod</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Every config class provides a <code>from_url()</code> classmethod. <code>DatabaseConfig.from_url()</code> auto-detects the backend from the URL scheme.
        </p>
        <CodeBlock language="python">{`from aquilia.db.configs import DatabaseConfig

# Auto-detect (returns the correct subclass)
cfg = DatabaseConfig.from_url("postgresql://admin:secret@localhost/mydb")
# → PostgresConfig instance

cfg = DatabaseConfig.from_url("sqlite:///data/app.db")
# → SqliteConfig instance

# Override specific fields
cfg = DatabaseConfig.from_url("postgresql://admin:secret@localhost/mydb", pool_size=20)`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex justify-between items-center pt-8 mt-8 border-t ${t('border-gray-700','border-gray-200')}`}>
        <Link to="/docs/database/engine" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          <ArrowLeft className="w-4 h-4" /> AquiliaDatabase
        </Link>
        <Link to="/docs/database/sqlite" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          SQLite Backend <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
      <NextSteps />
    </div>
  )
}
