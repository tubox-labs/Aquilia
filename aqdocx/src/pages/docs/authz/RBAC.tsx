import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Shield, AlertCircle } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function AuthZRBAC() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto space-y-12">
      {/* Header */}
      <div className="space-y-4">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium tracking-wide">
          <Shield className="w-4 h-4" />
          <span>Security &amp; Auth / Authorization / RBAC</span>
        </div>
        <h1 className={`text-4xl font-extrabold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="gradient-text font-mono relative group inline-block">
            Role-Based Access Control
            <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia's Role-Based Access Control is driven by the <DocTerm id="auth.rbac_engine">RBACEngine</DocTerm>. It supports explicit role definitions, permission mapping, multi-level role inheritance, and cyclic role detection.
        </p>
      </div>

      {/* Core Concepts */}
      <section className="space-y-6">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          How RBAC Works
        </h2>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Roles group users together, and permissions specify what operations are allowed on resources. Rather than checking roles directly, developers map permissions to roles and check those permissions at the route or handler level.
        </p>
        <div className="p-4 rounded-lg bg-blue-500/5 border-l-4 border-blue-500/30 flex gap-3 text-sm">
          <AlertCircle className="w-5 h-5 text-blue-500 shrink-0" />
          <div className={isDark ? 'text-gray-300' : 'text-gray-700'}>
            <strong>Role Inheritance:</strong> Sub-roles inherit all permissions of parent roles recursively. The hierarchy resolver automatically prevents cyclic reference errors.
          </div>
        </div>
      </section>

      {/* RBAC Setup & Hierarchy */}
      <section className="space-y-6">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Role Definition &amp; Inheritance
        </h2>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Define roles and their hierarchies on the <DocTerm id="auth.rbac_engine">RBACEngine</DocTerm>. In this example, the `admin` role inherits from `editor`, which in turn inherits from `guest`:
        </p>
        <CodeBlock language="python" filename="rbac_setup.py" highlightLines={[6, 9, 12, 15]}>
{`from aquilia.auth.authz import RBACEngine

rbac = RBACEngine()

# 1. Define base permissions for 'guest'
rbac.define_role("guest", permissions=["posts:read"])

# 2. Define 'editor' role, inheriting from 'guest'
rbac.define_role("editor", permissions=["posts:write"], inherits=["guest"])

# 3. Define 'admin' role, inheriting from 'editor'
rbac.define_role("admin", permissions=["posts:delete"], inherits=["editor"])

# Recursive permission checking
guest_perms = rbac.get_permissions("guest")   # {"posts:read"}
editor_perms = rbac.get_permissions("editor") # {"posts:read", "posts:write"}
admin_perms = rbac.get_permissions("admin")   # {"posts:read", "posts:write", "posts:delete"}`}
        </CodeBlock>
      </section>

      {/* Checking Permissions */}
      <section className="space-y-6">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Enforcing Permissions
        </h2>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Permissions can be checked dynamically by supplying a list of roles belonging to the user. This is typically invoked by the <DocTerm id="auth.authz_engine">AuthzEngine</DocTerm>:
        </p>
        <CodeBlock language="python" filename="rbac_checking.py" highlightLines={[4, 7]}>
{`# Checks if any of the user's active roles grant a specific permission
has_access = rbac.check_permission(roles=["editor"], permission="posts:write") # True

# Context-based validation
from aquilia.auth.authz import AuthzContext
ctx = AuthzContext(identity=user, resource="posts", action="delete", roles=["editor"])

result = rbac.check(ctx, permission="posts:delete")
# Returns AuthzResult(decision=Decision.DENY, reason="No role has permission: posts:delete")`}
        </CodeBlock>
      </section>

      {/* Footer Navigation */}
      <div className="flex justify-between items-center mt-16 pt-8 border-t border-white/10">
        <Link to="/docs/authz" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition font-medium">
          <ArrowLeft className="w-4 h-4" /> Overview
        </Link>
        <Link to="/docs/authz/abac" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition font-medium">
          Attribute-Based Access Control (ABAC) <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
