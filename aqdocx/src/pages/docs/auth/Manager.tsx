import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Settings, Shield, Clock, AlertTriangle, Key, RefreshCw, LogOut } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function AuthManager() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4"><Settings className="w-4 h-4" />Security &amp; Auth</div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            AuthManager
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">AuthManager</code> is the central coordinator for all authentication operations. It orchestrates identity verification, token issuance, password hashing, rate limiting, and session management — wiring together every auth sub-system in a single entry point.
        </p>
      </div>

      {/* Architecture */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Architecture</h2>
        <div className={boxClass}>
          <svg viewBox="0 0 700 240" className="w-full h-auto">
            <rect width="700" height="240" rx="16" fill={isDark ? '#0A0A0A' : '#f8fafc'} />
            <text x="350" y="28" textAnchor="middle" fill={isDark ? '#888' : '#64748b'} fontSize="13" fontWeight="700">AuthManager Orchestration</text>

            {/* Central AuthManager box */}
            <rect x="250" y="40" width="200" height="50" rx="10" fill="#3b82f615" stroke="#3b82f6" strokeWidth="1.5" />
            <text x="350" y="62" textAnchor="middle" fill="#3b82f6" fontSize="14" fontWeight="700">AuthManager</text>
            <text x="350" y="78" textAnchor="middle" fill={isDark ? '#666' : '#94a3b8'} fontSize="10">Central coordinator</text>

            {/* Sub-systems */}
            {[
              { x: 20,  y: 120, label: 'IdentityStore', color: '#22c55e' },
              { x: 155, y: 120, label: 'CredentialStore', color: '#f59e0b' },
              { x: 300, y: 120, label: 'TokenManager', color: '#8b5cf6' },
              { x: 440, y: 120, label: 'PasswordHasher', color: '#ef4444' },
              { x: 575, y: 120, label: 'RateLimiter', color: '#06b6d4' },
            ].map((b, i) => (
              <g key={i}>
                <rect x={b.x} y={b.y} width={125} height={40} rx="8" fill={b.color + '15'} stroke={b.color} strokeWidth="1" />
                <text x={b.x + 62.5} y={b.y + 24} textAnchor="middle" fill={b.color} fontSize="11" fontWeight="600">{b.label}</text>
                <line x1={b.x + 62.5} y1={b.y} x2={350} y2={90} stroke={isDark ? '#333' : '#cbd5e1'} strokeWidth="1" strokeDasharray="4 2" />
              </g>
            ))}

            {/* Operations */}
            <text x="350" y="195" textAnchor="middle" fill={isDark ? '#555' : '#94a3b8'} fontSize="11" fontWeight="600">OPERATIONS</text>
            {[
              { x: 30,  label: 'authenticate_password' },
              { x: 185, label: 'authenticate_api_key' },
              { x: 340, label: 'refresh_access_token' },
              { x: 495, label: 'revoke_token / logout' },
            ].map((op, i) => (
              <g key={i}>
                <rect x={op.x} y={207} width={145} height={26} rx="6" fill={isDark ? '#111' : '#f1f5f9'} stroke={isDark ? '#333' : '#cbd5e1'} strokeWidth="1" />
                <text x={op.x + 72.5} y={224} textAnchor="middle" fill={isDark ? '#ccc' : '#334155'} fontSize="9" fontWeight="600" fontFamily="monospace">{op.label}</text>
              </g>
            ))}
          </svg>
        </div>
      </section>

      {/* Constructor */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Constructor</h2>
        <CodeBlock language="python" filename="Initialization">{`from aquilia.auth import (
    AuthManager, RateLimiter, PasswordHasher,
    TokenManager, TokenConfig, KeyRing, KeyDescriptor, KeyAlgorithm,
    MemoryIdentityStore, MemoryCredentialStore, MemoryTokenStore,
)

# 1. Stores
identity_store  = MemoryIdentityStore()
credential_store = MemoryCredentialStore()
token_store     = MemoryTokenStore()

# 2. Key ring (one active signing key)
key = KeyDescriptor.generate(kid="k1", algorithm=KeyAlgorithm.RS256)
key_ring = KeyRing(keys=[key])

# 3. Token manager
token_manager = TokenManager(
    key_ring=key_ring,
    token_store=token_store,
    config=TokenConfig(
        issuer="my-app",
        audience=["api"],
        access_token_ttl=3600,      # 1 hour
        refresh_token_ttl=2592000,   # 30 days
    ),
)

# 4. Auth manager
auth = AuthManager(
    identity_store=identity_store,
    credential_store=credential_store,
    token_manager=token_manager,
    password_hasher=PasswordHasher(),          # Argon2id (auto-fallback to PBKDF2)
    rate_limiter=RateLimiter(
        max_attempts=5,
        window_seconds=900,     # 15 min window
        lockout_duration=3600,  # 1 hour lockout
    ),
)`}</CodeBlock>

        <div className="overflow-x-auto mt-6">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead><tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
              <th className="text-left py-3 pr-4 text-aquilia-500">Parameter</th>
              <th className="text-left py-3 pr-4 text-aquilia-500">Type</th>
              <th className="text-left py-3 text-aquilia-500">Description</th>
            </tr></thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['identity_store', 'MemoryIdentityStore', 'Storage backend for identities (lookup by ID or attribute)'],
                ['credential_store', 'MemoryCredentialStore', 'Storage for passwords, API keys, MFA credentials'],
                ['token_manager', 'TokenManager', 'Issues and validates access/refresh tokens'],
                ['password_hasher', 'PasswordHasher | None', 'Argon2id or PBKDF2 hasher — auto-created if None'],
                ['rate_limiter', 'RateLimiter | None', 'Failed-attempt limiter — auto-created if None'],
              ].map(([f, t, d], i) => (
                <tr key={i}>
                  <td className="py-2 pr-4 font-mono text-xs text-aquilia-400">{f}</td>
                  <td className="py-2 pr-4 font-mono text-xs text-gray-500">{t}</td>
                  <td className={`py-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{d}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Password Authentication */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}><Key className="w-5 h-5 text-aquilia-500" />Password Authentication</h2>
        <CodeBlock language="python" filename="authenticate_password">{`result = await auth.authenticate_password(
    username="alice@example.com",     # looked up by email then username
    password="SuperSecret!23",
    scopes=["profile", "orders.read"],
    session_id=None,                  # auto-generated if omitted
    client_metadata={"ip": "1.2.3.4", "user_agent": "Chrome/120"},
)

# AuthResult fields
result.identity          # Identity object
result.access_token      # Signed JWT (header.payload.signature)
result.refresh_token     # Opaque rt_<random>
result.session_id        # sess_<random>
result.expires_in        # 3600 (seconds)
result.token_type        # "Bearer"
result.metadata          # {"auth_method": "password", "client_metadata": {...}}

# Token response for API clients
result.to_dict()
# {
#   "access_token": "eyJ...",
#   "token_type": "Bearer",
#   "expires_in": 3600,
#   "refresh_token": "rt_...",
#   "scope": "profile orders.read"
# }`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-8 mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Password Auth Flow</h3>
        <div className={boxClass}>
          <ol className={`list-decimal list-inside space-y-2 text-sm ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
            <li><strong>Rate limit check</strong> — if locked out, raises <code className="text-red-400">AUTH_ACCOUNT_LOCKED</code></li>
            <li><strong>Identity lookup</strong> — searches by <code className="text-aquilia-400">email</code> then <code className="text-aquilia-400">username</code> attribute</li>
            <li><strong>Status check</strong> — rejects SUSPENDED or DELETED identities</li>
            <li><strong>Password verification</strong> — Argon2id constant-time comparison</li>
            <li><strong>Auto-rehash</strong> — upgrades hash if algorithm parameters changed</li>
            <li><strong>Rate limit reset</strong> — clears attempts on successful auth</li>
            <li><strong>MFA check</strong> — if MFA enrolled, raises <code className="text-yellow-400">AUTH_MFA_REQUIRED</code> with available methods</li>
            <li><strong>Token issuance</strong> — generates access JWT + opaque refresh token</li>
          </ol>
        </div>
      </section>

      {/* API Key Authentication */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}><Shield className="w-5 h-5 text-aquilia-500" />API Key Authentication</h2>
        <CodeBlock language="python" filename="authenticate_api_key">{`result = await auth.authenticate_api_key(
    api_key="ak_live_abc123def456...",
    required_scopes=["orders.read"],  # optional scope enforcement
)

# API key IS the token — no separate JWT issued
result.access_token   # == api_key
result.refresh_token  # None
result.session_id     # None
result.metadata       # {"auth_method": "api_key", "key_id": "...", "scopes": [...]}

# Key validation steps:
# 1. Extract prefix (first 8 chars) → lookup credential
# 2. SHA-256 hash comparison
# 3. Check expiration & status (ACTIVE, REVOKED, EXPIRED)
# 4. Scope enforcement
# 5. Identity status check`}</CodeBlock>
      </section>

      {/* Token Refresh */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}><RefreshCw className="w-5 h-5 text-aquilia-500" />Token Refresh</h2>
        <CodeBlock language="python" filename="Token Rotation">{`# Refresh token rotation (security best practice)
new_access, new_refresh = await auth.refresh_access_token(
    refresh_token="rt_old_token_here"
)

# The old refresh token is REVOKED after use
# This prevents replay attacks

# Verify & decode an access token
claims = await auth.verify_token(access_token)
# TokenClaims(iss, sub, aud, exp, iat, nbf, jti, scopes, roles, sid, tenant_id)

# Get identity directly from token
identity = await auth.get_identity_from_token(access_token)
# Returns None if token is invalid/expired`}</CodeBlock>
      </section>

      {/* Revocation & Logout */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}><LogOut className="w-5 h-5 text-aquilia-500" />Revocation &amp; Logout</h2>
        <CodeBlock language="python" filename="Token Revocation">{`# Revoke a single token
await auth.revoke_token("rt_abc...", token_type="refresh")
await auth.revoke_token(access_jwt, token_type="access")  # extracts JTI

# Logout — revoke everything for user or session
await auth.logout(identity_id="user_42")
await auth.logout(session_id="sess_abc123")

# Both can be combined for full logout
await auth.logout(identity_id="user_42", session_id="sess_abc123")`}</CodeBlock>
      </section>

      {/* Rate Limiter */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}><Clock className="w-5 h-5 text-aquilia-500" />Rate Limiter</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The built-in <code className="text-aquilia-500">RateLimiter</code> prevents brute-force password attacks with a sliding window and automatic lockout.
        </p>
        <CodeBlock language="python" filename="RateLimiter">{`from aquilia.auth import RateLimiter

limiter = RateLimiter(
    max_attempts=5,           # failures before lockout
    window_seconds=900,       # 15-minute sliding window
    lockout_duration=3600,    # 1-hour lockout
)

# Record a failed attempt
limiter.record_attempt("auth:password:alice@example.com")

# Check lockout status
limiter.is_locked_out("auth:password:alice@example.com")  # True after 5 failures

# Check remaining attempts
limiter.get_remaining_attempts("auth:password:alice@example.com")  # 3

# Reset on successful auth
limiter.reset("auth:password:alice@example.com")`}</CodeBlock>

        <div className="overflow-x-auto mt-6">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead><tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
              <th className="text-left py-3 pr-4 text-aquilia-500">Parameter</th>
              <th className="text-left py-3 pr-4 text-aquilia-500">Default</th>
              <th className="text-left py-3 text-aquilia-500">Description</th>
            </tr></thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['max_attempts', '5', 'Max failed attempts before lockout'],
                ['window_seconds', '900', 'Sliding window for counting attempts (15 min)'],
                ['lockout_duration', '3600', 'Lockout period after max attempts (1 hour)'],
              ].map(([f, t, d], i) => (
                <tr key={i}>
                  <td className="py-2 pr-4 font-mono text-xs text-aquilia-400">{f}</td>
                  <td className="py-2 pr-4 font-mono text-xs text-gray-500">{t}</td>
                  <td className={`py-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{d}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Faults */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}><AlertTriangle className="w-5 h-5 text-red-500" />Authentication Faults</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          AuthManager raises structured <code className="text-aquilia-500">Fault</code> exceptions integrated with AquilaFaults. Every fault has a code, severity, public message, and retryable flag.
        </p>
        <div className="overflow-x-auto">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead><tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
              <th className="text-left py-3 pr-4 text-aquilia-500">Fault</th>
              <th className="text-left py-3 pr-4 text-aquilia-500">Code</th>
              <th className="text-left py-3 text-aquilia-500">When Raised</th>
            </tr></thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['AUTH_INVALID_CREDENTIALS', 'AUTH_001', 'Wrong username/password or API key'],
                ['AUTH_ACCOUNT_LOCKED', 'AUTH_008', 'Too many failed attempts — lockout active'],
                ['AUTH_ACCOUNT_SUSPENDED', 'AUTH_007', 'Identity status is SUSPENDED'],
                ['AUTH_MFA_REQUIRED', 'AUTH_005', 'MFA enrolled — code verification needed'],
                ['AUTH_KEY_EXPIRED', 'AUTH_104', 'API key past expiration date'],
                ['AUTH_KEY_REVOKED', 'AUTH_105', 'API key status is REVOKED'],
                ['AUTH_TOKEN_INVALID', 'AUTH_002', 'Malformed, bad signature, or unknown kid'],
                ['AUTH_TOKEN_EXPIRED', 'AUTH_003', 'Access token past expiration time'],
                ['AUTH_TOKEN_REVOKED', 'AUTH_004', 'Token in revocation list'],
                ['AUTH_RATE_LIMITED', 'AUTH_009', 'Too many auth attempts in window'],
              ].map(([f, c, d], i) => (
                <tr key={i}>
                  <td className="py-2 pr-4 font-mono text-xs text-red-400">{f}</td>
                  <td className="py-2 pr-4 font-mono text-xs text-gray-500">{c}</td>
                  <td className={`py-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{d}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* DI Integration */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>DI Integration</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          AuthManager is available as a DI provider via <code className="text-aquilia-500">AuthManagerProvider</code>. All dependencies are resolved automatically.
        </p>
        <CodeBlock language="python" filename="DI Registration">{`from aquilia.auth.integration.di_providers import (
    AuthManagerProvider,
    IdentityStoreProvider,
    CredentialStoreProvider,
    TokenStoreProvider,
    TokenManagerProvider,
    KeyRingProvider,
    PasswordHasherProvider,
    RateLimiterProvider,
)

# All providers are @service(scope="app") singletons
# The DI container resolves the full dependency graph:
#
#   AuthManager
#   ├── IdentityStore   (MemoryIdentityStore)
#   ├── CredentialStore  (MemoryCredentialStore)
#   ├── TokenManager
#   │   ├── KeyRing     (auto-generated RS256 key)
#   │   └── TokenStore  (MemoryTokenStore)
#   ├── PasswordHasher  (Argon2id / PBKDF2)
#   └── RateLimiter     (5 attempts / 15 min / 1 hr lockout)`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
