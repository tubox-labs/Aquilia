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
          Sessions / Guards
        </div>
        <h1 className={`text-4xl font-mono ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          <span className="font-bold tracking-tighter gradient-text relative group inline-block">
            Session Guards &amp; Context
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-zinc-300' : 'text-zinc-700'}`}>
          Secure endpoints declaratively using <DocTerm id="sessions.guard">SessionGuard</DocTerm>, compose validations with <DocTerm id="sessions.requires">@requires</DocTerm>, 
          and manage scoped sessions inside code blocks using <DocTerm id="sessions.context">SessionContext</DocTerm> context managers.
        </p>
      </div>

      {/* SessionGuard */}
      <section className="mb-16">
        <h2 className={sectionHeaderClass}>SessionGuard Base Class</h2>
        <p className={textClass}>
          A <code className="text-aquilia-500">SessionGuard</code> handles endpoint authorization checks.
          <strong>Critical:</strong> The overridden <code className="text-aquilia-500">check()</code> method must return <code className="text-aquilia-500">True</code> on success.
          If it returns <code className="text-aquilia-500">None</code> (or does not return), the decorator treats it as falsy and raises an <code className="text-aquilia-500">AuthorizationFault</code>.
        </p>
        <CodeBlock language="python" filename="guard_base.py" highlightLines={[8, 14, 18, 22]}>{`from aquilia.sessions import Session, SessionGuard
from aquilia.sessions.faults import SessionPolicyViolationFault


class PremiumUserGuard(SessionGuard):
    """Guard that blocks non-premium users."""

    async def check(self, session: Session) -> bool:
        if not session.get("is_premium"):
            raise SessionPolicyViolationFault(
                "Premium subscription required",
                policy_name="premium_check",
            )
        return True # Critical: Must return True on success!`}</CodeBlock>
      </section>

      {/* Built-in Guards */}
      <section className="mb-16 border-t border-zinc-200 dark:border-zinc-800 pt-12">
        <h2 className={sectionHeaderClass}>Built-in Auth Guards</h2>
        <p className={textClass}>
          Session-aware authentication and authorization guards (such as <code className="text-aquilia-500">AdminGuard</code> and <code className="text-aquilia-500">VerifiedEmailGuard</code>)
          are defined in the authentication module:
        </p>
        
        <h3 className={`text-lg font-bold font-mono mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          AdminGuard
        </h3>
        <CodeBlock language="python" filename="admin_guard.py" highlightLines={[1, 10, 14]}>{`from aquilia.auth import AdminGuard, requires
from aquilia.sessions import Session
from aquilia import Controller, Get


class AdminDashboard(Controller):
    prefix = "/admin"

    @Get("/")
    @requires(AdminGuard())
    async def dashboard(self, ctx, session: Session):
        return ctx.json({"admin_panel": True})

    @Get("/users")
    @requires(AdminGuard())
    async def list_users(self, ctx, session: Session):
        users = await User.objects.all()
        return ctx.json([u.to_dict() for u in users])`}</CodeBlock>

        <h3 className={`text-lg font-bold font-mono mt-8 mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          VerifiedEmailGuard
        </h3>
        <CodeBlock language="python" filename="verified_guard.py" highlightLines={[1, 8]}>{`from aquilia.auth import VerifiedEmailGuard, requires
from aquilia import Controller, Post


class SecureController(Controller):
    prefix = "/secure"

    @Post("/transfer")
    @requires(VerifiedEmailGuard())
    async def transfer(self, ctx, session):
        body = await ctx.request.json()
        return ctx.json({"status": "completed"})`}</CodeBlock>
      </section>

      {/* @requires Decorator */}
      <section className="mb-16 border-t border-zinc-200 dark:border-zinc-800 pt-12">
        <h2 className={sectionHeaderClass}>@requires Decorator Composition</h2>
        <p className={textClass}>
          The <code className="text-aquilia-500">@requires</code> decorator chains multiple guards on a controller handler.
          All guards must pass (return <code className="text-aquilia-500">True</code>) for the endpoint to execute:
        </p>
        <CodeBlock language="python" filename="requires.py" highlightLines={[1, 12, 17]}>{`from aquilia.auth import requires, AdminGuard, VerifiedEmailGuard
from aquilia import Controller, Get, Post


class SensitiveController(Controller):
    prefix = "/sensitive"

    # Single guard check
    @Get("/admin-only")
    @requires(AdminGuard())
    async def admin_only(self, ctx, session):
        return ctx.json({"access": "admin"})

    # Multiple guards checked in sequence — ALL must pass
    @Post("/critical-action")
    @requires(AdminGuard(), VerifiedEmailGuard())
    async def critical(self, ctx, session):
        return ctx.json({"action": "executed"})`}</CodeBlock>
      </section>

      {/* Custom Guards */}
      <section className="mb-16 border-t border-zinc-200 dark:border-zinc-800 pt-12">
        <h2 className={sectionHeaderClass}>Custom Session Guards</h2>
        <p className={textClass}>
          Define custom session-level guards by extending <code className="text-aquilia-500">SessionGuard</code>:
        </p>
        <CodeBlock language="python" filename="custom_guards.py" highlightLines={[14, 23]}>{`from aquilia.sessions import SessionGuard
from aquilia.sessions.faults import SessionPolicyViolationFault


class RoleGuard(SessionGuard):
    """Enforces specific user roles."""

    def __init__(self, role: str):
        self.role = role

    async def check(self, session):
        principal = session.principal
        if not principal:
            raise SessionPolicyViolationFault("Authentication required", "role_check")
            
        roles = principal.attributes.get("roles", [])
        if self.role not in roles:
            raise SessionPolicyViolationFault(f"Role '{self.role}' required", "role_check")
            
        return True # Required success return`}</CodeBlock>
      </section>

      {/* SessionContext */}
      <section className="mb-16 border-t border-zinc-200 dark:border-zinc-800 pt-12">
        <h2 className={sectionHeaderClass}>SessionContext</h2>
        <p className={textClass}>
          The <DocTerm id="sessions.context">SessionContext</DocTerm> manager provides scoped asynchronous context managers.
          They accept the request context (<code className="text-aquilia-500">ctx</code>) and handle startup resolution and shutdown commit/rollbacks:
        </p>
        <CodeBlock language="python" filename="context.py" highlightLines={[6, 13, 20, 24]}>{`from aquilia.sessions import SessionContext


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
      </section>

      <NextSteps />
    </div>
  )
}
