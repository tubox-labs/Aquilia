import { useTheme } from '../../../context/ThemeContext';
import { CodeBlock } from '../../../components/CodeBlock';
import { ArrowLeft, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { NextSteps } from '../../../components/NextSteps';

export function ModelsTransactions() {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-2 text-sm mb-4">
          <Link to="/docs" className={isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-500'}>Docs</Link>
          <span className={isDark ? 'text-gray-500' : 'text-gray-400'}>/</span>
          <Link to="/docs/models/overview" className={isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-500'}>Models</Link>
          <span className={isDark ? 'text-gray-500' : 'text-gray-400'}>/</span>
          <span className={isDark ? 'text-gray-300' : 'text-gray-600'}>Transactions</span>
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Transactions
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-xl ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The atomic() context manager, on_commit/on_rollback hooks, isolation levels, and pessimistic locking.
        </p>
      </div>

      {/* Transactions */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Transactions</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The <code>atomic()</code> context manager wraps database operations in a transaction. It supports nesting via savepoints.
        </p>
        <CodeBlock language="python">
{`from aquilia.models.transactions import atomic

# Basic transaction
async with atomic(db):
    user = User(name="Alice", email="alice@co.com")
    await user.save(db)
    profile = Profile(user_id=user.id, bio="Hello")
    await profile.save(db)
    # If either fails, both are rolled back

# Nested transactions — uses SAVEPOINTs
async with atomic(db):
    await user.save(db)

    async with atomic(db):
        # Creates SAVEPOINT
        await risky_operation(db)
        # If this fails, only the inner block rolls back

    # Outer transaction continues

# Durable mode — prevents nesting, always creates a real transaction
async with atomic(db, durable=True):
    await critical_operation(db)

# as decorator
@atomic(db)
async def transfer_funds(from_id, to_id, amount):
    await Account.objects.filter(id=from_id).update(balance=F("balance") - amount)
    await Account.objects.filter(id=to_id).update(balance=F("balance") + amount)`}
        </CodeBlock>
      </section>

      {/* on_commit / on_rollback */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>on_commit / on_rollback Hooks</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Register callbacks that fire after the transaction successfully commits or rolls back. Callbacks are FIFO-ordered and only fire once.
        </p>
        <CodeBlock language="python">
{`from aquilia.models.transactions import atomic, on_commit, on_rollback

async with atomic(db) as txn:
    user = User(name="Bob")
    await user.save(db)

    # Runs only if the transaction commits
    on_commit(txn, lambda: send_welcome_email(user.id))
    on_commit(txn, lambda: invalidate_cache("users"))

    # Runs only if the transaction rolls back
    on_rollback(txn, lambda: log_failure("user_creation_failed"))

# Multiple callbacks execute in registration order
# on_commit hooks are suppressed if any exception occurs`}
        </CodeBlock>
      </section>

      {/* Isolation Levels */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Isolation Levels</h2>
        <CodeBlock language="python">
{`from aquilia.models.transactions import atomic, IsolationLevel

# Default isolation level (depends on DB engine)
async with atomic(db):
    ...

# Explicit isolation level (PostgreSQL)
async with atomic(db, isolation_level=IsolationLevel.SERIALIZABLE):
    ...

# Available levels:
# IsolationLevel.READ_UNCOMMITTED
# IsolationLevel.READ_COMMITTED     (PG default)
# IsolationLevel.REPEATABLE_READ    (MySQL default)
# IsolationLevel.SERIALIZABLE       (strictest)`}
        </CodeBlock>
      </section>

      {/* select_for_update */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Pessimistic Locking — select_for_update</h2>
        <CodeBlock language="python">
{`from aquilia.models.transactions import atomic

# SELECT ... FOR UPDATE locks the selected rows
async with atomic(db):
    account = await (
        Account.objects
        .select_for_update()   # basic row lock
        .filter(id=42)
        .first()
    )
    account.balance -= 100
    await account.save(db)

# Options:
# .select_for_update(nowait=True)       — raise error instead of waiting
# .select_for_update(skip_locked=True)  — skip locked rows
# .select_for_update(of=["self"])       — lock only this table (not JOINed)
# .select_for_update(no_key=True)       — FOR NO KEY UPDATE (PG: weaker lock)`}
        </CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex justify-between items-center pt-8 mt-8 border-t ${isDark ? 'border-gray-700' : 'border-gray-200'}`}>
        <Link
          to="/docs/models/signals"
          className={`flex items-center gap-2 text-sm font-medium ${isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-500'}`}
        >
          <ArrowLeft className="w-4 h-4" /> Signals
        </Link>
        <Link
          to="/docs/models/aggregation"
          className={`flex items-center gap-2 text-sm font-medium ${isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-500'}`}
        >
          Aggregation <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  );
}
