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
            Authorization Engine &amp; DSL
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia's authorization subsystem integrates RBAC, ABAC, scope checks, and tenant isolation into a unified `AuthzEngine`.
        </p>
      </div>

      {/* Decision Model */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Decision Model</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          {[
            { label: 'ALLOW', desc: 'Access is explicitly permitted.', color: '#22c55e' },
            { label: 'DENY', desc: 'Access is explicitly denied.', color: '#ef4444' },
            { label: 'ABSTAIN', desc: 'No opinion — defers evaluation to subsequent policies.', color: '#f59e0b' },
          ].map((d, i) => (
            <div key={i} className={boxClass}>
              <span className="font-mono font-bold text-sm" style={{ color: d.color }}>{d.label}</span>
              <p className={`mt-2 text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{d.desc}</p>
            </div>
          ))}
        </div>
        <CodeBlock language="python" filename="Authorization Structures">{`from aquilia.auth.authz import Decision, AuthzContext, AuthzResult

# AuthzContext - Input data for authorization checks
ctx = AuthzContext(
    identity=current_identity,
    resource="orders",
    action="delete",
    scopes=["orders:read", "orders:write"],
    roles=["editor"],
    tenant_id="tenant_123",
    session_id="sess_abc",
    attributes={"owner_id": "user_42"},
)

# AuthzResult - Output produced by policy evaluation
result = AuthzResult(
    decision=Decision.ALLOW,
    reason="Identity is resource owner",
    policy_id="owner_only",
)`}</CodeBlock>
      </section>

      {/* Unified AuthzEngine */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}><Cpu className="w-5 h-5 text-blue-500" />Unified AuthzEngine</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">AuthzEngine</code> coordinates RBAC and ABAC checks.
        </p>
        <CodeBlock language="python" filename="AuthzEngine Integration">{`from aquilia.auth.authz import AuthzEngine

engine = AuthzEngine(
    rbac=rbac_engine,
    abac=abac_engine,
)

# Set evaluation order for registered ABAC policies
engine.set_policy_order(["owner_can_edit", "business_hours_only"])

# Runs ABAC policies in order. Returns first non-ABSTAIN result. Default Deny.
result = engine.check(ctx)

# Throws AUTHZ_POLICY_DENIED on Decision.DENY
engine.authorize(ctx, raise_on_deny=True)

# Individual check methods (raise relevant faults on failure)
engine.check_scope(ctx, required_scopes=["orders:write"])
engine.check_role(ctx, required_roles=["admin"])
engine.check_permission(ctx, permission="orders:delete")
engine.check_tenant(ctx, resource_tenant_id="tenant_123")

# List all permitted actions
permitted = engine.list_permitted_actions(
    identity=current_user,
    resource="orders",
    actions=["read", "write", "delete"],
)`}</CodeBlock>
      </section>

      {/* RBAC Engine */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}><Shield className="w-5 h-5 text-green-500" />RBAC Engine</h2>
        <CodeBlock language="python" filename="rbac_setup.py">{`from aquilia.auth.authz import RBACEngine

rbac = RBACEngine()

# Define roles and permissions
rbac.define_role("editor", permissions=["posts:read", "posts:write"])
rbac.define_role("admin", inherits=["editor"], permissions=["posts:delete"])

# Check permission against a list of roles
allowed = rbac.check_permission(roles=["editor"], permission="posts:write") # True

# Evaluates against roles in AuthzContext
result = rbac.check(ctx, permission="posts:delete") # AuthzResult`}</CodeBlock>
      </section>

      {/* ABAC Engine */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}><Layers className="w-5 h-5 text-amber-500" />ABAC Engine</h2>
        <CodeBlock language="python" filename="abac_setup.py">{`from aquilia.auth.authz import ABACEngine, Decision, AuthzResult

abac = ABACEngine()

# Register policies by ID
abac.register_policy(
    policy_id="owner_can_edit",
    policy_func=lambda ctx: (
        AuthzResult(Decision.ALLOW) if ctx.attributes.get("owner_id") == ctx.identity.id
        else AuthzResult(Decision.ABSTAIN)
    )
)

# Evaluate specific policy
result = abac.evaluate(ctx, policy_id="owner_can_edit")`}</CodeBlock>
      </section>

      {/* PolicyBuilder */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>PolicyBuilder</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Use the static helper methods in <code className="text-aquilia-500">PolicyBuilder</code> to quickly construct ABAC policies:
        </p>
        <CodeBlock language="python" filename="PolicyBuilder Usage">{`from aquilia.auth.authz import PolicyBuilder

# Owner-only check
owner_policy = PolicyBuilder.owner_only(attribute="owner_id")

# Admin or owner check
admin_owner_policy = PolicyBuilder.admin_or_owner(
    admin_role="admin",
    attribute="owner_id",
)

# Time-based check (allowed hours in UTC)
business_hours_policy = PolicyBuilder.time_based(allowed_hours=(9, 17))`}</CodeBlock>
      </section>

      {/* Policy DSL */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Declarative Policy DSL</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">aquilia.auth.policy</code> module provides a declarative DSL for resource-based policies.
        </p>
        <CodeBlock language="python" filename="ArticlePolicy">{`from aquilia.auth.policy import Policy, PolicyRegistry, Allow, Deny, Abstain, rule

class ArticlePolicy(Policy):
    resource = "article"

    @rule
    def can_read(self, identity, resource):
        return Allow("Anyone can read")

    @rule
    def can_edit(self, identity, resource):
        if resource and resource.author_id == identity.id:
            return Allow("Author can edit")
        if "editor" in identity.roles:
            return Allow("Editor can edit")
        return Deny("Must be author or editor")

# Register instance of Policy in Registry
registry = PolicyRegistry()
registry.register(ArticlePolicy())

# Evaluate synchronously (returns PolicyResult)
result = registry.evaluate(
    resource="article",
    action="edit",
    identity=current_user,
    resource_obj=article,
)`}</CodeBlock>
      </section>

      {/* Nav */}
      <div className="flex justify-between items-center mt-16 pt-8 border-t border-white/10">
        <Link to="/docs/auth/guards" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition">
          <ArrowLeft className="w-4 h-4" /> Guards
        </Link>
        <Link to="/docs/sessions" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition">
          Sessions <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    
      <NextSteps />
    </div>
  )
}