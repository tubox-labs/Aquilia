import { useTheme } from '../../../../context/ThemeContext'
import { CodeBlock } from '../../../../components/CodeBlock'
import { DocTerm } from '../../../../components/docPreview'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight } from 'lucide-react'
import { NextSteps } from '../../../../components/NextSteps'

export function AtomicContexts() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const t = (d: string, l: string) => isDark ? d : l

  return (
    <div className="max-w-4xl mx-auto">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm mb-6">
        <Link to="/docs" className={t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}>Docs</Link>
        <span className={t('text-gray-500','text-gray-400')}>/</span>
        <Link to="/docs/models/overview" className={t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}>Models</Link>
        <span className={t('text-gray-500','text-gray-400')}>/</span>
        <span className={t('text-gray-300','text-gray-600')}>Transactions</span>
      </div>

      {/* Header */}
      <div className="mb-10">
        <h1 className={`text-4xl font-bold tracking-tighter mb-4 ${t('text-white','text-gray-900')}`}>
          <span className="gradient-text font-mono">Transactions: Atomic Contexts</span>
        </h1>
        <p className={`text-xl leading-relaxed ${t('text-gray-300','text-gray-600')}`}>
          Aquilia transaction manager supports decorators, context blocks, explicit isolation levels, read-only routing, watchdog timeout constraints, and durability safety checks.
        </p>
      </div>

      {/* atomic usage */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Atomic Usage</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Provide transaction safety with <DocTerm id="orm.atomic">atomic</DocTerm> context blocks or decorators:
        </p>
        <CodeBlock language="python">{`from aquilia.models.transactions import atomic

# Context Manager
async with atomic():
    user = await User.create(name="Alice")
    await Profile.create(user=user.id)

# Decorator
@atomic()
async def make_purchase(user_id, item_id):
    await User.objects.filter(id=user_id).update(balance=F("balance") - 10)
    await Order.create(user_id=user_id, item_id=item_id)`}</CodeBlock>
      </section>

      {/* Transaction options */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Advanced Options</h2>
        <div className="space-y-6">
          <div>
            <h3 className={`text-lg font-semibold mb-2 ${t('text-white','text-gray-900')}`}>Isolation Levels</h3>
            <p className={`text-sm mb-3 ${t('text-gray-300','text-gray-600')}`}>
              Configure SQL isolation level on PostgreSQL or MySQL:
            </p>
            <CodeBlock language="python">{`# Supports: READ UNCOMMITTED, READ COMMITTED, REPEATABLE READ, SERIALIZABLE
async with atomic(isolation="SERIALIZABLE"):
    ...`}</CodeBlock>
          </div>

          <div>
            <h3 className={`text-lg font-semibold mb-2 ${t('text-white','text-gray-900')}`}>Read-Only Transactions</h3>
            <p className={`text-sm mb-3 ${t('text-gray-300','text-gray-600')}`}>
              On SQLite, <code>readonly=True</code> routes queries to a reader connection pool, avoiding locking contentions with the database writer:
            </p>
            <CodeBlock language="python">{`async with atomic(readonly=True):
    users = await User.objects.all()`}</CodeBlock>
          </div>

          <div>
            <h3 className={`text-lg font-semibold mb-2 ${t('text-white','text-gray-900')}`}>Watchdog Timeout</h3>
            <p className={`text-sm mb-3 ${t('text-gray-300','text-gray-600')}`}>
              Cancel the block and trigger a rollback if execution exceeds the configured duration:
            </p>
            <CodeBlock language="python">{`# Raises QueryFault if block takes longer than 5 seconds
async with atomic(timeout=5.0):
    await long_running_query()`}</CodeBlock>
          </div>

          <div>
            <h3 className={`text-lg font-semibold mb-2 ${t('text-white','text-gray-900')}`}>Durability Safety</h3>
            <p className={`text-sm mb-3 ${t('text-gray-300','text-gray-600')}`}>
              Use <code>durable=True</code> to ensure this transaction block is strictly the outermost block, preventing nesting:
            </p>
            <CodeBlock language="python">{`async with atomic(durable=True):
    # Fails with QueryFault if called inside another transaction block
    ...`}</CodeBlock>
          </div>
        </div>
      </section>

      {/* Navigation */}
      <div className={`flex justify-between items-center pt-8 mt-8 border-t ${t('border-gray-700','border-gray-200')}`}>
        <Link to="/docs/models/relationships/m2m" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          <ArrowLeft className="w-4 h-4" /> Many-to-Many Operations
        </Link>
        <Link to="/docs/models/transactions/savepoints" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          Savepoints & Nesting <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
