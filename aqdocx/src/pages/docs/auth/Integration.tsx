import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Puzzle, Layers, Network, Cpu, Users } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function AuthIntegration() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto space-y-16">
      {/* Header Section */}
      <div className="space-y-4">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium tracking-wide">
          <Puzzle className="w-4 h-4" />
          <span>Security &amp; Auth</span>
        </div>
        <h1 className={`text-4xl font-extrabold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="gradient-text font-mono relative group inline-block">
            Integration &amp; Middleware
            <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500 font-mono text-sm">aquilia.auth.integration</code> package wires authentication seamlessly into Aquilia's dependency injection container, request-response middleware pipelines, session subsystems, and flow graphs.
        </p>
      </div>

      {/* Integration Overview */}
      <section className="space-y-6">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Integration Components
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {[
            { icon: <Cpu className="w-5 h-5" />, title: 'DI Providers', desc: 'Registers all auth services in the DI container with @service(scope="app") scopes. Zero configuration required.', color: '#22c55e' },
            { icon: <Layers className="w-5 h-5" />, title: 'Auth Middleware', desc: 'Runs a robust 6-phase pipeline that resolves sessions, validates JWT Bearer tokens, and registers the active identity.', color: '#3b82f6' },
            { icon: <Network className="w-5 h-5" />, title: 'Flow Guards', desc: 'Expresses authorization checks as composable nodes in Aquilia\'s pipeline graphs.', color: '#f59e0b' },
            { icon: <Users className="w-5 h-5" />, title: 'Session Bridge', desc: 'Extends default SessionPrincipal metadata to include active roles, token scopes, and tenant bindings.', color: '#8b5cf6' },
          ].map((s, i) => (
            <div key={i} className="flex gap-4 p-4 rounded-xl hover:bg-aquilia-500/5 transition-all duration-300 group">
              <div className="mt-1.5 group-hover:scale-110 transition-all duration-300" style={{ color: s.color }}>
                {s.icon}
              </div>
              <div className="space-y-1">
                <span className="font-bold text-sm font-mono block" style={{ color: s.color }}>
                  {s.title}
                </span>
                <p className={`text-xs leading-normal ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  {s.desc}
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* DI Providers */}
      <section className="space-y-4">
        <h2 className={`text-2.5xl font-bold tracking-tight flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Cpu className="w-6 h-6 text-green-500" />
          <span>DI Providers</span>
        </h2>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Importing <code className="text-aquilia-500 font-mono text-xs">aquilia.auth.integration.di_providers</code> exposes all auth services to the DI registry under <code className="text-aquilia-500 font-mono text-xs">@service(scope="app")</code>.
        </p>
        <CodeBlock language="python" filename="Registered Providers">{`from aquilia.auth.integration.di_providers import *

# Provider                      → Provides
# ─────────────────────────────────────────
# PasswordHasherProvider         → PasswordHasher  (Argon2id)
# KeyRingProvider                → KeyRing          (auto-generates RS256 key)
# TokenManagerProvider           → TokenManager     (15m access, 30d refresh)
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
# SessionEngineProvider          → SessionEngine     (auth sessions)
# SessionAuthBridgeProvider      → SessionAuthBridge (session ↔ auth)`}</CodeBlock>

        <h3 className={`text-lg font-bold pt-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Customizing Providers
        </h3>
        <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Override standard providers in the container context. Dependent services like <DocTerm id="auth.auth_manager">AuthManager</DocTerm> resolve overrides automatically.
        </p>
        <CodeBlock language="python" filename="Custom DI Wiring">{`from aquilia.di import Container

container = Container()

# Register custom database/cache storage implementations
container.register(IdentityStore, MyDatabaseIdentityStore)
container.register(TokenStore, RedisTokenStore(redis_client))

# Other default providers dynamically resolve with the overrides
`}</CodeBlock>
      </section>

      {/* Auth Middleware */}
      <section className="space-y-6">
        <h2 className={`text-2.5xl font-bold tracking-tight flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-6 h-6 text-blue-500" />
          <span>Auth Middleware Pipeline</span>
        </h2>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <DocTerm id="auth.aquil_auth_middleware">AquilAuthMiddleware</DocTerm> performs request authentication sequentially in 6 structured phases:
        </p>

        {/* Pipeline SVG */}
        <div className="flex justify-center py-4">
          <svg viewBox="0 0 700 320" className="w-full max-w-2xl h-auto" fill="none" xmlns="http://www.w3.org/2000/svg">
            {[
              { y: 10, label: '1. Resolve Session', desc: 'Resolve SessionEngine cookie or header', color: '#8b5cf6' },
              { y: 60, label: '2. Extract Auth', desc: 'Parse Authorization Bearer header into active token', color: '#3b82f6' },
              { y: 110, label: '3. Session Fallback', desc: 'Retrieve principal from active user session', color: '#22c55e' },
              { y: 160, label: '4. Check Requirements', desc: 'Halt requests if endpoint authentication is required', color: '#f59e0b' },
              { y: 210, label: '5. Inject Identity', desc: 'Register Identity in request-scoped DI container', color: '#ef4444' },
              { y: 260, label: '6. Execute Handler', desc: 'Process endpoint route and commit session updates', color: '#06b6d4' },
            ].map((step, i) => (
              <g key={i}>
                <rect x="20" y={step.y} width="660" height="40" rx="8" fill={step.color + '0c'} stroke={step.color} strokeWidth="1.5" />
                <text x="40" y={step.y + 25} fill={step.color} fontSize="13" fontWeight="bold" fontFamily="monospace">{step.label}</text>
                <text x="320" y={step.y + 25} fill={isDark ? '#a1a1aa' : '#52525b'} fontSize="11" fontFamily="sans-serif">{step.desc}</text>
              </g>
            ))}
          </svg>
        </div>

        <CodeBlock language="python" filename="Middleware Setup">{`from aquilia.auth.integration.middleware import (
    AquilAuthMiddleware,
    OptionalAuthMiddleware,
    SessionMiddleware,
)

app = Aquilia()

# Main authentication middleware
app.use(AquilAuthMiddleware(
    session_engine=session_engine,
    auth_manager=auth_manager,
    require_auth=False,   # Opt-in manually using decorators
))

# Optional Auth — resolves identities, but doesn't block anonymous clients
app.use(OptionalAuthMiddleware(
    session_engine=session_engine,
    auth_manager=auth_manager,
))

# Sessions Only — manages cookies/data context without auth evaluations
app.use(SessionMiddleware(session_engine=session_engine))
`}</CodeBlock>
      </section>

      {/* Flow Guards */}
      <section className="space-y-4">
        <h2 className={`text-2.5xl font-bold tracking-tight flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Network className="w-6 h-6 text-amber-500" />
          <span>Flow Guards</span>
        </h2>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Compose check constraints visually inside Aquilia flow pipelines using specialized Node implementations.
        </p>
        <CodeBlock language="python" filename="Flow Guard Implementations">{`from aquilia.auth.integration.flow_guards import (
    RequireAuthGuard,           # Verify authenticated identity presence
    RequireSessionAuthGuard,    # Assert session authentication state
    RequireTokenAuthGuard,      # Assert JWT bearer token presence
    RequireApiKeyGuard,         # Verify valid API key credentials
    RequireScopesGuard,         # Verify scopes (any or require_all)
    RequireRolesGuard,          # Verify roles (any or require_all)
    RequirePolicyGuard,         # Execute ABAC/RBAC Policy validation
)
`}</CodeBlock>

        <h3 className={`text-lg font-bold pt-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Flow Graph Assembly
        </h3>
        <CodeBlock language="python" filename="Graph Integration">{`from aquilia.flow import Flow
from aquilia.auth.integration.flow_guards import require_auth, require_roles

admin_flow = (
    Flow("admin_pipeline")
    .then(require_auth())
    .then(require_roles("admin", "superadmin"))
    .then(execute_admin_logic_node)
)
`}</CodeBlock>
      </section>

      {/* AuthPrincipal & Session Bridge */}
      <section className="space-y-4">
        <h2 className={`text-2.5xl font-bold tracking-tight flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Users className="w-6 h-6 text-purple-500" />
          <span>AuthPrincipal &amp; Session Bridge</span>
        </h2>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Extract user parameters, roles, and scope permissions dynamically from current session contexts:
        </p>
        <CodeBlock language="python" filename="Session Binding APIs">{`from aquilia.auth.integration.aquila_sessions import (
    bind_identity,
    bind_token_claims,
    get_identity_id,
    get_roles,
    get_scopes,
)

# Set bindings (executed during request intercept)
bind_identity(session, identity)
bind_token_claims(session, claims)

# Resolve attributes inside handler
user_id = get_identity_id(session)
roles = get_roles(session)
scopes = get_scopes(session)
`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
