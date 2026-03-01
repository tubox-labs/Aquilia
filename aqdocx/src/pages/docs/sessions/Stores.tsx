import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Database } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function SessionsStores() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Database className="w-4 h-4" />
          Sessions / Stores
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Session Stores
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Session stores are pluggable backends that persist session data. Aquilia ships with <code className="text-aquilia-500">MemoryStore</code> (LRU-based in-memory) and <code className="text-aquilia-500">FileStore</code> (JSON file-per-session), both implementing the <code className="text-aquilia-500">SessionStore</code> protocol.
        </p>
      </div>

      {/* SessionStore Protocol */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>SessionStore Protocol</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          All stores implement the <code className="text-aquilia-500">SessionStore</code> protocol:
        </p>
        <CodeBlock language="python" filename="protocol.py">{`from typing import Protocol, Optional
from aquilia.sessions import Session, SessionID


class SessionStore(Protocol):
    """Protocol for session storage backends."""

    async def load(self, session_id: SessionID) -> Optional[Session]:
        """Load a session by ID. Returns None if not found."""
        ...

    async def save(self, session: Session) -> None:
        """Persist a session (create or update)."""
        ...

    async def delete(self, session_id: SessionID) -> None:
        """Delete a session by ID."""
        ...

    async def exists(self, session_id: SessionID) -> bool:
        """Check if a session exists."""
        ...

    async def clear(self) -> None:
        """Delete all sessions from the store."""
        ...

    async def count(self) -> int:
        """Return the total number of stored sessions."""
        ...

    async def cleanup_expired(self) -> int:
        """Remove expired sessions. Returns count of removed sessions."""
        ...

    async def find_by_principal(
        self, principal_kind: str, principal_id: str
    ) -> list[Session]:
        """Find all sessions belonging to a specific principal."""
        ...`}</CodeBlock>
      </section>

      {/* MemoryStore */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>MemoryStore</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          An in-memory store with LRU eviction, principal indexing, and async locking. Ideal for development and single-process deployments.
        </p>
        <CodeBlock language="python" filename="memory_store.py">{`from aquilia.sessions import MemoryStore

# Direct construction
store = MemoryStore(
    max_sessions=10_000,    # LRU evicts when exceeded
    ttl_seconds=7200,       # Default TTL for stored sessions
)

# Factory methods for common configurations:

# Web-optimized: Higher capacity, moderate TTL
store = MemoryStore.web_optimized(max_sessions=10_000)

# API-optimized: Moderate capacity, longer TTL
store = MemoryStore.api_optimized(max_sessions=5_000)

# Mobile-optimized: Lower capacity, long TTL
store = MemoryStore.mobile_optimized(max_sessions=2_000)

# Development-focused: Low capacity, short TTL, verbose logging
store = MemoryStore.development_focused()

# High-throughput: Maximum capacity, minimal overhead
store = MemoryStore.high_throughput(max_sessions=100_000)`}</CodeBlock>

        <h3 className={`text-xl font-semibold mt-8 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>LRU Eviction</h3>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          When <code className="text-aquilia-500">max_sessions</code> is reached, the least-recently-used session is evicted:
        </p>
        <CodeBlock language="python" filename="lru.py">{`store = MemoryStore(max_sessions=3)

# Fill the store
await store.save(session_a)  # [A]
await store.save(session_b)  # [A, B]
await store.save(session_c)  # [A, B, C]

# Access A to make it "recently used"
await store.load(session_a.id)  # [B, C, A]

# Adding D evicts B (least recently used)
await store.save(session_d)  # [C, A, D]
await store.load(session_b.id)  # None — evicted`}</CodeBlock>

        <h3 className={`text-xl font-semibold mt-8 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Principal Index</h3>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          MemoryStore maintains a secondary index by principal for fast lookups:
        </p>
        <CodeBlock language="python" filename="principal_index.py">{`# Find all sessions for a specific user
sessions = await store.find_by_principal("user", "42")
print(f"User 42 has {len(sessions)} active sessions")

# Used by the engine for concurrency control:
# engine.check_concurrency() calls find_by_principal() 
# to count active sessions per user`}</CodeBlock>
      </section>

      {/* FileStore */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>FileStore</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          A file-based store that persists each session as a JSON file. Good for development, testing, and low-traffic deployments where persistence across restarts is needed.
        </p>
        <CodeBlock language="python" filename="file_store.py">{`from aquilia.sessions import FileStore

# Basic construction
store = FileStore(
    directory="/var/lib/aquilia/sessions",
    file_extension=".json",
)

# Session files are created as:
# /var/lib/aquilia/sessions/sess_A1b2C3d4E5f6G7h8.json
# /var/lib/aquilia/sessions/sess_X9y8Z7w6V5u4T3s2.json

# Atomic writes — uses tempfile + os.replace for crash safety
# Each file contains the full session as JSON:
# {
#   "id": "sess_A1b2C3d4E5f6G7h8...",
#   "data": {"cart": [...], "theme": "dark"},
#   "principal": {"kind": "user", "id": "42"},
#   "created_at": "2024-01-15T10:00:00Z",
#   "last_accessed_at": "2024-01-15T10:15:00Z",
#   "expires_at": "2024-01-15T12:00:00Z",
#   "scope": "USER",
#   "flags": ["AUTHENTICATED"],
#   "version": 3
# }`}</CodeBlock>
      </section>

      {/* Custom Store */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Building a Custom Store</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Implement the <code className="text-aquilia-500">SessionStore</code> protocol to create a Redis, PostgreSQL, or other backend:
        </p>
        <CodeBlock language="python" filename="redis_store.py">{`import json
from typing import Optional
from aquilia.sessions import Session, SessionID


class RedisStore:
    """Custom Redis session store."""

    def __init__(self, redis_client, prefix: str = "session:"):
        self._redis = redis_client
        self._prefix = prefix

    def _key(self, session_id: SessionID) -> str:
        return f"{self._prefix}{session_id.value}"

    async def load(self, session_id: SessionID) -> Optional[Session]:
        data = await self._redis.get(self._key(session_id))
        if data is None:
            return None
        return Session.from_dict(json.loads(data))

    async def save(self, session: Session) -> None:
        key = self._key(session.id)
        ttl = int(session.remaining_ttl.total_seconds())
        await self._redis.setex(
            key, ttl, json.dumps(session.to_dict())
        )
        # Update principal index
        if session.principal:
            index_key = f"principal:{session.principal.kind}:{session.principal.id}"
            await self._redis.sadd(index_key, session.id.value)

    async def delete(self, session_id: SessionID) -> None:
        await self._redis.delete(self._key(session_id))

    async def exists(self, session_id: SessionID) -> bool:
        return await self._redis.exists(self._key(session_id))

    async def clear(self) -> None:
        keys = await self._redis.keys(f"{self._prefix}*")
        if keys:
            await self._redis.delete(*keys)

    async def count(self) -> int:
        keys = await self._redis.keys(f"{self._prefix}*")
        return len(keys)

    async def cleanup_expired(self) -> int:
        # Redis handles expiry automatically via TTL
        return 0

    async def find_by_principal(
        self, principal_kind: str, principal_id: str
    ) -> list[Session]:
        index_key = f"principal:{principal_kind}:{principal_id}"
        session_ids = await self._redis.smembers(index_key)
        sessions = []
        for sid_value in session_ids:
            session = await self.load(SessionID(sid_value))
            if session:
                sessions.append(session)
        return sessions


# Register with engine:
engine = SessionEngine(
    stores={"redis": RedisStore(redis_client)},
    default_store="redis",
    # ...
)`}</CodeBlock>
      </section>

      {/* Store Comparison */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Store Comparison</h2>
        <div className={`overflow-x-auto ${boxClass}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
                <th className="text-left py-2 pr-4 font-semibold">Feature</th>
                <th className="text-left py-2 pr-4 font-semibold">MemoryStore</th>
                <th className="text-left py-2 pr-4 font-semibold">FileStore</th>
                <th className="text-left py-2 font-semibold">Custom (Redis)</th>
              </tr>
            </thead>
            <tbody className={isDark ? 'text-gray-400' : 'text-gray-600'}>
              {[
                ['Persistence', '❌ Lost on restart', '✅ Disk-persisted', '✅ Network-persisted'],
                ['Performance', '⚡ Fastest', '🐢 Disk I/O bound', '⚡ Fast (network)'],
                ['Multi-process', '❌ Single process', '✅ Shared filesystem', '✅ Shared network'],
                ['LRU Eviction', '✅ Built-in', '❌ Manual cleanup', '✅ Redis TTL'],
                ['Principal Index', '✅ Built-in', '❌ Full scan', '✅ Redis Sets'],
                ['Atomic Writes', 'N/A', '✅ tempfile+replace', '✅ Redis atomic ops'],
                ['Best For', 'Dev, single-server', 'Dev, low-traffic', 'Production, multi-node'],
              ].map(([feature, memory, file, custom], i) => (
                <tr key={i} className={`border-b ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
                  <td className="py-2 pr-4 font-semibold text-xs">{feature}</td>
                  <td className="py-2 pr-4 text-xs">{memory}</td>
                  <td className="py-2 pr-4 text-xs">{file}</td>
                  <td className="py-2 text-xs">{custom}</td>
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
