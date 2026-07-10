import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Shield } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function AuthZPolicies() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto space-y-12">
      {/* Header */}
      <div className="space-y-4">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium tracking-wide">
          <Shield className="w-4 h-4" />
          <span>Security &amp; Auth / Authorization / Policy DSL</span>
        </div>
        <h1 className={`text-4xl font-extrabold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="gradient-text font-mono relative group inline-block">
            Declarative Policy DSL
            <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The `aquilia.auth.policy` module provides a declarative, resource-centric policy language. Define complex authorization logic by subclassing <DocTerm id="auth.policy">Policy</DocTerm> and decorating methods with `@rule`.
        </p>
      </div>

      {/* Writing Policies */}
      <section className="space-y-6">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Defining Resource Policies
        </h2>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Resource policies group access rules for a specific resource type together. A rule method must be named <code>can_&#123;action&#125;</code> and return a <DocTerm id="auth.policy_result">PolicyResult</DocTerm> using <code>Allow</code>, <code>Deny</code>, or <code>Abstain</code>:
        </p>
        <CodeBlock language="python" filename="post_policy.py" highlightLines={[6, 9, 13, 17]}>
{`from aquilia.auth.policy import Policy, Allow, Deny, Abstain, rule

class PostPolicy(Policy):
    resource = "post" # Connects this policy to the "post" resource name

    @rule
    def can_read(self, identity, resource=None):
        # Open access to anyone for reading
        return Allow("Public resource")

    @rule
    def can_edit(self, identity, resource):
        # Allow if the identity is the author of the post
        if resource and resource.author_id == identity.id:
            return Allow("Author can edit")
        
        # Defer to other rules if the user is an admin
        if "admin" in identity.roles:
            return Abstain("Let admin rules decide")
            
        return Deny("Must be author or administrator")`}
        </CodeBlock>
      </section>

      {/* Policy Registry */}
      <section className="space-y-6">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          The Policy Registry
        </h2>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Polices are registered with a <DocTerm id="auth.policy_registry">PolicyRegistry</DocTerm>. When evaluating a permission, the registry locates the appropriate policy based on the resource name and evaluates the matching <code>can_&#123;action&#125;</code> method:
        </p>
        <CodeBlock language="python" filename="registry_evaluation.py" highlightLines={[6, 9]}>
{`from aquilia.auth.policy import PolicyRegistry
from post_policy import PostPolicy

# Initialize registry and register the policy
registry = PolicyRegistry()
registry.register(PostPolicy())

# Evaluate access dynamically
result = registry.evaluate(
    resource="post",
    action="edit",
    identity=current_identity,
    resource_obj=active_post
)

print(result.decision) # Decision.ALLOW or Decision.DENY
print(result.reason)   # "Author can edit" or "Must be author or administrator"`}
        </CodeBlock>
      </section>

      {/* Rule Resolution Engine */}
      <section className="space-y-6">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Rule Resolution Flow
        </h2>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          When `evaluate()` is called, the policy engine follows this order of operations:
        </p>
        <div className="space-y-4">
          {[
            { step: '1', title: 'Method Lookup', desc: 'Looks for a method named `can_{action}` matching the action argument.' },
            { step: '2', title: 'Rule Verification', desc: 'Verifies if the method has been decorated with `@rule`.' },
            { step: '3', title: 'Evaluation', desc: 'Runs the rule method with user identity and the resource object.' },
            { step: '4', title: 'Decision Propagation', desc: 'If the result is `Allow` or `Deny`, it is returned immediately. If `Abstain`, it defaults to Deny.' },
          ].map((item, idx) => (
            <div key={idx} className="flex gap-4 p-3 rounded-xl hover:bg-aquilia-500/5 transition-all duration-300">
              <span className="font-mono text-xl font-extrabold text-aquilia-500 bg-aquilia-500/10 w-8 h-8 rounded-full flex items-center justify-center shrink-0">
                {item.step}
              </span>
              <div className="space-y-1">
                <span className={`font-semibold text-sm block ${isDark ? 'text-white' : 'text-gray-900'}`}>{item.title}</span>
                <p className={`text-xs leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Footer Navigation */}
      <div className="flex justify-between items-center mt-16 pt-8 border-t border-white/10">
        <Link to="/docs/authz/abac" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition font-medium">
          <ArrowLeft className="w-4 h-4" /> ABAC
        </Link>
        <Link to="/docs/sessions" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition font-medium">
          Sessions <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
