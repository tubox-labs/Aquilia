import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Shield, User, Cpu, Laptop, HelpCircle } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function AuthIdentity() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto space-y-12">
      <div className="space-y-4">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium tracking-wide">
          <Shield className="w-4 h-4" />
          <span>Security &amp; Auth / Identity</span>
        </div>
        <h1 className={`text-4xl font-extrabold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="gradient-text font-mono relative group inline-block">
            Identity &amp; Credentials
            <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Deep dive into credential types — passwords (Argon2id), API keys (scoped, rate-limited), and how they map to the <DocTerm id="auth.identity">Identity</DocTerm> frozen dataclass.
        </p>
      </div>

      {/* Identity Methods */}
      <section className="space-y-6">
        <h2 className={`text-2.5xl font-bold tracking-tight flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <User className="w-6 h-6 text-blue-500" />
          <span>Identity Methods</span>
        </h2>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <DocTerm id="auth.identity">Identity</DocTerm> is a frozen dataclass — immutable after creation. It provides convenience methods for attribute access, permissions, and serialization.
        </p>
        <CodeBlock language="python" filename="Identity API">
{`from aquilia.auth.core import Identity, IdentityType, IdentityStatus

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
restored = Identity.from_dict(data)`}
        </CodeBlock>
      </section>

      {/* PasswordCredential */}
      <section className="space-y-6">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          PasswordCredential
        </h2>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <DocTerm id="auth.password_credential">PasswordCredential</DocTerm> manages authentication secrets for interactive users using modern hashing.
        </p>
        <CodeBlock language="python" filename="Password Auth">
{`from aquilia.auth.core import PasswordCredential

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
data = cred.to_dict()`}
        </CodeBlock>
      </section>

      {/* ApiKeyCredential */}
      <section className="space-y-6">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          ApiKeyCredential
        </h2>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <DocTerm id="auth.api_key_credential">ApiKeyCredential</DocTerm> facilitates secure machine-to-machine client validations with customizable rate limits and scopes.
        </p>
        <CodeBlock language="python" filename="API Key Auth">
{`from aquilia.auth.core import ApiKeyCredential

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

# Keys are hashed before storage — raw key only shown once at creation`}
        </CodeBlock>
      </section>

      {/* Identity Types - Premium Redesign */}
      <section className="space-y-6">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>Identity Types</h2>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia natively supports different types of entities accessing the platform. Each type has specialized lifecycles and authentication workflows:
        </p>
        <div className="space-y-4">
          {[
            { type: 'USER', desc: 'Human user with email, roles, and interactive browser/OAuth sessions.', icon: <User className="w-5 h-5" />, color: 'from-blue-500/20 to-blue-500/5', iconColor: 'text-blue-500' },
            { type: 'SERVICE', desc: 'Machine-to-machine identity for backend tasks, microservices, and external API requests.', icon: <Cpu className="w-5 h-5" />, color: 'from-purple-500/20 to-purple-500/5', iconColor: 'text-purple-500' },
            { type: 'DEVICE', desc: 'IoT or hardware identity for localized, physical machine authentication.', icon: <Laptop className="w-5 h-5" />, color: 'from-cyan-500/20 to-cyan-500/5', iconColor: 'text-cyan-500' },
            { type: 'ANONYMOUS', desc: 'Fallback unauthenticated principal carrying base context with guest permissions.', icon: <HelpCircle className="w-5 h-5" />, color: 'from-amber-500/20 to-amber-500/5', iconColor: 'text-amber-500' },
          ].map((item, i) => (
            <div key={i} className="group flex items-start gap-5 p-4 rounded-xl hover:bg-aquilia-500/5 dark:hover:bg-white/5 transition-all duration-300">
              <div className={`p-3 rounded-lg bg-gradient-to-br ${item.color} ${item.iconColor} transition-transform duration-300 group-hover:scale-110 shrink-0`}>
                {item.icon}
              </div>
              <div className="space-y-1">
                <span className="font-mono font-bold text-sm text-aquilia-500 tracking-wide">{item.type}</span>
                <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{item.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Identity Status */}
      <section className="space-y-6">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>Identity Status</h2>
        <div className="overflow-x-auto">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
                <th className="text-left py-3 pr-4 text-aquilia-500">Status</th>
                <th className="text-left py-3 text-aquilia-500">Meaning</th>
              </tr>
            </thead>
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