import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Database } from 'lucide-react'

export function CLIDatabaseCommands() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const sectionClass = "mb-16 scroll-mt-24"
  const h2Class = `text-2xl font-bold mb-6 flex items-center gap-3 ${isDark ? 'text-white' : 'text-gray-900'}`
  const h3Class = `text-lg font-semibold mt-8 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`
  const pClass = `mb-4 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`

  return (
    <div className="max-w-4xl mx-auto pb-20">
      {/* Header */}
      <div className="mb-12 border-b border-gray-200 dark:border-white/10 pb-8">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Database className="w-4 h-4" />
          CLI / Database
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Database Commands
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500 font-mono font-bold">aq db</code> command group manages migrations, introspects tables, dumps schemas, and runs database shells.
        </p>
      </div>

      {/* aq db makemigrations */}
      <section id="makemigrations" className={sectionClass}>
        <h2 className={h2Class}><DocTerm id="cli.db_makemigrations">aq db makemigrations</DocTerm></h2>
        <p className={pClass}>
          Analyzes your model classes in modules and diffs them against migration history to generate a new migration file. Diffs are compiled using the Aquilia DSL.
        </p>
        <CodeBlock language="bash" filename="Terminal">{`# Generate migrations for all modules
aq db makemigrations

# Generate migrations only for the users module
aq db makemigrations --app=users

# Fall back to legacy SQL migrations instead of DSL
aq db makemigrations --no-dsl`}</CodeBlock>

        <h3 className={h3Class}>Options</h3>
        <div className="overflow-x-auto py-2 mb-6">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-white/10 text-gray-500 dark:text-gray-400 text-left">
                <th className="px-4 py-3 font-semibold">Option</th>
                <th className="px-4 py-3 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5 text-gray-300' : 'divide-gray-150 text-gray-700'}`}>
              {[
                ['--app', 'Limit migration discovery to the named module.'],
                ['--migrations-dir', 'Destination directory (defaults to migrations/).'],
                ['--dsl / --no-dsl', 'Toggle DSL-driven migration snapshotting (defaults to --dsl).']
              ].map(([opt, desc], i) => (
                <tr key={i} className="hover:bg-aquilia-500/5 transition-colors">
                  <td className="px-4 py-2 font-mono text-xs text-aquilia-500 font-semibold">{opt}</td>
                  <td className="px-4 py-2 text-xs">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* aq db migrate */}
      <section id="migrate" className={sectionClass}>
        <h2 className={h2Class}><DocTerm id="cli.db_migrate">aq db migrate</DocTerm></h2>
        <p className={pClass}>
          Executes pending migration files, applying changes to database schemas safely.
        </p>
        <CodeBlock language="bash" filename="Terminal">{`# Apply all pending migrations
aq db migrate

# View execution plan without altering schemas
aq db migrate --plan

# Target a specific migration version (rolls back if version is in the past)
aq db migrate --target=0004_add_profile_indexing`}</CodeBlock>

        <h3 className={h3Class}>Options</h3>
        <div className="overflow-x-auto py-2 mb-6">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-white/10 text-gray-500 dark:text-gray-400 text-left">
                <th className="px-4 py-3 font-semibold">Option</th>
                <th className="px-4 py-3 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5 text-gray-300' : 'divide-gray-150 text-gray-700'}`}>
              {[
                ['--target', 'Roll forward or rollback to the designated migration target name.'],
                ['--plan', 'Logs the sequence of migrations to be executed without applying them.'],
                ['--fake', 'Registers migrations as applied in the history table without executing database operations.'],
                ['--database-url', 'Overrides the database URL defined in your configuration.']
              ].map(([opt, desc], i) => (
                <tr key={i} className="hover:bg-aquilia-500/5 transition-colors">
                  <td className="px-4 py-2 font-mono text-xs text-aquilia-500 font-semibold">{opt}</td>
                  <td className="px-4 py-2 text-xs">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* aq db showmigrations */}
      <section id="showmigrations" className={sectionClass}>
        <h2 className={h2Class}>aq db showmigrations</h2>
        <p className={pClass}>
          Displays all detected migration files, listing them sequentially with a checked or unchecked status indicator (e.g. <code className="text-aquilia-500">[X]</code> or <code className="text-aquilia-500">[ ]</code>) depending on whether they have been applied.
        </p>
        <CodeBlock language="bash" filename="Terminal">aq db showmigrations</CodeBlock>
      </section>

      {/* aq db sqlmigrate */}
      <section id="sqlmigrate" className={sectionClass}>
        <h2 className={h2Class}>aq db sqlmigrate</h2>
        <p className={pClass}>
          Prints the raw SQL DDL queries compiled for a specific migration target name. Extremely helpful for review processes or manual SQL schemas approval.
        </p>
        <CodeBlock language="bash" filename="Terminal">{`# Print SQL statements for migration 0002
aq db sqlmigrate 0002_create_user_table`}</CodeBlock>
      </section>

      {/* aq db dump */}
      <section id="dump" className={sectionClass}>
        <h2 className={h2Class}>aq db dump</h2>
        <p className={pClass}>
          Dumps model schemas into structured formats.
        </p>
        <CodeBlock language="bash" filename="Terminal">{`# Dump DDL schema output as SQL
aq db dump --emit=sql --output-dir=deploy/schema/`}</CodeBlock>
      </section>

      {/* aq db inspectdb */}
      <section id="inspectdb" className={sectionClass}>
        <h2 className={h2Class}>aq db inspectdb</h2>
        <p className={pClass}>
          Introspects an existing database and prints auto-generated Python model code representing the tables. Helps with migrating legacy databases.
        </p>
        <CodeBlock language="bash" filename="Terminal">{`# Introspect legacy database tables
aq db inspectdb --database-url="postgresql://user:pass@localhost/legacy"`}</CodeBlock>
      </section>

      {/* aq db shell */}
      <section id="shell" className={sectionClass}>
        <h2 className={h2Class}>aq db shell</h2>
        <p className={pClass}>
          Launches an interactive, async Python REPL with the database connection and module model classes pre-loaded, facilitating quick queries.
        </p>
        <CodeBlock language="bash" filename="Terminal">aq db shell</CodeBlock>
      </section>

      {/* aq db status */}
      <section id="status" className={sectionClass}>
        <h2 className={h2Class}>aq db status</h2>
        <p className={pClass}>
          Displays statistics on database connection states, including tables, columns, indexes, and row counts.
        </p>
        <CodeBlock language="bash" filename="Terminal">aq db status</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}