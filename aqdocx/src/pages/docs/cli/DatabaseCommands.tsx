import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { GitCommit, Search, Terminal, Table as TableIcon, Play } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function CLIDatabaseCommands() {
    const { theme } = useTheme()
    const isDark = theme === 'dark'

    // Styles
    const sectionClass = "mb-16 scroll-mt-24"
    const h2Class = `text-2xl font-bold mb-6 flex items-center gap-3 ${isDark ? 'text-white' : 'text-gray-900'}`
    const pClass = `mb-4 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`
    const codeClass = "text-xs font-mono bg-black/5 dark:bg-white/10 px-1.5 py-0.5 rounded text-aquilia-600 dark:text-aquilia-400"

    const Table = ({ children }: { children: React.ReactNode }) => (
        <div className={`overflow-hidden border rounded-lg mb-6 ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
            <table className="w-full text-sm text-left">
                <thead className={`text-xs uppercase ${isDark ? 'bg-white/5 text-gray-400' : 'bg-gray-50 text-gray-500'}`}>
                    <tr>
                        <th className="px-4 py-3 font-medium">Option</th>
                        <th className="px-4 py-3 font-medium">Description</th>
                        <th className="px-4 py-3 font-medium w-32">Default</th>
                    </tr>
                </thead>
                <tbody className={`divide-y ${isDark ? 'divide-white/10' : 'divide-gray-200'}`}>
                    {children}
                </tbody>
            </table>
        </div>
    )

    const Row = ({ opt, desc, def }: { opt: string, desc: string, def?: string }) => (
        <tr className={isDark ? 'hover:bg-white/5' : 'hover:bg-gray-50'}>
            <td className="px-4 py-3 font-mono text-aquilia-500">{opt}</td>
            <td className={`px-4 py-3 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>{desc}</td>
            <td className={`px-4 py-3 font-mono text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>{def || '-'}</td>
        </tr>
    )

    return (
        <div className="max-w-4xl mx-auto pb-20">
            {/* Header */}
            <div className="mb-12 border-b border-gray-200 dark:border-white/10 pb-8">
                <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
                    <Terminal className="w-4 h-4" />
                    CLI / Database
                </div>
                <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
                  <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
                    Database Commands
                    <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
                  </span>
                </h1>
                <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                    Comprehensive toolset for schema management, migrations, introspection, and database interaction. The <code className={codeClass}>aq db</code> command group provides 8 subcommands covering the full database lifecycle.
                </p>
            </div>

            {/* Sub-command Overview */}
            <section className={sectionClass}>
                <h2 className={h2Class}><Terminal className="w-6 h-6 text-aquilia-500" /> Sub-Commands</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {[
                    { cmd: 'aq db makemigrations', desc: 'Generate migration files from Model definitions with DSL or raw SQL' },
                    { cmd: 'aq db migrate', desc: 'Apply pending migrations to the database' },
                    { cmd: 'aq db showmigrations', desc: 'List all migrations and their applied/pending status' },
                    { cmd: 'aq db sqlmigrate', desc: 'Print the SQL for a specific migration file' },
                    { cmd: 'aq db dump', desc: 'Export schema as SQL DDL or annotated Python' },
                    { cmd: 'aq db inspectdb', desc: 'Introspect database and generate Model classes' },
                    { cmd: 'aq db shell', desc: 'Launch interactive REPL with models and DB pre-loaded' },
                    { cmd: 'aq db status', desc: 'Show database tables, row counts, and column info' },
                  ].map((item, i) => (
                    <div key={i} className={`p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`}>
                      <code className={`font-bold text-sm ${isDark ? 'text-aquilia-400' : 'text-aquilia-600'}`}>{item.cmd}</code>
                      <p className={`text-xs mt-1 ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>{item.desc}</p>
                    </div>
                  ))}
                </div>
            </section>

            {/* makemigrations */}
            <section id="makemigrations" className={sectionClass}>
                <h2 className={h2Class}><GitCommit className="w-6 h-6 text-purple-500" /> aq db makemigrations</h2>
                <p className={pClass}>
                    Generates new migration files by detecting changes in your <code className={codeClass}>Model</code> definitions. Discovers models from <code className={codeClass}>modules/*/models/</code>, <code className={codeClass}>modules/*/models.py</code>, and <code className={codeClass}>models/</code> at workspace root. By default uses the DSL system with schema snapshot diffing and rename detection. Pass <code className={codeClass}>--no-dsl</code> to fall back to legacy raw-SQL generation.
                </p>
                <CodeBlock language="bash" filename="Terminal">
                    aq db makemigrations [OPTIONS]
                </CodeBlock>
                <Table>
                    <Row opt="--app" desc="Limit to specific app/module name" />
                    <Row opt="--migrations-dir" desc="Directory for migration files" def="migrations" />
                    <Row opt="--dsl / --no-dsl" desc="Use DSL migration system (snapshot diffing) vs legacy raw SQL" def="--dsl" />
                </Table>
                <CodeBlock language="bash" filename="Terminal">{`# Generate DSL migration for all models
aq db makemigrations

# Generate for specific module only
aq db makemigrations --app products

# Use legacy raw-SQL migration format
aq db makemigrations --no-dsl

# Custom migrations directory
aq db makemigrations --migrations-dir db/migrations`}</CodeBlock>
            </section>

            {/* migrate */}
            <section id="migrate" className={sectionClass}>
                <h2 className={h2Class}><GitCommit className="w-6 h-6 text-purple-500" /> aq db migrate</h2>
                <p className={pClass}>
                    Applies pending migrations to the database. Auto-detects DSL and legacy migration formats. Supports targeting a specific migration for rollback, faking migrations, and dry-run planning.
                </p>
                <CodeBlock language="bash" filename="Terminal">
                    aq db migrate [OPTIONS]
                </CodeBlock>
                <Table>
                    <Row opt="--migrations-dir" desc="Directory containing migration files" def="migrations" />
                    <Row opt="--database-url" desc="Override database connection URL" def="sqlite:///db.sqlite3" />
                    <Row opt="--database" desc="Database alias for multi-db setups" def="default" />
                    <Row opt="--target" desc="Migrate/rollback to a specific revision" />
                    <Row opt="--fake" desc="Mark migrations as applied without executing SQL" def="false" />
                    <Row opt="--plan" desc="Show execution plan (dry-run) without applying" def="false" />
                </Table>
                <CodeBlock language="bash" filename="Terminal">{`# Apply all pending migrations
aq db migrate

# Preview SQL without applying
aq db migrate --plan

# Rollback to specific revision
aq db migrate --target 0002_add_email

# Mark as applied without running SQL
aq db migrate --fake

# Use specific database URL
aq db migrate --database-url postgresql://user:pass@localhost:5432/mydb`}</CodeBlock>
            </section>

            {/* showmigrations */}
            <section id="showmigrations" className={sectionClass}>
                <h2 className={h2Class}><GitCommit className="w-6 h-6 text-purple-500" /> aq db showmigrations</h2>
                <p className={pClass}>
                    Lists all migrations and their applied status. Shows <code className={codeClass}>[X]</code> for applied and <code className={codeClass}>[ ]</code> for pending. Connects to the real database to check the <code className={codeClass}>aquilia_migrations</code> tracking table.
                </p>
                <CodeBlock language="bash" filename="Terminal">
                    aq db showmigrations [OPTIONS]
                </CodeBlock>
                <Table>
                    <Row opt="--migrations-dir" desc="Directory containing migration files" def="migrations" />
                    <Row opt="--database-url" desc="Override database connection URL" def="sqlite:///db.sqlite3" />
                    <Row opt="--database" desc="Database alias for multi-db setups" def="default" />
                </Table>
            </section>

            {/* sqlmigrate */}
            <section id="sqlmigrate" className={sectionClass}>
                <h2 className={h2Class}><GitCommit className="w-6 h-6 text-purple-500" /> aq db sqlmigrate</h2>
                <p className={pClass}>
                    Prints the SQL for a specific migration. For DSL migrations, compiles operations to SQL for the target dialect. For legacy migrations, extracts SQL via regex or displays raw source. Supports partial name matching.
                </p>
                <CodeBlock language="bash" filename="Terminal">
                    aq db sqlmigrate MIGRATION_NAME [OPTIONS]
                </CodeBlock>
                <Table>
                    <Row opt="MIGRATION_NAME" desc="Migration file name without .py (positional)" />
                    <Row opt="--migrations-dir" desc="Directory containing migration files" def="migrations" />
                    <Row opt="--database" desc="Database alias (reserved for multi-db)" def="default" />
                </Table>
                <CodeBlock language="bash" filename="Terminal">{`# Show SQL for a migration
aq db sqlmigrate 0003_add_products_table

# Partial name match supported
aq db sqlmigrate add_products`}</CodeBlock>
            </section>

            {/* inspectdb */}
            <section id="inspection" className={sectionClass}>
                <h2 className={h2Class}><Search className="w-6 h-6 text-blue-500" /> aq db inspectdb</h2>
                <p className={pClass}>
                    Introspects an existing database and generates Python <code className={codeClass}>Model</code> class definitions. Maps SQL column types to Aquilia field types (CharField, IntegerField, etc.) automatically.
                </p>
                <CodeBlock language="bash" filename="Terminal">
                    aq db inspectdb [OPTIONS]
                </CodeBlock>
                <Table>
                    <Row opt="--database-url" desc="Database connection URL" def="sqlite:///db.sqlite3" />
                    <Row opt="--table, -t" desc="Limit to specific tables (repeatable)" />
                    <Row opt="--output, -o" desc="Write to file instead of stdout" />
                </Table>
                <CodeBlock language="bash" filename="Terminal">{`# Introspect all tables
aq db inspectdb

# Introspect specific tables
aq db inspectdb --table users --table orders

# Write to file
aq db inspectdb --output modules/products/models.py

# Use PostgreSQL
aq db inspectdb --database-url postgresql://localhost:5432/mydb`}</CodeBlock>
            </section>

            {/* dump */}
            <section id="dump" className={sectionClass}>
                <h2 className={h2Class}><Search className="w-6 h-6 text-blue-500" /> aq db dump</h2>
                <p className={pClass}>
                    Exports schema from discovered Model definitions. Generates DDL (CREATE TABLE, indexes, M2M tables) in raw SQL or annotated Python format.
                </p>
                <CodeBlock language="bash" filename="Terminal">
                    aq db dump [OPTIONS]
                </CodeBlock>
                <Table>
                    <Row opt="--emit" desc="Output format: sql (raw DDL) or python (annotated schema)" def="python" />
                    <Row opt="--output-dir" desc="Directory to write dump files" />
                </Table>
                <CodeBlock language="bash" filename="Terminal">{`# Dump as annotated Python
aq db dump

# Dump as raw SQL DDL
aq db dump --emit sql

# Write to directory
aq db dump --emit sql --output-dir schema/`}</CodeBlock>
            </section>

            {/* Shell */}
            <section id="shell" className={sectionClass}>
                <h2 className={h2Class}><Play className="w-6 h-6 text-green-500" /> aq db shell</h2>
                <p className={pClass}>
                    Opens an interactive Python REPL with database connection established and all discovered Model subclasses pre-imported. Also provides <code className={codeClass}>Q</code> query builder, <code className={codeClass}>ModelRegistry</code>, <code className={codeClass}>db</code>, <code className={codeClass}>loop</code>, and <code className={codeClass}>asyncio</code> in the namespace.
                </p>
                <CodeBlock language="bash" filename="Terminal">
                    aq db shell [OPTIONS]
                </CodeBlock>
                <Table>
                    <Row opt="--database-url" desc="Override database connection URL" def="sqlite:///db.sqlite3" />
                </Table>
                <CodeBlock language="python" filename="Shell Session">
                    {`Models loaded: User, Product, Order
Database: sqlite:///db.sqlite3
Tip: Use loop.run_until_complete(Product.get(pk=1)) for async ops

>>> loop.run_until_complete(User.filter(is_active=True).count())
150
>>> # Direct SQL access
>>> loop.run_until_complete(db.fetch_one("SELECT COUNT(*) as cnt FROM users"))`}
                </CodeBlock>
            </section>

            {/* Status */}
            <section id="status" className={sectionClass}>
                <h2 className={h2Class}><TableIcon className="w-6 h-6 text-orange-500" /> aq db status</h2>
                <p className={pClass}>
                    Show database status — lists all tables with row counts and column counts, plus aggregate totals.
                </p>
                <CodeBlock language="bash" filename="Terminal">
                    aq db status [OPTIONS]
                </CodeBlock>
                <Table>
                    <Row opt="--database-url" desc="Override database connection URL" def="sqlite:///db.sqlite3" />
                </Table>
                <CodeBlock language="text" filename="Example Output">{`  users                              42 rows  (5 columns)
  products                          128 rows  (8 columns)
  orders                             67 rows  (6 columns)
  aquilia_migrations                  3 rows  (3 columns)

  Total: 4 table(s), 240 row(s)`}</CodeBlock>
            </section>

            {/* Model Discovery */}
            <section className={sectionClass}>
                <h2 className={h2Class}>Model Discovery</h2>
                <p className={pClass}>
                    All <code className={codeClass}>aq db</code> commands automatically discover Model subclasses from these locations (in order):
                </p>
                <ul className={`list-disc pl-6 mb-4 space-y-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                    <li><code className={codeClass}>modules/*/models/__init__.py</code> — model packages with entry point</li>
                    <li><code className={codeClass}>modules/*/models/*.py</code> — additional model files in packages</li>
                    <li><code className={codeClass}>modules/*/models.py</code> — single-file model modules</li>
                    <li><code className={codeClass}>models/</code> — root-level models directory</li>
                </ul>
                <p className={pClass}>
                    Discovery uses package-aware imports with proper <code className={codeClass}>sys.modules</code> bootstrapping so relative imports resolve correctly.
                </p>
            </section>
        
          <NextSteps
            items={[
              { text: 'Core Commands', link: '/docs/cli/core' },
              { text: 'MLOps Commands', link: '/docs/cli/mlops' },
              { text: 'Artifact Commands', link: '/docs/cli/artifacts' },
              { text: 'Blueprint Docs', link: '/docs/blueprints' },
            ]}
          />
    </div>
    )
}