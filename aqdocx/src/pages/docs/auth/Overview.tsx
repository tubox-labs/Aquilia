import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Shield, Lock, Key, Fingerprint, Database, Layers } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function AuthOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto space-y-16">
      {/* Header Section */}
      <div className="space-y-4">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium tracking-wide">
          <Shield className="w-4 h-4" />
          <span>Security &amp; Authentication</span>
        </div>
        <h1 className={`text-4xl font-extrabold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="gradient-text font-mono relative group inline-block">
            AquilAuth
            <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
          {' '}— Enterprise-Grade Security
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia's authentication architecture is built on three pillars:{' '}
          <DocTerm id="auth.identity">Identity</DocTerm> (the principal),{' '}
          <DocTerm id="auth.password_credential">PasswordCredential</DocTerm> (the proof of identity), and{' '}
          <DocTerm id="auth.auth_guard">AuthGuard</DocTerm> (policy enforcement). It is async-first, deeply integrated with the dependency injection system, and provides zero-config setups for both API tokens and browser sessions.
        </p>
      </div>

      {/* Architecture Section */}
      <section className="space-y-6">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Authentication Pipeline
        </h2>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          When a request enters the application, it flows through a unified middleware chain that automatically parses authentication credentials, resolves sessions, and loads the active identity.
        </p>
        <div className="flex justify-center py-6">
          <svg viewBox="0 0 660 200" className="w-full max-w-2xl h-auto" fill="none" xmlns="http://www.w3.org/2000/svg">
            {[
              { x: 30, w: 120, label: 'Request', sub: 'Authorization header', color: '#3b82f6' },
              { x: 170, w: 120, label: 'Middleware', sub: '6-phase pipeline', color: '#f59e0b' },
              { x: 310, w: 120, label: 'Identity', sub: 'Resolve principal', color: '#22c55e' },
              { x: 450, w: 100, label: 'Guard', sub: 'Check policy', color: '#ef4444' },
              { x: 570, w: 70, label: 'Handler', sub: '', color: '#8b5cf6' },
            ].map((b, i) => (
              <g key={i}>
                <rect x={b.x} y="40" width={b.w} height="55" rx="12" fill={b.color + '0c'} stroke={b.color} strokeWidth="1.5" />
                <text x={b.x + b.w / 2} y="63" textAnchor="middle" fill={b.color} fontSize="13" fontWeight="700" fontFamily="monospace">{b.label}</text>
                {b.sub && <text x={b.x + b.w / 2} y="80" textAnchor="middle" fill={isDark ? '#888888' : '#64748b'} fontSize="9" fontFamily="sans-serif">{b.sub}</text>}
                {i < 4 && <line x1={b.x + b.w} y1={67} x2={b.x + b.w + 20} y2={67} stroke={isDark ? '#3f3f46' : '#d4d4d8'} strokeWidth="1.5" markerEnd="url(#authArrow)" />}
              </g>
            ))}

            {/* Credential types */}
            <text x="330" y="130" textAnchor="middle" fill={isDark ? '#a1a1aa' : '#52525b'} fontSize="11" fontWeight="700" letterSpacing="0.1em">CREDENTIAL TYPES</text>
            {[
              { x: 80, label: 'Password', desc: 'Argon2id hashing' },
              { x: 230, label: 'API Key', desc: 'Prefix-based match' },
              { x: 380, label: 'JWT Token', desc: 'Cryptographic Bearer' },
              { x: 520, label: 'Session', desc: 'Secure Cookie' },
            ].map((c, i) => (
              <g key={i}>
                <rect x={c.x} y="145" width={120} height="35" rx="8" fill={isDark ? '#09090b' : '#f4f4f5'} stroke={isDark ? '#27272a' : '#e4e4e7'} strokeWidth="1.2" />
                <text x={c.x + 60} y="160" textAnchor="middle" fill={isDark ? '#e4e4e7' : '#27272a'} fontSize="11" fontWeight="600" fontFamily="monospace">{c.label}</text>
                <text x={c.x + 60} y="172" textAnchor="middle" fill={isDark ? '#71717a' : '#a1a1aa'} fontSize="9" fontFamily="sans-serif">{c.desc}</text>
              </g>
            ))}

            <defs>
              <marker id="authArrow" viewBox="0 0 10 7" refX="10" refY="3.5" markerWidth="8" markerHeight="6" orient="auto">
                <polygon points="0 0, 10 3.5, 0 7" fill={isDark ? '#3f3f46' : '#d4d4d8'} />
              </marker>
            </defs>
          </svg>
        </div>
      </section>

      {/* Module Overview Section */}
      <section className="space-y-6">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Subsystem Components
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {[
            { icon: <Key className="w-5 h-5" />, title: 'core', desc: 'Identity structures, PasswordCredential representations, API keys, OAuth clients, and storage contracts.', color: '#3b82f6' },
            { icon: <Lock className="w-5 h-5" />, title: 'manager', desc: 'AuthManager coordinating verification, rate limiting, session binding, and lockout mechanisms.', color: '#22c55e' },
            { icon: <Fingerprint className="w-5 h-5" />, title: 'hashing', desc: 'Argon2id and PBKDF2 hashing functions coupled with password policy enforcement.', color: '#f59e0b' },
            { icon: <Shield className="w-5 h-5" />, title: 'tokens', desc: 'KeyRing rotation, JWT access token generation, and cryptographically signed claims.', color: '#8b5cf6' },
            { icon: <Shield className="w-5 h-5" />, title: 'guards', desc: 'RoleGuard and ScopeGuard decorators safeguarding API endpoints and handlers.', color: '#ef4444' },
            { icon: <Shield className="w-5 h-5" />, title: 'authz', desc: 'RBACEngine and ABACEngine mapping policy rules dynamically for permissions.', color: '#06b6d4' },
            { icon: <Layers className="w-5 h-5" />, title: 'oauth', desc: 'OAuth2Manager supporting authorization codes, PKCE validations, and client credentials.', color: '#ec4899' },
            { icon: <Fingerprint className="w-5 h-5" />, title: 'mfa', desc: 'TOTP provider (RFC 6238) enforcing MFA verification and backup recovery codes.', color: '#14b8a6' },
            { icon: <Database className="w-5 h-5" />, title: 'stores', desc: 'MemoryStore adapters for lightweight configurations and RedisTokenStore for production caches.', color: '#a855f7' },
          ].map((m, i) => (
            <div key={i} className="flex gap-4 p-4 rounded-xl hover:bg-aquilia-500/5 transition-all duration-300 group">
              <div className="mt-1.5 group-hover:scale-110 transition-all duration-300" style={{ color: m.color }}>
                {m.icon}
              </div>
              <div className="space-y-1">
                <span className="font-bold text-sm font-mono block tracking-tight" style={{ color: m.color }}>
                  {m.title}
                </span>
                <p className={`text-xs leading-normal ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  {m.desc}
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Application Integration Tutorial */}
      <section className="space-y-8">
        <div className="space-y-2">
          <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
            End-to-End Application Integration
          </h2>
          <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Rather than configuring independent components, this guide walks you through building a complete user registration, authentication, and endpoint authorization system backed by the database ORM and dependency injection.
          </p>
        </div>

        {/* Step 1 */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <span className="text-aquilia-500 font-bold font-mono text-lg">01.</span>
            <h3 className={`text-lg font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
              Define the User DB Model
            </h3>
          </div>
          <p className={`text-sm pl-8 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Extend the base <DocTerm id="orm.model">Model</DocTerm> to define columns for user names, emails, active flags, comma-separated roles, and cryptographically hashed passwords.
          </p>
          <div className="pl-8">
            <CodeBlock language="python" filename="models/user.py">{`from aquilia.models import Model
from aquilia.models.fields import CharField, EmailField, BooleanField, DateTimeField

class User(Model):
    table = "users"

    name = CharField(max_length=150)
    email = EmailField(unique=True)
    password_hash = CharField(max_length=255)
    is_active = BooleanField(default=True)
    roles = CharField(max_length=255, default="user")  # e.g. "user,admin"
    created_at = DateTimeField(auto_now_add=True)
`}</CodeBlock>
          </div>
        </div>

        {/* Step 2 */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <span className="text-aquilia-500 font-bold font-mono text-lg">02.</span>
            <h3 className={`text-lg font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
              Establish Request Validation Contracts
            </h3>
          </div>
          <p className={`text-sm pl-8 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Create incoming schema definitions (Contracts) to enforce type validation, boundary checks, and sanitizer casts on incoming API requests automatically.
          </p>
          <div className="pl-8">
            <CodeBlock language="python" filename="contracts/auth.py">{`from aquilia.contracts import Contract, Field

class SignUpContract(Contract):
    name = Field[str]()
    email = Field[str]()
    password = Field[str]()

class SignInContract(Contract):
    email = Field[str]()
    password = Field[str]()
`}</CodeBlock>
          </div>
        </div>

        {/* Step 3 */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <span className="text-aquilia-500 font-bold font-mono text-lg">03.</span>
            <h3 className={`text-lg font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
              Implement the Auth Controller
            </h3>
          </div>
          <p className={`text-sm pl-8 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Build controller methods to handle user creation, token issuance, and protected dashboard paths. Decorating methods with <DocTerm id="auth.authenticated">@authenticated</DocTerm> or <DocTerm id="auth.require_identity">@require_identity</DocTerm> isolates access boundaries.
          </p>
          <div className="pl-8">
            <CodeBlock language="python" filename="controllers/auth.py">{`from aquilia.controller import Controller, GET, POST
from aquilia.response import Response
from aquilia.auth.decorators import authenticated, require_identity
from aquilia.auth.manager import AuthManager
from aquilia.auth.core import Identity, IdentityType, IdentityStatus
from contracts.auth import SignUpContract, SignInContract
from models.user import User

class AuthController(Controller):
    prefix = "/auth"

    @POST("/signup")
    async def signup(self, ctx, contract: SignUpContract):
        """Register a new user, hashing their password hash."""
        data = contract.validated_data
        
        # Verify if record exists
        existing = await User.objects.filter(email=data["email"]).first()
        if existing:
            return Response.json({"error": "Email is already taken"}, status=400)
            
        auth_manager = ctx.container.resolve(AuthManager)
        hashed = auth_manager.password_hasher.hash(data["password"])
        
        user = await User.objects.create(
            name=data["name"],
            email=data["email"],
            password_hash=hashed,
            is_active=True,
            roles="user"
        )
        return Response.json({"success": True, "user_id": str(user.id)})

    @POST("/login")
    async def login(self, ctx, contract: SignInContract):
        """Authenticate user credentials and issue security tokens."""
        data = contract.validated_data
        auth_manager = ctx.container.resolve(AuthManager)
        
        user = await User.objects.filter(email=data["email"]).first()
        if not user or not user.is_active:
            return Response.json({"error": "Invalid credentials"}, status=401)
            
        # Initialize seed identity for dynamic stores
        identity = Identity(
            id=str(user.id),
            type=IdentityType.USER,
            attributes={
                "email": user.email,
                "name": user.name,
                "roles": user.roles.split(","),
            },
            status=IdentityStatus.ACTIVE,
        )
        
        try:
            # Complete login and return Issued Access and Refresh Tokens
            auth_result = await auth_manager.sign_in(
                username=user.email,
                password=data["password"],
                identity=identity,
            )
            return Response.json({
                "access_token": auth_result.access_token,
                "refresh_token": auth_result.refresh_token,
                "expires_in": auth_result.expires_in,
            })
        except Exception as e:
            return Response.json({"error": "Authentication failed"}, status=401)

    @GET("/profile")
    @authenticated
    async def profile(self, ctx, user: Identity):
        """Authenticated endpoint returns current user info."""
        return Response.json({
            "id": user.id,
            "name": user.get_attribute("name"),
            "email": user.get_attribute("email"),
            "roles": user.get_attribute("roles"),
        })

    @GET("/admin-panel")
    @require_identity(roles=["admin"])
    async def admin_panel(self, ctx, user: Identity):
        """Admin restricted route."""
        return Response.json({"message": "Welcome, Administrator!"})
`}</CodeBlock>
          </div>
        </div>

        {/* Step 4 */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <span className="text-aquilia-500 font-bold font-mono text-lg">04.</span>
            <h3 className={`text-lg font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
              Implement Database Adapters for Auth Storage
            </h3>
          </div>
          <p className={`text-sm pl-8 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Map the authentication protocols (`IdentityStore` and `CredentialStore`) directly to your database queries to resolve principals and store password updates securely.
          </p>
          <div className="pl-8">
            <CodeBlock language="python" filename="stores/database.py">{`from typing import Any
from aquilia.auth.core import IdentityStore, CredentialStore, Identity, PasswordCredential, IdentityStatus, IdentityType
from models.user import User

class DatabaseIdentityStore(IdentityStore):
    async def get(self, identity_id: str) -> Identity | None:
        user = await User.objects.filter(id=identity_id).first()
        if not user or not user.is_active:
            return None
        return Identity(
            id=str(user.id),
            type=IdentityType.USER,
            attributes={
                "email": user.email,
                "name": user.name,
                "roles": user.roles.split(","),
            },
            status=IdentityStatus.ACTIVE,
        )

    async def get_by_attribute(self, attribute: str, value: Any) -> Identity | None:
        if attribute == "email":
            user = await User.objects.filter(email=value).first()
            if user:
                return await self.get(str(user.id))
        return None

class DatabaseCredentialStore(CredentialStore):
    async def get_password(self, identity_id: str) -> PasswordCredential | None:
        user = await User.objects.filter(id=identity_id).first()
        if not user:
            return None
        return PasswordCredential(
            identity_id=identity_id,
            password_hash=user.password_hash
        )

    async def save_password(self, credential: PasswordCredential) -> None:
        await User.objects.filter(id=credential.identity_id).update(
            password_hash=credential.password_hash
        )
`}</CodeBlock>
          </div>
        </div>

        {/* Step 5 */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <span className="text-aquilia-500 font-bold font-mono text-lg">05.</span>
            <h3 className={`text-lg font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
              Bootstrap DI Registration and Middleware
            </h3>
          </div>
          <p className={`text-sm pl-8 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Register your database store overrides in the dependency injection container, append the <DocTerm id="auth.aquil_auth_middleware">AquilAuthMiddleware</DocTerm> stack, and launch the application.
          </p>
          <div className="pl-8">
            <CodeBlock language="python" filename="app.py">{`from aquilia import Aquilia
from aquilia.sessions import SessionEngine
from aquilia.auth.core import IdentityStore, CredentialStore
from aquilia.auth.manager import AuthManager
from aquilia.auth.integration.di_providers import register_auth_providers
from aquilia.auth.integration.middleware import AquilAuthMiddleware, EnhancedRequestScopeMiddleware
from stores.database import DatabaseIdentityStore, DatabaseCredentialStore
from controllers.auth import AuthController

app = Aquilia()

# 1. Register custom DB auth store adapters before initializing auth providers
app.container.register(IdentityStore, DatabaseIdentityStore)
app.container.register(CredentialStore, DatabaseCredentialStore)

# 2. Register all default providers (PasswordHasher, TokenManager, etc.)
register_auth_providers(app.container)

# 3. Resolve required managers from container
session_engine = app.container.resolve(SessionEngine)
auth_manager = app.container.resolve(AuthManager)

# 4. Attach request scope container creation middleware
app.use(EnhancedRequestScopeMiddleware(app.container))

# 5. Apply the main auth middleware to intercept requests
app.use(AquilAuthMiddleware(
    session_engine=session_engine,
    auth_manager=auth_manager,
    require_auth=False,  # Enforce opt-in per route using decorators
))

# 6. Bind controller endpoints
app.register_controller(AuthController)
`}</CodeBlock>
          </div>
        </div>
      </section>

      {/* Identity Configuration Schema Table */}
      <section className="space-y-6">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Identity Object Structure
        </h2>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The principal identity is immutable once instantiated, representing a secure entity descriptor inside RequestCtx.
        </p>
        <div className="overflow-x-auto">
          <table className={`w-full text-sm text-left ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className={`border-b ${isDark ? 'border-zinc-800' : 'border-zinc-200'}`}>
                <th className="py-3 font-semibold text-aquilia-500 font-mono text-xs w-1/4">Field</th>
                <th className="py-3 font-semibold text-aquilia-500 font-mono text-xs w-1/4">Type</th>
                <th className="py-3 font-semibold text-aquilia-500 text-xs w-2/4">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/10 dark:divide-zinc-800/50">
              {[
                ['id', 'str', 'Unique immutable principal identifier.'],
                ['type', 'IdentityType', 'System enumeration: USER, SERVICE, DEVICE, or ANONYMOUS.'],
                ['attributes', 'dict[str, Any]', 'ABAC metadata including roles, scopes, emails, groups.'],
                ['status', 'IdentityStatus', 'Active status: ACTIVE, SUSPENDED, DELETED, or PENDING.'],
                ['tenant_id', 'str | None', 'Optional key defining multi-tenant organizational scope.'],
                ['created_at', 'datetime', 'Entity registration timestamp.'],
                ['updated_at', 'datetime', 'Entity last modification timestamp.'],
              ].map(([f, t, d], i) => (
                <tr key={i} className="hover:bg-aquilia-500/2 transition-colors duration-200">
                  <td className="py-3 font-mono text-xs text-aquilia-400 font-bold">{f}</td>
                  <td className="py-3 font-mono text-xs text-gray-500">{t}</td>
                  <td className={`py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{d}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    
      <NextSteps />
    </div>
  )
}