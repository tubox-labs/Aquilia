import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Shield } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function SessionsGuards() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const sectionHeaderClass = `text-2xl font-mono font-bold tracking-tight mb-6 flex items-center gap-3 ${
    isDark ? 'text-white' : 'text-gray-900'
  }`
  const textClass = `text-sm leading-relaxed mb-6 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-12 border-b border-zinc-200 dark:border-zinc-800 pb-8">
        <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-widest text-aquilia-500 mb-4">
          <Shield className="w-4 h-4" />
          Sessions / Context
        </div>
        <h1 className={`text-4xl font-mono ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          <span className="font-bold tracking-tighter gradient-text relative group inline-block">
            Session Context
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-zinc-300' : 'text-zinc-700'}`}>
          Manage scoped sessions inside code blocks using <DocTerm id="sessions.context">SessionContext</DocTerm> context managers.
        </p>
      </div>

      {/* SessionContext */}
      <section className="mb-16">
        <h2 className={sectionHeaderClass}>Scoped Session Access with SessionContext</h2>
        <p className={textClass}>
          The <code className="text-aquilia-500">SessionContext</code> manager provides scoped asynchronous context managers.
          They accept the request context (<code className="text-aquilia-500">ctx</code>) and handle startup resolution and shutdown commit/rollbacks:
        </p>
        
        <div className="space-y-8">
          <div>
            <h3 className={`text-lg font-bold font-mono mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
              1. authenticated(ctx)
            </h3>
            <p className={textClass}>
              An asynchronous context manager that requires an active authenticated session. If no session exists, raises <code className="text-aquilia-500">SessionRequiredFault</code>. If the session is not authenticated, raises <code className="text-aquilia-500">AUTH_REQUIRED</code>.
            </p>
          </div>

          <div>
            <h3 className={`text-lg font-bold font-mono mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
              2. ensure(ctx)
            </h3>
            <p className={textClass}>
              An asynchronous context manager that ensures a session exists. If one is missing from the context, raises <code className="text-aquilia-500">SessionRequiredFault</code>.
            </p>
          </div>

          <div>
            <h3 className={`text-lg font-bold font-mono mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
              3. transactional(ctx)
            </h3>
            <p className={textClass}>
              A transactional session context that takes a snapshot of the session data dictionary on enter. If any exception is raised inside the context block, it automatically rolls back session modifications to prevent partial/invalid states.
            </p>
          </div>
        </div>

        <div className="mt-8">
          <CodeBlock language="python" filename="context_usage.py" highlightLines={[6, 13, 20, 24]}>{`from aquilia.sessions import SessionContext

# 1. .authenticated() — Context block requiring authentication
async def protected_operation(ctx):
    async with SessionContext.authenticated(ctx) as session:
        user_id = session.principal.id
        session["last_action"] = "protected_op"
    # Committed automatically on exiting the context block successfully


# 2. .ensure() — Context block ensuring a session exists
async def track_visitor(ctx):
    async with SessionContext.ensure(ctx) as session:
        session["visits"] = session.get("visits", 0) + 1


# 3. .transactional() — Context block with automatic snapshot-rollback on exceptions
async def critical_update(ctx):
    async with SessionContext.transactional(ctx) as session:
        session["balance"] -= 100
        # If any exception is raised here, session data is restored to its original snapshot state
        await process_external_billing()`}</CodeBlock>
        </div>
      </section>

      <NextSteps />
    </div>
  )
}
