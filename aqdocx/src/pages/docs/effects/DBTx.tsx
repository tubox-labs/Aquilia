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
          <span>EFFECTS / DATABASE TRANSACTION</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Database Transaction Effect
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <DocTerm id="effects.DBTx">DBTx</DocTerm> effect provides transactional database connections from the application pool. Implemented by the <DocTerm id="effects.DBTxProvider">DBTxProvider</DocTerm>, it automatically commits on request completion or rolls back when faults occur.
        </p>
      </div>

      {/* Philosophy */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">How Transactions are Bound</h2>
        <div className={`space-y-6 font-light leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          <p>
            When a handler requests database access, pulling raw connections manually can lead to leaked sessions or uncommitted transaction blocks. The <DocTerm id="effects.DBTx">DBTx</DocTerm> effect treats transactions as request-scoped resources. It wraps request processing with an atomic database scope, enforcing database safety at the framework boundaries.
          </p>
        </div>
      </section>

      {/* Modes */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Token Configuration &amp; Modes</h2>
        <p className={`mb-6 font-light ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          You can declare your database requirements in two modes using Python's class indexing syntax:
        </p>

        <div className="space-y-8 pl-4 border-l border-aquilia-500/20 mb-8">
          <div>
            <CodeBlock language="python" compact showLineNumbers={false}>{`DBTx["read"]`}</CodeBlock>
            <p className={`font-light text-sm mt-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Acquires a database connection configured as read-only. This optimizes SELECT performance, permits routing queries to read replicas, and raises errors if writing is attempted.
            </p>
          </div>
          <div>
            <CodeBlock language="python" compact showLineNumbers={false}>{`DBTx["write"]`}</CodeBlock>
            <p className={`font-light text-sm mt-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Acquires a database connection and immediately initiates a transaction block. Commits the transaction when the handler finishes successfully, or issues a SQL ROLLBACK if any exception escapes the handler.
            </p>
          </div>
        </div>
      </section>

      {/* DBTxHandle API */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">The DBTxHandle Interface</h2>
        <p className={`mb-6 font-light ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          When acquired, the resource injected into the context is an instance of <DocTerm id="effects.DBTxHandle">DBTxHandle</DocTerm>. It inherits from <code className="text-aquilia-400">dict</code> to keep metadata accessible, but exposes async helper wrappers to execute SQL within the active transaction:
        </p>

        <div className="space-y-8 pl-4 border-l border-blue-500/20 text-sm text-gray-400">
          <div>
            <CodeBlock language="python" compact showLineNumbers={false}>{`await handle.execute(sql: str, params: Sequence | None = None) -> AsyncCursor`}</CodeBlock>
            <p className="mt-2 font-light">Executes a SQL statement (e.g. INSERT, UPDATE, DELETE) binding parameters to prevent SQL injection. Returns an active query cursor.</p>
          </div>
          <div>
            <CodeBlock language="python" compact showLineNumbers={false}>{`await handle.fetch_all(sql: str, params: Sequence | None = None) -> list[dict[str, Any]]`}</CodeBlock>
            <p className="mt-2 font-light">Executes a query and returns all result rows mapped as key-value dictionaries.</p>
          </div>
          <div>
            <CodeBlock language="python" compact showLineNumbers={false}>{`await handle.fetch_one(sql: str, params: Sequence | None = None) -> dict[str, Any] | None`}</CodeBlock>
            <p className="mt-2 font-light">Fetches a single row. Returns a dictionary or <code className="text-aquilia-500">None</code> if no records match.</p>
          </div>
          <div>
            <CodeBlock language="python" compact showLineNumbers={false}>{`await handle.fetch_val(sql: str, params: Sequence | None = None) -> Any`}</CodeBlock>
            <p className="mt-2 font-light">Convenience method that fetches the first column of the first row (ideal for scalar queries like COUNT or returning primary keys).</p>
          </div>
          <div>
            <CodeBlock language="python" compact showLineNumbers={false}>{`await handle.execute_many(sql: str, params_list: Sequence[Sequence]) -> None`}</CodeBlock>
            <p className="mt-2 font-light">Executes the SQL statement iteratively over a list of parameter tuples in a highly optimized batch database operation.</p>
          </div>
        </div>

        {/* Properties */}
        <h3 className="text-md font-mono text-aquilia-300 mt-10 mb-4">Exposed Properties</h3>
        <div className="space-y-4 pl-4 border-l border-purple-500/20 text-sm text-gray-400">
          <div>
            <code className="text-white text-xs font-mono">handle.connection</code> — Returns the underlying raw DB engine connection or pool instance.
          </div>
          <div>
            <code className="text-white text-xs font-mono">handle.mode</code> — Returns the transaction acquisition mode: <code className="text-aquilia-400">"read"</code> or <code className="text-aquilia-400">"write"</code>.
          </div>
          <div>
            <code className="text-white text-xs font-mono">handle.transaction</code> — Points to the active transaction context instance.
          </div>
          <div>
            <code className="text-white text-xs font-mono">handle.acquired_at</code> — The monotonic timestamp when the connection was leased.
          </div>
        </div>
      </section>

      {/* Code Examples */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Practical Code Examples</h2>
        
        {/* Example 1: Write Controller with Rollback */}
        <h3 className="text-md font-mono text-aquilia-300 mb-4">1. Write Operation with Auto-Rollback (E-Commerce Checkout)</h3>
        <p className={`mb-6 font-light ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          If any exception is raised during execution, the transaction is rolled back automatically. The example below shows an enterprise e-commerce checkout handler checking inventory, deducting balances, recording audit ledgers, and allocating reward points:
        </p>

        <CodeBlock language="python" filename="controllers/checkout.py" highlightLines={[12, 19, 29]}>{`from aquilia.controller import Controller, POST, RequestCtx
from aquilia.flow import requires
from aquilia.effects import DBTx
from aquilia.faults.domains import OutOfStockFault, PaymentFailedFault

class CheckoutController(Controller):
    @POST("/checkout")
    @requires(DBTx["write"])
    async def process_checkout(self, ctx: RequestCtx) -> dict:
        body = await ctx.json()
        db = ctx.get_effect("DBTx")  # DBTxHandle instance
        
        # 1. Lock and inspect product stock
        stock = await db.fetch_val(
            "SELECT stock FROM products WHERE id = ? FOR UPDATE", 
            (body["product_id"],)
        )
        if stock is None or stock < body["quantity"]:
            # Raises error, transaction automatically aborts/rolls back
            raise OutOfStockFault(product_id=body["product_id"])
            
        # 2. Allocate inventory
        await db.execute(
            "UPDATE products SET stock = stock - ? WHERE id = ?",
            (body["quantity"], body["product_id"])
        )
        
        # 3. Create invoice ledger entry
        await db.execute(
            "INSERT INTO ledgers (user_id, amount, status) VALUES (?, ?, ?)",
            (ctx.user.id, body["price"] * body["quantity"], "PENDING")
        )
        
        # 4. Award loyalty reward points
        points_earned = int((body["price"] * body["quantity"]) * 0.10)
        await db.execute(
            "UPDATE user_rewards SET points = points + ? WHERE user_id = ?",
            (points_earned, ctx.user.id)
        )
        
        return {"status": "checkout_processed", "points_awarded": points_earned}`}</CodeBlock>

        {/* Example 2: Read Only replica optimization */}
        <h3 className="text-md font-mono text-aquilia-300 mt-10 mb-4">2. Read-Only Retrieval Optimization (SaaS Tenant Analytics)</h3>
        <p className={`mb-6 font-light ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Using the read-only mode avoids starting transactional locks on the database and signals to the loader that the connection can safely target replica instances:
        </p>

        <CodeBlock language="python" filename="controllers/analytics.py" highlightLines={[8, 12]}>{`from aquilia.controller import Controller, GET, RequestCtx
from aquilia.flow import requires
from aquilia.effects import DBTx

class TenantAnalyticsController(Controller):
    @GET("/analytics/mrr")
    @requires(DBTx["read"])
    async def get_mrr_metrics(self, ctx: RequestCtx) -> dict:
        db = ctx.get_effect("DBTx")
        
        # Querying replica server for read-heavy aggregation reports
        mrr = await db.fetch_val(
            "SELECT SUM(amount) FROM subscriptions WHERE status = ? AND tenant_id = ?",
            ("active", ctx.tenant.id)
        )
        
        churn_rate = await db.fetch_val(
            "SELECT COUNT(*) * 100.0 / (SELECT COUNT(*) FROM subscriptions WHERE tenant_id = ?) "
            "FROM subscriptions WHERE status = ? AND tenant_id = ?",
            (ctx.tenant.id, "cancelled", ctx.tenant.id)
        )
        
        return {
            "mrr": float(mrr or 0.0),
            "churn_rate": float(churn_rate or 0.0)
        }`}</CodeBlock>
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