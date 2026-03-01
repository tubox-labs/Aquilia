import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Key, Clock, RotateCw, Database, ShieldCheck } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function AuthTokens() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4"><Key className="w-4 h-4" />Security &amp; Auth</div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Token Management
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          AquilAuth's token system handles JWT-like access token signing/verification, opaque refresh tokens, key ring management with rotation, and multiple signing algorithms (RS256, ES256, EdDSA).
        </p>
      </div>

      {/* Key Management */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}><ShieldCheck className="w-5 h-5 text-aquilia-500" />Key Management</h2>
        <h3 className={`text-lg font-semibold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>KeyDescriptor</h3>
        <CodeBlock language="python" filename="Key Generation">{`from aquilia.auth.tokens import KeyDescriptor, KeyAlgorithm, KeyStatus

# Generate a new key pair
key = KeyDescriptor.generate(
    kid="key_2024_01",                  # Key ID (used in JWT header)
    algorithm=KeyAlgorithm.RS256,       # RS256 | ES256 | EdDSA
)
# KeyDescriptor(
#   kid="key_2024_01",
#   algorithm="RS256",
#   public_key_pem="-----BEGIN PUBLIC KEY-----...",
#   private_key_pem="-----BEGIN PRIVATE KEY-----...",
#   status="active",
#   created_at=datetime(...),
# )

# Key status lifecycle
key.is_active()        # True — can sign AND verify
key.can_verify()       # True for ACTIVE, ROTATING, RETIRED
key.status             # KeyStatus.ACTIVE

# Serialization
data = key.to_dict()               # Dict with PEM keys
key2 = KeyDescriptor.from_dict(data)`}</CodeBlock>

        <div className="overflow-x-auto mt-6">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead><tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
              <th className="text-left py-3 pr-4 text-aquilia-500">Algorithm</th>
              <th className="text-left py-3 pr-4 text-aquilia-500">Key Type</th>
              <th className="text-left py-3 text-aquilia-500">Description</th>
            </tr></thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['RS256', 'RSA 2048-bit', 'RSA with SHA-256 — widely compatible, larger keys'],
                ['ES256', 'ECDSA P-256', 'Elliptic Curve with SHA-256 — smaller keys, fast verification'],
                ['EdDSA', 'Ed25519', 'Edwards Curve — fastest, smallest signatures'],
              ].map(([a, k, d], i) => (
                <tr key={i}>
                  <td className="py-2 pr-4 font-mono text-xs text-aquilia-400">{a}</td>
                  <td className="py-2 pr-4 font-mono text-xs text-gray-500">{k}</td>
                  <td className={`py-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{d}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Key Status */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Key Lifecycle</h2>
        <div className="overflow-x-auto">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead><tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
              <th className="text-left py-3 pr-4 text-aquilia-500">Status</th>
              <th className="text-left py-3 pr-4 text-aquilia-500">Can Sign</th>
              <th className="text-left py-3 pr-4 text-aquilia-500">Can Verify</th>
              <th className="text-left py-3 text-aquilia-500">Description</th>
            </tr></thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['ACTIVE', '✅', '✅', 'Current signing key — only one active at a time'],
                ['ROTATING', '❌', '✅', 'Being promoted — not yet active for signing'],
                ['RETIRED', '❌', '✅', 'No longer signs but still verifies existing tokens'],
                ['REVOKED', '❌', '❌', 'Invalid for all operations — compromised key'],
              ].map(([s, sign, ver, d], i) => (
                <tr key={i}>
                  <td className="py-2 pr-4 font-mono text-xs text-aquilia-400">{s}</td>
                  <td className="py-2 pr-4 text-center">{sign}</td>
                  <td className="py-2 pr-4 text-center">{ver}</td>
                  <td className={`py-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{d}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* KeyRing */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}><RotateCw className="w-5 h-5 text-aquilia-500" />KeyRing &amp; Rotation</h2>
        <CodeBlock language="python" filename="Key Ring">{`from aquilia.auth.tokens import KeyRing, KeyDescriptor, KeyAlgorithm
from pathlib import Path

# Create ring with initial key
key1 = KeyDescriptor.generate(kid="k1", algorithm=KeyAlgorithm.ES256)
ring = KeyRing(keys=[key1])

ring.current_kid                    # "k1"
ring.get_signing_key()              # KeyDescriptor (active)
ring.get_verification_key("k1")     # KeyDescriptor (if can_verify)

# Key Rotation
key2 = KeyDescriptor.generate(kid="k2", algorithm=KeyAlgorithm.ES256)
ring.add_key(key2)                  # Add new key (ACTIVE by default)
ring.promote_key("k2")             # k2 → ACTIVE, k1 → RETIRED

# k1 can still VERIFY (existing tokens remain valid)
# k2 is now the SIGNING key
ring.current_kid                    # "k2"

# Revoke compromised key
ring.revoke_key("k1")              # k1 → REVOKED (can't verify anymore)

# Persistence
ring.to_file(Path("keys.json"))    # Save to disk
ring2 = KeyRing.from_file(Path("keys.json"))  # Load from disk

# Serialization
data = ring.to_dict()
ring3 = KeyRing.from_dict(data)`}</CodeBlock>
      </section>

      {/* TokenManager */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>TokenManager</h2>
        <CodeBlock language="python" filename="Token Configuration">{`from aquilia.auth.tokens import TokenManager, TokenConfig, KeyRing

config = TokenConfig(
    issuer="aquilia",                   # iss claim
    audience=["api"],                   # aud claim
    access_token_ttl=3600,              # 1 hour
    refresh_token_ttl=2592000,          # 30 days
    algorithm=KeyAlgorithm.RS256,       # default signing algorithm
)

manager = TokenManager(
    key_ring=ring,
    token_store=token_store,     # TokenStore protocol
    config=config,
)`}</CodeBlock>
      </section>

      {/* Access Tokens */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Access Tokens (JWT)</h2>
        <CodeBlock language="python" filename="Issue & Validate">{`# Issue signed access token
token = await manager.issue_access_token(
    identity_id="user_42",
    scopes=["profile", "orders.read"],
    roles=["admin"],
    session_id="sess_abc123",
    tenant_id="org_1",
    ttl=7200,                   # override TTL (2 hours)
)
# Format: header.payload.signature
# Header:  {"alg": "RS256", "kid": "k1", "typ": "JWT"}
# Payload: {"iss": "aquilia", "sub": "user_42", "aud": ["api"],
#           "exp": ..., "iat": ..., "nbf": ..., "jti": "at_...",
#           "scopes": ["profile", "orders.read"],
#           "roles": ["admin"], "sid": "sess_abc123", "tenant_id": "org_1"}

# Validate access token — checks:
#   1. Format (3 parts)
#   2. Header (alg, kid)
#   3. Signature (using KeyRing verification key)
#   4. Expiration (exp < now)
#   5. Not-before (nbf)
#   6. Revocation (token_store.is_token_revoked)
payload = await manager.validate_access_token(token)
# Returns decoded payload dict`}</CodeBlock>
      </section>

      {/* Refresh Tokens */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}><Clock className="w-5 h-5 text-aquilia-500" />Refresh Tokens</h2>
        <CodeBlock language="python" filename="Refresh Token Lifecycle">{`# Issue opaque refresh token (stored in token_store)
refresh = await manager.issue_refresh_token(
    identity_id="user_42",
    scopes=["profile"],
    session_id="sess_abc123",
)
# Format: "rt_<random>" — stored in TokenStore with expiration

# Validate refresh token
data = await manager.validate_refresh_token(refresh)
# Returns: {"identity_id": "user_42", "scopes": [...], "expires_at": "...", ...}

# Refresh token rotation (security best practice)
new_access, new_refresh = await manager.refresh_access_token(refresh)
# 1. Validates old refresh token
# 2. Revokes old refresh token (one-time use)
# 3. Issues new access + refresh tokens
# → Prevents replay attacks

# Revocation
await manager.revoke_token("rt_abc...")              # Single token
await manager.revoke_tokens_by_identity("user_42")   # All user tokens
await manager.revoke_tokens_by_session("sess_abc")   # All session tokens`}</CodeBlock>
      </section>

      {/* TokenClaims */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>TokenClaims</h2>
        <div className="overflow-x-auto">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead><tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
              <th className="text-left py-3 pr-4 text-aquilia-500">Claim</th>
              <th className="text-left py-3 pr-4 text-aquilia-500">Type</th>
              <th className="text-left py-3 text-aquilia-500">Description</th>
            </tr></thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['iss', 'str', 'Issuer (e.g., "aquilia")'],
                ['sub', 'str', 'Subject — identity ID'],
                ['aud', 'list[str]', 'Audience (e.g., ["api"])'],
                ['exp', 'int', 'Expiration time (Unix timestamp)'],
                ['iat', 'int', 'Issued at (Unix timestamp)'],
                ['nbf', 'int', 'Not before (Unix timestamp)'],
                ['jti', 'str', 'Token ID — unique per token (at_<random>)'],
                ['scopes', 'list[str]', 'Permitted scopes'],
                ['roles', 'list[str]', 'User roles (custom claim)'],
                ['sid', 'str | None', 'Session ID binding'],
                ['tenant_id', 'str | None', 'Multi-tenant ID'],
              ].map(([c, t, d], i) => (
                <tr key={i}>
                  <td className="py-2 pr-4 font-mono text-xs text-aquilia-400">{c}</td>
                  <td className="py-2 pr-4 font-mono text-xs text-gray-500">{t}</td>
                  <td className={`py-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{d}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* TokenStore Protocol */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}><Database className="w-5 h-5 text-aquilia-500" />TokenStore Protocol</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Token storage follows the <code className="text-aquilia-500">TokenStore</code> protocol. Two implementations are provided: <code className="text-aquilia-500">MemoryTokenStore</code> (dev/test) and <code className="text-aquilia-500">RedisTokenStore</code> (production).
        </p>
        <CodeBlock language="python" filename="TokenStore Protocol">{`class TokenStore(Protocol):
    async def save_refresh_token(self, token_id, identity_id, scopes, expires_at, session_id=None) -> None: ...
    async def get_refresh_token(self, token_id) -> dict | None: ...
    async def revoke_refresh_token(self, token_id) -> None: ...
    async def revoke_tokens_by_identity(self, identity_id) -> None: ...
    async def revoke_tokens_by_session(self, session_id) -> None: ...
    async def is_token_revoked(self, token_id) -> bool: ...

# Built-in implementations:
# MemoryTokenStore   — dict-based, for dev/testing
# RedisTokenStore    — Redis-backed with sorted sets, auto-expiry`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
