import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Shield, Lock, Key } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function AuthCredentials() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Shield className="w-4 h-4" />
          Auth / Credentials &amp; Hashers
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Credentials &amp; Hashers
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Password hashing with Argon2id (primary) and PBKDF2 (fallback), password policy enforcement with HIBP breach checking, and async-safe convenience functions.
        </p>
      </div>

      {/* PasswordHasher */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}><Lock className="w-5 h-5 text-green-500" />PasswordHasher</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">PasswordHasher</code> uses Argon2id as the primary algorithm with PBKDF2 as a fallback. All operations are async-safe — hashing runs in a thread executor to avoid blocking the event loop.
        </p>
        <CodeBlock language="python" filename="hashing.py">{`from aquilia.auth.hashing import PasswordHasher

hasher = PasswordHasher(
    algorithm="argon2id",       # primary algorithm
    memory_cost=65536,          # 64 MiB
    time_cost=3,                # 3 iterations
    parallelism=4,              # 4 threads
    hash_length=32,             # 32-byte output
    salt_length=16,             # 16-byte salt
    fallback_algorithm="pbkdf2",# PBKDF2-SHA256 fallback
)

# Async hash and verify (runs in thread pool)
hashed = await hasher.hash_async("MyP@ssw0rd!")
is_valid = await hasher.verify_async("MyP@ssw0rd!", hashed)  # → True

# Rehash check — detects when params have changed
if hasher.check_needs_rehash(hashed):
    new_hash = await hasher.hash_async(password)
    await credential_store.update_password(identity_id, new_hash)`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-8 mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Convenience Functions</h3>
        <CodeBlock language="python" filename="Shorthand">{`from aquilia.auth.hashing import hash_password, verify_password, validate_password

# Quick hash and verify (uses default PasswordHasher)
hashed = hash_password("MyP@ssw0rd!")
ok = verify_password("MyP@ssw0rd!", hashed)

# Validate against policy (sync helper)
result = validate_password("weak", policy)
# result.valid → False
# result.errors → ["Too short", "Missing digit", ...]`}</CodeBlock>
      </section>

      {/* PasswordPolicy */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}><Key className="w-5 h-5 text-amber-500" />PasswordPolicy</h2>
        <CodeBlock language="python" filename="Policy Configuration">{`from aquilia.auth.hashing import PasswordPolicy

policy = PasswordPolicy(
    min_length=12,                # minimum 12 characters
    require_uppercase=True,       # at least one A-Z
    require_lowercase=True,       # at least one a-z
    require_digit=True,           # at least one 0-9
    require_special=True,         # at least one !@#$%...
    max_repeated_chars=3,         # max 3 consecutive identical chars
    blacklist=["password", "qwerty", "123456"],  # banned passwords
    check_breached=True,          # HIBP breach check
    prevent_reuse=5,              # remember last 5 password hashes
)

# Validate — async because breach check calls HIBP API
result = await policy.validate_async("MyP@ssw0rd!")
if not result.valid:
    print(result.errors)
    # → ["Password found in breach database (HIBP)"]`}</CodeBlock>

        <div className={`mt-4 p-4 rounded-xl border-l-4 border-amber-500 ${isDark ? 'bg-amber-500/10' : 'bg-amber-50'}`}>
          <p className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <strong>HIBP k-Anonymity:</strong> Only the first 5 characters of the SHA-1 hash are sent to the HIBP API. The full hash is never transmitted — the response is checked locally using range queries.
          </p>
        </div>
      </section>

      {/* Hasher Parameters */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Hasher Parameters</h2>
        <div className="overflow-x-auto">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead><tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
              <th className="text-left py-3 pr-4 text-aquilia-500">Parameter</th>
              <th className="text-left py-3 pr-4 text-aquilia-500">Default</th>
              <th className="text-left py-3 text-aquilia-500">Description</th>
            </tr></thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['algorithm', 'argon2id', 'Primary hash algorithm (argon2id recommended)'],
                ['memory_cost', '65536', 'Memory in KiB (64 MiB) — higher = more resistant'],
                ['time_cost', '3', 'Number of iterations — higher = slower hashing'],
                ['parallelism', '4', 'Thread count for Argon2 — match CPU cores'],
                ['hash_length', '32', 'Output hash length in bytes'],
                ['salt_length', '16', 'Random salt length in bytes'],
                ['fallback_algorithm', 'pbkdf2', 'Fallback for verification of legacy hashes'],
              ].map(([p, d, desc], i) => (
                <tr key={i}>
                  <td className="py-2 pr-4 font-mono text-xs text-aquilia-400">{p}</td>
                  <td className="py-2 pr-4 font-mono text-xs text-gray-500">{d}</td>
                  <td className={`py-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* OAuthClient & MFACredential summary */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Other Credential Types</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { title: 'OAuthClient', desc: 'Registered OAuth 2.0 application with client_id, secret_hash, redirect_uris, grant_types, PKCE support, consent tracking, and configurable TTLs.', link: '/docs/auth/oauth', color: '#3b82f6' },
            { title: 'MFACredential', desc: 'Multi-factor credential supporting TOTP, WebAuthn, SMS, and email methods. Includes backup codes and webauthn_credentials.', link: '/docs/auth/mfa', color: '#22c55e' },
          ].map((c, i) => (
            <div key={i} className={boxClass}>
              <span className="font-mono font-bold text-sm" style={{ color: c.color }}>{c.title}</span>
              <p className={`mt-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{c.desc}</p>
            </div>
          ))}
        </div>
      </section>
    
      <NextSteps />
    </div>
  )
}