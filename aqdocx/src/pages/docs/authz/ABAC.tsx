import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Shield, User, Clock } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function AuthZABAC() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto space-y-12">
      {/* Header */}
      <div className="space-y-4">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium tracking-wide">
          <Shield className="w-4 h-4" />
          <span>Security &amp; Auth / Authorization / ABAC</span>
        </div>
        <h1 className={`text-4xl font-extrabold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="gradient-text font-mono relative group inline-block">
            Attribute-Based Access Control
            <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Attribute-Based Access Control enables access decisions based on resource metadata, user parameters, and environment context. In Aquilia, this is driven by the <DocTerm id="auth.abac_engine">ABACEngine</DocTerm> and `PolicyBuilder` helper utilities.
        </p>
      </div>

      {/* ABAC Engine Registration */}
      <section className="space-y-6">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Registering &amp; Evaluating Policies
        </h2>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          ABAC policies are callables that accept an `AuthzContext` and return an `AuthzResult`. Policies are registered with unique IDs in the <DocTerm id="auth.abac_engine">ABACEngine</DocTerm>:
        </p>
        <CodeBlock language="python" filename="abac_engine_setup.py" highlightLines={[8, 16]}>
{`from aquilia.auth.authz import ABACEngine, Decision, AuthzResult, AuthzContext

abac = ABACEngine()

# Define and register a custom policy
def check_owner(ctx: AuthzContext) -> AuthzResult:
    if ctx.attributes.get("owner_id") == ctx.identity.id:
        return AuthzResult(Decision.ALLOW, reason="Identity matches resource owner")
    return AuthzResult(Decision.ABSTAIN, reason="Identity is not owner")

abac.register_policy("owner_can_edit", check_owner)

# Evaluate the policy against a context
ctx = AuthzContext(identity=user, resource="posts:123", action="edit", attributes={"owner_id": "user_42"})
result = abac.evaluate(ctx, policy_id="owner_can_edit")
print(result.decision)  # Decision.ALLOW (if user.id == "user_42")`}
        </CodeBlock>
      </section>

      {/* Policy Builders */}
      <section className="space-y-6">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Built-in Policy Builders
        </h2>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia includes a static class `PolicyBuilder` providing pre-packaged ABAC configurations for common security requirements:
        </p>
        
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 py-4">
          {[
            { icon: <User className="w-5 h-5 text-blue-500" />, title: 'Owner Only', desc: 'Grants access only if the principal\'s ID matches the resource owner ID attribute.' },
            { icon: <Shield className="w-5 h-5 text-green-500" />, title: 'Admin or Owner', desc: 'Allows access if the user has an admin role or matches the resource owner ID.' },
            { icon: <Clock className="w-5 h-5 text-amber-500" />, title: 'Time Based', desc: 'Limits resource mutations to specific hours of the day (specified in UTC).' },
          ].map((item, idx) => (
            <div key={idx} className="p-4 rounded-xl hover:bg-aquilia-500/5 transition-all duration-300 flex flex-col gap-2">
              <div className="flex items-center gap-2">
                {item.icon}
                <span className={`font-semibold text-sm ${isDark ? 'text-white' : 'text-gray-900'}`}>{item.title}</span>
              </div>
              <p className={`text-xs leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{item.desc}</p>
            </div>
          ))}
        </div>

        <CodeBlock language="python" filename="policy_builders.py" highlightLines={[4, 7, 10]}>
{`from aquilia.auth.authz import PolicyBuilder

# 1. Owner-only check (looks up attribute in context.attributes)
owner_policy = PolicyBuilder.owner_only(attribute="owner_id")

# 2. Admin role or resource owner check
admin_or_owner_policy = PolicyBuilder.admin_or_owner(
    admin_role="administrator",
    attribute="owner_id",
)

# 3. Restrict access to business hours (9 AM - 5 PM UTC)
business_hours_policy = PolicyBuilder.time_based(allowed_hours=(9, 17))`}
        </CodeBlock>
      </section>

      {/* Footer Navigation */}
      <div className="flex justify-between items-center mt-16 pt-8 border-t border-white/10">
        <Link to="/docs/authz/rbac" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition font-medium">
          <ArrowLeft className="w-4 h-4" /> RBAC
        </Link>
        <Link to="/docs/authz/policies" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition font-medium">
          Declarative Policy DSL <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
