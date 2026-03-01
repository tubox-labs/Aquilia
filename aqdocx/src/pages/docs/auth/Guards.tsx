import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Shield, Lock, Key, Layers } from 'lucide-react'
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
            Guards
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Guards enforce authentication and authorization policies before route handlers execute. Aquilia provides built-in guards for Bearer tokens, API keys, RBAC/ABAC, scopes, and roles — plus decorators for quick inline protection.
        </p>
      </div>

      {/* Guard Types */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Built-in Guard Classes</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {[
            { icon: <Lock className="w-5 h-5" />, title: 'AuthGuard', desc: 'Validates Bearer token from Authorization header. Supports optional mode (resolves identity if present, doesn\'t block).', color: '#3b82f6' },
            { icon: <Key className="w-5 h-5" />, title: 'ApiKeyGuard', desc: 'Validates X-API-Key header against credential store. Checks key hash, expiration, and required scopes.', color: '#f59e0b' },
            { icon: <Shield className="w-5 h-5" />, title: 'AuthzGuard', desc: 'Full authorization with resource_extractor, scope checks, role checks, and RBAC/ABAC policy evaluation.', color: '#ef4444' },
            { icon: <Shield className="w-5 h-5" />, title: 'ScopeGuard', desc: 'Checks that the authenticated identity\'s token has the required scopes.', color: '#22c55e' },
            { icon: <Shield className="w-5 h-5" />, title: 'RoleGuard', desc: 'Checks identity roles. Supports require_all mode (must have ALL roles vs ANY role).', color: '#8b5cf6' },
          ].map((g, i) => (
            <div key={i} className={boxClass}>
              <div className="flex items-center gap-2 mb-2" style={{ color: g.color }}>{g.icon}<span className="font-semibold text-sm font-mono">{g.title}</span></div>
              <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{g.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* AuthGuard */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>AuthGuard (Bearer Token)</h2>
        <CodeBlock language="python" filename="guards.py">{`from aquilia.auth.guards import AuthGuard

# Standard — blocks unauthenticated requests
guard = AuthGuard(
    token_manager=token_manager,
    identity_store=identity_store,
)

# Optional mode — resolves identity if present, never blocks
guard = AuthGuard(
    token_manager=token_manager,
    identity_store=identity_store,
    optional=True,  # request.identity may be None
)

# Guard checks:
# 1. Extract "Bearer <token>" from Authorization header
# 2. Validate token signature via token_manager
# 3. Resolve identity from token claims (sub)
# 4. Verify identity is ACTIVE
# 5. Inject identity into request context`}</CodeBlock>
      </section>

      {/* ApiKeyGuard */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>ApiKeyGuard</h2>
        <CodeBlock language="python" filename="API Key Guard">{`from aquilia.auth.guards import ApiKeyGuard

guard = ApiKeyGuard(
    credential_store=credential_store,
    identity_store=identity_store,
    required_scopes=["read:users"],  # optional scope check
)

# Guard checks:
# 1. Extract key from X-API-Key header
# 2. Hash key with SHA-256 → lookup in credential store
# 3. Check key expiration and revocation
# 4. Verify scopes if required_scopes specified
# 5. Resolve identity from key's identity_id`}</CodeBlock>
      </section>

      {/* AuthzGuard */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>AuthzGuard (Full Authorization)</h2>
        <CodeBlock language="python" filename="AuthzGuard">{`from aquilia.auth.guards import AuthzGuard

guard = AuthzGuard(
    token_manager=token_manager,
    identity_store=identity_store,
    authz_engine=authz_engine,
    resource_extractor=lambda req: req.path_params.get("id"),
    required_scopes=["orders:write"],
    required_roles=["admin"],
    policy_name="order_access",
)

# Guard performs full chain:
# 1. Authenticate (Bearer token)
# 2. Check scopes against token claims
# 3. Check roles against identity attributes
# 4. Extract resource from request
# 5. Evaluate RBAC/ABAC policy via authz_engine`}</CodeBlock>
      </section>

      {/* Decorators */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}><Layers className="w-5 h-5 text-cyan-500" />Guard Decorators</h2>
        <CodeBlock language="python" filename="Decorators">{`from aquilia.auth.guards import require_auth, require_scopes, require_roles

# @require_auth — must be authenticated
@require_auth
async def protected_handler(request):
    identity = request.identity
    return json({"user": identity.id})

# @require_scopes — check token scopes
@require_scopes("orders:read", "orders:write")
async def manage_orders(request):
    ...

# @require_roles — check identity roles
@require_roles("admin", "superadmin")
async def admin_panel(request):
    ...`}</CodeBlock>
      </section>

      {/* Controller Pipeline */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Controller Pipeline</h2>
        <CodeBlock language="python" filename="Controller Guards">{`from aquilia.controller import Controller, Get, Post, Delete
from aquilia.auth.guards import AuthGuard, ApiKeyGuard, AuthzGuard

class OrderController(Controller):
    prefix = "/api/orders"
    # Controller-level guard — applies to ALL routes
    pipeline = [AuthGuard(token_manager=tm, identity_store=ids)]

    @Get("/")
    async def list_orders(self, ctx):
        return ctx.json({"orders": [...]})

    @Post("/")
    async def create_order(self, ctx):
        # Additional route-level guard
        scope_guard = ScopeGuard(required_scopes=["orders:write"])
        await scope_guard.check(ctx)
        data = await ctx.request.json()
        return ctx.json({"created": True})

    @Delete("/{id}")
    async def delete_order(self, ctx, id: str):
        # Inline role check
        role_guard = RoleGuard(roles=["admin"], require_all=True)
        await role_guard.check(ctx)
        return ctx.json({"deleted": id})`}</CodeBlock>
        <div className={`mt-4 p-4 rounded-xl border-l-4 border-aquilia-500 ${isDark ? 'bg-aquilia-500/10' : 'bg-aquilia-50'}`}>
          <p className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <strong>Pipeline execution order:</strong> Controller pipeline runs first, then route-level guards. If any guard raises a Fault, execution stops and the fault response is sent.
          </p>
        </div>
      </section>

      {/* Tenant Isolation */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Tenant Isolation</h2>
        <CodeBlock language="python" filename="Tenant Guard">{`from aquilia.auth.guards import AuthzGuard

# Use AuthzGuard with tenant check via authz_engine
guard = AuthzGuard(
    token_manager=tm,
    identity_store=ids,
    authz_engine=authz_engine,
    resource_extractor=lambda req: req.path_params.get("tenant_id"),
)

# Or use the authz engine directly for tenant checks:
# authz_engine.check_tenant(identity, resource_tenant_id)
# → raises AUTHZ_004 (TenantMismatch) if identity.tenant_id != resource tenant`}</CodeBlock>
      </section>
    
      <NextSteps />
    </div>
  )
}