import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Shield } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function SessionsGuards() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Shield className="w-4 h-4" />
          Sessions / Guards
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Session Guards & Context
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The enhanced session module provides <code className="text-aquilia-500">SessionGuard</code> for declarative access control, the <code className="text-aquilia-500">@requires</code> decorator for guard composition, and <code className="text-aquilia-500">SessionContext</code> for async context managers with transactional session operations.
        </p>
      </div>

      {/* SessionGuard */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>SessionGuard Base</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          A <code className="text-aquilia-500">SessionGuard</code> is a simple callable that inspects the session and raises a fault if the check fails:
        </p>
        <CodeBlock language="python" filename="guard_base.py">{`from aquilia.sessions.enhanced import SessionGuard
from aquilia.sessions import Session


class SessionGuard:
    """Base class for session access guards."""

    async def check(self, session: Session) -> None:
        """Override this. Raise a fault if the session fails the check.
        If the check passes, return None (or don't return).
        """
        raise NotImplementedError


# Example: Custom guard
class PremiumUserGuard(SessionGuard):
    async def check(self, session: Session) -> None:
        if not session.get("is_premium"):
            raise SessionPolicyViolationFault(
                "Premium subscription required",
                policy_name="premium_check",
            )`}</CodeBlock>
      </section>

      {/* Built-in Guards */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Built-in Guards</h2>

        <h3 className={`text-xl font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>AdminGuard</h3>
        <CodeBlock language="python" filename="admin_guard.py">{`from aquilia.sessions.enhanced import AdminGuard

# AdminGuard checks that:
# 1. Session has an authenticated principal
# 2. principal.kind == "admin" OR principal.attributes includes admin role

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

        <h3 className={`text-xl font-semibold mt-8 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>VerifiedEmailGuard</h3>
        <CodeBlock language="python" filename="verified_guard.py">{`from aquilia.sessions.enhanced import VerifiedEmailGuard

# VerifiedEmailGuard checks that:
# 1. Session is authenticated
# 2. principal.attributes["email_verified"] is True

class SecureController(Controller):
    prefix = "/secure"

    @Post("/transfer")
    @requires(VerifiedEmailGuard())
    async def transfer(self, ctx, session: Session):
        """Only verified users can transfer funds."""
        body = await ctx.json_body()
        # ... process transfer
        return ctx.json({"status": "completed"})`}</CodeBlock>
      </section>

      {/* @requires Decorator */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>@requires Decorator</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">@requires</code> decorator applies one or more guards to a handler. All guards must pass for the handler to execute:
        </p>
        <CodeBlock language="python" filename="requires.py">{`from aquilia.sessions.enhanced import requires, AdminGuard, VerifiedEmailGuard


class SensitiveController(Controller):
    prefix = "/sensitive"

    # Single guard
    @Get("/admin-only")
    @requires(AdminGuard())
    async def admin_only(self, ctx, session):
        return ctx.json({"access": "admin"})

    # Multiple guards — ALL must pass
    @Post("/critical-action")
    @requires(AdminGuard(), VerifiedEmailGuard())
    async def critical(self, ctx, session):
        """Must be admin AND have verified email."""
        return ctx.json({"action": "executed"})

    # Custom guard inline
    @Get("/premium")
    @requires(PremiumUserGuard())
    async def premium_content(self, ctx, session):
        return ctx.json({"content": "premium"})`}</CodeBlock>
      </section>

      {/* Custom Guards */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Custom Guards</h2>
        <CodeBlock language="python" filename="custom_guards.py">{`from aquilia.sessions.enhanced import SessionGuard
from aquilia.sessions.faults import SessionPolicyViolationFault


class RoleGuard(SessionGuard):
    """Guard that checks for a specific role."""

    def __init__(self, role: str):
        self.role = role

    async def check(self, session):
        principal = session.principal
        if not principal:
            raise SessionPolicyViolationFault(
                "Authentication required", policy_name="role_check"
            )
        roles = principal.attributes.get("roles", [])
        if self.role not in roles:
            raise SessionPolicyViolationFault(
                f"Role '{self.role}' required",
                policy_name="role_check",
            )


class IPWhitelistGuard(SessionGuard):
    """Guard that checks the request IP against a whitelist."""

    def __init__(self, allowed_ips: list[str]):
        self.allowed_ips = set(allowed_ips)

    async def check(self, session):
        client_ip = session.get("_client_ip", "")
        if client_ip not in self.allowed_ips:
            raise SessionPolicyViolationFault(
                "IP not whitelisted", policy_name="ip_whitelist"
            )


class TwoFactorGuard(SessionGuard):
    """Guard that requires completed 2FA."""

    async def check(self, session):
        if not session.get("2fa_verified"):
            raise SessionPolicyViolationFault(
                "Two-factor authentication required",
                policy_name="2fa_check",
            )


# Compose multiple custom guards:
@requires(
    RoleGuard("editor"),
    VerifiedEmailGuard(),
    TwoFactorGuard(),
)
async def publish_article(self, ctx, session):
    """Must be editor + verified email + 2FA."""
    ...`}</CodeBlock>
      </section>

      {/* SessionContext */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>SessionContext</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">SessionContext</code> singleton provides async context managers for structured session access:
        </p>
        <CodeBlock language="python" filename="context.py">{`from aquilia.sessions.enhanced import SessionContext

ctx_session = SessionContext  # Singleton


# .authenticated() — Context manager that requires authentication
async def protected_operation(request):
    async with ctx_session.authenticated(request) as session:
        # session is guaranteed to be authenticated here
        user_id = session.principal.id
        # ... do work
        session["last_action"] = "protected_op"
    # Session is auto-committed on exit


# .ensure() — Context manager that creates session if needed
async def track_visitor(request):
    async with ctx_session.ensure(request) as session:
        visits = session.get("visits", 0) + 1
        session["visits"] = visits


# .transactional() — Context manager with rollback on error
async def critical_update(request):
    async with ctx_session.transactional(request) as session:
        session["balance"] -= 100
        await external_payment_api()
        # If external_payment_api() raises, session changes are rolled back
        session["last_payment"] = datetime.now().isoformat()`}</CodeBlock>
      </section>

      {/* Combining Guards with Auth */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Integration with Auth System</h2>
        <CodeBlock language="python" filename="auth_integration.py">{`from aquilia import Controller, Get, Post
from aquilia.sessions import session, authenticated
from aquilia.sessions.enhanced import requires, AdminGuard
from aquilia.auth import guard


class UserManagementController(Controller):
    prefix = "/api/users"

    @Get("/")
    @authenticated                      # Session-based auth
    @guard("users:read")                # Permission-based authz
    async def list_users(self, ctx, principal):
        users = await User.objects.all()
        return ctx.json([u.to_dict() for u in users])

    @Post("/")
    @requires(AdminGuard())             # Session guard: admin only
    @guard("users:create")              # Permission check
    async def create_user(self, ctx, session):
        body = await ctx.json_body()
        user = await User.create(**body)
        return ctx.json(user.to_dict(), status=201)

    @Post("/:id/ban")
    @requires(AdminGuard(), TwoFactorGuard())
    async def ban_user(self, ctx, id: str, session):
        user = await User.objects.get(id=id)
        user.is_banned = True
        await user.save()
        return ctx.json({"banned": True})`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
