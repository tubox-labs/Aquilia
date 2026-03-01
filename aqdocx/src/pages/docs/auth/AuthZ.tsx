import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Lock, Shield, Layers, Cpu } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function AuthZPage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Lock className="w-4 h-4" />
          Security / Authorization
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Authorization
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia provides a unified <code className="text-aquilia-500">AuthzEngine</code> that combines RBAC, ABAC, scopes, and tenant isolation. Default-deny ensures secure-by-default access control. Results use the <code className="text-aquilia-500">Decision</code> enum: ALLOW, DENY, or ABSTAIN.
        </p>
      </div>

      {/* Decision & Context */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Decision Model</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          {[
            { label: 'ALLOW', desc: 'Access is explicitly permitted.', color: '#22c55e' },
            { label: 'DENY', desc: 'Access is explicitly denied.', color: '#ef4444' },
            { label: 'ABSTAIN', desc: 'No opinion — falls through to next check (default deny).', color: '#f59e0b' },
          ].map((d, i) => (
            <div key={i} className={boxClass}>
              <span className="font-mono font-bold text-sm" style={{ color: d.color }}>{d.label}</span>
              <p className={`mt-2 text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{d.desc}</p>
            </div>
          ))}
        </div>
        <CodeBlock language="python" filename="Authorization Types">{`from aquilia.auth.authz import Decision, AuthzContext, AuthzResult

# AuthzContext — input to any check
ctx = AuthzContext(
    identity=current_identity,
    resource="orders",
    action="delete",
    resource_id="order_42",
    environment={"ip": "1.2.3.4", "time": now()},
)

# AuthzResult — output from a check
result = AuthzResult(
    decision=Decision.ALLOW,
    reason="Admin role grants full access",
    matched_rules=["admin_full_access"],
)`}</CodeBlock>
      </section>

      {/* Unified AuthzEngine */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}><Cpu className="w-5 h-5 text-blue-500" />Unified AuthzEngine</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">AuthzEngine</code> wraps RBAC, ABAC, and scope checking in a single API. Use <code className="text-aquilia-500">authorize()</code> for the full chain or individual check methods.
        </p>
        <CodeBlock language="python" filename="AuthzEngine">{`from aquilia.auth.authz import AuthzEngine

engine = AuthzEngine(
    rbac_engine=rbac,
    abac_engine=abac,
    scope_checker=scope_checker,
)

# Full authorization check — runs all engines
result = await engine.authorize(ctx)
# result.decision → Decision.ALLOW / DENY

# Individual checks
await engine.check_scope(identity, required=["orders:write"])
await engine.check_role(identity, required=["admin"])
await engine.check_permission(identity, resource="orders", action="delete")
await engine.check_tenant(identity, resource_tenant_id="org_1")

# List all permitted actions for a resource
actions = await engine.list_permitted_actions(identity, resource="orders")
# → ["read", "write", "update"]  (not "delete" if denied)`}</CodeBlock>
      </section>

      {/* RBAC */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}><Shield className="w-5 h-5 text-green-500" />Role-Based Access Control (RBAC)</h2>
        <CodeBlock language="python" filename="rbac.py">{`from aquilia.auth.authz import RBACEngine

rbac = RBACEngine()

# Define roles with permissions
rbac.define_role("admin", permissions=[
    "articles:read", "articles:write", "articles:delete",
    "users:read", "users:write", "users:delete",
    "settings:manage",
])

rbac.define_role("editor", permissions=[
    "articles:read", "articles:write",
    "users:read",
])

rbac.define_role("viewer", permissions=[
    "articles:read", "users:read",
])

# Role inheritance with cycle detection
rbac.define_role("super_admin", inherits=["admin"], permissions=[
    "system:shutdown", "system:audit",
])

# Get effective permissions (follows inheritance)
perms = rbac.get_permissions("super_admin")
# → {"system:shutdown", "system:audit", "articles:*", "users:*", "settings:manage"}

# Check permission
allowed = await rbac.check_permission(identity, "articles:delete")
# → Decision.ALLOW if identity has "admin" or "super_admin" role

# Check via unified check()
result = await rbac.check(identity, resource="articles", action="delete")`}</CodeBlock>
      </section>

      {/* ABAC */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}><Layers className="w-5 h-5 text-amber-500" />Attribute-Based Access Control (ABAC)</h2>
        <CodeBlock language="python" filename="abac.py">{`from aquilia.auth.authz import ABACEngine

abac = ABACEngine()

# Register attribute-based policies
abac.register_policy(
    name="owner_can_edit",
    condition=lambda ctx: (
        ctx.action == "edit"
        and ctx.resource.get("owner_id") == ctx.identity.id
    ),
    decision=Decision.ALLOW,
)

abac.register_policy(
    name="business_hours_only",
    condition=lambda ctx: (
        ctx.action in ("write", "delete")
        and 9 <= ctx.environment.get("hour", 0) <= 17
    ),
    decision=Decision.DENY,  # deny outside business hours
)

abac.register_policy(
    name="department_access",
    condition=lambda ctx: (
        ctx.resource.get("department")
        in ctx.identity.get_attribute("departments", [])
    ),
    decision=Decision.ALLOW,
)

# Evaluate — all matching policies are evaluated
result = await abac.evaluate(ctx)`}</CodeBlock>
      </section>

      {/* ScopeChecker */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>ScopeChecker</h2>
        <CodeBlock language="python" filename="Scopes">{`from aquilia.auth.authz import ScopeChecker

checker = ScopeChecker()

# Check if identity's scopes satisfy requirements
result = checker.check_scopes(
    identity_scopes=["read", "write", "admin:read"],
    required_scopes=["read", "write"],
)
# → Decision.ALLOW (has both)

result = checker.check(identity, required=["admin:write"])
# → Decision.DENY (missing admin:write)`}</CodeBlock>
      </section>

      {/* PolicyBuilder */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>PolicyBuilder</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <code className="text-aquilia-500">PolicyBuilder</code> provides factory methods for common authorization patterns.
        </p>
        <CodeBlock language="python" filename="PolicyBuilder">{`from aquilia.auth.authz import PolicyBuilder

# Owner-only — only the resource owner can access
policy = PolicyBuilder.owner_only(owner_field="author_id")

# Admin or owner — admins + owner can access
policy = PolicyBuilder.admin_or_owner(
    admin_roles=["admin", "superadmin"],
    owner_field="author_id",
)

# Time-based — restrict access by time window
policy = PolicyBuilder.time_based(
    start_hour=9,
    end_hour=17,
    weekdays_only=True,
)`}</CodeBlock>
      </section>

      {/* Policy DSL */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Policy DSL</h2>
        <CodeBlock language="python" filename="policy.py">{`from aquilia.auth.policy import (
    Policy, PolicyRegistry, PolicyDecision,
    Allow, Deny, Abstain, rule,
)

class ArticlePolicy(Policy):
    """Authorization rules for Article resources."""

    @rule
    async def owner_can_manage(self, identity, article, action):
        if article.author_id == identity.id:
            return Allow(reason="Owner has full access")
        return Abstain()

    @rule
    async def editors_can_edit(self, identity, article, action):
        if "editor" in identity.roles and action != "delete":
            return Allow(reason="Editor access")
        return Abstain()

    @rule
    async def deny_suspended(self, identity, article, action):
        if identity.status == "suspended":
            return Deny(reason="Account suspended")
        return Abstain()

# Register and evaluate (default deny if no ALLOW)
registry = PolicyRegistry()
registry.register(ArticlePolicy)

result = await registry.evaluate(
    policy_class=ArticlePolicy,
    identity=current_user,
    resource=article,
    action="edit",
)

if result.decision == PolicyDecision.ALLOW:
    ...  # proceed
elif result.decision == PolicyDecision.DENY:
    ...  # 403 Forbidden`}</CodeBlock>
      </section>

      {/* Guard Integration */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Guard Integration</h2>
        <CodeBlock language="python" filename="guards.py">{`from aquilia.auth.guards import AuthGuard, AuthzGuard, ScopeGuard, RoleGuard

class ArticleController(Controller):
    prefix = "/api/articles"

    @Get("/")
    async def list_articles(self, ctx):
        """Public — no guard required."""
        ...

    @Get("/{id:int}")
    async def get_article(self, ctx, id: int):
        """Requires authentication."""
        guard = AuthGuard(token_manager=tm, identity_store=ids)
        await guard.check(ctx)
        ...

    @Put("/{id:int}")
    async def update_article(self, ctx, id: int):
        """Requires scope + RBAC check."""
        await ScopeGuard(required_scopes=["articles:write"]).check(ctx)
        await AuthzGuard(
            authz_engine=authz, resource_extractor=lambda r: r.path_params["id"],
        ).check(ctx)
        ...

    @Delete("/{id:int}")
    async def delete_article(self, ctx, id: int):
        """Admin role required."""
        await RoleGuard(roles=["admin"], require_all=True).check(ctx)
        ...`}</CodeBlock>
      </section>

      {/* Nav */}
      <div className="flex justify-between items-center mt-16 pt-8 border-t border-white/10">
        <Link to="/docs/auth" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition">
          <ArrowLeft className="w-4 h-4" /> Authentication
        </Link>
        <Link to="/docs/sessions" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition">
          Sessions <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    
      <NextSteps />
    </div>
  )
}