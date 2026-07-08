import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Shield, Layers, Cpu } from 'lucide-react'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'

export function AuthGuards() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4"><Shield className="w-4 h-4" />Security &amp; Auth</div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Guards &amp; Decorators
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia provides two separate guard modules: **Controller Decorators &amp; Guards** (`aquilia/auth/decorators.py`) for route handler level validation, and **Flow Pipeline Guards** (`aquilia/auth/guards.py`) for pipeline integration.
        </p>
      </div>

      {/* 1. Controller Decorators & Guards */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}><Layers className="w-5 h-5 text-blue-500" />1. Controller Decorators &amp; Guards</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          These decorators and guards are used directly in controller methods. They resolve identity/sessions from the active request context.
        </p>

        <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Decorators</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
          <div className={boxClass}>
            <span className="font-mono font-bold text-sm text-aquilia-500">@authenticated</span>
            <p className={`mt-2 text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Requires an authenticated identity. Can redirect browser requests if `login_url` is configured.
            </p>
          </div>
          <div className={boxClass}>
            <span className="font-mono font-bold text-sm text-aquilia-500">@require_identity</span>
            <p className={`mt-2 text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Validates specific roles, scopes, or custom attributes on the identity.
            </p>
          </div>
        </div>

        <CodeBlock language="python" filename="Controller Decorators">{`from aquilia.auth.decorators import authenticated, require_identity

@authenticated
async def get_profile(ctx, user: Identity):
    # user is automatically resolved and injected
    return {"user_id": user.id}

@authenticated(login_url="/login", redirect_if_html=True)
async def dashboard(ctx, session: Session):
    # Browser client gets redirected to /login?next=/dashboard on missing session
    return {"theme": session.get("theme")}

@require_identity(roles=["admin"], scopes=["users:write"])
async def delete_user(ctx, identity: Identity):
    ...`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-8 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Controller Guards</h3>
        <p className={`mb-4 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Guards are instances that implement a `check(identity, session)` method. They can be composed using the `@requires` decorator.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
          {[
            { title: 'AdminGuard', desc: 'Verifies the identity or session has the "admin" role.' },
            { title: 'VerifiedEmailGuard', desc: 'Checks if the email_verified attribute is True.' },
            { title: 'RoleGuard(*roles, require_all=False)', desc: 'Validates roles (any matching by default, or all).' },
            { title: 'ScopeGuard(*scopes, require_all=True)', desc: 'Validates OAuth scopes (all required by default).' },
          ].map((g, i) => (
            <div key={i} className={boxClass}>
              <span className="font-mono font-bold text-sm text-green-500">{g.title}</span>
              <p className={`mt-2 text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{g.desc}</p>
            </div>
          ))}
        </div>

        <CodeBlock language="python" filename="Controller Guards Composition">{`from aquilia.auth.decorators import requires, AdminGuard, VerifiedEmailGuard

@requires(AdminGuard(), VerifiedEmailGuard())
async def sensitive_panel(ctx):
    ...`}</CodeBlock>
      </section>

      {/* 2. Flow Pipeline Guards */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}><Cpu className="w-5 h-5 text-orange-500" />2. Flow Pipeline Guards</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Flow guards are pipeline nodes that execute on a `context` dictionary. They can automatically resolve the `AuthManager` or `AuthzEngine` from the context DI container if not passed explicitly.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
          {[
            { title: 'AuthGuard(auth_manager=None, optional=False)', desc: 'Extracts Bearer token from authorization header, validates it, and injects "identity" into the flow context.' },
            { title: 'ApiKeyGuard(auth_manager=None, required_scopes=None)', desc: 'Extracts API key from X-API-Key header and validates scopes.' },
            { title: 'AuthzGuard(...)', desc: 'Runs full scope, role, and ABAC/RBAC policy check using the AuthzEngine.' },
            { title: 'ScopeGuard(required_scopes)', desc: 'Asserts token_claims contains the required scopes.' },
            { title: 'RoleGuard(required_roles, require_all=False)', desc: 'Asserts token_claims contains the required roles.' },
          ].map((fg, i) => (
            <div key={i} className={boxClass}>
              <span className="font-mono font-bold text-xs text-orange-500">{fg.title}</span>
              <p className={`mt-2 text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{fg.desc}</p>
            </div>
          ))}
        </div>

        <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Flow Decorators</h3>
        <p className={`mb-4 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Shorthand decorators that run the Flow-based token parsing pipeline:
        </p>
        <CodeBlock language="python" filename="Flow Decorators">{`from aquilia.auth.guards import require_auth, require_scopes, require_roles

@require_auth(auth_manager)
@require_scopes("orders.read")
async def get_orders(request, identity: Identity):
    return {"orders": []}`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className="flex justify-between items-center mt-16 pt-8 border-t border-white/10">
        <Link to="/docs/auth/credentials" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition">
          Credentials
        </Link>
        <Link to="/docs/authz" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition">
          Authorization
        </Link>
      </div>
    
      <NextSteps />
    </div>
  )
}