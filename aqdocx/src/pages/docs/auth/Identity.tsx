import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Shield, User } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function AuthIdentity() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4"><Shield className="w-4 h-4" />Security &amp; Auth</div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Identity &amp; Credentials
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Deep dive into the credential types — passwords (Argon2id), API keys (scoped, rate-limited), and how they map to the <code className="text-aquilia-500">Identity</code> frozen dataclass.
        </p>
      </div>

      {/* Identity Methods */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}><User className="w-5 h-5 text-blue-500" />Identity Methods</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <code className="text-aquilia-500">Identity</code> is a frozen dataclass — immutable after creation. It provides convenience methods for attribute access and serialization.
        </p>
        <CodeBlock language="python" filename="Identity API">{`from aquilia.auth.core import Identity, IdentityType, IdentityStatus

identity = Identity(
    id="user_42",
    type=IdentityType.USER,
    attributes={
        "email": "alice@example.com",
        "name": "Alice",
        "roles": ["admin", "editor"],
        "scopes": ["read", "write", "admin:write"],
    },
    status=IdentityStatus.ACTIVE,
    tenant_id="org_1",
)

# Attribute access
identity.get_attribute("email")      # "alice@example.com"
identity.get_attribute("missing")    # None
identity.get_attribute("missing", "default")  # "default"

# Role / scope checks
identity.has_role("admin")           # True
identity.has_role("superadmin")      # False
identity.has_scope("read")           # True
identity.has_scope("admin:write")    # True

# Status checks
identity.is_active()                 # True (ACTIVE)
# Also checks: SUSPENDED → False, DELETED → False, PENDING → False

# Serialization
data = identity.to_dict()
restored = Identity.from_dict(data)`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>PasswordCredential</h2>
        <CodeBlock language="python" filename="Password Auth">{`from aquilia.auth.core import PasswordCredential

cred = PasswordCredential(
    identity_id="user_42",
    password_hash="$argon2id$v=19$m=65536,t=3,p=4$...",
    algorithm="argon2id",          # primary hasher
    must_change=False,
)

# Check rotation policy (default: 90 days)
if cred.should_rotate(max_age_days=90):
    # Prompt user to change password
    ...

# Touch on successful login — updates last_used_at
cred.touch()

# Serialization
data = cred.to_dict()`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>ApiKeyCredential</h2>
        <CodeBlock language="python" filename="API Key Auth">{`from aquilia.auth.core import ApiKeyCredential

# Key format: ak_<env>_<random>
# Example: ak_live_1234567890abcdef

key = ApiKeyCredential(
    identity_id="service_7",
    key_id="key_abc123",
    key_hash="sha256:...",          # SHA-256 of the raw key
    prefix="ak_live_",              # First 8 chars for identification
    scopes=["read:users", "write:orders"],
    rate_limit=100,                 # 100 requests per minute
    expires_at=None,                # Never expires (or set a datetime)
)

# Security checks
key.is_expired()     # False
key.has_scope("read:users")  # True

# Keys are hashed before storage — raw key only shown once at creation`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Identity Types</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { type: 'USER', desc: 'Human user with email, roles, and interactive sessions.' },
            { type: 'SERVICE', desc: 'Machine-to-machine identity for microservices and APIs.' },
            { type: 'DEVICE', desc: 'IoT or device identity for hardware-based authentication.' },
            { type: 'ANONYMOUS', desc: 'Unauthenticated principal with minimal permissions.' },
          ].map((item, i) => (
            <div key={i} className={boxClass}>
              <span className="text-aquilia-500 font-mono font-bold text-sm">{item.type}</span>
              <p className={`mt-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Identity Status</h2>
        <div className="overflow-x-auto">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead><tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
              <th className="text-left py-3 pr-4 text-aquilia-500">Status</th>
              <th className="text-left py-3 text-aquilia-500">Meaning</th>
            </tr></thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['ACTIVE', 'Identity is valid and can authenticate. is_active() returns True.'],
                ['SUSPENDED', 'Temporarily disabled by an administrator — can be reactivated.'],
                ['DELETED', 'Soft-deleted — identity data preserved but access denied.'],
                ['PENDING', 'Account created but not yet activated (e.g. awaiting email verification).'],
              ].map(([s, d], i) => (
                <tr key={i}>
                  <td className="py-2.5 pr-4 font-mono text-xs text-aquilia-400">{s}</td>
                  <td className={`py-2.5 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{d}</td>
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