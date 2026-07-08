import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Globe, Key, Smartphone, ArrowRight, Lock, ShieldCheck } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'


export function AuthOAuth() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto space-y-16">
      {/* Header Section */}
      <div className="space-y-4">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium tracking-wide">
          <Globe className="w-4 h-4" />
          <span>Security &amp; Auth</span>
        </div>
        <h1 className={`text-4xl font-extrabold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="gradient-text font-mono relative group inline-block">
            OAuth2 / OIDC
            <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500 font-mono text-sm">OAuth2Manager</code> implements a complete OAuth 2.0 / OpenID Connect authorization server supporting Authorization Code (with PKCE), Client Credentials, Device Authorization, and Refresh Token flows.
        </p>
      </div>

      {/* Supported Flows */}
      <section className="space-y-6">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Supported Grant Types
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {[
            { icon: <Key className="w-5 h-5" />, title: 'Authorization Code', desc: 'Standard web app flow with PKCE support. User authenticates via consent screen, app receives code, exchanges for tokens.', color: '#3b82f6' },
            { icon: <Lock className="w-5 h-5" />, title: 'Client Credentials', desc: 'Machine-to-machine authentication. No user involved — the client IS the identity. No refresh token issued.', color: '#22c55e' },
            { icon: <Smartphone className="w-5 h-5" />, title: 'Device Authorization', desc: 'Input-constrained devices (TVs, CLIs). Displays user code, polls for approval. Format: XXXX-XXXX.', color: '#f59e0b' },
            { icon: <ShieldCheck className="w-5 h-5" />, title: 'Refresh Token', desc: 'Rotate access tokens without re-authentication. Old refresh token is revoked on use (rotation for security).', color: '#8b5cf6' },
          ].map((flow, i) => (
            <div key={i} className="flex gap-4 p-4 rounded-xl hover:bg-aquilia-500/5 transition-all duration-300 group">
              <div className="mt-1.5 group-hover:scale-110 transition-all duration-300" style={{ color: flow.color }}>
                {flow.icon}
              </div>
              <div className="space-y-1">
                <span className="font-bold text-sm font-mono block" style={{ color: flow.color }}>
                  {flow.title}
                </span>
                <p className={`text-xs leading-normal ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  {flow.desc}
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* OAuth Client */}
      <section className="space-y-4">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          OAuthClient Model
        </h2>
        <CodeBlock language="python" filename="Client Registration">{`from aquilia.auth.core import OAuthClient

client = OAuthClient(
    client_id="app_my-frontend",
    client_secret_hash=OAuthClient.hash_client_secret("s3cr3t"),  # SHA-256
    name="My Frontend App",
    grant_types=["authorization_code", "refresh_token"],
    redirect_uris=["https://myapp.com/callback"],
    scopes=["profile", "orders.read", "orders.write"],
    require_pkce=True,           # Enforce PKCE (default)
    require_consent=True,        # Show consent screen (default)
    token_endpoint_auth_method="client_secret_post",
    access_token_ttl=3600,       # 1 hour
    refresh_token_ttl=2592000,   # 30 days
)
`}</CodeBlock>

        <div className="overflow-x-auto mt-6">
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
                ['client_id', 'str', 'Unique client identifier (app_<random>).'],
                ['client_secret_hash', 'str | None', 'SHA-256 hash of secret — None for public clients.'],
                ['name', 'str', 'Human-readable client name.'],
                ['grant_types', 'list[str]', 'Allowed grant types (authorization_code, client_credentials, refresh_token, device_code).'],
                ['redirect_uris', 'list[str]', 'Allowed redirect URIs for code flow.'],
                ['scopes', 'list[str]', 'Allowed scopes for this client.'],
                ['require_pkce', 'bool', 'Require PKCE for code flow (default True).'],
                ['require_consent', 'bool', 'Show consent screen (default True).'],
                ['token_endpoint_auth_method', 'str', 'client_secret_basic | client_secret_post | none.'],
                ['access_token_ttl', 'int', 'Access token TTL in seconds (default 3600).'],
                ['refresh_token_ttl', 'int', 'Refresh token TTL in seconds (default 2592000).'],
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

      {/* PKCE */}
      <section className="space-y-4">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-950'}`}>
          PKCE (Proof Key for Code Exchange)
        </h2>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          PKCE prevents authorization code interception. The client generates a <code className="text-aquilia-500 font-mono text-xs">code_verifier</code>, sends a SHA-256 hash as <code className="text-aquilia-500 font-mono text-xs">code_challenge</code>, then proves possession at token exchange.
        </p>
        <CodeBlock language="python" filename="PKCE Utilities">{`from aquilia.auth.oauth import PKCEVerifier

# 1. Client generates verifier (43-128 chars)
verifier  = PKCEVerifier.generate_code_verifier(length=128)

# 2. Client computes challenge
challenge = PKCEVerifier.generate_code_challenge(verifier, method="S256")

# 3. Server verifies at token exchange
is_valid  = PKCEVerifier.verify_code_challenge(verifier, challenge, method="S256")
# True — constant-time comparison via secrets.compare_digest`}</CodeBlock>
      </section>

      {/* Authorization Code Flow */}
      <section className="space-y-4">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Authorization Code Flow
        </h2>
        <div className="flex flex-wrap items-center gap-2 text-sm py-4">
          {['Client', 'authorize()', 'User Consent', 'grant_code()', 'exchange_code()', 'Tokens'].map((step, i, arr) => (
            <span key={i} className="flex items-center gap-2">
              <span className={`px-3 py-1 rounded-lg font-mono text-xs ${isDark ? 'bg-white/5 text-aquilia-400' : 'bg-aquilia-50 text-aquilia-600'}`}>{step}</span>
              {i < arr.length - 1 && <ArrowRight className="w-3 h-3 text-zinc-500" />}
            </span>
          ))}
        </div>
        <CodeBlock language="python" filename="Full Authorization Code Flow">{`from aquilia.auth.oauth import OAuth2Manager

oauth = OAuth2Manager(
    client_store=client_store,
    code_store=code_store,
    device_store=device_store,
    token_manager=token_manager,
    issuer="https://auth.myapp.com",
)

# Step 1: Authorization request
auth_request = await oauth.authorize(
    client_id="app_my-frontend",
    redirect_uri="https://myapp.com/callback",
    scope="profile orders.read",
    state="random-csrf-token",
    code_challenge=challenge,
    code_challenge_method="S256",
)
`}</CodeBlock>
      </section>

      {/* Client Credentials */}
      <section className="space-y-4">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Client Credentials Flow
        </h2>
        <CodeBlock language="python" filename="Machine-to-Machine">{`# Machine-to-machine auth — no user involved
tokens = await oauth.client_credentials_grant(
    client_id="app_backend-service",
    client_secret="service-secret",
    scope="internal.admin",
)
`}</CodeBlock>
      </section>

      {/* Device Flow */}
      <section className="space-y-4">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Device Authorization Flow
        </h2>
        <CodeBlock language="python" filename="Device Flow (TV / CLI)">{`# Step 1: Device requests authorization
device_resp = await oauth.device_authorization(
    client_id="app_tv-app",
    scope="profile",
)
`}</CodeBlock>
      </section>

      {/* OAuth Faults */}
      <section className="space-y-4">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          OAuth Faults
        </h2>
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
                ['AUTH_CLIENT_INVALID', 'AUTH_011', 'Unknown client_id or wrong client_secret.'],
                ['AUTH_GRANT_INVALID', 'AUTH_012', 'Invalid, expired, or used authorization code.'],
                ['AUTH_REDIRECT_URI_MISMATCH', 'AUTH_013', 'redirect_uri not in registered URIs.'],
                ['AUTH_SCOPE_INVALID', 'AUTH_014', 'Requested scope not allowed for client.'],
                ['AUTH_PKCE_INVALID', 'AUTH_015', 'Missing or failed PKCE verification.'],
                ['AUTH_CONSENT_REQUIRED', 'AUTH_301', 'User consent required before code grant.'],
                ['AUTH_DEVICE_CODE_PENDING', 'AUTH_302', 'User hasn\'t approved device yet.'],
                ['AUTH_DEVICE_CODE_EXPIRED', 'AUTH_303', 'Device code expired (15 min TTL).'],
                ['AUTH_SLOW_DOWN', 'AUTH_304', 'Device polling too frequently.'],
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

      {/* Stores */}
      <section className="space-y-4">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          OAuth Stores
        </h2>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          OAuth2Manager requires stores for client data, authorization codes, and device verification tokens.
        </p>
        <div className="overflow-x-auto">
          <table className={`w-full text-sm text-left ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className={`border-b ${isDark ? 'border-zinc-800' : 'border-zinc-200'}`}>
                <th className="py-3 font-semibold text-aquilia-500 font-mono text-xs w-1/2">Store</th>
                <th className="py-3 font-semibold text-aquilia-500 text-xs w-1/2">Purpose</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/10 dark:divide-zinc-800/50">
              {[
                ['MemoryOAuthClientStore', 'CRUD for registered OAuth clients.'],
                ['MemoryAuthorizationCodeStore', 'Manages one-time authentication codes (10 min TTL).'],
                ['MemoryDeviceCodeStore', 'Manages device authorization codes and tracking approval status.'],
              ].map(([s, d], i) => (
                <tr key={i} className="hover:bg-aquilia-500/2 transition-colors duration-200">
                  <td className="py-3 font-mono text-xs text-aquilia-400 font-bold">{s}</td>
                  <td className={`py-3 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{d}</td>
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
