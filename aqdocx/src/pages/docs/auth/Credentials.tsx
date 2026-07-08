import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Shield, Lock, Key } from 'lucide-react'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'


export function AuthCredentials() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto space-y-16">
      {/* Header Section */}
      <div className="space-y-4">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium tracking-wide">
          <Shield className="w-4 h-4" />
          <span>Auth / Credentials &amp; Hashers</span>
        </div>
        <h1 className={`text-4xl font-extrabold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="gradient-text font-mono relative group inline-block">
            Credentials &amp; Hashers
            <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Password hashing with Argon2id (primary) and PBKDF2 (fallback), password policy enforcement with HIBP breach checking, and async-safe convenience functions.
        </p>
      </div>

      {/* PasswordHasher */}
      <section className="space-y-4">
        <h2 className={`text-2.5xl font-bold tracking-tight flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Lock className="w-6 h-6 text-green-500" />
          <span>PasswordHasher</span>
        </h2>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500 font-mono text-xs">PasswordHasher</code> uses Argon2id as the primary algorithm with PBKDF2 as a fallback. All operations are async-safe — hashing runs in a thread executor to avoid blocking the event loop.
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

        <h3 className={`text-lg font-bold pt-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Convenience Functions
        </h3>
        <CodeBlock language="python" filename="Shorthand">{`from aquilia.auth.hashing import hash_password, verify_password, validate_password

# Quick hash and verify (uses default PasswordHasher)
hashed = hash_password("MyP@ssw0rd!")
ok = verify_password("MyP@ssw0rd!", hashed)

# Validate against policy (sync helper)
is_valid, errors = validate_password("weak", policy)
# is_valid  → False
# errors    → ["Password must be at least 12 characters", ...]`}</CodeBlock>
      </section>

      {/* PasswordPolicy */}
      <section className="space-y-4">
        <h2 className={`text-2.5xl font-bold tracking-tight flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Key className="w-6 h-6 text-amber-500" />
          <span>PasswordPolicy</span>
        </h2>
        <CodeBlock language="python" filename="Policy Configuration">{`from aquilia.auth.hashing import PasswordPolicy

policy = PasswordPolicy(
    min_length=12,                # minimum 12 characters
    require_uppercase=True,       # at least one A-Z
    require_lowercase=True,       # at least one a-z
    require_digit=True,           # at least one 0-9
    require_special=True,         # at least one special char
    check_breached=True,          # HIBP breach check
)

# Validate — async because breach check calls HIBP API
is_valid, errors = await policy.validate_async("MyP@ssw0rd!")
if not is_valid:
    print(errors)
    # → ["Password has been found in data breaches"]`}</CodeBlock>

        <div className={`mt-4 p-4 rounded-xl border-l-4 border-amber-500 ${isDark ? 'bg-amber-500/10' : 'bg-amber-50'}`}>
          <p className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <strong>HIBP k-Anonymity:</strong> Only the first 5 characters of the SHA-1 hash are sent to the HIBP API. The full hash is never transmitted — the response is checked locally using range queries.
          </p>
        </div>
      </section>

      {/* Hasher Parameters */}
      <section className="space-y-4">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Hasher Parameters
        </h2>
        <div className="overflow-x-auto">
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
                ['algorithm', 'argon2id', 'Primary hash algorithm (argon2id recommended).'],
                ['memory_cost', '65536', 'Memory in KiB (64 MiB) — higher = more resistant.'],
                ['time_cost', '3', 'Number of iterations — higher = slower hashing.'],
                ['parallelism', '4', 'Thread count for Argon2 — match CPU cores.'],
                ['hash_length', '32', 'Output hash length in bytes.'],
                ['salt_length', '16', 'Random salt length in bytes.'],
                ['fallback_algorithm', 'pbkdf2', 'Fallback for verification of legacy hashes.'],
              ].map(([p, d, desc], i) => (
                <tr key={i} className="hover:bg-aquilia-500/2 transition-colors duration-200">
                  <td className="py-3 font-mono text-xs text-aquilia-400 font-bold">{p}</td>
                  <td className="py-3 font-mono text-xs text-gray-500">{d}</td>
                  <td className={`py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* OAuthClient & MFACredential summary */}
      <section className="space-y-6">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Other Credential Types
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[
            { title: 'OAuthClient', desc: 'Registered OAuth 2.0 application with client ID, secret hash, redirect URIs, and configurable grant types.', link: '/docs/auth/oauth', color: '#3b82f6' },
            { title: 'MFACredential', desc: 'Multi-factor credential supporting TOTP, WebAuthn, SMS, and email methods with backup recovery code hashes.', link: '/docs/auth/mfa', color: '#22c55e' },
          ].map((c, i) => (
            <Link key={i} to={c.link} className="flex gap-4 p-5 rounded-xl hover:bg-aquilia-500/5 transition-all duration-300 group border border-transparent hover:border-aquilia-500/10">
              <div className="mt-1 p-2 rounded-lg bg-aquilia-500/10 group-hover:scale-105 transition-all" style={{ color: c.color }}>
                <Shield className="w-5 h-5" />
              </div>
              <div className="space-y-1">
                <span className="font-bold text-sm font-mono block" style={{ color: c.color }}>
                  {c.title}
                </span>
                <p className={`text-xs leading-normal ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  {c.desc}
                </p>
              </div>
            </Link>
          ))}
        </div>
      </section>
    
      <NextSteps />
    </div>
  )
}