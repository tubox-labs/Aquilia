import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Database, HardDrive, Server, Archive } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function AuthStores() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4"><Database className="w-4 h-4" />Security &amp; Auth</div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Stores &amp; Persistence
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          AquilAuth uses protocol-based stores for identities, credentials, tokens, and OAuth data. Memory implementations are provided for development; swap in Redis or database-backed stores for production.
        </p>
      </div>

      {/* Store Overview */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Store Architecture</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {[
            { icon: <HardDrive className="w-5 h-5" />, title: 'MemoryIdentityStore', desc: 'In-memory identity storage with attribute indexing. Async-safe with asyncio.Lock. Supports create, get, get_by_attribute, update, delete (soft), list_by_tenant.', color: '#22c55e' },
            { icon: <Archive className="w-5 h-5" />, title: 'MemoryCredentialStore', desc: 'Stores passwords, API keys, and MFA credentials. Separate dictionaries per credential type. Supports prefix-based API key lookup.', color: '#f59e0b' },
            { icon: <Database className="w-5 h-5" />, title: 'MemoryTokenStore', desc: 'Refresh token storage with revocation tracking. Tracks tokens by identity and session for bulk revocation. Expired token cleanup.', color: '#3b82f6' },
            { icon: <Server className="w-5 h-5" />, title: 'RedisTokenStore', desc: 'Production Redis-backed store. Hash-per-token, sorted sets for expiry, set-based revocation checks. Auto-cleanup via Redis TTL.', color: '#ef4444' },
          ].map((s, i) => (
            <div key={i} className={boxClass}>
              <div className="flex items-center gap-2 mb-2" style={{ color: s.color }}>{s.icon}<span className="font-semibold text-sm">{s.title}</span></div>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Identity Store */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>IdentityStore Protocol</h2>
        <CodeBlock language="python" filename="IdentityStore">{`class IdentityStore(Protocol):
    async def create(self, identity: Identity) -> None: ...
    async def get(self, identity_id: str) -> Identity | None: ...
    async def get_by_attribute(self, key: str, value: Any) -> Identity | None: ...
    async def update(self, identity: Identity) -> None: ...
    async def delete(self, identity_id: str) -> None: ...        # soft delete
    async def list_by_tenant(self, tenant_id: str) -> list[Identity]: ...`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-8 mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>MemoryIdentityStore</h3>
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

# Lookup by attribute (fast O(1) index)
user = await store.get_by_attribute("email", "alice@example.com")

# Soft delete — sets status to DELETED
await store.delete("user_42")

# List by tenant (excludes DELETED)
users = await store.list_by_tenant("org_1", limit=100, offset=0)`}</CodeBlock>
      </section>

      {/* Credential Store */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>CredentialStore Protocol</h2>
        <CodeBlock language="python" filename="CredentialStore">{`class CredentialStore(Protocol):
    # Password credentials
    async def create_password(self, credential: PasswordCredential) -> None: ...
    async def get_password(self, identity_id: str) -> PasswordCredential | None: ...
    async def update_password(self, credential: PasswordCredential) -> None: ...
    
    # API key credentials
    async def create_api_key(self, credential: ApiKeyCredential) -> None: ...
    async def get_api_key(self, key_id: str) -> ApiKeyCredential | None: ...
    async def get_api_key_by_hash(self, key_hash: str) -> ApiKeyCredential | None: ...
    async def list_api_keys(self, identity_id: str) -> list[ApiKeyCredential]: ...
    async def revoke_api_key(self, key_id: str) -> None: ...
    
    # MFA credentials
    async def create_mfa(self, credential: MFACredential) -> None: ...
    async def get_mfa(self, identity_id: str) -> list[MFACredential]: ...
    async def update_mfa(self, credential: MFACredential) -> None: ...`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-8 mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>MemoryCredentialStore</h3>
        <CodeBlock language="python" filename="Credential Operations">{`from aquilia.auth.stores import MemoryCredentialStore
from aquilia.auth.core import PasswordCredential, ApiKeyCredential, MFACredential

store = MemoryCredentialStore()

# Password — keyed by identity_id
await store.save_password(PasswordCredential(
    identity_id="user_42",
    password_hash="$argon2id$v=19$m=65536,t=2,p=4$...",
))
cred = await store.get_password("user_42")

# API Keys — keyed by key_id, searchable by prefix
await store.save_api_key(ApiKeyCredential(
    identity_id="user_42", key_id="key_1",
    key_hash="sha256...", prefix="ak_live_",
    scopes=["read", "write"],
))
key = await store.get_api_key_by_prefix("ak_live_")
keys = await store.list_api_keys("user_42")

# MFA — keyed by identity_id, one per mfa_type
await store.save_mfa(MFACredential(
    identity_id="user_42", mfa_type="totp",
    mfa_secret="base32secret",
))
mfa_list = await store.get_mfa("user_42", mfa_type="totp")`}</CodeBlock>
      </section>

      {/* OAuth Stores */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>OAuth Stores</h2>
        <CodeBlock language="python" filename="OAuth Stores">{`from aquilia.auth.stores import (
    MemoryOAuthClientStore,
    MemoryAuthorizationCodeStore,
    MemoryDeviceCodeStore,
)

# OAuth Client Store — CRUD for registered clients
client_store = MemoryOAuthClientStore()
await client_store.create(oauth_client)
client = await client_store.get("app_my-frontend")

# Authorization Code Store — one-time auth codes
code_store = MemoryAuthorizationCodeStore()
await code_store.save_code(
    code="ac_abc123", client_id="app_1",
    identity_id="user_42", redirect_uri="https://...",
    scopes=["profile"], expires_at=datetime.utcnow() + timedelta(minutes=10),
    code_challenge="sha256...", code_challenge_method="S256",
)
data = await code_store.get_code("ac_abc123")
consumed = await code_store.consume_code("ac_abc123")  # one-time use
await code_store.cleanup_expired()  # remove used/expired codes

# Device Code Store — device authorization flow
device_store = MemoryDeviceCodeStore()
await device_store.save_device_code(
    device_code="dc_xyz", user_code="WDJB-MJHT",
    client_id="app_tv", scopes=["profile"],
    expires_at=datetime.utcnow() + timedelta(minutes=15),
)
await device_store.authorize_device_code("WDJB-MJHT", identity_id="user_42")
await device_store.deny_device_code("WDJB-MJHT")`}</CodeBlock>
      </section>

      {/* Redis Token Store */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}><Server className="w-5 h-5 text-red-500" />RedisTokenStore (Production)</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          For production deployments, <code className="text-aquilia-500">RedisTokenStore</code> provides fast revocation checks and automatic TTL-based cleanup.
        </p>
        <CodeBlock language="python" filename="Redis Backend">{`from aquilia.auth.stores import RedisTokenStore

store = RedisTokenStore(
    redis_client=aioredis_client,       # aioredis async client
    key_prefix="aquilauth:",            # Redis key namespace
)

# Key structure:
#   aquilauth:token:<token_id>          → Hash (token data)
#   aquilauth:identity:<id>:tokens      → Set (token IDs)
#   aquilauth:session:<sid>:tokens      → Set (token IDs)
#   aquilauth:revoked                   → Set (revoked token IDs)

# All operations respect Redis TTL for auto-cleanup
# Revocation checks: O(1) SISMEMBER on revoked set
# Bulk revocation: SMEMBERS + SADD pipeline`}</CodeBlock>
      </section>

      {/* Crous Artifacts */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Crous Artifacts &amp; Audit</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Auth configuration and audit events can be stored as signed <code className="text-aquilia-500">CrousArtifact</code> objects — immutable records with SHA-256 hashes and RSA signatures.
        </p>
        <CodeBlock language="python" filename="Crous Integration">{`from aquilia.auth.crous import (
    KeyArtifact, PolicyArtifact, AuditEventArtifact,
    ArtifactSigner, AuditLogger, MemoryArtifactStore,
)

# Signed key artifact
key_artifact = KeyArtifact(
    artifact_id="key_art_001",
    key_descriptor=key,
    created_by="admin",
)

# Signed policy artifact
policy_artifact = PolicyArtifact(
    artifact_id="pol_art_001",
    policy_id="order_access",
    policy_data={"rules": [...]},
    created_by="admin",
)

# Audit logging with automatic artifact creation
store = MemoryArtifactStore()
signer = ArtifactSigner(signing_key=key)
logger = AuditLogger(artifact_store=store, signer=signer)

event = await logger.log_event(
    event_type="auth_login",
    result="success",
    identity_id="user_42",
    resource="api/v1/orders",
    action="authenticate",
    details={"method": "password", "ip": "1.2.3.4"},
)

# Query audit events
events = await logger.query_events(
    event_type="auth_login",
    identity_id="user_42",
    start_time=datetime(2024, 1, 1),
)`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
