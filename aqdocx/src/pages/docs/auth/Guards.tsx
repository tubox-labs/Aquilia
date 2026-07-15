import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Shield, Layers } from 'lucide-react'
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
          Aquilia provides a unified, context-first endpoint protection suite consisting of **Route Decorators** (<code className="text-aquilia-500 font-mono text-sm">aquilia/auth/decorators.py</code>) and composable **Stateless Guards** (<code className="text-aquilia-500 font-mono text-sm">aquilia/auth/guards.py</code>).
        </p>
      </div>

      {/* 1. Controller Decorators */}
      <section className="space-y-6">
        <h2 className={`text-2.5xl font-bold tracking-tight flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-6 h-6 text-blue-500" />
          <span>Controller Route Decorators</span>
        </h2>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Decorators run inside controller endpoints, resolving identities and session structures from active request scopes, injecting resolved parameters into the handler when they are requested.
        </p>

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
                <DocTerm id="auth.roles_required">@roles_required</DocTerm>
              </span>
              <p className={`text-xs leading-normal ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                Asserts specific roles (with support for inheritance via <DocTerm id="auth.permission_engine">PermissionEngine</DocTerm>) on the active identity.
              </p>
            </div>
          </div>

          <div className="flex gap-4 p-4 rounded-xl hover:bg-aquilia-500/5 transition-all duration-300 group">
            <div className="mt-1.5 group-hover:scale-110 transition-all duration-300" style={{ color: '#eab308' }}>
              <Shield className="w-5 h-5" />
            </div>
            <div className="space-y-1">
              <span className="font-bold text-sm font-mono block text-aquilia-500">
                <DocTerm id="auth.scopes_required">@scopes_required</DocTerm>
              </span>
              <p className={`text-xs leading-normal ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                Asserts specific OAuth scope capabilities on the identity.
              </p>
            </div>
          </div>

          <div className="flex gap-4 p-4 rounded-xl hover:bg-aquilia-500/5 transition-all duration-300 group">
            <div className="mt-1.5 group-hover:scale-110 transition-all duration-300" style={{ color: '#a855f7' }}>
              <Shield className="w-5 h-5" />
            </div>
            <div className="space-y-1">
              <span className="font-bold text-sm font-mono block text-aquilia-500">
                <DocTerm id="auth.optional_auth">@optional_auth</DocTerm>
              </span>
              <p className={`text-xs leading-normal ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                Resolves the identity if present but does not block anonymous clients. Injects identity or session into handler.
              </p>
            </div>
          </div>
        </div>

        <CodeBlock language="python" filename="Controller Decorators">{`from aquilia.auth.decorators import authenticated, roles_required, scopes_required, optional_auth

@authenticated
async def get_profile(ctx, user: Identity):
    # Principal is automatically resolved and injected
    return {"user_id": user.id}

@authenticated(login_url="/login", redirect_if_html=True)
async def dashboard(ctx, session: Session):
    # Web browsers get redirected to /login?next=/dashboard
    return {"theme": session.get("theme")}

@roles_required("admin")
async def delete_user(ctx, identity: Identity):
    ...

@scopes_required("reports:read", require_all=True)
async def fetch_reports(ctx):
    ...
`}</CodeBlock>
      </section>

      {/* 2. Composable Stateless Guards */}
      <section className="space-y-6">
        <h2 className={`text-2.5xl font-bold tracking-tight flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Shield className="w-6 h-6 text-green-500" />
          <span>Composable Stateless Guards</span>
        </h2>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Guards are stateless protocol classes implementing a <code className="text-aquilia-500 font-mono text-xs">check(ctx)</code> method. Multiple guards can be composed on any handler or pipeline using the <code className="text-aquilia-500 font-mono text-xs">@requires</code> decorator.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {[
            { title: 'AuthGuard(auth_manager=None, optional=False)', desc: 'Asserts authenticated identity. Supports proactive Bearer token extraction and verification.', termId: 'auth.auth_guard' },
            { title: 'RoleGuard(*roles, engine=None, require_all=True)', desc: 'Asserts active identity holds specified roles. Supports inheritance via PermissionEngine.', termId: 'auth.role_guard' },
            { title: 'ScopeGuard(*scopes, require_all=True)', desc: 'Asserts active identity holds required OAuth scopes.', termId: 'auth.scope_guard' },
            { title: 'PolicyGuard(key, engine, resource=None)', desc: 'Evaluates custom authorization policy defined in a PermissionEngine.', termId: 'auth.policy_guard' },
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

        <CodeBlock language="python" filename="Controller Guards Composition">{`from aquilia.auth.guards import requires, AuthGuard, RoleGuard, PolicyGuard
from aquilia.auth.permissions import PermissionEngine

permissions = PermissionEngine()
permissions.register_policy("is_owner", lambda identity, resource: identity.id == resource.owner_id)

class DocumentController(Controller):

    @requires(AuthGuard, RoleGuard("editor"))
    async def edit_document(self, ctx):
        ...

    @requires(AuthGuard(), PolicyGuard("is_owner", engine=permissions))
    async def delete_document(self, ctx):
        ...
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