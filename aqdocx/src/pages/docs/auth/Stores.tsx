import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Database, HardDrive, Server, Archive } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'


export function AuthStores() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto space-y-16">
      {/* Header Section */}
      <div className="space-y-4">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium tracking-wide">
          <Database className="w-4 h-4" />
          <span>Security &amp; Auth</span>
        </div>
        <h1 className={`text-4xl font-extrabold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="gradient-text font-mono relative group inline-block">
            Stores &amp; Persistence
            <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          AquilAuth uses protocol-based stores for identities, credentials, tokens, and OAuth data. Memory implementations are provided for development; swap in Redis or database-backed stores for production.
        </p>
      </div>

      {/* Store Overview */}
      <section className="space-y-6">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Store Architecture
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {[
            { icon: <HardDrive className="w-5 h-5" />, title: 'MemoryIdentityStore', desc: 'In-memory identity storage with attribute indexing. Async-safe with asyncio.Lock. Supports create, get, update, and soft delete.', color: '#22c55e' },
            { icon: <Archive className="w-5 h-5" />, title: 'MemoryCredentialStore', desc: 'Stores passwords, API keys, and MFA credentials. Separate dictionaries per credential type. Supports prefix-based lookup.', color: '#f59e0b' },
            { icon: <Database className="w-5 h-5" />, title: 'MemoryTokenStore', desc: 'Refresh token storage with revocation tracking. Tracks tokens by identity and session for bulk revocation.', color: '#3b82f6' },
            { icon: <Server className="w-5 h-5" />, title: 'RedisTokenStore', desc: 'Production Redis-backed store. Hash-per-token, sorted sets for expiry, set-based revocation checks. Auto-cleanup via Redis TTL.', color: '#ef4444' },
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

      {/* Identity Store */}
      <section className="space-y-4">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          IdentityStore Protocol
        </h2>
        <CodeBlock language="python" filename="IdentityStore">{`class IdentityStore(Protocol):
    async def create(self, identity: Identity) -> None: ...
    async def get(self, identity_id: str) -> Identity | None: ...
    async def get_by_attribute(self, key: str, value: Any) -> Identity | None: ...
    async def update(self, identity: Identity) -> None: ...
    async def delete(self, identity_id: str) -> None: ...        # soft delete
    async def list_by_tenant(self, tenant_id: str) -> list[Identity]: ...`}</CodeBlock>

        <h3 className={`text-lg font-bold pt-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          MemoryIdentityStore
        </h3>
        <CodeBlock language="python" filename="Usage">{`from aquilia.auth.stores import MemoryIdentityStore
from aquilia.auth.core import Identity, IdentityType, IdentityStatus

store = MemoryIdentityStore()

# Create — auto-indexes string/int/bool attributes
identity = Identity(
    id="user_42", type=IdentityType.USER,
    attributes={"email": "alice@example.com", "roles": ["admin"]},
    tenant_id="org_1",
)
await store.create(identity)
`}</CodeBlock>
      </section>

      {/* Credential Store */}
      <section className="space-y-4">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          CredentialStore Protocol
        </h2>
        <CodeBlock language="python" filename="CredentialStore">{`class CredentialStore(Protocol):
    # Password credentials
    async def create_password(self, credential: PasswordCredential) -> None: ...
    async def get_password(self, identity_id: str) -> PasswordCredential | None: ...
    async def update_password(self, credential: PasswordCredential) -> None: ...
`}</CodeBlock>
      </section>

      {/* OAuth Stores */}
      <section className="space-y-4">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          OAuth Stores
        </h2>
        <CodeBlock language="python" filename="OAuth Stores">{`from aquilia.auth.stores import (
    MemoryOAuthClientStore,
    MemoryAuthorizationCodeStore,
    MemoryDeviceCodeStore,
)
`}</CodeBlock>
      </section>

      {/* Redis Token Store */}
      <section className="space-y-4">
        <h2 className={`text-2.5xl font-bold tracking-tight flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Server className="w-6 h-6 text-red-500" />
          <span>RedisTokenStore (Production)</span>
        </h2>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          For production deployments, <code className="text-aquilia-500 font-mono text-xs">RedisTokenStore</code> provides fast revocation checks and automatic TTL-based cleanup.
        </p>
        <CodeBlock language="python" filename="Redis Backend">{`from aquilia.auth.stores import RedisTokenStore

store = RedisTokenStore(
    redis_client=aioredis_client,       # aioredis async client
    key_prefix="aquilauth:",            # Redis key namespace
)
`}</CodeBlock>
      </section>



      <NextSteps />
    </div>
  )
}
