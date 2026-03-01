import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Puzzle, Layers, Shield, Network, Cpu, Users } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function AuthIntegration() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4"><Puzzle className="w-4 h-4" />Security &amp; Auth</div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Integration &amp; Middleware
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">aquilia.auth.integration</code> package wires auth into Aquilia's DI container, middleware pipeline, session system, and flow graph — giving you zero-config auth with full extensibility.
        </p>
      </div>

      {/* Integration Overview */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Integration Components</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {[
            { icon: <Cpu className="w-5 h-5" />, title: 'DI Providers', desc: 'Auto-registers all auth services in the DI container with @service(scope="app"). Zero-config setup.', color: '#22c55e' },
            { icon: <Layers className="w-5 h-5" />, title: 'Auth Middleware', desc: 'Six-phase request pipeline — resolves sessions, extracts auth, checks requirements, injects identity.', color: '#3b82f6' },
            { icon: <Network className="w-5 h-5" />, title: 'Flow Guards', desc: 'Auth requirements as composable flow-graph nodes. Works with Aquilia\'s flow engine.', color: '#f59e0b' },
            { icon: <Users className="w-5 h-5" />, title: 'Session Bridge', desc: 'AuthPrincipal extends SessionPrincipal with roles, scopes, and tenant_id. Pre-built session policies.', color: '#8b5cf6' },
          ].map((s, i) => (
            <div key={i} className={boxClass}>
              <div className="flex items-center gap-2 mb-2" style={{ color: s.color }}>{s.icon}<span className="font-semibold text-sm">{s.title}</span></div>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* DI Providers */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}><Cpu className="w-5 h-5 text-green-500" />DI Providers</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Import <code className="text-aquilia-500">aquilia.auth.integration.di_providers</code> and all auth services auto-register with <code className="text-aquilia-500">@service(scope="app")</code>. Each provider constructs its service with sensible defaults.
        </p>
        <CodeBlock language="python" filename="Registered Providers">{`from aquilia.auth.integration.di_providers import *

# Provider                      → Provides
# ─────────────────────────────────────────
# PasswordHasherProvider         → PasswordHasher  (Argon2id)
# KeyRingProvider                → KeyRing          (auto-generates RS256 key)
# TokenManagerProvider           → TokenManager     (1h access, 7d refresh)
# RateLimiterProvider            → RateLimiter      (5 attempts, 15min lockout)
# MemoryIdentityStoreProvider    → IdentityStore    (in-memory)
# MemoryCredentialStoreProvider  → CredentialStore   (in-memory)
# MemoryTokenStoreProvider       → TokenStore        (in-memory)
# MemoryOAuthClientStoreProvider → OAuthClientStore  (in-memory)
# MemoryAuthCodeStoreProvider    → AuthorizationCodeStore (in-memory)
# MemoryDeviceCodeStoreProvider  → DeviceCodeStore   (in-memory)
# AuthManagerProvider            → AuthManager       (full auth pipeline)
# MFAManagerProvider             → MFAManager        (TOTP + backup codes)
# OAuth2ManagerProvider          → OAuth2Manager     (all 4 grant types)
# AuthzEngineProvider            → AuthzEngine       (RBAC + ABAC + scopes)
# SessionEngineProvider          → SessionManager    (auth sessions)
# SessionAuthBridgeProvider      → SessionAuthBridge (session ↔ auth)`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-8 mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Customizing Providers</h3>
        <CodeBlock language="python" filename="Custom DI">{`from aquilia.di import Container

container = Container()

# Override any provider with your own implementation
container.register(IdentityStore, MyDatabaseIdentityStore)
container.register(TokenStore, RedisTokenStore(redis_client))

# Other providers auto-resolve from the container
# AuthManager will receive YOUR IdentityStore + TokenStore`}</CodeBlock>
      </section>

      {/* Auth Middleware */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}><Layers className="w-5 h-5 text-blue-500" />Auth Middleware</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <code className="text-aquilia-500">AquilAuthMiddleware</code> runs a six-phase pipeline on every request:
        </p>

        {/* Pipeline SVG */}
        <div className={`${boxClass} mb-6 flex justify-center`}>
          <svg viewBox="0 0 700 320" className="w-full max-w-2xl" fill="none" xmlns="http://www.w3.org/2000/svg">
            {[
              { y: 10, label: '1. Resolve Session', desc: 'Load session from cookie/header', color: '#8b5cf6' },
              { y: 60, label: '2. Extract Auth', desc: 'Bearer token → validate → identity', color: '#3b82f6' },
              { y: 110, label: '3. Session Fallback', desc: 'No token? Use session identity', color: '#22c55e' },
              { y: 160, label: '4. Check Requirements', desc: 'Route requires auth? Block if missing', color: '#f59e0b' },
              { y: 210, label: '5. Inject Identity', desc: 'Bind identity to DI + request', color: '#ef4444' },
              { y: 260, label: '6. Execute Handler', desc: 'Run route → commit session', color: '#06b6d4' },
            ].map((step, i) => (
              <g key={i}>
                <rect x="20" y={step.y} width="660" height="40" rx="8" fill={step.color} fillOpacity="0.15" stroke={step.color} strokeWidth="1.5" />
                <text x="40" y={step.y + 26} fill={step.color} fontSize="14" fontWeight="bold" fontFamily="monospace">{step.label}</text>
                <text x="340" y={step.y + 26} fill={isDark ? '#9ca3af' : '#6b7280'} fontSize="12" fontFamily="monospace">{step.desc}</text>
              </g>
            ))}
          </svg>
        </div>

        <CodeBlock language="python" filename="Middleware Usage">{`from aquilia.auth.integration.middleware import (
    AquilAuthMiddleware,
    OptionalAuthMiddleware,
    SessionMiddleware,
)

app = Aquilia()

# Full auth middleware — enforces token/session auth
app.use(AquilAuthMiddleware(
    token_manager=token_manager,
    identity_store=identity_store,
    session_manager=session_manager,
    require_auth_default=False,   # opt-in per route
))

# Optional auth — resolves identity if present, never blocks
app.use(OptionalAuthMiddleware(
    token_manager=token_manager,
    identity_store=identity_store,
))

# Session-only — no token resolution, just session
app.use(SessionMiddleware(session_manager=session_manager))`}</CodeBlock>
      </section>

      {/* Flow Guards */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}><Network className="w-5 h-5 text-amber-500" />Flow Guards</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Flow guards express auth requirements as composable <code className="text-aquilia-500">FlowNode</code>s in Aquilia's flow graph. Each guard provides an <code className="text-aquilia-500">as_flow_node()</code> method.
        </p>
        <CodeBlock language="python" filename="Flow Guard Types">{`from aquilia.auth.integration.flow_guards import (
    # Guard classes
    RequireAuthGuard,           # any authenticated identity
    RequireSessionAuthGuard,    # auth via session only
    RequireTokenAuthGuard,      # auth via Bearer token only
    RequireApiKeyGuard,         # auth via API key
    RequireScopesGuard,         # check scopes (any or all)
    RequireRolesGuard,          # check roles  (any or all)
    RequirePermissionGuard,     # RBAC permission on resource
    RequirePolicyGuard,         # full ABAC/RBAC policy eval
    
    # Flow factories — return FlowNode directly
    require_auth,               # require_auth()
    require_scopes,             # require_scopes("read", "write")
    require_roles,              # require_roles("admin")
    require_permission,         # require_permission("orders", "delete")
)`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-8 mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Composing in a Flow</h3>
        <CodeBlock language="python" filename="Flow Composition">{`from aquilia.flow import Flow
from aquilia.auth.integration.flow_guards import (
    require_auth, require_scopes, require_roles,
)

# Sequential guards — all must pass
admin_flow = (
    Flow("admin_pipeline")
    .then(require_auth())
    .then(require_roles("admin", "superadmin"))
    .then(require_scopes("admin:write"))
    .then(handler_node)
)

# Scopes with require_all
api_flow = (
    Flow("api_pipeline")
    .then(require_auth())
    .then(RequireScopesGuard(
        scopes=["read", "write"],
        require_all=True,          # must have BOTH scopes
    ).as_flow_node())
    .then(handler_node)
)`}</CodeBlock>
      </section>

      {/* Controller Guards */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}><Shield className="w-5 h-5 text-red-500" />Controller Guards</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Use <code className="text-aquilia-500">ControllerGuardAdapter</code> to wrap any flow guard for use in a controller pipeline, or use the factory functions for a decorator-style API.
        </p>
        <CodeBlock language="python" filename="Controller Integration">{`from aquilia.auth.integration.flow_guards import (
    ControllerGuardAdapter,
    controller_require_auth,
    controller_require_scopes,
    controller_require_roles,
    controller_require_permission,
)

# Factory functions — return a guard ready for controller.use()
class OrderController(Controller):
    def __init__(self):
        super().__init__("/orders")
        self.use(controller_require_auth())
        self.use(controller_require_scopes("orders:read"))

    @get("/")
    async def list_orders(self, request):
        return json({"orders": [...]})

    @delete("/:id")
    async def delete_order(self, request, id: str):
        # Additional guard for this route only
        guard = controller_require_roles("admin")
        await guard.check(request)
        return json({"deleted": id})

# Or wrap any FlowGuard directly:
adapter = ControllerGuardAdapter.for_controller(
    RequirePolicyGuard(
        authz_engine=authz_engine,
        resource_type="orders",
        action="manage",
    )
)`}</CodeBlock>
      </section>

      {/* AuthPrincipal & Session Bridge */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}><Users className="w-5 h-5 text-purple-500" />AuthPrincipal &amp; Session Bridge</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <code className="text-aquilia-500">AuthPrincipal</code> extends <code className="text-aquilia-500">SessionPrincipal</code> with auth-specific data — roles, scopes, tenant_id, MFA verification status.
        </p>
        <CodeBlock language="python" filename="AuthPrincipal">{`from aquilia.auth.integration.aquila_sessions import (
    AuthPrincipal,
    bind_identity,
    bind_token_claims,
    get_identity_id,
    get_tenant_id,
    get_roles,
    get_scopes,
    is_mfa_verified,
    set_mfa_verified,
)

# Bind identity to session (called by middleware)
bind_identity(session, identity)   # sets identity_id, roles, tenant_id
bind_token_claims(session, claims) # sets scopes, sid

# Read from session (in handler)
user_id   = get_identity_id(session)   # "user_42"
tenant    = get_tenant_id(session)     # "org_1"
roles     = get_roles(session)         # ["admin", "editor"]
scopes    = get_scopes(session)        # ["read", "write"]
mfa_ok    = is_mfa_verified(session)   # True/False
set_mfa_verified(session, True)        # after MFA step`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-8 mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Preconfigured Session Policies</h3>
        <CodeBlock language="python" filename="Session Policies">{`from aquilia.auth.integration.aquila_sessions import (
    user_session_policy,     # browser-based users
    api_session_policy,      # API/backend services
    device_session_policy,   # IoT/long-lived devices
)

# user_session_policy:
#   TTL: 7 days
#   Transport: cookie (HttpOnly, Secure, SameSite=Lax)
#   ID rotation: on privilege escalation
#   Activity tracking: enabled

# api_session_policy:
#   TTL: 1 hour
#   Transport: header (X-Session-Token)
#   ID rotation: disabled
#   Activity tracking: disabled

# device_session_policy:
#   TTL: 90 days
#   Transport: header (X-Device-Session)
#   ID rotation: on privilege escalation
#   Activity tracking: enabled`}</CodeBlock>
      </section>

      {/* Session Manager */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Auth Session Manager</h2>
        <CodeBlock language="python" filename="SessionManager">{`from aquilia.auth.integration.sessions import (
    AuthSession, MemorySessionStore, SessionManager,
)

store = MemorySessionStore()
manager = SessionManager(
    session_store=store,
    max_sessions_per_identity=5,  # limit concurrent sessions
)

# Create session for authenticated identity
session = await manager.create(
    identity_id="user_42",
    metadata={"ip": "1.2.3.4", "ua": "Mozilla/5.0"},
)

# Get session (auto-checks expiry, updates last_activity)
session = await manager.get(session.session_id)

# Extend session (set new expiry)
await manager.extend(session.session_id, timedelta(hours=4))

# Rotate session ID (after privilege escalation / MFA)
new_session = await manager.rotate(session.session_id)

# Logout — single session
await manager.delete(session.session_id)

# Logout everywhere — all sessions for an identity
await manager.delete_all(identity_id="user_42")`}</CodeBlock>
      </section>

      {/* Full Wiring Example */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Full Wiring Example</h2>
        <CodeBlock language="python" filename="Complete Setup">{`from aquilia import Aquilia
from aquilia.auth.integration.di_providers import *   # auto-registers all
from aquilia.auth.integration.middleware import AquilAuthMiddleware
from aquilia.auth.integration.flow_guards import (
    require_auth, require_scopes,
)

app = Aquilia()

# DI providers auto-registered — resolve from container
token_manager = app.container.resolve(TokenManager)
identity_store = app.container.resolve(IdentityStore)
session_manager = app.container.resolve(SessionManager)

# Attach auth middleware
app.use(AquilAuthMiddleware(
    token_manager=token_manager,
    identity_store=identity_store,
    session_manager=session_manager,
))

# Public route
@app.get("/health")
async def health(request):
    return json({"status": "ok"})

# Protected route via flow
@app.get("/api/orders")
@require_auth()
@require_scopes("orders:read")
async def list_orders(request):
    identity = request.identity
    return json({"user": identity.id})`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
