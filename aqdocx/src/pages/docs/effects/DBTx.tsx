import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Workflow } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function EffectsDBTx() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <Workflow className="w-4 h-4" />
          <span>EFFECTS / DBTX</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Database Transaction Effect
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">DBTx</code> effect manages database transactions. It enforces connection pool acquisition before handlers run, committing or rolling back based on the request's success.
        </p>
      </div>

      {/* Mode Syntax */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Token Mode Configuration</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Database transactions can be declared using mode parameters. Using Python's class indexing syntax, you can request read-only or read-write capabilities:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8 text-sm">
          <div className="border-l-2 border-aquilia-500/20 pl-6 py-2">
            <code className="text-white text-xs font-mono font-bold block mb-1">DBTx["read"]</code>
            <p className="text-gray-400 leading-relaxed">
              Acquires a connection from the pool but configures it in read-only mode (optimizing read performance and safety).
            </p>
          </div>
          <div className="border-l-2 border-aquilia-500/20 pl-6 py-2">
            <code className="text-white text-xs font-mono font-bold block mb-1">DBTx["write"]</code>
            <p className="text-gray-400 leading-relaxed">
              Acquires a connection and starts a transaction. Automatically executes a SQL <code className="text-white">COMMIT</code> on success or <code className="text-white">ROLLBACK</code> on error.
            </p>
          </div>
        </div>
      </section>

      {/* DBTxHandle API */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Using DBTxHandle</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          When acquired, the resource injected into the context is an instance of <DocTerm id="effects.DBTxHandle">DBTxHandle</DocTerm>. While it inherits from <code className="text-aquilia-400">dict</code> to keep metadata accessible, it wraps connection execution directly with async helper methods:
        </p>

        <div className="space-y-4 mb-8 text-sm text-gray-400">
          <div className="border-b border-white/5 pb-2">
            <code className="text-white text-xs font-mono">await handle.execute(sql, params=None)</code> — Runs a query (insert/update/delete) and returns the raw cursor.
          </div>
          <div className="border-b border-white/5 pb-2">
            <code className="text-white text-xs font-mono">await handle.fetch_all(sql, params=None)</code> — Runs a select query and returns a list of dictionaries representing matching rows.
          </div>
          <div className="border-b border-white/5 pb-2">
            <code className="text-white text-xs font-mono">await handle.fetch_val(sql, params=None)</code> — Executes a select query and returns the value of the first column in the first row.
          </div>
          <div className="pb-2">
            <code className="text-white text-xs font-mono">await handle.execute_many(sql, params_list)</code> — Optimizes batch operations by running parameter lists against a single query.
          </div>
        </div>
      </section>

      {/* Code Example */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Code Implementation</h2>
        <CodeBlock language="python" filename="dbtx_usage.py" highlightLines={[6, 9, 13]}>{`class UserController(Controller):
    effects = [DBTx["write"]]

    @Post("/")
    async def create_user(self, ctx):
        body = await ctx.json()
        
        # 1. Execute SQL inside transaction scope
        await ctx.effects.db.execute(
            "INSERT INTO users (username, email) VALUES (?, ?)",
            (body["username"], body["email"])
        )
        
        # 2. Fetch the newly inserted identifier
        user_id = await ctx.effects.db.fetch_val("SELECT last_insert_rowid()")
        return ctx.json({"id": user_id}, status=201)`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/effects/overview" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Overview
        </Link>
        <Link to="/docs/effects/cache" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400 transition-colors">
          Cache Effect <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}