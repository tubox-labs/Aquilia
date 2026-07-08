import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Settings, Shield, Clock, AlertTriangle, Key, RefreshCw, LogOut } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function AuthManager() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto space-y-16">
      {/* Header Section */}
      <div className="space-y-4">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium tracking-wide">
          <Settings className="w-4 h-4" />
          <span>Security &amp; Auth</span>
        </div>
        <h1 className={`text-4xl font-extrabold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="gradient-text font-mono relative group inline-block">
            AuthManager
            <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <DocTerm id="auth.auth_manager">AuthManager</DocTerm> is the central coordinator for all authentication operations. It orchestrates identity verification, token issuance, password hashing, rate limiting, and session management.
        </p>
      </div>

      {/* Architecture */}
      <section className="space-y-6">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Architecture
        </h2>
        <div className="flex justify-center py-4">
          <svg viewBox="0 0 700 240" className="w-full max-w-2xl h-auto" fill="none" xmlns="http://www.w3.org/2000/svg">
            <text x="350" y="20" textAnchor="middle" fill={isDark ? '#e4e4e7' : '#27272a'} fontSize="13" fontWeight="700" fontFamily="sans-serif">AuthManager Orchestration</text>

            {/* Central AuthManager box */}
            <rect x="250" y="40" width="200" height="50" rx="12" fill="#3b82f60c" stroke="#3b82f6" strokeWidth="1.5" />
            <text x="350" y="62" textAnchor="middle" fill="#3b82f6" fontSize="14" fontWeight="700" fontFamily="monospace">AuthManager</text>
            <text x="350" y="78" textAnchor="middle" fill={isDark ? '#888888' : '#64748b'} fontSize="9" fontFamily="sans-serif">Central Coordinator</text>

            {/* Sub-systems */}
            {[
              { x: 20,  y: 120, label: 'IdentityStore', color: '#22c55e' },
              { x: 155, y: 120, label: 'CredentialStore', color: '#f59e0b' },
              { x: 300, y: 120, label: 'TokenManager', color: '#8b5cf6' },
              { x: 440, y: 120, label: 'PasswordHasher', color: '#ef4444' },
              { x: 575, y: 120, label: 'RateLimiter', color: '#06b6d4' },
            ].map((b, i) => (
              <g key={i}>
                <rect x={b.x} y={b.y} width={105} height={40} rx="8" fill={b.color + '0c'} stroke={b.color} strokeWidth="1.2" />
                <text x={b.x + 52.5} y={b.y + 24} textAnchor="middle" fill={b.color} fontSize="11" fontWeight="600" fontFamily="monospace">{b.label}</text>
                <line x1={b.x + 52.5} y1={b.y} x2={350} y2={90} stroke={isDark ? '#27272a' : '#e4e4e7'} strokeWidth="1.2" strokeDasharray="3 3" />
              </g>
            ))}

            {/* Operations */}
            <text x="350" y="195" textAnchor="middle" fill={isDark ? '#a1a1aa' : '#52525b'} fontSize="11" fontWeight="700" letterSpacing="0.05em" fontFamily="sans-serif">OPERATIONS</text>
            {[
              { x: 30,  label: 'authenticate_password' },
              { x: 190, label: 'authenticate_api_key' },
              { x: 350, label: 'refresh_access_token' },
              { x: 510, label: 'revoke_token / logout' },
            ].map((op, i) => (
              <g key={i}>
                <rect x={op.x} y="207" width={155} height="26" rx="6" fill={isDark ? '#09090b' : '#f4f4f5'} stroke={isDark ? '#27272a' : '#e4e4e7'} strokeWidth="1" />
                <text x={op.x + 77.5} y="223" textAnchor="middle" fill={isDark ? '#e4e4e7' : '#27272a'} fontSize="9" fontWeight="600" fontFamily="monospace">{op.label}</text>
              </g>
            ))}
          </svg>
        </div>
      </section>

      {/* Constructor */}
      <section className="space-y-4">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Constructor
        </h2>
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
          <table className={`w-full text-sm text-left ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className={`border-b ${isDark ? 'border-zinc-800' : 'border-zinc-200'}`}>
                <th className="py-3 font-semibold text-aquilia-500 font-mono text-xs w-1/4">Parameter</th>
                <th className="py-3 font-semibold text-aquilia-500 font-mono text-xs w-1/4">Type</th>
                <th className="py-3 font-semibold text-aquilia-500 text-xs w-2/4">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/10 dark:divide-zinc-800/50">
              {[
                ['identity_store', 'IdentityStore', 'Storage backend for resolving user identities.'],
                ['credential_store', 'CredentialStore', 'Storage backend for passwords, API keys, and MFA records.'],
                ['token_manager', 'TokenManager', 'Issues and verifies signed security tokens.'],
                ['password_hasher', 'PasswordHasher | None', 'Custom password hasher instance.'],
                ['rate_limiter', 'RateLimiter | None', 'Custom rate limiting rules.'],
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

      {/* Password Authentication */}
      <section className="space-y-6">
        <h2 className={`text-2.5xl font-bold tracking-tight flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Key className="w-6 h-6 text-aquilia-500" />
          <span>Password Authentication</span>
        </h2>
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
`}</CodeBlock>

        <h3 className={`text-lg font-bold pt-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Password Auth Flow
        </h3>
        
        {/* SVG Flow diagram */}
        <div className="flex justify-center py-4">
          <svg viewBox="0 0 600 450" className="w-full max-w-xl h-auto" fill="none" xmlns="http://www.w3.org/2000/svg">
            {[
              { num: '1', label: 'Rate Limit Check', desc: 'Blocks requests if locked out (AUTH_ACCOUNT_LOCKED)', color: '#3b82f6' },
              { num: '2', label: 'Identity Lookup', desc: 'Queries identity store by email or username', color: '#f59e0b' },
              { num: '3', label: 'Status Validation', desc: 'Rejects SUSPENDED or DELETED account records', color: '#ef4444' },
              { num: '4', label: 'Argon2id Verification', desc: 'Constant-time verification and auto-rehash checks', color: '#8b5cf6' },
              { num: '5', label: 'MFA Verification', desc: 'Enforces code checking if enrolled (AUTH_MFA_REQUIRED)', color: '#06b6d4' },
              { num: '6', label: 'Token Issuance', desc: 'Generates access JWT and opaque refresh tokens', color: '#22c55e' },
            ].map((step, i) => (
              <g key={i}>
                <circle cx="40" cy={35 + i * 75} r="16" fill={step.color + '15'} stroke={step.color} strokeWidth="2" />
                <text x="40" y={39 + i * 75} textAnchor="middle" fill={step.color} fontSize="11" fontWeight="bold" fontFamily="monospace">{step.num}</text>
                <text x="72" y={32 + i * 75} fill={isDark ? '#e4e4e7' : '#18181b'} fontSize="13" fontWeight="bold" fontFamily="sans-serif">{step.label}</text>
                <text x="72" y={48 + i * 75} fill={isDark ? '#a1a1aa' : '#71717a'} fontSize="11" fontFamily="sans-serif">{step.desc}</text>
                {i < 5 && <line x1="40" y1={51 + i * 75} x2="40" y2={94 + i * 75} stroke={isDark ? '#27272a' : '#e4e4e7'} strokeWidth="1.5" strokeDasharray="3 3" />}
              </g>
            ))}
          </svg>
        </div>
      </section>

      {/* API Key Authentication */}
      <section className="space-y-4">
        <h2 className={`text-2.5xl font-bold tracking-tight flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Shield className="w-6 h-6 text-aquilia-500" />
          <span>API Key Authentication</span>
        </h2>
        <CodeBlock language="python" filename="authenticate_api_key">{`result = await auth.authenticate_api_key(
    api_key="ak_live_abc123def456...",
    required_scopes=["orders.read"],  # optional scope enforcement
)

# API key IS the token — no separate JWT issued
result.access_token   # == api_key
result.refresh_token  # None
result.session_id     # None
result.metadata       # {"auth_method": "api_key", "key_id": "...", "scopes": [...]}
`}</CodeBlock>
      </section>

      {/* Token Refresh */}
      <section className="space-y-4">
        <h2 className={`text-2.5xl font-bold tracking-tight flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <RefreshCw className="w-6 h-6 text-aquilia-500" />
          <span>Token Refresh</span>
        </h2>
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
      <section className="space-y-4">
        <h2 className={`text-2.5xl font-bold tracking-tight flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <LogOut className="w-6 h-6 text-aquilia-500" />
          <span>Revocation &amp; Logout</span>
        </h2>
        <CodeBlock language="python" filename="Token Revocation">{`# Revoke a single token
await auth.revoke_token("rt_abc...", token_type="refresh")
await auth.revoke_token(access_jwt, token_type="access")  # extracts JTI

# Logout — revoke everything for user or session
await auth.logout(identity_id="user_42")
await auth.logout(session_id="sess_abc123")
`}</CodeBlock>
      </section>

      {/* Rate Limiter */}
      <section className="space-y-4">
        <h2 className={`text-2.5xl font-bold tracking-tight flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Clock className="w-6 h-6 text-aquilia-500" />
          <span>Rate Limiter</span>
        </h2>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The built-in <code className="text-aquilia-500 font-mono text-xs">RateLimiter</code> prevents brute-force password attacks with a sliding window and automatic lockout.
        </p>
        <CodeBlock language="python" filename="RateLimiter">{`from aquilia.auth import RateLimiter

limiter = RateLimiter(
    max_attempts=5,           # failures before lockout
    window_seconds=900,       # 15-minute sliding window
    lockout_duration=3600,    # 1-hour lockout
)

# Record a failed attempt
limiter.record_attempt("auth:password:alice@example.com")
`}</CodeBlock>

        <div className="overflow-x-auto mt-6">
          <table className={`w-full text-sm text-left ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className={`border-b ${isDark ? 'border-zinc-800' : 'border-zinc-200'}`}>
                <th className="py-3 font-semibold text-aquilia-500 font-mono text-xs w-1/4">Parameter</th>
                <th className="py-3 font-semibold text-aquilia-500 font-mono text-xs w-1/4">Default</th>
                <th className="py-3 font-semibold text-aquilia-500 text-xs w-2/4">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/10 dark:divide-zinc-800/50">
              {[
                ['max_attempts', '5', 'Max failed attempts before lockout.'],
                ['window_seconds', '900', 'Sliding window for counting attempts (15 min).'],
                ['lockout_duration', '3600', 'Lockout period after max attempts (1 hour).'],
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

      {/* Faults */}
      <section className="space-y-4">
        <h2 className={`text-2.5xl font-bold tracking-tight flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <AlertTriangle className="w-6 h-6 text-red-500" />
          <span>Authentication Faults</span>
        </h2>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          AuthManager raises structured <code className="text-aquilia-500 font-mono text-xs">Fault</code> exceptions integrated with AquilaFaults.
        </p>
        <div className="overflow-x-auto">
          <table className={`w-full text-sm text-left ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className={`border-b ${isDark ? 'border-zinc-800' : 'border-zinc-200'}`}>
                <th className="py-3 font-semibold text-aquilia-500 font-mono text-xs w-1/3">Fault</th>
                <th className="py-3 font-semibold text-aquilia-500 font-mono text-xs w-1/6">Code</th>
                <th className="py-3 font-semibold text-aquilia-500 text-xs w-1/2">When Raised</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/10 dark:divide-zinc-800/50">
              {[
                ['AUTH_INVALID_CREDENTIALS', 'AUTH_001', 'Wrong username/password or API key.'],
                ['AUTH_ACCOUNT_LOCKED', 'AUTH_008', 'Too many failed attempts — lockout active.'],
                ['AUTH_ACCOUNT_SUSPENDED', 'AUTH_007', 'Identity status is SUSPENDED.'],
                ['AUTH_MFA_REQUIRED', 'AUTH_005', 'MFA enrolled — code verification needed.'],
                ['AUTH_KEY_EXPIRED', 'AUTH_104', 'API key past expiration date.'],
                ['AUTH_KEY_REVOKED', 'AUTH_105', 'API key status is REVOKED.'],
                ['AUTH_TOKEN_INVALID', 'AUTH_002', 'Malformed, bad signature, or unknown kid.'],
                ['AUTH_TOKEN_EXPIRED', 'AUTH_003', 'Access token past expiration time.'],
                ['AUTH_TOKEN_REVOKED', 'AUTH_004', 'Token in revocation list.'],
                ['AUTH_RATE_LIMITED', 'AUTH_009', 'Too many auth attempts in window.'],
              ].map(([f, c, d], i) => (
                <tr key={i} className="hover:bg-aquilia-500/2 transition-colors duration-200">
                  <td className="py-3 font-mono text-xs text-red-500/90 font-bold">{f}</td>
                  <td className="py-3 font-mono text-xs text-gray-500">{c}</td>
                  <td className={`py-3 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{d}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* DI Integration */}
      <section className="space-y-4">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          DI Integration
        </h2>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          AuthManager is available as a DI provider via <code className="text-aquilia-500 font-mono text-xs">AuthManagerProvider</code>. All dependencies are resolved automatically.
        </p>
        <CodeBlock language="python" filename="DI Registration">{`from aquilia.auth.integration.di_providers import (
    AuthManagerProvider,
    IdentityStoreProvider,
    CredentialStoreProvider,
)
`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
