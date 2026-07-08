import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Shield, Layers, Cpu } from 'lucide-react'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function AuthGuards() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto space-y-16">
      {/* Header Section */}
      <div className="space-y-4">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium tracking-wide">
          <Shield className="w-4 h-4" />
          <span>Security &amp; Auth</span>
        </div>
        <h1 className={`text-4xl font-extrabold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="gradient-text font-mono relative group inline-block">
            Guards &amp; Decorators
            <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia provides two separate guard modules: **Controller Decorators &amp; Guards** (<code className="text-aquilia-500 font-mono text-sm">aquilia/auth/decorators.py</code>) for route handler validations, and **Flow Pipeline Guards** (<code className="text-aquilia-500 font-mono text-sm">aquilia/auth/guards.py</code>) for graph-based pipelines.
        </p>
      </div>

      {/* 1. Controller Decorators & Guards */}
      <section className="space-y-6">
        <h2 className={`text-2.5xl font-bold tracking-tight flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-6 h-6 text-blue-500" />
          <span>Controller Decorators &amp; Guards</span>
        </h2>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          These decorators and guards run inside controller endpoints, resolving identities and session structures from active request scopes.
        </p>

        <h3 className={`text-lg font-bold pt-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Built-in Decorators
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div className="flex gap-4 p-4 rounded-xl hover:bg-aquilia-500/5 transition-all duration-300 group">
            <div className="mt-1.5 group-hover:scale-110 transition-all duration-300" style={{ color: '#3b82f6' }}>
              <Shield className="w-5 h-5" />
            </div>
            <div className="space-y-1">
              <span className="font-bold text-sm font-mono block text-aquilia-500">
                <DocTerm id="auth.authenticated">@authenticated</DocTerm>
              </span>
              <p className={`text-xs leading-normal ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                Blocks requests lacking active authenticated identities. Can redirect browser clients if a login URL is configured.
              </p>
            </div>
          </div>

          <div className="flex gap-4 p-4 rounded-xl hover:bg-aquilia-500/5 transition-all duration-300 group">
            <div className="mt-1.5 group-hover:scale-110 transition-all duration-300" style={{ color: '#22c55e' }}>
              <Shield className="w-5 h-5" />
            </div>
            <div className="space-y-1">
              <span className="font-bold text-sm font-mono block text-aquilia-500">
                <DocTerm id="auth.require_identity">@require_identity</DocTerm>
              </span>
              <p className={`text-xs leading-normal ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                Asserts specific roles, scope capabilities, or custom attributes on the identity before executing the handler.
              </p>
            </div>
          </div>
        </div>

        <CodeBlock language="python" filename="Controller Decorators">{`from aquilia.auth.decorators import authenticated, require_identity

@authenticated
async def get_profile(ctx, user: Identity):
    # Principal is automatically resolved and injected
    return {"user_id": user.id}

@authenticated(login_url="/login", redirect_if_html=True)
async def dashboard(ctx, session: Session):
    # Web browsers get redirected to /login?next=/dashboard
    return {"theme": session.get("theme")}

@require_identity(roles=["admin"], scopes=["users:write"])
async def delete_user(ctx, identity: Identity):
    ...
`}</CodeBlock>

        <h3 className={`text-lg font-bold pt-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Controller Class Guards
        </h3>
        <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Class-based checks implementing a <code className="text-aquilia-500 font-mono text-xs">check(identity, session)</code> method. Multiple guards can be composed using the `@requires` wrapper.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {[
            { title: 'AdminGuard', desc: 'Validates that the authenticated identity or session possesses the admin role.', termId: 'auth.admin_guard' },
            { title: 'VerifiedEmailGuard', desc: 'Validates that the email_verified flag matches True.', termId: 'auth.auth_guard' },
            { title: 'RoleGuard(*roles, require_all=False)', desc: 'Validates roles (matches any role by default, or all).', termId: 'auth.role_guard' },
            { title: 'ScopeGuard(*scopes, require_all=True)', desc: 'Validates OAuth scopes (all scopes are required by default).', termId: 'auth.scope_guard' },
          ].map((g, i) => (
            <div key={i} className="flex gap-4 p-4 rounded-xl hover:bg-aquilia-500/5 transition-all duration-300 group">
              <div className="mt-1.5 group-hover:scale-110 transition-all duration-300" style={{ color: '#22c55e' }}>
                <Shield className="w-5 h-5" />
              </div>
              <div className="space-y-1">
                <span className="font-bold text-sm font-mono block text-green-500">
                  <DocTerm id={g.termId}>{g.title}</DocTerm>
                </span>
                <p className={`text-xs leading-normal ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  {g.desc}
                </p>
              </div>
            </div>
          ))}
        </div>

        <CodeBlock language="python" filename="Controller Guards Composition">{`from aquilia.auth.decorators import requires, AdminGuard, VerifiedEmailGuard

@requires(AdminGuard(), VerifiedEmailGuard())
async def sensitive_panel(ctx):
    ...
`}</CodeBlock>
      </section>

      {/* 2. Flow Pipeline Guards */}
      <section className="space-y-6">
        <h2 className={`text-2.5xl font-bold tracking-tight flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Cpu className="w-6 h-6 text-orange-500" />
          <span>Flow Pipeline Guards</span>
        </h2>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Flow guards are graph-node instances executing constraints on pipeline context inputs, dynamically resolving stores from DI containers.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {[
            { title: 'AuthGuard(auth_manager=None, optional=False)', desc: 'Extracts Bearer token from authorization header, validates it, and injects "identity" into the flow context.' },
            { title: 'ApiKeyGuard(auth_manager=None, required_scopes=None)', desc: 'Extracts API key from X-API-Key header and validates scopes.' },
            { title: 'AuthzGuard(...)', desc: 'Runs full scope, role, and ABAC/RBAC policy check using the AuthzEngine.' },
            { title: 'ScopeGuard(required_scopes)', desc: 'Asserts token_claims contains the required scopes.' },
            { title: 'RoleGuard(required_roles, require_all=False)', desc: 'Asserts token_claims contains the required roles.' },
          ].map((fg, i) => (
            <div key={i} className="flex gap-4 p-4 rounded-xl hover:bg-aquilia-500/5 transition-all duration-300 group">
              <div className="mt-1.5 group-hover:scale-110 transition-all duration-300" style={{ color: '#f97316' }}>
                <Shield className="w-5 h-5" />
              </div>
              <div className="space-y-1">
                <span className="font-bold text-xs font-mono block text-orange-500">
                  {fg.title}
                </span>
                <p className={`text-xs leading-normal ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  {fg.desc}
                </p>
              </div>
            </div>
          ))}
        </div>

        <h3 className={`text-lg font-bold pt-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Flow Shorthands
        </h3>
        <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Shorthand decorators that run the flow-based token parsing pipeline:
        </p>
        <CodeBlock language="python" filename="Flow Decorators">{`from aquilia.auth.guards import require_auth, require_scopes, require_roles

@require_auth(auth_manager)
@require_scopes("orders.read")
async def get_orders(request, identity: Identity):
    return {"orders": []}
`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className="flex justify-between items-center mt-16 pt-8 border-t border-zinc-800">
        <Link to="/docs/auth/credentials" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition font-mono text-sm">
          &larr; Credentials
        </Link>
        <Link to="/docs/authz" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition font-mono text-sm">
          Authorization &rarr;
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}