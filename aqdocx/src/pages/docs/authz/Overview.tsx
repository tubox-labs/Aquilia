import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Shield, Cpu, AlertTriangle } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function AuthZOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto space-y-12">
      {/* Header */}
      <div className="space-y-4">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium tracking-wide">
          <Shield className="w-4 h-4" />
          <span>Security &amp; Auth / Authorization</span>
        </div>
        <h1 className={`text-4xl font-extrabold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="gradient-text font-mono relative group inline-block">
            Authorization Engine
            <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia's authorization subsystem coordinates RBAC (Role-Based), ABAC (Attribute-Based), scope checks, and tenant isolation policies into a unified, high-performance evaluation coordinator named <DocTerm id="auth.authz_engine">AuthzEngine</DocTerm>.
        </p>
      </div>

      {/* Decision Model */}
      <section className="space-y-6">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Decision Model
        </h2>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia evaluates authorization requests using a tri-state decision model. This allows policies to explicitly permit access, explicitly deny access, or abstain to let downstream policies decide.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          {[
            { label: 'ALLOW', desc: 'Access is explicitly permitted. Evaluation terminates and access is granted immediately.', color: '#22c55e' },
            { label: 'DENY', desc: 'Access is explicitly denied. Evaluation terminates and a security fault is raised.', color: '#ef4444' },
            { label: 'ABSTAIN', desc: 'No opinion. Evaluation defers to subsequent registered policies or defaults to deny.', color: '#f59e0b' },
          ].map((d, i) => (
            <div key={i} className="p-5 rounded-xl hover:bg-aquilia-500/5 dark:hover:bg-white/5 transition-all duration-300 border-l-2" style={{ borderColor: d.color }}>
              <span className="font-mono font-bold text-sm" style={{ color: d.color }}>{d.label}</span>
              <p className={`mt-2 text-xs leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{d.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* AuthzContext and AuthzResult */}
      <section className="space-y-6">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Context &amp; Result Structures
        </h2>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Authorization requests are represented by `AuthzContext`, which holds the security principal (<DocTerm id="auth.identity">Identity</DocTerm>), resource ID, action, scopes, roles, attributes, and tenant ID. Evaluators produce `AuthzResult` objects:
        </p>
        <CodeBlock language="python" filename="Authorization Context" highlightLines={[4, 9, 13]}>
{`from aquilia.auth.authz import Decision, AuthzContext, AuthzResult

# AuthzContext - Input parameters for evaluating policies
ctx = AuthzContext(
    identity=current_identity,       # The authenticated Identity object
    resource="orders:1234",          # The resource being accessed
    action="delete",                 # Action name
    scopes=["orders:read", "orders:write"], # Scopes derived from JWT/Session
    roles=["editor"],                # Roles attached to the principal
    tenant_id="tenant_company_a",    # Tenant ID for isolation check
    attributes={"owner_id": "user_42"}, # Resource attributes for ABAC
)

# AuthzResult - Output describing decision outcome
result = AuthzResult(
    decision=Decision.ALLOW,
    reason="Identity is resource owner",
    policy_id="owner_only",
)`}
        </CodeBlock>
      </section>

      {/* Unified Engine Integration */}
      <section className="space-y-6">
        <h2 className={`text-2.5xl font-bold tracking-tight flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Cpu className="w-6 h-6 text-blue-500" />
          <span>Unified AuthzEngine</span>
        </h2>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <DocTerm id="auth.authz_engine">AuthzEngine</DocTerm> aggregates all sub-engines. It provides explicit helper checks for scopes, roles, permissions, and tenant mismatches, as well as a sequential ABAC policy evaluation pipeline.
        </p>
        
        <div className="p-4 rounded-lg bg-yellow-500/5 border-l-4 border-yellow-500/30 flex gap-3 text-sm">
          <AlertTriangle className="w-5 h-5 text-yellow-500 shrink-0" />
          <div className={isDark ? 'text-gray-300' : 'text-gray-700'}>
            <strong>Default Deny:</strong> If no policy explicitly returns <code>ALLOW</code> or <code>DENY</code>, the engine falls back to a secure default deny decision.
          </div>
        </div>

        <CodeBlock language="python" filename="AuthzEngine Execution" highlightLines={[7, 10, 13, 15]}>
{`from aquilia.auth.authz import AuthzEngine

# Initialize with sub-engines
engine = AuthzEngine(rbac=rbac_engine, abac=abac_engine)

# Configure order of ABAC policy runs
engine.set_policy_order(["owner_can_edit", "business_hours_only"])

# 1. Pipeline check: runs ABAC policies, returning first non-ABSTAIN result
result = engine.check(ctx)

# 2. Enforcement: raises AUTHZ_POLICY_DENIED on Decision.DENY
engine.authorize(ctx, raise_on_deny=True)

# 3. Direct checks (raise specific faults on authorization failure)
engine.check_scope(ctx, required_scopes=["orders:write"]) # Raises AUTHZ_INSUFFICIENT_SCOPE
engine.check_role(ctx, required_roles=["admin"])           # Raises AUTHZ_INSUFFICIENT_ROLE
engine.check_permission(ctx, permission="orders:delete")  # Raises AUTHZ_RESOURCE_FORBIDDEN
engine.check_tenant(ctx, resource_tenant_id="tenant_b")    # Raises AUTHZ_TENANT_MISMATCH

# 4. Utilities: filter allowed actions for a resource
permitted_actions = engine.list_permitted_actions(
    identity=current_user,
    resource="orders:1234",
    actions=["read", "write", "delete"]
)`}
        </CodeBlock>
      </section>

      {/* Footer Navigation */}
      <div className="flex justify-between items-center mt-16 pt-8 border-t border-white/10">
        <Link to="/docs/auth/guards" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition font-medium">
          <ArrowLeft className="w-4 h-4" /> Guards
        </Link>
        <Link to="/docs/authz/rbac" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition font-medium">
          Role-Based Access Control (RBAC) <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
